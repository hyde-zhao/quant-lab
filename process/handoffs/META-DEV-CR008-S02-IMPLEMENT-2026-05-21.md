---
handoff_id: "META-DEV-CR008-S02-IMPLEMENT-2026-05-21"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-dev"
recommended_agent_name: "dev-zhang"
status: "completed"
created_at: "2026-05-21T23:23:48+08:00"
workflow_id: "local_backtest"
change_id: "CR-008"
batch_id: "CR008-BATCH-A"
wave_id: "CR008-DEV-W2"
story_id: "CR008-S02-proxy-real-benchmark-field-separation"
reuse_key: "meta-dev|local_backtest|CR-008|CR008-S02-proxy-real-benchmark-field-separation|CR008-DEV-W2"
dispatch:
  required: true
  status: "completed"
  mode: "spawn_agent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".agents/agents/meta-dev.md"
  tool_name: "spawn_agent"
  agent_id: "019e4b24-7ee7-7b92-be23-b6587f592090"
  agent_name: "dev-zhu"
  thread_id: "019e4b24-7ee7-7b92-be23-b6587f592090"
  spawned_at: "2026-05-21T23:25:48+08:00"
  resumed_at: ""
  completed_at: "2026-05-21T23:39:19+08:00"
  evidence: "spawn_agent"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# META-DEV Handoff: CR008-S02 Implementation

## 目标

按已批准的 `process/stories/CR008-S02-proxy-real-benchmark-field-separation-LLD.md` 离线实现 proxy / real benchmark 字段隔离，并写入 CP6。

## Entry Gate

- CP5 batch approved: `checkpoints/CP5-CR008-BATCH-A-LLD-BATCH.md`
- LLD confirmed: `process/stories/CR008-S02-proxy-real-benchmark-field-separation-LLD.md`
- CR007-S02 verified: `process/checks/CP7-CR007-S02-benchmark-calendar-backfill-VERIFICATION-DONE.md`
- CR008-S01 verified: `process/checks/CP7-CR008-S01-research-input-contract-and-report-metadata-VERIFICATION-DONE.md`
- 当前 dev wave: `CR008-DEV-W2`
- 可立即调度：是。S01 已 verified，当前无 CR008 dev / qa 任务写 `experiments/run_experiment_15_factor_framework.py`。

## 写入范围

- `market_data/benchmarks.py`
- `experiments/run_experiment_13.py`
- `experiments/run_experiment_15_factor_framework.py`
- `tests/test_cr008_proxy_real_benchmark_fields.py`
- `process/checks/CP6-CR008-S02-proxy-real-benchmark-field-separation-CODING-DONE.md`

## 禁止范围

- 不修改 `market_data/connectors/**`、`market_data/runtime.py`、`market_data/storage.py`、`delivery/**`、HLD、ADR、Development Plan 或其他 Story LLD/CP5。
- 不联网、不真实 Tushare fetch、不真实 lake read/write。
- 不读取、列出、迁移、复制、比对或删除旧 `data/**`。
- 不读取或覆盖旧 `reports/data_quality_report.csv` 内容。
- 不读取、打印或记录 `.env`、token、NAS 凭据或真实私有路径。

## 测试与 CP6 要求

- 必跑：`uv run --python 3.11 pytest -q tests/test_cr008_proxy_real_benchmark_fields.py`
- 回归：`uv run --python 3.11 pytest -q tests/test_market_data_hs300_benchmark.py`
- 视修改范围复跑实验 13 / 15 相关测试。
- CP6 文件必须包含真实 Agent Dispatch Evidence、安全边界确认、测试命令与结果。

## 完成标准

- 缺真实 benchmark 时 `hs300_*` 输出次数为 0。
- 代理 benchmark 只写 `proxy_*` / `proxy_baseline`，不得写模糊 `benchmark_total_return` / `excess_return` 作为真实基准语义。
- 真实 benchmark available 时，`BenchmarkResult.to_metadata()` 的 coverage / quality / lineage / missing reason 证据被保留。
- 完成后 Story 进入 `ready-for-verification`，由 meta-po 创建 CP7 handoff。
