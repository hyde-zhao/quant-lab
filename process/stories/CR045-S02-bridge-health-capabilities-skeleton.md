---
story_id: "CR045-S02"
title: "Bridge Health Capabilities Skeleton"
story_slug: "bridge-health-capabilities-skeleton"
status: "ready-for-verification"
priority: "P0"
wave: "W2"
implementation_allowed: true
implementation_allowed_until: "CP5 approved at 2026-06-11T23:16:11+08:00; L2 skeleton / fixture / static only"
depends_on:
  - "CR045-S01"
dependency_contracts:
  - upstream_story: "CR045-S01"
    type: "contract"
    required_for: "authorization, hard-off, zero secret custody and not-authorized baseline"
feature_design_refs:
  - "docs/features/cr045-goldminer-bridge/DESIGN.md#api--接口设计"
  - "docs/features/cr045-goldminer-bridge/TEST-PLAN.md#测试范围"
  - "docs/features/cr045-goldminer-bridge/TASKS.md#cr045-s02"
lld_policy:
  required_level: "full-lld"
  trigger_reasons:
    - "cross-module-contract"
    - "external-interface"
    - "data-model"
  rationale: "health/capabilities 是 bridge API 共享合同，必须完整定义 schema、false flags、blocked reason 和 fixture 行为。"
  waiver_reason: ""
  revisit_condition: "任何真实 runtime health check、SDK import 或 Goldminer connection 需求出现时，暂停并发起 L3 授权。"
  evidence_path: "process/stories/CR045-S02-bridge-health-capabilities-skeleton-LLD.md"
file_ownership:
  primary:
    - "process/stories/CR045-S02-bridge-health-capabilities-skeleton.md"
    - "process/stories/CR045-S02-bridge-health-capabilities-skeleton-LLD.md"
    - "engine/goldminer_bridge_contract.py"
    - "tests/test_cr045_goldminer_bridge_contract.py"
  shared:
    - "docs/features/cr045-goldminer-bridge/DESIGN.md"
  merge_owner: "CR045-S02"
  forbidden:
    - ".env"
    - ".env.*"
    - "engine/goldminer_bridge_client.py"
lld_gate:
  required_inputs:
    - "CR045-S01 design evidence"
    - "docs/features/cr045-goldminer-bridge/DESIGN.md"
  design_evidence_type: "full-lld"
  design_evidence_path: "process/stories/CR045-S02-bridge-health-capabilities-skeleton-LLD.md"
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

# CR045-S02 Bridge Health Capabilities Skeleton

## 目标

定义 bridge L2 的 `health` 和 `capabilities` skeleton 合同，使未来实现只能返回 fixture/blocked 状态，不启动 Windows runtime，不导入真实 SDK，不声明真实只读、simulation 或 live 能力。

## 开发上下文（dev_context）

- 输入文件：S01 设计证据、`docs/features/cr045-goldminer-bridge/DESIGN.md`、`docs/design/ARCHITECTURE-DECISION-CR045.md`。
- 输出文件：`process/stories/CR045-S02-bridge-health-capabilities-skeleton-LLD.md`；未来 CP6 可创建 `engine/goldminer_bridge_contract.py` 和 `tests/test_cr045_goldminer_bridge_contract.py`。
- 接口约定：`BridgeHealth` 必须包含 `runtime_started=false`、`not_authorization=true`；`BridgeCapabilities` 必须包含 `real_broker_enabled=false`、`readonly_probe_ready=false`、`simulation_ready=false`、`live_ready=false`。
- 设计约束：不启动 Windows bridge runtime；不导入或调用 `gm` / `gmtrade`；不读取 endpoint、token、account_id。
- 平台目标：JSON-safe schema；fixture/static validation；Python 3.11 + uv。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR045-S01 | contract | S01 授权边界已声明 | CP5 approved + S01 design evidence confirmed | S02 消费 S01 hard-off 和不授权合同。 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `engine/goldminer_bridge_contract.py` | CR045-S02 future primary owner。 |
| primary | `tests/test_cr045_goldminer_bridge_contract.py` | CR045-S02 future primary owner。 |
| shared | `docs/features/cr045-goldminer-bridge/DESIGN.md` | 只读消费。 |
| forbidden | `.env`、`.env.*`、`engine/goldminer_bridge_client.py` | 不触碰凭据，不抢占 S03 client。 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR045-S02-T1 | 设计 | `CR045-S02-...-LLD.md` | 定义 `BridgeHealth` schema 和 runtime-not-started response。 |
| CR045-S02-T2 | 设计 | `CR045-S02-...-LLD.md` | 定义 `BridgeCapabilities` false flags 和 allowlist actions。 |
| CR045-S02-T3 | 设计 | `CR045-S02-...-LLD.md` | 定义 fixture tests 和 static assertions。 |

## 技术说明

本 Story 需要 `full-lld`。CP4 不写实现或 LLD。

## 验证上下文（validation_context）

| 项目 | 内容 |
|---|---|
| validation_mode | fixture-only + static-only |
| 验证入口 | CP6 后 `uv run --python 3.11 pytest -q tests/test_cr045_goldminer_bridge_contract.py`；CP7 artifact scan。 |
| 关键验证场景 | health 不启动 runtime；capabilities false flags；allowlist 仅三类 L2 actions。 |
| 禁止验证方式 | 不连接 Windows bridge，不登录 Goldminer，不读取凭据，不查询账户。 |

## 量化验收标准（acceptance_criteria）

- [ ] `BridgeHealth` schema 至少包含 `schema_version`、`status`、`runtime_started=false`、`not_authorization=true`、`reason`。
- [ ] `BridgeCapabilities` schema 至少包含 `real_broker_enabled=false`、`readonly_probe_ready=false`、`simulation_ready=false`、`live_ready=false`。
- [ ] L2 allowlist 只包含 `health`、`capabilities`、`readonly_probe_skeleton` 三类 action。
- [ ] 任何 health/capabilities fixture 都不得包含 token/account_id、account state、cash、position、order、fill 数据。
- [ ] 不得出现 `gm` / `gmtrade` runtime import 或 SDK call。
- [ ] dev_gate 在 CP5 approved 前保持 `implementation_allowed=false`。

## 阻塞说明

无 CP4 阻塞。真实 bridge health 属于 L3，当前不授权。
