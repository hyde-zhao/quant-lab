---
story_id: "CR010-S03-hs300-index-trade-calendar-backfill-loop"
title: "hs300_index + trade_calendar 历史回补闭环"
story_slug: "hs300-index-trade-calendar-backfill-loop"
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
  - "process/HLD-DATA-LAKE.md#7-消费边界"
open_items: 0
---

# LLD: CR010-S03-hs300-index-trade-calendar-backfill-loop - hs300_index + trade_calendar 历史回补闭环

## 1. Goal

修改 `hs300_index` 与 `trade_calendar` 的 canonical/validation/readers，确保真实 benchmark 与交易日分母分离、可发布、可审计；缺真实 `hs300_index` 时返回 typed missing，不使用 proxy 填充。

## 2. Requirements（Functional / Non-Functional）

### 2.1 Functional

- `hs300_index` canonical 必含 index_code、OHLC、pre_close、pct_chg、volume、amount、benchmark_kind、source lineage、`available_at_rule=daily_close_fact`。
- `trade_calendar` canonical 必含 trade_date、exchange、is_open、pretrade_date、source lineage、`available_at_rule`。
- coverage denominator 使用 `trade_calendar.is_open=true`。
- benchmark resolver 缺真实 published `hs300_index` 时返回 `required_missing` 或 proxy separation，不自动 backfill。

### 2.2 Non-Functional

- 不联网、不写真实 lake。
- 不读取旧 `data/**` 证明 benchmark/calendar。
- `hs300_index` 与 proxy 字段命名严格隔离。

## 3. 模块拆分与职责

| 模块 / 文件组 | 职责 | 说明 |
|---|---|---|
| `market_data/contracts.py` | 定义 index/calendar schema | exact dataset fields |
| `market_data/normalization.py` | 生成 canonical | 不用 proxy |
| `market_data/validation.py` | calendar denominator 和 index quality | open dates coverage |
| `market_data/readers.py` | benchmark/calendar reader | typed missing |
| `tests/test_market_data_normalization_validation_readers.py` | 回归与新增测试 | 覆盖 resolver separation |

## 4. 代码结构与文件影响范围

| 动作 | 文件路径 | 变更内容 |
|---|---|---|
| 修改 | `market_data/contracts.py` | 补齐 hs300_index/trade_calendar required fields |
| 修改 | `market_data/normalization.py` | 保持真实 index 与 proxy 隔离 |
| 修改 | `market_data/validation.py` | coverage denominator 仅用 open trade dates |
| 修改 | `market_data/readers.py` | 缺 published benchmark 返回 typed failure |
| 修改 | `tests/test_market_data_normalization_validation_readers.py` | 增加 S03 场景 |

## 5. 数据模型与持久化设计

| 对象 / 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `hs300_index.trade_date` | date | key | 交易日 |
| `hs300_index.index_code` | str | key | 默认 `000300.SH` |
| `benchmark_kind` | str | `hs300_price_index` | 不用 proxy |
| `available_at_rule` | str | `daily_close_fact` | 日频指数 |
| `trade_calendar.exchange` | str | key | 交易所 |
| `trade_calendar.is_open` | bool | required | coverage denominator |
| `trade_calendar.pretrade_date` | date | nullable | 前一交易日 |

## 6. API / Interface 设计

| 接口 / 入口 | 输入 | 输出 | 调用方 | 说明 |
|---|---|---|---|---|
| `normalize_dataset(hs300_index)` | raw index | canonical | CLI | 不联网 |
| `normalize_dataset(trade_calendar)` | raw calendar | canonical | CLI | 不联网 |
| `validate_dataset(hs300_index)` | canonical + calendar | quality | CLI | coverage/gap |
| `read_dataset(hs300_index)` | published catalog | data or typed failure | benchmark resolver | 缺失 required_missing |

## 7. 核心处理流程

1. normalize 生成 `hs300_index` 与 `trade_calendar` canonical。
2. validate calendar 的 open dates。
3. validate hs300_index 对 open dates 的 coverage。
4. publish 后 benchmark resolver 读取真实 `hs300_index`。
5. 缺失时 resolver 返回 typed missing，不使用 proxy。

## 8. 技术设计细节

- 关键规则：coverage denominator 只来自 `trade_calendar.is_open=true`。
- 依赖复用点：复用现有 benchmark reader/result schema。
- 兼容性处理：legacy proxy 字段保留为 proxy_baseline，不映射到 hs300_index。
- 图示类型选择：不需要图示。

## 9. 安全与性能设计

| 维度 | 设计措施 | 验证方式 |
|---|---|---|
| 安全 | 不触发 backfill | monkeypatch provider 不被调用 |
| 安全 | proxy/real 字段隔离 | 单测断言字段 |
| 性能 | calendar coverage 用 set membership | fixture 测试 |

## 10. 测试设计

| 测试场景 | 前置条件 | 操作 | 预期结果 | 验证方式 |
|---|---|---|---|---|
| hs300 required fields | fixture | normalize/validate | PASS | pytest |
| calendar denominator | open dates fixture | validate prices/index | denominator 使用 open dates | pytest |
| benchmark missing | 未 publish hs300 | reader/resolver | required_missing | pytest |
| proxy separation | proxy fixture | resolver | 不填 hs300 字段 | pytest |

## 11. 实施步骤

| TASK-ID | 动作 | 目标文件 | 详细描述 | 对应测试 |
|---|---|---|---|---|
| CR010-S03-T1 | 修改 | `market_data/contracts.py` | 补齐 schema | required fields |
| CR010-S03-T2 | 修改 | `market_data/normalization.py` | 真实 index 与 proxy 隔离 | proxy separation |
| CR010-S03-T3 | 修改 | `market_data/validation.py` | coverage denominator | calendar denominator |
| CR010-S03-T4 | 修改 | `market_data/readers.py` | typed missing | benchmark missing |
| CR010-S03-T5 | 修改 | `tests/test_market_data_normalization_validation_readers.py` | 增加测试 | 全部 |

## 12. 风险、难点与预研建议

| 风险 / 难点 | 影响 | 缓解措施 / 预研建议 |
|---|---|---|
| calendar 缺口导致 index coverage fail | readiness 不通过 | 报告 gap，不 publish production current truth |
| proxy 被误称真实 benchmark | 研究结论失真 | 字段和 status 分离 |

### OPEN / Spike 跟踪

| ID | 类型（OPEN / Spike） | 问题 | 下一动作 | 责任方 |
|---|---|---|---|---|
| 无 | OPEN | 无阻断项 | 不适用 | 不适用 |

## 13. 回滚与发布策略

- 发布方式：随 P0 index/calendar 合同发布。
- 回滚触发条件：真实 benchmark 缺失时仍返回 proxy、coverage 使用自然日。
- 回滚动作：撤回 S03 reader/validation 改动，保留已有 hs300 小窗口能力。

## 14. Definition of Done

- [x] LLD 14 节完成。
- [ ] hs300_index/trade_calendar canonical 测试通过。
- [ ] calendar denominator 与 benchmark missing/proxy separation 测试通过。
