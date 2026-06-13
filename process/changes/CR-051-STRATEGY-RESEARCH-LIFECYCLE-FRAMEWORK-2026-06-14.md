---
cr_id: "CR-051"
status: "blocked-design-draft-pending-active-lock"
impact_level: "high"
workflow_mode_before: "standard"
workflow_mode_after_change: "standard"
fast_lane_upgrade_reason: "命中研究生命周期架构、策略类型治理、归档拓扑、仓库边界、数据湖边界、研究 PC / 交易 PC 使用方式和后续多 CR 路线；不得使用 fast-lane。"
rollback_to: "CR051 CP2 requirement baseline"
approval_result: "design-draft-created-pending-cp2"
created_at: "2026-06-14T01:03:43+08:00"
created_by: "host-orchestrator"
approved_by: ""
approved_at: ""
source: "user"
linked_issue: ""
parent_cr: "CR-046"
source_checkpoint: "process/changes/CR-046-FOLLOW-UP-TRACKING-2026-06-13.md"
source_decision_id: "USER-20260614-STRATEGY-RESEARCH-LIFECYCLE-FIRST"
follow_up_type: "strategy-research-lifecycle-framework"
risk_class: "research_lifecycle_architecture_repository_archive_governance"
owner: "host-orchestrator"
revisit_condition: "CR046 恢复 / 关闭、CR051 正式 CP2 intake、或用户要求改变研究仓库 / 交易 PC 使用边界时重访。"
acceptance_criteria: "完成完整策略研究生命周期框架设计，覆盖信息收集、idea、立项、策略类型 taxonomy、研究协议、研究过程数据、报告、交付件、归档、数据湖、仓库拓扑、研究 PC 和交易 PC 使用方式，以及 CR052+ 后续路线。"
close_condition: "CR051 通过 CP8，且框架设计、归档设计、仓库使用设计、策略 taxonomy 和后续 CR 路线均完成验证；不要求完成多因子实现或任何真实交易运行。"
cr_index_path: "process/changes/CR-INDEX.yaml"
---

# CR-051 Strategy Research Lifecycle Framework

## 变更描述

用户确认后续策略研究路线应按以下顺序推进：

1. 先完成完整策略研究生命周期框架设计。
2. 再在新框架上把多因子策略的完整证明周期实现完成。
3. 最后再加入事件型、机器学习、择时、技术型、统计套利等其他策略类型。

本 CR 聚焦第 1 步：建立统一的策略研究生命周期框架和项目归档 / 仓库 / 数据湖治理设计，使后续 CR052 多因子完整证明周期、CR053 事件型策略、CR054 ML Spike 等能直接消费该框架。

CR051 只做设计和契约，不交付具体策略，不恢复 CR046，不启动 CR048 / CR049，不连接 QMT / MiniQMT，不读取凭据，不执行 provider fetch / lake write / catalog publish，不 submit/cancel，不 simulation/live。

## 当前状态与冲突预检

| 项 | 结论 |
|---|---|
| 当前 active formal CR | CR046 仍处于 `active-cp6-pass-ready-for-verification`，但用户已要求挂起 |
| CR051 来源 | CR046 follow-up candidate + 用户 2026-06-14 明确要求开始写 CR051 |
| 冲突判断 | CR051 与 CR046 有研究交付合同关联，但本轮只做研究生命周期框架设计，不触碰 CR046 CP7、不启动交易交付、不执行 runtime |
| 状态处理 | 为避免伪造 active lock，CR051 当前标记为 `blocked-design-draft-pending-active-lock`；正式推进 CP2/CP3 前需由用户确认是否释放 / 并行处理 CR046 锁 |
| 不授权边界 | 不恢复 CR046、不启动 CR047/CR048/CR049、不执行真实传输 / 导入 / 运行 / 交易 / 凭据 / provider / lake / publish |

## CP8 Follow-up 来源

| 字段 | 内容 |
|---|---|
| 父级 CR | `CR-046` |
| 来源检查点 | `process/changes/CR-046-FOLLOW-UP-TRACKING-2026-06-13.md` |
| 来源决策 ID | `USER-20260614-STRATEGY-RESEARCH-LIFECYCLE-FIRST` |
| follow-up 类型 | `strategy-research-lifecycle-framework` |
| 风险等级 | `research_lifecycle_architecture_repository_archive_governance` |
| owner | `host-orchestrator` |
| 重访条件 | CR051 正式 CP2 intake、CR046 状态变化、或用户调整仓库 / 归档 / PC 使用边界 |
| 验收标准 | 生命周期、策略 taxonomy、归档、仓库拓扑、数据湖边界、PC 使用方式和后续 CR 路线设计完成 |
| 关闭条件 | CR051 CP8 approved；多因子完整证明周期转 CR052 |

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `docs/design/HLD-CR051-STRATEGY-RESEARCH-LIFECYCLE-FRAMEWORK.md` | 新增 | N/A | 文档头部 `## 修订记录` | draft-created |
| `docs/design/BLUEPRINT.md` | 原文档更新 | 保留 FEAT-03 多因子研究和 FEAT-09 策略交付基线，后续追加 FEAT-10 策略研究生命周期 | `## 修订记录` | pending |
| `docs/design/DOMAIN-MAP.md` | 原文档更新 | 保留 CR030 / CR046 对象，后续追加 StrategyIdea / ResearchProject / ResearchProtocol / ResearchArchive 等对象 | `## 修订记录` | pending |
| `docs/design/DEPENDENCY-MAP.md` | 原文档更新 | 保留 FEAT-03 / FEAT-09 依赖，后续追加 FEAT-10 读写边界 | `## 修订记录` | pending |
| `docs/research/CR046-RESEARCH-FRAMEWORK-FOLLOWUP.md` | 原文档更新 | 保留 CR046 面向 QMT/MiniQMT 输出合同的 narrower baseline，CR051 扩展为完整生命周期 | `## 修订记录` | pending |
| `process/changes/CR-046-FOLLOW-UP-TRACKING-2026-06-13.md` | 原文档更新 | 保留 CR051-candidate 来源；追加正式设计稿路径和后续路线 | 文档对应行 | draft-created |
| `process/STATE.md` | 原文档更新 | 保留 CR046 挂起恢复点；追加 CR051 设计草案记录 | `history` | draft-created |
| `process/changes/CR-INDEX.yaml` | 原文档更新 | 保留 CR046 active lock；追加 CR051 blocked design draft / follow-up context | `blocked_crs` | draft-created |

## 旧基线映射

| 原基线对象 | 新增 / 修改对象 | 保留策略 | 映射说明 |
|---|---|---|---|
| CR030 多因子研究闭环 | CR052 多因子完整证明周期 | 原文保留 | CR030 是多因子中段能力；CR052 在 CR051 生命周期框架上补 idea / 立项 / 完整证明 / 反馈 |
| CR039 策略候选准入 | CR052 / CR055 | 原文保留 | CR039 的 `research_baseline` 作为历史候选，不自动升级为 delivery-candidate |
| CR041 paper simulation runner | CR055 research consumption bridge | 原文保留 | CR041 是消费端能力；CR055 统一研究输出到 paper / strategy package 的桥 |
| CR046 QMT / MiniQMT 策略交付框架 | CR055 / CR056 | 原文保留 | CR046 是交易交付合同；CR051 不恢复其 CP7，也不执行 runtime |
| CR005 / CR008 / CR014 / CR018 数据湖边界 | CR051 archive / lake governance | 原文保留 | 真实市场数据湖继续外置；仓库只存 schema / manifest / redacted summary |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论 | 处理动作 |
|------|----------|-----------|------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | 策略研究生命周期、项目归档、仓库拓扑、研究 PC / 交易 PC 使用方式 | true | 后续 CP2 补充完整需求；本轮先写 CR 和 HLD 草案 |
| 场景层 | 是否改变测试矩阵覆盖范围 | 信息收集、idea、立项、研究、准入、消费、反馈 | true | 后续新增 lifecycle scenarios 和 archive governance scenarios |
| 计划层 | 是否改变 Phase、Wave、Story / 任务依赖 | CR051、CR052、CR053、CR054、CR055、CR056 | true | 本 CR 固化后续 CR roadmap；多因子实现延后到 CR052 |
| 安全层 | 是否引入新的高风险动作或权限要求 | 研究归档、交易 PC、数据湖、策略包、broker lake | true | 设计分层归档；Git 不存真实数据 / 凭据 / 账户 / broker facts；交易 PC 只消费 release package |
| 交付层 | 是否需要重新生成交付物或回归子集 | HLD、蓝图、领域图、依赖图、归档设计、后续 CR 台账 | true | 新增 CR051 HLD，后续更新索引文档和验证规则 |

## 回退决策

- 影响范围：全局研究治理，但不触碰交易 runtime。
- 回退到阶段：`CR051 CP2 requirement baseline`。
- 需要重新确认的对象：
  - 是否继续采用单一主代码仓库 + 外置 archive/lake 的拓扑。
  - 是否允许研究 PC 使用完整开发仓库，交易 PC 只使用 release package / read-only checkout。
  - 是否把多因子完整证明周期固定为 CR052。
  - 是否将事件型、ML 等策略类型后置为独立 CR。

## fast-lane 判定

| 条件 | 是否命中 | 说明 |
|---|---|---|
| 仅低风险轻量实现 / 文档 / 规则修改 | false | 涉及全局研究生命周期和仓库 / 归档架构。 |
| 修改架构、权限、安全边界或平台安装路径 | true | 需要定义研究 PC、交易 PC、archive root、data lake 和 broker lake 边界。 |
| 修改外部接口契约、文件所有权或多 Story 依赖 | true | 影响研究输出、策略交付、paper simulation 和后续策略族扩展。 |
| 需要 HLD / LLD 才能解释影响 | true | 必须先完成 HLD 和蓝图。 |
| 是否保持 fast-lane | false | 必须 standard。 |

## LLD 设计批次门禁

- 是否需要 LLD 设计批次：true
- batch_id：`CR051-STRATEGY-RESEARCH-LIFECYCLE-BATCH-A`
- 批次范围来源：CR 影响分析 + 用户确认路线
- 批次内 Story：
  - `CR051-S01-lifecycle-and-taxonomy-framework`
  - `CR051-S02-repository-archive-and-data-lake-governance`
  - `CR051-S03-research-pc-and-trading-pc-workflow`
  - `CR051-S04-registry-and-evidence-contracts`
  - `CR051-S05-follow-up-cr-roadmap-and-admission-gates`
- 批次人工确认稿：`process/checkpoints/CP5-CR051-STRATEGY-RESEARCH-LIFECYCLE-BATCH-A-LLD-BATCH.md`
- 开发启动条件：
  - [ ] CR051 CP2 requirements approved
  - [ ] CR051 CP3 HLD approved
  - [ ] CR051 CP4 Story DAG PASS
  - [ ] 批次内全部 Story 设计证据已输出
  - [ ] 批次 CP5 人工确认结论为 `approved`

## 执行链路

| 顺序 | 责任角色 | 动作 | 输入 | 输出 | 门控 | 完成后下一步 |
|---|---|---|---|---|---|---|
| 1 | `host-orchestrator` | 创建 CR051 设计草案和冲突预检 | 用户请求、CR046 follow-up、当前状态 | CR051、HLD 草案、CR tracking draft | 用户已授权写草案 | 等待正式 CP2 intake |
| 2 | `meta-pm` | 补齐研究生命周期需求和场景 | CR051 草案、HLD 草案 | USE-CASES / REQUIREMENTS / TEST-MATRIX 修订 | CP2 | 交回 host |
| 3 | `meta-se` | 完成蓝图和 HLD | CP2 baseline | BLUEPRINT / DOMAIN / DEPENDENCY / HLD / ADR | CP3 | 交回 host |
| 4 | `meta-se` | 拆 Story 和 Feature 设计 | CP3 approved | STORY-BACKLOG / DEVELOPMENT-PLAN / FEATURE-DESIGN-MATRIX | CP4 / CP5 | 进入设计证据批次 |
| 5 | `meta-dev` | 实现框架契约 / schema / guardrail | CP5 approved | docs / schema / fixtures / tests | CP6 | 交回验证 |
| 6 | `meta-qa` | 验证框架和归档边界 | CP6 evidence | VERIFICATION-REPORT / REVIEW | CP7 | 准备 CP8 |
| 7 | `host-orchestrator` | CP8 收敛 | 全部证据 | CP8 Decision Brief | 用户确认 | 关闭 CR051，启动 CR052 |

## 后续事项台账

- 是否存在后续事项：true
- 台账路径：沿用本 CR 正式文件 §后续 CR 规划；CP8 时可拆独立 follow-up tracking
- CR 索引路径：`process/changes/CR-INDEX.yaml`
- 一致性检查：`uv run --python 3.11 python scripts/check_cr_tracking_consistency.py --project-root .`

| 候选编号 | 标题 | 状态 | 类型 | 优先级 | 正式 CR 路径 | 相关 active CR / blocked_by / superseded_by | 当前门控 | 阻塞原因 | 下一步 |
|---|---|---|---|---:|---|---|---|---|---|
| CR052-candidate | 多因子策略完整证明周期 | candidate | CR | 1 |  | blocked_by=CR051 | lifecycle_framework_gate | 需 CR051 生命周期 / taxonomy / archive 设计通过 | 在新框架上实现多因子从 idea 到 delivery-candidate 的完整证明周期 |
| CR053-candidate | 事件型策略研究流程 | candidate | CR | 2 |  | blocked_by=CR052 | strategy_family_gate | 需先证明多因子完整周期 | 建立事件定义、available_at、事件窗口、异常收益和事件组合准入 |
| CR054-candidate | ML 策略研究协议 Spike | spike_candidate | Spike | 3 |  | blocked_by=CR052 | ml_spike_gate | 需生命周期和多因子 proof cycle 稳定 | 只设计 ML protocol、walk-forward、model registry、drift，不默认新增依赖 |
| CR055-candidate | 研究消费桥：StrategyAdmissionPackage -> StrategyCoreContract | candidate | CR | 2 |  | blocked_by=CR051 | consumption_bridge_gate | 需 CR051 registry / evidence 合同 | 统一研究输出到 CR041 paper simulation 和 CR046 strategy package |
| CR056-candidate | 研究反馈闭环与策略退役机制 | candidate | CR | 4 |  | blocked_by=CR055 | feedback_gate | 需 paper / shadow / runtime evidence schema | 设计 post-run attribution、drift、incident、rework、retirement 回流 |

## 处理结论

- 审批结论：`design-draft-created-pending-cp2`
- [ ] 自动批准（低风险）
- [ ] 待人工确认（中风险）
- [x] 待人工审批（高风险）

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| USER-DECISION | `USER-20260614-STRATEGY-RESEARCH-LIFECYCLE-FIRST` | 用户确认先框架设计，再多因子完整证明周期，再加入其他策略类型 |
| CR | `CR-046` | QMT / MiniQMT 双目标策略交付框架；当前挂起，不恢复 |
| CR | `CR-030` | 当前多因子研究闭环基线 |
| CR | `CR-039` | 多因子候选策略准入基线 |
| CR | `CR-041` | API-less paper simulation runner 消费端基线 |
| DECISION | `CR-005 O-S01-02` | 真实 market data lake 在 Git 外部；推荐外置可配置 lake root |
