# 声音编辑器

> "本地跑中文 TTS，不是 Python 版本对不上，就是模型只支持普通话，
> 要么命令行一片空白。配了一下午，听到的第一句话是机器人读错字。"

一条命令装好，一条命令出音频。基于 **Qwen3-TTS**，支持中文方言、声音克隆、多角色对话。
给人类用，也给 AI / agent 直接调用。

<p align="center">
  <img src="assets/cover.jpg" width="100%" alt="声音编辑器"/>
</p>

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green.svg)](pyproject.toml)
[![Platform](https://img.shields.io/badge/Platform-macOS%20Apple%20Silicon-black.svg)](pyproject.toml)

[English README](README_EN.md) · 姊妹项目：[asr-studio](https://github.com/webkubor/asr-studio)（语音转文字）

---

## 一分钟装好

```bash
git clone https://github.com/webkubor/voice-editor.git
cd voice-editor
chmod +x install.sh && ./install.sh
source .venv/bin/activate
voice --help
```

脚本自动完成：创建 `.venv` → 安装依赖 → 下载基础模型。

---

## 真实效果

```bash
# 克隆已有角色音色生成台词
voice clone narrator "霜叶红于二月花，山色空蒙雨亦奇"
# → out/narrator_20260421_143201.wav  [2.3s]

# 用文字描述设计新音色
voice design xiao_jing "这是一段建模短句" --tone "温柔、清晰、偏少女"
# → voice 'xiao_jing' saved to personas.json

# 多角色对白
voice dialogue --script scripts/chapter_01.txt
# → out/dialogue_20260421_143502/  (5 files merged)
```

---

## 当前能力

| 功能 | 状态 | 命令 |
|:---|:---:|:---|
| 声音克隆（角色复用） | ✅ | `voice clone <persona> "台词"` |
| 音色设计（文字描述） | ✅ | `voice design <name> "短句" --tone` |
| 多角色对话生成 | ✅ | `voice dialogue --script` |
| 音色列表管理 | ✅ | `voice voice list` |
| **Web UI** | ✅ | `voice web` |
| 环境自检 | 🚧 | `voice doctor`（Phase 2）|

---

## Web UI

不想敲命令行？启动本地 Web 界面，浏览器里点一点就能用：

```bash
voice web
# → http://localhost:8866
```

功能：
- 左侧音色库管理（上传参考音频 → 自动注册）
- 克隆合成（选音色 → 输入文本 → 在线试听 → 下载）
- 音色设计（文字描述 → 生成全新音色 → 入库复用）
- 音频库（历史生成列表 → 播放 / 下载 / 删除）

---

## 为什么选 Qwen3-TTS

- 中文 52 种方言支持（普通话 / 粤语 / 闽南语 / 吴语…）
- Apple Silicon MPS 加速，M 系芯片本地实时推理
- 完全开源，不需要联网，不需要 API Key

---

## 项目结构

```
voice-editor/
├── cli/            # CLI 入口与子命令
├── core/           # 语音引擎 / 模式调度 / 音频处理
├── web/            # Web UI（FastAPI + 前端单页）
├── configs/        # 运行配置与 personas 映射
├── assets/         # 参考音频 / 标准样音 / 产出
├── models/         # 本地模型目录
└── out/            # 默认输出目录
```

---

## 给 AI / Agent 调用

项目根目录提供 `.claude/skills/tts.md`，Claude Code 可以直接读取后无歧义执行 TTS 任务：

```bash
# Claude Code 调用示例
voice clone <persona> "<台词>" -o <output.wav>
```

Agent 调用前请先确认 `source .venv/bin/activate` 已执行，或使用 `.venv/bin/voice`。

---

## 路线图

- [x] Phase 1 — 命名统一、README 清晰化
- [x] Phase 2a — CLI 稳定（clone / design / dialogue / voice list）
- [x] Phase 3 — WebUI MVP（上传音频 / 试听 / 下载）
- [ ] Phase 2b — `voice doctor` 环境自检
- [ ] Phase 4 — Agent 无交互安装模式

---

## 适合谁

- 本地跑中文配音的创作者（有声书 / 短剧 / 游戏 NPC）
- 想把配音流程接给 AI 助手的开发者
- 武侠 / 古风 / 方言内容生产者

---

## License

Apache-2.0 · 基于 Qwen3-TTS 二次开发

---

**完整命令参考 → [docs/COMMANDS.md](docs/COMMANDS.md)**
