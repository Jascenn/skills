---
name: vue-fullstack-init
description: Vue 3 全栈项目快速初始化工具。一键搭建 Vue 3 + Element Plus 前端和 Node.js/Spring Boot 后端的完整项目框架。当用户提到"创建新项目"、"搭建全栈应用"、"初始化 Vue 项目"时自动使用。
allowed-tools: Bash, Write, Read, Edit, Glob
---

# Vue 3 全栈项目快速初始化

基于你的技术栈偏好，快速搭建生产就绪的全栈项目框架，节省 2-3 小时初始化时间。

## 技术栈

### 前端
- **框架**: Vue 3 (Composition API + `<script setup>`)
- **构建工具**: Vite
- **UI 库**: Element Plus
- **路由**: Vue Router 4
- **状态管理**: Pinia
- **HTTP 客户端**: Axios
- **样式**: SCSS

### 后端选项
- **选项 1**: Node.js + Express + MySQL
- **选项 2**: Spring Boot + MySQL

## 使用场景

当用户说出以下关键词时自动激活：
- "创建一个新的全栈项目"
- "搭建 Vue 3 应用"
- "初始化前后端项目"
- "快速开始一个项目"

## 初始化流程

### 第一步：收集项目信息

询问用户以下信息：
1. **项目名称**: 用于创建目录和配置
2. **项目描述**: 用于 package.json 和 README
3. **后端技术栈**: Node.js 或 Spring Boot
4. **数据库名称**: MySQL 数据库名
5. **端口配置**:
   - 前端端口（默认 5173）
   - 后端端口（默认 8080）

### 第二步：创建前端项目

```bash
# 1. 使用 Vite 创建 Vue 3 项目
npm create vite@latest <project-name>-web -- --template vue

cd <project-name>-web

# 2. 安装核心依赖
npm install

# 3. 安装 Element Plus
npm install element-plus

# 4. 安装路由和状态管理
npm install vue-router@4 pinia

# 5. 安装 Axios
npm install axios

# 6. 安装 SCSS 支持
npm install -D sass

# 7. 安装常用工具库
npm install dayjs lodash-es
```

### 第三步：配置前端项目结构

创建标准化的目录结构：

```
<project-name>-web/
├── public/
│   └── favicon.ico
├── src/
│   ├── api/              # API 接口
│   │   ├── index.js      # Axios 配置
│   │   └── modules/      # 业务模块 API
│   ├── assets/           # 静态资源
│   │   ├── images/
│   │   └── styles/
│   │       └── main.scss
│   ├── components/       # 公共组件
│   │   ├── common/       # 通用组件
│   │   └── business/     # 业务组件
│   ├── composables/      # 组合式函数
│   ├── layouts/          # 布局组件
│   │   └── MainLayout.vue
│   ├── router/           # 路由配置
│   │   └── index.js
│   ├── stores/           # Pinia stores
│   │   └── user.js
│   ├── utils/            # 工具函数
│   │   ├── request.js    # 请求封装
│   │   └── auth.js       # 认证工具
│   ├── views/            # 页面组件
│   │   ├── Home.vue
│   │   └── Login.vue
│   ├── App.vue
│   └── main.js
├── .env.development       # 开发环境变量
├── .env.production        # 生产环境变量
├── vite.config.js
└── package.json
```

### 第四步：生成核心配置文件

#### vite.config.js
```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
```

#### src/main.js
```javascript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import './assets/styles/main.scss'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

app.mount('#app')
```

#### src/router/index.js
```javascript
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('@/views/Home.vue')
      }
    ]
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next('/login')
  } else {
    next()
  }
})

export default router
```

#### src/utils/request.js
```javascript
import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    const res = response.data
    if (res.code !== 200) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  error => {
    ElMessage.error(error.message || '网络错误')
    return Promise.reject(error)
  }
)

export default request
```

#### .env.development
```env
VITE_API_BASE_URL=http://localhost:8080/api
```

#### .env.production
```env
VITE_API_BASE_URL=/api
```

### 第五步：创建后端项目

#### 选项 A: Node.js + Express

```bash
# 1. 创建后端目录
mkdir <project-name>-server
cd <project-name>-server

# 2. 初始化 npm 项目
npm init -y

# 3. 安装依赖
npm install express mysql2 cors dotenv jsonwebtoken bcryptjs
npm install -D nodemon

# 4. 修改 package.json
```

**package.json scripts**:
```json
{
  "scripts": {
    "dev": "nodemon src/index.js",
    "start": "node src/index.js"
  }
}
```

**目录结构**:
```
<project-name>-server/
├── src/
│   ├── config/
│   │   └── db.js         # 数据库配置
│   ├── controllers/      # 控制器
│   ├── models/           # 数据模型
│   ├── routes/           # 路由
│   ├── middleware/       # 中间件
│   │   └── auth.js       # 认证中间件
│   ├── utils/            # 工具函数
│   └── index.js          # 入口文件
├── .env                  # 环境变量
└── package.json
```

**src/index.js**:
```javascript
const express = require('express')
const cors = require('cors')
require('dotenv').config()

const app = express()
const PORT = process.env.PORT || 8080

// 中间件
app.use(cors())
app.use(express.json())
app.use(express.urlencoded({ extended: true }))

// 路由
app.get('/api/health', (req, res) => {
  res.json({ code: 200, message: 'Server is running' })
})

// 启动服务
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`)
})
```

**src/config/db.js**:
```javascript
const mysql = require('mysql2/promise')

const pool = mysql.createPool({
  host: process.env.DB_HOST || 'localhost',
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || '',
  database: process.env.DB_NAME || '<database_name>',
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
})

module.exports = pool
```

**.env**:
```env
PORT=8080
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=<database_name>
JWT_SECRET=your-secret-key-here
```

#### 选项 B: Spring Boot

```bash
# 使用 Spring Initializr 生成项目
curl https://start.spring.io/starter.zip \
  -d dependencies=web,mysql,mybatis,lombok \
  -d groupId=com.example \
  -d artifactId=<project-name> \
  -d name=<project-name> \
  -d packageName=com.example.<project-name> \
  -d javaVersion=17 \
  -o <project-name>-server.zip

unzip <project-name>-server.zip -d <project-name>-server
```

**application.yml**:
```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/<database_name>?useUnicode=true&characterEncoding=utf-8&useSSL=false
    username: root
    password:
    driver-class-name: com.mysql.cj.jdbc.Driver

server:
  port: 8080

mybatis:
  mapper-locations: classpath:mapper/*.xml
  type-aliases-package: com.example.<project-name>.entity
  configuration:
    map-underscore-to-camel-case: true
```

### 第六步：初始化数据库

```sql
-- 创建数据库
CREATE DATABASE IF NOT EXISTS <database_name>
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE <database_name>;

-- 创建用户表（示例）
CREATE TABLE users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  email VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 第七步：生成项目文档

#### README.md
```markdown
# <Project Name>

<项目描述>

## 技术栈

### 前端
- Vue 3 + Vite
- Element Plus
- Vue Router 4
- Pinia
- Axios

### 后端
- Node.js + Express / Spring Boot
- MySQL

## 快速开始

### 前端

\`\`\`bash
cd <project-name>-web
npm install
npm run dev
\`\`\`

访问: http://localhost:5173

### 后端

**Node.js**:
\`\`\`bash
cd <project-name>-server
npm install
npm run dev
\`\`\`

**Spring Boot**:
\`\`\`bash
cd <project-name>-server
mvn spring-boot:run
\`\`\`

访问: http://localhost:8080

### 数据库

1. 创建数据库: `<database_name>`
2. 执行 SQL 脚本: `docs/database.sql`

## 项目结构

见 `docs/project-structure.md`

## 开发规范

见 `docs/coding-standards.md`
```

### 第八步：初始化 Git 仓库

```bash
# 在项目根目录
cd <project-name>

# 初始化 Git
git init

# 创建 .gitignore
cat > .gitignore << 'EOF'
# Dependencies
node_modules/
target/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.iml

# Build
dist/
build/

# Logs
*.log
EOF

# 首次提交
git add .
git commit -m "Initial commit: Vue 3 fullstack project setup"
```

## 完成后的操作提示

初始化完成后，向用户提供清晰的后续步骤：

```
✅ 项目初始化完成！

📁 项目结构:
  - <project-name>-web/     前端项目
  - <project-name>-server/  后端项目

🚀 快速启动:

  # 1. 启动数据库（如果需要）
  mysql -u root -p

  # 2. 启动后端
  cd <project-name>-server
  npm run dev              # Node.js
  # 或
  mvn spring-boot:run      # Spring Boot

  # 3. 启动前端
  cd <project-name>-web
  npm run dev

  # 4. 访问应用
  http://localhost:5173

📖 下一步建议:
  1. 修改 .env 文件配置数据库连接
  2. 创建数据库和表结构
  3. 开发第一个功能模块
  4. 配置 Git 远程仓库并推送

💡 提示:
  - API 接口文档: http://localhost:8080/api/docs
  - 前端代理配置已设置，API 请求自动转发到后端
  - 已配置热重载，修改代码自动刷新
```

## 可选功能

询问用户是否需要以下额外配置：

1. **ESLint + Prettier**: 代码规范和格式化
2. **Husky + lint-staged**: Git 钩子和代码检查
3. **Docker 配置**: 容器化部署
4. **CI/CD 配置**: GitHub Actions / GitLab CI
5. **单元测试**: Vitest (前端) + Jest (后端)
6. **API 文档**: Swagger / OpenAPI
7. **国际化**: vue-i18n

## 注意事项

- 自动检测系统是否安装了 Node.js、npm、MySQL 等必需工具
- 如果端口被占用，自动建议替代端口
- 敏感信息（如数据库密码）提醒用户手动填写
- 生成的代码遵循最佳实践和安全规范
- 提供清晰的目录结构说明和开发指南
