---
status: "draft-cp4"
version: "1.0"
feature_id: "FEAT-10"
feature_name: "Strategy Research Lifecycle and Project Migration Governance"
source_blueprint: "docs/design/BLUEPRINT.md"
source_hld: "docs/design/HLD-CR051-STRATEGY-RESEARCH-LIFECYCLE-FRAMEWORK.md"
source_matrix: "docs/design/FEATURE-DESIGN-MATRIX.md"
related_stories:
  - "CR051-S01-lifecycle-and-taxonomy-framework"
  - "CR051-S02-repository-archive-and-data-lake-governance"
  - "CR051-S03-research-pc-and-trading-pc-workflow"
  - "CR051-S04-registry-and-evidence-contracts"
  - "CR051-S05-follow-up-cr-roadmap-and-admission-gates"
  - "CR051-S06-project-identity-rename-and-legacy-alias"
lld_policy_summary: "S01..S04 full-lld; S05..S06 technical-note"
confirmed_by: ""
confirmed_at: ""
---

# Feature Design: Strategy Research Lifecycle and Project Migration Governance

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-14 | host-orchestrator | 初始 FEAT-10 设计，冻结策略研究生命周期、archive governance、硬件冷热分层、项目身份迁移和后续 CR gate |

## 摘要

| 项目 | 内容 |
|---|---|
| Feature 目标 | 将策略想法、资料、研究项目、协议、运行、验证、归档、交付候选和项目迁移统一进可审计生命周期 |
| 推荐方案 | 一个主 Git 仓库 + 外部 research archive / market data lake / broker archive；`quant-lab` 为 canonical name，`local_backtest` 为 legacy alias |
| 关键取舍 | 当前只冻结结构、合同和迁移计划，不执行真实目录重命名、NAS 操作、archive 搬迁或 runtime |
| 下游 Story | CR051-S01..S06 |
| LLD 策略 | S01..S04 full-lld；S05..S06 technical-note |

## 上游依据与输入

| 来源 | 路径 / ID | 被本设计消费的内容 |
|---|---|---|
| HLD | `docs/design/HLD-CR051-STRATEGY-RESEARCH-LIFECYCLE-FRAMEWORK.md` | 单主仓库、外部 archive、冷热分层、项目迁移、后续 CR roadmap、`quant-lab` 命名 |
| Blueprint | `docs/design/BLUEPRINT.md` FEAT-10 | Feature 边界、共享能力、跨 Feature 流程和禁止依赖 |
| Domain Map | `docs/design/DOMAIN-MAP.md` OBJ-33..43 / SM-13..15 | lifecycle、archive、identity、migration 领域对象和状态机 |
| Dependency Map | `docs/design/DEPENDENCY-MAP.md` FD-17..23 | no-real-operation、lake/archive/broker facts 隔离、交易主机边界 |
| User Decisions | DQ-CP3-CR051-01..06 | 硬件分层、交易主机非研究环境、阶段化迁移、不授权真实操作和项目新名 |

## 目标与非目标

| 类型 | 内容 | 来源 |
|---|---|---|
| Goal | 定义从 InformationSource / StrategyIdea 到 delivery_candidate 的研究生命周期 | HLD-CR051 |
| Goal | 定义 ResearchArchiveManifest / RunManifest 最小字段和冷热分层归档策略 | DQ-CP3-CR051-02 |
| Goal | 定义研究主机、NAS、交易主机的职责边界 | DQ-CP3-CR051-02/03 |
| Goal | 定义 `quant-lab` canonical name 与 `local_backtest` legacy alias 的迁移边界 | DQ-CP3-CR051-06 |
| Non-Goal | 实施具体策略、多因子完整证明、真实 QMT / MiniQMT、provider fetch、lake write、catalog publish、broker lake、NAS 搬迁、目录重命名、git push | CP2 / CP3 不授权项 |

## Feature 边界与相邻对象

| 对象 | 本 Feature 负责 | 不负责 | 相邻 Feature / 模块 | 边界判定依据 |
|---|---|---|---|---|
| StrategyIdea / ResearchProject | 生命周期、taxonomy、protocol 引用、状态转换 | 具体策略算法实现 | FEAT-01 / FEAT-03 | SM-13 |
| ResearchRun / ValidationEvidence | run manifest 字段、证据分级、claim boundary | 执行真实交易或 runtime 验证 | FEAT-03 / FEAT-07 / FEAT-09 | RULE-18 / RULE-19 |
| ResearchArchiveManifest | 外部 archive 指针、checksum、storage tier、retention policy | Git 存大 artifact、真实 NAS 迁移执行 | FEAT-02 / FEAT-08 | RULE-17 / FD-20 / FD-21 |
| ProjectIdentity / MigrationInventory | canonical name、legacy alias、迁移 inventory、验证规则 | 真实目录重命名、远端仓库改名、历史 process 批量替换 | FEAT-08 / FEAT-07 | SM-14 / SM-15 |
| Trading PC package consumer | 交易主机只消费已校验 package 的边界 | 交易主机承担研究开发和 archive 主机职责 | FEAT-09 / FEAT-07 | RULE-20 / FD-23 |

## 推荐结构

| 区域 | 目标形态 | 说明 |
|---|---|---|
| Git repository | `quant-lab` canonical project；当前仓库 `local_backtest` 作为 legacy alias 迁移来源 | Git 存代码、docs、schema、manifest spec、脱敏摘要 |
| Active workspace | 主力研究主机 2T SSD | 承载开发仓库、active research workspace、近期 run/cache |
| Hot cache / exchange | NAS 512G SSD | 承载 package exchange、manifest index、近期可复用 artifact 指针 |
| Warm archive | NAS 4T RAID | 承载 `RESEARCH_ARCHIVE_ROOT` 主体和长期可复跑证据 |
| Cold archive | NAS 14T HDD | 承载冷备份、旧项目和归档副本 |
| Trading host | 交易主机 512G SSD | 只消费 strategy package / runner bundle，不承载研究 archive |

## 数据模型与状态

| Object | Owner | 关键字段 | 状态变化 | 兼容性 |
|---|---|---|---|---|
| InformationSource | FEAT-10 | source_id、source_type、title、url_or_ref、license_note、credibility | captured -> triaged -> archived | 可由后续 CR052 扩展来源类型 |
| StrategyIdea | FEAT-10 | idea_id、hypothesis、source_refs、market_scope、expected_signal | captured -> triaged -> chartered -> rejected | 不绑定具体实现 |
| ResearchProtocol | FEAT-10 | universe、data_release_ref、metric_suite、cost_model、risk_assumptions | draft -> protocol_ready -> superseded | data release 只读消费 FEAT-02 |
| ResearchRun | FEAT-10 / FEAT-03 | commit、data_release、config_hash、seed、artifact_refs | planned -> completed -> archived | artifact_refs 指向外部 archive |
| ValidationEvidence | FEAT-10 / FEAT-07 | metrics、bias_checks、claim_boundary、runtime_claim_level | missing -> partial -> pass -> blocked | pass 不等于 runtime verified |
| ProjectIdentity | FEAT-10 | canonical_name、legacy_aliases、repo_name_target、doc_alias_policy | local_backtest_legacy -> quant_lab_canonical -> alias_verified | 历史审计名保留 |
| MigrationInventory | FEAT-10 / FEAT-08 | path_class、owner_feature、move_action、verification_rule、rollback_ref | draft -> inventory_ready -> move_ready -> verified | move_ready 不等于已授权执行 |

## 接口 / 文件契约

| Interface ID | 调用方 | 被调用方 | 输入契约 | 输出契约 | 错误模型 |
|---|---|---|---|---|---|
| IF-CR051-01 | strategy idea intake | lifecycle registry | source refs、hypothesis、taxonomy entry | StrategyIdea / ResearchProject draft | missing_source / duplicate_idea |
| IF-CR051-02 | research run | ResearchArchiveManifest | commit、data release、config hash、seed、artifact refs | manifest entry / archive pointer | missing_required_field / artifact_not_externalized |
| IF-CR051-03 | delivery candidate review | FEAT-09 strategy package contract | validation evidence、risk assumptions、order intent readiness | delivery_candidate / blocked claim | runtime_claim_not_authorized |
| IF-CR051-04 | migration planner | ProjectIdentity / MigrationInventory | path inventory、owner feature、move action、verification rule | migration plan / alias compatibility report | unauthorized_real_operation / historical_rewrite_blocked |

## 权限与安全

| Rule ID | 规则 | 触发条件 | 失败行为 | 测试入口 |
|---|---|---|---|---|
| SEC-CR051-01 | Git 不存真实大 artifact、凭据、账户标识或 broker facts | inventory / docs / tests | CP7 blocked | TEST-PLAN SEC-TC-01 |
| SEC-CR051-02 | 设计通过不授权 NAS 扫描、挂载、搬迁、删除或重命名 | migration tasks | fail closed | TEST-PLAN SEC-TC-02 |
| SEC-CR051-03 | `delivery_candidate` 不得声明为 runtime verified 或 trade-ready | evidence / docs | docs guardrail fail | TEST-PLAN SEC-TC-03 |
| SEC-CR051-04 | `quant-lab` 新名不得批量改写历史 process / CR / handoff 证据 | identity migration | blocked | TEST-PLAN SEC-TC-04 |
| SEC-CR051-05 | 交易主机只消费 package，不挂载 full research archive | host workflow | blocked | TEST-PLAN SEC-TC-05 |

## Story 拆分与 LLD 策略

| Story ID | feature_design_refs | lld_policy.required_level | 触发原因 | 必须进一步设计的问题 | 可用设计证据 |
|---|---|---|---|---|---|
| CR051-S01-lifecycle-and-taxonomy-framework | `DESIGN.md` / `TEST-PLAN.md` | full-lld | lifecycle / taxonomy / claim boundary | 状态机、taxonomy、idea -> delivery_candidate 路径 | LLD |
| CR051-S02-repository-archive-and-data-lake-governance | `DESIGN.md` / `TEST-PLAN.md` | full-lld | archive / storage / lake boundary | 外部 archive 指针、冷热分层、Git / lake / broker facts 隔离 | LLD |
| CR051-S03-research-pc-and-trading-pc-workflow | `DESIGN.md` / `TASKS.md` | full-lld | host workflow / package consumer boundary | 研究主机、NAS、交易主机职责和文件流 | LLD |
| CR051-S04-registry-and-evidence-contracts | `DESIGN.md` / `TEST-PLAN.md` | full-lld | manifest schema / guardrail | RunManifest、ArchiveManifest、ValidationEvidence 字段和校验 | LLD |
| CR051-S05-follow-up-cr-roadmap-and-admission-gates | `TASKS.md` | technical-note | follow-up tracking | CR052..CR056 gate 和入场证据 | Story 技术说明 |
| CR051-S06-project-identity-rename-and-legacy-alias | `DESIGN.md` / `TASKS.md` | technical-note | alias / migration compatibility | `quant-lab` canonical 与 `local_backtest` legacy 的新旧引用策略 | Story 技术说明 |

## Gotchas

| 场景 | 风险 | 规避 |
|---|---|---|
| 把 research archive 当作 market data current truth | 研究归档证据反向污染数据事实源 | archive 只存 run / artifact 指针；current truth 仍由 FEAT-02 publish gate 管理 |
| 把 `delivery_candidate` 当成可运行策略 | 后续 QMT / MiniQMT runtime 被隐式授权 | delivery_candidate 只能进入后续 CR，runtime_candidate 必须独立授权 |
| 为了改名批量替换历史 `local_backtest` | 破坏审计链，无法还原历史上下文 | 新文档使用 `quant-lab`，历史 process / CR / handoff 保留 legacy alias |
| 在 CP4 / CP5 执行真实搬迁 | 误删、误移动或泄露数据 | CP4 / CP5 只允许 inventory spec 和验证计划；真实操作另起授权门禁 |

## 完成准则

- FEAT-10 在 BLUEPRINT / DOMAIN-MAP / DEPENDENCY-MAP / FEATURE-DESIGN-MATRIX 中一致出现。
- CR051-S01..S06 均有 `feature_design_refs`、`lld_policy`、文件所有权和 CP5 批次。
- CP4 自动预检证明 DAG 无环、无无效引用、无新增人工阻断项、未授权操作计数为 0。
