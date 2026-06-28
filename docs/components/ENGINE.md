# 组件说明：数据与回测引擎

本组件覆盖数据准备、标准化、质量检查、离线读取、组合构建、回测、指标和候选输出。它是研究流程的基础，不直接连接 QMT gateway，不下单，不读取交易凭据。

## 1. 组件边界

| 子模块 | 责任 | 主要检查 |
|---|---|---|
| `engine.data_prep` | provider 请求规划、节流、重试、raw cache、manifest。 | source/interface allowlist、dry-run、manifest lineage。 |
| `engine.normalizer` | raw / manifest 到标准化 parquet。 | schema、日期、symbol、复权口径、重复行。 |
| `engine.quality` | 覆盖率、缺失率、重复记录、异常价格、新鲜度。 | `pass/warn/fail`、blocked claims。 |
| `engine.data_loader` | 离线读取 current truth 或 clean feed。 | PIT、quality gate、adjustment policy。 |
| `engine.portfolio` | 组合目标、调仓、交易成本、现金处理。 | lot size、turnover、cash、unfilled。 |
| `engine.backtest` | 单次回测和调仓 schedule。 | decision time、T+1、成本、净值。 |
| `engine.metrics` | 收益、回撤、Sharpe、换手等指标。 | 指标字段完整性和报告一致性。 |
| `engine.research_cli` | 本地研究 CLI 公共 helper。 | 内存预算、JSON 安全转换、参数解析，不包含业务研究逻辑。 |

## 2. 常用命令

```bash
uv sync --python 3.11
uv run --python 3.11 pytest -q
uv run --python 3.11 python -m compileall engine strategies tests
```

数据准备类命令如果需要 `.env`，只能由用户在本机显式执行；文档和 evidence 不保存 token 或私有 lake root。

脚本入口长期路径按能力域放在 `scripts/data_lake/`、`scripts/research/`、`scripts/qmt/` 和 `scripts/quality/`。根目录中带 `cr*`、`chapter*`、`stage*` 的脚本仅作为 legacy 兼容入口保留；新增入口必须通过 `scripts/quality/check_script_entrypoints.py`。

## 3. 检查清单

| 阶段 | 检查项 | 失败处理 |
|---|---|---|
| 数据准备前 | source/interface 已登记，date range 明确，run_id 唯一。 | 返回 dry-run remediation，不抓取。 |
| 标准化前 | raw cache 和 manifest 存在且 lineage 对齐。 | 不生成 current truth。 |
| 质量检查 | P0 dataset 通过 readiness，blocked claims 没有被覆盖。 | 保持 unavailable / blocked。 |
| 读取数据 | clean feed 完成 PIT、quality、复权和 benchmark policy gate。 | reader fail closed。 |
| 回测后 | 净值、交易、成本、指标和 metadata 一致。 | 不输出候选。 |
