---
handoff_id: "META-DEV-CR019-S08-IMPLEMENT-2026-05-31"
from_agent: "meta-po"
to_agent: "meta-dev"
workflow_id: "local_backtest-cr019"
change_id: "CR-019"
phase: "story-execution"
story_id: "CR019-S08-fallback-incident-signed-file-boundary"
wave_id: "CR019-W4-FALLBACK-DEFERRED"
status: "completed-closed"
created_at: "2026-05-31T08:53:24+08:00"
dispatch:
  required: true
  semantic: "stage-dispatch"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".agents/agents/meta-dev.md"
  tool_name: "multi_agent_v1.spawn_agent / multi_agent_v1.wait_agent / multi_agent_v1.close_agent"
  agent_id: "019e7b88-93ba-7223-b0f1-859c712eaf25"
  agent_name: "dev-yang"
  thread_id: "019e7b88-93ba-7223-b0f1-859c712eaf25"
  spawned_at: "2026-05-31T08:56:52+08:00"
  resumed_at: ""
  completed_at: "2026-05-31T09:04:53+08:00"
  closed_at: "2026-05-31T09:10:25+08:00"
  evidence: "spawn_agent returned agent_id=019e7b88-93ba-7223-b0f1-859c712eaf25 nickname=dev-yang; wait_agent returned completed CR019-S08 CP6 PASS; close_agent previous_status returned completed CR019-S08 CP6 PASS"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-dev"
  workflow_id: "local_backtest-cr019"
  change_id: "CR-019"
  story_id: "CR019-S08-fallback-incident-signed-file-boundary"
  wave_id: "CR019-W4-FALLBACK-DEFERRED"
---

# META-DEV CR-019 S08 Implementation Handoff

## 任务

请以 `meta-dev` 身份实现 `CR019-S08-fallback-incident-signed-file-boundary`。当前 S04/S05/S06/S07 均已 CP7 PASS 且 S07 已收敛为 `verified`，S08 的 LLD 与 CP5 已批准。本轮只允许受控离线 / fixture / dry-run 合同实现，目标是冻结 fallback / incident / signed file fail-closed 边界：gateway 不可达、auth fail、heartbeat fail、部署不满足、run gate fail 时只能返回 typed blocked result 或 manual-only dry-run payload，不得自动触发真实 QMT / broker 操作。

你不是独自在代码库中工作：当前仓库有多批未提交的 CR-015 / CR-016 / CR-017 / CR-018 / CR-019 产物。不要 revert 其他人的修改。若发现目标文件已有变更，先读懂并在其上增量修改。

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
| Upstream S04 CP7 | `process/checks/CP7-CR019-S04-windows-gateway-lifecycle-deployment-VERIFICATION-DONE.md` |
| Upstream S05 CP7 | `process/checks/CP7-CR019-S05-pairing-hmac-auth-redaction-VERIFICATION-DONE.md` |
| Upstream S06 CP7 | `process/checks/CP7-CR019-S06-qmt-endpoint-matrix-contract-VERIFICATION-DONE.md` |
| Upstream S07 CP7 | `process/checks/CP7-CR019-S07-run-gate-blocked-reason-integration-VERIFICATION-DONE.md` |
| Endpoint matrix | `trading/qmt_gateway_endpoints.py` |
| Run gate | `trading/qmt_gateway_gates.py` |
| Incident playbook | `docs/QMT-INCIDENT-PLAYBOOK.md` |

## 写入范围

| 类型 | 路径 | 规则 |
|---|---|---|
| code | `trading/qmt_gateway_fallback.py` | 创建 fail-closed fallback / signed dry-run payload / incident candidate 合同。 |
| test | `tests/test_cr019_qmt_gateway_fallback.py` | 创建 fixture-only 合同测试。 |
| docs | `docs/QMT-INCIDENT-PLAYBOOK.md` | 仅增量追加 S08 fallback / signed file manual-only 边界，不改写既有 CR015/CR016 语义。 |
| process | `process/checks/CP6-CR019-S08-fallback-incident-signed-file-boundary-CODING-DONE.md` | 写入 CP6 编码完成检查结果。 |
| process | `process/stories/CR019-S08-fallback-incident-signed-file-boundary.md` | 仅更新本 Story 的实现状态、CP6 结果和 agent 证据字段。 |

禁止修改：`process/STATE.md`、`process/STORY-STATUS.md`、`process/DEVELOPMENT-PLAN.yaml`、`process/STORY-BACKLOG.md`、HLD / ADR / CP5 人工审查稿、其他 Story 卡片、`pyproject.toml`、`uv.lock`、`.env`、凭据或 secret 值。

## 必须实现

1. `trading/qmt_gateway_fallback.py` 定义 `FallbackTrigger`，覆盖 `gateway_unreachable`、`auth_failed`、`heartbeat_failed`、`deployment_not_ready`、`run_gate_blocked`。
2. 定义 `FallbackDecision`，固定 `status="blocked"`，输出 `blocked_reason`、`incident_candidate`、`manual_dry_run_allowed`、`safety_counters`、`next_action`。
3. 定义 signed dry-run payload builder，字段必须包含并固定 `auto_execute=false`、`real_qmt_allowed=false`、`manual_handling_required=true`、`mode=manual_dry_run_only`。
4. 定义 payload validation：过期、签名状态、敏感字段、自动执行字段任一不满足时 fail closed，返回 typed blocked / invalid result，不进入真实 adapter。
5. `format_incident_candidate()` 只返回脱敏候选记录，不持久化真实 incident，不写 broker lake。
6. 增量更新 `docs/QMT-INCIDENT-PLAYBOOK.md`，明确 signed file drop 是人工 dry-run / 演练入口，不授权真实交易、撤单、账户查询、broker lake 写入、publish、simulation/live。
7. 提供 `collect_qmt_gateway_fallback_safety_counters()`，所有真实操作 counter 初始和测试后均为 0。
8. 不导入 `fastapi`、`uvicorn`、`requests`、`httpx`、`socket`、`urllib`、`subprocess`、`xtquant`、`xttrader`、`xtdata`。

## 必跑命令

```bash
PYTHONPYCACHEPREFIX=/tmp/cr019-s08-pycompile PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile trading/qmt_gateway_fallback.py tests/test_cr019_qmt_gateway_fallback.py
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
rg -n "rm -rf|sudo|curl|wget|nc |netcat|ssh|scp|chmod|chown|mkfs|dd if=|iptables|systemctl|kill -9|os\\.remove|shutil\\.rmtree|subprocess|Popen|eval\\(|exec\\(" trading/qmt_gateway_fallback.py tests/test_cr019_qmt_gateway_fallback.py docs/QMT-INCIDENT-PLAYBOOK.md
rg -n -i "ignore (all )?(previous|prior) instructions|system prompt|developer message|prompt injection|jailbreak|exfiltrate|leak" trading/qmt_gateway_fallback.py tests/test_cr019_qmt_gateway_fallback.py docs/QMT-INCIDENT-PLAYBOOK.md
git diff --check -- trading/qmt_gateway_fallback.py tests/test_cr019_qmt_gateway_fallback.py docs/QMT-INCIDENT-PLAYBOOK.md process/stories/CR019-S08-fallback-incident-signed-file-boundary.md process/checks/CP6-CR019-S08-fallback-incident-signed-file-boundary-CODING-DONE.md
```

若目标文件未被 Git 跟踪，需用等价 `git diff --check --no-index /dev/null <file>` 检查 whitespace，并在 CP6 中说明退出码 1 只是文件差异预期。

## 期望输出

`process/checks/CP6-CR019-S08-fallback-incident-signed-file-boundary-CODING-DONE.md`

完成后请回复：

- 修改文件列表
- CP6 文件路径与结论
- 实际执行的验证命令和结果
- 是否发现 BLOCKING / REQUIRED / OPEN 项
- forbidden operation counters 是否全部为 0
