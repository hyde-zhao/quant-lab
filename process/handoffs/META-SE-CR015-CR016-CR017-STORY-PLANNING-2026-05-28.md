---
handoff_id: "META-SE-CR015-CR016-CR017-STORY-PLANNING-2026-05-28"
from_agent: "meta-po"
to_agent: "meta-se"
created_at: "2026-05-28T05:47:14+08:00"
completed_at: "2026-05-28T06:17:53+08:00"
status: "completed"
workflow_id: "local_backtest-cr015-cr016-cr017"
change_ids:
  - "CR-015"
  - "CR-016"
  - "CR-017"
phase: "story-planning"
dispatch:
  required: true
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-se"
  agent_path: ".agents/agents/meta-se.md"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e6b6b-8496-7371-bcaf-4368f0de8f41"
  agent_name: "se-han"
  thread_id: "019e6b6b-8496-7371-bcaf-4368f0de8f41"
  spawned_at: "2026-05-28T05:51:12+08:00"
  resumed_at: ""
  completed_at: "2026-05-28T06:17:53+08:00"
  evidence: "spawn_agent"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# META-SE CR-015 / CR-016 / CR-017 Story Planning 交接

## Trigger

用户已在 2026-05-28T05:47:14+08:00 回复：

> @meta-po 通过审批，可以按照你推荐的方案，组织子agent推进项目。

meta-po 已回填 `checkpoints/CP3-CR015-CR016-CR017-HLD-REVIEW.md` 为 `approved`。本交接只授权进入 Story Plan / CP4。

## Approved Decisions

| ID | 已批准结论 |
|---|---|
| Q-030 | raw + `adj_factor` 为事实源；qfq 以 `as_of_trade_date` 为锚点；hfq 以 provider/base date 为锚点；`provider_factor_direction` 必填；异常价格进入 quality fail/warn。 |
| Q-031 | 独立 `prices_raw`、`adj_factor`、`prices_qfq`、`prices_hfq`、`returns_adjusted` view；旧 qfq 只读保留，兼容入口输出 migration summary。 |
| Q-032 | broker lake 外置 root；schema 覆盖 order/fill/position/asset/error/reconciliation/incident；默认 retention 3 年或用户配置；敏感字段脱敏 / 禁入库。 |
| Q-033 | OMS 状态机覆盖 accepted/partial/filled/cancel_pending/canceled/rejected/failed/unknown/timeout/manual_review/frozen；unknown/timeout 不自动成功。 |
| Q-034 | pre-trade risk hard block 覆盖现金、100 股整手、T+1 可卖、可用持仓、价格口径、重复 intent、单票 / 组合限额、异常价格；失败时 adapter_calls=0。 |
| Q-035 | stage gate 固定 `shadow -> simulation -> live_readonly -> small_live -> scale_up`；每阶段有准入、退出、回退、观察窗口、资金上限和失败阈值；CR-017 未验证前阻断 scale_up。 |
| Q-036 | T 日收盘后信号，T+1 限价 / 保护价；保护带以 raw close 或 broker reference price 的可配置百分比表达；超时未成交默认撤可撤单，单 run 自动重试上限为 1。 |
| Q-037 | 盘前 / 盘中 / 盘后对账覆盖委托、成交、持仓、资产、现金；超阈值 manual_review 或 kill switch；恢复需对账 pass + 人工接管记录。 |
| Q-038 | Linux 研究节点与 Windows QMT 节点解耦；默认 signed file drop + ack/error enum，后续可升级本地 RPC；adapter 只在 Windows；责任分为 research owner、trading node owner、approver。 |

## Required Inputs

| 输入 | 路径 |
|---|---|
| 当前状态 | `process/STATE.md` |
| CP3 人工审查结果 | `checkpoints/CP3-CR015-CR016-CR017-HLD-REVIEW.md` |
| CP3 自动预检 | `process/checks/CP3-CR015-CR016-CR017-HLD-CONSISTENCY.md` |
| CP2 intake 决策 | `checkpoints/CP2-CR015-CR016-CR017-INTAKE-DECISION-BRIEF.md` |
| 场景基线 | `process/USE-CASES.md`，重点 UC-10 至 UC-12 |
| 需求基线 | `process/REQUIREMENTS.md`，重点 REQ-098 至 REQ-122 |
| 澄清日志 | `process/CLARIFICATION-LOG.md`，重点 Q-030 至 Q-038 |
| 主 HLD | `process/HLD.md`，重点 §31 |
| 数据湖 HLD | `process/HLD-DATA-LAKE.md`，重点 §18 |
| QMT companion HLD | `process/HLD-QMT-TRADING.md` |
| ADR | `process/ARCHITECTURE-DECISION.md`，重点 ADR-053 至 ADR-061、AD-Q50 至 AD-Q58 |
| CR-015 | `process/changes/CR-015-QMT-TRADING-FOUNDATION-2026-05-27.md` |
| CR-016 | `process/changes/CR-016-QMT-SIMULATION-LIVE-ACTIVATION-2026-05-27.md` |
| CR-017 | `process/changes/CR-017-ADJUSTMENT-POLICY-DUAL-VIEW-SUPPORT-2026-05-27.md` |

## Task

按 `story-manager` 与 `wave-planner` 规则生成 CR-015 / CR-016 / CR-017 的 Story Plan，并完成 CP4 自动预检。

必须完成：

1. 增量更新 `process/STORY-BACKLOG.md`，不要覆盖已有 CR / Story 历史基线。
2. 增量更新 `process/DEVELOPMENT-PLAN.yaml`，给出 Story DAG、Wave、依赖类型、文件所有权和并行策略。
3. 创建或更新 `process/STORY-STATUS.md` 中 CR-015 / CR-016 / CR-017 的 Story 状态汇总。
4. 创建 CR-015 / CR-016 / CR-017 的 Story 卡片，路径必须在 `process/stories/` 下，使用稳定 ID 和 kebab-case slug。
5. 生成 `process/checks/CP4-CR015-CR016-CR017-STORY-DAG-PARALLEL-SAFETY.md`，结论为 `PASS` / `FAIL` / `BLOCKED`，并包含 Entry Criteria、Checklist、Exit Criteria、Deliverables。
6. 输出 LLD 设计批次建议，明确哪些 Story 可并行写 LLD，哪些开发必须串行。
7. 列出 CP5 前阻断项和不授权项。

## Planning Constraints

- CR-017 价格 / 复权合同必须先于或作为 CR-015 QMT raw 交易价隔离的 contract 依赖。
- CR-015 foundation 只允许 shadow / dry-run / mock 方向的 Story；真实 QMT API、真实账户查询、真实发单、撤单、真实 broker lake 写入必须保持 blocked 或 later-gated。
- CR-016 activation Story 必须依赖 CR-015 foundation 和 CR-017 口径边界；技术模拟盘可以规划，但真实操作仍需后续 CP5 + per-run 授权。
- Story Plan 可以并行规划 CR-017 与 CR-015 的无真实发单基础能力；CR-016 真实激活、small_live、scale_up 不得作为当前可直接实现项。
- CP4 只做自动预检，不生成 CP4 人工审查稿。
- CP4 摘要、风险和开放项必须能汇入后续 CP5 Decision Brief。

## Allowed Files

- `process/STORY-BACKLOG.md`
- `process/DEVELOPMENT-PLAN.yaml`
- `process/STORY-STATUS.md`
- `process/stories/CR015-*.md`
- `process/stories/CR016-*.md`
- `process/stories/CR017-*.md`
- `process/checks/CP4-CR015-CR016-CR017-STORY-DAG-PARALLEL-SAFETY.md`
- 本 handoff 的 `## Result Summary` 和 dispatch completion fields

## Forbidden Scope

- 不生成 LLD：不得创建或修改 `process/stories/*-LLD.md`。
- 不进入实现：不得修改业务代码、测试、`pyproject.toml`、`uv.lock`。
- 不修改 HLD / ADR / requirements / use-cases，除非发现阻断并先报告 BLOCKED。
- 不读取或输出 `.env`、token、QMT 账号、session、cookie、交易密码或任何凭据。
- 不执行真实抓取、真实写湖、publish current pointer、QMT API、发单、撤单、账户查询或账户写操作。
- 不覆盖旧报告、旧数据或旧 Story 历史记录。

## Expected Result Summary

完成后请在最终回复中给出：

- 修改 / 新增文件列表。
- Story 数、Wave 数、LLD 批次建议。
- CP4 自动预检文件与结论。
- CP5 前阻断项。
- 是否存在需要用户在 CP5 前先决策的问题。

## Result Summary

meta-se 已完成 CR-015 / CR-016 / CR-017 Story Planning 与 CP4 自动预检。

### 修改 / 新增文件

| 类型 | 路径 | 说明 |
|---|---|---|
| 更新 | `process/STORY-BACKLOG.md` | 增量追加 CR015/CR016/CR017 Story、Wave、DAG、阻断项与 CP5 待确认问题；未覆盖既有 CR / Story 历史 |
| 更新 | `process/DEVELOPMENT-PLAN.yaml` | 增量追加 CR015/CR016/CR017 Story DAG、Wave、依赖类型、文件所有权、LLD 批次建议与并行策略 |
| 更新 | `process/STORY-STATUS.md` | 增量追加 CR015/CR016/CR017 Story 状态汇总、Wave 进度、当前门控和 CP5 前阻断项 |
| 新增 | `process/checks/CP4-CR015-CR016-CR017-STORY-DAG-PARALLEL-SAFETY.md` | CP4 自动预检；包含 Entry Criteria、Checklist、Exit Criteria、Deliverables；结论 PASS |
| 新增 | `process/stories/CR017-S01-adjustment-policy-requirements-and-adr-refresh.md` | CR017 Story 卡片 |
| 新增 | `process/stories/CR017-S02-raw-prices-and-adj-factor-contract-hardening.md` | CR017 Story 卡片 |
| 新增 | `process/stories/CR017-S03-qfq-hfq-derived-view-normalization.md` | CR017 Story 卡片 |
| 新增 | `process/stories/CR017-S04-reader-api-and-policy-gates.md` | CR017 Story 卡片 |
| 新增 | `process/stories/CR017-S05-validation-quality-parity-and-leakage-tests.md` | CR017 Story 卡片 |
| 新增 | `process/stories/CR017-S06-research-qmt-consumer-docs-and-migration-guide.md` | CR017 Story 卡片 |
| 新增 | `process/stories/CR015-S01-qmt-environment-and-interface-spike.md` | CR015 Story 卡片 |
| 新增 | `process/stories/CR015-S02-qmt-broker-adapter-contract.md` | CR015 Story 卡片 |
| 新增 | `process/stories/CR015-S03-oms-order-state-machine.md` | CR015 Story 卡片 |
| 新增 | `process/stories/CR015-S04-pretrade-risk-gate.md` | CR015 Story 卡片 |
| 新增 | `process/stories/CR015-S05-broker-lake-schema-and-writer.md` | CR015 Story 卡片 |
| 新增 | `process/stories/CR015-S06-target-portfolio-to-order-intent-shadow-mode.md` | CR015 Story 卡片 |
| 新增 | `process/stories/CR015-S07-docs-and-foundation-runbook-boundary.md` | CR015 Story 卡片 |
| 新增 | `process/stories/CR016-S01-simulation-account-order-enable-gate.md` | CR016 Story 卡片 |
| 新增 | `process/stories/CR016-S02-reconciliation-service-and-reports.md` | CR016 Story 卡片 |
| 新增 | `process/stories/CR016-S03-monitoring-heartbeat-and-kill-switch.md` | CR016 Story 卡片 |
| 新增 | `process/stories/CR016-S04-simulation-live-runbook-and-approval-gates.md` | CR016 Story 卡片 |
| 新增 | `process/stories/CR016-S05-live-readonly-and-small-live-admission.md` | CR016 Story 卡片；later-gated |
| 新增 | `process/stories/CR016-S06-scale-up-and-research-maturity-gates.md` | CR016 Story 卡片；later-gated |
| 新增 | `process/stories/CR016-S07-docs-user-manual-and-incident-playbooks.md` | CR016 Story 卡片 |

### Story / Wave / LLD 批次

| 项 | 数量 / 建议 | 说明 |
|---|---|---|
| Story 总数 | 20 | CR017 6 个、CR015 7 个、CR016 7 个 |
| Wave 总数 | 8 | CR017 3 个、CR015 3 个、CR016 2 个 |
| LLD 批次建议 | 3 | `CR017-ADJUSTMENT-DUAL-VIEW-BATCH-A`、`CR015-QMT-FOUNDATION-BATCH-A`、`CR016-QMT-ACTIVATION-BATCH-A` |
| 可并行 LLD 分组 | 7 | 按 `max_parallel_lld=3` 分组，详见 `process/DEVELOPMENT-PLAN.yaml` 与 CP4 文件 |

### CP4 结果

| 检查点 | 路径 | 结论 |
|---|---|---|
| CR015/CR016/CR017 Story DAG / Parallel Safety | `process/checks/CP4-CR015-CR016-CR017-STORY-DAG-PARALLEL-SAFETY.md` | PASS |

### CP5 前阻断项

| ID | 阻断项 | 状态 |
|---|---|---|
| CR15-17-CP4-BLK-001 | 20 个 Story 尚未生成全量 LLD | OPEN |
| CR15-17-CP4-BLK-002 | CP5 自动预检与人工确认尚未发生 | OPEN |
| CR15-17-CP4-BLK-003 | CR017 复权双视图未验证前阻断 scale_up | OPEN |
| CR15-17-CP4-BLK-004 | CR015 foundation 未验证前阻断 CR016 activation | OPEN |
| CR15-17-CP4-BLK-005 | CR016-S05 / CR016-S06 属于 later-gated 范围 | OPEN |
| CR15-17-CP4-BLK-006 | 真实外部操作未授权 | OPEN |
| CR15-17-CP4-BLK-007 | 文件所有权冲突需 LLD 收敛 | OPEN |

### 边界复核

- 未创建或修改任何 `*-LLD.md`。
- 未修改业务代码、测试、`pyproject.toml` 或 `uv.lock`。
- 未读取凭据、未执行真实外部操作、未覆盖旧报告、旧数据或旧 Story 历史。
- 本结果只授权 meta-po 将 CP4 摘要汇入 CP5 Decision Brief；不授权 LLD 或实现。
