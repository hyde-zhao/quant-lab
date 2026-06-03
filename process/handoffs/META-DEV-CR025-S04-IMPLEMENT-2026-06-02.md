---
handoff_id: "META-DEV-CR025-S04-IMPLEMENT-2026-06-02"
from: "meta-po"
to: "meta-dev"
change_id: "CR-025"
story_id: "CR025-S04-backtrader-module-reference-no-copy-guardrail"
wave_id: "CR025-W1-FEED-GOVERNANCE"
status: "completed-closed"
created_at: "2026-06-02T07:33:45+08:00"
updated_at: "2026-06-02T07:41:20+08:00"
---

# META-DEV Handoff: CR025-S04 Implementation

## Dispatch

| 字段 | 值 |
|---|---|
| mode | `spawn_agent` |
| tool_name | `multi_agent_v1.spawn_agent` |
| agent_role | `meta-dev` |
| agent_name | `dev-xu` |
| agent_id | `019e8589-2c7b-7173-8aa5-1f8a327375fb` |
| thread_id | `019e8589-2c7b-7173-8aa5-1f8a327375fb` |
| spawned_at | `2026-06-02T07:33:45+08:00` |
| completed_at | `2026-06-02T07:37:38+08:00` |
| closed_at | `2026-06-02T07:41:20+08:00` |

## Scope

实现 `CR025-S04-backtrader-module-reference-no-copy-guardrail`，只允许受控离线 / fixture / 静态合同实现。

## Inputs

- `process/stories/CR025-S04-backtrader-module-reference-no-copy-guardrail.md`
- `process/stories/CR025-S04-backtrader-module-reference-no-copy-guardrail-LLD.md`
- `process/HLD.md`
- `process/ARCHITECTURE-DECISION.md`
- `checkpoints/CP5-CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT-BATCH-A-LLD-BATCH.md`

## Allowed Write Scope

- `docs/CR025-BACKTRADER-MODULE-REFERENCE.md`
- `tests/test_cr025_backtrader_no_copy_guardrail.py`
- `process/checks/CP6-CR025-S04-backtrader-module-reference-no-copy-guardrail-CODING-DONE.md`

## Not Authorized

- 修改 `pyproject.toml` / `uv.lock` 或安装依赖。
- 运行 Backtrader backend / samples / tests。
- 读取、复制、裁剪、改写或源码级移植 `/home/hyde/download/backtrader/**` 或 Backtrader GPLv3 源码。
- provider fetch、lake write、publish、QMT / MiniQMT / XtQuant、broker、simulation/live、凭据读取。
- 实现多因子研究主框架、FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪或策略准入包。

## Expected Output

- S04 文档与 guardrail 测试补丁。
- S04 定向测试结果。
- CP6 coding done 检查文件。
