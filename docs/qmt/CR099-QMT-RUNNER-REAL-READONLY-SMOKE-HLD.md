---
doc_id: "CR099-QMT-RUNNER-REAL-READONLY-SMOKE-HLD"
cr_id: "CR-099"
status: "approved-cp3-pending-cp5"
owner: "host-orchestrator"
created_at: "2026-06-19T15:54:07+08:00"
source_checkpoint: "process/checkpoints/CP2-CR099-RUNNER-REAL-READONLY-SMOKE-SCOPE-REVIEW.md"
---

# CR099 QMT Runner Real Readonly Smoke HLD

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 0.1 | 2026-06-19 | host-orchestrator | 初版 HLD，覆盖 runner 真实只读 smoke 架构、逐 run 授权、脱敏 evidence、失败路径和 CP3 决策项。 |
| 0.2 | 2026-06-19 | host-orchestrator | 用户回复“同意”批准 CP3；进入 CP5 design readiness，仍不授权 runtime。 |

## 1. 问题定义

CR098 已证明 runner readonly gateway integration 的离线路径可用；CR097 已证明 Windows gateway 的真实只读路径可用。但两者尚未在同一次受控运行里闭环：runner 作为消费方真实调用 Windows gateway 的 `health`、`capabilities` 和 `query_positions_readonly`，并输出可审计、脱敏、不可泄露账户原文的 evidence。

CR099 要解决的是“真实 runner readonly smoke”架构和门禁设计，不是立即运行。CP2 已由用户回复“同意”批准范围与不授权边界；CP3 只冻结架构和后续 CP5 设计输入，仍不授权读取 HMAC secret、读取 Windows `.env`、启动 gateway、执行 runner runtime 或查询账户。

## 2. 目标

| 目标 ID | 目标 | 可验证标准 |
|---|---|---|
| G-CR099-01 | runner 真实消费 Windows gateway readonly path | 逐 run 授权后，runner 通过既有 readonly adapter 依次调用 `health`、`capabilities`、`query_positions_readonly` |
| G-CR099-02 | 每次真实运行都有显式授权 | run contract 包含 `authorization_ref`、`run_id`、host、port、allowlist、endpoint、evidence dir 和中止条件 |
| G-CR099-03 | evidence 只保留脱敏摘要 | evidence 包含 endpoint summary、position_count 桶或计数、digest、`raw_payload_emitted=false`、forbidden counters；不得包含账号、证券代码、数量、资金、委托、成交或日志原文 |
| G-CR099-04 | 默认失败关闭 | 未通过 CP5 或缺少逐 run 授权、client env、gateway、session、redaction gate 时，状态转 blocked / pending-user，不执行真实 run |
| G-CR099-05 | 后续事项继续分流 | 非空持仓复测、交易日复测、NAS、order-write 和 release publish 不并入 CR099 |

## 3. 非目标

- 不实现 submit / cancel、buy / sell、simulation / live。
- 不读取或记录 Windows `.env`、HMAC secret、QMT 账号原文、资金、持仓明细原文、证券代码、委托、成交或原始日志。
- 不启动 gateway、不执行 runner runtime，除非 CP5 后用户提供逐 run 授权。
- 不做 NAS package exchange / pull / publish。
- 不恢复 CR089 或 CR020 gateway route。
- 不把 CR097 的一次性授权复用为 CR099 授权。
- 不要求当前 CR 解决非空账户、交易日或真实下单写路径。

## 4. Architecture Gray Areas

| 灰区 ID | 决策点 | 推荐 | 备选 | 影响面 |
|---|---|---|---|---|
| AGA-CR099-01 | 真实运行由谁执行 | CP5 后按 run contract 由 host-orchestrator 在用户逐 run 授权内执行 runner readonly smoke；若环境不可安全读取，则切换为用户手工 Windows-side 执行并回传脱敏 evidence | 只做离线 reverify；或直接在 Windows 侧绕过 runner | 能否证明 runner integration、权限边界、审计链 |
| AGA-CR099-02 | env / HMAC material 如何进入 | run contract 显式列出 client env 来源、读取方式和授权引用；无授权时不得读取任何 env / secret | 隐式读取默认路径或复用 CR097 env | secret 暴露面、可追溯性 |
| AGA-CR099-03 | evidence schema | CR099 专用 redacted evidence：`run_id`、`authorization_ref`、endpoint summary、position_count 桶 / digest、redaction counters、forbidden counters | 保存完整 CLI 输出或 gateway response | 账户隐私、安全审计 |
| AGA-CR099-04 | 是否合并后续目标 | 不合并；非空持仓、交易日、NAS、order-write 独立 CR | 合并进 CR099 | 范围、授权风险、完成时点 |

讨论日志：`process/discussions/CP3-CR099-HLD-DISCUSSION-LOG.md`。

## 5. 候选方案对比

| 方案 | 描述 | 优点 | 缺点 | 结论 |
|---|---|---|---|---|
| A | 复用 CR098 runner adapter + CR097 gateway pattern，新增 CR099 run contract / authorization_ref / evidence schema | 直接证明 runner 真实消费 gateway；最大化复用已验证组件；授权和 evidence 可审计 | 需要 CP5 细化 run manifest 与 redaction gate | 推荐 |
| B | 用户手工在 Windows 侧执行，并只回传脱敏 evidence | Codex 不触碰 secret / env；适合本机环境不可安全代理时 | 需要用户按步骤执行，自动化程度低 | fallback |
| C | 仅离线 reverify CR098 adapter | 风险最低，不触碰 runtime | 不能关闭真实 runner runtime 风险 | 只在用户暂不授权 runtime 时使用 |
| D | 合并 NAS、order-write、非空复测 | 一次覆盖更多事项 | 权限和范围显著膨胀，可能引入交易写风险 | 本 CR 禁止 |

## 6. 推荐架构

```text
CP5 Run Contract / Per-run Authorization
        |
        v
CR098 Strategy Runner
        |
        v
ReadonlyGatewayAdapterFacade
        |
        v
QmtClient + StdlibQmtRestTransport
        |
        v
Windows QMT Gateway (readonly allowlist only)
        |
        v
health / capabilities / query_positions_readonly
        |
        v
CR099 Redaction Gate
        |
        v
.quant-lab/evidence/qmt/cr099/redacted/<run_id>/
```

核心原则：

- 真实运行入口必须先读取 CP5 run contract，而不是隐式扫描 env、端口或 gateway。
- runner 只能访问 readonly allowlist；任何 submit / cancel / buy / sell endpoint 都必须在 adapter 层和 evidence counter 中保持 0。
- evidence 生成前先做 redaction；原始 response 不落盘、不打印到正式 evidence。
- 运行失败默认保留 blocked / preflight evidence，不尝试扩大权限自愈。

## 7. 模块职责

| 模块 | 职责 | 输入 | 输出 | 禁止行为 |
|---|---|---|---|---|
| CP5 Run Contract | 固化单次运行的授权、参数、allowlist、evidence dir 和中止条件 | CP3 HLD、用户授权文本 | YAML / Markdown run manifest | 不保存 secret 值 |
| Runner Readonly Adapter | 通过统一 facade 调用 readonly gateway | run contract、transport | endpoint result summary | 不调用交易写 endpoint |
| QmtClient / Transport | 按授权连接 Windows gateway | host、port、HMAC env 引用 | HTTP response in memory | 无授权时不得读 env / 发请求 |
| Redaction Gate | 将响应转为脱敏 evidence | in-memory readonly response | redacted JSON / YAML / Markdown evidence | 不落盘 raw payload |
| Verification Check | 校验 schema、forbidden counters、raw leak | redacted evidence | CP6 / CP7 结论 | 不扫描无关目录 |

## 8. 数据与配置流

| 阶段 | 数据 / 配置 | 来源 | 处理规则 |
|---|---|---|---|
| CP3 | HLD / Decision Brief | 本文件与 CP3 checkpoint | 只设计，不运行 |
| CP5 | run contract | CP3 approved + 用户授权草案 | 明确 `authorization_ref` / `run_id`；不写 secret |
| Runtime | host / port / env 引用 | 用户逐 run 授权 | 只在授权内读取最小必要配置 |
| Evidence | redacted summary | runner readonly result | 写入 `.quant-lab/evidence/qmt/cr099/redacted/` 或授权等价目录 |
| Verification | counters / digest | redacted evidence | forbidden counters 必须全部为 0 |

## 9. 关键流程

### 9.1 CP3 / CP5 设计流程

1. CP3 确认推荐架构、候选方案和不授权边界。
2. CP5 生成 run contract、evidence schema、preflight checklist 和 blocked-path 规则。
3. CP5 approve 后，仍等待用户逐 run 授权；没有授权则不执行。

### 9.2 真实运行流程

1. 用户提供逐 run 授权文本，包含 `authorization_ref`、`run_id`、host、port、readonly endpoint allowlist、client env 处理方式、evidence dir 和中止条件。
2. 运行前检查 CP5 approved、run contract 完整、redaction gate ready、forbidden counters 初始为 0。
3. runner 调用 `health`、`capabilities`、`query_positions_readonly`。
4. redaction gate 输出脱敏 evidence。
5. CP6 / CP7 校验 evidence schema、forbidden counters、raw leak 和运行边界。

### 9.3 失败 / 中止流程

| 触发条件 | 行为 | 状态 |
|---|---|---|
| 缺少 CP5 approve | 不读取 env，不运行 | blocked-pending-cp5 |
| 缺少逐 run 授权 | 不读取 env，不运行 | blocked-pending-runtime-authorization |
| client env / gateway 不可用 | 不重试扩大权限；记录 preflight blocked | blocked-runtime-preflight |
| redaction gate 未就绪 | 不运行或丢弃 in-memory result，不落 raw | blocked-redaction |
| forbidden counter 非 0 | 立即失败，停止交付 | needs-rework / blocked |
| 发现 raw payload / account leak | 立即失败，隔离 evidence，要求人工处理 | blocked-security |

## 10. 非功能设计

| 维度 | 设计 |
|---|---|
| 安全 | 默认不运行；逐 run 授权；readonly allowlist；forbidden counters；无 raw payload 落盘 |
| 可审计 | `authorization_ref`、`run_id`、checkpoint、context、run manifest 和 evidence 路径全链路可追溯 |
| 可回滚 | 运行前可停在 CP3 / CP5；运行失败只生成 blocked evidence，不修改生产系统 |
| 最小权限 | 不访问 NAS、provider/lake、release publish、交易写 endpoint 或无关目录 |
| 可验证 | CP6 / CP7 基于 schema、counters、digest 和路径白名单验证 |

## 11. Traceability

| 来源 | 目标 | 覆盖方式 |
|---|---|---|
| CR098-FU-01 | runner real readonly smoke | 本 HLD 推荐方案 A |
| DQ-CP2-CR099-01 | scope | 只覆盖 runner health / capabilities / query_positions_readonly |
| DQ-CP2-CR099-02 | runtime authorization | CP3 不授权运行，CP5 后逐 run 授权 |
| DQ-CP2-CR099-03 | security | redacted evidence / forbidden counters |
| DQ-CP2-CR099-04 | architecture | CR098 runner adapter + CR097 gateway pattern + CR099 run contract |
| DQ-CP2-CR099-05 | follow-up tracking | NAS / order-write / 非空复测独立 |

## 12. 场景模拟

| 场景 | 前置条件 | 期望结果 | 设计结论 |
|---|---|---|---|
| S1: CP3 approve 后无逐 run 授权 | CP3 approved，CP5 未完成 | 不读取 env，不运行 | PASS |
| S2: CP5 后用户授权一次 smoke | run contract 完整，gateway 可用 | runner 调用 3 个 readonly endpoint，输出 redacted evidence | PASS_WITH_RUNTIME_AUTH |
| S3: gateway 不可达 | 有授权但连接失败 | 输出 preflight blocked，不扩大权限 | PASS |
| S4: evidence 出现 raw field | redaction gate 检测泄露 | 立即 blocked-security | PASS |
| S5: 用户要求合并 NAS | 当前 CR099 | 拒绝合并，另起 CR | PASS |

## 13. 风险

| 风险 ID | 风险 | 等级 | 缓解 |
|---|---|---|---|
| R-CR099-01 | CP3 approve 被误解为真实运行授权 | HIGH | checkpoint 和 launch message 明确不授权；运行需 CP5 + 逐 run 授权 |
| R-CR099-02 | env / HMAC secret 泄露 | HIGH | run contract 只记录引用，不保存值；无授权不读取 |
| R-CR099-03 | account / positions raw 泄露 | HIGH | redaction gate、forbidden counters、raw_payload_emitted=false |
| R-CR099-04 | gateway / session 不稳定 | MEDIUM | blocked preflight，不自动扩大权限重试 |
| R-CR099-05 | 范围膨胀到 NAS / trading write | HIGH | out-of-scope 和 follow-up tracking 独立 |

## 14. ADR 候选

| ADR ID | 决策 | 状态 |
|---|---|---|
| ADR-CR099-01 | 使用 CR098 runner adapter + CR097 gateway pattern 作为真实 smoke 架构基线 | candidate |
| ADR-CR099-02 | CP3 / CP5 approve 与 runtime authorization 分离 | candidate |
| ADR-CR099-03 | CR099 evidence 只能写 redacted summary，禁止 raw payload | candidate |
| ADR-CR099-04 | 非空持仓、交易日、NAS、order-write 不并入 CR099 | candidate |

## 15. 分阶段落地

| 阶段 | 产物 | 完成准则 |
|---|---|---|
| CP3 | HLD、discussion log、context、precheck、checkpoint | 用户批准 CP3 决策项 |
| CP5 | run contract、evidence schema、preflight checklist、blocked-path checks | 用户批准 CP5，仍不等于 runtime 授权 |
| Runtime Authorization | 单次授权文本 | `authorization_ref` / `run_id` / allowlist / evidence dir 完整 |
| CP6 / CP7 | 运行或 blocked evidence、verification report | forbidden counters 为 0，或明确 blocked 原因 |
| CP8 | release readiness / closure | 用户确认 READY / READY_WITH_RISK / BLOCKED |

## 16. HLD 拆分判断

本 CR 不拆分多个 HLD。原因：目标是单一 runner real readonly smoke；NAS、order-write、非空复测和 release publish 已明确不并入。若用户改变范围，应另起 CR 或回到 CP2 修改，而不是在 CR099 内扩展子架构。

## 17. CP3 决策项

| 决策 ID | 决策类型 | 推荐方案 | 备选方案 |
|---|---|---|---|
| DQ-CP3-CR099-01 | architecture | 接受方案 A：CR098 runner adapter + CR097 gateway pattern + CR099 run contract | 用户手工 Windows-side 执行并回传脱敏 evidence |
| DQ-CP3-CR099-02 | runtime_authorization | CP3 approve 不授权真实 run；CP5 后逐 run 授权 | 永久禁止 runtime，只做离线 reverify |
| DQ-CP3-CR099-03 | security | 显式 env / HMAC handling，redacted evidence only | 允许保存完整输出，本 CR 不推荐 |
| DQ-CP3-CR099-04 | implementation | CP5 只设计 run manifest、evidence schema、preflight 和 tests；不执行 runtime | 直接进入运行，本 CR 不推荐 |
| DQ-CP3-CR099-05 | follow_up_tracking | 非空 / 交易日 / NAS / order-write 独立 follow-up | 合并进 CR099，本 CR 禁止 |

## 18. 自检

| 检查项 | 结果 | 说明 |
|---|---|---|
| 内部一致性 | PASS | CP2 / CP3 均保持“不授权 runtime” |
| 目标量化 | PASS | endpoint 数量、forbidden counters、evidence 字段均可验证 |
| 集成契约 | PASS | run contract / adapter / client / redaction / verification 职责明确 |
| 失败路径 | PASS | 缺授权、缺 env、gateway 失败、redaction 失败均定义中止行为 |
| 决策追溯 | PASS | DQ-CP2 到 DQ-CP3 显式映射 |
