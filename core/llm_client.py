"""LLM 客户端 — 通过 FreeLLMAPI (OpenAI 兼容) 实现 AI 文案生成与润色

依赖:
    - FreeLLMAPI 服务运行在 localhost:3001 (Docker 一键启动)
    - pip install openai

配置:
    环境变量 VOXCRAFT_LLM_BASE_URL (默认 http://localhost:3001/v1)
    环境变量 VOXCRAFT_LLM_API_KEY  (默认 freellmapi-local)
    环境变量 VOXCRAFT_LLM_MODEL    (默认 auto, 让路由器选模型)
"""

import os
from typing import Optional

_default_base = os.environ.get("VOXCRAFT_LLM_BASE_URL", "http://localhost:3001/v1")
_default_key = os.environ.get("VOXCRAFT_LLM_API_KEY", "freellmapi-local")
_default_model = os.environ.get("VOXCRAFT_LLM_MODEL", "auto")

# ── System Prompts ──────────────────────────────────────────

_GEN_SYSTEM = """\
你是一个专业的中文配音文案创作者。根据用户的描述生成适合语音合成 (TTS) 的中文文案。

规则:
1. 输出纯文本，不包含任何 Markdown 标记 (**、#、-、> 等)
2. 适合口语朗读，句子长度适中，长句拆短句
3. 自然使用逗号和句号制造停顿节奏
4. 中文为主，技术术语可保留英文
5. 不要输出任何解释说明，只输出文案本身
6. 如果用户指定了字数，尽量控制在范围内"""

_POLISH_SYSTEM = """\
你是一个专业的配音文案编辑。优化用户提供的文案，使其更适合语音合成 (TTS)。

优化方向:
1. 调整句子节奏，长句拆成短句
2. 用标点制造自然停顿 (逗号、句号、省略号)
3. 修正口语不通顺的表达
4. 保留原文意思、风格和情感基调
5. 输出纯文本，不包含任何 Markdown 标记
6. 不要输出任何解释说明，只输出优化后的文案"""


def _get_client():
    """懒加载 OpenAI 客户端"""
    from openai import OpenAI
    return OpenAI(
        base_url=_default_base,
        api_key=_default_key,
        timeout=30,
    )


def check_status() -> dict:
    """检测 FreeLLMAPI 是否可用

    返回:
        {"available": bool, "base_url": str, "model": str, "error": str}
    """
    try:
        client = _get_client()
        # 尝试列模型，能通就说明服务在线
        resp = client.models.list()
        models = [m.id for m in resp.data[:10]]
        return {
            "available": True,
            "base_url": _default_base,
            "model": _default_model,
            "models": models,
            "error": "",
        }
    except Exception as e:
        return {
            "available": False,
            "base_url": _default_base,
            "model": _default_model,
            "models": [],
            "error": str(e),
        }


def generate_script(prompt: str, word_count: Optional[int] = None) -> str:
    """根据提示词生成配音文案

    Args:
        prompt: 用户的描述，如 "写一段武侠旁白，讲一个剑客归隐山林的故事"
        word_count: 目标字数 (可选)

    Returns:
        生成的文案文本
    """
    client = _get_client()

    user_msg = prompt
    if word_count:
        user_msg += f"\n\n(目标字数: 约 {word_count} 字)"

    resp = client.chat.completions.create(
        model=_default_model,
        messages=[
            {"role": "system", "content": _GEN_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.8,
        max_tokens=2048,
    )
    return resp.choices[0].message.content.strip()


def polish_script(text: str, style: str = "") -> str:
    """润色文案使其更适合 TTS

    Args:
        text: 原始文案
        style: 风格提示 (可选)，如 "更激昂"、"更平静"、"更口语化"

    Returns:
        润色后的文案
    """
    client = _get_client()

    user_msg = text
    if style:
        user_msg += f"\n\n(风格要求: {style})"

    resp = client.chat.completions.create(
        model=_default_model,
        messages=[
            {"role": "system", "content": _POLISH_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.6,
        max_tokens=2048,
    )
    return resp.choices[0].message.content.strip()
