## 为什么改

<!-- 关联 Issue，说明当前问题或触发这次改动的具体场景。 -->
Closes #

## 改了什么

-

## 没改什么 / 已知限制

-

## 怎么验证

```bash
python3 -m py_compile wechat-mp-publisher/scripts/*.py && python3 -m py_compile xhs-pipeline-lingyi/xhs_pipeline_lingyi.py
```

- [ ] 已执行上述检查并附上关键输出
- [ ] 涉及界面、安装流程或交互时，已检查对应的桌面、移动端或操作系统

## 影响面

- [ ] 无破坏性变更
- [ ] 涉及配置项、CLI 参数、发布流程或数据迁移（说明回滚方式）

## 提交前

- [ ] 提交标题符合 `type(scope): subject`
- [ ] 未提交密钥、token、用户数据、日志或生成产物
- [ ] 已确认改动范围只覆盖：微信公众号与小红书发布流程
