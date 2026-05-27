---
handoff_id: "META-QA-CR011-S04-CP7-REVERIFY-2026-05-24"
from_agent: "meta-po"
to_agent: "meta-qa"
agent_name: "qa-hua the 2nd"
change_id: "CR-011"
story_id: "CR011-S04-ohlcv-vwap-clean-execution-feed"
wave_id: "CR011-DATA-BATCH-A-VERIFY-W4-RERUN1"
status: "completed"
created_at: "2026-05-24T13:16:23+08:00"
updated_at: "2026-05-24T13:21:41+08:00"
dispatch:
  mode: "resume_agent+send_input"
  agent_id: "019e585a-12bf-7721-affc-a0927f18c5c6"
  thread_id: "019e585a-12bf-7721-affc-a0927f18c5c6"
  tool_name: "resume_agent/send_input"
  spawned_at: ""
  resumed_at: "2026-05-24T13:17:17+08:00"
  completed_at: "2026-05-24T13:19:17+08:00"
  closed_at: "2026-05-24T13:21:22+08:00"
  result: "completed"
---

# META-QA CR011-S04 CP7 复验交接

## 任务

对 `CR011-S04-ohlcv-vwap-clean-execution-feed` 执行 CP7 复验，重点确认首次 CP7 阻断项 `CR011-S04-CP7-F01` 已关闭：`execution_price_policy` 对 mapping / string / backtest config / metadata 输入均保持 exact 四值语义。

## 输入

| 类型 | 路径 | 状态 |
|---|---|---|
| Story | `process/stories/CR011-S04-ohlcv-vwap-clean-execution-feed.md` | ready-for-verification |
| 首次 CP7 | `process/checks/CP7-CR011-S04-ohlcv-vwap-clean-execution-feed-VERIFICATION-DONE.md` | FAIL |
| blocker-fix CP6 | `process/checks/CP6-CR011-S04-CP7-BLOCKER-FIX-CODING-DONE.md` | PASS |
| blocker-fix handoff | `process/handoffs/META-DEV-CR011-S04-CP7-FIX-2026-05-24.md` | completed / closed |
| 原 CP6 | `process/checks/CP6-CR011-S04-ohlcv-vwap-clean-execution-feed-CODING-DONE.md` | PASS |
| S03 CP7 | `process/checks/CP7-CR011-S03-tradability-status-and-price-limit-gates-VERIFICATION-DONE.md` | PASS / verified |

## 允许写入范围

- `process/checks/CP7-CR011-S04-ohlcv-vwap-clean-execution-feed-REVERIFY-DONE.md`
- `process/stories/CR011-S04-ohlcv-vwap-clean-execution-feed.md` 的验证状态字段

## 禁止范围

- 不实现或修改 `CR011-S05` 至 `CR011-S08`。
- 不修改生产代码，除非发现验证阻断且先在 CP7 复验文件写明 FAIL / BLOCKED。
- 不真实联网，不真实 Tushare 抓取，不写真实 lake。
- 不读取、打印或记录 `.env`、token、密码、私钥、cookie、session 或其他凭据。
- 不读取、列出、迁移、复制、删除旧 `data/**`。
- 不覆盖 `reports/experiment_17_21/factor_strategy_report.md`。
- 不写 `delivery/**`。

## 必查项

- CP7 复验必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables 和 Agent Dispatch Evidence。
- 复验必须显式引用首次 CP7 FAIL 和 blocker-fix CP6 PASS。
- 重点确认 `" open "`、`""`、`" close_proxy "`、`OPEN`、`{"policy": " open "}`、`{"policy": ""}`、`{"execution_price_policy": " close_proxy "}`、`ExecutionPolicyConfig(policy=" close_proxy ")` 均抛出 `ValueError invalid_execution_price_policy`。
- 重点确认完全缺省 dict 仍默认 `close_proxy`，保持兼容边界。
- 回归确认 VWAP 缺失不静默 fallback、close_proxy degradation metadata / blocked claims、S03 tradability blocked 行不被重新放行。
- 复核默认验证路径中 `network_calls=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_operations=0`。

## 建议验证命令

- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile engine/research_dataset.py engine/backtest.py tests/test_cr011_execution_price_policy.py`
- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr011_execution_price_policy.py`
- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr011_tradability_gates.py tests/test_cr011_benchmark_policy_consumption.py tests/test_cr011_pit_universe_lifecycle.py tests/test_story_004_013.py::test_story_006_run_backtest_returns_metrics tests/test_cr006_lightweight_engine_adapter.py::test_canonical_gold_ok_feeds_data_loader_and_backtest`

## 期望输出

| 交付物 | 路径 |
|---|---|
| CP7 复验完成检查 | `process/checks/CP7-CR011-S04-ohlcv-vwap-clean-execution-feed-REVERIFY-DONE.md` |
| Story 验证状态 | `process/stories/CR011-S04-ohlcv-vwap-clean-execution-feed.md` |

若复验 PASS，可将 Story 状态推进为 `verified`；若仍 FAIL / BLOCKED，不得标记 verified，需在 CP7 复验中列明回修建议和最小回归集。
