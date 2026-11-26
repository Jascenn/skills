---
name: image-asset-processor
description: 图片资源处理器。自动化处理网站图片资源，包括 Logo、Favicon、图标的格式转换、多尺寸生成、压缩优化和路径配置。当用户提到"Logo 不显示"、"Favicon 更新"、"图标处理"、"图片优化"时自动使用。
allowed-tools: Bash, Read, Write, Edit, Glob
---

# 图片资源处理器

一站式解决网站图片资源处理需求，从格式转换到配置更新全自动化。

## 核心功能

1. **Favicon 完整方案**
   - 生成多尺寸 Favicon (16x16, 32x32, 192x192, 512x512)
   - 格式转换 (SVG → PNG → ICO)
   - 生成 Apple Touch Icon (180x180)
   - 更新 HTML 引用

2. **Logo 处理**
   - 多格式导出 (SVG, PNG, WebP)
   - 透明背景和白色背景版本
   - 响应式尺寸生成

3. **图片优化**
   - 自动压缩（无损/有损）
   - 格式转换为 WebP
   - 批量处理

4. **配置管理**
   - 自动更新 HTML meta 标签
   - 生成 manifest.json
   - 生成 browserconfig.xml (Windows)

## 使用场景

当用户说出以下关键词时自动激活：
- "Logo 不显示"
- "更新 Favicon"
- "添加网站图标"
- "图片太大了"
- "压缩图片"
- "图标显示不正常"
- "Apple Touch Icon"

## 处理流程

### 第一步：检测现有资源

```bash
# 查找可能的 Logo/Icon 文件
find . -type f \( \
  -name "*logo*" -o \
  -name "*icon*" -o \
  -name "*favicon*" -o \
  -name "*apple-touch-icon*" \
) | grep -E "\.(svg|png|ico|jpg)$"

# 检查 HTML 中的引用
grep -r "favicon" --include="*.html" .
grep -r "apple-touch-icon" --include="*.html" .
grep -r "manifest.json" --include="*.html" .
```

### 第二步：安装必要工具

检测并安装图片处理工具：

```bash
# macOS
if ! command -v convert &> /dev/null; then
  echo "安装 ImageMagick..."
  brew install imagemagick
fi

if ! command -v pngquant &> /dev/null; then
  echo "安装 pngquant..."
  brew install pngquant
fi

# Linux (Ubuntu/Debian)
# sudo apt-get install imagemagick pngquant webp

# 检查 Node.js 工具
if command -v npm &> /dev/null; then
  # sharp: 高性能图片处理
  npm list -g sharp || npm install -g sharp-cli
fi
```

### 第三步：Favicon 生成流程

#### 从 SVG 生成完整 Favicon 套件

```bash
#!/bin/bash
# favicon-generator.sh

SOURCE_FILE="logo.svg"  # 或 logo.png
OUTPUT_DIR="static/images/favicon"

mkdir -p "$OUTPUT_DIR"

# 1. 生成不同尺寸的 PNG
convert "$SOURCE_FILE" -resize 16x16 "$OUTPUT_DIR/favicon-16x16.png"
convert "$SOURCE_FILE" -resize 32x32 "$OUTPUT_DIR/favicon-32x32.png"
convert "$SOURCE_FILE" -resize 192x192 "$OUTPUT_DIR/android-chrome-192x192.png"
convert "$SOURCE_FILE" -resize 512x512 "$OUTPUT_DIR/android-chrome-512x512.png"

# 2. 生成 Apple Touch Icon
convert "$SOURCE_FILE" -resize 180x180 "$OUTPUT_DIR/apple-touch-icon.png"

# 3. 生成 ICO 文件（包含多个尺寸）
convert "$OUTPUT_DIR/favicon-16x16.png" \
        "$OUTPUT_DIR/favicon-32x32.png" \
        "$OUTPUT_DIR/favicon.ico"

# 4. 可选：优化 PNG
pngquant --quality=65-80 "$OUTPUT_DIR"/*.png --ext .png --force

echo "✅ Favicon 生成完成！"
```

#### 生成 manifest.json

```json
{
  "name": "您的应用名称",
  "short_name": "应用名",
  "description": "应用描述",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#000000",
  "icons": [
    {
      "src": "/static/images/favicon/android-chrome-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/static/images/favicon/android-chrome-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

#### 生成 browserconfig.xml (Windows)

```xml
<?xml version="1.0" encoding="utf-8"?>
<browserconfig>
    <msapplication>
        <tile>
            <square150x150logo src="/static/images/favicon/mstile-150x150.png"/>
            <TileColor>#000000</TileColor>
        </tile>
    </msapplication>
</browserconfig>
```

### 第四步：更新 HTML 引用

在 `<head>` 中添加完整的 Favicon 配置：

```html
<!-- Favicon -->
<link rel="icon" type="image/x-icon" href="/static/images/favicon/favicon.ico">
<link rel="icon" type="image/png" sizes="16x16" href="/static/images/favicon/favicon-16x16.png">
<link rel="icon" type="image/png" sizes="32x32" href="/static/images/favicon/favicon-32x32.png">

<!-- Apple Touch Icon -->
<link rel="apple-touch-icon" sizes="180x180" href="/static/images/favicon/apple-touch-icon.png">

<!-- Android Chrome -->
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#000000">

<!-- Microsoft -->
<meta name="msapplication-config" content="/browserconfig.xml">
<meta name="msapplication-TileColor" content="#000000">
```

### 第五步：Logo 多格式导出

```bash
#!/bin/bash
# logo-export.sh

SOURCE="logo.svg"
OUTPUT_DIR="static/images/logo"

mkdir -p "$OUTPUT_DIR"

# PNG 格式（不同尺寸）
convert "$SOURCE" -resize 200x200 "$OUTPUT_DIR/logo-200.png"
convert "$SOURCE" -resize 400x400 "$OUTPUT_DIR/logo-400.png"
convert "$SOURCE" -resize 800x800 "$OUTPUT_DIR/logo-800.png"

# WebP 格式（更小体积）
convert "$OUTPUT_DIR/logo-400.png" "$OUTPUT_DIR/logo-400.webp"

# 白色背景版本（用于深色模式）
convert "$SOURCE" -background white -flatten -resize 400x400 "$OUTPUT_DIR/logo-white-bg.png"

# 复制 SVG 原文件
cp "$SOURCE" "$OUTPUT_DIR/logo.svg"

echo "✅ Logo 导出完成！"
```

### 第六步：批量图片优化

```bash
#!/bin/bash
# optimize-images.sh

TARGET_DIR="${1:-.}"

echo "🔍 扫描图片文件..."

# 优化 PNG
find "$TARGET_DIR" -name "*.png" -type f | while read file; do
  echo "压缩: $file"
  pngquant --quality=65-80 "$file" --ext .png --force
done

# 优化 JPG
find "$TARGET_DIR" -name "*.jpg" -o -name "*.jpeg" -type f | while read file; do
  echo "压缩: $file"
  convert "$file" -quality 85 "$file"
done

# 转换为 WebP（可选）
find "$TARGET_DIR" -name "*.png" -o -name "*.jpg" -type f | while read file; do
  webp_file="${file%.*}.webp"
  if [ ! -f "$webp_file" ]; then
    echo "转换为 WebP: $file"
    cwebp -q 80 "$file" -o "$webp_file"
  fi
done

echo "✅ 图片优化完成！"
```

## 常见场景处理

### 场景 1: Favicon 不显示

**诊断步骤**：
```bash
# 1. 检查文件是否存在
ls -la static/images/favicon/favicon.ico
ls -la favicon.ico

# 2. 检查 HTML 引用
grep "favicon" index.html

# 3. 检查文件权限
chmod 644 static/images/favicon/*.png
chmod 644 static/images/favicon/*.ico

# 4. 测试浏览器缓存
# 提醒用户：Ctrl+F5 强制刷新或清除浏览器缓存
```

**修复方案**：
1. 确认文件路径正确
2. 添加或更新 HTML `<link>` 标签
3. 在文件名后添加版本号清除缓存：`favicon.ico?v=2`
4. 重启开发服务器

### 场景 2: Logo 尺寸不合适

```bash
# 检查当前 Logo 尺寸
identify logo.png
# 输出: logo.png PNG 1200x600 ...

# 计算合适的尺寸（保持宽高比）
# 如果 Logo 用于导航栏，建议高度 40-60px

convert logo.png -resize x50 logo-nav.png
# 高度 50px，宽度自动计算

# 或指定最大宽度
convert logo.png -resize 200x logo-nav.png
# 宽度最多 200px，高度自动
```

### 场景 3: 图片文件太大

```bash
# 检查图片大小
du -h *.png | sort -h

# 方案 1: 有损压缩（推荐）
pngquant --quality=60-80 large-image.png -o compressed.png
# 通常可减小 50-70%

# 方案 2: 调整尺寸
convert large-image.png -resize 50% smaller.png

# 方案 3: 转换为 WebP
cwebp -q 75 image.png -o image.webp
# 比 PNG 小 25-35%

# 方案 4: 使用 tinypng API (批量)
# https://tinypng.com/developers
```

### 场景 4: 需要响应式图片

生成多种尺寸并使用 `<picture>` 标签：

```bash
# 生成多尺寸
convert original.png -resize 400x banner-400.png
convert original.png -resize 800x banner-800.png
convert original.png -resize 1200x banner-1200.png
```

HTML 配置：
```html
<picture>
  <source media="(min-width: 1200px)" srcset="/images/banner-1200.webp" type="image/webp">
  <source media="(min-width: 800px)" srcset="/images/banner-800.webp" type="image/webp">
  <source media="(min-width: 400px)" srcset="/images/banner-400.webp" type="image/webp">
  <img src="/images/banner-800.png" alt="Banner">
</picture>
```

### 场景 5: SVG 优化

```bash
# 安装 SVGO
npm install -g svgo

# 优化 SVG
svgo logo.svg -o logo-optimized.svg

# 批量优化
svgo -f ./svg-icons -o ./svg-icons-optimized
```

## 标准目录结构

建议的图片资源组织方式：

```
static/images/
├── favicon/
│   ├── favicon.ico
│   ├── favicon-16x16.png
│   ├── favicon-32x32.png
│   ├── apple-touch-icon.png
│   ├── android-chrome-192x192.png
│   └── android-chrome-512x512.png
├── logo/
│   ├── logo.svg              # 原始矢量图
│   ├── logo-200.png
│   ├── logo-400.png
│   ├── logo-400.webp
│   └── logo-white-bg.png
├── icons/                    # UI 图标
│   ├── check.svg
│   ├── close.svg
│   └── menu.svg
└── banners/                  # Banner 图片
    ├── hero-1200.webp
    ├── hero-800.webp
    └── hero-400.webp
```

## 自动化脚本整合

创建一个完整的图片处理脚本：

```bash
#!/bin/bash
# process-all-images.sh

echo "🚀 开始处理图片资源..."

# 1. 生成 Favicon
if [ -f "logo.svg" ] || [ -f "logo.png" ]; then
  echo "📱 生成 Favicon..."
  bash favicon-generator.sh
fi

# 2. 导出 Logo
if [ -f "logo.svg" ]; then
  echo "🎨 导出 Logo..."
  bash logo-export.sh
fi

# 3. 优化所有图片
echo "⚡ 优化图片..."
bash optimize-images.sh static/images

# 4. 更新 HTML 引用
echo "📝 更新 HTML 配置..."
# 自动检测并更新 index.html

# 5. 生成资源清单
echo "📋 生成资源清单..."
cat > static/images/README.md << 'EOF'
# 图片资源说明

## Favicon
- favicon.ico: 通用图标
- favicon-16x16.png: 浏览器标签
- favicon-32x32.png: 快捷方式
- apple-touch-icon.png: iOS 主屏幕
- android-chrome-*.png: Android 主屏幕

## Logo
- logo.svg: 矢量原文件（可无限缩放）
- logo-200.png: 小尺寸（导航栏）
- logo-400.png: 中等尺寸（页脚）
- logo-800.png: 大尺寸（首页横幅）

## 使用建议
- 优先使用 WebP 格式（更小体积）
- 使用 SVG 用于图标和 Logo
- 大图片使用响应式加载
EOF

echo "✅ 所有图片处理完成！"
echo ""
echo "📁 生成的文件:"
find static/images -type f -name "*.png" -o -name "*.ico" -o -name "*.webp" | sort

echo ""
echo "💡 后续步骤:"
echo "1. 检查 HTML 中的 <link> 标签"
echo "2. 清除浏览器缓存测试"
echo "3. 提交到 Git"
```

## 性能优化建议

### 图片格式选择

| 场景 | 推荐格式 | 原因 |
|------|---------|------|
| Logo (矢量) | SVG | 可缩放，体积小 |
| Logo (位图) | PNG + WebP | 支持透明，WebP 更小 |
| Favicon | ICO + PNG | 兼容性最好 |
| 照片 | WebP + JPG | WebP 体积小 30% |
| 图标 | SVG | 清晰，可调色 |
| 大图背景 | WebP (响应式) | 按需加载 |

### 压缩质量建议

- **Logo/图标**: 无损压缩或 90+ 质量
- **产品图**: 80-85 质量
- **背景图**: 70-80 质量
- **缩略图**: 60-70 质量

### 懒加载配置

```html
<!-- 原生懒加载 -->
<img src="image.jpg" loading="lazy" alt="描述">

<!-- Vue 3 组件 -->
<template>
  <img
    v-lazy="imageSrc"
    :alt="alt"
  >
</template>
```

## 故障排除清单

```
✅ 检查清单：

1. 文件存在性
   [ ] favicon.ico 文件存在
   [ ] 路径正确（相对/绝对）
   [ ] 文件权限可读 (644)

2. HTML 配置
   [ ] <link> 标签正确
   [ ] 路径使用正确（/static/ 或 ./）
   [ ] 没有拼写错误

3. 缓存问题
   [ ] 清除浏览器缓存
   [ ] 添加版本号 (?v=1)
   [ ] 硬刷新 (Ctrl+F5)

4. 服务器配置
   [ ] 静态文件服务正常
   [ ] MIME 类型正确
   [ ] CORS 允许（如果跨域）

5. 图片质量
   [ ] 文件未损坏
   [ ] 尺寸合适
   [ ] 格式正确
```

## 输出报告

```
✅ 图片资源处理完成
====================

📊 处理统计:
  - Favicon: 6 个文件（75 KB）
  - Logo: 5 个文件（180 KB）
  - 优化图片: 23 个文件
  - 总节省: 2.3 MB (压缩率 62%)

📁 生成文件:
  static/images/favicon/
  static/images/logo/
  manifest.json
  browserconfig.xml

🔗 已更新配置:
  - index.html (添加 Favicon 引用)
  - manifest.json (PWA 配置)

💡 建议:
  - 清除浏览器缓存后测试
  - 考虑使用 CDN 加速图片加载
  - 定期检查图片体积

⏱️ 耗时: 8.5 秒
```

## 注意事项

1. **备份原文件**：处理前自动备份原始文件
2. **版本控制**：建议将优化后的图片提交到 Git
3. **命名规范**：使用语义化的文件名
4. **路径一致**：统一使用 `/static/images/` 或类似路径
5. **测试验证**：在不同浏览器和设备上测试显示效果
