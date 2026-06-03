---
handoff_id: "META-QA-CR019-S02-CP7-VERIFY-2026-05-30"
from_agent: "meta-po"
to_agent: "meta-qa"
workflow_id: "local_backtest-cr019"
change_id: "CR-019"
phase: "story-execution"
story_id: "CR019-S02-primary-benchmark-dashboard"
wave_id: "CR019-W1-ADMISSION-BENCHMARK"
status: "completed-closed"
created_at: "2026-05-30T19:45:13+08:00"
dispatch:
  required: true
  semantic: "stage-dispatch"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-qa"
  agent_path: ".agents/agents/meta-qa.md"
  tool_name: "multi_agent_v1.spawn_agent / multi_agent_v1.close_agent"
  agent_id: "019e78b4-95cb-7e53-b841-719d0f0f530b"
  agent_name: "qa-zhang"
  thread_id: "019e78b4-95cb-7e53-b841-719d0f0f530b"
  spawned_at: "2026-05-30T19:46:03+08:00"
  resumed_at: ""
  completed_at: "2026-05-30T19:51:32+08:00"
  closed_at: "2026-05-30T19:51:32+08:00"
  evidence: "spawn_agent returned agent_id=019e78b4-95cb-7e53-b841-719d0f0f530b nickname=qa-zhang; close_agent previous_status returned completed CR019-S02 CP7 PASS"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-qa"
  workflow_id: "local_backtest-cr019"
  change_id: "CR-019"
  story_id: "CR019-S02-primary-benchmark-dashboard"
  wave_id: "CR019-W1-ADMISSION-BENCHMARK"
---

# META-QA CR-019 S02 CP7 Verification Handoff

## 任务

请以 `meta-qa` 身份验证 `CR019-S02-primary-benchmark-dashboard`。当前 Story 已完成 CP6，状态为 `ready-for-verification`。本轮只允许受控离线 / fixture / dry-run 合同验证，验证目标是确认阶段六多基准看板、primary benchmark policy、proxy guard 和安全边界满足 Story、LLD、CP5 和 CP6 要求。

你不是独自在代码库中工作：当前仓库有多批未提交的 CR-015 / CR-016 / CR-017 / CR-018 / CR-019 产物。不要 revert 其他人的修改。QA 只允许写入本 Story 的 CP7 结果文件，除非发现阻断项需要在 CP7 中要求回修。

## 必读输入

| 类型 | 路径 |
|---|---|
| 项目规则 | `AGENTS.md` |
| 工作流状态 | `process/STATE.md` |
| Story 汇总 | `process/STORY-STATUS.md` |
| Story | `process/stories/CR019-S02-primary-benchmark-dashboard.md` |
| LLD | `process/stories/CR019-S02-primary-benchmark-dashboard-LLD.md` |
| CP5 auto | `process/checks/CP5-CR019-S02-primary-benchmark-dashboard-LLD-IMPLEMENTABILITY.md` |
| CP5 manual | `checkpoints/CP5-CR019-STAGE6-QMT-BRIDGE-BATCH-A-LLD-BATCH.md` |
| CP6 | `process/checks/CP6-CR019-S02-primary-benchmark-dashboard-CODING-DONE.md` |
| Dev handoff | `process/handoffs/META-DEV-CR019-S02-IMPLEMENT-2026-05-30.md` |
| S01 CP7 | `process/checks/CP7-CR019-S01-stage6-admission-gate-package-VERIFICATION-DONE.md` |
| CR018-S03 CP7 | `process/checks/CP7-CR018-S03-real-benchmark-index-components-weights-backfill-VERIFICATION-DONE.md` |
| Benchmark module | `engine/benchmark_policy.py` |
| S02 tests | `tests/test_cr019_primary_benchmark_policy.py` |
| S01 regression tests | `tests/test_cr019_stage6_admission_gate.py` |
| Schema docs | `reports/stage6_admission/benchmark_dashboard_schema.md` |

## 写入范围

| 类型 | 路径 | 规则 |
|---|---|---|
| process | `process/checks/CP7-CR019-S02-primary-benchmark-dashboard-VERIFICATION-DONE.md` | 写入 CP7 验证完成检查结果。 |

禁止修改：源码、测试、reports、Story 卡片、`process/STATE.md`、`process/STORY-STATUS.md`、`process/DEVELOPMENT-PLAN.yaml`、`process/STORY-BACKLOG.md`、`pyproject.toml`、`uv.lock`、`.env`、凭据或 secret 值。

## 必须验证

1. HS300、ZZ500、ZZ1000、中证全指 4 类 benchmark 字段覆盖率为 100%。
2. 大盘 / 中盘 / 小盘 / 全市场 universe profile 的 primary benchmark 选择 deterministic。
3. readiness 缺失时输出 `benchmark_unavailable` / blocked，不触发 provider fetch、lake write 或 publish。
4. proxy benchmark 写入真实 benchmark 字段时返回 `proxy_benchmark_forbidden`，proxy 写真实字段次数为 0。
5. universe / style 冲突或 primary readiness unavailable 时输出 `primary_benchmark_unresolved` / blocked。
6. `reports/stage6_admission/benchmark_dashboard_schema.md` 存在且只包含 schema 占位，不包含真实 benchmark 报告、账户、凭据或 QMT 输出；该文件被 `.gitignore:33:reports/` 忽略，需使用 `--no-index` 或等价方式单独检查。
7. `provider_fetch`、`lake_write`、`broker_lake_write`、`publish`、`current_pointer_publish`、`credential_read`、`qmt_api_call`、`xtquant_import`、`service_start`、`dependency_change`、`real_order_call`、`real_cancel_call`、`account_query_call`、`simulation_or_live_run` 全部为 0。
8. 未修改依赖文件，不读取 `.env`，不启动服务，不调用真实 QMT / provider / lake / broker / publish / simulation / live。
9. CP7 结果必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、测试结果和真实操作计数。

## 必跑命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr019_primary_benchmark_policy.py tests/test_cr019_stage6_admission_gate.py
```

建议额外运行：

```bash
PYTHONPYCACHEPREFIX=/tmp/cr019-s02-cp7-pycompile PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile engine/benchmark_policy.py tests/test_cr019_primary_benchmark_policy.py
git diff --check -- engine/benchmark_policy.py tests/test_cr019_primary_benchmark_policy.py process/checks/CP6-CR019-S02-primary-benchmark-dashboard-CODING-DONE.md process/stories/CR019-S02-primary-benchmark-dashboard.md process/handoffs/META-DEV-CR019-S02-IMPLEMENT-2026-05-30.md
git diff --check --no-index /dev/null reports/stage6_admission/benchmark_dashboard_schema.md
git diff --name-only -- pyproject.toml uv.lock .env
git status --short -- .pytest_cache tests/__pycache__ engine/__pycache__ trading/__pycache__
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -c "from engine.benchmark_policy import collect_benchmark_policy_safety_counters; print(collect_benchmark_policy_safety_counters())"
git check-ignore -v reports/stage6_admission/benchmark_dashboard_schema.md
```

## 期望输出

`process/checks/CP7-CR019-S02-primary-benchmark-dashboard-VERIFICATION-DONE.md`

完成后请回复：

- CP7 文件路径与结论
- 实际执行的验证命令和结果
- 是否发现 BLOCKING / REQUIRED / OPEN 项
- forbidden operation counters 是否全部为 0
