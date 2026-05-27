---
handoff_id: "META-SE-CR005-HS300-TUSHARE-DESIGN-REVISION-2026-05-17"
from_agent: "meta-po"
to_agent: "meta-se"
status: "completed"
created_at: "2026-05-17T18:33:09+08:00"
workflow_id: "local_backtest"
change_id: "CR-005"
story_id: "CR005-HS300-DESIGN-REVISION"
wave_id: "CR005-ROUND3-REVISION"
dispatch:
  required: true
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-se"
  agent_path: ".codex/agents/meta-se.toml"
  tool_name: "spawn_agent"
  agent_id: "019e3584-ec99-7210-aa06-5e15f29d3bef"
  agent_name: "se-chu"
  thread_id: "019e3584-ec99-7210-aa06-5e15f29d3bef"
  spawned_at: "2026-05-17T19:02:35+08:00"
  resumed_at: ""
  completed_at: "2026-05-17T19:02:35+08:00"
  evidence: "用户回报主线程已通过 spawn_agent 真实并行调度 meta-se；agent_id=019e3584-ec99-7210-aa06-5e15f29d3bef，nickname=se-chu，status completed then closed。meta-se 已按本 handoff 修订 CR-005、HLD、ADR、Story Backlog、Development Plan 和 CR005-S01..S06 Story 卡片，补齐两步契约、BenchmarkResult typed schema、hs300_index backfill job spec、accuracy/quality AC、CR005-S01->S04 DAG、S04/S06 dev_gate。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# Handoff：CR-005 第三轮 hs300 / Tushare 方案与计划修订

## 任务

请以 `meta-se` 身份修订 CR-005 方案层与计划层文档，不实现代码，不进入 CP5。

必须处理第三轮聚合评审结论：

1. 修订 `process/changes/CR-005-TUSHARE-5000-DATA-LAYER-REMEDIATION-2026-05-17.md`、`process/HLD.md` §22、`process/ARCHITECTURE-DECISION.md` ADR-015 / ADR-017、`process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml` 和 CR005-S01/S02/S03/S04/S05/S06 Story 卡片。
2. 明确两步契约：
   - 消费层缺 `hs300_index` 时只返回 structured `unavailable` / `required_missing`，可携带 `next_action` / `remediation_job_spec`，不得自动执行 fetch/backfill。
   - 数据层只有用户显式执行 `market_data` Tushare fetch/backfill job 时，才允许联网并写入 raw / manifest / canonical / quality / catalog / gold。
3. 补齐 `BenchmarkResult` typed schema，至少覆盖 status、dataset、source、index_code、interface、date range、coverage、quality_status、missing_reason、required、remediation job spec、catalog entry、run / lineage。
4. 补齐 `hs300_index` backfill job spec：dataset、source、exact interface、index code、start/end、lake root、run id、resume policy、dry-run 默认、manifest / quality / catalog 路径、错误枚举。
5. 补齐 accuracy / quality AC：benchmark_kind、trade calendar coverage denominator、missing trade dates、gap reason、duplicate key、source lineage、raw checksum 或等价 lineage、quality thresholds、available/unavailable 映射。
6. 修订 Story dev_gate 和 Development Plan：`market_data/cli.py` 或等价 job 所有权不得晚于 CR005-S04；CR005-S04/S06 必须等待 hs300 backfill job、reader quality、BenchmarkResult schema 和 benchmark policy 冻结。
7. 修订 CP3/CP4 自动预检和人工审查稿的输入要求；不要把被第三轮评审 superseded 的旧稿继续提交用户 approve。

## 最小上下文

- `process/STATE.md`
- `process/checks/REVIEW-CR005-HS300-TUSHARE-SUMMARY.md`
- `process/checks/REVIEW-CR005-HS300-TUSHARE-META-SE.md`
- `process/checks/REVIEW-CR005-HS300-TUSHARE-META-DEV.md`
- `process/checks/REVIEW-CR005-HS300-TUSHARE-META-QA.md`
- `process/changes/CR-005-TUSHARE-5000-DATA-LAYER-REMEDIATION-2026-05-17.md`
- `process/HLD.md`
- `process/ARCHITECTURE-DECISION.md`
- `process/STORY-BACKLOG.md`
- `process/DEVELOPMENT-PLAN.yaml`
- `process/stories/CR005-S01-tushare-connector-real-lake-writer.md`
- `process/stories/CR005-S02-tushare-dataset-schema-normalization.md`
- `process/stories/CR005-S03-multidataset-quality-catalog-readers.md`
- `process/stories/CR005-S04-hs300-local-benchmark.md`
- `process/stories/CR005-S05-comparison-backfill-docs.md`
- `process/stories/CR005-S06-backtrader-optional-backend.md`

## 禁止事项

- 不得实现代码、修改 `pyproject.toml` / `uv.lock`、写真实数据或 token。
- 不得进入 CP5。
- 不得把 `required_missing` 实现为 consumer 自动联网补数。
- 不得让旧等权代理填充 `hs300_index` benchmark 字段；若保留旧 proxy，必须命名为 `proxy_baseline`。

## 完成后

请回填本文件 frontmatter 的 dispatch 证据，并在结果中列出修改文件、仍为 OPEN 的 `CR5-Q*`、CP3/CP4 是否可重跑，以及是否需要 meta-qa 复核。

## 完成结果

- 状态：completed then closed。
- 修改文件：
  - `process/changes/CR-005-TUSHARE-5000-DATA-LAYER-REMEDIATION-2026-05-17.md`
  - `process/HLD.md`
  - `process/ARCHITECTURE-DECISION.md`
  - `process/STORY-BACKLOG.md`
  - `process/DEVELOPMENT-PLAN.yaml`
  - `process/stories/CR005-S01-tushare-connector-real-lake-writer.md`
  - `process/stories/CR005-S02-tushare-dataset-schema-normalization.md`
  - `process/stories/CR005-S03-multidataset-quality-catalog-readers.md`
  - `process/stories/CR005-S04-hs300-local-benchmark.md`
  - `process/stories/CR005-S05-comparison-backfill-docs.md`
  - `process/stories/CR005-S06-backtrader-optional-backend.md`
- 关键结果：补齐两步契约、`BenchmarkResult` typed schema、`hs300_index` backfill job spec、accuracy/quality AC、CR005-S01 -> CR005-S04 DAG 和 S04/S06 `dev_gate`。
