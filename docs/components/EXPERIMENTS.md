# 组件说明：实验与报告

实验组件用于把研究假设转成可复验的本地实验输出，包括因子实证、异象研究、参数扫描、候选筛选、图表和报告。实验输出不是 QMT-ready 或 simulation-ready 结论。

## 1. 组件边界

| 对象 | 责任 | 非目标 |
|---|---|---|
| research runner | 按研究能力域执行本地实验。 | 不连接 QMT，不发布策略。 |
| 参数扫描 | 生成参数组合和失败行记录。 | 不自动选择真实交易参数。 |
| 候选筛选 | 输出少量候选供人工复核。 | 不作为交易指令。 |
| 图表 / 报告 | 输出净值、回撤、指标和说明。 | 不替代数据质量或策略准入。 |

## 2. 常用检查

| 检查 | 通过标准 |
|---|---|
| 输入数据 | 使用 clean feed 或明确 unavailable。 |
| 参数空间 | 参数数量、范围、失败组合可追踪。 |
| 报告字段 | 收益、回撤、Sharpe、换手、成本、metadata 齐全。 |
| 候选数量 | 候选数受限，选择理由可解释。 |
| 声明边界 | 不声明 QMT-ready、simulation-ready、live-ready。 |

## 3. 与多因子研究的关系

实验组件可以生成研究证据，但策略准入包应由多因子研究组件汇总。若要进入模拟盘运行，必须再经过 runner 授权、gateway 检查、P1-P4 和对账。

## 4. ML 实验可选依赖

默认 `uv sync --python 3.11` 只安装核心依赖，足够运行普通实验、合同测试和 fixture/static 验证。实验 23-29 的 ML 全流程会进入 `scikit-learn` / `LightGBM` 路径，这些依赖在 `pyproject.toml` 的 `ml` dependency group 中。

运行 ML 训练、walk-forward 全流程或 `tests/test_experiment_23_29_ml_factor_suite.py` 前，先安装并启用该组：

```bash
uv sync --python 3.11 --group ml
uv run --python 3.11 --group ml pytest -q tests/test_experiment_23_29_ml_factor_suite.py
```

CR-139 S10 的 no-bypass / lake-as-of 合同测试属于 static/fixture 范围，不要求安装 `ml` 组。安装 `ml` 组只解决本地 ML 训练依赖，不授权 provider fetch、lake write、catalog publish、DuckDB runtime、QMT、simulation 或 live。
