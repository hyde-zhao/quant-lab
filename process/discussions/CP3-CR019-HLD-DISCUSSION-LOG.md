---
discussion_id: "CP3-CR019-HLD-DISCUSSION"
change_id: "CR-019"
phase: "solution-design"
agent_role: "meta-se"
created_at: "2026-05-30T17:16:19+08:00"
updated_at: "2026-05-30T17:44:36+08:00"
source_use_cases: [UC-15, UC-16, UC-17, UC-18]
source_requirements: [REQ-138, REQ-139, REQ-140, REQ-141, REQ-142, REQ-143, REQ-144, REQ-145, REQ-146, REQ-147, REQ-148, REQ-149, REQ-150, REQ-151, REQ-152, REQ-153, REQ-154, REQ-155, REQ-156, REQ-157, REQ-158, REQ-159, REQ-160]
status: "ready-for-cp3-review"
---

# CP3 CR-019 HLD 讨论日志

## 讨论范围

本日志记录 CR-019 solution-design 阶段的 Architecture Gray Areas、advisor table-first 输入和方案形成结论。正式消费对象仍是 `process/HLD.md` §33、`process/HLD-QMT-TRADING.md` §17、`process/ARCHITECTURE-DECISION.md` ADR-067..073 和 CP3 Decision Brief；本日志只用于审计和中断恢复。

本轮未追加新用户问题，原因是 CP2 已 approved，且 CP2-CR019-DQ-01 至 DQ-07 已覆盖核心设计决策。meta-se 未伪造独立 reviewer lane；以下 advisor table 是基于 CP2 approved 决策、CR-019 交接、UC/REQ 基线和架构自审形成的方案形成输入。

## 输入证据

| 文件 | 用途 |
|---|---|
| `checkpoints/CP2-CR019-REQUIREMENTS-BASELINE.md` | CP2 approved 决策，含 DQ-01 至 DQ-07 |
| `process/USE-CASES.md` | UC-15 至 UC-18，含 QMT C/S bridge、完整 endpoint matrix、后置能力 |
| `process/REQUIREMENTS.md` | REQ-138 至 REQ-160，含 QMT C/S 模块、C 侧接口、运行门控、安全和 fallback |
| `process/CLARIFICATION-LOG.md` | Q-039 至 Q-044 状态；Q-040 / Q-043 已 resolved；Q-039 / Q-041 / Q-042 / Q-044 需 CP3 冻结 |
| `docs/QMT-SIMULATION-LIVE-RUNBOOK.md` | stage gate、per-run authorization、kill switch、真实操作不自动授权 |
| `docs/QMT-INCIDENT-PLAYBOOK.md` | gateway / QMT incident、fail closed、recovery 边界 |
| `process/HLD-QMT-TRADING.md` | CR-015/016 QMT companion HLD；本轮需把通信默认值改为 CR-019 C/S bridge |

## Architecture Gray Areas

| Gray Area | 为什么影响 HLD | Canonical refs | 推荐讨论顺序 | 状态 |
|---|---|---|---|---|
| AGA-CR019-01：QMT C/S 模块边界 | 决定是否修改 ADR-061 通信默认值、是否更新 QMT companion HLD、C/S 文件所有权和后续 Story 拆分 | UC-16、REQ-145、REQ-149、REQ-159、CP2-DQ-01、DQ-07 | 1 | resolved-recommended |
| AGA-CR019-02：C 侧接口形态 | 决定策略 / OMS / admission / tests 通过 Python client 还是 CLI 访问 QMT 能力，影响可测试性和错误契约 | UC-16、UC-17、REQ-160、Q-044、CP2-DQ-07 | 2 | resolved-recommended |
| AGA-CR019-03：完整 endpoint matrix 与真实运行门控 | 决定接口范围、QA 矩阵、runbook 和安全授权边界；必须避免“endpoint 可见 = 真实操作授权” | UC-17、REQ-146、REQ-147、Q-041、CP2-DQ-01、DQ-04 | 3 | resolved-recommended |
| AGA-CR019-04：鉴权、绑定、防火墙和 fallback | 决定配对式 token/HMAC 默认启用、no-auth 临时范围、bind/firewall/redaction，以及 gateway 故障时是否 fail closed | UC-16、UC-17、REQ-148、REQ-150、REQ-151、Q-039、Q-042、CP3-CR019-DQ-04 | 4 | resolved-recommended |

## Advisor Table：AGA-CR019-01 QMT C/S 模块边界

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| QMT 独立 C/S：local_backtest C 侧 client + Windows FastAPI S 侧 gateway | 满足用户要求；C 侧不依赖 xtquant；支持 heartbeat、capabilities、typed blocked reason 和完整 endpoint matrix | 需要定义服务生命周期、bind、防火墙、API contract 和 incident | HLD、QMT companion、ADR、deployment、tests、docs | 推荐 | 适用于受控局域网 / 本机访问；若 Windows 服务无法安全部署，降级 signed file fallback |
| signed file drop 继续作为主路径 | 简单、低权限、易审计 | 不满足 D7；交互性弱；完整 QMT endpoint 难表达 | runbook、ops、fallback | 不推荐为主路径 | 只作为 FastAPI 不可达、鉴权失败或部署不满足时的 fallback |
| gateway 嵌入回测主进程 | 文件少，初期实现看似简单 | C/S 模块边界消失，WSL / QMT 平台边界混淆 | app、security、testing | 不推荐 | 仅当用户放弃独立 Windows gateway 时重新讨论 |

## Advisor Table：AGA-CR019-02 C 侧接口形态

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| Python client / 函数调用为主 + 薄 CLI | 内部策略、OMS、admission 和测试可类型化调用；CLI 仍可人工 smoke / ops | 需要维护 client API 和 CLI wrapper | C 侧 API、tests、docs、runbook | 推荐 | 若主要调用方变成外部脚本或多语言系统，可切换 CLI-first / REST SDK |
| CLI-first | 手工操作直观，脚本友好 | 内部调用需进程管理、文本解析、退出码和超时处理 | tests、ops、error handling | 不推荐 | 只在主要使用方式是外部命令编排时采用 |
| Python-only | 内部最薄，维护简单 | 缺少人工检查和运维入口 | C 侧 API | 条件备选 | 如果明确无需人工 smoke / ops 命令，可取消 CLI |

## Advisor Table：AGA-CR019-03 完整 endpoint matrix 与运行门控

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| 完整 endpoint matrix + run mode / stage / risk / kill-switch / authorization gate | 满足用户完整 QMT 功能目标；真实操作仍 fail closed | API / QA / runbook 范围较大 | API, testing, runbook, security, QMT | 推荐 | 可按 Story 分批实现，但目标矩阵不退回 dry-run-only |
| dry-run / readonly 子集 | 实现最小，安全 | 不满足用户纠偏；后续 endpoint 反复改契约 | API、tests | 不推荐为目标基线 | 可作为首批实现子集，不可作为最终接口范围 |
| 局域网内真实 endpoint 无门控直转 | 起步快 | 绕过 CR016 stage gate、risk gate 和 kill switch | safety、QMT、incident | 禁止 | 除非新 CR 明确风险接受，否则不得采用 |

## Advisor Table：AGA-CR019-04 鉴权、绑定、防火墙和 fallback

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| 配对式 token/HMAC 默认启用；fallback blocked-only / 人工 dry-run file | 用户已确认；能识别调用方并降低误调用；pairing 可人工批准；仍保持 fail closed | 需要定义 pairing request/list/approve/complete、secret 领取、timestamp、nonce、scope 和日志脱敏 | security、deployment、ops、incident、config | 推荐 | 多人、跨网段或 live 默认启用时，在此基础上增强 scope、rotation、mTLS/VPN 或 Windows ACL |
| no-auth 默认 | 初始调试最简单 | 用户已明确不接受作为默认；调用方不可识别；容易被误当安全方案 | security、docs、tests | 不推荐 | 仅允许本机 debug、fixture 测试或明确配置的临时模式 |
| 静态共享 token | 比 no-auth 多一层检查；实现较轻 | 不能表达 per-client scope；泄露后难定位；轮换和审计弱 | security、config、ops | 不推荐 | 仅作为极简临时替代，不作为目标基线 |
| mTLS / VPN / Windows ACL | 网络边界和身份强度更高 | 对阶段六第一版部署复杂度较高；证书 / 网络策略运维成本高 | security、deployment、ops | 后置增强 | 组织化多人访问、跨网段、默认 live 或合规要求提高时叠加 |
| 自动真实 QMT fallback | 可用性高 | 风险极高，绕过 gateway 和 gate | safety、broker、incident | 不推荐 / 禁止 | 不作为 CR-019 方案 |

## 方案形成结论

| 决策项 | 推荐结论 | 影响 |
|---|---|---|
| C/S bridge | 采用 local_backtest C 侧 Python client / 薄 CLI + Windows S 侧 FastAPI gateway | 更新 `process/HLD.md` §33、`process/HLD-QMT-TRADING.md` §17、ADR-068 |
| C 侧接口 | Python client / 函数调用为主，CLI 只薄包装 | 更新 ADR-069；后续 LLD 定义 typed request / response |
| Endpoint matrix | 完整 QMT endpoint 类别全部进入目标契约，真实转发受运行门控 | 更新 ADR-070；CP3 review 需用户确认 |
| 鉴权 | 配对式 token/HMAC 默认启用；no-auth 仅本机 debug / fixture / 显式临时；后续请求携带 client id、timestamp、nonce、HMAC signature | 更新 ADR-071；pairing、bind/firewall/redaction、timestamp/nonce/scope 必须作为 LLD 输入 |
| fallback | blocked-only 或人工 dry-run / signed file drop，禁止自动真实 QMT | 更新 ADR-072；incident playbook 后续刷新 |
| 后置能力 | Backtrader W6、Qlib W7、minute / Level2 Spike 后置 | 更新 ADR-073；不进入阶段六 P0 |

## Deferred Options

| 选项 | 延后原因 | 触发条件 |
|---|---|---|
| CLI-first C 侧接口 | 内部调用和测试成本高 | 主要调用方转为外部脚本 / 多语言系统 |
| no-auth 默认 | 用户已确认不得作为默认；调用方不可识别 | 仅本机 debug、fixture 测试或明确配置的临时模式 |
| 静态共享 token | per-client scope、审计和轮换不足 | 极简临时替代且不涉及真实交易授权时才重新评估 |
| mTLS / VPN / Windows ACL | 对阶段六第一版过重 | 安全边界升级或组织化多人访问 |
| 自动真实 QMT fallback | 不符合 fail-closed 和运行门控 | 不建议触发；如用户坚持需新 CR 风险接受 |
| Backtrader / Qlib / minute / Level2 提前 | 会挤占 admission 主线 | 满足 ADR-073 触发条件并新建 CR / Spike |

## CP3 决策输入

| 决策 ID | 待确认问题 | 推荐方案 | 备选方案 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|
| CP3-CR019-DQ-01 | 是否接受 QMT C/S bridge 主选替代 signed file drop 默认通信 | 接受 local_backtest C 侧 client + Windows FastAPI S 侧 gateway | signed file drop 主路径；gateway 嵌入回测主进程 | 影响 API、部署、安全和 QMT companion；服务复杂度上升 | 若 Windows 服务无法安全限定来源，回退 fallback |
| CP3-CR019-DQ-02 | 是否接受 C 侧 Python client / 函数调用为主 + 薄 CLI | 接受 | CLI-first；Python-only | 影响内部调用、测试、运维入口 | 外部命令编排为主时切 CLI-first；无 ops 入口需求时 Python-only |
| CP3-CR019-DQ-03 | 是否接受完整 endpoint matrix 与运行门控分离 | 接受 | dry-run-only；无门控直转 | API / QA 扩大；安全边界更清晰 | 可分批实现；不得无门控直转 |
| CP3-CR019-DQ-04 | 是否接受配对式 token/HMAC 默认启用，no-auth 仅本机 debug / fixture / 显式临时 | 接受：C 侧 pairing request，S 侧 list/approve，C 侧 complete；请求携带 client id、timestamp、nonce、HMAC signature | no-auth 默认；静态共享 token；mTLS / VPN / Windows ACL | pairing/HMAC 只识别调用方；真实交易仍必须经过 run mode、stage gate、risk gate、kill-switch 和 per-run authorization；日志禁止 secret / pairing code | 多人 / 跨网段 / live 默认启用时增强 scope、rotation 或强鉴权；本机 debug / fixture 才允许 no-auth |
| CP3-CR019-DQ-05 | 是否接受 fallback 只 blocked-only 或人工 dry-run / signed file drop | 接受 | 自动真实 fallback | 可用性降低但 fail closed | 自动真实 fallback 必须新 CR 风险接受 |
| CP3-CR019-DQ-06 | 是否接受 Backtrader/Qlib/minute/Level2 后置 | 接受 | 提前引入任一能力 | 主线聚焦 admission；外部依赖延后 | 满足触发条件后新建 CR / Spike |
| CP3-CR019-DQ-07 | 是否接受阶段六 admission 采用新多因子 gate + 多基准看板 + primary benchmark | 接受 | 只用 HS300；只看绝对收益 / 回撤 / 波动 / 成本 | 旧失败策略只作 blocked evidence；多基准字段和验证矩阵扩大 | 若策略转单一指数增强或市场中性，可切换 benchmark policy |

## CP3 DQ-04 用户修订记录

用户在 CP3 DQ-04 追加修订中明确选择“配对式 token/HMAC 默认启用”。no-auth 不再作为默认推荐方案，只允许本机 debug、fixture 测试或明确配置的临时模式。

配对流程冻结为设计输入：C 侧执行 pairing request；S 侧记录 pending request，字段含 `request_id`、client name、来源 IP、机器指纹摘要、创建时间和过期时间；S 侧管理员 list/approve；S 侧生成 client id + secret，并通过一次性 pairing code 或短 TTL 领取窗口交付；C 侧 complete 后，后续请求携带 `X-QMT-Client-Id`、`X-QMT-Timestamp`、`X-QMT-Nonce`、`X-QMT-Signature`。

HMAC 签名建议为 `HMAC_SHA256(secret, method + path + body_hash + timestamp + nonce)`。S 侧必须校验 approved client、timestamp 偏移、nonce replay 和 scope。HMAC 通过只代表“调用方已识别”，不代表 simulation / live / account / cancel 等真实操作授权；真实交易仍必须继续通过 run mode、stage gate、risk gate、kill-switch 和 per-run authorization。

## 自审结论

- Architecture Gray Areas 数量：4。
- Advisor table 使用固定表头：已满足。
- 用户 / CP2 已确认决策已消费：D1-D7、Q40、Q43、Q44 推荐。
- 真实操作授权：未授权；本讨论不要求也不执行真实 QMT / provider / lake / broker 操作。
- HLD 生成状态：可提交 CP3 自动预检和人工审查草案。
