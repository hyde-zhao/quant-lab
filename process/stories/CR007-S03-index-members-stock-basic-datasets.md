---
story_id: "CR007-S03-index-members-stock-basic-datasets"
title: "成分、权重与股票基础信息 readiness"
story_slug: "index-members-stock-basic-datasets"
status: "verified"
priority: "P0"
wave: "CR007-BATCH-A"
depends_on: ["CR007-S01-prices-long-horizon-backfill-planner", "CR005-S02", "CR005-S03"]
dependency_contracts:
  - upstream: "CR007-S01-prices-long-horizon-backfill-planner"
    type: "contract"
    required: "long-horizon date range、lake root 和 coverage policy 已冻结"
  - upstream: "CR005-S02"
    type: "contract"
    required: "dataset schema、PIT fields 和 normalization 规则已冻结"
  - upstream: "CR005-S03"
    type: "contract"
    required: "quality/catalog/readers 和 PIT as-of gate 已冻结"
file_ownership:
  primary:
    - "tests/test_cr007_index_members_stock_basic_datasets.py"
  shared:
    - "market_data/contracts.py"
    - "market_data/source_registry.py"
    - "market_data/connectors/tushare.py"
    - "market_data/normalization.py"
    - "market_data/validation.py"
    - "market_data/readers.py"
  merge_owner: "CR007-S03-index-members-stock-basic-datasets"
  forbidden:
    - "engine/**"
    - "experiments/**"
    - "README.md"
    - "docs/USER-MANUAL.md"
    - "data/**"
    - "reports/**"
    - ".env"
    - "credentials"
    - "delivery/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#245-高层模块与职责划分"
    - "process/ARCHITECTURE-DECISION.md#adr-021dataset-readiness-与-pit--非-pit-边界显式化"
    - "process/stories/CR007-S03-index-members-stock-basic-datasets.md"
  status: "cp5-approved"
  cp5_batch: "CR007-BATCH-A"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  required_contracts:
    - "dataset readiness status semantics frozen"
    - "PIT / non-PIT reporting contract frozen"
    - "CR007-BATCH-A CP5 approved"
  file_conflict_free: true
  cp5_required: true
  implementation_allowed: true
  implementation_scope: "offline-only"
  dev_handoff: "process/handoffs/META-DEV-CR007-S03-IMPLEMENT-2026-05-22.md"
  dev_agent_name: "dev-yang the 2nd"
  dev_agent_id: "019e4b8d-2218-76a1-85f7-ae32f58ff9c0"
  dev_started_at: "2026-05-22T01:19:45+08:00"
  previous_dev_agent_name: "dev-you"
  previous_dev_agent_id: "019e45c2-6da2-7de1-b918-edd973b5676b"
  previous_dev_status: "stalled-closed-no-output"
cp6_status: "PASS"
cp6_checkpoint: "process/checks/CP6-CR007-S03-index-members-stock-basic-datasets-CODING-DONE.md"
cp6_completed_at: "2026-05-22T01:28:12+08:00"
cp7_handoff: "process/handoffs/META-QA-CR007-S03-CP7-VERIFY-2026-05-22.md"
cp7_status: "PASS"
cp7_checkpoint: "process/checks/CP7-CR007-S03-index-members-stock-basic-datasets-VERIFICATION-DONE.md"
cp7_completed_at: "2026-05-22T01:36:18+08:00"
cp7_agent_name: "qa-shi the 2nd"
cp7_agent_id: "019e4b9a-46a8-7a12-93eb-544ab1dea396"
cp7_started_at: "2026-05-22T01:34:25+08:00"
verified_at: "2026-05-22T01:39:29+08:00"
created_at: "2026-05-20"
updated_at: "2026-05-22T01:39:29+08:00"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-007"
---

# CR007-S03：成分、权重与股票基础信息 readiness

## 目标

补齐 `index_members`、`index_weights`、`stock_basic` 的 dataset readiness：exact interface、schema、normalizer、validator、catalog、reader、PIT / 非 PIT 状态和 structured unavailable/warn 语义。PIT 不完整时不得伪装为 PIT available。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | CR007-AC-005、CR007-AC-008、CR007-AC-009 |
| HLD | §24.1、§24.5、§24.7、§24.8 |
| ADR | ADR-021 |

## 开发上下文（dev_context）

**背景说明**：当前代码存在 `index_members`、`index_weights`、`stock_basic` 常量，`index_weights` 部分链路已存在；但 Tushare registry / adapter / normalizer 对 `index_members` 和 `stock_basic` 不完整。该 Story 让 dataset 是否可用、是否 PIT、是否可被消费变成结构化状态。

**输入文件**：`market_data/contracts.py`、`market_data/source_registry.py`、`market_data/connectors/tushare.py`、`market_data/normalization.py`、`market_data/validation.py`、`market_data/readers.py`、CR005-S02/S03 Story/LLD。

**输出文件**：`market_data/contracts.py`、`market_data/source_registry.py`、`market_data/connectors/tushare.py`、`market_data/normalization.py`、`market_data/validation.py`、`market_data/readers.py`、`tests/test_cr007_index_members_stock_basic_datasets.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| registry | source=`tushare`、dataset、interface | exact provider method、target_dataset、pit_required | 未登记返回 source/interface not allowed |
| normalizer | raw/manifest success records | canonical parquet with key columns、PIT fields、lineage | 缺 PIT 字段时返回 schema/readiness error |
| reader | dataset、lake_root、date range、pit_policy | ReaderResult available/warn/unavailable/quality_failed | PIT 不完整不得 available |

**设计约束**：

- `index_weights` 不等同于 `index_members`，不能自动作为完整成分集。
- `stock_basic` 用于上市/退市/ST 等过滤前，必须定义 available/effective 字段。
- reader 不导入 connector/runtime，不触发 fetch/backfill。
- 不修改实验入口；实验消费归 CR007-S04 或后续 Story。

**命名规范**：使用 `readiness_status`、`pit_status`、`is_pit_universe`、`effective_date`、`available_date`、`available_at`。

**平台目标**：本地 canonical/gold dataset readiness 层。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR007-S03-T1 | 修改 | `market_data/contracts.py` | 补齐 index_members / stock_basic schema、key columns 和 PIT fields |
| CR007-S03-T2 | 修改 | `market_data/source_registry.py` / `connectors/tushare.py` | 补 exact interface 与 provider method，保持真实调用显式启用 |
| CR007-S03-T3 | 修改 | `market_data/normalization.py` / `validation.py` / `readers.py` | 实现 readiness、PIT gate、quality/readers 结果语义 |
| CR007-S03-T4 | 创建 | `tests/test_cr007_index_members_stock_basic_datasets.py` | 覆盖 available、PIT incomplete、quality fail、no connector/no old data |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr007_index_members_stock_basic_datasets.py`。

**验证方式**：tmp lake、raw/manifest fixture、canonical schema assertions、PIT status assertions。

**依赖环境**：Python 3.11、uv、pytest；不需要 Tushare token、不需要 NAS、不联网。

**关键验证场景**：

- `index_members`、`index_weights`、`stock_basic` 均能返回 readiness status。
- PIT 字段缺失时返回 warn/unavailable，不返回 PIT available。
- `index_weights` 不被自动当作完整 `index_members`。
- reader 网络调用和 connector/runtime 导入次数为 0。

## 量化验收标准（acceptance_criteria）

- [ ] 三类 dataset 均定义 key columns、required columns、quality/readiness status。
- [ ] PIT 不完整的 dataset 返回 PIT available 次数为 0。
- [ ] `index_weights` 自动替代 `index_members` 次数为 0。
- [ ] reader 调用 connector/runtime/storage 次数为 0。
- [ ] 旧 `data/**`、`.env`、token、NAS 凭据操作次数为 0。

## 阻塞说明

无 BLOCKING。真实成分历史完整性取决于后续真实 Tushare 授权和数据源能力；不阻塞 readiness 合同。
