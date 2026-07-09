@echo off
chcp 65001 >nul
echo ============================================================
echo   🍵 奶茶店智能选址分析系统 - 启动脚本
echo ============================================================
echo.

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 切换到后端目录
cd /d "%~dp0backend"

REM 检查依赖
echo 📦 检查依赖包...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo 📥 安装依赖包...
    pip install -r requirements.txt
)

echo.
echo 🚀 启动服务...
echo.
echo 📌 服务地址: http://localhost:5000
echo 📌 前端页面: http://localhost:5000/
echo.
echo 按 Ctrl+C 停止服务
echo.

python run.py

pause
