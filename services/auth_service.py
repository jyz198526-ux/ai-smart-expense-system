"""
易快报认证服务
实现Token获取、刷新和缓存管理
"""
import httpx
import json
import time
import logging
from typing import Optional
from config import EK_APP_KEY, EK_APP_SECURITY, EK_BASE_URL, TOKEN_CACHE_FILE

logger = logging.getLogger(__name__)

class AuthService:
    """易快报认证服务"""
    
    def __init__(self):
        self.app_key = EK_APP_KEY
        self.app_security = EK_APP_SECURITY
        self.base_url = EK_BASE_URL
        self.cache_file = TOKEN_CACHE_FILE
        self._token_cache = None
        self._startup_token_refreshed = False  # 标记启动时是否已刷新TOKEN
    
    async def get_access_token(self) -> str:
        """获取访问令牌（每次启动强制刷新）"""
        
        # 启动时强制刷新TOKEN
        if not self._startup_token_refreshed:
            logger.info("🔄 启动时强制刷新TOKEN")
            self._startup_token_refreshed = True
            
            # 加载缓存的token
            self._load_token_cache()
            
            # 尝试刷新令牌
            if self._token_cache and self._token_cache.get("refreshToken"):
                logger.info("使用refreshToken刷新访问令牌")
                if await self._refresh_token():
                    return self._token_cache["accessToken"]
            
            # 如果刷新失败，获取新令牌
            logger.info("获取全新的访问令牌")
            return await self._get_new_token()
        
        # 非启动时检查缓存
        if self._is_token_valid():
            logger.info("使用缓存的访问令牌")
            return self._token_cache["accessToken"]
        
        # 尝试刷新令牌
        if self._token_cache and self._token_cache.get("refreshToken"):
            logger.info("尝试刷新访问令牌")
            if await self._refresh_token():
                return self._token_cache["accessToken"]
        
        # 重新获取令牌
        logger.info("获取新的访问令牌")
        return await self._get_new_token()
    
    def _is_token_valid(self) -> bool:
        """检查令牌是否有效"""
        
        if not self._token_cache:
            self._load_token_cache()
        
        if not self._token_cache:
            return False
        
        # 检查是否过期（提前5分钟刷新）
        expire_time = self._token_cache.get("expireTime", 0) / 1000
        current_time = time.time()
        
        is_valid = current_time < (expire_time - 300)  # 提前5分钟
        
        if is_valid:
            logger.debug(f"Token有效，过期时间: {expire_time}, 当前时间: {current_time}")
        else:
            logger.debug(f"Token已过期或即将过期，过期时间: {expire_time}, 当前时间: {current_time}")
        
        return is_valid
    
    async def _get_new_token(self) -> str:
        """获取新的访问令牌"""
        
        url = f"{self.base_url}/v1/auth/getAccessToken"
        payload = {
            "appKey": self.app_key,
            "appSecurity": self.app_security
        }
        
        logger.info(f"调用易快报API获取新Token: {url}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"获取Token成功: {result.get('value', {}).get('accessToken', 'Unknown')[:20]}...")
            
            self._token_cache = result["value"]
            self._save_token_cache()
            
            return self._token_cache["accessToken"]
    
    async def _refresh_token(self) -> bool:
        """刷新访问令牌"""
        
        try:
            url = f"{self.base_url}/v2/auth/refreshToken"
            params = {
                "accessToken": self._token_cache["accessToken"],
                "refreshToken": self._token_cache["refreshToken"],
                "powerCode": "219904"
            }
            
            logger.info(f"刷新Token: {url}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, params=params)
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"刷新Token成功: {result.get('value', {}).get('accessToken', 'Unknown')[:20]}...")
                
                self._token_cache = result["value"]
                self._save_token_cache()
                
                return True
                
        except Exception as e:
            logger.error(f"刷新令牌失败: {e}")
            return False
    
    def _load_token_cache(self):
        """加载令牌缓存"""
        try:
            with open(self.cache_file, 'r') as f:
                self._token_cache = json.load(f)
                logger.debug("加载Token缓存成功")
        except FileNotFoundError:
            logger.debug("Token缓存文件不存在")
            self._token_cache = None
        except Exception as e:
            logger.error(f"加载Token缓存失败: {e}")
            self._token_cache = None
    
    def _save_token_cache(self):
        """保存令牌缓存"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self._token_cache, f)
                logger.debug("保存Token缓存成功")
        except Exception as e:
            logger.error(f"保存Token缓存失败: {e}")
    
    async def test_connection(self) -> bool:
        """测试连接是否正常"""
        try:
            token = await self.get_access_token()
            logger.info(f"认证服务测试成功，Token: {token[:20]}...")
            return True
        except Exception as e:
            logger.error(f"认证服务测试失败: {e}")
            return False




