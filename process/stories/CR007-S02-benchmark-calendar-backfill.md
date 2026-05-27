---
story_id: "CR007-S02-benchmark-calendar-backfill"
title: "benchmark 与交易日历同区间 backfill"
story_slug: "benchmark-calendar-backfill"
status: "draft"
priority: "P0"
wave: "CR007-BATCH-A"
depends_on: ["CR007-S01-prices-long-horizon-backfill-planner", "CR005-S04"]
dependency_contracts:
  - upstream: "CR007-S01-prices-long-horizon-backfill-planner"
    type: "contract"
    required: "长周期 planner、date range、coverage gate 和 resume policy 已冻结"
  - upstream: "CR005-S04"
    type: "contract"
    required: "`BenchmarkResult` schema、resolver 和 required_missing 语义已冻结"
file_ownership:
  primary:
    - "tests/test_cr007_benchmark_calendar_backfill.py"
  shared:
    - "market_data/cli.py"
    - "market_data/normalization.py"
    - "market_data/validation.py"
    - "market_data/catalog.py"
    - "market_data/readers.py"
    - "market_data/benchmarks.py"
  merge_owner: "CR007-S02-benchmark-calendar-backfill"
  forbidden:
    - "engine/**"
    - "experiments/run_experiment_13.py"
    - "data/**"
    - "reports/**"
    - ".env"
    - "credentials"
    - "delivery/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#247-关键流程"
    - "process/ARCHITECTURE-DECISION.md#adr-020真实沪深300-benchmark-必须与交易日历同区间覆盖"
    - "process/stories/CR007-S02-benchmark-calendar-backfill.md"
  status: "not-started"
  cp5_batch: "CR007-BATCH-A"
dev_gate:
  lld_confirmed: false
  dependencies_satisfied: false
  required_contracts:
    - "CR007-S01 planner contract frozen"
    - "trade_calendar denominator policy frozen"
    - "BenchmarkResult schema frozen"
  file_conflict_free: false
  cp5_required: true
  implementation_allowed: false
created_at: "2026-05-20"
updated_at: "2026-05-20"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-007"
---

# CR007-S02：benchmark 与交易日历同区间 backfill

## 目标

补齐 `hs300_index` 与 `trade_calendar` 同区间 backfill、normalize、validate、catalog 和 reader 合同。真实沪深300 benchmark 必须以 `trade_calendar.is_open=true` 为 denominator；缺口返回 typed `required_missing` / `unavailable`，不得用代理填充。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | CR007-AC-003、CR007-AC-004、CR007-AC-007 |
| HLD | §24.1、§24.5、§24.7、§24.8 |
| ADR | ADR-020 |

## 开发上下文（dev_context）

**背景说明**：当前 `hs300_index` 已有小样本链路，但只覆盖 2024 四天，不能作为 2025 或长周期 benchmark。实验和 benchmark resolver 必须依赖同区间 `trade_calendar` 和 `hs300_index` coverage。

**输入文件**：`market_data/cli.py`、`market_data/normalization.py`、`market_data/validation.py`、`market_data/catalog.py`、`market_data/readers.py`、`market_data/benchmarks.py`、CR005-S04 Story/LLD。

**输出文件**：`market_data/cli.py`、`market_data/normalization.py`、`market_data/validation.py`、`market_data/catalog.py`、`market_data/readers.py`、`market_data/benchmarks.py`、`tests/test_cr007_benchmark_calendar_backfill.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| benchmark/calendar plan | `hs300_index`、`trade_calendar`、start/end、index_code、exchange、lake_root、dry_run | target paths、batch plan、coverage denominator、quality thresholds | dry-run 不联网、不写湖 |
| validate hs300 coverage | canonical hs300 frame、trade_calendar open dates | coverage ratio、missing_trade_dates、gap_reason、quality_status | denominator 必须来自 open dates |
| benchmark resolver | lake_root、start/end、policy、required | `BenchmarkResult` available/unavailable/required_missing/quality_failed | 不调用 connector/runtime/storage |

**设计约束**：

- `hs300_index` 与 `prices` 无重叠时不得输出真实 benchmark 指标。
- 缺 `trade_calendar` 时不能用自然日 denominator 假装通过。
- 旧代理只能命名为 `proxy_baseline`，不得填充 `hs300_index`。
- 不修改实验十三消费文件；该工作归 CR007-S04。

**命名规范**：使用 `hs300_index`、`trade_calendar`、`coverage.denominator_mode=trade_calendar_open_dates`、`missing_trade_dates`、`gap_reason`。

**平台目标**：本地 canonical/gold benchmark 数据层。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR007-S02-T1 | 修改 | `market_data/cli.py` | 扩展 benchmark/calendar dry-run 和运维入口 |
| CR007-S02-T2 | 修改 | `market_data/normalization.py` / `validation.py` | 强化 hs300 与 trade_calendar 同区间 coverage gate |
| CR007-S02-T3 | 修改 | `market_data/catalog.py` / `readers.py` / `benchmarks.py` | 确认 quality/catalog/readers 与 BenchmarkResult metadata 对齐 |
| CR007-S02-T4 | 创建 | `tests/test_cr007_benchmark_calendar_backfill.py` | 覆盖同区间 available、coverage gap、calendar missing、no proxy/no network |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr007_benchmark_calendar_backfill.py`。

**验证方式**：tmp lake、canonical fixture、trade_calendar fixture、BenchmarkResult metadata 断言。

**依赖环境**：Python 3.11、uv、pytest；不需要 Tushare token、不需要 NAS、不联网。

**关键验证场景**：

- 2025 小窗口 `hs300_index` 与 `trade_calendar` coverage 完整时可返回 available。
- `hs300_index` 与请求日期无重叠时返回 required_missing 或 unavailable。
- 缺 trade_calendar 时无法声明 coverage pass。
- proxy_baseline 不填充 hs300 字段。

## 量化验收标准（acceptance_criteria）

- [ ] coverage denominator 使用 `trade_calendar.is_open=true`，自然日 denominator 使用次数为 0。
- [ ] `BenchmarkResult` metadata 包含 status、dataset、index_code、start/end、coverage、quality_status、missing_reason、lineage。
- [ ] `hs300_index` 与 `prices` 无同区间覆盖时真实 benchmark 输出次数为 0。
- [ ] 消费路径 connector/runtime/storage 调用次数为 0。
- [ ] 旧 `data/**`、`.env`、token、NAS 凭据操作次数为 0。

## 阻塞说明

无 BLOCKING。真实 Tushare backfill 和真实 lake 写入仍需另行授权。
