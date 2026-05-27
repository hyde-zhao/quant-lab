---
handoff_id: "META-DEV-CR011-S06-CP7-FIX-2026-05-24"
from_agent: "meta-po"
to_agent: "meta-dev"
agent_name: "dev-zhang the 2nd"
change_id: "CR-011"
story_id: "CR011-S06-industry-market-cap-style-exposure-data"
wave_id: "CR011-DATA-BATCH-A-DEV-W6-FIX"
blocker_id: "CR011-S06-CP7-F01"
status: "completed"
created_at: "2026-05-24T14:42:55+08:00"
updated_at: "2026-05-24T14:49:44+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e58b9-c810-75e2-b93c-cb90dcc60000"
  thread_id: "019e58b9-c810-75e2-b93c-cb90dcc60000"
  tool_name: "spawn_agent"
  spawned_at: "2026-05-24T14:43:58+08:00"
  completed_at: "2026-05-24T14:47:05+08:00"
  closed_at: "2026-05-24T14:49:44+08:00"
  result: "completed"
---

# META-DEV CR011-S06 CP7 阻断项最小回修交接

## 任务

修复 `CR011-S06-CP7-F01`：`merge_exposure_claims_into_metadata()` 未写入 canonical metadata 字段 `float_market_cap_availability`，导致 CR011-S06 CP7 验收失败。

本次只做最小字段契约回修，不扩大 S06 功能，不实现 S07/S08，不做真实数据接入。

## 输入

| 类型 | 路径 | 状态 |
|---|---|---|
| Story | `process/stories/CR011-S06-industry-market-cap-style-exposure-data.md` | in-development / returned-from-CP7 |
| LLD | `process/stories/CR011-S06-industry-market-cap-style-exposure-data-LLD.md` | confirmed |
| 原 CP6 | `process/checks/CP6-CR011-S06-industry-market-cap-style-exposure-data-CODING-DONE.md` | PASS |
| CP7 失败检查 | `process/checks/CP7-CR011-S06-industry-market-cap-style-exposure-data-VERIFICATION-DONE.md` | FAIL |
| QA handoff | `process/handoffs/META-QA-CR011-S06-CP7-VERIFY-2026-05-24.md` | completed-fail |

## 阻断项

| 缺陷 ID | 严重度 | 事实 | 最小修复 |
|---|---|---|---|
| `CR011-S06-CP7-F01` | BLOCKING | QA handoff 要求 `industry_availability`、`market_cap_availability`、`float_market_cap_availability`、`style_exposure_availability` 四类 availability 进入 metadata；当前实现写入 `metadata["float_market_cap"]`，`rg -n "float_market_cap_availability"` 无命中 | 在 `merge_exposure_claims_into_metadata()` 中写入 canonical 字段 `float_market_cap_availability = exposure_availability.get("float_market_cap", {})`，同步更新测试断言；如需兼容下游，可保留 `float_market_cap` alias，但 canonical 字段必须存在 |

## 允许写入范围

- `engine/research_dataset.py`
- `tests/test_cr011_exposure_claims.py`
- `process/checks/CP6-CR011-S06-CP7-BLOCKER-FIX-CODING-DONE.md`
- `process/stories/CR011-S06-industry-market-cap-style-exposure-data.md` 的实现状态字段

## 禁止范围

- 不实现或修改 `CR011-S07`、`CR011-S08`。
- 不修改 `market_data/connectors/**`、`market_data/runtime.py`、`market_data/storage.py`、`data/**`、`.env`、`reports/experiment_17_21/factor_strategy_report.md`、`delivery/**`。
- 不修改 `process/STATE.md`、`process/STORY-STATUS.md`、`process/DEVELOPMENT-PLAN.yaml`；这些由 meta-po 回填。
- 不真实联网，不真实 Tushare 抓取，不写真实 lake。
- 不读取、打印或记录 `.env`、token、密码、私钥、cookie、session 或其他凭据。
- 不读取、列出、迁移、复制、删除旧 `data/**`。
- 不覆盖旧 `reports/experiment_17_21/factor_strategy_report.md`。

## CP6 blocker-fix 要求

CP6 blocker-fix 文件必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、缺陷修复说明、验证命令和安全边界计数。结论为 PASS 时，可将 Story 状态推进为 `ready-for-verification`；若仍存在阻断，写 `FAIL` 或 `BLOCKED`，不得扩大范围。

## 建议验证命令

- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile engine/research_dataset.py tests/test_cr011_exposure_claims.py`
- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr011_exposure_claims.py`
- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr011_adjustment_audit.py tests/test_cr011_pit_universe_lifecycle.py tests/test_cr008_factor_auxiliary_data_contract.py tests/test_cr011_execution_price_policy.py tests/test_cr011_benchmark_policy_consumption.py`
- `rg -n "float_market_cap_availability" engine/research_dataset.py tests/test_cr011_exposure_claims.py process/stories/CR011-S06-industry-market-cap-style-exposure-data.md process/stories/CR011-S06-industry-market-cap-style-exposure-data-LLD.md`

## 期望输出

| 交付物 | 路径 |
|---|---|
| 最小字段契约回修 | `engine/research_dataset.py` |
| S06 测试断言修正 | `tests/test_cr011_exposure_claims.py` |
| CP6 blocker-fix 检查 | `process/checks/CP6-CR011-S06-CP7-BLOCKER-FIX-CODING-DONE.md` |
| Story 实现状态 | `process/stories/CR011-S06-industry-market-cap-style-exposure-data.md` |
