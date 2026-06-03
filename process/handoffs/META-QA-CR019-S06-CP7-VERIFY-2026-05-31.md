---
handoff_id: "META-QA-CR019-S06-CP7-VERIFY-2026-05-31"
from_agent: "meta-po"
to_agent: "meta-qa"
workflow_id: "local_backtest-cr019"
change_id: "CR-019"
phase: "story-execution"
story_id: "CR019-S06-qmt-endpoint-matrix-contract"
wave_id: "CR019-W3-AUTH-ENDPOINT-GATE"
status: "completed-closed"
created_at: "2026-05-31T08:16:20+08:00"
dispatch:
  required: true
  semantic: "stage-dispatch"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-qa"
  agent_path: ".agents/agents/meta-qa.md"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e7b64-9eb5-7193-99d1-57466159d32d"
  agent_name: "qa-wei"
  thread_id: "019e7b64-9eb5-7193-99d1-57466159d32d"
  spawned_at: "2026-05-31T08:17:35+08:00"
  resumed_at: ""
  completed_at: "2026-05-31T08:19:59+08:00"
  closed_at: "2026-05-31T08:25:16+08:00"
  evidence: "spawn_agent returned agent_id=019e7b64-9eb5-7193-99d1-57466159d32d nickname=qa-wei; wait_agent returned completed CR019-S06 CP7 PASS; close_agent previous_status returned completed CR019-S06 CP7 PASS"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-qa"
  workflow_id: "local_backtest-cr019"
  change_id: "CR-019"
  story_id: "CR019-S06-qmt-endpoint-matrix-contract"
  wave_id: "CR019-W3-AUTH-ENDPOINT-GATE"
---

# META-QA CR-019 S06 CP7 Verification Handoff

## 任务

请以 `meta-qa` 身份验证 `CR019-S06-qmt-endpoint-matrix-contract`。当前 Story 已完成 CP6，状态为 `ready-for-verification`。本轮只允许受控离线 / fixture / dry-run 合同验证，验证目标是确认完整 QMT endpoint matrix、typed allowed / blocked result、C 侧 client 消费合同和安全边界满足 Story、LLD、CP5、S03/S04/S05 上游合同与 CP6 要求。

你不是独自在代码库中工作：当前仓库有多批未提交的 CR-015 / CR-016 / CR-017 / CR-018 / CR-019 产物。不要 revert 其他人的修改。QA 只允许写入本 Story 的 CP7 结果文件，除非发现阻断项需要在 CP7 中要求回修。

## 必读输入

| 类型 | 路径 |
|---|---|
| 项目规则 | `AGENTS.md` |
| 工作流状态 | `process/STATE.md` |
| Story 汇总 | `process/STORY-STATUS.md` |
| Story | `process/stories/CR019-S06-qmt-endpoint-matrix-contract.md` |
| LLD | `process/stories/CR019-S06-qmt-endpoint-matrix-contract-LLD.md` |
| CP5 auto | `process/checks/CP5-CR019-S06-qmt-endpoint-matrix-contract-LLD-IMPLEMENTABILITY.md` |
| CP5 manual | `checkpoints/CP5-CR019-STAGE6-QMT-BRIDGE-BATCH-A-LLD-BATCH.md` |
| CP6 | `process/checks/CP6-CR019-S06-qmt-endpoint-matrix-contract-CODING-DONE.md` |
| Dev handoff | `process/handoffs/META-DEV-CR019-S06-IMPLEMENT-2026-05-31.md` |
| Upstream S03 CP7 | `process/checks/CP7-CR019-S03-qmt-cside-client-cli-contract-VERIFICATION-DONE.md` |
| Upstream S04 CP7 | `process/checks/CP7-CR019-S04-windows-gateway-lifecycle-deployment-VERIFICATION-DONE.md` |
| Upstream S05 CP7 | `process/checks/CP7-CR019-S05-pairing-hmac-auth-redaction-VERIFICATION-DONE.md` |
| Endpoint matrix | `trading/qmt_endpoint_matrix.py` |
| Gateway contracts | `trading/qmt_gateway_contracts.py` |
| Client contract | `trading/qmt_client.py` |
| S06 tests | `tests/test_cr019_qmt_endpoint_matrix.py` |
| Regression tests | `tests/test_cr019_qmt_cside_client_cli.py`、`tests/test_cr019_qmt_gateway_lifecycle.py`、`tests/test_cr019_qmt_pairing_hmac_auth.py` |

## 写入范围

| 类型 | 路径 | 规则 |
|---|---|---|
| process | `process/checks/CP7-CR019-S06-qmt-endpoint-matrix-contract-VERIFICATION-DONE.md` | 写入 CP7 验证完成检查结果。 |

禁止修改：源码、测试、docs、Story 卡片、`process/STATE.md`、`process/STORY-STATUS.md`、`process/DEVELOPMENT-PLAN.yaml`、`process/STORY-BACKLOG.md`、HLD / ADR / CP5 人工审查稿、`pyproject.toml`、`uv.lock`、`.env`、凭据或 secret 值。

## 必须验证

1. HLD §33.11 endpoint 类别覆盖率为 100%，且不是 dry-run-only 目标基线。
2. 每个 endpoint spec 显式包含 method、path、client method、required scope、gate inputs、real operation kind、default visibility、blocked reason。
3. 每类 endpoint 至少有 1 个 typed blocked result case。
4. `health` / `capabilities` 可见不提升为 account / order / cancel / simulation / live 授权。
5. S05 HMAC pass 只识别调用方和 scope，不直接授权 endpoint operation。
6. `trading/qmt_client.py` 只消费 matrix / contracts，不复制 gateway / run gate / risk gate / kill-switch 业务逻辑。
7. 真实 QMT / MiniQMT / XtQuant 调用、真实 order/cancel/account 查询、broker lake 写入、provider/lake/publish/simulation/live 计数全部为 0。
8. 目标文件不导入 `fastapi`、`uvicorn`、`requests`、`httpx`、`socket`、`urllib`、`subprocess`、`xtquant`、`xttrader`、`xtdata`。
9. 未修改依赖文件，不读取 `.env`，不启动 gateway，不绑定端口，不打开 socket，不调用真实 QMT / MiniQMT / XtQuant / provider / lake / broker / publish / simulation / live。
10. CP7 结果必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、测试结果和真实操作计数。

## 必跑命令

```bash
PYTHONPYCACHEPREFIX=/tmp/cr019-s06-cp7-pycompile PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile trading/qmt_endpoint_matrix.py trading/qmt_gateway_contracts.py trading/qmt_client.py tests/test_cr019_qmt_endpoint_matrix.py
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr019_qmt_endpoint_matrix.py tests/test_cr019_qmt_cside_client_cli.py tests/test_cr019_qmt_gateway_lifecycle.py tests/test_cr019_qmt_pairing_hmac_auth.py
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -c "from trading.qmt_client import collect_qmt_client_safety_counters; from trading.qmt_gateway_contracts import collect_qmt_gateway_contract_counters; print({'client': collect_qmt_client_safety_counters(), 'contracts': collect_qmt_gateway_contract_counters()})"
git diff --name-only -- pyproject.toml uv.lock .env
git status --short -- .pytest_cache tests/__pycache__ engine/__pycache__ trading/__pycache__
```

建议额外运行：

```bash
rg -n "^(from|import) (fastapi|uvicorn|requests|httpx|socket|urllib|subprocess|xtquant|xttrader|xtdata)\b" trading/qmt_endpoint_matrix.py trading/qmt_gateway_contracts.py trading/qmt_client.py tests/test_cr019_qmt_endpoint_matrix.py
rg -n "\b(open\(|read_text\(|write_text\(|dotenv|os\.environ|getenv|load_dotenv|keyring|credential|uvicorn\.|FastAPI\(|requests\.|httpx\.|socket\.|subprocess\.|os\.system|Popen\(|bind\(|listen\(|connect\(|place_order\(|cancel_order\(|query_account\(|publish\(|fetch\(|run_simulation\()" trading/qmt_endpoint_matrix.py trading/qmt_gateway_contracts.py trading/qmt_client.py tests/test_cr019_qmt_endpoint_matrix.py
git diff --check -- trading/qmt_endpoint_matrix.py trading/qmt_gateway_contracts.py trading/qmt_client.py tests/test_cr019_qmt_endpoint_matrix.py process/checks/CP6-CR019-S06-qmt-endpoint-matrix-contract-CODING-DONE.md process/stories/CR019-S06-qmt-endpoint-matrix-contract.md process/handoffs/META-DEV-CR019-S06-IMPLEMENT-2026-05-31.md
```

如果目标文件未被 Git 跟踪，需用等价 `git diff --check --no-index /dev/null <file>` 检查 whitespace，并在 CP7 中说明退出码 1 只是文件差异预期。

## 期望输出

`process/checks/CP7-CR019-S06-qmt-endpoint-matrix-contract-VERIFICATION-DONE.md`

完成后请回复：

- CP7 文件路径与结论
- 实际执行的验证命令和结果
- 是否发现 BLOCKING / REQUIRED / OPEN 项
- forbidden operation counters 是否全部为 0
