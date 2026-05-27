---
handoff_id: "META-DEV-CR007-S04-IMPLEMENT-2026-05-22"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-dev"
recommended_agent_name: "dev-he"
status: "completed"
created_at: "2026-05-22T04:53:48+08:00"
workflow_id: "local_backtest"
change_id: "CR-007"
linked_change: "CR-008"
batch_id: "CR007-BATCH-A"
wave_id: "CR007-DEV-W4"
story_id: "CR007-S04-experiment-real-benchmark-consumption"
reuse_key: "meta-dev|local_backtest|CR-007|CR007-S04-experiment-real-benchmark-consumption|CR007-DEV-W4"
dispatch:
  required: true
  status: "completed"
  mode: "spawn_agent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".agents/agents/meta-dev.md"
  tool_name: "spawn_agent"
  agent_id: "019e4c55-7298-7420-aebd-29b3cee9ad3a"
  agent_name: "dev-kong the 2nd"
  thread_id: "019e4c55-7298-7420-aebd-29b3cee9ad3a"
  spawned_at: "2026-05-22T04:58:54+08:00"
  resumed_at: ""
  completed_at: "2026-05-22T05:08:07+08:00"
  evidence: "主线程通过 spawn_agent 真实调度 meta-dev/dev-kong the 2nd 执行 CR007-S04 离线实现。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# META-DEV Handoff: CR007-S04 Implementation

## 目标

实现 `CR007-S04-experiment-real-benchmark-consumption` 的离线代码改造，并写入 CP6 编码完成检查结果。

## Entry Gate

- CR007 CP5 batch approved: `checkpoints/CP5-CR007-BATCH-A-LLD-BATCH.md`
- Story LLD confirmed: `process/stories/CR007-S04-experiment-real-benchmark-consumption-LLD.md`
- Upstream CR007-S02 verified: `process/checks/CP7-CR007-S02-benchmark-calendar-backfill-VERIFICATION-DONE.md`
- Upstream CR007-S03 verified: `process/checks/CP7-CR007-S03-index-members-stock-basic-datasets-VERIFICATION-DONE.md`
- CR008 priority blocker cleared: `CR008-BATCH-A` all six stories verified, including `process/checks/CP7-CR008-S06-factor-research-auxiliary-data-contract-VERIFICATION-DONE.md`

## 写入范围

- Primary:
  - `experiments/run_experiment_13.py`
  - `tests/test_cr007_experiment_real_benchmark_consumption.py`
- Shared, only if required by LLD:
  - `experiments/run_experiment_10.py`
  - `experiments/run_experiment_12.py`
  - `market_data/benchmarks.py`

## 必须实现

- 实验十三在真实 `hs300_index` benchmark available 且 coverage 合格时使用真实 benchmark metrics / equity / metadata。
- 真实 benchmark 缺失且 optional 时，只输出 `proxy_baseline`，不得填充 `hs300_index` 或声明沪深300超额收益。
- `--require-benchmark` 缺失时受控 fail fast，错误包含 status / missing reason，不写虚假 hs300 输出。
- 实验十/十二 benchmark metadata 语义与 S02 / S04 对齐；如无需修改，CP6 必须记录复核证据。
- 新增专项测试覆盖 real available、required missing、optional proxy、实验十/十二 metadata 一致、no connector/runtime/storage/no network/no old data/no legacy report/no secret。

## 必跑验证

- `uv run --python 3.11 pytest -q tests/test_cr007_experiment_real_benchmark_consumption.py`
- `uv run --python 3.11 pytest -q tests/test_market_data_hs300_benchmark.py tests/test_cr008_proxy_real_benchmark_fields.py`
- `uv run --python 3.11 python -m py_compile experiments/run_experiment_13.py experiments/run_experiment_10.py experiments/run_experiment_12.py market_data/benchmarks.py tests/test_cr007_experiment_real_benchmark_consumption.py`
- 静态复核 forbidden import / credential / old data / old report / destructive command / data job 边界。

## 禁止范围

- 不联网、不真实 Tushare fetch、不真实 lake read/write。
- 不执行补数、normalize、revalidate、replay、backfill job。
- 不读取、列出、迁移、复制、比对或删除旧 `data/**`。
- 不读取或覆盖旧 `reports/data_quality_report.csv` 内容。
- 不读取、打印或记录 `.env`、token、NAS 凭据或真实私有路径。
- 不修改 `delivery/**`、HLD、ADR、Development Plan、其他 Story LLD 或 CP5。
- 不启动 CR007-S05；S05 必须等待 S04 CP6/CP7。

## 输出要求

- 写入 `process/checks/CP6-CR007-S04-experiment-real-benchmark-consumption-CODING-DONE.md`。
- CP6 必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、安全边界确认、测试命令与结果。
- 若实现发现 LLD 与 S02/S03/CR008 verified contract 冲突，停止并在 CP6 或偏差记录中报告，不自行扩大范围。

## 完成记录

- 完成时间：2026-05-22T05:08:07+08:00
- CP6：`process/checks/CP6-CR007-S04-experiment-real-benchmark-consumption-CODING-DONE.md`，结论 `PASS`。
- 实现摘要：实验十三新增真实 `hs300_index` / required missing / optional `proxy_baseline` 三分支；实验十/十二补齐 missing metadata 语义；新增 S04 离线专项测试。
- 验证结果：
  - `uv run --python 3.11 pytest -q tests/test_cr007_experiment_real_benchmark_consumption.py`：`7 passed in 0.69s`
  - `uv run --python 3.11 pytest -q tests/test_market_data_hs300_benchmark.py tests/test_cr008_proxy_real_benchmark_fields.py`：`13 passed in 0.80s`
  - `uv run --python 3.11 python -m py_compile experiments/run_experiment_13.py experiments/run_experiment_10.py experiments/run_experiment_12.py market_data/benchmarks.py tests/test_cr007_experiment_real_benchmark_consumption.py`：PASS，退出码 0。
- 安全边界：未联网、未真实 Tushare fetch、未真实 lake read/write、未读取旧 `data/**`、未读取旧 `reports/data_quality_report.csv`、未读取凭据、未修改 `delivery/**` / HLD / ADR / Development Plan / 其他 LLD / CP5、未启动 CR007-S05。
