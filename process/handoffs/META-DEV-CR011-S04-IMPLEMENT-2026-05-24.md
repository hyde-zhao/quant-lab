---
handoff_id: "META-DEV-CR011-S04-IMPLEMENT-2026-05-24"
from_agent: "meta-po"
to_agent: "meta-dev"
agent_name: "dev-yang the 2nd"
change_id: "CR-011"
story_id: "CR011-S04-ohlcv-vwap-clean-execution-feed"
wave_id: "CR011-DATA-BATCH-A-DEV-W4"
status: "completed"
created_at: "2026-05-24T12:40:39+08:00"
updated_at: "2026-05-24T12:56:16+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e5849-babb-7bc1-96e2-b0796df1f229"
  thread_id: "019e5849-babb-7bc1-96e2-b0796df1f229"
  tool_name: "spawn_agent"
  spawned_at: "2026-05-24T12:41:35+08:00"
  resumed_at: ""
  completed_at: "2026-05-24T12:53:27+08:00"
  closed_at: "2026-05-24T12:55:35+08:00"
  result: "completed"
---

# META-DEV CR011-S04 实现交接

## 任务

按确认版 LLD 实现 `CR011-S04-ohlcv-vwap-clean-execution-feed`：定义 `open` / `close` / `vwap` / `close_proxy` 执行价 policy、VWAP 缺失降级、OHLCV / execution feed 只读输入和回测执行 metadata，确保新版实验不会把 close proxy 声明为真实 VWAP 或真实成交。

## 输入

| 类型 | 路径 | 状态 |
|---|---|---|
| Story | `process/stories/CR011-S04-ohlcv-vwap-clean-execution-feed.md` | dev-ready |
| LLD | `process/stories/CR011-S04-ohlcv-vwap-clean-execution-feed-LLD.md` | confirmed |
| CP5 | `checkpoints/CP5-CR011-DATA-BATCH-A-LLD-BATCH.md` | approved |
| S03 CP7 | `process/checks/CP7-CR011-S03-tradability-status-and-price-limit-gates-VERIFICATION-DONE.md` | PASS / verified |
| CR010-S02 | `process/STORY-STATUS.md` | verified |

## 允许写入范围

- `market_data/readers.py`
- `engine/research_dataset.py`
- `engine/backtest.py`
- `tests/test_cr011_execution_price_policy.py`
- `process/checks/CP6-CR011-S04-ohlcv-vwap-clean-execution-feed-CODING-DONE.md`
- `process/stories/CR011-S04-ohlcv-vwap-clean-execution-feed.md` 的实现状态字段

## 禁止范围

- 不实现 `CR011-S05` 至 `CR011-S08`。
- 不修改 `market_data/connectors/**`、`market_data/runtime.py`、`market_data/storage.py`、`market_data/contracts.py`。
- 不真实联网，不真实 Tushare 抓取，不写真实 lake。
- 不读取、打印或记录 `.env`、token、密码、私钥、cookie、session 或其他凭据。
- 不读取、列出、迁移、复制、删除旧 `data/**`。
- 不覆盖 `reports/experiment_17_21/factor_strategy_report.md`。
- 不写 `delivery/**`。

## 实现要求

- 消费 LLD 第 4、6、7、8、10、13 节；历史 open_items 仅作为风险上下文，当前 Story / CP5 / STATE 已放行实现。
- `execution_price_policy` 只允许 `open`、`close`、`vwap`、`close_proxy` 四类枚举或等价强校验结构。
- `vwap` 缺失时不得静默 fallback；若按策略降级为 `close_proxy`，必须写 `execution_degradation_reason`、`vwap_status`、`vwap_or_proxy`、blocked / limitation claims。
- 不允许 consumer 用 `amount / volume` 静默推导真实 VWAP；缺显式 VWAP lineage 时不得声明真实 VWAP / true fillability。
- 与 S03 tradability matrix 集成时，blocked / unavailable 行不得被执行价逻辑重新放行。
- CP6 必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables 和 Agent Dispatch Evidence。

## 建议验证

- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile market_data/readers.py engine/research_dataset.py engine/backtest.py tests/test_cr011_execution_price_policy.py`
- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr011_execution_price_policy.py`
- 相关回归优先覆盖 S03 tradability gates、S01 benchmark policy、S02 PIT lifecycle 和既有 backtest 测试。

## 完成要求

| 交付物 | 路径 |
|---|---|
| CP6 编码完成检查 | `process/checks/CP6-CR011-S04-ohlcv-vwap-clean-execution-feed-CODING-DONE.md` |
| Story 实现状态 | `process/stories/CR011-S04-ohlcv-vwap-clean-execution-feed.md` |

完成后将 Story 状态推进为 `ready-for-verification`；若发现阻断，不得标记 CP6 PASS，需在 CP6 中列明阻断项和回修建议。
