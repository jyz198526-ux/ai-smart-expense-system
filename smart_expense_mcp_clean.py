#!/usr/bin/env python3
"""
AI智能申请单系统 - MCP核心层（清理版）
处理模板获取、字段映射、申请单创建等核心业务逻辑
"""

import logging
import json
import time
import re
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import httpx
from services.auth_service import AuthService
from services.deepseek_service import DeepSeekService
from config import EK_BASE_URL

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartExpenseMCP:
    """智能申请单MCP核心控制器"""
    
    def __init__(self):
        self.auth_service = AuthService()
        self.deepseek_service = DeepSeekService()
        self.base_url = EK_BASE_URL
        self.template_cache = {}
        
        # 特殊字段列表：需要特殊处理的字段
        self.SPECIAL_FIELDS = {
            "requisitionMoney",  # 金额字段
            "expenseDate",       # 日期字段
            "requisitionDate"    # 申请日期字段
        }
    
    async def get_template_fields(self, template_type: str = "requisition") -> Dict[str, Any]:
        """获取申请单模板字段信息"""
        try:
            logger.info("开始获取申请单模板字段")
            
            # 1. 获取所有申请单模板列表（使用最新版本API）
            templates_url = f"{self.base_url}/v1/specifications/latestByType"
            params = {
                "accessToken": await self.auth_service.get_access_token(),
                "type": "requisition",  # 申请单类型
                "specificationGroupId": ""  # 空字符串表示所有分组
            }
            
            logger.info(f"调用模板列表API: {templates_url}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(templates_url, params=params)
                response.raise_for_status()
                
                templates_result = response.json()
                logger.info(f"获取到模板列表: {len(templates_result.get('items', []))} 个模板")
                
                # 2. 查找激活的申请单模板（优先选择"AI申请单"）
                templates = templates_result.get("items", [])
                target_template = None
                
                # 优先查找"AI申请单"
                for template in templates:
                    if template.get("active") and template.get("name") == "AI申请单":
                        target_template = template
                        logger.info(f"找到AI申请单模板: {template.get('name')} - ID: {template.get('id')}")
                        break
                
                # 如果没有找到AI申请单，选择第一个激活的模板
                if not target_template:
                    for template in templates:
                        if template.get("active"):
                            target_template = template
                            logger.info(f"找到申请单模板: {template.get('name')} - ID: {template.get('id')}")
                            break
                
                if not target_template:
                    return {
                        "success": False,
                        "message": "❌ 未找到申请单模板"
                    }
                
                # 3. 获取模板详细字段信息（包含可编辑字段）
                template_id = target_template["id"]
                detail_url = f"{self.base_url}/v2/specifications/byIds/editable/{template_id}"
                detail_params = {
                    "accessToken": await self.auth_service.get_access_token()
                }
                
                logger.info(f"调用模板详情API: {detail_url}")
                
                detail_response = await client.get(detail_url, params=detail_params)
                detail_response.raise_for_status()
                
                detail_result = detail_response.json()
                template_detail = detail_result.get("value", [{}])[0]
                
                # 4. 解析字段信息
                fields_info = []
                form = template_detail.get("form", {})
                
                # 基础字段
                basic_fields = [
                    {"name": "title", "label": "申请标题", "type": "text", "required": True},
                    {"name": "requisitionMoney", "label": "申请金额", "type": "money", "required": True},
                    {"name": "description", "label": "申请描述", "type": "textarea", "required": False},
                    {"name": "requisitionDate", "label": "申请日期", "type": "date", "required": True}
                ]
                
                fields_info.extend(basic_fields)
                
                # 自定义字段
                for field_name, field_config in form.items():
                    if field_name.startswith("u_"):
                        field_info = {
                            "name": field_name,
                            "label": field_config.get("name", field_name),
                            "type": self._get_field_type(field_config),
                            "required": field_config.get("required", False)
                        }
                        fields_info.append(field_info)
                
                logger.info(f"解析出 {len(fields_info)} 个字段")
                
                # 5. 格式化返回信息
                fields_display = "\n".join([
                    f"• **{field['label']}** ({field['name']}) - {field['type']}" + 
                    (" [必填]" if field['required'] else " [可选]")
                    for field in fields_info
                ])
                
                response_message = f"""
📋 **申请单模板字段信息**

**模板名称**: {target_template.get('name')}
**模板ID**: {template_id}
**字段总数**: {len(fields_info)} 个

**字段列表**:
{fields_display}

✅ 请提供以上字段的信息来创建申请单
"""
                
                return {
                    "success": True,
                    "message": response_message,
                    "data": {
                        "template_id": template_id,
                        "template_name": target_template.get('name'),
                        "fields": fields_info
                    }
                }
                
        except Exception as e:
            logger.error(f"获取模板字段失败: {e}")
            return {
                "success": False,
                "message": f"❌ 获取模板字段失败: {str(e)}"
            }
    
    def _get_field_type(self, field_config: Dict[str, Any]) -> str:
        """根据字段配置推断字段类型"""
        field_type = field_config.get("type", "text")
        
        type_mapping = {
            "text": "文本",
            "number": "数字", 
            "money": "金额",
            "date": "日期",
            "select": "选择",
            "multiSelect": "多选",
            "textarea": "长文本",
            "attachment": "附件",
            "staff": "员工",
            "department": "部门"
        }
        
        return type_mapping.get(field_type, "文本")
    
    async def create_smart_expense(self, user_input: str, template_type: str = "requisition") -> Dict[str, Any]:
        """创建智能申请单"""
        try:
            logger.info(f"开始创建申请单，用户输入: {user_input}")
            
            # 1. 先获取模板信息
            template_result = await self.get_template_fields(template_type)
            if not template_result["success"]:
                return template_result
            
            template_data = template_result["data"]
            template_id = template_data["template_id"]
            fields_info = template_data["fields"]
            
            logger.info(f"使用模板ID: {template_id}")
            
            # 2. 使用AI解析用户输入，提取字段信息
            field_mapping = await self._ai_extract_fields(user_input, fields_info)
            
            # 3. 验证必填字段
            validation_result = self._validate_required_fields(field_mapping, fields_info)
            if not validation_result[0]:
                return {
                    "success": False,
                    "message": f"❌ {validation_result[1]}"
                }
            
            # 4. 构建API请求体
            request_body = self._build_request_body(field_mapping, template_id)
            
            # 5. 调用创建API
            create_url = f"{self.base_url}/v2.2/flow/data"
            params = {
                "accessToken": await self.auth_service.get_access_token()
            }
            
            logger.info(f"调用创建申请单API: {create_url}")
            logger.info(f"请求体: {json.dumps(request_body, ensure_ascii=False, indent=2)}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(create_url, params=params, json=request_body)
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"创建申请单成功: {result}")
                
                # 6. 解析返回结果
                flow_data = result.get("flow", {})
                form_data = flow_data.get("form", {})
                
                document_code = form_data.get("code", "未知")
                document_title = form_data.get("title", "未知")
                
                success_message = f"""
🎉 **申请单创建成功！**

**单据编号**: {document_code}
**单据标题**: {document_title}
**申请金额**: {field_mapping.get('requisitionMoney', {}).get('standard', 'N/A')}元
**创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**当前状态**: 草稿

✅ 申请单已成功创建，您可以登录易快报系统查看详情
"""
                
                return {
                    "success": True,
                    "message": success_message,
                    "data": {
                        "document_code": document_code,
                        "document_title": document_title,
                        "flow_id": flow_data.get("id"),
                        "form_data": form_data
                    }
                }
                
        except Exception as e:
            logger.error(f"创建申请单失败: {e}")
            return {
                "success": False,
                "message": f"❌ 创建申请单失败: {str(e)}"
            }
    
    async def _ai_extract_fields(self, user_input: str, fields_info: List[Dict]) -> Dict[str, Any]:
        """使用AI从用户输入中提取字段信息"""
        try:
            # 构建AI提示词
            fields_desc = "\n".join([
                f"- {field['name']}: {field['label']} ({field['type']})" + 
                (" [必填]" if field['required'] else "")
                for field in fields_info
            ])
            
            ai_prompt = f"""
根据用户输入提取申请单字段信息，返回JSON格式：

用户输入: {user_input}

可用字段:
{fields_desc}

请提取以下信息并返回JSON：
{{
    "title": "从用户输入中提取的标题",
    "requisitionMoney": {{
        "standard": "金额数字字符串，如 '1000.00'",
        "standardUnit": "元",
        "standardScale": 2,
        "standardSymbol": "¥",
        "standardNumCode": "156",
        "standardStrCode": "CNY"
    }},
    "description": "申请描述或事由",
    "requisitionDate": {int(time.time() * 1000)},
    "u_项目1": "项目信息（如果有）",
    "其他自定义字段": "对应值"
}}

规则：
1. 如果用户未提供某字段，生成合理默认值
2. 金额必须是标准格式
3. 日期使用时间戳（毫秒）
4. 标题不超过14个字符
"""
            
            # 调用DeepSeek API
            response = await self.deepseek_service.simple_chat(ai_prompt)
            
            # 解析JSON响应
            try:
                field_mapping = json.loads(response)
                logger.info(f"AI提取的字段映射: {field_mapping}")
                return field_mapping
            except json.JSONDecodeError:
                # 如果AI返回的不是纯JSON，尝试提取JSON部分
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    field_mapping = json.loads(json_match.group())
                    logger.info(f"从AI响应中提取的字段映射: {field_mapping}")
                    return field_mapping
                else:
                    raise ValueError("AI响应不包含有效JSON")
                    
        except Exception as e:
            logger.error(f"AI字段提取失败: {e}")
            # 返回基础的字段映射
            return self._fallback_field_extraction(user_input)
    
    def _fallback_field_extraction(self, user_input: str) -> Dict[str, Any]:
        """备用字段提取方法"""
        logger.info("使用备用字段提取方法")
        
        # 提取标题
        title = "AI申请单"
        title_patterns = [
            r'标题[是为：:]\s*([^，,。\n]+)',
            r'申请\s*([^，,。\n]+)',
            r'([^，,。\n]*申请[^，,。\n]*)',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, user_input)
            if match:
                title = match.group(1).strip()[:14]  # 限制14字符
                break
        
        # 提取金额
        amount = "1000.00"
        amount_patterns = [
            r'金额[是为：:]\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*元',
            r'￥\s*(\d+\.?\d*)',
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, user_input)
            if match:
                amount = f"{float(match.group(1)):.2f}"
                break
        
        return {
            "title": title,
            "requisitionMoney": {
                "standard": amount,
                "standardUnit": "元",
                "standardScale": 2,
                "standardSymbol": "¥",
                "standardNumCode": "156",
                "standardStrCode": "CNY"
            },
            "description": user_input[:100],  # 截取前100字符作为描述
            "requisitionDate": int(time.time() * 1000),
            "u_项目1": "重要业务项目"
        }
    
    def _validate_required_fields(self, field_mapping: Dict[str, Any], fields_info: List[Dict]) -> tuple[bool, str]:
        """验证必填字段"""
        for field in fields_info:
            if field['required'] and field['name'] not in field_mapping:
                return False, f"缺少必填字段：{field['label']}"
        
        # 验证标题长度
        title = field_mapping.get("title", "")
        if len(title) > 14:
            return False, "标题长度超过14个字符"
        
        return True, "验证通过"
    
    def _build_request_body(self, field_mapping: Dict[str, Any], template_id: str) -> Dict[str, Any]:
        """构建API请求体"""
        request_body = {
            "form": {
                "specificationId": template_id,
                "submitterId": "ID01IBfgTxKWAL:S6g73MppKM3A00"  # 固定的提交人ID
            }
        }
        
        # 添加所有字段到form中
        for field_name, field_value in field_mapping.items():
            if field_name in self.SPECIAL_FIELDS:
                # 特殊字段处理
                processed_value = self._process_special_field(field_name, field_value)
                request_body["form"][field_name] = processed_value
            else:
                # 普通字段直接添加
                request_body["form"][field_name] = field_value
        
        return request_body
    
    def _process_special_field(self, field_name: str, field_value: Any) -> Any:
        """处理特殊字段"""
        if field_name == "requisitionMoney":
            # 金额字段已经是正确格式
            return field_value
        elif field_name == "requisitionDate":
            # 日期字段转换为时间戳
            if isinstance(field_value, (int, float)):
                return int(field_value)
            else:
                return int(time.time() * 1000)
        else:
            return field_value
    
    async def get_document_by_code(self, document_code: str) -> Dict[str, Any]:
        """根据单据编号查询申请单详情 - 简化版本"""
        return {
            "success": True,
            "message": "单据查询功能需要完整实现",
            "data": {}
        }
