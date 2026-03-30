---
name: wechat-mp-publisher
description: 通用微信公众号创作与发布 Skill。支持话题创作和素材整理，自动生成标题+大纲，扩写正文，推送草稿，保存到飞书 Base。
owner: 通用版
status: active
---

# wechat-mp-publisher

通用微信公众号创作与发布 Skill

## 快速配置

### 环境变量（~/.wechat-mp/config.env）

```bash
WECHAT_APPID=your_appid
WECHAT_SECRET=your_secret
WECHAT_TOKEN=your_token
WECHAT_THUMB_MEDIA_ID=your_cover_media_id
FEISHU_BASE_TOKEN=your_base_token
FEISHU_TABLE_ID=your_table_id
DEFAULT_AUTHOR=作者名
DEFAULT_TAGS=标签1,标签2
```

### 配置文件（.wechat-mp/EXTEND.md）

```md
default_author: 你的名字
default_tags: 写作,自媒体
default_cover_media_id: media_id
```

## 使用流程

**话题创作**：话题 → 生成标题+大纲 → 选择 → 扩写 → 推送
**素材整理**：素材 → 确认信息 → 整理 → 推送

## 核心功能

- 生成标题和大纲
- 扩写正文
- 推送草稿
- 保存到飞书 Base
- 防止内容丢失

## 命令

```bash
python3 mp_push.py --title "标题" --topic "主题" --body body.html --day 1
```
