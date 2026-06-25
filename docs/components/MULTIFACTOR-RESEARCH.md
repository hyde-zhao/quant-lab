# 组件说明：多因子研究

多因子研究组件覆盖 FactorSpec、FactorRunSpec、factor panel、label window、单因子评价、多因子组合和 StrategyAdmissionPackage。它输出“策略准入输入”，不输出真实交易许可。

## 1. 核心对象

| 对象 | 说明 | 检查 |
|---|---|---|
| `FactorSpec` | 因子定义、方向、依赖和 lineage。 | 字段完整、方向明确、无外部 truth 混入。 |
| `FactorRunSpec` | 一次因子运行的窗口、数据源和权限计数。 | run_id、date range、permission counters。 |
| factor panel | 因子值矩阵。 | no-lookahead、缺失、winsorize、zscore。 |
| label window | 未来收益或目标标签窗口。 | label 不重叠、available_at 合法。 |
| evaluation report | IC / RankIC / 分层收益 / turnover / cost / exposure。 | 指标齐全，blocked claims 优先。 |
| portfolio plan | 多因子组合权重和候选持仓。 | max weight、turnover、capacity、risk。 |
| admission package | 模拟盘入口审查输入。 | 证据 refs、限制、授权状态、handoff。 |

## 2. 输出边界

多因子研究的出口是 `StrategyAdmissionPackage` 或等价策略准入包。它可以交给 runner 做导入检查，但不能直接下单，也不能绕过 QMT gateway、stage gate、risk gate 或 reconciliation。

## 3. 必要检查

| 检查 | 必须满足 |
|---|---|
| 数据 | 使用 current truth 或 clean feed，PIT / quality pass。 |
| 因子 | 因子方向、可用时点、异常值处理和 lineage 可追踪。 |
| 标签 | label window 与 decision time 不泄漏。 |
| 单因子 | IC / RankIC / 分层收益 / turnover / cost / exposure 有结果或 unavailable。 |
| 多因子 | 组合规则、权重约束、换手约束和风险摘要明确。 |
| 准入 | 不声明 QMT-ready / simulation-ready，除非后续 runner gate 通过。 |
