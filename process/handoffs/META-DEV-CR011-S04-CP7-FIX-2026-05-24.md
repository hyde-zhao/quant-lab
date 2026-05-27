---
handoff_id: "META-DEV-CR011-S04-CP7-FIX-2026-05-24"
from_agent: "meta-po"
to_agent: "meta-dev"
agent_name: "dev-yang the 2nd"
change_id: "CR-011"
story_id: "CR011-S04-ohlcv-vwap-clean-execution-feed"
wave_id: "CR011-DATA-BATCH-A-DEV-W4-FIX1"
status: "completed"
created_at: "2026-05-24T13:07:33+08:00"
updated_at: "2026-05-24T13:13:51+08:00"
dispatch:
  mode: "resume_agent+send_input"
  agent_id: "019e5849-babb-7bc1-96e2-b0796df1f229"
  thread_id: "019e5849-babb-7bc1-96e2-b0796df1f229"
  tool_name: "resume_agent/send_input"
  spawned_at: ""
  resumed_at: "2026-05-24T13:08:19+08:00"
  completed_at: "2026-05-24T13:11:07+08:00"
  closed_at: "2026-05-24T13:13:05+08:00"
  result: "completed"
---

# META-DEV CR011-S04 CP7 Blocker Fix 交接

## 任务

修复 `CR011-S04-CP7-F01`：`execution_price_policy` mapping 输入未保持 exact 四值语义。当前实现错误接受 `{"policy": " open "}`、`{"policy": ""}`、`{"policy": " close_proxy "}`，违反 LLD 的 exact match / 显式空字符串非法要求。

## 输入

| 类型 | 路径 | 状态 |
|---|---|---|
| Story | `process/stories/CR011-S04-ohlcv-vwap-clean-execution-feed.md` | in-development / CP7 FAIL |
| CP6 | `process/checks/CP6-CR011-S04-ohlcv-vwap-clean-execution-feed-CODING-DONE.md` | PASS but superseded by CP7 FAIL |
| CP7 | `process/checks/CP7-CR011-S04-ohlcv-vwap-clean-execution-feed-VERIFICATION-DONE.md` | FAIL |
| 原实现 handoff | `process/handoffs/META-DEV-CR011-S04-IMPLEMENT-2026-05-24.md` | completed / closed |
| QA handoff | `process/handoffs/META-QA-CR011-S04-CP7-VERIFY-2026-05-24.md` | completed / failed |

## 允许写入范围

- `engine/research_dataset.py`
- `engine/backtest.py`（仅当 backtest config coercion 也需要 exact policy 修复）
- `tests/test_cr011_execution_price_policy.py`
- `process/checks/CP6-CR011-S04-CP7-BLOCKER-FIX-CODING-DONE.md`
- `process/stories/CR011-S04-ohlcv-vwap-clean-execution-feed.md` 的实现状态字段

## 禁止范围

- 不实现 `CR011-S05` 至 `CR011-S08`。
- 不修改 `market_data/readers.py`，除非能证明 exact policy 修复无法在上述两个 engine 文件完成。
- 不修改 `market_data/connectors/**`、`market_data/runtime.py`、`market_data/storage.py`、`market_data/contracts.py`。
- 不真实联网，不真实 Tushare 抓取，不写真实 lake。
- 不读取、打印或记录 `.env`、token、密码、私钥、cookie、session 或其他凭据。
- 不读取、列出、迁移、复制、删除旧 `data/**`。
- 不覆盖 `reports/experiment_17_21/factor_strategy_report.md`。
- 不写 `delivery/**`。

## 修复要求

- 显式传入 policy 时必须 exact match `open` / `close` / `vwap` / `close_proxy`，不得 `.strip()` 后接受。
- 显式空字符串必须抛出 `ValueError invalid_execution_price_policy`。
- 仅 policy 字段完全缺省时，才允许兼容默认 `close_proxy`。
- dict / mapping 输入、字符串输入、backtest `ExecutionPolicyConfig` / metadata 输入都必须保持上述语义。
- 补充测试覆盖 `{"policy": " open "}`、`{"policy": ""}`、`{"execution_price_policy": " close_proxy "}`、字符串 `" open "`、大小写非法值和完全缺省默认值。
- 回修后写新的 CP6 blocker-fix 检查，不得覆盖原 CP6。

## 建议验证

- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile engine/research_dataset.py engine/backtest.py tests/test_cr011_execution_price_policy.py`
- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr011_execution_price_policy.py`
- 精确 policy 负向探针应 PASS：`" open "`、`""`、`" close_proxy "` 均必须抛出 `ValueError`；完全缺省 dict 可默认 `close_proxy`。
- 回归 S03 tradability 与 S04 backtest 接入。

## 完成要求

| 交付物 | 路径 |
|---|---|
| CP6 blocker-fix 编码完成检查 | `process/checks/CP6-CR011-S04-CP7-BLOCKER-FIX-CODING-DONE.md` |
| Story 回修状态 | `process/stories/CR011-S04-ohlcv-vwap-clean-execution-feed.md` |

完成后将 Story 状态推进为 `ready-for-verification`；若发现阻断，不得标记 CP6 PASS，需在 blocker-fix CP6 中列明阻断项。
