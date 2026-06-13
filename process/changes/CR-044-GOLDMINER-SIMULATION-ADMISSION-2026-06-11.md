---
cr_id: "CR-044"
status: "closed-current-delivery"
impact_level: "high"
workflow_mode_before: "standard"
workflow_mode_after_change: "standard"
fast_lane_upgrade_reason: "掘金仿真准入涉及外部 broker、账号权限、凭据边界、per-run authorization、下单 / 撤单 / 对账和 kill switch，必须走 standard。"
rollback_to: "CR043 closed-spike-complete"
approval_result: "approved-to-start-cp2-intake-and-offline-engineering-design"
created_at: "2026-06-11T09:53:10+08:00"
created_by: "meta-po"
approved_by: "user"
approved_at: "2026-06-11T09:53:10+08:00"
source: "cp8-follow-up"
linked_issue: ""
parent_cr: "CR-043"
source_checkpoint: "process/checkpoints/CP8-CR043-DELIVERY-READINESS.md"
source_decision_id: "USER-20260611-START-CR044"
follow_up_type: "CR"
risk_class: "high"
owner: "meta-po"
predecessor_cr: "CR-043"
predecessor_conclusion: "NEEDS_ACCOUNT_PERMISSION"
authorization_scope: "L1 formal CR orchestration; L2 offline engineering design and fixture-only implementation; subagent dispatch allowed"
non_authorized_scope: "credential_read; login; connect; account_query; position_query; cash_query; order_submit; order_cancel; simulation_runtime; live_runtime; provider_fetch; lake_write; catalog_publish"
revisit_condition: "CP2 / CP3 明确账号权限、凭据处理、per-run authorization、只读查询、仿真下单 / 撤单、对账、kill switch 和 redaction 边界后，才能判断是否申请 L3 / L4 / L5 逐 run 授权。"
acceptance_criteria: "CR044 至少产出授权决策表、仿真准入 HLD、Story / LLD 批次、no-operation guard、redaction、kill switch、reconciliation、blocked-first adapter 设计与 fixture-only 验证；默认真实操作计数为 0。"
close_condition: "CR044 必须经 CP2 / CP3 / CP5 / CP6 / CP7 / CP8 收敛；若未获 L3+ 授权，只能关闭为 offline-admission-design-ready、blocked-by-account-permission 或 not-recommended，不得宣称 simulation/live ready。"
cr_index_path: "process/changes/CR-INDEX.yaml"
cp2_context_path: "process/context/CP2-CR044-REQUIREMENT-CONTEXT.yaml"
cp2_auto_check_path: "process/checks/CP2-CR044-REQUIREMENTS-BASELINE.md"
cp2_checkpoint_path: "process/checkpoints/CP2-CR044-REQUIREMENTS-BASELINE.md"
cp2_launch_message_path: "process/checks/CP2-CR044-HUMAN-GATE-LAUNCH-MESSAGE.md"
cp2_reviewed_by: "user"
cp2_reviewed_at: "2026-06-11T10:57:32+08:00"
cp2_review_status: "approved"
cp3_context_path: "process/context/CP3-CR044-DESIGN-CONTEXT.yaml"
cp3_auto_check_path: "process/checks/CP3-CR044-HLD-CONSISTENCY.md"
cp3_checkpoint_path: "process/checkpoints/CP3-CR044-HLD-REVIEW.md"
cp3_launch_message_path: "process/checks/CP3-CR044-HUMAN-GATE-LAUNCH-MESSAGE.md"
cp3_reviewed_by: "user"
cp3_reviewed_at: "2026-06-11T11:17:04+08:00"
cp3_review_status: "approved"
meta_se_handoff_path: "process/handoffs/META-SE-CR044-CP2-CP3-DESIGN-2026-06-11.md"
human_gate_validation: "PASS: uv run --python 3.11 python scripts/check_human_gate_decision_brief.py --checkpoint-file process/checkpoints/CP2-CR044-REQUIREMENTS-BASELINE.md --launch-message-file process/checks/CP2-CR044-HUMAN-GATE-LAUNCH-MESSAGE.md at 2026-06-11T10:03:28+08:00"
cp3_human_gate_validation: "PASS: uv run --python 3.11 python scripts/check_human_gate_decision_brief.py --checkpoint-file process/checkpoints/CP3-CR044-HLD-REVIEW.md --launch-message-file process/checks/CP3-CR044-HUMAN-GATE-LAUNCH-MESSAGE.md at 2026-06-11T11:01:02+08:00"
cr_tracking_consistency: "PASS: uv run --python 3.11 python scripts/check_cr_tracking_consistency.py --project-root . at 2026-06-11T11:01:02+08:00"
story_planning_handoff_path: "process/handoffs/META-SE-CR044-STORY-PLANNING-2026-06-11.md"
feature_design_matrix_cr044_path: "docs/design/FEATURE-DESIGN-MATRIX-CR044.md"
development_plan_cr044_path: "process/DEVELOPMENT-PLAN-CR044.yaml"
cp4_auto_check_path: "process/checks/CP4-CR044-STORY-DAG-PARALLEL-SAFETY.md"
cp4_status: "PASS"
cp5_batch_id: "CR044-LLD-BATCH-A-ADMISSION-GUARD"
cp5_batch_checkpoint_path: "process/checkpoints/CP5-CR044-ALL-STORIES-LLD-BATCH.md"
cp5_context_path: "process/context/CP5-CR044-LLD-CONTEXT.yaml"
cp5_launch_message_path: "process/checks/CP5-CR044-HUMAN-GATE-LAUNCH-MESSAGE.md"
cp5_auto_status: "PASS"
cp5_auto_pass_count: 6
cp5_manual_status: "approved"
cp5_approved_by: "user"
cp5_approved_at: "2026-06-11T11:54:21+08:00"
cp5_approval_text: "同意"
cp5_approval_interpretation: "accepted DQ-CP5-CR044-01..05 recommendations; authorizes only L2 blocked-first / fixture-only implementation and keeps all L3+ runtime operations not-authorized"
cp5_lld_handoff_path: "process/handoffs/META-DEV-CR044-LLD-BATCH-2026-06-11.md"
cp5_human_gate_validation: "PASS: uv run --python 3.11 python scripts/check_human_gate_decision_brief.py --checkpoint-file process/checkpoints/CP5-CR044-ALL-STORIES-LLD-BATCH.md --launch-message-file process/checks/CP5-CR044-HUMAN-GATE-LAUNCH-MESSAGE.md at 2026-06-11T11:50:28+08:00"
cp5_diff_check: "PASS: git diff --check -- CR044 CP5 files at 2026-06-11T11:50:28+08:00"
cr_tracking_consistency_latest: "PASS: uv run --python 3.11 python scripts/check_cr_tracking_consistency.py --project-root . at 2026-06-11T11:50:28+08:00"
cp6_context_path: "process/context/CP6-CR044-IMPLEMENTATION-CONTEXT.yaml"
cp6_implementation_handoff_path: "process/handoffs/META-DEV-CR044-IMPLEMENT-2026-06-11.md"
cp6_implementation_agent_id: "019eb4d3-e87d-73b0-b237-59740e4d473a"
cp6_implementation_agent_name: "dev-qin"
cp6_implementation_spawned_at: "2026-06-11T11:54:21+08:00"
cp6_implementation_completed_at: "2026-06-11T12:12:20+08:00"
cp6_status: "PASS"
cp6_pass_count: 6
cp6_validation: "PASS: PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr042_broker_adapter_contract.py tests/test_cr044_goldminer_admission_guard.py -> 13 passed at 2026-06-11T12:13:24+08:00"
cp7_context_path: "process/context/CP7-CR044-VERIFICATION-CONTEXT.yaml"
cp7_verification_handoff_path: "process/handoffs/META-QA-CR044-CP7-2026-06-11.md"
cp7_verification_agent_id: "019eb4e4-5664-7f80-af18-7c0e37db13c8"
cp7_verification_agent_name: "qa-cao"
cp7_verification_spawned_at: "2026-06-11T12:13:24+08:00"
cp7_verification_completed_at: "2026-06-11T12:18:26+08:00"
cp7_status: "PASS_WITH_RISK"
cp7_findings: "none-found"
release_context_path: "process/release/RELEASE-CONTEXT.yaml"
cp8_auto_check_path: "process/checks/CP8-CR044-DELIVERY-READINESS.md"
cp8_checkpoint_path: "process/checkpoints/CP8-CR044-DELIVERY-READINESS.md"
cp8_launch_message_path: "process/checks/CP8-CR044-HUMAN-GATE-LAUNCH-MESSAGE.md"
cp8_release_decision: "READY_WITH_RISK"
cp8_manual_status: "approved"
cp8_reviewed_by: "user"
cp8_reviewed_at: "2026-06-11T21:28:16+08:00"
cp8_approval_text: "同意"
cp8_approval_interpretation: "accepted DQ-CP8-CR044-01..05 recommendations; closes CR044 current offline admission delivery as READY_WITH_RISK / offline-admission-design-ready; does not authorize L3+ runtime"
closure_result: "offline-admission-design-ready"
closed_at: "2026-06-11T21:28:16+08:00"
---

## 变更描述

启动 CR044 Goldminer Simulation Admission。目标是在 CR043 `NEEDS_ACCOUNT_PERMISSION` 结论之后，按工程化门禁建立掘金仿真准入的需求、架构、Story / LLD、实现和验证路径。

本 CR 当前只授权：

- L1：正式 CR 编排、状态同步、CP2 / CP3 / CP5 / CP6 / CP7 / CP8 门禁准备。
- L2：离线工程设计和 fixture-only / blocked-first 工程资产实现。
- 子 agent 调度：允许 meta-po 调用 `meta-se`、`meta-dev`、`meta-qa` 分别处理设计、实现和验证。

本 CR 当前不授权读取凭据、登录、连接 broker、查询账户 / 持仓 / 资金 / 委托 / 成交、下单、撤单、启动 simulation/live、provider fetch、lake write 或 catalog publish。

## CP8 Follow-up 来源

| 字段 | 内容 |
|---|---|
| 父级 CR | `CR-043` |
| 来源检查点 | `process/checkpoints/CP8-CR043-DELIVERY-READINESS.md` |
| 来源决策 ID | `USER-20260611-START-CR044` |
| follow-up 类型 | `CR` |
| 风险等级 | `high` |
| owner | `meta-po` |
| 重访条件 | CR043 已关闭为 `NEEDS_ACCOUNT_PERMISSION`；CR044 先做账号 / 仿真权限准入设计和离线工程门禁。 |
| 验收标准 | 授权决策、账号权限边界、per-run authorization、凭据脱敏、只读查询、下单 / 撤单、对账、kill switch、blocked result 和 no-operation guard 均可审计。 |
| 关闭条件 | CP8 明确 `offline-admission-design-ready`、`blocked-by-account-permission`、`not-recommended` 或后续经逐 run 授权后的更细结论。 |

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md` | 原文档更新 | 保留 Track C CR044 原候选行，状态从 planned 转 active-cp2-intake | 本 CR 摘录 | approved |
| `process/changes/CR-INDEX.yaml` | 原文档更新 | 保留 CR043 关闭态，新增 CR044 active 索引 | N/A | approved |
| `process/STATE.md` | 原文档更新 | 保留 delivered 基线和 CR043 关闭结论，记录 CR044 active formal CR | N/A | approved |
| `docs/product/USE-CASES.md` | 不变 | 既有场景基线不变；CR044 的准入场景先落入过程门禁和 Story 设计 | 不适用 | approved |
| `docs/product/REQUIREMENTS.md` | 不变 | 既有需求基线不变；若 CP2 判定需要长期需求修订，再追加修订记录 | 不适用 | approved |
| `docs/design/HLD.md` | 原文档更新 / CR-scoped HLD | 既有全局 HLD 不整体重写；优先生成 CR044 scoped HLD / capsule，必要时再增量回写 | 待 CP3 判定 | pending |
| `process/stories/CR044-*` | 新增 | 不替换 CR041 / CR042 / CR043 Story；只新增 CR044 范围 Story | Story frontmatter | pending |

## 旧基线映射

| 原基线对象 | 新增 / 修改对象 | 保留策略 | 映射说明 |
|---|---|---|---|
| CR041 API-less Paper Simulation Runner | CR044 Goldminer Simulation Admission | CR041 closed-current-delivery 原样保留 | CR044 不修改本地 paper simulation 语义，只消费其 order intent / ledger / reconciliation 经验。 |
| CR042 Broker-Neutral Adapter Contract | CR044 Goldminer admission gate / blocked-first adapter | CR042 合同原样保留 | CR044 必须继续满足 `BrokerAdapter`、operation counters、sensitive field guard 和 `GoldminerStubBrokerAdapter` fail-closed 语义。 |
| CR043 Goldminer Adapter Spike | CR044 账号 / 仿真权限准入 | CR043 Spike 证据原样保留 | CR043 只证明 SDK 静态候选和接口映射，不能被解释为仿真运行授权。 |
| CR019 Track C CR044 候选 | CR044 正式 CR | 台账保留候选来源 | CR044 由 planned 转 active-cp2-intake。 |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论（true/false） | 处理动作 |
|------|----------|-----------|--------------------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | `REQUIREMENTS.md` / CR044 scoped requirements | true | 当前先创建 CR scoped 准入需求；CP2 判定是否回写长期需求。 |
| 场景层 | 是否改变测试矩阵覆盖范围 | CR044 authorization / redaction / kill switch / reconciliation / no-operation scenarios | true | 生成 CR044 scoped scenarios 和测试矩阵；默认真实操作计数为 0。 |
| 计划层 | 是否改变 Phase、Wave、Story / 任务依赖 | `STATE.md` / `CR-INDEX.yaml` / `process/stories/CR044-*` | true | CR044 转 active formal CR，进入 CP2 intake；后续由 meta-se 拆 Story 和 LLD 批次。 |
| 安全层 | 是否引入新的高风险动作或权限要求 | credential、account、broker runtime、submit / cancel、simulation / live | true | 当前只批准 L1/L2；L3+ 必须独立逐 run 授权。 |
| 交付层 | 是否需要重新生成交付物或回归子集 | broker adapter tests、runbook、quality report、release readiness | true | 后续至少需要本地 pytest、静态敏感字段扫描、no-operation guard、CP7 验证和 CP8 风险说明。 |

## 授权分层

| 层级 | 状态 | 允许动作 | 禁止动作 |
|---|---|---|---|
| L1 formal CR orchestration | approved | 创建 / 更新 CR、STATE、CR-INDEX、台账、checkpoint、context capsule、handoff | 不触碰凭据或 broker runtime |
| L2 offline engineering design | approved | 设计 HLD / Story / LLD / fixture-only 代码 / blocked-first guard / 本地测试 | 不调用真实 SDK runtime 方法，不新增持久 broker 依赖 |
| L3 credential / account permission check | not-authorized | N/A | 不读取 `.env`、token、account、password、session、cookie、private key |
| L4 simulation readonly query | not-authorized | N/A | 不查询 cash / position / order / fill / account state |
| L5 simulation submit / cancel / reconcile run | not-authorized | N/A | 不下单、不撤单、不启动 simulation/live |

## 回退决策

- 影响范围：局部高风险 CR
- 回退到阶段：`CR043 closed-spike-complete`
- 需要重新确认的对象：
  - 若 CP2 无法确认授权边界，CR044 保持 `blocked-by-authorization-scope`。
  - 若 CP3 无法形成安全架构，回退到 CR043 结论并关闭为 `not-recommended` 或 `blocked-by-account-permission`。
  - 若任何实现路径需要 L3+ 授权，必须先发起独立人工决策，不得静默执行。

## fast-lane 判定

| 条件 | 是否命中 | 说明 |
|---|---|---|
| 仅低风险轻量实现 / 文档 / 规则修改 | false | 涉及外部 broker 仿真准入和运行授权边界。 |
| 修改架构、权限、安全边界或平台安装路径 | true | 命中凭据、账号、broker runtime、下单 / 撤单和 kill switch。 |
| 修改外部接口契约、文件所有权或多 Story 依赖 | true | 会影响 broker adapter、authorization gate、redaction、reconciliation 和 runbook。 |
| 需要 HLD / LLD 才能解释影响 | true | 必须明确准入状态机、失败路径和逐 run 授权。 |
| 是否保持 fast-lane | false | 必须 standard。 |

## LLD 设计批次门禁

- 是否需要 LLD 设计批次：true
- batch_id：`CR044-LLD-BATCH`
- 批次范围来源：CR044 影响分析 / CP3 设计
- 批次内 Story（初稿，待 meta-se 细化）：
  - `CR044-S01-authorization-and-secret-boundary`
  - `CR044-S02-goldminer-admission-gate-and-capability-state`
  - `CR044-S03-readonly-query-field-mapping-blocked-first`
  - `CR044-S04-simulation-submit-cancel-kill-switch-contract`
  - `CR044-S05-reconciliation-and-redacted-evidence`
  - `CR044-S06-runbook-and-no-real-operation-guardrails`
- 批次人工确认稿：`process/checkpoints/CP5-CR044-ALL-STORIES-LLD-BATCH.md`
- 开发启动条件：
  - [ ] CP2 人工确认授权边界。
  - [ ] CP3 人工确认架构和不授权边界。
  - [ ] 批次内全部 Story 设计证据已输出（full-lld / technical-note / waived）。
  - [ ] 批次内全部 Story CP5 自动预检已通过。
  - [ ] 批次 CP5 人工确认结论为 `approved`。
  - [ ] 任一 L3+ 行为都有独立逐 run 授权；否则只能实现 blocked-first / fixture-only 资产。

## 执行链路

| 顺序 | 责任角色 | 动作 | 输入 | 输出 | 门控 | 完成后下一步 |
|---|---|---|---|---|---|---|
| 1 | `meta-po` | 创建 CR044 并分派 | 用户同意启动 CR044、CR043 结论 | 本 CR、STATE、CR-INDEX、台账 | 当前无 active formal CR | 调度 meta-se |
| 2 | `meta-se` | 完成 CR044 CP2 / CP3 设计输入和 Story 拆解 | CR044、CR041-043 证据、broker adapter 合同 | CR044 scoped HLD、Decision Brief 输入、Story / LLD 批次建议 | 不授权真实 broker runtime | 交回 meta-po 发起 CP2 / CP3 |
| 3 | `meta-dev` | CP5 通过后实现 L2 离线工程资产 | Story / LLD / CP5 | blocked-first code、fixture tests、guardrails、implementation evidence | 未获 L3+ 时真实操作计数必须为 0 | 交回 meta-qa |
| 4 | `meta-qa` | 验证 no-operation、redaction、gate、reconciliation 合同 | CP6 实现证据 | CP7 验证报告 / REVIEW | 不运行真实 broker | 交回 meta-po |
| 5 | `meta-po` | 收敛 CP8 | CR044 全部证据 | CP8 自动预检与人工审查稿 | 等待用户确认 | 关闭 CR044 或发起后续授权 CR |

## 自动终验授权

- 是否启用：false
- 授权范围：不适用
- 适用检查点：N/A
- 自动通过条件：N/A
- 授权原文：N/A
- 授权时间：N/A
- 回填要求：N/A

## CP8 关闭结果

| 字段 | 内容 |
|---|---|
| CP8 审查结论 | approved |
| 用户确认 | 2026-06-11T21:28:16+08:00 回复“同意” |
| 关闭状态 | `closed-current-delivery` |
| 关闭结论 | `offline-admission-design-ready` / `READY_WITH_RISK` |
| 接受决策 | `DQ-CP8-CR044-01` 至 `DQ-CP8-CR044-05` |
| 不授权边界 | 继续不授权 credential_read、login、connect、account/cash/position/order/fill query、order_submit、order_cancel、simulation/live、provider_fetch、lake_write、catalog_publish |
| 后续候选 | `CR-045-candidate` 仅作为 not-created follow-up；真实 Goldminer L3/L4/L5 验证必须另行授权 |

## 后续事项台账

- 是否存在后续事项：true
- 台账路径：`process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md`
- CR 索引路径：`process/changes/CR-INDEX.yaml`
- 一致性检查：`uv run --python 3.11 python scripts/check_cr_tracking_consistency.py --project-root .`

| 候选编号 | 标题 | 状态 | 类型 | 优先级 | 正式 CR 路径 | 相关 active CR / blocked_by / superseded_by | 当前门控 | 阻塞原因 | 下一步 |
|---|---|---|---|---:|---|---|---|---|---|
| CR-045-candidate | Goldminer credential / readonly probe authorization | not-created | CR candidate | 5 | N/A | follow-up-after-CR044 | not-started | L3+ / L4 / L5 未授权；当前只关闭 CR044 离线准入工程资产 | 用户明确授权凭据策略、运行窗口和 L3/L4/L5 边界后，另行启动正式 CR |

## 处理结论

- 审批结论：`approved-to-start-cp2-intake-and-offline-engineering-design`
- [x] 用户已明确要求启动 CR044
- [x] 用户已允许调用子 agent
- [x] 当前无 active formal CR 冲突
- [x] 当前只授权 L1 / L2
- [x] 不授权真实 broker / 凭据 / 账户 / 下单 / 撤单 / simulation/live
- [x] `meta-se` 已交回 CP2/CP3 设计输入：`process/handoffs/META-SE-CR044-CP2-CP3-DESIGN-2026-06-11.md`
- [x] CP2 自动预检 PASS：`process/checks/CP2-CR044-REQUIREMENTS-BASELINE.md`
- [x] CP2 人工审查稿已生成：`process/checkpoints/CP2-CR044-REQUIREMENTS-BASELINE.md`
- [x] 用户已回复“同意”，CP2 人工审查回填为 `approved`
- [x] CP3 自动预检 PASS：`process/checks/CP3-CR044-HLD-CONSISTENCY.md`
- [x] CP3 人工审查稿已生成：`process/checkpoints/CP3-CR044-HLD-REVIEW.md`
- [x] 用户已回复“同意”，CP3 人工审查回填为 `approved`
- [x] Human gate launch message 校验 PASS：`process/checks/CP2-CR044-HUMAN-GATE-LAUNCH-MESSAGE.md`
- [x] meta-se 已完成 Story planning：`process/handoffs/META-SE-CR044-STORY-PLANNING-2026-06-11.md`
- [x] Feature Design Matrix 已生成：`docs/design/FEATURE-DESIGN-MATRIX-CR044.md`
- [x] Development Plan 已生成：`process/DEVELOPMENT-PLAN-CR044.yaml`
- [x] CP4 自动预检 PASS：`process/checks/CP4-CR044-STORY-DAG-PARALLEL-SAFETY.md`
- [x] meta-dev 已完成 CP5 设计证据批次：`process/handoffs/META-DEV-CR044-LLD-BATCH-2026-06-11.md`
- [x] S01-S05 full-lld 与 S06 technical-note 已 ready-for-review
- [x] CP5 自动预检 6/6 PASS
- [x] CP5 人工审查稿已生成：`process/checkpoints/CP5-CR044-ALL-STORIES-LLD-BATCH.md`
- [x] 用户已回复“同意”，CP5 人工审查回填为 `approved`
- [x] meta-dev 已完成 L2 blocked-first / fixture-only 工程资产实现：`process/handoffs/META-DEV-CR044-IMPLEMENT-2026-06-11.md`
- [x] CP6 6/6 PASS；目标测试 `13 passed`
- [x] meta-qa 已完成 CP7 验证：`process/handoffs/META-QA-CR044-CP7-2026-06-11.md`
- [x] CP7 结论 `PASS_WITH_RISK`，findings none-found
- [x] CP8 自动预检 PASS；release_decision=`READY_WITH_RISK`
- [ ] 等待用户审查 CP8 人工终验稿

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| Follow-up | CR019 Track C CR-044 row | 候选项来源。 |
| Parent CR | CR-043 | Goldminer Adapter Spike；结论 `NEEDS_ACCOUNT_PERMISSION`。 |
| Upstream CR | CR-042 | Broker-Neutral Adapter Contract。 |
| Upstream CR | CR-041 | API-less Paper Simulation Runner。 |
| Code baseline | `engine/broker_adapter.py` | CR042 `GoldminerStubBrokerAdapter` 仍为当前唯一 Goldminer 运行态对象。 |
| Spike evidence | `process/research/cr043_goldminer_adapter_spike/SPIKE-CONCLUSION.md` | CR044 启动输入。 |

## 不授权声明

CR044 当前不授权读取 `.env`、token、账号、密码、session、cookie、密钥或终端配置；不授权登录、连接、查询真实或仿真账户、提交订单、撤单、真实 broker 调用、provider fetch、lake write、catalog publish、simulation/live 或任何交易运行。
