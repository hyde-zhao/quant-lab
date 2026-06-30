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

## 5. 实验编号索引

| 编号 | 入口 | 责任 |
|---:|---|---|
| 06/07 | `experiments/run_experiment_06_07.py` | 动量与 RSI 策略本地回测报告。 |
| 08 | `experiments/run_experiment_08.py` | MACD 金叉 / 死叉策略回测报告。 |
| 09 | `experiments/run_experiment_09.py` | 多策略参数敏感性分析。 |
| 10 | `experiments/run_experiment_10.py` | 样本外测试与过拟合风险排序。 |
| 12 | `experiments/run_experiment_12.py` | 市场环境分段策略比较。 |
| 13 | `experiments/run_experiment_13.py` | 代理 benchmark / 真实 benchmark 与交易成本对比。 |
| 14 | `experiments/run_experiment_14.py` | 数据与 benchmark 审计报告。 |
| 15 | `experiments/run_experiment_15_factor_framework.py` | 因子框架与单因子回测。 |
| 16 | `experiments/run_experiment_16_momentum_factor.py` | 动量因子验证。 |
| 17-21 | `experiments/run_experiment_17_21_factor_suite.py` | 多因子套件与研究报告。 |
| 23-29 | `experiments/run_experiment_23_29_ml_factor_suite.py` | ML 因子套件；需要 `ml` dependency group。 |
| 30-36 | `experiments/run_experiment_30_36_stage5.py` | Stage 5 多因子研究与候选产出。 |
| turnover | `experiments/run_experiment_turnover_factor.py` | abnormal turnover 因子研究；CR140 Phase 3 仅做合成 fixture 重构等价验证。 |

当前 `experiments/` 顶层只保留实验入口。production_strict 数据湖审计、reporting helper、CR139 lake / training contract helper 和 production current truth dry-run contract 已归位到 `scripts/data_lake/` 或 `engine/`。
