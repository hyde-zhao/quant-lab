# QMT Terminal Target

本 target 描述未来在 QMT 终端环境中执行 `qmt_interface_smoke` 的边界。当前文件只作为离线策略包材料，不包含可执行终端脚本。

## 可验证内容

- package manifest 中存在 `qmt_terminal` target。
- `runtime_authorized=false`，说明当前包不能触发真实 QMT 终端动作。
- 只读 smoke 合同限定为 `query_positions`，scope 为 `qmt:positions:read`。
- 后续证据必须使用 `evidence/redacted-smoke-result-template.yaml`，不得粘贴账户、证券代码、持仓数量、市值或日志原文。

## 运行前置条件

真实 QMT terminal 验证必须等到独立 runtime authorization 通过。授权前不得执行：

- 启动 QMT 终端或连接已启动终端。
- 导入或调用 XtQuant。
- 读取 `.env`、账号、密码、token、session 或交易凭据。
- 查询账户原文、资金原文、持仓原文、委托原文或成交原文。
- 下单、撤单、simulation 或 live。

## 后续人工 smoke 的最小范围

授权后也只允许用户手工执行 `query_positions` 只读 smoke，并回填脱敏摘要：

- `endpoint_id=query_positions`
- `path=/qmt/account/positions`
- `required_scope=qmt:positions:read`
- `raw_payload_included=false`
- `trade_write_attempted=false`
