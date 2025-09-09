#!/usr/bin/env python3
"""
测试员工历史单据查询功能
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from smart_expense_mcp import SmartExpenseMCP

async def test_staff_history():
    """测试员工历史单据查询"""
    
    mcp = SmartExpenseMCP()
    
    print("🔍 测试员工历史单据查询...")
    
    # 1. 测试员工查找
    print("\n1. 测试员工ID查找...")
    staff_id = await mcp._find_staff_by_name("金永志")
    print(f"员工ID: {staff_id}")
    
    if not staff_id:
        print("❌ 员工ID查找失败")
        return
    
    # 2. 测试历史单据查询
    print(f"\n2. 测试历史单据查询 (员工ID: {staff_id})...")
    result = await mcp.get_staff_history_documents("金永志", 5)
    
    print(f"\n📋 查询结果:")
    print(f"成功: {result['success']}")
    print(f"消息: {result['message'][:200]}...")
    
    if result.get('data'):
        data = result['data']
        print(f"总记录数: {data.get('total_count', 0)}")
        print(f"返回记录数: {data.get('returned_count', 0)}")
        print(f"单据类型统计: {data.get('type_statistics', {})}")

if __name__ == "__main__":
    asyncio.run(test_staff_history())



