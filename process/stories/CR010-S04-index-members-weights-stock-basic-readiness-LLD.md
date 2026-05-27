---
story_id: "CR010-S04-index-members-weights-stock-basic-readiness"
title: "index_members/index_weights/stock_basic readiness 强化"
story_slug: "index-members-weights-stock-basic-readiness"
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
  - "process/HLD-DATA-LAKE.md#41-p0-dataset"
  - "process/HLD-DATA-LAKE.md#7-消费边界"
open_items: 0
---

# LLD: CR010-S04-index-members-weights-stock-basic-readiness - index_members/index_weights/stock_basic readiness 强化

## 1. Goal

修改 membership/weights/basic dataset readiness，确保 `index_members`、`index_weights`、`stock_basic` 的职责不可互相替代，并在缺 PIT proof 时标记 `pit_incomplete` 或 `non_pit_snapshot`。

## 2. Requirements（Functional / Non-Functional）

### 2.1 Functional

- `index_members` 需要 effective/available/available_at 字段才能声明 PIT available。
- `index_weights` 不得替代完整 membership；缺完整 proof 时 readiness limited。
- `stock_basic` 只辅助股票状态，不证明历史 universe。
- reader/report 输出 readiness_status、pit_status、known_limitations。

### 2.2 Non-Functional

- 不读取真实/旧数据证明 PIT。
- production_strict 对 PIT 缺失默认阻断。
- exploratory 必须写 survivor bias limitation。

## 3. 模块拆分与职责

| 模块 / 文件组 | 职责 | 说明 |
|---|---|---|
| `market_data/contracts.py` | 定义 readiness/PIT 字段 | P0 dataset 合同 |
| `market_data/normalization.py` | 生成 canonical status 字段 | 缺字段保持 missing/limited |
| `market_data/validation.py` | PIT/readiness gate | 不伪造 available |
| `market_data/readers.py` | 读取 readiness metadata | strict/exploratory 行为 |
| `engine/universe.py` | 只消费 published readiness | 不自动补数 |

## 4. 代码结构与文件影响范围

| 动作 | 文件路径 | 变更内容 |
|---|---|---|
| 修改 | `market_data/contracts.py` | 补齐 PIT/readiness enum |
| 修改 | `market_data/normalization.py` | 规范 missing/limited 状态 |
| 修改 | `market_data/validation.py` | 缺 available_at/effective/available_date 时 fail/limited |
| 修改 | `market_data/readers.py` | 暴露 metadata 和 limitation |
| 修改 | `engine/universe.py` | production_strict 缺 PIT 阻断 |
| 修改 | `tests/test_market_data_multidataset_quality_readers.py` | 增加 readiness 测试 |

## 5. 数据模型与持久化设计

| 对象 / 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `index_members.effective_date` | date | required for PIT | 成分生效 |
| `index_members.available_date` | date | required for PIT | 可得日期 |
| `available_at` | timestamp | required for strict | 可用时点 |
| `pit_status` | enum | required | PIT 状态 |
| `readiness_status` | enum | required | ready/limited/missing |
| `stock_basic.snapshot_date` | date | required | 当前快照，不证明 PIT |

## 6. API / Interface 设计

| 接口 / 入口 | 输入 | 输出 | 调用方 | 说明 |
|---|---|---|---|---|
| `validate_dataset(index_members)` | canonical | readiness/PIT status | CLI | 缺 proof limited/fail |
| `read_dataset(index_members)` | published catalog | data + metadata | universe reader | strict gate |
| `build_universe(...)` | readiness metadata | universe or typed failure | engine | 不触发 backfill |

## 7. 核心处理流程

1. normalize 保留 source 字段和日期字段。
2. validate 判断 PIT proof 所需字段。
3. index_weights 仅作为权重数据，不能补齐 members。
4. stock_basic 只输出辅助 limitation。
5. reader/engine 按 realism/strict policy 返回数据或 typed failure。

## 8. 技术设计细节

- 关键规则：`stock_basic` 永远不能使 `pit_status=pit_available`。
- 依赖复用点：复用已有 readiness metadata 结构。
- 兼容性处理：旧 fixture 缺 PIT 字段时 exploratory 可 limited，production_strict fail。
- 图示类型选择：不需要图示。

## 9. 安全与性能设计

| 维度 | 设计措施 | 验证方式 |
|---|---|---|
| 安全 | 不读取旧数据判断成员 | 静态/单测 |
| 安全 | strict 缺 PIT 阻断 | engine 单测 |
| 性能 | readiness 判断按字段存在性和 groupby key | 小 fixture |

## 10. 测试设计

| 测试场景 | 前置条件 | 操作 | 预期结果 | 验证方式 |
|---|---|---|---|---|
| members PIT available | 字段完整 | validate | pit_available | pytest |
| members 缺 available_at | fixture 缺字段 | validate/read strict | pit_incomplete 或 fail | pytest |
| weights 不替代 members | 只有 weights | read universe | required_missing | pytest |
| stock_basic 只辅助 | 只有 stock_basic | production_strict | fail + limitation | pytest |

## 11. 实施步骤

| TASK-ID | 动作 | 目标文件 | 详细描述 | 对应测试 |
|---|---|---|---|---|
| CR010-S04-T1 | 修改 | `market_data/contracts.py` | 增加 readiness/PIT enum | all |
| CR010-S04-T2 | 修改 | `market_data/validation.py` | PIT proof 校验 | members PIT |
| CR010-S04-T3 | 修改 | `market_data/readers.py` | strict/exploratory metadata | weights/stock_basic |
| CR010-S04-T4 | 修改 | `engine/universe.py` | strict 缺 PIT 阻断 | stock_basic strict |
| CR010-S04-T5 | 修改 | `tests/test_market_data_multidataset_quality_readers.py` | 增加测试 | all |

## 12. 风险、难点与预研建议

| 风险 / 难点 | 影响 | 缓解措施 / 预研建议 |
|---|---|---|
| Tushare membership source PIT 语义未确认 | production universe 不可声明完整 | 保持 `pit_incomplete`，B 批次 Spike |
| 旧实验依赖固定股票池 | production_strict 回归失败 | exploratory 保留 limitation |

### OPEN / Spike 跟踪

| ID | 类型（OPEN / Spike） | 问题 | 下一动作 | 责任方 |
|---|---|---|---|---|
| 无 | OPEN | PIT source/interface 确认属于 CR010-S06 | 转入 B 批次 | meta-se / user |

## 13. 回滚与发布策略

- 发布方式：作为 readiness policy 更新。
- 回滚触发条件：strict 不阻断缺 PIT、weights 被当成完整 members。
- 回滚动作：撤回 universe strict gate 和 readiness enum 变更。

## 14. Definition of Done

- [x] LLD 14 节完成。
- [ ] PIT/readiness 单测通过。
- [ ] production_strict 缺 PIT 阻断，exploratory 输出 limitation。
