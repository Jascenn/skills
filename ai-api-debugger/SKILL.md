---
name: ai-api-debugger
description: AI API 调试助手。快速诊断和测试 AI 模型 API（如 Sora、GPT-4、Claude、Gemini 等）的连通性、认证和调用问题。当用户提到 API 调用失败、接口调试、模型测试或遇到 AI 服务错误时自动使用。
allowed-tools: Bash, Read, Edit, Write, Grep, Glob
---

# AI API 调试助手

专门用于快速诊断和测试各种 AI 模型 API 的连通性和调用问题。

## 核心功能

1. **API 连通性测试**
   - 验证 Base URL 可访问性
   - 检查 API Key 有效性
   - 测试认证机制

2. **请求诊断**
   - 格式化和验证请求参数
   - 检查必需字段和数据类型
   - 提供标准化的请求模板

3. **响应分析**
   - 解析 API 响应结构
   - 翻译常见错误代码
   - 提供错误解决方案

4. **代码生成**
   - 生成调用示例代码（JavaScript/Python）
   - 包含错误处理和重试逻辑
   - 适配不同 AI 服务的 SDK

## 使用场景

当用户遇到以下问题时自动激活：
- "API 调用失败"
- "模型接口连不上"
- "API Key 不work"
- "401/403/500 错误"
- "测试一下 Sora API"
- "调试 GPT-4 接口"

## 工作流程

### 第一步：收集信息
询问或从环境中获取：
- API Base URL
- API Key（安全处理，不完整显示）
- 目标模型名称
- 请求参数示例

### 第二步：基础连通性测试
```bash
# 测试 URL 可访问性
curl -I <base_url>

# 测试认证
curl -X POST <base_url>/models \
  -H "Authorization: Bearer <api_key>" \
  -H "Content-Type: application/json"
```

### 第三步：诊断分析
根据响应状态码提供诊断：
- **200-299**: 连接正常，继续测试完整请求
- **401**: API Key 无效或过期
- **403**: 权限不足或 IP 限制
- **404**: URL 路径错误
- **429**: 请求频率限制
- **500-599**: 服务器错误

### 第四步：完整请求测试
构建符合目标 API 规范的完整请求：

**Sora API 示例**：
```bash
curl -X POST <base_url>/v1/video/generations \
  -H "Authorization: Bearer <api_key>" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "测试提示词",
    "model": "sora-1.0-turbo",
    "size": "1280x720"
  }'
```

**OpenAI 兼容 API 示例**：
```bash
curl -X POST <base_url>/v1/chat/completions \
  -H "Authorization: Bearer <api_key>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### 第五步：生成调用代码
根据测试成功的请求，生成封装好的调用代码：

**JavaScript/Node.js**：
```javascript
async function callAIAPI(prompt) {
  const response = await fetch('<base_url>/v1/endpoint', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      prompt: prompt,
      // ... 其他参数
    })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`API Error: ${error.message}`);
  }

  return await response.json();
}
```

**Python**：
```python
import requests
import os

def call_ai_api(prompt):
    response = requests.post(
        '<base_url>/v1/endpoint',
        headers={
            'Authorization': f'Bearer {os.getenv("API_KEY")}',
            'Content-Type': 'application/json'
        },
        json={
            'prompt': prompt,
            # ... 其他参数
        }
    )
    response.raise_for_status()
    return response.json()
```

## 常见 AI 服务配置

### Sora API
- Base URL: 通常为 `https://api.sora.com` 或自建服务
- 认证: Bearer Token
- 关键参数: prompt, model, size, duration

### OpenAI API
- Base URL: `https://api.openai.com`
- 认证: Bearer Token
- 关键参数: model, messages, temperature

### Claude API
- Base URL: `https://api.anthropic.com`
- 认证: `x-api-key` header
- 关键参数: model, messages, max_tokens

### Gemini API
- Base URL: `https://generativelanguage.googleapis.com`
- 认证: API Key 作为查询参数
- 关键参数: model, contents

## 错误代码速查表

| 状态码 | 含义 | 解决方案 |
|--------|------|---------|
| 401 | 认证失败 | 检查 API Key 是否正确、是否过期 |
| 403 | 权限不足 | 检查账户额度、IP 白名单、服务权限 |
| 404 | 路径错误 | 检查 Base URL 和 endpoint 路径 |
| 429 | 频率限制 | 添加重试逻辑，增加请求间隔 |
| 500 | 服务器错误 | 检查请求参数格式，联系服务提供商 |
| 503 | 服务不可用 | 服务维护中，稍后重试 |

## 安全提示

1. **永远不要**在代码中硬编码 API Key
2. 使用环境变量存储敏感信息
3. 在日志中隐藏 API Key（只显示前/后几位）
4. 定期轮换 API Key
5. 为不同环境使用不同的 Key

## 输出格式

诊断完成后，提供清晰的报告：

```
✅ AI API 诊断报告
==================

🔗 连通性: 正常
🔐 认证状态: 有效
📊 测试请求: 成功

响应示例:
{
  "id": "xxx",
  "status": "success",
  ...
}

✨ 已生成调用代码（见上方）

💡 建议:
- 将 API Key 存储在 .env 文件
- 添加错误重试机制
- 实现请求频率控制
```

## 注意事项

- 在测试时使用最小的请求参数，避免消耗配额
- 对于生成类 API（如 Sora），建议先用简单提示词测试
- 自动检测项目中是否已有 API 配置文件（.env, config.js 等）
- 如果用户的项目中有相关配置，优先使用现有配置进行测试
