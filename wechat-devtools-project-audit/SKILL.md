---
name: wechat-devtools-project-audit
description: "用微信开发者工具 CLI 批量打开本地小程序/小游戏项目，并从工具日志与项目状态记录中提取真实编译结果。当用户说「打开我的小程序看看」「小程序体检」「哪些小程序能跑」「小程序给我个报告」，或需要判断某个微信项目为什么打不开、编译失败时使用。含 CLI 调用方式、沙箱必须关、编译结果的两个取证来源、以及「success 日志不可信」等关键陷阱。"
---

# 微信小程序项目体检与批量打开

## 核心原则

1. **不要靠静态分析下「能跑/不能跑」的结论。** 实测编译结果才是证据。静态检查（页面文件是否齐全）只能作为预筛，不能当结论。
2. **`simulator launch success` 是假信号。** 编译失败时工具**照样**会写 `simulator launch success`（只是渲染出错误页）。唯一可信的失败判据是 `simulator launch catch error ... CustomError: ...`。
3. **必须关沙箱。** CLI 要通过本地 HTTP 端口跟 IDE 通信，沙箱会拦截，表现为 `✖ IDE may already started at port xxxxx, trying to connect` → `✖ #initialize-error: wait IDE port timeout`。这不是项目问题，是沙箱问题。
4. **先找全项目，再动手。** 用户说的「我的小程序」可能只是其中一个，实际往往散落多处。先全盘扫描再问或再打开。

## 第 0 步：找全所有项目

```bash
# 常见位置：~/WeChatProjects、~/Development/**/miniprogram
find ~ -maxdepth 6 -name "project.config.json" -not -path "*/node_modules/*" 2>/dev/null
```

另外，**IDE 自己的历史记录里藏着更多线索**（见第 3 步的 localstorage），里面会列出用户最近开过的所有项目路径，包括已被移动的失效路径。

## 第 1 步：CLI 打开项目

```bash
CLI=/Applications/wechatwebdevtools.app/Contents/MacOS/cli
"$CLI" open --project "/绝对/路径" --lang zh
```

- **必须设 `dangerouslyDisableSandbox: true`**，否则必然 port timeout。
- 成功输出：`✔ IDE 已启动，HTTP 服务地址 http://127.0.0.1:xxxxx` + `✔ open`。
- IDE 未启动时 CLI 会自动拉起它（较慢，给足超时）。
- 一次开多个项目没问题，IDE 会开多个窗口。开完 `sleep 10~15` 再读日志。
- CLI 其他可用命令：`preview`、`upload`、`build-npm`、`auto`、`close`、`quit`、`islogin`。

## 第 2 步：静态预筛（快，但不能当结论）

用 Python（**不要用 shell glob**，路径含空格和中文会断）检查：
- `app.json` 里每个 `pages[]` 是否有对应 `.js` 和 `.wxml`
- `subpackages`/`subPackages` 里每个页面同样检查
- `tabBar.list[].iconPath` / `selectedIconPath` 文件是否存在
- 没有 `app.json` 的目录 = 根本不是小程序（常见于只有 `index.html` 的 H5）

## 第 3 步：取证——两个可信来源

### 来源 A：运行日志（最直接）

目录：`~/Library/Application Support/微信开发者工具/<hash>/WeappLog/logs/*.log`
（`<hash>` 每次安装/会话可能不同，用 glob 匹配 `微信开发者工具/*/WeappLog/logs`）

每个项目一个日志文件。关键行：

```
[ERROR] simulator launch catch error CustomError: app.json: 未找到 ["pages"][0] 对应的 pages/example/intro.wxml 文件
[ERROR] simulator launch catch error CustomError: app.json: 在项目根目录未找到 app.json
[INFO]  simulator launch success, set src http://127.0.0.1:xxxxx/appservice/mainframe
```

用 Python 遍历，正则提取 `dirpath = (/Users/\S+)` 定位项目，`CustomError: ([^\n"]{0,120})` 提错误。
**忽略**这些噪音错误（与项目无关）：`需要重新登录`、`access_token missing`、`41002 appid missing`、`ideplugin ... manifest.json not installed`。

### 来源 B：IDE 项目状态记录（能拿到结构化结论）

目录：`~/Library/Application Support/微信开发者工具/<hash>/WeappLocalData/localstorage_*.json`

搜 `"projectpath"`，每条附近有：
- `"extjson":{"error":"Error: ..."}` ← **编译错误，空则无错**
- `"compileType":"weapp" | "game"`
- `"appid"`
- `"miniappAttr":{"baseresponse":{"errcode":...,"errmsg":...}}` ← appid 校验结果

这个来源能一次性列出所有项目的编译状态，比逐条翻日志快。

## 已知陷阱

| 现象 | 真因 | 处理 |
|---|---|---|
| `wait IDE port timeout` | 沙箱拦截本地端口 | 加 `dangerouslyDisableSandbox: true` |
| 所有项目都 `errcode=40013 invalid appid` | **工具未登录** | 提醒用户先扫码登录，否则预览/上传/真机调试全废 |
| 小游戏报 `在项目根目录未找到 app.json` | CLI 把它当小程序编译（尽管 `compileType: "game"` 正确） | 项目本身没坏，让用户在工具里以「小游戏」类型手动导入 |
| 日志 `success` 但页面报错 | success 不代表编译通过 | 只看 `CustomError` |
| shell 循环处理不了路径 | 路径含空格/中文 | 改用 Python |

## 输出建议

报告按「能跑 / 不能跑」分组，每个项目给出：路径、类型、appid、页面数、代码量、**实测编译结论 + 原始错误文本**、git 状态（未提交改动量）。
跨项目问题单独成节（appid 复用、工具未登录、目录分散、改动积压）。

## 交付提醒

- 打开项目会真实弹出 IDE 窗口，属于用户可见动作，用户明确说「打开」时才做。
- 不要代替用户做 git 提交/回滚等写操作，先报告再等指令。
