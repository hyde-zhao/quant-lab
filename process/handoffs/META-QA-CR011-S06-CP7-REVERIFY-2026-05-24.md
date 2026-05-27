---
handoff_id: "META-QA-CR011-S06-CP7-REVERIFY-2026-05-24"
from_agent: "meta-po"
to_agent: "meta-qa"
agent_name: "qa-jin the 2nd"
change_id: "CR-011"
story_id: "CR011-S06-industry-market-cap-style-exposure-data"
wave_id: "CR011-DATA-BATCH-A-VERIFY-W6-REVERIFY"
blocker_id: "CR011-S06-CP7-F01"
status: "completed"
created_at: "2026-05-24T14:52:22+08:00"
updated_at: "2026-05-24T14:59:28+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e58c2-6271-7131-adf0-5e026d7680af"
  thread_id: "019e58c2-6271-7131-adf0-5e026d7680af"
  tool_name: "spawn_agent"
  spawned_at: "2026-05-24T14:53:20+08:00"
  completed_at: "2026-05-24T14:55:35+08:00"
  closed_at: "2026-05-24T14:59:28+08:00"
  result: "completed"
---

# META-QA CR011-S06 CP7 复验交接

## 任务

对 `CR011-S06-industry-market-cap-style-exposure-data` 执行 CP7 复验，重点确认 `CR011-S06-CP7-F01` 已关闭：metadata 必须包含 canonical `float_market_cap_availability`，且 `float_market_cap` alias 不破坏兼容性。

本次复验仍需确认 S06 原 CP7 的核心验收项、相关回归和安全边界；若 PASS，请写复验 CP7 并将 Story 标记为 `verified`。若 FAIL / BLOCKED，不得标记 verified。

## 输入

| 类型 | 路径 | 状态 |
|---|---|---|
| Story | `process/stories/CR011-S06-industry-market-cap-style-exposure-data.md` | ready-for-verification |
| LLD | `process/stories/CR011-S06-industry-market-cap-style-exposure-data-LLD.md` | confirmed |
| 原 CP6 | `process/checks/CP6-CR011-S06-industry-market-cap-style-exposure-data-CODING-DONE.md` | PASS |
| 首次 CP7 | `process/checks/CP7-CR011-S06-industry-market-cap-style-exposure-data-VERIFICATION-DONE.md` | FAIL / `CR011-S06-CP7-F01` |
| blocker-fix CP6 | `process/checks/CP6-CR011-S06-CP7-BLOCKER-FIX-CODING-DONE.md` | PASS |
| blocker-fix handoff | `process/handoffs/META-DEV-CR011-S06-CP7-FIX-2026-05-24.md` | completed |
| 上游 CR008-S06 | `process/checks/CP7-CR008-S06-factor-research-auxiliary-data-contract-VERIFICATION-DONE.md` | PASS |
| 上游 CR011-S02 | `process/checks/CP7-CR011-S02-pit-universe-and-stock-lifecycle-completion-VERIFICATION-DONE.md` | PASS |
| 上游 CR011-S05 | `process/checks/CP7-CR011-S05-adjustment-and-corporate-action-audit-VERIFICATION-DONE.md` | PASS |

## 允许写入范围

- `process/checks/CP7-CR011-S06-industry-market-cap-style-exposure-data-REVERIFY-DONE.md`
- `process/stories/CR011-S06-industry-market-cap-style-exposure-data.md` 的验证状态字段

## 禁止范围

- 不修改生产代码或测试代码，除非先在 CP7 复验文件写明 FAIL / BLOCKED。
- 不实现或修改 `CR011-S07`、`CR011-S08`。
- 不修改 `process/STATE.md`、`process/STORY-STATUS.md`、`process/DEVELOPMENT-PLAN.yaml`。
- 不修改 `market_data/connectors/**`、`market_data/runtime.py`、`market_data/storage.py`、`data/**`、`.env`、`reports/experiment_17_21/factor_strategy_report.md`、`delivery/**`。
- 不真实联网，不真实 Tushare 抓取，不写真实 lake。
- 不读取、打印或记录 `.env`、token、密码、私钥、cookie、session 或其他凭据。
- 不读取、列出、迁移、复制、删除旧 `data/**`。
- 不覆盖旧 `reports/experiment_17_21/factor_strategy_report.md`。

## 必查项

- CP7 复验文件必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables 和 Agent Dispatch Evidence。
- 验证 blocker-fix CP6 调度证据：`dispatch.mode=spawn_agent`，agent/thread id=`019e58b9-c810-75e2-b93c-cb90dcc60000`，completed/closed 已回填。
- 验证 canonical 字段：`float_market_cap_availability` 必须在生产代码和测试中存在，metadata top-level 输出必须可断言。
- 验证 alias：`float_market_cap` 可作为兼容 alias，但不得替代 canonical 字段。
- 复核 S06 原验收项：行业、市值、流通市值、style exposure availability；PIT as-of gate；neutralization / pure alpha / risk-model-adjusted claims 阻断；不伪造风险模型。
- 验证相关回归和安全边界：`network_calls=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_operations=0`、旧报告覆盖次数 0。

## 建议验证命令

- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile engine/research_dataset.py tests/test_cr011_exposure_claims.py`
- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr011_exposure_claims.py`
- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr011_adjustment_audit.py tests/test_cr011_pit_universe_lifecycle.py tests/test_cr008_factor_auxiliary_data_contract.py tests/test_cr011_execution_price_policy.py tests/test_cr011_benchmark_policy_consumption.py`
- `rg -n "float_market_cap_availability" engine/research_dataset.py tests/test_cr011_exposure_claims.py process/stories/CR011-S06-industry-market-cap-style-exposure-data.md process/stories/CR011-S06-industry-market-cap-style-exposure-data-LLD.md`

## 期望输出

| 交付物 | 路径 |
|---|---|
| CP7 复验完成检查 | `process/checks/CP7-CR011-S06-industry-market-cap-style-exposure-data-REVERIFY-DONE.md` |
| Story 验证状态 | `process/stories/CR011-S06-industry-market-cap-style-exposure-data.md` |
