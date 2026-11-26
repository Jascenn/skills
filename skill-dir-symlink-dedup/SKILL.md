---
name: skill-dir-symlink-dedup
description: "安全地把多个 AI 工具的 skills 目录去重为「单一真源 + 符号链接」。当需要清理 ~/.cc-switch、~/.claude、~/.codex、~/.openclaw、~/.hermes、~/.molili 等工具各自的技能副本，或要把某个工具目录的技能实体改成指向主目录的软链时使用。核心是先做五步只读验证、再小批试点，并严格区分「消费端目录」与「工具自有存储」——后者绝不能软链。"
---

# 技能目录软链去重

把 N 个 AI 工具各自的技能副本，收敛成「一个真源目录 + 各工具软链」。

**不是** git worktree —— worktree 解决多分支并行，不解决同内容多副本。

## 安全更正：以下规则优先于后文历史记录

后文保留了相互冲突的历史判断和操作示例，尚未全部整理；**不得直接执行其批量建链、移动或回滚脚本**。

- 个人目录先只读盘点；改动前列全受影响路径、说明风险并取得确认。先独立复制备份并验证成功，再操作；**每批最多 10 个文件**。
- **进程查询权限被拒绝应记为"状态未知"，不是"无进程"。** 旧日志只能证明该日志未更新，不能证明应用已停用；配置中缺少路径字段也不能证明路径硬编码或目录不可软链。
- db、配置文件和已有软链都只是**线索**；必须验证具体应用版本的读写、导入、更新和路径校验机制。CC Switch 曾在全量建链后出现不可读和回写，早期十项试点未回写**不能**推翻后续结果。
- mtime、文件大小与单个 `SKILL.md` 哈希**不能**证明版本新旧、完整目录一致或可安全替换。逐文件内容、权限、软链目标及 Git 历史都需核对；**有 remote 不等于本地历史可恢复**。
- 重复判定必须在**排除所有拟移除路径及其别名**的保留集合内验证；另一处仍保留的副本可用于证明跨目录重复，但不能据此同时移除两处。
- **零断链只覆盖实际扫描范围，不等于所有应用功能通过。** 成功验收还需应用打开、读取技能、正常运行及更新后检查。
- 二进制中的 `agents` 字串不能单独证明配置枚举、界面入口或迁移保护；需匹配版本的官方资料或界面验证。**原生迁移也不是"零风险"。**
- 本地 `.env` 中存在密钥不证明泄露、有效或必须吊销；不得输出值或向共享技能扩散。
- **「体积相同」不能推断「内容重复」**（实测两份 964.8 MB 目录，实际有 13/1 个独有文件和 5 个内容不同文件）。
- **反复出现的同类错误：凭间接指标推断，没做直接验证。**（超集检查循环引用 / 搬走存储目录留悬空 db / 凭体积断言重复）。**凡是"可以安全删除"的结论，都必须有直接比对证据。**
- **历史状态（2026-09-22）**：已进行的操作是**暂存归档、codex 提升和四文件复制**；**没有永久删除**，未完成独立备份完整性校验及应用端验收。Molili 当前运行状态未确认，CC Switch 存储位置迁移**未执行**。

## 本机既有事实（做之前先确认，别假设）

- 真源目录：`~/.agents/skills`（截至 2026-09 约 341 个技能 / 1.8 GB）
- 部分工具**已经**在用软链，不要重复劳动，先扫一遍现状

## 五步只读验证（缺一步都不要动）

### 1. 摸清各工具目录的软链/实体构成

```bash
for tool in claude codex gemini openclaw hermes cc-switch molili; do
  D="$HOME/.$tool/skills"
  [ -d "$D" ] || continue
  l=$(find "$D" -maxdepth 1 -type l 2>/dev/null | wc -l | tr -d ' ')
  e=$(find "$D" -maxdepth 1 -type d ! -path "$D" 2>/dev/null | wc -l | tr -d ' ')
  echo "~/.$tool/skills → 总 $(ls -1 "$D" 2>/dev/null | wc -l | tr -d ' ') | 软链 $l | 实体 $e"
done
```

### 2. 扫描断链（必须为 0）

```bash
find "$D" -maxdepth 1 -type l ! -exec test -e {} \; -print
```

### 3. 内容一致性：目标目录 vs 备份实体

```bash
# 逐文件 shasum 对比，注意排除 .git（见下方坑）
diff <(cd "$MAIN/$n" && find . -type f ! -path './.git/*' -exec shasum {} \; | sort) \
     <(cd "$BAK/$n"  && find . -type f ! -path './.git/*' -exec shasum {} \; | sort)
```

### 4. 确认工具**当前没在运行**

运行中回写会污染试点结论：

```bash
ps -Ao pid,comm | grep -i "<tool>" | grep -v grep
launchctl list | grep -i "<tool>"
ls -lt "$HOME/.<tool>/logs" | head
```

### 5. 确认目标技能在真源目录里都存在

```bash
for n in $(ls -1 "$TOOL_DIR"); do
  [ -d "$HOME/.agents/skills/$n" ] || echo "缺失: $n"
done
```

## 建链（小批试点，10 个起步）

```bash
MAIN="$HOME/.agents/skills"
TOOL="$HOME/.cc-switch/skills"
BAK="$HOME/_cleanup_staging_$(date +%Y%m%d)/<tool>-entity-backup"
mkdir -p "$BAK"

for n in skill-a skill-b; do
  [ -d "$TOOL/$n" ] && [ ! -L "$TOOL/$n" ] || { echo "跳过 $n"; continue; }
  mv "$TOOL/$n" "$BAK/$n"                      # 先备份，不是 rm
  ln -s "../../.agents/skills/$n" "$TOOL/$n"   # 相对链接，抗 home 迁移
  [ -r "$TOOL/$n/SKILL.md" ] && echo "✓ $n" || echo "✗ $n 不可读"
done
```

**用相对链接**（`../../.agents/skills/<n>`），不要写绝对路径 —— 换机器 / 改 home 名时不断链。

## 已知坑

| 坑 | 现象 | 解法 |
|---|---|---|
| 工具的「导入已有」按钮 | **复制**而非链接，制造新重复 | 别点。CC Switch 实测：一次点击新增 146 份实体副本 |
| `.git` 差异误判 | 备份含 `.git/`，真源不含 → 报"内容不一致" | 对比时排除 `.git`；但**记住该技能的 git 历史只在备份里** |
| 应用回写 | 工具启动后把软链还原成实体 | 实测 CC Switch **未发生**；但仍需观察一个版本升级周期 |
| `stat -f '%Sm'` | 在部分机器上不生效，输出原始 stat 结构 | 用 python `os.lstat().st_mtime` |
| 全量 shasum 超时 | 对 1.8G 目录逐文件哈希 → SIGTERM / 137 | 用轻量指纹：文件名列表 + SKILL.md 的 sha1 |
| `pgrep -fl` 假阳性 | 沙箱会把自己的完整命令行注入进程表 | 改用 `ps -Ao pid,comm \| grep` |
| BSD `du --exclude` | 不支持，返回空 | 用 find 或直接看目录构成 |
| BSD `grep -P` | `invalid option -- P` | 用 awk 做字段匹配 |
| `~` 存进变量不展开 | 函数收到 `~/...` 当字面量 | 传参前转绝对路径 |
| `grep -qxF` 对 tab 多字段文件 | 去重失效 | 用 `cut -f1` 或独立集合文件 |

## 冲突判定：同名但内容不同怎么办

**不要假设哪边新，用 mtime 实测。**

```python
import os, hashlib
def sk(d):
    p = os.path.join(d, "SKILL.md")
    if not os.path.isfile(p): return None, 0
    return hashlib.sha1(open(p,'rb').read()).hexdigest(), os.path.getmtime(p)
# 逐项比 (hash, mtime)；hash 不同时记录 mtime 差值，统计方向
```

CC Switch 实测：**71 项差异，71/71 全部是真源更新，工具侧 0 项更新**。
→ 真源是权威，建链会顺带**修复工具侧的陈旧技能**（有的落后 4 个月）。
这是建链的额外收益，不只是省空间。

**决策口径**：方向一致（真源全胜）→ 直接建链；
方向混合（各有更新）→ 逐个人工判断，**不要批量**。

## 建链前必做：超集检查（最容易漏的一步）

**`SKILL.md` 一致 ≠ 整个目录一致。** 参考文件、assets 可能只在一边有。

```python
def flist(d):
    s=set()
    for r,_,fs in os.walk(d):
        for f in fs:
            if f=='.DS_Store' or '/.git/' in os.path.join(r,f) or '__pycache__' in r: continue
            s.add(os.path.relpath(os.path.join(r,f),d))
    return s
only_src = flist(SRC) - flist(DST)     # 建链后会丢的文件
```

CC Switch 实测：311 个候选里 **14 项 src 有 dst 缺失的文件，合计 80 个**。
特征很典型 —— **`SKILL.md` 是主目录更新，但 `references/` 却是工具侧更全**：

| 技能 | 独有文件数 |
|---|---|
| `microsoft-foundry` | 19 |
| `lark-base` | 13 |
| `ljg-card` | 9 |
| `lark-whiteboard` | 8 |
| `lark-minutes` | 5 |

→ 两边各有优势，**谁都不是严格超集，直接建链会静默丢文件**。

**正确流程：先补齐，再建链。**

1. 把 src 独有文件复制进 dst（additive，不覆盖）
2. 校验 `only_src == 空` 对**全部**条目成立
3. 才执行建链

⚠️ 判断「一批目录是否 100% 重复」时，**参考索引必须排除被评估的目录本身**，
否则会拿自己跟自己比、永远得出"100% 重复"（实测结论会从「181 个文件重复」反转为「14 个孤本」）。
完整陷阱说明见 `disk-cleanup-rollback`。

⚠️ **「父技能里有同名文件」≠「可以删」** —— 顶层散件往往同名但内容不同
（实测散件是 2025-12 旧版，父技能已到 2026-03）。详见 `disk-cleanup-rollback`。

还要查**空目录**：实测主目录里有 4 个自定义技能是空壳，
只有工具侧有真实 `SKILL.md` —— 这类必须先把内容补进主目录，
否则建链后工具也读不到（而且这本身就是主目录的 bug，值得单独修）。

## 搬移方式：用 rename，不要用 cp

```python
os.rename(src, dst)                    # 同文件系统 → 瞬时 rename，零额外空间
os.symlink(f'../../.agents/skills/{n}', src)
```

**先确认同文件系统**：`os.stat(A).st_dev == os.stat(B).st_dev`

- `rename` 瞬时完成，333 个目录零耗时、零额外空间
- 比 `cp` + `rm` 安全得多 —— 没有"复制到一半"的中间态
- 数据仍在暂存区，观察期后清理即可

**不要用 `cp -al` 做硬链快照**：实测在 343 项 / 1.8 G 上超时（SIGTERM / 137），
且快照存在时空间根本没释放。**先补齐主目录，让主目录本身成为备份，才是正解。**

## ⛔ 最重要的一条：不要软链「工具自己的技能存储目录」

**软链化只该作用于工具的「消费端」目录，不该动工具自己的 SSOT 存储。**

| 目录类型 | 例子 | 能否软链 |
|---|---|---|
| 消费端（工具只读） | `~/.claude/skills`、`~/.codex/skills`、`~/.hermes/skills` | ✅ 可以 |
| 工具自有存储（工具要管理） | `~/.cc-switch/skills` | ❌ **不要** |

**判断方法**：看目录里是不是有工具的 db / 配置文件
（`cc-switch.db`、`settings.json`）。**有 → 那是工具的自有存储，别动。**

### 三级判据（先分类再动手）

先跑一遍这个表，别一上来就建链：

```bash
for t in claude codex gemini openclaw hermes cc-switch molili; do
  D="$HOME/.$t/skills"; [ -d "$D" ] || D="$HOME/.$t/active_skills"
  [ -d "$D" ] || continue
  printf "%-12s 总 %-4s 软链 %-4s 自有db %s\n" "$t" \
    "$(ls -1 "$D" | wc -l | tr -d ' ')" \
    "$(find "$D" -maxdepth 1 -type l | wc -l | tr -d ' ')" \
    "$(ls -1 "$HOME/.$t"/*.db 2>/dev/null | wc -l | tr -d ' ')"
done
```

| 判据 | 结论 |
|---|---|
| 同层级有工具的 db / 配置 | ❌ **自有存储，别软链** |
| 该目录**已有大量软链且工具正常** | ✅ 消费端，可软链 |
| 都没有 | ❓ 先小批试点验证 |

**实测结果（本机）**：

| 工具 | 总数 | 已软链 | 自有 db | 判定 |
|---|---|---|---|---|
| claude | 138 | **129** | 0 | ✅ 安全 |
| openclaw | 104 | **78** | 0 | ✅ 安全 |
| hermes | 89 | **61** | 3 | ⚠️ 谨慎 |
| codex | 15 | 3 | 0 | ✅ 安全 |
| gemini | 3 | 2 | 0 | ✅ 安全 |
| **cc-switch** | 343 | 0 | **1** | ❌ **不要动** |
| molili | 93 | 0 | 0 | ❌ **不要动**（见下） |

**关键推论**：「已有大量软链且工具正常」是最强的安全证据 ——
说明该目录是消费端，工具不会主动回写它。

### 「0 软链 + 0 db」不等于可以试点 —— 要看配置

Molili 实测（2026-09）：

| 检查项 | 结果 |
|---|---|
| 应用 / LaunchAgent / 进程 | 全部不存在 |
| `active_skills`(93) / `customized_skills`(86) | 0 软链，全实体 |
| 同层级 db | 0 |
| **`config.json` 里有没有 skills 路径** | **没有** —— 路径硬编码在 app 内 |

→ 没有配置项 = 路径**硬编码**，这是**工具自有存储**的另一种形态。
**判定 ❌ 不要软链**，只能「原样保留」或「整体归档」。

**补充判据**：`config.json` / `settings.json` 里**找不到** skills 目录设置，
说明路径是编译进程序的 → 与「有 db」等价，别动。

### 实测后果

把 CC Switch 存储目录的条目换成指向外部的软链后，**UI 里技能"打不开"** ——
文件系统层面一切正常（0 断链、332/343 SKILL.md 可读、权限正确），
但工具内部拒绝。

**旁证**：回滚时 338 条软链只剩 294 条 —— **44 条被工具自己还原成了实体**，
即"回写"真实发生了。

### 工具自己的软链方向是相反的

CC Switch 自己就用软链，但方向是从**存储**往**消费端**建：

```
~/.cc-switch/skills/<n>          ← 源（必须是真实目录）
      ↓ 工具自己建软链
~/.claude/skills/<n>、~/.codex/skills/<n>
```

日志原文：`Skill xxx 已通过 symlink 同步到 Codex`

**手工软链存储目录 = 把方向搞反了。**

## ✅ 优先找工具的原生方案（比手工软链好得多）

**动手前先查工具有没有官方支持的「共享目录」设置。手工软链是最后手段。**

CC Switch 就有两个独立设置（v3.13.0+）：

| 设置 | 位置 | 作用 |
|---|---|---|
| **存储位置** | Skills 面板 → 设置/管理菜单 | 源存哪：`~/.cc-switch/skills` 或 **`~/.agents/skills`** |
| **同步方式** | 设置 → 通用 | 怎么分发到各应用：**软链接** 或 复制 |

官方文档原文：

> **存储位置切换**：Skills 的源存储位置可以在两个位置之间切换 ——
> CC Switch 内置存储 `~/.cc-switch/skills/`，或 **`~/.agents/skills`**
> （符合社区 agent 工具约定的共享目录）。
> 切换过程**不会丢失 skill 状态** —— CC Switch 会平滑迁移现有 skill 到新位置。

**所以正确操作是**：把存储位置切到 `~/.agents/skills`，同步方式保持「软链接」。
零手工操作，零风险，达到同样的去重目标。

### 配置文件里的确切键与取值（已实测）

`~/.cc-switch/settings.json`：

```json
"skillSyncMethod": "auto",
"skillStorageLocation": "cc_switch"
```

二进制里能验证到 `agents` 这个取值：

```bash
B="/Applications/CC Switch.app/Contents/MacOS/cc-switch"
strings -n 6 "$B" | grep -E '\.agents'
# → cc_switch_lib::services::skill.agents      ← 模块名暴露了 agents 分支
```

**注意**：改 JSON 不是首选 —— CC Switch 还有 `cc-switch.db` 需要同步更新，
优先用界面里的「存储位置」开关（自带迁移 + 备份）。
二进制里另有「**存储迁移完成**」等中文文案，说明应用内建迁移流程。

**查文档的方法**：

```bash
# 工具自带的 Tauri/命令列表能暴露能力
strings "/Applications/<App>.app/Contents/MacOS/<app>" | grep -oE "migrate_[a-z_]+|set_[a-z_]+storage[a-z_]*"
# 例如发现 migrate_skill_storage → 说明原生支持迁移存储位置
```

再去搜官方文档确认。更多二进制探测技巧见 `ai-tool-state-forensics`。

## 出问题的回滚（rename 瞬时完成）

⚠️ **本节的 `rm` 只删软链本身，不删任何数据** —— 真实数据在 `$BAK` 里，
`mv` 会立刻把它搬回来。**这是本节唯一允许出现 `rm` 的场景**；
其余任何删除一律走系统废纸篓或交给用户手动执行（见 `disk-cleanup-rollback`）。

```bash
BAK=~/_cleanup_staging_<日期>/<tool>-entities-full
CC=~/.cc-switch/skills
for n in $(ls -1 "$BAK"); do
  [ -L "$CC/$n" ] || { echo "⚠️ $CC/$n 不是软链，跳过"; continue; }   # 加保险：只删软链
  rm "$CC/$n"
  mv "$BAK/$n" "$CC/$n"
done
```

**回滚后务必验证**：

```bash
ls -1 "$CC" | wc -l                                   # 条目数对得上
find "$CC" -maxdepth 1 -type l | wc -l                # 应为 0
find "$CC" -maxdepth 1 -type l ! -exec test -e {} \;  # 断链应为 0
```

## 别把「没有 SKILL.md 的目录」当垃圾清

真源目录里常有一批无 `SKILL.md` 的顶层目录。**先分类再动手，里面可能埋着真技能。**

实测 11 项分三类：

**1. 被提升的子目录**（如 `canvas-fonts` ← `canvas-design/canvas-fonts`、
`ooxml` ← `docx/ooxml`、`themes` ← `theme-factory/themes`、`core` ← `slack-gif-creator/core`）

用「某名字的子目录出现在哪些技能里」反查来源：

```python
for skill in os.listdir(AG):
    for r,dirs,_ in os.walk(os.path.join(AG,skill)):
        for d in dirs:
            if d in BARE_NAMES: hits[d].append(skill)
```

**⚠️ 但"溯源成功"不等于"可清"** —— 实测父技能里的同名文件
**内容并不相同**（散件是 2025-12 旧版，父技能已到 2026-03）。
必须逐文件比 sha1。

**2. 多技能同名目录碰撞后合并的散件**（如 `references`/`scripts`/`examples`）
—— 无法唯一溯源，同样只能逐文件校验，**默认不可删**。

**3. ⚠️ 埋着真技能 —— 最容易被误删**

实测埋了 4 个：

| 位置 | 情况 | 实测结论 |
|---|---|---|
| `requirements-clarity/skills/SKILL.md` | 完整技能，被多包了一层 | 真源已有同结构副本，sha1 一致 → 无需救 |
| `skills/codex/SKILL.md` | 技能被包在 `skills/` 容器里 | 真源也有（嵌套），内容仅差 1 字节 → **提升到顶层即可** |
| `skills/gemini/SKILL.md` | 同上 | 真源顶层已有 → 嵌套副本可弃 |
| `miniapp-fullstack-guide/skill.json` | 用 `skill.json` 而非 `SKILL.md` 的非标准技能 | 真源已有，sha1 一致 → 无需救 |

**教训**：别急着"救出"，**先比 sha1 确认真源到底有没有**。
实测 4 个里 3 个真源早已有一致副本，只有 `codex` 需要「提升」而非「救出」。

**检查方法**：对每个无 `SKILL.md` 的目录，往下挖 2–3 层找 `SKILL.md` 或 `skill.json`。

```bash
find "$AG/<裸目录>" -maxdepth 3 -name 'SKILL.md' -o -maxdepth 3 -name 'skill.json'
```

## 顺带排查：写死工具路径的技能

软链架构下，技能里**硬编码某个工具目录**会埋雷。

实测两个 `gemini` 技能逻辑完全相同，只有路径不同：
- 一个写 `~/.claude/skills/gemini/scripts/gemini.py`
- 一个写 `~/.Codex/skills/gemini/scripts/gemini.py`

```bash
# 找出所有硬编码工具路径的技能
grep -rl --include='SKILL.md' -E '~/\.(claude|codex|openclaw|hermes|molili)/' "$AG" | head -20
```

统一到真源路径（`~/.agents/skills/...`）后，两种写法都能用；否则换工具就断。

## 工具的「导入」类按钮要警惕

这类按钮的语义通常是 **import（复制进来）**，不是 **link**。

实测 CC Switch「导入已有」：
- 新增 146 项，**全部实体副本，0 软链**，157.7 MB
- 139 项与真源同名且内容一致 → 纯重复
- 7 项真源没有 → 真新内容，需反向合并进真源

**处置**：先挑出"真源没有的"合并进真源，其余的建链回收。

## 工具特定的配置检查

### CC Switch

```bash
# 关键：可能触发回写
grep -E 'skillSyncMethod|skillStorageLocation' ~/.cc-switch/settings.json
# skillSyncMethod: auto + skillStorageLocation: cc_switch → 有回写可能

# db 的 directory 列存相对名而非绝对路径 → 建链不影响其查找
sqlite3 ~/.cc-switch/cc-switch.db "PRAGMA table_info(skills);"
sqlite3 ~/.cc-switch/cc-switch.db "SELECT COUNT(*), COUNT(content_hash) FROM skills;"
```

`content_hash` 有填充 → 工具可能校验并回写。**这决定试点的风险等级。**

**实测结论（2026-09）**：CC Switch 打开后，10 条软链**全部存活，未回写**。
`content_hash` 有填充 ≠ 一定会回写。但仍建议观察一个版本升级周期。

界面上的「导入已有」按钮 = **复制**，会新增实体副本。别点。

## 安全红线

1. **只 `mv` 到 staging，绝不 `rm`** —— 保留回滚路径
2. **先小批（10 个）试点**，等用户实际用工具验证过再批量
3. **静态验证 ≠ 能用**。软链可读不代表工具认。必须让用户启动工具实测
4. 备份里的 `.git/` 可能是某技能唯一的版本历史 —— **不可删**
5. **不认识的按钮不要点**。工具里「导入 / 同步 / 恢复」类按钮默认按"复制"理解，
   点了就可能把刚清理掉的重复又造回来
6. **绝不软链工具自有存储目录**（见上文）

## 相关技能

| 需求 | 技能 |
|---|---|
| 腾磁盘空间、可回滚删除、重复/归档目录判定 | `disk-cleanup-rollback` |
| 工具报错、卡片空白、db 悬空记录、二进制探测 | `ai-tool-state-forensics` |
| Markdown / frontmatter 损坏修复 | `obsidian-frontmatter-repair` |
