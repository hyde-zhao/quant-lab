---
handoff_id: "META-DEV-CR019-S06-IMPLEMENT-2026-05-31"
from_agent: "meta-po"
to_agent: "meta-dev"
workflow_id: "local_backtest-cr019"
change_id: "CR-019"
phase: "story-execution"
story_id: "CR019-S06-qmt-endpoint-matrix-contract"
wave_id: "CR019-W3-AUTH-ENDPOINT-GATE"
status: "completed-closed"
created_at: "2026-05-31T08:01:00+08:00"
dispatch:
  required: true
  semantic: "stage-dispatch"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".agents/agents/meta-dev.md"
  tool_name: "multi_agent_v1.spawn_agent / multi_agent_v1.close_agent"
  agent_id: "019e7b57-2b50-7353-a782-a0f6ddc513af"
  agent_name: "dev-you"
  thread_id: "019e7b57-2b50-7353-a782-a0f6ddc513af"
  spawned_at: "2026-05-31T08:02:53+08:00"
  resumed_at: ""
  completed_at: "2026-05-31T08:12:36+08:00"
  closed_at: "2026-05-31T08:15:43+08:00"
  evidence: "spawn_agent returned agent_id=019e7b57-2b50-7353-a782-a0f6ddc513af nickname=dev-you; close_agent previous_status returned completed CR019-S06 CP6 PASS"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-dev"
  workflow_id: "local_backtest-cr019"
  change_id: "CR-019"
  story_id: "CR019-S06-qmt-endpoint-matrix-contract"
  wave_id: "CR019-W3-AUTH-ENDPOINT-GATE"
---

# META-DEV CR-019 S06 Implementation Handoff

## 任务

请以 `meta-dev` 身份实现 `CR019-S06-qmt-endpoint-matrix-contract`。当前 Story 的 CP5 / LLD 已获批，S03 / S04 / S05 均已 CP7 PASS 并收敛为 `verified`，S06 dev gate 已满足。实现目标是冻结完整 QMT endpoint matrix、typed allowed / blocked result 和 C 侧 client 消费合同。

本轮只允许受控离线 / fixture / dry-run 合同实现。Endpoint 完整支持不等于真实 QMT 操作授权；不得把 dry-run-only 当成目标基线。

你不是独自在代码库中工作：当前仓库有大量未提交的 CR-015 / CR-016 / CR-017 / CR-018 / CR-019 产物。不要 revert 其他人的修改；如遇已有内容，按当前文件事实增量合并。

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
| S03 CP7 | `process/checks/CP7-CR019-S03-qmt-cside-client-cli-contract-VERIFICATION-DONE.md` |
| S04 CP7 | `process/checks/CP7-CR019-S04-windows-gateway-lifecycle-deployment-VERIFICATION-DONE.md` |
| S05 CP7 | `process/checks/CP7-CR019-S05-pairing-hmac-auth-redaction-VERIFICATION-DONE.md` |
| Existing client | `trading/qmt_client.py` |
| Auth contract | `trading/qmt_auth.py` |
| Gateway config / lifecycle | `trading/qmt_gateway_config.py`、`trading/qmt_gateway_service.py` |
| Existing regression tests | `tests/test_cr019_qmt_cside_client_cli.py`、`tests/test_cr019_qmt_gateway_lifecycle.py`、`tests/test_cr019_qmt_pairing_hmac_auth.py` |

## 允许写入范围

| 类型 | 路径 | 规则 |
|---|---|---|
| source | `trading/qmt_endpoint_matrix.py` | 创建 endpoint matrix、category enum、endpoint spec、scope、gate inputs 和 blocked cases。 |
| source | `trading/qmt_gateway_contracts.py` | 创建 typed allowed / blocked result、blocked reason enum、error payload 和 operation counter contract。 |
| source | `trading/qmt_client.py` | 只做 S06 合同增量：接入 endpoint matrix 的类型化 client 方法；不得复制 gateway / run gate / risk gate 业务逻辑。 |
| tests | `tests/test_cr019_qmt_endpoint_matrix.py` | 创建 fixture-only 合同测试。 |
| process | `process/checks/CP6-CR019-S06-qmt-endpoint-matrix-contract-CODING-DONE.md` | 写入 CP6 编码完成检查结果，必须包含 Agent Dispatch Evidence。 |
| process | `process/stories/CR019-S06-qmt-endpoint-matrix-contract.md` | 仅允许追加 CP6 / 状态证据；不得修改需求、范围或验收标准。 |

禁止修改：`process/STATE.md`、`process/STORY-STATUS.md`、`process/DEVELOPMENT-PLAN.yaml`、`process/STORY-BACKLOG.md`、HLD / ADR / CP5 人工审查稿、其他 Story、README/docs、`pyproject.toml`、`uv.lock`、`.env`、凭据或 secret 值。

## 必须实现

1. 按 LLD §8 冻结 endpoint 覆盖类别：health / heartbeat、capabilities、intent validate、dry-run / mock、market query、account snapshot、positions、orders / trades、simulation submit、simulation cancel、live-readonly、live submit / cancel、reconciliation、kill-switch。
2. Endpoint spec 必须显式包含 method、path、client method、required scope、gate inputs、real operation kind、default visibility、blocked reason。
3. 每类 endpoint 至少包含 1 个 typed blocked result case。
4. `health` / `capabilities` 可见不提升为 account / order / cancel / simulation / live 授权。
5. Auth / HMAC 与 run gate 分离：S05 HMAC pass 只识别调用方和 scope，不改变 endpoint 操作授权。
6. `trading/qmt_client.py` 只消费 matrix / contracts，不内嵌 stage / risk / kill-switch / authorization 业务判断。
7. 真实 QMT / MiniQMT / XtQuant 调用计数为 0，broker lake 写入计数为 0，真实 order / cancel / account 查询计数为 0。
8. 不新增依赖，不启动 gateway，不绑定端口，不打开 socket，不读取 `.env` 或凭据，不导入 `xtquant`、`xttrader`、`xtdata`。

## 必跑命令

```bash
PYTHONPYCACHEPREFIX=/tmp/cr019-s06-pycompile PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile trading/qmt_endpoint_matrix.py trading/qmt_gateway_contracts.py trading/qmt_client.py tests/test_cr019_qmt_endpoint_matrix.py
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr019_qmt_endpoint_matrix.py tests/test_cr019_qmt_cside_client_cli.py tests/test_cr019_qmt_gateway_lifecycle.py tests/test_cr019_qmt_pairing_hmac_auth.py
git diff --name-only -- pyproject.toml uv.lock .env
git status --short -- .pytest_cache tests/__pycache__ engine/__pycache__ trading/__pycache__
```

建议额外运行：

```bash
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -c "from trading.qmt_client import collect_qmt_client_safety_counters; from trading.qmt_gateway_contracts import collect_qmt_gateway_contract_counters; print({'client': collect_qmt_client_safety_counters(), 'contracts': collect_qmt_gateway_contract_counters()})"
rg -n "^(from|import) (fastapi|uvicorn|requests|httpx|socket|urllib|subprocess|xtquant|xttrader|xtdata)\b" trading/qmt_endpoint_matrix.py trading/qmt_gateway_contracts.py trading/qmt_client.py tests/test_cr019_qmt_endpoint_matrix.py
rg -n "\b(open\(|read_text\(|write_text\(|dotenv|os\.environ|getenv|load_dotenv|keyring|credential|uvicorn\.|FastAPI\(|requests\.|httpx\.|socket\.|subprocess\.|os\.system|Popen\(|bind\(|listen\(|connect\(|place_order\(|cancel_order\(|query_account\(|publish\(|fetch\(|run_simulation\()" trading/qmt_endpoint_matrix.py trading/qmt_gateway_contracts.py trading/qmt_client.py tests/test_cr019_qmt_endpoint_matrix.py
git diff --check -- trading/qmt_endpoint_matrix.py trading/qmt_gateway_contracts.py trading/qmt_client.py tests/test_cr019_qmt_endpoint_matrix.py process/checks/CP6-CR019-S06-qmt-endpoint-matrix-contract-CODING-DONE.md process/stories/CR019-S06-qmt-endpoint-matrix-contract.md
```

如果目标文件未被 Git 跟踪，需用等价 `git diff --check --no-index /dev/null <file>` 检查 whitespace，并在 CP6 中说明退出码 1 只是文件差异预期。

## CP6 输出要求

请写入 `process/checks/CP6-CR019-S06-qmt-endpoint-matrix-contract-CODING-DONE.md`，结构必须包含：

- Entry Criteria
- Checklist
- Exit Criteria
- Deliverables
- Agent Dispatch Evidence
- Validation Results
- Forbidden Operation Counters
- 写入范围复核
- 结论

完成后请回复：

- CP6 文件路径与结论
- 实际改动文件
- 实际执行命令和结果
- 是否发现 BLOCKING / OPEN 项
- forbidden operation counters 是否全部为 0
