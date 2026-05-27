---
handoff_id: "META-DEV-CR005-S02-CP7-BLOCKER-FIX-2026-05-17"
from_agent: "meta-po"
to_agent: "meta-dev"
status: "completed-awaiting-cp7-reverification"
created_at: "2026-05-17T20:25:49+08:00"
workflow_id: "local_backtest"
change_id: "CR-005"
story_id: "CR005-S02"
wave_id: "CR005-CP6-S02-BLOCKER-FIX"
batch_id: "CR005-BATCH-A-S02-FIX"
dispatch:
  required: true
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".codex/agents/meta-dev.toml"
  tool_name: "spawn_agent"
  agent_id: "019e35e9-1736-7252-a5a5-4065e324a10d"
  agent_name: "dev-zhu"
  thread_id: "019e35e9-1736-7252-a5a5-4065e324a10d"
  spawned_at: "reported-by-main-thread; exact spawn time not provided"
  resumed_at: ""
  completed_at: "2026-05-17T20:32:50+08:00"
  evidence: "主线程真实 spawn_agent 调度 meta-dev/dev-zhu 执行本 handoff，agent_id/thread_id=019e35e9-1736-7252-a5a5-4065e324a10d，completed then closed。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# Handoff：CR-005 / CR005-S02 CP7 BLOCKING 修复

## 调度目标

请 `meta-dev` 只修复 `CR005-S02` 在 CP7 中暴露的两个 BLOCKING 项，并重新输出 / 更新 S02 的 CP6 编码完成检查结果。

不得实现或修改 `CR005-S01`、`CR005-S03`、`CR005-S04`、`CR005-S05`、`CR005-S06`；不得进入 Backtrader；不得执行真实联网、真实 Tushare fetch、真实 lake 写入或 token 相关运行。

## 当前状态（handoff 创建时）

- `CR005-S01`：CP7 PASS，允许 meta-po 标记为 `verified`。
- `CR005-S02`：CP7 FAIL，已退回 `in-development` / `blocked-by-cp7-fail`。
- Batch A 整体不得标记 verified，直到 S02 修复后重新通过 CP6 和 S02 CP7。

## 必须消费的输入

- `process/STATE.md`
- `process/stories/CR005-S02-tushare-dataset-schema-normalization.md`
- `process/stories/CR005-S02-tushare-dataset-schema-normalization-LLD.md`
- `process/checks/CP6-CR005-S02-tushare-dataset-schema-normalization-CODING-DONE.md`
- `process/checks/CP7-CR005-S02-tushare-dataset-schema-normalization-VERIFICATION-DONE.md`
- `process/checks/CP7-CR005-S01-tushare-connector-real-lake-writer-VERIFICATION-DONE.md`
- `process/handoffs/META-QA-CR005-BATCH-A-CP7-VERIFY-2026-05-17.md`
- `checkpoints/CP5-CR005-BATCH-A-LLD-BATCH.md`

## 必须修复的 BLOCKING 项

### CR005-S02-BLOCKER-001：非法日历日期未 fail fast

问题：

- `hs300_index` normalization 接受非法日历日期 `20261340`。
- 当前 `_parse_date` 只做字符串切片，可能输出无效日期形态 `2026-13-40`，未进行真实日期解析校验。

修复要求：

- 对 `%Y%m%d` 和 ISO-like 日期输入进行真实日历日期解析。
- 非法日期必须 fail fast，返回既有结构化 schema / canonical 错误类型；不得静默修正。
- 至少覆盖 `20261340`、非法月份、非法日期、格式错误和合法日期。

### CR005-S02-BLOCKER-002：`prices.daily` 与 separate `prices.adj_factor` manifest 不能 join

问题：

- 当前实现只支持 `prices.daily` raw 行内包含 `adj_factor`。
- Story / LLD 契约要求支持 `prices.daily + prices.adj_factor` 分离输入 join 后生成 adjusted OHLC。

修复要求：

- 在 normalization 层支持 exact `prices.daily` 与 `prices.adj_factor` records / manifest 输入 join。
- join key 必须为 `trade_date + symbol` 或 LLD 已冻结的等价 exact key。
- join 后必须输出 `adj_factor`、`adjusted_open`、`adjusted_high`、`adjusted_low`、`adjusted_close` 和统一 `adjustment_policy`。
- 缺失 `adj_factor`、重复 join key、日期 / symbol key 不匹配、`adjustment_policy` 冲突必须 fail fast。
- 不得把 join 逻辑下沉到 Backtrader、reader、engine 或实验代码。

## 允许修改的文件

只允许修改：

- `market_data/normalization.py`
- `tests/test_market_data_tushare_datasets.py`
- `process/checks/CP6-CR005-S02-tushare-dataset-schema-normalization-CODING-DONE.md`
- `process/stories/CR005-S02-tushare-dataset-schema-normalization.md`
- `process/STATE.md`
- `DEV-LOG.md`

如确需新增极小合成 fixture，必须位于 `tests/fixtures/**`，且必须脱敏、非真实 Tushare 数据；优先使用测试内临时数据，不新增 fixture 文件。

## 禁止修改的文件和范围

不得修改：

- `market_data/connectors/tushare.py`
- `market_data/config.py`
- `market_data/storage.py`
- `market_data/cli.py`
- `engine/**`
- `experiments/**`
- `market_data/readers.py`
- `data/**`
- `reports/**`
- `delivery/**`
- `pyproject.toml`
- `uv.lock`

不得新增：

- `tushare` 依赖
- Backtrader 依赖
- 真实行情数据
- 真实 Tushare 返回样本
- token、API key、cookie、session 或任何凭据

## 必须执行的最小回归

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

如果修复影响公共 normalization 行为，必须补跑：

```bash
TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q
```

## 必须输出

更新或重写：

- `process/checks/CP6-CR005-S02-tushare-dataset-schema-normalization-CODING-DONE.md`

CP6 文件必须包含：

- 真实 meta-dev 调度证据占位，待主线程回填 `tool_name=spawn_agent`、`agent_id/thread_id`、`agent_name`、`spawned_at`、`completed_at`。
- 两个 blocker 的修复说明。
- 最小回归命令与结果。
- 禁止范围复核。
- 未联网、未真实写湖、未使用 / 泄露 token、未改依赖的证据。

完成后请把 `CR005-S02` 状态推进到 `ready-for-verification`，但不得自行写 CP7 PASS 结论；S02 CP7 必须由 meta-qa 重新验证。

## 完成回报

完成后请回填本 handoff frontmatter 的 dispatch 字段和执行结果摘要，并报告：

- 修改文件清单
- S02 CP6 文件路径
- 测试命令与结果
- 是否仍存在 BLOCKING / REQUIRED 项
- 是否允许 meta-po 创建 S02 CP7 重验 handoff

## 执行结果摘要

| 项 | 结果 |
|---|---|
| 结论 | `PASS`，两个 CP7 BLOCKING 均已修复 |
| Story 状态 | `CR005-S02` 已推进到 `ready-for-verification`，未标记 `verified` |
| CP6 | `process/checks/CP6-CR005-S02-tushare-dataset-schema-normalization-CODING-DONE.md` 已更新为 `PASS` |
| 修改文件 | `market_data/normalization.py`、`tests/test_market_data_tushare_datasets.py`、`process/checks/CP6-CR005-S02-tushare-dataset-schema-normalization-CODING-DONE.md`、`process/stories/CR005-S02-tushare-dataset-schema-normalization.md`、`process/STATE.md`、`DEV-LOG.md`、本 handoff |
| 禁止范围 | 未修改 S03/S04/S05/S06、Backtrader、`engine/**`、`experiments/**`、`market_data/readers.py`、`data/**`、`reports/**`、`delivery/**`、依赖文件或真实 token/data |

### Blocker 修复

| Blocker | 修复结果 |
|---|---|
| `CR005-S02-BLOCKER-001` | `_parse_date` 改为真实日历解析：`%Y%m%d` 使用 `datetime.strptime`，ISO-like 输入使用 `date.fromisoformat`，非法月份、非法日期、`20261340` 和不可解析值均返回 `CanonicalSchemaError("invalid_date")`。 |
| `CR005-S02-BLOCKER-002` | `normalize_run(..., dataset=prices)` 支持同时消费 exact `prices.adj_factor` success records，按 `trade_date,symbol` join 到 `prices.daily` 并生成 `adj_factor`、`adjusted_open/high/low/close`、`adjustment_policy`；缺因子、duplicate key、policy 冲突和 key 不匹配均 fail fast。 |

### 测试命令与结果

| 命令 | 结果 |
|---|---|
| `TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q tests/test_market_data_tushare_datasets.py` | PASS，`9 passed in 0.45s` |
| `TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q tests/test_market_data_tushare_connector.py tests/test_market_data_tushare_datasets.py` | PASS，`14 passed in 0.44s` |
| `TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q tests/test_market_data_tushare_connector.py tests/test_market_data_tushare_datasets.py tests/test_market_data_contracts.py tests/test_market_data_runtime_storage.py tests/test_market_data_normalization_validation_readers.py tests/test_market_data_cli_comparison.py` | PASS，`51 passed in 0.78s` |
| `TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q` | PASS，`70 passed in 3.16s` |

### 交接给 meta-po / meta-qa

- 仍存在阻断 CP7 重验的项：无。
- REQUIRED 项：无。
- 允许 meta-po 创建 `CR005-S02` CP7 重验 handoff；重验范围应限定为 S02 blocker fix，不得扩展到 S03/S04/S05/S06 或 Backtrader。
