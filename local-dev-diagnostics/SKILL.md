---
name: local-dev-diagnostics
description: 本地开发环境诊断助手。自动诊断和修复"服务启动不了"、"页面不显示"、"端口被占用"等常见开发环境问题。当用户提到 localhost 无法访问、服务器启动失败、端口冲突、页面空白等问题时自动使用。
allowed-tools: Bash, Read, Grep, Glob
---

# 本地开发环境诊断助手

快速诊断和解决本地开发中最常见的环境问题，节省每次 15-30 分钟的排查时间。

## 核心功能

1. **服务启动诊断**
   - 检查端口占用情况
   - 验证进程是否正常运行
   - 分析启动日志错误

2. **依赖环境检查**
   - Node.js 和 npm/yarn/pnpm 版本
   - Python 和包管理器
   - 数据库服务状态
   - 环境变量配置

3. **网络连接测试**
   - localhost 端口可访问性
   - 前后端连接测试
   - 代理配置检查

4. **一键修复**
   - 自动杀死占用端口的进程
   - 重启服务
   - 清理缓存和重装依赖

## 使用场景

当用户遇到以下问题时自动激活：
- "服务器启动不了"
- "localhost:3000 打不开"
- "页面不显示" / "页面空白"
- "端口被占用"
- "npm run dev 报错"
- "Address already in use"
- "Cannot GET /"
- "ERR_CONNECTION_REFUSED"

## 诊断流程

### 阶段 1: 快速状态检查（10秒内完成）

```bash
# 1. 检查当前目录项目类型
ls -la | grep -E "(package.json|requirements.txt|pom.xml|go.mod)"

# 2. 检查常用开发端口占用
lsof -i :3000 -i :5173 -i :8080 -i :5000 -i :8000

# 3. 检查相关进程
ps aux | grep -E "(node|vite|webpack|vue|react|python|java|nginx)"

# 4. 检查网络监听
netstat -an | grep LISTEN
```

### 阶段 2: 项目类型识别

根据项目文件自动识别：

**前端项目**：
- `package.json` → Node.js 项目
- `vite.config.js` → Vite 项目
- `vue.config.js` → Vue CLI 项目
- `next.config.js` → Next.js 项目

**后端项目**：
- `pom.xml` → Java/Spring Boot
- `requirements.txt` → Python
- `go.mod` → Go
- `Cargo.toml` → Rust

### 阶段 3: 针对性诊断

#### 前端项目诊断

```bash
# 检查 Node.js 环境
node --version
npm --version

# 检查依赖安装状态
[ -d "node_modules" ] && echo "✅ 依赖已安装" || echo "❌ 需要安装依赖"

# 检查启动脚本
cat package.json | grep -A 5 '"scripts"'

# 检查端口配置
grep -r "port" vite.config.* vue.config.* 2>/dev/null

# 检查 .env 文件
ls -la .env* 2>/dev/null
```

#### 后端项目诊断

```bash
# Java/Spring Boot
if [ -f "pom.xml" ]; then
  # 检查 Maven
  mvn --version
  # 检查配置端口
  grep "server.port" src/main/resources/application.* 2>/dev/null
fi

# Python
if [ -f "requirements.txt" ]; then
  python --version
  # 检查虚拟环境
  [ -d "venv" ] || [ -d ".venv" ] && echo "✅ 虚拟环境存在"
fi
```

### 阶段 4: 数据库连接检查

```bash
# MySQL
if command -v mysql &> /dev/null; then
  mysql -u root -e "SELECT 1" 2>&1 | grep -q "ERROR" && echo "❌ MySQL 连接失败" || echo "✅ MySQL 运行正常"
fi

# PostgreSQL
if command -v psql &> /dev/null; then
  pg_isready && echo "✅ PostgreSQL 运行正常" || echo "❌ PostgreSQL 未运行"
fi

# MongoDB
if command -v mongo &> /dev/null; then
  pgrep mongod &> /dev/null && echo "✅ MongoDB 运行正常" || echo "❌ MongoDB 未运行"
fi

# Redis
if command -v redis-cli &> /dev/null; then
  redis-cli ping 2>&1 | grep -q "PONG" && echo "✅ Redis 运行正常" || echo "❌ Redis 未运行"
fi
```

### 阶段 5: 环境变量检查

```bash
# 检查 .env 文件
if [ -f ".env" ]; then
  echo "✅ .env 文件存在"
  # 检查关键配置（不显示敏感值）
  grep -E "^[A-Z_]+=" .env | sed 's/=.*/=***/'
else
  echo "⚠️ .env 文件不存在"
  # 检查是否有示例文件
  [ -f ".env.example" ] && echo "💡 发现 .env.example，建议复制创建 .env"
fi
```

## 常见问题自动修复

### 问题 1: 端口被占用

```bash
# 诊断
PORT=3000
PID=$(lsof -ti :$PORT)

if [ -n "$PID" ]; then
  echo "❌ 端口 $PORT 被进程 $PID 占用"
  ps -p $PID -o comm=

  # 询问是否终止
  echo "🔧 修复方案: kill -9 $PID"
fi
```

**自动修复**：
```bash
# 终止占用端口的进程
kill -9 $(lsof -ti :3000)
echo "✅ 已释放端口 3000"
```

### 问题 2: 依赖未安装或损坏

```bash
# 诊断
if [ ! -d "node_modules" ] || [ ! -f "node_modules/.package-lock.json" ]; then
  echo "❌ 依赖未正确安装"
fi
```

**自动修复**：
```bash
# 清理并重装
rm -rf node_modules package-lock.json
npm install
# 或
pnpm install
```

### 问题 3: 缓存问题

```bash
# 诊断
if [ -d ".vite" ] || [ -d ".next" ] || [ -d "dist" ]; then
  echo "⚠️ 检测到构建缓存，可能需要清理"
fi
```

**自动修复**：
```bash
# Vite 项目
rm -rf .vite dist node_modules/.vite

# Next.js 项目
rm -rf .next out

# Vue CLI 项目
rm -rf dist node_modules/.cache
```

### 问题 4: 权限问题

```bash
# 诊断
if [ ! -w "." ]; then
  echo "❌ 当前目录没有写权限"
fi

# 检查 node_modules 权限
if [ -d "node_modules" ]; then
  [ ! -w "node_modules" ] && echo "❌ node_modules 没有写权限"
fi
```

**自动修复**：
```bash
# 修复权限（谨慎使用）
sudo chown -R $(whoami) .
chmod -R u+w .
```

### 问题 5: 环境变量缺失

```bash
# 检查必需的环境变量
REQUIRED_VARS=("DATABASE_URL" "API_KEY" "PORT")

for var in "${REQUIRED_VARS[@]}"; do
  if ! grep -q "^$var=" .env 2>/dev/null; then
    echo "❌ 缺少环境变量: $var"
  fi
done
```

**自动修复**：
```bash
# 从示例文件复制
if [ -f ".env.example" ] && [ ! -f ".env" ]; then
  cp .env.example .env
  echo "✅ 已从 .env.example 创建 .env"
  echo "⚠️ 请编辑 .env 填入真实配置"
fi
```

## 诊断报告格式

```
🔍 本地开发环境诊断报告
========================

📁 项目类型: Vue 3 + Vite
📍 工作目录: /Users/xxx/project

✅ 运行环境
  - Node.js: v20.10.0
  - npm: 10.2.3
  - 依赖已安装: 是

⚠️ 发现问题
  1. 端口 3000 被占用 (PID: 12345, 进程: node)
  2. .env 文件不存在

🔧 建议修复步骤
  1. 终止占用端口的进程: kill -9 12345
  2. 创建环境配置: cp .env.example .env
  3. 重新启动服务: npm run dev

💡 快速修复
  执行以下命令一键修复:
  kill -9 12345 && cp .env.example .env && npm run dev
```

## 智能判断逻辑

根据用户描述自动选择检查重点：

| 用户描述 | 检查重点 |
|---------|----------|
| "页面空白" | 检查浏览器控制台、路由配置、API 连接 |
| "服务启动不了" | 检查端口占用、依赖安装、配置文件 |
| "Cannot GET /" | 检查路由配置、静态文件路径 |
| "数据库连接失败" | 检查数据库服务、连接字符串、防火墙 |
| "API 请求失败" | 检查后端服务、CORS 配置、网络代理 |

## 项目特定检查

### Vue 项目
```bash
# 检查路由配置
[ -f "src/router/index.js" ] || [ -f "src/router/index.ts" ]

# 检查主入口
[ -f "src/main.js" ] || [ -f "src/main.ts" ]

# 检查 Vite 配置
[ -f "vite.config.js" ] || [ -f "vite.config.ts" ]
```

### Spring Boot 项目
```bash
# 检查启动类
find src/main/java -name "*Application.java"

# 检查配置文件
ls src/main/resources/application.*

# 检查端口冲突
grep "server.port" src/main/resources/application.* | cut -d'=' -f2
```

## 使用提示

1. **首次诊断**会进行全面检查（约 15 秒）
2. **后续诊断**会根据上次结果聚焦问题（约 5 秒）
3. **自动修复**前会先显示将要执行的命令，征得用户确认
4. **敏感信息**（如 API Key）在输出中会自动脱敏
5. **诊断历史**会保存，方便追踪问题变化

## 注意事项

- 永远先展示诊断结果，再询问是否执行修复
- 对于 `kill` 和 `rm` 等危险操作，必须明确告知用户
- 如果用户的项目结构特殊，主动询问项目类型
- 检查结果使用 emoji 标记（✅ ❌ ⚠️ 💡）提高可读性
