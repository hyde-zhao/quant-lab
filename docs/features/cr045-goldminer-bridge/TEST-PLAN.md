---
status: draft-for-cp4
version: "1.0"
feature_id: "FEAT-CR045-GOLDMINER-BRIDGE"
source_design: "docs/features/cr045-goldminer-bridge/DESIGN.md"
---

# CR045 Feature Test Plan

## 测试范围

| Scope ID | 覆盖内容 | 来源 Story / Scenario | 测试层级 | 自动化状态 |
|---|---|---|---|---|
| TP-SCOPE-01 | Bridge health skeleton 返回 fixture/blocked 状态，且 `runtime_started=false`。 | CR045-S02 / UC-CR045-01 | unit / fixture | planned-after-CP5 |
| TP-SCOPE-02 | Capabilities skeleton 返回 `real_broker_enabled=false`、`readonly_probe_ready=false`、`simulation_ready=false`、`live_ready=false`。 | CR045-S02 / UC-CR045-02 | unit / fixture | planned-after-CP5 |
| TP-SCOPE-03 | WSL / Linux client 在无 runtime 时只做 fixture transport / network precheck，不启动或连接真实 bridge。 | CR045-S03 | unit / static | planned-after-CP5 |
| TP-SCOPE-04 | Readonly probe skeleton 在 L4 未授权时返回 blocked，且无 cash/position/order/fill/account state 数据。 | CR045-S04 / UC-CR045-03 | unit / fixture | planned-after-CP5 |
| TP-SCOPE-05 | Redaction and no-operation evidence 覆盖敏感字段类别、artifact scan、operation counts 全 0。 | CR045-S05 | static / fixture | planned-after-CP5 |
| TP-SCOPE-06 | Runbook 明确 L3/L4/L5 后续 gate 和 CP8 skeleton-ready 关闭语义。 | CR045-S06 / UC-CR045-04 | manual review | planned-for-CP5/CP8 |

## 风险驱动测试

| Risk ID | 风险 | 测试方式 | 证据 | 未覆盖原因 |
|---|---|---|---|---|
| R-CR045-FD-01 | CP3/CP5 被误读为运行授权。 | Review runbook、Story dev_gate、capabilities flags。 | CP5/CP7 checklist。 | 当前不运行真实 runtime。 |
| R-CR045-FD-02 | token/account_id/session/cookie/private key 泄漏。 | Artifact static scan；fixture negative cases。 | Scan summary；violations count must be 0。 | 不读取 `.env` 或任何凭据材料。 |
| R-CR045-FD-03 | WSL / Linux direct SDK import 或真实 SDK call。 | Static import/call scan for `gm` / `gmtrade` and broker runtime calls。 | CP7 static validation。 | L2 不允许 runtime import。 |
| R-CR045-FD-04 | Readonly skeleton 被误声明为 real-readonly-verified。 | Assert `real_readonly_verified=false` and blocked reason exists。 | Fixture tests and report wording review。 | 真实 readonly 需要 L4。 |
| R-CR045-FD-05 | Provider/lake/publish 误进入验证。 | Static command/path review。 | CP7 report。 | 当前禁止 provider fetch、lake write、catalog publish。 |

## 权限 / 安全 / 失败路径

| Case ID | 触发条件 | 期望行为 | 测试入口 |
|---|---|---|---|
| TP-SEC-01 | 请求、fixture、日志或文档中出现 token/account_id/password/session/cookie/private_key 等真实值。 | blocked 或 redacted；不得保存原值；CP7 FAIL / NEEDS_REWORK。 | CR045-S05 static scan。 |
| TP-SEC-02 | capabilities 中出现 `simulation_ready=true`、`live_ready=true` 或 `real_broker_enabled=true`。 | 测试失败；不允许进入 CP8。 | CR045-S02 fixture assertions。 |
| TP-SEC-03 | action 不在 `health`、`capabilities`、`readonly_probe_skeleton` allowlist。 | 返回 blocked，reason=`operation_not_whitelisted`。 | CR045-S04 negative fixture tests。 |
| TP-SEC-04 | L4 未授权但请求真实 cash/position/order/fill/account state。 | 返回 blocked，reason=`goldminer_readonly_query_not_authorized` 或 `per_run_authorization_missing`。 | CR045-S04 fixture tests。 |
| TP-SEC-05 | 任何 forbidden operation counter 非 0。 | CP6/CP7 FAIL；不得宣称 skeleton-ready。 | CR045-S05 no-operation validation。 |
| TP-SEC-06 | 实现或测试尝试启动 Windows bridge runtime、登录/连接 Goldminer。 | 阻断，交回 meta-po runtime_authorization gate。 | CP6/CP7 review。 |

## 手工验收

| Check ID | 操作 | 期望结果 | 责任方 |
|---|---|---|---|
| MAN-CR045-01 | 审查 Story 卡片和 CP5 设计证据。 | 每个 Story 有 `feature_design_refs`、`lld_policy`、依赖、file owner、dev_gate 和不授权边界。 | meta-po / user at CP5 |
| MAN-CR045-02 | 审查 runbook / release wording。 | 明确 CP5/CP8 approve 不授权 L3/L4/L5，不宣称 `real-readonly-verified`。 | meta-po / meta-qa |
| MAN-CR045-03 | 审查后续授权入口。 | L3/L4/L5 只能通过 meta-po 独立人工 gate 或新 CR。 | meta-po |
