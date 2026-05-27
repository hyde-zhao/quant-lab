---
handoff_id: "META-QA-CR011-S05-CP7-VERIFY-2026-05-24"
from_agent: "meta-po"
to_agent: "meta-qa"
agent_name: "qa-he the 2nd"
change_id: "CR-011"
story_id: "CR011-S05-adjustment-and-corporate-action-audit"
wave_id: "CR011-DATA-BATCH-A-VERIFY-W5"
status: "completed"
created_at: "2026-05-24T14:01:59+08:00"
updated_at: "2026-05-24T14:11:03+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e5894-193f-7be2-b18e-10085ef9ba4c"
  thread_id: "019e5894-193f-7be2-b18e-10085ef9ba4c"
  tool_name: "spawn_agent"
  spawned_at: "2026-05-24T14:02:47+08:00"
  completed_at: "2026-05-24T14:05:58+08:00"
  closed_at: "2026-05-24T14:11:03+08:00"
  result: "completed"
---

# META-QA CR011-S05 CP7 验证交接

## 任务

对 `CR011-S05-adjustment-and-corporate-action-audit` 执行 CP7 独立验证。重点验证复权 lineage、公司行动 availability、adjustment audit gate、metadata/claims 分层和安全边界。

## 输入

| 类型 | 路径 | 状态 |
|---|---|---|
| Story | `process/stories/CR011-S05-adjustment-and-corporate-action-audit.md` | ready-for-verification |
| LLD | `process/stories/CR011-S05-adjustment-and-corporate-action-audit-LLD.md` | confirmed |
| CP6 | `process/checks/CP6-CR011-S05-adjustment-and-corporate-action-audit-CODING-DONE.md` | PASS / adoption PASS |
| 原实现 handoff | `process/handoffs/META-DEV-CR011-S05-IMPLEMENT-2026-05-24.md` | closed-after-cp6-output |
| CP6 adoption handoff | `process/handoffs/META-DEV-CR011-S05-CP6-ADOPT-2026-05-24.md` | completed |
| S04 CP7 reverify | `process/checks/CP7-CR011-S04-ohlcv-vwap-clean-execution-feed-REVERIFY-DONE.md` | PASS |

## 允许写入范围

- `process/checks/CP7-CR011-S05-adjustment-and-corporate-action-audit-VERIFICATION-DONE.md`
- `process/stories/CR011-S05-adjustment-and-corporate-action-audit.md` 的验证状态字段

## 禁止范围

- 不修改生产代码或测试代码，除非先在 CP7 写明 FAIL / BLOCKED。
- 不实现或修改 `CR011-S06` 至 `CR011-S08`。
- 不修改 `process/STATE.md`、`process/STORY-STATUS.md`、`process/DEVELOPMENT-PLAN.yaml`。
- 不真实联网，不真实 Tushare 抓取，不写真实 lake。
- 不读取、打印或记录 `.env`、token、密码、私钥、cookie、session 或其他凭据。
- 不读取、列出、迁移、复制、删除旧 `data/**`。
- 不覆盖旧 `reports/experiment_17_21/factor_strategy_report.md`。
- 不写 `delivery/**`。

## 必查项

- CP7 必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables 和 Agent Dispatch Evidence。
- 验证 CP6 adoption 证据：原实现线程 `dev-xu the 2nd` 关闭前为 running，但已写 CP6；replacement `dev-he the 2nd` adoption PASS。
- 验证 `AdjustmentAuditRequest` / `AdjustmentAuditReaderResult` / `read_adjustment_audit_inputs` / `extract_adj_factor_lineage` / `evaluate_corporate_action_availability`。
- 验证 `AdjustmentAuditResult` / `evaluate_adjustment_audit` / `apply_adjustment_audit_gate`。
- 验证 4 个必填字段：`adjustment_policy`、`adj_factor_lineage`、`corporate_action_status`、`adjustment_audit_status`。
- 验证复权口径混用进入因子计算次数为 0。
- 验证公司行动缺失时完整公司行动审计声明输出次数为 0，并阻断 `corporate_action_audited`、`auditable_adjustment_chain`、`complete_corporate_action_audit`。
- 验证 `corporate_actions` 缺 explicit `available_at` 时为 `required_missing`，不得进入事件型决策。
- 验证 S04 execution policy / S01 benchmark / CR008 builder 兼容回归未被破坏。
- 验证默认路径 `network_calls=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_operations=0`。

## 建议验证命令

- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile market_data/readers.py engine/research_dataset.py tests/test_cr011_adjustment_audit.py`
- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr011_adjustment_audit.py`
- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr011_execution_price_policy.py tests/test_cr011_pit_universe_lifecycle.py tests/test_cr008_research_dataset_builder.py tests/test_cr008_factor_auxiliary_data_contract.py tests/test_cr011_benchmark_policy_consumption.py`

## 期望输出

| 交付物 | 路径 |
|---|---|
| CP7 验证完成检查 | `process/checks/CP7-CR011-S05-adjustment-and-corporate-action-audit-VERIFICATION-DONE.md` |
| Story 验证状态 | `process/stories/CR011-S05-adjustment-and-corporate-action-audit.md` |

若验证 PASS，可将 Story 状态推进为 `verified`；若 FAIL / BLOCKED，不得标记 verified，需列明阻断项、最小修复建议和最小回归集。
