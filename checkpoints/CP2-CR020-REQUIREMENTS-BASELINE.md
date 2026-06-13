---
checkpoint_id: "CP2"
checkpoint_name: "CR-020 Requirements Baseline"
type: "auto_then_manual"
status: "approved"
owner: "meta-po"
created_at: "2026-06-04T22:28:31+08:00"
reviewed_by: "user"
reviewed_at: "2026-06-04T22:53:33+08:00"
revised_at: "2026-06-04T23:10:18+08:00"
revision_text: "好的同意你的方案"
revision_interpretation: "用户接受 S 端 Windows 使用 `uv run` 启动 Python CLI，CLI 库采用 Typer；PowerShell/CMD 只作为 `uv run` 宿主。"
revised2_at: "2026-06-04T23:23:58+08:00"
revision2_text: "@meta-po 调度meta-se开始hld设计，设计时保持一致性，c端的cli也需要使用typer框架"
revision2_interpretation: "用户要求 S / C 两端 CLI 框架保持一致：C 端 Linux CLI 也使用 Typer；C 端 CLI 仍只用于配对、诊断和验收，业务 runtime 仍由 Python REST client 调用 REST API。"
auto_check_result: "process/checks/CP2-CR020-REQUIREMENTS-BASELINE.md"
auto_final_authorization: false
target:
  phase: "requirement-clarification"
  story_id: ""
  artifacts:
    - "process/changes/CR-020-QMT-WINDOWS-GATEWAY-SERVER-LOGIN-READONLY-QUERY-ADMISSION-2026-06-04.md"
    - "process/discussions/CP2-CR020-SCENARIO-DISCUSSION-LOG.md"
    - "process/checks/CP2-CR020-DISCUSSION-CHECKPOINT.json"
---

# CP2 CR-020 Requirements Baseline 人工审查

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---|---|
| `process/checks/CP2-CR020-REQUIREMENTS-BASELINE.md` | PASS | 0 | CR-020 已从候选转 active formal CR；Scenario Gray Areas 已由用户直接确认；无 blocking open item。 |

## Decision Brief

本轮 CP2 的目标是确认 CR-020 的需求基线：是否接受“Windows Gateway 服务端登录 + 首个只读查询接口”的范围、运行授权边界、凭据 `.env` 策略、S/C 分平台调用要求和不授权项。

如果你回复 `approve`，表示你接受以下 7 项推荐方案；不表示授权下方“不授权项”中的任何操作。

### CP2 决策修订记录

| 时间 | 用户原文 | 修订对象 | 修订结果 |
|---|---|---|---|
| 2026-06-04T23:10:18+08:00 | `好的同意你的方案` | DQ-CP2-CR020-04 S 端 Windows 命令面 | S 端正式命令面改为 `uv run` 启动的 Python CLI，CLI 库采用 Typer；PowerShell / CMD 只作为执行 `uv run` 的宿主 shell。C 端边界不变：Linux CLI 用于配对 / 诊断 / 验收，实际业务调用由 Python REST client 直接调用 gateway REST API。 |
| 2026-06-04T23:23:58+08:00 | `@meta-po 调度meta-se开始hld设计，设计时保持一致性，c端的cli也需要使用typer框架` | DQ-CP2-CR020-04 C 端 Linux CLI 框架 | C 端 Linux CLI 也使用 Typer，与 S 端 CLI 框架保持一致；C 端 CLI 仍只用于配对 / 诊断 / smoke test / CP7 验收，不替代业务 runtime。实际业务调用仍由 Python REST client 直接调用 gateway REST API。 |

### 待人工决策清单

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣分析 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|---|
| DQ-CP2-CR020-01 | `scope` | 是否确认 CR-020 从“gateway 实机部署 / health”升级为“Windows Gateway 服务端登录 + 至少一个只读查询接口”。背景是用户要求打通 `local_backtest` 与 QMT，并确认服务端需要登录 QMT。 | 接受升级范围：CR-020 覆盖 gateway 启动、端口、QMT 服务端登录 / 会话、HMAC / allowlist、C 侧 REST transport 和 `query_positions` 只读查询。 | A. 缩回只做 gateway health；B. 拆成两个 CR：先登录，再查询。 | 推荐方案能一次打通最小闭环；代价是 CR-020 风险升高、必须 standard。A 风险低但无法完成用户目标；B 风险更可控但交付变慢。 | 影响需求、HLD、Story、测试、文档和运行授权；风险等级 high。 | 若登录或查询验证不可控，回退到 `requirement-clarification`，拆分为 health-only CR 和 query CR。 |
| DQ-CP2-CR020-02 | `runtime_authorization` | 是否授权 CR-020 后续阶段在明确门禁下启动 Windows gateway、绑定端口、执行 QMT 服务端登录 / 会话检查，并调用 health / capabilities / `query_positions`。 | 授权仅限 CR-020 门禁内的只读 runtime：S 端通过 `uv run` Typer CLI 启停 gateway；服务端登录 QMT；C 端通过 Linux `uv run` Typer CLI 完成配对 / 诊断 / 验收，实际业务调用由 Python REST client 调用 health / capabilities / `query_positions`。 | A. 只授权离线设计，不允许运行；B. 只授权 gateway health，不授权 QMT 登录。 | 推荐方案满足打通目标；代价是需要严密凭据、日志脱敏和 Python REST client 合同。A 最安全但无法验证连接；B 可验证服务但不能证明 QMT 连接。 | 影响 Windows host、端口、防火墙、HMAC、日志、QMT session、Python REST transport；误用可能触发真实账户查询。 | 任一安全检查失败则 fail-closed，回退 CP3 / CP5 收窄 runtime。 |
| DQ-CP2-CR020-03 | `security` | 账号和密码以 `.env` 形式存放到项目中时，如何避免凭据泄露。 | 使用本地未跟踪 `.env` 保存真实 `QMT_LOGIN_ACCOUNT` / `QMT_LOGIN_PASSWORD` 等值；仓库只提交 `.env.example` 占位变量；日志、检查点、对话、memory 只记录脱敏 `credential_ref`。 | A. 使用操作系统 secret store，`.env` 只保存 secret 引用；B. 每次运行交互式输入，不落盘。 | 推荐方案与用户要求一致，落地简单；代价是依赖 `.gitignore` 和日志脱敏。A 更安全但实现复杂；B 不利于服务自启动。 | 影响安全、审计、运行手册和测试。真实值一旦进入 Git / 日志即为 blocker。 | 若发现泄露，立即停止推进，轮转凭据，清理日志，回退到 security redesign。 |
| DQ-CP2-CR020-04 | `implementation` | S 端命令、C 端配对命令和实际业务调用如何表达和验证。 | S 端 Windows 使用 `uv run` 启动 Python CLI，CLI 库采用 Typer；PowerShell / CMD 只作为 `uv run` 宿主，不作为正式 CLI 合同。C 端 Linux 也使用 `uv run` Typer CLI 完成配对、诊断、smoke test 和 CP7 验收；实际业务调用由 Python REST client 直接调用 gateway REST API。文档必须分清“S 端 Typer CLI 启停 / 诊断命令”“C 端 Typer CLI 配对 / 验收命令”和“Python REST 调用合同”。 | A. S / C 两端 CLI 都改用 Click；B. S / C 两端 CLI 都改用 argparse；C. S 端 Typer、C 端保留非 Typer CLI。 | 推荐方案贴合项目 `uv` 约束，S / C 命令体验和测试合同一致；代价是需要把 Typer 放入隔离的 `qmt-gateway` / CLI 依赖组。A 更成熟但样板更多；B 零新增 CLI 依赖但 UX 和类型约束较弱；C 依赖少但双端体验不一致。 | 影响 `docs/QMT-GATEWAY-INSTALL.md`、`trading/qmt_gateway_cli.py`、`trading/qmt_client_cli.py`、`trading/qmt_client.py`、Python REST transport、CP7 验收和回滚手册；CP3 / CP5 需设计 gateway 与 client CLI 依赖隔离。 | 若 Typer 与 Windows / XtQuant runtime 或 Linux client CLI 不兼容，回退到 CP3 / CP5 切换 Click；若依赖隔离不可接受，切换 argparse；若 Python REST client 合同不可实现，回退到 CP3 / CP5 重新选择 C 端 runtime 调用方式。 |
| DQ-CP2-CR020-05 | `implementation` | 首个只读查询接口选哪个。 | 选择 `query_positions` 作为首个接口，路径沿用 endpoint matrix 中的 positions 语义，要求结果脱敏、scope=`qmt:positions:read`、无交易副作用。 | A. 选择 `query_account`；B. 只做 health / capabilities，不做账户类查询。 | `query_positions` 能证明真实 QMT 连接和只读数据转发；代价是接触持仓敏感数据，需要脱敏。A 更偏资产快照，敏感度也高；B 风险低但不满足“至少一个查询接口”。 | 影响 endpoint matrix、client method、gateway route、redaction、CP7 fixture / 实机验证。 | 若持仓查询 API 不稳定，切换到 `query_account` 前必须重发 CP2 / CP3 决策。 |
| DQ-CP2-CR020-06 | `risk_acceptance` | 是否接受 CR-020 将触达真实 QMT 只读 API，但不授权交易和写操作。 | 接受只读风险：允许 `query_positions` 真实只读调用；明确不授权发单、撤单、改单、账户写入、simulation、live、broker lake、provider / lake / publish。 | A. 完全不接受真实 QMT 调用；B. 转到 CR-021 同时做 simulation。 | 推荐方案是最小真实连接闭环；代价是需要严格声明“只读不等于交易准入”。A 无法证明连接；B 跨越前置门禁，风险过高。 | 影响安全审计、运行授权和后续 CR-021..CR-024 的准入顺序。 | 若用户需要 simulation order，必须先关闭 CR-020，再启动 CR-021。 |
| DQ-CP2-CR020-07 | `architecture` | gateway runtime 与 CLI 依赖如何进入项目，避免 Linux C 端被 Windows-only / gateway-only 依赖污染。 | 推荐 CP3 设计为可选 `qmt-gateway` / Windows node runtime + C 端 CLI 隔离依赖：核心 Linux C 端业务 runtime 保持轻依赖；Typer 可作为 S / C CLI 的共享 CLI 框架，但 gateway server 和 QMT / XtQuant 相关依赖只在 S 端安装或按 extras / group 隔离；CP3 前不修改 `pyproject.toml` / `uv.lock`。 | A. 直接把 Typer / FastAPI / uvicorn / XtQuant 相关依赖加入主依赖；B. 完全不入依赖，只写外部安装说明。 | 推荐方案隔离最清晰，同时满足双端 CLI 一致性；代价是安装文档和验证命令更复杂。A 简单但污染主环境；B 最保守但自动化不足。 | 影响依赖治理、Windows 安装、Linux C 端兼容和 CI。 | 若 CP3 发现 XtQuant 只能以外部环境安装，切换为 S 端外部 runtime 方案；若 Typer 不能兼容 Windows gateway runtime 或 Linux client CLI，则切换 Click 或 argparse。 |

### CP2 追加字段

| 字段 | 内容 |
|---|---|
| 用户真实意图 | 打通 `local_backtest` 与 QMT 的连接，至少完成一个查询接口；服务端需要登录 QMT。 |
| 场景覆盖 | Windows S 端 `uv run` Typer CLI gateway 启停、QMT 登录 / 会话、Linux C 端 `uv run` Typer CLI 配对 / 诊断 / CP7 验收、Python REST client 调用 health / capabilities / `query_positions`、脱敏、fail-closed。 |
| 认知盲区补充 | Windows host、port、MiniQMT / XtQuant 版本、日志目录、允许来源和回滚方式尚未给出真实值；作为 CP3 / LLD 输入，不要求在 CP2 打印真实凭据。 |
| Scenario Gray Areas 处理结果 | `process/discussions/CP2-CR020-SCENARIO-DISCUSSION-LOG.md` 已记录；无 blocking open item。 |
| Deferred Ideas | `query_account`、`query_orders`、`query_trades` 后置；simulation / live 路线由 CR-021..CR-024 单独授权。 |
| 用户选择影响 | approve 后进入 CP3 HLD；修改则按修改项重写 CR / CP2；reject 则回退为 candidate 或 cancelled。 |
| 回退方式 | 回退到 `requirement-clarification`，必要时拆分 health-only / login / query CR。 |
| discussion log / checkpoint | `process/discussions/CP2-CR020-SCENARIO-DISCUSSION-LOG.md`；`process/checks/CP2-CR020-DISCUSSION-CHECKPOINT.json`。 |

### 不授权项

| 不授权项 | 说明 |
|---|---|
| 发单、撤单、改单、账户写入 | CP2 approve 不授权任何交易或写账户动作。 |
| simulation / live / live-readonly / small-live / scale-up | 仍需 CR-021..CR-024 单独启动和授权。 |
| provider fetch / lake write / broker lake write / publish | CR-020 只做 gateway / QMT readonly，不写数据湖或发布目录。 |
| 打印或保存真实凭据 | 账号、密码、token、session、交易密码、私钥不得进入 Git、对话、日志、检查点、memory。 |
| 扩大查询接口白名单 | 本轮只确认 `query_positions`；其他接口后置或重发决策。 |
| 自动终验授权 | `auto_final_authorization: false`；CP8 仍需人工确认。 |

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| CR-020 正式 CR 已创建 | PASS | `process/changes/CR-020-QMT-WINDOWS-GATEWAY-SERVER-LOGIN-READONLY-QUERY-ADMISSION-2026-06-04.md` | 已转 active-cp2-intake。 |
| CP2 自动预检已通过 | PASS | `process/checks/CP2-CR020-REQUIREMENTS-BASELINE.md` | 结论 PASS。 |
| 待人工决策清单完整 | PASS | 本文件 7 项 DQ | 覆盖 scope / runtime / security / implementation / risk / architecture。 |
| 不授权项已列出 | PASS | 本文件“不授权项” | 避免把 CP2 approve 误读为交易或凭据授权。 |

## Checklist

| # | 检查项 | 状态 | 证据 | 人工审查要点 |
|---|---|---|---|---|
| 1 | 是否接受 CR-020 范围升级 | approved | DQ-CP2-CR020-01 | 接受推荐范围。 |
| 2 | 是否接受只读 runtime 授权边界 | approved | DQ-CP2-CR020-02 | 不含交易、写账户、simulation / live。 |
| 3 | 是否接受 `.env` 凭据策略 | approved | DQ-CP2-CR020-03 | 真实值只在本地未跟踪 `.env`。 |
| 4 | 是否接受 S/C 调用分层 | approved | DQ-CP2-CR020-04 | S 端 Windows 使用 `uv run` Typer CLI；C 端配对 / 诊断 / 验收使用 Linux `uv run` Typer CLI；实际业务调用使用 Python REST client。 |
| 5 | 是否接受 `query_positions` 为首个接口 | approved | DQ-CP2-CR020-05 | 只读、脱敏、scope 控制。 |
| 6 | 是否接受只读 QMT 风险 | approved | DQ-CP2-CR020-06 | 明确不授权任何交易或写操作。 |
| 7 | 是否接受 gateway 依赖隔离策略 | approved | DQ-CP2-CR020-07 | CP3 前不改主依赖。 |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 人工结论为 `approved` | PASS | 本文件“人工审查结果” | 已通过，可进入 CP3。 |
| 修改意见已回填 | PASS | 用户回复 + 本文件 DQ-CP2-CR020-04 | 已采纳 C 端 Linux CLI 配对 / 验收 + Python REST runtime 修订；后续采纳 S 端 Windows `uv run` Typer CLI 修订；本次又采纳 C 端 Linux CLI 也使用 Typer 的一致性修订。 |
| 不授权项未被覆盖 | PASS | 本文件 + launch message | 任何交易 / 写操作 / 凭据泄露授权必须另起决策。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| CP2 自动预检 | `process/checks/CP2-CR020-REQUIREMENTS-BASELINE.md` | PASS | 已完成。 |
| CP2 人工审查稿 | `checkpoints/CP2-CR020-REQUIREMENTS-BASELINE.md` | approved | 用户已确认。 |
| CP2 门禁消息草稿 | `process/checks/CP2-CR020-HUMAN-GATE-LAUNCH-MESSAGE.md` | PASS | 已按 Typer S 端 CLI 口径修订。 |
| CR-020 正式 CR | `process/changes/CR-020-QMT-WINDOWS-GATEWAY-SERVER-LOGIN-READONLY-QUERY-ADMISSION-2026-06-04.md` | active-cp3-hld | CP2 approved，当前进入 CP3 HLD。 |

## 人工审查结果

| 字段 | 结果 |
|---|---|
| 审查结论 | approved |
| 审查人 | user |
| 审查时间 | 2026-06-04T22:53:33+08:00 |
| 用户原文 | `@meta-po 所有决策都同意你的备选方案。继续推进项目` |
| meta-po 解释 | 按“7 项 CP2 推荐决策全部同意并继续推进”处理；此前已采纳用户对 DQ-CP2-CR020-04 的 C 端边界修订、S 端 Windows `uv run` Typer CLI 修订；本次又采纳 C 端 Linux CLI 也使用 Typer 的一致性修订。若用户后续指定某项 A/B/C 备选，则按变更重新发起对应决策。 |
| 已接受决策项 | DQ-CP2-CR020-01；DQ-CP2-CR020-02；DQ-CP2-CR020-03；DQ-CP2-CR020-04；DQ-CP2-CR020-05；DQ-CP2-CR020-06；DQ-CP2-CR020-07 |
| 修改要求 | 已采纳 DQ-CP2-CR020-04 的三次修订：S 端 Windows 使用 `uv run` Typer CLI；C 端配对 / 诊断 / 验收使用 Linux `uv run` Typer CLI；实际业务调用由 Python REST client 直接调用 gateway REST API。 |
| 不授权确认 | approved：本次 CP2 不授权发单、撤单、改单、账户写入、simulation/live、provider/lake/publish、扩大查询白名单、自动终验或凭据泄露。 |

推荐回复：

approve

修改: <具体修改点>

reject
