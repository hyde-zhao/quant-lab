---
handoff_id: "META-DEV-CR018-S01-IMPLEMENT-2026-05-29"
from: "meta-po"
to: "meta-dev"
workflow_id: "local_backtest-cr018"
change_id: "CR-018"
story_id: "CR018-S01-production-current-truth-definition-and-dataset-groups"
wave_id: "CR018-W1-SCOPE-CONTRACT"
status: "completed-closed"
created_at: "2026-05-29T08:25:12+08:00"
dispatch:
  mode: "spawn_agent"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e7126-854e-7891-8e54-738187c8f2a6"
  thread_id: "019e7126-854e-7891-8e54-738187c8f2a6"
  agent_name: "dev-you"
  spawned_at: "2026-05-29T08:33:38+08:00"
  completed_at: "2026-05-29T08:42:04+08:00"
  closed_at: "2026-05-29T08:45:06+08:00"
---

# META-DEV Handoff: CR018-S01 Implementation

## Mission

实现 `CR018-S01-production-current-truth-definition-and-dataset-groups`。

本 Story 已通过 CP5，全量 LLD 批次已 approved。只允许受控离线 / fixture / dry-run 代码实现；严禁读取 `.env`、打印或保存 token、真实 provider fetch、真实 lake 写入、catalog current pointer publish、DuckDB 依赖变更或任何 QMT 操作。

## Required Inputs

| 类型 | 路径 |
|---|---|
| Story | `process/stories/CR018-S01-production-current-truth-definition-and-dataset-groups.md` |
| LLD | `process/stories/CR018-S01-production-current-truth-definition-and-dataset-groups-LLD.md` |
| CP5 auto | `process/checks/CP5-CR018-S01-production-current-truth-definition-and-dataset-groups-LLD-IMPLEMENTABILITY.md` |
| CP5 manual | `checkpoints/CP5-CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A-LLD-BATCH.md` |
| HLD / ADR | `process/HLD-DATA-LAKE.md` §19；`process/ARCHITECTURE-DECISION.md` ADR-062 / ADR-063 |

## Write Scope

| 类型 | 路径 | 规则 |
|---|---|---|
| primary | `market_data/release_scope.py` | 创建 release scope、2015 前 blocked reason、permission counters 合同。 |
| primary | `market_data/dataset_groups.py` | 创建 P0/P1 dataset group、claim matrix、readiness summary 合同。 |
| primary | `tests/test_cr018_release_scope_dataset_groups.py` | 创建离线合同测试。 |
| shared | `market_data/catalog.py` | 只允许增加 release scope / dataset group metadata helper；不得 publish current pointer。 |
| shared | `README.md`、`docs/USER-MANUAL.md` | 只允许增加 scoped release / dataset group / blocked claims 说明。 |

禁止修改：`process/REQUIREMENTS.md`、`process/USE-CASES.md`、`process/HLD.md`、`process/HLD-DATA-LAKE.md`、`process/ARCHITECTURE-DECISION.md`、`pyproject.toml`、`uv.lock`、`.env`、任何凭据文件、provider connector、真实 lake 数据文件、QMT 运行入口。

## Expected Implementation

1. 创建 `market_data/release_scope.py`，至少覆盖：
   - `ReleaseScope`
   - `ReleaseScopeResult`
   - `resolve_release_scope`
   - 2015 前 since-inception / pre-2015 claim 的 `blocked/future_backfill`
   - permission counters 默认全 0
2. 创建 `market_data/dataset_groups.py`，至少覆盖：
   - P0 / P1 dataset group registry
   - `required_for_publish`
   - P1 缺失阻断行业中性、市值中性、纯 alpha、容量、scale_up / 资金放大等声明
   - 未登记 dataset 阻断 readiness
   - JSON-ready readiness summary
3. 如确有必要，给 `market_data/catalog.py` 增加只读 metadata helper，不得调用 publish 或写 current pointer。
4. 创建离线测试，执行：
   - `uv run --python 3.11 pytest -q tests/test_cr018_release_scope_dataset_groups.py`
5. 若测试通过，写入 CP6：
   - `process/checks/CP6-CR018-S01-production-current-truth-definition-and-dataset-groups-CODING-DONE.md`

## CP6 Requirements

CP6 文件必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence 和结论。结论只能在以下条件满足时写 PASS：

- S01 离线测试 PASS。
- 未读取 `.env` 或凭据。
- provider fetch / lake write / current pointer publish / QMT operation 计数均为 0。
- 未改 `pyproject.toml` / `uv.lock`。
- 未触碰真实 lake 数据。

## Output Summary Required

完成后请在最终回复中列出：

- 修改文件列表。
- 执行的测试命令和结果。
- CP6 文件路径。
- 明确说明真实操作计数仍为 0。
