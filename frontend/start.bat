@echo off
chcp 65001 >nul
title ACG收藏馆 - 一键启动后端 + 前端
echo ============================================
echo   ACG收藏馆  一键启动 (后端 + 前端)
echo ============================================
echo.

REM 项目根目录（本脚本位于 frontend 子目录）
set "ROOT=%~dp0.."

REM ---------- 1. 启动 Redis ----------
echo [1/4] 检查 Redis...
tasklist /FI "IMAGENAME eq redis-server.exe" 2>nul | find /I "redis-server.exe" >nul
if %errorlevel%==0 (
    echo        Redis 已在运行,跳过启动
) else (
    echo        启动 Redis...
    start "Redis" redis-server
)

echo.

REM ---------- 2. 启动后端 ----------
echo [2/4] 启动后端 (FastAPI)...
cd /d "%ROOT%"
start "ACG后端" cmd /c "call venv\Scripts\activate && uvicorn main:app --reload --port 8000"
echo        后端已在新的窗口启动
echo.

REM 等待后端就绪
echo        等待后端就绪...
timeout /t 4 /nobreak >nul

echo.

REM ---------- 3. 安装前端依赖（如需要） ----------
echo [3/4] 检查前端依赖...
cd /d "%ROOT%\frontend"
if not exist node_modules (
    echo        检测到未安装依赖,正在安装 npm install（首次较慢）...
    call npm install
) else (
    echo        依赖已就绪,跳过安装
)

echo.

REM ---------- 4. 启动前端 ----------
echo [4/4] 启动前端 (Vite)...
start "ACG前端" cmd /c "cd /d ""%ROOT%\frontend"" && npm run dev"

echo.
echo ============================================
echo   启动完成!
echo   - 后端接口文档: http://localhost:8000/docs
echo   - 前端页面   : http://localhost:5173
echo   - 两个新窗口会自动打开并分别运行后端/前端
echo   关闭请直接关闭对应的窗口
echo ============================================
echo.
pause