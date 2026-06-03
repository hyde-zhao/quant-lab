---
checkpoint_id: "CP4"
checkpoint_name: "CR-030 Story DAG / 并行安全自动预检"
type: "auto_precheck"
status: "PASS"
owner: "meta-se"
created_at: "2026-06-03T08:30:00+08:00"
checked_at: "2026-06-03T08:30:00+08:00"
target:
  phase: "story-planning"
  change_id: "CR-030"
  story_scope:
    - "CR030-S01-external-reference-matrix-and-loop-contract"
    - "CR030-S02-factor-spec-run-spec-contract"
    - "CR030-S03-factor-panel-label-window-fail-closed"
    - "CR030-S04-factor-evaluation-report"
    - "CR030-S05-multifactor-combiner-portfolio-plan"
    - "CR030-S06-experiment-manifest-report-catalog"
    - "CR030-S07-strategy-admission-package-handoff"
    - "CR030-S08-safety-docs-and-follow-up-boundary"
  wave_scope:
    - "CR030-W1-CONTRACT-GOVERNANCE"
    - "CR030-W2-PANEL-EVALUATION"
    - "CR030-W3-COMBINATION-MANIFEST"
    - "CR030-W4-ADMISSION-SAFETY-DOCS"
  lld_batch: "CR030-MULTIFACTOR-RESEARCH-LOOP-BATCH-A"
  artifacts:
    - "process/ARCHITECTURE-DECISION.md"
    - "process/STORY-BACKLOG.md"
    - "process/DEVELOPMENT-PLAN.yaml"
    - "process/stories/CR030-S01-external-reference-matrix-and-loop-contract.md"
    - "process/stories/CR030-S02-factor-spec-run-spec-contract.md"
    - "process/stories/CR030-S03-factor-panel-label-window-fail-closed.md"
    - "process/stories/CR030-S04-factor-evaluation-report.md"
    - "process/stories/CR030-S05-multifactor-combiner-portfolio-plan.md"
    - "process/stories/CR030-S06-experiment-manifest-report-catalog.md"
    - "process/stories/CR030-S07-strategy-admission-package-handoff.md"
    - "process/stories/CR030-S08-safety-docs-and-follow-up-boundary.md"
    - "checkpoints/CP3-CR030-HLD-REVIEW.md"
manual_checkpoint: ""
---

# CP4 CR-030 Story DAG / 并行安全自动预检

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| CR-030 CP3 已人工 approve | PASS | `checkpoints/CP3-CR030-HLD-REVIEW.md` status=`approved` | 用户已接受 DQ-CP3-CR030-01 至 DQ-CP3-CR030-07；CP3 只授权进入 Story Plan / CP4。 |
| HLD / ADR baseline 已冻结到 Story Plan 输入 | PASS | `process/HLD.md` §35、`process/ARCHITECTURE-DECISION.md` ADR-079..086 | Story Plan 以 CP3 approved HLD / ADR 为输入。 |
| CR-030 Story Backlog / Development Plan 已增量更新 | PASS | `process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml` | 已追加 CR030-S01..S08、CR030-W1..W4、DAG、文件所有权和 CP5 前门控。 |
| CR-030 Story 卡片齐全 | PASS | `process/stories/CR030-S01..S08*.md` | 8 张 Story 卡片均存在，状态为 `planned-pending-cp5`，`implementation_allowed=false`。 |
| 禁止真实操作边界仍有效 | PASS | Story cards、`process/DEVELOPMENT-PLAN.yaml` `cr030_increment.no_real_operation_boundary` | 本轮未授权 LLD、实现、依赖变更、外部项目运行、源码迁移、provider/lake/publish、QMT/simulation/live/account/order/cancel 或凭据读取。 |

## Checklist

| # | 检查项 | 状态 | 证据 | 处理意见 |
|---|---|---|---|---|
| 1 | Story 数与 Wave 数一致 | PASS | Backlog / Development Plan / 8 张 Story cards | CR-030 = 8 个 Story、4 个 Wave、1 个全量 LLD 批次 `CR030-MULTIFACTOR-RESEARCH-LOOP-BATCH-A`。 |
| 2 | Story 覆盖需求 | PASS | CR030-S01..S08、REQ-174..REQ-185 | S01 覆盖 REQ-174/175/184，S02 覆盖 REQ-176/183，S03 覆盖 REQ-177，S04 覆盖 REQ-178，S05 覆盖 REQ-179，S06 覆盖 REQ-180，S07 覆盖 REQ-181，S08 覆盖 REQ-182/185。 |
| 3 | Use Case 覆盖完整 | PASS | UC-20..UC-27 映射 | UC-20/21 -> S01，UC-22 -> S02，UC-23 -> S03，UC-24 -> S04，UC-25 -> S05，UC-26 -> S06，UC-27 -> S07/S08。 |
| 4 | Story 粒度合理 | PASS | Story cards `目标` / `AI 可执行任务清单` | 每张 Story 可独立进入 LLD，且具备输入、输出、接口、约束、验证和 AC。 |
| 5 | AC 明确 | PASS | Story cards `acceptance_criteria` | 每张 Story 均含量化条件，覆盖字段率、错误计数、禁止操作计数或声明命中次数。 |
| 6 | INVEST 基本满足 | PASS | Story 列表与卡片 | 每张 Story 都有独立价值、明确合同边界、可估算范围、可测试验收；跨 Story 依赖已显式声明。 |
| 7 | 依赖关系完整 | PASS | `process/DEVELOPMENT-PLAN.yaml` `cr030_increment.dependency_graph` | 内部依赖为 S01 -> S02 -> S03 -> S04 -> S05/S06 -> S07 -> S08，并包含 CR011/CR019/CR025 外部只读合同依赖。 |
| 8 | 依赖类型明确 | PASS | Story frontmatter `dependency_type` | 已标注 `reference-boundary-contract`、`schema-contract`、`panel-label-contract`、`evaluation-report-contract`、`stage6-admission-contract` 等类型。 |
| 9 | DAG 无环 | PASS | `cr030_increment.dag_validation_result.cycles=[]` | 依赖单向从合同治理流向面板/评价、组合/manifest、准入/文档；无回边。 |
| 10 | `depends_on` 引用有效 | PASS | Development Plan `external_nodes` / Story cards | CR030 内部引用均存在；CR011-S08、CR019-S01、CR025-S03 作为已存在上游只读合同。 |
| 11 | 关键路径识别 | PASS | Development Plan Wave 顺序 | 关键路径为 S01 -> S02 -> S03 -> S04 -> S05/S06 -> S07 -> S08；S05/S06 可并行 LLD 起草但 S07 需等待二者合同冻结。 |
| 12 | 同 Wave 并行安全 | PASS | Wave policy、Story `file_ownership` | W1/W2/W3/W4 允许并行 LLD 起草；开发默认不并行或需 CP5 后按文件 owner 串行合并，避免 shared files 冲突。 |
| 13 | 文件所有权完整 | PASS | 8 张 Story cards `file_ownership` | 每张 Story 均声明 primary、shared、merge_owner 和 forbidden。 |
| 14 | LLD 批次全量化 | PASS | `CR030-MULTIFACTOR-RESEARCH-LOOP-BATCH-A` | S01..S08 必须全量进入同一 LLD 批次；可按 `max_parallel_lld=3` 分轮起草，CP5 必须统一确认。 |
| 15 | CP5 前实现门控关闭 | PASS | Story cards `implementation_allowed=false`、`dev_gate.cp5_required=true` | 8 个 Story 均未进入 dev-ready；CP5 全量确认前不得实现或标记 dev-ready。 |
| 16 | 外部项目边界清晰 | PASS | CR030-S01、ADR-079/080/086 | 外部项目只 reference / optional_spike / exclude / forbidden_migration；不得成为默认 truth / runner / provider / optimizer。 |
| 17 | CR-026 分流清晰 | PASS | CR030-S01、CR030-S08、ADR-086 | Qlib isolated runner 后置；本轮不启动 CR-026，不运行 qrun，不改依赖。 |
| 18 | StrategyAdmissionPackage 不授权交易 | PASS | CR030-S07、CR030-S08、ADR-085 | `order_intent_draft_v1` 仅为草稿引用；真实 QMT / simulation / live 仍需 CR-020..CR-024。 |
| 19 | QA 策略同步 | PASS | Story cards `validation_context` | 每张 Story 均定义验证入口、方式、依赖环境和关键验证场景；本阶段不执行验证。 |
| 20 | 禁止项未被触发 | PASS | 本轮产物范围 | 未生成 LLD；未改代码；未改依赖；未运行外部项目；未 provider/lake/publish/QMT/simulation/live；未读取凭据。 |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| DAG 校验通过 | PASS | `cr030_increment.dag_validation_result` | cycles=0，invalid_references=0，parallel_internal_dependencies=0。 |
| 文件冲突可控 | PASS | Story cards `file_ownership`、Wave policy | 未处理冲突 = 0；shared 文件在 CP5 后由 meta-po 按 merge_owner 串行调度。 |
| 首批队列可计算 | PASS | `CR030-MULTIFACTOR-RESEARCH-LOOP-BATCH-A` | S01/S02/S03 可作为前置合同 LLD 首轮候选；全量 CP5 必须等待 S01..S08 LLD 全部完成。 |
| CP5 汇总就绪 | PASS | Backlog、Development Plan、Story cards、本文件 | Story 边界、依赖、文件所有权、并行计划、OPEN / Spike 和不授权项可汇入 CP5 Decision Brief。 |
| CP4 不授权 LLD / 实现 / 真实操作 | PASS | 本文件 No-Real-Operation 声明 | CP4 只完成 Story Plan / DAG / 并行安全预检；不授权 LLD、代码、依赖、外部运行、数据写入或交易操作。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| Architecture Decision | `process/ARCHITECTURE-DECISION.md` | PASS | 已追加 ADR-079..086 与 AD-Q78..AD-Q81。 |
| Story Backlog | `process/STORY-BACKLOG.md` | PASS | 已追加 8 Story / 4 Wave / DAG / 阻塞项 / 待确认项。 |
| Development Plan | `process/DEVELOPMENT-PLAN.yaml` | PASS | 已追加 CR030 plan、依赖图、并行策略、文件所有权和 no-real-operation gates。 |
| Story 卡片 | `process/stories/CR030-S01-external-reference-matrix-and-loop-contract.md` | PASS | 外部项目矩阵与总合同。 |
| Story 卡片 | `process/stories/CR030-S02-factor-spec-run-spec-contract.md` | PASS | FactorSpec / FactorRunSpec。 |
| Story 卡片 | `process/stories/CR030-S03-factor-panel-label-window-fail-closed.md` | PASS | FactorPanel / LabelWindow fail-closed。 |
| Story 卡片 | `process/stories/CR030-S04-factor-evaluation-report.md` | PASS | 单因子评价报告。 |
| Story 卡片 | `process/stories/CR030-S05-multifactor-combiner-portfolio-plan.md` | PASS | 多因子组合。 |
| Story 卡片 | `process/stories/CR030-S06-experiment-manifest-report-catalog.md` | PASS | Manifest / Catalog。 |
| Story 卡片 | `process/stories/CR030-S07-strategy-admission-package-handoff.md` | PASS | StrategyAdmissionPackage / handoff。 |
| Story 卡片 | `process/stories/CR030-S08-safety-docs-and-follow-up-boundary.md` | PASS | Safety / docs / follow-up boundary。 |
| CP4 自动预检 | `process/checks/CP4-CR030-STORY-DAG-PARALLEL-SAFETY.md` | PASS | 本文件。 |

## No-Real-Operation 声明

| 操作类别 | 本轮状态 | 说明 |
|---|---|---|
| LLD 生成 | NOT_AUTHORIZED / NOT_DONE | 本轮只做 Story Plan / CP4，不创建 `CR030-*-LLD.md`。 |
| 代码实现 | NOT_AUTHORIZED / NOT_DONE | 未修改 `engine/**`、`trading/**`、`tests/**`、`docs/**` 等实现目标文件。 |
| 依赖变更 | NOT_AUTHORIZED / NOT_DONE | 未修改 `pyproject.toml`、`uv.lock`，未安装依赖。 |
| 外部项目 clone/install/run | NOT_AUTHORIZED / NOT_DONE | 未 clone/install/run Qlib、Alphalens、vectorbt、PyBroker、bt、Zipline Reloaded、QuantConnect LEAN、RQAlpha、vn.py、Backtrader 或其他外部项目。 |
| 外部源码复制 / 裁剪 / 改写 / 迁移 | NOT_AUTHORIZED / NOT_DONE | 未复制、裁剪、改写、vendor、fork 或源码级迁移外部项目代码 / 样例 / 测试 / 数据。 |
| provider fetch / lake / publish / reports overwrite | NOT_AUTHORIZED / NOT_DONE | 未抓取真实 provider，未写 lake，未 publish，未覆盖 reports。 |
| QMT / MiniQMT / XtQuant / gateway | NOT_AUTHORIZED / NOT_DONE | 未调用真实接口、未启动 gateway、未访问账户、未发单、未撤单、未查询账户。 |
| simulation / live run | NOT_AUTHORIZED / NOT_DONE | 未发起 simulation、live_readonly、small_live、scale_up 或任何真实 run。 |
| 凭据读取 | NOT_AUTHORIZED / NOT_DONE | 未读取 `.env`、token、secret、账户配置、broker 配置、交易密码、私钥、cookie 或 session。 |

## 结论

- 结论：`PASS`
- Story 数：8
- Wave 数：4
- LLD 批次：1，`CR030-MULTIFACTOR-RESEARCH-LOOP-BATCH-A`
- DAG cycles：0
- invalid references：0
- parallel internal dependency conflicts：0
- implementation allowed before CP5：false
- unauthorized operation executed count：0
- not-authorized category count：19
- 阻断项：0
- 豁免项：0
- 下一步：由 meta-po 组织 CR030-S01..S08 全量 LLD 队列；CP5 自动预检和人工确认前不得生成实现、不得改依赖、不得运行外部项目、不得源码迁移或触发任何真实数据 / 交易 / 凭据操作。
