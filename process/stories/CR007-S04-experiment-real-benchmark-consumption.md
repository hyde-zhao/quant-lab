---
story_id: "CR007-S04-experiment-real-benchmark-consumption"
title: "实验真实 benchmark 消费"
story_slug: "experiment-real-benchmark-consumption"
status: "verified"
priority: "P0"
wave: "CR007-BATCH-A"
depends_on: ["CR007-S02-benchmark-calendar-backfill", "CR007-S03-index-members-stock-basic-datasets"]
dependency_contracts:
  - upstream: "CR007-S02-benchmark-calendar-backfill"
    type: "contract"
    required: "`hs300_index` + `trade_calendar` coverage gate 和 BenchmarkResult policy 已冻结"
  - upstream: "CR007-S03-index-members-stock-basic-datasets"
    type: "contract"
    required: "dataset readiness、PIT / 非 PIT 状态和 proxy 说明字段已冻结"
file_ownership:
  primary:
    - "experiments/run_experiment_13.py"
    - "tests/test_cr007_experiment_real_benchmark_consumption.py"
  shared:
    - "experiments/run_experiment_10.py"
    - "experiments/run_experiment_12.py"
    - "market_data/benchmarks.py"
  merge_owner: "CR007-S04-experiment-real-benchmark-consumption"
  forbidden:
    - "market_data/connectors/**"
    - "market_data/runtime.py"
    - "market_data/storage.py"
    - "data/**"
    - "reports/**"
    - ".env"
    - "credentials"
    - "delivery/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#247-关键流程"
    - "process/ARCHITECTURE-DECISION.md#adr-020真实沪深300-benchmark-必须与交易日历同区间覆盖"
    - "process/ARCHITECTURE-DECISION.md#adr-021dataset-readiness-与-pit--非-pit-边界显式化"
    - "process/stories/CR007-S04-experiment-real-benchmark-consumption.md"
  status: "cp5-approved"
  cp5_batch: "CR007-BATCH-A"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  blocked_by: ""
  unblock_condition: "satisfied: CR007-S02/S03 CP7 PASS and CR008-BATCH-A all stories verified"
  required_contracts:
    - "CR007-S02 coverage and BenchmarkResult contract frozen"
    - "CR007-S03 readiness semantics frozen"
    - "CR007-BATCH-A CP5 approved"
  file_conflict_free: true
  cp5_required: true
  implementation_allowed: true
  implementation_scope: "offline-only"
  dev_handoff: "process/handoffs/META-DEV-CR007-S04-IMPLEMENT-2026-05-22.md"
  dev_agent_name: "dev-kong the 2nd"
  dev_agent_id: "019e4c55-7298-7420-aebd-29b3cee9ad3a"
  dev_started_at: "2026-05-22T04:58:54+08:00"
  dev_completed_at: "2026-05-22T05:08:07+08:00"
  cp6_status: "PASS"
  cp6_checkpoint: "process/checks/CP6-CR007-S04-experiment-real-benchmark-consumption-CODING-DONE.md"
  cp6_completed_at: "2026-05-22T05:08:07+08:00"
  upstream_cp7:
    - "process/checks/CP7-CR007-S02-benchmark-calendar-backfill-VERIFICATION-DONE.md"
    - "process/checks/CP7-CR007-S03-index-members-stock-basic-datasets-VERIFICATION-DONE.md"
    - "process/checks/CP7-CR008-S06-factor-research-auxiliary-data-contract-VERIFICATION-DONE.md"
cp6_status: "PASS"
cp6_checkpoint: "process/checks/CP6-CR007-S04-experiment-real-benchmark-consumption-CODING-DONE.md"
cp6_completed_at: "2026-05-22T05:08:07+08:00"
cp7_handoff: "process/handoffs/META-QA-CR007-S04-CP7-VERIFY-2026-05-22.md"
cp7_status: "PASS"
cp7_agent_name: "qa-jin the 2nd"
cp7_agent_id: "019e4c64-3c4f-7593-b962-26a379b184e8"
cp7_started_at: "2026-05-22T05:15:00+08:00"
cp7_checkpoint: "process/checks/CP7-CR007-S04-experiment-real-benchmark-consumption-VERIFICATION-DONE.md"
cp7_completed_at: "2026-05-22T05:17:26+08:00"
verified_at: "2026-05-22T05:20:49+08:00"
created_at: "2026-05-20"
updated_at: "2026-05-22T05:20:49+08:00"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-007"
---

# CR007-S04：实验真实 benchmark 消费

## 目标

修改实验十三，使其优先消费真实 `hs300_index` benchmark；复核实验十/十二参数和 metadata 与 CR-007 benchmark policy 一致。真实 benchmark 不可用时，代理只能作为 `proxy_baseline` 对照，不能填充 hs300 字段或声明沪深300超额收益。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | CR007-AC-010、CR007-AC-011 |
| HLD | §24.7、§24.8、§24.13 |
| ADR | ADR-020、ADR-021 |

## 开发上下文（dev_context）

**背景说明**：`experiments/run_experiment_10.py` 和 `run_experiment_12.py` 已有 `BenchmarkResult` 只读消费逻辑；`run_experiment_13.py` 当前仍固定构建“同股票池等权”代理。CR-007 要求实验十三在真实 benchmark 可用时使用 `hs300_index`，不可用时明确代理边界。

**输入文件**：`experiments/run_experiment_13.py`、`experiments/run_experiment_10.py`、`experiments/run_experiment_12.py`、`market_data/benchmarks.py`、CR005-S04 Story/LLD、CR007-S02/S03 Story。

**输出文件**：`experiments/run_experiment_13.py`、必要时修改 `experiments/run_experiment_10.py`、`experiments/run_experiment_12.py`、`market_data/benchmarks.py`、`tests/test_cr007_experiment_real_benchmark_consumption.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| experiment 13 benchmark args | lake_root、start/end、require_benchmark、allow_warn、benchmark_kind | BenchmarkResult metadata、真实 benchmark metrics 或 proxy_baseline | 不联网、不自动 backfill |
| comparison report | strategy metrics、benchmark metrics、benchmark metadata | cross_strategy_comparison、diagnostics、benchmark equity CSV | 缺真实 hs300 时不得写 hs300 excess |
| proxy fallback | close_df、initial_cash | `proxy_baseline` metrics | 只作对照，不填充 `hs300_index` |

**设计约束**：

- `run_experiment_13.py` 不导入 `market_data.connectors`、`market_data.runtime`、`market_data.storage`。
- 缺真实 benchmark 时可以继续输出代理对照，但字段名必须是 `proxy_baseline`。
- 真实 benchmark coverage 不完整时不得声明“vs 沪深300超额收益”。
- 不写真实 `reports/**` 作为设计阶段动作；后续实现测试使用 tmp output。

**命名规范**：使用 `hs300_index`、`proxy_baseline`、`benchmark_status`、`benchmark_missing_reason`、`benchmark_kind`。

**平台目标**：本地实验入口只读 benchmark 消费。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR007-S04-T1 | 修改 | `experiments/run_experiment_13.py` | 接入 `resolve_hs300_benchmark`，优先真实 benchmark |
| CR007-S04-T2 | 修改 | `experiments/run_experiment_10.py` / `run_experiment_12.py` | 复核参数、metadata 和 missing 行为与 CR-007 一致 |
| CR007-S04-T3 | 修改 | `market_data/benchmarks.py` | 如需补充实验十三消费所需 metadata，不改变数据层边界 |
| CR007-S04-T4 | 创建 | `tests/test_cr007_experiment_real_benchmark_consumption.py` | 覆盖 real available、required_missing、proxy_baseline、no network/no connector |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr007_experiment_real_benchmark_consumption.py`。

**验证方式**：monkeypatch benchmark resolver、tmp output dir、CSV metadata assertions、静态 import 边界扫描。

**依赖环境**：Python 3.11、uv、pytest；不需要 Tushare token、不需要 NAS、不联网。

**关键验证场景**：

- BenchmarkResult available 且 coverage=1.0 时，实验十三使用真实 benchmark。
- BenchmarkResult required_missing 时，实验十三输出 proxy_baseline 和 missing reason，不写 hs300 excess。
- `--require-benchmark` 或等价策略启用时缺失 benchmark 可阻断或显式失败。
- 实验十三 connector/runtime/storage 导入次数为 0。

## 量化验收标准（acceptance_criteria）

- [x] 实验十三真实 benchmark available 路径输出 hs300 metadata 字段不少于 8 个。
- [x] 缺真实 benchmark 时 `proxy_baseline` 使用次数可大于 0，但填充 `hs300_index` 字段次数为 0。
- [x] 消费路径网络调用、connector/runtime/storage 调用和真实 lake 写入次数均为 0。
- [x] 实验十/十二/十三 benchmark missing 语义一致。
- [x] 旧 `data/**`、`.env`、token、NAS 凭据操作次数为 0。

## 阻塞说明

无 BLOCKING。若用户要求缺真实 benchmark 时实验十三必须 hard fail，需要在 CP4 人工确认中修改默认策略。
