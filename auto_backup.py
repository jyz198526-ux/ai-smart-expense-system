#!/usr/bin/env python3
"""
自动Git备份脚本
定时提交代码到GitHub，避免代码丢失
"""
import os
import subprocess
import datetime
import logging
import schedule
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_git_command(command):
    """执行Git命令"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            encoding='utf-8'
        )
        if result.returncode == 0:
            logger.info(f"✅ 命令执行成功: {command}")
            if result.stdout.strip():
                logger.info(f"输出: {result.stdout.strip()}")
            return True
        else:
            logger.error(f"❌ 命令执行失败: {command}")
            logger.error(f"错误: {result.stderr.strip()}")
            return False
    except Exception as e:
        logger.error(f"❌ 执行命令异常: {command}, 错误: {e}")
        return False

def auto_backup():
    """自动备份到GitHub"""
    logger.info("🚀 开始自动备份...")
    
    # 检查是否有变化
    if not run_git_command("git diff --quiet"):
        logger.info("📝 检测到代码变化，开始备份...")
        
        # 添加所有文件
        if not run_git_command("git add ."):
            return False
        
        # 生成提交信息
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"🔄 自动备份 - {timestamp}"
        
        # 提交变化
        if not run_git_command(f'git commit -m "{commit_message}"'):
            return False
        
        # 推送到远程仓库（如果已配置）
        if run_git_command("git remote get-url origin"):
            logger.info("📤 推送到远程仓库...")
            if run_git_command("git push origin main"):
                logger.info("✅ 自动备份完成！")
            else:
                logger.warning("⚠️ 推送失败，但本地提交成功")
        else:
            logger.info("ℹ️ 未配置远程仓库，仅本地提交")
            
        return True
    else:
        logger.info("ℹ️ 没有代码变化，跳过备份")
        return True

def manual_backup():
    """手动备份"""
    logger.info("🔧 手动备份模式")
    return auto_backup()

def setup_github_remote(repo_url):
    """设置GitHub远程仓库"""
    logger.info(f"🔗 设置远程仓库: {repo_url}")
    
    # 添加远程仓库
    if run_git_command(f"git remote add origin {repo_url}"):
        logger.info("✅ 远程仓库添加成功")
        
        # 设置上游分支
        if run_git_command("git branch -M main"):
            logger.info("✅ 设置主分支为main")
            
            # 首次推送
            if run_git_command("git push -u origin main"):
                logger.info("🎉 首次推送成功！")
                return True
            else:
                logger.error("❌ 首次推送失败")
                return False
        else:
            logger.error("❌ 设置主分支失败")
            return False
    else:
        logger.error("❌ 添加远程仓库失败")
        return False

def start_auto_backup_schedule():
    """启动定时备份调度"""
    logger.info("⏰ 启动定时备份调度...")
    
    # 每30分钟备份一次
    schedule.every(30).minutes.do(auto_backup)
    
    # 每天晚上23:00备份
    schedule.every().day.at("23:00").do(auto_backup)
    
    logger.info("📅 备份计划:")
    logger.info("  - 每30分钟自动备份")
    logger.info("  - 每天23:00定时备份")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    except KeyboardInterrupt:
        logger.info("⏹️ 停止定时备份")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AI申请单系统自动备份工具")
    parser.add_argument("--manual", action="store_true", help="手动备份一次")
    parser.add_argument("--setup", type=str, help="设置GitHub仓库URL")
    parser.add_argument("--schedule", action="store_true", help="启动定时备份")
    
    args = parser.parse_args()
    
    if args.setup:
        setup_github_remote(args.setup)
    elif args.manual:
        manual_backup()
    elif args.schedule:
        start_auto_backup_schedule()
    else:
        logger.info("请使用 --help 查看可用选项")
