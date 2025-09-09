# API集成文档

## 📋 易快报API集成

### 🔐 认证机制

#### 获取访问令牌
```bash
POST https://app.ekuaibao.com/api/openapi/v1/auth/getAccessToken

Content-Type: application/json

{
    "appKey": "b433ffa4-ff6e-4e76-95e6-1a7bed8777eb",
    "appSecurity": "60ec2aa6-6354-40b5-a742-0e1034962b2f"
}
```

**成功响应**：
```json
{
    "value": {
        "accessToken": "u-E4PVy28Q0400",
        "refreshToken": "asg4PVy28Q0800", 
        "expireTime": 1531046137469,
        "corporationId": "34A73EyI8A0w00"
    }
}
```

#### 刷新访问令牌
```bash
POST https://app.ekuaibao.com/api/openapi/v2/auth/refreshToken?accessToken={token}&refreshToken={refresh_token}&powerCode=219904
```

---

## 📋 模板管理API

### 获取申请单模板列表
```bash
GET https://app.ekuaibao.com/api/openapi/v1/specifications/latestByType?accessToken={token}&type=requisition
```

**响应示例**：
```json
{
    "items": [
        {
            "id": "GQgbu2n6osbI00",
            "corporationId": "3Qobu2l0cs6k00",
            "name": "通用申请单",
            "state": "PUBLISHED",
            "flowType": "requisition"
        }
    ]
}
```

### 获取模板详情（含小版本号）
```bash
GET https://app.ekuaibao.com/api/openapi/v2/specifications/byIds/[GQgbu2n6osbI00]?accessToken={token}
```

**响应示例**：
```json
{
    "items": [
        {
            "id": "GQgbu2n6osbI00:ebd338960d9053892b3fd86dfa6f31690d014de7",
            "corporationId": "3Qobu2l0cs6k00", 
            "name": "通用申请单",
            "state": "PUBLISHED",
            "form": [
                {
                    "title": {
                        "label": "标题",
                        "type": "text",
                        "optional": false,
                        "maxLength": 14,
                        "minLength": 0
                    }
                },
                {
                    "requisitionMoney": {
                        "label": "申请金额",
                        "type": "money",
                        "optional": false
                    }
                },
                {
                    "u_项目1": {
                        "label": "项目名称", 
                        "type": "text",
                        "optional": true
                    }
                },
                {
                    "description": {
                        "label": "描述",
                        "type": "text",
                        "optional": true,
                        "maxLength": 140,
                        "minLength": 0
                    }
                }
            ],
            "flowType": "requisition"
        }
    ]
}
```

---

## 🏗️ 申请单创建API

### 创建申请单
```bash
POST https://app.ekuaibao.com/api/openapi/v2.2/flow/data?accessToken={token}&isCommit=false&isUpdate=false

Content-Type: application/json
```

**请求体结构**：
```json
{
    "form": {
        "specificationId": "GQgbu2n6osbI00:ebd338960d9053892b3fd86dfa6f31690d014de7",
        "submitterId": "D01IBfgTxKWAL:S6g73MppKM3A00",
        "title": "出差费用",
        "requisitionMoney": {
            "standard": "1000.00",
            "standardUnit": "元",
            "standardScale": 2,
            "standardSymbol": "¥",
            "standardNumCode": "156",
            "standardStrCode": "CNY"
        },
        "u_项目1": "北京会议",
        "description": "2024年出差费用申请"
    }
}
```

**成功响应**：
```json
{
    "value": "",
    "type": -1,
    "flow": {
        "id": "ID_3tMDtL05ClM",
        "form": {
            "code": "S25000089",
            "title": "出差费用",
            "requisitionMoney": {
                "standard": "1000.00",
                "standardUnit": "元"
            },
            "u_项目1": "北京会议",
            "description": "2024年出差费用申请",
            "submitterId": "D01IBfgTxKWAL:S6g73MppKM3A00",
            "specificationId": "GQgbu2n6osbI00:ebd338960d9053892b3fd86dfa6f31690d014de7"
        },
        "state": "draft",
        "flowType": "freeflow",
        "formType": "requisition"
    }
}
```

---

## 🔍 申请单查询API

### 根据单据ID查询详情
```bash
GET https://app.ekuaibao.com/api/openapi/v1.1/flowDetails?flowId=ID_3tMDtL05ClM&accessToken={token}
```

**响应示例**：
```json
{
    "value": {
        "id": "ID_3tMDtL05ClM",
        "form": {
            "code": "S25000089",
            "title": "出差费用",
            "requisitionMoney": {
                "standard": "1000.00",
                "standardUnit": "元"
            },
            "u_项目1": "北京会议",
            "description": "2024年出差费用申请",
            "submitterId": "D01IBfgTxKWAL:S6g73MppKM3A00",
            "submitDate": 1639392015024
        },
        "state": "draft",
        "flowType": "freeflow", 
        "formType": "requisition",
        "createTime": 1639392015626,
        "updateTime": 1639392015626
    }
}
```

---

## 🤖 DeepSeek API集成

### API配置
```python
DEEPSEEK_CONFIG = {
    "api_key": "sk-43816199a7fd42f88e93b14358954b88",
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-chat",
    "max_tokens": 2000,
    "temperature": 0.1
}
```

### 调用示例
```python
import httpx
import json

async def call_deepseek_api(messages: list) -> str:
    """调用DeepSeek API"""
    
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "max_tokens": 2000,
        "temperature": 0.1,
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_template_fields",
                    "description": "获取申请单模板字段清单"
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "create_smart_expense",
                    "description": "创建申请单",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_input": {
                                "type": "string",
                                "description": "用户输入的申请单信息"
                            }
                        },
                        "required": ["user_input"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_document_by_code", 
                    "description": "查询申请单详情",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "申请单编号"
                            }
                        },
                        "required": ["code"]
                    }
                }
            }
        ]
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        # 检查是否有工具调用
        if result.get("choices") and result["choices"][0].get("message", {}).get("tool_calls"):
            return result["choices"][0]["message"]
        else:
            return result["choices"][0]["message"]["content"]
```

---

## 🔧 Python实现示例

### 认证服务实现
```python
import httpx
import json
import time
from typing import Optional

class AuthService:
    """易快报认证服务"""
    
    def __init__(self):
        self.app_key = "b433ffa4-ff6e-4e76-95e6-1a7bed8777eb"
        self.app_security = "60ec2aa6-6354-40b5-a742-0e1034962b2f"
        self.base_url = "https://app.ekuaibao.com/api/openapi"
        self.cache_file = ".token_cache.json"
        self._token_cache = None
    
    async def get_access_token(self) -> str:
        """获取访问令牌（带缓存）"""
        
        # 检查缓存
        if self._is_token_valid():
            return self._token_cache["accessToken"]
        
        # 尝试刷新令牌
        if self._token_cache and self._token_cache.get("refreshToken"):
            if await self._refresh_token():
                return self._token_cache["accessToken"]
        
        # 重新获取令牌
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
        
        return current_time < (expire_time - 300)  # 提前5分钟
    
    async def _get_new_token(self) -> str:
        """获取新的访问令牌"""
        
        url = f"{self.base_url}/v1/auth/getAccessToken"
        payload = {
            "appKey": self.app_key,
            "appSecurity": self.app_security
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
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
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, params=params)
                response.raise_for_status()
                
                result = response.json()
                self._token_cache = result["value"]
                self._save_token_cache()
                
                return True
                
        except Exception as e:
            print(f"刷新令牌失败: {e}")
            return False
    
    def _load_token_cache(self):
        """加载令牌缓存"""
        try:
            with open(self.cache_file, 'r') as f:
                self._token_cache = json.load(f)
        except FileNotFoundError:
            self._token_cache = None
    
    def _save_token_cache(self):
        """保存令牌缓存"""
        with open(self.cache_file, 'w') as f:
            json.dump(self._token_cache, f)
```

### 易快报API调用服务
```python
class EkuaibaoAPIService:
    """易快报API调用服务"""
    
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self.base_url = "https://app.ekuaibao.com/api/openapi"
    
    async def get_requisition_templates(self) -> list:
        """获取申请单模板列表"""
        
        url = f"{self.base_url}/v1/specifications/latestByType"
        params = {
            "accessToken": await self.auth_service.get_access_token(),
            "type": "requisition"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            return response.json().get("items", [])
    
    async def get_template_detail(self, template_id: str) -> dict:
        """获取模板详情"""
        
        url = f"{self.base_url}/v2/specifications/byIds/[{template_id}]"
        params = {
            "accessToken": await self.auth_service.get_access_token()
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            items = response.json().get("items", [])
            return items[0] if items else {}
    
    async def create_requisition(self, request_body: dict) -> dict:
        """创建申请单"""
        
        url = f"{self.base_url}/v2.2/flow/data"
        params = {
            "accessToken": await self.auth_service.get_access_token(),
            "isCommit": "false",
            "isUpdate": "false"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, params=params, json=request_body)
            response.raise_for_status()
            
            return response.json()
    
    async def get_flow_detail(self, flow_id: str) -> dict:
        """获取申请单详情"""
        
        url = f"{self.base_url}/v1.1/flowDetails"
        params = {
            "accessToken": await self.auth_service.get_access_token(),
            "flowId": flow_id
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
```

---

## 🛡️ 错误处理

### 常见错误码
| 状态码 | 错误类型 | 处理方式 |
|--------|----------|----------|
| 400 | 请求参数错误 | 检查请求体格式和必填字段 |
| 401 | 认证失败 | 重新获取accessToken |
| 403 | 权限不足 | 检查功能授权 |
| 404 | 资源不存在 | 确认模板ID或单据ID是否正确 |
| 500 | 服务器错误 | 重试或联系技术支持 |

### 错误处理实现
```python
import httpx
from typing import Dict, Any

async def safe_api_call(
    method: str, 
    url: str, 
    **kwargs
) -> Dict[str, Any]:
    """安全的API调用，包含错误处理"""
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(method, url, **kwargs)
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                elif response.status_code == 401:
                    # 认证失败，可能需要刷新token
                    return {"success": False, "error": "认证失败，请重新获取token"}
                elif response.status_code == 400:
                    # 请求参数错误
                    error_detail = response.text
                    return {"success": False, "error": f"请求参数错误: {error_detail}"}
                else:
                    response.raise_for_status()
                    
        except httpx.TimeoutException:
            retry_count += 1
            if retry_count >= max_retries:
                return {"success": False, "error": "请求超时"}
        except httpx.HTTPStatusError as e:
            return {"success": False, "error": f"HTTP错误: {e.response.status_code}"}
        except Exception as e:
            return {"success": False, "error": f"未知错误: {str(e)}"}
    
    return {"success": False, "error": "重试次数超限"}
```

---

## 📊 API调用监控

### 性能指标
- **响应时间**: 各API端点的平均响应时间
- **成功率**: API调用成功率统计
- **错误分布**: 各类错误的发生频率

### 日志记录
```python
import logging
import time
from functools import wraps

def api_call_logger(func):
    """API调用日志装饰器"""
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            logging.info(f"API调用成功: {func.__name__}, 耗时: {duration:.2f}s")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logging.error(f"API调用失败: {func.__name__}, 耗时: {duration:.2f}s, 错误: {e}")
            raise
    
    return wrapper
```

---

*文档更新时间：2024年1月*
*版本：v1.0*

