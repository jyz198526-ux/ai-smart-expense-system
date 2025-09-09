"""
配置管理模块
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# DeepSeek AI配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-43816199a7fd42f88e93b14358954b88")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions")

# 易快报认证配置
EK_APP_KEY = os.getenv("EK_APP_KEY", "b433ffa4-ff6e-4e76-95e6-1a7bed8777eb")
EK_APP_SECURITY = os.getenv("EK_APP_SECURITY", "60ec2aa6-6354-40b5-a742-0e1034962b2f")
EK_BASE_URL = os.getenv("EK_BASE_URL", "https://app.ekuaibao.com/api/openapi")

# 服务配置
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

# 缓存配置
TOKEN_CACHE_FILE = ".token_cache.json"
FIELD_MAPPING_CACHE_FILE = ".field_mapping_cache.json"

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")







