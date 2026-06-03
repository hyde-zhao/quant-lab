---
handoff_id: "META-QA-CR019-S08-CP7-VERIFY-2026-05-31"
from_agent: "meta-po"
to_agent: "meta-qa"
workflow_id: "local_backtest-cr019"
change_id: "CR-019"
phase: "story-execution"
story_id: "CR019-S08-fallback-incident-signed-file-boundary"
wave_id: "CR019-W4-FALLBACK-DEFERRED"
status: "completed-closed"
created_at: "2026-05-31T09:11:59+08:00"
dispatch:
  required: true
  semantic: "stage-dispatch"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-qa"
  agent_path: ".agents/agents/meta-qa.md"
  tool_name: "multi_agent_v1.spawn_agent / multi_agent_v1.wait_agent / multi_agent_v1.close_agent"
  agent_id: "019e7b97-e047-7673-ab10-e375d3ce62e0"
  agent_name: "qa-hua"
  thread_id: "019e7b97-e047-7673-ab10-e375d3ce62e0"
  spawned_at: "2026-05-31T09:13:33+08:00"
  resumed_at: ""
  completed_at: "2026-05-31T09:16:42+08:00"
  closed_at: "2026-05-31T09:23:13+08:00"
  evidence: "spawn_agent returned agent_id=019e7b97-e047-7673-ab10-e375d3ce62e0 nickname=qa-hua; wait_agent returned completed CR019-S08 CP7 PASS; close_agent previous_status returned completed CR019-S08 CP7 PASS"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-qa"
  workflow_id: "local_backtest-cr019"
  change_id: "CR-019"
  story_id: "CR019-S08-fallback-incident-signed-file-boundary"
  wave_id: "CR019-W4-FALLBACK-DEFERRED"
---

# META-QA CR-019 S08 CP7 Verification Handoff

## 任务

请以 `meta-qa` 身份验证 `CR019-S08-fallback-incident-signed-file-boundary`。当前 Story 已完成 CP6，状态为 `ready-for-verification`。本轮只允许受控离线 / fixture / dry-run 合同验证，验证目标是确认 fallback / incident / signed file fail-closed 边界满足 Story、LLD、CP5 与 CP6 要求，并确认实现没有引入真实 QMT / broker / provider / lake / publish / simulation/live 操作。

你不是独自在代码库中工作：当前仓库有多批未提交的 CR-015 / CR-016 / CR-017 / CR-018 / CR-019 产物。不要 revert 其他人的修改。QA 只允许写入本 Story 的 CP7 结果文件，除非发现阻断项需要在 CP7 中要求回修。

## 必读输入

| 类型 | 路径 |
|---|---|
| 项目规则 | `AGENTS.md` |
| 工作流状态 | `process/STATE.md` |
| Story 汇总 | `process/STORY-STATUS.md` |
| Story | `process/stories/CR019-S08-fallback-incident-signed-file-boundary.md` |
| LLD | `process/stories/CR019-S08-fallback-incident-signed-file-boundary-LLD.md` |
| CP5 auto | `process/checks/CP5-CR019-S08-fallback-incident-signed-file-boundary-LLD-IMPLEMENTABILITY.md` |
| CP5 manual | `checkpoints/CP5-CR019-STAGE6-QMT-BRIDGE-BATCH-A-LLD-BATCH.md` |
| CP6 | `process/checks/CP6-CR019-S08-fallback-incident-signed-file-boundary-CODING-DONE.md` |
| Dev handoff | `process/handoffs/META-DEV-CR019-S08-IMPLEMENT-2026-05-31.md` |
| Upstream S04 CP7 | `process/checks/CP7-CR019-S04-windows-gateway-lifecycle-deployment-VERIFICATION-DONE.md` |
| Upstream S05 CP7 | `process/checks/CP7-CR019-S05-pairing-hmac-auth-redaction-VERIFICATION-DONE.md` |
| Upstream S06 CP7 | `process/checks/CP7-CR019-S06-qmt-endpoint-matrix-contract-VERIFICATION-DONE.md` |
| Upstream S07 CP7 | `process/checks/CP7-CR019-S07-run-gate-blocked-reason-integration-VERIFICATION-DONE.md` |
| Fallback module | `trading/qmt_gateway_fallback.py` |
| S08 tests | `tests/test_cr019_qmt_gateway_fallback.py` |
| Incident playbook | `docs/QMT-INCIDENT-PLAYBOOK.md` |
| Regression tests | `tests/test_cr019_qmt_gateway_run_gates.py`、`tests/test_cr019_qmt_gateway_lifecycle.py`、`tests/test_cr019_qmt_pairing_hmac_auth.py`、`tests/test_cr019_qmt_endpoint_matrix.py` |

## 写入范围

| 类型 | 路径 | 规则 |
|---|---|---|
| process | `process/checks/CP7-CR019-S08-fallback-incident-signed-file-boundary-VERIFICATION-DONE.md` | 写入 CP7 验证完成检查结果。 |

禁止修改：源码、测试、docs、Story 卡片、`process/STATE.md`、`process/STORY-STATUS.md`、`process/DEVELOPMENT-PLAN.yaml`、`process/STORY-BACKLOG.md`、HLD / ADR / CP5 人工审查稿、`pyproject.toml`、`uv.lock`、`.env`、凭据或 secret 值。

## 必须验证

1. `FallbackTrigger` 覆盖 `gateway_unreachable`、`auth_failed`、`heartbeat_failed`、`deployment_not_ready`、`run_gate_blocked`。
2. `FallbackDecision` 固定 `status=blocked`，包含 `blocked_reason`、`incident_candidate`、`manual_dry_run_allowed`、`safety_counters`、`next_action`。
3. signed dry-run payload 固定 `mode=manual_dry_run_only`、`auto_execute=false`、`real_qmt_allowed=false`、`manual_handling_required=true`。
4. payload validation 对过期、签名状态未通过、敏感字段、自动执行字段和非零 forbidden counter 均 fail closed。
5. incident candidate 只返回脱敏候选记录，不持久化真实 incident，不写 broker lake。
6. S08 复用 S06 typed blocked result，不定义第二套不兼容 endpoint result schema。
7. `docs/QMT-INCIDENT-PLAYBOOK.md` 的 S08 增量必须明确 signed file drop 只用于人工 dry-run / 演练，不授权真实交易、撤单、账户查询、broker lake 写入、publish、simulation/live。
8. 目标文件不导入 `fastapi`、`uvicorn`、`requests`、`httpx`、`socket`、`urllib`、`subprocess`、`xtquant`、`xttrader`、`xtdata`。
9. 未修改依赖文件，不读取 `.env`，不启动 gateway，不绑定端口，不打开 socket，不调用真实 QMT / MiniQMT / XtQuant / provider / lake / broker / publish / simulation / live。
10. CP7 结果必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、测试结果、Forbidden Operation Counters、OPEN / BLOCKING 结论。

## 必跑命令

```bash
PYTHONPYCACHEPREFIX=/tmp/cr019-s08-cp7-pycompile PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile trading/qmt_gateway_fallback.py tests/test_cr019_qmt_gateway_fallback.py
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr019_qmt_gateway_fallback.py tests/test_cr019_qmt_gateway_run_gates.py tests/test_cr019_qmt_gateway_lifecycle.py tests/test_cr019_qmt_pairing_hmac_auth.py tests/test_cr019_qmt_endpoint_matrix.py
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -c "from trading.qmt_gateway_fallback import collect_qmt_gateway_fallback_safety_counters; print(collect_qmt_gateway_fallback_safety_counters())"
git diff --name-only -- pyproject.toml uv.lock .env
git status --short -- .pytest_cache tests/__pycache__ engine/__pycache__ trading/__pycache__
```

建议额外运行：

```bash
rg -n "^(from|import) (fastapi|uvicorn|requests|httpx|socket|urllib|subprocess|xtquant|xttrader|xtdata)\b" trading/qmt_gateway_fallback.py tests/test_cr019_qmt_gateway_fallback.py
rg -n "\b(open\(|read_text\(|write_text\(|dotenv|os\.environ|getenv|load_dotenv|keyring|credential|uvicorn\.|FastAPI\(|requests\.|httpx\.|socket\.|subprocess\.|os\.system|Popen\(|bind\(|listen\(|connect\(|place_order\(|cancel_order\(|query_account\(|publish\(|fetch\(|run_simulation\()" trading/qmt_gateway_fallback.py tests/test_cr019_qmt_gateway_fallback.py docs/QMT-INCIDENT-PLAYBOOK.md
rg -n "secret|token|password|private key|account_id|account number|session|\\.env|真实账户|实盘账户|私有路径" docs/QMT-INCIDENT-PLAYBOOK.md trading/qmt_gateway_fallback.py tests/test_cr019_qmt_gateway_fallback.py
rg -n "rm -rf|sudo|curl|wget|nc |netcat|ssh|scp|chmod|chown|mkfs|dd if=|iptables|systemctl|kill -9|os\.remove|shutil\.rmtree|subprocess|Popen|eval\(|exec\(" trading/qmt_gateway_fallback.py tests/test_cr019_qmt_gateway_fallback.py docs/QMT-INCIDENT-PLAYBOOK.md
rg -n -i "ignore (all )?(previous|prior) instructions|system prompt|developer message|prompt injection|jailbreak|exfiltrate|leak" trading/qmt_gateway_fallback.py tests/test_cr019_qmt_gateway_fallback.py docs/QMT-INCIDENT-PLAYBOOK.md
git diff --check -- trading/qmt_gateway_fallback.py tests/test_cr019_qmt_gateway_fallback.py docs/QMT-INCIDENT-PLAYBOOK.md process/checks/CP6-CR019-S08-fallback-incident-signed-file-boundary-CODING-DONE.md process/stories/CR019-S08-fallback-incident-signed-file-boundary.md process/handoffs/META-DEV-CR019-S08-IMPLEMENT-2026-05-31.md
```

如果目标文件未被 Git 跟踪，需用等价 `git diff --check --no-index /dev/null <file>` 检查 whitespace，并在 CP7 中说明退出码 1 只是文件差异预期。

## 期望输出

`process/checks/CP7-CR019-S08-fallback-incident-signed-file-boundary-VERIFICATION-DONE.md`

完成后请回复：

- CP7 文件路径与结论
- 实际执行的验证命令和结果
- 是否发现 BLOCKING / REQUIRED / OPEN 项
- forbidden operation counters 是否全部为 0
