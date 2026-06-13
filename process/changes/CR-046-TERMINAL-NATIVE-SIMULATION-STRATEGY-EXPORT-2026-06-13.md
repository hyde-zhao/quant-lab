---
cr_id: "CR-046"
status: "active-cp6-pass-ready-for-verification"
impact_level: "high"
workflow_mode_before: "standard"
workflow_mode_after_change: "standard"
fast_lane_upgrade_reason: "命中交易终端、模拟盘执行、外部接口契约和运行授权边界；不得使用 fast-lane。"
rollback_to: "CP2 requirement baseline for CR046"
approval_result: "cp5-approved-cp6-pass-ready-for-cp7"
pause_status: "user-paused-before-cp7"
paused_at: "2026-06-14T00:29:41+08:00"
pause_reason: "用户要求 CR046 先挂起；恢复点保持 CP6 PASS / ready-for-verification，恢复前不推进 CP7。"
created_at: "2026-06-13T14:05:40+08:00"
created_by: "meta-po"
approved_by: "user"
approved_at: "2026-06-13T22:03:22+08:00"
source: "user"
linked_issue: ""
parent_cr: ""
source_checkpoint: ""
source_decision_id: ""
follow_up_type: ""
risk_class: "dual-target-trading-framework"
owner: "meta-po"
revisit_condition: "用户要求进入具体策略交付、QMT 终端运行验证、MiniQMT 实机连接、真实 submit/cancel、live 交易或 runner 运行时，另起后续 CR / runtime authorization gate。"
acceptance_criteria: "交付 QMT 终端与 MiniQMT runner 双目标策略交付框架、验证框架设计、安装设计、交付包契约和后续策略交付门禁；不交付具体交易策略、不执行终端运行验证、不授权真实下单。"
close_condition: "双目标框架设计、验证框架设计、runner 安装方案、策略交付契约、风险边界、后续 CR 切分和研究框架完善候选项通过 CP8。"
cr_index_path: "process/changes/CR-INDEX.yaml"
---

## 挂起记录

| 时间 | 触发 | 恢复点 | 挂起期间不授权 |
|---|---|---|---|
| 2026-06-14T00:29:41+08:00 | 用户要求“这个CR先挂起” | CP6 framework-first implementation PASS / ready-for-verification；恢复后应从 CP7 verification-execution 前置状态继续 | 不推进 CP7、不关闭 CR046、不启动 CR047 / CR051、不执行真实传输、导入、QMT 运行验证、MiniQMT 连接 / 安装、账户查询、submit/cancel、simulation/live、provider fetch、lake write 或 catalog publish |

## 变更描述

用户再次调整 CR046 目标：先把 QMT / MiniQMT 双目标框架订下来；策略交付和验证等权限、策略选择和运行条件就绪后再做。当前 CR 只设计框架和验证框架，后面再开始具体策略交付；框架必须覆盖策略交付形态，以及使用 MiniQMT 时的 runner 组件安装。研究完交易交付框架后，还需要继续完善研究框架。

本 CR 将交付目标从“单一 QMT 终端策略导出”升级为“双目标策略交付与验证框架”：

- 目标一：定义统一策略核心契约，使同一研究策略可交付到 QMT 终端内策略和 MiniQMT / XtQuant 外部 runner。
- 目标二：定义 QMT 终端交付形态，包括策略文件、配置、输入、输出、日志、shadow 报告和人工导入步骤。
- 目标三：定义 MiniQMT runner 交付形态，包括 runner 组件边界、Windows 安装目录、uv 管理方式、依赖隔离、启动 / 停止 / 日志 / kill switch / 配置文件。
- 目标四：定义验证框架，覆盖 fixture 静态验证设计、QMT 终端 shadow 验证计划、MiniQMT runner dry-run / install dry-run 计划、后续只读连接和 submit/cancel 授权门禁。
- 目标五：形成后续研究框架完善候选项，确保交易交付框架定稿后能反向约束研究输出格式、策略准入、order intents 和回测 / 模拟一致性。
- 当前不交付具体交易策略，不执行 QMT 终端运行验证，不实现真实 MiniQMT runner runtime，不连接 MiniQMT，不读取真实账号，不提交 / 撤单。
- QMT 当前可用：用户有 QMT 终端权限，可在 QMT 终端内运行策略。
- MiniQMT 当前为未来路线：用户当前没有 MiniQMT 权限；本 CR 设计 MiniQMT runner 安装与验证框架，但不执行实机连接。

## 当前事实输入

| 来源 | 事实 |
|---|---|
| CR041 | 已有本地 API-less paper simulation runner，可产出 `order_intents` / fills / positions / reconciliation 报告；不连接 broker。 |
| CR042 | 已有 broker-neutral adapter contract 和 Goldminer stub，仍不授权真实 broker runtime。 |
| CR043 | 掘金 gm/gmtrade 静态可行性 Spike 已关闭，真实运行需另行授权。 |
| CR044 | Goldminer simulation admission 离线准入设计已关闭，不授权真实账户查询、下单、撤单或 simulation/live。 |
| CR045 | Windows bridge readonly skeleton 已关闭；用户后续在 Windows 本机完成 `gm` 行情和 `gmtrade` 只读账户校验。 |
| RUN-EXEC-20260613-001 | 用户验证：掘金行情 API 成功；gmtrade 只读账户校验成功；两组本地 paper simulation pass。 |
| USER-20260613-QMT-BROKER-OPENED | 用户补充：QMT 已在券商开通，可在 QMT 终端里运行策略；当前没有 MiniQMT 权限，若未来考虑自研 runner 可再申请；掘金量化尚未开通券商，只有掘金量化账号。 |
| USER-20260613-DUAL-TARGET-FRAMEWORK | 用户要求：后续研究策略需要同时支持 QMT 和 MiniQMT；当前先形成 CR，设计框架和验证框架，后续再开始策略交付；框架需要包含策略交付和 MiniQMT runner 组件安装。 |
| USER-20260613-FRAMEWORK-FIRST-RESEARCH-FOLLOWUP | 用户要求：先把 QMT 框架订下来；策略交付和验证等有权限后再做；研究完框架后继续完善研究框架。 |
| CR040 / 项目记忆 | QMT/MiniQMT 路线此前因权限不可用被用户删除 / 取消；该历史基线保留，但已被 `USER-20260613-QMT-BROKER-OPENED` 部分修正。 |

## 目标口径

### 本轮 In Scope

- 双目标策略交付框架：
  - 策略核心合同：信号、目标持仓、order intents、风控输入、执行回报、对账报告。
  - QMT 终端 adapter 合同：终端内策略如何加载配置、读取输入、输出 shadow 报告、调用终端 API 的隔离点。
  - MiniQMT runner adapter 合同：外部 runner 如何加载同一策略核心、订阅行情、接收信号、路由订单、接收回报。
- 策略交付包结构：
  - `strategy_core/`：研究策略可复用核心逻辑或导出合同。
  - `targets/qmt_terminal/`：QMT 终端策略入口、配置样例、导入说明。
  - `targets/miniqmt_runner/`：MiniQMT runner 入口、安装脚本设计、服务/进程运行说明、配置样例。
  - `validation/`：fixture、schema、dry-run 输入、预期输出。
  - `docs/`：交付手册、运行手册、授权边界、排错。
  - 策略包传输形态：默认以 `strategy-package-<strategy_id>-<version>.zip`、`.sha256` 和 `manifest.yaml` 作为离线 artifact，经人工/受控文件通道传到交易运行 PC，再按 `targets/qmt_terminal/` 的人工导入步骤进入 QMT 终端；本 CR 只冻结合同，不执行传输、导入或运行。
- MiniQMT runner 组件安装设计：
  - Windows 目录规范。
  - uv 管理方式。
  - Python 版本与依赖隔离策略。
  - `xtquant` / MiniQMT 权限前置检查。
  - install dry-run / uninstall / upgrade / rollback 方案。
  - 日志、配置、kill switch、运行报告目录。
- 验证框架：
  - 本地 fixture 验证设计：不连接终端、不读取凭据。
  - QMT 终端 shadow 验证计划：定义人工验证步骤、输入输出和证据格式，本 CR 不执行。
  - MiniQMT runner install dry-run 计划：定义目录、配置、依赖声明和启动脚本结构，本 CR 不执行真实安装和连接。
  - 后续 MiniQMT 只读连接、submit/cancel、tick 级 runner 作为独立门禁。
- 研究框架反向约束：
  - 定义后续研究框架需要产出的策略元数据、目标持仓、order intents、风险假设、成本假设和验证证据。
  - 将研究框架完善登记为后续 CR 候选，不在本 CR 内实施。
- 掘金：
  - 保留为次级参考和对照，不作为本 CR 的核心目标。

### 本轮 Out of Scope

- 具体交易策略交付。
- QMT 终端 shadow / 模拟盘运行验证。
- 真实 MiniQMT runner runtime 实现。
- MiniQMT runner 组件真实安装。
- Windows API gateway / WSL bridge runtime 实现。
- 外部 Python 进程真实连接 QMT / XtQuant / MiniQMT。
- tick 级真实交易、盘口级资源控制、低延迟事件循环实现。
- 真实模拟盘 submit/cancel。
- live / 实盘交易。
- 连续无人值守运行。
- 真实账户资金 / 持仓 / 委托 / 成交查询。
- 数据湖写入、catalog publish、provider fetch。
- QMT 真实 submit/cancel 或账户写入验证，除非用户另起授权。

## CP8 Follow-up 来源

N/A。本 CR 由用户直接提出目标变更，不是 CP8 follow-up tracking 自动转入。

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `process/USE-CASES.md` | 原文档更新 | 既有模拟盘 / broker 准入场景保留；追加双目标策略交付框架场景 | `## 修订记录` | approved-cp2 |
| `process/REQUIREMENTS.md` | 原文档更新 | 既有 runner / broker / simulation admission 需求保留为历史基线；追加 QMT + MiniQMT 双目标框架需求 | `## 修订记录` | approved-cp2 |
| `docs/product/SCENARIOS.yaml` | 原文档更新 | 既有场景保留；追加 dual-target framework、QMT shadow、MiniQMT install dry-run、strategy package validation 场景 | 文件内修订记录或 CR 映射 | approved-cp2 |
| `docs/product/TEST-MATRIX.md` | 原文档更新 | 既有测试矩阵保留；追加 CR046 框架验证矩阵 | `## 修订记录` | approved-cp2 |
| `docs/design/HLD.md` | 原文档更新 | 既有 Goldminer / broker adapter 设计保留；追加 QMT + MiniQMT 双目标交付架构 | `## 修订记录` | approved-cp3 |
| `docs/design/ARCHITECTURE-DECISION.md` | 原文档更新 | 保留“先框架后策略交付、QMT 终端与 MiniQMT runner 双目标、真实连接后置授权”的决策依据 | `## 修订记录` | approved-cp3 |
| `docs/design/FEATURE-DESIGN-MATRIX.md` | 原文档更新 | 追加 CR046 feature 设计和 Story 的 lld_policy | `## 修订记录` | cp4-pass |
| `process/STORY-BACKLOG.md` | 原文档更新 | 追加 CR046 Story，保留旧 Story 状态 | 文件内修订记录或 CR 映射 | cp4-pass |
| `process/DEVELOPMENT-PLAN.yaml` | 原文档更新 | 追加 CR046 Wave，不替换已关闭 CR 的计划 | N/A | cp4-pass |
| `docs/goldminer/CR045-BRIDGE-RUNBOOK.md` | 不变 | CR045 只读桥接手册保留，不混写 CR046 终端策略运行手册 | 不适用 | n/a |
| `docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md` | 新增 | N/A | 文档头部修订记录 | pending-cp5-lld |
| `docs/qmt/CR046-VERIFICATION-FRAMEWORK.md` | 新增 | N/A | 文档头部修订记录 | pending-cp5-lld |
| `docs/qmt/CR046-MINIQMT-RUNNER-INSTALL-DESIGN.md` | 新增 | N/A | 文档头部修订记录 | pending-cp5-lld |
| `docs/research/CR046-RESEARCH-FRAMEWORK-FOLLOWUP.md` | 新增 | N/A | 文档头部修订记录 | pending-cp5-technical-note |

## 旧基线映射

| 原基线对象 | 新增 / 修改对象 | 保留策略 | 映射说明 |
|---|---|---|---|
| CR041 API-less paper simulation runner | CR046 terminal-native strategy export | 原文保留 | CR041 继续作为离线 order intents / candidate 输入来源，不升级为 broker runner。 |
| CR044 Goldminer simulation admission | CR046 Goldminer terminal strategy package | 原文保留 | CR044 的风控、授权、reconciliation 口径作为 CR046 的安全约束输入。 |
| CR045 Windows bridge readonly skeleton | CR046 terminal strategy runbook | 原文保留 | CR046 不复用 Windows bridge runtime；只复用用户 Windows 验证事实。 |
| CR040 QMT route deletion | CR046 QMT primary terminal strategy export | 原文保留 + 新事实覆盖 | QMT 历史删除原因是权限不可用；用户已在券商开通 QMT 后，该限制不再作为 CR046 主线阻断项。 |
| CR020 MiniQMT gateway / XtQuant route | CR046 MiniQMT runner install design | 原文保留 + 设计复用 | 用户当前没有 MiniQMT 权限；本 CR 只设计 runner 安装与验证框架，不做真实连接。 |
| CR045 Goldminer readonly validation | CR046 secondary Goldminer terminal notes | 原文保留 | 掘金侧继续作为已验证行情 / 只读接口补充，不作为本轮券商执行主线。 |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论 | 处理动作 |
|------|----------|-----------|------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | `REQUIREMENTS.md` | true | 从“终端策略导出”升级为“QMT + MiniQMT 双目标策略交付与验证框架”；具体策略交付后置。 |
| 场景层 | 是否改变测试矩阵覆盖范围 | `SCENARIOS.yaml` / `TEST-MATRIX.md` | true | 新增策略包合同静态验证、QMT 终端 shadow 验证计划、MiniQMT runner install dry-run 计划、权限缺失降级场景。 |
| 计划层 | 是否改变 Phase、Wave、Story / 任务依赖 | `process/DEVELOPMENT-PLAN.yaml` | true | 新增 CR046 Story 批次：架构框架、交付包合同、runner 安装设计、验证框架、后续策略交付门禁。 |
| 安全层 | 是否引入新的高风险动作或权限要求 | 交易终端 / MiniQMT runner / 授权边界 | true | impact_level=high；本 CR 仅设计框架和验证框架，不授权终端运行验证、真实连接、账户查询、submit/cancel。 |
| 交付层 | 是否需要重新生成交付物或回归子集 | framework docs / schema / validation plan / follow-up tracking | true | 新增框架文档、验证框架设计、安装设计、schema、fixture 设计和研究框架完善候选项。 |

## 回退决策

- 影响范围：局部，限定为 CR046 新增终端策略导出能力。
- 回退到阶段：`CP2 requirement baseline for CR046`。
- 需要重新确认的对象：
  - 是否将 CR046 改为双目标框架 CR，而非具体策略交付 CR。
  - 是否同时保留 QMT 终端和 MiniQMT runner 两个目标。
  - 是否把 MiniQMT runner 组件安装纳入本 CR 的设计 / dry-run，不做真实连接。
  - 是否把具体策略交付、QMT 终端运行验证、MiniQMT 只读连接、submit/cancel、tick runner 放入后续 CR。
  - 是否在框架研究完成后继续完善研究框架。

## fast-lane 判定

| 条件 | 是否命中 | 说明 |
|---|---|---|
| 仅低风险轻量实现 / 文档 / 规则修改 | false | 涉及交易终端策略、模拟盘路径和安全边界。 |
| 修改架构、权限、安全边界或平台安装路径 | true | 明确修改运行承载方式和授权边界。 |
| 修改外部接口契约、文件所有权或多 Story 依赖 | true | 需要定义终端策略输入 / 输出 / 风控合同。 |
| 需要 HLD / LLD 才能解释影响 | true | 需要拆分 Goldminer / QMT 两类终端适配边界。 |
| 是否保持 fast-lane | false | 必须 standard。 |

## LLD 设计批次门禁

- 是否需要 LLD 设计批次：true
- batch_id：`CR046-DUAL-TARGET-FRAMEWORK-BATCH-A`
- 批次范围来源：CR 影响分析
- 批次内 Story：
  - `CR046-S01-dual-target-strategy-architecture`
  - `CR046-S02-strategy-package-contract-and-schema`
  - `CR046-S03-qmt-terminal-target-framework`
  - `CR046-S04-miniqmt-runner-install-and-runtime-boundary`
  - `CR046-S05-verification-framework-and-evidence-model`
  - `CR046-S06-follow-up-strategy-delivery-gate`
  - `CR046-S07-research-framework-follow-up-contract`
- 批次人工确认稿：`process/checkpoints/CP5-CR046-LLD-BATCH.md`
- 开发启动条件：
  - [ ] 批次内全部 Story 设计证据已输出（full-lld / technical-note / waived）
  - [ ] 批次内全部 Story CP5 自动预检已通过
  - [ ] 批次 CP5 人工确认结论为 `approved`
  - [ ] 批次内每个 Story 的 `dev_gate` 已满足

## 执行链路

| 顺序 | 责任角色 | 动作 | 输入 | 输出 | 门控 | 完成后下一步 |
|---|---|---|---|---|---|---|
| 1 | `meta-po` | 创建 CR046 并完成 CP2 intake | 用户目标变更 / RUN-EXEC | CR046、STATE、CR-INDEX、CP2 决策项 | CR 已登记 | 分派需求 / 设计收敛 |
| 2 | `meta-pm` | 刷新需求、场景和测试矩阵 | CR046、现有产品文档 | USE-CASES / REQUIREMENTS / SCENARIOS / TEST-MATRIX 修订 | CP2 | 交回 meta-po |
| 3 | `meta-se` | 完成 HLD、ADR、Story 拆解和 Feature 设计 | CP2 baseline、CR046 | HLD / ADR / FEATURE-DESIGN-MATRIX / STORY-BACKLOG / DEVELOPMENT-PLAN | CP3 / CP4 | 交回 meta-po |
| 4 | `meta-dev` | 完成 LLD 批次与框架实现 | CP5 approved batch | 框架文档、schema、fixture 设计、验证框架、安装设计 | CP5 / CP6 | 交回 meta-po |
| 5 | `meta-qa` | 验证静态和 fixture 证据 | 实现产物 | VERIFICATION-REPORT / TEST-REPORT / REVIEW | CP7 | 交回 meta-po |
| 6 | `meta-doc` | 刷新运行手册和用户说明 | 已验证产物 | QMT / MiniQMT 框架手册与安装设计 | 文档自检 | 交回 meta-po |
| 7 | `meta-po` | 收敛 CP8 | 下游结果 | CP8 人工审查稿 | 等待用户确认 | 关闭 CR046 |

## 自动终验授权

- 是否启用：false
- 授权范围：不适用
- 适用检查点：CP8
- 自动通过条件：
  - [ ] 自动预检结论为 `PASS`
  - [ ] 无 `BLOCKING`
  - [ ] 无 `REQUIRED`
  - [ ] 授权动作明确包含关闭 CR 和 / 或推进 `delivered`
- 授权原文：
- 授权时间：
- 回填要求：若生效，人工审查稿必须标注 `approval_source=user-preauthorized`

## 后续事项台账

- 是否存在后续事项：true
- 台账路径：`process/changes/CR-046-FOLLOW-UP-TRACKING-2026-06-13.md`
- CR 索引路径：`process/changes/CR-INDEX.yaml`
- 一致性检查：`uv run --python 3.11 python scripts/check_cr_tracking_consistency.py --project-root .`
- 状态取值：`candidate` / `active` / `blocked` / `spike_candidate` / `converted-to-spike` / `closed` / `cancelled` / `superseded`

| 候选编号 | 标题 | 状态 | 类型 | 优先级 | 正式 CR 路径 | 相关 active CR / blocked_by / superseded_by | 当前门控 | 阻塞原因 | 下一步 |
|---|---|---|---|---:|---|---|---|---|---|
| CR047-candidate | 首个研究策略双目标交付 | candidate | CR | 1 |  | blocked_by=CR046 | strategy_delivery_gate | 需 CR046 框架、schema、验证框架通过 CP8 | 选择一个已通过研究准入的策略进行 QMT / MiniQMT 双目标交付 |
| CR048-candidate | QMT 终端真实模拟盘最小 submit/cancel 授权验证 | candidate | CR | 2 |  | blocked_by=CR047 | runtime_authorization | 需具体策略包和 QMT shadow 证据 | 用户逐 run 授权后启动 |
| CR049-candidate | MiniQMT / XtQuant 只读连接与 runner install 实机验证 | candidate | CR / Spike | 3 |  | blocked_by=MiniQMT 权限 | environment_authorization | 用户当前没有 MiniQMT 权限 | 权限开通后验证 userdata_mini、xtquant、账号只读、runner install |
| CR050-candidate | tick 级 MiniQMT runner / 资源控制 Spike | spike_candidate | Spike | 5 |  | blocked_by=MiniQMT 只读和日频模拟盘稳定证据 | research_spike | tick 级复杂度和资源控制高，不属于本轮 | 日频双目标稳定后再评估 |
| CR051-candidate | 研究框架完善：面向 QMT / MiniQMT 交付的策略准入与输出合同 | candidate | CR | 1 |  | blocked_by=CR046 | research_framework_gate | 需 CR046 框架定义研究输出合同 | 完善研究框架，使后续策略天然产出双目标交付所需元数据、order intents、风控假设和证据 |

## 待人工决策清单

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣摘要 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|---|
| DQ-CR046-01 | scope | CR046 是否改为 QMT + MiniQMT 双目标策略交付与验证框架，而不是具体策略交付？ | 是，本轮先交付框架和验证框架 | 继续交付一个 QMT 策略包 / 直接进入 MiniQMT runner 实现 | 推荐方案先统一合同和验证门禁，避免后续每个策略重复设计；直接交付会留下双目标不一致风险 | 本轮不会产生可交易具体策略 | CP8 后启动 CR047 做首个策略交付 |
| DQ-CR046-02 | architecture | 是否要求后续研究策略同时支持 QMT 终端和 MiniQMT runner？ | 是，双目标为标准交付合同 | 只支持 QMT / 只支持 MiniQMT | 推荐方案兼顾当前 QMT 可用和未来 runner 自动化；成本是框架复杂度更高 | 需要明确可复用策略核心和 adapter 边界 | 若 MiniQMT 权限长期不可得，可降级为 QMT-only |
| DQ-CR046-03 | implementation | MiniQMT runner 组件安装是否纳入本 CR？ | 是，纳入安装设计和 dry-run 方案，不执行真实安装 / 连接 | 完全不纳入 / 直接实现可运行 runner | 安装设计可提前冻结目录、uv、依赖、配置和日志规范；直接实现会被权限和安全门禁阻塞 | 需明确 install dry-run 方案不等于 runtime 授权 | MiniQMT 权限开通后另起实机验证 CR |
| DQ-CR046-04 | security | 本 CR 是否继续禁止 QMT 终端运行验证、真实账户查询、submit/cancel、live 和 MiniQMT 连接？ | 是，仅框架 / 验证框架设计 / fixture 设计 | 授权 QMT shadow / 授权只读连接 / 授权最小模拟盘提交 | 推荐方案风险最低，符合先框架后策略交付 | 无法产生真实运行证据，只产生设计和静态验证计划证据 | 后续 runtime_authorization gate 开启 |
| DQ-CR046-05 | follow_up_tracking | 首个具体策略交付是否作为 CR047 候选进入后续台账？ | 是，CR047-candidate | 在 CR046 内交付首个策略 / 暂不登记 | 推荐方案保持框架与策略交付分离，便于 CP8 判断 | 后续需要再次 CP2/CP3/CP5 确认具体策略 | CR046 CP8 通过后启动 |
| DQ-CR046-06 | follow_up_tracking | 研究框架完善是否作为 CR051 候选进入后续台账？ | 是，CR051-candidate | 并入 CR046 / 暂不登记 | 推荐方案先冻结交易交付框架，再反向完善研究框架，避免当前 CR 过大 | CR051 需要消费 CR046 输出合同 | CR046 CP8 通过后启动 |
| DQ-CR046-07 | implementation | 研究完成的策略以什么形式传到交易运行 PC？ | 采用 versioned strategy package artifact：zip + sha256 + manifest.yaml + docs bundle，经人工/受控文件传输到交易运行 PC，再由 QMT terminal target 人工导入 | Git release / 内网共享目录 / U 盘离线交付 / 自动同步 runner | 推荐方案隔离研究环境和交易 PC，传输对象可审计、可校验、可回滚；自动同步 runner 会引入运行授权和权限风险 | 影响 CR046-S02/S03 的 manifest、导入步骤和验证证据字段；不授权真实传输、导入、运行或交易 | 若 CP5 发现交易 PC 环境约束不同，可在 LLD 中把 transfer_channel 设为可配置枚举，但默认仍不自动运行 |

## 处理结论

- 审批结论：`cp4-auto-pass-pending-lld`
- [ ] 自动批准（低风险）
- [ ] 待人工确认（中风险）
- [x] 待人工审批（高风险）

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| USER-FACT | `USER-20260613-QMT-BROKER-OPENED` | 用户补充 QMT 已在券商开通，可在 QMT 终端里运行策略；当前没有 MiniQMT 权限，若未来考虑自研 runner 可再申请；掘金尚未开通券商，仅有掘金量化账号。 |
| USER-FACT | `USER-20260613-DUAL-TARGET-FRAMEWORK` | 用户要求后续研究策略同时支持 QMT 和 MiniQMT；当前先设计框架和验证框架，后续再开始策略交付；框架需包含策略交付和 MiniQMT runner 组件安装。 |
| USER-FACT | `USER-20260613-FRAMEWORK-FIRST-RESEARCH-FOLLOWUP` | 用户要求先把 QMT 框架订下来；策略交付和验证等有权限后再做；研究完框架后继续完善研究框架。 |
| RUN-EXEC | `runs/RUN-EXEC-20260613-001.md` | 用户 Windows 掘金 API / gmtrade 只读校验和本地 paper simulation 执行反馈。 |
| CR | `CR-041` | 本地 paper simulation runner，作为 order intents 输入来源。 |
| CR | `CR-044` | Goldminer simulation admission 离线准入设计，作为安全约束输入。 |
| CR | `CR-045` | Goldminer Windows bridge readonly probe skeleton，作为 Windows 环境事实输入。 |
