# 微信公众号发布 Skill（通用版）

通用的微信公众号内容创作与发布工具。

## 快速开始

### 方式一：使用初始化向导（推荐）

```bash
cd scripts
python3 init.py
```

按提示逐步配置：
1. 微信公众号 APPID、SECRET、TOKEN
2. 封面图 media_id（可选）
3. 默认作者（可选）
4. 默认标签（可选）
5. 飞书 Base（可选）

### 方式二：手动配置

```bash
mkdir -p ~/.wechat-mp
cp config.example.env ~/.wechat-mp/config.env
# 编辑配置文件
```

## 使用

```bash
# 基础用法
python3 scripts/mp_push.py --title "标题" --content "内容"

# 自定义作者和标签
python3 scripts/mp_push.py --title "标题" --content "内容" --author "张三" --tags "科技,AI"

# 跳过飞书 Base
python3 scripts/mp_push.py --title "标题" --content "内容" --no-feishu
```

## 配置说明

**必填项：**
- WECHAT_APPID - 公众号 AppID
- WECHAT_SECRET - 公众号 AppSecret
- WECHAT_TOKEN - 后台 Token

**可选项：**
- WECHAT_THUMB_MEDIA_ID - 封面图（推荐配置）
- DEFAULT_AUTHOR - 默认作者
- DEFAULT_TAGS - 默认标签
- FEISHU_BASE_TOKEN - 飞书记录管理
- FEISHU_TABLE_ID - 飞书表格 ID
