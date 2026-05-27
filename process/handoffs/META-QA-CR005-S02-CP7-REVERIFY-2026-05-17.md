---
handoff_id: "META-QA-CR005-S02-CP7-REVERIFY-2026-05-17"
from_agent: "meta-po"
to_agent: "meta-qa"
status: "completed-pass"
created_at: "2026-05-17T20:40:50+08:00"
workflow_id: "local_backtest"
change_id: "CR-005"
story_id: "CR005-S02"
wave_id: "CR005-CP7-S02-REVERIFY"
batch_id: "CR005-BATCH-A-S02-REVERIFY"
dispatch:
  required: true
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-qa"
  agent_path: ".codex/agents/meta-qa.toml"
  tool_name: "spawn_agent"
  agent_id: "019e35f6-ce84-7bb2-b034-dace99fef8b3"
  agent_name: "qa-he the 2nd"
  thread_id: "019e35f6-ce84-7bb2-b034-dace99fef8b3"
  spawned_at: "2026-05-17T20:40:50+08:00"
  resumed_at: ""
  completed_at: "2026-05-17T20:46:51+08:00"
  evidence: "主线程真实 spawn_agent 调度 meta-qa/qa-he the 2nd 执行本 handoff，agent_id/thread_id=019e35f6-ce84-7bb2-b034-dace99fef8b3，completed then closed。CR005-S02 CP7 blocker 重验结论 PASS，无 BLOCKING/REQUIRED 失败项。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# Handoff：CR005-S02 CP7 重验

## 验证范围

只验证 `CR005-S02` 的 CP7 blocker fix 和必要回归。

必须验证：

- `CR005-S02-BLOCKER-001`：非法日历日期必须 fail fast。
- `CR005-S02-BLOCKER-002`：`prices.daily` 与 exact `prices.adj_factor` 分离输入必须 join 生成 adjusted OHLC。
- S02 修复没有破坏 Batch A 已通过的离线基础回归。

不得验证、实现或推进：

- `CR005-S03` / `CR005-S04` / `CR005-S05` / `CR005-S06`
- Backtrader adapter 或 Backtrader 依赖
- 真实联网 fetch
- 真实 Tushare provider 调用
- 真实 lake 写入
- 真实 token、真实行情样本或生产数据

## 必须消费的输入

- `process/STATE.md`
- `process/stories/CR005-S02-tushare-dataset-schema-normalization.md`
- `process/stories/CR005-S02-tushare-dataset-schema-normalization-LLD.md`
- `process/checks/CP6-CR005-S02-tushare-dataset-schema-normalization-CODING-DONE.md`
- `process/checks/CP7-CR005-S02-tushare-dataset-schema-normalization-VERIFICATION-DONE.md`
- `process/handoffs/META-DEV-CR005-S02-CP7-BLOCKER-FIX-2026-05-17.md`
- `process/handoffs/META-QA-CR005-BATCH-A-CP7-VERIFY-2026-05-17.md`
- `process/checks/CP7-CR005-S01-tushare-connector-real-lake-writer-VERIFICATION-DONE.md`
- `checkpoints/CP5-CR005-BATCH-A-LLD-BATCH.md`

## 前置事实

- `CR005-S01` 已 CP7 PASS 并可保持 `verified`，本 handoff 不重验 S01。
- `CR005-S02` 已由 meta-dev/dev-zhu 修复两个 blocker，S02 CP6 修复后为 `PASS`。
- `CR005-S02` 当前应为 `ready-for-verification` / `verification_status=pending-reverification`。
- 本 handoff 不得把任何后续 Story 推进到实现或验证。

## 必须验证的检查项

### 1. Agent dispatch evidence

- S02 blocker fix CP6 必须记录真实 `spawn_agent`。
- `agent_id/thread_id=019e35e9-1736-7252-a5a5-4065e324a10d`。
- `agent_name=dev-zhu`。
- 不得保留 `current-codex-thread`、`codex-current-thread`、`not-exposed` 或旧 `dev-you` 作为 S02 blocker fix 证据。

### 2. `CR005-S02-BLOCKER-001` 重验

必须覆盖：

- `trade_date=20261340` fail fast。
- 非法月份 fail fast。
- 非法日期 fail fast，例如 `20260230`。
- ISO-like 非法日期 fail fast，例如 `2026-13-01`。
- 合法 `%Y%m%d` 与合法 ISO-like 日期仍可解析。

期望：

- 返回既有结构化 schema / canonical 错误类型。
- 不得静默修正、截断或输出无效 ISO-like 日期。

### 3. `CR005-S02-BLOCKER-002` 重验

必须覆盖：

- `prices.daily` 与 exact `prices.adj_factor` 分离 records / manifest 可按 `trade_date + symbol` join。
- 输出 `adj_factor`、`adjusted_open`、`adjusted_high`、`adjusted_low`、`adjusted_close`、`adjustment_policy`。
- 缺失 `adj_factor` fail fast。
- duplicate join key fail fast。
- daily / adj_factor key 不匹配 fail fast。
- `adjustment_policy` 冲突 fail fast。

期望：

- join 只在 Pandas / normalization 数据层完成。
- 不依赖 Backtrader、reader、engine 或实验代码。

### 4. 禁止范围复核

确认本轮修复未修改或依赖：

- `CR005-S03` / `CR005-S04` / `CR005-S05` / `CR005-S06`
- `market_data/connectors/tushare.py`
- `market_data/readers.py`
- `engine/**`
- `experiments/**`
- `data/**`
- `reports/**`
- `delivery/**`
- `pyproject.toml`
- `uv.lock`

确认未新增：

- `tushare` 依赖
- Backtrader 依赖
- 真实 Tushare 样本
- token / API key / cookie / session

## 推荐验证命令

默认离线、清空 token：

```bash
TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q tests/test_market_data_tushare_datasets.py
```

```bash
TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q tests/test_market_data_tushare_connector.py tests/test_market_data_tushare_datasets.py
```

```bash
TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q tests/test_market_data_tushare_connector.py tests/test_market_data_tushare_datasets.py tests/test_market_data_contracts.py tests/test_market_data_runtime_storage.py tests/test_market_data_normalization_validation_readers.py tests/test_market_data_cli_comparison.py
```

如 meta-qa 判断 normalization 影响公共路径，补跑：

```bash
TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q
```

## 必须输出

更新或重写：

- `process/checks/CP7-CR005-S02-tushare-dataset-schema-normalization-VERIFICATION-DONE.md`

CP7 文件必须包含：

- Agent Dispatch Evidence：`tool_name`、`agent_id`、`agent_name`、`thread_id`、`spawned_at`、`completed_at`
- S02 blocker fix 的真实 meta-dev dispatch evidence 复核
- 验证命令与结果
- 两个 blocker 的复验结果
- 禁止范围复核
- no-network / no-real-data / no-real-fetch / no-token 证据
- 是否允许 meta-po 将 `CR005-S02` 标记为 `verified`

完成后请回填本 handoff frontmatter `dispatch.tool_name`、`agent_id`、`agent_name`、`thread_id`、`spawned_at`、`completed_at` 和执行结果摘要。

## 执行结果回填

| 项 | 结果 |
|---|---|
| 结论 | `PASS`，`CR005-S02-BLOCKER-001` / `CR005-S02-BLOCKER-002` 均重验通过 |
| CP7 文件 | `process/checks/CP7-CR005-S02-tushare-dataset-schema-normalization-VERIFICATION-DONE.md` |
| Story 状态 | `verified`；无 BLOCKING / REQUIRED 失败项 |
| meta-dev dispatch 复核 | PASS，blocker fix 证据为 `tool_name=spawn_agent`，`agent_id/thread_id=019e35e9-1736-7252-a5a5-4065e324a10d`，`agent_name=dev-zhu` |
| 默认离线 | PASS，所有命令均设置 `TUSHARE_TOKEN=`，未联网、未真实 fetch、未真实写 lake |
| 禁止范围 | PASS，未进入 `CR005-S03/S04/S05/S06`、Backtrader、`engine/**`、`experiments/**`、`market_data/readers.py`、真实 `data/**`、真实 `reports/**` 或 `delivery/**` |
| verified 建议 | 允许 meta-po 将 `CR005-S02` 收敛为 `verified`；不得据此自动进入后续 Story |

### 命令与结果

| 命令 | 结果 |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q -p no:cacheprovider tests/test_market_data_tushare_datasets.py::test_hs300_invalid_date_missing_required_and_duplicate_fail_fast tests/test_market_data_tushare_datasets.py::test_normalize_hs300_index_exact_mapping_and_lineage tests/test_market_data_tushare_datasets.py::test_prices_daily_joins_separate_adj_factor_manifest tests/test_market_data_tushare_datasets.py::test_prices_separate_adj_factor_missing_duplicate_and_policy_fail_fast` | PASS，`4 passed in 0.45s` |
| `PYTHONDONTWRITEBYTECODE=1 TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q -p no:cacheprovider tests/test_market_data_tushare_datasets.py` | PASS，`9 passed in 0.48s` |
| `PYTHONDONTWRITEBYTECODE=1 TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q -p no:cacheprovider tests/test_market_data_tushare_connector.py tests/test_market_data_tushare_datasets.py` | PASS，`14 passed in 0.50s` |
| `PYTHONDONTWRITEBYTECODE=1 TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q -p no:cacheprovider tests/test_market_data_tushare_connector.py tests/test_market_data_tushare_datasets.py tests/test_market_data_contracts.py tests/test_market_data_runtime_storage.py tests/test_market_data_normalization_validation_readers.py tests/test_market_data_cli_comparison.py` | PASS，`51 passed in 0.91s` |
| `PYTHONDONTWRITEBYTECODE=1 TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q -p no:cacheprovider` | PASS，`70 passed in 3.50s` |
