---
handoff_id: "META-DEV-CR007-BATCH-A-DEV-W2-S02-2026-05-20"
from_agent: "meta-po"
to_agent: "meta-dev"
status: "completed"
created_at: "2026-05-20T23:10:25+08:00"
workflow_id: "local_backtest"
change_id: "CR-007"
batch_id: "CR007-BATCH-A"
wave_id: "CR007-DEV-W2"
story_id: "CR007-S02-benchmark-calendar-backfill"
recommended_agent_name: "dev-zhang"
recommended_thread_id: "019e45c2-383c-7cc1-a732-ee1b7652e423"
reuse_key: "meta-dev|local_backtest|CR-007|CR007-S02-benchmark-calendar-backfill|CR007-DEV-W2"
dispatch:
  required: true
  mode: "resume_agent+send_input"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".codex/agents/meta-dev.toml"
  tool_name: "resume_agent/send_input"
  agent_id: "019e45c2-383c-7cc1-a732-ee1b7652e423"
  agent_name: "dev-zhang"
  thread_id: "019e45c2-383c-7cc1-a732-ee1b7652e423"
  spawned_at: ""
  resumed_at: "2026-05-21T07:09:00+08:00"
  completed_at: "2026-05-21T07:09:00+08:00"
  evidence: "主线程通过 resume_agent + send_input 恢复 agent_id/thread_id=019e45c2-383c-7cc1-a732-ee1b7652e423 执行 S02 离线实现；S01 CP6 PASS 且 S01 CP7 PASS / verified。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# Meta-Dev Handoff: CR007-BATCH-A DEV W2 S02

## 任务目标

按已确认的 `process/stories/CR007-S02-benchmark-calendar-backfill-LLD.md` 实现 `CR007-S02-benchmark-calendar-backfill`，覆盖 `hs300_index` 与 `trade_calendar` 同区间 dry-run/backfill 规划、normalize、validate、catalog、reader 与 benchmark resolver 合同。

S02 当前 dev gate 依据：`CR007-S01` 已完成 CP6 PASS 与 CP7 PASS，S01 planner/date range/coverage gate/resume policy contract 已通过 QA 验证。S02 当前可直接调度离线实现。

## 最小输入

- `process/STATE.md`
- `process/changes/CR-007-CANONICAL-DATA-COVERAGE-BACKFILL-AND-BENCHMARK-2026-05-20.md`
- `process/HLD.md`
- `process/ARCHITECTURE-DECISION.md`
- `process/STORY-BACKLOG.md`
- `process/DEVELOPMENT-PLAN.yaml`
- `process/stories/CR007-S02-benchmark-calendar-backfill.md`
- `process/stories/CR007-S02-benchmark-calendar-backfill-LLD.md`
- `process/checks/CP5-CR007-S02-benchmark-calendar-backfill-LLD-IMPLEMENTABILITY.md`
- `checkpoints/CP5-CR007-BATCH-A-LLD-BATCH.md`
- `process/checks/CP6-CR007-S01-prices-long-horizon-backfill-planner-CODING-DONE.md`

## 允许文件范围

meta-dev 只能在必要范围内修改或创建：

- `market_data/cli.py`
- `market_data/normalization.py`
- `market_data/validation.py`
- `market_data/catalog.py`
- `market_data/readers.py`
- `market_data/benchmarks.py`
- `tests/test_cr007_benchmark_calendar_backfill.py`
- `process/checks/CP6-CR007-S02-benchmark-calendar-backfill-CODING-DONE.md`
- `process/STATE.md` 中与本 Story CP6 结果、dev/verify 队列相关的运行态字段
- Story 卡片或 `DEV-LOG.md` 仅在仓库既有约定需要记录实现状态时可更新

## 禁止事项

- 不得修改 `experiments/run_experiment_13.py`、`engine/**`、`data/**`、`reports/**`、`.env`、`delivery/**`。
- 不得读取、列出、迁移、复制、比对、删除或使用旧 `data/**`。
- 不得读取、打开、覆盖或把旧 `reports/data_quality_report.csv` 作为 current truth、coverage proof 或 fixture。
- 不得读取、打印或记录 `.env`、Tushare token、NAS 用户名、NAS 密码或任何凭据。
- 不得执行真实 Tushare 抓取、真实联网 backfill、真实 `/mnt/ugreen-data-lake` 写入或真实 lake 大规模读写。
- 不得与 S03 并行开发。S02/S03 共享 `market_data/normalization.py`、`market_data/validation.py`、`market_data/readers.py`，S03 必须等待 S02 CP6 PASS 且文件冲突清理后再进入 dev_ready。

## 实现要求

- 创建或等价实现 `benchmark-calendar-backfill` dry-run 组合入口；默认 `network_calls=0`、`writes=0`。
- benchmark coverage 分母必须是 `trade_calendar.is_open=true`，不得用自然日 denominator 声明通过。
- `resolve_hs300_benchmark` 增量保持向后兼容，只能新增可选 keyword 参数和 metadata 字段，不删除 CR005 已验证字段。
- reader / benchmark resolver 不导入 connector/runtime/storage，不触发 fetch/backfill。
- 所有测试使用 tmp lake、canonical fixture、trade calendar fixture 或 monkeypatch；不依赖 token、NAS、真实 lake 写入、旧数据或旧报告。

## CP6 要求

实现完成后必须写入：

- `process/checks/CP6-CR007-S02-benchmark-calendar-backfill-CODING-DONE.md`

CP6 文件必须包含：

- Entry Criteria、Checklist、Exit Criteria、Deliverables。
- Agent Dispatch Evidence：真实 `spawn_agent` / `resume_agent` / `send_input` 的 agent_id/thread_id、tool_name、开始与完成时间。
- 修改文件清单和偏离 LLD 的差异说明。
- 测试命令、结果和失败处理。
- 安全确认：真实 Tushare 抓取=false，真实 lake 写入=false，旧 `data/**` 操作=false，旧质量报告读取/覆盖=false，凭据读取/打印=false。
- S02/S03 文件冲突说明：S02 CP6 PASS 前 S03 不得并行开发。

## 建议验证命令

```bash
uv run --python 3.11 pytest -q tests/test_cr007_benchmark_calendar_backfill.py
uv run --python 3.11 pytest -q tests/test_market_data_cli_comparison.py::test_hs300_index_cli_normalize_validate_and_read
```

如实现触及 `market_data/benchmarks.py` / readers / validation，可追加相关离线回归；不得触发联网、真实 lake 写入、凭据读取或旧数据操作。

## 后续路由

- S02 CP6 PASS 后，meta-po 调度 meta-qa 执行 S02 CP7。
- S02 CP6 PASS 且 S02/S03 文件冲突清理后，S03 才能进入 `dev_ready`。

## Completion Draft

| 字段 | 值 |
|---|---|
| completed_by | meta-dev/dev-zhang |
| completed_at | 2026-05-21T07:09:00+08:00 |
| result | CP6 PASS |
| cp6_check | `process/checks/CP6-CR007-S02-benchmark-calendar-backfill-CODING-DONE.md` |
| modified_files | `market_data/cli.py`; `market_data/validation.py`; `market_data/readers.py`; `market_data/benchmarks.py`; `tests/test_cr007_benchmark_calendar_backfill.py`; `process/checks/CP6-CR007-S02-benchmark-calendar-backfill-CODING-DONE.md`; `process/handoffs/META-DEV-CR007-BATCH-A-DEV-W2-S02-2026-05-20.md` |
| tests | `uv run --python 3.11 pytest -q tests/test_cr007_benchmark_calendar_backfill.py` = 5 passed；`uv run --python 3.11 pytest -q tests/test_market_data_cli_comparison.py::test_hs300_index_cli_normalize_validate_and_read` = 1 passed；`uv run --python 3.11 pytest -q tests/test_market_data_hs300_benchmark.py tests/test_market_data_multidataset_quality_readers.py` = 15 passed |
| safety | 未执行真实 Tushare 抓取；未联网 backfill；未写 `/mnt/ugreen-data-lake`；未读取/操作旧 `data/**`；未读取/覆盖旧 `reports/data_quality_report.csv`；未读取/打印凭据。 |
| cr008_boundary | S02 仅完成 benchmark/calendar 数据生产侧合同；未推进实验报告字段、S04 文件或文档。 |
