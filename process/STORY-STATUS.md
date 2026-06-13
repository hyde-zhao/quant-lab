---
last_updated: "2026-06-14T00:29:41+08:00"
current_wave: "CR046-W1-ARCHITECTURE-CONTRACT"
current_story: ""
current_gate: "CR-046 用户挂起于 CP6 PASS / ready-for-verification；S01..S07 保持 ready-for-verification。恢复前不得推进 CP7、不得交付具体策略、不得真实传输 / 导入、不得 QMT 运行验证、不得连接 / 安装 MiniQMT、不得 submit/cancel、不得 simulation/live、不得 provider/lake/publish 或凭据读取。"
---

## Story 状态汇总

## CR-046：QMT / MiniQMT 双目标策略交付框架

| 对象 | 状态 | 证据 | 下一步 |
|---|---|---|---|
| Story Plan | cp4-auto-pass-pending-lld | `process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml`、7 张 `process/stories/CR046-S*.md`、`process/checks/CP4-CR046-STORY-DAG-PARALLEL-SAFETY.md` | 进入全量设计证据批次；CP5 前不得实现。 |
| LLD batch | approved | `CR046-DUAL-TARGET-FRAMEWORK-BATCH-A` | S01..S05 full-lld，S06..S07 technical-note，7 份 CP5 自动预检 PASS；CP5 人工确认 approved。 |
| CP6 implementation | PASS / user-paused-before-CP7 | `process/checks/CP6-CR046-DUAL-TARGET-FRAMEWORK-BATCH-A-CODING-DONE.md` | framework-first 文档 / 契约实现完成；用户已挂起 CR046，恢复前不进入 CP7。 |
| 安全边界 | not-authorized | CP2 / CP3 / CP4 不授权项 | 真实运行、连接、安装、submit/cancel、simulation/live、凭据、provider/lake/publish 均 blocked。 |

### CR046 Story Plan 队列

| Story ID | 标题 | Wave | 状态 | 设计证据 | lld_policy | Dev Gate | 负责人 | 阻塞 |
|---|---|---|---|---|---|---|---|---|
| CR046-S01-dual-target-strategy-architecture | 双目标策略交付架构与 FEAT-09 边界 | CR046-W1-ARCHITECTURE-CONTRACT | ready-for-verification | CP6 PASS | full-lld | blocked-runtime | host-orchestrator | CP7 前不得 verified |
| CR046-S02-strategy-package-contract-and-schema | 策略包合同、目录结构与 schema | CR046-W1-ARCHITECTURE-CONTRACT | ready-for-verification | CP6 PASS | full-lld | blocked-runtime | host-orchestrator | CP7 前不得 verified |
| CR046-S03-qmt-terminal-target-framework | QMT terminal target 框架 | CR046-W2-TARGETS-INSTALL | ready-for-verification | CP6 PASS | full-lld | blocked-runtime | host-orchestrator | QMT runtime not-authorized |
| CR046-S04-miniqmt-runner-install-and-runtime-boundary | MiniQMT runner 安装设计与运行边界 | CR046-W2-TARGETS-INSTALL | ready-for-verification | CP6 PASS | full-lld | blocked-runtime | host-orchestrator | MiniQMT install / connection not-authorized |
| CR046-S05-verification-framework-and-evidence-model | 验证框架与证据模型 | CR046-W3-VALIDATION-GATES | ready-for-verification | CP6 PASS | full-lld | blocked-runtime | host-orchestrator | 不得声明 runtime verified |
| CR046-S06-follow-up-strategy-delivery-gate | 后续具体策略交付门禁 | CR046-W4-FOLLOW-UP-HANDOFF | ready-for-verification | CP6 PASS | technical-note | blocked-runtime | host-orchestrator | 不启动 CR047 / CR049 |
| CR046-S07-research-framework-follow-up-contract | 研究框架反向完善合同 | CR046-W4-FOLLOW-UP-HANDOFF | ready-for-verification | CP6 PASS | technical-note | blocked-runtime | host-orchestrator | 不实施 CR051 |

## CR-030：多因子研究框架借鉴与研究闭环标准化

| 对象 | 状态 | 证据 | 下一步 |
|---|---|---|---|
| CR intake | active-cp2-intake | `process/changes/CR-030-MULTIFACTOR-RESEARCH-FRAMEWORK-REFERENCE-AND-RESEARCH-LOOP-STANDARDIZATION-2026-06-02.md`、`process/changes/CR-INDEX.yaml`、`process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md` | 组织 CP2 需求 / 场景基线，确认 FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪、策略准入包、外部 GitHub 项目借鉴范围和 CR-026 分流。 |
| Story Plan | not-started | N/A | CP2 / CP3 未通过前不得拆最终 Story；当前仅有正式 CR 文件中的候选 Story 草案。 |
| LLD batch | not-started | `CR030-MULTIFACTOR-RESEARCH-LOOP-BATCH-A` 为候选批次名 | CP4 自动预检和 CP5 全量 LLD 确认前不得进入实现。 |
| 安全边界 | not-authorized | CR-030 §14 | 不授权实现、依赖变更、外部项目 clone/install/run/source copy、provider/lake/publish、真实 broker / QMT / simulation / live 或凭据读取。 |

## G0：CR 状态收口第一批

| CR | 收口状态 | 证据 | 说明 |
|---|---|---|---|
| CR-005 | closed | `checkpoints/CP8-G0-CR-STATUS-CLOSURE-2026-05-30.md` | CR005-S01..S06 verified，后置文档收敛静态复核 PASS。 |
| CR-006 | closed | `checkpoints/CP8-G0-CR-STATUS-CLOSURE-2026-05-30.md` | CR006-BATCH-A CP7 batch summary PASS。 |
| CR-012 | closed | `checkpoints/CP8-G0-CR-STATUS-CLOSURE-2026-05-30.md` | limited-window strict 修正最终 readiness summary PASS。 |
| CR-010 / CR-014 | 未在本批关闭 | G0 自动预检 | 后续单独收敛，避免与后续 CR 覆盖关系混写。CR004、CR007、CR008、CR015、CR016、CR017 已在 2026-06-05 CP8 / 总关闭收口中关闭。 |
| CR-016 / CR-018 | 保持门控 | STATE / STORY-STATUS | later-gated，不因 G0 关闭解除真实操作门控。 |
| CR-019 | closed-current-delivery | `checkpoints/CP8-CR019-DELIVERY-READINESS.md`、`process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md` | 当前离线合同 / 文档交付已关闭；真实运行与 deferred capabilities 仍需独立 CR / Spike。 |

## CR-025：Research Execution Semantic Alignment 与 Backtrader optional reference

| 对象 | 状态 | 证据 | 下一步 |
|---|---|---|---|
| CR intake | closed | `process/changes/CR-025-BACKTRADER-OPTIONAL-EXECUTION-BACKEND-HARDENING-2026-05-31.md`、`checkpoints/CP8-CR025-DELIVERY-READINESS.md` | W1 S01/S04、W2 S02、W3 S03、W4 S05/S06 均已 CP7 PASS；CP8 自动预检 PASS，用户于 2026-06-02T23:10:16+08:00 回复“好的关闭CR025”，CR-025 当前交付范围已关闭。 |
| CP3 HLD / ADR | approved | `checkpoints/CP3-CR025-HLD-REVIEW.md`、`process/HLD.md` §34、`process/HLD-QMT-TRADING.md` §18、`process/ARCHITECTURE-DECISION.md` ADR-074..ADR-077 | CP3 只授权进入 Story Plan / CP4，不授权 LLD / 实现 / 真实运行。 |
| CP4 Story Plan / DAG / Parallel Safety | PASS | `process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml`、`process/checks/CP4-CR025-STORY-DAG-PARALLEL-SAFETY.md` | 6 Story / 4 Wave / 1 LLD 批次已规划；DAG 无环；文件所有权和禁止操作已显式化。 |
| LLD batch | approved | `CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT-BATCH-A` | S01..S06 全量 LLD 与 CP5 自动预检已完成，CP5 人工确认已 approved。 |
| Dev / Verify Gate | all-stories-verified | CP5 approved + Story DAG + S01/S02/S03/S04/S05/S06 CP6/CP7 PASS | S06 首轮 CP7 因 `QuantConnect LEAN` trace token 缺失失败；`process/checks/CP6-CR025-S06-CP7-BLOCKER-FIX-CODING-DONE.md` 与 `process/checks/CP7-CR025-S06-route-docs-and-follow-up-handoff-REVERIFY-DONE.md` 已 PASS；下一门禁为 CP8。 |
| 安全边界 | not-authorized | CR-025 / CP3 / CP4 | LLD、实现、依赖变更、Backtrader run、Backtrader GPLv3 源码复制 / 裁剪 / 改写 / 源码级移植、真实 broker、QMT / MiniQMT / XtQuant、provider fetch、lake / broker lake 写入、publish、simulation/live 和凭据读取均未授权。 |

### CR025 Story Plan 队列

| Story ID | 标题 | Wave | 状态 | LLD | Dev Gate | 阻塞 |
|---|---|---|---|---|---|---|
| CR025-S01-clean-feed-gate-backend-selector | clean feed gate 与 backend selector | CR025-W1-FEED-GOVERNANCE | verified | approved | CP6-PASS / CP7-PASS | `process/checks/CP7-CR025-S01-clean-feed-gate-backend-selector-VERIFICATION-DONE.md` PASS；默认 Backtrader import 为 0；不得改依赖、不得运行 Backtrader。 |
| CR025-S02-semantic-diff-schema-artifact | semantic diff schema 与 artifact | CR025-W2-SEMANTIC-DIFF | verified | approved | CP6-PASS / CP7-PASS | `process/checks/CP7-CR025-S02-semantic-diff-schema-artifact-VERIFICATION-DONE.md` PASS；不得把 reference 覆盖 baseline 或声明 simulation-ready。 |
| CR025-S03-order-intent-draft-qmt-boundary | `order_intent_draft_v1` 与 QMT 后续边界 | CR025-W3-ORDER-INTENT-QMT | verified | approved | CP6-PASS / CP7-PASS | `process/checks/CP7-CR025-S03-order-intent-draft-qmt-boundary-VERIFICATION-DONE.md` PASS；不得调用 QMT / MiniQMT / XtQuant、发单、撤单或查询账户。 |
| CR025-S04-backtrader-module-reference-no-copy-guardrail | Backtrader 模块 reference / no-copy guardrail | CR025-W1-FEED-GOVERNANCE | verified | approved | CP6-PASS / CP7-PASS | `process/checks/CP7-CR025-S04-backtrader-module-reference-no-copy-guardrail-VERIFICATION-DONE.md` PASS；`migration_candidate=[]`；不得复制、裁剪、改写或源码级移植 Backtrader GPLv3 源码 / samples / tests / datas。 |
| CR025-S05-no-real-operation-safety-verification | no-real-operation safety 与验证策略 | CR025-W4-SAFETY-VERIFICATION-DOCS | verified | approved | CP6-PASS / CP7-PASS | `process/checks/CP7-CR025-S05-no-real-operation-safety-verification-VERIFICATION-DONE.md` PASS；验证策略 fixture-only，真实操作计数均为 0。 |
| CR025-S06-route-docs-and-follow-up-handoff | QMT 后续路线衔接与用户文档边界 | CR025-W4-SAFETY-VERIFICATION-DOCS | verified | approved | CP6-PASS / CP6-blocker-fix-PASS / CP7-reverify-PASS | 首轮 CP7=`process/checks/CP7-CR025-S06-route-docs-and-follow-up-handoff-VERIFICATION-DONE.md` FAIL，阻断项 `CR025-S06-CP7-F01` 已由 `process/checks/CP6-CR025-S06-CP7-BLOCKER-FIX-CODING-DONE.md` 修复，并由 `process/checks/CP7-CR025-S06-route-docs-and-follow-up-handoff-REVERIFY-DONE.md` 复验 PASS；文档不得授权真实交易、gateway 启动、Backtrader run、publish、simulation/live 或多因子研究主框架实现；CR-030 已创建正式 CR，当前处于 CP2 intake。 |

### CR025 Wave 进度

| Wave | 总数 | planned-pending-cp5 | lld-ready | lld-running | lld-review | dev-ready | in-dev | ready-for-verification | verify-running | verified | blocked-by-dependency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CR025-W1-FEED-GOVERNANCE | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| CR025-W2-SEMANTIC-DIFF | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| CR025-W3-ORDER-INTENT-QMT | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| CR025-W4-SAFETY-VERIFICATION-DOCS | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |

### CR025 当前门控

| 门控项 | 状态 | 证据 | 说明 |
|---|---|---|---|
| Story Plan | completed | `process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml`、6 张 `process/stories/CR025-S*.md` | 6 Story / 4 Wave / DAG / 文件所有权已完成。 |
| CP4 自动预检 | PASS | `process/checks/CP4-CR025-STORY-DAG-PARALLEL-SAFETY.md` | 阻断项 0、豁免项 0；可交由 meta-po 组织全量 LLD 队列。 |
| LLD | approved | `CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT-BATCH-A` | 6 份 LLD 与 6 份 CP5 自动预检已完成；CP5 人工确认已 approved。 |
| CP5 人工审查 | approved | `checkpoints/CP5-CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT-BATCH-A-LLD-BATCH.md` | 用户已要求继续推进 CR-025；仅授权受控离线实现。 |
| Real operation | not-authorized | CP3 / CP4 no-real-operation 声明 | 真实 broker、QMT / MiniQMT / XtQuant、provider fetch、lake / broker lake 写入、publish、simulation/live、凭据读取均未授权。 |

## CR-019：阶段六多因子模拟盘架构与 FastAPI Bridge

| 对象 | 状态 | 证据 | 下一步 |
|---|---|---|---|
| CR intake | closed | `process/changes/CR-019-STAGE6-MULTIFACTOR-SIMULATION-ARCHITECTURE-2026-05-30.md` | 已记录 D1-D7、FastAPI bridge 主选、signed file drop fallback 和禁止真实操作范围；CP8 已 approved closed。 |
| CP1 用户场景完备门 | PASS | `process/checks/CP1-CR019-USE-CASE-COMPLETENESS.md` | 已新增 UC-15 至 UC-18 和 TS-019-01 至 TS-019-09。 |
| CP2 需求基线自动预检 | PASS | `process/checks/CP2-CR019-REQUIREMENTS-BASELINE.md` | 已新增 REQ-138 至 REQ-160；Q-040 已确认，Q-044 新增 C 侧接口形态推荐；Q-039 至 Q-044 不阻断 CP2，需 CP3 冻结或作为已决策输入。 |
| CP2 人工审查 | approved | `checkpoints/CP2-CR019-REQUIREMENTS-BASELINE.md` | 用户已同意推荐方案；CP2 已回填 approved。 |
| CP3 HLD / ADR | approved | `checkpoints/CP3-CR019-HLD-REVIEW.md` | 用户已 approve DQ-01 至 DQ-07；DQ-04 为配对式 token/HMAC 默认启用。CP3 通过只允许进入 Story Plan / CP4，不授权 LLD / 实现 / 真实 QMT。 |
| CP4 Story Plan / DAG / Parallel Safety | PASS | `process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml`、`process/checks/CP4-CR019-STORY-DAG-PARALLEL-SAFETY.md` | 10 Story / 5 Wave / 1 LLD 批次已规划；CP4 自动预检 PASS，阻断项 0。 |
| LLD batch | approved | `process/handoffs/META-DEV-CR019-LLD-BATCH-A-2026-05-30.md`、`process/handoffs/META-DEV-CR019-LLD-BATCH-B-2026-05-30.md`、`process/handoffs/META-DEV-CR019-LLD-BATCH-C-2026-05-30.md` | 3 个 meta-dev 批次均已完成并关闭；10 份 LLD 和 10 个 CP5 自动预检均已生成且 PASS。 |
| CP5 人工审查 | approved | `checkpoints/CP5-CR019-STAGE6-QMT-BRIDGE-BATCH-A-LLD-BATCH.md` | 用户已 approve；仅授权受控离线 / fixture / dry-run 合同实现，真实操作仍 blocked。 |
| 安全边界 | blocked-real-ops | CR-019 / CP3 / CP4 | FastAPI 实现、依赖变更、服务启动、真实 QMT / MiniQMT / XtQuant、真实发单 / 撤单 / 账户查询、凭据读取、真实 provider fetch、真实 lake 写入、publish、broker lake 写入和 simulation/live run 均未授权。 |

### CR019 Story Plan 队列

| Story ID | 标题 | Wave | 状态 | LLD | Dev Gate | 阻塞 |
|---|---|---|---|---|---|---|
| CR019-S01-stage6-admission-gate-package | 阶段六 admission gate 与 package 合同 | CR019-W1-ADMISSION-BENCHMARK | verified | approved | CP6 PASS / CP7 PASS | S01 已 verified；不得启动 simulation 或调用 QMT。 |
| CR019-S02-primary-benchmark-dashboard | 多基准看板与 primary benchmark policy | CR019-W1-ADMISSION-BENCHMARK | verified | approved | CP6 PASS / CP7 PASS | S02 已 verified；不得真实补 benchmark、不得 publish。 |
| CR019-S03-qmt-cside-client-cli-contract | QMT C 侧 Python client 与薄 CLI 合同 | CR019-W2-CS-TRANSPORT | verified | approved | CP6 PASS / CP7 PASS | `process/checks/CP7-CR019-S03-qmt-cside-client-cli-contract-VERIFICATION-DONE.md` PASS；未导入 `xtquant`，未读取凭据，未启动服务。 |
| CR019-S04-windows-gateway-lifecycle-deployment | Windows FastAPI gateway 生命周期与部署合同 | CR019-W2-CS-TRANSPORT | verified | approved | CP6 PASS / CP7 PASS | `process/checks/CP7-CR019-S04-windows-gateway-lifecycle-deployment-VERIFICATION-DONE.md` PASS；仍不得新增依赖、启动 FastAPI、打开端口或访问真实 QMT 服务端；`O-CR019-S04-01` 为非阻断 OPEN。 |
| CR019-S05-pairing-hmac-auth-redaction | 配对式 token/HMAC 与日志脱敏合同 | CR019-W3-AUTH-ENDPOINT-GATE | verified | approved | CP6 PASS / CP7 PASS | `process/checks/CP7-CR019-S05-pairing-hmac-auth-redaction-VERIFICATION-DONE.md` PASS；HMAC 只识别调用方，不授权真实交易。 |
| CR019-S06-qmt-endpoint-matrix-contract | 完整 QMT endpoint matrix 与 typed blocked result | CR019-W3-AUTH-ENDPOINT-GATE | verified | approved | CP6 PASS / CP7 PASS | `process/checks/CP7-CR019-S06-qmt-endpoint-matrix-contract-VERIFICATION-DONE.md` PASS；endpoint 可见不等于真实授权。 |
| CR019-S07-run-gate-blocked-reason-integration | 运行门控与 blocked reason 集成 | CR019-W3-AUTH-ENDPOINT-GATE | verified | approved | CP6 PASS / CP7 PASS | `process/checks/CP7-CR019-S07-run-gate-blocked-reason-integration-VERIFICATION-DONE.md` PASS；run gate blocked reason 合同已冻结，不授权真实 QMT / broker 操作。 |
| CR019-S08-fallback-incident-signed-file-boundary | fallback / incident / signed file fail-closed 边界 | CR019-W4-FALLBACK-DEFERRED | verified | approved | CP6 PASS / CP7 PASS | `process/checks/CP7-CR019-S08-fallback-incident-signed-file-boundary-VERIFICATION-DONE.md` PASS；fallback / signed file 只作为 fail-closed / manual-only 合同，不授权真实操作。 |
| CR019-S09-deferred-capability-register | Backtrader / Qlib / minute / Level2 后置能力 register | CR019-W4-FALLBACK-DEFERRED | verified | approved | CP6 PASS / CP7 PASS | `process/checks/CP7-CR019-S09-deferred-capability-register-VERIFICATION-DONE.md` PASS；主线程复验 `22 passed`，真实操作计数全 0。 |
| CR019-S10-docs-runbook-user-manual-boundary | CR-019 文档、runbook 与用户手册边界 | CR019-W5-DOCS-RUNBOOK | verified | approved | CP6 PASS / CP7 PASS | `process/checks/CP7-CR019-S10-docs-runbook-user-manual-boundary-VERIFICATION-DONE.md` PASS；主线程复验 `38 passed`，依赖 diff / 缓存 / 静态扫描均 PASS；文档不授权真实交易或 publish。 |

### CR019 Wave 进度

| Wave | 总数 | lld-approved | LLD approved | dev-ready | in-dev | ready-for-verification | verify-running | verified | blocked-by-dependency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CR019-W1-ADMISSION-BENCHMARK | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 2 | 0 |
| CR019-W2-CS-TRANSPORT | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 2 | 0 |
| CR019-W3-AUTH-ENDPOINT-GATE | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 3 | 0 |
| CR019-W4-FALLBACK-DEFERRED | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 2 | 0 |
| CR019-W5-DOCS-RUNBOOK | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 |

### CR019 当前门控

| 门控项 | 状态 | 证据 | 说明 |
|---|---|---|---|
| Story Plan | completed | `process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml`、10 张 `process/stories/CR019-S*.md` | 10 Story / 5 Wave / DAG / 文件所有权已完成。 |
| CP4 自动预检 | PASS | `process/checks/CP4-CR019-STORY-DAG-PARALLEL-SAFETY.md` | 阻断项 0、豁免项 0；可进入全量 LLD 队列。 |
| LLD | approved | `process/stories/CR019-S*-LLD.md`、`process/checks/CP5-CR019-S*-LLD-IMPLEMENTABILITY.md` | 10 份 LLD 均已 confirmed，10 个 CP5 自动预检均 PASS。 |
| CP5 人工审查 | approved | `checkpoints/CP5-CR019-STAGE6-QMT-BRIDGE-BATCH-A-LLD-BATCH.md` | 用户已 approve；进入受控 story-execution。 |
| CP8 | approved-closed | `process/checks/CP8-CR019-DELIVERY-READINESS.md`、`checkpoints/CP8-CR019-DELIVERY-READINESS.md` | CP8 自动预检 PASS，用户已同意按推荐方案实施；CR-019 当前离线合同 / 文档交付关闭。D-CP8-CR019-02 / D-CP8-CR019-05 后续按 `process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md` 独立跟踪，不授权真实运行。 |
| Real operation | not-authorized | CP3 / CP4 no-real-operation 声明 | 真实 QMT / MiniQMT / XtQuant、provider fetch、lake / broker lake 写入、publish、simulation/live 均未授权。 |

## CR-018：Production Data Lake Closure

| Story ID | 标题 | Wave | 状态 | LLD | Dev Gate | 负责人 | 阻塞 |
|---|---|---|---|---|---|---|---|
| CR018-S01 | production current truth 定义与 dataset group | CR018-W1-SCOPE-CONTRACT | verified | approved | CP6 PASS / CP7 PASS | meta-qa/qa-zhang | 无；真实抓取 / 写湖 / publish / QMT 仍 blocked |
| CR018-S02 | PIT / lifecycle / ST / suspend / trade_status / prices_limit readiness | CR018-W2-P0-P1-READINESS | verified | approved | CP6 PASS / CP7 PASS | meta-qa/qa-wei | 只允许 fixture-only readiness 合同，不授权真实抓取 / 写湖 / publish |
| CR018-S03 | 四类 benchmark 行情 / 成分 / 权重 readiness | CR018-W2-P0-P1-READINESS | verified | approved | CP6 PASS / CP7 PASS | meta-qa/qa-lv | 不得用 proxy benchmark 冒充真实 benchmark；真实操作计数为 0 |
| CR018-S04 | P1 行业 / 市值 / 风格 / 流动性 / 容量合同 | CR018-W2-P0-P1-READINESS | verified | approved | CP6 PASS / CP7 PASS | meta-qa/qa-shi | P1 不阻断 core release，但阻断中性化 / 容量 / scale_up 声明；真实操作计数为 0 |
| CR018-S05 | raw / adj_factor / qfq / hfq / returns_adjusted publish readiness | CR018-W2-P0-P1-READINESS | verified | approved | CP6 PASS / CP7 PASS | meta-qa/qa-kong | 复权 readiness 合同已验证；真实 provider fetch / lake write / publish / credential read / QMT 仍 blocked |
| CR018-S06 | production quality / readiness / rollback gate | CR018-W3-PUBLISH-ROLLBACK | verified | approved | CP6 PASS / CP7 PASS | meta-qa/qa-hua | release readiness / rollback gate 已验证；真实 provider fetch / lake write / publish / credential read / QMT 仍 blocked |
| CR018-S07 | Explicit Publish Gate 与 current reader smoke | CR018-W3-PUBLISH-ROLLBACK | verified | approved | CP6 PASS / CP7 PASS | meta-qa/qa-cao | explicit publish gate / current reader smoke 已验证；真实 current pointer publish 仍 blocked |
| CR018-S08 | published current truth 研究重跑 | CR018-W4-RERUN-QMT-ADMISSION | verified | approved | CP6 PASS / CP7 PASS | meta-qa/qa-hua the 2nd | fixture-only production rerun contract 已验证；真实长任务 / QMT 仍 blocked |
| CR018-S09 | QMT admission 后置边界 | CR018-W4-RERUN-QMT-ADMISSION | lld-approved-later-gated | approved | later-gated-by-per-run-authorization | meta-dev | S09 仍需明确 per-run QMT authorization；未授权前 simulation/live_readonly/small_live/scale_up 全 blocked |

### CR018 并行队列

| 队列 | Story | 依据 |
|---|---|---|
| lld_ready | 无 | 全部 LLD 已批准 |
| lld_running | 无 | 三个 meta-dev LLD 批次均已完成 |
| lld_review | 无 | CP5 已 approved |
| lld_batch_review | CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A | `checkpoints/CP5-CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A-LLD-BATCH.md` approved |
| dev_ready | 无 | S09 later-gated，未获 per-run QMT authorization |
| dev_running | 无 | 无 |
| verify_ready | 无 | 无 |
| verify_running | 无 | 无 |
| blocked_by_dependency | CR018-S09 | S09 需要后续 per-run QMT authorization；当前只能保持 no-op / blocked boundary |

### CR018 Story 检查点结果

| Story ID | CP5 LLD 可实现性 | CP5 人工确认 | CP6 编码完成 | CP7 验证完成 | 说明 |
|---|---|---|---|---|---|
| CR018-S01 | PASS | approved：`checkpoints/CP5-CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A-LLD-BATCH.md` | PASS：`process/checks/CP6-CR018-S01-production-current-truth-definition-and-dataset-groups-CODING-DONE.md` | PASS：`process/checks/CP7-CR018-S01-production-current-truth-definition-and-dataset-groups-VERIFICATION-DONE.md` | S01 verified；真实 provider fetch / lake write / publish / credential read / QMT 仍 blocked |
| CR018-S02 | PASS | approved：`checkpoints/CP5-CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A-LLD-BATCH.md` | PASS：`process/checks/CP6-CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill-CODING-DONE.md` | PASS：`process/checks/CP7-CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill-VERIFICATION-DONE.md` | verified；真实 provider fetch / lake write / publish / credential read / QMT 均为 0 |
| CR018-S03 | PASS | approved：`checkpoints/CP5-CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A-LLD-BATCH.md` | PASS：`process/checks/CP6-CR018-S03-real-benchmark-index-components-weights-backfill-CODING-DONE.md` | PASS：`process/checks/CP7-CR018-S03-real-benchmark-index-components-weights-backfill-VERIFICATION-DONE.md` | verified；真实 provider fetch / lake write / publish / credential read / QMT 均为 0 |
| CR018-S04 | PASS | approved：`checkpoints/CP5-CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A-LLD-BATCH.md` | PASS：`process/checks/CP6-CR018-S04-industry-market-cap-liquidity-and-exposure-data-CODING-DONE.md` | PASS：`process/checks/CP7-CR018-S04-industry-market-cap-liquidity-and-exposure-data-VERIFICATION-DONE.md` | verified；真实 provider fetch / lake write / publish / credential read / QMT 均为 0 |
| CR018-S05 | PASS | approved：`checkpoints/CP5-CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A-LLD-BATCH.md` | PASS：`process/checks/CP6-CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness-CODING-DONE.md` | PASS：`process/checks/CP7-CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness-VERIFICATION-DONE.md` | verified；真实 provider fetch / lake write / publish / credential read / QMT 均 blocked |
| CR018-S06 | PASS | approved：`checkpoints/CP5-CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A-LLD-BATCH.md` | PASS：`process/checks/CP6-CR018-S06-production-quality-readiness-audit-and-rollback-gate-CODING-DONE.md` | PASS：`process/checks/CP7-CR018-S06-production-quality-readiness-audit-and-rollback-gate-VERIFICATION-DONE.md` | verified；真实 provider fetch / lake write / publish / credential read / QMT 均 blocked |
| CR018-S07 | PASS | approved：`checkpoints/CP5-CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A-LLD-BATCH.md` | PASS：`process/checks/CP6-CR018-S07-explicit-publish-gate-and-current-reader-smoke-CODING-DONE.md` | PASS：`process/checks/CP7-CR018-S07-explicit-publish-gate-and-current-reader-smoke-VERIFICATION-DONE.md` | verified；真实 provider fetch / lake write / publish / credential read / QMT 均 blocked |
| CR018-S08 | PASS | approved：`checkpoints/CP5-CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A-LLD-BATCH.md` | PASS：`process/checks/CP6-CR018-S08-production-current-truth-research-rerun-CODING-DONE.md` | PASS：`process/checks/CP7-CR018-S08-production-current-truth-research-rerun-VERIFICATION-DONE.md` | verified；真实 provider fetch / lake write / publish / credential read / QMT 均 blocked |
| CR018-S09 | PASS | approved：`checkpoints/CP5-CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A-LLD-BATCH.md` | 未开始 | 未开始 | S09 需等待 S08 PASS 和后续授权 |

### CR018 Wave 进度

| Wave | 总数 | lld-ready | lld-review | dev-ready | in-dev | ready-for-verification | verify-running | verified | blocked |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CR018-W1-SCOPE-CONTRACT | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| CR018-W2-P0-P1-READINESS | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| CR018-W3-PUBLISH-ROLLBACK | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| CR018-W4-RERUN-QMT-ADMISSION | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|----------|------|------|------|--------|------|
| STORY-001 | 工程基线与数据契约骨架 | W0 | verified | meta-qa | 无；正式 8 维度验收 PASS，无 BLOCKING/REQUIRED 失败项 |
| STORY-002 | 数据准备节流重试与 manifest | W0 | verified | meta-qa | 无；正式验证 PASS，无 BLOCKING/REQUIRED 失败项 |
| STORY-003 | 标准化 parquet 与数据质量报告 | W0 | verified | meta-qa | 无；`BUG-STORY-003-001` 已 CLOSED / REGRESSION_PASS，正式回归 PASS |
| STORY-004 | 离线 Data Loader 与合同校验 | W1 | verified | meta-qa | 实现完成；pytest 覆盖离线 parquet、质量门禁、缺质量报告 fail fast；F-004 日志回归 PASS |
| STORY-005 | 动量信号与组合成交引擎 | W1 | verified | meta-qa | 实现完成；pytest 覆盖 T+1 买入与会计恒等式；F-004 日志回归 PASS |
| STORY-006 | 指标、单次回测报告与 metadata | W1 | verified | meta-qa | 实现完成；pytest 覆盖 2019-2025 schedule 边界、回测指标与日志回归 |
| STORY-007 | 60 组参数扫描报告 | W2 | verified | meta-qa | 实现完成；pytest 覆盖默认 60 组扫描、失败行 schema、文本字段防护与日志回归 |
| STORY-008 | 候选报告与聚宽人工验证模板 | W2 | verified | meta-qa | 实现完成；pytest 覆盖候选选择、selection_reason 与日志回归 |
| STORY-009 | PIT 股票池 Provider 增强契约 | W3 | verified | meta-qa | 实现完成；pytest 覆盖 `UNRESOLVED` registry fail fast 与日志回归；未伪造数据源 |
| STORY-010 | 交易状态与不可交易约束 | W3 | verified | meta-qa | 实现完成；pytest 覆盖 `UNRESOLVED` trade_status fail fast、portfolio 交易状态 gate 与日志回归 |
| STORY-011 | 涨跌停与事件 available_at 增强 | W3 | verified | meta-qa | 实现完成；pytest 覆盖 limit/events `UNRESOLVED` fail fast 与日志回归；保留 `STORY-010 -> STORY-011` 串行依赖 |
| STORY-012 | 偏差审计报告 | W3 | verified | meta-qa | 实现完成；pytest 覆盖对象优先审计输入、delta、缺候选 rank warning 降级与日志回归 |
| STORY-013 | 策略扩展接口与 RSI/MACD 示例 | W4 | verified | meta-qa | 实现完成；pytest 覆盖 RSI/MACD 默认参数、warm-up 后目标、非法参数失败与日志回归 |

## CR-005 Batch A 状态

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|---|---|---|---|---|---|
| CR005-S01 | Tushare connector 真实写湖边界 | CR5-W0 | verified | meta-qa | 无；CP7 PASS，lake root / `.gitignore`、默认离线、no-network、token、dry-run job spec 和禁区复核通过 |
| CR005-S02 | Tushare 多 dataset schema、PIT 字段与复权 normalization | CR5-W1 | verified | meta-qa | 无；CP7 重验 PASS，非法日期 fail fast 与 `prices.daily + prices.adj_factor` 分离 manifest join 均通过 |

## CR-005 Batch B1 / S03 LLD 状态

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|---|---|---|---|---|---|
| CR005-S03 | 多 dataset quality/catalog/readers 与 PIT/复权 gate | CR5-W2 | verified / CP7 PASS | meta-po | CP7 PASS，agent_id/thread_id=`019e363c-9916-7971-980a-699bcf023852`；meta-po 已收敛为 verified。下一步等待用户是否启动 S04，不得自动进入 S04/S05/S06 或 Backtrader |

## CR-005 Batch B2/C：S04/S05 Implementation / CP7 Queue

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|---|---|---|---|---|---|
| CR005-S04 | 沪深 300 本地基准与实验只读接入 | CR5-W3 | verified / CP7 PASS | meta-po | 无；S04 CP7 PASS，目标测试 6 passed，S04+S03 最小回归 15 passed，全量离线回归 90 passed；未联网、未真实写 lake、未进入 S06/Backtrader |
| CR005-S05 | 多源 comparison 与回补文档 | CR5-W4 | verified / CP7 PASS | meta-po | 无；S05 CP7 PASS，目标测试 5 passed，S05+S03 最小回归 14 passed，comparison CLI 回归 6 passed，全量离线回归 90 passed；未联网、未真实写 lake、未进入 S06/Backtrader |

## CR-005 Batch D：S06 LLD / Implementation Queue

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|---|---|---|---|---|---|
| CR005-S06 | Backtrader optional backend | CR5-W5 | verified / CP7 PASS | meta-po | 无阻塞；CP7=`process/checks/CP7-CR005-S06-backtrader-optional-backend-VERIFICATION-DONE.md`，meta-qa/qa-cao the 2nd agent_id/thread_id=`019e36bb-f4d5-7153-8b8d-738352fbc0b0`。专项 16 passed、全量 106 passed、真实 Backtrader Cerebro smoke 输出 `Cerebro`，forbidden import/token/network scan 无输出。 |

## CR-007 Batch A：Canonical 数据覆盖与 benchmark

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|---|---|---|---|---|---|
| CR007-S01 | 长周期 prices 回补 planner | CR007-DEV-W1 | verified | meta-qa | CP7 PASS；未授权真实 fetch/lake 写入 |
| CR007-S02 | benchmark / calendar 回补 | CR007-DEV-W2 | verified | meta-qa/qa-yan | CP7 PASS；`hs300_index` / `trade_calendar` 合同冻结 |
| CR007-S03 | 成分、权重与股票基础信息 readiness | CR007-VERIFY-W3-CR008-UNLOCK | verified | meta-qa/qa-shi the 2nd | CP7 PASS；专项 `6 passed`、相关 market_data 回归 `32 passed`；已作为 CR008-S05 解锁输入 |
| CR007-S04 | 实验真实 benchmark 消费 | CR007-VERIFY-W4 | verified | meta-qa/qa-jin the 2nd | CP7 PASS；CP7=`process/checks/CP7-CR007-S04-experiment-real-benchmark-consumption-VERIFICATION-DONE.md`，S04 定向 `7 passed`、S02/CR008 回归 `13 passed`、py_compile 通过 |
| CR007-S05 | 质量报告与文档 guardrail | CR007-VERIFY-W5 | verified | meta-qa/qa-he the 2nd | CP7 PASS；CP7=`process/checks/CP7-CR007-S05-data-quality-report-and-doc-guardrail-VERIFICATION-DONE.md`，S05 专项 `7 passed`、CR006/CR008 回归 `31 passed`、CR008 auxiliary/proxy 回归 `18 passed`、py_compile 通过 |

## CR-008 Batch A：研究级数据层口径硬化

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|---|---|---|---|---|---|
| CR008-S01 | research input 合同与报告 metadata | CR008-REVERIFY-W1 | verified | meta-po | CP7 重验 PASS；CP7=`process/checks/CP7-CR008-S01-research-input-contract-and-report-metadata-VERIFICATION-DONE.md`，测试 `22 passed`，CP7-F01/F02 已关闭 |
| CR008-S02 | proxy / real benchmark 字段隔离 | CR008-VERIFY-W2 | verified | meta-qa/qa-lv | CP7 PASS；CP7=`process/checks/CP7-CR008-S02-proxy-real-benchmark-field-separation-VERIFICATION-DONE.md`，测试 `16 passed`，无阻断项 |
| CR008-S03 | 统一 research dataset builder | CR008-VERIFY-W3 | verified | meta-qa/qa-he | CP7 PASS；CP7=`process/checks/CP7-CR008-S03-research-dataset-builder-VERIFICATION-DONE.md`，S03 定向 `9 passed`、回归 `31 passed`，无阻断项 |
| CR008-S04 | 质量、复权与 label window gate | CR008-VERIFY-W4A | verified | meta-qa/qa-kong the 2nd | CP7 PASS；CP7=`process/checks/CP7-CR008-S04-quality-adjustment-label-window-gates-VERIFICATION-DONE.md`，S04 定向 `11 passed`、S03 builder 回归 `9 passed`、py_compile 通过 |
| CR008-S05 | PIT / fixed universe 消费合同 | CR008-VERIFY-W5 | verified | meta-qa/qa-wei the 2nd | CP7 PASS；CP7=`process/checks/CP7-CR008-S05-pit-universe-consumption-contract-VERIFICATION-DONE.md`，S05 定向 `9 passed`、S03/S04 回归 `20 passed`、py_compile 通过 |
| CR008-S06 | 因子研究辅助数据合同 | CR008-VERIFY-W6 | verified | meta-qa/qa-zhang the 2nd | CP7 PASS；CP7=`process/checks/CP7-CR008-S06-factor-research-auxiliary-data-contract-VERIFICATION-DONE.md`，S06 定向 `11 passed`、S03/S04/S05 回归 `29 passed`、实验十五回归 `3 passed`、py_compile 通过 |

## CR-010：真实生产数据湖与研究真实性

### CR010-DL-BATCH-A：数据湖基础生产化

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|---|---|---|---|---|---|
| CR010-S01 | multi-dataset plan/run/publish CLI 合同 | CR010-DL-BATCH-A | verified | meta-po / direct-main-thread record | CP6/CP7 已记录 PASS；真实 Tushare resmoke 后 current truth 仍为 PARTIAL |
| CR010-S02 | prices + adj_factor 历史回补闭环 | CR010-DL-BATCH-A | verified | meta-po / direct-main-thread record | CP6/CP7 已记录 PASS；真实小窗口 `prices` readiness 为 warn_non_pit_universe |
| CR010-S03 | hs300_index + trade_calendar 回补闭环 | CR010-DL-BATCH-A | verified | meta-po / direct-main-thread record | CP6/CP7 已记录 PASS；`trade_calendar`、`hs300_index` readiness available |
| CR010-S04 | index_members / index_weights / stock_basic readiness 强化 | CR010-DL-BATCH-A | verified | meta-po / direct-main-thread record | CP6/CP7 已记录 PASS；2026-05-22 补探中 Tushare `index_member` 对 HS300 相关组合仍为 0 行，`index_members` 继续阻断；`index_weights` / `stock_basic` 不得替代 |
| CR010-S05 | catalog coverage 与 production readiness report | CR010-DL-BATCH-A | verified | meta-po / direct-main-thread record | CP6/CP7 已记录 PASS；补探后仍为 `current_truth_complete=false`、`production_strict=fail`，`exploratory=warn` |

### CR010-DL-BATCH-B：W3 数据契约与 fail-fast

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|---|---|---|---|---|---|
| CR010-S06 | PIT source/interface Spike 与 readiness 加固 | CR010-DL-BATCH-B | implemented / meta-qa CP7 PASS | main-thread + meta-qa/qa-cao | `index_members` 不由 `index_weights` / `stock_basic` 替代；验证见 `process/checks/CP7-CR010-REMAINING-BATCHES-META-QA-VERIFICATION-2026-05-22.md` |
| CR010-S07 | trade_status 合同 / reader / fail-fast | CR010-DL-BATCH-B | implemented / meta-qa CP7 PASS | main-thread + meta-qa/qa-cao | `trade_status` source/interface 或 `available_at` 缺失 fail-fast；production_strict 阻断 |
| CR010-S08 | prices_limit 合同 / gate / fail-fast | CR010-DL-BATCH-B | implemented / meta-qa CP7 PASS | main-thread + meta-qa/qa-cao | `prices_limit` source/interface 或 `available_at` 缺失 fail-fast；不声明真实可成交 |
| CR010-S09 | events 合同 / available_at gate / fail-fast | CR010-DL-BATCH-B | implemented / meta-qa CP7 PASS | main-thread + meta-qa/qa-cao | events 缺 explicit `available_at` fail-fast |

### CR010-QF-BATCH-C：实验消费与真实性报告

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|---|---|---|---|---|---|
| CR010-S10 | 统一 realism_mode 与 research metadata | CR010-QF-BATCH-C | implemented / meta-qa CP7 PASS | main-thread + meta-qa/qa-cao | `production_strict` 输出 blocked claims、readiness/PIT/W3 状态；缺口 fail |
| CR010-S11 | 16 experiments smoke 与 limitation matrix | CR010-QF-BATCH-C | implemented / meta-qa CP7 PASS | main-thread + meta-qa/qa-cao | 16 行 experiment realism matrix；experiment 11 标记 N/A |
| CR010-S12 | Backtrader / VectorBT clean feed 边界回归 | CR010-QF-BATCH-C | implemented / meta-qa CP7 PASS | main-thread + meta-qa/qa-cao | consumer boundary 静态验证无 connector/runtime/storage/provider/network/token/backfill |

### CR010-OPS-BATCH-D：备份、归档、恢复与保留策略

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|---|---|---|---|---|---|
| CR010-S13 | backup/archive/restore env 与 manifest/checksum/脱敏契约 | CR010-OPS-BATCH-D | implemented / meta-qa CP7 PASS | meta-dev/dev-xu + main-thread + meta-qa/qa-cao | dev agent `019e4f76-e461-7e20-87f4-cd6b79d713fc` 交付核心模块；报告脱敏验证 PASS |
| CR010-S14 | backup CLI dry-run / execute / verify / report | CR010-OPS-BATCH-D | implemented / meta-qa CP7 PASS / real smoke PASS | meta-dev/dev-xu + main-thread + meta-qa/qa-cao | `backup-plan/run/verify/report` 已接入 CLI；真实 release smoke：copied=4、skip=4、verify same=4、report computed=4 |
| CR010-S15 | restore CLI 与 restore drill | CR010-OPS-BATCH-D | implemented / meta-qa CP7 PASS / real smoke PASS | meta-dev/dev-xu + main-thread + meta-qa/qa-cao | `restore-root==lake-root` fail-fast；restore-drill 与 restore root read/revalidate/replay 通过，replay `network_calls=0` |
| CR010-S16 | retention policy 与 archive/backup cleanup | CR010-OPS-BATCH-D | implemented / meta-qa CP7 PASS | main-thread + meta-qa/qa-cao | retention 只读预检：published run 保护，failed/candidate run 保留；本版本不自动删除 |

### CR010 批次门控摘要

| 批次 | CP5 | CP6 | CP7 | 下一步 |
|---|---|---|---|---|
| CR010-DL-BATCH-A | approved | PASS | PASS | 已 verified；真实小窗口 resmoke PARTIAL，CR-010 不关闭 |
| CR010-DL-BATCH-B | old CP5/CP6/CP7 blocked records superseded | main-thread PASS | PASS: meta-qa/qa-cao | 代码与测试已通过；旧 handoff-only BLOCKED 记录见 `process/checks/CR010-BLOCKED-RECORDS-SUPERSEDED-2026-05-22.md` |
| CR010-QF-BATCH-C | old CP5/CP6/CP7 blocked records superseded | main-thread PASS | PASS: meta-qa/qa-cao | 代码与测试已通过；正式 QA 证据见 `process/checks/CP7-CR010-REMAINING-BATCHES-META-QA-VERIFICATION-2026-05-22.md` |
| CR010-OPS-BATCH-D | old CP5/CP6/CP7 blocked records superseded | dev-xu/main-thread PASS | PASS: meta-qa/qa-cao + real ops smoke | dev agent 交付 OPS 核心；真实 backup/restore smoke 见 `process/checks/REAL-TUSHARE-DATA-LAKE-SMOKE-CR010-INDEX-MEMBERS-OPS-2026-05-22.md` |

## CR-011：因子研究生产级数据补齐

### CR011-DATA-BATCH-A：数据与研究消费合同

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|---|---|---|---|---|---|
| CR011-S01 | 真实 benchmark 与 policy 消费 | CR011-DATA-BATCH-A | verified / CP7 PASS | meta-qa/qa-hua | CP6=`process/checks/CP6-CR011-S01-real-benchmark-and-policy-consumption-CODING-DONE.md`，CP7=`process/checks/CP7-CR011-S01-real-benchmark-and-policy-consumption-VERIFICATION-DONE.md`；S01 定向 6 passed，相关回归 74 passed |
| CR011-S02 | PIT 股票池与股票生命周期 | CR011-DATA-BATCH-A | verified / CP7 PASS | meta-qa/qa-shi | CP6 replacement 接管复核 PASS；CP7=`process/checks/CP7-CR011-S02-pit-universe-and-stock-lifecycle-completion-VERIFICATION-DONE.md`，S02 定向 `7 passed`、相关回归 `35 passed` |
| CR011-S03 | 可交易性与涨跌停门控 | CR011-DATA-BATCH-A | verified / CP7 PASS | meta-qa/qa-wei | CP7=`process/checks/CP7-CR011-S03-tradability-status-and-price-limit-gates-VERIFICATION-DONE.md`；S03 定向 `8 passed`、相关回归 `33 passed`、安全扫描 PASS |
| CR011-S04 | OHLCV / VWAP 干净执行 feed | CR011-DATA-BATCH-A | verified / CP7 reverify PASS | meta-qa/qa-hua the 2nd | 首次 CP7 FAIL 的 `CR011-S04-CP7-F01` 已由 blocker-fix CP6=`process/checks/CP6-CR011-S04-CP7-BLOCKER-FIX-CODING-DONE.md` 修复并由 CP7 复验=`process/checks/CP7-CR011-S04-ohlcv-vwap-clean-execution-feed-REVERIFY-DONE.md` PASS；agent_id/thread_id=`019e585a-12bf-7721-affc-a0927f18c5c6` |
| CR011-S05 | 复权与公司行动审计 | CR011-DATA-BATCH-A | verified / CP7 PASS | meta-qa/qa-he the 2nd | CP7=`process/checks/CP7-CR011-S05-adjustment-and-corporate-action-audit-VERIFICATION-DONE.md`；S05 定向 `7 passed`、S04/S01/CR008 回归 `57 passed`、available_at probe PASS、安全扫描 PASS |
| CR011-S06 | 行业 / 市值 / 风格暴露 | CR011-DATA-BATCH-A | verified / CP7 reverify PASS | meta-qa/qa-jin the 2nd | CP7 首验=`process/checks/CP7-CR011-S06-industry-market-cap-style-exposure-data-VERIFICATION-DONE.md` FAIL，阻断项 `CR011-S06-CP7-F01` 已由 CP6 blocker-fix=`process/checks/CP6-CR011-S06-CP7-BLOCKER-FIX-CODING-DONE.md` 修复，并由 CP7 复验=`process/checks/CP7-CR011-S06-industry-market-cap-style-exposure-data-REVERIFY-DONE.md` PASS；agent_id/thread_id=`019e58c2-6271-7131-adf0-5e026d7680af` |
| CR011-S07 | 流动性 / 容量 / 成本敏感性 | CR011-RESEARCH-BATCH-B | verified / CP7 PASS | meta-qa/qa-yan the 2nd | CP7=`process/checks/CP7-CR011-S07-liquidity-capacity-and-cost-sensitivity-VERIFICATION-DONE.md` PASS；S07 定向 `7 passed`、S03/S04/S06 回归 `40 passed`、benchmark/实验回归 `8 passed`，安全扫描 PASS；agent_id/thread_id=`019e58f5-c3ae-7930-8113-30f28ad4388e` |
| CR011-S08 | 因子审计面板与稳健性验证 | CR011-VALIDATION-BATCH-C | verified / CP7 PASS | meta-qa/qa-lv the 2nd | CP7=`process/checks/CP7-CR011-S08-factor-panel-audit-and-robust-validation-VERIFICATION-DONE.md` PASS；S08 定向 `3 passed`、S01/S02/S05/S07/实验回归 `29 passed`、fail-closed probe PASS；agent_id/thread_id=`019e5931-551d-7a41-bdf9-cbf98b0829fb` |

### CR011 批次门控摘要

| 批次 | CP5 自动预检 | CP5 人工确认 | 实现授权 | 下一步 |
|---|---|---|---|---|
| CR011-DATA-BATCH-A | PASS：S01..S06 六份 Story 级预检全通过 | approved：`checkpoints/CP5-CR011-DATA-BATCH-A-LLD-BATCH.md` | true for S01..S06，仍受 Story DAG / file ownership 串行调度 | S01/S02/S03/S04/S05/S06 verified；DATA-BATCH-A 已完成 |
| CR011-RESEARCH-BATCH-B | PASS：S07 Story 级预检通过 | approved：`checkpoints/CP5-CR011-RESEARCH-BATCH-B-LLD-BATCH.md` | true for S07 offline implementation | S07 CP6 PASS、CP7 PASS，RESEARCH-BATCH-B 已 verified |
| CR011-VALIDATION-BATCH-C | PASS：S08 Story 级预检通过 | approved：`checkpoints/CP5-CR011-VALIDATION-BATCH-C-LLD-BATCH.md` | true for S08 offline implementation | S08 CP6 PASS、CP7 PASS；VALIDATION-BATCH-C 已 verified；CR-011 文档刷新已完成；CP8 自动预检 PASS；用户已 approve CP8，CR-011 已关闭 |

## CR-014：全 A since-inception 生产数据湖 Story Plan

### CR014-FULL-HISTORY-LAKE-BATCH-A：执行态

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|---|---|---|---|---|---|
| CR014-S01-a-share-universe-lifecycle-contract | 全 A universe / lifecycle / code-change 合同 | CR014-W1-CONTRACTS | verified | meta-qa/qa-he | CP6 PASS；CP7 PASS；agent_id=`019e66a7-b1a5-7d21-8463-8a8c73422a06`；真实操作计数均为 0 |
| CR014-S02-parquet-layout-manifest-catalog-publish-gate | Parquet layout / manifest / catalog current pointer / publish gate | CR014-W1-CONTRACTS | verified | meta-qa/qa-lv | CP6 PASS；CP7 PASS；dev_agent_id=`019e66a7-f383-7b01-89e0-ca2951dd659c`；qa_agent_id=`019e66b4-4415-7b60-9dbd-ee706cd16828`；真实操作计数均为 0 |
| CR014-S03-p0-plan-run-normalize-validate-publish-contract | P0 dataset plan/run/normalize/validate/publish 合同 | CR014-W2-PIPELINE | verified | meta-qa/qa-hua | CP6 PASS；CP7 PASS；dev_agent_id=`019e66ba-bf09-7c31-98e9-86a4fdab70ec`；qa_agent_id=`019e66cb-6bd3-7bc3-96b8-88fd50ce59eb`；真实抓取与 raw/manifest 写湖仍拆到 S09；真实操作计数均为 0 |
| CR014-S04-duckdb-readonly-query-audit-parity-boundary | DuckDB read-only query/audit/parity 边界 | CR014-W2-PIPELINE | verified | meta-qa/qa-jin | CP6 PASS；CP7 PASS；dev_agent_id=`019e66cb-e892-7d11-8f59-753d62b13f4f`；qa_agent_id=`019e66d8-59ef-7a53-bf8e-caf959456b1f`；本批不引入 DuckDB 依赖、不写 `.duckdb`；真实操作计数均为 0 |
| CR014-S05-full-history-readiness-gap-claim-boundary | full-history readiness audit / gap register / claim boundary | CR014-W3-AUDIT-OPS | verified | meta-qa/qa-shi | CP6 PASS；CP7 PASS；dev_agent_id=`019e66e0-4083-7f61-92bd-20868a50cfb4`；qa_agent_id=`019e66f1-c806-79f1-8710-1df27ca34c50`；任一 P0 gate 未过时 full-A allowed claim=0；不读/覆盖旧 reports；真实操作计数均为 0 |
| CR014-S06-incremental-refresh-replay-retention-contract | incremental refresh / replay / retention 合同 | CR014-W3-AUDIT-OPS | verified | meta-qa/qa-zhang | CP6 PASS；CP7 PASS；dev_agent_id=`019e66d8-99d0-7823-9a85-5d850d07e8e7`；qa_agent_id=`019e66e7-ad3b-7882-92f8-bb2aaa4fc054`；replay 不触发 provider、不读凭据、不写 raw、不改 current pointer；retention 仅 dry-run |
| CR014-S07-research-consumer-readonly-docs-runbook-boundary | research consumer read-only contract 与 docs/runbook 后续边界 | CR014-W4-CONSUMER-BOUNDARY | verified | meta-qa/qa-cao | CP6 PASS；CP7 PASS；dev_agent_id=`019e671e-01d5-7472-97f0-9457e2c6bc2b`；qa_agent_id=`019e672d-81dd-7683-a31e-4aed391942b3`；研究消费层不得直接 DuckDB 写入/发布/扫未发布 lake；真实操作计数均为 0 |
| CR014-S08-w3-minute-tick-level2-vwap-blocked-decision-boundary | W3 / minute / tick / Level2 / VWAP blocked 决策边界 | CR014-W4-CONSUMER-BOUNDARY | verified | meta-qa/qa-wei | CP6 PASS；CP7 PASS；dev_agent_id=`019e66fc-3fbd-7c61-9b5e-9fedcf5fbbd0`；qa_agent_id=`019e6710-77a0-7441-b5d0-e9a05356be38`；W3/minute/tick/Level2/VWAP production allowed claim=0；真实操作计数均为 0 |
| CR014-S09-windowed-real-fetch-lake-write-run | 分时段真实抓取与 raw/manifest 写湖执行 | CR014-W5-REAL-RUN | full-history-2015-2026-ytd-prices-adj-factor-candidate-usable-non-pit-warn | meta-po | 真实 Tushare YTD smoke PASS；S10-S13 已关闭 2026 candidate 可用性；S14 已完成 2015-01-05..2026-05-28 全 A `prices`/`adj_factor` raw、manifest、canonical candidate，2768 个开市日、5536 条成功 manifest、`prices` 11311360 行、`adj_factor` 11823057 行，所有已观测 `prices` 交易对均有 `adj_factor`；仍因 PIT/W3 数据缺口不可自动 publish |

### CR014 门控摘要

| 项 | 状态 | 说明 |
|---|---|---|
| CP3 R2 | APPROVED | 用户已批准 D1-D12 推荐决策，采用 CR14-A |
| CP4 自动预检 | PASS | `process/checks/CP4-CR014-STORY-DAG-PARALLEL-SAFETY.md` 已生成，结论 PASS |
| LLD | APPROVED | 8 张 LLD 与 8 个 CP5 自动预检均已完成；用户已按推荐全部允许 |
| 实现授权 | true-for-batch-a-controlled-code | S01..S08 可按 Story DAG、文件所有权、CP6/CP7 进入受控离线实现 |
| 真实操作计数 | 0 | provider_fetch=0、lake_write=0、credential_read=0、duckdb_dependency_change=0 |
| Publish Gate | NOT_AUTHORIZED | Validate/parity PASS 不自动 publish；只有 Explicit Publish Gate 可更新 catalog current pointer |
| 真实抓取/写湖 | SPLIT_TO_BATCH_B | 已拆分为 `CR014-S09-windowed-real-fetch-lake-write-run`；需 S01..S08 verified 后独立 LLD / CP5 / authorization_id 才能分时段执行 |
| CP8 自动预检 | PASS | `process/checks/CP8-CR014-DELIVERY-READINESS.md` 已生成，结论 PASS |
| CP8 人工终验 | APPROVED | 用户已回复同意；`checkpoints/CP8-CR014-DELIVERY-READINESS.md` 已回填 approved；不包含 S09 真实执行授权 |

## CR-015 / CR-016 / CR-017：QMT 交易基础、模拟到实盘激活与复权双视图 Story Plan

### CR015-CR016-CR017 执行态汇总

| Story ID | 标题 | Wave | 状态 | 负责人 | 阻塞 |
|---|---|---|---|---|---|
| CR017-S01 | 复权策略需求与 ADR 回写边界 | CR017-W1-ADJUSTMENT-CONTRACTS | verified | meta-qa/qa-kong | CP7 PASS，真实操作计数为 0 |
| CR017-S02 | raw prices 与 adj_factor 合同硬化 | CR017-W1-ADJUSTMENT-CONTRACTS | verified | meta-qa/qa-kong | CP7 PASS，真实操作计数为 0 |
| CR017-S03 | qfq / hfq derived view normalization | CR017-W2-DERIVATION-READERS | verified | meta-qa/qa-wei | CP7 PASS，provider_fetch / lake_write / credential_read / publish / dependency_change / legacy_qfq_overwrite 均为 0 |
| CR017-S04 | reader API 与复权 policy gate | CR017-W2-DERIVATION-READERS | verified | meta-qa/qa-hua | CP7 PASS；DEV-LOG 额外写入已判定为非阻断过程偏差 |
| CR017-S05 | 质量、奇异价格与泄漏验证 | CR017-W3-CONSUMER-MIGRATION | verified | meta-qa/qa-yan | CP7 PASS，fixture-only，真实数据 / 凭据 / 写湖 / publish 计数均为 0 |
| CR017-S06 | research / QMT consumer 文档与迁移指南 | CR017-W3-CONSUMER-MIGRATION | verified | meta-qa/qa-hua the 2nd | CP7 PASS；consumer matrix、QMT raw-only、blocked claims、legacy qfq 保留、unsupported execution 边界与 CR017 回归均通过；真实操作计数为 0 |
| CR015-S01 | QMT 环境与接口边界 spike | CR015-W1-FOUNDATION-CONTRACTS | verified | meta-qa/qa-shi | CP7 PASS，真实 QMT / 发单 / 账户 / 凭据 / 写湖计数均为 0 |
| CR015-S02 | QMT broker adapter contract | CR015-W1-FOUNDATION-CONTRACTS | verified | meta-qa/qa-zhang | CP7 PASS，真实 QMT / 发单 / 撤单 / 账户 / 凭据 / 写湖计数均为 0 |
| CR015-S03 | OMS 订单状态机 | CR015-W2-OMS-RISK-LAKE | verified | meta-qa/qa-lv | CP7 PASS，unknown / timeout / cancel_failed 均不进入成功终态；真实 QMT / 发单 / 撤单 / 账户 / 凭据 / 写湖计数均为 0 |
| CR015-S04 | Pre-trade risk gate | CR015-W2-OMS-RISK-LAKE | verified | meta-qa/qa-yan the 2nd | CP7 PASS；九类 hard risk gate、非 raw/qfq/hfq execution blocked、S03 OMS 回归均通过；风险 hard block 时 adapter_calls=0 |
| CR015-S05 | broker lake schema 与脱敏 writer | CR015-W2-OMS-RISK-LAKE | verified | meta-qa/qa-kong the 2nd | CP7 PASS；broker lake schema / redaction / dry-run writer、S03/S04 回归和安全计数均通过；真实 broker lake 写入仍未授权 |
| CR015-S06 | target portfolio 到 order intent shadow mode | CR015-W3-SHADOW-RUNBOOK | verified | meta-qa/qa-lv the 2nd | CP7 PASS；S03/S04/S05/S06 回归 38 passed；真实操作计数均为 0，simulation/live 激活仍未授权 |
| CR015-S07 | foundation runbook 与职责边界 | CR015-W3-SHADOW-RUNBOOK | verified | meta-qa/qa-zhang the 2nd | CP7 PASS；文档边界测试 6 passed；不构成 simulation / live 授权 |
| CR016-S01 | simulation order enable gate | CR016-W1-SIMULATION-OPS-GATES | verified | meta-qa/qa-jin the 2nd | CP7 PASS；stage gate / adapter 回归 24 passed；真实 simulation run 仍需逐 run 授权 |
| CR016-S02 | 对账服务与报告 | CR016-W1-SIMULATION-OPS-GATES | verified | meta-qa/qa-cao the 2nd | CP7 PASS，指定回归 38 passed，静态扫描 violations=0，16 项真实操作计数均为 0 |
| CR016-S03 | 监控、心跳与 kill switch | CR016-W1-SIMULATION-OPS-GATES | verified | meta-qa/qa-wei the 2nd | CP7 PASS，指定回归 54 passed，静态扫描 violations=0，18 项真实操作计数均为 0 |
| CR016-S04 | simulation / live runbook 与审批门控 | CR016-W1-SIMULATION-OPS-GATES | verified | meta-qa/qa-shi the 2nd | CP7 PASS，指定回归 41 passed；QA 完成证据已回填，`close_agent` 返回 not found 因此不伪造 `closed_at`；不授权 small_live / scale_up 或任何真实 broker 操作 |
| CR016-S05 | live_readonly 与 small_live admission | CR016-W2-LIVE-SCALE-DOCS-GATED | lld-approved-later-gated | meta-dev | later-gated；small_live 需后续独立审批，当前 implementation_allowed=false |
| CR016-S06 | scale_up 与研究成熟度门控 | CR016-W2-LIVE-SCALE-DOCS-GATED | lld-approved-later-gated | meta-dev | later-gated；CR017 verified 与后续独立审批前持续阻断，当前 implementation_allowed=false |
| CR016-S07 | 用户手册与 incident playbooks | CR016-W2-LIVE-SCALE-DOCS-GATED | verified | meta-qa/qa-he the 2nd | CP7 PASS，指定回归 29 passed；S05/S06 作为 approved later-gated 合同输入，不进入实现；S07 只写文档和静态测试，不触发真实操作 |

### CR015-CR016-CR017 门控摘要

| 项 | 状态 | 说明 |
|---|---|---|
| CP3 HLD / ADR | APPROVED | 用户已批准 CR015/CR016/CR017 推荐方案与 Q-030..Q-038 决策 |
| CP4 自动预检 | PASS | `process/checks/CP4-CR015-CR016-CR017-STORY-DAG-PARALLEL-SAFETY.md` 已生成，结论 PASS |
| Story 总数 | 20 | CR017 6 个、CR015 7 个、CR016 7 个 |
| Wave 总数 | 8 | CR017 3 个、CR015 3 个、CR016 2 个 |
| LLD 批次建议 | 3 | `CR017-ADJUSTMENT-DUAL-VIEW-BATCH-A`、`CR015-QMT-FOUNDATION-BATCH-A`、`CR016-QMT-ACTIVATION-BATCH-A` |
| 受控离线实现授权 | true-for-approved-stories | CP5 已 approved；非 later-gated Story 可按 Story DAG、文件所有权和 CP6/CP7 门控实现；CR016-S05/S06 仍 later-gated |
| 真实操作授权 | false | 真实 QMT / broker、真实发单 / 撤单 / 账户查询、凭据读取、真实抓取、真实写湖、发布指针更新均未授权 |

### LLD 设计批次建议

| 批次 | 范围 | 可并行分组 | 说明 |
|---|---|---|---|
| CR017-ADJUSTMENT-DUAL-VIEW-BATCH-A | CR017-S01..S06 | S01/S02 可先行；S03/S04 依赖 S02；S05/S06 依赖 S03/S04 | 先冻结价格与复权双视图口径，为 QMT raw 价格隔离提供上游 contract |
| CR015-QMT-FOUNDATION-BATCH-A | CR015-S01..S07 | S01 可与 CR017-S01/S02 并行；S02 后串行进入 S03/S04/S05；S06/S07 收敛 | 只覆盖 shadow / dry-run / mock foundation，不授权真实交易节点操作 |
| CR016-QMT-ACTIVATION-BATCH-A | CR016-S01..S07 | S01/S02 在 CR015 foundation 之后并行；S03/S04 收敛；S05/S06 later-gated；S07 文档收尾 | simulation / live_readonly / small_live / scale_up 均受后续 CP5 和阶段门控约束 |

## Wave 进度

| Wave | 总数 | package-draft | ready-for-lld-review | package-ready-for-review | package-approved | in-development | ready-for-verification | verified | blocked |
|------|------|---------------|----------------------|--------------------------|------------------|----------------|------------------------|----------|---------|
| W0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 |
| W1 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 |
| W2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| W3 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| W4 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| CR014-W1-CONTRACTS | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| CR014-W2-PIPELINE | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| CR014-W3-AUDIT-OPS | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| CR014-W4-CONSUMER-BOUNDARY | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| CR014-W5-REAL-RUN | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| CR017-W1-ADJUSTMENT-CONTRACTS | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| CR017-W2-DERIVATION-READERS | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| CR017-W3-CONSUMER-MIGRATION | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| CR015-W1-FOUNDATION-CONTRACTS | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| CR015-W2-OMS-RISK-LAKE | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 |
| CR015-W3-SHADOW-RUNBOOK | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| CR016-W1-SIMULATION-OPS-GATES | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| CR016-W2-LIVE-SCALE-DOCS-GATED | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2 |

## 当前门控

### CR015 / CR016 / CR017 当前门控

| 对象 | 状态 | 证据 | 下一步 |
|---|---|---|---|
| Story Plan | completed | `process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml`、20 张 `process/stories/CR015/CR016/CR017-S*.md` | 已进入 CP8 delivery readiness |
| CP4 自动预检 | PASS | `process/checks/CP4-CR015-CR016-CR017-STORY-DAG-PARALLEL-SAFETY.md` | 不替代 CP5 人工确认 |
| LLD | approved | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | 20 份 LLD 均已 confirmed=true；S05/S06 later-gated 仅保留设计合同 |
| Implementation | controlled-scope-verified | CR017-S01..S06、CR015-S01..S07、CR016-S01..S04 与 S07 均 CP6/CP7 PASS | 只完成离线 / mock / fixture / 文档 / dry-run / shadow 范围；真实操作计数为 0 |
| Later-gated scope | blocked-before-new-approval | CR016-S05 / CR016-S06 | small_live / scale_up 需后续独立决策与授权；当前 implementation_allowed=false |
| CP8 终验 | approved-closed | `process/checks/CP8-CR015-CR016-CR017-DELIVERY-READINESS.md`、`checkpoints/CP8-CR015-CR016-CR017-DELIVERY-READINESS.md` | 用户于 2026-06-05 接受推荐方案；CR015 / CR016 / CR017 当前受控离线交付批次关闭，不授权真实运行 |

## CR-004 Batch D 当前状态

| 对象 | 状态 | 证据 | 下一步 |
|---|---|---|---|
| STORY-003 legacy quality addendum | CP5 approved / no code change required in G1 | `process/stories/STORY-003-parquet-quality-report-LLD.md`; `checkpoints/CP5-CR004-BATCH-D-DATALOADER-EXPERIMENT-READONLY-LLD-REVIEW.md` | 已由 STORY-004 Data Loader quality CSV 消费门禁覆盖；不重开真实抓取或真实报告生成。 |
| STORY-004 Data Loader first / no real fetch | verified / CP7 PASS | `process/checks/CP6-STORY-004-cr004-batch-d-dataloader-CODING-DONE.md`; `process/checks/CP7-STORY-004-cr004-batch-d-dataloader-VERIFICATION-DONE.md` | G1 完成；默认 warn 阻断、fail 不放行、manifest fail fast、Markdown human-only、metadata 决策字段与 non-PIT 警示已验证。 |
| STORY-018 实验十/十二只读接入 | verified / CP7 PASS | `process/checks/CP6-STORY-018-cr004-experiment-readonly-benchmark-CODING-DONE.md`; `process/checks/CP7-STORY-018-cr004-experiment-readonly-benchmark-VERIFICATION-DONE.md` | G1 完成；只读 benchmark resolver、显式本地 fixture、structured unavailable / required_missing 与 CR007 兼容已验证。 |
| CR-004 Batch D / G1 聚合验证 | PASS | `process/checks/CP7-CR004-BATCH-D-VERIFICATION-SUMMARY-2026-05-30.md` | 聚合回归 `48 passed`；继续保持真实 provider fetch / lake write / publish / credential read / QMT operation blocked。 |

本批次已收敛 CR-004 Batch D / G1 缺口；用户于 2026-06-05 确认 CR004 相关问题应已解决并接受总关闭方案，CR-004 总 CR 已关闭。关闭不代表真实沪深 300 全面 available、production current truth 已补齐或任何真实数据 / QMT 操作已获授权。

`STORY-001` 已完成实现范围收敛并通过 meta-qa 正式 8 维度验收，`process/VERIFICATION-REPORT.md` 结论为 PASS，无 BLOCKING 或 REQUIRED 失败项。meta-po 已将 `STORY-001` 收敛为 `verified`。

meta-po 静态复核的 STORY-001 实现源文件范围为：`pyproject.toml`、`uv.lock`、`config/data_prep.yaml`、`engine/__init__.py`、`engine/contracts.py`、`strategies/__init__.py`、`data/.gitkeep`、`reports/.gitkeep`。验证报告确认未发现 `STORY-002+` 源文件、data fetcher、manifest writer、quality report 逻辑、回测引擎逻辑、策略逻辑或 `delivery/**` 产物。导入验证产生的缓存和虚拟环境残留已清理，不作为 STORY-001 源实现范围。

`STORY-002` 依赖的 `STORY-001` 已满足。meta-dev 已创建 `process/stories/STORY-002-data-prep-throttle-manifest-LLD.md`，用户已明确回复 `确认通过`，meta-po 已将 LLD 确认为通过。meta-dev 报告 STORY-002 实现完成，且声明只修改 `engine/manifest.py`、`engine/akshare_adapter.py`、`engine/data_prep.py`、`engine/contracts.py`；未实现 STORY-003；未创建 normalizer/parquet/quality report；未写真实 `data/raw/**` 或 `data/manifests/**`；未调用真实 AKShare；未写 delivery；验证使用 fake adapter 和临时目录。meta-qa 正式验证结论 PASS，无 BLOCKING 或 REQUIRED 失败项；meta-po 已将 STORY-002 收敛为 `verified`。

`STORY-003` 依赖 `STORY-001` 与 `STORY-002`，当前均已 verified。W0 为串行 Wave，meta-dev 已完成 STORY-003 LLD、实现与限定范围 bugfix。meta-qa 已完成 `BUG-STORY-003-001` 回归验证，`process/VERIFICATION-REPORT.md` 中回归结论为 PASS，Bug 状态建议为 `CLOSED / REGRESSION_PASS`。meta-po 已关闭该 Bug，并将 STORY-003 从 `ready-for-verification` 收敛为 `verified`。

W0 包含 `STORY-001`、`STORY-002`、`STORY-003`，三者均已 verified，因此 W0 完成。用户已于 2026-05-15 明确确认通过 `STORY-004` 至 `STORY-013` 批量 LLD / Story Package，meta-po 已回写检查点与 LLD frontmatter，并进入 `story-execution`。本轮实现按主链 `STORY-004 -> STORY-005 -> STORY-006 -> STORY-007 -> STORY-008 -> STORY-009 -> STORY-010 -> STORY-011 -> STORY-012` 维持依赖串行；`STORY-013` 在 `STORY-008` 后文件所有权无冲突，随 W3 起点并行排队条件满足后实现。当前 `STORY-004` 至 `STORY-013` 均已完成实现并通过针对性 pytest。W3 硬门禁保持：`STORY-009/010/011` 的 `source/interface=UNRESOLVED` 未替换 exact 值前，相关 data_prep、normalizer、quality、loader 启用路径必须 fail fast；本轮只落地 fail-fast 防线，未伪造数据源。

## 非阻断观察项

| ID | 状态 | 归属 | 说明 | 后续处理 |
|---|---|---|---|---|
| OBS-STORY-003-GUARDRAIL-SCRIPT-MISSING | PROCESS_DEBT_OPEN | 仓库级流程债 | `scripts/check_delivery_guardrails.py` 与 `scripts/` 目录不存在，无法执行项目规则中的提交前 guardrail 命令。 | 不阻断 STORY-003 或 W0；不得在本轮越界创建脚本。后续可由独立流程治理 Story 或 QA 流程债处理。 |
| OBS-STORY-003-VALIDATION-ENV-STORY-ID | QA_OBSERVATION_OPEN | 后续 QA 观察项 | `process/VALIDATION-ENV.yaml` 的 `story_id` 仍为 `STORY-001`，但 `approval.confirmed=true`，且当前状态与 handoff 已指向 STORY-003/W1。 | 不阻断 STORY-003 或 W0；后续进入 STORY-004 验证前由 meta-po/meta-qa 决定是否刷新验证环境元数据，避免审计歧义。 |

## 阻塞项清单

- CR015/CR016/CR017 CP5 前阻断项已登记：20 个 Story 尚未生成全量 LLD，且 CP5 自动预检与人工确认未发生；不得进入实现。
- CR017 verified 前阻断 scale_up：复权双视图、读 API、质量与泄漏验证未完成前，CR016-S06 保持 later-gated。
- CR015 foundation verified 前阻断 CR016 activation：simulation / live_readonly / small_live / scale_up 均依赖 CR015-S06/S07 和 CR017-S05 之后的明确门控。
- 真实外部操作未授权：本阶段不允许真实外部接口调用、真实写入、发布指针更新或交易相关写操作。
- 文件所有权冲突需在 LLD 收敛：CR017 数据层共享文件、CR015 trading 目录与 CR016 ops/runbook 文件必须按 `DEVELOPMENT-PLAN.yaml` 的 merge_owner 串行或分批合并。
- 当前 CR-005 Batch A Story 执行 BLOCKING 阻塞项已关闭：`CR005-S02` CP7 重验 PASS，非法日历日期校验与 `prices.daily + prices.adj_factor` 分离输入 join 均已验证；`STORY-001` 至 `STORY-013` 历史基线仍均为 verified。不得据此自动进入 `CR005-S03/S04/S05/S06` 或 Backtrader。
- CR005-S03、CR005-S04、CR005-S05、CR005-S06 均已 CP7 PASS 并由 meta-po 收敛为 verified。S06 专项测试 `16 passed`，全量离线回归 `106 passed`，真实 Backtrader Cerebro smoke 输出 `Cerebro`；未联网、未真实写 lake、未读取 token、未导入 connector/runtime/storage。
- Documentation 阶段交付出口 BLOCKING 门控已关闭：用户已确认正式用户文档输出路径为仓库根 `README.md` + `docs/USER-MANUAL.md`。文档已输出并通过后置 QA；仍不得写 `delivery/**`、安装脚本、代码、测试或真实数据。
- 目录结构收敛门控已完成：meta-dev 执行前 `find work -type f -print` 与 `find delivery -type f -print` 均无输出，仅发现空目录；已用 `rmdir` 删除 `work/studies/quant-trading/local_backtest/`、清理后变空的 `work/` 父目录链、`delivery/` 下空子目录及 `delivery/` 本身；清理后 `work/` 与 `delivery/` 均不存在。meta-doc 已刷新 README / USER-MANUAL 的目录边界说明；meta-po 已复核文件系统与文档覆盖，无 BLOCKING；用户已于 2026-05-16 通过 CP8 人工终验。
- 人工确认门控：`checkpoints/STORY-004-LLD-CHECKPOINT.md` 已被批量 LLD 包门控取代；当前活动检查点为 `checkpoints/STORY-PACKAGE-LLD-CHECKPOINT.md`。
- LLD 输出门控：`process/handoffs/META-DEV-LLD-BATCH-REMAINING-2026-05-15.md` 已完成 9 个剩余 LLD 草案输出；meta-po 已完成批量 LLD / Story Package 聚合。
- 实现推进已完成：`STORY-004` 至 `STORY-013` 均已 verified。2026-05-16 Galileo 独立 meta-qa 对 `QA-IND-REQ-001 / F-004` 执行最小回归，`uv run --python 3.11 pytest -q tests/test_story_004_013.py::test_t_logging_minimal_01_cli_diagnostics` 结果 `1 passed`，`uv run --python 3.11 pytest -q` 结果 `10 passed`，`compileall` 通过；日志 REQUIRED 缺口已关闭。
- 文档阶段已收敛：`README.md` 与 `docs/USER-MANUAL.md` 已由 meta-doc 输出，meta-qa 后置文档复核 PASS，无 BLOCKING/REQUIRED 失败项；`process/TEST-STRATEGY.md`、`process/VERIFICATION-REPORT.md`、`process/DEVELOPMENT-PLAN.yaml` 与本文件已对齐 PASS / `CLOSED / REGRESSION_PASS` / delivered，历史 FAIL 记录仅作为可审计上下文保留。
- 全局限制执行结果：未写 `delivery/**`，未生成真实生产数据，未生成安装脚本；测试使用临时目录、fixture 或 fake runner。
- 下一状态：已交付 delivered；W3 真实数据源 `UNRESOLVED` 仍作为后续真实数据启用前风险处理。

## Documentation Readiness 路由

| 项 | 状态 | 说明 |
|---|---|---|
| QA documentation readiness | PASS | `process/handoffs/META-QA-DOCUMENTATION-READINESS-2026-05-16.md` 已支持进入 documentation；当前已收敛到 CP8 |
| 批量 LLD / Story Package 前置门控 | PASS | `checkpoints/STORY-PACKAGE-LLD-CHECKPOINT.md` 已确认通过，不阻塞 documentation |
| README / USER-MANUAL | PASS | 已由 meta-doc 输出到 `README.md` 与 `docs/USER-MANUAL.md`；本轮不修改正文 |
| 交付出口 | PASS | 用户已确认选项 2：仓库根 `README.md` + `docs/USER-MANUAL.md`，作为当前本地回测项目正式用户文档 |
| 后置 QA 文档复核 | PASS | `process/VERIFICATION-REPORT.md` 最新“文档后置 QA 复核报告：README / USER-MANUAL”结论 PASS，无 BLOCKING/REQUIRED；建议进入最终交付 / CP8 |
| CP8 交付就绪 | APPROVED / DELIVERED | meta-po 已刷新 CP8 自动预检与人工终验稿；用户已于 2026-05-16 回复 `通过`；CP8 已记录 `git status --short` 与允许范围，并继续跟踪 W3 真实数据源启用、`VALIDATION-ENV.yaml` 历史元数据滞后等非阻断项 |
| CR-001 目录结构收敛 | CLOSED / ACCEPTED / COMPLETED | meta-dev 已完成空目录核验与 `rmdir` 清理；meta-doc 已刷新 README / USER-MANUAL；meta-po 已复核 `work/` 与 `delivery/` 不存在、文档覆盖目录边界；无非空目录保留、无 BLOCKING；用户 CP8 终验已通过 |
