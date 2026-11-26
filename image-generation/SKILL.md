---
name: image-generation
description: "Generate and edit images via multiple backends: Alibaba Cloud Bailian (qwen-image-2.0), Google Nano Banana Pro (Gemini 3 Pro Image), and DashScope. Also covers AI-driven document illustration (配图, 插图) and animated GIF creation for Slack. Use for text-to-image, image-to-image, product promotion, e-commerce editing, marketing materials, social media covers, document illustrations, Slack GIFs. Triggers: generate image, create image, text to image, edit image, 生成图片, 文生图, 图片生成, 做封面, 生成配图, 配图, 插图, illustration, document images, GIF, animated GIF, Slack emoji GIF."
---

# image-generation — 多后端图片生成

## § Alibaba Cloud Bailian / DashScope (bailian-image-gen)

基于阿里云百炼平台 `qwen-image-2.0` 模型，支持文生图和图生图。

**凭据：** 从 `DASHSCOPE_API_KEY` 读取。

**Python API：**
```python
import dashscope
from dashscope import ImageSynthesis

response = ImageSynthesis.call(
    model="qwen-image-2.0-pro",
    prompt="your prompt",
    size="1024x1024",
    negative_prompt="...",     # optional
    ref_image_url="...",       # optional: image-to-image
)
print(response.output.results[0].url)
```

**适用场景：** 小红书封面、信息图、公众号配图、电商产品图、营销素材。

**支持的 size：** `1024x1024`, `1024x768`, `768x1024`, `1280x720`, `720x1280`

---

## § Google Nano Banana Pro / Gemini 3 Pro Image (nano-banana-pro)

Generate new images or edit existing ones using Google's Nano Banana Pro API.

**Usage:**
```bash
# Text-to-image
python /path/to/nano-banana-pro.py --prompt "a futuristic city at sunset" --size 2K

# Image-to-image (edit existing)
python /path/to/nano-banana-pro.py --prompt "make it look like winter" --input-image photo.jpg

# Size options: 1K, 2K, 4K
```

**API key:** Set `NANO_BANANA_API_KEY` or `GOOGLE_API_KEY` in environment.

---

## Choosing a Backend

| Use case | Recommended backend |
|----------|-------------------|
| 小红书/WeChat Chinese content | Bailian (qwen-image-2.0-pro) |
| High-res Western content | Nano Banana Pro (Gemini 3 Pro) |
| E-commerce product images | Bailian |
| Creative/artistic edits | Nano Banana Pro |

---

## § Document Illustration (document-illustrator)

AI-driven illustration generation from document content. Analyzes document structure, summarizes key points per section, and generates matching images.

**Triggers:** 配图, 插图, illustration, generate images for document, document images

**Workflow:**
1. Read the document (markdown, article, notes)
2. Analyze structure — identify sections and key themes
3. For each section, generate a prompt that captures the visual concept
4. Call image generation backend (Bailian or Nano Banana Pro)
5. Save images alongside the document; update references

**Style options:** realistic, illustration, flat design, infographic, diagram, cartoon

**Aspect ratios:** cover (16:9), inline (4:3), portrait (3:4), square (1:1)

```python
# Example: generate cover image from article title + first paragraph
prompt = f"Professional illustration for article: '{title}'. Theme: {summary}. Style: flat design, modern."
response = ImageSynthesis.call(model="qwen-image-2.0-pro", prompt=prompt, size="1280x720")
```

---

## § Slack GIF Creator (slack-gif-creator)

Create animated GIFs optimized for Slack emoji and messages.

**Slack constraints:**
- Emoji GIFs: 128×128px, under 3 seconds, 10-30 FPS, 48-128 colors
- Message GIFs: 480×480px

```bash
# ffmpeg: video clip → Slack-optimized GIF
ffmpeg -i input.mp4 -vf "fps=15,scale=128:128:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=64[p];[s1][p]paletteuse" -loop 0 output.gif

# ImageMagick: optimize existing GIF
convert -layers optimize -fuzz 5% input.gif output.gif

# Validate size
ls -lh output.gif   # target: <500KB for emoji, <2MB for messages
```

**Animation concepts for Slack emoji:**
- Pulse/glow: scale 1.0→1.1→1.0 over 1s
- Spin: rotate 0→360 over 2s
- Bounce: translate Y 0→-10→0 over 0.5s
- Blink: opacity 1→0→1 over 0.8s

Trigger words: "make me a GIF", "Slack GIF", "animated emoji", "GIF for Slack"
| Image-to-image with reference | Either (both support it) |
