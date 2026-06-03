---
handoff_id: "META-QA-CR019-S01-CP7-VERIFY-2026-05-30"
from_agent: "meta-po"
to_agent: "meta-qa"
workflow_id: "local_backtest-cr019"
change_id: "CR-019"
phase: "story-execution"
story_id: "CR019-S01-stage6-admission-gate-package"
wave_id: "CR019-W1-ADMISSION-BENCHMARK"
status: "completed-closed"
created_at: "2026-05-30T19:19:20+08:00"
dispatch:
  required: true
  semantic: "stage-dispatch"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-qa"
  agent_path: ".agents/agents/meta-qa.md"
  tool_name: "multi_agent_v1.spawn_agent / multi_agent_v1.close_agent"
  agent_id: "019e789d-05c2-7b62-bb76-deab5c911c4b"
  agent_name: "qa-cao"
  thread_id: "019e789d-05c2-7b62-bb76-deab5c911c4b"
  spawned_at: "2026-05-30T19:20:20+08:00"
  resumed_at: ""
  completed_at: "2026-05-30T19:25:30+08:00"
  closed_at: "2026-05-30T19:25:30+08:00"
  evidence: "spawn_agent returned agent_id=019e789d-05c2-7b62-bb76-deab5c911c4b nickname=qa-cao; close_agent previous_status returned completed CR019-S01 CP7 PASS"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-qa"
  workflow_id: "local_backtest-cr019"
  change_id: "CR-019"
  story_id: "CR019-S01-stage6-admission-gate-package"
  wave_id: "CR019-W1-ADMISSION-BENCHMARK"
---

# META-QA CR-019 S01 CP7 Verification Handoff

## 任务

请以 `meta-qa` 身份验证 `CR019-S01-stage6-admission-gate-package`。当前 Story 已完成 CP6，状态为 `ready-for-verification`。本轮只允许受控离线 / fixture / dry-run 合同验证，验证目标是确认阶段六 admission gate 与 package 合同满足 Story、LLD、CP5 和 CP6 要求，并且没有绕过真实操作门控。

你不是独自在代码库中工作：当前仓库有多批未提交的 CR-015 / CR-016 / CR-017 / CR-018 / CR-019 产物。不要 revert 其他人的修改。QA 只允许写入本 Story 的 CP7 结果文件，除非发现阻断项需要在 CP7 中要求回修。

## 必读输入

| 类型 | 路径 |
|---|---|
| 项目规则 | `AGENTS.md` |
| 工作流状态 | `process/STATE.md` |
| Story 汇总 | `process/STORY-STATUS.md` |
| Story | `process/stories/CR019-S01-stage6-admission-gate-package.md` |
| LLD | `process/stories/CR019-S01-stage6-admission-gate-package-LLD.md` |
| CP5 auto | `process/checks/CP5-CR019-S01-stage6-admission-gate-package-LLD-IMPLEMENTABILITY.md` |
| CP5 manual | `checkpoints/CP5-CR019-STAGE6-QMT-BRIDGE-BATCH-A-LLD-BATCH.md` |
| CP6 | `process/checks/CP6-CR019-S01-stage6-admission-gate-package-CODING-DONE.md` |
| Dev handoff | `process/handoffs/META-DEV-CR019-S01-IMPLEMENT-2026-05-30.md` |
| Admission module | `engine/stage6_admission.py` |
| Stage gate compatibility | `trading/stage_gate.py`、`tests/test_cr016_simulation_order_enable_gate.py` |
| S01 tests | `tests/test_cr019_stage6_admission_gate.py` |
| Schema docs | `reports/stage6_admission/README.md`、`reports/stage6_admission/admission_package_schema.md` |

## 写入范围

| 类型 | 路径 | 规则 |
|---|---|---|
| process | `process/checks/CP7-CR019-S01-stage6-admission-gate-package-VERIFICATION-DONE.md` | 写入 CP7 验证完成检查结果。 |

禁止修改：源码、测试、reports、Story 卡片、`process/STATE.md`、`process/STORY-STATUS.md`、`process/DEVELOPMENT-PLAN.yaml`、`process/STORY-BACKLOG.md`、`pyproject.toml`、`uv.lock`、`.env`、凭据或 secret 值。

## 必须验证

1. 10 类 P0 gate id 精确覆盖，且 coverage 为 100%。
2. 任一 P0 gate fail 时 `admission_status=blocked`。
3. 旧失败策略标记为 `simulation_ready` 的次数为 0。
4. 缺少 5 个连续真实交易日 dry-run evidence 时 fail closed。
5. missing / unknown gate id fail closed。
6. `trading/stage_gate.py` 中 admission helper 不改变 CR016 `StageGateResult` 语义。
7. `reports/stage6_admission/**` 只包含 schema / README 占位，不包含真实 run、账户、凭据或 QMT 输出。
8. `dependency_change`、`service_start / bind port`、`credential_read`、`QMT / MiniQMT / XtQuant operation`、`real_order`、`real_cancel`、`account_query`、`provider_fetch`、`lake_write`、`broker_lake_write`、`publish`、`simulation_or_live_run` 全部为 0。
9. 未修改依赖文件，不读取 `.env`，不启动服务，不调用真实 QMT / provider / lake / broker / publish / simulation / live。
10. CP7 结果必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、测试结果和真实操作计数。

## 必跑命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr019_stage6_admission_gate.py tests/test_cr016_simulation_order_enable_gate.py
```

建议额外运行：

```bash
PYTHONPYCACHEPREFIX=/tmp/cr019-s01-cp7-pycompile PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile engine/stage6_admission.py trading/stage_gate.py tests/test_cr019_stage6_admission_gate.py
git diff --check -- engine/stage6_admission.py trading/stage_gate.py tests/test_cr019_stage6_admission_gate.py reports/stage6_admission/README.md reports/stage6_admission/admission_package_schema.md process/checks/CP6-CR019-S01-stage6-admission-gate-package-CODING-DONE.md
git diff --name-only -- pyproject.toml uv.lock .env
git status --short -- .pytest_cache tests/__pycache__ engine/__pycache__ trading/__pycache__
```

## 期望输出

`process/checks/CP7-CR019-S01-stage6-admission-gate-package-VERIFICATION-DONE.md`

完成后请回复：

- CP7 文件路径与结论
- 实际执行的验证命令和结果
- 是否发现 BLOCKING / REQUIRED / OPEN 项
- forbidden operation counters 是否全部为 0
