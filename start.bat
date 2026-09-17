@echo off
chcp 65001 >nul
title ACG收藏馆

REM 切换到本脚本所在目录(%~dp0 自动取当前路径，以后移动文件夹也不用改)
cd /d "%~dp0"

REM 优先使用项目自带的虚拟环境
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo [提示] 没有找到 venv 虚拟环境，将使用系统 Python
    echo        如果提示缺少依赖，请执行: pip install -r requirements.txt
    echo.
)

python run.py %*

echo.
echo 服务已停止，按任意键关闭窗口。
pause >nul
