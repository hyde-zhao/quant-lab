---
doc_id: "CR098-QMT-RUNNER-READONLY-GATEWAY-INTEGRATION-HLD"
cr_id: "CR-098"
status: "draft-pending-cp3-approval"
owner: "host-orchestrator"
created_at: "2026-06-19T12:00:19+08:00"
source_checkpoint: "process/checkpoints/CP2-CR098-QMT-RUNNER-READONLY-INTEGRATION-SCOPE-REVIEW.md"
---

# CR098 QMT Runner Readonly Gateway Integration HLD

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 0.1 | 2026-06-19 | host-orchestrator | 初版 HLD，覆盖 runner-owned readonly gateway adapter、env contract、evidence、风险和 CP3 决策项。 |

## 1. 问题定义

CR091 已交付离线 strategy runner 合同、fake readonly gateway 和脱敏 evidence；CR097 已证明 Windows gateway 的真实只读链路可用。当前缺口是：runner 还没有以受控方式消费真实 gateway 的只读能力，因此还不能证明“runner 能通过 gateway 完成 health / capabilities / query_positions_readonly，并输出 redacted evidence”。

CR098 要解决这个集成缺口，同时保持最小权限：设计批准不等于运行授权，runner 默认仍为 offline/fake，真实 gateway 调用只能在后续逐 run 授权下执行。

## 2. 目标

| 目标 ID | 目标 | 可验证标准 |
|---|---|---|
| G-CR098-01 | runner 支持 readonly gateway adapter facade | adapter 支持 `health`、`capabilities`、`query_positions_readonly` 三类调用；其他 endpoint blocked |
| G-CR098-02 | 默认离线安全 | 未显式 runtime 授权时真实 HTTP call、secret read、account query 均为 0 |
| G-CR098-03 | evidence 脱敏 | 输出 `position_count`、`positions_digest`、`items_redacted_count`、`raw_payload_emitted=false` 和 forbidden counters |
| G-CR098-04 | runtime 授权分离 | CP3/CP5 approve 均不授权读取 HMAC env 或执行 runner runtime；CP7 runtime smoke 另行逐 run 授权 |

## 3. 非目标

- 不实现 submit / cancel、buy / sell、simulation / live。
- 不读取 Windows `.env`、QMT 账号原文、资金、持仓明细原文、委托、成交或原始日志。
- 不做 NAS package exchange / pull / publish。
- 不恢复 CR089 或 CR020 gateway route。
- 不把 CR097 的 HMAC env 作为默认可读配置。

## 4. Architecture Gray Areas

| 灰区 ID | 决策点 | 推荐 | 备选 | 影响面 |
|---|---|---|---|---|
| AGA-CR098-01 | adapter 放在哪里 | 扩展 runner-owned readonly facade | 新 CLI / 直接 XtQuant | 文件 owner、测试、回归 |
| AGA-CR098-02 | env 如何进入 | 显式 env path + per-run authorization | 隐式默认路径 | secret 暴露面 |
| AGA-CR098-03 | evidence schema | CR098 runtime summary + CR091 counters | 保存 CLI 原文 | 脱敏和审计 |
| AGA-CR098-04 | NAS 是否合并 | 不合并 | 合并 NAS | 权限边界 |

讨论日志：`process/discussions/CP3-CR098-HLD-DISCUSSION-LOG.md`。

## 5. 候选方案对比

| 方案 | 描述 | 优点 | 缺点 | 结论 |
|---|---|---|---|---|
| A | runner-owned readonly gateway adapter facade | 与 CR091 runner 结构一致；fake/real 可注入；默认安全；容易测试 | 需要新增 adapter contract 和 evidence fields | 推荐 |
| B | 独立 runtime runner CLI，绕过现有 wrapper | 不改现有 wrapper | runner 集成证明弱；重复 qmt client / evidence 逻辑 | 不推荐 |
| C | runner 直接 import XtQuant | 调用链短 | Windows-only、session/account 风险高，易扩大到交易写 | 本轮禁止 |
| D | 合并 NAS package exchange | 可覆盖取包 | 范围膨胀，触碰 NAS 权限 | 不推荐 |

## 6. 推荐架构

```text
Strategy Package / Fixture
        |
        v
CR091 Strategy Runner
        |
        v
ReadonlyGatewayAdapterFacade
   |                    |
   | fake/offline       | real/rest, per-run authorized only
   v                    v
FakeReadonlyQmtTransport   QmtClient + StdlibQmtRestTransport + HMAC headers
                             |
                             v
                     Windows QMT Gateway
                             |
                             v
                health / capabilities / query_positions
                             |
                             v
             CR098 Redacted Evidence under ~/.quant-lab
```

## 7. 模块职责

| 模块 | 职责 | 必须保持 | 禁止 |
|---|---|---|---|
| `trading/strategy_runner/readonly_gateway.py` | runner readonly facade；fake/real adapter 入口 | 默认 fake/offline；endpoint allowlist | 直接 import XtQuant |
| `trading/qmt_client.py` | HTTP client、typed response、transport abstraction | HMAC provider 注入；redaction metadata | 隐式读取 env |
| `trading/qmt_runtime.py` | Windows gateway runtime / stdlib transport | 仅 runtime CLI 显式启用 | runner 侧启动 gateway |
| `trading/strategy_runner/evidence.py` | runner evidence 汇总 | forbidden counters、redaction assurance | 保存原始持仓 |
| `tests/test_cr098_*` | contract / regression tests | fake default、real transport fixture、blocked endpoints | 访问真实 gateway |

## 8. 数据与配置流

| 数据 / 配置 | 来源 | 去向 | 规则 |
|---|---|---|---|
| `QMT_GATEWAY_HOST/PORT` | per-run minimal env | runner real adapter | 只在授权 run 读取 |
| `QMT_CLIENT_ID/SECRET` | per-run minimal env | HMAC header provider | 不落日志、不落 evidence |
| query result | Windows gateway | runner evidence | 只保留脱敏摘要 |
| forbidden counters | client / gateway / evidence | CP7 / evidence | 必须区分 allowed readonly counters 和 forbidden counters |

## 9. 关键流程

### 9.1 离线默认流程

1. runner 创建 `ReadonlyGatewayClient`。
2. 未传真实 transport 和 auth provider。
3. 使用 fake transport 返回 fixture result。
4. evidence 证明 `gateway_socket_open=0`、`credential_read=0`、`account_query=0`。

### 9.2 后续真实只读流程

1. 用户逐 run 授权读取最小 HMAC env。
2. runner real adapter 构造 `QmtClient` + `StdlibQmtRestTransport` + HMAC provider。
3. runner 调用 `health`、`capabilities`、`query_positions_readonly`。
4. 只保存 redacted evidence。
5. 如返回未脱敏结构或 forbidden counter 非 0，立即 BLOCKED。

## 10. 非功能设计

| 属性 | 设计 |
|---|---|
| 安全 | 默认不读 secret；真实 env path 必须显式传入并逐 run 授权 |
| 可测试性 | fake transport 和 injected transport 全覆盖；真实 HTTP 不进入默认 tests |
| 可维护性 | adapter facade 隔离 runner 与 qmt runtime；不让 runner 依赖 Windows-only XtQuant |
| 可观测性 | evidence 记录 run_id、request_id、endpoint status、digest、forbidden counters |
| 失败路径 | auth/env/session/redaction/transport 任一失败均返回 blocked，不做 fallback raw output |

## 11. Use Case → Architecture Traceability

| Use Case / 场景 | 架构对象 | 验证方式 |
|---|---|---|
| runner 离线策略验证 | fake readonly adapter | existing CR091 tests |
| runner 只读 gateway health | real readonly adapter | CP7 runtime smoke with authorization |
| runner 查询空持仓 / 非空持仓脱敏 | evidence summary | fixture tests + optional runtime smoke |
| 用户要求 NAS | follow-up routing | blocked / route to CR091-FU-02 |
| 用户要求 order-write | follow-up routing | blocked / route to order-write CR |

## 12. 关键场景模拟

| 场景 | 输入 | 预期路径 | 结果 |
|---|---|---|---|
| SIM-CR098-01 默认离线 runner | 无 runtime env | fake transport -> evidence | PASS，真实调用为 0 |
| SIM-CR098-02 授权真实只读 smoke | explicit env + authorization | real adapter -> gateway -> redacted evidence | PASS，保存脱敏摘要 |
| SIM-CR098-03 未授权 secret read | runner 尝试默认 env | blocked | PASS，credential_read 仍为 0 |
| SIM-CR098-04 order endpoint | `submit_order` | blocked_scope_denied | PASS，不触发 gateway |

## 13. 风险

| 风险 ID | 风险 | 等级 | 缓解 |
|---|---|---|---|
| R-CR098-01 | runner real adapter 被误读为交易能力 | HIGH | endpoint allowlist + `operation_authorized=false` + no order-write tests |
| R-CR098-02 | HMAC secret 泄露 | HIGH | per-run env authorization、不落 evidence、diff scan |
| R-CR098-03 | 原始持仓泄露 | HIGH | redaction scan，raw output blocks CP7 |
| R-CR098-04 | NAS/order-write 范围膨胀 | MEDIUM | follow-up tracking 分流 |

## 14. ADR 候选

| ADR | 决策 | 状态 |
|---|---|---|
| ADR-CR098-01 | runner-owned readonly gateway adapter facade | proposed |
| ADR-CR098-02 | per-run explicit env path，禁止隐式 secret read | proposed |
| ADR-CR098-03 | CR098 专用 redacted runtime evidence summary | proposed |
| ADR-CR098-04 | NAS/order-write 不并入 CR098 | proposed |

## 15. 分阶段落地建议

| 阶段 | 内容 | 退出条件 |
|---|---|---|
| CP3 | HLD 确认 | 用户 approve HLD 和 DQ-CP3-CR098-* |
| CP5 | LLD / TEST-PLAN / TASKS | 文件 owner、接口、测试、runtime authorization manifest 冻结 |
| CP6 | 实现 | adapter / evidence / tests 完成 |
| CP7 | 验证 | offline tests + optional real runner smoke with new authorization |
| CP8 | 收尾 | release context 和风险接受 |

## 16. HLD 拆分判断

| 判定项 | 结论 | 说明 |
|---|---|---|
| 核心产物数量 | 1 | CR098 只设计 runner readonly integration |
| Story 数量 | 预计 3-4 | 不超过拆分阈值 |
| ADR 聚类 | 单一聚类 | adapter / env / evidence / boundary 强耦合 |
| 结论 | 不拆分 | 单份 HLD 足够 |

## 17. CP3 待决策项

| 决策 ID | 决策类型 | 问题 | 推荐 |
|---|---|---|---|
| DQ-CP3-CR098-01 | architecture | 是否采用 runner-owned readonly gateway adapter facade？ | 采用 |
| DQ-CP3-CR098-02 | security | 是否确认 per-run explicit env path，禁止隐式 secret read？ | 确认 |
| DQ-CP3-CR098-03 | implementation | 是否允许 CP5 设计 adapter / evidence / tests，但 CP5 前不写代码？ | 允许 |
| DQ-CP3-CR098-04 | runtime_authorization | CP3 approve 是否授权真实 runner runtime？ | 不授权 |
| DQ-CP3-CR098-05 | follow_up_tracking | NAS/order-write/非空复测是否继续独立？ | 独立 |

## 18. 自审

| 检查项 | 结论 |
|---|---|
| 候选方案 >= 2 | PASS |
| Architecture Gray Areas 已记录 | PASS |
| 场景模拟通过 | PASS |
| 不授权边界明确 | PASS |
| HLD 拆分判断完成 | PASS |
