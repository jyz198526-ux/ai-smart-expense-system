# MCP层详细设计文档

## 📋 MCP层核心职责

MCP层充当AI与易快报API之间的"翻译官"，主要职责：

1. **动态获取模板元数据**：从易快报API获取最新模板定义
2. **AI字段映射**：使用DeepSeek AI将用户自然语言映射到模板字段
3. **构建API请求体**：根据AI映射和易快报API要求动态构建JSON请求体
4. **调用易快报API**：发送请求并处理响应
5. **错误处理与恢复**：处理各种异常情况并提供备用方案

---

## 🏗️ 核心架构设计

### 主要组件关系图
```
SmartExpenseMCP (主控制器)
├── TemplateManager (模板管理)
├── AIFieldMapper (AI字段映射)
├── FieldValidator (字段验证)
├── RequestBuilder (请求构建)
├── APIConnector (API连接)
└── ErrorRecovery (错误恢复)
```

### 设计原则
1. **零硬编码字段名**：除特殊字段外，所有字段处理都是动态的
2. **通用处理为主**：大多数字段直接赋值，少数字段特殊处理
3. **自适应扩展**：新增字段无需修改代码，AI自动适应

---

## 🔧 详细处理流程

### 步骤1：获取模板元数据
```python
class TemplateManager:
    """模板管理器"""
    
    def __init__(self):
        self.template_cache = {}
        self.cache_duration = 300  # 5分钟缓存
    
    async def get_template_metadata(self, template_type: str = "requisition") -> dict:
        """获取申请单模板元数据"""
        
        cache_key = f"template_{template_type}"
        
        # 检查缓存
        if self._is_cache_valid(cache_key):
            return self.template_cache[cache_key]
        
        # 1. 获取模板列表
        templates = await self._get_templates_by_type(template_type)
        if not templates:
            raise Exception("未找到申请单模板")
        
        # 2. 获取第一个模板的详细信息（含小版本号）
        template_id = templates[0]["id"]
        template_detail = await self._get_template_detail(template_id)
        
        # 3. 缓存结果
        self.template_cache[cache_key] = {
            "id": template_detail["id"],
            "name": template_detail["name"],
            "form": template_detail["form"],
            "cached_at": time.time()
        }
        
        return self.template_cache[cache_key]
    
    async def _get_templates_by_type(self, template_type: str) -> list:
        """调用易快报API获取模板列表"""
        url = f"{EK_BASE_URL}/v1/specifications/latestByType"
        params = {
            "accessToken": await self.auth_service.get_access_token(),
            "type": template_type
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json().get("items", [])
    
    async def _get_template_detail(self, template_id: str) -> dict:
        """获取模板详细信息（使用小版本号API）"""
        url = f"{EK_BASE_URL}/v2/specifications/byIds/[{template_id}]"
        params = {"accessToken": await self.auth_service.get_access_token()}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            items = response.json().get("items", [])
            return items[0] if items else {}
```

### 步骤2：AI字段映射生成
```python
class AIFieldMapper:
    """AI字段映射器"""
    
    async def generate_field_mapping(self, user_input: str, template_metadata: dict) -> dict:
        """使用AI生成字段映射"""
        
        # 提取字段描述
        field_descriptions = self._extract_field_descriptions(template_metadata)
        
        # 构建AI提示词
        mapping_prompt = self._build_mapping_prompt(user_input, field_descriptions)
        
        # 调用DeepSeek API
        ai_response = await self.deepseek_service.call_api(mapping_prompt)
        
        # 解析AI响应
        try:
            mapping_result = json.loads(ai_response)
            return {"success": True, "mapping": mapping_result}
        except json.JSONDecodeError:
            # AI输出格式错误，尝试修复
            return await self._fallback_mapping(user_input, ai_response)
    
    def _extract_field_descriptions(self, template_metadata: dict) -> dict:
        """从模板元数据中提取字段描述"""
        
        field_descriptions = {}
        
        for field_config in template_metadata["form"]:
            for field_name, field_info in field_config.items():
                field_descriptions[field_name] = {
                    "label": field_info.get("label", field_name),
                    "type": field_info.get("type", "text"),
                    "required": not field_info.get("optional", True),
                    "maxLength": field_info.get("maxLength"),
                    "description": self._generate_field_description(field_info)
                }
        
        return field_descriptions
    
    def _build_mapping_prompt(self, user_input: str, field_descriptions: dict) -> str:
        """构建AI字段映射提示词"""
        
        return f"""
        根据用户输入和模板字段定义，生成精确的字段映射：
        
        用户输入：{user_input}
        
        可用字段：
        {json.dumps(field_descriptions, ensure_ascii=False, indent=2)}
        
        ## 映射规则：
        1. 必须从用户输入中提取信息，分别映射到对应字段
        2. 不要将整个用户输入都放入description字段  
        3. 金额字段使用格式：{{"standard": "数值.00"}}
        4. 只映射模板中存在的字段
        5. 如果某个字段用户未提供，则不包含在输出中
        
        输出纯JSON格式的字段映射：
        """
```

### 步骤3：字段验证与处理
```python
class FieldValidator:
    """字段验证器"""
    
    def __init__(self):
        # 特殊字段配置（基于您的分析）
        self.SPECIAL_FIELDS = {
            "requisitionMoney",
            "expenseDate", 
            "submitDate"
        }
        
        self.ARCHIVE_FIELDS = {
            "u_自定义公司": "department",
            "submitterId": "staff",
            "expenseDepartment": "department"
        }
    
    async def validate_and_process_fields(self, ai_mapping: dict, template_metadata: dict) -> dict:
        """验证并处理AI映射的字段"""
        
        processed_fields = {}
        missing_required = []
        
        # 获取必填字段列表
        required_fields = self._get_required_fields(template_metadata)
        
        # 验证必填字段
        for field_name in required_fields:
            if field_name not in ai_mapping:
                missing_required.append(field_name)
        
        # 处理所有映射字段
        for field_name, field_value in ai_mapping.items():
            try:
                if field_name in self.SPECIAL_FIELDS:
                    # 特殊字段处理
                    processed_value = await self._process_special_field(field_name, field_value)
                elif field_name in self.ARCHIVE_FIELDS:
                    # 档案字段处理（名称→ID转换）
                    processed_value = await self._resolve_archive_field(field_name, field_value)
                else:
                    # 通用字段处理（您强调的主要路径）
                    processed_value = self._process_general_field(field_name, field_value, template_metadata)
                
                processed_fields[field_name] = processed_value
                
            except Exception as e:
                logger.error(f"字段处理失败: {field_name} = {field_value}, 错误: {e}")
                # 容错：字段处理失败时保留原值
                processed_fields[field_name] = field_value
        
        return {
            "success": len(missing_required) == 0,
            "processed_fields": processed_fields,
            "missing_required": missing_required
        }
    
    async def _process_special_field(self, field_name: str, field_value: any) -> any:
        """处理特殊字段"""
        
        if field_name == "requisitionMoney":
            # 构建易快报要求的金额对象
            if isinstance(field_value, dict) and "standard" in field_value:
                amount = field_value["standard"]
            else:
                amount = str(field_value)
            
            return {
                "standard": f"{float(amount):.2f}",
                "standardUnit": "元",
                "standardScale": 2,
                "standardSymbol": "¥",
                "standardNumCode": "156",
                "standardStrCode": "CNY"
            }
        
        elif field_name in ["expenseDate", "submitDate"]:
            # 日期转时间戳
            if isinstance(field_value, str):
                # 如果是日期字符串，转换为时间戳
                return self._parse_date_to_timestamp(field_value)
            elif isinstance(field_value, (int, float)):
                # 如果已经是时间戳，直接返回
                return int(field_value)
        
        return field_value
    
    async def _resolve_archive_field(self, field_name: str, field_value: str) -> str:
        """解析档案字段（名称→ID转换）"""
        
        archive_type = self.ARCHIVE_FIELDS[field_name]
        
        try:
            if archive_type == "department":
                return await self._get_department_id(field_value)
            elif archive_type == "staff":
                return await self._get_staff_id(field_value)
            elif archive_type == "project":
                return await self._get_project_id(field_value)
        except Exception as e:
            logger.warning(f"档案字段解析失败，使用原值: {field_name} = {field_value}, 错误: {e}")
            return field_value
        
        return field_value
```

### 步骤4：动态请求体构建
```python
class RequestBuilder:
    """动态请求体构建器"""
    
    async def build_create_request(self, processed_fields: dict, template_metadata: dict) -> dict:
        """构建创建申请单的请求体"""
        
        # 基础请求体结构
        request_body = {
            "form": {
                "specificationId": template_metadata["id"],
                "submitterId": await self._get_default_submitter_id()
            }
        }
        
        # 添加处理后的字段（您分析的核心逻辑）
        for field_name, field_value in processed_fields.items():
            request_body["form"][field_name] = field_value
        
        # 添加系统默认字段
        await self._add_system_defaults(request_body, template_metadata)
        
        return request_body
    
    async def _add_system_defaults(self, request_body: dict, template_metadata: dict):
        """添加系统默认字段"""
        
        # 如果没有提交日期，使用当前时间
        if "submitDate" not in request_body["form"]:
            request_body["form"]["submitDate"] = int(time.time() * 1000)
        
        # 如果没有申请日期，使用当前时间  
        if "expenseDate" not in request_body["form"]:
            request_body["form"]["expenseDate"] = int(time.time() * 1000)
```

---

## 🛡️ 错误处理与恢复机制

### 错误恢复管理器
```python
class ErrorRecoveryManager:
    """错误恢复管理器"""
    
    def __init__(self):
        self.retry_strategies = {
            "ai_mapping_failed": self._retry_with_simplified_prompt,
            "field_validation_failed": self._request_field_clarification,
            "api_call_failed": self._retry_with_fallback,
            "template_not_found": self._use_cached_template
        }
    
    async def handle_error(self, error_type: str, context: dict) -> dict:
        """统一错误处理入口"""
        
        strategy = self.retry_strategies.get(error_type, self._default_recovery)
        return await strategy(context)
    
    async def _retry_with_simplified_prompt(self, context: dict) -> dict:
        """简化提示词重试AI映射"""
        
        simplified_prompt = f"""
        用户说：{context['user_input']}
        
        请提取以下信息（没有的字段请留空）：
        - 标题：
        - 金额：
        - 项目：
        - 描述：
        
        直接输出JSON：
        {{"title": "...", "amount": "...", "project": "...", "description": "..."}}
        """
        
        try:
            ai_response = await self.deepseek_service.call_api(simplified_prompt)
            simple_mapping = json.loads(ai_response)
            
            # 转换为标准格式
            standard_mapping = self._convert_simple_to_standard(simple_mapping)
            return {"success": True, "mapping": standard_mapping}
            
        except Exception as e:
            return {"success": False, "error": f"简化重试也失败: {e}"}
    
    async def _request_field_clarification(self, context: dict) -> dict:
        """请求用户澄清缺失字段"""
        
        missing_fields = context.get("missing_required", [])
        
        field_descriptions = {
            "title": "申请单标题（如：出差费用、办公用品采购）",
            "requisitionMoney": "申请金额（如：1000元）",
            "u_项目1": "相关项目名称",
            "description": "详细说明"
        }
        
        missing_info = []
        for field in missing_fields:
            desc = field_descriptions.get(field, field)
            missing_info.append(f"- {desc}")
        
        return {
            "success": False,
            "message": f"还需要以下信息才能创建申请单：\n" + "\n".join(missing_info),
            "type": "request_more_info",
            "missing_fields": missing_fields
        }
```

---

## 🔄 动态字段适应机制

### 字段变化检测
```python
class FieldChangeDetector:
    """字段变化检测器"""
    
    def __init__(self):
        self.field_cache_file = ".field_mapping_cache.json"
        self.last_template_hash = None
    
    async def detect_template_changes(self, current_template: dict) -> dict:
        """检测模板字段变化"""
        
        current_hash = self._calculate_template_hash(current_template)
        cached_data = self._load_cache()
        
        if not cached_data or current_hash != cached_data.get("template_hash"):
            # 模板发生变化
            changes = self._analyze_changes(cached_data.get("template"), current_template)
            
            # 更新缓存
            self._save_cache({
                "template": current_template,
                "template_hash": current_hash,
                "last_updated": time.time()
            })
            
            return changes
        
        return {"has_changes": False}
    
    def _analyze_changes(self, old_template: dict, new_template: dict) -> dict:
        """分析模板变化"""
        
        old_fields = set(self._extract_field_names(old_template) if old_template else [])
        new_fields = set(self._extract_field_names(new_template))
        
        added_fields = new_fields - old_fields
        removed_fields = old_fields - new_fields
        
        return {
            "has_changes": bool(added_fields or removed_fields),
            "added_fields": list(added_fields),
            "removed_fields": list(removed_fields),
            "field_details": self._get_field_details(new_template, added_fields)
        }
```

### 自适应字段学习
```python
class AdaptiveFieldLearner:
    """自适应字段学习器"""
    
    async def learn_new_field_mapping(self, new_fields: list, user_input: str) -> dict:
        """学习新字段的映射规则"""
        
        learning_prompt = f"""
        易快报模板新增了以下字段，请分析用户输入并建议映射规则：
        
        新增字段：{json.dumps(new_fields, ensure_ascii=False, indent=2)}
        用户输入：{user_input}
        
        请分析：
        1. 用户输入中哪些信息可能对应这些新字段？
        2. 为每个新字段推荐可能的关键词/别名
        3. 建议字段的重要性等级（必填/可选）
        
        输出格式：
        {{
            "field_mappings": {{
                "u_出差目的地": {{
                    "possible_value": "从用户输入推测的值或null",
                    "keywords": ["目的地", "地点", "去哪"],
                    "importance": "optional"
                }}
            }},
            "confidence": 0.8
        }}
        """
        
        try:
            ai_response = await self.deepseek_service.call_api(learning_prompt)
            learned_rules = json.loads(ai_response)
            
            # 保存学习到的规则
            self._save_learned_mappings(learned_rules)
            
            return learned_rules
            
        except Exception as e:
            logger.error(f"新字段学习失败: {e}")
            return {"field_mappings": {}, "confidence": 0.0}
```

---

## 🚀 主控制器整合

### SmartExpenseMCP主类
```python
class SmartExpenseMCP:
    """智能申请单MCP主控制器"""
    
    def __init__(self):
        self.template_manager = TemplateManager()
        self.ai_field_mapper = AIFieldMapper()
        self.field_validator = FieldValidator()
        self.request_builder = RequestBuilder()
        self.error_recovery = ErrorRecoveryManager()
        self.field_detector = FieldChangeDetector()
        self.adaptive_learner = AdaptiveFieldLearner()
    
    async def create_smart_expense(self, user_input: str) -> dict:
        """核心创建申请单方法"""
        
        try:
            # 1. 获取模板元数据
            template_metadata = await self.template_manager.get_template_metadata()
            
            # 2. 检测模板变化
            changes = await self.field_detector.detect_template_changes(template_metadata)
            if changes.get("has_changes") and changes.get("added_fields"):
                await self.adaptive_learner.learn_new_field_mapping(
                    changes["added_fields"], user_input
                )
            
            # 3. AI字段映射
            mapping_result = await self.ai_field_mapper.generate_field_mapping(
                user_input, template_metadata
            )
            
            if not mapping_result["success"]:
                return await self.error_recovery.handle_error(
                    "ai_mapping_failed", {"user_input": user_input}
                )
            
            # 4. 字段验证和处理
            validation_result = await self.field_validator.validate_and_process_fields(
                mapping_result["mapping"], template_metadata
            )
            
            if not validation_result["success"]:
                return await self.error_recovery.handle_error(
                    "field_validation_failed", validation_result
                )
            
            # 5. 构建请求体
            request_body = await self.request_builder.build_create_request(
                validation_result["processed_fields"], template_metadata
            )
            
            # 6. 调用易快报API
            api_result = await self._call_ekuaibao_create_api(request_body)
            
            return self._format_success_response(api_result)
            
        except Exception as e:
            logger.error(f"创建申请单失败: {e}")
            return await self.error_recovery.handle_error(
                "general_error", {"error": str(e), "user_input": user_input}
            )
    
    async def get_template_fields(self) -> dict:
        """获取模板字段清单"""
        
        try:
            template_metadata = await self.template_manager.get_template_metadata()
            field_list = self._format_fields_for_display(template_metadata)
            
            return {
                "success": True,
                "message": self._generate_field_display_message(field_list),
                "fields": field_list
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"获取模板字段失败: {e}"
            }
    
    async def get_document_by_code(self, code: str) -> dict:
        """根据单据编号查询申请单"""
        
        try:
            url = f"{EK_BASE_URL}/v1.1/flowDetails"
            params = {
                "accessToken": await self.auth_service.get_access_token(),
                "flowId": code
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                result = response.json()
            
            return self._format_query_response(result)
            
        except Exception as e:
            return {
                "success": False,
                "message": f"查询申请单失败: {e}"
            }
```

---

## 📊 性能优化策略

### 缓存机制
1. **模板缓存**: 5分钟缓存，减少API调用
2. **字段映射缓存**: 成功的映射规则缓存，提高响应速度
3. **档案数据缓存**: 部门、员工等档案数据缓存

### 异步处理
1. **并发API调用**: 多个档案字段解析并行处理
2. **异步日志记录**: 不阻塞主流程
3. **背景任务**: 模板变化检测在后台运行

---

*文档更新时间：2024年1月*
*版本：v1.0*

