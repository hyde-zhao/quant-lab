---
story_id: "CR008-S03-research-dataset-builder"
title: "统一 research dataset builder"
story_slug: "research-dataset-builder"
status: "verified"
priority: "P0"
wave: "CR008-BATCH-A"
change_id: "CR-008"
depends_on: ["CR008-S01-research-input-contract-and-report-metadata", "CR008-S02-proxy-real-benchmark-field-separation"]
dependency_contracts:
  - upstream: "CR008-S01-research-input-contract-and-report-metadata"
    type: "contract"
    required: "`ResearchInputMetadata` 字段已冻结"
  - upstream: "CR008-S02-proxy-real-benchmark-field-separation"
    type: "contract"
    required: "benchmark 字段隔离和 missing 语义已冻结"
file_ownership:
  primary:
    - "engine/research_dataset.py"
    - "tests/test_cr008_research_dataset_builder.py"
  shared:
    - "engine/data_loader.py"
    - "market_data/readers.py"
  merge_owner: "CR008-S03-research-dataset-builder"
  forbidden:
    - "market_data/connectors/**"
    - "market_data/runtime.py"
    - "market_data/storage.py"
    - "data/**"
    - "reports/data_quality_report.csv"
    - ".env"
    - "credentials"
    - "delivery/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#25.4"
    - "process/ARCHITECTURE-DECISION.md#adr-026research_dataset_builder-只读消费-canonicalgold不触发补数"
    - "process/stories/CR008-S03-research-dataset-builder.md"
  status: "cp5-approved"
  cp5_batch: "CR008-BATCH-A"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  required_contracts:
    - "research_input_v1 contract frozen"
    - "proxy/real benchmark field contract frozen"
    - "CR008-BATCH-A CP5 approved"
  file_conflict_free: true
  cp5_required: true
  implementation_allowed: true
  implementation_scope: "offline-only"
  dev_handoff: "process/handoffs/META-DEV-CR008-S03-IMPLEMENT-2026-05-21.md"
  dev_agent_name: "dev-xu"
  dev_agent_id: "019e4b3c-b66b-7de0-8e8b-cc57c61779e0"
  dev_started_at: "2026-05-21T23:52:14+08:00"
cp6_status: "PASS"
cp6_checkpoint: "process/checks/CP6-CR008-S03-research-dataset-builder-CODING-DONE.md"
cp6_completed_at: "2026-05-22T00:04:41+08:00"
cp7_handoff: "process/handoffs/META-QA-CR008-S03-CP7-VERIFY-2026-05-22.md"
cp7_status: "PASS"
cp7_agent_name: "qa-he"
cp7_agent_id: "019e4b4b-6f0b-7a63-88f5-e0d3174b8b31"
cp7_started_at: "2026-05-22T00:08:18+08:00"
cp7_checkpoint: "process/checks/CP7-CR008-S03-research-dataset-builder-VERIFICATION-DONE.md"
cp7_completed_at: "2026-05-22T00:11:17+08:00"
verified_at: "2026-05-22T00:14:41+08:00"
created_at: "2026-05-21"
updated_at: "2026-05-22T00:14:41+08:00"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
---

# CR008-S03：统一 research dataset builder

## 目标

新增只读 `research_dataset_builder`，统一构建研究所需的价格、日历、benchmark、universe、metadata 和 gate result。builder 只消费 `market_data.readers` 与 benchmark resolver，不触发 fetch/backfill。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | CR008-AC-005、CR008-AC-006 |
| HLD | §25.4、§25.5、§25.7 |
| ADR | ADR-026 |

## 开发上下文（dev_context）

**背景说明**：实验十五已证明因子框架可跑，但入口分散。CR008 要求所有严肃研究消费统一从 builder 获取数据和 metadata。

**输入文件**：CR008-S01 / S02 Story、`market_data/readers.py` 合同、`market_data/benchmarks.py` 合同。

**输出文件**：`engine/research_dataset.py`、`engine/data_loader.py`、`market_data/readers.py`、`tests/test_cr008_research_dataset_builder.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| `ResearchDatasetRequest` | lake_root、start/end、universe、benchmark_policy、adjustment_policy、forward_return_horizon | request object | 必须显式传参，不隐式读取旧 data |
| `build_research_dataset` | request、reader results、BenchmarkResult | `ResearchDataset`、`GateResult` | missing 返回 typed result，不执行补数 |

**设计约束**：

- builder 不导入 `market_data.connectors`、`market_data.runtime`、`market_data.storage`。
- builder 不读取旧 `data/**`、旧质量报告或凭据。
- builder 的 remediation spec 只能建议上游数据 job，`auto_execute=false`。

**命名规范**：使用 `ResearchDatasetRequest`、`ResearchDataset`、`GateResult`、`known_limitations`、`allowed_claims`。

**平台目标**：本地 engine 研究入口。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR008-S01 | contract | 必须引用 metadata 字段 | metadata contract frozen | request/result 字段来源 |
| CR008-S02 | contract | 必须引用 benchmark 字段隔离 | benchmark contract frozen | benchmark 字段来源 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR008-S03-T1 | 创建 | `engine/research_dataset.py` | 定义 request/result/gate result 与只读 builder |
| CR008-S03-T2 | 修改 | `engine/data_loader.py` | 如需提供兼容 adapter，改为委托 builder |
| CR008-S03-T3 | 修改 | `market_data/readers.py` | 仅补只读 helper 或 result 字段，不触发 connector |
| CR008-S03-T4 | 创建 | `tests/test_cr008_research_dataset_builder.py` | 覆盖 happy path、missing、no-network、no-old-data、forbidden import |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr008_research_dataset_builder.py`。

**验证方式**：tmp lake reader fixture、BenchmarkResult monkeypatch、forbidden import scan、path access sentinel。

**依赖环境**：Python 3.11、uv、pytest；不需要真实 Tushare、NAS 或 token。

**关键验证场景**：

- prices/calendar/benchmark/universe 可用时返回 ResearchDataset。
- reader missing 时返回 typed missing，不自动补数。
- connector/runtime/storage import 次数为 0。
- 旧 data / old quality report / credentials access 次数为 0。

## 量化验收标准（acceptance_criteria）

- [ ] builder 消费路径网络调用次数为 0。
- [ ] forbidden import 次数为 0。
- [ ] missing remediation `auto_execute=false`。
- [ ] `ResearchDataset` metadata 覆盖 S01/S02 必填字段。
- [ ] tmp fixture 测试覆盖 available 和 required_missing 两类路径。

## 阻塞说明

无 BLOCKING。S04/S05/S06 会共享 `engine/research_dataset.py`，开发阶段默认串行。
