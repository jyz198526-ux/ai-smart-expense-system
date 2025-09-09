"""
FastAPI主服务
处理聊天接口和工具调用路由
"""
import json
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn

from services.auth_service import AuthService
from services.deepseek_service import DeepSeekService
from smart_expense_mcp import SmartExpenseMCP
from config import SERVER_HOST, SERVER_PORT

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="AI智能申请单系统",
    description="基于DeepSeek AI的智能申请单创建系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化服务
auth_service = AuthService()
deepseek_service = DeepSeekService()
mcp_service = SmartExpenseMCP()

# 请求模型
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []

class ChatResponse(BaseModel):
    message: str
    type: str = "text"  # text, success, error, template_fields
    data: Optional[Dict[str, Any]] = None

# 对话状态管理
conversation_states = {}

@app.get("/")
async def serve_frontend():
    """提供前端页面"""
    return FileResponse("templates/index.html")

@app.get("/version")
async def get_version():
    """获取系统版本信息"""
    try:
        # 获取当前系统版本
        version_info = {
            "system_version": "1.0.0",
            "build_date": "2025-01-09",
            "components": {
                "fastapi": "0.104.1",
                "deepseek_api": "chat-completions",
                "ekuaibao_api": "v1.1/v2.2"
            },
            "features": [
                "TOKEN刷新机制",
                "动态模板字段获取", 
                "AI智能申请单创建",
                "历史单据查询"
            ]
        }
        
        # 获取易快报API版本信息
        try:
            token = await auth_service.get_access_token()
            # 可以通过调用易快报API获取版本信息
            version_info["ekuaibao_status"] = "connected"
            version_info["token_status"] = "active"
        except Exception as e:
            version_info["ekuaibao_status"] = "error"
            version_info["token_status"] = "inactive"
            logger.warning(f"获取易快报版本信息失败: {e}")
        
        return version_info
        
    except Exception as e:
        logger.error(f"获取版本信息失败: {e}")
        return {
            "error": f"获取版本信息失败: {str(e)}"
        }

@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 测试认证服务
        auth_status = await auth_service.test_connection()
        
        # 测试AI服务
        ai_status = await deepseek_service.test_connection()
        
        return {
            "status": "healthy",
            "services": {
                "auth_service": "ok" if auth_status else "error",
                "deepseek_service": "ok" if ai_status else "error"
            }
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """聊天接口"""
    
    try:
        user_message = request.message.strip()
        
        if not user_message:
            raise HTTPException(status_code=400, detail="消息不能为空")
        
        logger.info(f"收到用户消息: {user_message}")
        
        # 构建对话历史
        messages = []
        for msg in request.history:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": user_message})
        
        # 获取MCP工具定义
        tools = deepseek_service.get_mcp_tools()
        
        # 调用AI进行对话
        ai_result = await deepseek_service.chat_with_tools(messages, tools)
        
        logger.info(f"AI响应: {ai_result}")
        
        # 解析AI响应
        if ai_result.get("choices"):
            ai_message = ai_result["choices"][0]["message"]
            
            logger.info(f"AI消息: {ai_message}")
            
            # 检查是否有工具调用
            if ai_message.get("tool_calls"):
                # AI要求调用工具
                tool_call = ai_message["tool_calls"][0]
                tool_name = tool_call["function"]["name"]
                tool_args = json.loads(tool_call["function"]["arguments"])
                
                logger.info(f"AI请求调用工具: {tool_name}, 参数: {tool_args}")
                
                # 调用MCP工具
                if tool_name == "get_template_fields":
                    mcp_result = await mcp_service.get_template_fields()
                    response_message = mcp_result["message"]
                    response_type = "template_fields" if mcp_result["success"] else "error"
                
                elif tool_name == "create_smart_expense":
                    user_input = tool_args.get("user_input", "")
                    mcp_result = await mcp_service.create_smart_expense(user_input)
                    response_message = mcp_result["message"]
                    response_type = "success" if mcp_result["success"] else "error"
                
                elif tool_name == "get_document_by_code":
                    code = tool_args.get("code", "")
                    mcp_result = await mcp_service.get_document_by_code(code)
                    response_message = mcp_result["message"]
                    response_type = "success" if mcp_result["success"] else "error"
                
                else:
                    response_message = f"未知的工具调用: {tool_name}"
                    response_type = "error"
            
            else:
                # AI直接回复
                response_message = ai_message.get("content", "抱歉，我无法理解您的请求。")
                response_type = "text"
        
        else:
            response_message = "抱歉，AI服务暂时无法响应。"
            response_type = "error"
        
        return ChatResponse(
            message=response_message,
            type=response_type
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"聊天处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")

@app.post("/api/test-auth")
async def test_auth():
    """测试认证服务"""
    try:
        token = await auth_service.get_access_token()
        return {
            "success": True,
            "message": "认证成功",
            "token_preview": token[:20] + "..." if len(token) > 20 else token
        }
    except Exception as e:
        logger.error(f"认证测试失败: {e}")
        raise HTTPException(status_code=500, detail=f"认证失败: {str(e)}")

if __name__ == "__main__":
    logger.info(f"启动服务器: {SERVER_HOST}:{SERVER_PORT}")
    uvicorn.run(
        "main:app", 
        host=SERVER_HOST, 
        port=SERVER_PORT, 
        reload=True,
        log_level="info"
    )
