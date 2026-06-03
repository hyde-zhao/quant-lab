---
tracking_id: "CR-019-FOLLOW-UP-TRACKING"
source_change_id: "CR-019"
status: "cr030-active-follow-up-candidates-open"
created_at: "2026-05-31T10:43:18+08:00"
updated_at: "2026-06-02T23:24:25+08:00"
owner: "meta-po"
cp8_decision: "approved-with-follow-up-tracking"
real_operation_authorization: false
formal_cr_files_precreated: "partial-cr025-closed-cr030-active"
cr_index: "process/changes/CR-INDEX.yaml"
---

# CR-019 Follow-up Tracking

本文件记录 CR-019 CP8 后的后续跟踪项。它不是实现授权，不创建真实运行许可，不替代后续 CR 的 CP2 / CP3 / CP5 / CP6 / CP7 / CP8 门控。

## Scope Boundary

| 边界 | 值 |
|---|---|
| 当前 CR-019 交付状态 | 离线合同 / fixture / dry-run / 文档边界已完成 |
| 当前真实 QMT / MiniQMT / XtQuant 操作授权 | `false` |
| 当前服务启动 / 端口绑定授权 | `false` |
| 当前凭据读取授权 | `false` |
| 当前 provider fetch / lake write / broker lake write / publish 授权 | `false` |
| 当前 simulation / live 授权 | `false` |
| 后续跟踪方式 | 独立 CR / Spike，重新走标准门控 |
| 正式 CR 文件预创建 | `CR-025 closed；CR-030 active；其他候选仍 false` |

## 状态字段约定

| 状态 | 含义 | 处理规则 |
|---|---|---|
| `candidate` | 候选 CR，尚未启动正式 CR | 只保留摘要、触发条件和下一步；不得预创建正式 CR 文件。 |
| `spike_candidate` | 候选 Spike，尚未启动正式 Spike CR | 只保留 Spike 触发条件和证据要求；等待用户选择是否推进。 |
| `active` | 已创建正式 CR，正在推进 | 填写正式 CR 路径、当前门控、阻塞原因和下一步。 |
| `blocked` | 已启动但被外部条件阻塞 | 保留正式 CR 路径、阻塞原因和恢复条件。 |
| `converted-to-spike` | 已从候选 CR 转为正式 Spike CR | 链接正式 Spike CR 文件，后续按 Spike 门控推进。 |
| `closed` | 对应正式 CR 已关闭 | 填写关闭证据，例如 CP8 approved 时间。 |
| `cancelled` | 明确取消，不再推进 | 保留取消理由，不删除候选行。 |
| `superseded` | 被另一个 CR 替代 | 填写替代 CR 路径和替代原因。 |

## 分流总览

| 类别 | 数量 | 阻断当前交付 | 说明 |
|---|---:|---|---|
| 关闭范围 | 2 | 否 | CR-019 当前离线合同 / fixture / dry-run / 文档边界已通过 CP8 关闭；CR-025 当前研究执行语义对齐交付已通过 CP8 关闭。 |
| 不授权范围 | 6 | 否 | 真实 QMT、服务启动、凭据、provider / lake / publish、simulation / live、外部 GitHub 项目依赖 / 源码迁移等均未授权。 |
| 风险接受项 | 2 | 否 | 接受真实运行与后置能力进入后续跟踪，不阻塞 CR-019 当前 CP8。 |
| 活跃后续 CR | 1 | 否 | CR-030 已按用户要求创建正式 CR，当前为 `active-cp2-intake`；仅授权 CR 编写与跟踪同步，不授权实现、依赖变更、外部项目运行或真实操作。 |
| 后续 CR 候选项 | 6 | 否 | CR-020..CR-024、CR-026 为候选 CR；只记录台账，不预创建正式 CR 文件。 |
| 后续 Spike 候选项 | 2 | 否 | CR-027..CR-028 为 Spike 候选；不预创建正式 Spike CR 文件。 |
| 取消 / deferred 项 | 4 | 否 | Backtrader / Qlib / minute / Level2 均保持 deferred / later-gated。 |

## CR Tracking Index Sync

新版 meta-flow 要求状态查询固定输出 `active formal CR`、`blocked formal CR`、`follow-up candidate`、`spike_candidate` 和 `stale_status_conflicts`。本台账的人读候选项已同步到机器索引：

| 标准对象 | 路径 / 状态 | 说明 |
|---|---|---|
| CR tracking index | `process/changes/CR-INDEX.yaml` | 记录 CR-030 active、CR-025 closed、CR-029 closed、CR-020..CR-028 和状态冲突收敛记录。 |
| STATE tracking view | `process/STATE.md.cr_tracking` | 记录 active / candidate / spike / stale conflict 视图。 |
| 一致性检查脚本 | `scripts/check_cr_tracking_consistency.py` | 用于静态检查 CR-019 follow-up 台账、CR-INDEX 和 STATE tracking 是否同步。 |

## Production Research-To-Execution 三条主线视图

用户已在 CR-025 CP2 修改意见中澄清：目标不是开发框架级 Backtrader/lightweight 回测框架，而是生产级策略研究回测、模拟盘和实盘框架。因此本台账除 Track A / Track B 外，补充一层面向推进决策的三条主线视图。

| 主线 | 目标 | 当前承接对象 | 当前状态 | 下一步建议 | 不授权边界 |
|---|---|---|---|---|---|
| A：研究可信度 | 让策略研究、数据、benchmark、PIT、tradability、cost、admission package 可审计、可复跑、可解释 | CR-018 / CR-029 真实数据链路结果；CR-030 多因子研究框架借鉴与研究闭环标准化；后续策略准入修复候选待用户决定 | 数据湖与 benchmark 链路 PASS；阶段六策略准入 blocked，`qmt_admission_allowed_count=0`；CR-030 已创建正式 CR，当前 `active-cp2-intake` | 下一步组织 CR-030 CP2，确认 FactorSpec / FactorRunSpec / IC / RankIC / 分层收益 / 多因子组合 / 实验追踪 / 策略准入包范围，并分流 CR-026 | 不把数据链路 PASS 写成策略可模拟盘；不自动启动 provider / publish / QMT；不安装、clone、运行或迁移 GitHub 项目 |
| B：回测 / 模拟一致性 | 让 lightweight baseline、Backtrader optional semantic reference 和后续 QMT simulation 使用一致的 clean feed、成本、target portfolio / order intent 语义 | CR-025 closed | CP8 approved closed；S01/S04/S02/S03/S05/S06 已 verified；S06 首轮 CP7 FAIL 已由 blocker fix 和 CP7 复验关闭 | 当前关闭；HLD 已冻结 semantic diff schema、order_intent_draft_v1，并记录 `/home/hyde/download/backtrader` 模块级借鉴 / 适配 / 移植候选 / 禁止移植对比 | 不替代 lightweight 主路径；不改依赖、不复制 / 移植 Backtrader 源码、不运行真实 broker / QMT；关闭不授权真实运行 |
| C：QMT 生产执行 | 通过 gateway、simulation、live-readonly、small-live、scale-up 阶段门控逐步进入真实环境 | CR-020..CR-024 candidate | 未启动；真实 QMT、服务启动、simulation/live 均未授权 | 用户可选择启动 CR-020 gateway health 准入；CR-021 以后必须等待前置关闭和 per-run 授权 | 不发单、不撤单、不查真实账户、不读取凭据正文；gateway health 不等于 simulation 授权 |

### Related Formal CR

| CR | 状态 | 来源决策 | 正式 CR 路径 | 与本台账关系 | 当前结论 / 下一步 |
|---|---|---|---|---|---|
| CR-025 | closed | `D-CP8-CR019-05` | `process/changes/CR-025-BACKTRADER-OPTIONAL-EXECUTION-BACKEND-HARDENING-2026-05-31.md` | 研究路线首个正式 CR，由候选转 active 后已 CP8 approved closed；归入回测 / 模拟一致性主线 | CP2 / CP3 approved，CP4 PASS，6 份 LLD 与 6 份 CP5 自动预检已完成，CP5 已 approved；S01/S04/S02/S03/S05/S06 已 verified；用户于 2026-06-02T23:10:16+08:00 回复“好的关闭CR025”。不得依赖变更、不得复制 / 移植 Backtrader 源码实现、不得真实 broker / QMT / provider / lake / publish。 |
| CR-029 | closed | `D-CP8-CR019-02` | `process/changes/CR-029-STAGE6-DATA-LAKE-ADMISSION-BENCHMARK-REAL-RUN-2026-05-31.md` | 独立真实数据湖运行授权 CR，不占用 CR-020..CR-028 候选编号；已从 active tracking 移除 | 真实 benchmark / admission 数据链路可用，但阶段六策略准入 blocked，`qmt_admission_allowed_count=0`；用户已接受结论并关闭 CR-029。 |
| CR-030 | active | `D-CP8-CR019-05` | `process/changes/CR-030-MULTIFACTOR-RESEARCH-FRAMEWORK-REFERENCE-AND-RESEARCH-LOOP-STANDARDIZATION-2026-06-02.md` | 研究可信度主线正式 CR，由候选转 active；用于补齐多因子研究闭环和外部 GitHub 项目借鉴边界 | 当前为 `active-cp2-intake`；下一步进入 CP2 需求 / 场景基线。CR 创建不授权实现、依赖变更、外部项目 clone/install/run/source copy、provider/lake/publish、QMT/simulation/live 或凭据操作。 |

### Stale Status Conflicts

| 冲突 ID | 状态 | 证据 | 处理方式 |
|---|---|---|---|
| STALE-CR019-ACTIVE-CHANGE | resolved | `process/STATE.md.active_change` 曾为 `CR-019`，但 `process/changes/CR-019-STAGE6-MULTIFACTOR-SIMULATION-ARCHITECTURE-2026-05-30.md` 已 `status=closed` | 本轮已将顶层 `active_change` 切换到 `CR-025`；记录保留用于审计。 |
| SYNC-CR029-RELATED-ACTIVE | resolved-closed | CR-029 使用 `parent_cr=CR-019` 和 `source_decision_id=D-CP8-CR019-02`，但不属于 CR-020..CR-028 候选序列 | CR-029 已关闭；相关记录仍在本节、`CR-INDEX.yaml` 和 `STATE.md.cr_tracking` 中保留。 |

## 启动候选 CR 流程

用户决定推进某一候选项时，使用 `@meta-po 启动后续 CR`，并给出台账路径、候选编号和目标摘要。meta-po 必须先读取本台账、`process/STATE.md.active_change` 和所有未关闭正式 CR，完成冲突预检后，才能创建正式 CR 文件并把对应候选项状态改为 `active`。

推荐启动格式：

```text
@meta-po 启动后续 CR：process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md 中的 CR-020。
目标：<本次目标摘要>。
授权边界：<本次是否授权服务启动 / 凭据 / 真实 QMT / provider / lake / publish / simulation/live>。
```

## CR 冲突预检

候选项启动前必须执行下表预检。`candidate` / `spike_candidate` 不占执行锁；只有创建正式 CR 并转为 `active` 后才参与未完成 CR 冲突判断。若存在重叠，默认不得并行推进，必须让用户选择合并到现有 CR、保持候选等待、标记 `blocked`、拆分无冲突子集或标记 `superseded` 并链接替代 CR。

| 检查项 | 结果 | 证据 | 处理结论 |
|---|---|---|---|
| 是否已有 `STATE.md.active_change` | 待启动时检查 | `process/STATE.md` | 若 active_change 非空，比较影响面后决定是否允许并行。 |
| 是否存在未关闭正式 CR | 待启动时检查 | `process/changes/CR-*.md` | 只把 `open` / `active` / `blocked` 正式 CR 视为未完成；候选项不占锁。 |
| 正式文档影响面是否重叠 | 待启动时检查 | 文档处理决策 | 重叠时默认等待或合并，不静默并行。 |
| Story / LLD 批次是否重叠 | 待启动时检查 | Story / CR 影响分析 | 影响同一 Story、LLD 批次或 Wave 时默认阻断并行。 |
| 文件 owner 是否冲突 | 待启动时检查 | Story file_ownership / CR 影响分析 | 冲突文件不得由两个 active CR 同时修改。 |
| 外部接口 / 安全 / 运行授权是否重叠 | 待启动时检查 | Decision Brief / CR | 涉及 QMT、凭据、服务启动、provider、lake、publish、simulation/live 时必须单独决策。 |
| 风险接受项和来源决策是否冲突 | 待启动时检查 | 本台账 / CP8 Decision Brief | 不得用新 CR 隐式覆盖 D-CP8-CR019-02 / D-CP8-CR019-05 的不授权边界。 |

## Track A: QMT Real-run Admission

来源决策：`D-CP8-CR019-02`

目标：把 CR-019 的 QMT C/S bridge 合同逐步推进到真实 Windows 环境和后续运行准入。每一步必须独立授权，前一步通过不自动授权下一步。

| 候选 CR | 名称 | 状态 | 类型 | 优先级 | 影响面 / 冲突键 | 正式 CR 路径 | 当前门控 | 阻塞原因 | 下一步 | 目标 | 启动条件 | 完成条件 | 明确禁止 |
|---|---|---|---|---:|---|---|---|---|---|---|---|---|---|
| CR-020 | QMT Windows gateway 实机部署准入 | candidate | CR | 1 | Windows FastAPI gateway；`trading/qmt_gateway_*`；`docs/QMT-GATEWAY-INSTALL.md`；service_start / port / HMAC | N/A | not-started | 等待用户明确启动 CR-020 | 用户选择推进后创建正式 CR-020，并从 CP2 重新进入标准门控 | 在 Windows 机器上验证 gateway 可安装、可启动、可被 C 侧调用，但不做真实交易 | 明确 Windows host、MiniQMT / XtQuant 版本、局域网地址、端口策略、日志目录、回滚方式 | health、endpoint discovery、HMAC pairing、redaction、blocked result 全部通过 | 不发单、不撤单、不查真实账户、不读取真实凭据正文 |
| CR-021 | QMT simulation 账号接入准入 | candidate | CR | 2 | simulation endpoints；order / cancel / account query；per-run authorization；kill switch；reconciliation | N/A | not-started | CR-020 尚未创建或关闭 | CR-020 closed 后，由用户选择是否创建正式 CR-021 | 在模拟盘验证 order / cancel / account query 的受控转发 | CR-020 PASS；明确 simulation 账号、per-run authorization、交易时段、资金上限、订单范围、kill switch、reconciliation | simulation order / cancel / account query 在授权窗口内可控执行，审计日志脱敏，异常 fail-closed | 不进入 live、不扩大账户范围、不自动连跳 small-live |
| CR-022 | Live-readonly 准入 | candidate | CR | 3 | live-readonly endpoints；account / position / order status；真实账户只读授权；broker lake no-write | N/A | not-started | CR-021 尚未创建或关闭 | CR-021 closed 后，由用户选择是否创建正式 CR-022 | 只读真实账户、持仓、委托状态，不发单 | CR-021 PASS；单次用户授权；只读接口白名单；回滚方案 | account / position / order status 只读通过，无交易副作用，敏感值不落盘不回显 | 不发单、不撤单、不写 broker lake |
| CR-023 | Small-live 准入 | candidate | CR | 4 | live order / cancel；pretrade risk；kill switch；reconciliation；incident playbook | N/A | not-started | CR-022 尚未创建或关闭 | CR-022 closed 后，由用户选择是否创建正式 CR-023 | 小资金真实发单试运行 | CR-022 PASS；资金上限、单笔上限、标的范围、交易时间、人工确认、撤单策略、kill switch | 小额订单闭环、reconciliation PASS、incident playbook 可用，失败自动停机 | 不放大资金、不扩大策略集合、不跳过人工确认 |
| CR-024 | Scale-up 准入 | candidate | CR | 5 | scale_up gate；research maturity；risk limits；资金 / 策略范围扩大；reconciliation evidence | N/A | not-started | CR-023 尚未创建或关闭 | CR-023 多轮稳定并由用户选择后创建正式 CR-024 | 放大资金或扩大策略范围 | CR-023 多轮稳定；研究成熟度 gate；风险限额；人工批准 | 达到稳定性、对账、风控、回撤、成交偏差等量化阈值 | 不把历史 small-live PASS 自动视为 scale-up 授权 |

## Track B: Deferred Capabilities

来源决策：`D-CP8-CR019-05`

目标：继续把 Backtrader W6、Qlib W7、minute Spike 和 Level2 Spike 作为后置能力跟踪，不纳入 CR-019 当前 Stage 6 P0 或 QMT C/S bridge 必需依赖。

| 候选 CR / Spike | capability_id | 状态 | 类型 | 优先级 | 影响面 / 冲突键 | 正式 CR 路径 | 当前门控 | 阻塞原因 | 下一步 | 目标 | 启动条件 | 完成条件 | 明确禁止 |
|---|---|---|---|---:|---|---|---|---|---|---|---|---|---|
| CR-025 | `backtrader_w6` / `research_execution_semantic_alignment` | closed | CR | 1 | Backtrader optional semantic reference；execution semantics；dependency isolation；clean feed；target portfolio / order intent；Backtrader module comparison；no broker | `process/changes/CR-025-BACKTRADER-OPTIONAL-EXECUTION-BACKEND-HARDENING-2026-05-31.md` | closed | CP8 自动预检 PASS；用户于 2026-06-02T23:10:16+08:00 回复“好的关闭CR025”；S01/S04/S02/S03/S05/S06 已 verified，S06 首轮 CP7 FAIL 已由 blocker fix 和 CP7 复验关闭 | 已关闭；后续研究闭环按 CR-030，真实 QMT 路线按 CR-020..CR-024 单独启动 | Research execution semantic alignment with Backtrader optional reference | 干净 feed、PIT、复权、benchmark、候选策略稳定性、target portfolio / order intent 字段证据、Backtrader 模块分析证据齐全 | 与轻量引擎的执行语义差异有量化报告，依赖隔离可验证，研究输出可形成可审计 order intent draft，Backtrader 模块处理策略可审查 | 不替代默认轻量主路径，不复制 / 移植 Backtrader 源码实现，不自动接入真实 broker |
| CR-026 | `qlib_w7` | candidate | CR | 2 | Qlib isolated runner；factor panel；label window；report catalog；provider / dependency boundary | N/A | not-started | factor panel、label window、报告 catalog 和 runner I/O 合同尚未冻结 | 用户选择推进后创建正式 CR-026，并从 CP2 重新进入标准门控 | Qlib isolated runner / factor workflow boundary | factor panel、label window、报告 catalog 和 runner I/O 合同冻结 | isolated runner fixture-only 验证通过，输出不替代当前 lake / engine truth | 不写真实 provider 路径，不直接进入主运行时 |
| CR-030 | `multifactor_framework_reference` | active | CR | 2 | 多因子研究框架借鉴；FactorSpec / FactorRunSpec；factor panel / label window；IC / RankIC；分层收益；多因子组合；实验追踪；策略准入包；GitHub 项目 license / dependency boundary | `process/changes/CR-030-MULTIFACTOR-RESEARCH-FRAMEWORK-REFERENCE-AND-RESEARCH-LOOP-STANDARDIZATION-2026-06-02.md` | CP2 intake | 等待 CP2 需求 / 场景基线确认；候选 GitHub 项目 license、维护状态和适配边界必须在 CP2/CP3 重验 | 组织 meta-pm 基于正式 CR 文件重整多因子研究场景和需求，并分流 CR-026 | 多因子研究框架借鉴与研究闭环标准化 | CR-025 已关闭；用户要求 CR-030 写入足够上下文以便清除对话上下文 | 输出自有多因子研究闭环 HLD / Story / LLD，可审计地借鉴成熟项目设计，但不复制源码、不引入依赖、不替代当前 lake / engine truth | 不 clone / install / run GitHub 项目，不迁移源码，不读取凭据，不 provider fetch / lake write / publish / QMT / simulation / live |
| CR-027 | `minute_spike` | spike_candidate | Spike | 3 | minute source / schema / storage / quality；execution realism；provider / lake no-write | N/A | not-started | 尚无日频执行假设失效证据和 minute source / schema / storage / quality plan | 用户选择推进后创建正式 Spike CR，并从 CP2 / CP3 重新进入标准门控 | Minute data feasibility Spike | 日频证据无法解释关键执行缺口，且有 source / schema / storage / quality plan | bounded experiment 通过，成本、质量和保留策略可审计 | 不做历史分钟数据真实抓取，不写 lake，不升级执行价声明 |
| CR-028 | `level2_spike` | spike_candidate | Spike | 4 | Level2 data rights；order-book schema；queue / impact-cost model；replay fixture；redaction | N/A | not-started | 尚无 L1 / minute 无法关闭 order-book、queue 或 impact-cost 风险的证据 | 用户选择推进后创建正式 Spike CR，并从 CP2 / CP3 重新进入标准门控 | Level2 rights and microstructure Spike | L1 / minute 仍无法关闭 order-book、queue 或 impact-cost 风险 | 数据权利、order-book schema、replay fixture、质量审计和成本评估齐全 | 不声明付费访问，不接真实 feed，不捕获 live quote |

### CR-030 多因子研究框架借鉴上下文（正式 CR 已创建）

CR-030 已创建为正式 CR：`process/changes/CR-030-MULTIFACTOR-RESEARCH-FRAMEWORK-REFERENCE-AND-RESEARCH-LOOP-STANDARDIZATION-2026-06-02.md`。本台账只保留摘要和索引；完整上下文、影响分析、候选 Story、待决策项和不授权项以正式 CR 文件为准。它来自 CR-025 CP5 前的定位澄清：当前系统核心目标是生产级多因子策略研究、回测、模拟盘和实盘衔接；Backtrader 在 CR-025 中只作为 lightweight execution engine 的 execution semantic reference，不承担多因子研究主框架。

| 上下文字段 | 内容 |
|---|---|
| 背景 | CR-025 已把 Backtrader 限定为 feed / broker / order / position / commission / slippage / analyzer 等执行语义参考；FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪、策略准入包均不属于 CR-025。 |
| 目标 | 在独立 CR 中评估成熟 GitHub 项目和最佳实践，提炼本项目自有多因子研究闭环：因子定义、因子运行、factor panel、label window、评价报告、组合构建、实验追踪、策略准入包和 research-to-execution handoff。 |
| 正式启动前必须重验 | GitHub 仓库当前状态、license、维护活跃度、依赖体量、数据接口假设、A 股适配性、是否允许商业 / 内部分发、是否适合 clean-room 借鉴。 |
| 与 CR-026 的关系 | CR-026 是窄范围 Qlib isolated runner / factor workflow boundary；CR-030 是更宽的多因子研究框架借鉴与研究闭环标准化。正式启动时可选择合并 CR-026、保持拆分或让 CR-026 作为 CR-030 的后续执行器 Spike。 |
| 与 CR-025 的关系 | CR-025 先关闭 clean feed、execution semantic diff、order_intent_draft_v1、Backtrader no-copy 与 QMT handoff 边界；CR-030 可消费 CR-025 的 clean feed / semantic evidence / order intent 边界，但不继承任何实现或运行授权。 |

| 候选参考对象 | 可借鉴方向 | 初始边界 |
|---|---|---|
| Qlib | data handler、dataset、processor、workflow recorder、Alpha158、TopK、ML factor workflow | 只作为设计参考；CR-026 已保留 isolated runner 窄范围；正式 CR 前不安装、不运行、不写 provider 路径。 |
| Alphalens | factor tear sheet、forward returns、IC / RankIC、分层收益、turnover、group analysis | 只借鉴评价口径；不直接引入依赖或复制实现。 |
| vectorbt | 向量化扫描、多参数 / 多资产广播、walk-forward 和性能分析思路 | 只借鉴研究效率与参数扫描模式；不替代现有 engine truth。 |
| Zipline Reloaded | 事件时间、pipeline / asset / calendar、order lifecycle | 偏执行 / 时间语义参考；不作为多因子评价主框架。 |
| QuantConnect LEAN | broker / fill / fee / slippage / portfolio / order model 分层 | 偏生产执行语义参考；不引入大型运行时。 |
| RQAlpha | A 股市场规则、配置化运行、mod 扩展、simulation / live 语义 | license / 非商业边界必须正式重验；当前不引入。 |
| vn.py / vnpy.alpha | 国内交易框架、alpha dataset / model / portfolio_strategy / paper_account / gateway 思路 | 只作为国内生态参考；不集成 gateway，不授权实盘。 |
| PyBroker | ML strategy、walk-forward、bootstrap、caching | 可借鉴 ML 策略实验组织；不替代本项目数据湖。 |
| bt | 组合构建 DSL，例如 select / weigh / rebalance | 可借鉴组合构建表达；不直接复制接口。 |
| Backtrader | feed / broker / order / commission / slippage / analyzer 执行语义参考 | 已由 CR-025 承接；不作为多因子研究主框架。 |

| 候选产出 | 说明 |
|---|---|
| `FactorSpec` | 因子定义、输入字段、窗口、PIT / available_at、依赖辅助数据和失败路径。 |
| `FactorRunSpec` | 因子批量运行、universe、label window、调参边界、缓存和可复跑 manifest。 |
| `FactorPanelContract` | 因子面板 schema、index、缺失值、winsorize / neutralize / zscore、lineage 和质量门控。 |
| `FactorEvaluationReport` | IC / RankIC、分层收益、换手、覆盖率、稳定性、benchmark / group 分析。 |
| `MultiFactorCombiner` | 多因子合成、权重、正交化 / 中性化、容量和风险暴露约束。 |
| `StrategyAdmissionPackage` | 研究结果进入模拟 / QMT 前的准入包，含 evidence、limitations、target portfolio / order intent handoff。 |
| `ExperimentManifest` | 研究运行的配置、版本、数据快照、代码版本、输出 artifact 和复跑入口。 |

| 不授权项 | 说明 |
|---|---|
| 依赖 / 源码 | 不 clone、install、run、vendoring、复制、裁剪、改写或源码级迁移任何 GitHub 项目。 |
| 外部操作 | 不读取凭据，不 provider fetch，不 lake write，不 catalog publish，不调用 QMT / broker，不进入 simulation / live。 |
| 结论边界 | 不把任何 GitHub 项目视为 production truth；正式 CR 必须重新验证 license、维护状态和适配边界。 |

| 触发条件 | 处理建议 |
|---|---|
| CR-025 CP8 关闭后继续研究主线 | 当前条件已满足：CR-030 已创建正式 CR 并进入 `active-cp2-intake`，下一步组织 CP2。 |
| 用户明确要求优先建设多因子研究闭环 | CR-025 已关闭；仍需对 CR-030 与 CR-026 / 研究准入修复候选的影响面做冲突预检。 |
| 需要 factor panel / label window / report catalog 标准化 | 优先从 CR-030 CP2/CP3 定义整体研究闭环；CR-026 可保留为 Qlib runner 子路线。 |

## 不授权范围

| 项目 ID | 范围 | 原因 | 需要未来授权时的动作 | 来源 |
|---|---|---|---|---|
| NA-CR019-01 | 真实 QMT / MiniQMT / XtQuant 操作 | CR-019 CP8 只关闭离线合同 / 文档交付，不是运行许可 | 创建正式 CR-020 或后续准入 CR，并重新通过人工门禁与 per-run authorization | D-CP8-CR019-02 |
| NA-CR019-02 | 服务启动 / 端口绑定 / Windows gateway 实机运行 | 当前只记录 gateway lifecycle / deployment 合同，未授权真实服务进程 | 创建正式 CR-020，明确 Windows host、端口、回滚和日志边界 | D-CP8-CR019-02 |
| NA-CR019-03 | 凭据读取、真实账号、token、password、cookie、session、private key | 当前台账不得承载敏感值或真实凭据正文 | 后续 CR 只记录脱敏 ref、授权窗口和回滚方案，不落盘凭据正文 | D-CP8-CR019-02 |
| NA-CR019-04 | provider fetch、lake write、broker lake write、publish | CR-019 未授权真实数据抓取、写湖或发布 | 后续独立 CR 需明确数据源、lake root、publish gate 和回滚 | D-CP8-CR019-02 |
| NA-CR019-05 | simulation / live / live-readonly / small-live / scale-up | 每个阶段必须逐 run 授权，前一阶段通过不自动授权下一阶段 | 按 CR-021..CR-024 顺序创建正式 CR 并走标准门控 | D-CP8-CR019-02 |
| NA-CR019-06 | Backtrader / Qlib / minute / Level2 当前启用 | 这些能力仍为 deferred / later-gated，不属于 CR-019 当前 P0 | 按 CR-025..CR-028 创建正式 CR / Spike 后再实现或验证 | D-CP8-CR019-05 |

## 风险接受项

| 项目 ID | 风险 | 接受条件 | 回退 / 切换条件 | 来源 |
|---|---|---|---|---|
| RA-CR019-01 | CR-019 关闭后仍存在真实 QMT 运行缺口 | 用户接受当前只关闭离线合同 / fixture / dry-run / 文档交付 | 需要真实运行时，从 CR-020 开始创建正式 CR，不复用 CR-019 CP8 作为授权 | D-CP8-CR019-02 |
| RA-CR019-02 | Backtrader / Qlib / minute / Level2 不进入 Stage 6 当前 P0 | 用户接受后置能力继续 deferred / later-gated | 触发条件满足时，按 CR-025..CR-028 创建正式 CR / Spike | D-CP8-CR019-05 |

## 关闭范围

| 项目 ID | 已关闭内容 | 关闭证据 | 来源 |
|---|---|---|---|
| CLOSE-CR019-01 | CR-019 当前离线合同 / fixture / dry-run / 文档边界 | `checkpoints/CP8-CR019-DELIVERY-READINESS.md` approved；`process/checks/CP8-CR019-DELIVERY-READINESS.md` PASS | CP8 |
| CLOSE-CR025-01 | CR-025 当前 research execution semantic alignment、Backtrader optional semantic reference、clean feed gate、semantic diff、`order_intent_draft_v1`、no-copy guardrail、no-real-operation safety 和 follow-up route boundary | `checkpoints/CP8-CR025-DELIVERY-READINESS.md` approved；`process/checks/CP8-CR025-DELIVERY-READINESS.md` PASS；用户回复“好的关闭CR025” | CP8 |

## 取消 / Deferred 项

| 项目 ID | 内容 | 状态 | 原因 | 可重启条件 | 来源 |
|---|---|---|---|---|---|
| DEF-CR019-01 | Backtrader W6 | deferred | 当前 Stage 6 P0 聚焦日频多因子 admission 和 QMT C/S bridge 合同 | 干净 feed、PIT、复权、benchmark 和候选策略稳定性证据齐全 | D-CP8-CR019-05 |
| DEF-CR019-02 | Qlib W7 | deferred | factor panel、label window、报告 catalog 和 isolated runner 边界尚未冻结 | factor panel、report catalog 和 runner I/O 合同冻结 | D-CP8-CR019-05 |
| DEF-CR019-03 | Minute Spike | deferred | minute 数据会扩大 storage、quality、latency、cost model 和执行真实性范围 | 日频证据无法解释关键执行缺口，且有 source / schema / storage / quality plan | D-CP8-CR019-05 |
| DEF-CR019-04 | Level2 Spike | deferred | Level2 依赖数据权利、order-book schema、queue model、成本和审计控制 | L1 / minute 仍无法关闭主要微观结构风险，并完成数据权利和回放 fixture 方案 | D-CP8-CR019-05 |

## Tracking Rules

1. 任何候选 CR / Spike 启动前，必须先创建正式 `process/changes/CR-*.md`，并重新进入 CP2 / CP3 / Story Plan / CP5。
2. 候选项不得在当前 CR-019 的 CP8 里被视为已实现、已验证或已授权。
3. 真实 QMT、服务启动、凭据读取、provider fetch、lake / broker lake 写入、publish、simulation 或 live 必须逐 run 授权。
4. `docs/CR019-DEFERRED-CAPABILITIES.md` 仍是 Track B 的 capability register；本文件只提供后续排序和 CR 候选入口。
5. 若后续发现候选项命名、范围或优先级需要调整，应先更新本台账，再创建或修订对应 CR。
6. 正式 CR 创建后，本台账只保留索引字段；详细需求、影响分析、Story / LLD 边界和文档处理决策必须写入正式 CR 文件。
7. 正式 CR 关闭后，必须回写本台账对应候选项状态为 `closed`，并补充关闭证据。

## CP8 Acceptance

用户已在 2026-05-31 回复“同意，按照你建议实施”。该回复接受：

- CR-019 当前离线合同 / 文档交付可按 CP8 `approve` 收敛；
- `D-CP8-CR019-02` 按 Track A 后续跟踪，不阻塞当前 CP8；
- `D-CP8-CR019-05` 按 Track B 后续跟踪，不阻塞当前 CP8；
- 当前 CP8 不授权任何真实 QMT、服务启动、凭据读取、provider fetch、lake / broker lake 写入、publish、simulation 或 live。
