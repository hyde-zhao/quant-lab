# REAL-TUSHARE-CR029 Stage6 Data Lake Admission / Benchmark Check

## 基本信息

| 字段 | 值 |
|---|---|
| CR | `CR-029` |
| 授权 ID | `AUTH-CR029-20260531-STAGE6-LAKE-TUSHARE` |
| 执行日期 | `2026-05-31` |
| 执行范围 | 阶段六策略准入判断、宽基 benchmark / primary benchmark 数据湖检查、真实 Tushare 候选补数、阶段六 published current truth 回测验证 |
| 真实凭据 | 已读取 `.env` 中 Tushare / lake 配置；未打印、未写入 token 或真实 lake root |
| 明确未授权 | `publish current pointer`、QMT / MiniQMT / XtQuant、真实下单、撤单、账户查询、broker lake 写入、simulation / live / small_live / scale_up |

## Entry Criteria

| 检查项 | 结果 | 证据 |
|---|---|---|
| 用户授权真实 lake 读写和 Tushare 抓取 | PASS | 用户明确表示可读取 `.env` 中 Tushare token 完成数据抓取 |
| `.env` 中必要配置存在 | PASS | `TUSHARE_TOKEN`、`MARKET_DATA_LAKE_ROOT`、lake 写权限均已通过存在性 / 可写性预检；未披露真实值 |
| CR 冲突预检 | PASS_WITH_LIMITS | `CR-029-STAGE6-DATA-LAKE-ADMISSION-BENCHMARK-REAL-RUN-2026-05-31.md` 已记录；本 CR 不修改代码契约、不启动 QMT、不 publish |
| 当前 published data lake 基线 | PASS | `report-readiness --report production --realism-mode production_strict` 在执行前可读，核心 published current truth 可用于研究 |

## 真实 Tushare 候选数据

本轮补充的是 `2026-05-29` 的最小候选窗口，用于验证阶段六 benchmark 最新日数据链路。候选数据已写入 raw / canonical / quality，但没有发布为 current truth。

| 数据集 | run_id | 范围 | normalize | validate | catalog 状态 |
|---|---|---:|---|---|---|
| `trade_calendar` | `run-cr029-stage6-benchmark-latest-20260529-calendar` | `2026-05-29` | PASS，1 行 | PASS，missing_rate=0.0 | 候选文件保留，current catalog 已恢复到 CR018 published entry |
| `hs300_index` / HS300 | `run-cr029-stage6-benchmark-latest-20260529-HS300` | `2026-05-29` | PASS，1 行 | PASS，missing_rate=0.0 | 候选文件保留，未发布 |
| `hs300_index` / ZZ500 | `run-cr029-stage6-benchmark-latest-20260529-ZZ500` | `2026-05-29` | PASS，1 行 | PASS，missing_rate=0.0 | 候选文件保留，未发布 |
| `hs300_index` / ZZ1000 | `run-cr029-stage6-benchmark-latest-20260529-ZZ1000` | `2026-05-29` | PASS，1 行 | PASS，missing_rate=0.0 | 候选文件保留，未发布 |
| `hs300_index` / CSI_ALL_SHARE | `run-cr029-stage6-benchmark-latest-20260529-CSIALL` | `2026-05-29` | PASS，1 行 | PASS，missing_rate=0.0 | 候选文件保留，未发布 |

候选文件存在性已检查，以下相对路径均存在：

| 类别 | 相对路径 |
|---|---|
| calendar raw | `raw/tushare/trade_calendar.daily/20260529/run_id=run-cr029-stage6-benchmark-latest-20260529-calendar/trade-calendar-20260529.jsonl` |
| calendar canonical | `canonical/trade_calendar/1.0/run_id=run-cr029-stage6-benchmark-latest-20260529-calendar/part-trade-calendar-20260529.parquet` |
| calendar quality | `quality/run-cr029-stage6-benchmark-latest-20260529-calendar/trade_calendar_quality.csv` |
| HS300 canonical | `canonical/hs300_index/1.0/run_id=run-cr029-stage6-benchmark-latest-20260529-HS300/part-index-daily-HS300-20260529.parquet` |
| ZZ500 canonical | `canonical/hs300_index/1.0/run_id=run-cr029-stage6-benchmark-latest-20260529-ZZ500/part-index-daily-ZZ500-20260529.parquet` |
| ZZ1000 canonical | `canonical/hs300_index/1.0/run_id=run-cr029-stage6-benchmark-latest-20260529-ZZ1000/part-index-daily-ZZ1000-20260529.parquet` |
| CSI_ALL_SHARE canonical | `canonical/hs300_index/1.0/run_id=run-cr029-stage6-benchmark-latest-20260529-CSIALL/part-index-daily-CSIALL-20260529.parquet` |
| catalog 修复备份 | `quality/run-cr029-stage6-benchmark-latest-20260529-calendar/catalog-before-cr029-candidate-restore.json` |

## Catalog 副作用与修复

`market_data.cli validate` 会把对应 dataset 的 catalog 最新 entry 写成 `candidate_unpublished`。本轮验证 `trade_calendar` 和 `hs300_index` 后，production readiness 曾短暂变为 `fail`，原因是 readiness 报告看到最新 catalog entry 为候选未发布。

处理动作：

1. 备份验证后的 catalog 到 `quality/run-cr029-stage6-benchmark-latest-20260529-calendar/catalog-before-cr029-candidate-restore.json`。
2. 仅将 `trade_calendar` 与 `hs300_index` 两个 catalog entry 恢复到 CR018 已发布 release 中的原记录。
3. 保留 2026-05-29 候选 raw / canonical / quality 文件；不删除候选证据。
4. 不执行 2026-05-29 候选数据 publish，不改变 current truth release。

恢复后的 catalog 状态：

| dataset | published | run_id | 范围 |
|---|---|---|---|
| `trade_calendar` | true | `run-cr014-s14-trade-calendar-2015-2026-232302` | `2015-01-01`..`2026-05-28` |
| `hs300_index` | true | `run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529` | `2015-01-01`..`2026-05-28` |

恢复后再次执行 `report-readiness --report production --realism-mode production_strict`：

| 指标 | 结果 |
|---|---|
| status | `pass` |
| published_count | `10` |
| candidate_unpublished_count | `0` |
| missing_required_count | `0` |
| current_truth_complete | `true` |
| allowed_claims | `production_strict_research` |

## 多基准与 Primary Benchmark 策略

已生成 benchmark dashboard：

`reports/cr029_stage6_precheck/release-cr018-production-current-truth-20150101-20260528-20260529/run-cr029-precheck-stage6-current-truth-20260531/stage6-benchmark-dashboard.json`

| 检查项 | 结果 |
|---|---|
| dashboard status | `ready` |
| benchmark_count | `4` |
| primary_benchmark | `CSI_ALL_SHARE` |
| selection_basis | `universe=all_market -> CSI_ALL_SHARE`；`style=mixed -> CSI_ALL_SHARE`；`readiness=ready` |
| QMT / publish / simulation counters | 全部为 `0` |

Published current truth 中已可读的 benchmark 数据摘要：

| dataset | index_code | rows | min_date | max_date |
|---|---|---:|---|---|
| `hs300_index` | `399300.SZ` | 2768 | `2015-01-05` | `2026-05-28` |
| `hs300_index` | `000905.SH` | 2768 | `2015-01-05` | `2026-05-28` |
| `hs300_index` | `000852.SH` | 2768 | `2015-01-05` | `2026-05-28` |
| `hs300_index` | `000985.SH` | 2768 | `2015-01-05` | `2026-05-28` |
| `index_members` | `399300.SZ` | 66600 | `2015-01-30` | `2026-05-06` |
| `index_members` | `000905.SH` | 68000 | `2015-01-30` | `2026-04-30` |
| `index_members` | `000852.SH` | 70000 | `2015-07-31` | `2026-04-30` |
| `index_members` | `000985.SH` | 72000 | `2015-10-30` | `2026-04-30` |
| `index_weights` | `399300.SZ` | 66600 | `2015-01-30` | `2026-05-06` |
| `index_weights` | `000905.SH` | 68000 | `2015-01-30` | `2026-04-30` |
| `index_weights` | `000852.SH` | 70000 | `2015-07-31` | `2026-04-30` |
| `index_weights` | `000985.SH` | 72000 | `2015-10-30` | `2026-04-30` |

结论：多基准与 primary benchmark 数据面可用；全市场 / mixed style 策略的 primary benchmark 选中 `CSI_ALL_SHARE`。

## 阶段六策略准入判断

已运行 published current truth 阶段六研究 / 回测：

`reports/cr029_stage6_precheck/release-cr018-production-current-truth-20150101-20260528-20260529/run-cr029-precheck-stage6-current-truth-20260531/rerun-report.json`

摘要：

| 指标 | 结果 |
|---|---:|
| coverage | `2015-01-01`..`2026-05-28` |
| status | `fail` |
| strategy_pass | `false` |
| low_vol_top20_annual_return | `2.6937%` |
| hs300_annual_return | `2.7673%` |
| low_vol_minus_hs300_annual_return | `-0.0736%` |
| low_vol_top20_max_drawdown | `-55.8749%` |
| hs300_max_drawdown | `-46.6961%` |
| low_vol_rank_ic_mean | `0.088391` |
| qmt_admission_allowed_count | `0` |

已生成 admission package：

`reports/cr029_stage6_precheck/release-cr018-production-current-truth-20150101-20260528-20260529/run-cr029-precheck-stage6-current-truth-20260531/stage6-admission-package.json`

阻断项：

| claim_id | reason_code | severity | 解锁条件 |
|---|---|---|---|
| `stage6_data_quality` | `research_rerun_failed` | P0 | rerun on published current truth until passed |
| `stage6_benchmark_excess` | `benchmark_excess_failed` | P0 | 提升阶段六策略，直到超额收益为正且回撤可接受 |
| `stage6_robustness` | `strategy_criteria_failed` | P0 | 策略改进并完成稳健性验证后重跑 |
| `stage6_ablation` | `ablation_evidence_missing_for_admission` | P0 | 补充阶段六 ablation evidence |
| `stage6_presim_and_5day_dry_run` | `dry_run_5day_missing` | P0 | 提供 pre-sim 与连续 5 个真实交易日 dry-run evidence |
| `simulation_ready` | `old_strategy_failed_rerun` | P0 | 替换旧失败策略并重跑通过 |

结论：阶段六数据链路和回测执行链路可运行，但策略准入结果为 `blocked`，不能进入 QMT admission。

## 验证命令

| 命令 | 结果 |
|---|---|
| `uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli normalize ... trade_calendar ...` | PASS |
| `uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli validate ... trade_calendar ...` | PASS |
| `uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli normalize ... hs300_index ...` | PASS，四个 benchmark run 均通过 |
| `uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli validate ... hs300_index --open-trade-dates 2026-05-29 ...` | PASS，四个 benchmark run 均通过 |
| `uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli report-readiness --report production --realism-mode production_strict` | PASS，恢复后 current truth complete |
| `uv run --python 3.11 pytest -q tests/test_cr019_stage6_admission_gate.py tests/test_cr019_primary_benchmark_policy.py tests/test_cr018_production_current_truth_rerun.py tests/test_cr018_benchmark_group_readiness.py` | PASS，34 passed |
| `uv run --python 3.11 pytest -q tests/test_cr018_publish_current_reader_smoke.py tests/test_cr018_readiness_rollback_gate.py` | PASS，11 passed |

## Operation Counters

| 操作 | 计数 | 说明 |
|---|---:|---|
| `.env` credential read | 1 | 仅运行时读取，未打印 token |
| provider_fetch | 5 | trade calendar 1 次，benchmark index 4 次 |
| candidate raw/canonical/quality write | 5 组 | 2026-05-29 日历 + 4 个 benchmark index |
| catalog candidate validate write | 5 次 | validate 写入候选状态；随后恢复 current catalog entry |
| catalog restore write | 1 | 只恢复 `trade_calendar` 与 `hs300_index` 到 CR018 published entry |
| current pointer publish | 0 | 未发布 2026-05-29 候选 |
| QMT / MiniQMT / XtQuant | 0 | 未启动 |
| simulation / live / small_live / scale_up | 0 | 未运行 |
| real order / cancel / account query | 0 | 未调用 |

## Exit Criteria

| 条件 | 结果 |
|---|---|
| 阶段六 benchmark 最新日候选数据可抓取、可规范化、可验证 | PASS |
| 多基准 dashboard 可生成，primary benchmark 可选择 | PASS |
| published current truth readiness 保持可用 | PASS |
| 阶段六回测任务可运行 | PASS |
| 阶段六策略准入通过 | FAIL / BLOCKED |
| 不越过未授权边界 | PASS |

## 结论

数据湖层面：

- 已完成 `2026-05-29` 日历和四个 benchmark index 的真实 Tushare 候选补数、整理和质量验证。
- published current truth 仍保持 CR018 release：`2015-01-01`..`2026-05-28`，production readiness 为 `pass`。
- `2026-05-29` 候选数据未发布到 current truth；如需纳入 current，需要单独 Explicit Publish Gate。

策略准入层面：

- 阶段六回测可以在真实 published current truth 上运行。
- 当前低波 Top20 策略不满足准入条件：年化收益略低于 HS300，最大回撤更差，`qmt_admission_allowed_count=0`。
- 因此阶段六策略准入判断的结论是 `blocked`，不是 `pass`。
