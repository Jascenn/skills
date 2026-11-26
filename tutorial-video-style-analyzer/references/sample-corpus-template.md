# Tutorial Reference Corpus Template

Use this template when abstracting a reusable style system across multiple reference tutorial or screen-recording demo videos. Replace the sample entries with the actual videos in your reference folder.

## Sampled Videos

| Video | Duration | Format Notes | Role In Corpus |
| --- | ---: | --- | --- |
| `01-feature-comparison-demo.mp4` | ~90s | 16:9 / 30fps | Short proof/demo, before-vs-after comparison |
| `02-macos-setup-walkthrough.mp4` | ~180s | 16:9 / 60fps | Desktop software configuration walkthrough |
| `03-account-and-api-switching.mp4` | ~300s | 16:9 / 60fps | Longer configuration and troubleshooting tutorial |
| `04-environment-install-guide.mp4` | ~320s | 16:9 / 60fps | Installation and command-line validation |

Use subtitles/SRT files to extract copy rhythm and pacing beats rather than copying filler words verbatim.

## Cross-Video Style Pattern: 真实操作证明型教程

One-line definition:

```text
用真实录屏把一个技术流程从入口、操作、验证到结果走完，让观众相信“我照着做也能完成”。
```

### Shared Narrative Structure

```text
演示主题 -> 打开入口/教程/系统 -> 输入或配置关键参数 -> 执行步骤 -> 等待/处理异常 -> 展示成功状态 -> 用页面状态或命令结果验证
```

### Editing & Subtitle Rules

- Use real screen recording as primary evidence, with zoom-ins on key fields, menu paths, or command outputs.
- Use split-screen when comparing two modes or before/after states.
- Keep captions short (`动作词 + 目标对象`, e.g. `配置 API Key`, `验证环境`, `确认运行成功`) and avoid covering the demonstrated UI button or input field.
- Favor first-person, step-by-step live spoken beats (`我们来演示一下…` / `然后点击…` / `这样就已经配置好了`).
