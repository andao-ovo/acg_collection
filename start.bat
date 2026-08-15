@echo off
echo ============================
echo   ACG收藏馆 一键启动
echo ============================

REM 进入项目文件夹
cd /d D:\虚拟c盘\study\0.4更新用户系统

REM 启动 Redis（如果没启动）
echo 启动 Redis...
start redis-server

REM 激活虚拟环境
call venv\Scripts\activate

REM 启动后端
echo 启动后端...
uvicorn main:app --reload

pause