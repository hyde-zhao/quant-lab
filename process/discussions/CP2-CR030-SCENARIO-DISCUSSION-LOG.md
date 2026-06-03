---
change_id: "CR-030"
phase: "requirement-clarification"
discussion_type: "CP2 scenario gray areas"
status: "draft-cp2-input-complete"
created_at: "2026-06-03T00:06:23+08:00"
created_by: "meta-po"
local_qlib_path: "/home/hyde/download/qlib"
analysis_artifact: "process/research/CR030-MULTIFACTOR-FRAMEWORK-REFERENCE-ANALYSIS-2026-06-03.md"
runtime_authorization: "none"
---

# CP2 CR-030 场景讨论日志

## 1. 讨论背景

用户要求推进 CR-030，并明确本地 Qlib 已下载到 `/home/hyde/download/qlib`。本轮用户进一步授权可以开启子 agent 进行 web search，并要求继续分析。

本轮已完成三类输入收敛：

| 输入 | 处理方式 | 结果 |
|---|---|---|
| 本地 Qlib | 静态读取 README、LICENSE、docs、examples、workflow/data/recorder/report/evaluation/strategy 等关键路径 | 形成 Qlib 借鉴 / 不引入矩阵 |
| 其他多因子项目 | 启动两个 explorer 子 agent 做公开资料 web search | 形成 Alphalens、vectorbt、PyBroker、bt、Zipline Reloaded、LEAN、RQAlpha、vn.py 分类建议 |
| CP2 需求 / 场景 | 启动 meta-pm 子 agent做 CR-030 CP2 收敛建议 | 形成 UC-20..UC-27、REQ-174..REQ-185 和 CR-026 分流建议 |

本轮未安装、未运行、未 clone 外部项目，未复制源码，未修改依赖，未触发 provider / lake / publish / QMT / simulation / live / credential 操作。

## 2. 用户目标复述

CR-030 的目标不是把本项目扩展成大型通用量化平台，也不是优先集成 Qlib。当前目标是把本项目收敛成生产级多因子策略研究和回测框架，并为后续模拟盘和真实 QMT 路线准备可审计准入证据。

因此，CP2 应冻结以下主线：

| 主线 | 推荐 CP2 口径 |
|---|---|
| 多因子研究闭环 | 使用项目自有契约，外部项目只做静态借鉴 |
| 外部项目范围 | Qlib、Alphalens、vectorbt、Zipline Reloaded、QuantConnect LEAN、RQAlpha、vn.py / vnpy.alpha、PyBroker、bt、Backtrader 均进入借鉴矩阵 |
| CR-026 分流 | 保留为 Qlib isolated runner 后续 Spike candidate，不并行启动、不授权实现 |
| QMT 路线 | CR-030 只生成研究证据和 handoff 边界，不授权 CR-020..CR-024 的真实 QMT 操作 |

## 3. Scenario Gray Areas

| 灰区 ID | 问题 | 为什么重要 | 推荐处理 | 状态 |
|---|---|---|---|---|
| SGA-030-01 | CR-030 是自有多因子闭环主线，还是 Qlib-first runner 集成？ | 决定架构、依赖、数据事实源和 Story 拆分 | 采用自有闭环主线；Qlib 作为强参考和后续 runner Spike 输入 | decision-item |
| SGA-030-02 | 外部项目应借鉴哪些，不借鉴哪些？ | 影响 HLD 准确性、许可证边界和分析完整性 | 全部候选进入静态借鉴矩阵；HLD 逐项标注 reference / spike / exclude / forbidden migration | decision-item |
| SGA-030-03 | 多因子对象是否采用项目自有 schema？ | 直接采用外部对象会引入依赖和数据假设 | 采用 `FactorSpec` / `FactorRunSpec` / `FactorPanelContract` / `LabelWindowSpec` 等项目自有契约 | decision-item |
| SGA-030-04 | 现有 `research_dataset.py` 和实验 17-21 是否复用？ | 若重做会制造平行框架和验证债 | 作为基线能力复用并标准化，避免从零重写 | decision-item |
| SGA-030-05 | CP2 是否授权运行 / 安装 / clone 外部项目？ | 运行授权会扩大许可证、依赖和安全面 | 不授权；CP2 只确认需求、场景、静态调研范围和不授权边界 | decision-item |
| SGA-030-06 | 研究输出能否直接进入 QMT / simulation / live？ | 容易把研究报告误解为交易授权 | 只允许报告和 `order_intent_draft_v1` 草稿；真实 QMT 后续 CR 单独授权 | decision-item |
| SGA-030-07 | Qlib EnhancedIndexing / optimizer 是否纳入 P0？ | 需要风险模型、cvxpy、benchmark / factor exposure 数据 | 不纳入 P0；作为后续组合优化 Spike | non-blocking-open |
| SGA-030-08 | vectorbt / PyBroker 是否作为性能或 ML 验证依赖？ | Commons Clause / 非商业口径和依赖复杂度较高 | 仅作为 optional Spike 参考；不默认依赖 | non-blocking-open |
| SGA-030-09 | RQAlpha 能否引入 A 股事件回测？ | 公开许可证口径存在非商业限制，需要严审 | 仅做只读设计 Spike 候选，不依赖、不复制 | non-blocking-open |

## 4. Deferred Ideas

| ID | 延后项 | 延后原因 | 重启条件 |
|---|---|---|---|
| DEF-030-01 | Qlib isolated runner / qrun 执行 | Factor panel、label window、report catalog 和 runner I/O 合同尚未冻结 | CR-030 完成契约冻结后，单独启动 CR-026 或 Spike |
| DEF-030-02 | Qlib EnhancedIndexing / cvxpy optimizer | 风险模型和依赖复杂度较高，超出 P0 | 多因子组合基线通过后，用户要求组合优化且许可证 / 依赖通过 |
| DEF-030-03 | vectorbt 性能对标 | 许可证和抽象面需评估 | 当前实现出现性能瓶颈或批量实验形状无法满足 |
| DEF-030-04 | PyBroker ML walk-forward / bootstrap | 非商业口径和外部数据入口需隔离 | ML 因子 / 模型策略进入 CR-030 后续 Story |
| DEF-030-05 | RQAlpha / vn.py 实盘生态接入 | 与真实交易 / gateway / broker 权限相关 | CR-020..CR-024 对应 QMT 路线完成授权后再评估 |
| DEF-030-06 | 真实 provider / lake / publish / QMT 操作 | 当前 CP2 不授权真实运行 | 后续单独 CR、CP5 和 per-run authorization |

## 5. CP2 待决策项草案

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|
| DQ-CP2-CR030-01 | scope | CR-030 是否确认为自有多因子研究闭环主线？ | 确认 CR-030 为主线；外部项目不作为默认框架 | 以 Qlib runner 为主线；或仅做文档调研 | Qlib-first 会扩大依赖和数据事实源冲突 | CP3 证明 runner 必要时另启 CR-026 |
| DQ-CP2-CR030-02 | scope | 是否确认 UC-20 至 UC-27 为本轮场景基线？ | 确认并写入 `USE-CASES.md` 增量 | 收窄到 Qlib + Alphalens；或延后外部项目矩阵 | 场景过窄会漏掉成熟实践，过宽会增加设计成本 | CP2 修改后重发基线 |
| DQ-CP2-CR030-03 | follow_up_tracking | CR-026 如何分流？ | 保留为 Qlib isolated runner 后续 Spike candidate，不并行启动 | 合并为 CR-030 Story；取消 CR-026 | 合并会扩大实现范围，取消可能错过 Qlib runner 价值 | 契约冻结后重新启动 CR-026 |
| DQ-CP2-CR030-04 | implementation | 多因子对象是否采用项目自有命名与 schema？ | 采用 `FactorSpec` / `FactorRunSpec` / `FactorPanelContract` 等自有契约 | 直接采用 Qlib / Alphalens / Zipline 对象模型 | 外部对象会带来依赖和语义迁移风险 | CP3 如需适配层再单独决策 |
| DQ-CP2-CR030-05 | runtime_authorization | CP2 是否授权安装、运行、克隆外部项目或真实 provider / QMT 操作？ | 不授权 | 授权隔离运行 Spike | 运行授权会扩大安全、依赖和许可证风险 | 需要运行时另行 CP3/CP5 或 CR 授权 |
| DQ-CP2-CR030-06 | scope | 外部项目调研面是否采用 CR-030 候选清单？ | 采用完整候选清单，CP3 逐项复核 | 收窄为少数项目 | 完整矩阵更利于准确性，但 HLD 工作量更高 | CP2 可按优先级删减 |
| DQ-CP2-CR030-07 | implementation | 现有 research dataset 与实验 17-21 是否作为基线能力复用？ | 复用并标准化，不重做平行框架 | 从零重写多因子框架 | 重写风险高且会绕开已验证能力 | CP3 如发现现有能力不足，再补缺口 |
| DQ-CP2-CR030-08 | runtime_authorization | 研究到执行交接是否只允许报告和 `order_intent_draft_v1` 草稿？ | 是，不生成真实交易信号、不 QMT-ready | 允许生成可执行 order | 会绕过 CR-020..CR-024 和 Stage6 gate | 后续 QMT CR 单独授权 |
| DQ-CP2-CR030-09 | risk_acceptance | CP2 approve 是否接受“静态调研但不授权运行”的风险边界？ | 接受 | 要求立即运行外部项目验证 | 运行会引入依赖和许可证不确定性 | 后续单独 Spike |

## 6. CP2 正式化建议

下一步如果进入 CP2 人工门禁，应完成以下动作：

1. 将 UC-20 至 UC-27 增量写入 `process/USE-CASES.md`，保留旧 UC-01 至 UC-19 基线。
2. 将 REQ-174 至 REQ-185 增量写入 `process/REQUIREMENTS.md`，保留旧 REQ-001 至 REQ-173 基线。
3. 写入 `process/checks/CP1-CR030-USE-CASE-COMPLETENESS.md` 和 `process/checks/CP2-CR030-REQUIREMENTS-BASELINE.md`。
4. 写入 `checkpoints/CP2-CR030-REQUIREMENTS-BASELINE.md`，Decision Brief 必须打印 DQ-CP2-CR030-01 至 DQ-CP2-CR030-09。
5. 发起人工确认时只给出 `approve`、`修改: <具体修改点>`、`reject` 三个回复。

当前本日志只表示 CP2 输入收敛，不表示 CP2 人工批准。
