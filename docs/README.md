# quant-lab 文档导航

本目录按“组件说明 + 场景案例 + 参考边界 + legacy 归档”组织。正式阅读入口是本文件和 [USER-MANUAL.md](USER-MANUAL.md)；CR 编号文档只作为历史审计引用，不再作为用户首选入口。

## 1. 组件文档

| 组件 | 文档 | 说明 |
|---|---|---|
| 数据与引擎 | [components/ENGINE.md](components/ENGINE.md) | 数据准备、标准化、质量、loader、portfolio、backtest、metrics。 |
| 实验与报告 | [components/EXPERIMENTS.md](components/EXPERIMENTS.md) | chapter 实验、参数扫描、候选输出、报告检查。 |
| 多因子研究 | [components/MULTIFACTOR-RESEARCH.md](components/MULTIFACTOR-RESEARCH.md) | FactorSpec、factor panel、单因子评价、多因子组合、策略准入包。 |
| QMT gateway | [components/QMT-GATEWAY.md](components/QMT-GATEWAY.md) | Windows S 端 gateway、C 端 client、env、health、capabilities、positions。 |
| Runner | [components/RUNNER.md](components/RUNNER.md) | 策略导入、runner operator、P1-P4、evidence、manual takeover。 |

## 2. 场景案例

| 场景 | 文档 | 读者 |
|---|---|---|
| 多因子策略研究：从数据准备到输出策略 | [scenarios/MULTIFACTOR-RESEARCH-TO-STRATEGY.md](scenarios/MULTIFACTOR-RESEARCH-TO-STRATEGY.md) | 研究员 / 策略开发者 |
| 多因子策略运行：策略导入、gateway、runner、对账 | [scenarios/MULTIFACTOR-SIMULATION-RUNNER-OPERATION.md](scenarios/MULTIFACTOR-SIMULATION-RUNNER-OPERATION.md) | 模拟盘操作者 |
| 日常运维：盘前、盘中、盘后、异常恢复 | [scenarios/DAILY-OPERATIONS.md](scenarios/DAILY-OPERATIONS.md) | 操作者 / 值守人员 |

## 3. 参考边界

| 参考 | 文档 | 说明 |
|---|---|---|
| QMT gateway 安装运行 | [QMT-GATEWAY-INSTALL.md](QMT-GATEWAY-INSTALL.md) | 保留顶层路径，供测试和历史引用读取。 |
| QMT C/S bridge | [QMT-C-S-BRIDGE-RUNBOOK.md](QMT-C-S-BRIDGE-RUNBOOK.md) | 保留顶层路径，记录 endpoint / HMAC / no-real-operation 边界。 |
| QMT stage activation | [QMT-SIMULATION-LIVE-RUNBOOK.md](QMT-SIMULATION-LIVE-RUNBOOK.md) | 保留顶层路径，记录 stage gate、approval、rollback。 |
| QMT incident | [QMT-INCIDENT-PLAYBOOK.md](QMT-INCIDENT-PLAYBOOK.md) | 保留顶层路径，记录 incident 和 recovery。 |
| Runner 授权边界 | [reference/RUNNER-QMT-AUTHORIZATION.md](reference/RUNNER-QMT-AUTHORIZATION.md) | 非 CR 命名的授权参考入口。 |
| Backtrader reference | [reference/BACKTRADER-MODULE-REFERENCE.md](reference/BACKTRADER-MODULE-REFERENCE.md) | 非 CR 命名的 Backtrader no-copy 参考入口。 |

## 4. CR 命名文档整改策略

CR 编号文档的整改原则：

1. 用户首选入口不使用 CR 编号命名。
2. 已被新文档完整承接的 CR 顶层路径移入 `legacy/archive/`。
3. 新增规范文档放入 `components/`、`scenarios/`、`reference/` 或 `legacy/`。
4. CR 文档只保留历史来源、归档原因和当前 canonical 入口。

映射表见 [legacy/CR-DOCS-MIGRATION.md](legacy/CR-DOCS-MIGRATION.md)。
