# CR-034 第三章真实实证

## 当前结论

- 最新实证：`PASS`
- 正式 run_id：`run-chapter3-empirical-2000-2019`
- 覆盖窗口：2000-01-01 至 2019-12-31
- 因子数量：7
- 因子面板行数：2,640,077
- 标签行数：447,186
- 调仓期数：239
- 资源边界：`--max-memory-gb 16`，正式报告观测最大 RSS 约 2.15GB，`memory_status=pass`

## 产物

| 文件 | 说明 |
|---|---|
| `run-chapter3-empirical-2000-2019/EMPIRICAL-RUN-REPORT.md` | 人工可读实证报告 |
| `run-chapter3-empirical-2000-2019/EMPIRICAL-RUN-REPORT.json` | 机器可读实证报告 |
| `run-chapter3-empirical-2000-2019/factor_metrics.csv` | 7 个因子的单因子评价摘要 |
| `run-chapter3-empirical-2000-2019/MULTIFACTOR-ADMISSION-SUMMARY.json` | 后续多因子研究准入摘要 |
| `../../../reports/chapter3_factor_panel/run-chapter3-empirical-2000-2019/factor_panel.parquet` | 第三章 7 因子月度长表面板 |
| `../../../reports/chapter3_factor_panel/run-chapter3-empirical-2000-2019/factor_panel_manifest.json` | 因子面板 manifest、operation_counts 和内存预算证据 |

## 运行方式

正式 2000-2019 窗口必须使用默认 `chunked` 模式。该模式按年份生成 part 文件，并支持 `--resume` 复用已完成年度产物，避免全量 pandas 矩阵造成资源压力。

`full` 模式仅允许两年以内调试窗口；若要放开长窗口，必须显式传 `--allow-large-full-run`，但不作为 16GB 环境下的默认路径。

## 使用边界

本目录产物允许作为项目内部多因子研究输入；不构成 production-valid、QMT-ready、simulation-ready、live-ready 或 broker order 授权。后续如果进入模拟盘、实盘或 QMT 链路，必须走独立 CR / per-run authorization。
