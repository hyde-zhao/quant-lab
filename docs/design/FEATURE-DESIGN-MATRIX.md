---
status: "draft-current-index"
version: "1.3"
source_blueprint: "docs/design/BLUEPRINT.md"
source_hld: "docs/design/HLD.md"
source_adr: "docs/design/ARCHITECTURE-DECISION.md"
change: "CR-053"
confirmed_by: ""
confirmed_at: ""
---

# Feature Design Matrix

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-07 | meta-po | 新增 Feature 设计适用性矩阵，覆盖八个主要 Feature / Epic |
| 1.1 | 2026-06-13 | meta-po | 按 CR-046 增补 FEAT-09 双目标策略交付框架，实现设计三件套和 7 个 Story 的 lld_policy |
| 1.2 | 2026-06-14 | host-orchestrator | 按 CR-051 增补 FEAT-10 策略研究生命周期与 quant-lab 迁移治理，实现设计三件套和 6 个 Story 的 lld_policy |
| 1.3 | 2026-06-14 | host-orchestrator | 按 CR-053 增补 FEAT-10-CR053 quant-lab migration inventory / dry-run scoped design、5 个 Story 和 CP5 批次 |

## 适用性判定规则

| 维度 | 需要 Feature 设计的触发条件 | 可豁免条件 |
|---|---|---|
| 数据与状态 | 新增 / 修改核心对象、状态机、迁移、兼容策略 | 只读展示或无状态配置 |
| 接口与依赖 | 跨模块、外部接口、共享契约、依赖方向需要冻结 | 单文件局部改动且无新接口 |
| 权限与安全 | 权限边界、敏感信息、审计、运行授权 | 无权限变化且无敏感数据 |
| 运行与可靠性 | 并发、幂等、重试、性能、降级、回滚 | 无运行时风险扩展 |
| 多 Story 复用 | 多个 Story 共享同一能力边界或任务清单 | 单 Story 可直接用技术说明覆盖 |

## Feature 设计矩阵

| Feature ID | Feature / Epic | 来源 | 适用性 | 判定理由 | 需要产物 | 关联 Story | 建议 lld_policy | 重访条件 |
|---|---|---|---|---|---|---|---|---|
| FEAT-01 | 本地研究与轻量回测核心 | BLUEPRINT、HLD、STORY-001..013 | waived | 基线已 verified，当前不重写已验证 Story；后续新增高风险改造再进入 required | none / legacy evidence | STORY-001..013、CR008、CR011 | waived for baseline；新增跨模块改造用 full-lld | 修改 data loader、backtest engine、portfolio 或 report schema 时 |
| FEAT-02 | 生产级市场数据湖 | BLUEPRINT、HLD-DATA-LAKE、ADR-013..022/030..035/048..054/062..066 | required | 拥有事实源、publish gate、rollback、external lake root、provider 授权和 schema 状态机 | `docs/features/market-data-lake/*` | CR004..CR005、CR007、CR010、CR014、CR017、CR018 | full-lld | 新增 dataset、publish 规则、DuckDB 事实边界、真实写湖或 rollback 行为时 |
| FEAT-03 | 研究数据集与多因子研究闭环 | BLUEPRINT、HLD §35、ADR-079..086 | required | 多个 Story 共享 FactorSpec、FactorRunSpec、LabelWindow、ReportCatalog、AdmissionPackage | `docs/features/factor-research-loop/*` | CR011、CR019、CR030 | full-lld | 新增因子 schema、label window、组合器、admission package 字段时 |
| FEAT-04 | 执行语义对齐与可选后端参考 | BLUEPRINT、HLD §34、ADR-074..078 | required | 涉及 optional backend、依赖隔离、license/no-copy、semantic diff 和 order intent draft | `docs/features/execution-semantics-reference/*` | CR025、CR030 | full-lld | 新增 Backtrader / Qlib / external runner 依赖、运行或源码适配时 |
| FEAT-05 | QMT C/S Gateway 与只读运行准入 | BLUEPRINT、HLD §36、ADR-087..093 | required | 跨 Linux / Windows、HMAC、凭据引用、QMT login/session 和只读真实验证风险高 | `docs/features/qmt-gateway-readonly/*` | CR019、CR020 | full-lld | 恢复 CR-020 真实验证、扩大 endpoint 或引入新 gateway runtime 时 |
| FEAT-06 | OMS / 风控 / Broker Lake / 阶段激活 | BLUEPRINT、HLD-QMT、ADR-055..061 | required | 状态机、风控、broker facts、真实交易阶段和 kill switch 风险最高 | `docs/features/qmt-trading-governance/*` | CR015、CR016、CR017、CR021..024 candidate | full-lld | 启动 CR-021 simulation、CR-022 live_readonly、CR-023 small_live、CR-024 scale_up 时 |
| FEAT-07 | 安全、授权与 no-real-operation 治理 | BLUEPRINT、DEPENDENCY-MAP、全部高风险 CR | required | 横切 provider/lake/publish/QMT/credential/authorization，必须有统一测试与文档门禁 | `docs/features/runtime-authorization-safety/*` | CR014、CR019、CR020、CR025、CR030、后续 CR021..024 | full-lld | 任一真实操作授权、凭据路径、日志策略或 CP 人工门禁语义变化时 |
| FEAT-08 | 文档、Runbook 与发布证据 | README、USER-MANUAL、QMT docs、CP8 | waived / required-by-change | 普通文档刷新可 waived；涉及授权语义、运行手册、真实验证步骤时 required | none by default；按 CR 生成 docs plan | CR015..CR020、CP8 | technical-note / full-lld when safety relevant | 文档新增真实运行步骤、授权声明或 runbook 流程时 |
| FEAT-09 | QMT / MiniQMT 双目标策略交付框架 | BLUEPRINT v1.1、HLD-CR046、ADR-CR046-001..006 | required | 新增策略核心合同、策略包 schema、QMT terminal target、MiniQMT runner install design、验证证据模型和后续 CR gate；涉及外部交易终端边界与 no-real-operation 安全约束 | `docs/features/qmt-miniqmt-dual-target-framework/*` | CR046-S01..S07 | full-lld for S01..S05；technical-note for S06..S07 | 启动具体策略交付、真实 QMT shadow、MiniQMT install / connection、submit/cancel 或研究框架反向完善时 |
| FEAT-10 | 策略研究生命周期与项目迁移治理 | BLUEPRINT v1.2、DOMAIN-MAP v1.2、DEPENDENCY-MAP v1.2、HLD-CR051 | required | 新增策略生命周期、taxonomy、archive manifest、硬件冷热分层、项目身份、迁移 inventory 和后续 CR gate；涉及迁移、安全和跨 Feature 合同 | `docs/features/strategy-research-lifecycle/*` | CR051-S01..S06 | full-lld for S01..S04；technical-note for S05..S06 | 启动 CR052 多因子完整证明、真实目录迁移、NAS 操作、项目包名重命名、交易主机 package 消费或 runtime_candidate gate 时 |
| FEAT-10-CR053 | quant-lab migration inventory / dry-run | HLD-CR053、ADR-CR053-001..007、CR051 archive governance | required | CR053 是 FEAT-10 的迁移 dry-run 增量，新增 root map、repo inventory、path references、transfer/backup plan 和 CR058 输入；涉及 NAS / lake / Windows / Linux 映射和不授权边界 | `docs/features/quant-lab-migration-dry-run/*` | CR053-S01..S05 | full-lld for S01..S04；technical-note for S05 | CR058 真实 repo-local migration、CR060 NAS/archive 实迁、数据湖 root 迁移、交易机 package import 方式变化时 |

## Story 下游消费表

| Story / Story Group | feature_design_refs | lld_policy.required_level | trigger_reasons | 设计证据 | CP5 审查方式 |
|---|---|---|---|---|---|
| STORY-001..013 | legacy HLD / ADR / Story LLD | waived for CR-031 | baseline verified | `process/stories/STORY-*.md` | 不回写历史 Story |
| CR004..CR018 data-lake-related | `docs/features/market-data-lake/DESIGN.md` | full-lld for new changes | data / state / publish / migration / authorization | existing `process/stories/CR*-LLD.md` + feature index | 后续 CR 增量审查 |
| CR030-S01..S08 | `docs/features/factor-research-loop/DESIGN.md` | full-lld | schema / report catalog / admission / no-real-op | existing CR030 LLD + feature index | 后续变更审查 |
| CR025-S01..S06 | `docs/features/execution-semantics-reference/DESIGN.md` | full-lld | optional backend / license / semantic diff | existing CR025 LLD + feature index | 后续变更审查 |
| CR019 / CR020 | `docs/features/qmt-gateway-readonly/DESIGN.md` | full-lld | external runtime / security / readonly QMT | CR019 / CR020 LLD + feature index | CR020 恢复前审查 |
| CR015 / CR016 / future CR021..024 | `docs/features/qmt-trading-governance/DESIGN.md` | full-lld | OMS / risk / stage gate / broker lake | CR015 / CR016 LLD + feature index | 新 CR 必须审查 |
| 全部高风险 CR | `docs/features/runtime-authorization-safety/DESIGN.md` | full-lld | runtime authorization / no-real-op / redaction | safety feature index | CP2/CP3/CP5/CP8 均消费 |
| CR046-S01-dual-target-strategy-architecture | `docs/features/qmt-miniqmt-dual-target-framework/DESIGN.md` | full-lld | architecture / cross-feature / safety | Story LLD | CP5 自动预检 + 批量人工确认 |
| CR046-S02-strategy-package-contract-and-schema | `docs/features/qmt-miniqmt-dual-target-framework/DESIGN.md`、`TEST-PLAN.md` | full-lld | schema / contract / validation | Story LLD | CP5 自动预检 + 批量人工确认 |
| CR046-S03-qmt-terminal-target-framework | `docs/features/qmt-miniqmt-dual-target-framework/DESIGN.md`、`docs/features/runtime-authorization-safety/DESIGN.md` | full-lld | external terminal boundary / no-runtime | Story LLD | CP5 自动预检 + 批量人工确认 |
| CR046-S04-miniqmt-runner-install-and-runtime-boundary | `docs/features/qmt-miniqmt-dual-target-framework/DESIGN.md`、`docs/features/runtime-authorization-safety/DESIGN.md` | full-lld | install design / external runtime boundary / credential safety | Story LLD | CP5 自动预检 + 批量人工确认 |
| CR046-S05-verification-framework-and-evidence-model | `docs/features/qmt-miniqmt-dual-target-framework/TEST-PLAN.md` | full-lld | validation evidence / safety claims | Story LLD | CP5 自动预检 + 批量人工确认 |
| CR046-S06-follow-up-strategy-delivery-gate | `docs/features/qmt-miniqmt-dual-target-framework/TASKS.md` | technical-note | follow-up tracking / low implementation risk | Story 技术说明 | CP5 自动预检 + 批量人工确认 |
| CR046-S07-research-framework-follow-up-contract | `docs/features/qmt-miniqmt-dual-target-framework/DESIGN.md` | technical-note | research handoff / follow-up contract | Story 技术说明 | CP5 自动预检 + 批量人工确认 |
| CR051-S01-lifecycle-and-taxonomy-framework | `docs/features/strategy-research-lifecycle/DESIGN.md`、`TEST-PLAN.md` | full-lld | lifecycle / taxonomy / cross-feature / claim boundary | Story LLD | CP5 自动预检 + 批量人工确认 |
| CR051-S02-repository-archive-and-data-lake-governance | `docs/features/strategy-research-lifecycle/DESIGN.md`、`TEST-PLAN.md` | full-lld | archive governance / storage tiering / lake boundary / safety | Story LLD | CP5 自动预检 + 批量人工确认 |
| CR051-S03-research-pc-and-trading-pc-workflow | `docs/features/strategy-research-lifecycle/DESIGN.md`、`TASKS.md` | full-lld | host workflow / package consumer boundary / migration safety | Story LLD | CP5 自动预检 + 批量人工确认 |
| CR051-S04-registry-and-evidence-contracts | `docs/features/strategy-research-lifecycle/DESIGN.md`、`TEST-PLAN.md` | full-lld | manifest schema / validation evidence / guardrail | Story LLD | CP5 自动预检 + 批量人工确认 |
| CR051-S05-follow-up-cr-roadmap-and-admission-gates | `docs/features/strategy-research-lifecycle/TASKS.md` | technical-note | follow-up tracking / admission gate | Story 技术说明 | CP5 自动预检 + 批量人工确认 |
| CR051-S06-project-identity-rename-and-legacy-alias | `docs/features/strategy-research-lifecycle/DESIGN.md`、`TASKS.md` | technical-note | project identity / alias compatibility / no bulk rewrite | Story 技术说明 | CP5 自动预检 + 批量人工确认 |
| CR053-S01-root-map-and-host-mapping-contract | `docs/features/quant-lab-migration-dry-run/DESIGN.md`、`TEST-PLAN.md` | full-lld | NAS root map / Linux research host / Windows package exchange / lake alias | Story LLD | CP5 自动预检 + 批量人工确认 |
| CR053-S02-repo-inventory-and-path-classification | `docs/features/quant-lab-migration-dry-run/DESIGN.md`、`TEST-PLAN.md` | full-lld | repo-local inventory / path classification / forbidden content boundary | Story LLD | CP5 自动预检 + 批量人工确认 |
| CR053-S03-path-reference-and-legacy-alias-dry-run | `docs/features/quant-lab-migration-dry-run/DESIGN.md`、`TEST-PLAN.md` | full-lld | path references / legacy alias / manual-review dry-run | Story LLD | CP5 自动预检 + 批量人工确认 |
| CR053-S04-manifest-transfer-and-backup-plan | `docs/features/quant-lab-migration-dry-run/DESIGN.md`、`TEST-PLAN.md` | full-lld | manifest-first transfer / backup plan / restore rehearsal | Story LLD | CP5 自动预检 + 批量人工确认 |
| CR053-S05-cr058-migration-input-and-close-gate | `docs/features/quant-lab-migration-dry-run/DESIGN.md`、`TASKS.md` | technical-note | CR058 input / close gate / no-real-migration boundary | Story 技术说明 | CP5 自动预检 + 批量人工确认 |

## 提前确认的关键决策

| Decision ID | 决策类型 | 问题 | 推荐方案 | 备选方案 | 优劣摘要 | 影响 / 风险 | 回退 / 切换条件 | 状态 |
|---|---|---|---|---|---|---|---|---|
| DQ-FD-001 | implementation | 是否为所有 required Feature 补完整 DESIGN / TEST-PLAN / TASKS | 已按推荐补齐 FEAT-02、FEAT-03、FEAT-04、FEAT-05、FEAT-06、FEAT-07 六个 required Feature 索引 | 只补蓝图三件套，不补 Feature 索引 | 推荐方案让后续 CR 有稳定设计入口；备选 diff 更小但仍需翻 legacy HLD | 影响后续 CR 的设计入口完整性 | 若后续 Feature 设计与 legacy HLD 冲突，以 legacy HLD/ADR 为准并修订索引 | resolved-cr031 |
| DQ-FD-002 | implementation | 是否批量修改历史 Story 卡片增加 `feature_design_refs` | 推荐：不批量修改，只在后续变更 Story 中增量引用 | 批量回写 134 个 Story | 推荐方案避免污染已验证历史证据；批量回写追溯更完整但风险高 | 影响审计 diff 和 Story 历史稳定性 | 若未来执行统一文档迁移 CR，可专门处理 | resolved-cr031 |
| DQ-FD-CR046-01 | implementation | 是否为 FEAT-09 生成独立 DESIGN / TEST-PLAN / TASKS | 已生成；作为 CR046-S01..S07 的共同设计输入 | 只在 HLD 中保留；拆成多个 Feature 目录 | 推荐方案让策略包、QMT target、MiniQMT runner 和验证框架共用同一入口；只放 HLD 会让 CP5 LLD 输入分散 | 影响 CP4、CP5 和后续 CR047/049/051 消费 | 若后续 FEAT-09 变大，可拆分子 Feature，但需新 CR 或 CP5 决策 | resolved-cp4 |
| DQ-FD-CR046-02 | implementation | 策略从研究侧传到交易运行 PC 的默认形态是什么 | 采用 `strategy-package-<strategy_id>-<version>.zip` + `.sha256` + `manifest.yaml`，经人工/受控文件通道传到交易运行 PC，再由 QMT terminal target 人工导入 | Git release / 内网共享目录 / U 盘离线交付 / 自动同步 runner | 推荐方案可审计、可校验、可回滚，并隔离研究环境与交易 PC；自动同步 runner 会引入运行授权风险 | 影响 CR046-S02/S03 的 artifact、checksum、transfer_channel 和 manual_import_steps 字段 | 若 CP5 发现交易 PC 环境约束不同，可把 transfer_channel 设为枚举，但不得自动运行 | approved-by-user-2026-06-13 |
| DQ-FD-CR051-01 | implementation | 是否为 FEAT-10 生成独立 DESIGN / TEST-PLAN / TASKS，并将 CR051-S01..S06 纳入单一 CP5 批次 | 生成独立三件套；S01..S04 full-lld，S05..S06 technical-note；统一批次 `CR051-STRATEGY-RESEARCH-LIFECYCLE-BATCH-A` | 只保留 HLD；拆成迁移 Feature 与研究 Feature 两个目录 | 推荐方案降低 CP5 下游读取成本，并把迁移 / archive / lifecycle 的安全边界合并审查；只留 HLD 会让 Story LLD 输入分散，拆两个 Feature 会增加当前 CP4 复杂度 | 影响 CR052..CR056 进入条件、项目迁移计划和后续文档刷新 | 若 CP5 发现迁移实施风险高于研究生命周期，可拆出后续 Migration CR；真实迁移仍需独立授权 | resolved-cp4 |
| DQ-FD-CR053-01 | implementation | 是否为 CR053 生成 FEAT-10 scoped migration dry-run 三件套，并将 CR053-S01..S05 纳入单一 CP5 批次 | 生成 `docs/features/quant-lab-migration-dry-run/*`；S01..S04 full-lld，S05 technical-note；统一批次 `CR053-MIGRATION-INVENTORY-BATCH-A` | 只复用 FEAT-10 CR051 三件套；拆成 NAS / repo / backup 三个 Feature | 推荐方案让 CR053 dry-run 输入独立可审查，同时不污染 CR051 closed baseline；只复用 CR051 会让迁移 dry-run 细节分散；拆三 Feature 对当前范围过重 | 影响 CP5 设计证据、CP6 静态报告和 CR058 输入 | 若 CP5 发现 NAS / 数据湖迁移超出 dry-run，可拆出 CR060+；真实迁移仍需独立授权 | resolved-cp4 |

## 豁免与 N/A 说明

| Feature ID | 豁免 / N/A 原因 | 影响范围 | 风险接受 | 重访条件 | 责任方 |
|---|---|---|---|---|---|
| FEAT-01 | 基线已 verified，本轮只补索引 | STORY-001..013 和已关闭基础回测能力 | accepted | 修改核心 engine / strategies / reports schema 时 | meta-po / meta-se |
| FEAT-08 | 普通文档刷新可由 CR / CP8 处理 | README、USER-MANUAL、runbook | accepted | 文档新增真实操作步骤或授权语义时 | meta-doc / meta-qa |

## 自检

| 检查项 | 结果 | 证据 |
|---|---|---|
| 所有 Feature / Epic 均已判定 | PASS | §Feature 设计矩阵覆盖 FEAT-01..10，并新增 FEAT-10-CR053 scoped migration dry-run |
| required Feature 均有产物计划或已生成 | PASS | FEAT-02/03/04/05/06/07 已有索引；FEAT-09、FEAT-10 与 FEAT-10-CR053 已生成 DESIGN / TEST-PLAN / TASKS |
| 每个 Story 均有 feature_design_refs 与 lld_policy | PASS | CR046-S01..S07、CR051-S01..S06、CR053-S01..S05 均已在 Story 下游消费表登记 |
| 提前确认的关键决策已进入人工决策队列或 N/A | PASS | DQ-FD-001..002 已在 CR-031 留痕；DQ-FD-CR046-01 与 DQ-FD-CR051-01 已作为 CP4 设计决策记录，CP5 前无新增人工阻断项 |
