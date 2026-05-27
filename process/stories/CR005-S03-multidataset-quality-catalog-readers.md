---
story_id: "CR005-S03"
title: "多 dataset quality/catalog/readers 与 PIT/复权 gate"
story_slug: "multidataset-quality-catalog-readers"
status: "verified"
priority: "P0"
wave: "CR5-W2"
depends_on: ["CR005-S02"]
dependency_contracts:
  - upstream: "CR005-S02"
    type: "contract"
    required: "P0 dataset schema、key columns、PIT 可得性字段、adjusted price normalization 输出契约 confirmed"
file_ownership:
  primary:
    - "tests/test_market_data_multidataset_quality_readers.py"
  shared:
    - "market_data/validation.py"
    - "market_data/catalog.py"
    - "market_data/readers.py"
    - "market_data/contracts.py"
  merge_owner: "CR005-S03"
  forbidden:
    - "market_data/connectors/**"
    - "market_data/runtime.py"
    - "market_data/storage.py"
    - "engine/backtest.py"
    - "experiments/**"
    - "data/**"
    - "reports/**"
    - "delivery/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#226-集成契约"
    - "process/ARCHITECTURE-DECISION.md#adr-014cr-005-多-dataset-schema-与-quality-gate-先于消费方冻结"
    - "process/ARCHITECTURE-DECISION.md#adr-017pit-与复权由-pandas-数据层保证backtrader-只消费干净输入"
    - "process/stories/CR005-S03-multidataset-quality-catalog-readers.md"
  status: "approved"
  lld_path: "process/stories/CR005-S03-multidataset-quality-catalog-readers-LLD.md"
  cp5_auto_result: "process/checks/CP5-CR005-S03-multidataset-quality-catalog-readers-LLD-IMPLEMENTABILITY.md"
  cp5_manual_review: "checkpoints/CP5-CR005-BATCH-B1-S03-LLD-BATCH.md"
  confirmed_by: "user"
  confirmed_at: "2026-05-17T21:39:16+08:00"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  required_contracts:
    - "CR005-S02 hs300 schema and exact mapping frozen"
    - "trade calendar coverage denominator frozen"
    - "quality status and reader unavailable mapping frozen"
  file_conflict_free: true
  cp5_required: true
  cp5_confirmed: true
  implementation_allowed: true
  implementation_handoff: "process/handoffs/META-DEV-CR005-S03-IMPLEMENT-2026-05-17.md"
  cp6_checkpoint: "process/checks/CP6-CR005-S03-multidataset-quality-catalog-readers-CODING-DONE.md"
verification_status: "verified"
verification_handoff: "process/handoffs/META-QA-CR005-S03-CP7-VERIFY-2026-05-17.md"
verification_checkpoint: "process/checks/CP7-CR005-S03-multidataset-quality-catalog-readers-VERIFICATION-DONE.md"
verified_by: "meta-po"
verified_at: "2026-05-17T22:11:52+08:00"
created_at: "2026-05-17"
updated_at: "2026-05-17T22:11:52+08:00"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-005"
---

# CR005-S03：多 dataset quality/catalog/readers 与 PIT/复权 gate

## 目标

为 CR005-S02 新增 dataset 提供统一 quality CSV、catalog、只读 reader、PIT as-of gate、复权一致 gate 和 `hs300_index` 专项 accuracy gate，使实验、轻量回测、Backtrader 都只能通过本地质量门消费已清洗数据。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | CR005-AC-007、CR005-AC-008、CR005-AC-010、CR005-AC-012、CR005-AC-013、CR005-AC-016、CR005-AC-018 |
| HLD | §22.6、§22.8、§22.9 |
| ADR | ADR-014、ADR-017 |

## 开发上下文（dev_context）

**背景说明**：当前 `market_data/validation.py` 和 `readers.py` 主要支持 `prices`。CR-005 需要 dataset 级 quality gate，且 reader 是所有消费方唯一入口。本 Story 必须把 PIT as-of join 与复权一致性变成消费前门控，防止 Backtrader、实验或轻量回测绕过数据层。

**输入文件**：`market_data/contracts.py`、`market_data/validation.py`、`market_data/catalog.py`、`market_data/readers.py`、CR005-S02 Story/LLD。

**输出文件**：`market_data/validation.py`、`market_data/catalog.py`、`market_data/readers.py`、`tests/test_market_data_multidataset_quality_readers.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 约束 |
|---|---|---|---|
| `validate_dataset(dataset, lake_root, expected_range, ...)` | dataset、日期、symbols/index_code、thresholds | `QualityResult` | 含 `fetch_status`、`dataset_status`、coverage、denominator、thresholds |
| `validate_hs300_index(...)` 或等价规则 | `hs300_index` canonical/gold、`trade_calendar` open dates、requested range、thresholds | `QualityResult` + missing dates/gap reason | denominator 来自交易日历 open dates；`index_code+trade_date` 唯一；lineage 必须可追溯 |
| `CatalogStore.upsert/get/list` | dataset quality summary | catalog entry | 记录 schema_version、coverage、quality_status、latest_manifest_run_id |
| `read_dataset(dataset, lake_root, filters, quality_policy)` | dataset、date range、symbols/index_code | DataFrame 或结构化错误 | 不导入 connector/runtime；quality fail 阻断 |
| `read_factor_panel` / 等价 reader | dataset set、decision calendar、PIT policy、adjustment_policy | PIT 对齐且复权一致的 factor panel / score / OHLCV feed | as-of join 必须满足 `available_at <= decision_time`；收益/指标/forward return 使用 adjusted price |

**设计约束**：

- quality CSV 是机器事实源；Markdown human-only。
- `fetch_status` 和 `dataset_status` 必须分离。
- `hs300_index` quality CSV 必须记录 `benchmark_kind`、coverage denominator、missing_trade_dates_json、gap_reason、duplicate_key_count、source、source_interface、source_run_id、manifest_run_id、raw_checksum 或等价 lineage、quality thresholds。
- quality `fail` 不得被 `allow_warn` 放行。
- reader 缺失数据时结构化失败或 unavailable，不自动补数。
- reader 不写 raw/manifest/canonical/quality/catalog。
- reader 输出给 Backtrader 前必须已完成 PIT 对齐和复权价格选择；Backtrader adapter 不得承担该职责。
- `available_at > decision_time`、缺少 PIT 可得性字段、`adjustment_policy` 混用或 adjusted price 缺失均必须阻断消费。

**命名规范**：quality 字段使用 snake_case；复杂列表字段用 `_json` 后缀。

**平台目标**：多 dataset 本地只读消费面。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR005-S03-T1 | 修改 | `market_data/validation.py` | 支持多 dataset quality、coverage、thresholds、双状态、PIT as-of 校验、复权一致校验和 `hs300_index` 专项 accuracy gate |
| CR005-S03-T2 | 修改 | `market_data/catalog.py` | 支持多 dataset catalog entry 和 quality path |
| CR005-S03-T3 | 修改 | `market_data/readers.py` | 支持 `prices` 以外 dataset 的只读 filter，以及干净 factor panel / score / OHLCV feed 输出契约 |
| CR005-S03-T4 | 创建 | `tests/test_market_data_multidataset_quality_readers.py` | 覆盖 quality gate、catalog、PIT as-of、复权一致、reader no-network/no-connector import |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_market_data_multidataset_quality_readers.py`。

**验证方式**：临时 parquet 数据湖 + quality CSV + 静态导入扫描。

**依赖环境**：Python 3.11、uv、pytest、pandas、pyarrow；不需要 token、不联网。

**关键验证场景**：

- `hs300_index` 覆盖请求区间时 reader 成功。
- `hs300_index` coverage denominator 使用 `trade_calendar` open dates；缺交易日输出 missing list 和 gap reason。
- `index_code+trade_date` 重复时 dataset_status/quality_status 为 fail。
- source lineage 缺失或 raw checksum / 等价 lineage 缺失时 quality fail 或 unavailable。
- quality `fail` 阻断 reader。
- quality `warn` 只有显式策略可放行。
- 非行情记录 `available_at > decision_time` 时 reader 阻断。
- `adjustment_policy` 混用、`adj_factor` 缺失或 adjusted price 缺失时 reader 阻断。
- reader 可输出已 PIT/复权清洗的 factor panel / score / OHLCV feed 给 Backtrader。
- `market_data/readers.py` 不导入 `market_data.connectors` / `runtime`。

## 量化验收标准（acceptance_criteria）

- [x] 每个 P0 dataset quality CSV 至少输出 20 个字段或等价完整字段集。
- [x] quality 字段包含 `fetch_status`、`dataset_status`、`quality_status`、coverage、denominator、thresholds、run/source/interface。
- [x] `hs300_index` quality 字段包含 `benchmark_kind`、coverage denominator、missing trade dates、gap reason、duplicate key count、source lineage、raw checksum 或等价 lineage、quality thresholds。
- [x] `hs300_index` duplicate key count 大于 0 时 reader/resolver 可用次数为 0。
- [x] `hs300_index` coverage 未达到 threshold 时映射为 `unavailable` 或 `required_missing`，并保留 remediation spec 所需缺口区间。
- [x] catalog 至少记录 4 个 P0 dataset 的最新 coverage 和 quality_status。
- [x] reader 默认网络调用次数为 0。
- [x] reader/import 静态扫描中 connector/runtime import 命中数为 0。
- [x] 参与消费的非行情数据 as-of join 后 100% 满足 `available_at <= decision_time`。
- [x] `adjustment_policy` 混用、adjusted price 缺失或 `adj_factor` 口径冲突时消费成功次数为 0。
- [x] 输出给 Backtrader 的 factor panel / score / OHLCV feed 已通过 PIT、复权和 quality gate。
- [x] 不修改 `market_data/connectors/**`、`engine/**`、`experiments/**`、真实 `data/**` 或 `reports/**`。

## 阻塞说明

无 BLOCKING。本 Story 是 CR005-S04 和 CR005-S06 的开发门控前置；未 verified 或 contract frozen 前，CR005-S04 不得实现 available 真实路径，Backtrader 不得进入开发。CR005-S06 的 dev_gate 还必须同时等待 CR005-S02 的 PIT 字段和 adjusted price 契约 confirmed。

## LLD / CP5 状态

- 状态：`approved`，已实现并进入 `ready-for-verification`。
- LLD：`process/stories/CR005-S03-multidataset-quality-catalog-readers-LLD.md`。
- CP5 自动预检：`process/checks/CP5-CR005-S03-multidataset-quality-catalog-readers-LLD-IMPLEMENTABILITY.md`，结论 `PASS`，OPEN 项 5 个。
- 调度证据：`process/handoffs/META-DEV-CR005-S03-LLD-2026-05-17.md` 记录主线程真实 `spawn_agent` 调度 meta-dev/dev-xu the 2nd，agent_id/thread_id=`019e3612-e8d5-75a0-bdfd-d0986b413d53`。
- CP6 编码完成：`process/checks/CP6-CR005-S03-multidataset-quality-catalog-readers-CODING-DONE.md`，结论 `PASS`。
- 实现调度证据：`process/handoffs/META-DEV-CR005-S03-IMPLEMENT-2026-05-17.md` 记录主线程真实 `spawn_agent` 调度 meta-dev/dev-yang the 2nd，agent_id/thread_id=`019e362c-89d6-7311-ac56-c546fdcd38c6`。
- CP7 验证完成：`process/checks/CP7-CR005-S03-multidataset-quality-catalog-readers-VERIFICATION-DONE.md`，结论 `PASS`；建议 meta-po 收敛为 `verified`，但本 Story 状态仍等待 meta-po 最终回写。
- 验证调度证据：`process/handoffs/META-QA-CR005-S03-CP7-VERIFY-2026-05-17.md` 记录主线程真实 `spawn_agent` 调度 meta-qa/qa-shi the 2nd，agent_id/thread_id=`019e363c-9916-7971-980a-699bcf023852`。
- 边界：本轮只完成 S03 CP7 验证；未进入 S04/S05/S06、Backtrader、真实联网或真实写 lake，未修改实现代码、`pyproject.toml` 或 `uv.lock`。
