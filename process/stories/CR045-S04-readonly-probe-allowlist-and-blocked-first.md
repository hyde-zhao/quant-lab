---
story_id: "CR045-S04"
title: "Readonly Probe Allowlist and Blocked-First"
story_slug: "readonly-probe-allowlist-and-blocked-first"
status: "ready-for-verification"
priority: "P0"
wave: "W3"
implementation_allowed: true
implementation_allowed_until: "CP5 approved at 2026-06-11T23:16:11+08:00; L2 skeleton / fixture / static only"
depends_on:
  - "CR045-S01"
  - "CR045-S02"
  - "CR045-S03"
dependency_contracts:
  - upstream_story: "CR045-S01"
    type: "contract"
    required_for: "authorization and blocked reasons"
  - upstream_story: "CR045-S02"
    type: "contract"
    required_for: "bridge API schema"
  - upstream_story: "CR045-S03"
    type: "contract"
    required_for: "client request/response semantics"
feature_design_refs:
  - "docs/features/cr045-goldminer-bridge/DESIGN.md#异常失败与降级策略"
  - "docs/features/cr045-goldminer-bridge/TEST-PLAN.md#权限--安全--失败路径"
  - "docs/features/cr045-goldminer-bridge/TASKS.md#cr045-s04"
lld_policy:
  required_level: "full-lld"
  trigger_reasons:
    - "external-interface"
    - "security"
    - "permission"
    - "rollback"
  rationale: "readonly probe 涉及未来账户查询边界；当前必须定义 skeleton-only、allowlist 和 L4 未授权 blocked-first。"
  waiver_reason: ""
  revisit_condition: "用户要求真实 cash/position/order/fill/account state 查询时，停止并发起 L4 readonly probe 授权。"
  evidence_path: "process/stories/CR045-S04-readonly-probe-allowlist-and-blocked-first-LLD.md"
file_ownership:
  primary:
    - "process/stories/CR045-S04-readonly-probe-allowlist-and-blocked-first.md"
    - "process/stories/CR045-S04-readonly-probe-allowlist-and-blocked-first-LLD.md"
    - "engine/goldminer_bridge_probe.py"
    - "tests/test_cr045_goldminer_readonly_probe.py"
  shared:
    - "engine/goldminer_bridge_contract.py"
  merge_owner: "CR045-S04"
  forbidden:
    - ".env"
    - ".env.*"
    - "data/market_data"
    - "catalog"
lld_gate:
  required_inputs:
    - "CR045-S01 design evidence"
    - "CR045-S02 design evidence"
    - "CR045-S03 design evidence"
  design_evidence_type: "full-lld"
  design_evidence_path: "process/stories/CR045-S04-readonly-probe-allowlist-and-blocked-first-LLD.md"
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

# CR045-S04 Readonly Probe Allowlist and Blocked-First

## 目标

定义 readonly probe skeleton 的 allowlist 和 blocked-first response。当前不查询 cash、position、order、fill 或 account state，不声明 real-readonly-verified。

## 开发上下文（dev_context）

- 输入文件：S01-S03 设计证据、Feature DESIGN / TEST-PLAN / TASKS、ADR-CR045-002/004/007。
- 输出文件：`process/stories/CR045-S04-readonly-probe-allowlist-and-blocked-first-LLD.md`；未来 CP6 可创建 `engine/goldminer_bridge_probe.py` 和 `tests/test_cr045_goldminer_readonly_probe.py`。
- 接口约定：`ReadonlyProbeRequest` 只表达 skeleton probe；`ReadonlyProbeResponse` 在 L4 未授权时必须 `status=blocked`、`real_readonly_verified=false`、operation counts 全 0。
- 设计约束：不触发账户/资金/持仓/委托/成交查询；不读取真实账号；不访问 provider/lake/catalog。
- 平台目标：fixture-only / static-only；后续 L4 才能真实 probe。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR045-S01 | contract | 授权和 blocked reason declared | CP5 approved + confirmed | 决定 L4 not-authorized。 |
| CR045-S02 | contract | API schema declared | CP5 approved + confirmed | 消费 bridge contract。 |
| CR045-S03 | contract | client request semantics declared | CP5 approved + confirmed | 消费 client request shape。 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `engine/goldminer_bridge_probe.py` | CR045-S04 future primary owner。 |
| primary | `tests/test_cr045_goldminer_readonly_probe.py` | CR045-S04 future primary owner。 |
| shared | `engine/goldminer_bridge_contract.py` | 消费 S02 contract；必要修改由 S04 与 S02 协调。 |
| forbidden | `.env`、`.env.*`、`data/market_data`、`catalog` | 禁止真实数据、provider/lake/publish 路径。 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR045-S04-T1 | 设计 | `CR045-S04-...-LLD.md` | 定义 readonly probe skeleton request/response schema。 |
| CR045-S04-T2 | 设计 | `CR045-S04-...-LLD.md` | 定义 L4 未授权 blocked reason 和 allowlist decision table。 |
| CR045-S04-T3 | 设计 | `CR045-S04-...-LLD.md` | 定义 negative fixture cases：真实查询请求必须 blocked。 |

## 技术说明

本 Story 需要 `full-lld`。CP4 不写实现或 LLD。

## 验证上下文（validation_context）

| 项目 | 内容 |
|---|---|
| validation_mode | fixture-only + static-only |
| 验证入口 | CP6 后 `uv run --python 3.11 pytest -q tests/test_cr045_goldminer_readonly_probe.py`；CP7 artifact scan。 |
| 关键验证场景 | L4 missing authorization；probe kind allowed but real query blocked；real_readonly_verified=false。 |
| 禁止验证方式 | 不查询 cash/position/order/fill/account state，不连接 Goldminer。 |

## 量化验收标准（acceptance_criteria）

- [ ] `ReadonlyProbeRequest` 不得包含真实 token/account_id、account state、broker session 或真实 endpoint。
- [ ] `ReadonlyProbeResponse` 在当前 L2 下必须 `status=blocked` 且 `real_readonly_verified=false`。
- [ ] blocked reason 至少覆盖 `per_run_authorization_missing`、`goldminer_readonly_query_not_authorized`、`operation_not_whitelisted`、`sensitive_material_present`。
- [ ] cash/position/order/fill/account state 的真实查询请求必须被 negative fixture 设计覆盖。
- [ ] forbidden operation counters 必须保持全 0。
- [ ] 不得把 readonly skeleton 写成 `real-readonly-verified`。

## 阻塞说明

无 CP4 阻塞。真实 readonly probe 属于 L4，当前不授权。
