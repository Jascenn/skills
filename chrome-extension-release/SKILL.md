---
name: chrome-extension-release
description: 编排一次 Chrome / Edge 扩展完整发版：前置检查→版本确认→build/verify→商店材料检查→tag/GitHub Release→生成提交手册→人工提交步骤清单。适用于任何基于 manifest.json 的 MV3 扩展项目。触发词：发版、上架、release、chrome web store、edge add-ons、提交商店。
---

# Chrome / Edge 扩展发版编排

本 skill 只做**编排与判断**，不隐藏构建逻辑。构建、验证、打包一律调项目自身脚本；商店字段口径与提交模板见 [references/](references/)。项目参数（build 命令、仓库路径、隐私政策 URL、权限理由）从项目根的 `PROJECT.md` 和 `PUBLISHING.md` 读，不在这里硬编码。

## 流程

### 1. 前置检查

```bash
git status --short                 # 必须干净
```

任一不满足 → 停止，报告，不继续。项目如有 lint/test，按其 `PUBLISHING.md` 或 package.json 定义的脚本执行，全绿才继续。

### 2. 版本确认

版本号唯一来源：项目 `manifest.json` 的 `version`。

- 新版本：同步 bump `manifest.json`，并在 `CHANGELOG.md` 顶部新增 `## [<version>] - YYYY-MM-DD` 条目。
- 已发版本复跑（同版本重打）：版本号不动，把新变更合并进 CHANGELOG 既有条目；后续 tag/release 走「重打」分支。

### 3. 构建、验证、打包

按项目 `PUBLISHING.md` 的构建章节执行，典型形式：

```bash
./build.sh --all                  # 产出 dist/*-chrome.zip 和 dist/*-edge.zip
```

产物校验要点（项目脚本应已内置，不在 skill 里重复实现）：
- zip 根有 `manifest.json`
- 无 `__MACOSX` / `.DS_Store`
- 图标尺寸与 manifest 声明一致
- description ≤ 132 字符

### 4. 商店材料 freshness

材料涉及截图、图标、隐私政策链接，发版前逐项核对：

1. 截图尺寸符合目标商店要求（Chrome/Edge 均 1280×800 或 640×480）
2. 隐私政策 URL 指向当前 main 分支
3. `PUBLISHING.md` 权限理由与 manifest 当前权限一一对应（无遗漏、无多余）

权限或数据流向有变时：先改 `PRIVACY.md` 事实层，再改 `PUBLISHING.md` 文案层，最后同步 README。

### 5. 终验

项目定义了 test / e2e / lint 则全部跑绿，没有则跳过此步，不伪造结果。

### 6. 提交、tag、GitHub Release

```bash
git add -A && git commit -m "Release v<version>"
git tag v<version> && git push origin main --tags
gh release create v<version> dist/<package>.zip --title "v<version>" --notes-file <(awk '/^## \[/{n++} n==1' CHANGELOG.md)
```

- 上传 zip 用项目实际产物名，从 `dist/` 确认，不猜。
- awk 提取当前版本 CHANGELOG 段落（截取到下一个 `## ` 前）；不要用 `head -n -1`（BSD head 不支持负数行数）。
- gh 认证失败 → 报告并跳过 release，不伪造结果。

**重打分支**（版本号未变、tag 已存在）：`git commit --amend` 并入原提交 → `git push origin main` → `git tag -f v<version> && git push -f origin v<version>` → `gh release delete v<version> --yes` 后重新 create（旧 zip 作废，上传新 zip）。

### 7. 提交手册

按 [references/submission-template.md](references/submission-template.md) 在项目 `PUBLISHING.md` 或独立文件 `SUBMISSION-v<version>.md` 里落一版，内容含：

- 目标商店、上传包路径、版本号
- 每个商店 tab 要填什么（从项目 `PUBLISHING.md` 抄口径，skill 不复制字段内容）
- 提交后要记录的标识符（扩展 ID、Store ID、Product ID 等）

### 8. 提交后人工步骤（告知用户）

商店提交是人工动作，AI 不代填。生成清单后告知用户逐项操作：

1. 打开各商店开发者后台，按提交手册逐 tab 填写
2. 提交审核
3. 记录返回的商店标识符，回填项目 `PROJECT.md` 商店标识表和 `PUBLISHING.md` 提交记录
4. 审核通过后：README 补商店链接，`PROJECT.md` 回填上线 URL

## 边界

- 不自动 commit/push，除非用户明确说 commit/push。
- 不代填商店后台（涉及登录），只生成清单。
- 遇到与项目 `PUBLISHING.md` 冲突的指令，以项目文档为准，报告差异。
