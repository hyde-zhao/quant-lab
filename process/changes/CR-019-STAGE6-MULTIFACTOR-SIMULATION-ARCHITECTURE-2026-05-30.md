---
cr_id: "CR-019"
status: "closed"
impact_level: "high"
workflow_mode_before: "standard"
workflow_mode_after_change: "standard"
fast_lane_upgrade_reason: "本变更确认阶段六 A 股多因子模拟盘准入的工程路线，并将 Linux/WSL 研究节点与 Windows QMT 节点之间的通信方式从 signed file drop 调整为 FastAPI 本地服务；同时冻结 Qlib、Backtrader、分钟数据、QMT Level2 的引入优先级。命中外部接口、权限安全、QMT 交易节点、服务鉴权、跨系统通信、多 Story 依赖和后续 LLD 设计，必须走 standard。"
rollback_to: "requirement-clarification"
approval_result: "cp8-approved-closed"
created_at: "2026-05-30T13:58:46+08:00"
created_by: "meta-po"
approved_by: "user"
approved_at: "2026-05-30T13:58:46+08:00"
source: "user"
approval_text: "D7 使用fastAPI搭建本地服务，文档你可以参考/home/hyde/workspace/llm-wiki/llm-wiki/work/studies/quant-trading/sources/迅投QMT极速策略交易系统说明文档.md。其他按照你建议的方案实施。请帮我形成一个CR，CR需要包含足够的上下文，必要的参考文档链接。"
linked_issue: ""
updated_at: "2026-05-31T10:43:18+08:00"
cp8_auto_result: "process/checks/CP8-CR019-DELIVERY-READINESS.md"
cp8_manual_review: "checkpoints/CP8-CR019-DELIVERY-READINESS.md"
cp8_approved_by: "user"
cp8_approved_at: "2026-05-31T10:43:18+08:00"
follow_up_tracking: "process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md"
---

# CR-019 阶段六 A 股多因子模拟盘架构与 QMT FastAPI 本地服务桥接

## 变更描述

用户已确认阶段六目标不是“完成 20 只股票练习”，而是推进到 **A 股多因子策略制定，并达到可申请模拟盘状态**。在前一轮架构取舍分析中，用户批准以下决策组合：

```text
D1 = Backtrader 后置 optional execution backend
D2 = Qlib 后置 isolated runner
D3 = 分钟数据不作为 P0，只做后置 Spike
D4 = QMT xtdata 不进 WSL 主路径；Windows QMT bridge 是最终 simulation 推荐架构
D5 = 暂不申请 QMT Level2
D6 = shadow + 5日 dry-run 后再申请 QMT simulation
D7 = 第一版 QMT 桥接通信方式改为 FastAPI 本地服务，而不是 signed file drop
```

本 CR 的目标是把上述决策纳入 `local_backtest` 的正式变更管理，形成后续 HLD、Story、LLD、实现和验证的统一上下文。CR-019 不直接授权真实 QMT / MiniQMT / XtQuant 操作，不授权真实发单、撤单、账户查询、凭据读取、真实 broker lake 写入或真实 simulation run；这些仍必须受 CR-015 / CR-016 / CR-017 的 stage gate、per-run authorization、reconciliation gate、kill switch 和 recovery gate 约束。

### 用户已批准决策

| 决策 ID | 批准方案 | 影响 |
|---|---|---|
| D1 | Backtrader 不作为阶段六 P0；在数据 gate 和候选策略稳定后，作为 W6 optional execution backend 做实 | 短期优先完成多因子数据、因子、组合和准入报告；后续再补订单、成交、现金、持仓、滑点、佣金对照。 |
| D2 | Qlib 不进入主干事实源；先借鉴 workflow，后续 W7 通过 isolated runner / exporter 做 benchmark | 避免 Qlib provider_uri、社区数据或默认 workflow 污染本项目 production current truth。 |
| D3 | 分钟级数据不作为 P0；先完成日频多因子模拟盘准入，后续在执行质量场景做 1m/5m Spike | 避免全市场分钟数据的存储、校验、索引、回放复杂度提前阻塞主线。 |
| D4 | QMT xtdata 研究阶段非必须；最终 simulation 前采用 Windows QMT bridge，WSL 不直接依赖 xtquant | 符合 QMT 运行在 Windows 主系统、回测框架运行在 WSL 的现实部署。 |
| D5 | 暂不申请 QMT Level2；仅在微观结构、盘口深度、逐笔成交、冲击成本成为主要风险时再申请 | 当前阻断在日频多因子、PIT、行业 / 市值、benchmark、交易状态和 dry-run。 |
| D6 | 先完成本地 shadow + 连续 5 个真实交易日 dry-run，再申请 QMT simulation per-run authorization | 保持 CR016 的 staged activation 路径，不把失败策略推入模拟盘。 |
| D7 | WSL 与 Windows QMT 节点的第一版桥接改为 FastAPI 本地服务 | 替代此前 CP3 已批准的 signed file drop 默认方式；需要重新设计鉴权、接口、状态机、部署和验证。 |

### 当前基线

| 基线 | 当前事实 | 证据 |
|---|---|---|
| 阶段六目标 | 已扩展为 A 股多因子模拟盘准入，新增实验 49-66 | `/home/hyde/workspace/llm-wiki/llm-wiki/work/studies/quant-trading/working/阶段六学习目标和计划.md` |
| 策略状态 | latest production current truth 重跑后，旧多因子和低波策略均未通过准入；QMT admission allowed count = 0 | `process/checks/REAL-TUSHARE-CR018-PRODUCTION-RERUN-2026-05-29.md`、`reports/production_current_truth/**/qmt-admission-evidence.json` |
| QMT foundation | CR-015 / CR-016 / CR-017 已形成 shadow、dry-run、mock、OMS、risk gate、runbook、raw-only 价格边界；真实 operation 仍 blocked | `docs/QMT-SIMULATION-LIVE-RUNBOOK.md`、`docs/QMT-INCIDENT-PLAYBOOK.md`、`trading/qmt_adapter.py` |
| CP3 旧通信决策 | Q-038 曾批准 Linux 研究节点与 Windows QMT 节点默认使用 signed file drop + ack/error enum，后续可升级本地 RPC | `process/STATE.md`、`process/CLARIFICATION-LOG.md#Q-038` |
| 新通信决策 | 用户已要求 D7 使用 FastAPI 搭建本地服务 | 本 CR 用户批准文本 |
| Backtrader | 已有 optional backend 和 clean feed gate，当前偏 smoke；不接管默认轻量主路径 | `engine/backtrader_adapter.py`、`docs/ROADMAP.md` |
| Qlib | 已被定义为 isolated benchmark runner / workflow 参考，不进入默认依赖、不接管数据事实源 | `docs/ROADMAP.md`、`/home/hyde/workspace/llm-wiki/llm-wiki/work/studies/quant-trading/working/sources/microsoft-qlib-analysis-report.md` |
| QMT 说明文档 | QMT 支持模型研究、Python 模型、模型交易、模拟 / 实盘模式、委托 / 成交 / 持仓查看、Level2 行情展示 | `/home/hyde/workspace/llm-wiki/llm-wiki/work/studies/quant-trading/sources/迅投QMT极速策略交易系统说明文档.md` |

## 参考文档

| 类型 | 路径 / 链接 | 用途 |
|---|---|---|
| 阶段六主计划 | `/home/hyde/workspace/llm-wiki/llm-wiki/work/studies/quant-trading/working/阶段六学习目标和计划.md` | 阶段六实验 49-66 的学习与实践范围。 |
| 多因子准入方案 | `/home/hyde/workspace/llm-wiki/llm-wiki/work/studies/quant-trading/working/stage6-simulation/MULTIFACTOR-SIMULATION-ADMISSION-PLAN.md` | 多因子策略从 research 到 simulation admission 的总体 gate。 |
| 数据缺口方案 | `/home/hyde/workspace/llm-wiki/llm-wiki/work/studies/quant-trading/working/stage6-simulation/DATA-GAP-SOURCE-ACQUISITION-PLAN.md` | Tushare 5000、QMT Level1 / Level2、分钟数据优先级。 |
| local_backtest 改进方案 | `/home/hyde/workspace/llm-wiki/llm-wiki/work/studies/quant-trading/working/stage6-simulation/LOCAL-BACKTEST-IMPROVEMENT-PLAN.md` | W1-W8 改进路线，含 Backtrader / Qlib 边界。 |
| QMT 系统说明 | `/home/hyde/workspace/llm-wiki/llm-wiki/work/studies/quant-trading/sources/迅投QMT极速策略交易系统说明文档.md` | QMT 客户端、模型研究、模型交易、模拟 / 实盘模式、Level2 行情、交易面板事实来源。 |
| QMT xtdata 官方文档 | `https://dict.thinktrader.net/nativeApi/xtdata.html` | xtdata 行情模块能力、历史 / 实时 K 线、订阅、Level1 / Level2 字段说明。 |
| QMT staged activation runbook | `docs/QMT-SIMULATION-LIVE-RUNBOOK.md` | `shadow -> simulation -> live_readonly -> small_live -> scale_up` gate、per-run authorization、reconciliation、kill switch。 |
| QMT incident playbook | `docs/QMT-INCIDENT-PLAYBOOK.md` | heartbeat、risk、reconciliation、manual trigger、recovery 处理边界。 |
| Backtrader / Qlib roadmap | `docs/ROADMAP.md` | Backtrader optional backend 与 Qlib isolated runner 的既有架构边界。 |
| Backtrader adapter | `engine/backtrader_adapter.py` | 当前 optional backend、clean feed gate、延迟 import、安全计数实现基线。 |
| QMT adapter contract | `trading/qmt_adapter.py` | 当前只允许 shadow / dry-run / mock，不调用真实 QMT / MiniQMT / XtQuant / broker API。 |

## 目标范围

### In Scope

1. 将阶段六 A 股多因子模拟盘准入路线纳入正式 CR，后续补充 USE-CASES / REQUIREMENTS / HLD / ADR / Story / LLD。
2. 明确 Backtrader、Qlib、分钟数据、QMT Level2 的优先级和非前置边界。
3. 将 Windows QMT 节点与 local_backtest / WSL 研究节点的桥接方式设计为 **QMT 独立 C/S 模块**：C 侧位于 local_backtest，S 侧部署在 Windows QMT 节点并提供 FastAPI gateway，由 S 侧将 REST 请求转换为 QMT / XtQuant 接口调用并访问 QMT 服务端。
4. 设计 C 侧统一 Python client / 函数接口、可选薄 CLI、S 侧 FastAPI gateway 接口契约、鉴权、部署、日志脱敏、heartbeat、stage gate、reconciliation、kill switch、fallback 和测试策略。
5. 保持 CR-015 / CR-016 / CR-017 的真实操作门禁：无 per-run authorization 时真实 QMT operation 计数必须为 0。
6. 后续通过 Story 分批实现：先 dry-run / readonly capability / mock endpoint，再进入 simulation-gated endpoint。

### Out of Scope

1. 本 CR 创建时不实现 FastAPI 代码，不新增依赖，不修改 `pyproject.toml` / `uv.lock`。
2. 不启动 QMT / MiniQMT / GUI，不调用 xtdata / xttrader，不查询真实账户，不提交真实订单或撤单。
3. 不把 Qlib 加入默认依赖，不让 Qlib 读取 `.env`、token、provider_uri、raw path 或写数据湖。
4. 不把 Backtrader 变成默认回测框架，不让 Backtrader 触发 fetch/backfill、PIT、复权或 benchmark 补齐。
5. 不把分钟 / tick / Level2 作为阶段六 P0。
6. 不因 FastAPI 服务存在而绕过 CR016 的 per-run authorization、stage gate、reconciliation gate 和 kill switch。

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `process/USE-CASES.md` | 原文档更新 | 保留 UC-10..UC-12 QMT 场景和既有 signed file drop 基线；新增 CR019 FastAPI 本地服务桥接场景，并说明旧通信方案被替换为备选 | `## 修订记录` | completed |
| `process/REQUIREMENTS.md` | 原文档更新 | 保留 REQ-098..REQ-122；新增阶段六多因子准入、QMT C/S bridge、安全鉴权、local_backtest / Windows 部署、D1-D7 与 Q40 / Q44 决策需求 | `## 修订记录` | completed |
| `process/HLD.md` | 原文档更新 | 保留现有研究 / 数据湖 / QMT 边界；新增阶段六多因子模拟盘架构与 QMT C/S bridge companion 关系 | `## 修订记录` | completed |
| `process/HLD-QMT-TRADING.md` | 原文档更新 | 保留 CR015/016/017 QMT foundation / activation 设计；将默认通信从 signed file drop 调整为 FastAPI 服务，signed file drop 降为 fallback | `## 修订记录` | completed |
| `process/ARCHITECTURE-DECISION.md` | 原文档更新 | 保留 ADR-053..061；新增 CR019 ADR：Backtrader 后置、Qlib 后置、分钟数据后置、QMT C/S bridge、C 侧接口形态、QMT Level2 后置 | `## 修订记录` | completed |
| `process/STORY-BACKLOG.md` | 原文档更新 | 保留 CR015/016/017/018 Story；新增 CR019 Story，标注对 CR018 production current truth / strategy admission 的依赖 | `## 修订记录` | completed |
| `process/DEVELOPMENT-PLAN.yaml` | 原文档更新 | 保留已完成 Waves；新增 CR019 Wave，QMT C/S bridge 置于多因子 dry-run / admission 后置或并行 Spike | YAML history / wave 注释 | completed |
| `process/TEST-STRATEGY.md` | 原文档更新 | 保留 CR015/016/017/018 测试策略；新增 QMT C/S bridge API contract、C 侧 client、auth、stage gate、forbidden operation、WSL/Windows smoke 策略 | `## CR-019` 增量章节 | completed |
| `docs/QMT-SIMULATION-LIVE-RUNBOOK.md` | 原文档更新 | 保留 CR016 staged activation；新增 QMT C/S bridge 启动前置、heartbeat、授权、kill switch 和 fallback 操作边界 | 文档 CR019 章节 | completed |
| `docs/QMT-INCIDENT-PLAYBOOK.md` | 原文档更新 | 保留 incident 枚举；新增 FastAPI 服务不可达、鉴权失败、heartbeat 丢失、adapter timeout、reconciliation diff 的 incident 映射 | 文档 CR019 章节 | completed |
| `docs/ROADMAP.md` | 原文档更新 | 保留 Backtrader / Qlib 边界；新增 CR019 决策落点和阶段顺序 | Backtrader/Qlib 章节 | not-in-current-cp8-delivery |
| `README.md` / `docs/USER-MANUAL.md` | 原文档更新 | 保留 QMT later-gated 说明；新增 QMT C/S bridge 的用户可见限制和不授权声明 | 对应 QMT / Stage6 章节 | completed |
| `trading/**` | HLD / LLD 后更新 | 保留 CR015 shadow / dry-run / mock adapter；新增 FastAPI gateway 只能经 LLD / CP5 后实现 | 不适用 | completed-offline-contract |
| `tests/**` | HLD / LLD 后更新 | 保留现有 CR015/016/017 安全测试；新增 FastAPI API contract、auth、forbidden operation、mock transport 测试 | 不适用 | completed |

## 旧基线映射

| 原基线对象 | 新增 / 修改对象 | 保留策略 | 映射说明 |
|---|---|---|---|
| Q-038：signed file drop + ack/error enum 默认通信 | D7：FastAPI 本地服务 bridge | 原文保留为历史决策 + 备选 fallback | 用户已明确要求 D7 使用 FastAPI；signed file drop 不删除，降级为 FastAPI 不可用时的 fallback。 |
| CR015 QMT adapter shadow / dry-run / mock only | CR019 QMT C/S bridge API contract | 原文保留 + 包装调用 | QMT gateway 不得绕过 CR015 adapter mode、raw-only、risk gate、stage gate。 |
| CR016 staged activation | CR019 FastAPI simulation-gated endpoints | 原文保留 + 新增入口 | FastAPI 的真实 simulation endpoint 只有在 CR016 stage gate + per-run authorization PASS 时可用。 |
| CR017 raw execution policy | FastAPI order intent schema | 原文保留 + 强制继承 | FastAPI request 中执行价和对账价只能使用 raw / broker price；qfq/hfq 只能作为研究 metadata。 |
| docs/ROADMAP Backtrader optional backend | CR019 Backtrader W6 后置 | 原文保留 | Backtrader 继续 optional，不阻断阶段六 P0。 |
| docs/ROADMAP Qlib isolated runner | CR019 Qlib W7 后置 | 原文保留 | Qlib 继续 isolated，不进入主干事实源。 |
| CR014 / CR018 minute / Level2 blocked claims | CR019 分钟 / Level2 后置 Spike | 原文保留 | 分钟 / Level2 不解除 blocked claim；后续独立 Story 和授权后才能接入。 |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论（true/false） | 处理动作 |
|------|----------|-----------|--------------------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | `REQUIREMENTS.md`、阶段六多因子准入、QMT C/S bridge、QMT 后置门控 | true | 新增 CR019 需求：D1-D7、Q40 多基准 + primary benchmark、QMT C/S 模块、C 侧接口形态、FastAPI gateway、接口鉴权、WSL/Windows 部署、Backtrader/Qlib/分钟/Level2 优先级。 |
| 场景层 | 是否改变测试矩阵覆盖范围 | `USE-CASES.md`、QMT simulation operator、research owner、trading node owner | true | 新增 QMT C/S 模块和 Windows QMT FastAPI 服务桥接场景；覆盖 C 侧 client、S 侧 gateway、完整 endpoint matrix、运行门控、服务故障 fallback。 |
| 计划层 | 是否改变 Phase、Wave、任务依赖 | `DEVELOPMENT-PLAN.yaml`、Story DAG、CR018 / CR016 依赖 | true | 回退到 requirement-clarification；CR019 后续必须经过 CP2、CP3、CP4、全量 LLD、CP5 后才能实现。 |
| 安全层 | 是否引入新的高风险动作或权限要求 | FastAPI 服务、QMT / MiniQMT 节点、可选请求鉴权、日志、凭据、真实 broker 操作 | true | FastAPI gateway 必须支持完整 QMT 功能接口类别，但真实转发受 run mode / stage gate / risk gate / kill switch 控制；第一版可在受控局域网内不做应用层鉴权，或采用最简 token/HMAC；必须设计日志脱敏、bind / firewall、fallback 和事故处理。 |
| 交付层 | 是否需要重新生成交付物或回归子集 | README、USER-MANUAL、QMT runbook、incident playbook、TEST-STRATEGY、API docs | true | 后续刷新文档、API contract、runbook、测试策略、用户手册和回归集。 |

## 回退决策

- 影响范围：全局。
- 回退到阶段：`requirement-clarification`。
- 需要重新确认的对象：
  - D1-D7 是否作为 CR019 正式需求基线。
  - QMT C/S bridge 与 CR015/CR016/CR017 的边界。
  - C 侧接口形态：Python client / 函数调用、CLI-first 或 Python client 主接口 + 薄 CLI。
  - FastAPI 监听地址、是否启用最简鉴权、日志脱敏、启动和停止方式。
  - WSL -> Windows QMT 节点连接方式和防火墙策略。
  - signed file drop 是否保留为 fallback。
  - 完整 QMT endpoint matrix、simulation / live / account / cancel / query 的运行门控字段。
  - Backtrader / Qlib / 分钟数据 / Level2 的后置触发条件。

## fast-lane 判定

| 条件 | 是否命中 | 说明 |
|---|---|---|
| 仅低风险轻量实现 / 文档 / 规则修改 | false | 涉及跨系统服务、QMT 节点、接口鉴权和后续真实 simulation gate。 |
| 修改架构、权限、安全边界或平台安装路径 | true | QMT C/S bridge 改变 CR016/Q-038 通信架构和安全边界。 |
| 修改外部接口契约、文件所有权或多 Story 依赖 | true | 涉及 `trading/**`、runbook、测试、WSL/Windows deployment、API schema。 |
| 需要 HLD / LLD 才能解释影响 | true | 需要定义 endpoint、state gate、auth、heartbeat、fallback、test strategy。 |
| 是否保持 fast-lane | false | 必须 standard。 |

## Architecture Gray Areas

| Gray Area | Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|---|
| local_backtest / WSL 与 Windows QMT 通信方式 | QMT C/S 模块：C 侧 Python client + Windows FastAPI S 侧 gateway | 自动化强，适合 heartbeat、capability、snapshot、ack/recon；用户已指定模块从框架摘离且 Windows 可运行 / 可安装 | 需要 C/S 契约、服务生命周期、防火墙、接口测试和 incident 处理 | trading、docs、tests、runbook、安全 | 推荐 | 若本地网络 / 防火墙不稳定，切回 signed file drop fallback。 |
| WSL 与 Windows QMT 通信方式 | signed file drop | 简单、可审计、误触发风险低 | 自动化弱，实时性差，不符合用户 D7 新要求 | runbook、gateway | 备选 fallback | FastAPI 不可用、端口策略受限、实盘前需要最低风险降级时使用。 |
| C 侧接口形态 | Python client / 函数调用为主 + 薄 CLI | 内部策略、OMS、测试和运行治理可类型化调用，便于 mock；CLI 仍可用于人工 smoke 和运维 | 需要维护一层 client API 和 CLI wrapper | trading、tests、docs、runbook | 推荐 | 若后续主要由外部脚本或多语言系统调用，可切换 CLI-first 或 REST SDK。 |
| C 侧接口形态 | CLI-first | 手工操作直观、便于 shell 脚本 | local_backtest 内部调用需进程管理、文本解析、退出码和超时处理，测试成本高 | trading、tests | 备选 | 只在主要使用方式变成外部命令编排时采用。 |
| C 侧接口形态 | 纯 Python-only | 内部集成最简单，接口最薄 | 缺少独立人工检查和运维入口 | trading、tests | 备选 | 只在确认无需人工 smoke / 运维命令时采用。 |
| FastAPI 服务能力边界 | 完整 QMT endpoint matrix + 运行门控 | 满足用户“完整 QMT 功能接口”目标，同时通过 run mode / stage gate / risk gate 控制真实转发 | HLD/LLD 和测试矩阵更复杂 | API、testing、runbook、安全、QMT | 推荐 | 若实现量过大，可按 Story 拆分，但接口目标不退回 dry-run-only。 |
| FastAPI 服务能力边界 | dry-run / readonly / mock only | 风险最小，能先验证部署和 API contract | 不满足用户要求的完整 QMT 功能支持 | API、testing、runbook | 不推荐作为目标基线 | 只可作为实现分批的首个 Story，不可作为最终网关范围。 |
| FastAPI 服务能力边界 | 局域网内所有真实 endpoint 无门控直转 | 集成最快 | 风险高，容易绕过 stage gate、risk gate 或 kill switch | 安全、QMT、incident | 不推荐 | 只有用户另行明确接受风险并新建授权门控才可考虑。 |
| 服务绑定方式 | Windows QMT 节点本地绑定 + WSL 专用访问策略 | 符合 QMT 在 Windows、研究在 WSL 的部署现实 | 需要环境 Spike 确认 WSL 到 Windows host IP、Windows 防火墙、端口策略 | deployment、security | 推荐 | 若无法安全限定 WSL 访问范围，改用 signed file drop fallback。 |
| 分钟数据 | 后置 1m/5m Spike | 不阻塞日频多因子 P0 | 执行质量评估暂时粗 | market_data、execution | 推荐 | 实验 58-59 显示执行成本成为主风险时启动。 |
| Backtrader | W6 optional backend | 补执行语义，不污染主路径 | 不能解决 alpha 和数据缺口 | engine、reports | 推荐后置 | 候选策略冻结后接入。 |
| Qlib | W7 isolated runner | 补 ML benchmark 和 workflow 纪律 | 数据导出 / 依赖隔离成本 | experiments、reports | 推荐后置 | 因子库和 report catalog 稳定后启动。 |

## QMT C/S Bridge 初始契约草案

> 本节只定义 CR intake 级候选契约，正式字段以 HLD / LLD / CP5 批准版为准。

### 推荐部署形态

```text
local_backtest QMT client module (C side)
  |
  | typed Python call from strategy / OMS / ops
  | REST request with run_id / intent_id / stage / mode
  v
Windows QMT FastAPI gateway (S side)
  |
  +--> capability / heartbeat
  +--> intent validation / dry-run / mock events
  +--> market / account / position / order / trade query
  +--> simulation submit / cancel
  +--> live-readonly / live submit / live cancel
  +--> reconciliation / kill-switch
  |
  v
MiniQMT / XtQuant / QMT client -> QMT service, only when run mode / stage gate / risk gate allow forwarding
```

### 候选 endpoint

| Endpoint 类别 | 第一版状态 | 用途 | 禁止项 |
|---|---|---|---|
| health / capabilities | required | 服务存活、版本、时间、QMT client 状态摘要、gateway 支持能力 | 不返回凭据或未脱敏账户信息；不因 capability 可见而授权真实操作。 |
| intent validate / dry-run | required | 校验 order intent schema、raw price policy、risk status、生成 mock ack / blocked reason | 不调用真实 QMT order API。 |
| market query | required | 通过 Windows gateway 查询 QMT 行情能力或字段覆盖 | 不作为研究事实源自动写 lake；不绕过 production data lake 声明边界。 |
| account / position / order / trade query | required | 支持账户、持仓、委托、成交等 QMT 查询接口类别 | 未满足 live-readonly / run mode 时返回 blocked；日志必须脱敏。 |
| simulation submit / cancel | required | 支持 QMT simulation 委托与撤单接口类别 | 未满足 simulation run mode、stage gate、risk gate、kill switch 时返回 blocked。 |
| live-readonly / live submit / live cancel | required but later-gated | 支持实盘只读、小资金实盘和撤单接口类别，供后续阶段启用 | 未满足 CR016 live_readonly / small_live / scale_up gate 时返回 blocked。 |
| reconciliation / kill-switch | required | 支持对账查询、停止新单、紧急停止等运行治理接口类别 | kill-switch 真实撤单动作必须受运行模式和人工策略约束。 |

### 安全与鉴权最低要求

| 要求 | 最低标准 |
|---|---|
| 默认模式 | Gateway 接口面支持完整 QMT 功能类别；C 侧通过 Python client / 函数接口发起调用；默认运行模式和真实转发条件由 HLD/LLD 冻结，未满足条件时返回 blocked。 |
| C/S 边界 | C 侧位于 local_backtest 内，不导入 xtquant；S 侧位于 Windows QMT 节点，接收 REST 请求并转换为 QMT / XtQuant 接口调用，再由 Windows QMT 客户端访问 QMT 服务端。 |
| 认证 | 第一版可在受控局域网内不做应用层鉴权；若 CP3 判定需要鉴权，采用最简 token / HMAC，token / secret 只在 Windows 节点环境中读取，不写入仓库、不写日志。 |
| 运行门控 | 真实 simulation / live / account / cancel / query 转发必须检查 run mode、stage gate、risk gate、kill-switch 状态和必要上下文；鉴权不是运行门控的替代品。 |
| 绑定与防火墙 | HLD/LLD 必须确认 Windows 监听地址、WSL 访问路径、局域网边界和 Windows 防火墙；禁止默认暴露到公网或不受控局域网。 |
| 日志 | 只记录脱敏 `run_id`、`intent_id`、状态、blocked reason、latency、endpoint；不得记录 token、密码、账户号、真实资金明细。 |
| 价格口径 | 真实 order intent 只能使用 `raw` / broker price；qfq/hfq 仅可作为 research metadata。 |
| 失败行为 | 可选鉴权失败、stage gate fail、risk fail、raw policy fail、heartbeat fail 均 hard block，adapter call count 必须为 0。 |
| fallback | FastAPI 不可达时，不自动绕过 gateway 改走真实 QMT；只能 blocked 或进入人工 dry-run / signed file drop 备选路径。 |

## LLD 设计批次门禁

- 是否需要 LLD 设计批次：true
- batch_id：`CR019-STAGE6-MULTIFACTOR-SIMULATION-ARCHITECTURE-BATCH-A`
- 批次范围来源：CR019 影响分析 / HLD / CP3 / CP4
- 批次内候选 Story：
  - `CR019-S01-stage6-multifactor-requirements-and-decision-baseline`
  - `CR019-S02-backtrader-qlib-minute-level2-priority-adr-refresh`
  - `CR019-S03-qmt-fastapi-bridge-hld-and-api-contract`
  - `CR019-S04-qmt-fastapi-bridge-full-endpoint-matrix-and-run-gates`
  - `CR019-S05-qmt-fastapi-bridge-windows-wsl-deployment-spike`
  - `CR019-S06-qmt-fastapi-bridge-windows-installable-command`
  - `CR019-S07-qmt-fastapi-bridge-simulation-live-account-cancel-interfaces`
  - `CR019-S08-qmt-client-module-python-api-and-cli-wrapper`
  - `CR019-S09-docs-runbook-incident-playbook-and-user-manual-refresh`
- 批次人工确认稿：`checkpoints/CP5-CR019-STAGE6-MULTIFACTOR-SIMULATION-ARCHITECTURE-LLD-BATCH.md`
- 开发启动条件：
  - [ ] CP2 需求基线通过。
  - [ ] CP3 HLD / ADR 通过。
  - [ ] CP4 Story DAG / parallel safety 通过。
  - [ ] 批次内全部 Story LLD 已输出。
  - [ ] 批次内全部 Story CP5 自动预检已通过。
  - [ ] 批次 CP5 人工确认结论为 `approved`。
  - [ ] FastAPI 真实 QMT / simulation endpoint 另有 per-run authorization 和 CR016 gate PASS。

## CP1 / CP2 需求基线结果

2026-05-30，`meta-pm/pm-wang` 已完成 CR-019 requirement-clarification / CP2 准备，结论如下：

| 检查点 | 文件 | 结论 | 说明 |
|---|---|---|---|
| CP1 用户场景完备门 | `process/checks/CP1-CR019-USE-CASE-COMPLETENESS.md` | PASS | 新增 UC-15 至 UC-18，覆盖阶段六多因子模拟盘准入、QMT C/S bridge、完整 endpoint matrix、运行门控、fallback 和后置能力边界。 |
| CP2 需求基线自动预检 | `process/checks/CP2-CR019-REQUIREMENTS-BASELINE.md` | PASS | 新增 REQ-138 至 REQ-160，覆盖 D1-D7、Q40 多基准、QMT C/S 模块、C 侧接口形态、FastAPI gateway、安全鉴权、WSL / Windows 部署、stage gate、per-run authorization、fallback、日志脱敏、禁止真实操作默认值和后置触发条件。 |
| CP2 人工审查稿 | `checkpoints/CP2-CR019-REQUIREMENTS-BASELINE.md` | approved | 用户已确认后进入 CP3 HLD / ADR / Story Plan；后续 CP3 / CP5 / CP8 也已完成。 |

CP2 blocker 已关闭。Q-039 至 Q-044 已在后续 CP3 / HLD、Story Plan、LLD 和 CP8 中按用户确认口径收敛；这些确认仍不授权真实 QMT / MiniQMT / XtQuant 操作、真实发单 / 撤单 / 账户查询、凭据读取、真实 provider fetch、真实 lake 写入、publish、真实 broker lake 写入或 simulation run。

## 执行链路

| 顺序 | 责任角色 | 动作 | 输入 | 输出 | 门控 | 完成后下一步 |
|---|---|---|---|---|---|---|
| 1 | `meta-po` | 创建 CR019 并记录 D1-D7 决策 | 用户请求、阶段六方案、QMT 文档、现有 CR015/016/017/018 状态 | 本 CR、STATE 更新 | CR 已登记 | 等待需求 / 场景增量 |
| 2 | `meta-pm` | 刷新 USE-CASES / REQUIREMENTS | CR019、阶段六计划、QMT 说明文档、runbook | UC/REQ 增量、CP2 Decision Brief 输入 | 不实现、不调用 QMT | 交回 meta-po |
| 3 | `meta-se` | 输出 HLD / ADR / Story Plan | CP2 approved、CR019 | HLD、ADR、Story Backlog、Development Plan、CP3/CP4 | 用户 CP3 approve | 进入 LLD |
| 4 | `meta-dev` | 输出全量 LLD | CP3/CP4 approved、Story Plan | LLD、CP5 自动预检 | 用户 CP5 approve | 进入实现 |
| 5 | `meta-dev` | 实现 QMT C/S bridge、C 侧 client、S 侧 gateway、完整 endpoint matrix 和安全 gate | CP5 approved、授权边界 | 代码、API schema、tests、CP6 | 无未授权真实 QMT operation | 交给 QA |
| 6 | `meta-qa` | 验证 API contract、auth、stage gate、forbidden operations、WSL/Windows smoke | CP6、tests、runbook | CP7、回归报告 | CP7 PASS | 文档收敛 |
| 7 | `meta-doc` | 刷新 runbook、incident playbook、README、USER-MANUAL | 验证结果、CR019 | 文档更新、CP8 输入 | 文档自检 | 交回 meta-po |
| 8 | `meta-po` | CP8 终验并关闭 CR | CP7、文档、用户确认 | CP8 审查稿、STATE 更新 | 用户 CP8 approve | 关闭 CR019 |

## 自动终验授权

- 是否启用：false
- 授权范围：不适用
- 适用检查点：CP8
- 自动通过条件：不适用
- 授权原文：
- 授权时间：
- 回填要求：已等待并于 2026-05-31T10:43:18+08:00 回填用户 CP8 人工确认。

## 处理结论

- 审批结论：`cp8-approved-closed`
- [ ] 自动批准（低风险）
- [ ] 待人工确认（中风险）
- [x] 已通过 CP8 人工终验并关闭当前离线合同 / 文档交付；真实 FastAPI simulation endpoint、真实 QMT operation、依赖变更和部署仍需后续独立 CR / Spike 与 per-run authorization。

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| CR | CR-015 | QMT foundation、OMS、adapter、risk gate、shadow / dry-run / mock 边界。 |
| CR | CR-016 | QMT staged activation、simulation / live_readonly / small_live / scale_up gate。 |
| CR | CR-017 | raw / qfq / hfq / returns_adjusted 双视图与 QMT raw execution policy。 |
| CR | CR-018 | production current truth 与 production rerun；QMT admission 当前仍 blocked。 |
| 外部文档 | `迅投QMT极速策略交易系统说明文档.md` | QMT 模型研究、模型交易、模拟 / 实盘、委托 / 成交、Level2 事实来源。 |
| 官方文档 | `https://dict.thinktrader.net/nativeApi/xtdata.html` | xtdata 行情模块接口事实来源。 |
| 项目文档 | `docs/QMT-SIMULATION-LIVE-RUNBOOK.md` | staged activation 和 per-run authorization 边界。 |
| 项目文档 | `docs/ROADMAP.md` | Backtrader / Qlib 接入边界。 |
