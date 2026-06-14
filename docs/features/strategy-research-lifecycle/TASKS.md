---
status: "draft-cp4"
version: "1.0"
feature_id: "FEAT-10"
feature_name: "Strategy Research Lifecycle and Project Migration Governance"
source_design: "docs/features/strategy-research-lifecycle/DESIGN.md"
source_test_plan: "docs/features/strategy-research-lifecycle/TEST-PLAN.md"
cp5_batch: "CR051-STRATEGY-RESEARCH-LIFECYCLE-BATCH-A"
---

# Tasks: Strategy Research Lifecycle and Project Migration Governance

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-14 | host-orchestrator | 初始 FEAT-10 任务清单，拆分 CR051-S01..S06 的设计证据和后续实现输入 |

## Story 任务总览

| Story | LLD 策略 | 主要任务 | 输出候选 |
|---|---|---|---|
| CR051-S01-lifecycle-and-taxonomy-framework | full-lld | 冻结 lifecycle、taxonomy、状态机、idea intake 和 delivery_candidate claim boundary | `docs/research/LIFECYCLE.md`、`docs/research/STRATEGY-TAXONOMY.md` |
| CR051-S02-repository-archive-and-data-lake-governance | full-lld | 冻结 archive root、冷热分层、Git / lake / broker facts 边界和 retention policy | `docs/research/ARCHIVE-GOVERNANCE.md`、`docs/research/RESEARCH-ARCHIVE-MANIFEST-SPEC.md` |
| CR051-S03-research-pc-and-trading-pc-workflow | full-lld | 冻结研究主机、NAS、交易主机的文件流、package exchange 和 package consumer 边界 | `docs/research/HOST-WORKFLOW.md` |
| CR051-S04-registry-and-evidence-contracts | full-lld | 冻结 RunManifest、ArchiveManifest、ValidationEvidence、ProjectIdentity、MigrationInventory 合同和 guardrail | `docs/research/RESEARCH-REGISTRY-SPEC.md` |
| CR051-S05-follow-up-cr-roadmap-and-admission-gates | technical-note | 冻结 CR052..CR056 后续路线、入场证据和不授权项 | `process/changes/CR-051-STRATEGY-RESEARCH-LIFECYCLE-FRAMEWORK-2026-06-14.md` |
| CR051-S06-project-identity-rename-and-legacy-alias | technical-note | 冻结 `quant-lab` canonical name、legacy alias、README / package / docs 迁移顺序 | `docs/research/PROJECT-IDENTITY-MIGRATION.md` |

## 原子任务

| TASK-ID | Story | 动作 | 目标文件 | 描述 |
|---|---|---|---|---|
| TASK-CR051-001 | S01 | 创建 | `docs/research/LIFECYCLE.md` | 定义 idea -> project -> protocol -> run -> validation -> delivery_candidate 生命周期 |
| TASK-CR051-002 | S01 | 创建 | `docs/research/STRATEGY-TAXONOMY.md` | 定义策略族、数据依赖、执行依赖、风险类别和后续扩展字段 |
| TASK-CR051-003 | S02 | 创建 | `docs/research/ARCHIVE-GOVERNANCE.md` | 定义 Git、research archive、market data lake、broker lake 边界和冷热分层 |
| TASK-CR051-004 | S02 | 创建 | `docs/research/RESEARCH-ARCHIVE-MANIFEST-SPEC.md` | 定义 archive manifest 字段、checksum、storage tier、retention policy |
| TASK-CR051-005 | S03 | 创建 | `docs/research/HOST-WORKFLOW.md` | 定义研究主机、NAS、交易主机职责和 package exchange 流程 |
| TASK-CR051-006 | S04 | 创建 | `docs/research/RESEARCH-REGISTRY-SPEC.md` | 定义 run / validation / project identity / migration inventory registry contract |
| TASK-CR051-007 | S04 | 增加 | `tests/` 或检查脚本候选 | 后续实现阶段增加 manifest / guardrail 静态检查；CP4 不写代码 |
| TASK-CR051-008 | S05 | 更新 | `process/changes/CR-051-STRATEGY-RESEARCH-LIFECYCLE-FRAMEWORK-2026-06-14.md` | 将 CR052..CR056 路线与 CR051 gate 绑定 |
| TASK-CR051-009 | S06 | 创建 | `docs/research/PROJECT-IDENTITY-MIGRATION.md` | 定义 `quant-lab` / `local_backtest` alias、README / pyproject / package rename 顺序 |
| TASK-CR051-010 | S06 | 更新 | `README.md` / `docs/USER-MANUAL.md` 候选 | 后续实现阶段刷新对外名称；不得批量改写历史审计 |

## Wave 计划

| Wave | Story | 并行性 | 进入条件 | 完成准则 |
|---|---|---|---|---|
| CR051-W1-LIFECYCLE-ARCHIVE-IDENTITY | S01、S02、S06 | LLD 可并行；开发按文件所有权合并 | CP4 PASS | lifecycle、archive、alias 三条主线设计证据齐备 |
| CR051-W2-HOST-REGISTRY | S03、S04 | S03 依赖 S02/S06；S04 依赖 S01/S02 | W1 contract declared | host workflow 与 registry contract 可消费 |
| CR051-W3-FOLLOW-UP-GATES | S05 | 串行 | S01..S04 设计证据齐备 | CR052..CR056 gate 和 CP5 handoff 完成 |

## 不授权任务

- 不执行目录重命名、远端仓库改名、git push 或 tag 发布。
- 不扫描、挂载、复制、删除或迁移 NAS。
- 不执行 provider fetch、lake write、catalog publish、broker lake write。
- 不连接、导入或运行 QMT / MiniQMT，不读取账号、凭据、token、session 或 `.env`。
- 不批量重写历史 `process/`、handoff、CR 审计文件中的旧名。

## 完成准则

- CR051-S01..S06 均有 Story 卡片和 CP5 设计证据路径。
- Development Plan 包含 CR051 DAG、Wave 和文件所有权说明。
- CP4 自动预检证明阻断项为 0，且新增人工决策项为 0。
