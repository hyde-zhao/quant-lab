---
handoff_id: "META-QA-CR019-S04-CP7-VERIFY-2026-05-30"
from_agent: "meta-po"
to_agent: "meta-qa"
workflow_id: "local_backtest-cr019"
change_id: "CR-019"
phase: "story-execution"
story_id: "CR019-S04-windows-gateway-lifecycle-deployment"
wave_id: "CR019-W2-CS-TRANSPORT"
status: "completed-closed"
created_at: "2026-05-30T20:40:44+08:00"
dispatch:
  required: true
  semantic: "stage-dispatch"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-qa"
  agent_path: ".agents/agents/meta-qa.md"
  tool_name: "multi_agent_v1.spawn_agent / multi_agent_v1.close_agent"
  agent_id: "019e78e8-037c-78c1-81e8-050ec8d844f5"
  agent_name: "qa-wei"
  thread_id: "019e78e8-037c-78c1-81e8-050ec8d844f5"
  spawned_at: "2026-05-30T20:42:15+08:00"
  resumed_at: ""
  completed_at: "2026-05-30T20:45:16+08:00"
  closed_at: "2026-05-30T20:49:47+08:00"
  evidence: "spawn_agent returned agent_id=019e78e8-037c-78c1-81e8-050ec8d844f5 nickname=qa-wei; close_agent previous_status returned completed CR019-S04 CP7 PASS"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-qa"
  workflow_id: "local_backtest-cr019"
  change_id: "CR-019"
  story_id: "CR019-S04-windows-gateway-lifecycle-deployment"
  wave_id: "CR019-W2-CS-TRANSPORT"
---

# META-QA CR-019 S04 CP7 Verification Handoff

## 任务

请以 `meta-qa` 身份验证 `CR019-S04-windows-gateway-lifecycle-deployment`。当前 Story 已完成 CP6，状态为 `ready-for-verification`。本轮只允许受控离线 / fixture / dry-run 合同验证，验证目标是确认 Windows gateway 生命周期、配置、部署边界和安全门控满足 Story、LLD、CP5 和 CP6 要求。

你不是独自在代码库中工作：当前仓库有多批未提交的 CR-015 / CR-016 / CR-017 / CR-018 / CR-019 产物。不要 revert 其他人的修改。QA 只允许写入本 Story 的 CP7 结果文件，除非发现阻断项需要在 CP7 中要求回修。

## 必读输入

| 类型 | 路径 |
|---|---|
| 项目规则 | `AGENTS.md` |
| 工作流状态 | `process/STATE.md` |
| Story 汇总 | `process/STORY-STATUS.md` |
| Story | `process/stories/CR019-S04-windows-gateway-lifecycle-deployment.md` |
| LLD | `process/stories/CR019-S04-windows-gateway-lifecycle-deployment-LLD.md` |
| CP5 auto | `process/checks/CP5-CR019-S04-windows-gateway-lifecycle-deployment-LLD-IMPLEMENTABILITY.md` |
| CP5 manual | `checkpoints/CP5-CR019-STAGE6-QMT-BRIDGE-BATCH-A-LLD-BATCH.md` |
| CP6 | `process/checks/CP6-CR019-S04-windows-gateway-lifecycle-deployment-CODING-DONE.md` |
| Dev handoff | `process/handoffs/META-DEV-CR019-S04-IMPLEMENT-2026-05-30.md` |
| Upstream S03 CP7 | `process/checks/CP7-CR019-S03-qmt-cside-client-cli-contract-VERIFICATION-DONE.md` |
| Gateway config module | `trading/qmt_gateway_config.py` |
| Gateway lifecycle module | `trading/qmt_gateway_service.py` |
| S04 tests | `tests/test_cr019_qmt_gateway_lifecycle.py` |
| S03 regression tests | `tests/test_cr019_qmt_cside_client_cli.py` |
| Gateway install doc | `docs/QMT-GATEWAY-INSTALL.md` |

## 写入范围

| 类型 | 路径 | 规则 |
|---|---|---|
| process | `process/checks/CP7-CR019-S04-windows-gateway-lifecycle-deployment-VERIFICATION-DONE.md` | 写入 CP7 验证完成检查结果。 |

禁止修改：源码、测试、docs、Story 卡片、`process/STATE.md`、`process/STORY-STATUS.md`、`process/DEVELOPMENT-PLAN.yaml`、`process/STORY-BACKLOG.md`、`pyproject.toml`、`uv.lock`、`.env`、凭据或 secret 值。

## 必须验证

1. gateway command、配置路径、bind、firewall、allowlist、heartbeat、redaction 字段覆盖率为 100%。
2. public exposure 默认 fail closed；public exposure allowed count 为 0。
3. `service_start_count`、`port_bind_count`、`qmt_api_call`、`dependency_change`、`credential_read` 全部为 0。
4. `trading/qmt_gateway_config.py`、`trading/qmt_gateway_service.py` 和 S04 测试不导入 `fastapi`、`uvicorn`、`requests`、`httpx`、`socket`、`urllib`、`subprocess`、`xtquant`、`xttrader`、`xtdata`。
5. 目标源码和文档不包含服务启动、端口绑定、HTTP client、socket、真实发单、撤单、账户查询、provider fetch、lake write、publish、simulation/live run 入口。
6. 安装文档只包含 `<windows-host>`、`<port>`、`<config-path>` 等占位符，不包含真实 host、真实路径、真实凭据或英文敏感字面量 `secret/token/account/password/.env`。
7. `O-CR019-S04-01` 作为非阻断 OPEN 保留：真实 FastAPI runtime 依赖、安装脚本和服务启动授权仍不在 S04 范围。
8. 未修改依赖文件，不读取 `.env`，不启动 FastAPI 服务，不绑定端口，不调用真实 QMT / MiniQMT / XtQuant / provider / lake / broker / publish / simulation / live。
9. CP7 结果必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、测试结果和真实操作计数。

## 必跑命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr019_qmt_gateway_lifecycle.py tests/test_cr019_qmt_cside_client_cli.py
```

建议额外运行：

```bash
PYTHONPYCACHEPREFIX=/tmp/cr019-s04-cp7-pycompile PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile trading/qmt_gateway_config.py trading/qmt_gateway_service.py tests/test_cr019_qmt_gateway_lifecycle.py
git diff --check -- trading/qmt_gateway_config.py trading/qmt_gateway_service.py tests/test_cr019_qmt_gateway_lifecycle.py docs/QMT-GATEWAY-INSTALL.md process/checks/CP6-CR019-S04-windows-gateway-lifecycle-deployment-CODING-DONE.md process/stories/CR019-S04-windows-gateway-lifecycle-deployment.md process/handoffs/META-DEV-CR019-S04-IMPLEMENT-2026-05-30.md
git diff --name-only -- pyproject.toml uv.lock .env
git status --short -- .pytest_cache tests/__pycache__ engine/__pycache__ trading/__pycache__
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -c "from trading.qmt_gateway_config import collect_gateway_safety_counters as c; print(c())"
rg -n "^(from|import) (fastapi|uvicorn|requests|httpx|socket|urllib|subprocess|xtquant|xttrader|xtdata)\b" trading/qmt_gateway_config.py trading/qmt_gateway_service.py tests/test_cr019_qmt_gateway_lifecycle.py
rg -n "\b(uvicorn\.|FastAPI\(|requests\.|httpx\.|socket\.|subprocess\.|os\.system|Popen\(|bind\(|listen\(|connect\(|place_order\(|cancel_order\(|query_account\(|publish\(|fetch\(|run_simulation\()" trading/qmt_gateway_config.py trading/qmt_gateway_service.py docs/QMT-GATEWAY-INSTALL.md
rg -n -i "secret|token|account|password|\.env" docs/QMT-GATEWAY-INSTALL.md
```

如果目标文件未被 Git 跟踪，需用等价 `git diff --check --no-index /dev/null <file>` 检查 whitespace，并在 CP7 中说明退出码 1 只是文件差异预期。

## 期望输出

`process/checks/CP7-CR019-S04-windows-gateway-lifecycle-deployment-VERIFICATION-DONE.md`

完成后请回复：

- CP7 文件路径与结论
- 实际执行的验证命令和结果
- 是否发现 BLOCKING / REQUIRED / OPEN 项
- forbidden operation counters 是否全部为 0
