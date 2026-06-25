---
status: ready
cr_id: CR-095
---

# CR095 Feedback

## 观察信号

| Signal ID | 信号 | 阈值 | 处理 |
|---|---|---|---|
| FB-CR095-01 | standalone checker 与主 CLI summary 再次不一致 | 任意 active / blocked / candidate / spike 摘要差异 | 创建后续 issue 或 CR |
| FB-CR095-02 | 下游脚本依赖旧 stdout 第一行 | 用户反馈解析失败 | 评估是否增加 `--summary/--no-summary` 参数或文档迁移说明 |

## 后续候选

当前无新增后续 CR 候选；如发现 stdout 兼容性问题，先记录反馈，再由用户明确选择是否启动新 CR。
