---
check_id: "EXPERIMENTS-RERUN-2026-05-22"
workflow_id: "local_backtest"
scope: "experiments-rerun"
executed_at: "2026-05-22T08:36:17+08:00"
result: "PASS_WITH_OBSERVATION"
artifact_root: "/tmp/local_backtest_experiments_rerun_20260522_083245"
diagnostic_root: "/tmp/local_backtest_experiment09_diagnostic_20260522_083245"
---

# experiments 实践全量复跑结果

## Entry Criteria

| 准则 | 状态 | 证据 |
|---|---|---|
| 用户要求明确 | PASS | 用户要求“experiments 中的实践，都重跑一下”。 |
| 范围已确认 | PASS | 仓库当前实际实验入口为 `run_experiment_06_07.py`、`08.py`、`09.py`、`10.py`、`12.py`、`13.py`、`14.py`、`15_factor_framework.py`、`16_momentum_factor.py`；`reporting.py` 为共享 helper。 |
| 安全边界明确 | PASS | 本轮不使用 `--env-file .env`，不触发真实 Tushare，不写仓库默认 `reports/**` 或真实 `data/**`；直接 CLI 输出统一写 `/tmp`。 |

## Agent Dispatch Evidence

| Lane | mode | agent | agent_id | handoff | result |
|---|---|---|---|---|---|
| pytest A | `spawn_agent` | `qa-wei` | `019e4d19-3cba-7523-af94-dc07fb6d8a85` | `process/handoffs/META-QA-EXPERIMENTS-RERUN-A-2026-05-22.md` | PASS |
| pytest B | `spawn_agent` | `qa-lv` | `019e4d19-3d01-7ad2-bcb0-9fb4ae3e2c88` | `process/handoffs/META-QA-EXPERIMENTS-RERUN-B-2026-05-22.md` | PASS |
| CLI smoke / static | main thread | `meta-po` | N/A | 本文件 | PASS_WITH_OBSERVATION |

## Pytest 复跑结果

| 分组 | 命令 | 结果 |
|---|---|---|
| A | `uv run --python 3.11 pytest -q tests/test_story_004_013.py tests/test_cr007_experiment_real_benchmark_consumption.py tests/test_market_data_hs300_benchmark.py` | PASS，`32 passed` |
| B | `uv run --python 3.11 pytest -q tests/test_experiment_14_data_and_benchmark.py tests/test_experiment_15_factor_framework.py tests/test_experiment_16_momentum_factor.py tests/test_cr008_research_input_metadata.py tests/test_cr008_proxy_real_benchmark_fields.py tests/test_cr008_factor_auxiliary_data_contract.py` | PASS，`42 passed` |

## 静态与语法检查

| 检查 | 命令摘要 | 结果 |
|---|---|---|
| 语法编译 | `uv run --python 3.11 python -m compileall -q experiments tests` | PASS，退出码 0 |
| forbidden import | 扫描 `experiments/` 是否导入 `market_data.connectors/runtime/storage` | PASS，无命中 |
| 凭据边界 | 扫描 `.env`、`TUSHARE_TOKEN`、NAS/credential 相关模式 | PASS，无命中 |
| 危险命令 | 扫描 `rm -rf`、`sudo`、`curl`、`wget`、`subprocess`、`os.system`、`shell=True` 等 | PASS，无命中 |

## CLI 实践复跑结果

所有 CLI 均使用 `/tmp/local_backtest_experiments_rerun_20260522_083245/data` 的合成 parquet fixture，输出写入 `/tmp/local_backtest_experiments_rerun_20260522_083245/reports/**`。

| 实践入口 | 结果 | 关键输出 / 观察 |
|---|---|---|
| `run_experiment_06_07.py` | PASS | 生成 `/tmp/local_backtest_experiments_rerun_20260522_083245/reports/experiments_06_07/backtest_report.md` |
| `run_experiment_08.py` | PASS | 生成 `/tmp/local_backtest_experiments_rerun_20260522_083245/reports/experiment_08/backtest_report.md` |
| `run_experiment_09.py` common fixture | OBSERVED_FAIL | 退出码 1；`sanity_check.csv` 中 RSI 两组极端参数收益均为 `0.0`，触发预期 fail-fast：`sanity check 未通过：存在参数组收益完全相同，已停止参数扫描`。 |
| `run_experiment_09.py` volatility diagnostic fixture | PASS | 使用波动型 `/tmp` fixture 重跑，退出码 0；momentum、RSI、MACD 三组 sanity 均 PASS，生成 `/tmp/local_backtest_experiment09_diagnostic_20260522_083245/reports/experiment_09/backtest_report.md`。 |
| `run_experiment_10.py` | PASS | 生成 `/tmp/local_backtest_experiments_rerun_20260522_083245/reports/experiment_10/backtest_report.md` |
| `run_experiment_12.py` | PASS | 生成 `/tmp/local_backtest_experiments_rerun_20260522_083245/reports/experiment_12/backtest_report.md` |
| `run_experiment_13.py` | PASS | 生成 `/tmp/local_backtest_experiments_rerun_20260522_083245/reports/experiment_13/backtest_report.md` |
| `run_experiment_14.py` | PASS | 生成 `/tmp/local_backtest_experiments_rerun_20260522_083245/reports/experiment_14/data_and_benchmark_report.md` |
| `run_experiment_15_factor_framework.py` | PASS | 生成 `/tmp/local_backtest_experiments_rerun_20260522_083245/reports/experiment_15/factor_schema.json` |
| `run_experiment_16_momentum_factor.py` | PASS | 生成 `/tmp/local_backtest_experiments_rerun_20260522_083245/reports/experiment_16/data_coverage.csv` |

## Observation

| 项 | 状态 | 说明 |
|---|---|---|
| 实验 09 对输入形态敏感 | OBSERVATION | 在单调趋势型 common fixture 上，RSI 两组极端参数都没有形成收益差异，触发脚本设计中的 sanity fail-fast。使用波动型 fixture 后同一入口 PASS，因此当前证据不指向代码回归，而是说明实验 09 CLI smoke 需要具备足够波动的价格输入才能覆盖 RSI 参数注入。 |

## Exit Criteria

| 准则 | 状态 | 证据 |
|---|---|---|
| experiments 相关 pytest 全部通过 | PASS | A 组 `32 passed`，B 组 `42 passed`。 |
| 实验 CLI 入口已直接复跑 | PASS_WITH_OBSERVATION | 9 个入口均执行；实验 09 common fixture 触发预期 sanity fail-fast，diagnostic fixture 复跑通过。 |
| 未触发真实 Tushare / `.env` | PASS | 本轮所有命令均未使用 `--env-file .env`。 |
| 未写仓库默认 `reports/**` / 真实 `data/**` | PASS | CLI 输出均写 `/tmp/local_backtest_experiments_rerun_20260522_083245` 或 `/tmp/local_backtest_experiment09_diagnostic_20260522_083245`。 |
| 静态安全边界通过 | PASS | forbidden import、凭据、危险命令扫描均无命中。 |

## Deliverables

| 交付物 | 路径 / 位置 | 状态 |
|---|---|---|
| experiments 复跑汇总检查结果 | `process/checks/EXPERIMENTS-RERUN-2026-05-22.md` | DONE |
| QA A handoff | `process/handoffs/META-QA-EXPERIMENTS-RERUN-A-2026-05-22.md` | DONE |
| QA B handoff | `process/handoffs/META-QA-EXPERIMENTS-RERUN-B-2026-05-22.md` | DONE |
| CLI smoke artifacts | `/tmp/local_backtest_experiments_rerun_20260522_083245` | DONE |
| experiment 09 diagnostic artifacts | `/tmp/local_backtest_experiment09_diagnostic_20260522_083245` | DONE |

## Conclusion

结论：`PASS_WITH_OBSERVATION`。

experiments 相关 pytest 全部通过，静态/语法/安全边界检查通过，直接 CLI smoke 中除实验 09 common fixture 外均通过。实验 09 的 common fixture 失败为预期 sanity fail-fast：RSI 两组参数收益完全相同。使用波动型 fixture 复跑实验 09 后通过，因此当前没有发现阻断性代码回归；需要记录的观察项是实验 09 CLI smoke 数据必须包含足够波动，不能使用单调趋势 fixture 作为唯一实践输入。
