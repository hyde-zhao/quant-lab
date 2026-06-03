---
handoff_id: "META-DEV-CR019-S07-IMPLEMENT-2026-05-31"
from_agent: "meta-po"
to_agent: "meta-dev"
workflow_id: "local_backtest-cr019"
change_id: "CR-019"
phase: "story-execution"
story_id: "CR019-S07-run-gate-blocked-reason-integration"
wave_id: "CR019-W3-AUTH-ENDPOINT-GATE"
status: "completed-closed"
created_at: "2026-05-31T08:26:06+08:00"
dispatch:
  required: true
  semantic: "stage-dispatch"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".agents/agents/meta-dev.md"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e7b6d-929e-7bd2-be73-cbdad9a94a36"
  agent_name: "dev-he"
  thread_id: "019e7b6d-929e-7bd2-be73-cbdad9a94a36"
  spawned_at: "2026-05-31T08:27:22+08:00"
  resumed_at: ""
  completed_at: "2026-05-31T08:37:31+08:00"
  closed_at: "2026-05-31T08:42:42+08:00"
  evidence: "spawn_agent returned agent_id=019e7b6d-929e-7bd2-be73-cbdad9a94a36 nickname=dev-he; wait_agent returned completed CR019-S07 CP6 PASS; close_agent previous_status returned completed CR019-S07 CP6 PASS"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-dev"
  workflow_id: "local_backtest-cr019"
  change_id: "CR-019"
  story_id: "CR019-S07-run-gate-blocked-reason-integration"
  wave_id: "CR019-W3-AUTH-ENDPOINT-GATE"
---

# META-DEV CR-019 S07 Implementation Handoff

## 任务

请以 `meta-dev` 身份实现 `CR019-S07-run-gate-blocked-reason-integration`。当前 S06 已 CP7 PASS 并收敛为 `verified`；S07 的 S01/S06/CR015-S04/CR016-S03/CR016-S04 依赖均已满足。实现目标是创建 QMT gateway 运行门控聚合器，将 S06 endpoint matrix / typed result、S05 auth、CR019-S01 admission、CR016 stage gate、CR015 pre-trade risk、CR016 kill-switch、per-run authorization 与 raw execution policy 汇总为 fail-closed blocked reason 合同。

你不是独自在代码库中工作：当前仓库有多批未提交的 CR-015 / CR-016 / CR-017 / CR-018 / CR-019 产物。不要 revert 其他人的修改。共享文件只允许新增 read-only adapter 或兼容性 helper，不得改变 CR015/CR016 已验证语义。

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
| S01 CP7 | `process/checks/CP7-CR019-S01-stage6-admission-gate-package-VERIFICATION-DONE.md` |
| S05 CP7 | `process/checks/CP7-CR019-S05-pairing-hmac-auth-redaction-VERIFICATION-DONE.md` |
| S06 CP7 | `process/checks/CP7-CR019-S06-qmt-endpoint-matrix-contract-VERIFICATION-DONE.md` |
| Endpoint matrix | `trading/qmt_endpoint_matrix.py` |
| Gateway result contracts | `trading/qmt_gateway_contracts.py` |
| Auth contract | `trading/qmt_auth.py` |
| Stage gate | `trading/stage_gate.py` |
| Pre-trade risk | `trading/pretrade_risk.py` |
| Kill switch | `trading/kill_switch.py` |
| 上游测试 | `tests/test_cr019_qmt_endpoint_matrix.py`、`tests/test_cr019_qmt_pairing_hmac_auth.py`、`tests/test_cr015_pretrade_risk_gate.py`、`tests/test_cr016_monitoring_kill_switch.py`、`tests/test_cr016_runbook_approval_gates.py`、`tests/test_cr016_simulation_order_enable_gate.py` |

## 写入范围

| 类型 | 路径 | 规则 |
|---|---|---|
| code | `trading/qmt_gateway_gates.py` | 创建运行门控聚合器、decision/result 转换和安全 counter。 |
| test | `tests/test_cr019_qmt_gateway_run_gates.py` | 创建 S07 fixture-only 合同测试。 |
| shared code | `trading/stage_gate.py` | 只允许新增 admission / stage gate read-only adapter；不得改 stage progression 语义。 |
| shared code | `trading/pretrade_risk.py` | 只允许新增 risk read-only adapter；不得降低 hard block 或增加 broker 操作。 |
| shared code | `trading/kill_switch.py` | 只允许新增 kill-switch / heartbeat read-only adapter；不得启动监控服务或持久化 incident。 |
| process | `process/checks/CP6-CR019-S07-run-gate-blocked-reason-integration-CODING-DONE.md` | 写入 CP6 编码完成检查结果。 |
| process | `process/stories/CR019-S07-run-gate-blocked-reason-integration.md` | 仅可回写 CP6 / ready-for-verification 状态字段。 |

禁止修改：`process/STATE.md`、`process/STORY-STATUS.md`、`process/DEVELOPMENT-PLAN.yaml`、`process/STORY-BACKLOG.md`、HLD / ADR / CP5 人工审查稿、README / docs、`pyproject.toml`、`uv.lock`、`.env`、凭据或 secret 值。

## 必须实现

1. `trading/qmt_gateway_gates.py` 提供 `QmtGateContext`、`QmtGateDecision`、`evaluate_qmt_gateway_gates()`、`to_qmt_gateway_result()` 和 `collect_qmt_gateway_gate_safety_counters()` 等稳定入口。
2. blocked reason priority 固定为 auth -> endpoint/schema -> admission/stage -> authorization -> risk -> kill_switch -> raw_policy -> operation_not_authorized；主 reason 可单一返回，detail 可暴露 suppressed reasons。
3. 任一 gate missing / fail / unknown 必须 fail closed，`adapter_call`、`qmt_api_call`、`real_order`、`real_cancel`、`account_query`、`broker_lake_write`、`simulation_or_live_run` 均为 0。
4. HMAC pass 只识别调用方和 scope，不得直接授权 account / order / cancel / simulation / live。
5. S07 必须消费 S06 `QmtEndpointSpec` / `QmtGatewayResult` / `QmtBlockedReason`，不得定义第二套不兼容 error schema。
6. 对 `stage_gate.py`、`pretrade_risk.py`、`kill_switch.py` 只增加 read-only adapter，不删除、不重命名、不改变既有函数、枚举和测试期望。
7. 不读取 `.env`，不启动 gateway，不绑定端口，不打开 socket，不导入或调用真实 QMT / MiniQMT / XtQuant / provider / lake / broker / publish / simulation / live。
8. CP6 必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、测试结果、forbidden operation counters 和 no-real-operation 说明。

## 必跑命令

```bash
PYTHONPYCACHEPREFIX=/tmp/cr019-s07-pycompile PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile trading/qmt_gateway_gates.py trading/stage_gate.py trading/pretrade_risk.py trading/kill_switch.py tests/test_cr019_qmt_gateway_run_gates.py
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr019_qmt_gateway_run_gates.py tests/test_cr019_qmt_endpoint_matrix.py tests/test_cr019_qmt_pairing_hmac_auth.py tests/test_cr015_pretrade_risk_gate.py tests/test_cr016_monitoring_kill_switch.py tests/test_cr016_runbook_approval_gates.py tests/test_cr016_simulation_order_enable_gate.py
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -c "from trading.qmt_gateway_gates import collect_qmt_gateway_gate_safety_counters; print(collect_qmt_gateway_gate_safety_counters())"
git diff --name-only -- pyproject.toml uv.lock .env
git status --short -- .pytest_cache tests/__pycache__ engine/__pycache__ trading/__pycache__
git diff --check -- trading/qmt_gateway_gates.py trading/stage_gate.py trading/pretrade_risk.py trading/kill_switch.py tests/test_cr019_qmt_gateway_run_gates.py process/checks/CP6-CR019-S07-run-gate-blocked-reason-integration-CODING-DONE.md process/stories/CR019-S07-run-gate-blocked-reason-integration.md
```

建议额外运行：

```bash
rg -n "^(from|import) (fastapi|uvicorn|requests|httpx|socket|urllib|subprocess|xtquant|xttrader|xtdata)\b" trading/qmt_gateway_gates.py trading/stage_gate.py trading/pretrade_risk.py trading/kill_switch.py tests/test_cr019_qmt_gateway_run_gates.py
rg -n "\b(open\(|read_text\(|write_text\(|dotenv|os\.environ|getenv|load_dotenv|keyring|credential|uvicorn\.|FastAPI\(|requests\.|httpx\.|socket\.|subprocess\.|os\.system|Popen\(|bind\(|listen\(|connect\(|place_order\(|cancel_order\(|query_account\(|publish\(|fetch\(|run_simulation\()" trading/qmt_gateway_gates.py trading/stage_gate.py trading/pretrade_risk.py trading/kill_switch.py tests/test_cr019_qmt_gateway_run_gates.py
rg -n -i "ignore (all )?(previous|prior) instructions|system prompt|developer message|prompt injection|jailbreak|exfiltrate|leak" trading/qmt_gateway_gates.py trading/stage_gate.py trading/pretrade_risk.py trading/kill_switch.py tests/test_cr019_qmt_gateway_run_gates.py
```

如果目标文件未被 Git 跟踪，需用等价 `git diff --check --no-index /dev/null <file>` 检查 whitespace，并在 CP6 中说明退出码 1 只是文件差异预期。

## 期望输出

`process/checks/CP6-CR019-S07-run-gate-blocked-reason-integration-CODING-DONE.md`

完成后请回复：

- 修改 / 新增文件路径
- CP6 文件路径与结论
- 实际执行的验证命令和结果
- 是否发现 BLOCKING / REQUIRED / OPEN 项
- forbidden operation counters 是否全部为 0
