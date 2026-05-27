---
handoff_id: "META-DEV-CR005-S06-IMPLEMENT-2026-05-17"
from_agent: "meta-po"
to_agent: "meta-dev"
status: "completed"
created_at: "2026-05-18T00:00:56+08:00"
dispatched_at: "2026-05-18T00:00:56+08:00"
completed_at: "2026-05-18T00:12:32+08:00"
workflow_id: "local_backtest"
change_id: "CR-005"
story_id: "CR005-S06"
wave_id: "CR5-W5"
phase: "story-execution"
tool_name: "spawn_agent"
agent_id: "019e36b0-6aa1-7b92-a9b9-4ef69d986471"
thread_id: "019e36b0-6aa1-7b92-a9b9-4ef69d986471"
agent_name: "dev-qin the 2nd"
dispatch_mode: "subagent"
cp5_manual_review: "checkpoints/CP5-CR005-BATCH-D-S06-LLD-BATCH.md"
cp5_auto_result: "process/checks/CP5-CR005-S06-backtrader-optional-backend-LLD-IMPLEMENTABILITY.md"
expected_cp6: "process/checks/CP6-CR005-S06-backtrader-optional-backend-CODING-DONE.md"
---

# META-DEV Handoff: CR005-S06 Implementation

## Mission

实现 `CR005-S06` Backtrader optional backend。Backtrader 只能作为显式启用的可选后端，不得替代默认轻量回测路径。

## Dispatch Evidence

| 字段 | 值 |
|---|---|
| dispatch_required | `true` |
| dispatch_mode | `subagent` |
| platform | `codex` |
| tool_name | `spawn_agent` |
| agent_role | `meta-dev` |
| agent_id / thread_id | `019e36b0-6aa1-7b92-a9b9-4ef69d986471` |
| agent_name | `dev-qin the 2nd` |
| dispatched_at | `2026-05-18T00:00:56+08:00` |
| completed_at | `2026-05-18T00:12:32+08:00` |

## Confirmed Gate

| Gate | Result | Evidence |
|---|---|---|
| CP5 auto | PASS | `process/checks/CP5-CR005-S06-backtrader-optional-backend-LLD-IMPLEMENTABILITY.md` |
| CP5 manual | approved | `checkpoints/CP5-CR005-BATCH-D-S06-LLD-BATCH.md` |
| LLD | confirmed | `process/stories/CR005-S06-backtrader-optional-backend-LLD.md` |

## User-Confirmed Dependency Decision

- Dependency group: `backtrader`
- Fixed version: `backtrader==1.9.78.123`
- Dependency command: use `uv add --group backtrader backtrader==1.9.78.123`; do not hand-edit `uv.lock`.
- Implementation must lazy import Backtrader.
- Default `lightweight` path must not require, import, or install Backtrader.
- CP6 must verify Python 3.11 import + tiny Cerebro smoke test.
- If real Backtrader smoke fails, degrade to `backend_unavailable` + fake smoke; do not switch to a fork in this Story.

## Allowed Files

| Scope | Files |
|---|---|
| Primary implementation | `engine/backtrader_adapter.py` |
| Tests | `tests/test_backtrader_optional_backend.py` |
| Minimal selector / wrapper | `engine/backtest.py` |
| Docs | `README.md`, `docs/USER-MANUAL.md` |
| Dependency | `pyproject.toml`, `uv.lock` |
| Process | `process/checks/CP6-CR005-S06-backtrader-optional-backend-CODING-DONE.md`, `process/stories/CR005-S06-backtrader-optional-backend.md`, this handoff |

## Forbidden Scope

- Do not modify or import `market_data/connectors/**`, `market_data/runtime.py`, or `market_data/storage.py`.
- Do not read or write `TUSHARE_TOKEN`.
- Do not make network calls or add network clients.
- Do not fetch Tushare data.
- Do not write real `data/**`, `reports/**`, or `delivery/**`.
- Do not submit `__pycache__/**`, `*.pyc`, `.ipynb_checkpoints/**`, credentials, tokens, or real market data.

## Required Implementation Behavior

1. Create `engine/backtrader_adapter.py` with typed request/result objects, dependency probe, input validation, metadata builder, and explicit `run_backtrader_backend(...)`.
2. Use lazy import only inside dependency probe/runtime path; importing `engine.backtrader_adapter` must work without Backtrader installed.
3. Keep `engine/backtest.py` default behavior unchanged. Prefer a minimal wrapper or selector; if extending a public function, default must remain `lightweight`.
4. Return structured statuses: `completed`, `backend_unavailable`, `input_rejected`, `benchmark_unavailable`, `failed`.
5. Reject unclean inputs before running Backtrader: quality fail, PIT fail, `available_at > decision_time`, missing/conflicting adjusted price, mixed `adjustment_policy`.
6. Benchmark unavailable / required_missing must only produce typed result and metadata; it must not fetch, backfill, write lake, or fill `hs300_index` from `proxy_baseline`.
7. Completed Backtrader path is limited to rebalance, execution, cost, position, equity, and risk analysis.

## Required CP6 Verification

Run and record exact commands/results in CP6:

```bash
UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_backtrader_optional_backend.py
UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q
UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 --group backtrader python -c "import backtrader as bt; cerebro = bt.Cerebro(); print(type(cerebro).__name__)"
```

If the real Backtrader smoke command fails, record the failure in CP6 and demonstrate the fallback path with a fake smoke test that returns `backend_unavailable` without breaking default lightweight tests.

## Expected CP6 Output

Create `process/checks/CP6-CR005-S06-backtrader-optional-backend-CODING-DONE.md` with:

- Agent Dispatch Evidence: `spawn_agent` id/thread/name, start/end time.
- Changed files list.
- Verification commands and results.
- Import/lazy-import evidence.
- No-network/no-token/no-lake-write/no-forbidden-import evidence.
- Explicit note whether real Backtrader tiny Cerebro smoke passed or degraded to `backend_unavailable` + fake smoke.

## Completion Summary

| 项目 | 结果 |
|---|---|
| Story status | `ready-for-verification` |
| CP6 | `process/checks/CP6-CR005-S06-backtrader-optional-backend-CODING-DONE.md`，结论 `PASS` |
| Real Backtrader smoke | PASS，输出 `Cerebro` |
| Fallback fake smoke | PASS，`tests/test_backtrader_optional_backend.py::test_fake_backtrader_smoke_completed_path` 覆盖 |

## Changed Files

| 文件 | 说明 |
|---|---|
| `engine/backtrader_adapter.py` | 新增 typed request/result、dependency probe、input validation、benchmark metadata builder、`run_backtrader_backend(...)`。 |
| `engine/backtest.py` | 新增 `select_backtest_backend(...)` 与 `run_backtest_with_backend(...)`；默认 `run_backtest(...)` 语义保持不变。 |
| `tests/test_backtrader_optional_backend.py` | 新增 S06 专项测试，覆盖 lazy import、dependency missing、forbidden import/no token/no network/no write、quality/PIT/复权阻断、benchmark missing、fake smoke。 |
| `README.md` | 补充 Backtrader optional backend 安装、显式启用和边界说明。 |
| `docs/USER-MANUAL.md` | 补充 Backtrader optional backend 操作、状态处理和故障边界。 |
| `pyproject.toml`、`uv.lock` | 通过 `uv add --group backtrader backtrader==1.9.78.123` 增加 dependency group 和锁定版本。 |
| `process/stories/CR005-S06-backtrader-optional-backend.md` | 更新验收项与状态为 `ready-for-verification`。 |
| `process/checks/CP6-CR005-S06-backtrader-optional-backend-CODING-DONE.md` | 新增 CP6 编码完成检查结果。 |

## Verification Results

| 命令 | 结果 |
|---|---|
| `UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_backtrader_optional_backend.py` | `16 passed in 0.38s` |
| `UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q` | `106 passed in 3.30s` |
| `UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 --group backtrader python -c "import backtrader as bt; cerebro = bt.Cerebro(); print(type(cerebro).__name__)"` | `Cerebro` |

## Boundaries

- 未修改 `market_data/connectors/**`、`market_data/runtime.py`、`market_data/storage.py`。
- 未执行真实 Tushare fetch，未读取 token，未写真实 `data/**`、`reports/**` 或 `delivery/**`。
- 静态扫描 `engine/backtrader_adapter.py` 与 `engine/backtest.py`，未命中 forbidden import、token/env 读取或网络库。
- Backtrader 真实 smoke 已通过，因此未触发真实 smoke 失败 fallback；fake smoke 仍由专项测试覆盖。
