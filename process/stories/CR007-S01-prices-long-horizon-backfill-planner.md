---
story_id: "CR007-S01-prices-long-horizon-backfill-planner"
title: "长周期 prices backfill planner"
story_slug: "prices-long-horizon-backfill-planner"
status: "verified"
priority: "P0"
wave: "CR007-BATCH-A"
depends_on: ["CR006-S01-tushare-first-data-acquisition-runbook", "CR005-S02", "CR005-S03"]
dependency_contracts:
  - upstream: "CR006-S01-tushare-first-data-acquisition-runbook"
    type: "contract"
    required: "Tushare-first acquisition、raw/manifest 审计、canonical/gold lineage 和 no-old-data 边界已冻结"
  - upstream: "CR005-S02"
    type: "contract"
    required: "prices / adj_factor schema、复权 normalization 和 exact interface mapping 已冻结"
  - upstream: "CR005-S03"
    type: "contract"
    required: "quality/catalog/readers 和复权一致 gate 已冻结"
file_ownership:
  primary:
    - "tests/test_cr007_prices_long_horizon_backfill_planner.py"
  shared:
    - "market_data/cli.py"
    - "market_data/runtime.py"
    - "market_data/connectors/tushare.py"
    - "market_data/normalization.py"
    - "market_data/validation.py"
  merge_owner: "CR007-S01-prices-long-horizon-backfill-planner"
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
    - "process/HLD.md#24-cr-007-canonical-数据覆盖与真实-benchmark-增量设计"
    - "process/ARCHITECTURE-DECISION.md#adr-019长周期-backfill-采用分批-plannerresume-与-coverage-gate"
    - "process/stories/CR007-S01-prices-long-horizon-backfill-planner.md"
  status: "approved"
  cp5_batch: "CR007-BATCH-A"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  required_contracts:
    - "CR007 CP3/CP4 approved"
    - "CR007-BATCH-A all LLD and CP5 approved"
    - "dry-run planner scope approved; real fetch/write still not authorized"
  file_conflict_free: true
  cp5_required: true
  implementation_allowed: true
execution:
  cp6_status: "PASS"
  cp6_checkpoint: "process/checks/CP6-CR007-S01-prices-long-horizon-backfill-planner-CODING-DONE.md"
  cp6_completed_at: "2026-05-20T23:10:00+08:00"
  cp7_status: "PASS"
  cp7_checkpoint: "process/checks/CP7-CR007-S01-prices-long-horizon-backfill-planner-VERIFICATION-DONE.md"
  cp7_completed_at: "2026-05-20T23:26:10+08:00"
  verified_by: "meta-qa/qa-he"
  verified_agent_id: "019e45fd-2ffb-73c0-8f20-c69a745ff0ef"
created_at: "2026-05-20"
updated_at: "2026-05-20"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-007"
---

# CR007-S01：长周期 prices backfill planner

## 目标

为 `prices.daily` 与 `prices.adj_factor` 建立长周期 backfill dry-run planner，覆盖 `2015-01-01` 至 `2025-12-31` 或用户指定 end date。该 Story 只设计和实现可审计的计划、分批、resume 和 coverage gate，不授权真实 Tushare 抓取、真实 lake 写入或旧 `data/**` 读取。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | CR007-AC-001、CR007-AC-002、CR007-AC-006 |
| HLD | §24.1、§24.5、§24.7、§24.8 |
| ADR | ADR-019 |

## 开发上下文（dev_context）

**背景说明**：CR-006 已完成 Tushare-first structured lake 底座，但当前 `prices` 只有 2025 小窗口，不能支撑 2015-2020 分段测试或 2015-2025 样本内外研究。长周期 backfill 必须先规划分批和覆盖校验，避免无边界全市场抓取。

**输入文件**：`process/HLD.md`、`process/ARCHITECTURE-DECISION.md`、`process/changes/CR-007-CANONICAL-DATA-COVERAGE-BACKFILL-AND-BENCHMARK-2026-05-20.md`、`market_data/cli.py`、`market_data/runtime.py`、`market_data/connectors/tushare.py`、`market_data/normalization.py`、`market_data/validation.py`。

**输出文件**：`market_data/cli.py` 或等价 job、`market_data/runtime.py`、`market_data/connectors/tushare.py`、`market_data/normalization.py`、`market_data/validation.py`、`tests/test_cr007_prices_long_horizon_backfill_planner.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| `prices-long-horizon-plan` 或等价 planner | dataset=`prices`、start/end、symbols 或 universe source、batch_size、date_slice、lake_root、run_id、dry_run | batch plan、`prices.daily` / `prices.adj_factor` requests、target raw/manifest/canonical/quality/catalog/gold paths、resume policy、coverage gate | dry-run 网络调用 0、写入 0；缺 symbols/universe 返回 `universe_missing` |
| resume policy | existing manifest status summary | `success=skip`、`failed/partial_success=retry`、`duplicate_manifest=fail` | 不读取旧 `data/**` 判断 resume |
| coverage gate | planned trading dates、symbols、canonical partitions | expected rows、missing dates/symbols、coverage ratio、quality status | 不能用 2025 小窗口证明 2015-2025 覆盖 |

**设计约束**：

- 不指定 `ts_code` 或 universe source 的全市场长周期抓取不得作为默认策略。
- `prices.daily` 与 `prices.adj_factor` 必须使用同一复权口径；冲突时 fail fast。
- planner 不打印真实 lake path 以外的敏感信息；凭据只以 env var name 表达。
- 本 Story 不修改 `engine/**`、`experiments/**`、README、docs、真实 `data/**`、`reports/**`、`.env` 或 `delivery/**`。

**命名规范**：保留 `prices`、`prices.daily`、`prices.adj_factor`、`run_id`、`batch_id`、`resume_policy`、`coverage_gate`、`dry_run`。

**平台目标**：本地 Python 研究工具；uv 管理依赖；无安装脚本；无 `delivery/**` 输出。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR007-S01-T1 | 修改 | `market_data/cli.py` | 增加或扩展长周期 prices dry-run planner，输出分批计划、resume policy 和 coverage gate |
| CR007-S01-T2 | 修改 | `market_data/runtime.py` | 确认 batch status / resume 语义可被 planner 使用 |
| CR007-S01-T3 | 修改 | `market_data/normalization.py` / `validation.py` | 明确 `prices.daily` + `adj_factor` 长周期 coverage 和复权一致校验 |
| CR007-S01-T4 | 创建 | `tests/test_cr007_prices_long_horizon_backfill_planner.py` | 覆盖 dry-run、无 universe fail fast、resume、coverage gate、no old data/no credential |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr007_prices_long_horizon_backfill_planner.py`。

**验证方式**：tmp lake、fake manifest、fixture symbols、dry-run JSON 输出、静态扫描。

**依赖环境**：Python 3.11、uv、pytest；不需要 Tushare token、不需要 NAS、不联网。

**关键验证场景**：

- dry-run 网络调用次数为 0，写入次数为 0。
- 缺少 symbols/universe source 时返回结构化错误。
- `prices.daily` 与 `prices.adj_factor` 计划使用相同 date slices、symbols 和 adjustment policy。
- coverage gate 不把局部小窗口声明为长周期通过。
- 旧 `data/**` 读取、列出、迁移、复制、比对、删除次数为 0。

## 量化验收标准（acceptance_criteria）

- [ ] plan 输出字段不少于 12 个：dataset、source、interfaces、start_date、end_date、symbols_or_universe、batch_count、date_slices、run_id、resume_policy、target_paths、coverage_gate。
- [ ] dry-run 情况 `network_calls=0` 且 `writes=0`。
- [ ] 无 symbols / universe source 的长周期全市场默认抓取次数为 0。
- [ ] `prices.daily` 与 `prices.adj_factor` 复权口径冲突时 fail fast。
- [ ] 旧 `data/**` 操作次数为 0；`.env` / token / NAS 凭据读取或打印次数为 0。

## 阻塞说明

无 BLOCKING。真实抓取和真实 lake 写入仍为 OPEN，需用户另行显式授权；不阻塞本 Story 的 dry-run planner LLD。
