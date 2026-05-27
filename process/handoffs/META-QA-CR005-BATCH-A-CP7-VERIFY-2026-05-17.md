---
handoff_id: "META-QA-CR005-BATCH-A-CP7-VERIFY-2026-05-17"
from_agent: "meta-po"
to_agent: "meta-qa"
status: "completed-fail"
created_at: "2026-05-17T20:11:27+08:00"
workflow_id: "local_backtest"
change_id: "CR-005"
story_id: "CR005-BATCH-A-CP7"
wave_id: "CR005-CP7-BATCH-A"
batch_id: "CR005-BATCH-A"
dispatch:
  required: true
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-qa"
  agent_path: ".codex/agents/meta-qa.toml"
  tool_name: "spawn_agent"
  agent_id: "019e35dc-03f8-7f40-9e26-0759c29d80e9"
  agent_name: "qa-zhang"
  thread_id: "019e35dc-03f8-7f40-9e26-0759c29d80e9"
  spawned_at: "2026-05-17T20:11:27+08:00"
  resumed_at: ""
  completed_at: "2026-05-17T20:18:14+08:00"
  evidence: "主线程真实 spawn_agent 调度 meta-qa/qa-zhang 执行本 handoff，agent_id/thread_id=019e35dc-03f8-7f40-9e26-0759c29d80e9，completed then closed。结论：CR005-S01 PASS；CR005-S02 FAIL，Batch A 不允许整体 verified。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# Handoff：CR-005 Batch A CP7 验证

## 验证范围

只验证 CR-005 Batch A：

- `CR005-S01`：Tushare connector 真实写湖边界与 `hs300_index` backfill job spec
- `CR005-S02`：Tushare 多 dataset schema、PIT 字段与复权 normalization

不得验证或推进：

- `CR005-S03` / `CR005-S04` / `CR005-S05` / `CR005-S06`
- Backtrader adapter
- 真实联网 fetch
- 真实 lake 写入

## 必须消费的输入

- `process/STATE.md`
- `process/handoffs/META-DEV-CR005-BATCH-A-IMPLEMENT-2026-05-17.md`
- `process/checks/CP6-CR005-S01-tushare-connector-real-lake-writer-CODING-DONE.md`
- `process/checks/CP6-CR005-S02-tushare-dataset-schema-normalization-CODING-DONE.md`
- `process/stories/CR005-S01-tushare-connector-real-lake-writer.md`
- `process/stories/CR005-S02-tushare-dataset-schema-normalization.md`
- `process/stories/CR005-S01-tushare-connector-real-lake-writer-LLD.md`
- `process/stories/CR005-S02-tushare-dataset-schema-normalization-LLD.md`
- `checkpoints/CP5-CR005-BATCH-A-LLD-BATCH.md`
- `process/checks/QA-CR005-QUALITY-REVIEW.md`
- `process/checks/REVIEW-CR005-HS300-TUSHARE-META-QA-POST-REVISION.md`

## 必须验证的重点

1. Agent dispatch evidence：
   - CP6 S01/S02 均必须记录真实 `spawn_agent`。
   - `agent_id/thread_id=019e35c8-da0b-7652-85af-017dd422cc29`。
   - `agent_name=dev-you`。
2. Lake root / `.gitignore` 决策：
   - 真实 lake root 必须外置且可配置。
   - 优先显式 `--lake-root` 或 `MARKET_DATA_LAKE_ROOT`。
   - 未配置 lake root 时必须 fail fast / structured missing，不得静默写 `./data`。
   - `.gitignore` 必须阻止 repo 内误放 raw/canonical/gold/quality/lake artifacts、本地 env 文件入库，同时允许 `tests/fixtures/` 小型脱敏样本。
3. 默认离线：
   - 默认测试无 token、无网络、无 NAS 依赖。
   - 不执行真实 Tushare fetch。
4. token 不泄露：
   - token 值不得进入 stdout/stderr、manifest、quality/catalog、fixture、日志或错误消息。
5. no-network：
   - import `market_data.connectors.tushare` 不得导入真实 provider、不得联网、不得读取 token 值。
   - provider 只能延迟导入 / 注入，且默认路径不触发。
6. `hs300-backfill` dry-run：
   - dry-run 默认无写入、无网络。
   - 缺 lake root structured missing / fail fast。
   - 有外置 temp lake root 时只使用 `tmp_path` 或测试临时目录。
7. PIT 字段：
   - `index_weights` 等非行情数据必须具备 `available_date` / `effective_date` / `available_at`。
   - 缺 PIT 字段 fail fast 或 structured status。
8. adjusted price：
   - `prices + adj_factor` 生成 adjusted OHLC。
   - `adjustment_policy` 单 run 唯一。
   - 冲突或 duplicate key fail fast。
9. exact interface：
   - unknown / fuzzy interface 必须 fail fast。
   - 不得 contains / similarity / alias 猜测。
10. 禁止范围：
   - 不得修改 / 依赖 `engine/data_loader.py`、`engine/backtest.py`、`experiments/**`、`market_data/readers.py`。
   - 不得引入 Backtrader 或真实 Tushare 依赖。
   - 不得写真实 `data/**`、`reports/**`、真实 token 或真实 Tushare 样本。

## 推荐验证命令

所有命令默认必须离线、清空 token：

```bash
TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q tests/test_market_data_tushare_connector.py tests/test_market_data_tushare_datasets.py
```

```bash
TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q tests/test_market_data_contracts.py tests/test_market_data_runtime_storage.py
```

```bash
TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q tests/test_market_data_tushare_connector.py tests/test_market_data_tushare_datasets.py tests/test_market_data_contracts.py tests/test_market_data_runtime_storage.py tests/test_market_data_normalization_validation_readers.py tests/test_market_data_cli_comparison.py
```

```bash
TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q
```

如需补充静态边界检查，可使用 `rg` / `find`，但不得联网。

## 必须输出

写入两个 CP7 结果文件：

- `process/checks/CP7-CR005-S01-tushare-connector-real-lake-writer-VERIFICATION-DONE.md`
- `process/checks/CP7-CR005-S02-tushare-dataset-schema-normalization-VERIFICATION-DONE.md`

每个 CP7 文件必须包含：

- Agent Dispatch Evidence：`tool_name`、`agent_id`、`agent_name`、`thread_id`、`spawned_at`、`completed_at`
- 验证命令与结果
- 质量门检查项
- 禁止范围复核
- token / no-network / no-real-data / no-real-fetch 证据
- 是否存在 BLOCKING / REQUIRED / RECOMMENDED

## 完成回报

完成后请回填本文件 frontmatter `dispatch.tool_name`、`agent_id`、`agent_name`、`thread_id`、`spawned_at`、`completed_at` 和结果摘要，并报告：

- 两个 CP7 文件路径
- 验证命令与结果
- 是否存在阻断 Batch A 进入 verified 的项
- 是否允许 meta-po 将 CR005-S01/S02 标记为 verified

## 执行结果回填

| 项 | 结果 |
|---|---|
| CP7 S01 | PASS：`process/checks/CP7-CR005-S01-tushare-connector-real-lake-writer-VERIFICATION-DONE.md` |
| CP7 S02 | FAIL：`process/checks/CP7-CR005-S02-tushare-dataset-schema-normalization-VERIFICATION-DONE.md` |
| 推荐命令 | PASS：`12 passed`、`22 passed`、`49 passed`、`68 passed` |
| dry-run | PASS：缺 lake root 返回 `lake_root_missing`；设置 `MARKET_DATA_LAKE_ROOT=/tmp/local-backtest-cp7-dryrun-lake` 时 job spec 完整、`network_calls=0`、`writes=0`、无文件写入 |
| 阻断项 | `CR005-S02-BLOCKER-001` 非法日历日期 `20261340` 被接受；`CR005-S02-BLOCKER-002` separate `prices.adj_factor` manifest 不能与 `prices.daily` join 生成 adjusted OHLC |
| verified 建议 | 允许 `CR005-S01` 标记为 `verified`；不允许 `CR005-S02` 标记为 `verified`；Batch A 整体不得进入 verified |
