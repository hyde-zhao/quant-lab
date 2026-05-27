---
handoff_id: "META-QA-CR005-S04-CP7-VERIFY-2026-05-17"
from_agent: "codex-main-orchestrator"
to_agent: "meta-qa"
status: "completed"
created_at: "2026-05-17T23:24:30+08:00"
workflow_id: "local_backtest"
change_id: "CR-005"
story_id: "CR005-S04"
wave_id: "CR005-CP7-S04-VERIFY"
batch_id: "CR005-BATCH-B2C-S04-S05-CP7"
parallel_group: "CR005-S04-S05-CP7"
dispatch:
  required: true
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-qa"
  tool_name: "spawn_agent"
  agent_id: "019e368a-3a6e-76d3-9852-51a4df77869f"
  agent_name: "qa-kong the 2nd"
  thread_id: "019e368a-3a6e-76d3-9852-51a4df77869f"
  spawned_at: "2026-05-17T23:24:30+08:00"
  completed_at: "2026-05-17T23:26:48+08:00"
  evidence: "主线程真实 spawn_agent 调度 meta-qa/qa-kong the 2nd；agent_id/thread_id=019e368a-3a6e-76d3-9852-51a4df77869f。CR005-S04 CP7 已完成，结果见 process/checks/CP7-CR005-S04-hs300-local-benchmark-VERIFICATION-DONE.md。"
result:
  status: "PASS"
  result_path: "process/checks/CP7-CR005-S04-hs300-local-benchmark-VERIFICATION-DONE.md"
  tests:
    - command: "UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_market_data_hs300_benchmark.py"
      result: "PASS: 6 passed in 0.66s"
    - command: "UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_market_data_hs300_benchmark.py tests/test_market_data_multidataset_quality_readers.py"
      result: "PASS: 15 passed in 0.78s"
    - command: "UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q"
      result: "PASS: 90 passed in 3.00s"
  blockers: []
---

# META-QA Handoff: CR005-S04 CP7 验证

## 目标

验证 `CR005-S04`：沪深 300 本地基准与实验只读接入。完成后写入 CP7 验证结果，不得标记 Story `verified`，由主线程/meta-po 收敛。

## 必读输入

- Story：`process/stories/CR005-S04-hs300-local-benchmark.md`
- LLD：`process/stories/CR005-S04-hs300-local-benchmark-LLD.md`
- CP5：`process/checks/CP5-CR005-S04-hs300-local-benchmark-LLD-IMPLEMENTABILITY.md`
- CP5 人工审查：`checkpoints/CP5-CR005-BATCH-B2C-S04-S05-LLD-BATCH.md`
- CP6：`process/checks/CP6-CR005-S04-hs300-local-benchmark-CODING-DONE.md`
- 实现 handoff：`process/handoffs/META-DEV-CR005-S04-IMPLEMENT-2026-05-17.md`
- 相关代码：`market_data/benchmarks.py`、`experiments/run_experiment_10.py`、`experiments/run_experiment_12.py`、`tests/test_market_data_hs300_benchmark.py`

## 验证重点

- `BenchmarkResult` typed schema 覆盖 status、dataset、source、index_code、interface、date range、coverage、quality_status、missing_reason、required、benchmark_kind、next_action、remediation_job_spec、catalog_entry、run/lineage。
- `available`、`unavailable`、`required_missing`、`quality_failed` 行为符合 LLD。
- `required_missing` 只返回 `next_action` / `remediation_job_spec`，`dry_run=true` 默认，不执行 backfill。
- resolver 与实验入口不导入 connector/runtime/storage，不联网，不读 `TUSHARE_TOKEN`，不写 raw/manifest/canonical/quality/catalog/gold。
- 缺 benchmark 时不静默代理；代理只能命名为 `proxy_baseline`，不得填充 `hs300_index` 或声明 hs300 相对收益。
- 实验十/十二默认兼容旧 `--data-dir`，仅在显式 `--market-data-lake-root` 或 `--require-benchmark` 时只读接入 benchmark metadata。
- 不进入 `CR005-S05`、`CR005-S06`、Backtrader 或真实数据写入范围。

## 必跑验证

```bash
UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_market_data_hs300_benchmark.py
```

```bash
UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_market_data_hs300_benchmark.py tests/test_market_data_multidataset_quality_readers.py
```

## 建议补充

```bash
UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q
```

## 预期输出

- 写入 `process/checks/CP7-CR005-S04-hs300-local-benchmark-VERIFICATION-DONE.md`。
- CP7 文件必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、测试结果和结论。
- 若发现 BLOCKING，必须写明阻断项和最小修复建议；不得直接修复业务代码。

## 禁止范围

- 不执行真实联网、真实 Tushare fetch、真实写 lake。
- 不写 token/API key/cookie/session。
- 不修改 `market_data/connectors/**`、`engine/**`、`data/**`、`reports/**`、`delivery/**`、`pyproject.toml`、`uv.lock`。
- 不启动 S06 或 Backtrader。

## 执行结果

| 项目 | 结果 |
|---|---|
| 执行状态 | completed |
| CP7 结果 | `process/checks/CP7-CR005-S04-hs300-local-benchmark-VERIFICATION-DONE.md`，结论 PASS |
| 指定测试 | `UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_market_data_hs300_benchmark.py` -> 6 passed in 0.66s |
| 最小回归 | `UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_market_data_hs300_benchmark.py tests/test_market_data_multidataset_quality_readers.py` -> 15 passed in 0.78s |
| 全量回归 | `UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q` -> 90 passed in 3.00s |
| 安全 / 边界扫描 | PASS；未发现危险命令、token 读取/泄露、connector/runtime/storage import、网络客户端或自动写 lake |
| 停止点 | 未更新 `process/STATE.md`、`process/STORY-STATUS.md`、`DEV-LOG.md`，未标记 Story verified |
