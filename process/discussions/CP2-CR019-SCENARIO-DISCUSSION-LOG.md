---
status: completed
change_id: CR-019
created_at: "2026-05-30T15:03:02+08:00"
created_by: meta-pm
source_use_cases: [UC-15, UC-16, UC-17, UC-18]
source_requirements: [REQ-138, REQ-139, REQ-140, REQ-141, REQ-142, REQ-143, REQ-144, REQ-145, REQ-146, REQ-147, REQ-148, REQ-149, REQ-150, REQ-151, REQ-152, REQ-153, REQ-154, REQ-155, REQ-156, REQ-157, REQ-158, REQ-159, REQ-160]
---

# CP2 CR-019 场景讨论日志

## 讨论目标

本轮记录 CR-019 requirement-clarification / CP2 准备的 Scenario Gray Areas。目标是把用户已确认的阶段六多因子模拟盘准入路线、QMT C/S bridge 主方案、完整 QMT endpoint matrix、运行门控和后置能力范围转化为可交给 meta-se 的场景与需求输入。

本轮没有向用户提出新的阻断问题，原因是 CR-019 已明确 D1-D7 决策，且用户已确认 Q40 推荐方案；剩余问题 Q-039 至 Q-044 均属于 CP3/HLD 需要冻结的设计细节或 CP2 推荐决策项，不阻断 CP2。

## 读取输入

| 输入 | 用途 |
|---|---|
| `AGENTS.md` | 确认 Meta Flow 目录、CR 增量追溯、CP1/CP2 检查点结构、中文输出和安全边界 |
| `process/changes/CR-019-STAGE6-MULTIFACTOR-SIMULATION-ARCHITECTURE-2026-05-30.md` | 确认 D1-D7、文档处理决策、旧基线映射、QMT C/S bridge 草案和禁止真实操作范围 |
| `process/USE-CASES.md` | 保留 UC-01 至 UC-14 旧基线，增量新增 UC-15 至 UC-18 |
| `process/REQUIREMENTS.md` | 保留 REQ-001 至 REQ-137 旧基线，增量新增 REQ-138 至 REQ-160 |
| `process/CLARIFICATION-LOG.md` | 追加调研发现、D1-D7、Q-039 至 Q-044 与 CP2 brief 输入 |
| `process/STATE.md` | 确认当前 active_change 为 CR-019，范围限定为需求/场景/检查/交接，不授权实现或真实 QMT / provider / 数据写入 |
| `docs/QMT-SIMULATION-LIVE-RUNBOOK.md` | 继承 stage gate、per-run authorization、runbook、对账、kill switch 和 no-real-op 边界 |
| `docs/QMT-INCIDENT-PLAYBOOK.md` | 继承 incident、blocked execution claims、recovery 与安全处理边界 |
| `docs/ROADMAP.md` | 确认 Backtrader optional backend、Qlib isolated runner、minute / Level2 后置定位 |
| 阶段六学习目标与三份 stage6-simulation 计划 | 确认阶段六目标、admission package、数据缺口和 local_backtest 改进路线 |
| 迅投 QMT 系统说明文档 | 仅作为 QMT 平台能力背景，不作为当前真实账户或权限证明 |

## Scenario Gray Areas

| 灰区 ID | 问题 | 候选理解 | 采用方案 | 影响面 | 状态 |
|---|---|---|---|---|---|
| SGA-019-01 | 阶段六目标是包装既有失败策略，还是重新建立多因子模拟盘准入链路？ | A. 包装旧策略进入模拟盘；B. 重建 production-ready 多因子 admission。 | 采用 B。旧多因子 / 低波 production rerun fail 必须保留为 blocked evidence，阶段六以实验 49-66 和 admission package 重建准入。 | 范围、成功指标、验证、QMT 后置 | resolved |
| SGA-019-02 | local_backtest / WSL 与 Windows QMT 节点第一版桥接采用 signed file drop，还是 FastAPI C/S 模块？ | A. signed file drop 主路径；B. QMT C/S 模块：local_backtest C 侧 client + Windows FastAPI S 侧 gateway；C. 直接 WSL 调 xtquant。 | 采用 B；A 降级为 fallback；C 排除。Windows 节点拥有 QMT adapter 边界，local_backtest / WSL 不直接依赖 xtquant。 | 架构、部署、安全、后续 Story | resolved |
| SGA-019-03 | FastAPI gateway 的接口面是否只做 dry-run，还是覆盖完整 QMT 功能？ | A. 只做 dry-run / readonly 子集；B. 覆盖完整 QMT 功能接口类别，真实转发由运行门控控制。 | 采用 B。用户已纠正：不做应用层鉴权不等于不做 simulation / account / cancel / live 等 QMT 功能；gateway 必须从回测框架摘离，作为 Windows 可运行 / 可安装命令。 | API、部署、安全、授权、运行治理、测试 | resolved |
| SGA-019-04 | Backtrader / Qlib / minute / Level2 是否纳入阶段六 P0？ | A. 全部纳入 P0；B. Backtrader/Qlib 后置、minute/Level2 Spike；C. 全部排除。 | 采用 B。Backtrader 为后置 optional backend，Qlib 为后置 isolated runner，minute/Level2 仅在触发条件满足后另起 CR / Spike。 | 范围、依赖、里程碑、Deferred Ideas | resolved |

## D1-D7 决策追溯

| 决策 ID | 已确认方案 | 备选方案 | 取舍说明 | 落点 |
|---|---|---|---|---|
| D1 | Backtrader 后置 optional execution backend | 阶段六 P0 引入 Backtrader | 后置可避免框架迁移挤占多因子 admission 主线；触发后仍能提供执行对照。 | UC-18；REQ-139；REQ-155 |
| D2 | Qlib 后置 isolated runner | 默认引入 Qlib 并接管因子 workflow | 隔离 runner 可控制依赖和 provider 边界，避免破坏本地数据湖事实源。 | UC-18；REQ-140；REQ-156 |
| D3 | 分钟数据后置 Spike | 分钟数据作为 P0 | 日频多因子 admission 可先推进；只有执行现实性实验证明日频不足时再 Spike。 | UC-18；REQ-141；REQ-157 |
| D4 | QMT xtdata 不进 WSL 主路径，最终 simulation 采用 Windows QMT bridge | WSL 直接依赖 xtquant | Windows 节点持有 QMT adapter 更符合平台和安全边界。 | UC-16；REQ-142；REQ-149 |
| D5 | 暂不申请 QMT Level2 | 首轮申请 Level2 | 当前没有微观结构主风险证据；Level2 权限、成本和数据审计后置。 | UC-18；REQ-143；REQ-158 |
| D6 | shadow + 连续 5 个真实交易日 dry-run 后再申请 QMT simulation | 直接申请 simulation | 5 日 dry-run 是最低运行稳定性和安全计数证据；通过后仍需 per-run authorization。 | UC-15；UC-17；REQ-144；REQ-154 |
| D7 | 第一版桥接采用 FastAPI 本地服务，signed file drop fallback | signed file drop 主路径 | FastAPI 可提升可观测性和交互性；fallback 保留失败路径但不得自动真实 QMT。 | UC-16；UC-17；REQ-145 至 REQ-150 |

## 用户纠偏记录

| 时间 | 纠偏点 | 已更新的理解 | 落点 |
|---|---|---|---|
| 2026-05-30 | “不做鉴权并不是 QMT 的功能不做；QMT 仍然需要能够实现模拟盘、实盘等功能。” | FastAPI gateway 必须支持完整 QMT 功能接口类别；鉴权策略与功能覆盖分离。 | UC-16、UC-17、REQ-146、REQ-147、CP2 Decision Brief |
| 2026-05-30 | “回测框架需要支持完整的 QMT 功能，只是通过 API 网关转发。” | WSL 回测框架只通过 HTTP API 访问 Windows gateway；gateway 转发完整 QMT 能力，真实转发受 run mode / stage gate / risk gate 控制。 | UC-16、REQ-149、CR-019 FastAPI Bridge 契约 |
| 2026-05-30 | “服务网关需要从框架摘离出来，做成 Windows 系统可运行和安装的命令。” | CP3/HLD 必须定义 Windows gateway 命令、安装方式、启动 / 停止方式、配置路径和防火墙边界。 | REQ-149、CP2-CR019-DQ-01 |
| 2026-05-30 | “若实在需要鉴权，可实现最简 MAC/token 方式。” | 第一版默认可无应用层鉴权；若 CP3 判定需要，则采用最简 token / HMAC，不采用重型安全方案。 | REQ-148、Q-039、CP2-CR019-DQ-02 |
| 2026-05-30 | “Q40 同意你的推荐方案。” | 阶段六 admission benchmark 采用多基准看板 + primary benchmark 规则，HS300、ZZ500、ZZ1000、中证全指同时输出，primary benchmark 按策略 universe / 风格选择。 | Q-040、REQ-138、REQ-154、A-051、CP2-CR019-DQ-03 |
| 2026-05-30 | “QMT 模块是一个独立模块，包含 C/S 两部分。” | C 侧位于 local_backtest，面向框架暴露统一 Python 接口；S 侧部署在 Windows，接收 C 侧 REST 请求并转换为 QMT / XtQuant 接口调用。 | UC-16、REQ-159、REQ-160、CP2-CR019-DQ-07 |

## Deferred Ideas

| ID | 想法 / 风险 / 扩展场景 | 来源 | 延后原因 | 重启条件 |
|---|---|---|---|---|
| DEF-019-01 | Backtrader W6 optional execution backend | D1 / ROADMAP | 不是阶段六 P0；需先稳定 clean feed、候选策略和轻量主路径 | clean feed、成本/可交易性 gate 和候选策略稳定后另起 Story |
| DEF-019-02 | Qlib W7 isolated runner | D2 / ROADMAP | 不能作为默认依赖或事实源；需要隔离输入输出契约 | factor panel、report catalog、PIT/available_at 和 export/import schema 稳定 |
| DEF-019-03 | 分钟数据 Spike | D3 / data gap plan | 当前不是 P0；会扩大数据工程和执行价范围 | 实验 58-59 证明日频执行假设不足且成为 admission 主风险 |
| DEF-019-04 | QMT Level2 Spike | D5 / QMT 文档背景 | 无当前授权，不应首轮申请；涉及权限、成本、微观结构审计 | L1/minute 不足且订单簿深度 / 排队 / 冲击成本成为主要风险，并获得独立授权 |
| DEF-019-05 | direct simulation submit endpoint | SGA-019-03 | FastAPI 服务存在不等于 simulation 授权；simulation endpoint later-gated | CR016 stage gate、per-run authorization、reconciliation 和 kill switch 设计通过 |
| DEF-019-06 | 直接迁移到外部框架主路径 | SGA-019-04 | 会挤占多因子 admission 和数据治理主线 | 后续 CR 明确框架迁移目标、收益和安全验证范围 |

## No Blocking Questions

本轮没有需要用户立即新增回答的阻断问题，原因如下：

- CR-019 已明确 D1-D7，足以增量更新 `USE-CASES.md` 和 `REQUIREMENTS.md`。
- Q-039 至 Q-044 是 CP3/HLD 的设计冻结项或已纳入 CP2 推荐决策项，不影响 CP2 需求基线成立。
- Q-044 已形成推荐方案并进入 CP2 Decision Brief；若用户 `approve`，即接受 Python client / 函数调用为主 + 薄 CLI。
- 本轮只做 requirement-clarification / CP2 准备，不进入 FastAPI 实现、依赖修改、真实 QMT 调用或真实数据写入，因此无需在 CP2 追加实现级授权问题。

## 安全声明

- 未实现代码。
- 未新增依赖。
- 未启动 FastAPI 或任何本地服务。
- 未调用真实 QMT / MiniQMT / XtQuant。
- 未读取凭据、`.env`、token、账户、session、cookie 或交易密码。
- 未执行真实 provider fetch。
- 未写真实 `data/`、`reports/`、`delivery/`。
- 迅投 QMT 系统说明文档只作为能力背景，不作为当前真实权限证明。
