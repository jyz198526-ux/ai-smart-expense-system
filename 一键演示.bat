@echo off
chcp 65001 >nul
title AI智能申请单系统 - 一键演示

echo.
echo =====================================================
echo    🎭 AI智能申请单系统 - 一键演示启动
echo =====================================================
echo.

:: 切换到项目目录
cd /d "%~dp0"

:: 运行启动前检查
echo 🔍 正在进行演示前检查...
echo.
python 启动前检查.py

if errorlevel 1 (
    echo.
    echo ❌ 检查失败，无法启动演示
    echo 请查看上方错误信息并修复问题
    pause
    exit /b 1
)

echo.
echo ✅ 检查完成，准备启动演示...
echo.

:: 等待用户确认
echo 📋 演示准备就绪！
echo.
echo 🎯 演示流程：
echo    1. 系统将启动在 http://localhost:8000
echo    2. 输入："我要创建申请单"
echo    3. 查看AI展示的字段清单
echo    4. 输入："标题是北京出差，金额3000元，项目是客户调研"
echo    5. 验证申请单创建成功
echo.
echo 💡 演示亮点：
echo    ✅ 严格两阶段交互
echo    ✅ 动态字段适应
echo    ✅ 智能字段映射  
echo    ✅ 闭环验证机制
echo.

set /p confirm="准备开始演示吗？(Y/N): "
if /i not "%confirm%"=="Y" (
    echo 演示已取消
    pause
    exit /b 0
)

:: 启动系统
echo.
echo 🚀 正在启动AI智能申请单系统...
echo.
echo =====================================================
echo    系统启动中...
echo    🌐 访问地址: http://localhost:8000
echo    📖 演示指南: 演示启动指南.md
echo    🛑 按 Ctrl+C 停止服务
echo =====================================================
echo.

:: 自动打开浏览器（延迟3秒）
start "" /min cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:8000"

:: 启动服务器
python main.py

echo.
echo 🎭 演示结束
pause







