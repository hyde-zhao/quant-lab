---
check_id: "CR007-EXPERIMENT-06-13-RERUN-2026-05-20"
type: "runtime_observation"
status: "PARTIAL"
owner: "meta-po"
created_at: "2026-05-20T23:07:07+08:00"
change_id: "CR-007"
output_root: "/tmp/local_backtest_exp_20260520"
---

# CR007 实验 6-13 重跑观察

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 使用 canonical/gold 只读输入 | PASS | 命令均传入 `--input-mode canonical-gold --market-data-lake-root <configured-lake-root>` | 未使用 legacy-flat，未读取旧 `data/**` |
| 不读取旧质量报告 | PASS | 命令均传入 `--quality-report /tmp/local_backtest_exp_20260520/no_quality_report.csv` | canonical/gold 路径未消费旧 `reports/data_quality_report.csv` |
| 不覆盖仓库报告 | PASS | 输出根目录为 `/tmp/local_backtest_exp_20260520` | 未写仓库 `reports/**` |
| 不使用凭据或真实抓取 | PASS | 未使用 `--env-file`、未启用 Tushare 抓取命令 | 只读已有 canonical lake 数据 |

## Checklist

| # | 检查项 | 状态 | 证据 | 说明 |
|---|---|---|---|---|
| 1 | canonical `prices` 是否可用于短窗口策略回测 | PASS | loader 输出 rows=80，symbols=6，start=2025-01-02，end=2025-05-07 | quality_status=`warn`，dataset_status=`warn` |
| 2 | 实验 6/7 是否可运行 | PASS | `/tmp/local_backtest_exp_20260520/experiments_06_07/backtest_report.md` | 动量、RSI 均完成；使用 5/6 股票、80 个交易日 |
| 3 | 实验 8 是否可运行 | PASS | `/tmp/local_backtest_exp_20260520/experiment_08/backtest_report.md` | MACD 完成；5 股票、80 个交易日 |
| 4 | 实验 9 是否可运行 | PASS | `/tmp/local_backtest_exp_20260520/experiment_09/backtest_report.md` | 参数敏感性扫描完成，sanity check 均 PASS |
| 5 | 实验 10 默认 2015-2025 口径是否可运行 | FAIL | `ValueError: 训练期或样本外测试期为空，请检查本地数据覆盖范围` | 长周期训练 / 样本外数据不齐 |
| 6 | 实验 10 小窗口切分是否可运行 | PASS | `/tmp/local_backtest_exp_20260520/experiment_10_window/backtest_report.md` | 2025-01-02..2025-03-14 训练，2025-03-17..2025-05-07 测试 |
| 7 | 实验 12 默认市场分段是否可运行 | PARTIAL | `/tmp/local_backtest_exp_20260520/experiment_12/segment_summary.csv` | 2015-2020 分段全部 `skipped_no_local_data` |
| 8 | 实验 13 是否可运行 | PASS_WITH_LIMITATION | `/tmp/local_backtest_exp_20260520/experiment_13/backtest_report.md` | 依赖实验 10 小窗口输出和实验 12 分段输出；报告仍使用基准代理，不是真实沪深300 |
| 9 | 实验 11 是否存在可执行入口 | N/A | `rg run_experiment_11` 未发现脚本 | 当前仓库没有 `experiments/run_experiment_11.py` |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 可判断当前数据是否齐全 | PASS | 本文件 Checklist | 当前只足以支持 2025 小窗口实验，不足以支持 2015-2025 长周期目标 |
| 未越过安全边界 | PASS | 命令与输出路径 | 未读 `.env`，未真实抓取，未写真实 lake，未读旧 `data/**` 或旧质量报告 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| 实验 6/7 临时输出 | `/tmp/local_backtest_exp_20260520/experiments_06_07/` | PASS | 临时观察产物，不入仓库 |
| 实验 8 临时输出 | `/tmp/local_backtest_exp_20260520/experiment_08/` | PASS | 临时观察产物，不入仓库 |
| 实验 9 临时输出 | `/tmp/local_backtest_exp_20260520/experiment_09/` | PASS | 临时观察产物，不入仓库 |
| 实验 10 小窗口临时输出 | `/tmp/local_backtest_exp_20260520/experiment_10_window/` | PASS | 默认长周期口径失败后，使用当前可用窗口补跑 |
| 实验 12 临时输出 | `/tmp/local_backtest_exp_20260520/experiment_12/` | PARTIAL | 默认 2015-2020 分段无数据 |
| 实验 13 临时输出 | `/tmp/local_backtest_exp_20260520/experiment_13/` | PASS_WITH_LIMITATION | 使用小窗口实验 10 依赖；仍为基准代理 |

## 结论

- 结论：`PARTIAL`
- 当前 canonical `prices` 数据可读，但只覆盖 `2025-01-02` 至 `2025-05-07`，6 个标的、80 个交易日，质量状态为 `warn`。
- 实验 6/7/8/9/13 可在 2025 小窗口运行。
- 实验 10 的正式默认目标 `2015-01-01` 至 `2025-12-31` 不可运行，原因是训练期或样本外测试期为空。
- 实验 12 的 2015-2020 市场分段全部因本地数据不足跳过。
- 当前数据仍未齐全：CR007 所要求的长周期 `prices`、真实同区间 `hs300_index` / `trade_calendar`、市场分段和真实 benchmark 仍未满足。
