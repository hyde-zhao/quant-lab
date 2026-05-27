---
story_id: "CR008-S01-research-input-contract-and-report-metadata"
title: "research input 合同与报告 metadata"
story_slug: "research-input-contract-and-report-metadata"
status: "verified"
priority: "P0"
wave: "CR008-BATCH-A"
change_id: "CR-008"
depends_on: ["CR007-S02-benchmark-calendar-backfill"]
dependency_contracts:
  - upstream: "CR007-S02-benchmark-calendar-backfill"
    type: "contract"
    required: "`BenchmarkResult`、coverage denominator 和 missing reason 字段已冻结"
file_ownership:
  primary:
    - "tests/test_cr008_research_input_metadata.py"
  shared:
    - "engine/research_dataset.py"
    - "experiments/reporting.py"
    - "experiments/run_experiment_14.py"
    - "experiments/run_experiment_15_factor_framework.py"
  merge_owner: "CR008-S01-research-input-contract-and-report-metadata"
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
    - "process/HLD.md#25-cr-008-研究级数据层口径硬化增量设计"
    - "process/ARCHITECTURE-DECISION.md#adr-024research_input_v1-作为唯一新研究入口与报告-metadata-合同"
    - "process/stories/CR008-S01-research-input-contract-and-report-metadata.md"
  status: "cp5-approved"
  cp5_batch: "CR008-BATCH-A"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  required_contracts:
    - "CR008 CP3/CP4 approved"
    - "CR008-BATCH-A CP5 approved"
    - "CR007-S02 benchmark/calendar contract frozen"
  file_conflict_free: true
  cp5_required: true
  implementation_allowed: true
  implementation_scope: "offline-only"
  dev_handoff: "process/handoffs/META-DEV-CR008-S01-IMPLEMENT-2026-05-21.md"
cp6_status: "PASS"
cp6_checkpoint: "process/checks/CP6-CR008-S01-research-input-contract-and-report-metadata-CODING-DONE.md"
cp6_completed_at: "2026-05-21T22:54:43+08:00"
cp7_handoff: "process/handoffs/META-QA-CR008-S01-CP7-VERIFY-2026-05-21.md"
cp7_checkpoint: "process/checks/CP7-CR008-S01-research-input-contract-and-report-metadata-VERIFICATION-DONE.md"
cp7_status: "PASS"
cp7_completed_at: "2026-05-21T23:19:44+08:00"
cp7_reverify_handoff: "process/handoffs/META-QA-CR008-S01-CP7-REVERIFY-2026-05-21.md"
blocker_fix_handoff: "process/handoffs/META-DEV-CR008-S01-CP7-BLOCKER-FIX-2026-05-21.md"
blocker_fix_status: "PASS"
blocker_fix_checkpoint: "process/checks/CP6-CR008-S01-CP7-BLOCKER-FIX-CODING-DONE.md"
created_at: "2026-05-21"
updated_at: "2026-05-21T23:23:48+08:00"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
---

# CR008-S01：research input 合同与报告 metadata

## 目标

定义 `research_input_v1` 和新研究报告强制 metadata 合同，使所有 CR008 后的新报告都能披露数据 lineage、coverage、benchmark、universe、复权、label window、quality/readiness 和 known limitations。历史报告保持 legacy，不作为 current truth 或 coverage proof。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | CR008-AC-001、CR008-AC-002 |
| HLD | §25.1、§25.4、§25.7 |
| ADR | ADR-024 |

## 开发上下文（dev_context）

**背景说明**：实验十四和实验十五暴露报告 metadata 口径不统一。CR008 要求新报告必须通过统一 research input metadata 描述数据、benchmark、股票池、复权和限制项。

**输入文件**：`process/HLD.md` §25、`process/ARCHITECTURE-DECISION.md` ADR-024、CR008 变更单、CR007-S02 LLD。

**输出文件**：`engine/research_dataset.py`、`experiments/reporting.py`、`experiments/run_experiment_14.py`、`experiments/run_experiment_15_factor_framework.py`、`tests/test_cr008_research_input_metadata.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| `ResearchInputMetadata` | dataset coverage、BenchmarkResult、universe metadata、label horizon、quality/readiness | dict / dataclass metadata | 必填字段缺失时报告生成失败 |
| report metadata writer | report kind、research input metadata、known limitations | Markdown / CSV metadata section | 不读取旧报告内容；不写真实 lake |

**设计约束**：

- 新报告 metadata 必须包含 `manifest_run_id` 或 `source_run_id`、coverage start/end、benchmark status、universe mode、adjustment policy、label window、quality/readiness、known limitations。
- 旧 `reports/data_quality_report.csv` 只能被标记为 legacy，不得作为 current quality truth。
- 不导入 connector/runtime/storage，不触发 backfill。

**命名规范**：使用 `research_input_v1`、`coverage_start`、`coverage_end`、`benchmark_status`、`universe_mode`、`label_available_end`、`known_limitations`。

**平台目标**：本地 Python 研究工具；默认离线、tmp fixture、uv 运行。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR007-S02 | contract | 可基于 confirmed LLD 起草 | S02 BenchmarkResult 字段冻结 | 只依赖字段合同，不要求真实 benchmark 已抓取 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR008-S01-T1 | 创建/修改 | `engine/research_dataset.py` | 定义 metadata dataclass / typed dict 和必填字段校验 |
| CR008-S01-T2 | 创建/修改 | `experiments/reporting.py` | 创建报告 metadata 写入 helper |
| CR008-S01-T3 | 修改 | `experiments/run_experiment_14.py` / `run_experiment_15_factor_framework.py` | 接入 metadata helper 或保留兼容 wrapper |
| CR008-S01-T4 | 创建 | `tests/test_cr008_research_input_metadata.py` | 覆盖必填字段、legacy report 边界和 no old data/no credentials |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr008_research_input_metadata.py`。

**验证方式**：tmp metadata fixture、BenchmarkResult monkeypatch、Markdown/CSV 字段断言、静态 import/path scan。

**依赖环境**：Python 3.11、uv、pytest；不需要 Tushare token、不需要 NAS、不联网。

**关键验证场景**：

- metadata 必填字段全部存在。
- 缺 `benchmark_status`、`universe_mode`、`label_available_end` 等字段时 fail。
- 旧 `reports/data_quality_report.csv` 只作为字符串 legacy 提及，不读取内容。
- connector/runtime/storage import 次数为 0。

## 量化验收标准（acceptance_criteria）

- [ ] 新报告 metadata 必填字段覆盖率为 100%。
- [ ] 旧报告 current truth / coverage proof 使用次数为 0。
- [ ] builder / reporting 消费路径网络调用次数为 0。
- [ ] `data/**`、旧 `reports/data_quality_report.csv`、`.env`、token、NAS 凭据操作次数为 0。
- [ ] `tests/test_cr008_research_input_metadata.py` 覆盖必填字段缺失和 legacy report 边界。

## 阻塞说明

无 BLOCKING。CR008 CP3/CP4/CP5 未通过前不得进入实现。
