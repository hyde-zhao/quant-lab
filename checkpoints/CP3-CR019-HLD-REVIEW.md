---
checkpoint_id: "CP3"
checkpoint_name: "CR-019 HLD / ADR 人工审查"
type: "auto_then_manual"
status: "approved"
owner: "meta-po"
created_at: "2026-05-30T17:16:19+08:00"
updated_at: "2026-05-30T17:44:36+08:00"
reviewed_by: "user"
reviewed_at: "2026-05-30T18:04:03+08:00"
auto_check_result: "process/checks/CP3-CR019-HLD-CONSISTENCY.md"
target:
  phase: "solution-design"
  change_id: "CR-019"
  artifacts:
    - "process/HLD.md"
    - "process/HLD-QMT-TRADING.md"
    - "process/ARCHITECTURE-DECISION.md"
    - "process/discussions/CP3-CR019-HLD-DISCUSSION-LOG.md"
    - "process/checks/CP3-CR019-DISCUSSION-CHECKPOINT.json"
    - "process/checks/CP3-CR019-HLD-CONSISTENCY.md"
---

# CP3 CR-019 HLD / ADR 人工审查

> 本文件为 meta-se 生成、meta-po 正式发起的 CP3 人工审查稿。用户已选择 `approve`，接受 DQ-01 至 DQ-07 全部推荐方案；CP3 通过仅授权进入 Story Plan / CP4，不授权 LLD、代码实现、依赖变更、服务启动或真实 QMT 操作。

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---|---|
| `process/checks/CP3-CR019-HLD-CONSISTENCY.md` | PASS | 0 | HLD / QMT companion HLD / ADR / discussion log / checkpoint 均已更新；未越过 CP3，未执行真实 QMT / provider / lake / broker 操作。 |

## Decision Brief

### 待人工决策清单

| 决策 ID | 待确认问题 | 推荐方案 | 备选方案 | 优劣分析 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|
| CP3-CR019-DQ-01 | 是否接受 CR-019 将 QMT 通信主路径从 ADR-061 的 signed file drop 默认值修订为独立 C/S 模块？背景：用户已确认 QMT 模块必须包含 local_backtest C 侧和 Windows S 侧。 | 接受 QMT C/S bridge：C 侧位于 local_backtest，S 侧为 Windows 可运行 / 可安装 FastAPI gateway，通过 REST 转换为 QMT / XtQuant 调用；signed file drop 降级为 fallback。 | 备选 A：继续 signed file drop 作为主路径；备选 B：gateway 嵌入回测主进程。 | 推荐方案满足用户目标、支持完整 endpoint 和 heartbeat；备选 A 安全简单但交互性和能力面不足；备选 B 文件少但破坏 C/S 边界。 | 影响 HLD-QMT、ADR-061 增量、API contract、部署、安全、测试和 runbook；服务复杂度上升。 | 若 Windows 端口 / 防火墙无法安全限定，降级为 signed file drop fallback；不得让 WSL 直连 xtquant。 |
| CP3-CR019-DQ-02 | 是否接受 C 侧接口采用 Python client / 函数调用为主 + 薄 CLI？背景：Q-044 要冻结 local_backtest 内部如何消费 QMT 能力。 | 接受：Python client / 函数调用服务策略、OMS、admission 和测试；CLI 只复用同一 client 做人工 smoke、运维检查和脚本包装。 | 备选 A：CLI-first；备选 B：纯 Python-only。 | 推荐方案内部可测试性最好且保留运维入口；CLI-first 手工友好但内部调用需进程管理和文本解析；Python-only 最薄但缺 smoke / ops 入口。 | 影响 C 侧模块边界、错误契约、mock、CLI 文档和后续 Story 拆分。 | 如果主要调用方变为外部脚本 / 多语言系统，切换 CLI-first 或 REST SDK；如果确认无需人工入口，取消 CLI。 |
| CP3-CR019-DQ-03 | 是否接受完整 QMT endpoint matrix 与运行门控分离？背景：用户已纠正“不做鉴权并不是 QMT 功能不做”。 | 接受：gateway 支持 health/capabilities、validate/dry-run、行情、账户、持仓、委托、成交、simulation submit/cancel、live-readonly、live submit/cancel、reconciliation、kill-switch；真实转发由 run mode / stage / risk / kill-switch / per-run authorization 控制。 | 备选 A：dry-run / readonly 子集；备选 B：局域网内无门控直转。 | 推荐方案兼顾完整能力和安全；备选 A 实现简单但不满足用户目标；备选 B 最快但风险不可接受。 | 影响 API schema、测试矩阵、runbook、incident 和安全声明；完整接口面增加工作量。 | 可按 Story 分批实现，但目标矩阵不退回 dry-run-only；无门控直转必须另起 CR 并接受风险。 |
| CP3-CR019-DQ-04 | 是否接受配对式 token/HMAC 默认启用，no-auth 仅本机 debug / fixture / 显式临时？背景：Q-039 与用户 DQ-04 修订要求冻结鉴权、绑定、防火墙、pairing 和日志脱敏。 | 接受：C 侧执行 pairing request；S 侧记录 pending request 并由管理员 list / approve；S 侧生成 client id + secret 和一次性 pairing code 或短 TTL 领取窗口；C 侧 complete 后，请求携带 client id、timestamp、nonce、HMAC signature。 | 备选 A：no-auth 默认；备选 B：静态共享 token；备选 C：mTLS / VPN / Windows ACL。 | 推荐方案能识别调用方并保留人工批准；A 最简单但用户已明确不接受作为默认；B 较轻但 per-client scope、审计和轮换不足；C 安全更强但部署成本高。 | HMAC 通过只代表调用方已识别，不代表 simulation / live / account / cancel 授权；日志不得输出 secret、pairing code 或 token；no-auth 误设为默认会扩大误调用风险。 | 多人、跨网段或 live 默认启用时增强 scope、rotation、mTLS/VPN 或 Windows ACL；仅本机 debug、fixture 测试或明确配置的临时模式允许 no-auth。 |
| CP3-CR019-DQ-05 | 是否接受 FastAPI fallback 只允许 blocked-only 或人工 dry-run / signed file drop？背景：Q-042 要冻结 gateway 失败时行为。 | 接受：gateway 不可达、鉴权失败、heartbeat fail 或部署不满足时 fail closed；可生成 dry-run / signed file drop 供人工处理；不得自动真实 QMT。 | 备选 A：仅 blocked-only；备选 B：自动切换备用真实 QMT 路径。 | 推荐方案安全和审计平衡；A 最安全但排障信息少；B 可用性高但会绕过 gate。 | 影响 incident playbook、运行连续性和故障恢复；自动 fallback 风险极高。 | 若运维需要更强排障，保留 dry-run file；自动真实 fallback 必须新 CR 风险接受。 |
| CP3-CR019-DQ-06 | 是否接受 Backtrader、Qlib、minute 和 Level2 均后置触发，不进入阶段六 P0？ | 接受：Backtrader W6 optional backend、Qlib W7 isolated runner、minute / Level2 Spike 后置，满足触发条件后另起 CR / Story / CP。 | 备选 A：提前 Backtrader；备选 B：提前 Qlib；备选 C：提前 minute / Level2。 | 推荐方案保持主线聚焦 admission 和 QMT bridge；备选会扩大依赖、数据工程、权限和验证范围。 | 影响 roadmap、Story priority、依赖和测试矩阵；提前高频 / Level2 可能引入权限与成本风险。 | clean feed / candidate strategy / factor panel / 微观结构风险证据满足后，另起 CR / Spike。 |
| CP3-CR019-DQ-07 | 是否接受阶段六 admission 采用新多因子 gate + 多基准看板 + primary benchmark，且旧失败策略只作为 blocked evidence？ | 接受：阶段六 admission 以实验 49-66 建立新多因子 gate；同时输出 HS300、ZZ500、ZZ1000、中证全指，并按策略 universe / 风格选择 primary benchmark。 | 备选 A：只用 HS300；备选 B：只看绝对收益 / 回撤 / 波动 / 成本。 | 推荐方案能减少风格错配并保持可判定；A 简单但偏大盘；B 适合绝对收益策略但不适合作为 long-only A 股多因子默认准入。 | 影响 admission report、tracking / excess 口径、freeze fields 和后续 simulation 申请证据。 | 若策略转单一指数增强，切换对应单基准；若策略转市场中性，切换绝对收益主口径。 |

| 字段 | 内容 |
|---|---|
| 推荐决策 | `approve`：接受 CR-019 HLD / ADR 推荐方案，确认阶段六 admission、多基准 + primary benchmark、QMT C/S bridge、C 侧 Python client + 薄 CLI、完整 endpoint matrix 与运行门控分离、配对式 token/HMAC 默认启用、no-auth 仅 debug / fixture / 显式临时、fail-closed fallback 和后置能力边界。 |
| 备选方案 | `修改: <具体修改点>`：指定要调整的 DQ；`reject`：不接受当前 HLD，回退到 solution-design 或 requirement-clarification。 |
| 影响维度 | 用户价值、实现复杂度、可验证性、维护成本、平台兼容、安全 / 权限、交付影响。 |
| 优劣分析 | 推荐方案满足用户完整 QMT 能力与安全门控目标，代价是 API / 部署 / 测试复杂度上升；备选方案要么范围不足，要么风险过高。 |
| 风险与回退 | 主要风险为 endpoint 可见被误解为真实授权、HMAC pass 被误解为交易授权、secret / pairing code 泄露、no-auth 临时模式被误设为默认、fallback fail-open、QMT 文档能力被误当当前权限。若 CP3 不通过，回退到 AGA-CR019-01..04 和 Q-039/Q-041/Q-042/Q-044。 |
| 用户需决策事项 | CP3-CR019-DQ-01 至 CP3-CR019-DQ-07；用户回复 `approve` 表示接受上表全部推荐方案。 |

### CP3 追加 Decision Brief 字段

| 字段 | 内容 |
|---|---|
| 候选架构适用条件 | 推荐 CR19-A 适用于受控局域网 / WSL + Windows QMT 节点分离、需要完整 QMT 功能接口但真实操作仍 gate-controlled 的场景。 |
| 优化项 | 从 signed file drop 主路径升级为 C/S gateway；C 侧类型化 Python client；完整 endpoint matrix；capabilities、heartbeat、blocked reason 和 redaction 更可观测。 |
| 牺牲项 | 服务生命周期、bind、防火墙、鉴权、API contract 和 QA 范围扩大；CP3 通过后仍需 CP4/CP5 才能实现。 |
| 影响面 | 主 HLD §33、QMT companion HLD §17、ADR-067..073、后续 Story Plan、runbook、incident playbook、测试策略和用户文档。 |
| 切换条件 | 网络服务无法安全部署时回退 signed file dry-run fallback；多人 / 跨网段 / live 默认启用时在 pairing/HMAC 基础上增强 scope、rotation、mTLS/VPN 或 Windows ACL；外部脚本成为主调用方时考虑 CLI-first / REST SDK。 |
| Use Case -> Architecture Traceability | `process/HLD.md` §33.6 将 UC-15..UC-18 映射到 admission gate、C/S bridge、endpoint matrix、后置能力。 |
| 关键场景模拟结果 | `process/HLD.md` §33.7 覆盖 capabilities、未授权 simulation submit、gateway 不可达 / 鉴权失败、提前 Qlib / Level2 四个场景，推荐架构均能 fail closed 或 deferred。 |
| 未决风险 | CP3 仍需用户确认 DQ-01..DQ-07；CP3 通过不授权实现或真实操作。 |
| discussion log / checkpoint | `process/discussions/CP3-CR019-HLD-DISCUSSION-LOG.md`；`process/checks/CP3-CR019-DISCUSSION-CHECKPOINT.json`。 |

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| CR-019 CP2 已批准 | approved | `checkpoints/CP2-CR019-REQUIREMENTS-BASELINE.md` status=`approved` | 通过 |
| CP3 自动预检 PASS | approved | `process/checks/CP3-CR019-HLD-CONSISTENCY.md` | 通过 |
| Architecture Gray Areas 已处理 | approved | `process/discussions/CP3-CR019-HLD-DISCUSSION-LOG.md`；`process/checks/CP3-CR019-DISCUSSION-CHECKPOINT.json` | 通过 |
| HLD / ADR 增量存在 | approved | `process/HLD.md` §33；`process/HLD-QMT-TRADING.md` §17；ADR-067..073 | 通过 |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 是否接受 CR-019 问题定义和非目标 | approved | `process/HLD.md` §33.1 | 通过 |
| 2 | 是否接受候选方案对比和推荐 CR19-A | approved | `process/HLD.md` §33.3 | 通过 |
| 3 | 是否接受 QMT C/S bridge 主选 | approved | `process/HLD.md` §33.4；ADR-068 | 通过 |
| 4 | 是否接受 C 侧 Python client / 薄 CLI | approved | `process/HLD.md` §33.9；ADR-069 | 通过 |
| 5 | 是否接受完整 endpoint matrix 与运行门控分离 | approved | `process/HLD.md` §33.11；ADR-070 | 通过 |
| 6 | 是否接受配对式 token/HMAC、bind / firewall / redaction 策略 | approved | `process/HLD.md` §33.10、§33.10.1、§33.13；ADR-071 | 通过 |
| 7 | 是否接受 fallback fail-closed 策略 | approved | `process/HLD.md` §33.12；ADR-072 | 通过 |
| 8 | 是否接受 Backtrader / Qlib / minute / Level2 后置 | approved | `process/HLD.md` §33.14；ADR-073 | 通过 |
| 9 | 是否接受 QMT companion HLD 同步修订 | approved | `process/HLD-QMT-TRADING.md` §17 | 通过 |
| 10 | 是否确认 CP3 通过仍不授权实现或真实操作 | approved | `process/checks/CP3-CR019-HLD-CONSISTENCY.md` No-Real-Operation 声明 | 通过 |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| 人工结论为 approved / changes_requested / rejected | approved | 本文件“人工审查结果” | 通过 |
| 若 approved，DQ-01..DQ-07 均视为接受推荐方案 | approved | Decision Brief | 通过 |
| 若 changes_requested，需指定决策 ID 和修改点 | approved | 用户回复为 `approve`，无需修改点 | 通过 |
| 若 rejected，回退到 solution-design / requirement-clarification | approved | 未触发 reject | 通过 |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| CR-019 HLD 主增量 | `process/HLD.md` | approved | 通过 |
| QMT companion HLD 增量 | `process/HLD-QMT-TRADING.md` | approved | 通过 |
| ADR 增量 | `process/ARCHITECTURE-DECISION.md` | approved | 通过 |
| CP3 讨论日志 | `process/discussions/CP3-CR019-HLD-DISCUSSION-LOG.md` | approved | 通过 |
| CP3 讨论恢复点 | `process/checks/CP3-CR019-DISCUSSION-CHECKPOINT.json` | approved | 通过 |
| CP3 自动预检 | `process/checks/CP3-CR019-HLD-CONSISTENCY.md` | approved | 通过 |

## 人工审查结果

- 结论：`approved`
- 审查人：user
- 审查时间：2026-05-30T18:04:03+08:00
- 修改意见：用户选择 `approve (Recommended)`，接受 CP3-CR019-DQ-01 至 CP3-CR019-DQ-07 全部推荐方案；DQ-04 已按用户上一轮确认修订为配对式 token/HMAC 默认启用。
- 风险接受项：CP3 通过仅授权进入 Story Plan / CP4；不授权 LLD、代码实现、依赖变更、服务启动、凭据读取、真实 QMT / MiniQMT / XtQuant 操作、真实 provider fetch、真实 lake / broker lake 写入、publish 或 simulation / live run。
