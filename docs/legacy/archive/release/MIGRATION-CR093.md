---
status: ready
cr_id: CR-093
---

# CR093 Migration

## 迁移结论

| 项目 | 结论 | 说明 |
|---|---|---|
| 数据迁移 | N/A | 不读写业务数据、market data、reports 或 lake |
| 配置迁移 | N/A | 不新增环境变量或配置 |
| 状态 schema | N/A | 不改变 process/STATE schema，只改变 checker 对历史文本的解释 |
| CLI 参数 | N/A | `meta-flow check cr-tracking` 参数不变 |
| 安装路径 | N/A | 不改变安装目录；外部 checker 源代码语义修复 |

## 兼容性说明

CR093 对历史状态采用归一解释，不要求旧账本全文重写。历史审计文本保留；当前状态仍以顶层 `active_change`、正式 CR frontmatter、CR-INDEX 和 follow-up tracking 当前表格为准。
