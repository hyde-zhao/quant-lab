---
status: "current-index"
version: "1.1"
change: "CR-046"
legacy_sources:
  - "process/HLD.md"
  - "process/HLD-DATA-LAKE.md"
  - "process/HLD-QMT-TRADING.md"
current_change_sources:
  - "docs/design/HLD-CR046-QMT-MINIQMT-DUAL-TARGET-FRAMEWORK.md"
---

# HLD Current Index

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-07 | meta-po | 新增 HLD 长期索引，保留 legacy HLD 为审计来源 |
| 1.1 | 2026-06-13 | meta-po | 按 CR-046 增补双目标策略交付框架 HLD 入口 |

## 定位

本文不是新的完整 HLD，也不替代 `process/HLD*.md`。它是长期阅读入口，用于说明当前项目三类 HLD 的职责分布和消费顺序。

## HLD 分区

| HLD | 职责 | 当前用途 |
|---|---|---|
| `process/HLD.md` | 本地研究、轻量回测、研究消费、报告、多因子闭环、Backtrader optional reference、Stage6 admission 和 QMT gateway 相关主线索引 | 主研究 / 消费层 HLD legacy source |
| `process/HLD-DATA-LAKE.md` | 生产级市场数据湖、P0/P1 dataset、catalog current truth、publish gate、DuckDB readonly candidate、复权双视图、production current truth closure | 数据生产 / 数据事实源 HLD legacy source |
| `process/HLD-QMT-TRADING.md` | QMT 交易接入、OMS、adapter、broker lake、stage gate、runbook、reconciliation、kill switch、QMT C/S bridge 交易治理侧 | QMT 交易治理 HLD legacy source |
| `docs/design/HLD-CR046-QMT-MINIQMT-DUAL-TARGET-FRAMEWORK.md` | QMT terminal + MiniQMT runner 双目标策略交付框架、策略包契约、验证框架、MiniQMT runner 安装设计和后续 CR 门禁 | CR046 当前 CP3 审查主 HLD |

## 当前架构摘要

| 层 | Owner Feature | 当前边界 |
|---|---|---|
| 数据生产 | FEAT-02 | 只有用户显式授权的数据湖生产链路可触发 provider / lake write / publish；consumer 不自动补数 |
| 研究消费 | FEAT-01 / FEAT-03 | 只读 published data、quality/readiness、claim boundary；输出研究报告、factor evaluation 和 admission package |
| 执行语义 | FEAT-04 | lightweight 为默认主路径；Backtrader / external frameworks 只作 optional reference / Spike |
| QMT gateway | FEAT-05 | 当前 CR-020 只到 Windows/QMT `query_positions` readonly manual validation，不授权交易或 simulation/live |
| 交易治理 | FEAT-06 | CR-015/016 已有 shadow / dry-run / mock / runbook 边界，后续 CR-021..024 才可能逐级解禁 |
| 安全授权 | FEAT-07 | 所有真实操作必须有独立授权；文档、健康检查、Story verified 不构成授权 |
| 双目标策略交付 | FEAT-09 | CR046 只定义 QMT terminal 与 MiniQMT runner 策略交付框架、验证框架和安装设计；不交付具体策略，不执行 runtime |

## 消费规则

| 场景 | 默认读取 |
|---|---|
| 判断 Feature 边界 | `docs/design/BLUEPRINT.md` |
| 判断领域对象和状态 | `docs/design/DOMAIN-MAP.md` |
| 判断允许 / 禁止依赖 | `docs/design/DEPENDENCY-MAP.md` |
| 深入 HLD 细节 | 对应 `process/HLD*.md` |
| 审查 CR046 双目标策略交付框架 | `docs/design/HLD-CR046-QMT-MINIQMT-DUAL-TARGET-FRAMEWORK.md` |
| 判断 ADR | `docs/design/ARCHITECTURE-DECISION.md` + `process/ARCHITECTURE-DECISION.md` |
| 判断 Story 范围 | `process/STORY-BACKLOG.md`、`process/stories/*.md` |

## 不授权项

本文不授权 provider fetch、lake write、catalog publish、DuckDB 事实源写入、gateway 启动、端口绑定、QMT / MiniQMT / XtQuant 调用、真实 `.env` 读取、账户查询、交易、撤单、simulation、live_readonly、small_live、scale_up 或 broker lake 写入。
