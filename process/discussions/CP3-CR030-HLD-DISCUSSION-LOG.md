---
change_id: "CR-030"
phase: "solution-design"
discussion_type: "CP3 architecture gray areas"
status: "draft-cp3-input-complete"
created_at: "2026-06-03T07:34:00+08:00"
created_by: "meta-se"
source_use_cases: "process/USE-CASES.md v1.14"
source_requirements: "process/REQUIREMENTS.md v1.15"
source_cp2_manual: "checkpoints/CP2-CR030-REQUIREMENTS-BASELINE.md"
analysis_artifact: "process/research/CR030-MULTIFACTOR-FRAMEWORK-REFERENCE-ANALYSIS-2026-06-03.md"
local_qlib_path: "/home/hyde/download/qlib"
runtime_authorization: "none"
---

# CP3 CR-030 HLD 讨论日志

## 1. 背景与边界

CR-030 CP2 已由用户确认，`process/USE-CASES.md` v1.14 与 `process/REQUIREMENTS.md` v1.15 是本轮 HLD 的正式输入。CP2 Decision Brief 中 `DQ-CP2-CR030-01` 至 `DQ-CP2-CR030-09` 已确认自有多因子研究闭环、外部项目静态借鉴、schema 基线复用、CR-026 分流和不授权边界。

本轮 meta-se 只做 HLD 设计和 CP3 自动预检材料，不发起 CP3 人工确认，不写 `checkpoints/CP3-CR030-HLD-REVIEW.md`。人工确认由 meta-po 负责。

本轮未执行以下动作：实现代码、修改测试、修改 `pyproject.toml` / `uv.lock`、安装 / 运行 / clone 外部项目、运行 qrun、触发 provider fetch、lake write、catalog publish、QMT / MiniQMT / XtQuant、simulation、live、账户查询、发单、撤单或凭据读取。

## 2. Architecture Gray Areas

| 灰区 ID | 关键问题 | 为什么会影响架构 | 影响面 | canonical refs | 处理结果 |
|---|---|---|---|---|---|
| AGA-CR030-01 | 自有多因子闭环主线还是 Qlib runner-first？ | 决定事实源、入口、依赖、provider、report truth、Story 边界和 CR-026 是否并行。 | 范围、模块、数据、依赖、运行授权、验证 | UC-20, UC-21, REQ-174, REQ-184, DQ-CP2-CR030-01/03 | 采用项目自有闭环；Qlib runner 保持 CR-026 后置 Spike。 |
| AGA-CR030-02 | 外部项目如何纳入矩阵而不成为默认框架？ | 决定许可证风险、依赖策略、后续 Spike 队列和禁止迁移边界。 | 许可证、依赖、文档、安全、维护 | UC-21, REQ-175, A-065, A-069, SM-42 | 覆盖 10 类项目，按 reference_only / optional_spike / exclude / forbidden_migration 分类。 |
| AGA-CR030-03 | schema 和校验是否从零设计、复用基线还是直接采用外部对象？ | 决定字段字典、错误码、fail-closed 策略、测试 fixture 和双 truth 风险。 | 数据合同、模块、测试、防泄漏、维护 | UC-22, UC-23, REQ-176, REQ-177, REQ-183, DQ-CP2-CR030-04 | 采用项目自有契约 + 现有基线复用 + 外部项目 cross-check + fail-closed。 |
| AGA-CR030-04 | 多因子组合默认采用可解释组合还是 optimizer / ML workflow？ | 决定是否引入 cvxpy、风险模型、ML 训练、benchmark exposure 和组合优化 Story。 | 组合、依赖、可解释性、性能、验证 | UC-25, REQ-179, SGA-030-07, DEF-030-02 | P0 采用可解释组合；EnhancedIndexing / cvxpy / ML optimizer 后置 Spike。 |
| AGA-CR030-05 | StrategyAdmissionPackage 到 QMT handoff 是否可能被误读为交易授权？ | 决定运行授权、QMT route、order intent 字段和 CP3 不授权项表达。 | 安全、QMT、风险接受、文档、gate | UC-27, REQ-181, REQ-182, A-068, A-070, DQ-CP2-CR030-08 | 只输出 `order_intent_draft_v1` 草稿和 blocked reasons；真实 QMT 另行 CR。 |

## 3. Advisor Table

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| CR30-A：项目自有多因子研究闭环主线 | 与 `research_input_v1`、实验 17-21、CR-011、Stage6 gate 和 CR-025 order intent 边界一致；权限最小；可审计；可 fail-closed。 | 需要将脚本和报告能力标准化为正式合同；短期不获得 Qlib qrun / optimizer 的完整 runtime 能力。 | `engine/research_dataset.py`、实验 17-21、factor panel、label gate、报告、manifest/catalog、admission package、docs、QA fixture。 | 推荐。作为 CR-030 CP3 主选方案。 | 适用于当前不授权依赖、外部运行、provider、QMT 的状态；若后续自有 runner 表达力或性能不足，再以 CR-026 / Spike 接入 isolated runner。 |
| CR30-B：Qlib runner-first / qrun 集成 | 成熟 workflow、DataHandler、Recorder、SigAnaRecord、PortAnaRecord 和 EnhancedIndexing 生态完整。 | 引入 `provider_uri`、`qlib.init`、`.bin`、MLflow/pickle、LightGBM/cvxpy 等依赖；冲击 data lake / catalog truth；当前未授权运行或改依赖。 | 依赖、数据入口、runner、provider、报告 truth、权限、安全、维护、CR-026。 | 不推荐作为 CR-030 默认方案；保留为 CR-026 后续 Spike。 | 仅在 FactorPanel / LabelWindow / ReportCatalog / runner I/O 合同冻结，且用户单独批准依赖隔离、provider 禁用、运行授权和回归范围后切换。 |
| CR30-C：文档 / Spike-only，不冻结自有合同 | 交付成本最低；许可证 / 依赖风险低。 | 无法为 CP4/CP5 提供可执行输入；schema、leakage、evaluation、admission 仍无统一合同。 | 文档、Decision Brief、后续 CR backlog。 | 不推荐作为主线；可作为 CP3 不通过时的回退。 | 若用户不接受任何合同冻结，或许可证 / 依赖风险需要先独立评估，则回退到此方案。 |
| CR30-D：外部框架适配层 / adapter-first | 未来可把 Qlib / Alphalens / Zipline 对象转换为内部对象。 | 内部合同未冻结前会产生空转抽象和双 truth。 | 接口、映射、错误码、测试、维护。 | 条件推荐为后续增强，不进入 P0。 | 当 CR30-A 的内部合同稳定并出现明确外部 runner / analyzer 导入需求时再评估。 |

## 4. 推荐方案

推荐 CR30-A：项目自有多因子研究闭环。

推荐理由：

- 满足 `REQ-174` 至 `REQ-185`，且直接消费 CP2 已确认的 DQ。
- 保持本项目 data lake / catalog / `research_input_v1` / CR-011 / Stage6 gate 为 truth，避免外部 provider 或 runner 接管。
- 能把 Qlib、Alphalens、Zipline、LEAN 等成熟经验用于 cross-check，但不引入默认依赖或运行授权。
- 对 `StrategyAdmissionPackage` 和 `order_intent_draft_v1` 保持 not-authorized 边界，避免研究报告被误读为 QMT-ready。

## 5. Deferred Architecture Ideas

| ID | 想法 / 风险 / 扩展方向 | 来源 | 延后原因 | 触发切换或重启条件 |
|---|---|---|---|---|
| DAI-CR030-01 | Qlib isolated runner / qrun / provider_uri / Recorder import-export | CR-026, Qlib static analysis | 内部 FactorPanel / LabelWindow / ReportCatalog / runner I/O 合同尚未冻结；当前不授权运行。 | CR-030 合同冻结后，单独启动 CR-026 或 bounded Spike。 |
| DAI-CR030-02 | Qlib EnhancedIndexing / cvxpy optimizer | Qlib static analysis, UC-25 | 风险模型、benchmark exposure、optimizer 依赖和回归成本超出 P0。 | 可解释组合不足，且用户接受依赖和许可证风险。 |
| DAI-CR030-03 | vectorbt 批量实验性能对标 | 外部项目矩阵 | 当前无性能瓶颈证据，Commons Clause 需复核。 | 自有批量评价出现量化性能瓶颈。 |
| DAI-CR030-04 | PyBroker ML walk-forward / bootstrap | 外部项目矩阵 | ML 策略和非商业口径需独立边界。 | ML 因子 / 模型策略进入后续 CR。 |
| DAI-CR030-05 | RQAlpha / vn.py 交易生态接入 | 外部项目矩阵 | 与真实交易、gateway、broker 权限和运行治理相关。 | CR-020..CR-024 获得独立授权后再评估。 |

## 6. CP3 待决策项草案

| 决策 ID | 决策类型 | 推荐方案 | 备选方案 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|
| DQ-CP3-CR030-01 | architecture | 接受 CR30-A 项目自有多因子研究闭环。 | Qlib runner-first；文档 / Spike-only。 | 影响 Story 边界、数据 truth、依赖和 QA。 | 若用户要求 runner，回退到 CR-026 CP2/CP3。 |
| DQ-CP3-CR030-02 | implementation | 接受 schema provenance、字段字典、错误码和 fail-closed 策略。 | 直接采用外部对象；从零设计。 | 影响后续 LLD / fixture / report。 | CP3 修改字段字典后重跑自动预检。 |
| DQ-CP3-CR030-03 | follow_up_tracking | 保持 CR-026 Qlib runner 后置。 | 合并入 CR-030 P0；取消。 | 影响 follow-up tracking 和运行授权。 | 合同冻结后启动 CR-026。 |
| DQ-CP3-CR030-04 | implementation | P0 可解释组合，optimizer 后置。 | 默认 EnhancedIndexing / cvxpy；不设计组合。 | 影响依赖、可解释性和验证。 | 另起 optimizer Spike。 |
| DQ-CP3-CR030-05 | security | CP3 通过不授权实现、依赖变更、外部项目运行或真实操作。 | 授权 bounded runtime Spike；授权安装但不运行。 | 防止 provider/lake/QMT/credential 越权。 | 需要运行时另起 CR / Spike。 |
| DQ-CP3-CR030-06 | runtime_authorization | `StrategyAdmissionPackage` 只输出 `order_intent_draft_v1` 草稿。 | 生成可执行 order；完全不设计执行 handoff。 | 影响 QMT route 和误读风险。 | QMT CR approved 后再消费 draft。 |
| DQ-CP3-CR030-07 | risk_acceptance | 接受静态调研支撑 HLD，runtime 细节转后续 Spike。 | 先运行外部项目；删除外部项目参考。 | 静态资料可能遗漏运行细节。 | 后续实现发现阻塞时转 bounded Spike。 |

## 7. 结论

Architecture Gray Areas 已处理，无 BLOCKING 缺失信息。HLD 草案已写入 `process/HLD.md` §35，并将作为 meta-po 生成 CP3 Decision Brief 和人工审查稿的输入。
