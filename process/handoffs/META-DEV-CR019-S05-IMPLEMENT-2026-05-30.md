---
handoff_id: "META-DEV-CR019-S05-IMPLEMENT-2026-05-30"
from_agent: "meta-po"
to_agent: "meta-dev"
workflow_id: "local_backtest-cr019"
change_id: "CR-019"
phase: "story-execution"
created_at: "2026-05-30T20:54:11+08:00"
status: "completed-closed"
dispatch:
  required: true
  semantic: "stage-dispatch"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".agents/agents/meta-dev.md"
  tool_name: "multi_agent_v1.spawn_agent / multi_agent_v1.close_agent"
  agent_id: "019e78f3-f659-7760-8a21-84d1b14832d4"
  agent_name: "dev-yang"
  thread_id: "019e78f3-f659-7760-8a21-84d1b14832d4"
  spawned_at: "2026-05-30T20:55:19+08:00"
  resumed_at: ""
  completed_at: "2026-05-30T21:07:46+08:00"
  closed_at: "2026-05-30T21:07:46+08:00"
  evidence: "spawn_agent returned agent_id=019e78f3-f659-7760-8a21-84d1b14832d4 nickname=dev-yang; close_agent previous_status returned completed CR019-S05 CP6 PASS"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-dev"
  workflow_id: "local_backtest-cr019"
  change_id: "CR-019"
  story_id: "CR019-S05-pairing-hmac-auth-redaction"
  wave_id: "CR019-W3-AUTH-ENDPOINT-GATE"
---

# META-DEV CR-019 S05 Implementation Handoff

## 任务

请以 `meta-dev` 身份实现 `CR019-S05-pairing-hmac-auth-redaction`。当前 CR019-S03 和 CR019-S04 均已通过 CP6 / CP7 并收敛为 `verified`，S05 Story 卡片为 `dev-ready`。本次只允许受控离线 / fixture / dry-run 合同实现，目标是冻结 pairing、HMAC 调用方识别、auth mode fail-closed 和日志脱敏合同。

HMAC 只用于识别调用方和 endpoint scope，不授权 simulation / live / account / cancel，不替代 CR015 / CR016 / CR019-S07 的 run gate、risk gate、kill switch 或 per-run authorization。

## 必读输入

| 文件 | 用途 |
|---|---|
| `AGENTS.md` | CP6 / CP7 门控、真实子 agent 证据、禁止真实操作边界 |
| `process/STATE.md` | 当前 CR-019、S05 dev-ready、真实操作禁止范围 |
| `process/STORY-STATUS.md` | S05 dev-ready 与后续 Story gate |
| `checkpoints/CP5-CR019-STAGE6-QMT-BRIDGE-BATCH-A-LLD-BATCH.md` | CP5 approved 决策与 DQ-01..DQ-07 |
| `process/stories/CR019-S05-pairing-hmac-auth-redaction.md` | Story 卡片、文件 owner、dev_gate |
| `process/stories/CR019-S05-pairing-hmac-auth-redaction-LLD.md` | S05 approved LLD，必须按第 4 / 6 / 10 / 11 / 14 节实现 |
| `process/checks/CP5-CR019-S05-pairing-hmac-auth-redaction-LLD-IMPLEMENTABILITY.md` | S05 CP5 自动预检 |
| `process/checks/CP7-CR019-S03-qmt-cside-client-cli-contract-VERIFICATION-DONE.md` | S03 client / CLI / REST transport contract verified 证据 |
| `process/checks/CP7-CR019-S04-windows-gateway-lifecycle-deployment-VERIFICATION-DONE.md` | S04 gateway config / lifecycle contract verified 证据 |
| `trading/qmt_gateway_config.py` | S04 gateway config 合同；当前 Story 只允许追加 auth mode / TTL / skew / nonce 配置 |

## 允许写入范围

| 类型 | 路径 |
|---|---|
| 创建 | `trading/qmt_auth.py` |
| 创建 | `trading/qmt_redaction.py` |
| 创建 | `tests/test_cr019_qmt_pairing_hmac_auth.py` |
| 修改 | `trading/qmt_gateway_config.py`，仅允许追加 auth mode、TTL、clock skew、nonce TTL、no-auth 显式临时配置与对应验证，不得破坏 S04 字段 / tests |
| 创建 | `process/checks/CP6-CR019-S05-pairing-hmac-auth-redaction-CODING-DONE.md` |
| 可修改 | `process/stories/CR019-S05-pairing-hmac-auth-redaction.md`，仅允许将状态推进到 `ready-for-verification` 并记录 CP6 证据 |

## 禁止事项

- 不得修改 `pyproject.toml`、`uv.lock`、`.env` 或任何凭据文件。
- 不得读取 `.env`、Windows credential、token、secret、cookie、session、私钥、账户号、交易密码或任何真实凭据文件。
- 不得生成、保存或打印真实 secret；测试中可使用明确标注的 fixture-only 字符串，不得伪装为真实凭据。
- 不得把 pairing code、secret、token、账户、session、cookie、`.env`、私有路径写入日志、报告、检查点或测试快照。
- 不得启动服务、绑定端口、打开 socket、导入 FastAPI / uvicorn / requests / httpx / socket / subprocess / xtquant / xttrader / xtdata。
- 不得调用 QMT / MiniQMT / XtQuant、不得发单、撤单、查询真实账户。
- 不得执行 provider fetch、lake write、broker lake write、publish、current pointer publish、simulation/live run。
- 不得把 HMAC pass 解释为交易授权；不得绕过 run gate、risk gate、kill switch 或 per-run authorization。
- 不得修改 HLD、ADR、REQUIREMENTS、STORY-BACKLOG、DEVELOPMENT-PLAN、STATE、STORY-STATUS 或 CR019-S06..S10 Story。

## 实现要求

1. 创建 `trading/qmt_auth.py`，至少覆盖：
   - `PairingRequest`
   - `PairingApproval`
   - `QmtHmacHeaders`
   - `QmtAuthConfig`
   - `QmtAuthResult`
   - `QmtAuthBlockedReason`
   - pairing request / list / approve / complete 四步合同
   - `validate_hmac_request`
   - `validate_auth_mode`
   - `collect_qmt_auth_safety_counters`
2. 创建 `trading/qmt_redaction.py`，至少覆盖：
   - `RedactionReport`
   - `redact_qmt_text`
   - `redact_qmt_mapping`
   - secret、pairing code、token、account、session、cookie、trade password、`.env`、private path 脱敏规则
   - `scan_for_qmt_sensitive_leaks`
3. 修改 `trading/qmt_gateway_config.py`：
   - 在不破坏 S04 `GatewayConfig` / `build_gateway_config` / `validate_gateway_security` / tests 的前提下追加 auth config 字段。
   - 默认 auth mode 必须是 `pairing_hmac`。
   - no-auth 只能在 debug / fixture / explicit temporary 场景被显式允许；默认必须 fail closed。
   - 默认合同值按 LLD 冻结：`pairing_request_ttl_seconds=600`、`pairing_code_ttl_seconds=300`、`hmac_clock_skew_seconds=300`、`nonce_ttl_seconds=600`。
4. 创建 `tests/test_cr019_qmt_pairing_hmac_auth.py`，至少覆盖：
   - pair request / list / approve / complete 四步字段覆盖率为 100%。
   - pair list / approve / complete 不泄露 secret、pairing code、token。
   - timestamp skew、nonce replay、scope denied、signature mismatch、client 未批准、pairing code 过期均 hard block，adapter / QMT call 计数为 0。
   - HMAC pass 仍不授权 simulation / live / account / cancel，`trade_authorized=false`。
   - no-auth 默认 blocked，只有 fixture/debug/explicit temporary 且显式配置时才允许 auth mode 通过，但仍不授权真实交易。
   - 结构化和文本日志脱敏后 secret、pairing code、token、账户、session、cookie、交易密码、`.env`、私有路径泄露次数为 0。
   - dependency_change、credential_read、qmt_api_call、real_order、real_cancel、account_query、provider_fetch、lake_write、publish、simulation_or_live_run 均为 0。
5. 创建 CP6 自动检查结果 `process/checks/CP6-CR019-S05-pairing-hmac-auth-redaction-CODING-DONE.md`，必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、Validation Results、Forbidden Operation Counters 和写入范围复核。

## 建议验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr019_qmt_pairing_hmac_auth.py tests/test_cr019_qmt_gateway_lifecycle.py tests/test_cr019_qmt_cside_client_cli.py
```

可追加：

```bash
PYTHONPYCACHEPREFIX=/tmp/cr019-s05-pycompile PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile trading/qmt_auth.py trading/qmt_redaction.py trading/qmt_gateway_config.py tests/test_cr019_qmt_pairing_hmac_auth.py
git diff --check -- trading/qmt_auth.py trading/qmt_redaction.py trading/qmt_gateway_config.py tests/test_cr019_qmt_pairing_hmac_auth.py process/checks/CP6-CR019-S05-pairing-hmac-auth-redaction-CODING-DONE.md process/stories/CR019-S05-pairing-hmac-auth-redaction.md
git diff --name-only -- pyproject.toml uv.lock .env
git status --short -- .pytest_cache tests/__pycache__ engine/__pycache__ trading/__pycache__
rg -n "^(from|import) (fastapi|uvicorn|requests|httpx|socket|urllib|subprocess|xtquant|xttrader|xtdata)\b" trading/qmt_auth.py trading/qmt_redaction.py trading/qmt_gateway_config.py tests/test_cr019_qmt_pairing_hmac_auth.py
rg -n "\b(open\(|read_text\(|write_text\(|dotenv|os\.environ|getenv|load_dotenv|keyring|credential|place_order\(|cancel_order\(|query_account\(|publish\(|fetch\(|run_simulation\()" trading/qmt_auth.py trading/qmt_redaction.py trading/qmt_gateway_config.py tests/test_cr019_qmt_pairing_hmac_auth.py
```

如果目标文件未被 Git 跟踪，需用等价 `git diff --check --no-index /dev/null <file>` 检查 whitespace，并在 CP6 中说明退出码 1 只是文件差异预期。

## 完成后回复

请列出：

- 修改文件清单
- CP6 文件路径与结论
- 实际执行的验证命令和结果
- forbidden operation counters 是否全部为 0
- 是否存在 BLOCKING / OPEN 项；预期无阻断 OPEN，真实 secret / 凭据 / QMT / 服务启动均应为 0
