---
handoff_id: "META-QA-EXPERIMENTS-RERUN-B-2026-05-22"
from_agent: "meta-po"
to_agent: "meta-qa"
workflow_id: "local_backtest"
change_id: "EXPERIMENTS-RERUN"
scope: "experiments-rerun-pytest-b"
status: "completed"
created_at: "2026-05-22T08:32:13+08:00"
dispatch:
  mode: "spawn_agent"
  tool_name: "spawn_agent"
  agent_id: "019e4d19-3d01-7ad2-bcb0-9fb4ae3e2c88"
  agent_name: "qa-lv"
  thread_id: "019e4d19-3d01-7ad2-bcb0-9fb4ae3e2c88"
  spawned_at: "2026-05-22T08:32:45+08:00"
  completed_at: "2026-05-22T08:36:17+08:00"
result:
  status: "PASS"
  command: "uv run --python 3.11 pytest -q tests/test_experiment_14_data_and_benchmark.py tests/test_experiment_15_factor_framework.py tests/test_experiment_16_momentum_factor.py tests/test_cr008_research_input_metadata.py tests/test_cr008_proxy_real_benchmark_fields.py tests/test_cr008_factor_auxiliary_data_contract.py"
  summary: "42 passed, failed=0, blocked=0"
---

# Handoff：experiments 实践复跑 B

## 目标

复跑实验 14、15、16 及研究输入 metadata、proxy/real benchmark 字段、辅助数据合同相关 pytest，观察是否存在回归。

## 命令

```bash
uv run --python 3.11 pytest -q tests/test_experiment_14_data_and_benchmark.py tests/test_experiment_15_factor_framework.py tests/test_experiment_16_momentum_factor.py tests/test_cr008_research_input_metadata.py tests/test_cr008_proxy_real_benchmark_fields.py tests/test_cr008_factor_auxiliary_data_contract.py
```

## 边界

- 不使用 `--env-file .env`。
- 不触发真实 Tushare。
- 不写仓库默认 `reports/**` 或真实 `data/**`。
- 不修改代码或过程文件；结果在最终回复中返回，由 meta-po 汇总。
