"""
DeepSeek AI服务
处理AI对话和工具调用
"""
import httpx
import json
import logging
from typing import List, Dict, Any, Optional
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL

logger = logging.getLogger(__name__)

class DeepSeekService:
    """DeepSeek AI服务"""
    
    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY
        self.api_url = DEEPSEEK_API_URL
        self.model = "deepseek-chat"
        
        # 强化自然语言理解的系统提示词
        self.system_prompt = """
你是一个智能申请单助手。用户会用各种自然语言表达来与你交流，你需要理解他们的真实意图并调用对应工具。

用户意图识别规则：
1. 查询模板字段信息：
   - "查看字段"、"有哪些字段"、"模板信息"、"申请表结构" 
   → 调用 get_template_fields()

2. 创建/提交申请单（用户的各种表达方式）：
   - "创建申请单"、"提交申请"、"写一个申请"、"帮我申请"
   - "我要申请..."、"申请一下..."、"需要申请..."
   - "报销..."、"出差..."、"培训费用..."、"购买..."
   - 包含金额、费用、具体项目内容的描述
   → 调用 create_smart_expense()

3. 查询已有单据：
   - "查询单据" + 编号
   → 调用 get_document_by_code()

核心理念：理解用户真实意图，不拘泥于具体用词。
- "创建"、"提交"、"写一个"、"帮我做"都是同一个意思
- 用户说话可能很随意，要智能理解背后的需求
- 即使用词不标准，也要准确识别意图

你必须调用工具，不能直接回复文字！
"""
    
    async def chat_with_tools(self, messages: List[Dict[str, str]], tools: List[Dict] = None) -> Dict[str, Any]:
        """与AI对话（支持工具调用）"""
        
        # 添加系统提示词
        system_message = {"role": "system", "content": self.system_prompt}
        full_messages = [system_message] + messages
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": full_messages,
            "max_tokens": 2000,
            "temperature": 0.0,  # 降低随机性，提高工具调用一致性
        }
        
        # 如果提供了工具，添加到请求中
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "required"  # 强制AI使用工具，不允许纯文本回复
        
        logger.info(f"调用DeepSeek API，消息数量: {len(full_messages)}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"DeepSeek API响应成功")
            
            return result
    
    async def simple_chat(self, user_message: str) -> str:
        """简单对话（无工具调用）"""
        
        messages = [{"role": "user", "content": user_message}]
        
        try:
            result = await self.chat_with_tools(messages)
            
            if result.get("choices"):
                return result["choices"][0]["message"]["content"]
            else:
                return "抱歉，AI服务暂时无法响应。"
                
        except Exception as e:
            logger.error(f"简单对话失败: {e}")
            return f"AI服务错误: {str(e)}"
    
    def get_mcp_tools(self) -> List[Dict]:
        """获取MCP工具定义"""
        
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_template_fields",
                    "description": "获取AI申请单模板的详细信息，包括所有可填字段及其规则。当用户要创建申请单时必须先调用此工具。",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "create_smart_expense",
                    "description": "创建申请单，根据用户输入的信息智能创建申请单",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_input": {
                                "type": "string",
                                "description": "用户输入的申请单信息，包含标题、金额、项目等"
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
                    "description": "根据申请单编号查询申请单详情",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "申请单编号，如S25000089"
                            }
                        },
                        "required": ["code"]
                    }
                }
            }
        ]
    
    async def test_connection(self) -> bool:
        """测试AI服务连接"""
        try:
            result = await self.simple_chat("你好")
            logger.info(f"DeepSeek服务测试成功: {result[:50]}...")
            return True
        except Exception as e:
            logger.error(f"DeepSeek服务测试失败: {e}")
            return False

            return False
