---
discussion_id: "CP2-CR020-SCENARIO-DISCUSSION"
change_id: "CR-020"
status: "cp2-approved-revised-for-typer-server-cli"
created_at: "2026-06-04T22:28:31+08:00"
revised_at: "2026-06-04T23:23:58+08:00"
owner: "meta-po"
source: "user-direct-clarification"
---

# CP2 CR-020 Scenario Discussion Log

## 讨论结论

本轮 CR-020 来源于 CR-019 CP8 follow-up 台账中的 `CR-020` 候选项。原候选标题为“QMT Windows gateway 实机部署准入”，用户在本轮明确要求把目标推进为 `local_backtest` 与 QMT 的真实连接，至少完成一个查询接口，并确认服务端需要实现 QMT 账号登录。

用户已确认的场景边界如下：

| 场景项 | 结论 | 影响 |
|---|---|---|
| 范围升级 | CR-020 从仅 gateway health / 实机部署准入升级为 Windows Gateway 服务端登录与只读查询接口准入 | 需要按 standard 模式重新走 CP2 / CP3 / CP5 / CP6 / CP7 / CP8 |
| 服务端登录 | 服务端需要实现 QMT 账号登录和会话管理 | 需要 runtime authorization、凭据边界、日志脱敏和 fail-closed 设计 |
| 首个查询接口 | 至少完成一个查询接口；推荐以 `query_positions` 作为首个只读接口 | 需要只读 scope、HMAC / allowlist、脱敏和禁止交易副作用 |
| S / C 调用边界 | S 端 Windows 使用 `uv run` 启动 Typer Python CLI；PowerShell / CMD 仅作为 `uv run` 宿主。C 端配对、诊断和验收使用 Linux `uv run` Typer CLI；实际业务调用由 Python REST client 直接调用 gateway REST API | 安装手册和验收脚本必须分平台表达；LLD 必须同时定义 S 端 Typer CLI contract、C 端 Typer CLI pairing contract 和 Python REST transport contract |
| 凭据形态 | 登录账号和密码以 `.env` 形式存放到项目中 | 只允许本地未跟踪 `.env` 保存真实值；入库材料只写 `.env.example`、变量名和脱敏引用 |

## Scenario Gray Areas

| 问题 ID | 灰区 | 处理分类 | 当前处理 |
|---|---|---|---|
| Q-CR020-01 | CR-020 是否只做 gateway health，还是包含真实 QMT 登录与查询 | `resolved-by-user` | 用户同意升级为服务端登录 + 至少一个查询接口 |
| Q-CR020-02 | 是否需要服务端登录 QMT 账号 | `resolved-by-user` | 用户确认服务端需要实现登录 |
| Q-CR020-03 | S 端命令、C 端配对命令和实际业务调用如何区分 | `resolved-by-user` | 用户确认 S 端 Windows 使用 `uv run` Typer CLI；C 端配对 / 诊断 / 验收使用 Linux `uv run` Typer CLI；实际业务调用由 Python REST client 直接调用 REST API |
| Q-CR020-04 | 账号密码是否进入项目 | `decision-item` | 推荐本地未跟踪 `.env`；真实值不进入 Git、对话、日志、检查点或 memory |
| Q-CR020-05 | 首个查询接口选择 | `decision-item` | 推荐 `query_positions`，`query_account` / `orders` / `trades` 后置 |
| Q-CR020-06 | 是否授权交易、撤单、账户写入或 simulation / live | `decision-item` | 推荐本 CR 不授权任何交易或写操作 |

## Deferred Ideas

| 项目 | 状态 | 说明 |
|---|---|---|
| `query_account` | deferred | 可在 `query_positions` 通过后作为后续只读接口追加，不作为本轮最小完成口径。 |
| `query_orders` / `query_trades` | deferred | 仍属于只读，但更接近真实订单语义，建议在 CR-020 关闭后按后续 CR 或扩展 Story 处理。 |
| QMT simulation order / cancel | deferred-to-CR021 | 等 CR-020 关闭后，按 CR-021 单独授权。 |
| live-readonly / small-live / scale-up | deferred-to-CR022-CR024 | 需要逐级独立 CR 和运行授权。 |

## 恢复点

若后续对话上下文丢失，恢复 CR-020 时优先读取：

1. `process/changes/CR-020-QMT-WINDOWS-GATEWAY-SERVER-LOGIN-READONLY-QUERY-ADMISSION-2026-06-04.md`
2. `process/checks/CP2-CR020-REQUIREMENTS-BASELINE.md`
3. `checkpoints/CP2-CR020-REQUIREMENTS-BASELINE.md`
4. `process/checks/CP2-CR020-HUMAN-GATE-LAUNCH-MESSAGE.md`
5. `process/changes/CR-INDEX.yaml`
6. `process/STATE.md`
