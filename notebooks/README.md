# 本地研究 Notebook

本目录提供本地探索入口，不替代正式报告图表。正式可复现图表仍由 `engine.charts.generate_report_charts("reports")` 写入 `reports/charts/*.png` 与 `reports/charts/index.md`。

## 启动方式

先同步探索依赖：

```bash
uv sync --python 3.11 --group exploration
```

启动 Notebook：

```bash
uv run --python 3.11 --group exploration jupyter notebook notebooks/local_research_intro.ipynb
```

## 边界

- Notebook 默认只做 inline 展示，不写入正式报告目录。
- 示例读取 `reports/equity_curve.csv` 后绘制净值和回撤；文件不存在时只提示，不生成正式数据。
- K 线示例只在用户自备 OHLCV 数据存在且字段完整时启用 `mplfinance`；缺少 `open/high/low/close/volume` 或 `Open/High/Low/Close/Volume` 时跳过。
- 不提交 `.ipynb_checkpoints/`、`notebooks/outputs/` 或 `notebooks/tmp/`。
