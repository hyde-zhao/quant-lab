---
handoff_id: "META-DEV-CR011-S05-IMPLEMENT-2026-05-24"
from_agent: "meta-po"
to_agent: "meta-dev"
agent_name: "dev-xu the 2nd"
change_id: "CR-011"
story_id: "CR011-S05-adjustment-and-corporate-action-audit"
wave_id: "CR011-DATA-BATCH-A-DEV-W5"
status: "closed-after-cp6-output"
created_at: "2026-05-24T13:27:28+08:00"
updated_at: "2026-05-24T13:54:37+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e5874-b0e9-75e2-94c6-53819d4fff14"
  thread_id: "019e5874-b0e9-75e2-94c6-53819d4fff14"
  tool_name: "spawn_agent"
  spawned_at: "2026-05-24T13:28:30+08:00"
  resumed_at: ""
  completed_at: "2026-05-24T13:43:54+08:00"
  closed_at: "2026-05-24T13:54:37+08:00"
  result: "shutdown_after_cp6_output"
---

# META-DEV CR011-S05 实现交接

## 任务

实现 `CR011-S05-adjustment-and-corporate-action-audit` 的离线代码与 CP6 自检。目标是在 reader / research dataset 层补齐复权 lineage、公司行动 availability 与 adjustment audit gate，使缺公司行动时阻断完整审计声明，复权口径混用时不得进入因子计算。

你不是独占代码库：当前工作树已有 CR011-S01..S04 的实现和复验修复。不得回退他人修改；若发现冲突，按现有实现适配，并在 CP6 写清楚。

## 输入

| 类型 | 路径 | 状态 |
|---|---|---|
| Story | `process/stories/CR011-S05-adjustment-and-corporate-action-audit.md` | dev-ready |
| LLD | `process/stories/CR011-S05-adjustment-and-corporate-action-audit-LLD.md` | confirmed / implementation_allowed |
| CP5 自动预检 | `process/checks/CP5-CR011-S05-adjustment-and-corporate-action-audit-LLD-IMPLEMENTABILITY.md` | PASS |
| CP5 批次人工确认 | `checkpoints/CP5-CR011-DATA-BATCH-A-LLD-BATCH.md` | approved |
| 上游 runtime | `process/checks/CP7-CR010-S02-prices-adj-factor-history-backfill-loop-VERIFICATION-DONE.md` | verified |
| 上游 contract | `process/checks/CP7-CR008-S04-quality-adjustment-label-window-gates-VERIFICATION-DONE.md` | verified |
| S04 已验证 | `process/checks/CP7-CR011-S04-ohlcv-vwap-clean-execution-feed-REVERIFY-DONE.md` | PASS |

## 允许写入范围

- `market_data/readers.py`
- `engine/research_dataset.py`
- `tests/test_cr011_adjustment_audit.py`
- `process/checks/CP6-CR011-S05-adjustment-and-corporate-action-audit-CODING-DONE.md`
- `process/stories/CR011-S05-adjustment-and-corporate-action-audit.md` 的实现状态字段

## 禁止范围

- 不实现或修改 `CR011-S06` 至 `CR011-S08`。
- 不修改 `market_data/connectors/**`、`market_data/runtime.py`、`market_data/storage.py`、`data/**`、`.env`、`reports/experiment_17_21/factor_strategy_report.md`、`delivery/**`。
- 不真实联网，不真实 Tushare 抓取，不写真实 lake。
- 不读取、打印或记录 `.env`、token、密码、私钥、cookie、session 或其他凭据。
- 不读取、列出、迁移、复制、删除旧 `data/**`。
- 不覆盖旧 `reports/experiment_17_21/factor_strategy_report.md`。
- 不修改 `process/STATE.md`、`process/STORY-STATUS.md`、`process/DEVELOPMENT-PLAN.yaml`；这些由 meta-po 回填。

## 实现要点

- 在 `market_data/readers.py` 新增或等价实现：
  - `AdjustmentAuditRequest`
  - `AdjustmentAuditReaderResult`
  - `read_adjustment_audit_inputs`
  - `extract_adj_factor_lineage`
  - `evaluate_corporate_action_availability`
- 在 `engine/research_dataset.py` 新增或等价实现：
  - `AdjustmentAuditResult`
  - `evaluate_adjustment_audit`
  - `apply_adjustment_audit_gate`
- 必须输出并验证 4 个必填字段：`adjustment_policy`、`adj_factor_lineage`、`corporate_action_status`、`adjustment_audit_status`。
- `adjustment_audit_status` 至少支持 `pass`、`required_missing`、`quality_failed`。
- 复权口径混用、policy mismatch、缺 `adj_factor` lineage 或 quality fail 不得进入因子计算；`mixed_adjustment_policy_count` 必须可审计。
- 缺公司行动、缺 explicit `available_at` 或 source/interface 未确认时，必须阻断 `corporate_action_audited`、`auditable_adjustment_chain`、`complete_corporate_action_audit` 等完整审计声明；但可保留 `adjusted_price_used` / `adjustment_policy_consistent` 等保守声明。
- 新 reader/helper 不得通过 env fallback 自动读取真实 lake；`lake_root=None` 应返回 typed missing 或使用显式传入的 fake reader。

## CP6 要求

CP6 文件必须写入：

- Entry Criteria、Checklist、Exit Criteria、Deliverables。
- Agent Dispatch Evidence：`spawn_agent`、agent id/thread id、handoff path、完成时间。
- 代码变更清单与 TASK-ID 对应关系。
- 验证命令和结果。
- 安全确认：`network_calls=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_operations=0`、旧报告覆盖次数 0。

## 建议验证命令

- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile market_data/readers.py engine/research_dataset.py tests/test_cr011_adjustment_audit.py`
- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr011_adjustment_audit.py`
- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr011_execution_price_policy.py tests/test_cr011_pit_universe_lifecycle.py tests/test_cr008_research_dataset_builder.py tests/test_cr008_factor_auxiliary_data_contract.py`

## 期望输出

| 交付物 | 路径 |
|---|---|
| reader / audit 实现 | `market_data/readers.py`、`engine/research_dataset.py` |
| S05 测试 | `tests/test_cr011_adjustment_audit.py` |
| CP6 编码完成检查 | `process/checks/CP6-CR011-S05-adjustment-and-corporate-action-audit-CODING-DONE.md` |
| Story 实现状态 | `process/stories/CR011-S05-adjustment-and-corporate-action-audit.md` |

若 CP6 PASS，请将 Story 状态推进为 `ready-for-verification`；若实现发现上游合同或授权阻断，请写 CP6 `BLOCKED` 并停止，不得扩大范围。
