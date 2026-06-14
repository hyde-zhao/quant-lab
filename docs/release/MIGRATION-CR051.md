---
status: "READY"
version: "1.0"
change_id: "CR-051"
created_at: "2026-06-14T09:00:24+08:00"
---

# Migration Notes: CR051

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-14 | host-orchestrator | 初版 CR051 迁移说明，明确当前只交付迁移计划，不执行真实迁移 |

## 当前迁移结论

| 项目 | 结论 |
|---|---|
| 项目正式名 | `quant-lab` |
| legacy alias | `local_backtest` 保留为历史审计名 |
| 当前目录重命名 | N/A，未授权 |
| 远端仓库改名 | N/A，未授权 |
| README / USER-MANUAL / pyproject 改名 | 后续 CR054 评估 |
| NAS / archive migration | 后续 CR053 评估并单独授权 |

## 后续迁移门禁

真实迁移必须先完成 inventory、forbidden content scan、rollback_ref、用户单独授权和 dry-run，不得从 CR051 CP8 approve 推导授权。

