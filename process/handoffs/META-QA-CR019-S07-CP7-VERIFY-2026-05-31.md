---
handoff_id: "META-QA-CR019-S07-CP7-VERIFY-2026-05-31"
from_agent: "meta-po"
to_agent: "meta-qa"
workflow_id: "local_backtest-cr019"
change_id: "CR-019"
phase: "story-execution"
story_id: "CR019-S07-run-gate-blocked-reason-integration"
wave_id: "CR019-W3-AUTH-ENDPOINT-GATE"
status: "completed-closed"
created_at: "2026-05-31T08:43:26+08:00"
dispatch:
  required: true
  semantic: "stage-dispatch"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-qa"
  agent_path: ".agents/agents/meta-qa.md"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e7b7d-4f34-7fe0-9678-bf8f8b8f26ae"
  agent_name: "qa-yan"
  thread_id: "019e7b7d-4f34-7fe0-9678-bf8f8b8f26ae"
  spawned_at: "2026-05-31T08:44:33+08:00"
  resumed_at: ""
  completed_at: "2026-05-31T08:46:57+08:00"
  closed_at: "2026-05-31T08:50:59+08:00"
  evidence: "spawn_agent returned agent_id=019e7b7d-4f34-7fe0-9678-bf8f8b8f26ae nickname=qa-yan; wait_agent returned completed CR019-S07 CP7 PASS; close_agent previous_status returned completed CR019-S07 CP7 PASS"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-qa"
  workflow_id: "local_backtest-cr019"
  change_id: "CR-019"
  story_id: "CR019-S07-run-gate-blocked-reason-integration"
  wave_id: "CR019-W3-AUTH-ENDPOINT-GATE"
---

# META-QA CR-019 S07 CP7 Verification Handoff

## 任务

请以 `meta-qa` 身份验证 `CR019-S07-run-gate-blocked-reason-integration`。当前 Story 已完成 CP6，状态为 `ready-for-verification`。本轮只允许受控离线 / fixture / dry-run 合同验证，验证目标是确认 gateway run gate 聚合器、blocked reason priority、S06 typed result 复用、CR015/CR016 只读 gate adapter、HMAC 不授权交易和 forbidden operation counters 满足 Story、LLD、CP5 与 CP6 要求。

你不是独自在代码库中工作：当前仓库有多批未提交的 CR-015 / CR-016 / CR-017 / CR-018 / CR-019 产物。不要 revert 其他人的修改。QA 只允许写入本 Story 的 CP7 结果文件，除非发现阻断项需要在 CP7 中要求回修。

## 必读输入

| 类型 | 路径 |
|---|---|
| 项目规则 | `AGENTS.md` |
| 工作流状态 | `process/STATE.md` |
| Story 汇总 | `process/STORY-STATUS.md` |
| Story | `process/stories/CR019-S07-run-gate-blocked-reason-integration.md` |
| LLD | `process/stories/CR019-S07-run-gate-blocked-reason-integration-LLD.md` |
| CP5 auto | `process/checks/CP5-CR019-S07-run-gate-blocked-reason-integration-LLD-IMPLEMENTABILITY.md` |
| CP5 manual | `checkpoints/CP5-CR019-STAGE6-QMT-BRIDGE-BATCH-A-LLD-BATCH.md` |
| CP6 | `process/checks/CP6-CR019-S07-run-gate-blocked-reason-integration-CODING-DONE.md` |
| Dev handoff | `process/handoffs/META-DEV-CR019-S07-IMPLEMENT-2026-05-31.md` |
| Upstream S01 CP7 | `process/checks/CP7-CR019-S01-stage6-admission-gate-package-VERIFICATION-DONE.md` |
| Upstream S05 CP7 | `process/checks/CP7-CR019-S05-pairing-hmac-auth-redaction-VERIFICATION-DONE.md` |
| Upstream S06 CP7 | `process/checks/CP7-CR019-S06-qmt-endpoint-matrix-contract-VERIFICATION-DONE.md` |
| Gate aggregator | `trading/qmt_gateway_gates.py` |
| Shared adapters | `trading/stage_gate.py`、`trading/pretrade_risk.py`、`trading/kill_switch.py` |
| S07 tests | `tests/test_cr019_qmt_gateway_run_gates.py` |
| Regression tests | `tests/test_cr019_qmt_endpoint_matrix.py`、`tests/test_cr019_qmt_pairing_hmac_auth.py`、`tests/test_cr015_pretrade_risk_gate.py`、`tests/test_cr016_monitoring_kill_switch.py`、`tests/test_cr016_runbook_approval_gates.py`、`tests/test_cr016_simulation_order_enable_gate.py` |

## 写入范围

| 类型 | 路径 | 规则 |
|---|---|---|
| process | `process/checks/CP7-CR019-S07-run-gate-blocked-reason-integration-VERIFICATION-DONE.md` | 写入 CP7 验证完成检查结果。 |

禁止修改：源码、测试、docs、Story 卡片、`process/STATE.md`、`process/STORY-STATUS.md`、`process/DEVELOPMENT-PLAN.yaml`、`process/STORY-BACKLOG.md`、HLD / ADR / CP5 人工审查稿、`pyproject.toml`、`uv.lock`、`.env`、凭据或 secret 值。

## 必须验证

1. `trading/qmt_gateway_gates.py` 提供并冻结 `QmtGateContext`、`QmtGateDecision`、`evaluate_qmt_gateway_gates()`、`to_qmt_gateway_result()`、`collect_qmt_gateway_gate_safety_counters()`。
2. blocked reason priority 固定为 auth -> endpoint/schema -> admission/stage -> authorization -> risk -> kill_switch -> raw_policy -> operation_not_authorized。
3. 任一 gate missing / fail / unknown 必须 fail closed，`adapter_call`、`qmt_api_call`、`real_order`、`real_cancel`、`cancel_order`、`account_query`、`broker_lake_write`、`simulation_or_live_run` 均为 0。
4. HMAC pass 只识别调用方和 scope，不得直接授权 account / order / cancel / simulation / live。
5. S07 必须消费 S06 `QmtEndpointSpec` / `QmtGatewayResult` / `QmtBlockedReason`，不得定义第二套不兼容 error schema。
6. `stage_gate.py`、`pretrade_risk.py`、`kill_switch.py` 只新增 read-only adapter；不得删除、重命名或改变既有函数、枚举和测试期望。
7. 目标文件不导入 `fastapi`、`uvicorn`、`requests`、`httpx`、`socket`、`urllib`、`subprocess`、`xtquant`、`xttrader`、`xtdata`。
8. 未修改依赖文件，不读取 `.env`，不启动 gateway，不绑定端口，不打开 socket，不调用真实 QMT / MiniQMT / XtQuant / provider / lake / broker / publish / simulation / live。
9. CP7 结果必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、测试结果、Forbidden Operation Counters、OPEN / BLOCKING 结论。

## 必跑命令

```bash
PYTHONPYCACHEPREFIX=/tmp/cr019-s07-cp7-pycompile PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile trading/qmt_gateway_gates.py trading/stage_gate.py trading/pretrade_risk.py trading/kill_switch.py tests/test_cr019_qmt_gateway_run_gates.py
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr019_qmt_gateway_run_gates.py tests/test_cr019_qmt_endpoint_matrix.py tests/test_cr019_qmt_pairing_hmac_auth.py tests/test_cr015_pretrade_risk_gate.py tests/test_cr016_monitoring_kill_switch.py tests/test_cr016_runbook_approval_gates.py tests/test_cr016_simulation_order_enable_gate.py
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -c "from trading.qmt_gateway_gates import collect_qmt_gateway_gate_safety_counters; print(collect_qmt_gateway_gate_safety_counters())"
git diff --name-only -- pyproject.toml uv.lock .env
git status --short -- .pytest_cache tests/__pycache__ engine/__pycache__ trading/__pycache__
```

建议额外运行：

```bash
rg -n "^(from|import) (fastapi|uvicorn|requests|httpx|socket|urllib|subprocess|xtquant|xttrader|xtdata)\b" trading/qmt_gateway_gates.py trading/stage_gate.py trading/pretrade_risk.py trading/kill_switch.py tests/test_cr019_qmt_gateway_run_gates.py
rg -n "\b(open\(|read_text\(|write_text\(|dotenv|os\.environ|getenv|load_dotenv|keyring|credential|uvicorn\.|FastAPI\(|requests\.|httpx\.|socket\.|subprocess\.|os\.system|Popen\(|bind\(|listen\(|connect\(|place_order\(|cancel_order\(|query_account\(|publish\(|fetch\(|run_simulation\()" trading/qmt_gateway_gates.py trading/stage_gate.py trading/pretrade_risk.py trading/kill_switch.py tests/test_cr019_qmt_gateway_run_gates.py
git diff --check -- trading/qmt_gateway_gates.py trading/stage_gate.py trading/pretrade_risk.py trading/kill_switch.py tests/test_cr019_qmt_gateway_run_gates.py process/checks/CP6-CR019-S07-run-gate-blocked-reason-integration-CODING-DONE.md process/stories/CR019-S07-run-gate-blocked-reason-integration.md process/handoffs/META-DEV-CR019-S07-IMPLEMENT-2026-05-31.md
rg -n -i "ignore (all )?(previous|prior) instructions|system prompt|developer message|prompt injection|jailbreak|exfiltrate|leak" trading/qmt_gateway_gates.py trading/stage_gate.py trading/pretrade_risk.py trading/kill_switch.py tests/test_cr019_qmt_gateway_run_gates.py
```

如果目标文件未被 Git 跟踪，需用等价 `git diff --check --no-index /dev/null <file>` 检查 whitespace，并在 CP7 中说明退出码 1 只是文件差异预期。

## 期望输出

`process/checks/CP7-CR019-S07-run-gate-blocked-reason-integration-VERIFICATION-DONE.md`

完成后请回复：

- CP7 文件路径与结论
- 实际执行的验证命令和结果
- 是否发现 BLOCKING / REQUIRED / OPEN 项
- forbidden operation counters 是否全部为 0
