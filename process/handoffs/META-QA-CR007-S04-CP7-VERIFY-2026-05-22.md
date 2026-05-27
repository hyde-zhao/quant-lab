---
handoff_id: "META-QA-CR007-S04-CP7-VERIFY-2026-05-22"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-qa"
recommended_agent_name: "qa-jin the 2nd"
status: "completed"
created_at: "2026-05-22T05:14:16+08:00"
workflow_id: "local_backtest"
change_id: "CR-007"
linked_change: "CR-008"
batch_id: "CR007-BATCH-A"
wave_id: "CR007-VERIFY-W4"
story_id: "CR007-S04-experiment-real-benchmark-consumption"
reuse_key: "meta-qa|local_backtest|CR-007|CR007-S04-experiment-real-benchmark-consumption|CR007-VERIFY-W4"
dispatch:
  required: true
  status: "completed"
  mode: "spawn_agent"
  platform: "codex"
  agent_role: "meta-qa"
  agent_path: ".agents/agents/meta-qa.md"
  tool_name: "spawn_agent"
  agent_id: "019e4c64-3c4f-7593-b962-26a379b184e8"
  agent_name: "qa-jin the 2nd"
  thread_id: "019e4c64-3c4f-7593-b962-26a379b184e8"
  spawned_at: "2026-05-22T05:15:00+08:00"
  resumed_at: ""
  completed_at: "2026-05-22T05:17:26+08:00"
  evidence: "主线程通过 spawn_agent 真实调度 meta-qa/qa-jin the 2nd 执行 CR007-S04 CP7 验证；CP7 已写入 PASS。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# META-QA Handoff: CR007-S04 CP7 Verification

## 目标

验证 `CR007-S04-experiment-real-benchmark-consumption` 的离线实现是否满足已批准 LLD、CP6 与 CR007/CR008 安全边界，并写入 CP7 验证结果。

## Entry Gate

- CR007 CP5 batch approved: `checkpoints/CP5-CR007-BATCH-A-LLD-BATCH.md`
- Story LLD confirmed: `process/stories/CR007-S04-experiment-real-benchmark-consumption-LLD.md`
- CP6 PASS: `process/checks/CP6-CR007-S04-experiment-real-benchmark-consumption-CODING-DONE.md`
- 实现 handoff completed: `process/handoffs/META-DEV-CR007-S04-IMPLEMENT-2026-05-22.md`
- Upstream CR007-S02 verified: `process/checks/CP7-CR007-S02-benchmark-calendar-backfill-VERIFICATION-DONE.md`
- Upstream CR007-S03 verified: `process/checks/CP7-CR007-S03-index-members-stock-basic-datasets-VERIFICATION-DONE.md`
- CR008-BATCH-A all verified, including `process/checks/CP7-CR008-S06-factor-research-auxiliary-data-contract-VERIFICATION-DONE.md`

## 验证范围

- `experiments/run_experiment_13.py`
- `experiments/run_experiment_10.py`
- `experiments/run_experiment_12.py`
- `tests/test_cr007_experiment_real_benchmark_consumption.py`
- `process/checks/CP6-CR007-S04-experiment-real-benchmark-consumption-CODING-DONE.md`

## 必跑验证

- `uv run --python 3.11 pytest -q tests/test_cr007_experiment_real_benchmark_consumption.py`
- `uv run --python 3.11 pytest -q tests/test_market_data_hs300_benchmark.py tests/test_cr008_proxy_real_benchmark_fields.py`
- `uv run --python 3.11 python -m py_compile experiments/run_experiment_13.py experiments/run_experiment_10.py experiments/run_experiment_12.py market_data/benchmarks.py tests/test_cr007_experiment_real_benchmark_consumption.py`
- 静态复核 forbidden import / credential / old data / old report / destructive command / data job 边界。
- 检查真实 `hs300_index` available 路径是否输出真实 benchmark metrics / equity / metadata，不输出 proxy 文件。
- 检查 optional missing 是否只输出 `proxy_baseline`，不得填充 `hs300_index` 或声明沪深300超额收益。
- 检查 `--require-benchmark` missing 是否受控 fail fast，错误含 status / missing reason。
- 检查实验十/十二 missing metadata 是否与 S04 语义一致。

## 禁止范围

- 不修改业务实现文件，除非发现验证阻塞需要在 CP7 中报告，不直接修复。
- 不联网、不真实 Tushare fetch、不真实 lake read/write。
- 不执行补数、normalize、revalidate、replay、backfill job。
- 不读取、列出、迁移、复制、比对或删除旧 `data/**`。
- 不读取或覆盖旧 `reports/data_quality_report.csv` 内容。
- 不读取、打印或记录 `.env`、token、NAS 凭据或真实私有路径。
- 不修改 `delivery/**`、HLD、ADR、Development Plan、其他 Story LLD 或 CP5。
- 不启动 CR007-S05；S05 必须等待 S04 CP7 PASS 后由 meta-po 重新计算 dev gate。

## 输出要求

- 写入 `process/checks/CP7-CR007-S04-experiment-real-benchmark-consumption-VERIFICATION-DONE.md`。
- CP7 必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、安全边界确认、测试命令与结果。
- 若验证 PASS，建议 meta-po 将 S04 推进到 `verified`，再评估 CR007-S05 dev gate。
