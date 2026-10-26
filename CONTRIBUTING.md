# 贡献指南 Contributing

`Skills`：面向内容发布与工作流自动化的可复用 Skill 集合。 小改动可以直接提 PR；涉及对外行为、数据结构、发布流程或批量重构时，请先开 Issue 对齐范围。

## 本地验证

```bash
python3 -m py_compile wechat-mp-publisher/scripts/*.py
python3 -m py_compile xhs-pipeline-lingyi/xhs_pipeline_lingyi.py
```

如果 README 的安装步骤无法照做，请把它当作 bug 提交。不要把“在我机器上能跑”当作验证完成。

## 分支与提交

- 分支名使用 `feat/`、`fix/`、`docs/`、`refactor/`、`chore/` 前缀和 kebab-case 描述。
- `main` 只接受 PR；不要直接推送，也不要 force push 已共享的分支。
- 提交标题使用 Conventional Commits，例如 `fix(cli): preserve backup before overwrite`。
- 一个 PR 只解决一个问题。行为变化、格式化、依赖升级不要混在同一次提交里。
- 默认建议 squash merge，让一个 PR 对应 `main` 上的一条可回溯记录。

## 本项目的安全边界

- 不要提交微信公众号 AppSecret、飞书 token、小红书登录态、浏览器 Cookie、用户稿件或真实发布日志。
- 示例配置只能使用占位值；新增初始化向导时不得把用户填写的密钥回写到版本控制内的文件。
- 修改发布、定时、删除或覆盖行为时必须提供预览或 dry-run，并在 README 写清失败后的回滚方式。
- 保留每个子 Skill 自己的许可证与第三方来源说明；不能用一个顶层许可证覆盖来源不明的代码或素材。

## PR 最少要写什么

1. 为什么需要改，关联的 Issue 或具体问题。
2. 改了什么，以及明确没有改什么。
3. 陌生人能照着执行的验证命令和结果。
4. 影响面与回滚方式；涉及页面时附桌面和移动端截图。

## 审查与合并

单人维护时，PR 的价值是给未来的自己留下“当时为什么这样做”。评论建议标注 `【阻塞】`、`【建议】` 或 `【nit】`。安全漏洞不要开公开 Issue，请按 [SECURITY.md](SECURITY.md) 私下报告。

## 范围

本项目主要覆盖：微信公众号发布、小红书流水线、飞书联动、初始化脚本和 Skill 文档。
