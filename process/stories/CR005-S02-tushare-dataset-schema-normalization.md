---
story_id: "CR005-S02"
title: "Tushare 多 dataset schema、PIT 字段与复权 normalization"
story_slug: "tushare-dataset-schema-normalization"
status: "verified"
priority: "P0"
wave: "CR5-W1"
depends_on: ["CR005-S01", "STORY-016"]
dependency_contracts:
  - upstream: "CR005-S01"
    type: "contract"
    required: "Tushare raw/manifest result contract frozen"
  - upstream: "STORY-016"
    type: "contract"
    required: "canonical prices normalization 基础契约稳定"
file_ownership:
  primary:
    - "tests/test_market_data_tushare_datasets.py"
  shared:
    - "market_data/contracts.py"
    - "market_data/source_registry.py"
    - "market_data/normalization.py"
  merge_owner: "CR005-S02"
  forbidden:
    - "engine/**"
    - "experiments/**"
    - "market_data/connectors/tushare.py"
    - "market_data/readers.py"
    - "data/**"
    - "reports/**"
    - "delivery/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#224-dataset-与接口契约"
    - "process/ARCHITECTURE-DECISION.md#adr-014cr-005-多-dataset-schema-与-quality-gate-先于消费方冻结"
    - "process/ARCHITECTURE-DECISION.md#adr-017pit-与复权由-pandas-数据层保证backtrader-只消费干净输入"
    - "process/stories/CR005-S02-tushare-dataset-schema-normalization.md"
  status: "approved"
  lld_path: "process/stories/CR005-S02-tushare-dataset-schema-normalization-LLD.md"
  cp5_precheck: "process/checks/CP5-CR005-S02-tushare-dataset-schema-normalization-LLD-IMPLEMENTABILITY.md"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  required_contracts:
    - "CR005-S01 `hs300_index` backfill job spec frozen"
    - "Tushare `index_daily` raw -> canonical exact mapping frozen before implementation"
  file_conflict_free: true
  cp5_required: true
  implementation_status: "cp7-reverification-pass"
  cp6_checkpoint: "process/checks/CP6-CR005-S02-tushare-dataset-schema-normalization-CODING-DONE.md"
  cp7_checkpoint: "process/checks/CP7-CR005-S02-tushare-dataset-schema-normalization-VERIFICATION-DONE.md"
  verification_status: "pass"
  blocker_fix_status: "completed"
  cp7_reverification_status: "pass"
  cp7_reverification_handoff: "process/handoffs/META-QA-CR005-S02-CP7-REVERIFY-2026-05-17.md"
  resolved_blockers:
    - "CR005-S02-BLOCKER-001: _parse_date 已使用真实日历解析校验 %Y%m%d 与 ISO 输入，非法月份、非法日期和不可解析值 fail fast"
    - "CR005-S02-BLOCKER-002: prices.daily 已支持与 exact prices.adj_factor success records 按 trade_date,symbol join，缺因子、duplicate key、policy 冲突和 key 不匹配均 fail fast"
  blocker_fix_handoff: "process/handoffs/META-DEV-CR005-S02-CP7-BLOCKER-FIX-2026-05-17.md"
created_at: "2026-05-17"
updated_at: "2026-05-17T20:46:51+08:00"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-005"
---

# CR005-S02：Tushare 多 dataset schema、PIT 字段与复权 normalization

## 目标

为 Tushare 写湖链路扩展多 dataset 契约和 raw -> canonical/gold normalization，至少覆盖 `prices`、`hs300_index`、`trade_calendar`、`index_weights` 四个 P0 dataset。同步冻结 PIT 可得性字段和复权价格生成契约：非行情数据定义 `available_date` / `effective_date` / `available_at`，行情层保存 `adj_factor` 与统一 `adjustment_policy` 下的 adjusted price。

`hs300_index` 必须同时冻结 benchmark accuracy 所需字段与 exact raw -> canonical 映射，使 CR005-S04 能基于本地数据返回 `BenchmarkResult`，而不是在 resolver 中猜测 Tushare 字段或自动补数。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | CR005-AC-003、CR005-AC-004、CR005-AC-005、CR005-AC-006、CR005-AC-012、CR005-AC-013、CR005-AC-016 |
| HLD | §22.4、§22.7、§22.8 |
| ADR | ADR-014、ADR-017 |

## 开发上下文（dev_context）

**背景说明**：当前 `market_data/contracts.py` 只定义 `prices/index_members/trade_calendar`，`normalization.py` 只支持 `prices`。CR-005 要在消费方接入前冻结多 dataset schema、PIT 可得性字段和复权价格契约，避免 Backtrader 或实验各自猜字段、各自实现 as-of join 或各自计算复权因子。

**输入文件**：`market_data/contracts.py`、`market_data/source_registry.py`、`market_data/normalization.py`、`process/HLD.md`、`process/ARCHITECTURE-DECISION.md`、CR005-S01 Story。

**输出文件**：`market_data/contracts.py`、`market_data/source_registry.py`、`market_data/normalization.py`、`tests/test_market_data_tushare_datasets.py`。

**接口约定**：

| Dataset | Key | 必需字段下限 | 说明 |
|---|---|---|---|
| `prices` | `trade_date + symbol` | `open/high/low/close`、`adjusted_open/adjusted_high/adjusted_low/adjusted_close` 或 LLD 确认的等价 adjusted price、`adj_factor`、`source`、`source_run_id`、`adjustment_policy`、`available_at` | 股票行情、收益、技术指标、forward return 的统一复权价格输入 |
| `hs300_index` | `trade_date + index_code` | `close`、`pre_close` 或 `pct_chg`、`benchmark_kind`、`source`、`source_interface`、`source_run_id`、`schema_version`、`available_at`、`lineage_raw_checksum` 或等价 lineage | 本地沪深 300 基准；默认候选 exact interface 为 `hs300_index.daily`，映射 Tushare `index_daily(ts_code='399300.SZ')` |
| `trade_calendar` | `trade_date + exchange` | `is_open`、`pretrade_date`、`source`、`source_interface`、`source_run_id` | coverage 分母；CR005-S03 以 open dates 作为 hs300 coverage denominator |
| `index_weights` | `trade_date + index_code + con_code` | `weight`、`effective_date`、`available_date`、`available_at`、`source_run_id` | 成分权重和 PIT 股票池输入 |
| `stock_basic` | `symbol` | `list_date`、`delist_date`、`status`、`effective_date`、`available_date`、`available_at`、`source_run_id` | 后续股票池过滤的非行情 PIT 输入 |

**设计约束**：

- raw 到 dataset 只允许显式 `target_dataset` 或 exact interface mapping。
- `hs300_index` raw -> canonical 映射必须列出 raw field、canonical field、type、nullable、unit、key、dedupe rule、sort rule、date parser、index code normalization 和 missing policy。
- 禁止 fuzzy、contains、相似度、自动猜测 dataset。
- 非行情 dataset 必须声明 as-of join 所需字段；参与回测的记录必须能在 CR005-S03 被验证为 `available_at <= decision_time`。
- 行情 dataset 必须在 normalization 层生成或保存 adjusted price；价格收益、技术指标和 forward return 不得在下游重新选择复权口径。
- 不读取 `TUSHARE_TOKEN`，不导入真实 provider。
- 不修改 reader、实验或 Backtrader。

**命名规范**：dataset 使用 snake_case；接口名采用 `<dataset>.<frequency_or_kind>`，例如 `hs300_index.daily`。

**平台目标**：本地 Parquet 数据湖 schema 扩展；无真实数据写入。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR005-S02-T1 | 修改 | `market_data/contracts.py` | 增加 dataset 常量、schema、key columns、PIT 可得性字段和 status 枚举扩展 |
| CR005-S02-T2 | 修改 | `market_data/source_registry.py` | 增加 Tushare exact interface -> target_dataset 映射，标注行情/非行情 dataset |
| CR005-S02-T3 | 修改 | `market_data/normalization.py` | 支持多 dataset normalization、lineage 校验、`adj_factor` 合并、adjusted price 生成和 `hs300_index` raw->canonical 映射 |
| CR005-S02-T4 | 创建 | `tests/test_market_data_tushare_datasets.py` | 覆盖 exact mapping、unknown dataset fail、必需字段缺失、PIT 字段缺失、复权冲突、hs300 字段类型/单位/重复 key fixture |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_market_data_tushare_datasets.py`。

**验证方式**：临时 raw/manifest fixture + parquet schema 断言。

**依赖环境**：Python 3.11、uv、pytest、pandas、pyarrow；不需要网络或 token。

**关键验证场景**：

- `target_dataset=hs300_index` 可输出 canonical/gold 候选路径。
- Tushare `index_daily` fixture 可映射为 `hs300_index` canonical，保留 index_code、benchmark_kind、source_interface、source_run_id 和 raw checksum 或等价 lineage。
- unknown interface / unknown target_dataset 结构化失败。
- `prices` 复权口径缺失、`adj_factor` 缺失或 adjusted price 混用失败。
- 非行情 dataset 缺少 `available_date` / `effective_date` / `available_at` 或等价字段时 schema 校验失败。
- `index_weights` key 重复可被后续 quality 识别。

## 量化验收标准（acceptance_criteria）

- [ ] 至少 4 个 P0 dataset 有常量、schema 和 key columns。
- [ ] Tushare P0 interface 至少 4 个 exact 映射到 target_dataset。
- [ ] `hs300_index` raw -> canonical 映射表至少覆盖 raw field、canonical field、type、nullable、unit、key、dedupe rule、sort rule、date parser、index code normalization、missing policy。
- [ ] `hs300_index` canonical 字段包含 `benchmark_kind`、`source_interface`、`schema_version`、`source_run_id`、raw checksum 或等价 lineage。
- [ ] unknown dataset / unknown interface 100% fail fast。
- [ ] 参与 PIT 的非行情 dataset 100% 定义 `available_date` / `effective_date` / `available_at` 或 LLD 确认的等价字段。
- [ ] `prices` 或关联行情层 100% 保存 `adj_factor` 与 adjusted price，且 `adjustment_policy` 单次运行唯一。
- [ ] 价格收益、技术指标和 forward return 的输入字段明确指向 adjusted price，不由 Backtrader 或消费方重新计算复权因子。
- [ ] normalization 不导入 connector/runtime，不读取 token。
- [ ] 不修改 `engine/**`、`experiments/**`、`market_data/readers.py`、`data/**`、`reports/**`。

## 阻塞说明

`CR5-Q1` 仍为 OPEN：Tushare 5000 档 exact 限频和字段细节未确认。LLD 可用字段别名映射表表达候选字段，但真实实现前必须由 CP5 冻结 exact 字段。

`CR5-Q2` 仍为 OPEN：沪深 300 采用价格指数、全收益指数或其他口径尚未确认。未确认前，`benchmark_kind` 可作为待冻结字段进入 schema；真实 available 路径不得把不同口径混入同一 catalog entry。
