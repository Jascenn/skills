---
name: ai-tool-state-forensics
description: "排查 macOS 上 AI 工具（CC Switch、Claude Code、Codex、OpenClaw、Hermes、Molili 等）的「东西坏了」类问题。当用户说技能打不开、卡片空白、看不到内容、列表里点了是空的、工具里少了东西时使用。核心是区分「界面/记录故障」与「文件真的损坏」，先用日志和 db 定位，不要先假设是自己改坏的。含 db 悬空记录核对、二进制能力探测、SKILL.md frontmatter 诊断脚本。"
---

# AI 工具状态取证

## 首要原则

**用户说"坏了"时，第一步不是修文件，而是先定位故障层。**
先分清三件事，能省掉大量盲查：

1. 工具**是否在运行**（运行中状态在变）
2. 日志里**有没有对应的读取记录**（没有 → 失败停在界面层）
3. **db 与文件是否一致**

⚠️ **别先假设是自己改坏的。** 问清楚"点的是哪一个"往往一步到位。

## ⛔ 搬走工具存储目录的条目会留下悬空 db 记录

**工具的 db 里通常有指向存储目录的条目。搬走文件但不更新 db，会留下"启用中但文件不存在"的记录。**

实测：把 9 个目录移出 `~/.cc-switch/skills` 后，db 立刻出现 9 条 `directory_missing`，
且**全部 `enabled_claude = 1`** —— 界面里显示为已启用、点开是空的。

**动手前后都要做这个核对**：

```python
import sqlite3, pathlib
base = pathlib.Path.home()/'.cc-switch/skills'
db = sqlite3.connect(f'file:{pathlib.Path.home()}/.cc-switch/cc-switch.db?mode=ro', uri=True)
db.execute('PRAGMA query_only=ON')          # 必须只读
for ident, name, d in db.execute('SELECT id,name,directory FROM skills'):
    p = base/d
    if not p.exists():                 print('directory_missing', name)
    elif not (p/'SKILL.md').is_file(): print('SKILL.md_missing', name)
```

**判读**：

| 结果 | 含义 |
|---|---|
| 改动**后**出现新的 `directory_missing` | ❌ **你造成的**，必须还原 |
| 改动前后都是 `SKILL.md_missing` | ⚠️ 改动前就坏的（多为拍平残留），非本次造成 |

**清理坏记录要趁工具关闭时**，或走工具自己的「卸载」入口（自带备份）。
**不要在应用运行时手改 db** —— 它有自动同步钩子（实测日志有
`[AutoSync] Triggered by table=skills`），可能覆盖你的写入或产生冲突。

## 验收时先区分「界面故障」和「点了坏记录」

工具日志是判断的关键证据。实测排查路径：

1. **工具是否在运行** —— 看日志是否仍在写入，比 `ps` 可靠（沙箱常拒绝 `ps`）
2. **日志里有没有对应的读取记录** —— 若用户操作时间点**完全没有**日志，
   说明失败停在界面层，或点的是结构性损坏的条目
3. **db 与文件是否一致** —— 见上面的核对脚本

实测结论：CC Switch 的 332/343 条记录可读，**11 条指向无顶层 `SKILL.md` 的目录**
（8 个拍平散件 + `skills` 容器 + 2 个非标准格式）。
点这 11 条必然是空的 —— **这是记录本身的问题，不是文件损坏**。

→ **所以问清楚"点的是哪一个"能省掉大量盲查。**

## ⚠️ 先确认工具到底有没有"看内容"这个功能

**用户说"看不到内容"，第一步不是修文件，而是确认工具是否支持看全文。**

实测 CC Switch 3.20.3：把二进制里所有 `*skill*` 命令提取出来，**只有一个读取命令**
`read_skill_name_desc` —— 它只读**名称 + 描述**用于列表展示。
**没有** `read_skill_content` / `preview_skill` / `view_skill`。

```python
import re
b = open('/Applications/CC Switch.app/Contents/MacOS/cc-switch','rb').read()
toks = set(m.group().decode('ascii') for m in
           re.finditer(rb'[a-z][a-z0-9_]{4,}(?:skill|skills)[a-z0-9_]*', b))
print([t for t in sorted(toks) if any(k in t for k in ('content','read','preview','view','detail'))])
# → 只有 read_skill_name_desc
```

**结论：CC Switch 面板本来就不展示 SKILL.md 全文**（它管安装/卸载/启用/更新，不管阅读）。
"看不到内容"如果指的是看全文，那是**功能不存在**，不是坏了。

**给用户的替代路径**：直接开文件，别指望在管理器里读。

```bash
open ~/.agents/skills/<技能名>/          # 真源，Finder
cat  ~/.agents/skills/<技能名>/SKILL.md  # 直接看
```

## 卡片空白的三类真实原因（`description` 为空）

`read_skill_name_desc` 解析失败会让卡片空白。实测 19 条空描述分三类：

| 类型 | 数量 | 原因 |
|---|---|---|
| 无 `SKILL.md` | 11 | 拍平残留 / 容器目录 / 非标准格式 |
| 没有 YAML frontmatter | 5 | 文件开头就没有 `---` 块 |
| frontmatter **非法** | 2 | `description` 值里含未加引号的 `: `；或缺结尾 `---` |
| frontmatter 缺 `description` 字段 | 1 | 只有 `name` |

**诊断脚本**（逐条判定，不猜）：

```python
import re, os
for name, d in rows:                      # rows 来自 db 的 (name, directory)
    p = os.path.join(base, d, 'SKILL.md')
    if not os.path.exists(p):
        print(name, '→ 无 SKILL.md'); continue
    txt = open(p, encoding='utf-8', errors='replace').read()
    m = re.match(r'^---\s*\n(.*?)\n---', txt, re.S)
    if not m: print(name, '→ 无 frontmatter'); continue
    if not re.search(r'^description:\s*\S', m.group(1), re.M):
        print(name, '→ 缺 description 字段')
```

**注意**：`description` 里含 `: `（如 `Use when: (1) ...`）会让 YAML 解析失败 ——
必须整体加引号。这是最隐蔽的一类。详见 `obsidian-frontmatter-repair`。

**另外**：db 的 `directory` 列**可能与 `name` 不同**（如 `name` 是 `xxx(Maia)`，
目录名却是别的）。按名字拼路径会 `FileNotFoundError` —— **要用 `directory` 列拼**。

## 判断工具是否在运行（沙箱下）

`ps` 常被沙箱拒绝，`pgrep -fl` 会有假阳性（沙箱把自己的完整命令行注入进程表）。

```bash
# ✅ 推荐：看日志是否仍在写入
ls -lt "$HOME/.<tool>/logs" | head
tail -c 800 "$HOME/.<tool>/copaw.log"

# ✅ 次选：进程表 + 只比 comm 字段
ps -Ao pid,comm | grep -i "<tool>" | grep -v grep

# ✅ LaunchAgent
launchctl list | grep -i "<tool>"

# 应用是否存在
ls -d /Applications/*[Mm]olili* ~/Applications/*[Mm]olili*
```

**判读纪律**：
- 进程查询权限被拒绝应记为**"状态未知"，不是"无进程"**。
- 旧日志只能证明**该日志未更新**，不能证明应用已停用。
- 配置中缺少路径字段**不能**证明路径硬编码（需进一步看二进制）。

**实测案例（Molili 停用 6 个月的证据链）**：应用不存在 + 无 LaunchAgent + 日志停在
`2026-03-25 19:45`（优雅关闭后零写入）。注意 `active_skills` 的 mtime 虽晚于日志，
但那是**外部批量操作**留下的，不是工具在跑 —— **mtime 不能证明进程活跃**。

## 从二进制里探测工具能力

Tauri / Electron 应用的能力常能从二进制字符串里挖出来：

```bash
B="/Applications/<App>.app/Contents/MacOS/<app>"
strings -n 6 "$B" | grep -E '\.agents'                    # 找路径约定
strings "$B" | grep -oE "migrate_[a-z_]+|set_[a-z_]+storage[a-z_]*"   # 找迁移/设置命令
```

**前端文案提取**（Tauri 把 i18n 打进二进制，`strings` 抓不到中文）：

```python
import re
data = open(B,'rb').read()
pat = re.compile(rb'(?:[\xe4-\xe9][\x80-\xbf]{2}){2,}')   # UTF-8 CJK 连续段
for m in pat.finditer(data):
    s = m.group().decode('utf-8', 'ignore')
    if any(k in s for k in ('存储','技能','同步')): print(s)
```

注意：i18n 字典常被压成一整条超长串，能拿到关键词但切不出单条文案。

**⚠️ 纪律**：二进制中的字串**不能单独证明**配置枚举、界面入口或迁移保护；
需匹配版本的官方资料或界面验证。**原生迁移也不是"零风险"。**

## 安全纪律

- **本地 `.env` 中存在密钥不证明泄露、有效或必须吊销**；不得输出值或向共享技能扩散。
  是否轮换需核实使用情况及暴露范围。
- **零断链只覆盖实际扫描范围，不等于所有应用功能通过。** 成功验收还需应用打开、
  读取技能、正常运行及更新后检查。**静态验证 ≠ 能用。**

## 相关技能

- 磁盘清理导致文件被搬走 → `disk-cleanup-rollback`
- 技能目录软链去重、建链、回滚 → `skill-dir-symlink-dedup`
- Markdown / frontmatter 损坏的修复流程 → `obsidian-frontmatter-repair`
