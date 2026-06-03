---
story_id: "CR017-S05-validation-quality-parity-and-leakage-tests"
title: "复权 quality / parity / leakage 验证矩阵"
story_slug: "validation-quality-parity-and-leakage-tests"
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

# LLD: CR017-S05 — 复权 quality / parity / leakage 验证矩阵

本文档只定义 CR017-S05 的验证矩阵和 quality gate 设计；CP5 统一确认前不得实现测试文件或修改 validation / quality 代码。

## 1. Goal

创建 `tests/test_cr017_adjustment_quality_parity.py`、`tests/test_cr017_adjustment_leakage_gates.py` 的实现蓝图，并限定 `market_data/validation.py`、`market_data/quality.py` 的共享修改，量化 TS-017-01..03 的 formula parity、quality、single-policy 和 QMT raw execution leakage 验证。

## 2. Requirements（Functional / Non-Functional）

### 2.1 Functional

- 覆盖 REQ-098、REQ-099、REQ-100、REQ-101、REQ-102、REQ-121。
- TS-017-01、TS-017-02、TS-017-03 均至少包含 1 个正向和 1 个失败场景。
- 缺 factor direction、缺 as-of、混用 policy、复权价进入 execution 字段均 fail。
- parity mismatch 必须输出结构化 reason，不能只输出自由文本。

### 2.2 Non-Functional

- 测试只使用 fixture；不读取真实数据、旧报告内容、凭据或私有路径。
- warning 不得作为 production pass；quality status 必须可区分 pass/warn/fail/required_missing。
- CP5 前真实操作计数均为 0。

## 3. 模块拆分与职责

| 模块 / 文件组 | 职责 | 说明 |
|---|---|---|
| `tests/test_cr017_adjustment_quality_parity.py` | 覆盖 raw/factor/derived lineage、qfq as-of、hfq/returns parity 和 mismatch reason | S05 primary |
| `tests/test_cr017_adjustment_leakage_gates.py` | 覆盖 single-policy 和 QMT raw execution leakage | S05 primary |
| `market_data/validation.py` | 增加 adjustment quality gate、blocked reason、required_missing 映射 | shared；S02 已定义基础 reason |
| `market_data/quality.py` | 增加 adjustment jump warning / fail 质量枚举或 helper | shared |

## 4. 代码结构与文件影响范围

| 动作 | 文件路径 | 变更内容 |
|---|---|---|
| 创建 | `tests/test_cr017_adjustment_quality_parity.py` | 增加 TS-017-01/02 fixture parity 和质量失败测试 |
| 创建 | `tests/test_cr017_adjustment_leakage_gates.py` | 增加 TS-017-03 single-policy 与 execution leakage 测试 |
| 修改 | `market_data/validation.py` | 接入 quality fail / blocked reason 枚举和 gate result |
| 修改 | `market_data/quality.py` | 接入 adjustment jump warning / unexplained fail helper |

## 5. 数据模型与持久化设计

| 对象 / 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `AdjustmentQualityResult` | dataclass / typed dict | `status`、`reason_code`、`view_id`、`source_run_id`、`lineage_checksum` 必填 | quality gate 输出 |
| `ParityCheckResult` | dataclass / typed dict | `status`、`mismatch_reason`、`expected`、`actual` 或摘要必填 | 结构化 parity |
| `LeakageGuardResult` | dataclass / typed dict | `status`、`blocked_reason`、`field_name`、`policy` 必填 | QMT leakage 阻断 |

无新增持久化；测试 fixture 存在于测试文件内或项目既有 fixture 目录，禁止读取真实 lake。

## 6. API / Interface 设计

| 接口 / 入口 | 输入 | 输出 | 调用方 | 说明 |
|---|---|---|---|---|
| `adjustment_quality_gate(metadata)` | raw/factor/derived metadata | `AdjustmentQualityResult` | validation、tests | 缺 lineage/as-of/direction fail |
| `check_adjustment_parity(input, expected)` | fixture raw/factor/output | `ParityCheckResult` | tests | mismatch reason 结构化 |
| `guard_execution_price_leakage(intent_or_metadata)` | reader metadata、order intent sample | `LeakageGuardResult` | CR015 risk、tests | qfq/hfq execution field fail |
| `build_ts017_matrix()` | 无 | TS-017 scenario map | tests / docs | 可追溯 UC/REQ |

## 7. 核心处理流程

1. 读取 S02/S03/S04 合同输出形态作为 fixture schema。
2. 对 TS-017-01 验证 raw/factor/derived lineage 和 quality status。
3. 对 TS-017-02 验证 qfq as-of、input snapshot 和 deterministic lineage。
4. 对 TS-017-03 验证 single-policy gate 与 QMT raw execution boundary。
5. 任一 fail 输出 structured reason；不把 warning 计为 production pass。

## 8. 技术设计细节

- 关键规则：`required_missing`、`mixed_adjustment_policy`、`execution_requires_raw`、`unexplained_adjustment_jump` 必须是稳定 reason code。
- 依赖复用：复用 S02 contract result、S03 derived candidate、S04 reader metadata 的字段名。
- 兼容性处理：测试不读取旧 qfq 真实内容，只验证迁移声明字段。
- 图示类型选择：流程图不强制；测试矩阵以表格固定。

## 9. 安全与性能设计

| 维度 | 设计措施 | 验证方式 |
|---|---|---|
| 安全 | fixture-only；禁止 provider、lake、credential、old report content；复权 execution leakage hard fail | operation counters 和 leakage tests |
| 可验证性 | 每个 TS 场景至少正向 / 失败各 1 个 | test collection 名称与 TS id 对应 |
| 性能 | 测试数据小样本，运行不依赖真实数据规模 | pytest 单文件验证 |

## 10. 测试设计

| 测试场景 | 前置条件 | 操作 | 预期结果 | 验证方式 |
|---|---|---|---|---|
| TS-017-01 正向 | raw/factor/derived metadata 完整 | quality gate | PASS | `test_ts017_01_quality_lineage_pass` |
| TS-017-01 失败 | factor direction 缺失 | quality gate | FAIL structured reason | `test_ts017_01_missing_direction_fails` |
| TS-017-02 正向 | qfq as-of fixture | parity check | PASS deterministic | `test_ts017_02_qfq_asof_parity_pass` |
| TS-017-02 失败 | qfq 缺 as-of | quality gate | FAIL `missing_as_of_trade_date` | `test_ts017_02_missing_asof_fails` |
| TS-017-03 失败 | order intent execution price 使用 qfq | leakage guard | FAIL `execution_requires_raw` | `test_ts017_03_adjusted_execution_price_fails` |

## 11. 实施步骤

| TASK-ID | 动作 | 目标文件 | 详细描述 | 对应测试 |
|---|---|---|---|---|
| CR017-S05-T1 | 创建 | `tests/test_cr017_adjustment_quality_parity.py` | 固化 TS-017-01/02 quality parity tests | quality / parity tests |
| CR017-S05-T2 | 创建 | `tests/test_cr017_adjustment_leakage_gates.py` | 固化 TS-017-03 single-policy 与 QMT leakage tests | leakage tests |
| CR017-S05-T3 | 修改 | `market_data/validation.py` | 增加 quality gate result 和 blocked reason | validation tests |
| CR017-S05-T4 | 修改 | `market_data/quality.py` | 增加 adjustment warning/fail helper | quality tests |

## 12. 风险、难点与预研建议

| 风险 / 难点 | 影响 | 缓解措施 / 预研建议 |
|---|---|---|
| warning 被当成 pass | 生产质量误放行 | status 明确区分，production pass 不接受 warning |
| 真实数据被测试误读 | 泄露或不可重复 | fixture-only，禁止真实 lake / 旧报告内容 |
| reason 只有自由文本 | QA 无法稳定断言 | 固定 reason code + human message |

### OPEN / Spike 跟踪

| ID | 类型（OPEN / Spike） | 问题 | 下一动作 | 责任方 |
|---|---|---|---|---|
| 无 | N/A | 无阻断 OPEN；真实数据 parity 不在本 Story 默认范围 | 如需真实 parity，另起授权 | meta-po |

## 13. 回滚与发布策略

- 发布方式：CP5 approved 后提交离线测试与 quality helper，不触发真实验证。
- 回滚触发条件：fixture 测试读取真实路径、warning 被视为 pass、leakage guard 允许非 raw execution。
- 回滚动作：撤回 S05 tests 和 validation / quality 增量，保留上游 S02/S03/S04 合同。

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
