---
checkpoint_id: "CP3"
checkpoint_name: "CR-020 HLD Review"
type: "auto_then_manual"
status: "approved"
owner: "meta-po"
created_at: "2026-06-04T23:32:09+08:00"
reviewed_by: "user"
reviewed_at: "2026-06-05T06:49:15+08:00"
auto_check_result: "process/checks/CP3-CR020-HLD-CONSISTENCY.md"
target:
  phase: "solution-design"
  story_id: ""
  artifacts:
    - "process/HLD.md"
    - "process/discussions/CP3-CR020-HLD-DISCUSSION-LOG.md"
    - "process/checks/CP3-CR020-DISCUSSION-CHECKPOINT.json"
    - "process/checks/CP3-CR020-HLD-CONSISTENCY.md"
---

# CP3 CR-020 HLD Review 人工审查

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---|---|
| `process/checks/CP3-CR020-HLD-CONSISTENCY.md` | PASS | 0 | HLD §36、Architecture Gray Areas、advisor table、ADR 候选、Story 候选、NFR、风险和不授权边界均已覆盖。 |

## Decision Brief

本轮 CP3 的目标是确认 CR-020 的高层架构：是否接受“Windows gateway + 服务端登录 / session ready + HMAC / allowlist / scope / redaction + C 端 Python REST client runtime + `query_positions` 单接口只读准入”的推荐设计。

如果你回复 `approve`，表示你接受以下 7 项推荐方案；不表示授权下方“不授权项”中的任何操作。

### 候选架构适用条件

| 方案 | 适用条件 | 优化项 | 牺牲项 | 切换条件 |
|---|---|---|---|---|
| CR20-A 推荐：分层 Windows gateway + 双端 Typer CLI + C 端 Python REST client | Typer 可隔离安装；QMT positions 可只读调用；HMAC/allowlist/scope/redaction 可 fail-closed | 满足 CP2，CLI 一致，业务 runtime typed，安全边界可测 | 多合同维护成本较高 | Typer 不兼容、positions API 不稳定或依赖隔离失败时切换。 |
| CR20-B：health/login only | QMT 查询不可控但登录可验证 | 风险较低，保留登录证据 | 不满足至少一个查询接口 | `query_positions` 无法脱敏或无法证明只读时回退。 |
| CR20-C：外部 Windows runtime | XtQuant 依赖无法纳入仓库隔离环境 | Linux 主依赖最干净 | 可审计性和 CP7 标准化较弱 | XtQuant 只能外部安装或 gateway 依赖隔离失败时切换。 |

### Use Case -> Architecture Traceability 摘要

| Use Case / 场景 | 架构承载 | 验证方向 |
|---|---|---|
| Windows S 端 gateway 启停与 health | S 端 `uv run` Typer CLI、Gateway Process Boundary | CP7 S 端命令 evidence 和日志脱敏扫描。 |
| QMT 服务端登录 / session ready | Login / Session Manager、本地未跟踪 `.env`、redacted `credential_ref` | session ready status；真实凭据原文出现次数为 0。 |
| Linux C 端 pairing / diagnostics / validation | C 端 `uv run` Typer CLI、pairing_hmac | pairing / wrong scope / nonce replay blocked cases。 |
| C 端业务调用 | Python REST client direct gateway REST API | typed request / response / timeout / error code。 |
| `query_positions` 只读接口 | Endpoint Matrix、Dispatcher、Redaction | scope=`qmt:positions:read`；其他 endpoint later-gated。 |
| 不授权边界 | No-order safety、blocked endpoint list、forbidden counters | order/cancel/account_write/simulation/live/provider/lake/publish 均为 0。 |

### 关键场景模拟结果

| 模拟 ID | 场景 | 结果 |
|---|---|---|
| SIM-CR020-01 | S 端正常启动并 session ready | PASS |
| SIM-CR020-02 | C 端 Python REST client 查询 positions | PASS |
| SIM-CR020-03 | C 端 CLI 不作为业务 runtime | PASS |
| SIM-CR020-04 | 未授权 endpoint 被调用 | PASS |
| SIM-CR020-05 | 回滚后再次查询 | PASS |

### Architecture Gray Areas 处理结果

| 灰区 | 推荐处理 | 备选 | 状态 |
|---|---|---|---|
| S / C CLI 与业务 runtime 边界 | S/C CLI 均 Typer；C CLI 只验收；业务 runtime 是 Python REST client | CLI runtime；取消 C CLI | decision-item |
| 服务端登录、`.env` 与 session ready | 本地未跟踪 `.env` + redacted credential_ref + session ready gate | OS secret store；交互输入；health-only | decision-item |
| HMAC / allowlist / scope / redaction | pairing_hmac 默认、allowlist 必填、scope per endpoint、redaction fail-closed | no-auth local only；HMAC only | decision-item |
| `query_positions`、依赖隔离与回滚 | 只解锁 `query_positions`；S 端依赖隔离；C 端 REST client | 多 endpoint；主依赖统一；外部 runtime | decision-item |

discussion log / checkpoint：

- `process/discussions/CP3-CR020-HLD-DISCUSSION-LOG.md`
- `process/checks/CP3-CR020-DISCUSSION-CHECKPOINT.json`

### 待人工决策清单

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣分析 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|---|
| DQ-CP3-CR020-01 | `architecture` | 是否接受 CR20-A 分层 Windows gateway + 双端 Typer CLI + C 端 Python REST client 作为推荐架构？背景是 CR-020 需要同时证明 gateway runtime、服务端登录、只读查询和不越权安全边界。 | 接受 CR20-A：S 端 Windows `uv run` Typer CLI 管 gateway lifecycle / login / diagnostics；C 端 Linux `uv run` Typer CLI 仅 pairing / diagnostics / smoke / CP7；业务 runtime 为 Python REST client direct REST API。 | A. health/login only；B. 外部 Windows runtime。 | 推荐方案满足 CP2 和最小闭环；health/login 风险低但不满足查询；外部 runtime 依赖干净但可审计性弱。 | 影响 S01..S06、CP5、CP7、docs、安全边界和依赖隔离。 | `query_positions` 或依赖隔离失败时切换到 health/login only 或外部 runtime。 |
| DQ-CP3-CR020-02 | `implementation` | 是否确认 S/C CLI 一致使用 Typer，但 C 端 CLI 不作为业务 runtime？触发条件是用户要求 C 端 CLI 也用 Typer，同时要求业务调用由 Python REST client 直接调用 gateway API。 | 确认：S CLI 管 lifecycle；C CLI 管 pairing / diagnostics / validation；业务 runtime 为 Python REST client。 | A. CLI 作为 runtime；B. C 端无 CLI。 | 推荐方案与 CP2 一致；CLI runtime 类型和安全弱；无 C CLI 会削弱 CP7 验收。 | 影响 `qmt_gateway_cli.py`、`qmt_client_cli.py`、`qmt_client.py`、docs、QA。 | REST client 不可实现时回退 CP3；Typer 不兼容时切 Click / argparse。 |
| DQ-CP3-CR020-03 | `security` | 是否接受 `.env` 本地未跟踪 + redacted `credential_ref` 作为凭据策略？背景是用户要求账号密码以 `.env` 形式存放，但项目禁止读取或输出真实凭据。 | 接受：真实值只在本地未跟踪 `.env`；仓库只放 `.env.example` 占位；日志、检查点、文档、memory 只记录 redacted `credential_ref`。 | A. OS secret store；B. 每次交互输入。 | 推荐方案符合用户要求且落地简单；OS store 更安全但复杂；交互输入影响服务启动和复验。 | 凭据泄露为最高风险，影响安全、审计、运维和 CP7。 | 发现泄露立即停止、轮转凭据、清理日志，回退 security redesign。 |
| DQ-CP3-CR020-04 | `security` | 是否接受 pairing_hmac + allowlist + scope + redaction 全部 fail-closed？背景是 CR-020 触达真实只读 QMT API，必须有身份、来源、scope 和脱敏控制。 | 接受：pairing_hmac 默认启用，allowlist 必填，scope 逐 endpoint 校验，redaction fail-closed。 | A. no-auth local only；B. HMAC only。 | 推荐方案安全最完整；no-auth 风险高；HMAC only 网络边界不足。 | 影响 auth middleware、endpoint matrix、gateway config、CP7 wrong-scope / replay / source tests。 | 真实 readonly 不允许 no-auth；fixture/local_debug 可局部豁免但不得连接 QMT。 |
| DQ-CP3-CR020-05 | `implementation` | 是否确认只解锁 `query_positions`，scope=`qmt:positions:read`？背景是 CP2 已选择首个接口，其他 endpoint 仍应 later-gated。 | 确认：仅 `POST /qmt/account/positions` 进入本轮只读白名单，结果脱敏，其他 endpoint blocked。 | A. 改 `query_account`；B. health-only。 | positions 能证明真实只读连接；account 可替代但需重决策；health-only 不满足目标。 | 触达持仓敏感信息，需要强制 redaction 和 no-order safety。 | positions API 不稳定或无法脱敏时回退 CP3 改接口或收窄范围。 |
| DQ-CP3-CR020-06 | `architecture` | 是否接受 S 端 gateway / XtQuant 依赖隔离，CP3 前不改 `pyproject.toml` / `uv.lock`？背景是需避免 Windows-only / gateway-only 依赖污染 Linux C 端主 runtime。 | 接受：CP3 只定义隔离策略；CP5 LLD 再决定 extras / group / external runtime；CP3 前不改锁。 | A. 主依赖统一安装；B. 完全外部 runtime。 | 推荐方案兼顾隔离和可交付；主依赖污染 Linux；外部 runtime 可审计性弱。 | 影响 Windows / Linux 兼容、CI、安装文档和运行手册。 | 隔离不可行时切外部 runtime；Typer 不兼容时切 Click / argparse。 |
| DQ-CP3-CR020-07 | `runtime_authorization` | 是否确认 CP3 通过不授权实现、启动、QMT 连接、交易、写入、simulation/live、provider/lake/publish 或凭据输出？背景是 HLD approval 可能被误读为运行许可。 | 确认：CP3 仅允许进入 Story Planning / CP4，不授权任何运行或真实凭据读取。 | A. 授权 bounded smoke；B. 授权依赖准备。 | 推荐方案权限最小；bounded smoke 或依赖准备需要后续 CP5/CP6/CP7 或独立运行授权。 | 防止越权运行、凭据泄露、交易误触和数据写入。 | 用户明确运行授权时由 meta-po 单独发起，不通过本 CP3 隐含授权。 |

### ADR 候选摘要

| ADR ID | 决策 | 推荐结论 | 状态 |
|---|---|---|---|
| ADR-087 | CR-020 runtime 分层 | S CLI / C CLI / Python REST client 分层 | HLD candidate |
| ADR-088 | Windows gateway 进程边界 | gateway 是唯一 QMT 服务端触达点 | HLD candidate |
| ADR-089 | `.env` 凭据策略 | 本地未跟踪 `.env` + redacted `credential_ref` | HLD candidate |
| ADR-090 | 登录与 session ready gate | not ready 阻断查询 | HLD candidate |
| ADR-091 | HMAC / allowlist / scope / nonce | pairing_hmac 默认启用，allowlist 必填 | HLD candidate |
| ADR-092 | `query_positions` 首个只读接口 | 只解锁 positions，其他 later-gated | HLD candidate |
| ADR-093 | 依赖隔离 | S 端 gateway / XtQuant 依赖隔离 | HLD candidate |

### Story / Wave 候选摘要

> 以下仅作为 CP3 通过后的 Story Planning 输入。CP3 未 approved 前不得写入正式 `process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml` 或 Story 卡片。

| Story | 标题 | 建议 Wave | 依赖 |
|---|---|---|---|
| CR020-S01 | Windows gateway runtime 与部署准入 | W1 | CP3 approved |
| CR020-S02 | 服务端 QMT 登录 / 会话管理 | W1 | S01 contract |
| CR020-S03 | C 侧 Python REST transport 与 Typer CLI | W2 | S01 auth endpoint contract |
| CR020-S04 | HMAC / pairing / allowlist / scope 实机准入 | W2 | S01、S03 |
| CR020-S05 | `query_positions` 只读查询接口 | W3 | S02、S03、S04 |
| CR020-S06 | 文档、运行手册与 CP7 实机验收 | W4 | S01..S05 |

### 未决风险

| 风险 | 状态 | 处理 |
|---|---|---|
| Windows host、port、MiniQMT / XtQuant version、log dir、allowlist source 未填 | non-blocking-open | 作为 CP5 / CP6 / CP7 环境输入，不在 CP3 输出真实值。 |
| XtQuant 依赖隔离形态未定 | non-blocking-open | CP3 推荐隔离策略；CP5 LLD 决定 extras / group / external runtime。 |
| `query_positions` 实际 QMT API 细节未验证 | non-blocking-open | CP5 LLD 和 CP7 实机验证处理；失败则回退 CP3 / CP5。 |

### 不授权项

如果你回复 `approve`，不表示授权以下 10 项禁止操作：

| 不授权项 | 说明 |
|---|---|
| 发单、撤单、改单、账户写入或任何 broker 写操作 | CR-020 仅只读查询设计和后续门控。 |
| simulation、live-readonly、small-live、scale-up 或任何真实交易准入 | 仍由 CR-021..CR-024 单独授权。 |
| provider fetch、真实联网补数、真实 lake write、catalog publish / current pointer publish、broker lake write 或 reports overwrite | CR-020 不触发数据生产 / 发布路径。 |
| 把 `query_positions` 以外的真实 QMT 查询接口纳入本轮默认白名单 | 其他 endpoint 保持 later-gated。 |
| 把账号、密码、token、session、交易密码、私钥写入 Git、对话、日志、检查点、memory 或任何入库文件 | 只允许 `.env.example` 占位和 redacted `credential_ref`。 |
| 在 CP3 前修改 `pyproject.toml` / `uv.lock` | 依赖形态 CP5 后再定。 |
| 把 Windows gateway / XtQuant 依赖加入 Linux C 端主依赖 | 必须隔离或外部 runtime。 |
| 把 C 端 Typer CLI 配对 / 验收命令误当成业务 runtime | 业务 runtime 必须是 Python REST client。 |
| 启动 gateway、绑定端口、连接 QMT、读取真实 `.env` | CP3 只确认 HLD，不授权运行。 |
| 启动 CR-021..CR-024 或扩大到 simulation / live 路线 | 后续 CR 独立门控。 |

### 自动终验授权

| 字段 | 内容 |
|---|---|
| 自动终验授权 | false |
| 适用检查点 | CP3 |
| 说明 | CP3 只确认 HLD 设计，不具备自动终验、实现授权、运行授权或 CR 关闭授权。 |

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| CP2 approved | approved | `checkpoints/CP2-CR020-REQUIREMENTS-BASELINE.md` | 用户本轮同意，接受 CP3 七项推荐方案。 |
| HLD §36 已生成 | approved | `process/HLD.md` §36 | 用户本轮同意，接受 CP3 七项推荐方案。 |
| CP3 自动预检 PASS | approved | `process/checks/CP3-CR020-HLD-CONSISTENCY.md` | 用户本轮同意，接受 CP3 七项推荐方案。 |
| discussion log / checkpoint 存在 | approved | `process/discussions/CP3-CR020-HLD-DISCUSSION-LOG.md`、`process/checks/CP3-CR020-DISCUSSION-CHECKPOINT.json` | 用户本轮同意，接受 CP3 七项推荐方案。 |
| 待人工决策项完整 | approved | 本文件 7 项 DQ | 用户本轮同意，接受 CP3 七项推荐方案。 |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 是否接受 CR20-A 推荐架构 | approved | DQ-CP3-CR020-01 | 接受推荐方案。 |
| 2 | 是否接受 S/C Typer CLI 与 Python REST runtime 分层 | approved | DQ-CP3-CR020-02 | 接受推荐方案。 |
| 3 | 是否接受 `.env` redacted credential_ref 凭据策略 | approved | DQ-CP3-CR020-03 | 接受推荐方案。 |
| 4 | 是否接受 HMAC / allowlist / scope / redaction fail-closed | approved | DQ-CP3-CR020-04 | 接受推荐方案。 |
| 5 | 是否确认只解锁 `query_positions` | approved | DQ-CP3-CR020-05 | 接受推荐方案。 |
| 6 | 是否接受 S 端依赖隔离与 CP3 前不改锁 | approved | DQ-CP3-CR020-06 | 接受推荐方案。 |
| 7 | 是否确认 CP3 不授权实现、运行或真实凭据读取 | approved | DQ-CP3-CR020-07 | 接受推荐方案；本批准仅限设计层。 |
| 8 | HLD / ADR / Risk / NFR 是否内部一致 | approved | `process/HLD.md` §36 | 用户本轮同意，接受 CP3 七项推荐方案。 |
| 9 | Story 候选与工作量是否一致 | approved | HLD §36.15、§36.16 | 6 Story / 4 Wave；用户本轮同意。 |
| 10 | 不授权边界是否足够清晰 | approved | 本文件“不授权项” | CP3 approve 不授权实现、依赖变更、gateway 启动、QMT 连接、真实 `.env` 读取、交易、账户写入、simulation/live、provider/lake/publish 或凭据输出。 |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| 用户接受或修改全部 CP3 决策项 | approved | 人工审查结果 | 用户本轮同意，接受 DQ-CP3-CR020-01..07 推荐方案。 |
| CP3 通过后可进入 Story Planning / CP4 | approved | HLD §36、DQ | 仅允许进入 story-planning / CP4。 |
| 未授权运行 / 实现 / 凭据读取 | approved | 不授权项 | CP3 approve 不授权实现、依赖变更、gateway 启动、QMT 连接、真实 `.env` 读取、交易、账户写入、simulation/live、provider/lake/publish 或凭据输出。 |
| 若用户要求修改，相关 DQ / HLD / checkpoint 已刷新 | N/A | 修订记录 | 用户未要求修改；本轮按 approve 处理。 |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| HLD 增量 | `process/HLD.md` §36 | approved | 用户本轮同意，接受 CP3 七项推荐方案。 |
| CP3 discussion log | `process/discussions/CP3-CR020-HLD-DISCUSSION-LOG.md` | approved | 用户本轮同意，接受 CP3 七项推荐方案。 |
| CP3 discussion checkpoint | `process/checks/CP3-CR020-DISCUSSION-CHECKPOINT.json` | approved | 用户本轮同意，接受 CP3 七项推荐方案。 |
| CP3 自动预检 | `process/checks/CP3-CR020-HLD-CONSISTENCY.md` | approved | 自动预检 PASS；人工批准。 |
| CP3 人工审查稿 | `checkpoints/CP3-CR020-HLD-REVIEW.md` | approved | 已回填人工审查结果。 |
| 正式 ADR / Story / Development Plan | N/A | N/A | CP3 未 approved 前不得写入；待 CP3 approved 后进入 story-planning。 |

## 人工审查结果

- 结论：`approved`
- 审查人：user
- 审查时间：2026-06-05T06:49:15+08:00
- 修改意见：用户回复“同意，你需要拉起meta-po 组织子agent完成任务，可以并行的时候需要并行拉起子agent进行”；按 CP3 approve 处理，接受 DQ-CP3-CR020-01..07 推荐方案。
- 风险接受项：仅限设计层接受 CR20-A 推荐架构、双端 Typer CLI / Python REST runtime 分层、`.env` redacted credential_ref 策略、HMAC / allowlist / scope / redaction fail-closed、只解锁 `query_positions`、S 端依赖隔离和 CP3 不授权运行边界；不授权实现、依赖变更、gateway 启动、QMT 连接、真实 `.env` 读取、交易、账户写入、simulation/live、provider/lake/publish 或凭据输出。

推荐回复：

approve

修改: <具体修改点>

reject
