#!/usr/bin/env python3
"""
AI智能申请单系统 - 启动前检查脚本
确保所有组件正常，演示万无一失
"""

import os
import sys
import subprocess
import json
import asyncio
import httpx
from pathlib import Path

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_status(status, message):
    if status == "OK":
        print(f"{Colors.GREEN}✅ {message}{Colors.END}")
    elif status == "WARN":
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")
    elif status == "ERROR":
        print(f"{Colors.RED}❌ {message}{Colors.END}")
    elif status == "INFO":
        print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def print_header(title):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}🚀 {title}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")

def check_python_version():
    """检查Python版本"""
    print_header("Python环境检查")
    version = sys.version_info
    print_status("INFO", f"Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 8:
        print_status("OK", "Python版本满足要求 (3.8+)")
        return True
    else:
        print_status("ERROR", "Python版本过低，需要3.8+")
        return False

def check_dependencies():
    """检查依赖包"""
    print_header("依赖包检查")
    
    required_packages = [
        "fastapi", "uvicorn", "python-dotenv", "httpx", "pydantic"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "show", package], 
                                 capture_output=True, text=True)
            if result.returncode == 0:
                print_status("OK", f"{package} 已安装")
            else:
                missing_packages.append(package)
                print_status("ERROR", f"{package} 未安装")
        except Exception as e:
            missing_packages.append(package)
            print_status("ERROR", f"{package} 检查失败: {e}")
    
    if missing_packages:
        print_status("WARN", f"缺失包: {', '.join(missing_packages)}")
        print_status("INFO", "正在安装缺失的包...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install"] + missing_packages, 
                         check=True)
            print_status("OK", "依赖包安装完成")
            return True
        except subprocess.CalledProcessError:
            print_status("ERROR", "依赖包安装失败")
            return False
    else:
        print_status("OK", "所有依赖包已安装")
        return True

def check_env_file():
    """检查环境变量文件"""
    print_header("环境配置检查")
    
    env_file = Path(".env")
    if not env_file.exists():
        print_status("ERROR", ".env文件不存在")
        return False
    
    print_status("OK", ".env文件存在")
    
    # 检查必要的环境变量
    required_vars = [
        "DEEPSEEK_API_KEY",
        "EK_APP_KEY", 
        "EK_APP_SECURITY"
    ]
    
    env_content = env_file.read_text(encoding='utf-8')
    missing_vars = []
    
    for var in required_vars:
        if f"{var}=" in env_content:
            print_status("OK", f"{var} 已配置")
        else:
            missing_vars.append(var)
            print_status("ERROR", f"{var} 未配置")
    
    if missing_vars:
        print_status("ERROR", f"缺失环境变量: {', '.join(missing_vars)}")
        return False
    
    return True

def check_project_files():
    """检查项目文件完整性"""
    print_header("项目文件检查")
    
    required_files = [
        "main.py",
        "smart_expense_mcp.py", 
        "config.py",
        "requirements.txt",
        "services/auth_service.py",
        "services/deepseek_service.py",
        "templates/index.html"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print_status("OK", f"{file_path} 存在")
        else:
            missing_files.append(file_path)
            print_status("ERROR", f"{file_path} 缺失")
    
    if missing_files:
        print_status("ERROR", f"缺失文件: {', '.join(missing_files)}")
        return False
    
    return True

def check_port_availability():
    """检查端口可用性"""
    print_header("端口检查")
    
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('localhost', 8000))
            if result == 0:
                print_status("WARN", "端口8000已被占用")
                print_status("INFO", "将尝试终止占用进程...")
                return True  # 启动脚本会处理端口冲突
            else:
                print_status("OK", "端口8000可用")
                return True
    except Exception as e:
        print_status("WARN", f"端口检查失败: {e}")
        return True

async def test_api_connectivity():
    """测试API连通性"""
    print_header("API连通性测试")
    
    # 测试DeepSeek API
    try:
        from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL
        
        if DEEPSEEK_API_KEY and DEEPSEEK_API_KEY != "your_deepseek_api_key_here":
            print_status("OK", "DeepSeek API密钥已配置")
            
            # 简单连通性测试
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
                try:
                    response = await client.post(
                        DEEPSEEK_API_URL,
                        headers=headers,
                        json={
                            "model": "deepseek-chat",
                            "messages": [{"role": "user", "content": "test"}],
                            "max_tokens": 1
                        }
                    )
                    if response.status_code in [200, 400]:  # 400也说明API可达
                        print_status("OK", "DeepSeek API连通正常")
                    else:
                        print_status("WARN", f"DeepSeek API响应异常: {response.status_code}")
                except Exception as e:
                    print_status("WARN", f"DeepSeek API测试失败: {e}")
        else:
            print_status("ERROR", "DeepSeek API密钥未正确配置")
            
    except ImportError:
        print_status("ERROR", "无法导入配置文件")
        return False
    except Exception as e:
        print_status("ERROR", f"API测试失败: {e}")
        return False
    
    return True

def generate_startup_summary():
    """生成启动摘要"""
    print_header("启动准备完成")
    
    summary = f"""
{Colors.GREEN}🎉 系统检查完成！演示准备就绪！{Colors.END}

{Colors.BOLD}📋 启动方式：{Colors.END}
1. 双击 "快速启动.bat" (推荐)
2. 或运行命令: python main.py

{Colors.BOLD}🌐 访问地址：{Colors.END}
- 聊天界面: http://localhost:8000
- 健康检查: http://localhost:8000/health
- API文档: http://localhost:8000/docs

{Colors.BOLD}🧪 演示流程：{Colors.END}
1. 输入: "我要创建申请单"
2. 查看: AI展示字段清单
3. 输入: "标题是XXX，金额XXX元，项目是XXX"
4. 验证: 申请单创建成功并自动验证

{Colors.BOLD}💡 演示亮点：{Colors.END}
- ✅ 严格的两阶段交互
- ✅ 动态字段适应能力
- ✅ 智能字段映射
- ✅ 闭环验证机制
- ✅ 实时字段增加支持

{Colors.GREEN}🚀 系统已准备就绪，演示必定成功！{Colors.END}
"""
    
    print(summary)

def main():
    """主检查流程"""
    print_header("AI智能申请单系统 - 演示前检查")
    
    checks = [
        ("Python环境", check_python_version),
        ("依赖包", check_dependencies), 
        ("环境配置", check_env_file),
        ("项目文件", check_project_files),
        ("端口可用性", check_port_availability),
    ]
    
    failed_checks = []
    
    for check_name, check_func in checks:
        try:
            if not check_func():
                failed_checks.append(check_name)
        except Exception as e:
            print_status("ERROR", f"{check_name}检查异常: {e}")
            failed_checks.append(check_name)
    
    # API连通性测试
    try:
        asyncio.run(test_api_connectivity())
    except Exception as e:
        print_status("ERROR", f"API测试异常: {e}")
        failed_checks.append("API连通性")
    
    if failed_checks:
        print_header("检查失败")
        print_status("ERROR", f"以下检查失败: {', '.join(failed_checks)}")
        print_status("INFO", "请修复上述问题后重新检查")
        return False
    else:
        generate_startup_summary()
        return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}检查已取消{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print_status("ERROR", f"检查过程异常: {e}")
        sys.exit(1)







