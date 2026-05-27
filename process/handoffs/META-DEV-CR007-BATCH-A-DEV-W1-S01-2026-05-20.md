---
handoff_id: "META-DEV-CR007-BATCH-A-DEV-W1-S01-2026-05-20"
from_agent: "meta-po"
to_agent: "meta-dev"
status: "coding-done"
created_at: "2026-05-20T22:50:52+08:00"
workflow_id: "local_backtest"
change_id: "CR-007"
batch_id: "CR007-BATCH-A"
wave_id: "CR007-DEV-W1"
story_id: "CR007-S01-prices-long-horizon-backfill-planner"
recommended_agent_name: "dev-kong"
recommended_thread_id: "019e45c2-0270-77e2-b3a7-b5634c1e2155"
reuse_key: "meta-dev|local_backtest|CR-007|CR007-S01-prices-long-horizon-backfill-planner|CR007-DEV-W1"
dispatch:
  required: true
  mode: "send_input"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".codex/agents/meta-dev.toml"
  tool_name: "send_input"
  agent_id: "019e45c2-0270-77e2-b3a7-b5634c1e2155"
  agent_name: "dev-kong"
  thread_id: "019e45c2-0270-77e2-b3a7-b5634c1e2155"
  spawned_at: ""
  resumed_at: "2026-05-20T22:50:52+08:00"
  completed_at: "2026-05-20T23:10:00+08:00"
  evidence: "主线程通过 send_input 复用 meta-dev/dev-kong 线程执行 CR007-S01 离线实现；agent_id/thread_id=019e45c2-0270-77e2-b3a7-b5634c1e2155。已生成代码、测试和 CP6；未执行真实抓取或真实 lake 写入。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# Meta-Dev Handoff: CR007-BATCH-A DEV W1 S01

## 任务目标

按已确认的 `process/stories/CR007-S01-prices-long-horizon-backfill-planner-LLD.md` 实现 `CR007-S01-prices-long-horizon-backfill-planner`，仅覆盖长周期 `prices.daily` + `prices.adj_factor` dry-run planner、resume policy 输出、coverage gate 输出和离线测试。

CP5 批次人工确认已通过，原始审批文本为 `同意`。`implementation_allowed=true` 仅代表允许进入离线代码实现调度，不授权真实数据抓取或真实数据湖写入。

## 最小输入

- `process/STATE.md`
- `process/changes/CR-007-CANONICAL-DATA-COVERAGE-BACKFILL-AND-BENCHMARK-2026-05-20.md`
- `process/HLD.md`
- `process/ARCHITECTURE-DECISION.md`
- `process/STORY-BACKLOG.md`
- `process/DEVELOPMENT-PLAN.yaml`
- `process/stories/CR007-S01-prices-long-horizon-backfill-planner.md`
- `process/stories/CR007-S01-prices-long-horizon-backfill-planner-LLD.md`
- `process/checks/CP5-CR007-S01-prices-long-horizon-backfill-planner-LLD-IMPLEMENTABILITY.md`
- `checkpoints/CP5-CR007-BATCH-A-LLD-BATCH.md`

## 允许文件范围

meta-dev 只能在必要范围内修改或创建：

- `market_data/cli.py`
- `market_data/runtime.py`
- `market_data/connectors/tushare.py`
- `market_data/normalization.py`
- `market_data/validation.py`
- `tests/test_cr007_prices_long_horizon_backfill_planner.py`
- `process/checks/CP6-CR007-S01-prices-long-horizon-backfill-planner-CODING-DONE.md`
- `process/STATE.md` 中与本 Story CP6 结果、dev/verify 队列相关的运行态字段
- Story 卡片或 `DEV-LOG.md` 仅在仓库既有约定需要记录实现状态时可更新

## 禁止事项

- 不得修改 `engine/**`、`experiments/**`、`README.md`、`docs/USER-MANUAL.md`、`delivery/**`。
- 不得读取、列出、迁移、复制、比对、删除或使用旧 `data/**`。
- 不得读取、打开、覆盖或把旧 `reports/data_quality_report.csv` 作为 current truth、coverage proof 或 fixture。
- 不得读取、打印或记录 `.env`、Tushare token、NAS 用户名、NAS 密码或任何凭据。
- 不得执行真实 Tushare 抓取、真实联网 backfill、真实 `/mnt/ugreen-data-lake` 写入或真实 lake 大规模读写。
- 不得把 CP5 的 `implementation_allowed=true` 解释为真实数据执行授权。

## 实现要求

- 默认离线、dry-run、可单测；网络调用计数必须为 0，真实写入计数必须为 0。
- planner 必须要求显式 `--symbols` 或 `--universe-source`；两者缺失时返回结构化 `universe_missing`。
- 输出必须覆盖 `dataset`、`source`、`interfaces`、`start_date`、`end_date`、`symbols_or_universe`、`batch_count`、`date_slices`、`run_id`、`resume_policy`、`target_paths`、`coverage_gate`。
- `prices.daily` 与 `prices.adj_factor` 必须共享相同 symbol batches、date slices、run_id、resume policy 和 adjustment policy。
- target path 只允许显示 `<configured-lake-root>` 或相对路径，不得打印真实私有路径。
- 不扫描旧 `data/**` 判断 resume，不读取旧质量报告作为覆盖证明。

## CP6 要求

实现完成后必须写入：

- `process/checks/CP6-CR007-S01-prices-long-horizon-backfill-planner-CODING-DONE.md`

CP6 文件必须包含：

- Entry Criteria、Checklist、Exit Criteria、Deliverables。
- Agent Dispatch Evidence：真实 `spawn_agent` / `resume_agent` / `send_input` 的 agent_id/thread_id、tool_name、开始与完成时间。
- 修改文件清单和偏离 LLD 的差异说明。
- 测试命令、结果和失败处理。
- 安全确认：真实 Tushare 抓取=false，真实 lake 写入=false，旧 `data/**` 操作=false，旧质量报告读取/覆盖=false，凭据读取/打印=false。
- Story 状态建议：CP6 PASS 后进入 `ready-for-verification`，等待 meta-qa CP7。

## 建议验证命令

```bash
uv run --python 3.11 pytest -q tests/test_cr007_prices_long_horizon_backfill_planner.py
```

如 LLD 指定了相关离线 market_data 回归，meta-dev 可追加运行，但不得触发联网、真实 lake 写入、凭据读取或旧数据操作。

## 后续路由

- S01 CP6 PASS 后，meta-po 再调度 meta-qa 执行 S01 CP7 验证。
- S02 默认等待 S01 CP6 PASS 后进入 `dev_ready`。
- S02 与 S03 共享 `market_data/normalization.py`、`market_data/validation.py`、`market_data/readers.py`，默认不得并行开发。

## 完成记录草稿

| 字段 | 值 |
|---|---|
| completion_status | `coding-done` |
| completed_at | `2026-05-20T23:10:00+08:00` |
| cp6 | `process/checks/CP6-CR007-S01-prices-long-horizon-backfill-planner-CODING-DONE.md` |
| cp6_conclusion | `PASS` |
| implementation_files | `market_data/cli.py`; `market_data/runtime.py`; `market_data/normalization.py`; `market_data/validation.py`; `tests/test_cr007_prices_long_horizon_backfill_planner.py` |
| tests | `uv run --python 3.11 pytest -q tests/test_cr007_prices_long_horizon_backfill_planner.py` -> 11 passed; related market_data regression -> 18 passed |
| safety | `real_tushare_fetch=false; real_lake_write=false; old_data_operations=false; old_quality_report_read_or_overwrite=false; credentials_read_or_printed=false` |
| next_status_recommendation | `ready-for-verification` |
