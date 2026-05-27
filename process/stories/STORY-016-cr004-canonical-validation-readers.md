---
story_id: "STORY-016"
title: "CR-004 canonical 标准化、质量校验与只读 reader"
story_slug: "cr004-canonical-validation-readers"
status: "verified"
priority: "P0"
wave: "CR4-W2"
depends_on: ["STORY-015"]
dependency_contracts:
  - upstream: "STORY-015"
    type: "runtime"
    required: "raw/manifest 格式可由 normalization 消费"
file_ownership:
  primary:
    - "market_data/normalization.py"
    - "market_data/validation.py"
    - "market_data/readers.py"
    - "market_data/catalog.py"
    - "tests/test_market_data_normalization_validation_readers.py"
  shared:
    - "market_data/contracts.py"
    - "market_data/lake_layout.py"
  merge_owner: "STORY-016"
  forbidden:
    - "engine/**"
    - "experiments/**"
    - "delivery/**"
    - "market_data/connectors/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#214-数据湖分层"
    - "process/ARCHITECTURE-DECISION.md#adr-009回测与实验主路径只读-market_data-数据湖"
    - "process/ARCHITECTURE-DECISION.md#adr-011parquet-数据湖-canonical-schema-与-manifest-契约"
    - "process/stories/STORY-016-cr004-canonical-validation-readers.md"
  status: "approved"
  lld_path: "process/stories/STORY-016-cr004-canonical-validation-readers-LLD.md"
  cp5_precheck: "process/checks/CP5-CR004-BATCH-B-STORY-016-LLD-PRECHECK.md"
  cp5_review: "checkpoints/CP5-CR004-BATCH-B-STORY-016-LLD-REVIEW.md"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  cp5_required: true
  cp5_status: "approved"
  implementation_status: "completed"
  verification_status: "PASS"
  cp7_checkpoint: "process/checks/CP7-STORY-016-cr004-canonical-validation-readers-VERIFICATION-DONE.md"
created_at: "2026-05-17"
updated_at: "2026-05-17"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-004"
---

# STORY-016：CR-004 canonical 标准化、质量校验与只读 reader

## 目标

从 STORY-015 产出的 raw + manifest 派生 canonical parquet，输出 quality/catalog，并提供不触发 connector、不联网、不写入数据湖的只读 reader。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | CR-004-AC-004, CR-004-AC-005；继承 REQ-052、REQ-056、REQ-057 |
| HLD | §21.4 数据湖分层；§21.7 关键流程；§21.8 非功能需求 |
| ADR | ADR-009, ADR-011 |

## 开发上下文（dev_context）

**背景说明**：CR-004 的关键读写分界是 canonical parquet。normalization 和 validation 可以写 canonical/quality/catalog；reader 只能读取 canonical/gold，不得导入 connector/runtime。

**输入文件**：`process/HLD.md`、`process/ARCHITECTURE-DECISION.md`、STORY-014/015 Story 与 LLD、`market_data/contracts.py`、`market_data/lake_layout.py`、`market_data/storage.py`。

**输出文件**：`market_data/normalization.py`、`market_data/validation.py`、`market_data/readers.py`、`market_data/catalog.py`、`tests/test_market_data_normalization_validation_readers.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 约束 |
|---|---|---|---|
| `normalize_run(manifest_path, lake_root, dataset)` | manifest、raw 路径、schema registry | canonical parquet、normalization summary | 未知 source/interface/schema fail fast |
| `validate_dataset(dataset, lake_root, expected_range)` | canonical、manifest、catalog | quality result | 检查字段缺失、重复键、价格非负、覆盖区间、manifest 一致性 |
| `CatalogStore` | validation summary | catalog JSON 或 parquet | 至少记录 dataset、schema_version、coverage、quality_status、latest_manifest_run_id |
| `read_canonical(dataset, filters)` | canonical/gold 路径、日期、symbols | pandas DataFrame 或 typed result | 不导入 connector/runtime；不写文件；缺失数据结构化失败 |

**设计约束**：

- `readers.py` 不得 import `market_data.connectors` 或 `market_data.runtime`。
- canonical schema 必须从 STORY-014 契约读取，不在本 Story 另起不兼容字段。
- 价格异常规则：真实价格应为正数；fake 数据可允许 0 仅当契约明确为非价格数据，否则异常。
- quality status 至少包含 `pass` / `warn` / `fail` 或 CR-004 等价状态。
- quality result 第一版必须固定输出 CSV 与 Markdown；CSV 是 canonical source，Markdown 只作为人类可读渲染。
- CSV 中复杂列表字段必须使用 JSON 字符串并以 `_json` 后缀命名；质量报告必须披露 `fetch_status` 与 `dataset_status`，不得只输出泛化 `status`。
- raw 到 dataset 只允许显式 `target_dataset` 或 exact interface 映射；禁止模糊匹配、相似度匹配、contains 匹配或自动猜测。
- prices 缺失率第一版主分母为 `open_trade_dates_in_requested_range * target_symbols`；quality result 必须披露 `denominator_mode` 和 non-PIT universe 风险。
- 所有质量阈值必须显式配置或来自可追溯默认常量；不得在 validation 逻辑中写隐藏魔法数。
- 每个 dataset quality result 必须输出 coverage 字段：`requested_start`、`requested_end`、`actual_start`、`actual_end`、`requested_symbols_count`、`actual_symbols_count`、`open_trade_dates_count`、`expected_rows`、`actual_rows`、`missing_rows`、`missing_rate`。
- 每份质量报告必须输出可复现字段：`run_id`、`generated_at`、`source_name`、`source_interface`、`target_dataset`、`input_config_hash`。
- 第一版接受 non-PIT 股票池；缺 `is_pit_universe` 时必须设置 `is_pit_universe=false` 并强制披露 `universe_mode`、`pit_status` 和 survivorship bias 风险。
- catalog 首轮可用 JSON，后续可迁移 parquet。

**命名规范**：canonical dataset 名使用 `prices`、`index_members`、`trade_calendar` 或 STORY-014 registry 中的 exact 名称；quality 输出字段使用 snake_case。

**平台目标**：本地 parquet 数据湖标准化与只读消费面。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| STORY-015 | runtime | 可在 raw/manifest contract 冻结后起草 LLD | 默认等待 STORY-015 verified；若 contract 依赖被 CP5 冻结可并行开发非冲突文件 | 本 Story 消费 raw/manifest，不修改 connector |

### 文件系统布局

```text
market_data/
├── normalization.py
├── validation.py
├── catalog.py
└── readers.py
tests/
└── test_market_data_normalization_validation_readers.py
```

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| S016-T1 | 创建 | `market_data/normalization.py` | 读取 raw/manifest，派生 canonical parquet |
| S016-T2 | 创建 | `market_data/validation.py` | 实现字段、重复、价格、覆盖、manifest 一致性检查 |
| S016-T3 | 创建 | `market_data/catalog.py` | 写入和读取最小 catalog |
| S016-T4 | 创建 | `market_data/readers.py` | 提供只读 canonical/gold reader |
| S016-T5 | 创建 | `tests/test_market_data_normalization_validation_readers.py` | 覆盖 normalize/validate/catalog/readers 和 no-network/no-connector import |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_market_data_normalization_validation_readers.py`；静态扫描 `market_data/readers.py` 中不得出现 connector/runtime import。

**验证方式**：单元测试 + 临时 parquet 数据湖 + 静态扫描。

**依赖环境**：Python 3.11、uv、pytest、pandas、pyarrow；不需要网络或真实行情。

**关键验证场景**：

- 从 fake raw + manifest 生成 canonical parquet。
- 缺必需字段时 validation fail。
- 重复 `(trade_date, symbol)` 时 validation fail 或 warn，按 LLD 决策。
- 负价格被标记异常。
- reader 只读 canonical 并按 date/symbol filter 返回数据。

## 量化验收标准（acceptance_criteria）

- [ ] canonical prices parquet 至少包含 5 个必需字段，且 schema_version 可追溯。
- [ ] validation 至少覆盖 5 类检查：字段缺失、重复键、异常价格、覆盖区间、manifest 一致性。
- [ ] quality result 至少输出 dataset、quality_status、fetch_status、dataset_status、coverage、denominator_mode、thresholds、复现字段和 issue_count。
- [ ] quality CSV 为 canonical source，Markdown 仅为人类可读渲染；复杂列表字段使用 `_json` 后缀 JSON 字符串。
- [ ] raw 到 dataset 映射只使用显式 `target_dataset` 或 exact interface；禁止模糊、相似度、contains 或自动猜测。
- [ ] catalog 至少记录 dataset、schema_version、coverage、quality_status、latest_manifest_run_id。
- [ ] reader 网络调用次数为 0，且静态上不导入 connector/runtime。
- [ ] 不修改 `engine/**`、`experiments/**`、`delivery/**`。

## 后续 LLD 输入约束

LLD 必须定义 canonical 文件分区策略、schema 演进策略、quality 状态阈值、reader filter API 和异常类型，并消费 `process/constraints/CR004-QUALITY-DATALOADER-CONFIRMATION-CONSTRAINTS-2026-05-17.md` 中的质量报告、coverage、fetch/dataset 双状态、non-PIT 披露和可复现性门禁。若需要为了 tests 增加 fixture，必须使用临时目录或小型合成数据，不得提交真实行情。

## 阻塞说明

无 BLOCKING；真实沪深 300 gold 数据集口径仍为 OPEN，将由 STORY-018 处理为只读契约。
