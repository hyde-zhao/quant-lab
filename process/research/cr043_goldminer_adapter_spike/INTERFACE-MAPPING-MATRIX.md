# CR043 Goldminer Adapter 接口映射矩阵

生成时间：2026-06-11T08:25:00+08:00  
状态：draft-for-CP3  
输入证据：

- L0 本地合同：`engine/broker_adapter.py`
- L1 / L2 工程事实报告：`process/research/cr043_goldminer_adapter_spike/ENGINEERING-FEASIBILITY.md`

## 结论摘要

当前静态事实足以支持 CR043 继续进入 CP3 方案边界确认，但不足以启动 CR044 或实现真实 adapter。

- `gm` 更贴近当前项目 Python 3.11 运行时，静态确认存在 order / cancel / cash / position / execution 相关符号。
- `gmtrade` 更贴近独立交易 SDK，但当前公开 wheel 不支持 Python 3.11；Python 3.10 隔离环境静态 import 成功。
- 资金、持仓、委托、撤单、成交回报均能形成候选映射，但字段结构、账号权限和错误语义仍需要后续官方结构文档或 CR044 前置账号权限核对。
- 所有真实运行动作继续 fail-closed：不读取凭据、不登录、不连接、不查询账户、不下单、不撤单。

## 映射矩阵

| CR042 内部合同 | schema / 字段 | `gm` 静态候选 | `gmtrade` 静态候选 | 权限 / 副作用 | CR043 允许状态 | 映射结论 | 风险 / 待确认 |
|---|---|---|---|---|---|---|---|
| `BrokerAdapter.capabilities()` | `broker_adapter_capability_v1`；`can_query_cash`、`can_query_positions`、`can_submit_order_intents`、`can_cancel_orders`、`requires_credentials`、`real_broker_enabled`、`simulation_ready`、`live_ready`、`not_authorization` | `gm.api` 静态符号覆盖 order / cancel / cash / position / execution | `gmtrade.api` 静态符号覆盖 order / cancel / cash / execution / login / start | SDK 能力不等于当前授权；真实能力依赖 token、account、endpoint、login | L2-static-only | 可设计 capability source 为 `goldminer_static_probe`，但 `real_broker_enabled=false`、`simulation_ready=false`、`live_ready=false`，并保留 `not_authorization=true` | CP3 必须明确主选 SDK；能力声明不得被 UI 或 runner 误读为运行许可 |
| `query_cash()` | `BrokerCashSnapshot.cash`、`available_cash`、`currency`、`as_of`、`source` | `get_cash(account_id=None)` | `get_cash(account=None)` | 账户查询；需要账号对象或 account_id；可能连接 broker | blocked | 只能静态记录候选接口；真实 adapter 未授权时应返回 blocked 或抛 `GOLDMINER_SPIKE_REQUIRED` | 返回字段结构、币种、可用资金语义待官方结构文档或账号权限核对 |
| `query_positions()` | `BrokerPositionSnapshot.symbol`、`quantity`、`sellable_qty`、`average_cost`、`market_value`、`as_of`、`source` | `get_position(account_id=None)` | `get_positions` present；`get_position` missing | 账户持仓查询；需要账号上下文；可能连接 broker | blocked | 可定义 singular/plural adapter normalization 层，但 CR043 不运行 | `gmtrade` singular/plural 差异需 CP3 记录；可卖数量、成本价、市值字段待确认 |
| `submit_order_intents()` | `BrokerOrderRequest.request_id`、`symbol`、`side`、`quantity`、`target_trade_date`、`execution_price_policy`、`order_type` | `order_volume(symbol, volume, side, order_type, position_effect, price=0, ...)` | `order_volume(...)`、`order_batch(order_infos, account=None)` | 下单；产生 broker 状态变化 | blocked | 只允许把内部 order intent 字段映射到候选参数名；任何调用必须阻断 | side / order_type / position_effect / price / order_duration / order_qualifier 的枚举值需官方确认 |
| `cancel_order()` | `adapter_order_ref`、`reason`、`BrokerAdapterResult` | `order_cancel(wait_cancel_orders)`、`order_cancel_all()` | `order_cancel(wait_cancel_orders)`、`order_cancel_all(account=None)` | 撤单；产生 broker 状态变化 | blocked | 可记录撤单接口候选；真实 adapter 需要订单引用结构映射 | `wait_cancel_orders` 结构、单笔 / 批量撤单返回状态待确认 |
| `BrokerFillEvent` | `adapter_order_ref`、`filled_qty`、`status`、`exec_price`、`costs`、`reason_code` | `get_execution_reports()`；事件机制待确认 | `get_execution_reports(account=None)`；`start()` 与事件回调相关 | 成交查询和事件订阅；需要账号 / event loop / broker 连接 | L2-static-only for symbols; runtime blocked | 可设计成交回报标准化层，但事件泵不在 CR043 内启动 | 成交状态枚举、部分成交、拒单、费用字段待确认 |
| `BrokerAdapterErrorEvent` | `broker_adapter_error_v1`；`code`、`message`、`source`、`retryable` | 静态枚举可继续核对；当前报告仅确认 API 符号 | `gmtrade.enum` / docstring 可继续静态核对 | 错误语义可能来自 SDK 异常、账号权限、网络和交易拒绝 | L2-static-only | 可建立错误归一化候选：credential_missing、login_required、permission_denied、network_error、order_rejected、cancel_rejected、unknown_sdk_error | 需要官方错误码 / 异常类清单，当前不得脑补为已验证 |
| `FORBIDDEN_ADAPTER_OPERATION_COUNTERS` | `real_broker_call`、`real_order_call`、`real_cancel_call`、`real_account_query`、`real_position_query`、`real_cash_query`、`credential_read`、`goldminer_import_or_call`、`gmtrade_import_or_call` | `gm` L2 静态 import 已在隔离环境执行，未写项目依赖 | `gmtrade` L2 静态 import 已在 Python 3.10 隔离环境执行，Python 3.11 解析失败 | 任何真实调用计数非零必须阻断 | L2-static-only | 后续若写探针脚本，必须区分 `static_import_probe` 与 `runtime_call`; 真实 adapter 默认计数为 0 | CR042 当前 counter 名称把 import 和 call 合并为 `goldminer_import_or_call` / `gmtrade_import_or_call`，若后续要记录 L2 import，需另行设计静态证据计数，避免误伤 no-runtime guard |
| `SENSITIVE_FIELD_PATTERNS` | token、secret、password、session、account_id、broker_account、real_account、trade_password、credential | `set_token(token)` 静态存在 | `set_token(token)`、`account(account_id='', account_alias='')` 静态存在 | 触及凭据 / 账户标识 | blocked | 任何 adapter 输入、报告、日志、artifact 中出现敏感字段名或值，均应按 CR042 validator 阻断或脱敏 | `account_id` 是敏感字段；CR043 不要求用户提供、不读取、不保存 |
| `GoldminerStubBrokerAdapter` | 当前 `can_* = false`，blocked reason=`goldminer_spike_required` | N/A | N/A | 无真实副作用 | allowed | 继续保留为唯一 Goldminer 运行态对象；CR043 不替换成真实 adapter | 真实 adapter 必须进入后续 LLD / 实现 / 验证门禁 |

## 主选 SDK 初判

| 方案 | 优点 | 缺点 | 当前建议 |
|---|---|---|---|
| `gm` | Python 3.11 静态 import 成功；公开版本较新；符号覆盖行情、订单、撤单、资金、持仓、成交 | 可能同时覆盖研究 / 交易 API；真实交易语义、账号模式和事件机制需进一步确认 | 作为当前项目同 runtime 方案的主选候选 |
| `gmtrade` | 名称和 docstring 更贴近独立交易 SDK；提供 endpoint、account、login、start/stop、order/cancel/query 符号 | Python 3.11 无匹配 wheel；需要 Python 3.10 隔离 runtime 或等待新 wheel | 作为交易 SDK fallback / 独立 runtime 候选 |

## CP3 必须决策的问题

| 决策 ID | 类型 | 问题 | 推荐 |
|---|---|---|---|
| CP3-CR043-DQ-01 | architecture | 主选 SDK 使用 `gm` 还是 `gmtrade` | 推荐 `gm` 作为 Python 3.11 主选候选，`gmtrade` 作为 Python 3.10 隔离 runtime fallback。 |
| CP3-CR043-DQ-02 | implementation | 是否允许在当前 CR043 写真实 adapter 代码 | 不允许。CR043 只输出 Spike 证据和设计输入；真实 adapter 进入后续 CR。 |
| CP3-CR043-DQ-03 | security | capability 是否可以声明 SDK 支持的交易能力 | 可以声明“SDK 静态支持候选”，但必须同时声明 `not_authorization=true`、`real_broker_enabled=false`、`simulation_ready=false`、`live_ready=false`。 |
| CP3-CR043-DQ-04 | risk_acceptance | `gmtrade` Python 3.11 不可用如何处理 | 标为技术选型风险；若后续必须使用 `gmtrade`，需要 Python 3.10 隔离运行方案。 |

## No-Operation Guard

| 动作 | CR043 行为 |
|---|---|
| 读取 token / account / session / 密码 | 禁止；任何发现必须停止并记录为越界。 |
| 调用 `set_token`、`account`、`login`、`set_endpoint`、`start` | 禁止；即使函数静态存在也不得调用。 |
| 调用 `get_cash`、`get_position` / `get_positions`、`get_unfinished_orders`、`get_execution_reports` | 禁止；属于账户运行查询。 |
| 调用 `order_volume`、`order_batch`、`order_cancel`、`order_cancel_all`、`order_close_all` | 禁止；属于交易或撤单副作用。 |
| 启动 simulation/live | 禁止；只能由 CR044 或后续独立 CR 逐 run 授权。 |

## CR044 准入建议输入

CR043 目前不能给出 CR044 PASS。若后续 CP3 收敛，可考虑以下关闭结论：

| 结论 | 触发条件 |
|---|---|
| `PASS_WITH_UNKNOWN_RISKS` | SDK 主选和接口映射明确，未知项均可在 CR044 前通过账号权限或官方结构文档核对关闭。 |
| `NEEDS_ACCOUNT_PERMISSION` | 接口存在但资金 / 持仓 / 委托 / 成交字段必须依赖账号权限才能确认。 |
| `BLOCKED_BY_DOCS` | 官方资料或 SDK 结构无法支撑字段映射和错误归一化。 |
| `NOT_RECOMMENDED` | Python runtime、SDK 兼容性、权限边界或 no-operation guard 无法接受。 |
