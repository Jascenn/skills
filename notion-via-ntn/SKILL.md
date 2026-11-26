---
name: notion-via-ntn
description: 用 Notion 官方 CLI `ntn`（经 HTTPS_PROXY/Surge）读写 Notion，绕开 Electron/undici 不读系统代理的坑。当 WorkBuddy 的 Notion MCP 连接器报 `fetch failed`/`unauthorized`、连接器反复掉线，或需要稳定地批量拉取/写入 Notion 数据库时使用。也包含判断「某程序到底认不认环境变量代理」的决定性实验方法。
---

# Notion 访问走 `ntn` CLI（+ 代理），别依赖 WorkBuddy MCP

## 何时用这个技能

- WorkBuddy 的 Notion 连接器状态在 `ready` / `error: fetch failed` / `unauthorized` 之间反复横跳
- 需要稳定、可脚本化、可定时地读写 Notion 数据库
- 需要判断某个程序是否真的走了代理

## 核心事实（先看这个，省半小时）

**WorkBuddy（Electron）的 MCP 请求走 Node/undici 的 `fetch`，它不读 macOS 系统代理，也不受 `HTTPS_PROXY` 影响。**
所以哪怕系统代理配好了、Surge 在跑，WorkBuddy 仍会直连 `mcp.notion.com`。

实测直连 `mcp.notion.com` 在国内是**剧烈抖动**的：同一分钟内 5 次采样能得到
`1.22s / 12.0s超时 / 12.0s超时 / 5.62s / 12.0s超时`，连接器探针成功率约 **1/5**。
走 Surge 则稳定 **0.28–0.9s，5/5 成功**。

## 决定性实验：怎么判断一个程序认不认代理

**不要靠测量延迟来判断** —— 噪声太大，会得出错误结论（本项目踩过这个坑）。
唯一可靠的判据是**把代理指向死端口**：

```bash
# 若该程序尊重代理 → 请求必然立刻失败（连不上 127.0.0.1:9）
# 若它忽略代理 → 请求照样成功（因为走的是直连）
HTTPS_PROXY=http://127.0.0.1:9 HTTP_PROXY=http://127.0.0.1:9 <cmd> ...
```

已验证的结果：

| 目标 | 死端口实验结果 | 判定 |
|---|---|---|
| Node/undici `fetch`（WorkBuddy 用的那套） | **8/8 全部成功** | ❌ 完全不读代理 |
| `ntn`（Rust/reqwest） | `ntn doctor` 报 `Token valid ! Failed to list workers` | ✅ 确实读代理 |

**两个坑**：
1. `NODE_USE_ENV_PROXY=1` 会打印 `[UNDICI-EHPA] Warning: EnvHttpProxyAgent is experimental`，
   **但这条警告不代表代理生效** —— `fetch` 依然不走它。别被日志骗了。
2. 环境变量必须在**进程启动前**设置。运行时 `process.env.HTTPS_PROXY = ...` 赋值**无效**。
3. 给 WorkBuddy 注入环境变量这条路**已验证无效**，别再试：
   `launchctl setenv HTTPS_PROXY ...` + `NODE_USE_ENV_PROXY=1` 都不行。

## 正确做法：用 `ntn`

`ntn` 是 Notion 官方 CLI（Rust/reqwest，**默认读 `HTTPS_PROXY`**）。

```bash
# 0. 检查是否安装 + 登录态
which ntn || echo "未装：brew install notion-cli"
ntn doctor          # 期望看到 Token valid ✔ API authenticated successfully

# 1. 所有调用都带上代理
export HTTPS_PROXY=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890

# 2. 搜索工作区里所有 data source（注意 filter 值是 data_source 不是 database）
ntn api /v1/search -X POST \
  -d '{"filter":{"value":"data_source","property":"object"},"page_size":100}'

# 3. 查一个 data source 的内容
ntn api /v1/data_sources/<DS_ID>/query -X POST -d '{"page_size":100}'

# 4. 写一条记录
ntn api /v1/pages -X POST -d '{
  "parent":{"type":"data_source_id","data_source_id":"<DS_ID>"},
  "properties":{"Name":{"title":[{"text":{"content":"标题"}}]},
                "金额":{"number":100},
                "日期":{"date":{"start":"2026-09-29"}}}}'
```

登录态存在 **macOS 钥匙串**（条目名 `notion-cli`），不在配置文件里，无需手动配 token。

## 字段名的两个陷阱

1. **日期属性在原生 API 里就叫 `时间` / `日期`**，不是 `date:时间:start`。
   后者是 **MCP SQL 模式**的列名转换，别混用。
2. 用 SQL 模式看到 `ROUND(SUM(x),2)` 的总额才是权威口径。
   **金额绝不能逐条 `round(2)`** —— Notion 里有 `9.996 / 10.728 / 76.841` 这类值，
   逐条舍入再求和会让总额差 1 分。要保留原始精度、只对最终合计取整。

## 顺带：怎么找出「哪个数据库才是真在用的」

当某个库看起来是空的或只有占位数据时，**别猜名字，用数据筛**：

1. 搜出全部 data source
2. 逐个 `query` 拿真实行数（`page_size` 分页累加）
3. **排除**：0 行、2–3 行且名字像模板（「项目一/项目二」「测试-xxx」「已完成示例：…」）
4. **确认**：看内容能否与别处的已知真实数据**交叉印证**
   （例：项目名里有「给客户 A 更新项目 X」，而收入记录里也全是「给客户 A…」→ 确认同一人）

⚠️ Notion 里 ID 长得很像的库很多（例如 `aaaa1111-…0001` vs `aaab1111-…0002`），
**仅凭 ID 或名字极易搞错，必须核对内容**。

## 配额陷阱

Notion 的 `query_data_sources` 撞配额时，报错是
`Streamable HTTP error ... {"error":"internal_error"}` —— **看起来像网络抖动，实际是配额**。
**判别法：同样报错重试一次，若变成 `usage_limit_reached` 就是配额**，别再往网络上查。
规避：少用 SQL 聚合，改为一次批量拉明细后在本地算。

## 别做的三件事

- ❌ 别为这事去开 Surge 增强模式（TUN）。TUN 改的是**全机**网络行为，
  而 `ntn` 用 `HTTPS_PROXY` 已能精确地只让这一个工具走代理 —— 收益与代价不成比例。
- ❌ 别在 Surge 里给 `mcp.notion.com` 配规则来救 WorkBuddy —— 应用压根不经过 Surge，配了命中不到。
- ❌ 别靠"重启 WorkBuddy"当修复。实测重启后是 **4 次失败 + 第 5 次才成功**，属幸存者偏差。

## 参考落地脚本结构（如项目已配置配套同步脚本）

若项目目录下已配置配套同步实现，遇到同类需求**先看这些脚本，别重写**：

| 文件 | 作用 |
|---|---|
| `<project-dir>/scripts/notion-sync.py` | 同步核心。封装 ntn 调用、分页、多个库的字段映射 |
| `<project-dir>/scripts/sync-now.sh` | **一键同步入口**。含前置检查（ntn 存在 + 代理通路检查）、跑同步、重建离线页。退出码 0/2/3/4/5 分别代表 成功/缺 ntn/代理不通/同步失败/离线页生成失败 |
| `<project-dir>/scripts/notion-push-drafts.py` | 本地草稿写回 Notion。**默认只演练，必须 `--confirm` 才真写**。唯一会写用户 Notion 的动作，谨慎处理 |
| `<project-dir>/scripts/notion-api.py` | ntn 的薄封装，带 `fetch_all()` 分页与 `all_data_sources()`；CLI 有 `list`/`count`/`dump` |
| `<project-dir>/scripts/probe-ds.sh` | 探某一个 data source 的真实行数 |
| `<project-dir>/scripts/tests/` | 页面侧回归测试（DOM 桩，见 `static-html-domstub-test` 技能） |

**给用户手动同步的三条路**（按便利度）：
1. 工作台页面上的 **「同步一次」按钮**（走 `POST /api/sync`，本地服务代跑 `sync-now.sh`，约 7 秒）
2. `bash <project-dir>/scripts/sync-now.sh`
3. 口头说「同步一次」，由助手跑上一条

⚠️ **展示给用户的链接必须带 `?token=`** —— 本地服务对 `/data.json` 和 `/api/sync` 都要求令牌。
裸链接 `http://127.0.0.1:8787/workbench.html` 的后果不是"打不开"，而是更难发现的两个静默故障：
**页面照常显示但用的是浏览器缓存的旧数据**（`/data.json` 401 → 静默退回 localStorage），
以及**点同步 `0.0s` 就失败**（`/api/sync` 401，服务端第一层就拦下，脚本根本没跑）。
- 令牌：`~/.config/<app>/sync-token`（32 位，稳定不轮换）
- **最省事**：`bash scripts/open-workbench.sh`（`--open` 直接开浏览器）打印有效链接并自检
- `GET /` 会 302 重定向到带令牌的链接，所以 `http://127.0.0.1:8787/` 是最稳入口
- 令牌会记进 localStorage（`wb_token`），浏览器打开过一次带令牌链接后裸链接也能用

⚠️ 页面那个按钮依赖本地服务 `app.py` 用 **`ThreadingHTTPServer`**：该接口阻塞等脚本跑完，
而脚本最后要 POST 回同一服务写数据，单线程会**正好 30 秒自锁**。

**相关技能**：页面侧改动后的回归测试见 `static-html-domstub-test`（含"归一丢字段 / 筛选漏排序 /
用分类名当金额符号代理 / 类名没写 CSS"四类静默故障的判别法）。
