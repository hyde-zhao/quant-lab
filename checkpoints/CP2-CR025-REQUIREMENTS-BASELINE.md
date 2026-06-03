---
checkpoint_id: "CP2"
checkpoint_name: "CR-025 需求 / 场景基线人工审查"
type: "auto_then_manual"
status: "approved"
owner: "meta-po"
created_at: "2026-05-31T22:18:00+08:00"
reviewed_by: "user"
reviewed_at: "2026-06-01T21:43:54+08:00"
auto_check_result: "process/checks/CP2-CR025-REQUIREMENTS-BASELINE.md"
target:
  phase: "requirement-clarification"
  change_id: "CR-025"
  artifacts:
    - "process/USE-CASES.md"
    - "process/REQUIREMENTS.md"
    - "process/CLARIFICATION-LOG.md"
---

# CP2 CR-025 需求 / 场景基线人工审查

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---:|---|
| `process/checks/CP1-CR025-USE-CASE-COMPLETENESS.md` | PASS | 0 | UC-19、REQ-161 至 REQ-173 完整，安全边界明确。 |
| `process/checks/CP2-CR025-REQUIREMENTS-BASELINE.md` | PASS | 0 | CP2 自动预检通过，可发起人工确认。 |
| `process/checks/CP2-CR025-DISCUSSION-CHECKPOINT.json` | PASS | 0 | Scenario Gray Areas desk review 完成，`cp2_ready=true`。 |

## Decision Brief

### 待人工决策清单

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣分析 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|---|
| DQ-CP2-CR025-01 | `scope` | 是否接受 CR-025 的需求 / 场景基线修订为 production-grade research-to-execution route：Backtrader 仅作为 optional execution realism / semantic reference，CR-025 负责研究执行语义对照与 target portfolio / order intent 衔接，不替代 lightweight 主路径、不实现真实 QMT？ | 接受 UC-19、SM-33 至 SM-40、REQ-161 至 REQ-172 的修订范围；默认 lightweight 不变，Backtrader 只做研究对照，生产执行由 QMT OMS / risk / adapter / broker lake / staged activation 路线承接。 | 备选 A：缩小为只做文档 / HLD，不进入后续实现设计；备选 B：扩大为 Backtrader 主路径迁移；备选 C：另起完整交易平台 / LEAN / 自研事件驱动框架评估 CR。 | 推荐方案对齐用户生产级目标，并把 CR-025 控制在研究到执行接口对齐；A 风险最低但无法验证执行语义；B 只能统一回测框架，不能解决生产 OMS / 风控 / 实盘治理；C 可能正确但范围远大，应独立立项。 | 影响研究执行后端、默认 engine 声明、target portfolio / order intent 合同、后续 HLD / LLD 和 CR tracking；误判会导致主路径被替换或把 CR-025 误当真实运行授权。 | 若后续发现必须迁移主路径或完整交易平台，另起架构 CR；若 order intent 衔接无法在 CR-025 内收敛，回退 CP2 或拆分新 CR。 |
| DQ-CP2-CR025-02 | `implementation` | 是否接受 CP5 前不得实现、不得新增 Backtrader 依赖、不得修改 `pyproject.toml` / `uv.lock`？ | 接受 CP5 前只做需求 / 设计 / LLD；实现、依赖变更和 Backtrader 运行必须等 CP5 approved。 | 备选 A：允许 CP3 后做 Spike 依赖验证；备选 B：现在引入 optional extra。 | 推荐方案符合门控，避免依赖泄漏；A 需单独 Spike；B 会越过当前 CP5。 | 影响依赖锁、默认环境、CI / 回归稳定性。 | 若 CP3 发现依赖策略无法设计，转 Spike 或回退 CP2。 |
| DQ-CP2-CR025-03 | `runtime_authorization` | 是否确认本 CP2 不授权真实 broker、QMT / MiniQMT / XtQuant、provider fetch、lake write、publish 或凭据读取？ | 确认全部不授权，相关计数必须为 0。 | 备选 A：为后续真实 broker 单独建 CR；备选 B：为数据补取 / publish 单独建 CR。 | 推荐方案保持研究路线与真实运行隔离；备选需要独立授权和更高风险门控。 | 防止 optional semantic reference 和 order intent 衔接被误解为真实交易、真实数据运行或 QMT gateway / simulation / live 授权。 | 任一真实操作需求出现时，停止 CR-025 并新建独立 CR / per-run authorization。 |
| DQ-CP2-CR025-04 | `follow_up_tracking` | 是否接受把 CR tracking 补充为三条主线视图，并据此调整推进顺序？ | 接受三条主线：A 研究可信度，B 回测 / 模拟一致性，C QMT 生产执行。CR-025 先完成 B 线 CP2/CP3 范围冻结；CR-020 可在用户明确启动后作为 C 线 gateway health 准入并行候选，但不授权交易；CR-026..CR-028 继续后置。 | 备选 A：维持原“CR-025 完全关闭后才启动 CR-020”；备选 B：立即启动 CR-020 并把 CR-025 暂停；备选 C：CR-025 与 CR-026 并行。 | 推荐方案保留当前 active lock，又不把真实 QMT 路线无条件推迟到 CR-025 CP8；A 最保守但会延迟生产链路基础设施；B 推进 QMT 更快但会增加服务 / 授权风险；C 增加研究依赖和 runner 冲突。 | 影响后续 CR 排序、active lock、gateway health、研究准入和高风险授权边界。 | 若用户决定生产执行优先，先做 CR-020 冲突预检并单独发起 CP2；若 CR-025 HLD 发现 order intent 衔接不足，先收敛 CR-025 再启动 C 线。 |

| 字段 | 内容 |
|---|---|
| 推荐决策 | `approve`：接受 CR-025 修订后的 production-grade research-to-execution 需求 / 场景基线，进入 CP3/HLD；不授权实现、依赖变更、服务启动、QMT、simulation、live 或真实运行。 |
| 备选方案 | `修改: <具体修改点>`：修改 scope、依赖策略、安全边界或推进顺序后重发 CP2；`reject`：不接受 CR-025 当前需求 / 场景基线，回退到 requirement-clarification。 |
| 影响维度 | 用户价值：获得可评审的 production-grade research-to-execution 路线入口；实现复杂度：中到高；可验证性：依赖 clean feed、semantic diff report 与 order intent 字段合同；维护成本：需保持 optional 隔离和 tracking 主线视图；安全 / 权限：真实运行全部不授权。 |
| 优劣分析 | 推荐方案保持轻量主路径稳定，同时让 Backtrader 对照能力服务于回测 / 模拟一致性；主要代价是多一条 optional reference 契约、order intent 衔接和回归矩阵。 |
| 风险与回退 | 风险等级：中。若用户误把 CP2 当作实现授权，可能导致依赖泄漏或真实运行越权；回退方式是将 `USE-CASES.md` / `REQUIREMENTS.md` CR-025 增量保持 draft 并回到 CP2 前澄清。 |
| 用户需决策事项 | 是否接受 DQ-CP2-CR025-01 至 DQ-CP2-CR025-04 的推荐方案。 |

### CP2 追加 Decision Brief 字段

| 字段 | 内容 |
|---|---|
| 用户真实意图 | 建设生产级策略研究回测、模拟盘和实盘框架；CR-025 只负责研究执行语义对照、依赖隔离、clean feed、semantic diff 和 target portfolio / order intent 衔接，不替代轻量主路径，不接真实 broker。 |
| 场景覆盖 | 修订 UC-19，覆盖 production-grade research-to-execution 三条主线、optional reference 选择、依赖隔离、clean feed gate、semantic diff report、order intent 衔接、声明边界和安全计数。 |
| 认知盲区补充 | Backtrader 不替代 lightweight；未安装 Backtrader 是合法环境；Backtrader 输出不是 QMT admission pass 或 production truth；CR-025 approve 也不是 gateway、simulation、live 或账户操作授权。 |
| Scenario Gray Areas | SGA-025-01/02/04/05 已 resolved；SGA-025-03 和 Q-051 作为 CP3 设计项，不阻断 CP2。 |
| Deferred Ideas | 真实 broker、主路径迁移、provider/lake/publish、QMT admission 误用、Backtrader 源码级移植实现 / 完整事件驱动框架、CR-025 内直接真实运行均 deferred；Backtrader 模块级分析进入 CP3/HLD 输入。 |
| 用户追加 CP3 指令 | meta-se 必须充分分析本地 Backtrader 项目 `/home/hyde/download/backtrader`，在 HLD 中记录可借鉴、可适配、可移植候选和禁止移植模块；源码级移植若被推荐，必须单列许可证、维护、回归和授权影响，不构成 CP2/CP3 实现授权。 |
| discussion log / checkpoint | `process/discussions/CP2-CR025-SCENARIO-DISCUSSION-LOG.md`；`process/checks/CP2-CR025-DISCUSSION-CHECKPOINT.json`。 |

## 用户视角复述与不授权项

如果你回复 `approve`，表示你接受以上 4 项推荐方案，允许 CR-025 进入 CP3/HLD 设计。

这不表示授权以下 10 类操作：

| 不授权项 | 状态 |
|---|---|
| 实现 Backtrader backend 或修改业务代码 | 不授权 |
| 修改 `pyproject.toml` / `uv.lock` 或新增 Backtrader 依赖 | 不授权 |
| 运行 Backtrader optional backend | 不授权 |
| 复制 / 移植 Backtrader 源码实现或自研完整事件驱动交易框架 | 不授权；仅授权 CP3/HLD 分析模块级借鉴 / 适配 / 移植候选 |
| 真实 broker / Backtrader live store | 不授权 |
| QMT / MiniQMT / XtQuant、simulation、live、account query、order/cancel | 不授权 |
| provider fetch 或真实联网补数 | 不授权 |
| lake write、broker lake write、catalog publish | 不授权 |
| 读取、打印、记录或保存任何凭据 / token / session / cookie / 交易密码 | 不授权 |
| 把 Backtrader 输出声明为 production truth、simulation-ready 或 QMT admission pass | 不授权 |

## Entry Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| CP1 通过 | 待审查 | `process/checks/CP1-CR025-USE-CASE-COMPLETENESS.md` | 结论 PASS。 |
| CP2 自动预检通过 | 通过 | `process/checks/CP2-CR025-REQUIREMENTS-BASELINE.md` | 结论 PASS。 |
| 场景 / 需求增量可读 | 通过 | `process/USE-CASES.md`、`process/REQUIREMENTS.md` | 均已确认，进入 CP3/HLD。 |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 是否接受 UC-19 场景基线 | 通过 | `process/USE-CASES.md` | 用户批准 CR-025，并追加 Backtrader 本地项目分析要求。 |
| 2 | 是否接受 REQ-161 至 REQ-173 需求基线 | 通过 | `process/REQUIREMENTS.md` | 用户批准 CR-025，并追加 Backtrader 本地项目分析要求。 |
| 3 | 是否接受 research-to-execution route / Backtrader optional reference / lightweight default 范围 | 通过 | DQ-CP2-CR025-01 | 允许 CP3/HLD 分析 Backtrader 模块；不改变 lightweight 默认主路径。 |
| 4 | 是否接受 CP5 前不得实现 / 改依赖 | 通过 | DQ-CP2-CR025-02 | Backtrader 本地项目分析不等于依赖变更或实现授权。 |
| 5 | 是否接受真实运行全部不授权 | 通过 | DQ-CP2-CR025-03 | 真实 broker / QMT / provider / lake / publish / credential 均不授权。 |
| 6 | 是否接受三条主线 tracking 与 CR-020 可独立冲突预检的推进口径 | 通过 | DQ-CP2-CR025-04 | 当前先推进 CR-025 CP3；CR-020 仍需后续单独启动。 |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| 若 approve：CR-025 可进入 CP3/HLD | 通过 | CP2 自动预检 + 本人工确认 | 用户已批准；CP3 必须包含 Backtrader 本地项目模块级分析。 |
| 若修改：回退 CP2 前澄清 | N/A | 用户修改意见 | 用户未要求回退 CP2，仅追加 CP3/HLD 分析约束。 |
| 若 reject：CR-025 保持 active 但 blocked / 待重整 | N/A | 用户拒绝意见 | 用户未拒绝。 |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| CP2 自动预检 | `process/checks/CP2-CR025-REQUIREMENTS-BASELINE.md` | 通过 | 自动预检 PASS。 |
| CP2 人工审查稿 | `checkpoints/CP2-CR025-REQUIREMENTS-BASELINE.md` | 通过 | 本文件已回填人工审查结果。 |
| 场景基线增量 | `process/USE-CASES.md` | 通过 | UC-19 已确认，追加 Backtrader 本地项目分析约束。 |
| 需求基线增量 | `process/REQUIREMENTS.md` | 通过 | REQ-161 至 REQ-173 已确认。 |

## 人工审查结果

- 结论：`approved`
- 审查人：user
- 审查时间：2026-06-01T21:43:54+08:00
- 修改意见：允许按 meta-po 推荐推进 CR-025；CP3/HLD 必须让 meta-se 充分分析本地 Backtrader 项目 `/home/hyde/download/backtrader`，对比哪些模块可借鉴或移植，移植候选也必须在 HLD 中记录。
- 风险接受项：接受 CP3/HLD 进行模块级移植可行性分析；不接受 CP2/CP3 直接实施源码级移植、依赖变更、Backtrader 运行、QMT / simulation / live 或真实账户操作。
