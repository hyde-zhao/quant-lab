---
story_id: "CR008-S02-proxy-real-benchmark-field-separation"
title: "proxy / real benchmark 字段隔离"
story_slug: "proxy-real-benchmark-field-separation"
status: "verified"
priority: "P0"
wave: "CR008-BATCH-A"
change_id: "CR-008"
depends_on: ["CR007-S02-benchmark-calendar-backfill", "CR008-S01-research-input-contract-and-report-metadata"]
dependency_contracts:
  - upstream: "CR007-S02-benchmark-calendar-backfill"
    type: "contract"
    required: "`hs300_index` + `trade_calendar` coverage gate 与 BenchmarkResult missing reason 已冻结"
  - upstream: "CR008-S01-research-input-contract-and-report-metadata"
    type: "contract"
    required: "`research_input_v1` benchmark metadata 字段已冻结"
file_ownership:
  primary:
    - "tests/test_cr008_proxy_real_benchmark_fields.py"
  shared:
    - "experiments/run_experiment_13.py"
    - "experiments/run_experiment_15_factor_framework.py"
    - "market_data/benchmarks.py"
  merge_owner: "CR008-S02-proxy-real-benchmark-field-separation"
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
    - "process/HLD.md#25.7"
    - "process/ARCHITECTURE-DECISION.md#adr-025proxy-benchmark-与真实-benchmark-字段强隔离"
    - "process/stories/CR008-S02-proxy-real-benchmark-field-separation.md"
  status: "cp5-approved"
  cp5_batch: "CR008-BATCH-A"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  required_contracts:
    - "CR007-S02 BenchmarkResult coverage contract frozen"
    - "CR008-S01 research input metadata contract frozen"
    - "CR008-BATCH-A CP5 approved"
  file_conflict_free: true
  cp5_required: true
  implementation_allowed: true
  implementation_scope: "offline-only"
  dev_handoff: "process/handoffs/META-DEV-CR008-S02-IMPLEMENT-2026-05-21.md"
cp6_status: "PASS"
cp6_checkpoint: "process/checks/CP6-CR008-S02-proxy-real-benchmark-field-separation-CODING-DONE.md"
cp6_completed_at: "2026-05-21T23:35:20+08:00"
cp7_handoff: "process/handoffs/META-QA-CR008-S02-CP7-VERIFY-2026-05-21.md"
cp7_status: "PASS"
cp7_agent_name: "qa-lv"
cp7_agent_id: "019e4b34-8ad3-74e3-9a38-b9f8730d05fe"
cp7_started_at: "2026-05-21T23:43:24+08:00"
cp7_checkpoint: "process/checks/CP7-CR008-S02-proxy-real-benchmark-field-separation-VERIFICATION-DONE.md"
cp7_completed_at: "2026-05-21T23:45:32+08:00"
verified_at: "2026-05-21T23:49:35+08:00"
created_at: "2026-05-21"
updated_at: "2026-05-21T23:49:35+08:00"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
---

# CR008-S02：proxy / real benchmark 字段隔离

## 目标

拆分代理 benchmark 与真实 `hs300_index` benchmark 的报告字段和 metadata。真实 benchmark 不可用时，报告只能写 `proxy_*` / `proxy_baseline`，真实 `hs300_*` 输出次数必须为 0。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | CR008-AC-003、CR008-AC-004 |
| HLD | §25.3、§25.7、§25.13 |
| ADR | ADR-025 |

## 开发上下文（dev_context）

**背景说明**：CR007 已要求真实 benchmark 优先，但 CR008 进一步要求字段强隔离，避免 `benchmark_total_return` 或 `excess_return` 被误读为真实沪深300。

**输入文件**：CR007-S02 LLD、CR007-S04 LLD、`process/HLD.md` §25、`process/ARCHITECTURE-DECISION.md` ADR-025。

**输出文件**：`experiments/run_experiment_13.py`、`experiments/run_experiment_15_factor_framework.py`、`market_data/benchmarks.py`、`tests/test_cr008_proxy_real_benchmark_fields.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| benchmark metadata normalization | `BenchmarkResult`、proxy metrics | `hs300_*` 或 `proxy_*` 字段 | 二者不得互相填充 |
| report comparison fields | strategy metrics、benchmark kind | CSV / Markdown fields | 缺真实 hs300 时不得写沪深300超额 |

**设计约束**：

- 缺真实 benchmark、coverage gap、quality fail、policy unconfirmed 时，`hs300_*` 字段输出次数为 0。
- proxy 只允许作为探索对照，必须带 `benchmark_missing_reason`。
- S02 不修改数据生产层，不执行真实抓取。

**命名规范**：使用 `proxy_baseline`、`proxy_total_return`、`proxy_excess_return`、`hs300_total_return`、`hs300_excess_return`、`benchmark_status`。

**平台目标**：本地实验报告字段合同，默认离线。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR007-S02 | contract | 可基于 confirmed LLD 起草 | BenchmarkResult coverage / missing reason frozen | 提供真实 benchmark 可用性判断 |
| CR008-S01 | contract | 可并行起草但需对齐 metadata 字段 | research input metadata frozen | 提供新报告字段事实源 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR008-S02-T1 | 修改 | `market_data/benchmarks.py` | 增加 benchmark metadata 字段隔离 helper 或保持接口透传 |
| CR008-S02-T2 | 修改 | `experiments/run_experiment_13.py` | 将真实 / proxy 字段分支输出 |
| CR008-S02-T3 | 修改 | `experiments/run_experiment_15_factor_framework.py` | 因子框架报告引用字段隔离语义 |
| CR008-S02-T4 | 创建 | `tests/test_cr008_proxy_real_benchmark_fields.py` | 覆盖 real available、proxy only、required missing 和 no forbidden imports |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr008_proxy_real_benchmark_fields.py`。

**验证方式**：BenchmarkResult monkeypatch、tmp report output、CSV/metadata 字段断言、AST import scan。

**依赖环境**：Python 3.11、uv、pytest；不需要 token、NAS 或真实 lake。

**关键验证场景**：

- real available 时写 `hs300_*` 并可不写 proxy。
- missing 时只写 `proxy_*` / `proxy_baseline`，不写 `hs300_*`。
- required benchmark missing 时受控失败或结构化 missing，不生成虚假 hs300。
- 旧 `data/**` 和旧质量报告操作次数为 0。

## 量化验收标准（acceptance_criteria）

- [ ] 缺真实 benchmark 时 `hs300_*` 输出次数为 0。
- [ ] proxy 字段全部使用 `proxy_*` / `proxy_baseline` 命名。
- [ ] metadata 包含 `benchmark_status`、`benchmark_kind`、`benchmark_missing_reason`。
- [ ] 相关文件 connector/runtime/storage import 次数为 0。
- [ ] 旧 `data/**`、旧质量报告、`.env` 和凭据操作次数为 0。

## 阻塞说明

无 BLOCKING。CR007-S04 在 CR008 CP3/CP4 设计确认前保持 hold，避免字段语义返工。
