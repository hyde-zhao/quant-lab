# CR-025 Backtrader 模块 Reference / No-Copy Guardrail

## 1. 目的与适用范围

本文是 `CR025-S04-backtrader-module-reference-no-copy-guardrail` 的模块 reference 合同。它只把 `process/HLD.md` §34.5 / §34.14、`process/ARCHITECTURE-DECISION.md` ADR-075 / ADR-076 / ADR-078 和 CP5 批次人工确认中的结论落为可测试边界。

Backtrader 在 CR-025 中只作为 lightweight execution engine 的 execution semantic reference，用于理解 feed、broker、order、trade、position、commission、slippage、analyzer、observer、writer 和 strategy lifecycle 等执行语义。Backtrader 不作为多因子研究主框架，不作为 production truth，不作为 simulation-ready 结论，不作为 QMT admission pass，也不替代本项目的 lightweight baseline。

本文不读取、复制、裁剪、改写或源码级移植 `/home/hyde/download/backtrader/**` 中的 Backtrader GPLv3 / GPLv3+ 源码、samples、tests、datas、live store 或 line/metaclass runtime。本文也不授权运行 Backtrader backend、Backtrader samples、Backtrader tests、真实 broker、QMT / MiniQMT / XtQuant、provider fetch、lake write、catalog publish、simulation/live 或凭据读取。

## 2. 决策输入

| 输入 | 合同含义 |
|---|---|
| HLD §34.5 Backtrader 本地项目模块级分析矩阵 | 四类模块处理分类：`reference_only`、`adapt_interface`、`migration_candidate`、`exclude`。 |
| HLD §34.14 主要风险与应对 | GPLv3 源码复制、默认主路径漂移、clean feed 绕过、order intent draft 被误用、多因子研究范围膨胀均为风险。 |
| ADR-075 | Backtrader 模块处理采用 reference/adapt/exclude 分类；`migration_candidate` 当前为空。 |
| ADR-076 | GPLv3 源码级移植默认 no-copy；任何例外需要新 CR、legal review、CP3 和 CP5。 |
| ADR-078 | CR-025 不承接多因子研究闭环主框架；相关能力进入后续 CR，当前记录为 CR-030 候选边界。 |
| CP5 批次人工确认 | `approve` 只授权受控离线 / fixture / 静态合同实现，不授权依赖变更、Backtrader 运行、源码迁移、真实操作或多因子研究主框架实现。 |

## 3. 分类枚举合同

分类枚举固定为四类，测试按 exact token 验证：

- `reference_only`：只用于语义、模块职责和边界参考，不复制实现。
- `adapt_interface`：只允许在本项目中 clean-room 定义接口、字段和行为合同，不移植 Backtrader internals。
- `migration_candidate`：当前必须为空。
- `exclude`：默认禁止进入 CR-025 实现范围。

当前源码级迁移候选为空，必须同时满足以下两个形式：

```yaml
migration_candidate: []
```

```text
migration_candidate=[]
```

`migration_candidate=[]` 不是永久禁止任何未来迁移，而是表示 CR-025 当前没有源码级迁移候选。任何候选从空集合变为非空，都必须停止当前 Story，另起 CR，完成 legal review，并重新通过 CP3 决策和 CP5 LLD / 实现授权。

## 4. 模块 Reference 矩阵

| 分类 | 模块 / 概念 | 允许事项 | 禁止事项 | 后续切换条件 |
|---|---|---|---|---|
| `reference_only` | `cerebro.py`、broker、order/trade/position、analyzer/observer、strategy/signal、plot/writer、samples/tests | 作为 execution semantic reference 识别编排、现金、成交、订单状态、仓位、成本、滑点、报告和生命周期语义。 | 禁止复制 `Cerebro` run loop、broker 状态机、Order/Trade/Position 类、analyzer 公式、strategy 继承模型、plot/writer 源码、samples/tests/datas。 | 若需要真实 Backtrader 对照，只能在后续 CP5 授权 optional dependency runtime，不把源码纳入仓库。 |
| `adapt_interface` | clean feed、semantic diff、commission/sizer/fill assumption、target order 概念 | 使用本项目自有代码定义 clean feed gate、semantic diff 字段、成本 / 滑点 / filler 假设和 target portfolio / order intent draft。 | 禁止移植 Backtrader line engine、metaclass runtime、broker internals、feed internals 或指标库实现。 | 仅在对应 Story / LLD 已批准、文件 owner 明确且测试验证通过后落地。 |
| `migration_candidate` | `[]` | 当前无默认源码级候选。 | 禁止在 CR-025 中加入 fork、vendor、裁剪、重命名或手工改写的 Backtrader GPLv3 源码。 | 新 CR + legal review + CP3 风险接受 + CP5 实现授权 + 回滚策略。 |
| `exclude` | live broker/store、外部 feeds、line/metaclass runtime、indicator library migration、samples/tests/datas copy、真实 broker 集成 | 仅可作为风险识别和禁止边界说明。 | 禁止适配 live store，禁止包装外部 broker，禁止复制样例 / 测试 / 数据，禁止引入 line/metaclass 兼容层，禁止把 indicators / Strategy / analyzer 体系改造成多因子研究框架。 | 必须另起 CR；真实 broker / live / QMT 路线还需要独立 runtime authorization。 |

## 5. No-Copy / No-Source-Migration / No-Vendored-Source

CR-025 的默认合规合同为：

- `no-copy`：不复制、裁剪、改写或源码级移植 Backtrader GPLv3 / GPLv3+ 源码。
- `no-source-migration`：不把 Backtrader 类、函数、line runtime、metaclass runtime、broker internals、store internals、indicator implementation、sample strategy、test fixture 或 datas 文件重写成本项目源码。
- `no-vendored-source`：不在本仓库创建 `backtrader/**`、`vendor/backtrader/**`、`vendors/backtrader/**`、`third_party/backtrader/**`、`external/backtrader/**` 或等价 vendored source tree。

禁止路径和禁止内容至少覆盖以下 6 类：

| 类别 | 禁止项 | CR-025 计数 |
|---|---|---:|
| source | Backtrader GPLv3 / GPLv3+ 源码复制、裁剪、改写、fork、vendor、源码级移植 | 0 |
| samples | Backtrader `samples/` 样例策略、样例脚本、样例配置复制 | 0 |
| tests | Backtrader `tests/` 测试源码、断言模式、测试 fixture 复制 | 0 |
| datas | Backtrader `datas/` 或测试数据文件复制、改名、裁剪 | 0 |
| live store | `store.py` / `stores/`、IB / Oanda / VisualChart 等 live broker/store 包装或迁移 | 0 |
| line/metaclass runtime | `metabase.py`、`lineiterator.py`、line buffer、line series、metaclass runtime 或兼容层迁移 | 0 |

允许的测试 fixture 必须由本项目重新构造，描述行为类别即可，不使用 Backtrader samples / tests / datas。允许的接口适配必须是 clean-room interface adaptation，只消费本项目已冻结的 clean feed、semantic diff、order intent draft 或后续独立 Story 的合同。

## 6. Execution Semantic Reference 边界

CR-025 允许参考的 execution semantic 范围包括：

- feed：clean OHLCV / factor panel / score 输入字段、calendar、timeframe/compression 概念，但不复制 Backtrader feed 源码。
- broker / order / trade / position：现金、价值、成交、拒单、过期、margin、partial fill、position update 等状态词表和差异维度。
- commission / sizer / slippage / filler：作为成本、目标仓位、成交假设和差异解释字段。
- analyzer / observer / writer：作为报告类别、timeline event 和结果可解释性参考，不复制公式或 line 体系。
- strategy lifecycle / target order concept：只用于把研究输出解释成 target portfolio / order intent draft，不继承 Backtrader Strategy。

这些参考只服务 lightweight execution engine 的执行语义对齐。任何输出必须标记为 research comparison 或 documentation contract，不得写成默认主路径、production truth、simulation-ready、QMT admission pass 或真实交易授权。

## 7. 多因子研究边界与 CR-030 候选

CR-025 不实现、不设计、不验收多因子研究闭环主框架。以下对象均不属于 CR-025，也不由 Backtrader 承接：

- FactorSpec
- FactorRunSpec
- IC / RankIC
- 分层收益
- 多因子组合
- 实验追踪
- 策略准入包
- Qlib isolated runner
- Alphalens-style factor tear sheet
- vnpy.alpha-style alpha research workflow

多因子研究闭环应另起后续 CR，当前边界记录为 CR-030 候选。CR-030 可以参考 Qlib / Alphalens / vnpy.alpha 的研究框架、因子评价、分层收益、组合构建、实验追踪和准入包思路，但不得从 CR-025 自动继承依赖变更、provider fetch、lake write、catalog publish、Backtrader runtime、QMT / MiniQMT / XtQuant、simulation/live 或凭据读取授权。

## 8. 例外流程

任何源码级 migration candidate、fork、vendored subset、样例 / 测试 / 数据复制、live store 迁移、line/metaclass runtime 迁移或 Backtrader indicators / Strategy / analyzer 体系向多因子研究框架扩展的需求，都必须按以下流程处理：

1. 停止当前 CR-025 Story 实现，不在本 Story 中扩大范围。
2. 由 meta-po 发起新 CR 或回退 CR-025 CP3 / CP5。
3. 在 CP3 中明确模块、替代方案、GPLv3 / copyleft 影响、维护成本、回归范围、分发策略和回滚点。
4. 完成 legal review / 开源合规确认。
5. 在 CP5 中重新冻结 LLD、文件 owner、测试策略、许可证标注、风险接受和用户授权。
6. 未完成上述步骤前，`migration_candidate=[]` 保持不变。

## 9. 禁止操作计数

| 禁止操作 | 计数 | 说明 |
|---|---:|---|
| Backtrader run | 0 | 不运行 Backtrader backend、samples、tests 或真实 runtime。 |
| Backtrader source copy / source migration | 0 | 不复制、裁剪、改写、fork、vendor 或源码级移植。 |
| provider fetch | 0 | 不联网抓取、不触发 Tushare / AkShare / 外部 provider。 |
| lake write | 0 | 不写 raw / manifest / canonical / quality / catalog / gold 或 broker lake。 |
| catalog publish | 0 | 不发布 current pointer。 |
| credential read | 0 | 不读取 `.env`、token、password、cookie、session、account、private key 或交易密码。 |
| QMT / MiniQMT / XtQuant operation | 0 | 不启动 gateway，不发单，不撤单，不查询账户或持仓。 |
| broker / simulation / live | 0 | 不接入真实 broker，不执行 simulation/live/live-readonly/small-live/scale-up。 |
| multifactor framework implementation | 0 | 不实现 FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪或策略准入包。 |
| Qlib / Alphalens / vnpy.alpha integration | 0 | 仅作为 CR-030 后续候选参考，不引入依赖或集成。 |

## 10. CP7 验证入口

S04 的验证应保持静态、离线、fixture-only：

```bash
uv run --python 3.11 pytest -q tests/test_cr025_backtrader_no_copy_guardrail.py
```

验证不得读取 `/home/hyde/download/backtrader/**`，不得运行 Backtrader，得出的结论只覆盖本文档合同、仓库内 vendored source 候选路径和当前测试的静态安全边界。
