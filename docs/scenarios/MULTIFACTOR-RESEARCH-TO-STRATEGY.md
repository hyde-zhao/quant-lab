# 场景案例：多因子策略研究，从数据准备到输出策略

本案例面向研究员，目标是从本地数据准备开始，完成多因子研究，并输出可交给 runner 审查的策略准入包。该案例不连接 QMT gateway，不下单，不读取交易凭据。

## 大步骤 1：准备环境和研究范围

### 1.1 同步依赖

```bash
uv sync --python 3.11
uv run --python 3.11 pytest -q
```

检查：

| 检查项 | 通过标准 |
|---|---|
| Python | 使用 3.11。 |
| 依赖 | `uv sync` 成功。 |
| 基础测试 | pytest 通过或失败项已定位。 |

### 1.2 定义研究窗口和 run id

小步骤：

1. 确认 `start_date`、`end_date`、universe、benchmark。
2. 生成唯一 `run_id`。
3. 确认本轮只做研究，不做 QMT / simulation / live。

检查：

| 检查项 | 通过标准 |
|---|---|
| 时间窗口 | 起止日期明确，不能超过数据可用范围。 |
| universe | PIT 股票池或 fixed universe 的偏差披露明确。 |
| 权限计数 | provider fetch / lake write / credential read 是否需要授权已明确。 |

## 大步骤 2：数据准备

### 2.1 先做 dry-run

示例：

```bash
UV_CACHE_DIR=.cache/uv uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli hs300-backfill \
  --index-code <index-code> \
  --start-date <start-date> \
  --end-date <end-date> \
  --run-id <run-id> \
  --dry-run true
```

检查：

| 检查项 | 通过标准 |
|---|---|
| source/interface | exact source 和 interface 在 allowlist 内。 |
| lake root | 指向外置 lake，不写仓库默认 `data/**`。 |
| dry-run | 网络调用和写湖为 0。 |
| remediation | 缺失项以结构化 job spec 输出。 |

### 2.2 执行授权后的数据准备

小步骤：

1. 用户确认 `.env` 由本机加载，不打印 token。
2. 执行 provider fetch / raw write。
3. 生成 manifest。
4. 记录 run id 和 source/interface。

检查：

| 检查项 | 通过标准 |
|---|---|
| 凭据 | 不写入日志、文档、evidence。 |
| raw | raw cache 与 manifest 对齐。 |
| resume | 重跑策略明确，duplicate manifest 不静默覆盖。 |

## 大步骤 3：标准化和质量检查

### 3.1 标准化

```bash
UV_CACHE_DIR=.cache/uv uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli normalize \
  --dataset <dataset> \
  --run-id <run-id>
```

检查：

| 检查项 | 通过标准 |
|---|---|
| schema | 必填列存在。 |
| lineage | normalized candidate 可追溯 raw / manifest。 |
| adjustment policy | raw / qfq / hfq / returns_adjusted 不混用。 |

### 3.2 验证质量

```bash
UV_CACHE_DIR=.cache/uv uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli validate \
  --dataset <dataset> \
  --run-id <run-id>
```

检查：

| 检查项 | 通过标准 |
|---|---|
| quality status | P0 数据集为 pass。 |
| PIT | `available_at <= decision_time`。 |
| blocked claims | blocked 优先于 allowed，不被下游覆盖。 |
| publish | validate pass 不等于 publish。 |

## 大步骤 4：构建研究输入

### 4.1 读取 clean feed

小步骤：

1. 从 catalog current truth 或 validated candidate 读取数据。
2. 检查 benchmark、calendar、universe、tradability。
3. 生成研究输入 metadata。

检查：

| 检查项 | 通过标准 |
|---|---|
| clean feed | PIT、quality、复权、benchmark policy 均通过。 |
| unavailable | 缺失数据返回 typed unavailable，不静默回退旧数据。 |

### 4.2 构建 factor panel 和 label window

小步骤：

1. 定义 `FactorSpec` 和 `FactorRunSpec`。
2. 生成 factor panel。
3. 生成 label window。
4. 做 no-lookahead 检查。

检查：

| 检查项 | 通过标准 |
|---|---|
| factor direction | 正负方向明确。 |
| panel stages | raw、directional、winsorized、zscore 可追踪。 |
| label | label window 不重叠，不使用未来可得信息。 |

## 大步骤 5：单因子评价

小步骤：

1. 计算 IC / RankIC。
2. 计算分层收益。
3. 计算 turnover、cost、exposure。
4. 输出单因子报告。

检查：

| 检查项 | 通过标准 |
|---|---|
| IC / RankIC | 指标存在或 unavailable 原因明确。 |
| 分层收益 | 分组数量、收益、样本数齐全。 |
| 成本 | 成本假设明确，不默认真实成交。 |
| exposure | 行业 / 风格暴露可解释。 |

## 大步骤 6：多因子组合和策略候选

小步骤：

1. 选择因子池。
2. 配置组合方法，例如 `rule_weight` 或 `linear_score`。
3. 生成 `MultiFactorPortfolioPlan`。
4. 生成候选策略摘要。

检查：

| 检查项 | 通过标准 |
|---|---|
| 权重 | 单因子权重、max_weight、归一化规则明确。 |
| 风险 | 单票上限、组合上限、换手约束明确。 |
| 容量 | capacity / liquidity 缺失时不声明可放大。 |
| 输出 | 只输出研究候选，不下单。 |

## 大步骤 7：输出策略准入包

小步骤：

1. 汇总数据证据、因子证据、组合证据和限制。
2. 生成 `StrategyAdmissionPackage` 或等价 JSON。
3. 标记 blocked claims 和 limitations。
4. 把包交给 runner 做导入检查。

检查：

| 检查项 | 通过标准 |
|---|---|
| evidence refs | 每个结论有证据引用。 |
| limitations | QMT-ready / simulation-ready / live-ready 未被误声明。 |
| handoff | runner 所需 strategy_id、run_id、target date、capital base 明确。 |
| 安全 | 凭据、账号、token、私有路径不在包内。 |
