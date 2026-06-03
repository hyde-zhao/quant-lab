---
handoff_id: "META-QA-CR019-S03-CP7-VERIFY-2026-05-30"
from_agent: "meta-po"
to_agent: "meta-qa"
workflow_id: "local_backtest-cr019"
change_id: "CR-019"
phase: "story-execution"
story_id: "CR019-S03-qmt-cside-client-cli-contract"
wave_id: "CR019-W2-CS-TRANSPORT"
status: "completed-closed"
created_at: "2026-05-30T20:12:36+08:00"
dispatch:
  required: true
  semantic: "stage-dispatch"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-qa"
  agent_path: ".agents/agents/meta-qa.md"
  tool_name: "multi_agent_v1.spawn_agent / multi_agent_v1.close_agent"
  agent_id: "019e78cd-b3e8-74c0-ba1e-6172a5bf125e"
  agent_name: "qa-shi"
  thread_id: "019e78cd-b3e8-74c0-ba1e-6172a5bf125e"
  spawned_at: "2026-05-30T20:13:30+08:00"
  resumed_at: ""
  completed_at: "2026-05-30T20:16:35+08:00"
  closed_at: "2026-05-30T20:21:24+08:00"
  evidence: "spawn_agent returned agent_id=019e78cd-b3e8-74c0-ba1e-6172a5bf125e nickname=qa-shi; close_agent previous_status returned completed CR019-S03 CP7 PASS"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-qa"
  workflow_id: "local_backtest-cr019"
  change_id: "CR-019"
  story_id: "CR019-S03-qmt-cside-client-cli-contract"
  wave_id: "CR019-W2-CS-TRANSPORT"
---

# META-QA CR-019 S03 CP7 Verification Handoff

## 任务

请以 `meta-qa` 身份验证 `CR019-S03-qmt-cside-client-cli-contract`。当前 Story 已完成 CP6，状态为 `ready-for-verification`。本轮只允许受控离线 / fixture / dry-run 合同验证，验证目标是确认 QMT C 侧 Python client、薄 CLI、REST gateway transport 合同和安全边界满足 Story、LLD、CP5 和 CP6 要求。

你不是独自在代码库中工作：当前仓库有多批未提交的 CR-015 / CR-016 / CR-017 / CR-018 / CR-019 产物。不要 revert 其他人的修改。QA 只允许写入本 Story 的 CP7 结果文件，除非发现阻断项需要在 CP7 中要求回修。

## 必读输入

| 类型 | 路径 |
|---|---|
| 项目规则 | `AGENTS.md` |
| 工作流状态 | `process/STATE.md` |
| Story 汇总 | `process/STORY-STATUS.md` |
| Story | `process/stories/CR019-S03-qmt-cside-client-cli-contract.md` |
| LLD | `process/stories/CR019-S03-qmt-cside-client-cli-contract-LLD.md` |
| CP5 auto | `process/checks/CP5-CR019-S03-qmt-cside-client-cli-contract-LLD-IMPLEMENTABILITY.md` |
| CP5 manual | `checkpoints/CP5-CR019-STAGE6-QMT-BRIDGE-BATCH-A-LLD-BATCH.md` |
| CP6 | `process/checks/CP6-CR019-S03-qmt-cside-client-cli-contract-CODING-DONE.md` |
| Dev handoff | `process/handoffs/META-DEV-CR019-S03-IMPLEMENT-2026-05-30.md` |
| Upstream CP7 | `process/checks/CP7-CR015-S02-qmt-broker-adapter-contract-VERIFICATION-DONE.md` |
| Upstream CP7 | `process/checks/CP7-CR016-S04-simulation-live-runbook-and-approval-gates-VERIFICATION-DONE.md` |
| Upstream CP7 | `process/checks/CP7-CR019-S01-stage6-admission-gate-package-VERIFICATION-DONE.md` |
| Upstream CP7 | `process/checks/CP7-CR019-S02-primary-benchmark-dashboard-VERIFICATION-DONE.md` |
| Client module | `trading/qmt_client.py` |
| CLI module | `trading/qmt_cli.py` |
| Transport module | `trading/qmt_transport.py` |
| S03 tests | `tests/test_cr019_qmt_cside_client_cli.py` |
| CR015 regression tests | `tests/test_cr015_qmt_adapter_contract.py` |
| S01 regression tests | `tests/test_cr019_stage6_admission_gate.py` |

## 写入范围

| 类型 | 路径 | 规则 |
|---|---|---|
| process | `process/checks/CP7-CR019-S03-qmt-cside-client-cli-contract-VERIFICATION-DONE.md` | 写入 CP7 验证完成检查结果。 |

禁止修改：源码、测试、reports、Story 卡片、`process/STATE.md`、`process/STORY-STATUS.md`、`process/DEVELOPMENT-PLAN.yaml`、`process/STORY-BACKLOG.md`、`pyproject.toml`、`uv.lock`、`.env`、凭据或 secret 值。

## 必须验证

1. C 侧 `xtquant` / `xttrader` / `xtdata` import 次数为 0。
2. `trading/qmt_client.py` 和 `trading/qmt_cli.py` 不导入 `fastapi`、`requests`、`httpx`、`socket`、`urllib`、`uvicorn`。
3. CLI 通过 fake client 注入验证 100% 复用 client contract，不复制 endpoint gate、auth、transport 或 business logic。
4. health / capabilities / market query / order intent / simulation-live 请求均返回 typed blocked result；`validate_intent` 只做合同校验，不执行真实 gateway。
5. later-gated endpoint 默认 blocked；account / positions / orders / trades / simulation / live / reconcile / kill_switch 未获 per-run authorization 时不得触发真实操作。
6. `trading/qmt_transport.py` 只追加 REST gateway enum / metadata / timeout / error 合同，CR015 signed file-drop `build_transport_payload` 严格白名单语义仍通过回归。
7. `dependency_change`、`service_start`、`credential_read`、`qmt_operation`、`qmt_api_call`、`xtquant_import`、`real_order`、`real_cancel`、`account_query`、`provider_fetch`、`lake_write`、`broker_lake_write`、`publish`、`current_pointer_publish`、`simulation_or_live_run`、`service_bind`、`http_client_call`、`gateway_socket_open` 全部为 0。
8. 未修改依赖文件，不读取 `.env`，不启动服务，不打开 socket，不调用真实 QMT / provider / lake / broker / publish / simulation / live。
9. CP7 结果必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、测试结果和真实操作计数。

## 必跑命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr019_qmt_cside_client_cli.py tests/test_cr015_qmt_adapter_contract.py tests/test_cr019_stage6_admission_gate.py
```

建议额外运行：

```bash
PYTHONPYCACHEPREFIX=/tmp/cr019-s03-cp7-pycompile PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile trading/qmt_client.py trading/qmt_cli.py trading/qmt_transport.py tests/test_cr019_qmt_cside_client_cli.py
git diff --check -- trading/qmt_client.py trading/qmt_cli.py trading/qmt_transport.py tests/test_cr019_qmt_cside_client_cli.py process/checks/CP6-CR019-S03-qmt-cside-client-cli-contract-CODING-DONE.md process/stories/CR019-S03-qmt-cside-client-cli-contract.md process/handoffs/META-DEV-CR019-S03-IMPLEMENT-2026-05-30.md
git diff --name-only -- pyproject.toml uv.lock .env
git status --short -- .pytest_cache tests/__pycache__ engine/__pycache__ trading/__pycache__
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -c "from trading.qmt_client import collect_qmt_client_safety_counters; print(collect_qmt_client_safety_counters())"
rg -n "^(from|import) (xtquant|xttrader|xtdata|requests|httpx|socket|urllib|uvicorn|fastapi)|\\b(open|write_text|to_csv|publish|fetch|run_simulation|place_order|cancel_order|query_account)\\(" trading/qmt_client.py trading/qmt_cli.py trading/qmt_transport.py tests/test_cr019_qmt_cside_client_cli.py
```

如果目标文件未被 Git 跟踪，需用等价 `git diff --check --no-index /dev/null <file>` 检查 whitespace，并在 CP7 中说明退出码 1 只是文件差异预期。

## 期望输出

`process/checks/CP7-CR019-S03-qmt-cside-client-cli-contract-VERIFICATION-DONE.md`

完成后请回复：

- CP7 文件路径与结论
- 实际执行的验证命令和结果
- 是否发现 BLOCKING / REQUIRED / OPEN 项
- forbidden operation counters 是否全部为 0
