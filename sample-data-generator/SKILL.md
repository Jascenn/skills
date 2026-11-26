---
name: sample-data-generator
description: 智能示例数据生成器。为开发和测试自动生成符合业务逻辑的真实中文示例数据。当用户提到"生成测试数据"、"添加示例数据"、"没有数据展示"、"需要演示数据"时自动使用。
allowed-tools: Bash, Read, Write, Grep, Glob
---

# 智能示例数据生成器

自动分析数据库结构并生成真实、符合业务逻辑的中文示例数据，便于开发调试和功能演示。

## 核心功能

1. **自动分析表结构**
   - 读取数据库 schema
   - 识别字段类型和约束
   - 分析表关联关系

2. **智能数据生成**
   - 根据字段名语义生成相关数据
   - 支持中文姓名、地址、公司等
   - 遵守外键和唯一性约束

3. **业务逻辑感知**
   - 识别常见字段类型（邮箱、手机、URL）
   - 生成有关联性的数据（订单-商品）
   - 符合真实业务场景

4. **多种导出格式**
   - SQL INSERT 语句
   - JSON 格式
   - CSV 文件

## 使用场景

当用户说出以下关键词时自动激活：
- "生成一些测试数据"
- "添加示例数据"
- "表里没有数据"
- "需要演示数据"
- "数据库是空的"
- "模拟用户数据"

## 数据生成流程

### 第一步：获取数据库结构

```bash
# 方式 1: 从 SQL 文件读取
if [ -f "schema.sql" ] || [ -f "database.sql" ]; then
  # 解析建表语句
fi

# 方式 2: 从 ORM 模型文件读取
# Java: Entity 类
# Node.js: Sequelize/TypeORM models
# Python: SQLAlchemy models

# 方式 3: 直接连接数据库
mysql -u root -p -e "SHOW TABLES FROM <database>"
mysql -u root -p -e "DESCRIBE <table_name>"
```

### 第二步：分析表结构

识别以下信息：
- **主键**: 自增 ID 还是 UUID
- **外键**: 关联表和字段
- **唯一约束**: username, email 等
- **非空约束**: 必填字段
- **默认值**: 时间戳、状态等
- **字段类型**: INT, VARCHAR, TEXT, DATETIME 等

### 第三步：字段语义识别

根据字段名推断数据类型：

| 字段名模式 | 生成数据类型 | 示例 |
|-----------|-------------|------|
| *name, *_name | 中文姓名 | 张三、李四 |
| username, account | 用户名 | zhangsan, lisi123 |
| email, *_email | 邮箱 | zhangsan@example.com |
| phone, mobile, tel | 手机号 | 13800138000 |
| address, *_address | 地址 | 北京市朝阳区xxx街道 |
| company, *_company | 公司名 | XX科技有限公司 |
| title, *_title | 标题 | 根据表名生成相关标题 |
| content, description | 描述文本 | 多段落文本 |
| url, link, *_url | URL | https://example.com |
| avatar, *_image, *_img | 图片 URL | https://picsum.photos/200 |
| price, amount, *_price | 价格 | 99.99 |
| status | 状态码 | 0, 1, 2 |
| created_at, created_time | 创建时间 | 最近时间戳 |
| updated_at, updated_time | 更新时间 | 创建时间之后 |

### 第四步：生成数据

#### 中文数据库

**常用姓氏（100个）**：
```javascript
const surnames = ['王', '李', '张', '刘', '陈', '杨', '黄', '赵', '周', '吴', '徐', '孙', '马', '朱', '胡', '郭', '何', '林', '罗', '高', '郑', '梁', '谢', '宋', '唐', '许', '韩', '冯', '邓', '曹', '彭', '曾', '萧', '田', '董', '袁', '潘', '于', '蒋', '蔡', '余', '杜', '叶', '程', '苏', '魏', '吕', '丁', '任', '沈']
```

**常用名字**：
```javascript
const givenNames = ['伟', '芳', '娜', '秀英', '敏', '静', '丽', '强', '磊', '军', '洋', '勇', '艳', '杰', '涛', '明', '超', '秀兰', '霞', '平', '刚', '桂英']
```

**中文城市和地址**：
```javascript
const cities = ['北京市', '上海市', '广州市', '深圳市', '杭州市', '成都市', '武汉市', '西安市', '南京市', '重庆市']
const districts = ['朝阳区', '海淀区', '浦东新区', '天河区', '南山区', '西湖区', '锦江区']
const streets = ['中山路', '人民路', '建设街', '解放路', '幸福路', '文化街']
```

**公司名称模板**：
```javascript
const companyPrefixes = ['阿里', '腾讯', '百度', '京东', '华为', '小米', '字节跳动']
const companyTypes = ['科技有限公司', '网络科技公司', '信息技术有限公司', '软件开发公司']
```

#### 示例：用户表数据生成

```javascript
// 伪代码示例
function generateUser(id) {
  const surname = randomChoice(surnames)
  const givenName = randomChoice(givenNames)
  const name = surname + givenName
  const username = pinyin(name) + randomInt(100, 999)

  return {
    id: id,
    username: username,
    password: bcrypt.hash('123456'), // 默认密码
    real_name: name,
    email: `${username}@example.com`,
    phone: `138${randomInt(10000000, 99999999)}`,
    avatar: `https://i.pravatar.cc/150?img=${id}`,
    gender: randomChoice([0, 1]), // 0女 1男
    birthday: randomDate('1980-01-01', '2000-12-31'),
    address: `${randomChoice(cities)}${randomChoice(districts)}${randomChoice(streets)}${randomInt(1, 999)}号`,
    status: 1, // 1正常 0禁用
    created_at: randomDate('2023-01-01', '2024-12-01'),
    updated_at: 'NOW()'
  }
}
```

### 第五步：处理表关联

#### 一对多关系示例：用户和订单

```sql
-- 1. 先生成用户数据（主表）
INSERT INTO users (username, real_name, ...) VALUES
  ('zhangsan', '张三', ...),
  ('lisi', '李四', ...);

-- 2. 再生成订单数据（从表）
INSERT INTO orders (user_id, order_no, ...) VALUES
  (1, 'ORD20240101001', ...), -- 张三的订单
  (1, 'ORD20240102001', ...), -- 张三的另一个订单
  (2, 'ORD20240103001', ...); -- 李四的订单
```

#### 多对多关系示例：学生和课程

```sql
-- 1. 生成学生数据
INSERT INTO students (...) VALUES (...);

-- 2. 生成课程数据
INSERT INTO courses (...) VALUES (...);

-- 3. 生成关联关系
INSERT INTO student_courses (student_id, course_id, score) VALUES
  (1, 1, 85), -- 学生1选修课程1，分数85
  (1, 2, 92), -- 学生1选修课程2
  (2, 1, 78); -- 学生2选修课程1
```

### 第六步：生成 SQL 文件

```sql
-- =====================================================
-- 示例数据生成
-- 生成时间: 2024-01-01 10:00:00
-- 表: users, orders
-- 数据量: 50 users, 200 orders
-- =====================================================

USE <database_name>;

-- 清空现有数据（可选）
-- TRUNCATE TABLE orders;
-- TRUNCATE TABLE users;

-- 用户数据
INSERT INTO `users` (`id`, `username`, `password`, `real_name`, `email`, `phone`, `avatar`, `status`, `created_at`) VALUES
(1, 'zhangsan123', '$2a$10$...', '张三', 'zhangsan123@example.com', '13800138001', 'https://i.pravatar.cc/150?img=1', 1, '2023-06-15 10:30:00'),
(2, 'lisi456', '$2a$10$...', '李四', 'lisi456@example.com', '13800138002', 'https://i.pravatar.cc/150?img=2', 1, '2023-07-20 14:20:00'),
-- ... 更多数据
(50, 'wangwu789', '$2a$10$...', '王五', 'wangwu789@example.com', '13800138050', 'https://i.pravatar.cc/150?img=50', 1, '2024-01-10 09:15:00');

-- 订单数据
INSERT INTO `orders` (`id`, `user_id`, `order_no`, `total_amount`, `status`, `created_at`) VALUES
(1, 1, 'ORD20230615001', 299.00, 2, '2023-06-15 11:00:00'),
(2, 1, 'ORD20230720001', 599.00, 2, '2023-07-20 15:30:00'),
-- ... 更多数据
(200, 50, 'ORD20240110001', 199.00, 1, '2024-01-10 10:00:00');
```

### 第七步：生成 JSON 格式（可选）

```json
{
  "users": [
    {
      "id": 1,
      "username": "zhangsan123",
      "real_name": "张三",
      "email": "zhangsan123@example.com",
      "phone": "13800138001",
      "status": 1,
      "created_at": "2023-06-15T10:30:00Z"
    }
  ],
  "orders": [
    {
      "id": 1,
      "user_id": 1,
      "order_no": "ORD20230615001",
      "total_amount": 299.00,
      "status": 2,
      "created_at": "2023-06-15T11:00:00Z"
    }
  ]
}
```

## 特殊场景处理

### 场景 1: 电商系统

```javascript
// 商品数据
const products = [
  { name: 'iPhone 15 Pro', category: '手机', price: 7999, stock: 100 },
  { name: '小米电视 65寸', category: '电视', price: 2999, stock: 50 },
  { name: '华为笔记本', category: '电脑', price: 5999, stock: 30 }
]

// 订单明细关联商品
function generateOrderItem(orderId, productId) {
  const product = products[productId - 1]
  const quantity = randomInt(1, 3)
  return {
    order_id: orderId,
    product_id: productId,
    product_name: product.name,
    price: product.price,
    quantity: quantity,
    subtotal: product.price * quantity
  }
}
```

### 场景 2: 博客系统

```javascript
// 文章标题和内容
const articleTopics = ['技术', '生活', '旅游', '美食', '科技']
const titleTemplates = [
  '如何{verb}{topic}',
  '{topic}的十大{noun}',
  '我的{topic}心得分享',
  '深入理解{topic}'
]

function generateArticle() {
  const topic = randomChoice(articleTopics)
  const title = renderTemplate(randomChoice(titleTemplates), { topic })
  const content = generateParagraphs(3, 5) // 3-5段

  return {
    title: title,
    content: content,
    author_id: randomInt(1, 10),
    category: topic,
    views: randomInt(100, 10000),
    likes: randomInt(10, 500),
    status: 1,
    created_at: randomDate('2023-01-01', '2024-12-01')
  }
}
```

### 场景 3: 教育系统

```javascript
// 学生成绩数据
const subjects = ['语文', '数学', '英语', '物理', '化学', '生物', '历史', '地理', '政治']

function generateScore(studentId, courseId) {
  const subject = subjects[courseId - 1]
  const baseScore = {
    '语文': 85, '数学': 80, '英语': 88,
    '物理': 75, '化学': 78, '生物': 82
  }[subject] || 80

  // 基于基础分数添加随机波动 ±15
  const score = baseScore + randomInt(-15, 15)

  return {
    student_id: studentId,
    course_id: courseId,
    subject: subject,
    score: Math.max(0, Math.min(100, score)), // 限制在 0-100
    exam_date: randomDate('2024-01-01', '2024-06-01')
  }
}
```

## 数据量建议

根据表类型建议合理的数据量：

| 表类型 | 建议数量 | 原因 |
|--------|---------|------|
| 用户表 | 20-50 | 足够演示用户列表和分页 |
| 文章/商品 | 50-100 | 展示搜索、筛选、排序功能 |
| 订单 | 100-300 | 演示订单列表和统计 |
| 评论/日志 | 200-500 | 测试大数据量的查询性能 |
| 系统配置 | 5-10 | 基本配置项即可 |
| 权限/角色 | 3-5 | 常见角色组合 |

## 执行数据导入

### 方式 1: MySQL 命令行

```bash
# 导入 SQL 文件
mysql -u root -p <database_name> < sample_data.sql

# 或者直接执行
mysql -u root -p -e "source /path/to/sample_data.sql"
```

### 方式 2: 程序代码

**Node.js**:
```javascript
const mysql = require('mysql2/promise')
const fs = require('fs')

async function importData() {
  const connection = await mysql.createConnection({
    host: 'localhost',
    user: 'root',
    password: '',
    database: '<database_name>',
    multipleStatements: true
  })

  const sql = fs.readFileSync('sample_data.sql', 'utf8')
  await connection.query(sql)
  console.log('✅ 数据导入成功')
  await connection.end()
}
```

**Python**:
```python
import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='<database_name>'
)

cursor = conn.cursor()
with open('sample_data.sql', 'r', encoding='utf-8') as f:
    sql = f.read()
    for statement in sql.split(';'):
        if statement.strip():
            cursor.execute(statement)

conn.commit()
print('✅ 数据导入成功')
```

## 输出报告

```
✅ 示例数据生成完成
====================

📊 生成统计:
  - users 表: 50 条记录
  - orders 表: 200 条记录
  - order_items 表: 456 条记录
  - products 表: 30 条记录

📁 生成文件:
  - sample_data.sql (45.2 KB)
  - sample_data.json (38.7 KB)

🔗 表关联:
  - users → orders (一对多)
  - orders → order_items (一对多)
  - order_items → products (多对一)

💡 默认账号:
  用户名: zhangsan123
  密码: 123456

🚀 导入命令:
  mysql -u root -p <database> < sample_data.sql

⏱️ 耗时: 2.3 秒
```

## 注意事项

1. **数据安全**：
   - 默认密码使用 bcrypt 加密
   - 不生成真实的敏感信息
   - 明确标记为测试数据

2. **数据一致性**：
   - 遵守外键约束
   - 保证唯一性约束
   - 时间字段符合逻辑顺序

3. **性能考虑**：
   - 批量插入而非逐条插入
   - 大数据量时分批生成
   - 提供禁用索引的选项

4. **可定制性**：
   - 询问用户需要的数据量
   - 允许用户指定特定字段的值
   - 支持增量添加数据

5. **清理提示**：
   - 生成的 SQL 包含可选的 TRUNCATE 语句
   - 提醒用户备份重要数据
   - 提供数据清理脚本
