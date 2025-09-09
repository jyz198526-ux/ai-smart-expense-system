#!/usr/bin/env python3
"""
测试AI和MCP之间的集成问题
"""

import asyncio
import httpx
import json

async def test_ai_mcp_integration():
    """测试AI和MCP集成"""
    print("=" * 60)
    print("测试AI和MCP集成")
    print("=" * 60)
    
    # 测试消息
    test_message = "查看金永志的历史申请记录"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"发送消息: {test_message}")
            
            response = await client.post(
                "http://localhost:8000/api/chat",
                json={
                    "message": test_message,
                    "history": []
                }
            )
            
            print(f"HTTP状态: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"响应类型: {result.get('type', 'unknown')}")
                message = result.get('message', '')
                print(f"消息长度: {len(message)}")
                
                # 分析响应内容
                if "暂无历史申请单据" in message:
                    print("❌ AI返回暂无历史单据 - MCP调用可能失败")
                elif "历史单据查询说明" in message:
                    print("⚠️ AI返回API限制说明 - MCP异常处理被触发")
                elif "<div" in message and "单据" in message:
                    print("✅ AI返回HTML格式历史单据 - 集成正常")
                elif "查询员工" in message and "发生错误" in message:
                    print("❌ AI返回错误信息 - MCP调用异常")
                else:
                    print("❓ AI返回其他内容")
                
                print(f"\n完整响应:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                print(f"错误内容: {response.text}")
                
    except Exception as e:
        print(f"❌ 测试异常: {e}")

if __name__ == "__main__":
    asyncio.run(test_ai_mcp_integration())


