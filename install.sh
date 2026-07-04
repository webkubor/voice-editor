#!/bin/bash
set -e

echo "🎙️ 欢迎使用声音编辑器 (Voice Editor) 安装向导 🎙️"
echo "=========================================================================="

# 1. Check for Python
if ! command -v python3 &> /dev/null
then
    echo "❌ 错误: 未找到 Python3。请先安装 Python 3.9+。"
    exit 1
fi

# 2. Check for FFmpeg (Required for MP3 and Auto-clipping)
if ! command -v ffmpeg &> /dev/null
then
    echo "⚠️ 警告: 未找到 FFmpeg。处理 MP3 和自动裁剪功能需要它。"
    echo "建议在 Mac 上执行: brew install ffmpeg"
fi

echo "3. Creating Python Virtual Environment (.venv)..."
python3 -m venv .venv

echo "4. Activating Virtual Environment..."
source .venv/bin/activate

echo "5. Upgrading pip and setuptools..."
pip install --upgrade pip
pip install "setuptools<70"

echo "6. Installing project dependencies..."
pip install -e .
pip install pydub modelscope

echo "7. Downloading Base Models (1.7B Recommended)..."
python -m modelscope.cli.cli download --model Qwen/Qwen3-TTS-12Hz-1.7B-Base --local_dir ./models/Base-1.7B

echo "=========================================================================="
echo "✨ 安装完成！"
echo "解码器（Tokenizer）已随模型自动下载。"
echo "To start: source .venv/bin/activate && voice --help"
