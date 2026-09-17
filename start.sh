#!/usr/bin/env sh
# ACG收藏馆 一键启动 (macOS / Linux)
# 用法:  ./start.sh          或   sh start.sh
set -e

cd "$(dirname "$0")"

# 优先使用项目自带的虚拟环境
if [ -f "venv/bin/activate" ]; then
    . venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
    . .venv/bin/activate
else
    echo "[提示] 没有找到 venv 虚拟环境，将使用系统 Python"
    echo "       如果提示缺少依赖，请执行: pip install -r requirements.txt"
    echo
fi

exec python run.py "$@"
