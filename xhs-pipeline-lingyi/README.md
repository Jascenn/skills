# xhs-pipeline-lingyi

小红书内容发布完整流水线，by [凌一](https://lingyi.bio)

## 功能

- 一条命令完成：生图 → 写草稿 → 飞书记录
- 自动生图（基于 DashScope qwen-image-2.0-pro，可选）
- 草稿写入小红书（标题/正文/标签/定时/原创）
- 飞书内容库自动新建/更新记录（可选）
- 支持从飞书内容库读取内容发布

## 依赖

**必须先安装底层库：**

> 底层自动化引擎来自 [autoclaw-cc/xiaohongshu-skills](https://github.com/autoclaw-cc/xiaohongshu-skills)，本 skill 仅调用其脚本，不包含其代码。

```bash
git clone https://github.com/autoclaw-cc/xiaohongshu-skills \
  ~/.openclaw/workspace/skills/xiaohongshu-skills
cd ~/.openclaw/workspace/skills/xiaohongshu-skills
uv sync
```

**可选：自动生图**

使用阿里云 DashScope `qwen-image-2.0-pro` 模型生图，需要申请 API key：
- 申请地址：https://dashscope.aliyun.com
- 配置方式：`--setup` 时填入脚本路径，或设置环境变量 `DASHSCOPE_API_KEY`

## 安装

```bash
# 通过 Claude Code skill-install 安装
/skill-install https://github.com/Jascenn/xhs-pipeline-lingyi
```

或手动：

```bash
git clone https://github.com/Jascenn/xhs-pipeline-lingyi \
  ~/.claude/skills/xhs-pipeline-lingyi
```

## 首次配置

```bash
python3 ~/.claude/skills/xhs-pipeline-lingyi/xhs_pipeline_lingyi.py --setup
```

引导配置：
- xiaohongshu-skills 路径（必填，默认自动检测）
- 图片生成脚本路径（可选）
- 飞书内容库配置（可选）
- 飞书选题表配置（可选）

配置保存在 `~/.xhs-pipeline-lingyi/config.json`，随时可用 `--setup` 重新配置。

## 快速开始

```bash
# 最简用法：自己提供图片
python3 ~/.claude/skills/xhs-pipeline-lingyi/xhs_pipeline_lingyi.py \
  --title "你的标题" \
  --content "正文内容

#标签1 #标签2 #标签3" \
  --images /path/to/img1.png /path/to/img2.png

# 自动生图
python3 ~/.claude/skills/xhs-pipeline-lingyi/xhs_pipeline_lingyi.py \
  --title "你的标题" \
  --content "正文内容" \
  --auto-gen-images
```

## 参数说明

| 参数 | 说明 | 是否必填 |
|------|------|---------|
| `--title` | 标题（≤20字） | 是（或 --from-feishu） |
| `--content` | 正文内容 | 否 |
| `--content-file` | 正文文件路径 | 否 |
| `--images` | 图片路径或 URL 列表 | 与 --auto-gen-images 二选一 |
| `--auto-gen-images` | 自动生图 | 否 |
| `--image-output-dir` | 生图输出目录 | 否 |
| `--from-feishu` | 从飞书内容库读取 | 否 |
| `--record-id` | 飞书内容表 record_id | --from-feishu 时必填 |
| `--topic-record-id` | 飞书选题表 record_id | 否 |
| `--schedule-at` | 定时发布时间 ISO8601 | 否，默认今日 19:00 |
| `--visibility` | 可见范围 | 否，默认公开 |
| `--no-feishu-update` | 跳过飞书回写 | 否 |
| `--feishu-backend` | lark-cli 或 openclaw | 否，默认 lark-cli |
| `--setup` | 重新运行配置向导 | 否 |

## 注意事项

- 需要 Chrome 浏览器已启动并登录小红书
- 标题不超过 20 字（汉字计 1，英文每 2 个计 1）
- 标签写在正文最后一行，格式：`#标签1 #标签2`

## License

MIT
