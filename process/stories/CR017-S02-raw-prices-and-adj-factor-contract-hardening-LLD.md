---
story_id: "CR017-S02-raw-prices-and-adj-factor-contract-hardening"
title: "raw prices 与 adj_factor 事实源合同强化"
story_slug: "raw-prices-and-adj-factor-contract-hardening"
lld_version: "1.0"
tier: "M"
status: "approved"
confirmed: true
implementation_allowed: true
created_by: "meta-dev"
created_at: "2026-05-28T06:23:40+08:00"
confirmed_by: "user"
confirmed_at: "2026-05-28T07:03:27+08:00"
cp5_batch: "CR017-ADJUSTMENT-DUAL-VIEW-BATCH-A"
shared_fragments: []
open_items: 0
pre_cp5_real_operation_counts:
  provider_fetch: 0
  lake_write: 0
  credential_read: 0
  current_pointer_publish: 0
  dependency_change: 0
  legacy_qfq_overwrite: 0
---

# LLD: CR017-S02 — raw prices 与 adj_factor 事实源合同强化

本文档只定义 CR017-S02 的合同层设计，等待 CP5 统一确认；不得在确认前实现或触发真实抓取 / 写湖。

## 1. Goal

创建 `market_data/adjustment_contracts.py` 和 `tests/test_cr017_raw_adj_factor_contract.py` 的实现蓝图，并限定对 `market_data/contracts.py`、`market_data/validation.py` 的共享修改，使 `prices_raw` 与 `adj_factor` 成为可验证事实源合同。

## 2. Requirements（Functional / Non-Functional）

### 2.1 Functional

- 覆盖 REQ-098、REQ-100、REQ-104；`prices_raw` 必须保留未复权 OHLCV、source/interface、run_id、batch_id、available_at、lineage checksum 和 quality status。
- `adj_factor` 必须包含 `provider_factor_direction`、`factor_base_date_policy`、`source_run_id`、`available_at` 和 as-of 相关字段。
- factor direction、lineage、raw OHLC 合法性缺失或失败时，后续派生允许次数为 0。

### 2.2 Non-Functional

- 本 Story 不拥有 connector、runtime、真实 provider 字段复核或 lake 写入。
- 所有校验为离线 schema / fixture 校验；CP5 前真实操作计数均为 0。
- 与 CR017-S01 policy id、CR010-S02 prices / adj_factor 历史回补合同保持兼容。

## 3. 模块拆分与职责

| 模块 / 文件组 | 职责 | 说明 |
|---|---|---|
| `market_data/adjustment_contracts.py` | 定义 raw price、adj_factor、lineage 和 validation result 合同 | S02 primary |
| `market_data/contracts.py` | 增加 view / schema 常量导出 | shared；不得破坏既有 catalog |
| `market_data/validation.py` | 增加 quality failure / required_missing reason 枚举 | shared；S05 后续扩展 |
| `tests/test_cr017_raw_adj_factor_contract.py` | 覆盖必需字段、direction、lineage、非法 raw price 和权限计数 | 离线 fixture |

## 4. 代码结构与文件影响范围

| 动作 | 文件路径 | 变更内容 |
|---|---|---|
| 创建 | `market_data/adjustment_contracts.py` | 定义 `RawPriceContract`、`AdjFactorContract`、`LineageRef`、`ContractCheckResult` 与验证函数 |
| 修改 | `market_data/contracts.py` | 增加 `prices_raw`、`adj_factor` schema id 和字段集常量 |
| 修改 | `market_data/validation.py` | 增加 `missing_factor_direction`、`missing_lineage`、`invalid_raw_ohlc` 等 reason |
| 创建 | `tests/test_cr017_raw_adj_factor_contract.py` | 创建纯 fixture contract tests |

## 5. 数据模型与持久化设计

| 对象 / 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `prices_raw` | dataset schema | `trade_date`、`symbol`、OHLCV、`source`、`source_interface`、`source_run_id`、`batch_id`、`available_at`、`available_at_rule`、`lineage_checksum`、`quality_status` 必填 | 不被 qfq/hfq 覆盖 |
| `adj_factor` | dataset schema | `adj_factor`、`provider_factor_direction`、`factor_base_date_policy`、`source_run_id`、`available_at`、`as_of_trade_date` 或可推导 as-of、`quality_status` 必填 | direction 未确认则派生 blocked |
| `ContractCheckResult` | dataclass / typed dict | `status=pass/fail/required_missing`、`reason_code`、`field`、`operation_counts` | 结构化错误暴露 |

无新增持久化写入；只定义 schema / validation 合同。

## 6. API / Interface 设计

| 接口 / 入口 | 输入 | 输出 | 调用方 | 说明 |
|---|---|---|---|---|
| `validate_prices_raw_contract(rows_or_schema)` | raw rows 或 schema metadata | `ContractCheckResult` | S03、S05、tests | OHLC 非法或 lineage 缺失 fail |
| `validate_adj_factor_contract(rows_or_schema)` | factor rows 或 schema metadata | `ContractCheckResult` | S03、S05、tests | direction / base policy 缺失 blocked |
| `validate_source_lineage(metadata)` | `source_run_id`、`batch_id`、`lineage_checksum` | `ContractCheckResult` | publish / reader 前校验 | 不读取真实路径 |
| `build_required_field_sets()` | 无 | raw/factor field sets | tests、contracts export | exact 字段集 |

## 7. 核心处理流程

1. 读取 S01 policy 合同和 CR010-S02 prices / adj_factor 基线字段。
2. 对 `prices_raw` 执行必需字段、OHLC 合法性、lineage 完整性和 quality status 校验。
3. 对 `adj_factor` 执行 factor value、provider direction、base policy、as-of、available_at 和 lineage 校验。
4. 任一必需字段缺失时返回 `required_missing` 或 `fail`，后续 derivation gate 为 blocked。
5. 输出纯内存结果；不触发 provider、lake write 或 current pointer publish。

## 8. 技术设计细节

- 关键规则：`provider_factor_direction` 必须是 explicit enum，不允许用数值趋势隐式推断方向。
- 依赖复用：沿用 CR014/CR010 的 Parquet/catalog 概念，只定义 CR017 raw/factor 事实源字段。
- 兼容性处理：不重命名旧 prices 合同；新增 view id 与字段集以显式命名隔离。
- 图示类型选择：流程图不强制，本 Story 为单向 schema contract 校验；第 7 节步骤足以描述。

## 9. 安全与性能设计

| 维度 | 设计措施 | 验证方式 |
|---|---|---|
| 安全 | 禁止读取凭据、真实 provider、真实私有路径；只处理 fixture / schema metadata | operation counters 测试为 0 |
| 一致性 | raw/factor 合同失败时不允许下游派生 | S03/S05 消费 `ContractCheckResult` |
| 性能 | 字段校验按行数线性，schema 校验常量级 | fixture smoke 覆盖 |

## 10. 测试设计

| 测试场景 | 前置条件 | 操作 | 预期结果 | 验证方式 |
|---|---|---|---|---|
| raw 必需字段完整 | raw fixture | validate raw | PASS | `test_prices_raw_required_fields_pass` |
| raw OHLC 非法 | close<=0 非缺失 | validate raw | FAIL `invalid_raw_ohlc` | `test_invalid_raw_price_fails` |
| factor direction 缺失 | factor fixture 缺字段 | validate factor | `required_missing`，derivation blocked | `test_missing_factor_direction_blocks` |
| lineage 缺失 | 缺 `source_run_id` 或 checksum | validate lineage | required_missing | `test_missing_lineage_is_required_missing` |
| qfq/hfq 不覆盖 raw | raw schema + derived schema | 检查 view id | raw 保持 source-of-truth | `test_derived_view_does_not_overwrite_raw` |

## 11. 实施步骤

| TASK-ID | 动作 | 目标文件 | 详细描述 | 对应测试 |
|---|---|---|---|---|
| CR017-S02-T1 | 创建 | `market_data/adjustment_contracts.py` | 定义 raw / factor 合同对象、field sets 和 validate 函数 | raw / factor contract tests |
| CR017-S02-T2 | 修改 | `market_data/contracts.py` | 增加 view id、schema version、字段集导出 | import / schema tests |
| CR017-S02-T3 | 修改 | `market_data/validation.py` | 增加 CR017 reason code 和 required_missing 映射 | reason tests |
| CR017-S02-T4 | 创建 | `tests/test_cr017_raw_adj_factor_contract.py` | 固化上述离线测试 | 全部 S02 tests |

## 12. 风险、难点与预研建议

| 风险 / 难点 | 影响 | 缓解措施 / 预研建议 |
|---|---|---|
| provider factor direction 理解错误 | 后续 qfq/hfq 全量方向错误 | direction 必须显式字段；方向未知不实现派生 |
| raw 与 qfq/hfq 路径混淆 | 原始交易价被覆盖 | 独立 view id；raw schema 不接受 derived overwrite |
| validation shared 文件与 S05 冲突 | 后续并行开发冲突 | CP5 后按 S02 -> S03 -> S04 -> S05 串行合并 shared 文件 |

### OPEN / Spike 跟踪

| ID | 类型（OPEN / Spike） | 问题 | 下一动作 | 责任方 |
|---|---|---|---|---|
| 无 | N/A | 无阻断 OPEN；真实 provider 字段复核不属于本 Story | 若后续需要真实复核，另起授权 Story | meta-po |

## 13. 回滚与发布策略

- 发布方式：CP5 approved 后作为离线 contract 层发布，不发布真实数据。
- 回滚触发条件：direction 缺失仍允许派生、raw 被 derived 覆盖、旧合同导出破坏。
- 回滚动作：移除 `adjustment_contracts.py` 导出和 shared 文件增量，保留旧 CR010 合同不变。

## 14. Definition of Done

- [x] 14 个章节全部填写完成。
- [x] 文件影响范围、接口、测试与实施步骤可直接指导编码。
- [x] `confirmed=false`、`implementation_allowed=false` 时不进入实现。
- [x] CP5 前真实操作计数均为 0。
- [x] frontmatter 已填写 `tier=M`。
- [x] OPEN / Spike 已清点，当前无阻断项。
- [ ] 等待全部目标 Story 的 LLD 与 CP5 自动预检汇总后统一人工确认。

## 人工确认区

本 LLD 等待 `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` 统一确认；确认前不得实现。

**CP5 checklist 摘要**：

| # | 检查项 | 状态 | 证据 |
|---|---|---|---|
| 1 | LLD 覆盖 AC | 待检查 | 第 2 / 10 / 14 节 |
| 2 | 与 HLD / ADR 一致 | 待检查 | 第 3 / 8 / 12 节 |
| 3 | 文件影响范围明确 | 待检查 | 第 4 / 11 节 |
| 4 | 接口契约完整 | 待检查 | 第 6 节 |
| 5 | 测试与 dev_gate 可计算 | 待检查 | 第 10 / 14 节 |
