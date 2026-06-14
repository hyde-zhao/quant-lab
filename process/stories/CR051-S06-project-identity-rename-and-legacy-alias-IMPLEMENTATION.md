---
story_id: "CR051-S06-project-identity-rename-and-legacy-alias"
status: "implemented-cp6"
owner: "host-orchestrator"
implemented_at: "2026-06-14T09:00:24+08:00"
cp6_check: "process/checks/CP6-CR051-S06-project-identity-rename-and-legacy-alias-CODING-DONE.md"
---

# CR051-S06 Implementation

## 实现对象

| 对象 | 路径 | 结果 |
|---|---|---|
| project identity migration | `docs/research/PROJECT-IDENTITY-MIGRATION.md` | 已创建 |

## 设计契约映射

| 技术说明契约 | 实现位置 | 验证 |
|---|---|---|
| `quant-lab` canonical name | `PROJECT-IDENTITY-MIGRATION.md` §Identity Contract | 静态 review |
| `local_backtest` legacy alias | `PROJECT-IDENTITY-MIGRATION.md` §Alias Policy | 静态 review |
| 不执行真实 rename / push / history rewrite | `PROJECT-IDENTITY-MIGRATION.md` §禁止项 | guardrail review |

## 验证摘要

- 本 Story 只创建迁移计划文档。
- 未修改目录、远端、package metadata、README、USER-MANUAL 或历史审计文件。

