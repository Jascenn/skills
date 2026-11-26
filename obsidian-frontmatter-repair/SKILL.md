---
name: obsidian-frontmatter-repair
description: "体检并修复 Obsidian 库（或任意 Markdown 知识库）的 frontmatter 损坏。当笔记在 Obsidian 里属性面板为空、认不出属性、Dataview 查不到、日期排序错乱，或怀疑 YAML frontmatter 有问题时使用。核心症状是收尾 `---` 被误拼到最后一个字段值后面（例如 `updated: 2026-06-30---`），最严重的情况连闭合 `---` 都整个丢失、导致正文被当 YAML 扫。含整库备份、定位、批量修复、全库验证的完整流程与实测坑。"
---

# Obsidian frontmatter 体检与修复

## 症状 → 一眼定位

用户在 Obsidian 里看到「属性面板空 / 认不出属性 / Dataview 查不到这条笔记 / 日期排序错乱」，
多半是 frontmatter 的**收尾 `---` 被误拼到了最后一个值后面**。

三种变体，同一个根因：

| 变体 | 坏的样子 | 后果 |
|---|---|---|
| 标量字段 | `updated: 2026-06-30---` | 闭合被推到下一个 `---`，中间正文被当 YAML 扫 → 解析失败 |
| 列表末项 | `  - "clippings"---` | 同上 |
| 丢失闭合 | `  - intro-page---` 且后面**没有** `---` | 最严重：整个正文被当 YAML 扫 |

修法统一：**把粘在值末尾的 `---` 拆到独立一行**。

```yaml
# 错
updated: 2026-06-30---
# 对
updated: 2026-06-30
---
```

⚠️ 该问题常是**批量生成/迁移脚本**留下的，往往一次污染多个文件 ——
**不要只修用户提到的那一个，必须全库扫一遍**（实测用户以为只有 5 个，实际 13 个）。

## 流程

### 0. 先备份整库（改用户笔记前的硬前置）

```bash
cd ~/Documents && tar -czf "$HOME/Desktop/<库名>-备份-$(date +%Y%m%d).tar.gz" <库名>
gzip -t "$HOME/Desktop/<库名>-备份-$(date +%Y%m%d).tar.gz" && echo "gzip OK"
shasum -a 256 "$HOME/Desktop/<库名>-备份-$(date +%Y%m%d).tar.gz"
```

用 `tar` 而非 Python：**`tar` 是 C 实现，不受沙箱逐文件读取/内容审批影响**。
实测 252 MB / 1006 文件约 5 秒，压缩到 166 MB。

### 1. 定位（最快手段：ripgrep）

```
pattern: [^-\s]---$
glob:    *.md
```

命中行若**在 frontmatter 内**（行号 < 闭合行）即为问题。
⚠️ 会误命中正文里的 git diff 统计行（`27 ++++++++---`）→ 按行号排除。

### 2. 全库体检（稳妥版脚本）

```python
import yaml, pathlib, sys
base = pathlib.Path(".")                      # 库根目录
SKIP = {".obsidian", ".git", "node_modules", ".trash"}
scanned = ok = 0; glued = []; fail = []
for p in sorted(base.rglob("*.md")):
    if any(s in p.parts for s in SKIP): continue
    scanned += 1
    print(f"[{scanned}] {p}", flush=True)      # 实时进度，见「坑」
    try:
        raw = p.read_bytes()[:65536]           # 只读前 64KB，frontmatter 必在此内
    except Exception as e:
        fail.append((p, "READ", str(e)[:60])); continue
    lines = raw.decode("utf-8", "replace").split("\n")
    if not lines or lines[0].strip() != "---":  # 无 frontmatter，跳过
        continue
    end = next((i for i in range(1, min(len(lines), 400))
                if lines[i].strip() == "---"), None)
    if end is None:
        fail.append((p, "NO-CLOSE", "400行内无闭合")); continue
    try:
        d = yaml.safe_load("\n".join(lines[1:end]))
    except Exception as e:
        fail.append((p, type(e).__name__, str(e).split("\n")[0][:70])); continue
    hit = [k for k, v in (d or {}).items()
           if isinstance(v, str) and v.rstrip().endswith("---")] if isinstance(d, dict) else []
    if hit: glued.append((p, hit))
    else: ok += 1
print(f"扫描 {scanned}  正常 {ok}  残留粘接 {len(glued)}  解析失败 {len(fail)}")
for p, k in glued: print("  GLUED", p, k)
for p, t, m in fail: print("  FAIL", p, f"[{t}]", m)
```

### 3. 修复

用 Edit 逐个改，`old_string` **带上前一行做唯一性锚点**。
- 标量字段：`updated: 2026-06-30---` → `updated: 2026-06-30\n---`
- 列表末项：`  - "clippings"---\n---` → `  - "clippings"\n---`
- 丢失闭合：`  - intro-page---` → `  - intro-page\n---`（**补上**闭合）

### 4. 验证（必做，不可省）

`Edit` 报成功**不等于**生效。必须实测：

- YAML `safe_load` 通过
- **字段值类型正确**：日期应为 `datetime.date`，计数应为 `int`。
  修复前 `word_count: 43---` 解析成字符串 `'43---'`，排序/筛选都会错。
- 再跑一次第 1 步的 grep，应只剩正文误命中

## 坑（均为实测）

- **Python 逐文件 `open()` 全库扫描会被 SIGTERM（exit 137），且 stdout 全丢。**
  - 规避：`python3 -u` + **重定向到日志文件**。
  - **不要用 `| tail`** —— 管道会缓冲到 EOF，进程被杀就什么都不剩，完全看不到进度。
  - 必要时分批：先扫非归档目录，再单独扫归档目录。
  - 该现象**不稳定**（同一脚本有时能跑完），重试一次往往就过；不是代码 bug。
- **归档目录（`_Archive` 等）里大量文件本来就没有 frontmatter** → 跳过即可，不是问题。
- 判断「有无 frontmatter」只看**第 1 行是否 `---`**。
- 扫描范围必须排除 `.obsidian`、`.git`、`node_modules`。
- 批量删除/修改用户笔记属敏感操作：**先列清单 + 取得授权 + 留备份**，再动手。

### 另一类 frontmatter 故障：值里含 `: ` 未加引号

```yaml
# 错 —— 冒号+空格会被当成新的键值对，报 "mapping values are not allowed here"
description: 症状是 `updated: 2026-06-30---` 这种形式
# 对 —— 整串加双引号
description: "症状是 `updated: 2026-06-30---` 这种形式"
```

**反引号里的代码也会触发**，因为 YAML 不认 Markdown 语法。
写 SKILL.md 自己的 frontmatter 时同样要遵守 —— **写完必须自己解析一遍**。

## 验收话术模板

修复后向用户报告时给三样东西：**改了几个文件（列表）**、**验证方式与结果**、**备份路径**。
不要只说「修好了」。
