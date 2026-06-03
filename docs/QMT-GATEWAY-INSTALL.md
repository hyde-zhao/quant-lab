# QMT Gateway 安装与运行边界

本文冻结 CR019-S04 的 Windows QMT gateway 生命周期与部署合同。当前范围只提供命令结构、配置字段、校验规则和离线验证入口；不得启动真实服务，不得绑定真实端口，不得访问 Windows QMT 节点，不得调用 QMT / MiniQMT / XtQuant。

## 适用范围

| 项目 | 边界 |
|---|---|
| 运行位置 | Windows QMT 节点 |
| C 侧入口 | local_backtest Python client / 薄 CLI |
| S 侧形态 | 未来 FastAPI gateway；本 Story 只冻结 lifecycle / deployment contract |
| 真实运行 | 本 Story 不授权 |
| 真实交易 | 本 Story 不授权 |
| 真实凭据 | 不得写入真实凭据，不得读取私有配置，不得把交易身份材料写进文档 |

## 命令结构

命令样例只表示结构，不可直接执行真实服务：

```bash
qmt-gateway serve --config <config-path> --host <windows-host> --port <port> --auth-mode pairing_hmac
```

字段说明：

| 字段 | 示例 | 说明 |
|---|---|---|
| `--config` | `<config-path>` | 配置文件路径占位符；当前测试只使用显式 fixture |
| `--host` | `<windows-host>` | Windows gateway bind host 占位符；公网和 `0.0.0.0` 默认阻断 |
| `--port` | `<port>` | 端口占位符；当前实现不绑定端口 |
| `--auth-mode` | `pairing_hmac` | S04 只保留鉴权模式槽位；配对细节由 S05 冻结 |

## 配置字段

| 配置组 | 必填字段 | Fail-closed 条件 |
|---|---|---|
| bind | `bind_host`、`port`、`public_exposure_allowed`、`wsl_access_host` | `0.0.0.0`、公网地址、端口越界或显式公网暴露 |
| firewall | `required`、`enabled`、`inbound_rule_present`、`rule_name`、`profile` | 防火墙未启用、规则缺失或不要求防火墙 |
| allowlist | `sources`、`required`、`description` | 来源为空、来源不可解析或来源为公网网段 |
| heartbeat | `interval_seconds`、`stale_after_seconds`、`unhealthy_after_missed` | 间隔小于等于 0，或 stale 小于 interval |
| redaction | `redacted_fields`、`required_fields`、`redaction_status` | 脱敏字段不完整 |

## 生命周期

| Transition | 当前 S04 行为 |
|---|---|
| `plan` | 只返回 `ready_to_start` 计划，不启动服务 |
| `start` / `serve` / `run` / `bind` | 返回 `service_start_forbidden` |
| `stop` / `shutdown` | 只记录 `stopped` 计划，不执行系统命令 |
| heartbeat unhealthy | 返回 `heartbeat_failed`，真实 QMT 调用计数保持 0 |

## 禁止事项

- 不得安装依赖或修改依赖锁定文件。
- 不得启动 FastAPI、uvicorn 或任何 Windows 服务。
- 不得绑定端口、打开网络连接或执行系统服务命令。
- 不得读取私有配置、交易身份材料、浏览器会话、私钥或本机认证材料。
- 不得调用 QMT / MiniQMT / XtQuant。
- 不得真实发单、撤单、查询交易账户或写 broker lake。
- 不得执行 provider fetch、lake write、publish、simulation 或 live run。

## 离线验证入口

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr019_qmt_gateway_lifecycle.py
```

预期结果：

| 检查 | 预期 |
|---|---|
| public exposure allowed count | 0 |
| service start count | 0 |
| port bind count | 0 |
| qmt api call count | 0 |
| dependency change count | 0 |
| credential read count | 0 |

## 后续边界

`O-CR019-S04-01` 保持 OPEN：真实 FastAPI runtime 依赖、安装脚本和服务启动授权不在 S04 范围。后续如需真实 Windows 节点 smoke、服务启动 dry-run 或端口验证，必须由 meta-po / user 单独授权，并重新进入对应 Story 或变更流程。
