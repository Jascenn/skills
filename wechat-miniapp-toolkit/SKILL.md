---
name: wechat-miniapp-toolkit
description: 微信小程序项目的本地工具箱——用微信开发者工具 CLI 打开/关闭/预览/上传项目，以及对小程序项目做静态体检（配置解析、包体积、页面完整性、组件与图片引用校验、隐私合规扫描）。当用户说"打开我的小程序"、"在开发者工具里看看"、"小程序体检/出份体检报告"、"清理冗余的小程序项目"、"检查小程序能不能上线"时使用。
---

# 微信小程序工具箱

两块能力：**① 开发者工具 CLI 操作**、**② 小程序静态体检**。

## 一、先定位项目

小程序项目的特征：目录下有 `project.config.json`（含 appid）+ `app.json`（含 pages）。

```bash
find ~ -maxdepth 6 -name "project.config.json" -not -path "*/node_modules/*" -not -path "*/Library/*" 2>/dev/null
```

读 `project.config.json` 拿 appid / projectname / libVersion / miniprogramRoot；读 `app.json` 拿 pages / tabBar / subPackages。

**关键判断**：
- 多个项目可能**共用同一 AppID**（同一账号的不同迭代副本）。按 `git log -1` 时间、`app.json` 的
  `navigationBarTitleText`、`pages` 内容区分主力与副本——停在模板状态的那个通常是副本。
- 目录里**没有 `app.json` 就不是小程序**（多半是 Web HTML 原型，`app.js` 里写的是 `class Xxx` 而非 `App({})`）。

## 二、开发者工具 CLI

```bash
CLI=/Applications/wechatwebdevtools.app/Contents/MacOS/cli
```

| 命令 | 用途 |
|---|---|
| `open --project <路径>` | 打开项目；IDE 未启动会自动拉起 |
| `close --project <路径> --port <端口>` | 关闭项目窗口 |
| `preview --project <路径>` | 生成预览二维码 |
| `upload --project <路径> -v <版本> -d <描述>` | 上传代码 |
| `build-npm --project <路径>` | 构建 npm |
| `login` / `islogin` | 登录状态 |
| `open-other` / `cache` / `quit` | 其他项目 / 清缓存 / 退出 IDE |
| `cloud` | CloudBase 相关命令 |

统一加 `--lang zh` 让输出中文。

### ⚠️ 端口坑（必读）
`close` **必须带当前实际端口**：
- 不带 `--port` → 报 `wait IDE port timeout`
- 带过期端口 → 报「IDE 已启动并在监听 `<新端口>`，需要重启才能使用端口 `<旧端口>`」

正确姿势：先执行一次 `open`，从返回的 `✔ IDE 已启动，HTTP 服务地址 http://127.0.0.1:<port>`
抄下端口，再用它 `close`。**端口每次 IDE 重启都会变**，不要复用旧值。

### 打开多个项目
逐个 `open`（IDE 是单例，串行执行，不要并发）。CLI 每次打印的是同一个端口，属正常。

### 工具的项目列表与缓存（排查僵尸条目）
工具把项目列表存在 `~/Library/Application Support/微信开发者工具/<hash>/WeappLocalData/`：
- `hash_key_map_2.json` 是 key→hash 映射表，找 `reduxPersist:projectList` 拿到对应 hash
- 对应文件 `localstorage_<hash>.json` 即项目列表，每条含 `projectPath`

**目录重构后（路径变了）旧记录会残留**，启动页点开报「目录不存在」，工具不会自动清。
用这条命令列出有效/失效：

```bash
python3 - <<'EOF'
import json, os, glob
base = os.path.expanduser('~/Library/Application Support/微信开发者工具')
m = json.load(open(glob.glob(base + '/*/WeappLocalData/hash_key_map_2.json')[0]))
h = m['reduxPersist:projectList']
d = json.load(open(glob.glob(base + f'/*/WeappLocalData/localstorage_{h}.json')[0]))
for k, v in d.items():
    p = v.get('projectPath', k)
    print(('  存在  ' if os.path.exists(p) else '  失效  ') + p)
EOF
```

**清理方式**：`cli quit` 退出工具 → 备份该 json → 删掉 `projectPath` 不存在的条目 → 用户重新打开工具。
⚠️ 工具运行时会用内存副本覆盖文件，**必须先 quit 再改**，并且要先备份。

**缓存体积**：`du -sh "<工具数据目录>/<hash>"/* | sort -rh`。
`WeappCache` 可清（`cli cache` 或删掉后自动重建）；`WeappApplication`（基础库）、
`WeappVendor`、`WeappPlugin` 是运行依赖，**别动**。整个数据目录常见 1–2 GB 量级，属正常。

### 退出工具的正确姿势
优先 `cli quit --port <当前端口>`。若 quit 后进程仍在（`pgrep -fl wechatwebdevtools` 有输出），
用 `pkill -f wechatwebdevtools` 兜底。
⚠️ 本环境 **AppleScript 控制应用被权限拦截**（`osascript -e 'tell application ... to quit'`
报 `privilege violation (-10004)`），不要指望 osascript，直接用 pkill。

### ⚠️ IDE 端口每次启动都会变
反复 open/quit 时端口会连续更换（实测一次会话里见过 62801 → 33647 → 27947 → 57397）。
CLI 报「IDE 已启动并在监听 `<新端口>`，需要重启才能使用端口 `<旧端口>`」时，
**用它提示的新端口重试**即可成功，不要死磕旧端口。
启动期间根路径返回 502 属正常过渡态，服务就绪后返回 404。

## 三、静态体检

两个脚本，接受任意多个项目路径：

```bash
python3 scripts/healthcheck.py <项目路径> [<项目路径> ...]   # 配置 / 体积 / 结构 / 代码扫描
python3 scripts/refcheck.py    <项目路径> [<项目路径> ...]   # 组件 / 图片 / 路由 引用完整性
```

`healthcheck.py` 同时把原始数据存成 `healthcheck.json`，采集项：appid、页面数与分包、
tabBar、`__usePrivacyCheck__`、urlCheck、上传包估算、大文件 Top10、缺失页面文件、孤立页面、
TODO / console.log 计数、疑似密钥、外部域名、依赖、git 状态。

`refcheck.py` 输出三类失效引用：组件路径不可解析、图片资源缺失、页面路由未注册。

### 最有价值的三个检查项
1. **`app.json` 声明页面 vs 实际文件**——声明了但文件不存在 → 打开即编译失败（最高频的 P0）。
   同时反向查：目录里有 wxml 但未注册 → 模板残留 / 死代码。
2. **`usingComponents` 路径可解析性**——组件名写错，或目录迁移后漏改路径。
3. **主包 2 MB 上限**——超限无法上传。重点看 `miniprogram_npm/` 占比，
   组件库（如 TDesign）常被全量打入，实际只用了几个组件。

### 合规检查点
- `app.json` 有无 `__usePrivacyCheck__`；代码里是否用了 `wx.setClipboardData` /
  `wx.chooseAddress` / `wx.getLocation` / `wx.chooseImage` 等**隐私接口**
  → 需在公众平台配《用户隐私保护指引》，否则接口会被拦截、也是审核驳回高发点
- `project.config.json` 的 `setting.urlCheck` 是否为 `false`（上线前须确认 request 合法域名已配）
- 占位数据：`api.xxx.com`、`yourusername`、示例手机号 / UID、`替换为实际…` 注释
- 后端是否真的存在：看有没有 `test-data.json` / `mock/` / `envList.js` 为空

### 判定文件编码时注意
**不要**用 `head -c` / `grep` 的结果判定乱码——按字节截断多字节 UTF-8 字符会产生假的 ``，
要用 Read 工具读原文确认。

## 四、清理冗余项目的安全约定
1. 先列清单 + 说明冗余依据（同 AppID 的模板副本 / 无 app.json / 空目录），**等用户明确确认**
2. 删前用 `git -C <项目> status --porcelain` 和 `git remote -v` 确认没有用户独有改动
   （remote 指向官方模板仓库 + 工作区干净 = 安全）
3. 删前先 `close` 掉工具里打开的项目窗口
4. **一律用 `/usr/bin/trash <path>...` 移废纸篓，绝不 `rm -rf`**（macOS 原生，支持多路径，可原样恢复）
5. 删前导出文件明细清单留档，并告知用户可恢复

## 五、失败兜底
- CLI 报端口错误 → 重新 `open` 拿新端口再试
- `cli open` 连续报 `wait IDE port timeout` → **IDE 冷启动耗时超过 CLI 默认等待，等 10 秒再重试**即可成功
- `open` 返回成功但项目报错 → 检查 `app.json` 的 pages 是否都有对应文件
- 找不到云开发环境 → 看 `envList.js` 是否为空；`wx.cloud.init` 的 `env` 参数是否还是 `your-env-id`
- 工具的窗口状态缓存（`hash_key_map_2.json` 里的 `project2_*` / `toolbar_*` 键）**工具退出时会自愈**，
  不必手改核心映射文件

## 六、工具数据目录的大头：历史安装包
清缓存前先看一眼 `WeappApplication/` 和 `WeappCache/WeappApplication/` —— 这两处常常
**不是缓存，而是工具下载的历史版本安装包 `.dmg`**（单个 340–370 MB），
工具更新后不会自动清理。实测一次就积了 4 个、**1.4 GB**。

```bash
D=~/Library/Application\ Support/微信开发者工具/<hash>
ls "$D/WeappApplication/" "$D/WeappCache/WeappApplication/"
du -sh "$D"   # 清理前后对比
```

这些 dmg 可安全移入废纸篓（`/usr/bin/trash`），体积立降。真正的运行时缓存
（`requireCache` / `WeappCompileCache` / `dirCache`）和 `WeappVendor` / `WeappPlugin` /
`WeappForeignPkgs` **不要动**。
