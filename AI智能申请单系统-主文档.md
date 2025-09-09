# AI智能申请单系统 - 完整开发文档

## 📋 项目概述

### 🎯 项目目标
构建一个基于AI的智能申请单填写系统，用户通过自然语言即可创建、查询易快报申请单，系统自动提取字段信息并调用易快报API完成单据创建。

### 🌟 核心特性
- **两阶段交互模式**：先展示字段清单 → 用户填写信息 → 创建申请单
- **智能字段映射**：AI自动从用户描述中提取标题、金额、项目等字段
- **动态模板适应**：系统自动适应新增/删除字段，无需手动配置
- **零硬编码设计**：除特殊字段外，所有字段映射均由AI动态处理

### 📊 技术栈
- **后端框架**: FastAPI
- **AI服务**: DeepSeek API
- **HTTP客户端**: httpx (异步)
- **前端**: HTML/CSS/JavaScript 聊天界面
- **认证**: 易快报 OAuth 2.0

---

## 🔐 关键配置信息

### API密钥与接口
```bash
# DeepSeek AI
DEEPSEEK_API_KEY=sk-43816199a7fd42f88e93b14358954b88
DEEPSEEK_API_URL=https://api.deepseek.com/chat/completions

# 易快报认证
EK_APP_KEY=b433ffa4-ff6e-4e76-95e6-1a7bed8777eb
EK_APP_SECURITY=60ec2aa6-6354-40b5-a742-0e1034962b2f

# 易快报API基础URL
EK_BASE_URL=https://app.ekuaibao.com/api/openapi
```

### 关键API端点
```bash
# 获取Token
POST /api/openapi/v1/auth/getAccessToken

# 刷新Token
POST /api/openapi/v2/auth/refreshToken?accessToken={token}&refreshToken={refresh_token}&powerCode=219904

# 获取申请单模板列表
GET /api/openapi/v1/specifications/latestByType?accessToken={token}&type=requisition

# 获取模板详情（含小版本号）
GET /api/openapi/v2/specifications/byIds/[{template_id}]?accessToken={token}

# 创建申请单
POST /api/openapi/v2.2/flow/data?accessToken={token}&isCommit=false&isUpdate=false

# 查询申请单详情
GET /api/openapi/v1.1/flowDetails?flowId={flow_id}&accessToken={token}
```

---

## 🏗️ 系统架构

### 整体架构图
```
用户前端界面 → FastAPI主服务 → DeepSeek AI服务
                     ↓
              AI意图识别与处理
                     ↓
              智能MCP工具层
                     ↓
              易快报API集成
```

### 核心组件说明
1. **前端界面** (`templates/index.html`): 简洁的聊天界面
2. **FastAPI服务** (`main.py`): 主要API端点和路由
3. **DeepSeek集成** (`services/deepseek_service.py`): AI服务调用
4. **认证服务** (`services/auth_service.py`): Token管理
5. **智能MCP层** (`smart_expense_mcp.py`): 核心业务逻辑

---

## 🔄 交互流程设计

### 两阶段交互模式

#### 阶段一：模板字段展示
```
用户: "我要创建申请单"
     ↓
系统: 调用 get_template_fields()
     ↓
AI: "我为您获取了申请单模板，需要填写以下字段：
    📋 必填字段：
    - 标题：申请单名称（最多14个字符）
    - 金额：申请金额
    📝 可选字段：
    - 项目：相关项目名称
    - 描述：详细说明
    请提供这些信息。"
```

#### 阶段二：信息收集与创建
```
用户: "标题是出差费用，金额1000元，项目是北京会议"
     ↓
系统: 调用 create_smart_expense()
     ↓
AI: "✅ 申请单创建成功！
    - 单据编号：S25000089
    - 标题：出差费用
    - 金额：1000元
    - 项目：北京会议
    - 状态：草稿"
```

### 查询流程
```
用户: "查询申请单S25000089"
     ↓
系统: 调用 get_document_by_code()
     ↓
AI: "📋 申请单详情：
    - 编号：S25000089
    - 标题：出差费用
    - 状态：已提交
    - 创建时间：2024-01-26 10:30:00"
```

---

## 📁 项目目录结构

```
AI智能申请单系统/
├── main.py                     # FastAPI主服务
├── smart_expense_mcp.py        # 智能MCP核心层
├── services/
│   ├── auth_service.py         # 认证服务
│   └── deepseek_service.py     # DeepSeek AI服务
├── templates/
│   └── index.html              # 前端聊天界面
├── configs/
│   ├── field_mappings.json     # 字段映射配置
│   └── special_fields.json     # 特殊字段配置
├── .env                        # 环境变量
├── requirements.txt            # 依赖管理
├── .token_cache.json          # Token缓存（运行时生成）
└── README.md                   # 项目说明
```

---

## 🚀 开发计划

### 阶段一：基础架构搭建 (1-2天)
1. **项目初始化**
   - 创建项目目录结构
   - 配置虚拟环境和依赖
   - 设置环境变量管理

2. **认证服务开发** (`services/auth_service.py`)
   - 实现易快报Token获取和刷新
   - 文件缓存机制
   - Token过期检测

3. **FastAPI主服务** (`main.py`)
   - 创建基础API端点
   - 配置CORS和中间件
   - 对话状态管理

### 阶段二：AI集成与意图识别 (2-3天)
4. **DeepSeek服务** (`services/deepseek_service.py`)
   - 集成DeepSeek API
   - 两阶段交互提示词
   - 工具调用处理

5. **AI意图识别**
   - 创建申请单请求检测
   - 字段信息提供检测
   - 查询请求检测

### 阶段三：MCP层核心实现 (2-3天)
6. **智能MCP层** (`smart_expense_mcp.py`)
   - 模板字段展示功能
   - AI字段映射和验证
   - 动态请求体构建
   - 错误处理和恢复

### 阶段四：前端与完善 (1-2天)
7. **前端界面** (`templates/index.html`)
   - 聊天界面设计
   - 字段清单显示组件
   - 实时消息显示

8. **系统优化**
   - 性能优化
   - 日志系统
   - 集成测试

---

## 📝 核心文档链接

本文档包含以下子文档：
- [AI提示词设计文档](./AI提示词设计文档.md)
- [MCP层详细设计文档](./MCP层详细设计文档.md)
- [API集成文档](./API集成文档.md)
- [错误处理与容错机制文档](./错误处理与容错机制文档.md)

---

## ✅ 成功标准

### 测试用例
1. **创建测试**: "创建一份标题为测试费用的申请单，金额500元"
   - 成功标准：返回易快报的真实单据编号，能在易快报后台看到单据

2. **查询测试**: "查询申请单S25000089"
   - 成功标准：返回该单据的详细信息

3. **容错测试**: "我想申请钱"
   - 成功标准：AI能正确追问缺少的信息

### 性能指标
- **响应时间**: 单次创建 < 5秒
- **成功率**: 字段映射准确率 > 95%
- **可扩展性**: 新增字段无需代码修改

---

*文档创建时间：2024年1月*
*版本：v1.0*

