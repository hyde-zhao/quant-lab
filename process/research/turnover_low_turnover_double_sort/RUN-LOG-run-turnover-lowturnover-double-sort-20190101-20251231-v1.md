# 运行记录：run-turnover-lowturnover-double-sort-20190101-20251231-v1

**开始时间**: 2026-06-03T15:57:45Z

## 命令

```bash
uv run --python 3.11 python experiments/run_experiment_turnover_factor.py \
    --start-date 2019-01-01 \
    --end-date 2025-12-31 \
    --warmup-start 2018-01-02 \
    --run-id run-turnover-lowturnover-double-sort-20190101-20251231-v1 \
    --rebalance-freq 20 \
    --group-count 5 \
    --forward-horizon 20 \
    --min-252d-samples 60
```

## 输出路径

- 研究报告: reports/factor_research/turnover_low_turnover_double_sort/run-turnover-lowturnover-double-sort-20190101-20251231-v1/turnover_factor_replication_report.md
- 数据产物: reports/factor_research/turnover_low_turnover_double_sort/run-turnover-lowturnover-double-sort-20190101-20251231-v1/
- 过程文档: process/research/turnover_low_turnover_double_sort/
