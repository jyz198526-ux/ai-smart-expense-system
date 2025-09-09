#!/usr/bin/env python3
"""
测试通用单据查询API
"""

import asyncio
import sys
import os
import httpx
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.auth_service import AuthService
from config import EK_BASE_URL

async def test_general_docs_api():
    """测试通用单据查询"""
    
    auth_service = AuthService()
    token = await auth_service.get_access_token()
    base_url = EK_BASE_URL
    
    print(f"🔍 测试通用单据查询API...")
    
    # 尝试不同的查询方式
    test_cases = [
        # 通用单据查询
        "/v1/docs?start=0&count=10",
        "/v1/docs?start=0&count=10&type=requisition",
        "/v1/docs?start=0&count=10&formType=requisition",
        
        # 流程查询
        "/v1/flows?start=0&count=10",
        "/v1/flows?start=0&count=10&type=requisition",
        
        # 可能的历史查询
        "/v1/docs/history?start=0&count=10",
        "/v1/flows/history?start=0&count=10",
        
        # 按状态查询
        "/v1/docs?start=0&count=10&state=approved",
        "/v1/flows?start=0&count=10&state=approved",
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for endpoint in test_cases:
            try:
                url = f"{base_url}{endpoint}&accessToken={token}"
                
                print(f"\n🌐 测试: {endpoint}")
                response = await client.get(url)
                print(f"   状态码: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"   ✅ 成功!")
                    data = response.json()
                    if isinstance(data, dict):
                        count = data.get('count', 0)
                        items = data.get('items', [])
                        print(f"   记录总数: {count}")
                        print(f"   返回条数: {len(items)}")
                        
                        if items:
                            first_item = items[0]
                            print(f"   第一条记录类型: {first_item.get('formType', 'unknown')}")
                            if 'form' in first_item:
                                form = first_item['form']
                                print(f"   标题: {form.get('title', 'N/A')}")
                                print(f"   提交人: {form.get('submitterId', 'N/A')}")
                    
                elif response.status_code == 404:
                    print(f"   ❌ 端点不存在")
                else:
                    print(f"   ⚠️  状态码: {response.status_code}")
                    
            except Exception as e:
                print(f"   💥 异常: {str(e)[:100]}")

if __name__ == "__main__":
    asyncio.run(test_general_docs_api())



