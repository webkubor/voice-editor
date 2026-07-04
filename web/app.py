"""声音编辑器 Web UI — FastAPI 后端

启动方式:
    .venv/bin/python -m web.app
    或
    .venv/bin/voice web
"""

import os
import sys
import json
import re
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── 路径设置 ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

OUT_DIR = BASE_DIR / "out"
TEMP_DIR = BASE_DIR / "assets" / "temp"
REF_DIR = BASE_DIR / "assets" / "reference_audio"
PERSONAS_FILE = BASE_DIR / "configs" / "personas.json"
MODELS_DIR = BASE_DIR / "models"

for d in [OUT_DIR, TEMP_DIR, REF_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── 引擎单例（懒加载） ────────────────────────────────────
_engine_lock = threading.Lock()
_base_engine = None
_design_engine = None
_processor = None
_model_status = {"base": False, "design": False, "loading": False, "error": ""}


def _check_model_dir(model_type: str) -> bool:
    """检查模型是否下载完成（不是 .incomplete 文件）"""
    if model_type == "VoiceDesign":
        p = MODELS_DIR / "VoiceDesign-1.7B"
    else:
        p = MODELS_DIR / "Base-1.7B"
    if not p.exists():
        return False
    # 检查是否有完整的 model.safetensors（不是 .incomplete）
    safetensors = list(p.glob("*.safetensors"))
    incomplete = list(p.glob("*.incomplete"))
    return len(safetensors) > 0 and len(incomplete) == 0


def _model_downloading(model_type: str) -> bool:
    """检查模型是否正在下载"""
    if model_type == "VoiceDesign":
        p = MODELS_DIR / "VoiceDesign-1.7B"
    else:
        p = MODELS_DIR / "Base-1.7B"
    if not p.exists():
        return False
    return len(list(p.glob("*.incomplete"))) > 0


def _get_processor():
    global _processor
    if _processor is None:
        from core.processor import AudioProcessor
        _processor = AudioProcessor(str(BASE_DIR))
    return _processor


def _get_base_engine():
    """懒加载 Base 引擎（克隆模式用）"""
    global _base_engine, _model_status
    if _base_engine is not None:
        return _base_engine

    with _engine_lock:
        if _base_engine is not None:
            return _base_engine
        if not _check_model_dir("Base"):
            raise RuntimeError(
                f"Base 模型未下载。请先运行 install.sh 或手动下载:\n"
                f"  .venv/bin/python -m modelscope.cli.cli download "
                f"--model Qwen/Qwen3-TTS-12Hz-1.7B-Base --local_dir ./models/Base-1.7B"
            )
        from core.engine import TTSBaseEngine
        print("🚀 正在加载 Base-1.7B 引擎...")
        _base_engine = TTSBaseEngine("Base", "1.7B")
        _model_status["base"] = True
        print("✅ Base 引擎就绪")
        return _base_engine


def _get_design_engine():
    """懒加载 VoiceDesign 引擎（设计模式用）"""
    global _design_engine, _model_status
    if _design_engine is not None:
        return _design_engine

    with _engine_lock:
        if _design_engine is not None:
            return _design_engine
        if not _check_model_dir("VoiceDesign"):
            raise RuntimeError(
                f"VoiceDesign 模型未下载。请手动下载:\n"
                f"  .venv/bin/python -m modelscope.cli.cli download "
                f"--model Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign --local_dir ./models/VoiceDesign-1.7B"
            )
        from core.engine import TTSBaseEngine
        print("🚀 正在加载 VoiceDesign-1.7B 引擎...")
        _design_engine = TTSBaseEngine("VoiceDesign", "1.7B")
        _model_status["design"] = True
        print("✅ VoiceDesign 引擎就绪")
        return _design_engine


# ── Pydantic 模型 ─────────────────────────────────────────
class CloneRequest(BaseModel):
    persona: str
    text: str
    tone: Optional[str] = ""
    emotion: Optional[str] = ""
    emotion_priority: bool = False
    reference_audio: Optional[str] = None


class DesignRequest(BaseModel):
    voice_name: str
    text: str = "这是一段用于音色建模的短句，请保持自然呼吸。"
    tone: str = ""
    emotion: str = ""
    commit: bool = False


class PersonaAddRequest(BaseModel):
    key: str
    name: Optional[str] = None
    instruction: Optional[str] = ""


# ── FastAPI 应用 ──────────────────────────────────────────
app = FastAPI(title="声音编辑器 Web UI", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")


# ── 页面路由 ──────────────────────────────────────────────
@app.get("/")
async def index():
    return FileResponse(str(Path(__file__).parent / "static" / "index.html"))


# ── API 路由 ──────────────────────────────────────────────
@app.get("/api/status")
async def get_status():
    """检查模型和系统状态"""
    return {
        "base_model": _check_model_dir("Base"),
        "design_model": _check_model_dir("VoiceDesign"),
        "base_downloading": _model_downloading("Base"),
        "design_downloading": _model_downloading("VoiceDesign"),
        "base_loaded": _base_engine is not None,
        "design_loaded": _design_engine is not None,
        "loading": _model_status["loading"],
        "error": _model_status["error"],
    }


def _scan_design_presets() -> list:
    """扫描 configs/presets/ 目录，加载设计配方"""
    preset_dir = BASE_DIR / "configs" / "presets"
    result = []
    if not preset_dir.exists():
        return result
    for f in sorted(preset_dir.glob("*.json")):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                cfg = json.load(fh)
            if cfg.get("model_type") != "VoiceDesign":
                continue
            voice_name = cfg.get("voice_name", "").strip()
            if not voice_name:
                continue
            result.append({
                "voice_name": voice_name,
                "config_file": f.name,
                "tone": cfg.get("tone", ""),
                "emotion": cfg.get("emotion", ""),
                "text": cfg.get("text", ""),
            })
        except Exception:
            continue
    return result


@app.get("/api/personas")
async def list_personas():
    """列出所有已注册音色 + 设计预设"""
    # 从 personas.json 加载已注册音色
    registered = {}
    if PERSONAS_FILE.exists():
        try:
            with open(PERSONAS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        for key, val in data.items():
            if isinstance(val, dict):
                name = val.get("name", key)
                temp_path = TEMP_DIR / f"当前参考_{name}.wav"
                ref_rel = val.get("ref", "")
                ref_path = BASE_DIR / ref_rel if ref_rel else None
                registered[key] = {
                    **val,
                    "source": "registered",
                    "has_temp": temp_path.exists(),
                    "has_ref": ref_path.exists() if ref_path else False,
                }
            else:
                registered[key] = {
                    "name": val,
                    "source": "registered",
                    "has_temp": False,
                    "has_ref": False,
                }

    # 设计预设
    presets = _scan_design_presets()

    return {"personas": registered, "presets": presets, "total": len(registered)}


@app.post("/api/personas/add")
async def add_persona(
    key: str = Form(...),
    name: str = Form(None),
    instruction: str = Form(""),
    audio: UploadFile = File(...),
):
    """上传参考音频并注册新音色"""
    from core.utils import upsert_persona_mapping, sanitize_path_component

    display_name = name or key
    safe_key = sanitize_path_component(key, fallback="unknown")
    safe_name = sanitize_path_component(display_name, fallback="未命名角色")

    # 保存上传的音频
    ext = os.path.splitext(audio.filename or "audio.wav")[1].lower()
    if ext not in (".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac"):
        ext = ".wav"

    ref_filename = f"{safe_name}_参考{ext}"
    ref_path = REF_DIR / ref_filename
    with open(ref_path, "wb") as f:
        content = await audio.read()
        f.write(content)

    # 提取标准样音
    processor = _get_processor()
    temp_path = processor.extract_voice_seed(
        str(ref_path), display_name, max_sec=10, skip_start_ms=1500
    )

    ref_rel = os.path.relpath(str(temp_path), str(BASE_DIR)).replace("\\", "/")
    upsert_persona_mapping(
        str(BASE_DIR),
        persona_key=safe_key,
        persona_name=display_name,
        ref_rel=ref_rel,
        design_rel="",
        instruction=instruction or "",
    )

    return {"ok": True, "key": safe_key, "name": display_name, "ref": ref_rel}


@app.delete("/api/personas/{key}")
async def delete_persona(key: str):
    """删除音色注册（不删除音频文件）"""
    if not PERSONAS_FILE.exists():
        raise HTTPException(404, "personas.json 不存在")

    with open(PERSONAS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if key not in data:
        raise HTTPException(404, f"音色 {key} 不存在")

    del data[key]
    with open(PERSONAS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {"ok": True}


@app.post("/api/clone")
async def clone(req: CloneRequest):
    """克隆合成"""
    import soundfile as sf
    import torch
    from core.modes.cloner import CloneMode
    from core.utils import get_persona_map, get_persona_cn

    # 校验
    if not req.text.strip():
        raise HTTPException(400, "文本不能为空")
    if len(req.text) > 400:
        raise HTTPException(400, f"文本过长（{len(req.text)} > 400 字）")

    persona_map = get_persona_map()
    if req.persona not in persona_map:
        raise HTTPException(400, f"音色 {req.persona} 未注册，请先在 Web UI 上传参考音频")

    pdata = persona_map[req.persona]
    if not isinstance(pdata, dict):
        pdata = {}
    display_name = get_persona_cn(req.persona)

    # 解析参考音频
    ref_path = None
    if req.reference_audio:
        p = Path(req.reference_audio)
        if not p.is_absolute():
            p = BASE_DIR / req.reference_audio
        if p.exists():
            ref_path = p

    if not ref_path:
        temp_path = TEMP_DIR / f"当前参考_{display_name}.wav"
        if temp_path.exists():
            ref_path = temp_path

    if not ref_path:
        ref_rel = pdata.get("ref", "")
        if ref_rel:
            p = BASE_DIR / ref_rel
            if p.exists():
                ref_path = p

    if not ref_path:
        raise HTTPException(
            400,
            f"音色 {req.persona} 未找到参考音频。"
            f"请先上传参考音频或检查 assets/temp/当前参考_{display_name}.wav"
        )

    # 构建指令
    base_instruct = pdata.get("instruction", "")
    if req.emotion_priority:
        final_instruct = (req.tone or req.emotion or "").strip()
    else:
        raw = " ".join(filter(None, [req.tone or "", req.emotion or ""]))
        final_instruct = f"{base_instruct} {raw}".strip()

    try:
        engine = _get_base_engine()
        processor = _get_processor()
        cloner = CloneMode(engine, processor)

        # 生成
        torch.manual_seed(42)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(42)

        wavs, sr = cloner.run(
            persona=req.persona,
            text=req.text,
            lang="Chinese",
            instruct=final_instruct,
            emotion_priority=req.emotion_priority,
            allow_ref_fallback=True,
            reference_audio=str(ref_path),
        )

        # 保存
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = re.sub(r"[^\w\u4e00-\u9fff-]", "_", display_name)
        out_filename = f"[克隆]{safe_name}_{ts}.wav"
        out_path = OUT_DIR / out_filename
        sf.write(str(out_path), wavs[0], sr)
        processor.apply_post_tuning(str(out_path))

        return {
            "ok": True,
            "filename": out_filename,
            "url": f"/api/audio/{out_filename}",
            "persona": display_name,
            "text": req.text,
        }
    except RuntimeError as e:
        raise HTTPException(500, str(e))
    except Exception as e:
        raise HTTPException(500, f"合成失败: {e}")


@app.post("/api/design")
async def design(req: DesignRequest):
    """音色设计"""
    import soundfile as sf
    from core.modes.designer import DesignMode
    from core.utils import (
        upsert_persona_mapping,
        resolve_design_voice_key,
        write_generation_json,
        sanitize_path_component,
    )

    if not (req.tone or req.emotion):
        raise HTTPException(400, "必须提供 tone 或 emotion（至少一个）")

    if not req.text.strip():
        req.text = "这是一段用于音色建模的短句，请保持自然呼吸。"
    if len(req.text) > 45:
        raise HTTPException(400, f"设计文本过长（{len(req.text)} > 45 字）")

    instruct = " ".join(p.strip() for p in [req.tone, req.emotion] if p.strip())

    try:
        engine = _get_design_engine()
        processor = _get_processor()
        designer = DesignMode(engine, processor)

        wavs, sr = designer.run(text=req.text, lang="Chinese", instruct=instruct)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = re.sub(r"[^\w\u4e00-\u9fff-]", "_", req.voice_name)
        out_filename = f"[设计]{safe_name}_{ts}.wav"
        out_path = OUT_DIR / out_filename
        sf.write(str(out_path), wavs[0], sr)
        processor.apply_design_cleanup(str(out_path))

        result = {
            "ok": True,
            "filename": out_filename,
            "url": f"/api/audio/{out_filename}",
            "voice_name": req.voice_name,
        }

        # 如果 commit，沉淀到标准样音库
        if req.commit:
            voice_key = resolve_design_voice_key({"voice_name": req.voice_name})
            temp_seed_path = processor.extract_voice_seed(
                str(out_path), req.voice_name, max_sec=10, skip_start_ms=0
            )
            ref_rel = os.path.relpath(str(temp_seed_path), str(BASE_DIR)).replace("\\", "/")
            design_rel = f"voice_designs/{safe_name}.json"
            upsert_persona_mapping(
                str(BASE_DIR),
                persona_key=voice_key,
                persona_name=req.voice_name,
                ref_rel=ref_rel,
                design_rel=design_rel,
                instruction=instruct,
            )
            write_generation_json(str(BASE_DIR), voice_key, source="voice_design")
            result["committed"] = True
            result["persona_key"] = voice_key

        return result
    except RuntimeError as e:
        raise HTTPException(500, str(e))
    except Exception as e:
        raise HTTPException(500, f"设计失败: {e}")


@app.get("/api/audio-list")
async def audio_list():
    """列出已生成的音频文件"""
    files = []
    if OUT_DIR.exists():
        for f in sorted(OUT_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.suffix.lower() == ".wav":
                stat = f.stat()
                files.append({
                    "filename": f.name,
                    "url": f"/api/audio/{f.name}",
                    "size": stat.st_size,
                    "size_mb": round(stat.st_size / 1024 / 1024, 2),
                    "created": datetime.fromtimestamp(stat.st_mtime).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                })
    return {"files": files}


@app.get("/api/audio/{filename}")
async def get_audio(filename: str):
    """获取音频文件"""
    # 防止路径穿越
    safe = os.path.basename(filename)
    path = OUT_DIR / safe
    if not path.exists():
        raise HTTPException(404, f"音频文件不存在: {safe}")
    return FileResponse(str(path), media_type="audio/wav", filename=safe)


@app.delete("/api/audio/{filename}")
async def delete_audio(filename: str):
    """删除音频文件"""
    safe = os.path.basename(filename)
    path = OUT_DIR / safe
    if not path.exists():
        raise HTTPException(404, f"音频文件不存在: {safe}")
    path.unlink()
    return {"ok": True}


# ── 启动入口 ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("  声音编辑器 Web UI")
    print("  http://localhost:8866")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8866)
