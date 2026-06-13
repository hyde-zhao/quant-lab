# CR043 Goldminer Adapter Spike 工程事实可行性报告

生成时间：2026-06-11T08:05:00+08:00  
状态：draft-for-CP2/CP3  
范围：L1 官方公开资料核对 + L2 隔离 SDK 静态核对  

## 结论摘要

CR043 的工程事实初判为：**可继续推进到 CP2/CP3 边界确认，但不能进入 CR044 仿真准入或真实 adapter 实现。**

原因：

- `gm` SDK 在公开包元数据中显示可用于 Python 3.11，且 L2 静态 import `gm.api` 成功。
- `gm.api` 静态核对确认存在 `set_token`、`history`、`subscribe`、`order_volume`、`order_cancel`、`order_cancel_all`、`get_cash`、`get_position`、`get_unfinished_orders`、`get_execution_reports` 等符号。
- `gmtrade` 独立交易 SDK 在 Python 3.10 隔离环境可 import，静态核对确认存在 token、endpoint、account、login、start/stop、order、cancel、cash、unfinished orders、execution reports 等符号。
- `gmtrade` 在当前项目 Python 3.11 运行时不可直接满足依赖解析：公开 wheel 只覆盖 `cp36m`、`cp37m`、`cp38`、`cp39`、`cp310`。若选择 `gmtrade` 作为交易 SDK，后续需要 Python 3.10 隔离运行或等待/确认 cp311 wheel。
- 官方公开仿真接入资料明确指出仿真 API 涉及 token、account_id、登录账户、下单、撤单、资金/持仓/委托成交查询和实时交易事件；这些均属于 CR044 或后续运行授权范围，CR043 内必须继续阻断真实调用。

## 证据等级

| 等级 | 本轮状态 | 说明 |
|---|---|---|
| L0 local contract baseline | confirmed | CR042 `BrokerAdapter` / `GoldminerStubBrokerAdapter` 已存在。 |
| L1 official public docs check | partial-confirmed | 可访问官方 PyPI 包元数据与 myquant 官方 GitHub 仿真接入文档；部分 myquant docs2 页面通过搜索可见但直接抓取返回 403。 |
| L2 isolated SDK static check | partial-confirmed | `gm` Python 3.11 import / 符号核对成功；`gmtrade` Python 3.10 import / 符号核对成功；`gmtrade` Python 3.11 解析失败。 |
| L3 account / credential check | not-authorized | 不读取 token、账号、密码、session。 |
| L4 simulation/live runtime | not-authorized | 不登录、不连接、不查询账户、不下单、不撤单。 |

## L1 官方公开事实

| 事实 ID | 来源 | 事实 | CR043 判断 |
|---|---|---|---|
| F-CR043-L1-001 | `https://pypi.org/project/gm/` | `gm` 最新公开版本为 `3.0.184`，发布日期 2026-06-02；PyPI 分类包含 Python 3.11 / 3.12 / 3.13；包说明为“掘金量化 掘金3 sdk”。 | `gm` 是当前项目 Python 3.11 下优先静态核对对象。 |
| F-CR043-L1-002 | `https://pypi.org/project/gmtrade/` | `gmtrade` 最新公开版本为 `3.0.6`，发布日期 2023-10-16；包说明为“掘金3 交易sdk”；wheel 覆盖到 `cp310`，包括 Linux / Windows。 | `gmtrade` 是交易 SDK 候选，但与项目 Python 3.11 不直接匹配。 |
| F-CR043-L1-003 | `https://github.com/myquant/paper-trading-doc` | 掘金仿真 API 接入资料说明可下单、撤单、查询资金、持仓、委托成交，并有实时消息推送。 | 能力面覆盖 BrokerAdapter 的 order/cancel/cash/position/fill/event 需求，但属于运行授权高风险面。 |
| F-CR043-L1-004 | `https://github.com/myquant/paper-trading-doc` | 仿真 API 接入地址示例为 `api.myquant.cn:9000`，账户登录需要 token 和 account_id。 | 任何真实连接、登录、token、account_id 均不属于 CR043 当前授权。 |
| F-CR043-L1-005 | `https://github.com/myquant/paper-trading-doc` | 文档示例列出 `order_volume`、`order_batch`、`order_cancel`、`order_cancel_all`、`order_close_all`、`get_unfinished_orders`、`get_execution_reports`、`get_position`、`get_cash` 和交易事件。 | 可作为接口映射矩阵输入，但不能直接运行。 |

## L2 SDK 静态核对

### `gm` 静态核对

执行边界：Python 3.11、`uv run --no-project --isolated --with gm`、无 token、无登录、无连接、无接口调用。

| 项 | 结果 |
|---|---|
| 包名 | `gm` |
| 版本 | `3.0.184` |
| Requires-Python | `>=3.6, <4` |
| Python 3.11 import | PASS |
| `gm.api` import | PASS |
| 关键模块 | `gm.api`、`gm.constant`、`gm.enum`、`gm.model`、`gm.csdk` |

静态符号 / 签名：

| 符号 | 静态结果 | 签名 / 说明 |
|---|---|---|
| `set_token` | present | `(token)` |
| `history` | present | `(symbol, frequency, start_time, end_time, fields=None, skip_suspended=True, fill_missing=None, adjust=None, adjust_end_time='', df=False)` |
| `subscribe` | present | `(symbols, frequency=None, count=0, wait_group=False, wait_group_timeout='10s', unsubscribe_previous=False, fields=None, format='df')` |
| `order_volume` | present | `(symbol, volume, side, order_type, position_effect, price=0, trigger_type=0, stop_price=0, order_duration=0, order_qualifier=0, account='')` |
| `order_cancel` | present | `(wait_cancel_orders)` |
| `order_cancel_all` | present | `()` |
| `get_cash` | present | `(account_id=None)` |
| `get_position` | present | `(account_id=None)` |
| `get_unfinished_orders` | present | `()` |
| `get_execution_reports` | present | `()` |

风险：

- 静态存在不等于当前授权可调用。
- `set_token`、订单、撤单、账户查询、订阅 / 事件都可能触及凭据、连接或运行侧状态，CR043 内必须 fail-closed。

### `gmtrade` 静态核对

执行边界：Python 3.10、`uv run --no-project --isolated --with gmtrade`、无 token、无登录、无连接、无接口调用。

| 项 | 结果 |
|---|---|
| 包名 | `gmtrade` |
| 版本 | `3.0.6` |
| Requires-Python | `>=3.6, <4` |
| Python 3.11 解析 | FAIL：无 cp311 wheel |
| Python 3.10 import | PASS |
| 关键模块 | `gmtrade.api`、`gmtrade.constant`、`gmtrade.enum`、`gmtrade.csdk`、`gmtrade.pb` |

静态符号 / 签名：

| 符号 | 静态结果 | 签名 / 说明 |
|---|---|---|
| `set_token` | present | `(token)` |
| `set_endpoint` | present | `(serv_addr='localhost:7001')` |
| `account` | present | `(account_id='', account_alias='')` |
| `login` | present | `(*args)` |
| `start` | present | `(filename=None)` |
| `stop` | present | `()` |
| `order_volume` | present | `(symbol, volume, side, order_type, position_effect, price=0, order_duration=0, order_qualifier=0, account=None)` |
| `order_batch` | present | `(order_infos, account=None)` |
| `order_cancel` | present | `(wait_cancel_orders)` |
| `order_cancel_all` | present | `(account=None)` |
| `order_close_all` | present | `(account=None)` |
| `get_unfinished_orders` | present | `(account=None)` |
| `get_execution_reports` | present | `(account=None)` |
| `get_cash` | present | `(account=None)` |
| `get_position` | missing | 文档/示例提到 singular；SDK 静态符号核对为 missing。 |
| `get_positions` | present | 通过 position-like 符号扫描发现。 |

风险：

- `gmtrade` 更贴近独立交易 SDK，但当前项目 Python 3.11 不直接可用。
- 后续若采用 `gmtrade`，需独立 Python 3.10 runtime 方案或确认新版本 cp311 支持。
- `set_endpoint` 默认 `localhost:7001`，官方仿真文档示例可用 `api.myquant.cn:9000`；endpoint 选择属于运行授权，不在 CR043 执行。

## BrokerAdapter 映射矩阵

| CR042 内部合同 | `gm` 静态候选 | `gmtrade` 静态候选 | 映射结论 | CR043 允许动作 |
|---|---|---|---|---|
| `BrokerAdapter.capabilities()` | `dir(gm.api)` 显示 order/cash/position/execution 相关符号 | `gmtrade.api` 显示 order/cancel/cash/execution/start/login 相关符号 | 可设计 capability，但必须区分“SDK 支持”和“当前授权允许”。 | 静态映射 |
| `query_cash()` / `BrokerCashSnapshot` | `get_cash(account_id=None)` | `get_cash(account=None)` | 可映射资金查询能力；字段需后续官方结构文档或账号权限核对。 | 静态映射；不查询账户 |
| `query_positions()` / `BrokerPositionSnapshot` | `get_position(account_id=None)` | `get_positions` present；`get_position` missing | 可映射持仓查询能力，但 singular/plural API 有差异。 | 静态映射；不查询账户 |
| `submit_order_intents()` / `BrokerOrderRequest` | `order_volume(...)` | `order_volume(...)`、`order_batch(...)` | 可映射基础委托；需处理 side/order_type/position_effect/price/order_duration/order_qualifier。 | 静态映射；不下单 |
| `cancel_order()` | `order_cancel(wait_cancel_orders)`、`order_cancel_all()` | `order_cancel(wait_cancel_orders)`、`order_cancel_all(account=None)` | 可映射撤单能力；需明确订单引用结构。 | 静态映射；不撤单 |
| `BrokerFillEvent` | `get_execution_reports()`；交易事件待进一步映射 | `get_execution_reports(account=None)`；事件 `start()` 相关 | 成交回报可通过查询或事件映射；事件泵属于运行侧，CR043 不启动。 | 静态映射 |
| `BrokerAdapterErrorEvent` | `OrderRejectReason_*`、`CancelOrderRejectReason_*` 等枚举 | docstring / enum 可继续静态核对 | 可建立错误归一化矩阵。 | 静态映射 |
| `GoldminerStubBrokerAdapter` | N/A | N/A | 继续作为 fail-closed stub；不得在 CR043 静默替换为真实 adapter。 | 保留 stub |

## 权限与运行边界

| 能力 | 当前事实 | 当前授权 | 后续要求 |
|---|---|---|---|
| 官方文档核对 | 部分可访问，部分 docs2 页面抓取 403 | 允许 | 记录来源、时间、版本和不可访问项。 |
| SDK 下载 / import | `gm` Python 3.11 PASS；`gmtrade` Python 3.10 PASS | 允许隔离静态核对 | 不写项目依赖，不调用运行函数。 |
| token | 官方资料和 SDK 均显示 token 是身份认证关键项 | 不授权 | CR044 前单独凭据方案。 |
| account_id / account object | 官方资料和 SDK 均显示账户对象 / 账户 ID 参与交易接口 | 不授权 | CR044 前单独账号权限核对。 |
| endpoint / login / start | `gmtrade` 静态符号存在 | 不授权 | CR044 或单独运行授权。 |
| cash / position query | SDK 静态符号存在 | 不授权真实查询 | 只做字段和返回结构映射。 |
| order / cancel | SDK 静态符号存在 | 不授权 | CR044 逐 run 授权。 |
| simulation/live | 官方资料支持仿真交易 | 不授权 | CR044 独立启动。 |

## 风险清单

| 风险 ID | 风险 | 影响 | 处理 |
|---|---|---|---|
| R-CR043-001 | `gmtrade` 不支持项目 Python 3.11 wheel | 若采用 gmtrade，需要隔离 Python 3.10 runtime | 作为 CR044 前置技术选型决策。 |
| R-CR043-002 | 官方 docs2 页面部分抓取 403 | 资料完整性可能不足 | 标记为 partial-confirmed；可由用户提供官方文档导出或授权浏览器人工核对。 |
| R-CR043-003 | `gm` 和 `gmtrade` 两条 SDK 线能力重叠但版本节奏不同 | adapter 选型可能混淆 | CP3 必须明确主选 SDK 和 fallback。 |
| R-CR043-004 | token / account_id 是关键前置 | 凭据边界不清会阻塞 CR044 | CR043 不读取凭据，只输出凭据处理方案。 |
| R-CR043-005 | 订单 / 撤单 / 事件泵均可能产生 broker 状态变化 | 误调用会越权 | 所有真实运行函数在 CR043 内必须 fail-closed。 |
| R-CR043-006 | SDK 静态符号存在不等于账号权限可用 | CR044 仍可能被账号权限阻塞 | 结论可为 `NEEDS_ACCOUNT_PERMISSION`。 |

## 当前阶段决策建议

| 决策 | 推荐 |
|---|---|
| 是否继续 CR043 | 继续，进入 CP2/CP3 边界设计。 |
| 主选 SDK | 初步建议优先评估 `gm`，因为 Python 3.11 支持更贴近当前项目；`gmtrade` 作为独立交易 SDK候选，但需要 Python 3.10 隔离运行。 |
| 是否启动 CR044 | 暂不启动。 |
| CR043 关闭候选结论 | 当前不应 PASS；建议继续 CP3 映射后再判断 `PASS_WITH_UNKNOWN_RISKS` / `NEEDS_ACCOUNT_PERMISSION` / `NOT_RECOMMENDED`。 |

## 本轮未执行动作

- 未读取 `.env`、token、账号、密码、session、cookie、密钥或终端配置。
- 未登录掘金。
- 未连接 broker。
- 未查询资金、持仓、订单或成交。
- 未下单、撤单或改单。
- 未启动 simulation/live。
- 未写 lake、未 publish。
- 未修改项目依赖声明或锁文件。
