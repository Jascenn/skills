# Skills

凌一的公开 Skills 集合 — 通用开发工具、自动化流水线与 macOS/AI 工程实战经验沉淀（共 24 个脱敏通用 Skill）。

> 本仓库所有技能均已完成脱敏与去凭证处理，不包含任何个人密钥、私密配置或环境硬编码路径。

## Skills 目录

### 1. macOS / AI 工具链工程实战（12 个）

| Skill | 定位 | 入口 |
|---|---|---|
| `ai-tool-state-forensics` | 排查 macOS AI 工具状态故障、DB 悬空记录、二进制能力探测与 frontmatter 诊断 | [SKILL.md](./ai-tool-state-forensics/SKILL.md) |
| `disk-cleanup-rollback` | macOS 安全磁盘空间回收与 `tar` 全量可回滚删除规程 | [SKILL.md](./disk-cleanup-rollback/SKILL.md) |
| `skill-dir-symlink-dedup` | 多 AI 工具 skills 目录安全软链接去重与校验规程 | [SKILL.md](./skill-dir-symlink-dedup/SKILL.md) |
| `obsidian-frontmatter-repair` | 体检并批量修复 Obsidian / Markdown 库损坏的 YAML frontmatter | [SKILL.md](./obsidian-frontmatter-repair/SKILL.md) |
| `thirdparty-skill-install` | 多注册中心检索、源码安全审计与第三方 Skill 渲染落盘流程 | [SKILL.md](./thirdparty-skill-install/SKILL.md) |
| `notion-via-ntn` | 用 Notion 官方 CLI `ntn` 经环境变量代理稳定读写数据库与排查陷阱 | [SKILL.md](./notion-via-ntn/SKILL.md) |
| `dkfile-host` | 单文件 HTML 托管发布（DKFile CLI）与公网可达性预热验证 | [SKILL.md](./dkfile-host/SKILL.md) |
| `static-html-domstub-test` | 无框架单文件 HTML 应用的最小 DOM 桩回归测试与静默故障清单 | [SKILL.md](./static-html-domstub-test/SKILL.md) |
| `web-seo-perf-audit` | 线上站点响应头、压缩率、SEO 元数据、多语言与首屏负载实测审计 | [SKILL.md](./web-seo-perf-audit/SKILL.md) |
| `chrome-extension-release` | Chrome / Edge MV3 扩展发版编排、清单校验与商店提交手册生成 | [SKILL.md](./chrome-extension-release/SKILL.md) |
| `wechat-devtools-project-audit` | 微信开发者工具 CLI 批量编译取证与日志错误提取 | [SKILL.md](./wechat-devtools-project-audit/SKILL.md) |
| `wechat-miniapp-toolkit` | 微信小程序开发者工具 CLI 操作、静态体检与资源引用完整性校验 | [SKILL.md](./wechat-miniapp-toolkit/SKILL.md) |

### 2. 内容创作与桌面工具（5 个）

| Skill | 定位 | 入口 |
|---|---|---|
| `lingyi-mac-annual-apps` | 年度 Mac 常用软件扫描、2400×1350 海报渲染与交互编辑（支持发布 [MacStack](https://mac.lingyi.tools)） | [SKILL.md](./lingyi-mac-annual-apps/SKILL.md) |
| `wechat-mp-publisher` | 通用微信公众号创作、HTML 模板排版与草稿推送工具 | [SKILL.md](./wechat-mp-publisher/SKILL.md) |
| `xhs-pipeline-lingyi` | 小红书内容发布流水线（生图、草稿写入、飞书内容库联动） | [SKILL.md](./xhs-pipeline-lingyi/SKILL.md) |
| `tutorial-video-style-analyzer` | 从参考教程/录屏视频抽象可复用的剪辑、文案与字幕风格体系 | [SKILL.md](./tutorial-video-style-analyzer/SKILL.md) |
| `image-generation` | 多后端 AI 生图与配图指引（阿里百炼 `qwen-image-2.0` / Nano Banana Pro） | [SKILL.md](./image-generation/SKILL.md) |

### 3. 通用全栈开发与调试工具（7 个）

| Skill | 定位 | 入口 |
|---|---|---|
| `vue-fullstack-init` | Vue 3 + Element Plus + Node.js/Spring Boot 全栈项目初始化指南 | [SKILL.md](./vue-fullstack-init/SKILL.md) |
| `miniapp-fullstack-guide` | 微信小程序全栈开发向导（架构、支付接入、提审与 CI/CD） | [SKILL.md](./miniapp-fullstack-guide/SKILL.md) |
| `ai-api-debugger` | AI 模型 API 连通性、认证与请求参数快速诊断 | [SKILL.md](./ai-api-debugger/SKILL.md) |
| `local-dev-diagnostics` | 本地开发环境启动失败、端口占用与前后端联调排查 | [SKILL.md](./local-dev-diagnostics/SKILL.md) |
| `image-asset-processor` | 网站 Favicon、Logo 多尺寸生成、格式转换与压缩优化 | [SKILL.md](./image-asset-processor/SKILL.md) |
| `sample-data-generator` | 根据表结构生成符合业务语义的中文测试数据（SQL / JSON / CSV） | [SKILL.md](./sample-data-generator/SKILL.md) |
| `dev-environment` | 本地开发调试、Docker、Vercel、Playwright 测试与环境备份速查 | [SKILL.md](./dev-environment/SKILL.md) |

## 安装

单个安装（通过 `skills` CLI）：

```bash
npx skills add Jascenn/skills --skill <skill-name>
```

或全量克隆到本地并通过软链接接入各类 AI 客户端：

```bash
git clone https://github.com/Jascenn/skills.git
```

## 贡献与安全

欢迎提交 PR 或 Issue。

- 参与开发前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。
- 安全问题请按 [SECURITY.md](SECURITY.md) 私下报告，不要开公开 Issue。

## 许可证

本项目原创代码采用 [MIT License](LICENSE)。第三方依赖、上游项目与外部素材继续遵循各自许可证。
