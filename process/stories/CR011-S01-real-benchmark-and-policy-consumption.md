---
story_id: "CR011-S01-real-benchmark-and-policy-consumption"
title: "真实 benchmark 与 policy 消费"
story_slug: "real-benchmark-and-policy-consumption"
status: "verified"
priority: "P0"
wave: "CR011-DATA-BATCH-A"
depends_on:
  - "CR010-S03-hs300-index-trade-calendar-backfill-loop"
  - "CR010-S05-catalog-coverage-production-readiness-report"
  - "CR008-S02-proxy-real-benchmark-field-separation"
dependency_contracts:
  - upstream: "CR010-S03-hs300-index-trade-calendar-backfill-loop"
    type: "runtime"
    required: "hs300_index 与 trade_calendar 的 current truth、coverage、quality/readiness 和 missing reason 可被只读消费"
  - upstream: "CR010-S05-catalog-coverage-production-readiness-report"
    type: "runtime"
    required: "catalog coverage、readiness report、publish gate 和 source_run_id lineage 可追溯"
  - upstream: "CR008-S02-proxy-real-benchmark-field-separation"
    type: "contract"
    required: "proxy_* 与 hs300_* 字段隔离合同已冻结，proxy 不得填充真实 benchmark 字段"
file_ownership:
  primary:
    - "tests/test_cr011_benchmark_policy_consumption.py"
  shared:
    - "market_data/benchmarks.py"
    - "engine/research_dataset.py"
    - "experiments/run_experiment_17_21_factor_suite.py"
  merge_owner: "CR011-S01-real-benchmark-and-policy-consumption"
  forbidden:
    - "market_data/connectors/**"
    - "market_data/runtime.py"
    - "market_data/storage.py"
    - ".env"
    - "data/**"
    - "reports/experiment_17_21/factor_strategy_report.md"
    - "delivery/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#27-cr-011-因子研究生产级数据补齐增量设计"
    - "process/HLD-DATA-LAKE.md#14-cr-011-因子研究数据补齐增量"
    - "process/ARCHITECTURE-DECISION.md#adr-036cr-011-benchmark-policy-consumption-必须区分真实-benchmark-与-proxy-baseline"
    - "process/stories/CR011-S01-real-benchmark-and-policy-consumption.md"
  status: "approved"
  cp5_batch: "CR011-DATA-BATCH-A"
  cp5_precheck: "process/checks/CP5-CR011-S01-real-benchmark-and-policy-consumption-LLD-IMPLEMENTABILITY.md"
  manual_review: "checkpoints/CP5-CR011-DATA-BATCH-A-LLD-BATCH.md"
  confirmed_by: "user"
  confirmed_at: "2026-05-24T10:24:02+08:00"
  preconditions:
    - "CR-011 CP3 人工确认通过"
    - "CR-011 CP4 自动预检通过并由 meta-po 汇入 CP5"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  required_contracts:
    - "BenchmarkPolicyResult schema frozen"
    - "CR011-DATA-BATCH-A CP5 approved"
  file_conflict_free: true
  cp5_required: true
  implementation_allowed: true
  reason: "CR011-DATA-BATCH-A CP5 已 approved；S01 上游合同已冻结，当前无 dev_running 文件冲突，可作为 DATA-BATCH-A 首个实现 Story。"
created_at: "2026-05-23"
updated_at: "2026-05-24T10:47:32+08:00"
source_hld: "process/HLD.md"
companion_hld: "process/HLD-DATA-LAKE.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-011"
---

# CR011-S01：真实 benchmark 与 policy 消费

## 目标

让实验 17-21 v2 只读 `hs300_index` / benchmark policy，并严格隔离 `hs300_*` 与 `proxy_*` 字段。该 Story 只定义后续 LLD/实现的消费合同、字段门禁和报告 metadata，不授权自动抓取 benchmark、不覆盖旧报告、不使用 proxy 填充 `hs300_*`。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-08 |
| 需求 | REQ-071、REQ-080、REQ-081、REQ-082、CR011-AC-001 |
| HLD | `process/HLD.md` §27.1、§27.4、§27.5、§27.7；`process/HLD-DATA-LAKE.md` §14.1、§14.2、§14.5 |
| ADR | ADR-036 |
| Backlog / Plan | `process/STORY-BACKLOG.md` CR011-S01；`process/DEVELOPMENT-PLAN.yaml` wave `CR011-DATA-BATCH-A` |

## 开发上下文（dev_context）

**背景说明**：实验 17-21 旧报告仍是 fixed snapshot / proxy baseline / close proxy 的探索基线。CR-011 需要让新版研究在真实 `hs300_index` 可用时输出生产级 benchmark 字段，在不可用时输出 `required_missing` / `blocked_claims`，而不是把同股票池代理收益写成沪深 300 超额收益。

**输入文件**：`process/HLD.md`、`process/HLD-DATA-LAKE.md`、`process/ARCHITECTURE-DECISION.md`、`process/REQUIREMENTS.md`、`process/USE-CASES.md`、`process/changes/CR-011-FACTOR-RESEARCH-DATA-COMPLETION-2026-05-23.md`、`market_data/benchmarks.py`、`engine/research_dataset.py`、`experiments/run_experiment_17_21_factor_suite.py`。

**输出文件**：`market_data/benchmarks.py`、`engine/research_dataset.py`、`experiments/run_experiment_17_21_factor_suite.py`、`tests/test_cr011_benchmark_policy_consumption.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| `BenchmarkPolicyResult` 或等价结构 | `benchmark_policy=hs300_required`、date range、catalog current truth、quality policy | `benchmark_policy_id`、`benchmark_kind`、`index_code`、coverage、quality/readiness、`hs300_available`、missing reason | 缺真实 benchmark 时返回 `required_missing` 或 `unavailable`，不得自动 backfill |
| research input benchmark gate | `ResearchDataset` 请求、proxy baseline result、真实 benchmark result | 分离后的 `hs300_*` 与 `proxy_*` metadata、`allowed_claims` / `blocked_claims` | proxy 写入 `hs300_*` 字段次数必须为 0 |
| report metadata writer | benchmark gate result、baseline path、run metadata | `benchmark_missing_reason`、`proxy_baseline_used`、coverage ratio、source lineage | 不修改 `reports/experiment_17_21/factor_strategy_report.md` |

**设计约束**：

- CP3 / CP4 未通过前不得进入 LLD；`CR011-DATA-BATCH-A` CP5 批次确认前不得实现。
- 消费层只读 published catalog / readers / benchmark resolver；不得导入 `market_data.connectors`、`market_data.runtime`、`market_data.storage` 或读取 `.env`。
- 默认路径真实联网、真实 lake 写入、凭据读取、旧 `data/**` 操作次数均为 0。
- 旧 `reports/experiment_17_21/factor_strategy_report.md` 只能作为 baseline 路径引用，不得覆盖或重写。

**命名规范**：保留 `BenchmarkPolicyResult`、`benchmark_policy_id`、`benchmark_kind`、`hs300_available`、`hs300_coverage_ratio`、`proxy_baseline_used`、`benchmark_missing_reason`、`allowed_claims`、`blocked_claims`。

**平台目标**：本地 Python 因子研究工具；uv 管理依赖；无安装脚本；无 `delivery/**` 输出。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR011-S01-T1 | 修改 | `market_data/benchmarks.py` | 增加或扩展 benchmark policy result 字段，表达真实 `hs300_index` availability、coverage、quality 和 missing reason |
| CR011-S01-T2 | 修改 | `engine/research_dataset.py` | 将 benchmark policy gate 纳入 `research_input_v1` metadata，缺真实 benchmark 时写 blocked claims |
| CR011-S01-T3 | 修改 | `experiments/run_experiment_17_21_factor_suite.py` | 新版实验消费分离后的 `hs300_*` / `proxy_*` 字段，不覆盖旧报告 |
| CR011-S01-T4 | 创建 | `tests/test_cr011_benchmark_policy_consumption.py` | 覆盖 proxy 不写 `hs300_*`、缺真实 benchmark 结构化 missing、no network/no credential/no old report overwrite |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr011_benchmark_policy_consumption.py`。

**验证方式**：fixture catalog、fake benchmark result、offline monkeypatch、报告 metadata 快照和静态 forbidden path/import 扫描。

**依赖环境**：Python 3.11、uv、pytest；不需要 Tushare token、不需要真实 lake、不联网。

**关键验证场景**：

- 真实 `hs300_index` 可用时输出 6 个 benchmark policy 字段并写入 source lineage。
- 真实 benchmark 缺失或 quality fail 时 production_strict fail，exploratory 只能输出 proxy 和 limitation。
- proxy baseline 写入 `hs300_*` 字段次数为 0。
- `.env`、`data/**`、`market_data/connectors/**`、`delivery/**` 和旧报告写入次数为 0。

## 量化验收标准（acceptance_criteria）

- [ ] 新版实验 benchmark metadata 固定输出 6 个字段：`benchmark_policy_id`、`benchmark_kind`、`hs300_available`、`hs300_coverage_ratio`、`proxy_baseline_used`、`benchmark_missing_reason`。
- [ ] proxy baseline 写入 `hs300_*` 字段次数为 0。
- [ ] 缺真实 benchmark 时 production_strict 通过次数为 0，并输出机器可解析 `required_missing` / `blocked_claims`。
- [ ] 默认验证路径 `network_calls=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_operations=0`。
- [ ] 旧 `reports/experiment_17_21/factor_strategy_report.md` 覆盖次数为 0。

## 阻塞说明

OPEN：CR-011 CP3 / CP4 尚未通过，本 Story 不得进入 LLD。OPEN：`CR011-DATA-BATCH-A` CP5 尚未完成，任何实现、真实联网、真实 lake 写入、凭据读取、旧 `data/**` 操作和旧报告覆盖均不得发生。当前无新增 BLOCKING 设计问题；阻塞项来自既有门控。
