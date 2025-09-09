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
        # 注意：不使用任何缓存，每次都实时拉取最新数据
        
        # 不再使用硬编码的特殊字段列表，改为动态判断字段类型
    
    def _translate_field_type(self, api_type: str) -> str:
        """将API返回的字段类型翻译为中文显示"""
        type_mapping = {
            "text": "文本",
            "money": "金额", 
            "date": "日期",
            "select": "选择",
            "number": "数字",
            "checkbox": "复选框",
            "textarea": "长文本"
        }
        return type_mapping.get(api_type, "文本")
    
    async def get_template_fields(self, template_type: str = "requisition") -> Dict[str, Any]:
        """获取申请单模板字段信息（每次都重新拉取最新模板）"""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"🚨 [{current_time}] 开始获取申请单模板字段 - 强制实时拉取最新版本（不使用任何缓存）")
            
            # 1. 获取所有申请单模板列表（使用最新版本API）
            logger.info("🔄 强制刷新TOKEN以获取最新模板数据")
            # 强制刷新TOKEN，确保获取最新数据
            await self.auth_service._refresh_token()
            
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
                templates_count = len(templates_result.get('items', []))
                logger.info(f"📋 获取到模板列表: {templates_count} 个模板")
                
                # 打印所有模板的名称和ID，便于调试
                for i, template in enumerate(templates_result.get('items', [])):
                    logger.info(f"   模板{i+1}: {template.get('name')} (ID: {template.get('id')}, 激活: {template.get('active')})")
                
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
                logger.info("🔄 再次强制刷新TOKEN以获取模板详情")
                await self.auth_service._refresh_token()
                
                detail_url = f"{self.base_url}/v2/specifications/byIds/editable/[{template_id}]"
                detail_params = {
                    "accessToken": await self.auth_service.get_access_token()
                }
                
                logger.info(f"调用模板详情API: {detail_url}")
                
                detail_response = await client.get(detail_url, params=detail_params)
                detail_response.raise_for_status()
                
                detail_result = detail_response.json()
                template_detail = detail_result.get("items", [{}])[0]
                # 更新为包含版本的完整模板ID
                full_template_id = template_detail.get("id", template_id)
                
                # 4. 解析字段信息
                fields_info = []
                form_fields = template_detail.get("form", [])
                
                # 从模板详情中解析字段（form现在是字典数组）
                available_fields = []
                for field_item in form_fields:
                    logger.info(f"处理字段项: {field_item}, 类型: {type(field_item)}")
                    if isinstance(field_item, dict):
                        # 提取字段名（字典的key）
                        for field_name, field_config in field_item.items():
                            available_fields.append(field_name)
                            logger.info(f"解析到字段: {field_name}, 配置: {field_config}")
                
                logger.info(f"📊 可用字段列表: {available_fields}")
                logger.info(f"📊 字段总数: {len(available_fields)}")
                
                # 记录模板的完整信息用于变化检测
                template_signature = f"{target_template.get('name')}:{len(available_fields)}:{sorted(available_fields)}"
                template_hash = hash(template_signature)
                logger.info(f"🔍 模板签名: {template_signature}")
                logger.info(f"🔍 模板哈希值: {template_hash} (用于检测模板变化)")
                
                # 动态构建字段信息（基于API返回的实际字段配置）
                fields_info = []
                
                # 遍历所有从API获取的字段，动态构建字段信息
                for field_name in available_fields:
                    # 从API响应中查找对应字段的详细配置
                    field_config = None
                    for form_field in form_fields:
                        if isinstance(form_field, dict) and field_name in form_field:
                            field_config = form_field[field_name]
                            break
                    
                    if field_config:
                        # 根据API返回的配置动态生成字段信息
                        field_info = {
                            "name": field_name,
                            "label": field_config.get("label", field_name),
                            "type": self._translate_field_type(field_config.get("type", "text")),
                            "required": not field_config.get("optional", False)
                        }
                        fields_info.append(field_info)
                        logger.info(f"动态添加字段: {field_name} -> {field_info}")
                    else:
                        # 如果找不到配置，使用默认值
                        field_info = {
                            "name": field_name,
                            "label": field_name,
                            "type": "文本",
                            "required": True
                        }
                        fields_info.append(field_info)
                        logger.warning(f"使用默认配置的字段: {field_name}")
                
                logger.info(f"解析出 {len(fields_info)} 个字段")
                
                # 5. 格式化返回信息
                fields_display = "\n".join([
                    f"• **{field['label']}** - {field['type']}" + 
                    (" [必填]" if field['required'] else " [可选]")
                    for field in fields_info
                ])
                
                response_message = f"""
📋 **申请单模板字段信息**

**模板名称**: {target_template.get('name')}
**字段总数**: {len(fields_info)} 个

**字段列表**:
{fields_display}

✅ 请提供以上字段的信息来创建申请单
"""
                
                return {
                    "success": True,
                    "message": response_message,
                    "data": {
                        "template_id": full_template_id,  # 使用包含版本的完整模板ID
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
            
            # 1. 每次都重新获取最新的模板信息（不使用缓存）
            logger.info("重新拉取最新的申请单模板信息")
            template_result = await self.get_template_fields(template_type)
            if not template_result["success"]:
                return template_result
            
            template_data = template_result["data"]
            template_id = template_data["template_id"]
            fields_info = template_data["fields"]
            
            logger.info(f"使用模板ID: {template_id}")
            
            # 2. 使用AI解析用户输入，提取字段信息
            field_mapping = await self._ai_extract_fields(user_input, fields_info)
            
            # 2.5. 添加固定的提交人ID
            field_mapping["submitterId"] = "ID01IBfgTxKWAL:S6g73MppKM3A00"
            
            # 3. 验证必填字段
            validation_result = self._validate_required_fields(field_mapping, fields_info)
            if not validation_result[0]:
                return {
                    "success": False,
                    "message": f"❌ {validation_result[1]}"
                }
            
            # 4. 构建API请求体
            request_body = self._build_request_body(field_mapping, template_id, fields_info)
            
            # 5. 调用创建API
            create_url = f"{self.base_url}/v2.2/flow/data"
            params = {
                "accessToken": await self.auth_service.get_access_token()
            }
            
            logger.info(f"调用创建申请单API: {create_url}")
            logger.info(f"请求体: {json.dumps(request_body, ensure_ascii=False, indent=2)}")
            logger.info(f"字段映射: {json.dumps(field_mapping, ensure_ascii=False, indent=2)}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(create_url, params=params, json=request_body)
                
                # 如果是400错误，记录详细的错误信息
                if response.status_code == 400:
                    error_detail = response.text
                    logger.error(f"400错误详情: {error_detail}")
                    return {
                        "success": False,
                        "message": f"❌ 创建申请单失败 (400错误): {error_detail}"
                    }
                
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
你是一个智能申请单助手。用户想要创建申请单，你需要从他们的自然语言输入中提取字段信息。

用户输入: {user_input}

可用字段列表:
{fields_desc}

请你发挥强大的自然语言理解能力：
1. 理解用户的真实意图（创建、提交、写一个申请单等都是同一个意思）
2. 智能匹配用户描述的内容到对应字段
3. 用户可能用各种表达方式，你要灵活理解
4. 即使用户没有明确提到某个字段，也要生成合理的默认值

字段格式要求：
- 金额类型: {{"standard": "数字.00", "standardUnit": "元", "standardScale": 2, "standardSymbol": "¥", "standardNumCode": "156", "standardStrCode": "CNY"}}
- 日期类型: 时间戳毫秒数，智能理解各种日期表达：
  * "今天" → {int(time.time() * 1000)}
  * "明天" → {int((time.time() + 86400) * 1000)}
  * "下周一" → 计算对应的时间戳
  * "2024-01-15" → 转换为时间戳
  * "1月15日" → 转换为2024年对应日期的时间戳
  * "下个月5号" → 计算下个月5号的时间戳
  * 如果没有明确日期，默认使用当前时间
- 其他类型: 直接使用合适的值

日期智能理解示例：
- 用户说"明天开始"、"下周申请"、"月底截止" → 计算对应的具体时间戳
- 用户说"2024年1月15日"、"1/15"、"01-15" → 转换为标准时间戳
- 相对时间："3天后"、"下周二"、"下个月" → 基于当前时间计算

请直接返回JSON格式的完整字段映射，包含所有字段：
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
            "requisitionDate": int(time.time() * 1000)
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
    
    
    def _build_request_body(self, field_mapping: Dict[str, Any], template_id: str, fields_info: List[Dict]) -> Dict[str, Any]:
        """构建API请求体 - 完全动态处理所有字段"""
        request_body = {
            "form": {
                "specificationId": template_id,
                "submitterId": "ID01IBfgTxKWAL:S6g73MppKM3A00"  # 固定的提交人ID
            }
        }
        
        # 确保submitterId在字段映射中
        field_mapping["submitterId"] = "ID01IBfgTxKWAL:S6g73MppKM3A00"
        
        # 动态处理所有字段，根据字段类型进行相应处理
        for field_name, field_value in field_mapping.items():
            processed_value = self._process_field_by_type(field_name, field_value, fields_info)
            request_body["form"][field_name] = processed_value
        
        return request_body
    
    def _process_field_by_type(self, field_name: str, field_value: Any, fields_info: List[Dict]) -> Any:
        """根据字段类型动态处理字段值"""
        # 查找字段配置
        field_config = None
        for field in fields_info:
            if field['name'] == field_name:
                field_config = field
                break
        
        # 如果没有找到字段配置，直接返回原值
        if not field_config:
            return field_value
            
        field_type = field_config.get('type', '文本')
        
        # 根据字段类型动态处理
        if field_type == '金额':
            # 金额字段保持原格式（AI已经处理为正确格式）
            return field_value
        elif field_type == '日期':
            # 日期字段智能处理
            return self._process_date_field(field_value)
        else:
            # 文本、选择等字段直接返回
            return field_value
    
    def _process_date_field(self, date_value: Any) -> int:
        """智能处理日期字段，支持多种格式"""
        import datetime
        import re
        
        # 如果已经是时间戳，直接返回
        if isinstance(date_value, (int, float)):
            # 确保是毫秒级时间戳
            if date_value < 10000000000:  # 小于这个数说明是秒级
                return int(date_value * 1000)
            return int(date_value)
        
        # 如果是字符串，尝试解析
        if isinstance(date_value, str):
            try:
                # 移除常见的中文描述词
                date_str = date_value.replace('日期', '').replace('时间', '').strip()
                
                # 常见日期格式匹配
                patterns = [
                    (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d'),
                    (r'(\d{4})/(\d{1,2})/(\d{1,2})', '%Y/%m/%d'),
                    (r'(\d{1,2})-(\d{1,2})', f'{datetime.datetime.now().year}-%m-%d'),
                    (r'(\d{1,2})/(\d{1,2})', f'{datetime.datetime.now().year}/%m/%d'),
                    (r'(\d{1,2})月(\d{1,2})日', f'{datetime.datetime.now().year}-%m-%d'),
                ]
                
                for pattern, fmt in patterns:
                    match = re.search(pattern, date_str)
                    if match:
                        if '月' in pattern:
                            # 处理中文日期格式
                            month, day = match.groups()
                            date_obj = datetime.datetime(datetime.datetime.now().year, int(month), int(day))
                        else:
                            # 处理标准格式
                            if len(match.groups()) == 2:  # 只有月日
                                month, day = match.groups()
                                date_obj = datetime.datetime(datetime.datetime.now().year, int(month), int(day))
                            else:  # 有年月日
                                year, month, day = match.groups()
                                date_obj = datetime.datetime(int(year), int(month), int(day))
                        
                        return int(date_obj.timestamp() * 1000)
                        
            except Exception as e:
                logger.warning(f"日期解析失败: {date_value}, 错误: {e}")
        
        # 如果都无法解析，返回当前时间
        logger.info(f"使用当前时间作为日期字段默认值: {date_value}")
        return int(time.time() * 1000)

    async def get_document_by_code(self, document_code: str) -> Dict[str, Any]:
        """根据单据编号查询申请单详情 - 简化版本"""
        return {
            "success": True,
            "message": "单据查询功能需要完整实现",
            "data": {}
        }
