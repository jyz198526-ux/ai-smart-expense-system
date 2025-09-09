@echo off
chcp 65001 >nul
title AI智能申请单系统 - 快速启动

echo.
echo ==========================================
echo    🚀 AI智能申请单系统 快速启动
echo ==========================================
echo.

:: 切换到项目目录
cd /d "%~dp0"
echo 📁 当前目录: %CD%

:: 检查Python环境
echo.
echo 🔍 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python环境
    echo 请安装Python 3.8+
    pause
    exit /b 1
)
python --version

:: 检查依赖
echo.
echo 📦 检查依赖包...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo 📥 安装依赖包...
    pip install -r requirements.txt
)
echo ✅ 依赖包检查完成

:: 检查环境变量
echo.
echo 🔑 检查环境配置...
if not exist .env (
    echo ❌ 错误: 未找到.env配置文件
    echo 请确保.env文件存在并包含必要的API密钥
    pause
    exit /b 1
)
echo ✅ 环境配置文件存在

:: 检查端口
echo.
echo 🌐 检查端口8000...
netstat -an | find "8000" | find "LISTENING" >nul
if not errorlevel 1 (
    echo ⚠️  警告: 端口8000已被占用，尝试终止...
    for /f "tokens=5" %%a in ('netstat -ano ^| find "8000" ^| find "LISTENING"') do (
        taskkill /pid %%a /f >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
)

:: 启动服务
echo.
echo 🚀 启动AI智能申请单系统...
echo.
echo ==========================================
echo    系统启动中，请稍候...
echo    访问地址: http://localhost:8000
echo    按 Ctrl+C 停止服务
echo ==========================================
echo.

:: 启动服务器
python main.py

echo.
echo 服务已停止
pause







