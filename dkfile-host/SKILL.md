---
name: dkfile-host
description: 把本地 HTML 文件/产物发布到 DKFile（dkfile.net）免费托管并拿到可分享公网链接；查询已托管文件、配额与可达性。当用户要"发布/上线/托管 HTML"、"生成分享链接"、"传到 dkfile"、"看已上传的页面"时使用。
---

# DKFile 托管（dkfile.net）

免费 HTML 托管服务。只收单文件 `.html` / `.htm`（≤100 MB），**同名覆盖**且外链 URL 不变 —— 适合报告、看板、单页 demo 的迭代发布。

## 何时用

- 用户做了一个 HTML 产物（报告 / dashboard / 单页工具），想拿到**公网可访问的链接**分享。
- 需要列出/核对已托管页面与剩余配额。
- 需要把发布物做迭代更新（重新上传同名文件即可，链接不变）。

不适用：需要 JS / CSS / 图片等多资源目录的项目 —— 单文件接口会拒。那类走「文件夹项目」，若账号未开通文件夹项目权限会报 `1312 文件夹项目未激活`，需先在 dkfile 站点申请。

## 工具

CLI：`~/.dkfile/dkfile`（真实实现为 `~/.dkfile/dkfile.py`，纯标准库）
密钥：`~/.dkfile/config.json`（600 权限，字段 `api_key` / `base_url` / `username`）；亦可用 `DKFILES_KEY` 环境变量覆盖。
主文档：`~/.dkfile/README.md`（如有外部文档副本同步约定，修改主文档后记得同步）。

```bash
~/.dkfile/dkfile info                       # 账号、配额、上传限制
~/.dkfile/dkfile ls --page 1 --per-page 20  # 已托管文件列表
~/.dkfile/dkfile upload page.html --project "项目名" --desc "说明"
~/.dkfile/dkfile check <url|文件名>          # 验证公网可达性
~/.dkfile/dkfile <cmd> ... --json            # 输出原始 JSON
```

## 标准发布流程

1. 写好本地 HTML（放工作区，不要放个人目录）。
2. `~/.dkfile/dkfile upload <file> --project "<项目名>"`
3. 看输出里的 `地址` 与 `预热` 行；把 URL 给用户。
4. 改动后重传同名文件即可，URL 不变（返回 `is_update: true`）。

## 必须知道的坑（实测）

1. **必须带浏览器 User-Agent。** 默认 `python-urllib` UA 会被 Cloudflare 以 HTTP 403 + `error code 1010` 拒绝。CLI 已内置 Chrome UA，自写脚本时务必带上。
2. **新文件首次公网读取会超时。** 上传后立刻匿名抓取，常常连续 3~4 次 35s 超时，之后才 200（进入缓存）。**这是回源慢，不是上传失败** —— 不要据此判定失败或重复上传。CLI 的 `预热` 步骤已自动解决。
3. **站点本身有间歇性 522 / 连接超时**（Cloudflare 回源失败），API 与公网页面都会遇到。所有请求需重试（CLI 内置 4 次指数退避）。
4. **认证头是 `Authorization: Bearer <key>`**，key 形如 `dkfile_<64位hex>`。不带 `Bearer` 前缀会得到 `401 {"error_code":"UNAUTHORIZED","message":"请先登录"}`。
5. **速率限制**：响应头 `X-RateLimit-Remaining/Limit/Window`；超限返回 `429` + `error_code 1203`（小时）/`1204`（分钟），响应含 `retry_after`（秒）。
6. `GET /dkfile_api/files` 的 `total` 与 `upload/info` 的 `current_file_count` **可能不一致**（实测 22 vs 24），以 `info` 为准。
7. 上传是 `multipart/form-data`，字段 `file` + 可选 `project_name` / `description`。

## 端点速查（已实测）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/dkfile_api/upload/info` | 配额、限制、账号 |
| GET | `/dkfile_api/files?page=&per_page=` | 文件列表（分页） |
| POST | `/dkfile_api/upload` | 上传/覆盖单个 HTML |
| GET | `/api/folders/{name}/files` | 文件夹项目（需权限，未开通时返回 1312） |
| POST | `/api/folders/{name}/batch_upload` | 批量上传（需权限） |
| POST | `/api/folders/{name}/publish` | 发布文件夹项目（需权限） |

图床 / 数据托管 API 走 **Session Cookie**，不支持 API Key，本 CLI 未覆盖。

文档：<https://dkfile.net/api> · 错误码全表：<https://dkfile.net/api/error-codes>
