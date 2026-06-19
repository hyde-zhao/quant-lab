---
status: "confirmed"
version: "1.0"
source_cr: "CR-092"
parent_cr: "CR-091"
owner: "host-orchestrator"
created_at: "2026-06-18T16:45:00+08:00"
confirmed: true
confirmed_by: "user"
confirmed_at: "2026-06-18T16:55:00+08:00"
validation_mode: "design-and-evidence-review-only"
---

# CR092 Real QMT Readonly Runtime Smoke TEST-PLAN

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.1 | 2026-06-18 | host-orchestrator | 回填 CP5 approved，并进入 CP6 manual guide / evidence template / static checker 实现。 |
| 1.0 | 2026-06-18 | host-orchestrator | 初始 TEST-PLAN，覆盖 CP5 readiness、模拟账户 evidence 审查、敏感字段拒收、NAS / order-write 分流和 runtime 未授权边界。 |

## 1. 测试目标

验证 CR092 CP5 设计证据是否足以进入后续 readiness / manual guide 准备，同时确认本轮不执行真实 runtime。

## 2. 范围

### In Scope

- LLD 完整性和 HLD 一致性检查。
- Authorization Brief 字段完整性检查。
- Manual Readonly Smoke Guide 的输入 / 输出合同检查。
- 模拟账户 evidence 合同检查。
- 敏感字段和越权路径拒收规则检查。
- NAS / order-write / ledger hygiene 分流检查。

### Out of Scope

- 启动、连接、安装或运行 QMT / MiniQMT / XtQuant / gateway / runner。
- 访问、列取、读取、复制、拉取、写入、发布或删除 NAS。
- 读取 `.env`、凭据、真实账户、真实资金 / 持仓 / 委托 / 成交或未指定日志。
- submit / cancel、buy / sell。
- simulation / live。
- provider fetch、lake write、catalog publish。

## 3. 测试矩阵

| 测试 ID | 场景 | 输入 | 验证步骤 | 预期结果 | 类型 | 证据 |
|---|---|---|---|---|---|---|
| TP-CR092-01 | LLD 完整性 | LLD 文件 | 检查 14 章节、DoD、OPEN / Spike | PASS | static-review | `process/stories/CR092-REAL-QMT-READONLY-RUNTIME-SMOKE-LLD.md` |
| TP-CR092-02 | HLD 一致性 | HLD + LLD | 核对方案 A、模拟账户 evidence、NAS 分流 | PASS | static-review | HLD / LLD |
| TP-CR092-03 | Authorization Brief 字段 | run_id / account_mode / scope / forbidden list | 核对必填字段 | PASS | contract-review | CP5 checkpoint |
| TP-CR092-04 | 模拟账户 evidence 接受 | 用户明确提供 `account_mode=simulated` evidence | 检查字段白名单 | accepted | evidence-review | future evidence |
| TP-CR092-05 | 凭据拒收 | `.env` / token / credential 字段 | 检查拒收规则 | rejected | security-review | future evidence |
| TP-CR092-06 | 真实账户拒收 | real_account / live / real funds 字段 | 检查拒收规则 | rejected | security-review | future evidence |
| TP-CR092-07 | NAS 分流 | NAS path / pull / publish 请求 | 检查 classifier | route to CR091-FU-02 | governance-review | CP5 checkpoint |
| TP-CR092-08 | order-write 分流 | submit / cancel / buy / sell 请求 | 检查 classifier | route to CR091-FU-03 | governance-review | CP5 checkpoint |
| TP-CR092-09 | runtime 未授权 | 无逐 run runtime authorization | 检查执行门禁 | blocked | gate-review | CP5 checkpoint |

## 4. Evidence 合同

允许读取的 evidence 必须满足：

- 用户明确给出路径或直接粘贴内容。
- `account_mode` 为 `simulated`，或内容被用户声明为模拟账户测试证据。
- 不包含 `.env`、凭据、token、真实账户、真实资金、真实持仓、真实委托、真实成交、NAS 路径或未指定原始日志。

建议字段：

```yaml
run_id: "cr092-smoke-YYYYMMDD-HHMM"
account_mode: "simulated"
scope:
  - "health"
  - "capabilities"
  - "query_positions_readonly"
health_status: "PASS|FAIL|N/A"
capabilities_status: "PASS|FAIL|N/A"
query_positions_status: "PASS|FAIL|N/A"
redaction_status: "PASS|FAIL"
forbidden_counters:
  nas_access: 0
  credential_read: 0
  real_account_read: 0
  submit_cancel: 0
  simulation_live: 0
  provider_lake_publish: 0
notes: ""
```

## 5. 敏感字段拒收规则

| 信号 | 处理 | 路由 |
|---|---|---|
| `.env` / token / password / secret / credential | 立即拒收，停止读取 | security gate |
| real_account / live / real funds / real position / real order / real fill | 立即拒收 | security gate |
| NAS path / NAS pull / NAS publish | 不在 CR092 执行 | CR091-FU-02 |
| submit / cancel / buy / sell | 不在 CR092 执行 | CR091-FU-03 |
| provider fetch / lake write / catalog publish | 不在 CR092 执行 | new CR 或 follow-up |

## 6. 通过条件

- CP5 自动预检 PASS。
- LLD / TEST-PLAN 与 HLD 的方案 A 一致。
- DQ-CP5-CR092-01..06 均由用户确认或修改后重提。
- 不授权项在 checkpoint 和 launch message 中一致。
- 不执行任何真实 runtime、NAS、凭据或交易写动作。

## 7. 失败 / 回退

| 失败类型 | 处理 |
|---|---|
| CP5 设计缺口 | 修改 LLD / TEST-PLAN 后重提 CP5。 |
| 用户拒绝模拟账户 evidence 读取边界 | 回退到只读脱敏 summary 模式。 |
| 用户要求 NAS | 启动或等待 CR091-FU-02。 |
| 用户要求 order-write | 启动或等待 CR091-FU-03。 |
| 用户要求真实 runtime | 另起逐 run runtime authorization gate。 |
