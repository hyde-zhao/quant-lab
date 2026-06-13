---
status: "draft-current-index"
version: "1.0"
feature_id: "FEAT-02"
source_matrix: "docs/design/FEATURE-DESIGN-MATRIX.md"
source_blueprint: "docs/design/BLUEPRINT.md"
change: "CR-031"
---

# Feature Design: market-data-lake

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-07 | meta-po | 新增生产级市场数据湖 Feature 设计索引 |

## Feature 摘要

| 项 | 内容 |
|---|---|
| Feature 目标 | 统一 `market_data/` 的生产级数据湖事实源、publish gate、quality/readiness、rollback 和只读消费边界 |
| Owner | FEAT-02 |
| 主要代码面 | `market_data/**` |
| 主要设计来源 | `process/HLD-DATA-LAKE.md`、`process/ARCHITECTURE-DECISION.md` ADR-013..022、ADR-030..035、ADR-048..054、ADR-062..066 |
| 非授权声明 | 本文不授权 provider fetch、真实 lake write、catalog publish、DuckDB 事实源写入或凭据读取 |

## Feature 边界与相邻对象

| 对象 | 本 Feature 负责 | 不负责 | 相邻 Feature / 模块 | 边界判定依据 |
|---|---|---|---|---|
| MarketDataRun / ManifestBatch | plan/run/normalize/validate/publish/replay 的 run 和 batch 审计 | 策略回测逻辑 | FEAT-01 | `process/HLD-DATA-LAKE.md` |
| DatasetCandidate / CatalogCurrentTruth | candidate、quality、readiness、publish、current pointer、rollback | 研究报告最终解释 | FEAT-03 / FEAT-08 | ADR-048、ADR-052、ADR-064 |
| AdjustmentView | raw + adj_factor 事实源、qfq/hfq/returns_adjusted 派生视图 | QMT 委托 / 成交执行价 | FEAT-06 | ADR-053、ADR-054 |
| ClaimBoundary | allowed / blocked / required_missing 的数据侧事实 | 运行授权 | FEAT-07 | CR-013..CR-030 |

## 输入 / 输出契约

| 方向 | 契约 |
|---|---|
| 输入 | 用户显式授权、source/interface allowlist、date range、dataset group、lake root、raw/manifest 或 candidate |
| 输出 | raw、manifest、canonical、gold、quality、readiness、catalog current pointer、release summary、claim boundary |
| 错误输出 | `required_missing`、`source_unresolved`、`quality_failed`、`resume_conflict`、`publish_blocked`、`authorization_missing` |

## 失败路径

| 失败点 | 行为 |
|---|---|
| 缺授权 | provider fetch、lake write、publish 全部 blocked |
| validate fail | 不得更新 current pointer，consumer 只能得到 unavailable / blocked claim |
| quality warn | exploratory 可用；production strict 默认 blocked，除非 publish policy 显式允许 |
| replay conflict | 返回 `resume_conflict`，不得覆盖已发布 current truth |
| DuckDB candidate 写事实源 | blocked；DuckDB 只能是只读候选能力 |

## 下游 Story / CR 映射

| 范围 | 消费方式 |
|---|---|
| CR004..CR010 | 数据湖基础能力和 Tushare-first 生产链路 |
| CR014 / CR018 | 全 A since-inception current truth、publish gate、release / rollback |
| CR017 | 复权双视图和 QMT raw 执行价隔离 |
| CR030 | 多因子研究只读 published data 和 blocked claims |

## Gotchas

- validate pass 不是 publish，publish 才能更新 current pointer。
- consumer 发现缺口只能返回 structured missing，不得自动补数。
- qfq/hfq 是研究视图，不是 QMT 执行价。
- DuckDB 只读不等于没有写风险，禁止把 `.duckdb` 作为事实源。

