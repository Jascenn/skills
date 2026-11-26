---
name: dev-environment
description: "Local development environment tools: diagnose startup failures and port conflicts, Docker container management, Vercel deployment, Playwright web app testing, sample/test data generation, web image asset processing (favicon, logo, icon), and OpenClaw backup/restore. Use when: localhost not accessible, service won't start, port conflict, Docker operations, deploy to Vercel, test web app with Playwright, generate test data, process favicon/logo/icons, backup OpenClaw, restore from backup, Logo不显示, Favicon更新, 图标处理, 图片优化, 服务启动不了, 端口被占用, 生成测试数据."
---

# dev-environment — Local Development Tools

## § Local Dev Diagnostics (local-dev-diagnostics)

Diagnose and fix common local development problems.

**Triggers:** localhost无法访问, 服务器启动失败, 端口冲突, 页面空白, service won't start, port conflict

**Diagnostic steps:**
```bash
# Check port usage
lsof -i :3000
netstat -tulpn | grep 3000

# Kill process on port
kill -9 $(lsof -t -i:3000)

# Check service status
ps aux | grep node
systemctl status nginx

# Check logs
tail -f /var/log/nginx/error.log
journalctl -u myservice -f

# Verify env vars
env | grep -E "NODE_ENV|DATABASE_URL|PORT"

# Check Node/Python versions
node --version && npm --version
python --version && pip --version
```

**Common fixes:**
- Port conflict → kill process or change port in config
- Missing env vars → check `.env` file exists and is loaded
- DB not running → `brew services start postgresql` / `docker start db`
- Node modules missing → `rm -rf node_modules && npm install`

---

## § Docker (docker-essentials)

Essential Docker commands for container and image management.

```bash
# Run container
docker run -d -p 8080:80 --name myapp nginx
docker run -it ubuntu bash                    # interactive

# Container lifecycle
docker start/stop/restart myapp
docker rm myapp                               # remove stopped container
docker rm -f myapp                            # force remove running

# Logs and exec
docker logs -f myapp
docker exec -it myapp bash

# Images
docker images
docker pull nginx:latest
docker build -t myapp:latest .
docker rmi myapp:latest

# Docker Compose
docker compose up -d
docker compose down
docker compose logs -f
docker compose ps

# Cleanup
docker system prune -f                        # remove unused resources
docker volume prune -f
```

---

## § Vercel Deployment (vercel-deploy)

Deploy and manage Vercel projects.

```bash
# Install CLI
npm i -g vercel

# Deploy
vercel                                        # preview deployment
vercel --prod                                 # production deployment

# Environment variables
vercel env add VARIABLE_NAME                  # add env var
vercel env ls                                 # list env vars
vercel env rm VARIABLE_NAME                   # remove env var

# Logs and status
vercel logs                                   # recent logs
vercel inspect <deployment-url>               # deployment details

# Domains
vercel domains ls
vercel domains add example.com
```

**Config file** (`vercel.json`):
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [{"source": "/(.*)", "destination": "/index.html"}]
}
```

---

## § Web App Testing with Playwright (webapp-testing)

Test local web applications using Python Playwright.

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("http://localhost:3000")
    
    # Verify element
    assert page.locator("h1").text_content() == "Expected Title"
    
    # Screenshot
    page.screenshot(path="screenshot.png")
    
    # Click and fill
    page.click("button#submit")
    page.fill("input[name=email]", "test@example.com")
    
    # Wait for navigation
    page.wait_for_url("**/dashboard")
    
    browser.close()
```

**Helper:** `scripts/with_server.py` manages server lifecycle for tests.

**Install:** `pip install playwright && playwright install chromium`

---

## § Sample/Test Data Generation (sample-data-generator)

Generate realistic Chinese business data for development and testing.

**Triggers:** 生成测试数据, 添加示例数据, 没有数据展示, 需要演示数据

**Process:**
1. Read database schema (SQL DDL or ORM models)
2. Analyze field names and types semantically
3. Generate realistic data respecting constraints (FK, unique, not null)

**Supported field types:**
- 姓名 (Chinese names), 手机号 (phone), 邮箱 (email), 地址 (address)
- 公司名 (company), 产品名 (product), 金额 (amount), 日期 (date)
- Status fields, enum values, boolean flags

```python
# Example output for user table
INSERT INTO users (name, phone, email, address) VALUES
('张伟', '13812345678', 'zhangwei@example.com', '北京市朝阳区建国路88号'),
('李娜', '13987654321', 'lina@example.com', '上海市浦东新区陆家嘴环路1000号');
```

---

## § Web Image Asset Processing (image-asset-processor)

Automate website image asset processing: favicon, logo, icon format conversion, multi-size generation, compression.

**Triggers:** Logo不显示, Favicon更新, 图标处理, 图片优化, favicon generation, logo processing

### Favicon Complete Solution

```bash
# SVG → PNG → ICO pipeline
convert logo.svg -resize 16x16 favicon-16.png
convert logo.svg -resize 32x32 favicon-32.png
convert logo.svg -resize 192x192 favicon-192.png
convert logo.svg -resize 512x512 favicon-512.png
convert favicon-16.png favicon-32.png favicon.ico

# Apple Touch Icon
convert logo.svg -resize 180x180 apple-touch-icon.png
```

### Logo Multi-Format Export

```bash
# SVG → PNG/WebP
convert logo.svg -resize 200x200 logo.png
cwebp logo.png -o logo.webp

# Compression
pngquant --quality=80-90 logo.png
```

### HTML References

```html
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
```

### site.webmanifest

```json
{
  "icons": [
    {"src": "/favicon-192.png", "sizes": "192x192", "type": "image/png"},
    {"src": "/favicon-512.png", "sizes": "512x512", "type": "image/png"}
  ]
}
```

---

## § OpenClaw Backup & Restore (openclaw-backup)

Backup and restore OpenClaw configuration, credentials, and workspace.

```bash
# Create backup
./scripts/backup.sh [backup_dir]   # default: ~/openclaw-backups/
# Output: openclaw-YYYY-MM-DD_HHMM.tar.gz
```

**Backed up:** `openclaw.json`, `credentials/`, `agents/`, `workspace/`, `telegram/`, `cron/`
**Excluded:** `completions/` (cache), `*.log`

```bash
# Quick restore
openclaw gateway stop
mv ~/.openclaw ~/.openclaw-old
tar -xzf ~/openclaw-backups/openclaw-YYYY-MM-DD_HHMM.tar.gz -C ~
openclaw gateway start
```

**Daily cron backup:**
```json
{
  "name": "daily-backup",
  "schedule": {"kind": "cron", "expr": "0 3 * * *", "tz": "UTC"},
  "payload": {"kind": "agentTurn", "message": "Run ~/.openclaw/backup.sh and report result to user."},
  "sessionTarget": "isolated",
  "delivery": {"mode": "announce"}
}
```
