---
cr_id: "CR-025"
status: "closed"
impact_level: "high"
workflow_mode_before: "standard"
workflow_mode_after_change: "standard"
fast_lane_upgrade_reason: "CR-025 已从 Backtrader optional backend 单点增强修订为 production-grade research-to-execution 路线中的研究执行语义对照与接口对齐，涉及可选依赖、执行语义、clean feed、target portfolio / order intent 合同、broker/QMT 边界、回测-模拟一致性和后续研究路线治理，命中架构、依赖变更、执行契约和多模块验证，必须走 standard。"
rollback_to: "requirement-clarification"
approval_result: "cp8-approved-closed"
created_at: "2026-05-31T21:43:48+08:00"
created_by: "meta-po"
approved_by: "user"
approved_at: "2026-05-31T21:43:48+08:00"
source: "cp8-follow-up"
linked_issue: ""
parent_cr: "CR-019"
source_checkpoint: "checkpoints/CP8-CR019-DELIVERY-READINESS.md"
source_decision_id: "D-CP8-CR019-05"
follow_up_type: "research-route-deferred-capability"
risk_class: "research_to_execution_contract_and_execution_semantics"
owner: "meta-po"
revisit_condition: "用户澄清目标不是开发框架级回测框架，而是生产级策略研究回测、模拟盘和实盘框架；CR-025 需服务于 research-to-execution 主线，并在 CP3/HLD 中分析本地 Backtrader 项目 `/home/hyde/download/backtrader`。"
acceptance_criteria: "CR-025 明确 production-grade research-to-execution 的三条主线映射；Backtrader 仅作为 optional execution realism / semantic reference；lightweight 主路径不被替代；research output 到 target portfolio / order intent 的边界、clean feed、执行语义差异、Backtrader 模块级借鉴 / 适配 / 移植候选 / 禁止移植对比、安全计数、无真实 broker/QMT/provider/lake/publish 和可回滚策略均可验证。"
close_condition: "CP8 终验 approved；CR-025 仅关闭研究执行语义对照与接口对齐能力，不授权真实 broker、QMT、provider fetch、lake write、publish、simulation、live 或任何账户操作。"
cp8_auto_result: "process/checks/CP8-CR025-DELIVERY-READINESS.md"
cp8_auto_status: "PASS"
cp8_manual_review: "checkpoints/CP8-CR025-DELIVERY-READINESS.md"
cp8_manual_status: "approved"
cp8_approved_by: "user"
cp8_approved_at: "2026-06-02T23:10:16+08:00"
cp8_approval_text: "好的关闭CR025"
closed_by: "user"
closed_at: "2026-06-02T23:10:16+08:00"
closed_scope: "research execution semantic alignment、Backtrader optional semantic reference、clean feed gate、semantic diff、order_intent_draft_v1、no-copy guardrail、no-real-operation safety、follow-up route boundary"
cr_index_path: "process/changes/CR-INDEX.yaml"
source_tracking: "process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md"
cp5_approved_by: "user"
cp5_approved_at: "2026-06-02T07:19:31+08:00"
cp5_approval_text: "@meta-po 将后续多因子框架借鉴其他github项目的cr记录好，CR中需要有足够的上下文。然后继续推进CR-025"
---

# CR-025 Research execution semantic alignment and Backtrader optional reference

## 变更描述

用户确认按推荐顺序推进：先关闭 CR-029 并同步状态，再收敛旧 CR 状态，然后推进研究路线，最后推进真实 QMT 路线。

本 CR 将 CR-019 follow-up 台账中的 `CR-025 Backtrader optional execution backend hardening` 从 `candidate` 转为正式 CR。CP2 澄清后，本 CR 的目标不再表达为“开发或迁移到某个回测框架”，而是服务于生产级 `research-to-execution` 平台路线：

1. 研究可信度主线：保留数据湖、ResearchDataset、quality / PIT / benchmark / tradability / cost gate 作为研究事实源与策略准入基础。
2. 回测 / 模拟一致性主线：把 lightweight 回测、Backtrader optional semantic reference 和后续 QMT simulation 都约束到同一 target portfolio / order intent 语义链路上。
3. QMT 生产执行主线：真实 broker 触达仍由 QMT OMS / risk / adapter / broker lake / staged activation 路线承接，CR-025 不授权真实运行。

本 CR 只在不替代当前轻量主路径、不默认复制 / 移植 Backtrader 源码、不接入真实 broker、不触发真实数据抓取或写湖的前提下，定义研究执行语义对照和接口对齐边界：

1. 定义 Backtrader optional reference 的适用范围、非目标和切换条件。
2. 保持默认 lightweight engine 为研究主路径；Backtrader 只能作为显式选择的 execution realism / semantic reference。
3. 明确 clean feed 输入、执行价格、滑点 / 手续费 / 撮合语义与当前轻量引擎的差异报告。
4. 明确 research output 到 target portfolio / order intent 的衔接边界，避免研究结果无法进入 QMT OMS stage gate。
5. 明确依赖隔离和 lazy import 规则，避免默认安装或测试路径强依赖 Backtrader。
6. 要求 CP3/HLD 分析 `/home/hyde/download/backtrader` 的 GPLv3 license、模块职责、可借鉴设计、可适配接口、源码级移植候选和禁止移植模块；源码级移植若被推荐，必须单列 CP3 决策、许可证影响、维护成本和 CP5 实现授权。
7. 明确禁止真实 broker、QMT、provider fetch、lake write、publish、simulation、live 和任何账户操作。

## CP8 Follow-up 来源

| 字段 | 内容 |
|---|---|
| 父级 CR | `CR-019` |
| 来源检查点 | `checkpoints/CP8-CR019-DELIVERY-READINESS.md` |
| 来源决策 ID | `D-CP8-CR019-05` |
| follow-up 类型 | `research-route-deferred-capability` |
| 风险等级 | `research_to_execution_contract_and_execution_semantics` |
| owner | `meta-po` |
| 重访条件 | 用户澄清目标为生产级策略研究回测、模拟盘和实盘框架；CR-025 需对齐 research-to-execution 路线，而不是做框架级迁移。 |
| 验收标准 | 三条主线映射、optional reference 边界、Backtrader 本地项目模块级分析、依赖隔离、clean feed、target portfolio / order intent 衔接、执行语义差异、主路径不替代和无真实 broker/QMT 均有检查证据。 |
| 关闭条件 | CP8 approved；关闭不授权真实交易、真实数据抓取、写湖、publish、simulation、live 或 QMT。 |

## CR 冲突预检

| 检查项 | 结果 | 证据 | 处理结论 |
|---|---|---|---|
| `STATE.md.active_change` | PASS | CR-025 关闭后顶层 `active_change` 已清空 | 旧 CR-019 指针冲突保持 resolved；当前无 active formal CR。 |
| 当前 active formal CR | PASS | `CR-029` 已关闭；`CR-025` 已按用户 CP8 确认关闭 | 不并行启动 CR-026、CR-030 或 QMT CR；后续候选需单独冲突预检。 |
| CR-019 follow-up 台账 | PASS | `process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md` | `CR-025` 转 closed；`CR-026` / `CR-030` 保持 candidate，`CR-027` / `CR-028` 保持 spike_candidate。 |
| 旧 CR 状态收敛 | PASS_WITH_LIMITS | `process/checks/CP8-G2-CR-STATUS-CLOSURE-2026-05-31.md` | 已关闭 CR-014 和 CR-029；其他旧 CR 已更新为 pending close / pending CP8 / later-gated，不阻断 CR-025 intake。 |
| 正式文档影响面 | REVIEW | `README.md`、`docs/USER-MANUAL.md`、`process/HLD.md`、`process/HLD-QMT-TRADING.md`、`process/ARCHITECTURE-DECISION.md`、`process/DEVELOPMENT-PLAN.yaml` | CP2 已批准；CP3/HLD 必须记录 Backtrader 本地项目分析和模块级取舍，不直接进入实现。 |
| Story / LLD 批次 | REVIEW | Backtrader optional reference、research output / target portfolio / order intent 衔接、engine adapter / experiments / tests | 必须由 CP3/CP4/CP5 确认 Story 与 LLD 批次后才可实现。 |
| 文件 owner 冲突 | PASS_WITH_LIMITS | 当前不修改代码 | 后续若涉及 `engine/**`、`experiments/**`、`tests/**`、`pyproject.toml` / `uv.lock`，必须在 LLD 文件所有权中冻结。 |
| 外部接口 / 安全 / 运行授权 | PASS_WITH_LIMITS | 本 CR 禁止真实 broker、QMT、provider fetch、lake write、publish | 依赖变更只能在 CP5 明确批准后执行。 |
| 风险接受项和来源决策 | PASS | `D-CP8-CR019-05` | Backtrader 仍为 deferred research capability，不进入真实交易链路。 |

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `process/USE-CASES.md` | 原文档更新 | 既有 Stage 6、QMT 与研究场景基线保留；CR-025 修订为 production-grade research-to-execution 场景 | `## 修订记录` | approved-CP2 |
| `process/REQUIREMENTS.md` | 原文档更新 | 既有研究、执行和 QMT 边界需求保留；CR-025 修订 optional reference、order intent 衔接和 Backtrader 项目分析需求 | `## 修订记录` | approved-CP2 |
| `process/HLD.md` | 原文档更新 | 既有 lightweight 主路径保留；新增 research-to-execution 三主线、Backtrader optional reference 架构边界和 `/home/hyde/download/backtrader` 模块级分析 | `## 修订记录` | approved-CP3 |
| `process/HLD-QMT-TRADING.md` | 原文档更新 | 既有 QMT OMS / risk / adapter / staged activation 保留；CP3 只同步研究输出到 order intent 的接口边界 | `## 修订记录` | approved-CP3 |
| `process/ARCHITECTURE-DECISION.md` | 原文档更新 | 既有 engine / data lake / QMT ADR 保留；新增 research-to-execution route 与 optional reference ADR | `## 修订记录` | approved-CP3 |
| `process/STORY-BACKLOG.md` | 原文档更新 | 既有 Story 状态不回滚；新增 CR025 Story | `## 修订记录` | CP4-PASS |
| `process/DEVELOPMENT-PLAN.yaml` | 原文档更新 | 既有 Wave 与 CR 状态保留；新增 CR025 Wave | frontmatter / waves | CP4-PASS |
| `README.md` / `docs/USER-MANUAL.md` | 原文档更新候选 | 当前用户文档保留；CP8 后补 optional backend 使用边界 | 修订记录或相关状态章节 | pending-CP8 |

## 旧基线映射

| 原基线对象 | 新增 / 修改对象 | 保留策略 | 映射说明 |
|---|---|---|---|
| `lightweight engine` 主路径 | `backtrader_optional_reference` | 原文保留 | Backtrader 不替代 lightweight 默认主路径，只作为显式可选的 execution realism / semantic reference。 |
| `CR-015/016/019` QMT OMS / risk / adapter 基线 | `research_to_order_intent_alignment` | 原文保留 | CR-025 只定义研究侧输出如何对齐 target portfolio / order intent，不接管 QMT OMS、不发起 simulation/live。 |
| `CR-019 D-CP8-CR019-05` deferred capability | `CR-025` 正式研究路线 CR | 台账保留 + 正式 CR 承接 | CR-019 不重开；CR-025 独立走 CP2/CP3/CP5/CP8。 |
| `CR016` QMT simulation / live route | 本 CR 非目标 | 原文保留 | optional semantic reference 与 order intent draft 不授权真实 QMT、simulation 或 live。 |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论（true/false） | 处理动作 |
|------|----------|-----------|--------------------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | `REQUIREMENTS.md` | true | CP2 已确认 REQ-161..REQ-173；CR-025 范围为 production-grade research-to-execution 路线中的 optional reference、Backtrader 项目分析与 order intent 衔接，不替换旧基线。 |
| 场景层 | 是否改变测试矩阵覆盖范围 | 研究执行后端、target portfolio / order intent、Backtrader module comparison、实验 smoke、回归矩阵 | true | 增加三条主线映射、Backtrader 本地项目模块级分析、lightweight vs Backtrader 语义差异、研究到模拟衔接和依赖隔离场景。 |
| 计划层 | 是否改变 Phase、Wave、任务依赖 | `STORY-BACKLOG.md`、`DEVELOPMENT-PLAN.yaml` | true | CP4 后定义 CR025 Story / Wave，CP5 后才允许实现。 |
| 安全层 | 是否引入新的高风险动作或权限要求 | optional dependency、broker/QMT 边界、真实运行禁区 | true | 禁止真实 broker / QMT / provider / lake / publish / simulation / live；依赖变更需 CP5。 |
| 交付层 | 是否需要重新生成交付物或回归子集 | README、USER-MANUAL、测试策略、回归测试 | true | CP8 前刷新用户文档和验证报告。 |

## 回退决策

- 影响范围：局部但跨研究执行后端、实验入口、依赖声明和文档。
- 回退到阶段：`requirement-clarification`
- 需要重新确认的对象：production-grade research-to-execution 三条主线映射、optional reference 范围、Backtrader 本地项目模块级分析、源码级移植候选风险、依赖策略、research output / target portfolio / order intent 衔接、执行语义差异验收、Story / LLD 批次、真实运行禁区。

## fast-lane 判定

| 条件 | 是否命中 | 说明 |
|---|---|---|
| 仅低风险轻量实现 / 文档 / 规则修改 | false | 涉及执行语义与依赖边界。 |
| 修改架构、权限、安全边界或平台安装路径 | true | optional reference、research-to-execution 接口和 broker/QMT 禁区必须显式设计。 |
| 修改外部接口契约、文件所有权或多 Story 依赖 | true | 可能涉及 engine adapter、target portfolio / order intent contract、experiments、tests、pyproject。 |
| 需要 HLD / LLD 才能解释影响 | true | 必须先完成 CP3 / CP5。 |
| 是否保持 fast-lane | false | 升级 / 保持 standard。 |

## LLD 设计批次门禁

- 是否需要 LLD 设计批次：true
- batch_id：`CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT-BATCH-A`
- 批次范围来源：CR 影响分析 + CP4 Story Plan
- 批次内 Story：`CR025-S01-clean-feed-gate-backend-selector`、`CR025-S02-semantic-diff-schema-artifact`、`CR025-S03-order-intent-draft-qmt-boundary`、`CR025-S04-backtrader-module-reference-no-copy-guardrail`、`CR025-S05-no-real-operation-safety-verification`、`CR025-S06-route-docs-and-follow-up-handoff`
- 批次人工确认稿：`checkpoints/CP5-CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT-BATCH-A-LLD-BATCH.md`
- 批次人工确认状态：`approved`（2026-06-02T07:19:31+08:00，user）
- 开发启动条件：
  - [x] 批次内全部 Story LLD 已输出
  - [x] 批次内全部 Story CP5 自动预检已通过
  - [x] 批次 CP5 人工确认结论为 `approved`
  - [x] W1 `CR025-S01` / `CR025-S04` 的 `dev_gate` 已满足
  - [x] W1 `CR025-S01` / `CR025-S04` 的 CP6 / CP7 已 PASS，当前为 `verified`
  - [x] S02 依赖 S01 / S04 verified 已满足，CP6 / CP7 已 PASS，当前为 `verified`
  - [x] S03 依赖 S02 与 CR015 / CR017 合同已满足，CP6 / CP7 已 PASS，当前为 `verified`
  - [x] S05 依赖 S01 / S02 / S03 / S04 verified 已满足，CP6 / CP7 已 PASS，当前为 `verified`
  - [x] S06 依赖已满足，S05 verified 后 W4 串行阻塞解除，CP6 已 PASS；首轮 CP7 因 `QuantConnect LEAN` trace token 缺失失败，blocker fix CP6 已 PASS，CP7 复验 PASS，当前为 `verified`

## Story Execution 当前状态

| Story | 当前状态 | CP6 | 下一门禁 | 说明 |
|---|---|---|---|---|
| `CR025-S01-clean-feed-gate-backend-selector` | `verified` | PASS：`process/checks/CP6-CR025-S01-clean-feed-gate-backend-selector-CODING-DONE.md` | CP7 PASS：`process/checks/CP7-CR025-S01-clean-feed-gate-backend-selector-VERIFICATION-DONE.md` | 默认 lightweight 不 import Backtrader；显式 Backtrader 在 clean feed、runtime gate 或依赖不可用时结构化 blocked / unavailable。 |
| `CR025-S04-backtrader-module-reference-no-copy-guardrail` | `verified` | PASS：`process/checks/CP6-CR025-S04-backtrader-module-reference-no-copy-guardrail-CODING-DONE.md` | CP7 PASS：`process/checks/CP7-CR025-S04-backtrader-module-reference-no-copy-guardrail-VERIFICATION-DONE.md` | `migration_candidate=[]`；Backtrader 只作为执行语义 reference，不承接多因子研究主框架。 |
| `CR025-S02-semantic-diff-schema-artifact` | `verified` | PASS：`process/checks/CP6-CR025-S02-semantic-diff-schema-artifact-CODING-DONE.md` | CP7 PASS：`process/checks/CP7-CR025-S02-semantic-diff-schema-artifact-VERIFICATION-DONE.md` | semantic diff schema/artifact 受控离线实现已验证；reference 不覆盖 baseline。 |
| `CR025-S03-order-intent-draft-qmt-boundary` | `verified` | PASS：`process/checks/CP6-CR025-S03-order-intent-draft-qmt-boundary-CODING-DONE.md` | CP7 PASS：`process/checks/CP7-CR025-S03-order-intent-draft-qmt-boundary-VERIFICATION-DONE.md` | order_intent_draft_v1 离线合同已验证；不授权 QMT / MiniQMT / XtQuant / broker 操作。 |
| `CR025-S05-no-real-operation-safety-verification` | `verified` | PASS：`process/checks/CP6-CR025-S05-no-real-operation-safety-verification-CODING-DONE.md` | CP7 PASS：`process/checks/CP7-CR025-S05-no-real-operation-safety-verification-VERIFICATION-DONE.md` | fixture-only 安全验证测试已完成；真实操作计数为 0。 |
| `CR025-S06-route-docs-and-follow-up-handoff` | `verified` | PASS：`process/checks/CP6-CR025-S06-route-docs-and-follow-up-handoff-CODING-DONE.md`；blocker fix PASS：`process/checks/CP6-CR025-S06-CP7-BLOCKER-FIX-CODING-DONE.md` | CP7 复验 PASS：`process/checks/CP7-CR025-S06-route-docs-and-follow-up-handoff-REVERIFY-DONE.md` | 首轮 CP7 FAIL 证据已保留；文档不得授权真实交易、Backtrader run、publish、simulation/live 或多因子研究主框架实现。 |

## 执行链路

| 顺序 | 责任角色 | 动作 | 输入 | 输出 | 门控 | 完成后下一步 |
|---|---|---|---|---|---|---|
| 1 | `meta-po` | 创建 CR 并同步 tracking | 用户当前指令、CR-019 台账 | 本 CR、STATE、CR-INDEX | CR 已登记 | 进入 CP2 |
| 2 | `meta-pm` | 需求 / 场景澄清 | 本 CR、CR-019 deferred register、当前研究路线、用户生产级 research-to-execution 目标 | USE-CASES / REQUIREMENTS 增量、CP2 输入 | CP2 人工确认 | 交回 meta-po |
| 3 | `meta-se` | HLD / ADR / Story Plan | CP2 approved；必须分析 `/home/hyde/download/backtrader` | HLD / ADR / Story / Development Plan 增量；Backtrader module comparison matrix | CP3 / CP4 | 交回 meta-po |
| 4 | `meta-dev` | 全量 LLD 批次 | CP4 PASS；6 Story 卡片；禁止真实操作边界 | 6 份 LLD、6 份 CP5 自动预检 | CP5 自动预检 + CP5 人工确认 | 交回 meta-po 发起 CP5 |
| 5 | `meta-dev` | 受控离线实现 | CP5 approved | 代码、CP6 | CP6 | 交回 meta-po 路由验证 |
| 6 | `meta-qa` | 验证与回归 | CP6 PASS | CP7、TEST-STRATEGY 增量 | CP7 | 交回 meta-po |
| 7 | `meta-doc` / `meta-po` | 文档与终验 | verified 结果 | README / USER-MANUAL、CP8 | CP8 approved | 关闭 CR |

## 自动终验授权

- 是否启用：false
- 授权范围：不适用
- 适用检查点：CP8
- 自动通过条件：
  - [ ] 自动预检结论为 `PASS`
  - [ ] 无 `BLOCKING`
  - [ ] 无 `REQUIRED`
  - [ ] 授权动作明确包含关闭 CR 和 / 或推进 `delivered`
- 授权原文：
- 授权时间：
- 回填要求：未启用自动终验；CR-025 已由 CP8 人工确认关闭。

## 后续事项台账

- 是否存在后续事项：true
- 台账路径：`process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md`
- CR 索引路径：`process/changes/CR-INDEX.yaml`
- 一致性检查：`uv run --python 3.11 python scripts/check_cr_tracking_consistency.py --project-root .`

| 候选编号 | 标题 | 状态 | 类型 | 优先级 | 正式 CR 路径 | 相关 active CR / blocked_by / superseded_by | 当前门控 | 阻塞原因 | 下一步 |
|---|---|---|---|---:|---|---|---|---|---|
| CR-026 | Qlib isolated runner / factor workflow boundary | candidate | CR | 2 |  | blocked_by=factor panel / label window / report catalog not frozen | not-started | 等待 factor workflow 合同冻结；当前不并行启动 | 可在 CR-030 CP2/CP3 决定合并、保留拆分或转为后续 runner Spike |
| CR-030 | 多因子研究框架借鉴与研究闭环标准化 | candidate | CR | 2 |  | blocked_by=GitHub/license/维护状态/适配边界未验证 | not-started | 已记录足够上下文到 CR-019 follow-up 台账；CR-025 已关闭，若用户选择研究路线，可启动 CR-030 冲突预检 + CP2 | 正式启动时重新验证 Qlib / Alphalens / vectorbt / Zipline Reloaded / LEAN / RQAlpha / vn.py / PyBroker / bt / Backtrader 等项目的 license、维护状态和 clean-room 借鉴边界 |
| CR-020 | QMT Windows gateway 实机部署准入 | candidate | CR | 1 |  | blocked_by=runtime authorization not granted | not-started | 当前不启动真实服务 / 端口 / QMT；若用户决定生产执行链路优先，可单独启动 CR-020，但不授权交易 | 用户决定推进 QMT 真实路线时，先启动 CR-020 gateway health 准入冲突预检 + CP2 |

## 处理结论

- 审批结论：`cp8-approved-closed`
- [ ] 自动批准（低风险）
- [ ] 待人工确认（中风险）
- [x] CP8 自动预检 PASS + 人工终验 approved：CP2 / CP3 / CP5 已 approved，CP4 自动预检 PASS，6 个 Story 均已 CP6 / CP7 PASS 并 verified；S06 首轮 CP7 FAIL 已由 blocker-fix CP6 与 CP7 REVERIFY 关闭。用户于 2026-06-02T23:10:16+08:00 回复“好的关闭CR025”，CR-025 当前交付范围已关闭；关闭不授权安装依赖、运行 Backtrader、源码迁移或触发真实外部操作。

## 当前禁止事项

- 未授权修改 `pyproject.toml` / `uv.lock` 引入 Backtrader。
- 未授权真实 broker、QMT / MiniQMT / XtQuant、simulation、live、small_live、scale_up。
- 未授权 provider fetch、真实 lake write、broker lake write、catalog publish。
- 未授权读取、打印、记录或保存 token、账户、session、cookie、密码或私钥。
- 未授权把 Backtrader 结果作为默认研究 truth、替代 lightweight 主路径、simulation-ready 或 QMT admission pass。
- 未授权把 CR-025 解释为完整交易平台、模拟盘或实盘实现。

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| 父级 CR | `CR-019` | 提供 deferred capability register 和研究路线来源。 |
| 来源决策 | `D-CP8-CR019-05` | Backtrader / Qlib / minute / Level2 后置能力跟踪。 |
| 后续候选 | `CR-026` | Qlib isolated runner，等待 CR-025 或 factor workflow 合同冻结。 |
| 后续路线 | `CR-020` | 真实 QMT route 起点；可在 CR-025 CP2/CP3 范围确认后按用户决策独立启动 gateway health 准入，但不自动授权交易。 |
