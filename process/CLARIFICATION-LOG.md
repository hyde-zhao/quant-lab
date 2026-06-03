---
status: active
created_at: "2026-05-13"
created_by: "meta-pm"
---

# 澄清与调研日志

## 修订记录

| 日期 | 记录人 | 事项 | 结果 |
|---|---|---|---|
| 2026-05-13 | meta-pm | 初始化阶段零快速调研 | 基于用户输入和官方页面核验，形成初始范围判断 |
| 2026-05-13 | meta-pm | Review Round 1 需求阶段整改 | 补齐阶段零结构、状态化 Q-001/Q-002/Q-003，并将 blocking/required 项关联到 USE-CASES/REQUIREMENTS |
| 2026-05-14 | meta-pm | 需求确认前草稿刷新 | 根据 meta-po 交接文件追加 HLD 前必须确认问题 Q-004 至 Q-011，并将复权、时点、缺失数据、非 PIT 股票池和报告 metadata 限制项回写需求草稿 |
| 2026-05-14 | meta-pm | 数据源限速需求刷新 | 根据数据源限速交接文件追加 HLD 前确认问题 Q-012 至 Q-019，并将节流、退避、断点续传、raw 缓存、manifest、质量报告、最近 N 个交易日回补和失败降级回写需求草稿 |
| 2026-05-23 | meta-pm | CR-011 因子研究生产级数据补齐 | 增量新增 UC-08 与 REQ-071 至 REQ-082，保留实验 17-21 旧基线并固化生产级数据准入、因子审计和稳健性验证边界 |
| 2026-05-25 | meta-pm | CR-013 unsupported data 与 claim boundary | USE-CASES 按 CR 决策保持不变；REQUIREMENTS 增量升级到 v1.6，新增 REQ-083 至 REQ-087，固化 2020-2024 full-history 不得外推、真实 VWAP / 分钟执行价 blocked、unsupported register 文档和报告声明边界、无 provider/lake/credential/old data 权限 |
| 2026-05-26 | meta-pm | CR-014 A 股 since-inception 生产级全历史数据湖需求澄清 | 增量新增 UC-09 与 REQ-088 至 REQ-097，保留 CR-010/012/013 旧基线，固化全 A current truth、证券生命周期、P0 分层、catalog current pointer、增量刷新 / replay、DuckDB 只读候选、权限边界和 claim boundary；本增量待 CP2 用户确认 |
| 2026-05-27 | meta-po | CR-015 / CR-016 / CR-017 intake 决策澄清 | 将 QMT foundation、QMT activation 与复权双视图压缩为 5 个待决策问题 D-ALL-01 至 D-CR16-01，并生成 CP2 intake decision brief，等待用户确认 |
| 2026-05-27 | meta-pm | CR-015 / CR-016 / CR-017 场景与需求基线增量刷新 | 用户已 approve CP2 intake 全部推荐方案；增量新增 UC-10 至 UC-12、REQ-098 至 REQ-122，保留 UC-01 至 UC-09 与 REQ-001 至 REQ-097，记录 REQUIRED_FOR_CP3 开放问题 |
| 2026-05-28 | meta-po | CR-015 / CR-016 / CR-017 CP3 审批回填 | 用户已 approve CP3 HLD/ADR 推荐方案；Q-030 至 Q-038 更新为 RESOLVED_CP3，可进入 Story Plan / CP4，仍不授权 LLD、代码实现、真实 QMT 操作、真实抓取或真实写湖 |
| 2026-05-30 | meta-pm | CR-019 阶段六多因子模拟盘架构与 FastAPI bridge 需求澄清 | 已记录 D1-D7 已确认决策；新增 UC-15 至 UC-18 与 REQ-138 至 REQ-158；无阻断 CP2 的新增问题，CP3 需冻结 FastAPI 绑定 / 鉴权 / endpoint schema / fallback 细节 |
| 2026-05-30 | meta-po | CR-019 Q40 与 QMT C/S 模块补充澄清 | 用户同意 Q40 推荐方案；新增 QMT 独立 C/S 模块要求：C 侧位于 local_backtest 暴露统一 Python 接口，S 侧部署在 Windows 并通过 REST 转换为 QMT 接口调用；C 侧接口形态作为 Q-044 / CP2 决策项 |
| 2026-05-31 | meta-pm | CR-025 Backtrader optional execution backend hardening CP2 前澄清 | 基于 CR-025 与 CR-019 follow-up 台账完成阶段零调研、Scenario Gray Areas desk review、UC-19 与 REQ-161 至 REQ-168 增量；不发起 CP2 人工门禁，不实现代码，不修改依赖，不触发真实 broker/QMT/provider/lake/publish |
| 2026-05-31 | meta-po | CR-025 CP2 修改意见：production-grade research-to-execution 目标澄清 | 用户澄清目标不是开发框架级 Backtrader/lightweight 回测框架，而是生产级策略研究回测、模拟盘和实盘框架；CR-025 修订为研究执行语义对照与 target portfolio / order intent 衔接，QMT 真实运行仍由 CR-020..CR-024 承接 |
| 2026-06-01 | meta-po | CR-025 CP2 approved 与 Backtrader 本地项目 HLD 分析要求 | 用户批准推进 CR-025，并要求 meta-se 在 CP3/HLD 充分分析 `/home/hyde/download/backtrader`，对比可借鉴、可适配、可移植和禁止移植模块；源码级移植只作为 HLD 决策项，不构成实现授权 |

## 调研发现（2026-05-31，CR-025）

### 现有可复用资源

- `process/changes/CR-025-BACKTRADER-OPTIONAL-EXECUTION-BACKEND-HARDENING-2026-05-31.md` 已明确文档处理决策：`USE-CASES.md` 与 `REQUIREMENTS.md` 采用原文档更新候选，旧基线保留；Backtrader optional backend 从 CR-019 follow-up Track B 转为正式 CR，但 CP2/CP3/CP5/CP8 均未通过。
- `process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md` 已将 `CR-025 backtrader_w6` 标记为 active，目标为 Backtrader optional execution backend hardening，启动条件为 clean feed、PIT、复权、benchmark 和候选策略稳定性证据齐全，完成条件为执行语义差异有量化报告且依赖隔离可验证。
- 既有 `USE-CASES.md` 已有 UC-18 后置能力边界，既有 `REQUIREMENTS.md` 已有 `REQ-070`、`REQ-139`、`REQ-155`，可作为 CR-025 增量的旧基线，不需要删除或重排。
- CR-019 已明确 Backtrader 不属于阶段六 P0，不阻断日频多因子 admission，也不替代 lightweight 主路径。

### 平台能力约束

- 当前仍为 production 模式，场景主体是 local_backtest 目标产物，不是 meta-flow 自我开发。
- 本轮用户限定只修改 `process/CLARIFICATION-LOG.md`、`process/USE-CASES.md`、`process/REQUIREMENTS.md`、`process/checks/CP1-CR025-USE-CASE-COMPLETENESS.md` 和 `process/handoffs/META-PM-CR025-REQ-CLARIFICATION-2026-05-31.md`。
- 不允许实现代码、不允许新增 Backtrader 依赖、不允许修改 `pyproject.toml` / `uv.lock`、不允许运行 Backtrader、不允许触发真实数据 / QMT / provider / lake / publish。
- CR-025 不授权真实 broker、Backtrader live store、QMT / MiniQMT / XtQuant、simulation、live、account query、cancel、order submit、provider fetch、lake write、broker lake write、catalog publish 或凭据读取。

### 对需求的初步影响

- 需要把 UC-18 的 deferred Backtrader 能力增量展开为 UC-19，明确 optional research backend、默认 lightweight 主路径、依赖隔离、clean feed、semantic diff report 和安全计数。
- 需要新增 REQ-161 至 REQ-168，保留 REQ-070 / REQ-139 / REQ-155 的旧基线，不把旧需求改写成新的编号体系。
- 需要将 `USE-CASES.md` 与 `REQUIREMENTS.md` 当前状态切回 draft / ready_for_design=false，等待 meta-po 后续 CP2 人工确认；本轮不把 CP2 标为 approved。
- 本轮信息足以形成 CP1 PASS：无阻断性问题需要追问；CP3 仍需冻结 optional extra 策略、adapter 边界、semantic diff schema 和最小回归范围。

## CR-025 Scenario Gray Areas Desk Review（2026-05-31）

| 灰区 ID | 问题 | 推荐理解 | 备选理解 | 影响 / 取舍 | 状态 |
|---|---|---|---|---|---|
| SGA-025-01 | Backtrader 是 optional research backend，还是替代 lightweight 主路径？ | 推荐：optional research backend，默认 lightweight 主路径不变。 | 备选：迁移到 Backtrader 主路径。 | 推荐方案回归面小且符合 CR-025；备选会扩大依赖、架构和测试范围，应另起设计决策。 | resolved-from-CR |
| SGA-025-02 | Backtrader 依赖是否进入默认安装 / 默认测试？ | 推荐：CP5 前不改依赖，后续采用 optional extra + lazy import。 | 备选：默认依赖引入。 | 推荐方案保护未安装环境和轻量主路径；备选会导致依赖变更和默认测试风险，需 CP5 批准。 | resolved-from-CR |
| SGA-025-03 | clean feed 与执行语义差异如何验收？ | 推荐：先做 clean feed gate，再输出 lightweight vs Backtrader semantic diff report。 | 备选：只看最终收益指标。 | 推荐方案可解释成交、现金、成本、滑点和净值差异；备选无法定位语义差异。 | resolved-from-desk-review |
| SGA-025-04 | 是否允许真实 broker / QMT / provider / lake / publish？ | 推荐：全部不授权，安全计数必须为 0。 | 备选：接入 Backtrader broker 或 provider。 | 推荐方案符合研究路线；备选会触发真实运行和数据授权，应另起 CR。 | resolved-from-CR |
| SGA-025-05 | CR-025 是否应开发框架级回测内核，还是服务生产级 research-to-execution 路线？ | 推荐：服务 production-grade research-to-execution 路线；CR-025 负责研究执行语义对照与 target portfolio / order intent 衔接。 | 备选：迁移 / 自研完整回测或事件驱动框架。 | 推荐方案对齐用户真实目标，并避免许可证、维护和回归风险；备选需另起架构 CR。 | resolved-by-user |

## CR-025 默认决策与开放项（2026-05-31）

| ID | 状态 | 问题 | 默认处理 / 推荐方案 | 是否阻断 CP2 | 关联需求 |
|---|---|---|---|---|---|
| Q-045 | RESOLVED_FROM_CR | Backtrader 是否替代 lightweight engine？ | 不替代；默认主路径仍为 lightweight engine，Backtrader 仅显式选择时作为 optional research backend。 | 否 | REQ-161, REQ-166, REQ-167 |
| Q-046 | RESOLVED_FROM_CR | Backtrader 依赖是否现在引入？ | CP5 前不改依赖；后续若实现，采用 optional extra / lazy import；未安装时返回 `backend_unavailable`。 | 否 | REQ-162, REQ-167, REQ-168 |
| Q-047 | RESOLVED_FROM_DESK_REVIEW | Backtrader 输入数据如何约束？ | 只能消费本地 clean feed；缺 PIT、`available_at`、复权、benchmark、tradability、cost 或 quality 时返回 blocked。 | 否 | REQ-163 |
| Q-048 | REQUIRED_FOR_CP3 | semantic diff report 的最终 schema 和阈值如何冻结？ | CP3/HLD 冻结调仓、成交、现金、成本、滑点、税费、净值和差异字段；本轮只定义验收方向。 | 否；阻断 CP3 设计完成 | REQ-164 |
| Q-049 | RESOLVED_FROM_CR | CR-025 是否授权真实 broker、QMT、provider、lake、publish 或凭据读取？ | 不授权；安全计数全部为 0；任何真实运行或数据写入需独立 CR / per-run 授权。 | 否 | REQ-165, REQ-168 |
| Q-050 | RESOLVED_BY_USER | CR-025 目标是否为框架级回测内核开发？ | 否。用户目标是生产级策略研究回测、模拟盘和实盘框架；CR-025 应服务 research-to-execution 路线，不复制 Backtrader 源码、不迁移主路径、不自研完整事件驱动框架。 | 否 | REQ-161, REQ-169, REQ-172 |
| Q-051 | REQUIRED_FOR_CP3 | research output 到 target portfolio / order intent 的字段合同如何冻结？ | CP3/HLD 冻结 strategy_id、run_id、signal_date、target_trade_date、symbol、target_weight/target_qty、research_adjustment_policy、execution_price_policy、cost_config_ref、data_lineage_ref、limitations 等最小字段。 | 否；阻断 CP3 设计完成 | REQ-169 |

## 2026-05-31 CR-025 场景与需求增量摘要

| 类别 | 纳入内容 | 落点 |
|---|---|---|
| 用户真实意图 | 用户要求生产级策略研究回测、模拟盘和实盘框架；CR-025 不做框架级回测内核迁移，而是让研究执行语义对照、依赖隔离、clean feed、semantic diff 和 target portfolio / order intent 衔接可评审。 | `process/USE-CASES.md` v1.12 UC-19；`process/REQUIREMENTS.md` v1.13 REQ-161 至 REQ-172 |
| 候选理解与取舍 | 候选 A：Backtrader 替换主路径，统一到外部框架，功能可能更完整但依赖和回归面大；候选 B：Backtrader 作为显式 optional research backend，轻量主路径保留，范围小且符合 CR-025。推荐 B。 | SGA-025-01；UC-19；REQ-161 |
| 推荐范围 | Scope 为 production-grade research-to-execution 三条主线映射、optional reference 选择、依赖隔离、未安装降级、clean feed gate、semantic diff report、target portfolio / order intent 衔接、lightweight 主路径回归、安全计数和 CP5 前不得实现。 | `USE-CASES.md` UC-19 / TS-025；`REQUIREMENTS.md` REQ-161 至 REQ-172 |
| 明确排除 | 本轮不实现代码、不新增依赖、不运行 Backtrader、不接真实 broker / QMT / provider / lake / publish、不读取凭据、不覆盖报告、不把 Backtrader 结果作为 production truth 或 QMT admission。 | `USE-CASES.md` Out of Scope；`REQUIREMENTS.md` Out of Scope |
| 成功指标 | 新增 SM-33 至 SM-40，覆盖 lightweight 默认路径、依赖隔离、clean feed、执行语义差异、无真实操作、三条主线映射、order intent 衔接和禁止框架级扩张。 | `process/USE-CASES.md` 成功指标 |
| 测试场景 | 新增 TS-025-01 至 TS-025-10，覆盖默认路径、lazy import、clean feed gate、semantic diff、安全计数、声明边界、门控不越级、三条主线 tracking、order intent 字段和禁止框架级扩张。 | `process/USE-CASES.md` CR-025 验证场景矩阵 |
| 风险与影响 | 主要风险为 Backtrader 替代主路径、依赖泄漏、clean feed 绕过、语义差异不可解释、真实 broker 范围膨胀、结果被误当作 QMT admission、tracking 单线化、order intent 衔接缺失和框架级扩张。 | `process/REQUIREMENTS.md` RA-057 至 RA-065 |
| 待用户决策 | CP2 需确认 CR-025 增量基线是否接受推荐范围；若 approve，仅表示接受需求 / 场景范围，不授权实现、依赖变更、真实 broker/QMT/provider/lake/publish。 | 交回 meta-po 发起 CP2；本轮不发起人工门禁 |

### CP2 Decision Brief 输入（CR-025）

| 字段 | 内容 |
|---|---|
| 用户真实意图 | 建设生产级策略研究回测、模拟盘和实盘框架；CR-025 只负责研究执行语义对照、依赖隔离、clean feed、semantic diff 和 target portfolio / order intent 衔接，使后续 HLD/LLD 可评审；不替代轻量主路径，不接真实 broker。 |
| 认知盲区补充 | optional semantic reference 仍可能带来默认依赖泄漏、未安装环境失败、执行语义不可比、clean feed 绕过、报告声明误用、order intent 衔接缺失和真实 broker 范围膨胀风险，需在 CP2 前纳入需求。 |
| Scenario Gray Areas 处理结果 | 已 desk review SGA-025-01 至 SGA-025-05；已写入 `process/discussions/CP2-CR025-SCENARIO-DISCUSSION-LOG.md` 与 `process/checks/CP2-CR025-DISCUSSION-CHECKPOINT.json`；结论已落入 `USE-CASES.md`、`REQUIREMENTS.md` 和本日志。 |
| Deferred Ideas | Backtrader live broker / store、替换 lightweight 主路径、provider/lake/publish 由 Backtrader 触发、Backtrader 对照作为 QMT admission pass、复制 / 移植 Backtrader 源码、自研完整事件驱动框架、CR-025 内直接启动 QMT gateway / simulation / live 均延后或排除。 |
| 候选理解与取舍 | 推荐 production-grade research-to-execution route 下的 optional semantic reference 与 order intent 衔接；备选为主路径迁移、完整交易平台评估或真实 broker 接入。推荐方案范围可控、可验证且服务生产路线；备选需另起 CR 和更高风险授权。 |
| 推荐范围 | UC-19、SM-33 至 SM-40、TS-025-01 至 TS-025-10、REQ-161 至 REQ-172；CP2 approve 只确认需求范围，不授权实现、依赖变更、源码移植、服务启动或真实运行。 |
| 场景充分性判断 | 已覆盖用户、任务、动机、时间、环境、方式、异常、集成和数据生命周期维度；CP1 可 PASS。 |
| 风险与影响 | 主要风险记录为 RA-057 至 RA-065；无阻断 CP2 的开放问题，Q-048 与 Q-051 留给 CP3/HLD 冻结。 |

## 调研发现（2026-05-30，CR-019）

### 现有可复用资源

- `process/changes/CR-019-STAGE6-MULTIFACTOR-SIMULATION-ARCHITECTURE-2026-05-30.md` 已明确文档处理决策：`USE-CASES.md` 与 `REQUIREMENTS.md` 均采用原文档增量更新，旧基线保留；D1-D7 已获用户批准。
- `docs/QMT-SIMULATION-LIVE-RUNBOOK.md` 与 `docs/QMT-INCIDENT-PLAYBOOK.md` 已提供 QMT stage gate、per-run authorization、runbook、对账、kill switch、recovery 和禁止真实操作的治理边界；这些是 CR-019 stage gate 的输入，不构成真实 QMT 授权。
- `docs/ROADMAP.md` 已把 Backtrader 定位为 optional backend，把 Qlib 定位为 isolated runner，把分钟 / Level2 能力定位为后置触发能力。
- 阶段六外部学习资料与 stage6-simulation 三份计划已明确：既有多因子 / 低波 production rerun 当前未通过模拟盘准入；阶段六目标应转为重新制定 A 股多因子策略并形成 admission package。
- 迅投 QMT 系统说明文档可作为 QMT 模拟运行、模型交易、文件交互、Level2 能力背景，但不得推断当前项目已具备真实账户、模拟盘、Level2 或交易权限。

### 平台能力约束

- 当前仍为 production 模式，场景主体是 local_backtest 目标产物，不是 meta-flow 自我开发。
- 本轮范围只允许更新 `process/USE-CASES.md`、`process/REQUIREMENTS.md`、`process/CLARIFICATION-LOG.md`、`process/discussions/`、`process/checks/` 和 `process/handoffs/`。
- 不允许实现 FastAPI、不新增依赖、不启动服务、不调用真实 QMT / MiniQMT / XtQuant、不读取凭据、不执行真实 provider fetch、不写真实 data / reports / delivery。
- QMT C/S bridge 只能进入需求和 HLD 输入；simulation endpoint 必须 later-gated，不能因服务存在、endpoint 可见或 dry-run pass 自动解禁。

### 对需求的初步影响

- 需要新增阶段六多因子 admission 场景，明确旧失败策略不得包装为可申请模拟盘。
- 需要把 D7 主选从 Q-038 的 signed file drop 更新为 Windows QMT FastAPI 本地服务，同时保留 signed file drop 为 dry-run / blocked fallback。
- 需要把 dry-run / readonly / simulation-gated 分层写入需求，明确 allowed endpoint 与 later-gated endpoint 的区别。
- 需要把 Backtrader、Qlib、分钟数据、Level2 写成后置触发条件和 Deferred Ideas，避免范围膨胀。

## CR-019 已确认决策 D1-D7（2026-05-30）

| 决策 ID | 用户确认结论 | 状态 | 影响面 | 落点 |
|---|---|---|---|---|
| D1 | Backtrader 后置为 optional execution backend。 | RESOLVED | 范围、依赖、执行对照 | UC-18；REQ-139；REQ-155 |
| D2 | Qlib 后置为 isolated runner。 | RESOLVED | 研究框架、ML workflow、依赖边界 | UC-18；REQ-140；REQ-156 |
| D3 | 分钟数据不作为 P0，只做后置 Spike。 | RESOLVED | 数据范围、执行价、计划复杂度 | UC-18；REQ-141；REQ-157 |
| D4 | QMT xtdata 不进入 WSL 主路径；最终 simulation 前采用 Windows QMT bridge，WSL 不直接依赖 xtquant。 | RESOLVED | 部署架构、安全边界、QMT adapter 归属 | UC-16；REQ-142；REQ-149 |
| D5 | 暂不申请 QMT Level2。 | RESOLVED | 数据权限、成本、微观结构范围 | UC-18；REQ-143；REQ-158 |
| D6 | shadow + 连续 5 个真实交易日 dry-run 后再申请 QMT simulation。 | RESOLVED | stage gate、admission package、授权 | UC-15；UC-17；REQ-144；REQ-154 |
| D7 | WSL 与 Windows QMT 节点第一版桥接采用 FastAPI 本地服务，而不是 signed file drop 主路径。 | RESOLVED | API 合同、部署、fallback、HLD/ADR | UC-16；UC-17；REQ-145 至 REQ-150 |

## 调研发现（2026-05-27）

### 现有可复用资源

- `checkpoints/CP2-CR015-CR016-CR017-INTAKE-DECISION-BRIEF.md` 已记录用户在 2026-05-27T22:50:13+08:00 approve 全部推荐方案，D-ALL-01 至 D-CR16-01 可作为本轮需求基线输入。
- `process/changes/CR-015-QMT-TRADING-FOUNDATION-2026-05-27.md`、`process/changes/CR-016-QMT-SIMULATION-LIVE-ACTIVATION-2026-05-27.md`、`process/changes/CR-017-ADJUSTMENT-POLICY-DUAL-VIEW-SUPPORT-2026-05-27.md` 均明确 `USE-CASES.md` / `REQUIREMENTS.md` 采用原文档更新，旧基线保留。
- `process/USE-CASES.md` 已有 UC-01 至 UC-09 confirmed 基线；本轮只追加 UC-10 至 UC-12，不重排旧场景。
- `process/REQUIREMENTS.md` 已有 REQ-001 至 REQ-097 confirmed 基线；本轮只追加 REQ-098 至 REQ-122，不重排旧需求。

### 平台能力约束

- 当前仍为 production 模式，场景主体是目标本地研究 / 数据湖 / QMT 交易接入工具，不是 meta-flow 自身。
- 本轮 meta-pm 写入范围限定为 `process/USE-CASES.md`、`process/REQUIREMENTS.md`、`process/CLARIFICATION-LOG.md`；不修改 STATE、HLD、ADR、Story、代码、测试、README、docs、reports 或检查点文件。
- CR-015 / CR-016 / CR-017 均不授权实现、不授权真实发单、不授权真实抓取或写湖、不授权读取 `.env`、token、账户、session、cookie 或交易密码。
- QMT 交易接入引入外部交易接口、Windows QMT / MiniQMT 节点、OMS、broker lake、pre-trade hard block、凭据和运行治理，后续必须保持 standard 流程和严格 review gate。

### 对需求的初步影响

- CR-017 需要先冻结 raw/qfq/hfq/returns_adjusted 与 QMT raw 执行价格隔离，避免复权价误入真实委托、成交和 broker 对账。
- CR-015 可并行做无真实发单 foundation：OMS、adapter、订单状态机、pre-trade hard block、broker lake 和 shadow / dry-run / mock 验证。
- CR-016 真实激活后置：必须等待 CR-015 foundation 和 CR-017 口径边界，且每次真实 QMT 操作必须有 per-run 授权、runbook、对账和 kill switch。
- HLD 阶段仍需冻结公式、schema、broker lake、状态机、风控清单、阶段准入阈值、限价 / 保护价、对账阈值和 kill switch 行为，这些问题不阻塞已批准的 CP2 intake，但应作为 REQUIRED_FOR_CP3 开放项跟踪。

## 调研发现（2026-05-26）

### 现有可复用资源

- `process/changes/CR-014-A-SHARE-SINCE-INCEPTION-PRODUCTION-DATA-LAKE-2026-05-26.md` 已批准进入 standard 变更流程，并明确文档处理方式为原文档增量更新：`USE-CASES.md` 保留旧场景基线并新增 A 股 since-inception production data lake 场景，`REQUIREMENTS.md` 保留 REQ-001 至 REQ-087 并追加新需求。
- 现有 `process/HLD-DATA-LAKE.md` 已定义数据湖分层、publish gate、P0 dataset、catalog current truth、consumer 只读边界、CR-013 full-history blocked / unsupported register 边界，可作为后续 HLD 增量输入；本轮不修改 HLD。
- 当前代码事实中已存在 `market_data/lake_layout.py` 的 `raw` / `manifest` / `canonical` / `gold` / `quality` / `catalog` 路径契约，以及 `market_data/catalog.py` 的 JSON catalog current truth 结构；本轮只把这些事实转为需求，不修改代码。
- `.agents/skills/use-case-discovery/SKILL.md`、`requirement-extraction/SKILL.md`、`requirement-clarifier/SKILL.md` 可复用为本轮场景增量、需求提取和澄清问题记录的执行规范。

### 平台能力约束

- 当前目标仍为本地 Python 研究工具 / 生产数据湖，不是 meta-flow 自我开发；`engagement_mode=production`，场景主体为目标产物而非当前工作流。
- CR-014 不授权 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 读取 / 列出 / 迁移 / 复制 / 比对 / 删除、旧 reports 覆盖或 DuckDB 依赖引入。
- DuckDB 在本阶段只能作为 HLD 待决策的 read-only query / audit / feature extraction 候选能力；不得在需求阶段承诺依赖或用 `.duckdb` 替代 Parquet lake / catalog / manifest。
- meta-pm 本轮写入范围限定为 `process/USE-CASES.md`、`process/REQUIREMENTS.md`、`process/CLARIFICATION-LOG.md`；CP1 / CP2 自动检查文件和人工 checkpoint 由 meta-po 后续发起。

### 对需求的初步影响

- CR-014 将目标从 limited-window / 2020-2024 roadmap 升级为 A 股证券自存在 / 上市日起至当前交易日的 production current truth，必须新增 `UC-09` 和 `REQ-088` 起的需求，而不是覆盖 UC-08 或 REQ-083 至 REQ-087。
- 新需求必须显式处理全 A universe、证券生命周期 / 退市 / 代码变更、P0 dataset 分层、catalog current pointer、增量刷新 / replay、DuckDB 只读候选、权限计数、claim boundary 和可量化验证场景。
- `USE-CASES.md` 与 `REQUIREMENTS.md` 的 CR-014 增量应回到 draft / ready_for_design=false，等待 CP2 用户确认后再进入 HLD。

## 调研发现（2026-05-13）

### 现有可复用资源

- `process/REQUEST.md` 已登记本地日频组合回测层的原始目标、推荐目录、第一版能力、数据路线、框架路线和动量策略核心函数示意。
- `process/INPUT-INDEX.md` 已索引 AKShare 与 RQAlpha 官方依据，可作为数据源风险和后续框架取舍背景。
- 当前需求阶段不复用大型量化框架作为第一版主路径；RQAlpha、Backtrader、vectorbt、bt 仅作为后续迁移或优化候选。
- 当前仓库内已存在 `process/USE-CASES.md` 与 `process/REQUIREMENTS.md` draft，本轮采用增量修订，不替换为新文档。

### 平台能力约束

- 目标平台是本地 Python 研究工具，不是 Claude Code、Codex Skill、OpenClaw 或聚宽自动化集成。
- Python 工程必须遵循项目 uv 规则：依赖声明以 `pyproject.toml` 为准，锁定以 `uv.lock` 为准，执行入口使用 `uv run`，不得提交 `.venv/`。
- 第一版回测与参数扫描主路径必须支持离线执行；前提是当前仓库根下三类 parquet 文件已存在。
- 聚宽在第一版中只作为人工少量候选验证平台；不自动调用、不自动联网、不轮询任务。

### 对需求的初步影响

- 工程根统一为当前仓库根 `/home/hyde/workspace/local_backtest`，原始请求中的示意路径只保留为背景，不作为实施根。
- 数据链路拆为“独立数据准备”和“离线只读回测主路径”；AKShare 拉取可后置为独立脚本或后续 Story。
- 第一版必须显式披露固定成分股快照和幸存者偏差，避免把学习型结果误解为实盘级结论。
- 本地与聚宽的校验目标是方向一致性和差异可解释，不是逐日净值一致。
- 参数扫描规范输出统一为 `reports/momentum_param_sweep_local.csv`，聚宽回填候选清单统一为 `reports/momentum_candidates_local.csv`。

## 阶段零快速调研

### 已核验事实

| 主题 | 结论 | 来源 |
|---|---|---|
| AKShare 定位 | AKShare 是 Python 财经数据接口库，适合学习和研究阶段的数据获取；其声明数据用于学术研究、仅供参考，接口可能受不可控因素影响。 | https://pypi.org/project/akshare/ |
| RQAlpha 定位 | RQAlpha 官方文档将其定位为覆盖数据获取、算法交易、回测引擎、模拟交易、实盘交易到数据分析的程序化交易方案，并强调配置方式和扩展性。 | https://rqalpha.readthedocs.io/zh-cn/develop/ |

### 初始判断

- 当前阶段优先建设项目内轻量日频组合回测层，不引入完整事件驱动框架。
- 第一版数据链路采用“独立数据准备 + parquet 本地缓存 + 回测只读本地缓存”。
- 第一版以动量策略为验收主线，RSI、MACD 作为后续扩展策略。
- 后续 HLD 阶段需要重新核对具体 AKShare 接口字段、复权字段、沪深 300 成分股接口和交易日历接口；这些不在需求阶段提前锁死实现细节。

## 澄清问题状态

| ID | 状态 | 问题 | 默认处理 | 是否阻塞 HLD | 关联需求 |
|---|---|---|---|---|---|
| Q-001 | RESOLVED_DEFAULT | 第一版是否需要自动联网拉取 AKShare 数据，还是先假设 parquet 已存在？ | 第一版回测/扫描主路径只读本地 parquet、manifest 和质量报告摘要；联网能力只能存在于独立数据准备/更新流程，且该流程必须节流、有限重试、断点续传和输出 raw/manifest/质量报告。 | 否；HLD 需要同时设计离线回测主路径和独立数据准备入口，但不得把联网能力放入回测/扫描/候选筛选主路径。 | REQ-016, REQ-021, REQ-034, REQ-047 - REQ-057 |
| Q-002 | RESOLVED_FOR_HLD | 手续费、滑点、印花税的默认费率是否固定为某组值？ | 成本接口和扣除规则已定：使用 `commission_rate`、`slippage_rate`、`sell_tax_rate`；默认费率可在 HLD/LLD 作为显式配置确认，报告必须记录实际值。 | 否；费率默认值待 HLD/LLD 显式配置确认，但不阻塞 HLD。 | REQ-009, REQ-035 |
| Q-003 | RESOLVED_DEFAULT | 本地回测结果与聚宽校验的“方向一致”如何量化？ | 不要求逐日净值一致；比较候选排序方向、收益/回撤量级、换手特征和差异解释。 | 否；已形成验收口径。 | REQ-030, RA-006 |
| Q-004 | REQUIRED_FOR_HLD | 默认复权口径采用前复权、后复权还是不复权？本地回测与聚宽候选验证是否必须使用同一口径？ | 暂不指定默认值；需求只固化“同一运行口径一致、不得混用、报告 metadata 记录实际口径”。 | 是；HLD 必须给出默认复权口径、配置项和报告字段。 | REQ-037, RA-007 |
| Q-005 | REQUIRED_FOR_HLD | 第一版成交假设如何定义：T+1 开盘、T+1 收盘、VWAP 近似，还是仅按收盘到收盘收益归属？ | 暂定硬约束为 T 日收盘后生成信号、T+1 或之后成交；成交价口径和收益归属待 HLD 确认。 | 是；HLD 必须定义成交价、成交日期、成本扣除和收益归属。 | REQ-005, REQ-008, REQ-023 |
| Q-006 | REQUIRED_FOR_HLD | 股票池表达采用固定当前沪深 300 快照文件，还是需要在第一版引入日期维度或 PIT 接口占位？ | 第一版按固定当前沪深 300 快照处理，并标记 `is_pit_universe=false` 与幸存者偏差；PIT universe provider 列为后续 P1 增强。 | 是；HLD 必须确定 `index_members.parquet` schema、快照日期字段和未来 PIT 扩展点。 | REQ-003, REQ-031, REQ-042 |
| Q-007 | REQUIRED_FOR_HLD | 缺失价、停牌和无成交如何处理：剔除、留现金、延后成交、失败，还是按不同场景分层处理？ | 当前需求禁止静默填充；历史窗口不足和信号端点缺失剔除，成交价缺失或无成交留现金/记录未成交/失败的细分规则待 HLD 确认。 | 是；HLD 必须给出数据加载、信号排名和组合成交三层处理表。 | REQ-006, REQ-008, REQ-039, REQ-040 |
| Q-008 | REQUIRED_FOR_HLD | 第一版 parquet 数据字段最低要求是否强制包含 `available_at`、`adjustment_policy`、成交状态或成交量？ | 当前需求允许日线价格在 HLD 批准后用“收盘后可用”规则推导 `available_at`；事件字段第一版默认不纳入。最低字段集仍需 HLD 确认。 | 是；HLD 必须明确最小 schema、可选字段和缺字段失败行为。 | REQ-021, REQ-037, REQ-038 |
| Q-009 | REQUIRED_FOR_HLD | 涨跌停字段是否第一版强制输入？若不强制，报告限制项和候选聚宽验证如何表达该偏差？ | 当前需求将涨跌停撮合列为第一版可延后但必须警示；涨跌停约束作为后续 P1 增强。 | 是；HLD 必须决定涨跌停字段是否进入第一版 schema 或仅进入 metadata 限制项。 | REQ-015, REQ-041, REQ-044 |
| Q-010 | REQUIRED_FOR_HLD | 未来函数校验做到哪个层级：数据加载层、信号层、股票池层、事件层、报告审计层，还是全部覆盖？ | 当前需求要求所有参与决策字段满足 `available_at <= decision_time`；具体校验层级和错误策略待 HLD 确认。 | 是；HLD 必须定义校验边界、失败策略和测试样例。 | REQ-038, REQ-045, RA-008 |
| Q-011 | REQUIRED_FOR_HLD | 财报披露日和财报/公告事件是否明确列为第一版 Out of Scope？ | 当前需求默认财报披露日和事件字段第一版 Out of Scope；若纳入则必须提供事件级 `available_at` 并调整需求范围。 | 是；HLD 前需确认是否保持 Out of Scope，以免设计阶段误引入事件数据。 | REQ-015, REQ-041, REQ-045, A-009 |
| Q-012 | REQUIRED_FOR_HLD | 数据准备默认节流参数如何取值：`request_interval_seconds`、`batch_size`、`max_concurrency` 的默认值分别是多少？ | 当前需求只固化三项均可配置，且默认保守串行抓取；`max_concurrency` 建议默认 1，但默认值仍待 HLD 前确认。 | 是；HLD 必须给出默认节流参数、配置位置和覆盖测试方式。 | REQ-047, REQ-048, REQ-049 |
| Q-013 | REQUIRED_FOR_HLD | `max_retries` 默认上限和 `backoff_policy` 采用固定退避还是指数退避？退避细节记录到 manifest 还是日志？ | 当前需求只固化重试必须有限、不可无限循环，且退避过程必须可记录到 manifest 或日志。 | 是；HLD 必须定义默认重试次数、退避算法、最大等待边界和记录字段。 | REQ-050, REQ-055 |
| Q-014 | REQUIRED_FOR_HLD | 断点续传状态由 manifest、独立 checkpoint 文件还是二者共同承载？批次状态枚举如何定义？ | 当前需求只固化断点续传必须基于 manifest/checkpoint，跳过已成功批次，除 `force_refresh` 或最近 N 交易日回补外不重复抓取。 | 是；HLD 必须定义 checkpoint 载体、批次 ID、状态枚举和恢复算法。 | REQ-051, REQ-055 |
| Q-015 | REQUIRED_FOR_HLD | 最近 N 个交易日回补的默认 N 取值是多少，是否对价格、复权因子、成分股和交易日历采用同一窗口？ | 当前需求只固化 N 可配置，且必须基于交易日历而不是自然日。 | 是；HLD 必须给出默认 N、适用数据类型和与增量缺口补齐的优先级关系。 | REQ-053, REQ-054, A-012 |
| Q-016 | REQUIRED_FOR_HLD | raw 缓存保留策略是什么：长期保留、按批次滚动保留、按大小清理，还是由用户手动清理？ | 当前需求只固化 raw 缓存必须存在，标准化 parquet 必须可从 raw 派生；保留周期和清理策略待确认。 | 是；HLD 必须定义 raw 路径组织、命名、保留/清理策略和复现边界。 | REQ-052, RA-012 |
| Q-017 | REQUIRED_FOR_HLD | manifest schema 的文件格式、字段类型、路径、状态枚举和版本字段如何定义？ | 当前需求已列出 manifest 至少记录字段，但未锁定 JSON、JSONL、YAML 或 parquet 等具体格式。 | 是；HLD 必须定义 manifest schema、兼容升级规则和与质量报告的关联方式。 | REQ-051, REQ-055 |
| Q-018 | REQUIRED_FOR_HLD | 数据质量报告阈值如何定义：缺失率、失败率、重复记录、异常价格达到什么条件时阻塞数据准备或仅警告？ | 当前需求只固化质量报告必须记录统计和异常定位；阻塞阈值与质量状态枚举待确认。 | 是；HLD 必须定义质量阈值、`quality_status` 枚举、失败/警告策略和报告字段。 | REQ-056, RA-012 |
| Q-019 | REQUIRED_FOR_HLD | 数据源不可用时，本地缓存新鲜度如何披露：按自然日、交易日、最近成功批次还是覆盖区间缺口计算？ | 当前需求只固化本地 parquet 合规时回测/扫描继续离线运行，并披露最近成功更新时间、数据新鲜度、失败批次和可能影响。 | 是；HLD 必须定义新鲜度计算方式、报告展示字段和不可用数据源的降级提示。 | REQ-034, REQ-057 |
| Q-020 | REQUIRED_FOR_CP2 | CR-014 的全 A universe 覆盖边界是否包含沪深北全部 A 股、科创板、创业板、北交所、退市 / 摘牌证券和历史代码变更？ | 默认按“全 A 证券自存在 / 上市日起至当前交易日”处理，并要求生命周期缺口进入 `required_missing` / `blocked_claims`。 | 是；CP2 未确认前不得进入 HLD。 | REQ-088, REQ-089, RA-026, RA-027 |
| Q-021 | REQUIRED_FOR_CP2 | CR-014 P0 dataset 清单是否沿用 `prices`、`adj_factor`、`hs300_index`、`trade_calendar`、`index_members`、`index_weights`、`stock_basic`，并新增 lifecycle / code-change 能力为 P0？ | 默认沿用 CR-010 P0 dataset，并把生命周期 / 代码变更作为全 A current truth 的必需能力；W3 / minute / tick / Level2 仍需单独决策。 | 是；CP2 未确认前不得进入 HLD。 | REQ-090, REQ-096 |
| Q-022 | REQUIRED_FOR_CP2 | “当前交易日”是否定义为最近已闭市交易日，还是允许盘中 / 当日未闭市数据进入 current truth？ | 默认采用最近已闭市且交易日历 `is_open=true` 的交易日；盘中或未闭市数据不进入 production current truth。 | 是；CP2 未确认前不得进入 HLD。 | REQ-088, REQ-097 |
| Q-023 | REQUIRED_FOR_CP2 | DuckDB 是否只作为 read-only query / audit / feature extraction 候选，且依赖引入必须等 HLD/CP3/CP5 决策？ | 默认只读候选，不新增依赖，不写 `.duckdb` 事实源，不替代 Parquet lake / catalog / manifest。 | 是；CP2 未确认前不得进入 HLD。 | REQ-093, RA-030 |
| Q-024 | REQUIRED_FOR_CP2 | CR-014 后续真实 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 操作和旧 reports 覆盖是否均需单独授权？ | 默认全部保持 0；任何真实执行必须由后续 Story / CP5 和用户显式授权控制。 | 是；CP2 未确认前不得进入 HLD 或实现。 | REQ-094, REQ-095, RA-031 |
| Q-025 | RESOLVED_USER_APPROVED | CR-015 / CR-016 / CR-017 的推进顺序是否采用“CR-017 先冻结口径边界、CR-015 foundation 可并行设计、CR-016 真实激活后置”的混合推进方式？ | 用户已在 CP2 intake approve 推荐方案：采用混合推进，先冻结复权与 raw 交易价边界；CR-015 做无真实发单 foundation；CR-016 等 CR-015 foundation 和 CR-017 口径边界后推进。 | 否；CP2 intake 已批准，可进入 HLD；CP3 仍需冻结实现级细节。 | CR-015, CR-016, CR-017, REQ-098 - REQ-122 |
| Q-026 | RESOLVED_USER_APPROVED | QMT 接入是否采用 Windows QMT / MiniQMT 节点 + XtQuant 外部 Python API + OMS + adapter，并禁止策略直接调用 QMT API？ | 用户已 approve 推荐方案：采用 adapter / OMS 隔离，策略层不得直接调用 QMT。 | 否；HLD 可按该边界设计。 | CR-015, REQ-105 |
| Q-027 | RESOLVED_USER_APPROVED | CR-015 是否必须建立本地订单状态机、外置 broker lake 和 pre-trade hard risk gate，且默认只允许 shadow / dry-run / mock？ | 用户已 approve 推荐方案：必须建立订单状态机、外置 broker lake 和 pre-trade hard block；CR-015 不授权真实发单，默认 shadow / dry-run / mock。 | 否；HLD 可按该安全底座设计。 | CR-015, CR-016, REQ-107 - REQ-110 |
| Q-028 | RESOLVED_USER_APPROVED | CR-017 是否采用 `prices_raw` + `adj_factor` 作为事实源，并派生独立 `prices_qfq`、`prices_hfq`、`returns_adjusted`，且 QMT 只使用 raw / broker price？ | 用户已 approve 推荐方案：采用 raw + adj_factor 事实源和独立派生视图；qfq 记录 `as_of_trade_date`；QMT 禁止使用复权价下单。 | 否；HLD 可按该数据口径设计。 | CR-017, CR-015, CR-016, REQ-098 - REQ-104 |
| Q-029 | RESOLVED_USER_APPROVED | CR-016 是否采用 `shadow -> QMT 模拟盘 -> 实盘只读 -> 小资金实盘 -> 放大资金` 的阶段激活路径，并要求 runbook、对账、kill switch 和 per-run 授权？ | 用户已 approve 推荐方案：采用阶段激活；CR-017 不阻断技术模拟盘，但阻断生产策略复权治理声明和资金放大。 | 否；HLD 可按该阶段路径设计。 | CR-016, CR-017, REQ-112 - REQ-120 |
| Q-030 | RESOLVED_CP3 | CR-017 的 qfq/hfq 公式、provider `adj_factor` 字段方向、复权因子可用时间和异常价格解释如何冻结？ | CP3 已批准推荐方案：冻结 raw + `adj_factor` 事实源，qfq 以 `as_of_trade_date` 为锚点，hfq 以 provider/base date 为锚点，`provider_factor_direction` 必填，异常价格进入 quality fail/warn。 | 否；已由 `checkpoints/CP3-CR015-CR016-CR017-HLD-REVIEW.md` 批准，可进入 Story Plan，仍不授权实现或真实写入。 | REQ-098 - REQ-100, REQ-122 |
| Q-031 | RESOLVED_CP3 | CR-017 的 dataset/view schema、旧 qfq 兼容入口和迁移策略如何定义？ | CP3 已批准推荐方案：独立 `prices_raw`、`adj_factor`、`prices_qfq`、`prices_hfq`、`returns_adjusted` view；旧 qfq 只读保留，兼容入口输出 migration summary。 | 否；已由 CP3 批准，可进入 Story Plan，仍不授权实现或真实写入。 | REQ-099, REQ-101, REQ-103, REQ-122 |
| Q-032 | RESOLVED_CP3 | CR-015 的 broker lake root、schema、保留策略、脱敏字段和与研究数据湖的分层边界如何定义？ | CP3 已批准推荐方案：broker lake 外置 root，schema 覆盖 order/fill/position/asset/error/reconciliation/incident，默认 retention 3 年或用户配置，敏感字段脱敏 / 禁入库。 | 否；已由 CP3 批准，可进入 Story Plan，仍不授权真实账户查询、发单或写入 broker lake。 | REQ-108, REQ-111, REQ-122 |
| Q-033 | RESOLVED_CP3 | CR-015 OMS 状态机如何映射 QMT / mock adapter 事件，unknown、timeout、partial fill、撤单失败和重试策略如何处理？ | CP3 已批准推荐方案：OMS 状态机覆盖 accepted/partial/filled/cancel_pending/canceled/rejected/failed/unknown/timeout/manual_review/frozen；unknown/timeout 不自动成功。 | 否；已由 CP3 批准，可进入 Story Plan，仍不授权真实 QMT API。 | REQ-107, REQ-116, REQ-122 |
| Q-034 | RESOLVED_CP3 | CR-015 pre-trade hard risk gate 的精确规则、阈值、配置位置和失败行为如何定义？ | CP3 已批准推荐方案：现金、100 股整手、T+1 可卖、可用持仓、价格口径、重复 intent、单票 / 组合限额、异常价格均 hard block，失败时 adapter_calls=0。 | 否；已由 CP3 批准，可进入 Story Plan，仍不授权实现或真实发单。 | REQ-109, REQ-110, REQ-122 |
| Q-035 | RESOLVED_CP3 | CR-016 各阶段进入 / 退出 / 回退的量化阈值如何定义，尤其模拟盘、实盘只读、小资金实盘和资金放大？ | CP3 已批准推荐方案：stage gate 固定 `shadow -> simulation -> live_readonly -> small_live -> scale_up`，每阶段有准入、退出、回退、观察窗口、资金上限和失败阈值；CR-017 未验证前阻断 scale_up。 | 否；已由 CP3 批准，可进入 Story Plan，仍不授权模拟盘或实盘真实操作。 | REQ-112, REQ-119, REQ-122 |
| Q-036 | RESOLVED_CP3 | CR-016 T+1 限价 / 保护价策略、超时撤单、失败重试和未成交处理如何定义？ | CP3 已批准推荐方案：T 日收盘后信号，T+1 限价 / 保护价；保护带基于 raw close 或 broker reference price 可配置；超时未成交默认撤可撤单，单 run 自动重试上限为 1。 | 否；已由 CP3 批准，可进入 Story Plan，仍不授权真实发单或撤单。 | REQ-115, REQ-122 |
| Q-037 | RESOLVED_CP3 | CR-016 盘前 / 盘中 / 盘后对账差异阈值、处理责任和 kill switch 触发 / 恢复条件如何定义？ | CP3 已批准推荐方案：盘前 / 盘中 / 盘后对账覆盖委托、成交、持仓、资产、现金；超阈值进入 manual_review 或 kill switch；恢复需对账 pass + 人工接管记录。 | 否；已由 CP3 批准，可进入 Story Plan，仍不授权真实账户查询或实盘运行。 | REQ-116, REQ-117, REQ-122 |
| Q-038 | RESOLVED_CP3 | Linux 研究节点与 Windows QMT / MiniQMT 交易节点之间的部署、通信、鉴权、隔离和运维责任如何定义？ | CP3 已批准推荐方案：Linux 研究节点与 Windows QMT 节点解耦，默认 signed file drop + ack/error enum，后续可升级本地 RPC；adapter 只在 Windows；责任分为 research owner、trading node owner、approver。 | 否；已由 CP3 批准，可进入 Story Plan，仍不授权部署或真实 QMT API 调用。 | REQ-105, REQ-111, REQ-113, REQ-122 |
| Q-039 | REQUIRED_FOR_CP3 | FastAPI bridge 的 bind host/port、防火墙、endpoint schema、鉴权方式、过期 / 轮换和日志脱敏细节如何冻结？ | 用户已明确第一版服务只在局域网运行，可不做应用层鉴权；CP3 推荐冻结为“受控局域网 + Windows gateway 命令 + 可选最简 token/HMAC”，并明确不做鉴权不等于不做 QMT 功能接口。 | 否；不阻断 CP2，阻断 FastAPI gateway HLD/LLD。 | REQ-146, REQ-148, REQ-149, REQ-151 |
| Q-040 | RESOLVED | 阶段六多因子 admission 的 benchmark 组合、tracking / excess 口径和策略冻结字段如何定义？ | 用户已同意推荐方案：采用“多基准看板 + primary benchmark 规则”，同时输出 HS300、ZZ500、ZZ1000 和中证全指，并按策略 universe / 风格选择 primary benchmark；具体阈值由 CP3 冻结。 | 否；作为 CP3 admission 设计输入。 | REQ-138, REQ-154, A-051 |
| Q-041 | REQUIRED_FOR_CP3 | FastAPI gateway 支持完整 QMT simulation / live / account / cancel / query 接口后，真实转发所需的 run mode、stage gate、risk gate、kill switch 和必要授权上下文如何定义？ | 用户已明确 QMT 功能接口必须完整支持；CP3 推荐把“接口覆盖”和“运行门控”拆开：endpoint 类别完整，真实转发由 run mode / stage gate 控制，若实在需要鉴权则采用最简 token/HMAC。 | 否；不阻断 CP2，阻断 gateway HLD/LLD 和真实转发实现。 | REQ-146, REQ-147, REQ-148 |
| Q-042 | REQUIRED_FOR_CP3 | FastAPI gateway 失败时 fallback 的切换条件、处理责任和是否保留 signed file drop 如何定义？ | 用户澄清 gateway 是局域网 Windows 服务；CP3 推荐默认 fallback 为 blocked-only 或人工 dry-run file，不允许自动绕过 gateway 触发真实 QMT；signed file drop 仅作为备选人工处理，不再作为完整功能替代路径。 | 否；不阻断 CP2，阻断 fallback 实现。 | REQ-145, REQ-150 |
| Q-043 | RESOLVED | Backtrader、Qlib、分钟数据和 Level2 后置能力的 Story 顺序、Spike 进入条件和退出标准如何定义？ | 用户已同意：Backtrader 后置为 W6 optional execution backend，Qlib 后置为 W7 isolated runner，分钟数据和 Level2 作为后置 Spike；未触发前不进入阶段六 P0。 | 否；作为 CP3/Story Plan 范围控制输入。 | REQ-139 - REQ-143, REQ-155 - REQ-158 |
| Q-044 | REQUIRED_FOR_CP3 | QMT C 侧对 local_backtest 暴露的统一接口应采用 Python 函数 / client、CLI-first，还是 Python client 主接口 + 薄 CLI？ | 推荐“Python client / 函数调用为主 + 薄 CLI 为辅”：内部策略、OMS、测试和运行治理直接调用类型化 Python client；CLI 只复用同一 client 做人工 smoke、运维检查和脚本入口。备选 A：CLI-first，利于手工操作但内部调用和测试成本高；备选 B：纯 Python-only，内部集成最简单但缺少运维入口。 | 否；不阻断 CP2，阻断 C 侧接口 HLD/LLD。 | REQ-159, REQ-160 |
| Q-045 | RESOLVED_FROM_CR | Backtrader 是否替代 lightweight engine？ | 不替代；默认主路径仍为 lightweight engine，Backtrader 仅显式选择时作为 optional research backend。 | 否；作为 CR-025 CP2 范围基线。 | REQ-161, REQ-166, REQ-167 |
| Q-046 | RESOLVED_FROM_CR | Backtrader 依赖是否现在引入？ | CP5 前不改依赖；后续若实现，采用 optional extra / lazy import；未安装时返回 `backend_unavailable`。 | 否；作为 CR-025 CP2 范围基线。 | REQ-162, REQ-167, REQ-168 |
| Q-047 | RESOLVED_FROM_DESK_REVIEW | Backtrader 输入数据如何约束？ | 只能消费本地 clean feed；缺 PIT、`available_at`、复权、benchmark、tradability、cost 或 quality 时返回 blocked。 | 否；作为 CR-025 CP2 范围基线。 | REQ-163 |
| Q-048 | REQUIRED_FOR_CP3 | semantic diff report 的最终 schema 和阈值如何冻结？ | CP3/HLD 冻结调仓、成交、现金、成本、滑点、税费、净值和差异字段；本轮只定义验收方向。 | 否；不阻断 CP2，阻断 CR-025 HLD 完成。 | REQ-164 |
| Q-049 | RESOLVED_FROM_CR | CR-025 是否授权真实 broker、QMT、provider、lake、publish 或凭据读取？ | 不授权；安全计数全部为 0；任何真实运行或数据写入需独立 CR / per-run 授权。 | 否；作为 CR-025 CP2 范围基线。 | REQ-165, REQ-168 |

## 2026-05-30 CR-019 场景与需求增量摘要

| 类别 | 纳入内容 | 落点 |
|---|---|---|
| 用户真实意图 | 用户要把阶段六推进为 A 股多因子策略的模拟盘准入路线，同时修正 local_backtest / Windows QMT 桥接主方案为 QMT C/S 模块：C 侧暴露统一 Python 接口，S 侧部署在 Windows 并通过 REST 转换为 QMT 接口；核心目标是安全地达到“可申请模拟盘”，不是绕过 stage gate 直接 simulation。 | `process/USE-CASES.md` v1.10 UC-15 至 UC-18；`process/REQUIREMENTS.md` v1.11 REQ-138 至 REQ-160 |
| 候选理解与取舍 | 候选 A：包装既有失败策略进入模拟盘，范围小但结论错误；候选 B：重建 production-ready 多因子 admission，范围更大但符合阶段六目标。候选 C：继续 signed file drop 主路径，简单但实时性和可观测性弱；候选 D：FastAPI 本地服务主路径，复杂度更高但符合 D7。用户已批准 B + D，signed file drop 保留 fallback。 | `process/discussions/CP2-CR019-SCENARIO-DISCUSSION-LOG.md`；UC-15 至 UC-17；REQ-138、REQ-145 |
| 推荐范围 | Scope 为阶段六多因子 admission、D1-D7、完整 QMT FastAPI gateway 合同、Windows 可安装 / 可运行 gateway 命令、完整 QMT 功能 endpoint matrix、运行门控、可选最简鉴权、fallback、日志脱敏和后置能力触发条件。 | `USE-CASES.md` Out of Scope / 边界说明；`REQUIREMENTS.md` 需求上下文 / CR-019 FastAPI Bridge 契约 |
| 明确排除 | 本轮不实现代码、不新增依赖、不启动 FastAPI、不调用真实 QMT / MiniQMT / XtQuant、不读取凭据、不真实 provider fetch、不写真实 data / reports / delivery；QMT 文档只作为能力背景。 | `USE-CASES.md` Out of Scope；`REQUIREMENTS.md` 明确排除项；handoff 安全声明 |
| 成功指标 | 新增 SM-27 至 SM-32，覆盖 admission gate、5 日 dry-run、FastAPI 默认安全、WSL/Windows 部署、后置能力边界、日志脱敏和禁止真实操作计数。 | `process/USE-CASES.md` 成功指标 |
| 测试场景 | 新增 TS-019-01 至 TS-019-09，覆盖 D1-D7、旧失败策略 blocked、完整 QMT gateway endpoint matrix、simulation / live / account / cancel / query 运行门控、可选鉴权脱敏、部署边界、fallback、后置触发和 QMT 文档背景边界。 | `process/USE-CASES.md` CR-019 验证场景矩阵 |
| 风险与影响 | 主要风险为 FastAPI 服务被误解为无门控真实 QMT 通道、局域网运行被误写为无风险、鉴权 / 日志脱敏不足、gateway 与回测框架耦合、fallback 误触发真实 QMT、QMT 文档过度推断、旧失败策略被包装、后置能力范围膨胀和 5 日 dry-run 被跳过。 | `process/REQUIREMENTS.md` RA-048 至 RA-055 |
| 待用户决策 | 用户已纠正 Q-039 / Q-041 / Q-042，同意 Q-043，并确认 Q-040 推荐方案；新增 Q-044 需在 CP2/CP3 冻结 C 侧接口形态，当前推荐 Python client / 函数调用为主 + 薄 CLI。 | `checkpoints/CP2-CR019-REQUIREMENTS-BASELINE.md` |

### CP2 Decision Brief 输入（CR-019）

| 字段 | 内容 |
|---|---|
| 用户真实意图 | 构建阶段六 A 股多因子模拟盘准入路线，并采用 Windows QMT FastAPI 本地服务作为 WSL / Windows 桥接主方案，同时维持真实 QMT 操作和 simulation 的严格后置授权。 |
| 认知盲区补充 | FastAPI gateway 必须支持完整 QMT 功能接口；不做应用层鉴权不等于减少 simulation / account / cancel / live 等功能。FastAPI 可用也不等于无门控真实 QMT；QMT 文档能力不等于当前账户权限；旧失败策略不能包装为 admission pass；后置能力不能挤占 P0；fallback 不能自动真实 QMT。 |
| Scenario Gray Areas 处理结果 | 已处理 SGA-019-01 阶段六目标、SGA-019-02 bridge 主方案、SGA-019-03 dry-run/readonly/simulation-gated 安全边界、SGA-019-04 后置能力范围；讨论日志见 `process/discussions/CP2-CR019-SCENARIO-DISCUSSION-LOG.md`，恢复点见 `process/checks/CP2-CR019-DISCUSSION-CHECKPOINT.json`。 |
| Deferred Ideas | Backtrader W6 optional backend、Qlib W7 isolated runner、分钟数据 Spike、Level2 Spike、direct simulation submit、直接迁移到外部框架均延后。 |
| 待人工决策项 | CP2 需确认修订后基线：采纳完整 QMT gateway 接口覆盖、QMT 独立 C/S 模块、Windows 独立 gateway 命令、C 侧 Python client 主接口 + 薄 CLI 推荐、局域网无应用层鉴权或最简 token/HMAC 的鉴权策略、Q-040 已确认多基准 + primary benchmark、Q-043 后置能力顺序。 |

## 2026-05-14 需求刷新摘要

| 类别 | 纳入内容 | 落点 |
|---|---|---|
| 第一版硬约束 | 复权口径一致；T 日收盘后生成信号、T+1 或之后成交；`available_at <= decision_time`；历史窗口不足剔除；缺失价格或无成交不得静默填充；固定当前沪深 300 股票池标记非 PIT 和幸存者偏差；报告 metadata 强制输出限制项。 | `process/USE-CASES.md` v1.2；`process/REQUIREMENTS.md` v1.2 |
| 第一版警示项 | 完整停牌状态、涨跌停撮合、新股上市初期特殊规则、退市整理/摘牌、ST 历史状态、财报披露日、沪深 300 历史成分变化。 | `USE-CASES.md` Out of Scope、边界说明、UC-01/UC-02/UC-06；`REQUIREMENTS.md` REQ-015、REQ-041、风险与假设 |
| 后续增强优先级 | PIT universe provider、交易状态表、涨跌停约束、事件 `available_at`、偏差审计报告。 | `USE-CASES.md` UC-06；`REQUIREMENTS.md` REQ-042 至 REQ-046、M3 |
| HLD 前确认项 | 默认复权口径、成交假设、股票池表达、缺失价/停牌处理、数据字段最低要求、涨跌停字段是否强制、未来函数校验层级、财报是否第一版 Out of Scope。 | Q-004 至 Q-011，状态均为 `REQUIRED_FOR_HLD` |

## 2026-05-14 数据源限速刷新摘要

| 类别 | 纳入内容 | 落点 |
|---|---|---|
| 数据链路边界 | 数据准备/更新流程可联网；回测、扫描、候选筛选和本地差异分析主路径必须物理隔离并离线只读本地 parquet、manifest 和质量报告摘要。 | `process/USE-CASES.md` v1.3 边界说明、UC-01、UC-03；`process/REQUIREMENTS.md` v1.3 REQ-016、REQ-034、REQ-057 |
| 数据源限速与节流 | 数据准备默认保守串行抓取，支持 `request_interval_seconds`、`batch_size`、`max_concurrency`，且相邻请求间隔必须可验证。 | `USE-CASES.md` UC-01；`REQUIREMENTS.md` REQ-047 至 REQ-049 |
| 重试退避与断点续传 | `max_retries` 必须有上限，`backoff_policy` 必须可记录；断点续传基于 manifest/checkpoint，不重复已成功批次，除非强制刷新或最近 N 个交易日回补。 | `USE-CASES.md` UC-01；`REQUIREMENTS.md` REQ-050、REQ-051 |
| raw 缓存与增量更新 | raw 缓存必须存在，标准化 parquet 必须可从 raw 派生；默认只补缺口，并支持基于交易日历的最近 N 个交易日回补。 | `USE-CASES.md` UC-01；`REQUIREMENTS.md` REQ-052 至 REQ-054 |
| manifest 与质量报告 | manifest 记录批次、数据源、接口、请求参数、范围、请求时间、成功项、失败项、错误信息、重试次数、raw 路径、标准化输出路径、覆盖范围和最终状态；质量报告记录覆盖、缺失、失败、字段缺失、重复、异常价格、回补数量、最近成功更新时间和数据新鲜度。 | `USE-CASES.md` UC-01、UC-03、UC-06；`REQUIREMENTS.md` 数据准备产物契约、报告 schema、REQ-055、REQ-056 |
| 失败降级 | 数据源不可用时，若本地 parquet 覆盖区间和 schema 合规，回测/扫描/候选筛选仍可离线运行，并披露失败项与新鲜度。 | `USE-CASES.md` 边界说明、UC-03；`REQUIREMENTS.md` REQ-034、REQ-057、RA-010、RA-011 |
| HLD 前确认项 | 默认节流参数、重试次数/退避策略、断点续传状态承载、最近 N 日回补默认值、raw 缓存保留策略、manifest schema、质量报告阈值、数据源不可用时的新鲜度披露。 | Q-012 至 Q-019，状态均为 `REQUIRED_FOR_HLD` |

## Review Round 1 整改摘要

| 类别 | 处理结果 | 落点 |
|---|---|---|
| 场景补强 | 补齐 UC-04 差异分析输出、本地/聚宽/平台边界、固定成分股快照和幸存者偏差、第一版离线只读 parquet 主路径。 | `process/USE-CASES.md` v1.1 |
| 成功指标 | 修订 SM-05 为可验收的扫描耗时记录和平台任务减少指标；解释“实践六”和“方向一致”。 | `process/USE-CASES.md` v1.1 |
| 覆盖自检 | D1 补齐 UC-05/UC-06。 | `process/USE-CASES.md` v1.1 |
| 需求补强 | 补齐工程根、路径归属、数据 schema、`close_df`、交易日序、无前视偏差、成本模型、指标假设、扫描 CSV、候选清单、过拟合警示和报告边界。 | `process/REQUIREMENTS.md` v1.1 |
| 澄清项 | Q-001/Q-002/Q-003 均已状态化，不存在未处理的开放澄清项。 | 本文件 |

## 2026-05-23 CR-011 场景与需求增量摘要

| 类别 | 纳入内容 | 落点 |
|---|---|---|
| 用户真实意图 | 用户希望把实验 17-21 的探索性结论从 fixed snapshot / proxy benchmark / close proxy 升级为可审计、可复现、可分层验证的生产级因子研究输入；旧结论不删除，只保留为历史 baseline。 | `process/USE-CASES.md` v1.5 UC-08；`process/REQUIREMENTS.md` v1.5 REQ-071 至 REQ-082 |
| 候选理解与取舍 | 候选 A：只补真实 `hs300_index`，成本低但仍无法支撑生产级因子结论；候选 B：同时补 benchmark、PIT、可交易性、执行价、复权/公司行动、行业市值风格、容量成本、因子审计和稳健性验证，范围更大但与 CR-011 目标一致。本轮采用候选 B。 | `process/USE-CASES.md` UC-08；`process/REQUIREMENTS.md` CR-011 生产级因子研究数据契约 |
| 推荐范围 | Scope 为生产级因子研究数据准入、声明门控、新版报告产物和安全授权边界；Out of Scope 为覆盖旧报告、需求阶段真实联网/写湖/凭据读取、超出 readiness 覆盖窗口的完整历史 PIT 或生产 current truth 声明。 | `process/USE-CASES.md` Out of Scope / UC-08；`process/REQUIREMENTS.md` 明确排除项 |
| 成功指标 | 新增 SM-10 至 SM-13，覆盖生产级准入、因子审计面板完整性、稳健性验证覆盖和真实数据授权/凭据边界。 | `process/USE-CASES.md` 成功指标；`process/REQUIREMENTS.md` REQ-071 至 REQ-082 |
| 风险与影响 | 主要风险为只补局部数据导致旧结论被误升级、limited window 被外推、辅助数据缺失却声明中性化/容量可交易、因子预处理不可审计、真实执行泄露凭据或误写 lake。 | `process/REQUIREMENTS.md` RA-016 至 RA-021 |
| 待 meta-se 消费 | HLD 需要冻结 CR-011 数据域 gate、执行价策略、行业/风格/容量模型、factor audit panel schema、稳健性验证矩阵、报告产物路径和真实执行授权边界；CP3/CP4 通过前不得进入 LLD，CP5 批次确认前不得实现代码。 | 后续 `process/HLD.md` / `process/HLD-DATA-LAKE.md` / ADR / Story Plan |

## 2026-05-25 CR-013 需求增量摘要

| 类别 | 纳入内容 | 落点 |
|---|---|---|
| 用户真实意图 | 用户已批准将 CR-013 的 unsupported data 与 claim boundary 纳入需求基线，防止 CR-012 limited-window pass 被误外推为 2020-2024 或全历史生产级可用。 | `process/REQUIREMENTS.md` v1.6 REQ-083 |
| 声明边界 | 2020-2024 readiness 仍为 `research_limited_only`，10 个正式 dataset 均为 `limited_window_only`；真实 VWAP / VWAP fill / 分钟执行价仍为 blocked。 | `process/REQUIREMENTS.md` v1.6 REQ-083, REQ-084 |
| unsupported register | `unsupported_data_register.csv` 中 research-only、unsupported、contract-supported-but-unavailable 项必须进入用户文档和报告声明边界，且 `pass_denominator=excluded` 不得计入生产级 pass。 | `process/REQUIREMENTS.md` v1.6 REQ-085 |
| 权限边界 | 本轮不授权 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 读取或旧报告覆盖；后续真实补数或数据接入必须另行显式授权。 | `process/REQUIREMENTS.md` v1.6 REQ-086, REQ-087 |

## 2026-05-26 CR-014 场景与需求增量摘要

| 类别 | 纳入内容 | 落点 |
|---|---|---|
| 用户真实意图 | 用户要把数据湖目标从 limited-window / roadmap-only 升级为生产级 A 股全历史数据湖，覆盖 A 股证券自存在 / 上市日起至当前交易日的可审计 current truth，而不是继续停留在 2020-2024 blocked 或 2025-2026 limited-window 通过声明。 | `process/USE-CASES.md` v1.6 UC-09；`process/REQUIREMENTS.md` v1.7 REQ-088 |
| 候选理解与取舍 | 候选 A：只扩展 2020-2024 roadmap，改动小但仍不能支撑用户要求的全 A since-inception current truth；候选 B：定义全 A universe、证券生命周期、P0 分层、catalog current pointer、增量刷新 / replay 和 claim boundary，范围更大但与 CR-014 目标一致。本轮采用候选 B。DuckDB 作为候选查询 / 审计能力纳入 HLD 待决策，不在需求阶段承诺依赖。 | `process/USE-CASES.md` UC-09；`process/REQUIREMENTS.md` REQ-088 至 REQ-097 |
| 推荐范围 | Scope 为全 A since-inception current truth 范围、证券生命周期 / 退市 / 代码变更、P0 dataset 分层、catalog current pointer、增量刷新 / replay、DuckDB 只读候选、权限计数、claim boundary 和 TS-014 验证矩阵；Out of Scope 为本阶段真实抓取、写湖、凭据读取、旧 `data/**` 操作、旧报告覆盖、DuckDB 依赖修改和 `.duckdb` 事实源替代。 | `process/USE-CASES.md` Out of Scope / UC-09；`process/REQUIREMENTS.md` 明确排除项 |
| 成功指标 | 新增 SM-14 至 SM-18，覆盖全 A since-inception current truth 可声明性、证券生命周期覆盖、P0 分层与 current pointer 可审计、增量刷新 / replay 稳定性和 DuckDB 候选边界。 | `process/USE-CASES.md` 成功指标；`process/REQUIREMENTS.md` REQ-088 至 REQ-097 |
| 测试场景 | 新增 TS-014-01 至 TS-014-07，覆盖全 A coverage denominator、退市 / 代码变更、P0 分层 / current pointer、增量刷新 / replay、DuckDB 只读边界、权限计数和 claim boundary。 | `process/USE-CASES.md` CR-014 验证场景矩阵；`process/REQUIREMENTS.md` REQ-096 |
| 风险与影响 | 主要风险为 universe 边界未冻结、生命周期缺口导致幸存者偏差、validate pass 污染 current pointer、replay 误触发 provider、DuckDB 被误解为已批准依赖或事实源、权限边界被误读为真实执行授权。 | `process/REQUIREMENTS.md` RA-026 至 RA-031 |
| 待 CP2 用户确认 | 需要确认全 A 覆盖边界、P0 dataset 清单、当前交易日口径、DuckDB 只读候选定位、以及真实 provider / lake / credential / old data / reports 操作均需单独授权。 | Q-020 至 Q-024 |

### CP2 Decision Brief 输入（CR-014）

| 字段 | 内容 |
|---|---|
| 用户真实意图 | 建设生产级 A 股全历史数据湖，使全 A 证券从存在 / 上市日起至当前交易日的 P0 数据、生命周期、catalog current pointer、增量刷新和声明边界可审计、可重放、可持续维护。 |
| 候选理解与取舍 | 候选 A 是继续补 2020-2024 / limited-window 缺口，优点是范围小，缺点是不能满足全 A since-inception current truth；候选 B 是升级为全 A production data lake，优点是匹配用户目标，缺点是需要 HLD/Story/权限/测试全链路重做。本轮推荐候选 B。DuckDB 只作为 HLD 待决策候选，不作为本阶段依赖承诺。 |
| 推荐范围 | 纳入全 A universe、证券生命周期、P0 分层、catalog current pointer、增量刷新 / replay、DuckDB 只读候选、权限边界和 claim boundary；排除真实抓取、写湖、凭据读取、旧数据操作、旧报告覆盖、DuckDB 依赖修改和实现级代码变更。 |
| 成功指标 | SM-14 至 SM-18；验收口径为 P0 coverage numerator / denominator、生命周期缺口、current pointer publish、replay no-provider/no-credential、权限计数 0、DuckDB dependency_changes=0、blocked_claims 完整。 |
| 风险与影响 | 若 CP2 不确认覆盖边界和 P0 清单，HLD 无法冻结 dataset / Story；若 DuckDB 角色不清，可能引入不必要依赖或事实源冲突；若权限边界不清，可能误触发真实 provider / lake / credential / old data 操作。 |
| 待用户决策 | Q-020 全 A 覆盖边界；Q-021 P0 dataset 清单；Q-022 当前交易日口径；Q-023 DuckDB 只读候选定位；Q-024 真实执行授权边界。 |

### CR-014 默认假设

| ID | 默认假设 | 关联需求 |
|---|---|---|
| A-021 | “当前交易日”默认指最近已闭市且交易日历 `is_open=true` 的交易日，最终口径待 CP2/HLD 确认。 | REQ-088, REQ-097 |
| A-022 | P0 dataset 默认沿用 CR-010 的 7 个 P0 dataset，并把生命周期 / 代码变更作为全 A current truth 必需能力，最终清单待 CP2/HLD 决策。 | REQ-089, REQ-090 |
| A-023 | DuckDB 默认只作为 HLD 待决策的 read-only query / audit / feature extraction 候选，不进入需求阶段依赖。 | REQ-093 |
| A-024 | 本轮只修改 `process/USE-CASES.md`、`process/REQUIREMENTS.md`、`process/CLARIFICATION-LOG.md`。 | REQ-094 |
| A-025 | 未经后续单独授权，provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 操作、旧 reports 覆盖和 DuckDB 依赖修改均保持 0。 | REQ-094, REQ-095 |

## 2026-05-27 CR-015 / CR-016 / CR-017 场景与需求增量摘要

| 类别 | 纳入内容 | 落点 |
|---|---|---|
| 用户真实意图 | 用户已确认后续会使用 QMT 接口进行模拟盘和实盘，但要求先把复权口径、raw 交易价格、OMS / adapter / broker lake / risk / 运行治理和授权边界写入场景与需求基线，避免未设计先实现或误发真实订单。 | `process/USE-CASES.md` v1.7 UC-10 至 UC-12；`process/REQUIREMENTS.md` v1.8 REQ-098 至 REQ-122 |
| 候选理解与取舍 | 候选 A：先做 QMT 交易接入，复权双视图后置，速度快但容易把复权价误用于交易；候选 B：先冻结 CR-017 raw/qfq/hfq 边界，同时并行设计 CR-015 无真实发单 foundation，CR-016 真实激活后置，范围更大但安全。用户已 approve 候选 B。 | CP2 intake D-ALL-01、D-CR15-01、D-CR15-02、D-CR17-01、D-CR16-01 |
| 推荐范围 | Scope 为 `prices_raw` + `adj_factor` 事实源、qfq/hfq/returns_adjusted 派生、QMT raw 执行价隔离、OMS、QMT adapter、订单状态机、pre-trade hard block、外置 broker lake、shadow / dry-run / mock、阶段激活、runbook、对账、kill switch、per-run 授权和验证矩阵。 | `USE-CASES.md` Out of Scope / 边界说明 / UC-10 至 UC-12；`REQUIREMENTS.md` 需求上下文 / 契约 / REQ-098 至 REQ-122 |
| 明确排除 | 本轮不修改代码、不引入依赖、不读取 `.env` / token / 账户信息、不真实抓取、不写真实 lake、不发布 current pointer、不真实发单 / 撤单 / 账户写操作、不把 broker lake 写入仓库、不把 qfq/hfq 作为 QMT 执行价。 | `USE-CASES.md` Out of Scope；`REQUIREMENTS.md` 明确排除项 |
| 成功指标 | 新增 SM-19 至 SM-24，覆盖 QMT foundation 安全边界、OMS / broker lake 审计、复权双视图、QMT raw 执行价隔离、阶段激活门控、runbook / 对账 / kill switch / per-run 授权。 | `USE-CASES.md` 成功指标 |
| 测试场景 | 新增 TS-015-01 至 TS-016-03 与 TS-017-01 至 TS-017-03，覆盖 QMT API 绕过、pre-trade hard block、OMS 状态机、broker lake 脱敏、raw/qfq/hfq 分层、qfq as-of、单 run 口径、raw 执行价、阶段激活、runbook / 授权、对账和 kill switch。 | `USE-CASES.md` 验证场景矩阵；`REQUIREMENTS.md` REQ-121 |
| 风险与影响 | 主要风险为复权价误入交易执行、qfq as-of 缺失导致历史漂移不可审计、QMT API 绕过 OMS/risk、broker lake 或凭据泄露、状态机未处理 unknown / partial fill、warn-only 风控、阶段推进过快、kill switch / 对账缺失。 | `REQUIREMENTS.md` RA-032 至 RA-041 |
| CP3 决策结果 | 公式和 provider 字段解释、dataset/view schema、broker lake schema、OMS 状态机、pre-trade risk 阈值、阶段准入阈值、限价 / 保护价、对账阈值、kill switch、Linux 研究节点与 Windows QMT 节点通信部署均按推荐方案批准。 | Q-030 至 Q-038；`checkpoints/CP3-CR015-CR016-CR017-HLD-REVIEW.md`；`REQUIREMENTS.md` REQ-122 |

### CP2 Decision Brief 输入（CR-015 / CR-016 / CR-017）

| 字段 | 内容 |
|---|---|
| 用户真实意图 | 在继续保留本地研究 / 数据湖资产的基础上，引入 QMT 模拟盘和实盘能力，但必须先建立价格口径隔离、OMS / adapter / broker lake / risk 安全底座和阶段化运行治理，防止误发单、凭据泄露、复权价下单和未经授权真实操作。 |
| 候选理解与取舍 | 已讨论并批准的候选包括：A. 严格串行先完成 CR-017 再做 QMT，安全但慢；B. QMT 优先，速度快但价格口径和交易风险高；C. 混合推进，先冻结 CR-017 口径边界，CR-015 foundation 并行设计，CR-016 真实激活后置。用户已 approve C。 |
| 推荐范围 | 纳入 CR-017 raw/qfq/hfq/returns_adjusted 与 QMT raw 执行价隔离、CR-015 OMS / QMT adapter / 订单状态机 / broker lake / pre-trade hard block、CR-016 阶段激活 / runbook / 对账 / kill switch / per-run 授权；排除真实发单、真实抓取、写湖、凭据读取、代码实现和资金放大。 |
| 成功指标 | SM-19 至 SM-24；验收口径为真实 QMT API 调用计数 0（未授权）、策略层 QMT 直连 0、qfq/hfq 执行价 hard block、状态机覆盖异常、broker lake 脱敏外置、stage gate 不可跳过、runbook / 对账 / kill switch / per-run 授权完整。 |
| 风险与影响 | 若 CR-017 未冻结，可能复权价误入交易；若 CR-015 缺 OMS / risk / broker lake，真实发单不可审计；若 CR-016 缺 runbook / 对账 / kill switch / per-run 授权，模拟盘或实盘风险不可控；若 CP3 未冻结公式 / 阈值 / 状态机，后续 Story 无法安全拆解。 |
| 待用户决策 | CR-015 / CR-016 / CR-017 的 CP2 intake 与 CP3 HLD / ADR 均已 approve。Q-030 至 Q-038 已按推荐方案收敛；下一步进入 Story Plan / CP4，仍不得进入 LLD、实现或真实 QMT / 数据操作。 |

### CR-015 / CR-016 / CR-017 默认假设

| ID | 默认假设 | 关联需求 |
|---|---|---|
| A-026 | 用户已 approve CP2 intake 全部推荐方案，D-ALL-01 至 D-CR16-01 进入需求基线。 | REQ-098 - REQ-122 |
| A-027 | CR-017 默认采用 `prices_raw` + `adj_factor` 事实源，独立派生 qfq/hfq/returns_adjusted，qfq 记录 `as_of_trade_date`，QMT 只使用 raw / broker price。 | REQ-098 - REQ-104 |
| A-028 | CR-015 默认只允许 shadow / dry-run / mock；真实发单、撤单、账户写操作、凭据读取和真实 broker lake 写入均为 0。 | REQ-105 - REQ-111 |
| A-029 | CR-016 默认按 shadow、模拟盘、实盘只读、小资金实盘、资金放大顺序推进，每次真实 QMT 操作都需要 per-run 授权。 | REQ-112 - REQ-120 |
| A-030 | CR-017 不阻断 CR-016 技术模拟盘，但在实现验证前阻断生产策略复权治理完成声明和资金放大。 | REQ-118 - REQ-120 |
| A-031 | 本轮 meta-pm 不修改代码、不读取 `.env` / token / 账户信息、不真实抓取、不写湖、不发单。 | REQ-104, REQ-110, REQ-114 |
