@echo off
chcp 65001 >nul
echo 🚀 AI智能申请单系统 - GitHub集成设置
echo.

:MENU
echo 请选择操作:
echo 1. 初始提交到GitHub
echo 2. 设置定时备份
echo 3. 手动备份一次
echo 4. 查看Git状态
echo 5. 退出
echo.
set /p choice=请输入选项 (1-5): 

if "%choice%"=="1" goto SETUP_GITHUB
if "%choice%"=="2" goto SETUP_SCHEDULE
if "%choice%"=="3" goto MANUAL_BACKUP
if "%choice%"=="4" goto GIT_STATUS
if "%choice%"=="5" goto EXIT
goto MENU

:SETUP_GITHUB
echo.
echo 📝 GitHub仓库设置
echo 请先在GitHub上创建一个新的空仓库
echo.
set /p repo_url=请输入GitHub仓库URL (例: https://github.com/username/repo.git): 

if "%repo_url%"=="" (
    echo ❌ 仓库URL不能为空
    pause
    goto MENU
)

echo.
echo 🔄 正在设置GitHub仓库...

REM 配置Git用户信息（如果还没有配置）
git config --global user.name >nul 2>&1
if errorlevel 1 (
    set /p git_name=请输入Git用户名: 
    git config --global user.name "%git_name%"
)

git config --global user.email >nul 2>&1
if errorlevel 1 (
    set /p git_email=请输入Git邮箱: 
    git config --global user.email "%git_email%"
)

REM 初始提交
echo 📦 添加所有文件...
git add .

echo 📝 创建初始提交...
git commit -m "🎉 初始提交: AI智能申请单系统"

echo 🔗 添加远程仓库...
git remote add origin %repo_url%

echo 📤 推送到GitHub...
git branch -M main
git push -u origin main

if errorlevel 0 (
    echo.
    echo ✅ GitHub仓库设置成功！
    echo 🔗 仓库地址: %repo_url%
    echo.
    echo 💡 提示: 你现在可以:
    echo    - 使用选项2设置定时备份
    echo    - 使用选项3手动备份
) else (
    echo.
    echo ❌ 设置失败，请检查:
    echo    - 网络连接是否正常
    echo    - GitHub仓库URL是否正确
    echo    - 是否有推送权限
)

pause
goto MENU

:SETUP_SCHEDULE
echo.
echo ⏰ 设置定时备份
echo.
echo 正在启动定时备份服务...
echo 📅 备份计划:
echo    - 每30分钟自动备份
echo    - 每天23:00定时备份
echo.
echo 💡 提示: 按 Ctrl+C 停止定时备份
echo.
python auto_backup.py --schedule
goto MENU

:MANUAL_BACKUP
echo.
echo 🔧 手动备份
echo.
python auto_backup.py --manual
echo.
pause
goto MENU

:GIT_STATUS
echo.
echo 📊 Git仓库状态
echo.
git status
echo.
echo 📈 提交历史 (最近5条):
git log --oneline -5
echo.
pause
goto MENU

:EXIT
echo.
echo 👋 感谢使用AI智能申请单系统！
exit /b 0
