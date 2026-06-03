---
handoff_id: "META-DEV-CR004-STORY-018-IMPLEMENT-2026-05-30"
from: "meta-po"
to: "meta-dev"
change_id: "CR-004"
story_id: "STORY-018"
wave_id: "CR004-BATCH-D"
batch_id: "CR004-BATCH-D-STORY-018"
status: "completed"
created_at: "2026-05-30T14:25:41+08:00"
completed_at: "2026-05-30T14:41:12+08:00"
dispatch:
  mode: "spawn_agent"
  platform: "codex"
  tool_name: "spawn_agent"
  agent_role: "meta-dev"
  agent_id: "019e7793-8f33-7b92-87d9-f5c09947daf4"
  agent_name: "dev-kong"
  spawned_at: "2026-05-30T14:32:00+08:00"
  completed_at: "2026-05-30T14:39:00+08:00"
  closed_at: "2026-05-30T14:39:30+08:00"
result:
  cp6: "process/checks/CP6-STORY-018-cr004-experiment-readonly-benchmark-CODING-DONE.md"
  implementation_status: "completed"
  verification_status: "pending-cp7"
---

# META-DEV Handoff：CR-004 Batch D / STORY-018 实现

## Dispatch

| 字段 | 值 |
|---|---|
| mode | `spawn_agent` |
| tool_name | `spawn_agent` |
| agent_role | `meta-dev` |
| agent_id / thread_id | `019e7793-8f33-7b92-87d9-f5c09947daf4` |
| agent_name | `dev-kong` |
| completed | 是 |
| inline fallback | 未使用 |

## 任务范围

只实现 STORY-018 LLD 限定范围：

- `market_data/benchmarks.py`
- `experiments/run_experiment_10.py`
- `experiments/run_experiment_12.py`
- `tests/test_market_data_experiment_readers.py`

明确未授权、未修改范围：

- `engine/**`
- `market_data/readers.py`
- `market_data/connectors/**`
- `market_data/runtime.py`
- `market_data/storage.py`
- `data/**`
- `reports/**`
- `delivery/**`
- `pyproject.toml`
- `uv.lock`

## 完成内容

1. 实验十 / 十二新增 `--market-data-root`，作为 `--market-data-lake-root` 的兼容别名。
2. 实验十 / 十二新增 `--benchmark-path`，支持显式本地 hs300 benchmark fixture，只读读取 parquet / csv / parquet 目录。
3. `resolve_hs300_benchmark(..., benchmark_path=...)` 优先读取显式 benchmark path；该路径不调用 connector/runtime/storage，不联网，不写 lake。
4. `BenchmarkResult.to_metadata()` 增加结构化 benchmark metadata 字段。
5. 缺 benchmark 时返回结构化 `unavailable` 或 `required_missing`，不把真实 `hs300_index` 字段静默填成 proxy。
6. 保持 CR007 兼容：缺真实 benchmark 时实验十 / 十二仍保留 `proxy_baseline` 字段语义，但不写 `hs300_index`。
7. 新增 `tests/test_market_data_experiment_readers.py` 覆盖参数、显式 benchmark path、缺 benchmark、proxy 兼容、no write 和静态边界。

## 验证

| 命令 | 结果 | 说明 |
|---|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_market_data_experiment_readers.py tests/test_market_data_hs300_benchmark.py tests/test_cr007_experiment_real_benchmark_consumption.py` | PASS：19 passed | STORY-018 专项、既有 hs300 benchmark、CR007 benchmark 兼容回归。 |
| `PYTHONPYCACHEPREFIX=/tmp/cr004-s18-pycompile uv run --python 3.11 python -m py_compile market_data/benchmarks.py experiments/run_experiment_10.py experiments/run_experiment_12.py tests/test_market_data_experiment_readers.py` | PASS | 编译检查通过。 |
| `git diff --check -- market_data/benchmarks.py experiments/run_experiment_10.py experiments/run_experiment_12.py tests/test_market_data_experiment_readers.py` | PASS | whitespace 检查通过。 |

## 风险与边界

- 本实现不抓取真实沪深 300，不生成真实 benchmark，不写真实 lake。
- `--allow-benchmark-unavailable` 当前作为兼容参数接收；默认缺基准即写 unavailable metadata 并继续，`--require-benchmark` 才返回 required_missing。
- `market_data/benchmarks.py` 在本次开始前已有 CR018 相关未提交变更；本 handoff 只声明 STORY-018 增量，不把全文件 diff 都归因于本 Story。
