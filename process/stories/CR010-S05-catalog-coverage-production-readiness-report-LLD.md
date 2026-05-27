---
story_id: "CR010-S05-catalog-coverage-production-readiness-report"
title: "catalog coverage 与 production readiness report"
story_slug: "catalog-coverage-production-readiness-report"
lld_version: "1.0"
tier: "M"
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
  - "process/HLD-DATA-LAKE.md#5-quality--readiness--publish"
  - "process/HLD-DATA-LAKE.md#8-非功能设计"
open_items: 0
---

# LLD: CR010-S05-catalog-coverage-production-readiness-report - catalog coverage 与 production readiness report

## 1. Goal

创建 catalog coverage report 和 production readiness report，披露 P0 七个 dataset 的 publish 状态、date range、source/interface、quality/readiness/PIT、known limitations，并让 production_strict 对缺口 fail-fast。

## 2. Requirements（Functional / Non-Functional）

### 2.1 Functional

- report 覆盖 `prices`、`adj_factor`、`hs300_index`、`trade_calendar`、`index_members`、`index_weights`、`stock_basic`。
- 报告区分 published current truth、unpublished candidate、missing required。
- production_strict 对缺 PIT、缺真实 benchmark、缺 W3、缺复权、quality fail 阻断。
- exploratory 允许 limitation，但必须输出 allowed_claims/blocked_claims。

### 2.2 Non-Functional

- 不把 repo `data/**` 或 `reports/data_quality_report.csv` 当 current truth。
- 默认不读取真实 `/mnt/ugreen-data-lake`；真实 smoke 需另行授权。
- 报告不打印 token 或真实私有路径。

## 3. 模块拆分与职责

| 模块 / 文件组 | 职责 | 说明 |
|---|---|---|
| `market_data/catalog.py` | 聚合 catalog coverage | published/current truth 来源 |
| `market_data/validation.py` | readiness report payload | quality/PIT/W3 状态 |
| `market_data/readers.py` | strict/exploratory 消费判定 | 返回 metadata |
| `engine/research_dataset.py` | 消费 readiness metadata | 不触发 backfill |
| `tests/test_cr010_data_lake_publish_and_contracts.py` | 报告和 strict gate 测试 | tmp lake |

## 4. 代码结构与文件影响范围

| 动作 | 文件路径 | 变更内容 |
|---|---|---|
| 修改 | `market_data/catalog.py` | 新增 coverage/readiness report builder |
| 修改 | `market_data/validation.py` | 输出 production readiness payload |
| 修改 | `market_data/readers.py` | 返回 allowed_claims/blocked_claims |
| 修改 | `engine/research_dataset.py` | production_strict 缺口 fail-fast |
| 修改 | `tests/test_cr010_data_lake_publish_and_contracts.py` | 覆盖 report 与 strict/exploratory |

## 5. 数据模型与持久化设计

| 对象 / 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `CoverageRow.dataset` | str | P0 exact | 七个 dataset |
| `publish_status` | enum | published/candidate/missing | current truth 状态 |
| `date_range` | object | nullable | published 才完整 |
| `quality_status` | enum | pass/warn/fail/missing | report 必填 |
| `readiness_status` | enum | ready/limited/missing | report 必填 |
| `pit_status` | enum | required | universe/weights/basic |
| `known_limitations` | list | required | 可为空 |
| `blocked_claims` | list | required | production claim 阻断 |

## 6. API / Interface 设计

| 接口 / 入口 | 输入 | 输出 | 调用方 | 说明 |
|---|---|---|---|---|
| `build_catalog_coverage_report(lake_root, datasets)` | catalog path + dataset list | rows + summary | CLI/QA | 只读 |
| `build_production_readiness_report(...)` | coverage rows + policy | strict/exploratory status | research builder | 不联网 |
| `market_data report-readiness` | lake root + mode | JSON/CSV/Markdown | 用户/QA | 默认 tmp/fixture |

## 7. 核心处理流程

1. 读取 published catalog。
2. 对 P0 七个 dataset 建立 coverage row。
3. 标记 missing/candidate/published。
4. 合并 quality/readiness/PIT/known limitations。
5. 生成 exploratory 与 production_strict 两套结论。
6. 对缺口输出 remediation spec，`auto_execute=false`。

## 8. 技术设计细节

- 关键规则：current truth 只来自 published catalog。
- 依赖复用点：复用 `read_dataset` metadata 与 `ResearchDatasetRequest.realism_mode`。
- 兼容性处理：旧 legacy report 只以 limitation 名称出现，不读取内容。
- 图示类型选择：不需要图示。

## 9. 安全与性能设计

| 维度 | 设计措施 | 验证方式 |
|---|---|---|
| 安全 | 默认只读 tmp/fixture catalog | 单测 |
| 安全 | remediation `auto_execute=false` | JSON 断言 |
| 性能 | report 聚合 P0 七行，小对象处理 | 单测 |

## 10. 测试设计

| 测试场景 | 前置条件 | 操作 | 预期结果 | 验证方式 |
|---|---|---|---|---|
| P0 coverage rows | 部分 published catalog | build report | 七行，缺失披露 | pytest |
| strict 缺 PIT fail | pit incomplete | readiness report strict | fail | pytest |
| exploratory limitation | warn/limited | readiness report exploratory | allowed with limitation | pytest |
| legacy not current truth | repo data/report 存在 | build report | 不读取、不标 current | pytest |
| remediation no auto execute | missing W3 | report | auto_execute=false | pytest |

## 11. 实施步骤

| TASK-ID | 动作 | 目标文件 | 详细描述 | 对应测试 |
|---|---|---|---|---|
| CR010-S05-T1 | 修改 | `market_data/catalog.py` | build catalog coverage report | P0 coverage |
| CR010-S05-T2 | 修改 | `market_data/validation.py` | build production readiness payload | strict/exploratory |
| CR010-S05-T3 | 修改 | `market_data/readers.py` | allowed/blocked claims metadata | exploratory limitation |
| CR010-S05-T4 | 修改 | `engine/research_dataset.py` | production_strict 缺口 fail-fast | strict fail |
| CR010-S05-T5 | 修改 | `tests/test_cr010_data_lake_publish_and_contracts.py` | 增加 report tests | all |

## 12. 风险、难点与预研建议

| 风险 / 难点 | 影响 | 缓解措施 / 预研建议 |
|---|---|---|
| 外置 lake 当前只含部分 dataset | 被误读为完整 P0 truth | report 明确 missing required |
| legacy report 被误用 | current truth 污染 | 不读取内容，仅标 legacy non-current |
| W3 尚未确认 | strict 大量 fail | B 批次 fail-fast 合同继续推进 |

### OPEN / Spike 跟踪

| ID | 类型（OPEN / Spike） | 问题 | 下一动作 | 责任方 |
|---|---|---|---|---|
| CR010-S05-O1 | OPEN | 真实外置 lake report 是否执行 | 等用户另行授权真实 smoke | user |

## 13. 回滚与发布策略

- 发布方式：作为 CLI/report helper 发布，不改变真实 lake。
- 回滚触发条件：report 读取旧数据、误称 missing dataset 已 published、strict 不阻断 quality fail。
- 回滚动作：撤回 report builder 和 strict gate 变更，保留 catalog publish gate。

## 14. Definition of Done

- [x] LLD 14 节完成。
- [ ] P0 七 dataset coverage report 测试通过。
- [ ] production_strict/exploratory readiness 测试通过。
- [ ] legacy data/report 不作为 current truth。
