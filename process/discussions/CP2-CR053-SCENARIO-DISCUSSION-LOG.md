---
cr_id: CR-053
discussion_id: CP2-CR053-SCENARIO-DISCUSSION
status: approved
owner: host-orchestrator
created_at: 2026-06-14T09:39:26+08:00
---

# CP2 CR053 场景讨论日志

## 背景

用户在 CR051 关闭后回复“cr053”。CR051 关闭状态中的下一步建议是单独启动 `CR053 migration inventory / dry-run`，但 CR051 原后续表中曾把 `CR053-candidate` 写成事件型策略研究流程。本日志记录该编号冲突和迁移 dry-run 的用户可见场景。

## Scenario Gray Areas

| 问题 ID | 问题 | 推荐方案 | 当前结论 | 影响 |
|---|---|---|---|---|
| SGQ-CR053-01 | `cr053` 是否解释为迁移 inventory / dry-run？ | 是。按最新 STATE / CR-INDEX 和用户当前指令启动迁移盘点 / dry-run。 | 用户已回复“好的，同意” | 避免把本轮误转到事件型策略研究。 |
| SGQ-CR053-02 | CR053 是否可以执行真实目录迁移？ | 不可以。CR053 CP2 只放行 CP3 设计。 | 用户已回复“好的，同意” | 防止提前移动目录、改远端或破坏恢复点。 |
| SGQ-CR053-03 | inventory 是否包含 NAS / 外部 archive？ | 首版不包含。只设计 Git 内 inventory / dry-run；NAS 和外部 archive 另行授权。 | 用户已回复“好的，同意” | 避免访问外部存储和大数据。 |
| SGQ-CR053-04 | 是否允许读取 `.env` 或凭据定位敏感路径？ | 不允许。敏感路径只能通过文件名 / ignore / manifest 规则静态识别，不读内容。 | 用户已回复“好的，同意” | 维持凭据边界。 |
| SGQ-CR053-05 | 旧事件型策略 CR053 候选如何处理？ | 改号为 `CR057-candidate`，不删除。 | 用户已回复“好的，同意” | 保留策略路线追溯，释放 CR053 给迁移 dry-run。 |

## 冻结场景草案

| 场景 ID | 场景 | 预期 |
|---|---|---|
| SC-CR053-01 | 仓库路径 inventory | 识别当前 Git 仓库内代码、docs、process、research docs、脚本、测试、报告和潜在 archive / output 边界。 |
| SC-CR053-02 | 路径引用 dry-run | 识别 README、docs、process、pyproject、脚本中的 `local_backtest` / 旧路径引用，形成不改写报告。 |
| SC-CR053-03 | 禁止内容分类 | 识别凭据、账户、真实数据、大 artifact、broker facts 的规则和检查边界，不读取秘密内容。 |
| SC-CR053-04 | Git 归档点设计 | 明确 pre-inventory、pre-file-move、post-mechanical-move、post-reference-fix 的提交 / tag 建议。 |
| SC-CR053-05 | 真实迁移门禁 | mechanical move、NAS migration、remote rename、push/tag 都必须另起授权门。 |
| SC-CR053-06 | 编号冲突修正 | 迁移 CR 使用 CR053；事件型策略候选改为 CR057。 |

## 不授权项

| 项目 | 状态 |
|---|---|
| 真实目录重命名 / 文件移动 | not-authorized |
| 远端仓库改名 | not-authorized |
| git push / tag publish / 重写历史 | not-authorized |
| NAS scan / mount / copy / delete / migration | not-authorized |
| external archive migration execution | not-authorized |
| provider fetch / lake write / catalog publish | not-authorized |
| QMT / MiniQMT import / connection / runtime | not-authorized |
| `.env`、token、account_id、账号、密码、session、cookie、private key 读取 | not-authorized |
| submit / cancel / simulation / live trading | not-authorized |
| CR046 CP7 验证或关闭 | not-authorized |
