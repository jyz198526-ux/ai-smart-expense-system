# 🔗 GitHub集成设置指南

## 🚀 方式一：使用GitHub Personal Access Token（推荐）

### 1. 创建GitHub Personal Access Token

1. 登录GitHub，进入 **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. 点击 **Generate new token (classic)**
3. 设置token信息：
   - **Note**: `AI智能申请单系统`
   - **Expiration**: 选择合适的过期时间
   - **Select scopes**: 勾选以下权限：
     - ✅ `repo` (完整仓库权限)
     - ✅ `workflow` (工作流权限)

4. 点击 **Generate token**
5. **立即复制并保存token**（只显示一次！）

### 2. 创建GitHub仓库

1. 在GitHub上创建新仓库：**Create a new repository**
2. 设置仓库信息：
   - **Repository name**: `ai-smart-expense-system`
   - **Description**: `AI智能申请单系统 - 基于DeepSeek AI和易快报API`
   - **Visibility**: Public 或 Private（根据需要）
   - ❌ **不要**勾选 "Add a README file"（我们已经有了）

3. 复制仓库URL，例如：
   ```
   https://github.com/yourusername/ai-smart-expense-system.git
   ```

### 3. 配置本地Git

运行以下命令配置Git：

```bash
# 配置Git用户信息
git config --global user.name "您的姓名"
git config --global user.email "您的邮箱@example.com"

# 配置Git使用token认证
git config --global credential.helper store
```

### 4. 连接GitHub仓库

```bash
# 添加远程仓库
git remote add origin https://github.com/yourusername/ai-smart-expense-system.git

# 推送代码（会提示输入用户名和密码）
# 用户名：您的GitHub用户名
# 密码：使用刚才创建的Personal Access Token
git push -u origin main
```

## 🔑 方式二：使用SSH密钥（高级）

### 1. 生成SSH密钥

```bash
# 生成SSH密钥对
ssh-keygen -t ed25519 -C "您的邮箱@example.com"

# 启动ssh-agent
eval "$(ssh-agent -s)"

# 添加SSH私钥到ssh-agent
ssh-add ~/.ssh/id_ed25519
```

### 2. 添加SSH公钥到GitHub

1. 复制SSH公钥：
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```

2. 在GitHub上：**Settings** → **SSH and GPG keys** → **New SSH key**
3. 粘贴公钥内容并保存

### 3. 使用SSH URL连接仓库

```bash
# 使用SSH URL添加远程仓库
git remote add origin git@github.com:yourusername/ai-smart-expense-system.git

# 推送代码
git push -u origin main
```

## 🤖 自动化设置

### 使用我们的自动化脚本

1. **Windows用户**：双击运行 `github_setup.bat`
2. **手动设置**：运行 `python auto_backup.py --setup https://github.com/yourusername/repo.git`

### 环境变量配置（可选）

创建 `.env` 文件添加GitHub相关配置：

```env
# GitHub配置（可选）
GITHUB_TOKEN=your_personal_access_token
GITHUB_REPO=yourusername/ai-smart-expense-system
GITHUB_BRANCH=main
```

## 📋 完整操作步骤

### 第一次设置：

```bash
# 1. 配置Git用户信息
git config --global user.name "您的姓名"
git config --global user.email "您的邮箱"

# 2. 添加所有文件
git add .

# 3. 创建初始提交
git commit -m "🎉 初始提交: AI智能申请单系统v1.0.0"

# 4. 连接GitHub仓库
git remote add origin https://github.com/yourusername/ai-smart-expense-system.git

# 5. 推送到GitHub
git push -u origin main
```

### 后续使用：

```bash
# 手动备份
python auto_backup.py --manual

# 启动定时备份
python auto_backup.py --schedule
```

## ⚠️ 注意事项

1. **Personal Access Token安全**：
   - 不要在代码中硬编码token
   - 定期更新token
   - 只给必要的权限

2. **首次推送认证**：
   - 用户名：GitHub用户名
   - 密码：Personal Access Token（不是GitHub密码）

3. **自动备份频率**：
   - 每30分钟检查一次代码变化
   - 每天23:00自动备份
   - 可根据需要调整

## 🔧 故障排除

### 推送失败？
```bash
# 检查远程仓库配置
git remote -v

# 重新设置远程仓库
git remote set-url origin https://github.com/yourusername/repo.git
```

### 认证失败？
- 确认Personal Access Token权限正确
- 检查token是否过期
- 使用token作为密码，不是GitHub密码

### 需要帮助？
运行自动化脚本会有详细的交互式指导！
