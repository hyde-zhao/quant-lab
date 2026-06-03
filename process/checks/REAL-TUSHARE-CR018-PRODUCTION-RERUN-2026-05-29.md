---
check_id: "REAL-TUSHARE-CR018-PRODUCTION-RERUN-2026-05-29"
type: "real-production-current-truth-research-rerun"
status: "FAIL"
owner: "meta-po"
created_at: "2026-05-29T22:16:12+08:00"
checked_at: "2026-05-29T22:16:12+08:00"
target:
  change_id: "CR-018"
  story_id: "CR018-S08-production-current-truth-research-rerun"
  release_id: "release-cr018-production-current-truth-20150101-20260528-20260529"
  run_id: "run-cr018-production-rerun-20150101-20260528-20260529-01"
  coverage: "2015-01-01..2026-05-28"
---

# CR018 Published Current Truth 阶段三到阶段五真实重跑证据

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| production current truth 已发布 | PASS | `process/checks/REAL-TUSHARE-CR018-RELEASE-PUBLISH-2026-05-29.md` | 10 个核心 dataset 均为 `published/pass/available` |
| `production_strict` readiness 可用 | PASS | `uv run --python 3.11 python -m market_data.cli report-readiness --lake-root /mnt/ugreen-data-lake --realism-mode production_strict` | 返回 `status=pass`、`blockers=[]`、`candidate_unpublished_count=0`、`published_count=10` |
| `trade_status` current pointer 覆盖修复 | PASS | `scripts/cr018_release_catalog_publish.py`、catalog 元数据复查 | `trade_status` 指向 `canonical/trade_status/1.0/run_id=run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529`，`coverage_denominator=11311360`，`coverage_start=2015-01-01`，`coverage_end=2026-05-28`，`file_count=12` |
| 研究重跑脚本语法检查 | PASS | `uv run --python 3.11 python -m py_compile scripts/cr018_run_production_current_truth_research.py scripts/cr018_release_catalog_publish.py` | 无输出，通过 |
| 研究重跑脚本空白检查 | PASS | `git diff --check -- scripts/cr018_run_production_current_truth_research.py scripts/cr018_release_catalog_publish.py` | 无输出，通过 |

## Checklist

| # | 检查项 | 状态 | 证据 | 处理意见 |
|---|---|---|---|---|
| 1 | 使用 published current pointer 作为唯一输入 | PASS | `rerun-report.json` 中 `mode=real_published_current_truth_rerun`、`candidate_read_count=0`、`proxy_input_allowed_count=0` | 保持只读 current truth |
| 2 | 阶段三核心研究重跑 | PASS | `phase3-factor-ic-summary.csv`、`phase3-low-vol-group-returns.csv`、`phase3-strategy-summary.csv` | 已重算 IC、Rank IC、低波分组和 TopN 组合 |
| 3 | 阶段四低波稳健性核心重跑 | PASS | `phase4-low-vol-annual-breakdown.csv`、`rerun-report.json.phase_4` | 低波 Rank IC 均值为 `0.08839059147967537`，方向为正 |
| 4 | 阶段五风险、成本、容量、可交易性核心重跑 | PASS | `phase5-cost-grid.csv`、`rerun-report.json.phase_5` | 产生风险、成本网格、容量和 unfilled 统计 |
| 5 | 真实 benchmark 使用 | PASS | `rerun-report.json.phase_3.benchmark_metrics.399300.SZ` | 沪深300 `399300.SZ` 覆盖 `2015-01-05..2026-05-28` |
| 6 | 策略准入标准 | FAIL | `rerun-report.json.summary` | 低波 Top20 年化略低于沪深300，且最大回撤更差，不能解锁 QMT admission |
| 7 | QMT 操作边界 | PASS | `qmt-admission-evidence.json` | `allowed=false`、`qmt_admission_allowed_count=0`、`qmt_operation=0` |
| 8 | 真实操作边界 | PASS | `rerun-report.json.operation_counts` | `provider_fetch=0`、`credential_read=0`、`lake_write=0`、`catalog_current_pointer_publish=0`、`qmt_operation=0` |

## Research Summary

| 指标 | 值 | 结论 |
|---|---:|---|
| `status` | `fail` | 阶段三到阶段五已执行，但策略准入失败 |
| `strategy_pass` | `false` | 不满足 QMT admission 前置条件 |
| `low_vol_top20_annual_return` | `2.693702%` | 略低于沪深300 |
| `hs300_annual_return` | `2.767291%` | 真实 benchmark |
| `low_vol_minus_hs300_annual_return` | `-0.073589%` | 未跑赢沪深300 |
| `low_vol_top20_max_drawdown` | `-55.874898%` | 回撤劣于沪深300 |
| `hs300_max_drawdown` | `-46.696139%` | 真实 benchmark 回撤 |
| `low_vol_rank_ic_mean` | `0.08839059147967537` | 排名相关性仍为正 |
| `qmt_admission_allowed_count` | `0` | QMT simulation / live 继续阻断 |

## Phase 5 Tradability

| 项目 | 值 |
|---|---|
| `unfilled_trade_count` | `185` |
| `unfilled_reason_counts.limit_down_sell_blocked` | `12` |
| `unfilled_reason_counts.limit_up_buy_blocked` | `6` |
| `unfilled_reason_counts.missing_execution_price` | `164` |
| `unfilled_reason_counts.not_tradable` | `2` |
| `unfilled_reason_counts.st_buy_blocked` | `1` |
| `capacity.status` | `available` |
| `capacity.valid_participation_count` | `4522` |
| `capacity.over_10pct_count` | `3736` |

## Commands

```bash
uv run --python 3.11 python -m py_compile scripts/cr018_run_production_current_truth_research.py scripts/cr018_release_catalog_publish.py
git diff --check -- scripts/cr018_run_production_current_truth_research.py scripts/cr018_release_catalog_publish.py
uv run --python 3.11 python scripts/cr018_run_production_current_truth_research.py --lake-root /mnt/ugreen-data-lake --release-id release-cr018-production-current-truth-20150101-20260528-20260529 --run-id run-cr018-production-rerun-20150101-20260528-20260529-01 --start-date 2015-01-01 --end-date 2026-05-28 --overwrite
uv run --python 3.11 python -m market_data.cli report-readiness --lake-root /mnt/ugreen-data-lake --realism-mode production_strict
```

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| 重跑脚本 | `scripts/cr018_run_production_current_truth_research.py` | PASS | 只读 published current truth，不读凭据，不调用 provider，不发布 catalog，不操作 QMT |
| 发布脚本修复 | `scripts/cr018_release_catalog_publish.py` | PASS | `trade_status` release publish 使用 run 目录，避免只发布 2015 单文件 |
| 研究总报告 | `reports/production_current_truth/release-cr018-production-current-truth-20150101-20260528-20260529/run-cr018-production-rerun-20150101-20260528-20260529-01/rerun-report.json` | FAIL | 报告生成成功，策略准入失败 |
| 人类摘要 | `reports/production_current_truth/release-cr018-production-current-truth-20150101-20260528-20260529/run-cr018-production-rerun-20150101-20260528-20260529-01/rerun-summary.md` | FAIL | 与 JSON summary 一致 |
| QMT 准入证据 | `reports/production_current_truth/release-cr018-production-current-truth-20150101-20260528-20260529/run-cr018-production-rerun-20150101-20260528-20260529-01/qmt-admission-evidence.json` | PASS | `allowed=false`，`qmt_admission_allowed_count=0` |
| 标准输入快照 | `reports/production_current_truth/release-cr018-production-current-truth-20150101-20260528-20260529/run-cr018-production-rerun-20150101-20260528-20260529-01/input_data/` | PASS | `prices_rows=11311360`、`benchmark_rows=11072`、`index_members_rows=11311360` |

## Notes

- 本次真实研究重跑没有读取 `.env`，没有 provider fetch，没有真实 lake write，没有 catalog current pointer publish，没有 DuckDB 依赖变更，没有 QMT 操作。
- 运行期间出现 pandas `FutureWarning`：`Downcasting object dtype arrays on .fillna...`。该 warning 非阻断，不影响本次报告生成；随后已将脚本中的 bool 矩阵缺失填充改为 `where(...).astype(bool)`，避免后续运行继续触发同类 warning。
- 本次 `status=FAIL` 表示策略准入失败，不表示数据湖发布失败。数据湖 `production_strict` readiness 仍为 `PASS`。

## 结论

- 结论：`FAIL`
- 阻断项：`qmt_admission` 被 `production_rerun_strategy_criteria_failed` 阻断。
- 豁免项：无。
- 下一步：不要进入 QMT simulation / live；先分析低波 production rerun 失败原因，补齐或接入 P1 行业、市值、流动性、风险模型约束后再重跑，或由用户另行决策调整策略准入标准。
