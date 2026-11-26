# 扩展商店提交手册模板

> 复制到项目 `SUBMISSION-v<version>.md` 或并入 `PUBLISHING.md`，按实际商店删改。

## v<version> 提交手册

### Chrome Web Store

入口：https://chrome.google.com/webstore/devconsole

| 步骤 | 内容 | 状态 |
|---|---|---|
| 1 | 上传 `dist/<package>-chrome.zip` | ☐ |
| 2 | 商品详情：标题/摘要自动，详细描述按项目 PUBLISHING.md 抄 | ☐ |
| 3 | 截图上传（1280×800） | ☐ |
| 4 | 隐私权：Single purpose → 权限理由逐框 → Remote code: No → Data usage → Limited use → 隐私政策 URL | ☐ |
| 5 | 分发：Public / 免费 / 目标地区 | ☐ |
| 6 | 提交审核 | ☐ |

提交后记录：

- 扩展 ID：``
- 提交时间：``
- 状态：

### Edge Add-ons

入口：https://partner.microsoft.com/dashboard/microsoftedge

| 步骤 | 内容 | 状态 |
|---|---|---|
| 1 | 上传 `dist/<package>-edge.zip` | ☐ |
| 2 | 名称/简述自动，详细描述按项目 PUBLISHING.md 抄 | ☐ |
| 3 | 截图 + Logo | ☐ |
| 4 | 隐私政策 URL + 可见性 | ☐ |
| 5 | 提交审核 | ☐ |

提交后记录：

- Store ID：``
- CRX ID：``
- Product ID：``
- 提交时间：``
- 状态：

### 审核通过后回填项

- [ ] README 补商店安装链接
- [ ] `PROJECT.md` 商店标识表补上线 URL
- [ ] `PUBLISHING.md` 提交记录补通过时间
