# Skills

凌一的 Skills 集合 - 通用工具和自动化脚本

## Skills 列表

### lingyi-mac-annual-apps

年度 Mac 常用软件扫描、2400×1350 高清海报生成、离线编辑器与 [MacStack · lingyi](https://mac.lingyi.tools) 社区一键发布工具

**功能：**
- 优先读取 macOS 屏幕使用时间（`knowledgeC.db`）真实前台时长，自动回退 ActivityWatch 与 Spotlight 活跃天数
- 原生提取 `.app` 高清透明图标，自动去噪与中英文分类，支持 AI CLI 检测
- 零依赖 Swift 海报渲染器（支持杂志宋体 / 无衬线、自动桌面壁纸、背景高斯模糊、角标与署名）
- 自带离线 Canvas 2D 交互编辑器，支持一键发布至 `https://mac.lingyi.tools` 及本地凭证撤回

**一键安装：**
```bash
npx skills add Jascenn/skills --skill lingyi-mac-annual-apps
```

[查看详细文档](./lingyi-mac-annual-apps/SKILL.md)

### xhs-pipeline-lingyi

小红书内容发布完整流水线

**功能：**
- 自动生图（可选，基于 DashScope）
- 草稿写入小红书（标题/正文/标签/定时/原创）
- 飞书内容库记录管理（可选）
- 支持从飞书内容库读取内容发布

**快速开始：**
```bash
python3 xhs-pipeline-lingyi/xhs_pipeline_lingyi.py --setup
```

[查看详细文档](./xhs-pipeline-lingyi/README.md)

### wechat-mp-publisher

通用微信公众号创作与发布工具

**功能：**
- 话题创作（生成标题+大纲）
- 素材整理
- 推送草稿到公众号
- 保存到飞书 Base（可选）

**快速开始：**
```bash
cd wechat-mp-publisher/scripts
python3 init.py
```

[查看详细文档](./wechat-mp-publisher/README.md)

## 安装

```bash
git clone https://github.com/Jascenn/skills.git
```

## 贡献与安全

欢迎提交 PR 或 Issue。

- 参与开发前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。
- 安全问题请按 [SECURITY.md](SECURITY.md) 私下报告，不要开公开 Issue。

## 许可证

本项目原创代码采用 [MIT License](LICENSE)。第三方依赖、上游项目与外部素材继续遵循各自许可证。
