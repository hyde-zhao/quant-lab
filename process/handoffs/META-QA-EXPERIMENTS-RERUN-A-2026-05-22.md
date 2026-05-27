---
handoff_id: "META-QA-EXPERIMENTS-RERUN-A-2026-05-22"
from_agent: "meta-po"
to_agent: "meta-qa"
workflow_id: "local_backtest"
change_id: "EXPERIMENTS-RERUN"
scope: "experiments-rerun-pytest-a"
status: "completed"
created_at: "2026-05-22T08:32:13+08:00"
dispatch:
  mode: "spawn_agent"
  tool_name: "spawn_agent"
  agent_id: "019e4d19-3cba-7523-af94-dc07fb6d8a85"
  agent_name: "qa-wei"
  thread_id: "019e4d19-3cba-7523-af94-dc07fb6d8a85"
  spawned_at: "2026-05-22T08:32:45+08:00"
  completed_at: "2026-05-22T08:36:17+08:00"
result:
  status: "PASS"
  command: "uv run --python 3.11 pytest -q tests/test_story_004_013.py tests/test_cr007_experiment_real_benchmark_consumption.py tests/test_market_data_hs300_benchmark.py"
  summary: "32 passed, failed=0, blocked=0"
---

# Handoff：experiments 实践复跑 A

## 目标

复跑实验 06/07、09、10、12、13 及 benchmark / proxy 边界相关 pytest，观察是否存在回归。

## 命令

```bash
uv run --python 3.11 pytest -q tests/test_story_004_013.py tests/test_cr007_experiment_real_benchmark_consumption.py tests/test_market_data_hs300_benchmark.py
```

## 边界

- 不使用 `--env-file .env`。
- 不触发真实 Tushare。
- 不写仓库默认 `reports/**` 或真实 `data/**`。
- 不修改代码或过程文件；结果在最终回复中返回，由 meta-po 汇总。
