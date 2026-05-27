---
handoff_id: "META-DEV-CR005-BATCH-A-LLD-2026-05-17"
from_agent: "meta-po"
to_agent: "meta-dev"
status: "completed-closed"
created_at: "2026-05-17T19:13:17+08:00"
workflow_id: "local_backtest"
change_id: "CR-005"
story_id: "CR005-BATCH-A-LLD"
wave_id: "CR005-CP5-BATCH-A"
batch_id: "CR005-BATCH-A"
dispatch:
  required: true
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".codex/agents/meta-dev.toml"
  tool_name: "spawn_agent"
  agent_id: "019e35ab-7bca-7cf2-8f2f-2f763f501565"
  agent_name: "dev-yang"
  thread_id: "019e35ab-7bca-7cf2-8f2f-2f763f501565"
  spawned_at: "reported-by-main-thread; exact spawn time not provided"
  resumed_at: ""
  completed_at: "2026-05-17T19:23:44+08:00"
  evidence: "用户回报主线程已按本 handoff 真实 spawn_agent 调度 meta-dev；agent_id=019e35ab-7bca-7cf2-8f2f-2f763f501565，nickname=dev-yang，状态 completed then closed。结果以两个 LLD、两个 Story 级 CP5 自动预检、Story 状态、STATE 与 DEV-LOG 文件为证。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# Handoff：CR-005 CP5 Batch A LLD 设计

## 执行结果回填

- 状态：completed-closed；主线程已真实 `spawn_agent` 调度 `meta-dev/dev-yang`，`agent_id=019e35ab-7bca-7cf2-8f2f-2f763f501565`。
- 输出 LLD：
  - `process/stories/CR005-S01-tushare-connector-real-lake-writer-LLD.md`
  - `process/stories/CR005-S02-tushare-dataset-schema-normalization-LLD.md`
- Story 级 CP5 自动预检：
  - `process/checks/CP5-CR005-S01-tushare-connector-real-lake-writer-LLD-IMPLEMENTABILITY.md`
  - `process/checks/CP5-CR005-S02-tushare-dataset-schema-normalization-LLD-IMPLEMENTABILITY.md`
- 未进入实现：未修改 `market_data/**`、测试实现、`pyproject.toml`、`uv.lock`、`data/**`、`reports/**` 或 `delivery/**`。
- 下一步：meta-po 聚合两个 LLD 与 Story 级 CP5 自动预检，生成 `checkpoints/CP5-CR005-BATCH-A-LLD-BATCH.md` 并发起人工确认。

## 批次范围

本批次只要求 `meta-dev` 起草 LLD，不实现代码：

- `CR005-S01`：Tushare connector 真实写湖与 hs300 backfill job spec
- `CR005-S02`：Tushare 多 dataset schema、PIT 字段与复权 normalization

批次边界理由：

- S01 / S02 是 CR-005 后续 S03 quality/readers、S04 hs300 benchmark resolver、S06 Backtrader optional backend 的基础 contract。
- A 批目标是冻结真实源写湖、`hs300_index` backfill job、dataset schema、PIT 字段、`adj_factor` / adjusted price 和 normalization 的 LLD 输入。
- 本批次不得进入实现；LLD 完成后由 meta-po 生成 CP5 Batch A 自动预检和人工审查稿，用户确认后才允许进入开发门控计算。

## 必须输出

请在 `process/stories/` 下为本批次输出 LLD 文档，文件名建议：

- `process/stories/CR005-S01-tushare-connector-real-lake-writer-LLD.md`
- `process/stories/CR005-S02-tushare-dataset-schema-normalization-LLD.md`

每个 LLD 必须保持项目 LLD 消费契约要求的 14 个可见章节，并包含：

- `tier`
- `shared_fragments`
- `open_items`
- 文件影响范围
- 接口设计
- 数据模型 / schema / typed status
- 异常处理
- 测试设计
- 实施步骤
- 回滚策略
- CP5 前置风险与未决项

## CR005-S01 LLD 强输入

必须覆盖：

1. Tushare 默认 disabled、import no-network、missing token / not allowlisted fail fast。
2. `market_data` 写湖 / 数据准备层才允许显式调用 Tushare；consumer 不得调用。
3. `hs300_index` backfill job spec：
   - `target_dataset=hs300_index`
   - `source=tushare`
   - exact interface，默认候选 `hs300_index.daily` 映射 Tushare `index_daily`
   - `index_code=399300.SZ`
   - start/end date
   - lake root
   - run id
   - resume policy
   - dry-run 默认 true
   - raw / manifest / canonical / quality / catalog 输出路径
   - 错误枚举
4. manifest / idempotency / resume / partial success contract。
5. token 不得进入 manifest、quality、catalog、stdout/stderr、日志、测试 fixture 或文档示例值。
6. CP5 QA 输入：fake provider / fixture 默认离线，真实网络只允许显式人工环境。

## CR005-S02 LLD 强输入

必须覆盖：

1. `hs300_index` raw -> canonical exact 字段映射、类型、nullable、单位、key、dedupe、sort、date parser、index code normalization。
2. `prices` 与 `adj_factor` / adjusted price / `adjustment_policy` 契约。
3. 非行情数据 `available_date` / `effective_date` / `available_at` PIT as-of join 规则。
4. `trade_calendar`、`index_weights`、`prices` / `adj_factor` 与 `hs300_index` 的 schema registry 关系。
5. 缺字段、未来可得性、复权口径混用、duplicate key 和非法日期的 fail fast / structured unavailable 行为。
6. CP5 QA 输入：`next_action` 字段表一致性和 fake backfill 后 resolver available 的后续跨 Story 集成测试必须作为 S03/S04 交接要求记录。

## 最小上下文

- `process/STATE.md`
- `process/USE-CASES.md`
- `process/REQUIREMENTS.md`
- `process/changes/CR-005-TUSHARE-5000-DATA-LAYER-REMEDIATION-2026-05-17.md`
- `process/HLD.md`
- `process/ARCHITECTURE-DECISION.md`
- `process/STORY-BACKLOG.md`
- `process/DEVELOPMENT-PLAN.yaml`
- `process/checks/CP3-CR005-HLD-PRECHECK.md`
- `process/checks/CP4-CR005-STORY-PLAN-PRECHECK.md`
- `checkpoints/CP3-CR005-HLD-REVIEW.md`
- `checkpoints/CP4-CR005-STORY-PLAN-REVIEW.md`
- `process/checks/REVIEW-CR005-HS300-TUSHARE-META-QA-POST-REVISION.md`
- `process/stories/CR005-S01-tushare-connector-real-lake-writer.md`
- `process/stories/CR005-S02-tushare-dataset-schema-normalization.md`
- 代码事实：
  - `market_data/connectors/tushare.py`
  - `market_data/source_registry.py`
  - `market_data/config.py`
  - `market_data/runtime.py`
  - `market_data/storage.py`
  - `market_data/contracts.py`
  - `market_data/validation.py`
  - `market_data/cli.py`
  - `pyproject.toml`

## 禁止事项

- 不得实现代码。
- 不得修改 `pyproject.toml` / `uv.lock`。
- 不得写真实行情数据、真实 token、真实 Tushare 返回样本或 `data/**` 大文件。
- 不得执行真实联网测试。
- 不得进入 CP6 / CP7。
- 不得把 Backtrader adapter 或 CR005-S03/S04/S05/S06 实现混入本批次。

## 完成后回报

请回填本文件 frontmatter `dispatch.tool_name`、`agent_id`、`agent_name`、`thread_id`、`spawned_at`、`completed_at` 和结果摘要，并列出：

- 生成的 LLD 文件路径
- 未决 OPEN 项
- CP5 Batch A 自动预检建议
- 是否存在阻断 CP5 人工审查的项
