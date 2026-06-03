---
checkpoint_id: "CP2"
checkpoint_name: "CR-019 需求基线人工审查"
type: "auto_then_manual"
status: "approved"
owner: "meta-po"
created_at: "2026-05-30T15:18:00+08:00"
reviewed_by: "user"
reviewed_at: "2026-05-30T17:12:54+08:00"
auto_check_result: "process/checks/CP2-CR019-REQUIREMENTS-BASELINE.md"
target:
  phase: "requirement-clarification"
  change_id: "CR-019"
  artifacts:
    - "process/USE-CASES.md"
    - "process/REQUIREMENTS.md"
    - "process/CLARIFICATION-LOG.md"
    - "process/checks/CP1-CR019-USE-CASE-COMPLETENESS.md"
    - "process/checks/CP2-CR019-REQUIREMENTS-BASELINE.md"
    - "process/discussions/CP2-CR019-SCENARIO-DISCUSSION-LOG.md"
    - "process/checks/CP2-CR019-DISCUSSION-CHECKPOINT.json"
---

# CP2 CR-019 需求基线人工审查

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---|---|
| `process/checks/CP1-CR019-USE-CASE-COMPLETENESS.md` | PASS | 0 | CR-019 场景已覆盖 D1-D7、Q40 多基准、阶段六多因子模拟盘准入、QMT C/S bridge、完整 endpoint matrix、运行门控、signed file drop fallback 和后置能力边界。 |
| `process/checks/CP2-CR019-REQUIREMENTS-BASELINE.md` | PASS | 0 | REQ-138 至 REQ-160 均有来源场景和可检查验收条件；Q-039 至 Q-044 为 CP3/HLD 冻结项或已决策输入，不阻断 CP2。 |

## Decision Brief

### 待人工决策清单

| 决策 ID | 待确认问题 | 推荐方案 | 备选方案 | 优劣分析 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|
| CP2-CR019-DQ-01 | 是否确认 QMT FastAPI gateway 的目标是“完整 QMT 功能接口覆盖”，而不是 dry-run-only？背景：用户已纠正“不做鉴权并不是 QMT 功能不做”。 | 确认 gateway endpoint matrix 必须覆盖完整 QMT 功能类别：health/capabilities、validate/dry-run、行情、账户、持仓、委托、成交、simulation submit/cancel、live-readonly、live submit/cancel、reconciliation、kill-switch；真实转发由运行门控控制。 | 备选 A：只做 dry-run/readonly 子集；备选 B：继续 signed file drop 主路径，不做 API gateway。 | 推荐方案符合用户目标，能让回测框架通过网关支持完整 QMT 能力；备选 A 实现简单但不满足用户纠偏；备选 B 风险较低但自动化和可观测性弱。 | 影响 API schema、Story 拆解、Windows gateway 实现、测试矩阵和 QMT 运行治理；完整接口面扩大实现范围和验证范围。 | 若 CP3 发现完整接口范围过大，可拆分 Story，但不得把目标改回 dry-run-only，除非用户重新决策。 |
| CP2-CR019-DQ-02 | Q-039：局域网运行下是否需要应用层鉴权？ | 第一版默认无应用层鉴权，前提是只在受控局域网 / 本机可达范围运行，并在 HLD 冻结 bind、防火墙、日志脱敏和运行门控；若 CP3 判定仍需鉴权，则采用最简 token / HMAC。 | 备选 A：强制最简 token / HMAC；备选 B：mTLS / VPN / Windows ACL 等强安全方案。 | 推荐方案最贴合用户使用方式，复杂度最低；A 防误调用更好但增加密钥管理；B 安全最强但对阶段六过重。 | 局域网不等于零风险；仍需防止公网误暴露、日志泄露和误调用。鉴权策略不影响 QMT 功能接口覆盖。 | 若后续开放跨网段、多人访问或真实 live endpoint 默认启用，切换到 token / HMAC 或更强方案。 |
| CP2-CR019-DQ-03 | Q-040：阶段六 admission benchmark / tracking / freeze fields 采用哪种方案？ | 已按用户确认采用“多基准看板 + primary benchmark 规则”：同时输出 HS300、ZZ500、ZZ1000、中证全指；按策略 universe / 风格选择 primary benchmark，admission pass/fail 以 primary benchmark、风险约束和 blocked claims 为主。 | 备选 A：只用 HS300；备选 B：只用中证全指；备选 C：不设主基准，只看绝对收益 / 回撤 / 波动 / 成本。 | 推荐方案覆盖大盘 / 中盘 / 小盘 / 全市场，能减少风格错配；A 简单但偏大盘；B 适合全 A 但不解释风格偏离；C 适合绝对收益策略但不适合 long-only A 股多因子默认准入。 | 影响 admission report、tracking / excess 口径、策略冻结字段、测试矩阵和后续 QMT simulation 申请证据。 | 若策略类型明确为单一指数增强，可切换到对应单基准；若策略转市场中性，可切换到绝对收益主口径。 |
| CP2-CR019-DQ-04 | Q-041：完整 QMT endpoint 支持后，真实 simulation / live / account / cancel 如何门控？ | 接口完整支持；真实转发由 run mode、stage gate、risk gate、kill switch 和必要授权上下文控制。鉴权是调用方识别问题，不替代运行门控。 | 备选 A：局域网内完全信任调用方，所有真实 endpoint 可直接转发；备选 B：只设计接口，不实现真实转发。 | 推荐方案兼顾完整能力和运行治理；A 最简单但会绕过 CR016 stage gate；B 风险低但不满足完整 QMT 能力目标。 | 影响真实 QMT 调用路径、审计、事故恢复和 CP6/CP7 验证。 | 若后续用户明确要求无门控直连，需要新 CR / 风险接受；默认不得采用。 |
| CP2-CR019-DQ-05 | Q-042：FastAPI gateway 失败时 fallback 如何处理？ | 第一版采用 blocked-only 或人工 dry-run file fallback；不得自动绕过 gateway 触发真实 QMT。signed file drop 只作为备选人工处理，不作为完整功能替代路径。 | 备选 A：保留 signed file drop dry-run fallback；备选 B：自动切换到备用服务或真实 QMT 路径。 | 推荐方案最安全，避免 fail-open；A 增加审计连续性但要定义 schema；B 可用性强但风险高，不推荐。 | 影响 incident playbook、运行连续性和故障恢复；自动 fallback 若设计不当会绕过 gate。 | 如果后续运维需要离线处理，可启用 signed file drop dry-run fallback；不得启用自动真实 QMT fallback。 |
| CP2-CR019-DQ-06 | Q-043：是否接受 Backtrader / Qlib / minute / Level2 后置顺序？ | 接受：Backtrader 后置为 W6 optional execution backend，Qlib 后置为 W7 isolated runner，分钟数据和 Level2 作为后置 Spike；未触发前不进入阶段六 P0。 | 备选 A：提前 Backtrader；备选 B：提前 Qlib；备选 C：提前 minute / Level2。 | 推荐方案保持阶段六主线聚焦多因子 admission 和 QMT gateway；备选会扩大依赖、数据工程和验证范围。 | 影响 Story Plan、依赖、数据需求和准入节奏。 | 当 clean feed、candidate strategy、factor panel 或执行质量证据达到触发条件时，另起 Story / CR。 |
| CP2-CR019-DQ-07 | Q-044：QMT C 侧对 local_backtest 暴露的统一接口采用 CLI 模式还是 Python 函数调用模式？ | 采用“Python client / 函数调用为主 + 薄 CLI 为辅”：C 侧在 local_backtest 内提供类型化 Python client / 函数接口；CLI 复用同一 client，仅用于人工 smoke、运维检查和脚本包装。 | 备选 A：CLI-first；备选 B：纯 Python-only。 | 推荐方案最适合框架内部集成、单元测试、mock 和错误处理，同时保留人工排障入口；CLI-first 手工友好但内部调用需进程管理、文本解析和退出码约定；纯 Python-only 最简单但缺少独立检查和运维入口。 | 影响模块边界、测试方式、用户命令、文档、Windows/WSL 联调和 Story 拆解。 | 若后续主要由外部脚本或多语言系统调用，可切换 CLI-first 或 REST SDK；若明确只供 Python 内部使用，可取消 CLI，只保留 Python client。 |

| 字段 | 内容 |
|---|---|
| 推荐决策 | `approve`：批准修订后的 CR-019 CP2 需求基线，确认完整 QMT gateway 接口覆盖、QMT 独立 C/S 模块、C 侧 Python client 主接口 + 薄 CLI、局域网默认无应用层鉴权 / 可选最简 token-HMAC、多基准 + primary benchmark、真实转发运行门控、blocked-only / 人工 dry-run fallback、Q-043 后置顺序。 |
| 备选方案 | `修改: <具体修改点>`：指出要调整的 gateway 功能范围、鉴权策略、benchmark 方案、运行门控或 fallback；`reject`：暂停 CR-019，不进入 CP3。 |
| 影响维度 | 用户价值、实现复杂度、可验证性、维护成本、平台兼容、安全 / 权限、交付影响。 |
| 优劣分析 | 推荐方案推进最快且门控完整；修改方案提高精确度但延后；拒绝方案风险最低但阶段六无法继续。 |
| 风险与回退 | 风险等级为中高，来自 FastAPI 服务边界、QMT 权限、凭据和 stage gate；回退点为 requirement-clarification。 |
| 用户需决策事项 | CP2-CR019-DQ-01 至 CP2-CR019-DQ-07；其中 DQ-03 已由用户确认采用推荐方案。 |

### CP2 追加 Decision Brief 字段

| 字段 | 内容 |
|---|---|
| 用户真实意图 | 将阶段六推进为 A 股多因子策略的模拟盘准入路线，并采用 QMT 独立 C/S 模块作为 local_backtest / Windows QMT 桥接主方案；C 侧位于 local_backtest 并暴露统一 Python 接口，S 侧作为 Windows 系统可运行 / 可安装 gateway，接口面支持完整 QMT 功能，并通过 REST 转换为 QMT / XtQuant 接口调用。 |
| 场景覆盖 | 新增 UC-15 至 UC-18，覆盖多因子 admission、QMT C/S bridge、完整 QMT endpoint matrix、安全门控和后置能力边界。 |
| 认知盲区补充 | 不做应用层鉴权不等于不做 QMT 功能；完整 endpoint 支持不等于无门控真实 QMT；QMT 模块独立不等于 C 侧只能 CLI 调用；局域网运行不等于零风险；QMT 文档能力不等于当前账户权限；旧失败策略不能包装为 admission pass；后置能力不能挤占 P0；fallback 不能自动真实 QMT。 |
| Scenario Gray Areas 处理结果 | 已处理 SGA-019-01 至 SGA-019-04；日志见 `process/discussions/CP2-CR019-SCENARIO-DISCUSSION-LOG.md`，恢复点见 `process/checks/CP2-CR019-DISCUSSION-CHECKPOINT.json`。 |
| Deferred Ideas | Backtrader W6 optional backend、Qlib W7 isolated runner、分钟数据 Spike、Level2 Spike、自动真实 QMT fallback、直接迁移到外部框架均延后。 |
| 用户选择影响 | `approve` 后进入 CP3；`修改` 后回退需求澄清补改；`reject` 后 CR-019 保持 open / blocked。 |
| 回退方式 | 回退到 `requirement-clarification`，按指定 UC / REQ / 决策项增量修订并重新生成 CP1 / CP2。 |
| discussion log / checkpoint | `process/discussions/CP2-CR019-SCENARIO-DISCUSSION-LOG.md`；`process/checks/CP2-CR019-DISCUSSION-CHECKPOINT.json`。 |

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| CR-019 已登记并获准进入需求 / 设计推进 | approved | `process/changes/CR-019-STAGE6-MULTIFACTOR-SIMULATION-ARCHITECTURE-2026-05-30.md` | 用户已批准 D1-D7 与 CR intake；本审查确认 CP2 基线。 |
| CP1 场景完备门通过 | approved | `process/checks/CP1-CR019-USE-CASE-COMPLETENESS.md` | 自动结论 PASS。 |
| CP2 需求基线自动预检通过 | approved | `process/checks/CP2-CR019-REQUIREMENTS-BASELINE.md` | 自动结论 PASS。 |
| discussion log 和 checkpoint 存在 | approved | `process/discussions/CP2-CR019-SCENARIO-DISCUSSION-LOG.md`；`process/checks/CP2-CR019-DISCUSSION-CHECKPOINT.json` | 无 CP2 blocker。 |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 是否接受 UC-15 至 UC-18 作为 CR-019 场景基线 | approved | `process/USE-CASES.md` | 覆盖阶段六 admission、QMT C/S bridge、safety gate、后置能力。 |
| 2 | 是否接受 REQ-138 至 REQ-160 作为 CR-019 需求基线 | approved | `process/REQUIREMENTS.md` | 覆盖 D1-D7、QMT C/S 模块、C 侧接口形态、FastAPI、安全、部署、stage gate、fallback、后置能力。 |
| 3 | 是否接受 D1-D7 作为后续 HLD / ADR 输入 | approved | `process/CLARIFICATION-LOG.md`；CR-019 | 用户已在 CR intake 中批准。 |
| 4 | 是否接受 Q-039 至 Q-044 的状态安排 | approved | `process/CLARIFICATION-LOG.md` | Q-040 / Q-043 已 resolved；Q-039 / Q-041 / Q-042 / Q-044 不阻断 CP2，但阻断 CP5 / 实现。 |
| 5 | 是否确认 CP2 不授权实现或真实操作 | approved | REQ-152；CR-019 Out of Scope | FastAPI 实现、依赖变更、真实 QMT、凭据、fetch、写湖、publish、simulation 均仍 blocked。 |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| 人工结论为 approved / changes_requested / rejected | approved | 本文件“人工审查结果” | 用户已回复“同意你的方案”。 |
| 无 CP2 blocker 未处理 | approved | CP2 自动预检；Decision Brief | 自动预检已判定 0 blocker。 |
| CP3 输入明确 | approved | Q-039 至 Q-044；REQ-138 至 REQ-160 | 可交给 meta-se。 |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| CP2 人工审查稿 | `checkpoints/CP2-CR019-REQUIREMENTS-BASELINE.md` | approved | 本文件。 |
| 场景基线 | `process/USE-CASES.md` | approved | v1.10。 |
| 需求基线 | `process/REQUIREMENTS.md` | approved | v1.11。 |
| 澄清日志 | `process/CLARIFICATION-LOG.md` | approved | Q-039 至 Q-044 留给 CP3 / HLD，其中 Q-040 和 Q-043 已 resolved。 |
| CP1 / CP2 自动检查 | `process/checks/CP1-CR019-USE-CASE-COMPLETENESS.md`；`process/checks/CP2-CR019-REQUIREMENTS-BASELINE.md` | approved | 均 PASS。 |

## 人工审查结果

- 结论：`approved`
- 审查人：user
- 审查时间：2026-05-30T17:12:54+08:00
- 修改意见：同意推荐方案；授权 meta-po 组织并推进项目。
- 风险接受项：接受 CR-019 CP2 基线进入 CP3；仍不授权 FastAPI 实现、依赖变更、真实 QMT / MiniQMT / XtQuant 操作、真实发单 / 撤单 / 账户查询、凭据读取、真实 provider fetch、真实 lake 写入、publish、真实 broker lake 写入或 simulation / live run。
