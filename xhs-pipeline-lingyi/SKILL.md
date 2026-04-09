---
name: xhs-pipeline-lingyi
description: 小红书内容发布完整流水线。支持自动生图、草稿写入、飞书内容库记录管理。当用户要发小红书、写草稿、生图发布时触发。
version: 1.0.0
---

# xhs-pipeline-lingyi

小红书内容发布流水线，支持：
- 自动生图（可选）
- 草稿写入小红书
- 飞书内容库记录管理（可选）

## 依赖

安装前需要先安装底层库：
```bash
git clone https://github.com/autoclaw-cc/xiaohongshu-skills ~/.openclaw/workspace/skills/xiaohongshu-skills
cd ~/.openclaw/workspace/skills/xiaohongshu-skills
uv sync
```

## 首次配置

```bash
python3 ~/.claude/skills/xhs-pipeline-lingyi/xhs_pipeline_lingyi.py --setup
```

## 用法

```bash
# B 线：直接传参 + 自动生图
python3 xhs_pipeline_lingyi.py \
  --title "标题" \
  --content "正文内容 #标签1 #标签2" \
  --auto-gen-images

# B 线：自己提供图片
python3 xhs_pipeline_lingyi.py \
  --title "标题" \
  --content "正文内容" \
  --images /path/to/img1.png /path/to/img2.png

# A 线：从飞书读取
python3 xhs_pipeline_lingyi.py \
  --from-feishu \
  --record-id recvXXXXXX
```

## 参数

| 参数 | 说明 |
|------|------|
| `--setup` | 重新运行配置向导 |
| `--title` | 标题（≤20字） |
| `--content` | 正文内容 |
| `--content-file` | 正文文件路径 |
| `--images` | 图片路径或 URL |
| `--auto-gen-images` | 自动生图 |
| `--from-feishu` | 从飞书读取内容 |
| `--record-id` | 飞书内容表 record_id |
| `--topic-record-id` | 飞书选题表 record_id |
| `--schedule-at` | 定时发布时间 ISO8601 |
| `--no-feishu-update` | 跳过飞书回写 |
| `--feishu-backend` | lark-cli（默认）或 openclaw |
