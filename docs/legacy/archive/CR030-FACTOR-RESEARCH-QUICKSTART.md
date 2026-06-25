# CR030 因子研究快速开始

本文件是 CR-030 多因子研究历史归档入口。新用户优先阅读 [../components/MULTIFACTOR-RESEARCH.md](../components/MULTIFACTOR-RESEARCH.md) 和 [../scenarios/MULTIFACTOR-RESEARCH-TO-STRATEGY.md](../scenarios/MULTIFACTOR-RESEARCH-TO-STRATEGY.md)。它说明如何理解 FactorSpec 到 StrategyAdmissionPackage 的研究路径，不授权 QMT、simulation、live 或真实交易。

## 快速路径

| 步骤 | 目标 | 边界 |
|---|---|---|
| 定义因子 | 使用项目内部 `FactorSpec` / `FactorRunSpec` 描述因子。 | 不把外部框架对象作为 truth。 |
| 准备 panel / label | 使用带 lineage 的 factor panel 和 label window。 | 不触发 provider fetch 或 lake write。 |
| 单因子评价 | 输出 IC / RankIC / 分层收益 / turnover / cost / exposure。 | 不声明 simulation-ready 或 live-ready。 |
| 多因子组合 | 生成研究侧组合计划。 | 不自动下单。 |
| 准入包 | 形成模拟盘入口审查输入。 | 不等于真实运行授权。 |

当前真实 simulation operator 操作入口见 [../USER-MANUAL.md](../USER-MANUAL.md) 的 runner 模块。
