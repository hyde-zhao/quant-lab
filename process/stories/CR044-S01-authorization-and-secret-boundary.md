---
story_id: "CR044-S01"
title: "Authorization and Secret Boundary"
story_slug: "authorization-and-secret-boundary"
status: "ready-for-verification"
priority: "P0"
wave: "W1"
implementation_allowed: true
implementation_allowed_until: "L2 blocked-first / fixture-only only; no L3+ runtime"
depends_on: []
dependency_contracts: []
feature_design_refs:
  - "docs/design/FEATURE-DESIGN-MATRIX-CR044.md#feat-cr044-auth"
lld_policy:
  required_level: "full-lld"
  trigger_reasons:
    - "security"
    - "permission"
    - "runtime_authorization"
    - "shared-story-boundary"
  rationale: "授权层级、敏感字段、零凭据持有和 redaction 是 CR044 全部后续 Story 的前置合同。"
  waiver_reason: ""
  revisit_condition: "任何凭据、账号、session、cookie、private key 或真实账户标识需要读取或记录时，暂停并发起 L3 安全授权。"
  evidence_path: "process/stories/CR044-S01-authorization-and-secret-boundary-LLD.md"
file_ownership:
  primary:
    - "process/stories/CR044-S01-authorization-and-secret-boundary.md"
    - "process/stories/CR044-S01-authorization-and-secret-boundary-LLD.md"
  shared:
    - "docs/design/FEATURE-DESIGN-MATRIX-CR044.md"
  merge_owner: "CR044-S01"
  forbidden:
    - ".env"
    - ".env.*"
    - "engine/broker_adapter.py"
    - "tests/test_cr042_broker_adapter_contract.py"
lld_gate:
  required_inputs:
    - "process/checkpoints/CP2-CR044-REQUIREMENTS-BASELINE.md"
    - "process/checkpoints/CP3-CR044-HLD-REVIEW.md"
    - "docs/design/FEATURE-DESIGN-MATRIX-CR044.md"
  design_evidence_type: "full-lld"
  design_evidence_path: "process/stories/CR044-S01-authorization-and-secret-boundary-LLD.md"
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

# CR044-S01 Authorization and Secret Boundary

## 目标

冻结 CR044 的授权分层、零凭据持有、敏感字段分类、redaction 和 fail-closed 规则，使 S02-S06 在没有 L3+ 授权时只能设计或实现 fixture-only blocked-first 资产。

## 开发上下文（dev_context）

- 输入文件：`process/changes/CR-044-GOLDMINER-SIMULATION-ADMISSION-2026-06-11.md`、`process/checkpoints/CP2-CR044-REQUIREMENTS-BASELINE.md`、`process/checkpoints/CP3-CR044-HLD-REVIEW.md`、`docs/design/FEATURE-DESIGN-MATRIX-CR044.md`、`engine/broker_adapter.py`。
- 输出文件：`process/stories/CR044-S01-authorization-and-secret-boundary-LLD.md`；本 Story 卡片。
- 接口约定：定义 L1/L2/L3/L4/L5 authorization layer、not-authorized action list、sensitive field patterns、redaction evidence shape、blocked reason taxonomy。
- 设计约束：不得读取 `.env`、token、account、password、session、cookie、private key；不得要求用户提供真实账户材料；不得引入真实 SDK import/call。
- 命名规范：新增标识使用 `CR044_*` 或 `cr044_*` 前缀；敏感字段输出只能是字段名、规则 ID、`REDACTED` 或 `present=true/false`。
- 平台目标：Python 3.11、uv、fixture-only；任何真实 runtime 行为 fail-closed。
- AI 可执行任务清单：

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR044-S01-T1 | 设计 | `process/stories/CR044-S01-authorization-and-secret-boundary-LLD.md` | 描述授权分层、敏感字段分类和 redaction 合同。 |
| CR044-S01-T2 | 设计 | `process/stories/CR044-S01-authorization-and-secret-boundary-LLD.md` | 定义 fail-closed 决策表和 L3+ 逐 run 授权触发条件。 |
| CR044-S01-T3 | 设计 | `process/stories/CR044-S01-authorization-and-secret-boundary-LLD.md` | 给出后续测试 fixture 的输入/输出边界，不写真实值。 |

## 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| N/A | N/A | CP2/CP3 approved | CP5 approved | S01 是 CR044 设计批次根节点。 |

## 验证上下文（validation_context）

| 项目 | 内容 |
|---|---|
| validation_mode | static-only + fixture-only |
| 验证入口 | 后续 `uv run --python 3.11 pytest -q tests/test_cr042_broker_adapter_contract.py tests/test_cr044_goldminer_admission_guard.py` |
| 关键验证场景 | 敏感字段出现时 blocked/redacted；不授权动作计数非零时 blocked；真实操作计数默认全 0。 |
| 禁止验证方式 | 不读取凭据、不连接 broker、不查询账户、不提交/撤销订单、不启动 simulation/live。 |
| CP7 关注点 | artifact scan 不能出现真实 token/account/session/cookie/private key 或真实 broker order ref。 |

## 量化验收标准（acceptance_criteria）

- [ ] `authorization_layers` 至少覆盖 L1、L2、L3、L4、L5，并声明 L3+ 当前 not-authorized。
- [ ] `not_authorized_actions` 至少覆盖 15 项：credential_read、login、connect、account/cash/position/order/fill query、submit、cancel、simulation/live、provider_fetch、lake_write、catalog_publish。
- [ ] 敏感字段分类至少覆盖 token、secret、password、passwd、cookie、session、private_key、account_id、broker_account、real_account、trade_password、credential。
- [ ] LLD 必须声明所有真实 runtime 行为在无逐 run 授权时 fail-closed。
- [ ] 任何输出证据不得包含真实凭据值、账号值、session、cookie 或 private key。
- [ ] `implementation_allowed=false until CP5 approved` 保持成立。

## 阻塞说明

无。当前阻塞只适用于真实 runtime，非 L2 离线设计。
