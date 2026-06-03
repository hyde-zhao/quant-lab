---
handoff_id: "META-DEV-CR019-S02-IMPLEMENT-2026-05-30"
from_agent: "meta-po"
to_agent: "meta-dev"
workflow_id: "local_backtest-cr019"
change_id: "CR-019"
phase: "story-execution"
created_at: "2026-05-30T19:27:50+08:00"
status: "completed-closed"
dispatch:
  required: true
  semantic: "stage-dispatch"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".agents/agents/meta-dev.md"
  tool_name: "multi_agent_v1.spawn_agent / multi_agent_v1.close_agent"
  agent_id: "019e78a4-9720-7133-bb77-26978f45be69"
  agent_name: "dev-you"
  thread_id: "019e78a4-9720-7133-bb77-26978f45be69"
  spawned_at: "2026-05-30T19:28:38+08:00"
  resumed_at: ""
  completed_at: "2026-05-30T19:41:55+08:00"
  closed_at: "2026-05-30T19:41:55+08:00"
  evidence: "spawn_agent returned agent_id=019e78a4-9720-7133-bb77-26978f45be69 nickname=dev-you; close_agent previous_status returned completed S02 implementation with CP6 PASS"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-dev"
  workflow_id: "local_backtest-cr019"
  change_id: "CR-019"
  story_id: "CR019-S02-primary-benchmark-dashboard"
  wave_id: "CR019-W1-ADMISSION-BENCHMARK"
---

# META-DEV CR-019 S02 Implementation Handoff

## 任务

请以 `meta-dev` 身份实现 `CR019-S02-primary-benchmark-dashboard`。当前 S01 已通过 CP6 / CP7 并收敛为 `verified`，CR018-S03 benchmark readiness 已 verified，S02 Story 卡片为 `dev-ready`。本次只允许受控离线 / fixture / dry-run 合同实现。

## 必读输入

| 文件 | 用途 |
|---|---|
| `AGENTS.md` | CP6 / CP7 门控、真实子 agent 证据、禁止真实操作边界 |
| `process/STATE.md` | 当前 CR-019、S01 verified、S02 dev-ready、真实操作禁止范围 |
| `process/STORY-STATUS.md` | S02 dev-ready 与后续 Story gate |
| `checkpoints/CP5-CR019-STAGE6-QMT-BRIDGE-BATCH-A-LLD-BATCH.md` | CP5 approved 决策与 DQ-01..DQ-07 |
| `process/stories/CR019-S02-primary-benchmark-dashboard.md` | Story 卡片、文件 owner、dev_gate |
| `process/stories/CR019-S02-primary-benchmark-dashboard-LLD.md` | S02 approved LLD，必须按第 4 / 6 / 10 / 11 / 14 节实现 |
| `process/checks/CP7-CR019-S01-stage6-admission-gate-package-VERIFICATION-DONE.md` | S01 已 verified 的依赖证据 |
| `process/checks/CP7-CR018-S03-real-benchmark-index-components-weights-backfill-VERIFICATION-DONE.md` | CR018-S03 benchmark readiness verified 证据 |
| `engine/stage6_admission.py` | 只读参考 admission package / benchmark ref 字段，不得修改 |

## 允许写入范围

| 类型 | 路径 |
|---|---|
| 创建 | `engine/benchmark_policy.py` |
| 创建 | `tests/test_cr019_primary_benchmark_policy.py` |
| 创建 | `reports/stage6_admission/benchmark_dashboard_schema.md` |
| 创建 | `process/checks/CP6-CR019-S02-primary-benchmark-dashboard-CODING-DONE.md` |
| 可修改 | `process/stories/CR019-S02-primary-benchmark-dashboard.md`，仅允许将状态推进到 `ready-for-verification` 并记录 CP6 证据 |

## 禁止事项

- 不得修改 `pyproject.toml`、`uv.lock`、`.env` 或任何凭据文件。
- 不得启动服务、绑定端口、调用 QMT / MiniQMT / XtQuant、读取账户、发单、撤单或查询真实账户。
- 不得执行 provider fetch、lake write、broker lake write、publish、simulation/live run。
- 不得修改 `engine/stage6_admission.py`、`trading/stage_gate.py`、S01 测试、HLD、ADR、需求、Backlog、Development Plan、STATE 或 STORY-STATUS。
- 不得进入 CR019-S03..S10 的实现。
- 不得把 proxy benchmark 写入真实 benchmark 字段；proxy 只能作为 comparison-only / blocked reason。

## 实现要求

1. 创建 `engine/benchmark_policy.py`，至少覆盖：
   - `BenchmarkId`
   - `BenchmarkReadiness`
   - `PrimaryBenchmarkDecision`
   - `BenchmarkDashboard`
   - `required_stage6_benchmarks`
   - `build_benchmark_readiness`
   - `select_primary_benchmark`
   - `build_benchmark_dashboard`
   - `reject_proxy_as_real_benchmark`
   - safety / permission counters
2. 创建 `tests/test_cr019_primary_benchmark_policy.py`，覆盖：
   - HS300、ZZ500、ZZ1000、中证全指 4 类 benchmark 字段覆盖率 100%
   - 大盘 / 中盘 / 小盘 / 全市场 universe profile 的 deterministic primary 选择
   - readiness 缺失时 `benchmark_unavailable` / blocked，且不触发补数
   - proxy benchmark 写入真实字段时返回 `proxy_benchmark_forbidden`
   - universe / style 冲突或 primary readiness unavailable 时 `primary_benchmark_unresolved` / blocked
   - provider_fetch、lake_write、publish、credential_read、qmt_api_call 全部为 0
3. 创建 `reports/stage6_admission/benchmark_dashboard_schema.md`，只写 schema 占位，不写真实 benchmark 报告。
4. 创建 CP6 自动检查结果 `process/checks/CP6-CR019-S02-primary-benchmark-dashboard-CODING-DONE.md`，必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence 和测试结果。

## 建议验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr019_primary_benchmark_policy.py tests/test_cr019_stage6_admission_gate.py
```

可追加：

```bash
PYTHONPYCACHEPREFIX=/tmp/cr019-s02-pycompile PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile engine/benchmark_policy.py tests/test_cr019_primary_benchmark_policy.py
git diff --check -- engine/benchmark_policy.py tests/test_cr019_primary_benchmark_policy.py reports/stage6_admission/benchmark_dashboard_schema.md process/checks/CP6-CR019-S02-primary-benchmark-dashboard-CODING-DONE.md
git diff --name-only -- pyproject.toml uv.lock .env
```

## 完成后回复

请列出：

- 修改文件清单
- CP6 文件路径与结论
- 实际执行的验证命令和结果
- 是否触发任何 forbidden 操作，预期应为 0
- 是否存在 BLOCKING / OPEN 项
