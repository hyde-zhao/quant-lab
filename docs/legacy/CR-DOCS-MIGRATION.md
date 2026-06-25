# CR 命名文档整改映射

本文件记录 `docs/` 中 CR 命名文档的整改结果。原则是：用户首选入口改为非 CR 命名；旧 CR 路径如已被新文档完整承接，则移入 `docs/legacy/archive/` 作为审计归档，不再作为用户阅读入口。

## 1. 顶层 CR 文档

| 原路径 | 当前状态 | 新入口 |
|---|---|---|
| `docs/CR138-RUNNER-QMT-AUTHORIZATION-RUNBOOK.md` | 已归档到 [archive/CR138-RUNNER-QMT-AUTHORIZATION-RUNBOOK.md](archive/CR138-RUNNER-QMT-AUTHORIZATION-RUNBOOK.md) | [../reference/RUNNER-QMT-AUTHORIZATION.md](../reference/RUNNER-QMT-AUTHORIZATION.md) |
| `docs/CR025-BACKTRADER-MODULE-REFERENCE.md` | 已归档到 [archive/CR025-BACKTRADER-MODULE-REFERENCE.md](archive/CR025-BACKTRADER-MODULE-REFERENCE.md) | [../reference/BACKTRADER-MODULE-REFERENCE.md](../reference/BACKTRADER-MODULE-REFERENCE.md) |
| `docs/CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md` | 已归档到 [archive/CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md](archive/CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md) | [../reference/RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md](../reference/RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md) |
| `docs/CR030-FACTOR-RESEARCH-QUICKSTART.md` | 已归档到 [archive/CR030-FACTOR-RESEARCH-QUICKSTART.md](archive/CR030-FACTOR-RESEARCH-QUICKSTART.md) | [../components/MULTIFACTOR-RESEARCH.md](../components/MULTIFACTOR-RESEARCH.md) 和 [../scenarios/MULTIFACTOR-RESEARCH-TO-STRATEGY.md](../scenarios/MULTIFACTOR-RESEARCH-TO-STRATEGY.md) |

## 2. Release CR 文档

原 `docs/release/` 下的 CR093、CR094、CR095 release note、deploy checklist、migration、rollback、feedback 普通文件已移入 [archive/release/](archive/release/)。

原 `docs/release/` 中指向外部 artifact repo 的 CR 命名 symlink 不纳入源码仓库的当前用户入口；如本机存在，应由 artifact repo 或本地 process 路由管理，不作为 `docs/release/` 下的正式文档。

## 3. 后续规则

后续新增用户文档不得再用 CR 编号作为主文件名；CR 编号只允许出现在过程证据、变更单、归档说明和必要的历史追溯中。组件说明放入 `components/`，操作案例放入 `scenarios/`，边界参考放入 `reference/`，历史件放入 `legacy/archive/`。
