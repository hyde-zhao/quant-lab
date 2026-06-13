---
story_id: "CR045-S01"
title: "Windows Bridge Security Boundary"
story_slug: "windows-bridge-security-boundary"
status: "ready-for-verification"
priority: "P0"
wave: "W1"
implementation_allowed: true
implementation_allowed_until: "CP5 approved at 2026-06-11T23:16:11+08:00; L2 skeleton / fixture / static only"
depends_on: []
dependency_contracts: []
feature_design_refs:
  - "docs/features/cr045-goldminer-bridge/DESIGN.md#权限与安全"
  - "docs/features/cr045-goldminer-bridge/TEST-PLAN.md#权限--安全--失败路径"
  - "docs/features/cr045-goldminer-bridge/TASKS.md#cr045-s01"
lld_policy:
  required_level: "full-lld"
  trigger_reasons:
    - "security"
    - "permission"
    - "runtime_authorization"
    - "shared-story-boundary"
  rationale: "Windows bridge 的授权层级、凭据驻留、hard-off kill switch 和不授权边界是 S02-S06 的根合同。"
  waiver_reason: ""
  revisit_condition: "任何凭据、账号、session、cookie、private key、真实账户标识或 Windows runtime 需要读取/启动时，暂停并交回 meta-po 发起 L3+ 授权。"
  evidence_path: "process/stories/CR045-S01-windows-bridge-security-boundary-LLD.md"
file_ownership:
  primary:
    - "process/stories/CR045-S01-windows-bridge-security-boundary.md"
    - "process/stories/CR045-S01-windows-bridge-security-boundary-LLD.md"
  shared:
    - "docs/features/cr045-goldminer-bridge/DESIGN.md"
  merge_owner: "CR045-S01"
  forbidden:
    - ".env"
    - ".env.*"
    - "engine/goldminer_bridge_contract.py"
    - "engine/goldminer_bridge_client.py"
    - "engine/goldminer_bridge_probe.py"
lld_gate:
  required_inputs:
    - "process/checkpoints/CP3-CR045-HLD-REVIEW.md"
    - "docs/design/ARCHITECTURE-DECISION-CR045.md"
    - "docs/design/FEATURE-DESIGN-MATRIX-CR045.md"
    - "docs/features/cr045-goldminer-bridge/DESIGN.md"
  design_evidence_type: "full-lld"
  design_evidence_path: "process/stories/CR045-S01-windows-bridge-security-boundary-LLD.md"
  status: "confirmed"
dev_gate:
  implementation_allowed: true
  allowed_after: "CP5 approved"
  design_evidence_confirmed: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  real_runtime_authorized: false
---

# CR045-S01 Windows Bridge Security Boundary

## 目标

冻结 CR045 的 Windows bridge 安全边界：Windows trading PC 是唯一未来 Goldminer SDK/runtime/execution boundary；WSL / Linux 只做研究、回测、组合生成、order intent 和 bridge client；当前只允许 L2 skeleton / fixture / static validation。

## 开发上下文（dev_context）

- 输入文件：`process/context/CP3-CR045-DESIGN-CONTEXT.yaml`、`process/checkpoints/CP3-CR045-HLD-REVIEW.md`、`docs/design/HLD-CR045-GOLDMINER-WINDOWS-BRIDGE.md`、`docs/design/ARCHITECTURE-DECISION-CR045.md`、`docs/features/cr045-goldminer-bridge/DESIGN.md`。
- 输出文件：`process/stories/CR045-S01-windows-bridge-security-boundary-LLD.md`；本 Story 卡片。
- 接口约定：定义 L1/L2/L3/L4/L5 authorization layer、not-authorized action list、zero secret custody、hard-off kill switch、blocked reason taxonomy。
- 设计约束：不读取 `.env`、token、account_id、账号、密码、session、cookie、private key；不启动 Windows bridge runtime；不登录/连接 Goldminer；不查询账户；不交易；不 simulation/live；不 provider/lake/publish。
- 命名规范：CR045 新增标识使用 `CR045_*` 或 `cr045_*` 前缀；敏感字段输出只能是字段名、规则 ID、`REDACTED` 或 present/count 摘要。
- 平台目标：Python 3.11 + uv；fixture/static only；Windows runtime 仅作为未来边界，不作为当前执行对象。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| N/A | N/A | CP3 approved + Feature DESIGN ready | CP5 approved | S01 是 CR045 设计批次根节点。 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `process/stories/CR045-S01-windows-bridge-security-boundary.md` | CR045-S01 |
| primary | `process/stories/CR045-S01-windows-bridge-security-boundary-LLD.md` | CR045-S01 |
| shared | `docs/features/cr045-goldminer-bridge/DESIGN.md` | 只读消费；不在 CP5 后抢占 Feature 设计。 |
| forbidden | `.env`、`.env.*`、future bridge code files | 当前 Story 不触碰凭据和实现文件。 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR045-S01-T1 | 设计 | `CR045-S01-...-LLD.md` | 定义 L1-L5 授权层级和每层允许/禁止动作。 |
| CR045-S01-T2 | 设计 | `CR045-S01-...-LLD.md` | 定义 zero secret custody、敏感字段类别和 redaction 失败行为。 |
| CR045-S01-T3 | 设计 | `CR045-S01-...-LLD.md` | 定义 hard-off kill switch、blocked reason 和 no-operation 计数要求。 |

## 技术说明

本 Story 需要 `full-lld`。CP4 只定义范围和门控，不在本卡片内展开 LLD。

## 验证上下文（validation_context）

| 项目 | 内容 |
|---|---|
| validation_mode | static-only + review-only |
| 验证入口 | CP5 LLD review；CP7 static scan / fixture tests after implementation。 |
| 关键验证场景 | L3/L4/L5 当前 not-authorized；敏感值泄漏数为 0；真实操作计数为 0。 |
| 禁止验证方式 | 不读取凭据、不启动 runtime、不连接 Goldminer、不查询账户、不下单/撤单、不 simulation/live。 |

## 量化验收标准（acceptance_criteria）

- [ ] LLD 至少覆盖 L1、L2、L3、L4、L5 五层 authorization model。
- [ ] not-authorized list 至少覆盖 credential_read、token/account_id collection、Windows bridge runtime start、Goldminer login/connect、account/cash/position/order/fill query、submit/cancel、simulation/live、provider_fetch、lake_write、catalog_publish。
- [ ] LLD 明确 Windows trading PC 是唯一未来 SDK/runtime/execution boundary，WSL / Linux 不持有 SDK/凭据、不直接连接 Goldminer、不直接下单。
- [ ] 敏感字段分类至少覆盖 token、secret、password、passwd、cookie、session、private_key、account_id、broker_account、real_account、trade_password、credential。
- [ ] `dev_gate.real_runtime_authorized=false`，且实现不得在 CP5 前开始。
- [ ] 任何输出证据不得包含真实凭据值、账号值、session、cookie 或 private key。

## 阻塞说明

无 CP4 阻塞。真实 runtime、凭据或账户查询需求是 L3+ 阻塞，必须另行授权。
