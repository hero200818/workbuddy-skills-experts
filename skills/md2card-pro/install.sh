#!/bin/bash
# md2card-pro 技能依赖安装脚本
# 用法: bash install.sh

echo "=== md2card-pro 依赖安装 ==="

# 1. 安装系统依赖
echo "[1/3] 安装系统依赖 (pandoc, chromium)..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y pandoc chromium-browser 2>/dev/null || sudo apt-get install -y pandoc chromium 2>/dev/null
elif command -v brew &> /dev/null; then
    brew install pandoc chromium
else
    echo "请手动安装 pandoc 和 chromium"
fi

# 2. 安装 Python 依赖
echo "[2/3] 安装 Python 依赖..."
pip3 install pypandoc Pillow -i https://pypi.org/simple/

# 3. 验证安装
echo "[3/3] 验证安装..."
pandoc --version 2>/dev/null | head -1 && echo "✓ pandoc 已安装" || echo "✗ pandoc 未安装"
python3 -c "import pypandoc; print('✓ pypandoc 已安装')" 2>/dev/null || echo "✗ pypandoc 未安装"
python3 -c "import PIL; print('✓ Pillow 已安装')" 2>/dev/null || echo "✗ Pillow 未安装"
which chromium-browser chromium google-chrome 2>/dev/null | head -1 && echo "✓ Chromium 已安装" || echo "✗ Chromium 未安装（将使用 wkhtmltoimage）"

echo ""
echo "=== 安装完成 ==="
echo "使用方法: python3 md2card_pro.py 输入.md 输出.png --tag 标签名"
echo "风格: iOS 27 液态玻璃（唯一）"
