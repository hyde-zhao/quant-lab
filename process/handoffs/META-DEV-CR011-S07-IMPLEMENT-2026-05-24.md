---
handoff_id: "META-DEV-CR011-S07-IMPLEMENT-2026-05-24"
from_agent: "meta-po"
to_agent: "meta-dev"
agent_name: "dev-lv the 2nd"
change_id: "CR-011"
story_id: "CR011-S07-liquidity-capacity-and-cost-sensitivity"
wave_id: "CR011-RESEARCH-BATCH-B-DEV-W7"
status: "completed"
created_at: "2026-05-24T15:25:45+08:00"
updated_at: "2026-05-24T15:47:13+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e58e5-8503-79e3-a6d0-489ca72aa27f"
  thread_id: "019e58e5-8503-79e3-a6d0-489ca72aa27f"
  tool_name: "spawn_agent"
  spawned_at: "2026-05-24T15:31:45+08:00"
  resumed_at: ""
  completed_at: "2026-05-24T15:44:14+08:00"
  closed_at: "2026-05-24T15:47:13+08:00"
  result: "completed"
---

# META-DEV CR011-S07 实现交接

## 任务

按确认版 LLD 实现 `CR011-S07-liquidity-capacity-and-cost-sensitivity` 的离线代码与 CP6 自检。目标是让新版实验 17-21 v2 在输出容量或成本相关结论前，必须消费可追溯的 amount、volume、turnover、ADV 或等价流动性输入，固定输出 `[0, 5, 10, 20]` bps 四档成本敏感性网格，并在容量报告中至少包含成交额占比、换手、持仓数、样本损失、成本侵蚀 5 类字段。

你不是独占代码库：当前工作树已有 CR011-S01..S06 的实现和验证结果。不得回退他人修改；若发现冲突，按现有实现适配，并在 CP6 写清楚。

## 输入

| 类型 | 路径 | 状态 |
|---|---|---|
| Story | `process/stories/CR011-S07-liquidity-capacity-and-cost-sensitivity.md` | dev-ready |
| LLD | `process/stories/CR011-S07-liquidity-capacity-and-cost-sensitivity-LLD.md` | confirmed / implementation_allowed |
| CP5 自动预检 | `process/checks/CP5-CR011-S07-liquidity-capacity-and-cost-sensitivity-LLD-IMPLEMENTABILITY.md` | PASS |
| CP5-B 批次人工确认 | `checkpoints/CP5-CR011-RESEARCH-BATCH-B-LLD-BATCH.md` | approved |
| 上游 S03 CP7 | `process/checks/CP7-CR011-S03-tradability-status-and-price-limit-gates-VERIFICATION-DONE.md` | PASS / verified |
| 上游 S04 CP7 复验 | `process/checks/CP7-CR011-S04-ohlcv-vwap-clean-execution-feed-REVERIFY-DONE.md` | PASS / verified |
| 上游 S06 CP7 复验 | `process/checks/CP7-CR011-S06-industry-market-cap-style-exposure-data-REVERIFY-DONE.md` | PASS / verified |

## 允许写入范围

- `engine/research_dataset.py`
- `engine/portfolio.py`
- `experiments/run_experiment_17_21_factor_suite.py`
- `tests/test_cr011_capacity_cost_sensitivity.py`
- `process/checks/CP6-CR011-S07-liquidity-capacity-and-cost-sensitivity-CODING-DONE.md`
- `process/stories/CR011-S07-liquidity-capacity-and-cost-sensitivity.md` 的实现状态字段

## 禁止范围

- 不实现或修改 `CR011-S08`。
- 不修改 `market_data/connectors/**`、`market_data/runtime.py`、`market_data/storage.py`、`data/**`、`.env`、`reports/experiment_17_21/factor_strategy_report.md`、`delivery/**`。
- 不修改 `process/STATE.md`、`process/STORY-STATUS.md`、`process/DEVELOPMENT-PLAN.yaml`；这些由 meta-po 回填。
- 不真实联网，不真实 Tushare 抓取，不写真实 lake。
- 不读取、打印或记录 `.env`、token、密码、私钥、cookie、session 或其他凭据。
- 不读取、列出、迁移、复制、删除旧 `data/**`。
- 不覆盖旧 `reports/experiment_17_21/factor_strategy_report.md`。

## 实现要求

- 消费 LLD 第 4、6、7、8、10、13 节；当前 Story / CP5-B / STATE 已放行离线实现。
- 固定 `cost_grid_bps=[0, 5, 10, 20]`，按 exact 顺序输出四档成本场景；不得根据历史表现自动选优、删减或重排。
- 容量报告必须结构化输出 5 类字段：成交额占比、换手、持仓数、样本损失、成本侵蚀。
- `engine.research_dataset` 必须把 liquidity / capacity 输入 availability 纳入研究 metadata，并输出 `liquidity_capacity_status`、`capacity_cost_status`、`allowed_claims`、`blocked_claims` 和 missing reason。
- `engine.portfolio` 必须提供容量和成本敏感性计算入口，基于 trades、holdings、portfolio returns、liquidity bundle 和固定成本网格输出 JSON-safe 结果。
- 缺 amount、volume、turnover、ADV 或等价 liquidity/capacity 输入时，不得声明 `capacity_tradable`、`capacity_supported`、`liquidity_screened_capacity` 或等价容量可交易 claim；相关声明输出次数为 0。
- 只提供单一成本点、缺少四档成本网格或 cost scenario 行不完整时，`cost_sensitivity_status=fail`，并写 `blocked_claims`。
- S03 tradability blocked trades、S04 execution price degradation 和 S06 exposure / size claims 不得被 S07 放宽；S07 只能合并上游 blocked claims，不能重新允许真实可成交、真实 VWAP、中性化或容量声明。
- 实验脚本只追加 CR011 v2 metadata / artifact contract，不覆盖旧实验 17-21 报告；最终版本化报告路径归 S08 / documentation 阶段消费。

## CP6 要求

CP6 文件必须写入：

- Entry Criteria、Checklist、Exit Criteria、Deliverables。
- Agent Dispatch Evidence：`spawn_agent`、agent id/thread id、handoff path、完成时间。
- 代码变更清单与 TASK-ID 对应关系。
- 验证命令和结果。
- 安全确认：`network_calls=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_operations=0`、旧报告覆盖次数 0。

## 建议验证命令

- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile engine/research_dataset.py engine/portfolio.py experiments/run_experiment_17_21_factor_suite.py tests/test_cr011_capacity_cost_sensitivity.py`
- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr011_capacity_cost_sensitivity.py`
- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr011_tradability_gates.py tests/test_cr011_execution_price_policy.py tests/test_cr011_exposure_claims.py`

## 期望输出

| 交付物 | 路径 |
|---|---|
| capacity / cost metadata 与 helper 实现 | `engine/research_dataset.py`、`engine/portfolio.py`、`experiments/run_experiment_17_21_factor_suite.py` |
| S07 测试 | `tests/test_cr011_capacity_cost_sensitivity.py` |
| CP6 编码完成检查 | `process/checks/CP6-CR011-S07-liquidity-capacity-and-cost-sensitivity-CODING-DONE.md` |
| Story 实现状态 | `process/stories/CR011-S07-liquidity-capacity-and-cost-sensitivity.md` |

若 CP6 PASS，请将 Story 状态推进为 `ready-for-verification`；若实现发现上游合同或授权阻断，请写 CP6 `BLOCKED` 并停止，不得扩大范围。

## 完成结果

| 项 | 结果 | 证据 |
|---|---|---|
| S07 离线实现 | completed | `engine/research_dataset.py`、`engine/portfolio.py`、`experiments/run_experiment_17_21_factor_suite.py`、`tests/test_cr011_capacity_cost_sensitivity.py` |
| CP6 自检 | PASS | `process/checks/CP6-CR011-S07-liquidity-capacity-and-cost-sensitivity-CODING-DONE.md` |
| 子 agent 关闭 | closed | `agent_id=019e58e5-8503-79e3-a6d0-489ca72aa27f`，closed_at=`2026-05-24T15:47:13+08:00` |
| 下一门控 | CP7 | 等待 meta-po 调度 meta-qa 独立验证 |
