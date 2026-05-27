# 回测平台演进路线

## 当前定位

`local_backtest` 是本地 A 股日频研究回测与数据可信层，不是 JoinQuant API 兼容层，也不是完整实盘交易系统。它的主价值在于把数据获取、数据湖、质量门禁、lineage、复权口径、PIT 边界和本地回测结果固化为可复现研究链路。

当前主干继续保留三层职责：

| 层 | 职责 |
|---|---|
| `market_data/` | 数据湖、catalog、quality、lineage、复权/PIT 契约和只读 reader |
| `engine/` | 轻量日频回测、指标、报告、候选筛选和偏差审计 |
| `strategies/` | 可测的策略纯函数接口和示例策略 |

## 演进原则

1. 数据可信层优先于回测引擎替换。
2. 当前轻量 engine 继续作为默认主路径。
3. 开源框架以可选后端或加速器方式集成，不接管数据湖、quality gate、catalog 或 lineage。
4. 回测、扫描、候选筛选和实验消费路径默认离线，不隐式联网、不隐式补数。
5. 聚宽验证作为真实性对照，不作为必须完全复刻的 API 目标。
6. 缺少真实数据、质量未通过或 benchmark policy 未确认时，消费层返回结构化不可用和 remediation spec，不自动执行数据层 job。

## 推荐方向

主干继续在当前骨架上完善，不整体迁移到单一开源框架。

| 对象 | 定位 | 使用边界 |
|---|---|---|
| 当前轻量 engine | 默认主路径 | 负责日频研究、候选筛选、报告和可解释结果 |
| Backtrader | 可选事件驱动后端 | 负责更真实的订单、成交、仓位、分钟级验证和轻量 engine 对照 |
| VectorBT | 可选扫描加速器 | 负责大规模参数扫描和向量化信号研究，不定义最终交易语义 |
| Qlib | 未来因子/机器学习研究候选 | 仅在机器学习因子平台成为主目标后单独评估 |
| LEAN | 未来实盘/多资产平台候选 | 仅在实盘、模拟盘或多资产统一引擎成为主目标后单独评估 |
| Zipline Reloaded | 暂缓 | 当前 A 股数据 bundle 和本项目契约适配成本高，短期不优先 |

## Backtrader 与 Qlib 引入边界

> 本节记录 2026-05-26 对 Backtrader 与 Microsoft Qlib 的引入评估结论。评估依据包括当前 `local_backtest` 架构、`process/ARCHITECTURE-DECISION.md` 的 ADR-023/024、已实现的 `engine/backtrader_adapter.py`、Qlib 本地 clone `/tmp/qlib-microsoft-20260526`，以及外部分析报告 `work/studies/quant-trading/sources/microsoft-qlib-analysis-report.md`。

### 总体结论

Backtrader 与 Qlib 可引入的能力不属于同一层。

| 框架 | 最适合补齐的能力 | 与本项目关系 | 推荐形态 |
|---|---|---|---|
| Backtrader | 事件驱动回测、订单、成交、仓位、broker、commission、slippage、分钟级验证 | 与当前轻量 engine 的回测/执行层相邻，结构贴合度较高 | 进程内 optional backend，延迟 import，只消费 clean feed |
| Qlib | 机器学习因子研究 workflow、Alpha158/Alpha360、Model Zoo、IC/Rank IC、MLflow artifact、标准 benchmark | 与当前数据可信层差异较大，平台级集成会冲突事实源 | 进程外 sandbox / optional benchmark runner，通过 exporter 交换派生产物 |

核心判断：

- Backtrader 可以继续做实为“交易执行真实性对照层”，但不得替代默认轻量 engine。
- Qlib 不适合直接集成平台本体，也不适合接管本项目数据层；短期只吸收研究范式，必要时通过隔离 exporter / runner 做 ML benchmark。
- 两者都不能成为 `market_data` 的事实源，不能接管 quality gate、catalog、lineage、PIT、复权口径或 benchmark policy。
- `research_input_v1` / `ResearchDataset` 应作为所有外部框架的统一上游消费合同：Backtrader 消费 clean feed，Qlib 消费只读导出的派生 Qlib 数据。

推荐的统一外部框架接入形态：

```text
market_data published catalog / canonical / gold
        |
        v
research_input_v1 / ResearchDataset
        |
        +--> lightweight engine（默认主路径）
        |
        +--> Backtrader clean feed adapter（交易执行真实性对照）
        |
        +--> Qlib export adapter（隔离 ML benchmark runner）
        |
        +--> future VectorBT panel adapter（扫描加速）
```

### Backtrader 可引入部分

Backtrader 的价值集中在“把同一份 clean feed 放进更接近真实交易执行语义的事件驱动后端中验证”。它不负责数据生产、PIT、复权、质量判定或 benchmark 补齐。

| 可引入部分 | 价值 | 优先级 | 边界 |
|---|---|---|---|
| Backtrader `Cerebro` runner | 提供标准事件循环和 broker 容器 | P1 | 仅显式 `backend="backtrader"` 时运行 |
| clean OHLCV DataFeed | 将 canonical/gold 派生 feed 映射到 Backtrader | P1 | feed 必须已通过 quality/PIT/复权 gate |
| commission / slippage / min cost | 验证成本、滑点、最低佣金、印花税对收益的影响 | P1 | 成本配置必须写入报告 metadata |
| broker cash / position | 输出现金、持仓、调仓后净值 | P1 | 不覆盖轻量 engine 结果，只做对照 |
| orders / trades / positions | 补齐订单、成交、持仓明细 | P1 | 输出到隔离对照报告，不写数据湖 |
| strategy wrapper | 将本项目 score / target weights 转成 Backtrader 下单逻辑 | P2 | 策略信号仍由 `strategies/` 或实验层生成 |
| minute feed validation | 分钟级执行和日频组合联动验证 | P2/P3 | 依赖分钟数据、VWAP/成交量等字段补齐 |
| analyzer / risk supplement | 作为额外风险指标来源 | P3 | 指标定义需与本项目报告口径并列说明 |

Backtrader 禁止承担的职责：

- 不读取 connector、runtime、storage、raw、manifest 或 `.env` / token。
- 不联网、不触发 fetch/backfill、不写真实 lake。
- 不生成 PIT，不计算复权因子，不修补缺失 benchmark。
- 不在 quality fail、PIT fail、复权口径冲突或 `available_at > decision_time` 时继续运行。
- 不替代 `engine.backtest` 默认主路径，不覆盖轻量 engine 结果。

Backtrader 后续做实路径：

1. 固化 clean feed contract：OHLCV、calendar、benchmark metadata、quality/PIT/adjustment gate、cost config。
2. 将 adapter 从当前 smoke 级别推进到真实 Backtrader data feed + broker run。
3. 输出 orders、trades、positions、equity curve、metrics，并与轻量 engine 在同一报告中并排对照。
4. 在分钟级数据、真实 VWAP / open / high / low、交易状态字段补齐后，再扩展分钟级执行验证。

### Qlib 可引入部分

Qlib 的价值集中在“机器学习量化研究工程化”：标准 workflow、数据切分、特征/标签、模型训练、预测记录、信号分析、组合回测和实验 artifact。它不适合成为本项目数据层或默认回测框架。

| 可引入部分 | 引入方式 | 价值 | 优先级 |
|---|---|---|---|
| workflow 纪律 | 借鉴到本项目实验配置 | 明确 dataset、feature_set、label、split、model、cost、benchmark_policy、claims_policy | P1 |
| train/valid/test + fit window | 借鉴到 ML 实验规范 | 防止标准化、processor、模型选择污染未来数据 | P1 |
| Signal / IC / Portfolio artifact 分层 | 借鉴报告结构 | 区分 prediction、signal analysis、portfolio analysis | P1 |
| IC / Rank IC / ICIR | 与本项目指标口径对照 | 强化预测信号质量评估 | P1 |
| Alpha158 / Alpha360 | Qlib sandbox 中跑 | 提供成熟 ML 因子 baseline | P2 |
| LightGBM / Model Zoo benchmark | Qlib sandbox 中跑 | 横向比较 ML 模型和特征集 | P2 |
| TopkDropoutStrategy | Qlib 内部对照策略 | 将预测分数转换为组合回测的标准 baseline | P2 |
| MLflow recorder | 后续可选实验记录后端 | 管理模型、预测、label、参数和 artifact | P3 |
| Expression Engine / cache | 长期参考 | 因子表达式和大规模缓存 | P3，当前不直接拆代码 |

Qlib 禁止承担的职责：

- 不作为 `market_data` 的事实源；Qlib `.bin` 只能是派生验证数据。
- 不接管 quality gate、catalog、lineage、PIT、复权、benchmark policy 或 `allowed_claims` / `blocked_claims`。
- 不在默认环境中 import Qlib，不把 `pyqlib` 加入默认依赖。
- 不让 `provider_uri` 成为本项目主运行配置。
- 不用社区 Qlib 数据证明本项目策略有效。
- 不用 Qlib 结果覆盖本项目轻量 engine 或 Backtrader 对照结果。

Qlib 后续验证路径分四级：

| 级别 | 目标 | 数据 | 输出 | 可声明结论 |
|---|---|---|---|---|
| Q0：外部 smoke | 验证 Qlib 能跑通官方 workflow | 外部 Qlib 社区/示例数据 | `mlruns`、pred、label、IC、portfolio artifact | 仅声明 Qlib 工具链可运行 |
| Q1：close-only export | 验证本项目数据可安全导出到 Qlib | 显式本地 parquet 或 quality pass 的 close/volume/amount | close proxy workflow、IC/Rank IC | 仅声明转换链路和信号评估可运行，真实 benchmark/VWAP/PIT 仍 blocked |
| Q2：canonical/gold exporter | 形成只读 Qlib 派生数据 | published canonical/gold、catalog、quality pass | Qlib `.bin`、export manifest、对照报告 | 可做同区间、同股票池、同成本假设的 ML benchmark 对照 |
| Q3：optional ML backend | 机器学习因子平台成为主目标时评估 | P0 数据补齐后的生产级研究输入 | Alpha158/Alpha360、Model Zoo、TopkDropout、MLflow artifact | 可评估是否作为长期 ML 研究后端 |

Qlib exporter 的最低验收边界：

- 输入只读，默认不读取旧 `data/**`，不读取 `.env`、token、cookie、session。
- 输出只能写入 `/tmp/qlib-*` 或用户显式指定的隔离目录，不写真实 lake。
- `export_manifest.json` 必须记录源 dataset、date range、symbol count、field list、quality status、lineage/source run id、known limitations。
- 缺少真实 `open/high/low/vwap` 时，不得声明真实执行价或完整 Alpha158 生产结论；`real_vwap_execution`、`vwap_fill_claim`、`pit_universe_research` 等必须按实际数据状态 blocked。
- Qlib 预测结果导回本项目时，只能作为 `score` / benchmark artifact，由本项目报告层重新套用 `research_input_v1` metadata 和 claims gate。

### Backtrader 与 Qlib 分工对照

| 本项目问题 | 优先方向 | 原因 |
|---|---|---|
| 默认日频策略筛选、候选生成、可解释报告 | 轻量 engine | 当前主路径透明、依赖少、易测试 |
| 订单、成交、仓位、现金、滑点、佣金、分钟级执行 | Backtrader | Backtrader 与交易执行层相邻，能补轻量 engine 的执行语义 |
| 大规模参数扫描和纯信号矩阵扫描 | VectorBT | 向量化扫描更适合参数组合爆炸场景 |
| ML 因子 benchmark、Alpha158/Alpha360、Model Zoo | Qlib sandbox | Qlib 在 ML 研究 workflow 上成熟，但必须隔离事实源 |
| 数据湖、catalog、quality、lineage、PIT、复权 | 本项目 `market_data` | 这是本项目核心价值，不能外包给外部框架 |
| 真实 benchmark、PIT universe、交易状态、行业、市值、容量等 P0 数据缺口 | 本项目数据层优先补齐 | Backtrader 和 Qlib 都依赖这些输入，不能替代它们 |

## 阶段路线

### Phase 1：补齐日频研究可信度

目标：让当前轻量 engine 成为可靠的聚宽验证前筛选器。

范围：

- 将真实 benchmark 接入指标计算。
- 增加 Alpha、Beta、信息比率、Sortino、策略波动率、基准波动率、超额收益和超额收益回撤。
- 成本模型补最低佣金、买卖分侧费率、100 股整数手和可配置滑点模型。
- 将涨跌停、停牌、交易状态接入 `run_backtest` 主路径。
- 将 OHLCV、volume、amount、high_limit、low_limit、paused 等字段纳入主输入契约。
- 报告明确区分 `hs300_index`、`proxy_baseline` 和缺失 benchmark 的结构化原因。

### Phase 2：Backtrader 可选后端做实

目标：支持事件驱动和更真实订单语义，同时保持轻量 engine 为默认主路径。

范围：

- 从 canonical/gold clean feed 构建 Backtrader data feed。
- 接入 commission、slippage、cash、position 和 broker 口径。
- 输出 orders、trades、positions、equity curve 和 metrics。
- 与轻量 engine 做同策略、同数据、同成本假设的对照报告。
- 支持分钟级策略验证，但不让 Backtrader 读取 connector、token、raw/manifest 或触发 backfill。

### Phase 3：VectorBT 加速参数扫描

目标：提升大规模参数扫描效率。

范围：

- 将纯信号策略映射为向量化扫描。
- 保持指标、候选报告和 CSV schema 与当前 engine 对齐。
- 仅消费已通过 quality gate 的本地数据。
- 不改变数据湖、quality gate、PIT、复权和 benchmark 契约。

### Phase 4：因子研究与归因

目标：补齐阶段三资料中的因子分析能力。

范围：

- IC / Rank IC。
- 分组收益和分层净值。
- 因子覆盖率、换手和稳定性。
- 因子暴露、风格偏差和基准对照。
- 若机器学习因子研究成为主目标，再单独评估 Qlib，而不是直接替换当前回测主干。

### Phase 5：平台级能力评估

目标：在需求明确变成实盘、多资产或统一交易平台时，重新评估平台选型。

范围：

- 评估 LEAN 或独立实盘系统，不把实盘能力混入当前轻量研究主干。
- 评估是否需要完整订单生命周期、持久化订单簿、模拟盘、实盘 broker 接口和多资产风控。
- 明确数据授权、凭据管理、部署、监控和回滚策略。

## 不做事项

短期不做：

- 不把当前项目整体迁移到 Backtrader、VectorBT、Zipline、Qlib 或 LEAN。
- 不复刻完整 JoinQuant API。
- 不做实盘交易。
- 不让回测路径隐式联网或隐式补抓数据。
- 不把真实行情数据、token、凭据或私有路径提交到 Git。
- 不让开源后端绕过 `market_data` 的 quality gate、catalog、lineage、PIT 或复权契约。

## 决策表

| 场景 | 方向 |
|---|---|
| 日频策略筛选 | 当前轻量 engine |
| 更真实订单和分钟级验证 | Backtrader optional backend |
| 大规模参数扫描 | VectorBT optional backend |
| 因子分析和归因 | 当前框架先补 IC、分组收益、风格暴露；必要时评估 Qlib |
| ML 模型横向 benchmark | Qlib isolated runner，先 smoke 后 exporter |
| ML 预测分数进入交易执行对照 | 本项目 score -> Backtrader clean feed / Qlib TopkDropout 对照，结果并列呈现 |
| 机器学习因子平台 | 单独评估 Qlib |
| 实盘 / 多资产 / 专业交易平台 | 单独评估 LEAN 或独立实盘系统 |

## 切换条件

出现以下情况时，再评估扩大开源框架占比：

| 触发条件 | 评估方向 |
|---|---|
| 自研订单撮合复杂度明显超过 Backtrader 适配成本 | 扩大 Backtrader 后端职责 |
| 分钟级策略成为主场景 | 优先做 Backtrader clean feed 和事件循环验证 |
| 参数扫描耗时成为主要瓶颈 | 接入 VectorBT 扫描加速 |
| 需要标准 ML workflow、Alpha158/Alpha360 或 Model Zoo 横向比较 | 先做 Qlib isolated runner，不进入默认依赖 |
| 因子机器学习研究成为主目标，且 P0 数据缺口已补齐 | 单独评估 Qlib optional ML backend |
| Qlib benchmark 在同数据、同区间、同成本口径下稳定提供增量 | 评估 canonical/gold -> Qlib exporter 是否固化 |
| 需要实盘、模拟盘或多资产统一引擎 | 单独评估 LEAN 或独立实盘平台 |

## 文档与决策关系

| 文档 | 角色 |
|---|---|
| `docs/ROADMAP.md` | 长期演进路线入口 |
| `README.md` | 项目入口摘要和 roadmap 链接 |
| `process/ARCHITECTURE-DECISION.md` | 已确认架构决策留痕 |
| `process/STORY-BACKLOG.md` / `process/DEVELOPMENT-PLAN.yaml` | 具体可执行任务和阶段计划 |
| `docs/USER-MANUAL.md` | 当前已实现能力的用户操作说明，不承载未来路线正文 |
