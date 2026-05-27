---
handoff_id: "META-QA-CR011-S04-CP7-VERIFY-2026-05-24"
from_agent: "meta-po"
to_agent: "meta-qa"
agent_name: "qa-hua the 2nd"
change_id: "CR-011"
story_id: "CR011-S04-ohlcv-vwap-clean-execution-feed"
wave_id: "CR011-DATA-BATCH-A-VERIFY-W4"
status: "completed"
created_at: "2026-05-24T12:58:38+08:00"
updated_at: "2026-05-24T13:05:15+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e585a-12bf-7721-affc-a0927f18c5c6"
  thread_id: "019e585a-12bf-7721-affc-a0927f18c5c6"
  tool_name: "spawn_agent"
  spawned_at: "2026-05-24T12:59:22+08:00"
  resumed_at: ""
  completed_at: "2026-05-24T13:02:28+08:00"
  closed_at: "2026-05-24T13:05:15+08:00"
  result: "failed"
---

# META-QA CR011-S04 CP7 验证交接

## 任务

对 `CR011-S04-ohlcv-vwap-clean-execution-feed` 执行 CP7 独立验证，复核执行价 policy、OHLCV / VWAP feed、`close_proxy` 降级 metadata、backtest 接入和 S03 tradability blocked 行优先级是否按确认版 LLD 与 CP6 落地，并写入 CP7 验证完成检查结果。

## 输入

| 类型 | 路径 | 状态 |
|---|---|---|
| Story | `process/stories/CR011-S04-ohlcv-vwap-clean-execution-feed.md` | ready-for-verification |
| LLD | `process/stories/CR011-S04-ohlcv-vwap-clean-execution-feed-LLD.md` | confirmed |
| CP5 | `checkpoints/CP5-CR011-DATA-BATCH-A-LLD-BATCH.md` | approved |
| CP6 | `process/checks/CP6-CR011-S04-ohlcv-vwap-clean-execution-feed-CODING-DONE.md` | PASS |
| dev handoff | `process/handoffs/META-DEV-CR011-S04-IMPLEMENT-2026-05-24.md` | completed / closed |
| S03 CP7 | `process/checks/CP7-CR011-S03-tradability-status-and-price-limit-gates-VERIFICATION-DONE.md` | PASS / verified |

## 允许写入范围

- `process/checks/CP7-CR011-S04-ohlcv-vwap-clean-execution-feed-VERIFICATION-DONE.md`
- `process/stories/CR011-S04-ohlcv-vwap-clean-execution-feed.md` 的验证状态字段

## 禁止范围

- 不实现或修改 `CR011-S05` 至 `CR011-S08`。
- 不修改生产代码，除非发现验证阻断且先在 CP7 写明 FAIL / BLOCKED。
- 不真实联网，不真实 Tushare 抓取，不写真实 lake。
- 不读取、打印或记录 `.env`、token、密码、私钥、cookie、session 或其他凭据。
- 不读取、列出、迁移、复制、删除旧 `data/**`。
- 不覆盖 `reports/experiment_17_21/factor_strategy_report.md`。
- 不写 `delivery/**`。

## 必查项

- CP7 必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables 和 Agent Dispatch Evidence。
- 验证 CP6 的 `Agent Dispatch Evidence` 与本 handoff 一致，不能把 handoff-only 当作完成证据。
- 复核 `execution_price_policy` 只接受 `open` / `close` / `vwap` / `close_proxy` 四值。
- 复核 VWAP 缺失时不得静默 fallback；`close_proxy` 必须写 `execution_degradation_reason`、`vwap_status`、`vwap_or_proxy`、blocked / limitation claims。
- 复核 consumer 不得用 `amount / volume` 静默推导真实 VWAP。
- 复核 S03 tradability blocked / unavailable 行不得被执行价逻辑重新放行。
- 复核默认验证路径中 `network_calls=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_operations=0`。

## 建议验证命令

- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile market_data/readers.py engine/research_dataset.py engine/backtest.py tests/test_cr011_execution_price_policy.py`
- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr011_execution_price_policy.py`
- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr011_tradability_gates.py tests/test_cr011_benchmark_policy_consumption.py tests/test_cr011_pit_universe_lifecycle.py tests/test_story_004_013.py::test_story_006_run_backtest_returns_metrics tests/test_cr006_lightweight_engine_adapter.py::test_canonical_gold_ok_feeds_data_loader_and_backtest`

## 期望输出

| 交付物 | 路径 |
|---|---|
| CP7 验证完成检查 | `process/checks/CP7-CR011-S04-ohlcv-vwap-clean-execution-feed-VERIFICATION-DONE.md` |
| Story 验证状态 | `process/stories/CR011-S04-ohlcv-vwap-clean-execution-feed.md` |

若 CP7 PASS，可将 Story 状态推进为 `verified`；若发现 FAIL / BLOCKED，不得标记 verified，需在 CP7 中列明回修建议和最小回归集。
