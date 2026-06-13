---
discussion_id: "CP3-CR020-HLD-DISCUSSION"
change_id: "CR-020"
status: "ready-for-cp3-human-gate"
created_at: "2026-06-04T23:32:09+08:00"
owner: "meta-se"
source: "cp2-approved-baseline-and-static-contract-review"
phase: "solution-design"
---

# CP3 CR-020 HLD Discussion Log

## 讨论目标

本日志记录 CR-020 在正式生成 HLD 前的 Architecture Gray Areas 和 advisor table-first 方案形成输入。它不替代 `process/HLD.md` §36，也不授权实现、依赖变更、gateway 启动、QMT 连接、真实凭据读取、交易、账户写入、simulation/live、provider/lake/publish。

## 输入证据

| 输入 | 路径 | 结论 |
|---|---|---|
| CP2 人工确认 | `checkpoints/CP2-CR020-REQUIREMENTS-BASELINE.md` | CP2 approved；S 端 Windows CLI 与 C 端 Linux CLI 均使用 Typer；C 端业务 runtime 仍是 Python REST client。 |
| CR 文件 | `process/changes/CR-020-QMT-WINDOWS-GATEWAY-SERVER-LOGIN-READONLY-QUERY-ADMISSION-2026-06-04.md` | 范围为 Windows gateway 服务端登录 + `query_positions` 只读接口准入。 |
| CP2 讨论日志 | `process/discussions/CP2-CR020-SCENARIO-DISCUSSION-LOG.md` | 用户已确认服务端登录、`.env` 凭据形态、首个查询接口和不授权边界。 |
| endpoint matrix | `trading/qmt_endpoint_matrix.py` | `query_positions` 当前为 later-gated，路径 `POST /qmt/account/positions`，scope=`qmt:positions:read`。 |
| client 合同 | `trading/qmt_client.py` | 当前 `query_positions` 返回 later-gated blocked result，后续需接入 Python REST transport。 |
| auth 合同 | `trading/qmt_auth.py` | 已具备 pairing / HMAC / timestamp / nonce / scope 的离线合同。 |
| gateway lifecycle | `trading/qmt_gateway_config.py`、`trading/qmt_gateway_service.py` | 当前 start/bind 仍阻断；CR-020 需要在 CP5 后按授权解除 gateway lifecycle。 |
| 安装文档 | `docs/QMT-GATEWAY-INSTALL.md` | 当前文档仍是 CR019 离线安装边界，需要后续 Story 修订。 |

## Architecture Gray Areas

| 问题 ID | 灰区 | 为什么影响 HLD | canonical refs | 处理分类 |
|---|---|---|---|---|
| AGA-CR020-01 | S / C CLI 与业务 runtime 边界 | 会决定模块边界、验收命令、业务调用路径和文档口径；若把 C 端 CLI 误当 runtime，会违背 CP2。 | CP2 DQ-CP2-CR020-04；HLD §36.3；CR 文件 frontmatter `cli_consistency_policy` | decision-item |
| AGA-CR020-02 | 服务端登录、`.env` 凭据读取与 session ready | 会决定 gateway 启动流程、凭据脱敏、错误路径和是否能证明 QMT 连接。 | CP2 DQ-CP2-CR020-03；HLD §36.7；`qmt_gateway_config.py` redaction contract | decision-item |
| AGA-CR020-03 | HMAC / allowlist / scope / redaction 的 fail-closed 边界 | 会决定安全权限、来源控制、防重放、scope 检查和 CP7 验证面。 | CP2 DQ-CP2-CR020-06/07；`qmt_auth.py`；HLD §36.12 | decision-item |
| AGA-CR020-04 | `query_positions` 解锁、依赖隔离与回滚 | 会决定首个 endpoint、依赖治理、Story DAG、回滚和是否污染 Linux 主 runtime。 | `qmt_endpoint_matrix.py`；CP2 DQ-CP2-CR020-05/07；HLD §36.15 | decision-item |

## Advisor Table-First 输入

### AGA-CR020-01：S / C CLI 与业务 runtime 边界

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| A. S 端 Windows `uv run` Typer CLI，C 端 Linux `uv run` Typer CLI 仅 pairing / diagnostics / CP7，业务 runtime 为 Python REST client | 满足 CP2；CLI 一致；业务 runtime typed | 需要维护 S CLI、C CLI、REST client 三个合同 | CLI 文件、client、docs、CP7 | 推荐 | Typer 可隔离安装；若 Typer 不兼容则切 Click / argparse。 |
| B. S / C CLI 都作为业务 runtime wrapper | 命令面统一 | 业务调用经 shell，错误和安全边界弱；违背 CP2 | client runtime、策略调用 | 不推荐 | REST client 不可实现且用户重发决策时才切换。 |
| C. C 端取消 CLI，只保留 REST client | 依赖更少 | 缺 pairing / smoke / CP7 稳定命令面；违背用户 Typer 一致性要求 | CP7、docs | 不推荐 | C CLI 依赖隔离不可接受且用户修改 CP2 时切换。 |

### AGA-CR020-02：服务端登录、`.env` 与 session ready

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| A. gateway 启动时读取本地未跟踪 `.env`，登录 QMT 并形成 session ready，日志只输出 `credential_ref` | 符合 CP2；支持 health/session 证据 | 依赖 redaction 和本地运维纪律 | `.env.example`、login/session、logs | 推荐 | 真实 `.env` 不入库；泄露时切 OS secret store。 |
| B. 每次交互式输入账号密码 | 不落盘 | 不利于服务启动和复验；shell 历史也有风险 | S CLI、runbook | 备选 | `.env` 风险不可接受时切换。 |
| C. 只做 health，不登录 QMT | 风险最低 | 不满足 CR-020 最小闭环 | scope、验收 | 治理备选 | QMT 登录无法 fail-closed 时回退。 |

### AGA-CR020-03：HMAC / allowlist / scope / redaction

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| A. pairing_hmac 默认启用，allowlist 必填，scope 逐 endpoint 校验，redaction 作为响应和日志门 | 与现有 auth 合同一致；安全可测试 | 实现复杂度较高 | auth middleware、endpoint matrix、logs | 推荐 | scope 从 matrix 消费；nonce store 可先进程内 TTL 并在 CP5 暴露风险。 |
| B. 局域网 allowlist + no-auth | 简单 | 不符合 CR019/CP2；缺身份审计 | 安全、CP7 | 不推荐 | 仅 fixture/local_debug。 |
| C. 只做 HMAC，不做 allowlist | 身份强 | 网络暴露风险仍在 | 网络边界、安全 | 不推荐 | 完全 loopback 且用户接受风险时局部豁免。 |

### AGA-CR020-04：`query_positions`、依赖隔离与回滚

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| A. 只解锁 `query_positions`，gateway / XtQuant / server 依赖按 S 端隔离，C 端主 runtime 只消费 Python REST client | 最小闭环；不污染 Linux 主依赖 | 文档和 CP7 命令更复杂 | endpoint、client、gateway、dependencies | 推荐 | XtQuant 若只能外部安装则切外部 runtime；positions 不稳定则回退改 `query_account`。 |
| B. 同时解锁 account / orders / trades | 覆盖更完整 | 扩大敏感面，违背首个接口限制 | security、tests | 不推荐 | CR-020 关闭后另起 CR。 |
| C. 全部依赖加入主依赖 | 安装简单 | 污染 Linux 主环境；CP3 前禁止改依赖 | pyproject/uv.lock、CI | 不推荐 | 隔离不可行且用户接受依赖风险时切换。 |

## 推荐方案

推荐 CR20-A：分层 Windows gateway + 双端 Typer CLI + C 端 Python REST client。

适用条件：

- S 端 Windows gateway / XtQuant 依赖可与 Linux C 端主 runtime 隔离。
- `query_positions` 可被实现为只读、脱敏、scope=`qmt:positions:read`。
- HMAC / allowlist / scope / redaction 均可 fail-closed。
- C 端 CLI 只用于 pairing / diagnostics / smoke / CP7 validation，不替代 Python REST client runtime。

## 备选方案

| 备选 | 采用条件 | 代价 |
|---|---|---|
| CR20-B health/login only | QMT positions API 不稳定，或 CP3/CP5 无法证明只读脱敏 | 无法满足“至少一个查询接口”的当前目标，需要回退需求或拆 CR。 |
| CR20-C 外部 Windows runtime | XtQuant 只能在外部 Windows 环境安装，无法纳入仓库依赖隔离 | 可审计性和 CP7 标准化较弱，需要 runbook 补强。 |

## Deferred Options

| 项目 | 状态 | 原因 | 重访条件 |
|---|---|---|---|
| `query_account` | deferred | 敏感度相近但不是 CP2 选择的首个接口 | `query_positions` 不稳定且用户重发 CP3 决策。 |
| `query_orders` / `query_trades` | deferred | 更接近订单语义，容易被误读为交易准入 | CR-020 关闭后另起只读接口扩展 CR。 |
| simulation / live | deferred-to-CR021-CR024 | 当前 CR 不授权交易或 live 路线 | CR-020 closed 后单独 CP2 / CP3 / CP5。 |
| OS secret store | fallback | 当前用户要求 `.env`；OS store 实现复杂 | 发现 `.env` 泄露风险或用户提高安全要求。 |

## 关键取舍

| 维度 | 推荐方案取舍 |
|---|---|
| 复杂度 | 接受中高复杂度，以换取清晰的 S CLI / C CLI / REST client / gateway / auth 边界。 |
| 成本 | 需要 6 个候选 Story 和 4 个 Wave；CP5 全量 LLD 前不得实现。 |
| 扩展性 | 后续只读 endpoint 可按 endpoint matrix 逐项解锁，但本轮只允许 `query_positions`。 |
| 可验证性 | Typer CLI 用于 diagnostics / CP7，Python REST client 用于业务 runtime，失败路径可测试。 |
| 维护成本 | 多合同维护成本高，但避免 CLI runtime 和业务 runtime 混淆。 |
| 平台兼容 | S 端依赖隔离优先，避免 Windows-only / XtQuant 依赖污染 Linux C 端。 |
| 安全风险 | 采用 fail-closed；CP3 不授权运行和真实凭据读取。 |

## 场景模拟结果

| 模拟 | 结果 |
|---|---|
| S 端启动 + session ready | PASS：配置、`.env`、login、redaction 任一失败均 blocked。 |
| C 端 Python REST client 查询 positions | PASS：HMAC、allowlist、scope、session、redaction 全部通过才返回 redacted payload。 |
| C 端 CLI 被误用为业务 runtime | PASS：HLD / Decision Brief 明确禁止，CP3 DQ 要求用户确认。 |
| 未授权 endpoint 调用 | PASS：`query_positions` 以外保持 later-gated / blocked。 |

## 用户需决策点

| 决策 ID | 决策类型 | 推荐方案 | 备选方案 | 影响 |
|---|---|---|---|---|
| DQ-CP3-CR020-01 | architecture | 接受 CR20-A | health/login only；外部 Windows runtime | 总体架构和 Story 边界 |
| DQ-CP3-CR020-02 | implementation | S/C CLI 均 Typer，C CLI 不作 runtime | CLI runtime；无 C CLI | 调用合同和 CP7 |
| DQ-CP3-CR020-03 | security | `.env` 未跟踪 + redacted credential_ref | OS secret store；交互输入 | 凭据治理 |
| DQ-CP3-CR020-04 | security | HMAC / allowlist / scope / redaction fail-closed | no-auth；HMAC only | 安全边界 |
| DQ-CP3-CR020-05 | implementation | 只解锁 `query_positions` | `query_account`；health-only | endpoint 白名单 |
| DQ-CP3-CR020-06 | architecture | S 端依赖隔离，CP3 前不改锁 | 主依赖统一；外部 runtime | 依赖治理 |
| DQ-CP3-CR020-07 | runtime_authorization | CP3 不授权实现或运行 | bounded smoke；依赖准备 | 运行授权 |

## 回退点

若 CP3 不通过，应回退到以下设计问题：

1. AGA-CR020-01：重新定义 S/C CLI 与 Python REST client runtime 边界。
2. AGA-CR020-02：重新选择 `.env`、OS secret store 或交互输入。
3. AGA-CR020-04：回退为 health/login only，或将 `query_positions` 改为 `query_account` 后重发 CP3。
4. 依赖隔离失败时切换 CR20-C 外部 Windows runtime。
