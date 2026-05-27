---
handoff_id: "META-DEV-CR005-S04-IMPLEMENT-2026-05-17"
from_agent: "codex-main-orchestrator"
to_agent: "meta-dev"
status: "completed"
created_at: "2026-05-17T23:10:12+08:00"
workflow_id: "local_backtest"
change_id: "CR-005"
story_id: "CR005-S04"
wave_id: "CR005-CP6-S04-IMPLEMENT"
batch_id: "CR005-BATCH-B2-S04-IMPLEMENT"
parallel_group: "CR005-S04-S05-IMPLEMENT"
dispatch:
  required: true
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-dev"
  tool_name: "spawn_agent"
  agent_id: "019e367e-b356-79c0-9023-863f58d9979a"
  agent_name: "dev-zhu the 2nd"
  thread_id: "019e367e-b356-79c0-9023-863f58d9979a"
  spawned_at: "2026-05-17T23:10:12+08:00"
  completed_at: "2026-05-17T23:24:00+08:00"
  evidence: "主线程真实 spawn_agent 调度 meta-dev/dev-zhu the 2nd；agent_id/thread_id=019e367e-b356-79c0-9023-863f58d9979a。CR005-S04 已完成实现与 CP6，结果见 process/checks/CP6-CR005-S04-hs300-local-benchmark-CODING-DONE.md。"
---

# META-DEV Handoff: CR005-S04 实现 / CP6

## 目标

仅实现 `CR005-S04`：沪深 300 本地基准与实验只读接入。实现完成后必须输出 CP6 编码完成自检，不得进入 CP7。

## 已批准输入

- Story：`process/stories/CR005-S04-hs300-local-benchmark.md`
- LLD：`process/stories/CR005-S04-hs300-local-benchmark-LLD.md`
- CP5 自动预检：`process/checks/CP5-CR005-S04-hs300-local-benchmark-LLD-IMPLEMENTABILITY.md`
- CP5 人工审查：`checkpoints/CP5-CR005-BATCH-B2C-S04-S05-LLD-BATCH.md`，已 approved，reviewed_by=user，reviewed_at=`2026-05-17T23:10:12+08:00`
- 上游 verified：
  - `process/checks/CP7-CR005-S01-tushare-connector-real-lake-writer-VERIFICATION-DONE.md`
  - `process/checks/CP7-CR005-S03-multidataset-quality-catalog-readers-VERIFICATION-DONE.md`
  - `process/stories/STORY-018-cr004-experiment-readonly-benchmark-LLD.md`

## 允许修改文件

- `market_data/benchmarks.py`
- `tests/test_market_data_hs300_benchmark.py`
- `experiments/run_experiment_10.py`
- `experiments/run_experiment_12.py`
- `market_data/readers.py`（仅在 resolver 只读适配必要时小范围修改；不得改写 S03 reader gate 语义）
- `process/checks/CP6-CR005-S04-hs300-local-benchmark-CODING-DONE.md`
- `process/stories/CR005-S04-hs300-local-benchmark.md`
- `process/handoffs/META-DEV-CR005-S04-IMPLEMENT-2026-05-17.md`

## 并行文件边界

- S05 会并行修改 `market_data/comparison.py`、`README.md`、`docs/USER-MANUAL.md`、`tests/test_market_data_tushare_comparison.py`。
- S04 不得修改 README / USER-MANUAL / comparison / S05 测试。
- 不要更新 `process/STATE.md`、`process/STORY-STATUS.md`、`DEV-LOG.md`，由主线程在两个 CP6 完成后统一汇总。

## 必须实现的边界

- `BenchmarkResult` typed schema 与 `BenchmarkPolicy` / `NextAction` / `RemediationJobSpec`。
- 缺 `hs300_index` 返回 typed `unavailable` / `required_missing`，不得自动联网、不得自动 backfill、不得静默代理。
- `remediation_job_spec.dry_run=true` 默认，且消费层不执行。
- resolver 与实验入口不得导入 connector/runtime/storage，不读 token，不写 raw/manifest/canonical/quality/catalog/gold。
- 旧 `--data-dir` 只保留本地价格路径；代理只能命名为 `proxy_baseline`。

## 必须验证

```bash
UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_market_data_hs300_benchmark.py
```

建议补充：

```bash
UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_market_data_hs300_benchmark.py tests/test_market_data_multidataset_quality_readers.py
```

## 预期输出

- 更新允许范围内的 S04 实现与测试。
- 写入 `process/checks/CP6-CR005-S04-hs300-local-benchmark-CODING-DONE.md`，包含 Agent Dispatch Evidence、修改文件、测试结果、越界复核。
- 将 S04 Story 推进到 `ready-for-verification`，但不得标记 `verified`。

## 禁止范围

- 不修改 `README.md`、`docs/USER-MANUAL.md`、`market_data/comparison.py`、`tests/test_market_data_tushare_comparison.py`。
- 不进入 `CR005-S05` 实现范围、`CR005-S06` 或 Backtrader。
- 不修改 `engine/backtest.py`、`engine/backtrader_adapter.py`、`market_data/connectors/**`、真实 `data/**`、`reports/**`、`delivery/**`、`pyproject.toml`、`uv.lock`。
- 不执行真实联网、真实 Tushare fetch、真实写 lake、写 token 或提交真实行情数据。

## 执行结果

| 项目 | 结果 |
|---|---|
| 实现状态 | completed |
| CP6 | `process/checks/CP6-CR005-S04-hs300-local-benchmark-CODING-DONE.md`，结论 PASS |
| Story 状态 | `process/stories/CR005-S04-hs300-local-benchmark.md` 已推进到 `ready-for-verification` |
| 修改文件 | `market_data/benchmarks.py`、`tests/test_market_data_hs300_benchmark.py`、`experiments/run_experiment_10.py`、`experiments/run_experiment_12.py`、S04 Story、S04 CP6、本 handoff |
| 未修改范围 | README、docs/USER-MANUAL、market_data/comparison.py、tests/test_market_data_tushare_comparison.py、process/STATE.md、process/STORY-STATUS.md、DEV-LOG.md |
| 指定测试 | `UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_market_data_hs300_benchmark.py` -> 6 passed |
| 补充回归 | `UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_market_data_hs300_benchmark.py tests/test_market_data_multidataset_quality_readers.py` -> 15 passed |
| 停止点 | 未进入 CP7，未标记 verified |
