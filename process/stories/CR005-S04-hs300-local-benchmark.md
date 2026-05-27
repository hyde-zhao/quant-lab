---
story_id: "CR005-S04"
title: "沪深 300 本地基准与实验只读接入"
story_slug: "hs300-local-benchmark"
status: "verified"
priority: "P0"
wave: "CR5-W3"
depends_on: ["CR005-S01", "CR005-S03", "STORY-018"]
dependency_contracts:
  - upstream: "CR005-S01"
    type: "contract"
    required: "`hs300_index` backfill job spec frozen；本 Story 只引用 remediation spec，不执行 job"
  - upstream: "CR005-S03"
    type: "runtime"
    required: "`hs300_index` reader 与 quality gate 可消费"
  - upstream: "STORY-018"
    type: "contract"
    required: "实验十/十二只读接入边界保留"
file_ownership:
  primary:
    - "market_data/benchmarks.py"
    - "tests/test_market_data_hs300_benchmark.py"
  shared:
    - "experiments/run_experiment_10.py"
    - "experiments/run_experiment_12.py"
    - "market_data/readers.py"
  merge_owner: "CR005-S04"
  forbidden:
    - "market_data/connectors/**"
    - "engine/backtest.py"
    - "engine/backtrader_adapter.py"
    - "data/**"
    - "reports/**"
    - "delivery/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#227-关键流程"
    - "process/HLD.md#2261-benchmarkresult-typed-schema"
    - "process/HLD.md#2262-hs300_index-backfill-job-spec"
    - "process/ARCHITECTURE-DECISION.md#adr-015沪深-300-基准优先使用本地-hs300_index"
    - "process/stories/CR005-S04-hs300-local-benchmark.md"
  status: "approved"
  lld_path: "process/stories/CR005-S04-hs300-local-benchmark-LLD.md"
  cp5_auto_result: "process/checks/CP5-CR005-S04-hs300-local-benchmark-LLD-IMPLEMENTABILITY.md"
  cp5_manual_review: "checkpoints/CP5-CR005-BATCH-B2C-S04-S05-LLD-BATCH.md"
  confirmed_by: "user"
  confirmed_at: "2026-05-17T23:10:12+08:00"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  required_contracts:
    - "CR005-S01 `hs300_index` backfill job spec frozen"
    - "CR005-S03 `hs300_index` reader quality/catalog verified or contract frozen"
    - "`BenchmarkResult` schema frozen"
    - "benchmark policy / benchmark_kind frozen or available path disabled"
  file_conflict_free: true
  cp5_required: true
  cp5_confirmed: true
  implementation_allowed: true
  implementation_handoff: "process/handoffs/META-DEV-CR005-S04-IMPLEMENT-2026-05-17.md"
created_at: "2026-05-17"
updated_at: "2026-05-17T23:26:48+08:00"
verification_gate:
  cp7_status: "PASS"
  cp7_result: "process/checks/CP7-CR005-S04-hs300-local-benchmark-VERIFICATION-DONE.md"
  verification_handoff: "process/handoffs/META-QA-CR005-S04-CP7-VERIFY-2026-05-17.md"
  verified_by: "meta-po"
  verified_at: "2026-05-17T23:26:48+08:00"
  agent_id: "019e368a-3a6e-76d3-9852-51a4df77869f"
  agent_name: "qa-kong the 2nd"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-005"
---

# CR005-S04：沪深 300 本地基准与实验只读接入

## 目标

提供只读本地 `hs300_index` benchmark resolver，并让实验十/十二在显式启用市场数据模式时消费本地 canonical/gold 基准；缺失时返回 `BenchmarkResult` typed `unavailable` / `required_missing` / `quality_failed`，可携带 `next_action` / `remediation_job_spec`，但不联网、不静默代理、不自动补数。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | CR005-AC-003、CR005-AC-008、CR005-AC-015、CR005-AC-017、CR005-AC-018、CR005-AC-019 |
| HLD | §22.7、§22.8 |
| ADR | ADR-015 |

## 开发上下文（dev_context）

**背景说明**：当前仓库没有 `market_data/benchmarks.py`；STORY-018 的 LLD 已规划只读 benchmark resolver。CR-005 用 Tushare 写入的 `hs300_index` 提供真实本地基准，但口径仍需用户确认。第三轮评审要求本 Story 冻结消费层 typed result，明确 required_missing 只给出人工可执行的数据层 backfill 建议，不在 resolver 或实验入口自动执行。

**输入文件**：`market_data/readers.py`、`market_data/catalog.py`、`experiments/run_experiment_10.py`、`experiments/run_experiment_12.py`、STORY-018 LLD、CR005-S01/S03 Story/LLD。

**输出文件**：`market_data/benchmarks.py`、`tests/test_market_data_hs300_benchmark.py`，必要时修改 `experiments/run_experiment_10.py`、`experiments/run_experiment_12.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 约束 |
|---|---|---|---|
| `resolve_hs300_benchmark(config)` | lake_root、date range、quality_policy、require_benchmark、benchmark_policy | `BenchmarkResult` + optional benchmark series | 只读 local canonical/gold；缺失 typed unavailable / required_missing；不执行 remediation |
| `BenchmarkResult` | status、dataset、source、index_code、interface、date range、coverage、quality_status、missing_reason、required、remediation_job_spec、catalog_entry、run/lineage | 实验 metadata / Backtrader 对照输入 | 必须可序列化；不得含 token 值；status 枚举固定 |
| 实验入口 | 显式 market_data root / benchmark path | 实验结果 metadata | 不联网、不调用 connector；旧路径只回退本地价格数据，不回退为 hs300 代理 |

**`remediation_job_spec` 字段**：

| 字段 | 要求 |
|---|---|
| dataset/source/interface | `hs300_index` / `tushare` / exact `hs300_index.daily` 或 CP5 冻结值 |
| index_code/date range | 默认候选 `399300.SZ`，start/end 来自请求区间或缺口区间 |
| lake_root/run_id/resume_policy | 由调用配置或 spec 生成；不得自动创建真实数据目录 |
| dry_run | 默认 `true` |
| paths | manifest_path、quality_path、catalog_path 必须存在于 spec 或可由 spec deterministic 推导 |
| errors | 至少覆盖 source_disabled、interface_not_allowed、missing_credential、lake_root_invalid、quality_failed、resume_conflict |

**设计约束**：

- 缺少 `hs300_index` 时不得使用当前股票池等权代理静默替代。
- `required_missing` 只能返回 typed result 和 remediation spec；resolver、实验入口、Data Loader、Backtrader 不得调用 connector/runtime/storage。
- `--require-benchmark` 或等价策略启用时，缺失基准应 `required_missing`。
- 输出 metadata 必须披露 benchmark source、status、dataset、index_code、interface、date range、quality、coverage、missing_reason、required、口径和 lineage。
- 旧 `--data-dir` 回退只表示继续读取旧本地价格输入；旧等权或同股票池代理如保留，字段名必须为 `proxy_baseline`，不得填充 `hs300_index` 或声明 hs300 相对收益。
- 不修改 `engine/backtest.py` 或 Backtrader adapter。

**命名规范**：benchmark status 使用 `available`、`unavailable`、`required_missing` 或 LLD 确认的等价枚举。

**平台目标**：实验本地真实基准只读消费。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR005-S04-T1 | 创建 | `market_data/benchmarks.py` | 实现只读 benchmark resolver、`BenchmarkResult` typed schema 和 remediation spec 生成 |
| CR005-S04-T2 | 修改 | `experiments/run_experiment_10.py` | 接入显式本地 benchmark 元数据，不联网 |
| CR005-S04-T3 | 修改 | `experiments/run_experiment_12.py` | 同步实验十二基准只读路径 |
| CR005-S04-T4 | 创建 | `tests/test_market_data_hs300_benchmark.py` | 覆盖 available/unavailable/required_missing/quality_failed、no-network、remediation spec、proxy_baseline 边界、旧路径回退 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_market_data_hs300_benchmark.py`。

**验证方式**：临时 canonical/gold fixture、实验入口单元测试、文件系统快照。

**依赖环境**：Python 3.11、uv、pytest；不需要网络或 token。

**关键验证场景**：

- 有 `hs300_index` 且 quality pass 时返回 available。
- 缺基准时返回 unavailable。
- require benchmark 时缺失返回 required_missing。
- typed result 包含 status、dataset、source、index_code、interface、date range、coverage、quality_status、missing_reason、required、remediation_job_spec、catalog_entry、run/lineage。
- `required_missing` payload 带 `next_action.type=run_data_layer_backfill` 或等价值，但消费层不执行。
- 缺基准时 proxy_baseline 不填充 `hs300_index` 字段。
- 实验入口不导入 connector、不联网、不写数据湖。

## 量化验收标准（acceptance_criteria）

- [ ] benchmark resolver 至少输出 13 个 typed 字段：status、dataset、source、index_code、interface、start_date、end_date、coverage、quality_status、missing_reason、required、remediation_job_spec、catalog_entry、run/lineage。
- [ ] `unavailable` / `required_missing` payload 的 `remediation_job_spec.dry_run` 默认值为 true。
- [ ] `required_missing` 情况下 connector/runtime/storage 调用次数为 0，raw/manifest/canonical/quality/catalog/gold 写入次数为 0。
- [ ] 基准缺失时静默代理次数为 0。
- [ ] 实验入口默认网络调用次数为 0。
- [ ] 旧 `--data-dir` 或等价路径保留，但用于 hs300 字段填充的 proxy 次数为 0；如保留代理，只能输出 `proxy_baseline`。
- [ ] 不修改 `market_data/connectors/**`、`engine/backtest.py`、`engine/backtrader_adapter.py`、真实 `data/**`。

## 阻塞说明

`CR5-Q2` 仍为 OPEN：沪深 300 采用价格指数、全收益指数或其他口径尚未确认。可先交付只读 resolver 和 unavailable 结构，available 真实数据路径需后续确认。

## 开发完成交接

| 项目 | 内容 |
|---|---|
| CP6 | `process/checks/CP6-CR005-S04-hs300-local-benchmark-CODING-DONE.md` |
| 实现文件 | `market_data/benchmarks.py`、`experiments/run_experiment_10.py`、`experiments/run_experiment_12.py` |
| 测试文件 | `tests/test_market_data_hs300_benchmark.py` |
| 验证入口 | `UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_market_data_hs300_benchmark.py` |
| 最小回归 | `UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_market_data_hs300_benchmark.py tests/test_market_data_multidataset_quality_readers.py` |
| 结果 | 目标测试 6 passed；最小回归 15 passed |
| 交接状态 | CP7 PASS；已收敛为 verified |

## 验证完成状态

| 项目 | 内容 |
|---|---|
| CP7 | `process/checks/CP7-CR005-S04-hs300-local-benchmark-VERIFICATION-DONE.md` |
| QA handoff | `process/handoffs/META-QA-CR005-S04-CP7-VERIFY-2026-05-17.md` |
| QA agent | `qa-kong the 2nd` / `019e368a-3a6e-76d3-9852-51a4df77869f` |
| 目标测试 | `6 passed` |
| 最小回归 | `15 passed` |
| 全量离线回归 | `90 passed` |
| 结论 | `PASS`；无 BLOCKING / REQUIRED 失败项 |
