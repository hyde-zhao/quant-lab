---
story_id: "CR044-S06"
title: "Runbook and No Real Operation Guardrails"
story_slug: "runbook-and-no-real-operation-guardrails"
status: "ready-for-verification"
priority: "P1"
wave: "W5"
implementation_allowed: true
implementation_allowed_until: "L2 blocked-first / fixture-only only; no L3+ runtime"
depends_on:
  - "CR044-S01"
  - "CR044-S02"
  - "CR044-S03"
  - "CR044-S04"
  - "CR044-S05"
dependency_contracts:
  - upstream_story: "CR044-S01"
    type: "contract"
    required_for: "authorization and redaction baseline"
  - upstream_story: "CR044-S02"
    type: "contract"
    required_for: "admission gate and capability state"
  - upstream_story: "CR044-S03"
    type: "contract"
    required_for: "readonly blocked mapping"
  - upstream_story: "CR044-S04"
    type: "contract"
    required_for: "kill switch and submit/cancel blocked semantics"
  - upstream_story: "CR044-S05"
    type: "contract"
    required_for: "redacted evidence and reconciliation"
feature_design_refs:
  - "docs/design/FEATURE-DESIGN-MATRIX-CR044.md#feat-cr044-runbook"
lld_policy:
  required_level: "technical-note"
  trigger_reasons:
    - "validation"
    - "runtime_authorization"
    - "docs-handoff"
  rationale: "当前只需 runbook、no-real-operation checklist 和 CP7 关注点；若产生可执行 guard/script/schema，升级 full-lld。"
  waiver_reason: ""
  revisit_condition: "runbook 驱动自动 guard、schema、脚本或状态机时升为 full-lld。"
  evidence_path: "process/stories/CR044-S06-runbook-and-no-real-operation-guardrails.md#技术说明"
file_ownership:
  primary:
    - "process/stories/CR044-S06-runbook-and-no-real-operation-guardrails.md"
  shared:
    - "tests/test_cr044_goldminer_admission_guard.py"
  merge_owner: "CR044-S06"
  forbidden:
    - ".env"
    - ".env.*"
    - "engine/broker_adapter.py"
lld_gate:
  required_inputs:
    - "CR044-S01 design evidence"
    - "CR044-S02 design evidence"
    - "CR044-S03 design evidence"
    - "CR044-S04 design evidence"
    - "CR044-S05 design evidence"
  design_evidence_type: "technical-note"
  design_evidence_path: "process/stories/CR044-S06-runbook-and-no-real-operation-guardrails.md#技术说明"
  status: "ready-for-review"
dev_gate:
  implementation_allowed: true
  allowed_after: "CP5 approved"
  design_evidence_confirmed: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  real_runtime_authorized: false
---

# CR044-S06 Runbook and No Real Operation Guardrails

## 目标

把 S01-S05 的授权、gate、readonly、kill switch、reconciliation 合同收敛为可审查的 runbook、no-real-operation checklist 和 QA/CP7 验证入口。当前默认是 `technical-note`，不写 LLD 正文。

## 开发上下文（dev_context）

- 输入文件：S01-S05 设计证据、`docs/design/FEATURE-DESIGN-MATRIX-CR044.md`、`process/DEVELOPMENT-PLAN-CR044.yaml`、CP3 checkpoint。
- 输出文件：本 Story 卡片的 CP5 技术说明；如升级 full-lld，则输出 `process/stories/CR044-S06-runbook-and-no-real-operation-guardrails-LLD.md`。
- 接口约定：列出 allowed/offline-only actions、forbidden runtime actions、pre-run checklist、artifact scan checklist、CP7 evidence checklist。
- 设计约束：不得把 runbook 写成运行授权；不得新增真实 runtime 命令；不得要求读取 `.env` 或账户材料。
- 平台目标：文档/fixture-only；如后续新增脚本或 schema，必须升级 full-lld 并重新纳入 CP5。
- AI 可执行任务清单：

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR044-S06-T1 | 补充 | 本文件 `## 技术说明` | 在 CP5 前由 meta-dev 补齐 technical-note，覆盖 no-real-operation runbook。 |
| CR044-S06-T2 | 补充 | 本文件 `## 技术说明` | 列出 CP6/CP7 禁止操作检查和 artifact scan 清单。 |
| CR044-S06-T3 | 判定 | 本文件或 LLD | 若 runbook 驱动可执行 guard/script/schema，则升级 full-lld。 |

## 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR044-S01-S05 | contract | 上游设计证据齐全后补 technical-note | CP5 approved + 上游合同确认 | S06 是收敛 Story，不抢占 `engine/broker_adapter.py`。 |

## 技术说明

| 项目 | 内容 |
|---|---|
| 设计证据类型 | `technical-note`，不升级 full-lld。原因：本 Story 当前只沉淀人工 runbook、no-real-operation checklist、CP6/CP7 审查入口和禁止操作复述，不新增可执行 guard、schema、脚本或状态机。 |
| 设计依据 | `process/checkpoints/CP2-CR044-REQUIREMENTS-BASELINE.md` 已批准 L1/L2-only、零凭据持有和 L3+ 逐 run 授权；`process/checkpoints/CP3-CR044-HLD-REVIEW.md` 已批准 blocked-first、redaction-first、S01-S06 批次且 CP3 不等于 simulation-ready；`docs/design/FEATURE-DESIGN-MATRIX-CR044.md#feat-cr044-runbook` 指定 S06 默认 technical-note；S01-S05 LLD 提供授权、gate、readonly、kill switch、reconciliation 合同。 |
| 文件影响 | 仅更新本 Story 卡片 `## 技术说明` 和对应 CP5 自动预检；不修改 `engine/broker_adapter.py`，不创建脚本、schema、自动 guard 或测试文件。若后续要求 runbook 直接驱动可执行 guard / 脚本 / schema / 状态迁移，必须回退 CP5 并升级 full-lld。 |
| 接口 / 数据 / 权限变化 | 当前无代码接口和持久化数据变化。runbook 只列出人工检查入口：allowed offline actions、forbidden runtime actions、pre-run authorization checklist、artifact sensitive scan checklist、CP7 evidence checklist。权限上继续只允许 L1 formal CR orchestration 和 L2 offline engineering design / fixture-only；继续不授权 credential_read、login、connect、account/cash/position/order/fill query、submit/cancel、simulation/live、provider_fetch、lake_write、catalog_publish。 |
| 异常和回退 | 发现任何真实 runtime 需求、凭据/账号材料、真实 SDK import/call、真实 query/submit/cancel、provider/lake/catalog 操作时，runbook 指示 fail-closed：停止当前 Story 实现或验证，将事项交回 meta-po 发起独立授权决策或新 CR。发现 artifact 含敏感字段原值时，CP7 必须 FAIL / NEEDS_REWORK，并要求 redaction 后重验。 |
| 测试入口 | CP5 审查本 technical-note 完整性；CP6 后可使用 CR044 fixture tests、CR042 回归、AST forbidden import/call scan、artifact sensitive field scan、operation_counts 全 0 检查；CP7 人工审查确认 approve/CP5/CP8 均不授权 L3+。禁止以真实 broker/sdk/provider/lake/catalog 操作为验证入口。 |
| 风险与重访条件 | 风险 1：runbook 被误读为运行授权，缓解为在用户可见段落列出“不授权项”和真实操作计数必须为 0。风险 2：S01-S05 后续实现扩展出可执行 guard，缓解为触发 full-lld 升级条件。风险 3：真实账号权限长期不可得，缓解为 CP8 只允许关闭为 offline-admission-design-ready、blocked-by-account-permission 或 not-recommended，不得宣称 simulation-ready/live-ready。 |
| 偏离记录 | 无设计偏离。S06 保持 `technical-note`，未升级 full-lld；依据为 Feature Matrix 的升级条件未命中：本次不新增可执行 guard、schema、脚本或状态机。 |

### Runbook 检查清单草案

| 分类 | 检查项 | 预期结果 |
|---|---|---|
| Allowed offline actions | 阅读 CR044/CP2/CP3/CP5 证据；运行 fixture-only 单测；执行静态 AST / artifact scan | PASS，且不接触真实 broker runtime。 |
| Forbidden runtime actions | credential_read、login、connect、account/cash/position/order/fill query、submit/cancel、simulation/live、provider_fetch、lake_write、catalog_publish | 均为 not-authorized；任何触发都 fail-closed。 |
| Operation counts | `real_broker_call`、`real_order_call`、`real_cancel_call`、`real_account_query`、`real_position_query`、`real_cash_query`、`credential_read`、`goldminer_import_or_call`、`gmtrade_import_or_call` 等 | 当前授权下必须全为 0。 |
| Artifact scan | token、secret、password、passwd、cookie、session、private_key、account_id、broker_account、real_account、trade_password、credential、broker_order_id、execution ref | 不得出现真实值；只允许字段名、规则 ID、`REDACTED`、present flag、计数。 |
| 用户可见授权提示 | CP5/CP8 approve 不授权 L3+；真实动作必须逐 run 授权 | 必须在 CP5 batch 和最终 runbook 中单独列出。 |

## 验证上下文（validation_context）

| 项目 | 内容 |
|---|---|
| validation_mode | review-only + static-only |
| 验证入口 | CP5 technical-note review；CP7 artifact scan；CR044 guard tests 结果摘要 |
| 关键验证场景 | runbook 不授权 runtime；禁止操作清单完整；CP7 可证明真实操作计数为 0。 |
| 禁止验证方式 | 不提供真实 runtime 命令，不读取凭据，不连接 broker，不 provider_fetch/lake_write/catalog_publish。 |
| CP7 关注点 | 用户视角说明 approve/CP5/CP8 均不等于 L3+ 授权；不授权项单独列出。 |

## 量化验收标准（acceptance_criteria）

- [ ] runbook 禁止操作清单至少覆盖 CR044 当前 15 项 not-authorized action。
- [ ] 明确 `approve`、CP5、CP8 均不授权 credential_read、login、connect、query、submit/cancel、simulation/live。
- [ ] no-real-operation checklist 至少覆盖 operation_counts、forbidden imports/calls、artifact sensitive scan 三类证据。
- [ ] 若新增 executable guard、script、schema 或状态机，`lld_policy.required_level` 必须升级为 `full-lld`。
- [ ] S06 不修改 `engine/broker_adapter.py`，不抢占 S02-S05 shared code merge ownership。
- [ ] `implementation_allowed=false until CP5 approved` 保持成立。

## 阻塞说明

无 L2 文档/技术说明阻塞；可执行 guard 若纳入范围则需升级 full-lld。
