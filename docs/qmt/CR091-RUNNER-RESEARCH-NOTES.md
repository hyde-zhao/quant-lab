# CR091 Runner Research Notes

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| v0.1 | 2026-06-18 | host-orchestrator | 启动 CR091 静态研究，形成多因子优先、通用策略可扩展的 runner 方案输入。 |
| v0.2 | 2026-06-18 | host-orchestrator | 按用户要求补充 CR091 推荐框架与参考框架的功能支持矩阵和取舍理由。 |
| v0.3 | 2026-06-18 | host-orchestrator | 明确对比材料的文档分层：研究报告保留完整矩阵，HLD 仅保留架构决策摘要。 |

## 研究边界

本研究只做静态阅读和方案分析，不执行下列动作：

- 不克隆、安装或运行外部项目。
- 不启动 QMT / MiniQMT / XtQuant / gateway / runner。
- 不访问 NAS。
- 不读取 `.env`、凭据、账号、账户、资金、持仓、委托、成交或日志原文。
- 不执行 submit / cancel / simulation / live / provider / lake / publish。

## 本地基线

| 本地对象 | 观察结论 | 对 CR091 的设计含义 |
|---|---|---|
| `engine/multifactor_contracts.py` | 多因子研究合同已有 `FactorSpec` / `FactorRunSpec`、禁止操作计数和 blocked claims，默认不声明 QMT / simulation / live ready。 | 多因子应作为首选策略输入，但只能作为研究级准入包消费，不能直接放大为可交易。 |
| `engine/multifactor_strategy_candidates.py` | 已有 `multifactor_strategy_admission_package_v1`、策略候选、风险成本摘要、因子贡献和全零 operation counts。 | runner 首版应优先消费多因子 admission package，并转成目标组合 / order intent draft。 |
| `engine/order_intent_draft.py` | 已有 `order_intent_draft_v1`，默认 `qmt_allowed=false`、`not_authorization=true`，并阻断 QMT / XtQuant / submit / cancel / account / simulation / live。 | CR091 不应发明新的订单语义；应把策略输出规范化到现有 order intent draft。 |
| `strategies/base.py` | 已有 RSI / MACD / momentum 的纯函数策略分发，输出 `StrategyResult`。 | 需要新增 StrategyAdapter 层，让非多因子策略也能进入同一 runner 输入契约。 |
| `trading/qmt_client.py` | QMT client 是可注入 transport 的离线 typed contract，默认不启动服务、不读凭据、不执行交易。 | runner 应只依赖该 typed client / fake transport，真实 HTTP transport 仅在用户逐 run 授权后手工使用。 |
| `trading/qmt_gateway_contracts.py` | `query_positions` 合同已有 endpoint、scope、脱敏 payload 和禁止操作计数。 | 首版只读 runner 的唯一账户侧能力应保持 health / capabilities / query_positions。 |
| `packages/qmt_interface_smoke/0.1.0/manifest.yaml` | CR089 包声明 runtime / NAS / credential / account / trade_write 全 false，并定义离线校验和只读 smoke 合同。 | 可作为 CR091 package intake 的第一个 fixture，但不激活 CR089 runtime。 |
| `scripts/collect_cr089_qmt_runtime_smoke_summary.py` | 交易主机本地采集脚本只输出脱敏摘要，禁止输出原始账户、持仓、secret、nonce、signature 或日志。 | CR091 evidence writer 应沿用 redacted summary only 模型。 |

## 外部参考矩阵

| 项目 | 来源 | 可借鉴点 | 不采纳 / 后置点 | 对推荐方案的影响 |
|---|---|---|---|---|
| lite-qmt-executor | https://github.com/lotey/lite-qmt-executor | 交易引擎分层、HTTP / WebSocket 信号入口、策略插件、队列和 ticker 调度、WAL / 状态恢复思路。 | 项目配置要求 QMT 路径和真实资金账号，支持买卖接口和自动拉起 miniQMT；这些不进入 CR091 首版。 | 借鉴“调度骨架和策略插件”概念，但不采用其执行器主体。 |
| qmt-gateway | https://github.com/zillionare/qmt-gateway | Windows gateway 服务化、REST / WebSocket API、health / connection status、服务层与 xtquant 分离。 | 交易 API、API key、自动启动 QMT、密码 / 管理界面、日志流、资产 / 委托 / 成交端点风险过高。 | 证明 gateway 隔离方向合理，但 CR091 只消费本仓库既有只读 gateway contract。 |
| xqshare | https://github.com/jasonhu/xqshare | xtquant remote proxy、客户端接口兼容、远程隔离思路。 | 示例包含 client secret、账户对象、连接交易服务器和查询持仓；不适合作为首版 runner 主体。 | 借鉴“远端代理”作为长期方向，首版不引入。 |
| vnpy_qmt | https://github.com/ruyisee/vnpy_qmt | vn.py gateway 接入、事件引擎、成熟交易应用边界。 | 目标是连接 mini 客户端实现普通买卖，完整 vn.py 体系对当前最小 runner 过重。 | 作为未来复杂事件驱动 / 下单 CR 的参考，不纳入 CR091 首版。 |

## 功能支持矩阵

说明：

- `支持`：CR091 首版设计或参考框架的核心能力。
- `不支持`：明确不提供，或不作为该框架目标。
- `部分`：存在相邻能力，但不是完整目标能力。
- `后置`：CR091 不放入首版，但可作为后续 CR 独立评估。

| 功能 / 能力 | CR091 推荐框架 | lite-qmt-executor | qmt-gateway | xqshare | vnpy_qmt | CR091 取舍原因 |
|---|---|---|---|---|---|---|
| 多因子 admission package 消费 | 支持 | 不支持 | 不支持 | 不支持 | 不支持 | 这是 CR091 的核心缺口：把 CR039/CR038 多因子研究产物转成 runner 可验证输入；参考框架主要面向执行 / 网关，不解决研究准入包消费。 |
| RSI / MACD / momentum 等非多因子策略适配 | 支持 | 部分，支持买卖策略插件 | 不支持 | 不支持 | 部分，依赖 vn.py 策略体系 | CR091 使用统一 `StrategyAdapter`，既优先多因子，也避免后续每类策略各自写 runner。 |
| 策略包 manifest / checksum 校验 | 支持 | 不支持 | 不支持 | 不支持 | 不支持 | CR091 需要可审计 package intake；外部框架更关注运行配置和交易 API，不提供本仓库所需的 package 审批合同。 |
| 本地 immutable cache / active pointer | 支持 | 不支持 | 不支持 | 不支持 | 不支持 | 首版避免从 NAS 原地运行，使用本地不可变缓存降低路径漂移和半写入风险。 |
| 离线 fixture / fake transport 自动验证 | 支持 | 不支持 | 不支持 | 不支持 | 不支持 | CR091 当前不授权 runtime，所以必须用 fake transport 证明合同和边界；参考框架通常以真实 QMT / miniQMT 运行环境为前提。 |
| 只读 health / capabilities / query_positions | 支持，仅受控只读 | 部分，执行器可封装 broker 查询但非只读门禁主体 | 支持更多账户 / 连接状态接口 | 支持持仓查询示例 | 部分，通过 vn.py gateway 连接后可查询 | CR091 只保留最小只读对账面，避免资产、委托、成交、日志等原始输出进入 evidence。 |
| 买入 / 卖出 / 撤单 | 不支持，拆 CR092 | 支持 | 支持 | 后置 / 取决于 xttrader 风格接口 | 支持普通买卖 | 交易写接口需要 order intent、pre-trade risk、kill switch、撤单语义和逐 run 授权，不能混入 runner 首版。 |
| 自动启动 QMT / miniQMT | 不支持 | 支持一键脚本自动拉起 | 支持可选自动启动 QMT | 不作为核心目标 | 不支持，要求先启动登录 QMT mini | 自动启动会触碰交易终端、路径、登录和凭据边界；CR091 首版必须保持 agent 不启动 runtime。 |
| API key / secret / session 鉴权 | 不支持 agent 侧读取 | 部分，信号网关 token 配置 | 支持 session / API key | 支持 client secret | 取决于 vn.py / QMT 配置 | CR091 不读取 `.env` 或 secret；鉴权只作为未来交易主机本地逐 run 授权的一部分。 |
| 行情 WebSocket / 历史数据下载 | 不支持 | 部分，作为执行输入周边 | 支持行情 WebSocket 和历史数据下载 | 支持行情 / 下载示例 | 依赖 vn.py 生态 | CR091 只验证策略包消费和只读对账，不引入行情 provider、历史数据下载或 lake/publish 风险。 |
| Web UI / 交易台 | 不支持 | 不支持核心 UI | 支持 Web 交易台 | 不支持 | 支持 vn.py UI | UI 会扩大账号、日志、委托和操作面；CR091 首版只交付可测试的离线 runner 合同。 |
| 日志流 / 原始日志查看 | 不支持，只允许脱敏 evidence | 部分 | 支持日志流 / 日志文件 | 支持服务端 / 客户端日志 | 依赖 vn.py 日志体系 | CR091 明确禁止原始日志和账户/持仓明细输出，只保留 redacted summary。 |
| NAS package pull / publish | 不支持，拆 CR093 | 不支持 | 不支持 | 不支持 | 不支持 | NAS 自动交换是独立存储 / 发布治理问题；CR091 首版只定义本地 cache / active pointer。 |
| 完整事件驱动交易系统 | 不支持 | 部分，轻量 TradingEngine | 部分，gateway service | 不支持 | 支持 vn.py 事件引擎接入 | 当前目标不是完整交易平台；若未来需要复杂事件驱动，再评估 vn.py / Lean 类框架。 |
| Backtest / simulation / live | 不支持 | 不支持回测，支持实盘执行 | 不支持回测，支持交易接口 | 后置 / 远程 xtquant 能力 | vn.py 生态可扩展，但 vnpy_qmt 本身是 gateway | CR091 首版不证明 simulation-ready 或 live-ready；这些必须独立门禁。 |
| 交易风控 / kill switch | 不支持交易风控，只支持 fail-closed 权限门 | 部分，执行策略可自定义 | 部分，取决于服务层 | 不支持 | 依赖 vn.py 生态 | CR091 不进入下单链路；真正交易风控应和 CR092 order write 一起设计。 |

## 取舍结论

CR091 不是要复制一个成熟交易执行框架，而是要补齐本仓库缺失的“策略研究产物到 runner 可验证输入”的中间层。因此取舍原则是：

1. 凡是能增强策略包可审计性、离线验证、脱敏 evidence 和多策略统一输入的能力，首版支持。
2. 凡是会触碰真实 QMT runtime、账号、凭据、日志、下单、撤单、行情下载、NAS 发布或 UI 操作的能力，首版不支持。
3. 参考框架的分层、插件、gateway 隔离和事件驱动思想可借鉴，但不直接 vendor / 改造，因为直接采用会把交易写接口和 runner 验证混在一起。

## 文档分层与维护约定

| 文档 | 保留内容 | 不重复维护内容 | 目的 |
|---|---|---|---|
| 本研究报告 | 完整外部参考矩阵、完整功能支持矩阵、支持 / 不支持 / 部分 / 后置判断、取舍理由。 | 不承担最终架构承诺；不替代 HLD 的推荐方案和 ADR。 | 作为 CR091 的调研证据和后续追溯入口。 |
| `CR091-QMT-STRATEGY-RUNNER-HLD.md` | 只保留影响架构取舍的决策摘要：为何选择 clean-room package-driven runner，哪些参考能力被借鉴或拒绝。 | 不复制完整功能矩阵，避免研究证据和架构决策双份漂移。 | 支撑 CP3 架构确认和 CP5 实施前审查。 |
| `CR091-QMT-STRATEGY-RUNNER-TEST-PLAN.md` / LLD | 只引用研究报告和 HLD 的结论，落到验证范围、fixture 和任务拆分。 | 不再维护参考框架对比表。 | 保持测试与实现文档聚焦可执行验证。 |

## 方案判断

不推荐直接改造任何外部 runner / gateway 项目。原因是这些项目的核心价值集中在真实交易、自动登录、账户和订单接口，而 CR091 当前要解决的是“策略如何被 runner 验证和消费”的结构缺口。直接引入外部执行器会把 runner gap 和交易写权限混在一起，扩大风险面。

推荐采用 clean-room package-driven runner：

1. 多因子优先：以 `multifactor_strategy_admission_package_v1` 作为首个一等输入。
2. 通用策略可扩展：新增 `StrategyAdapter`，把多因子、RSI / MACD / momentum、未来自定义策略统一成 `TargetPortfolioSnapshot` 和 `OrderIntentDraftV1`。
3. runner 只做 package intake、manifest / checksum 校验、immutable cache、active pointer、只读 gateway 对账、脱敏 evidence。
4. QMT / MiniQMT / XtQuant / gateway runtime 只保留为用户交易主机逐 run 授权后的手工可选验证，不进入默认实现。
5. submit / cancel / simulation / live 必须拆为 CR092 或后续独立高风险 CR。

## 结论

CR091 的最佳路线不是“先把 QMT 跑起来”，而是先建立一个 broker-neutral、package-driven、multi-factor-first 的策略运行合同。它应能消费多因子策略包，也能适配已有单策略函数和后续策略包，但在 CP5 之前只形成设计与测试计划，在 CP6 之后也只允许离线 fixture / fake transport 验证。
