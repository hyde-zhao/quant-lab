---
story_id: "CR010-S02-prices-adj-factor-history-backfill-loop"
title: "prices + adj_factor 历史回补闭环"
story_slug: "prices-adj-factor-history-backfill-loop"
lld_version: "1.0"
tier: "L"
status: "confirmed"
confirmed: true
implementation_allowed: true
created_by: "Codex direct-main-thread"
created_at: "2026-05-22T15:13:28+08:00"
confirmed_by: "user"
confirmed_at: "2026-05-22T15:13:28+08:00"
approval_text: "你可以默认人工审批通过，继续推进项目。"
cp5_manual_review: "checkpoints/CP5-CR010-DL-BATCH-A-LLD-BATCH.md"
cp5_batch: "CR010-DL-BATCH-A"
change_id: "CR-010"
shared_fragments:
  - "process/HLD-DATA-LAKE.md#41-p0-dataset"
  - "process/HLD-DATA-LAKE.md#43-available_at_rule"
open_items: 0
---

# LLD: CR010-S02-prices-adj-factor-history-backfill-loop - prices + adj_factor 历史回补闭环

## 1. Goal

修改 P0 `prices` 与 `adj_factor` canonical/validation/catalog 合同，确保历史行情和复权因子可以成对离线发布，且 qfq adjusted 字段、`daily_close_fact` 可用时点、OHLC/重复键/coverage/复权一致性都有可测试 gate。

## 2. Requirements（Functional / Non-Functional）

### 2.1 Functional

- `prices` canonical 必含 OHLCV、amount、adjusted close 或 adjustment policy metadata、source/interface/run_id、`available_at`、`available_at_rule`、lineage checksum。
- `adj_factor` 独立 canonical 必含 `adj_factor`、`adjustment_policy`、source/interface/run_id、`available_at`、`available_at_rule`。
- validate 检查 duplicate key、OHLC 关系、负数/零价格、coverage、future availability、adj_factor key mismatch 和 adjustment policy conflict。
- publish metadata 暴露 date range、quality/readiness/pit、known limitations。

### 2.2 Non-Functional

- 不读取旧 `data/**` 或 legacy report 证明 coverage。
- 不写真实 lake；全部使用 tmp lake/fixture。
- 字段缺失必须 fail-fast，不用默认值伪造 current truth。

## 3. 模块拆分与职责

| 模块 / 文件组 | 职责 | 说明 |
|---|---|---|
| `market_data/contracts.py` | 定义 `prices` / `adj_factor` schema 和 available_at_rule | exact dataset contract |
| `market_data/normalization.py` | 从 raw/manifest 生成 canonical | 复用现有 adj_factor lookup |
| `market_data/validation.py` | 执行 quality/readiness 校验 | coverage denominator 依赖 trade_calendar |
| `market_data/catalog.py` | publish metadata | 记录 lineage 与 limitations |
| `market_data/readers.py` | strict/exploratory 读取策略 | fail/warn 行为与 S01 一致 |
| `tests/test_market_data_multidataset_quality_readers.py` | 多 dataset 单测 | 扩展 prices/adj_factor 场景 |

## 4. 代码结构与文件影响范围

| 动作 | 文件路径 | 变更内容 |
|---|---|---|
| 修改 | `market_data/contracts.py` | 补齐 `prices`、`adj_factor` required fields 与 available_at_rule 常量 |
| 修改 | `market_data/normalization.py` | 确保 `adj_factor` 独立 canonical 与 `prices` 复权 lookup 一致 |
| 修改 | `market_data/validation.py` | 增加 OHLC、重复键、coverage、adjustment consistency 检查 |
| 修改 | `market_data/catalog.py` | publish 时写入 dataset 级 readiness 与 limitation |
| 修改 | `tests/test_market_data_multidataset_quality_readers.py` | 增加 S02 fixture |

## 5. 数据模型与持久化设计

| 对象 / 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `prices.trade_date` | date | key | 交易日 |
| `prices.symbol` | str | key | 股票代码 |
| `open/high/low/close` | float | positive, OHLC relation | 行情字段 |
| `volume/amount` | float | non-negative | 成交字段 |
| `available_at_rule` | str | `daily_close_fact` | 日频价格事实 |
| `adj_factor.adj_factor` | float | positive | 复权因子 |
| `adjustment_policy` | str | exact match | 默认 qfq |
| `lineage_raw_checksum` | str | non-empty | 审计字段 |

## 6. API / Interface 设计

| 接口 / 入口 | 输入 | 输出 | 调用方 | 说明 |
|---|---|---|---|---|
| `normalize_dataset(prices)` | raw daily + manifest | prices canonical | CLI normalize | 不联网 |
| `normalize_dataset(adj_factor)` | raw adj_factor + manifest | adj_factor canonical | CLI normalize | 独立 canonical |
| `validate_dataset(prices)` | prices canonical + optional calendar/adj | quality candidate | CLI validate | 复权与 OHLC gate |
| `read_dataset(prices)` | published catalog + policy | DataFrame/metadata | consumer | 只读 publish |

## 7. 核心处理流程

1. `normalize` 读取 fixture raw/manifest，生成 `prices` 与 `adj_factor` canonical。
2. `validate` 先校验 required fields 与 duplicate key。
3. `validate` 检查 OHLC、价格非负、coverage denominator、`available_at_rule`。
4. `validate` 检查 `prices` 与 `adj_factor` 的 key/adjustment_policy 一致性。
5. `publish` 写 current truth metadata，reader 按 policy 消费。

## 8. 技术设计细节

- 关键算法 / 规则：duplicate key 为 `(trade_date, symbol)`；OHLC 要求 high >= max(open, close, low)，low <= min(open, close, high)。
- 依赖选择与复用点：复用现有 normalization dataclass 和 pandas 校验工具。
- 兼容性处理：保留已有 prices fixture；新增字段缺失时在 strict validation 中 fail。
- 图示类型选择：不需要图示，流程少于 3 个主要分支。

## 9. 安全与性能设计

| 维度 | 设计措施 | 验证方式 |
|---|---|---|
| 安全 | 不从旧 `data/**` 推导 coverage | 单测只使用 tmp lake |
| 安全 | 不输出 token 或真实路径 | CLI 输出断言 |
| 性能 | DataFrame 校验按 dataset 分组向量化 | 小 fixture 单测 |

## 10. 测试设计

| 测试场景 | 前置条件 | 操作 | 预期结果 | 验证方式 |
|---|---|---|---|---|
| prices canonical required fields | raw fixture | normalize + validate | PASS | pytest |
| adj_factor 独立 canonical | raw fixture | normalize adj_factor | canonical 字段完整 | pytest |
| duplicate key fail | 重复 key fixture | validate | quality fail | pytest |
| OHLC fail | high/low 异常 fixture | validate | quality fail | pytest |
| adjustment conflict fail | policy 不一致 | validate | fail | pytest |
| publish metadata | pass candidate | publish | catalog metadata 完整 | pytest |

## 11. 实施步骤

| TASK-ID | 动作 | 目标文件 | 详细描述 | 对应测试 |
|---|---|---|---|---|
| CR010-S02-T1 | 修改 | `market_data/contracts.py` | 补齐 fields 与 available_at_rule | required fields |
| CR010-S02-T2 | 修改 | `market_data/normalization.py` | 支持/强化 adj_factor canonical | adj_factor canonical |
| CR010-S02-T3 | 修改 | `market_data/validation.py` | 增加 OHLC、重复键、coverage、复权一致性校验 | duplicate/OHLC/adjustment |
| CR010-S02-T4 | 修改 | `market_data/catalog.py` | 写 readiness metadata | publish metadata |
| CR010-S02-T5 | 修改 | `tests/test_market_data_multidataset_quality_readers.py` | 增加 fixture 覆盖 | 全部 |

## 12. 风险、难点与预研建议

| 风险 / 难点 | 影响 | 缓解措施 / 预研建议 |
|---|---|---|
| calendar 缺失导致 coverage 不完整 | 误判长期行情质量 | 标记 denominator missing，S03 补齐 calendar |
| adj_factor 与 prices 日期不完全一致 | adjusted price 错误 | key mismatch fail 或 limitation |
| 旧 fixture 字段不足 | 测试回归 | 为旧 fixture 添加最小 source metadata |

### OPEN / Spike 跟踪

| ID | 类型（OPEN / Spike） | 问题 | 下一动作 | 责任方 |
|---|---|---|---|---|
| 无 | OPEN | 无阻断项 | 不适用 | 不适用 |

## 13. 回滚与发布策略

- 发布方式：作为 CR010-DL-BATCH-A 的 P0 dataset 合同增强发布。
- 回滚触发条件：旧 reader 无法读取已发布 prices、validate 错误阻断正常 pass fixture、metadata 缺失。
- 回滚动作：回退 S02 对 contracts/normalization/validation/catalog 的变更，保留 S01 publish gate。

## 14. Definition of Done

- [x] LLD 14 节完成。
- [ ] `prices` 与 `adj_factor` canonical required fields 测试通过。
- [ ] duplicate/OHLC/adjustment conflict 测试通过。
- [ ] publish metadata 包含 required catalog fields。
