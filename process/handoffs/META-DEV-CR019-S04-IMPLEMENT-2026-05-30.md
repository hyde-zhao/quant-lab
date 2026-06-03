---
handoff_id: "META-DEV-CR019-S04-IMPLEMENT-2026-05-30"
from_agent: "meta-po"
to_agent: "meta-dev"
workflow_id: "local_backtest-cr019"
change_id: "CR-019"
phase: "story-execution"
created_at: "2026-05-30T20:23:50+08:00"
status: "completed-closed"
dispatch:
  required: true
  semantic: "stage-dispatch"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".agents/agents/meta-dev.md"
  tool_name: "multi_agent_v1.spawn_agent / multi_agent_v1.close_agent"
  agent_id: "019e78d8-0980-7af0-83a0-5c0b4aaa8d74"
  agent_name: "dev-lv"
  thread_id: "019e78d8-0980-7af0-83a0-5c0b4aaa8d74"
  spawned_at: "2026-05-30T20:24:51+08:00"
  resumed_at: ""
  completed_at: "2026-05-30T20:32:44+08:00"
  closed_at: "2026-05-30T20:37:15+08:00"
  evidence: "spawn_agent returned agent_id=019e78d8-0980-7af0-83a0-5c0b4aaa8d74 nickname=dev-lv; close_agent previous_status returned completed S04 implementation with CP6 PASS"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-dev"
  workflow_id: "local_backtest-cr019"
  change_id: "CR-019"
  story_id: "CR019-S04-windows-gateway-lifecycle-deployment"
  wave_id: "CR019-W2-CS-TRANSPORT"
---

# META-DEV CR-019 S04 Implementation Handoff

## 任务

请以 `meta-dev` 身份实现 `CR019-S04-windows-gateway-lifecycle-deployment`。当前 CR019-S03 已通过 CP6 / CP7 并收敛为 `verified`，S04 Story 卡片为 `dev-ready`。本次只允许受控离线 / fixture / dry-run 合同实现，目标是冻结 Windows QMT gateway 生命周期、配置、命令、heartbeat、部署边界和文档说明。

本 Story 的 “FastAPI gateway” 只表示未来 S 侧服务形态；当前实现不得启动 FastAPI、不得安装依赖、不得绑定真实端口、不得访问 Windows 节点或真实 QMT。

## 必读输入

| 文件 | 用途 |
|---|---|
| `AGENTS.md` | CP6 / CP7 门控、真实子 agent 证据、禁止真实操作边界 |
| `process/STATE.md` | 当前 CR-019、S04 dev-ready、真实操作禁止范围 |
| `process/STORY-STATUS.md` | S04 dev-ready 与后续 Story gate |
| `checkpoints/CP5-CR019-STAGE6-QMT-BRIDGE-BATCH-A-LLD-BATCH.md` | CP5 approved 决策与 DQ-01..DQ-07 |
| `process/stories/CR019-S04-windows-gateway-lifecycle-deployment.md` | Story 卡片、文件 owner、dev_gate |
| `process/stories/CR019-S04-windows-gateway-lifecycle-deployment-LLD.md` | S04 approved LLD，必须按第 4 / 6 / 10 / 11 / 14 节实现 |
| `process/checks/CP7-CR019-S03-qmt-cside-client-cli-contract-VERIFICATION-DONE.md` | S03 client / CLI / REST transport contract verified 证据 |
| `trading/qmt_client.py` | 只读参考 C 侧 endpoint / blocked result 合同，不得复制业务逻辑 |
| `trading/qmt_transport.py` | 只读参考 REST gateway transport metadata 合同 |

## 允许写入范围

| 类型 | 路径 |
|---|---|
| 创建 | `trading/qmt_gateway_config.py` |
| 创建 | `trading/qmt_gateway_service.py` |
| 创建 | `tests/test_cr019_qmt_gateway_lifecycle.py` |
| 创建 | `docs/QMT-GATEWAY-INSTALL.md` |
| 创建 | `process/checks/CP6-CR019-S04-windows-gateway-lifecycle-deployment-CODING-DONE.md` |
| 可修改 | `process/stories/CR019-S04-windows-gateway-lifecycle-deployment.md`，仅允许将状态推进到 `ready-for-verification` 并记录 CP6 证据 |

## 禁止事项

- 不得修改 `pyproject.toml`、`uv.lock`、`.env` 或任何凭据文件。
- 不得安装依赖、不得导入或依赖 FastAPI / uvicorn / requests / httpx / socket runtime。
- 不得启动服务、绑定真实端口、打开 socket、执行 subprocess 或系统服务命令。
- 不得读取 Windows credential、`.env`、token、secret、cookie、session、私钥、账户号或交易密码。
- 不得调用 QMT / MiniQMT / XtQuant、不得发单、撤单、查询真实账户。
- 不得执行 provider fetch、lake write、broker lake write、publish、current pointer publish、simulation/live run。
- 不得修改 HLD、ADR、REQUIREMENTS、STORY-BACKLOG、DEVELOPMENT-PLAN、STATE、STORY-STATUS 或 CR019-S05..S10 Story。
- 不得实现 S05 pairing/HMAC secret lifecycle；S04 只保留 auth mode / header slot 引用。

## 实现要求

1. 创建 `trading/qmt_gateway_config.py`，至少覆盖：
   - `GatewayBindConfig`
   - `GatewayFirewallPolicy`
   - `GatewayAllowlist`
   - `HeartbeatPolicy`
   - `RedactionPolicy`
   - `GatewayConfig`
   - `GatewayConfigValidation`
   - `GatewaySafetyCounters`
   - `build_gateway_config`
   - `validate_gateway_security`
   - `collect_gateway_safety_counters`
2. 创建 `trading/qmt_gateway_service.py`，至少覆盖：
   - `GatewayCommandSpec`
   - `GatewayLifecycleState`
   - `GatewayLifecyclePlan`
   - `GatewayHealthSummary`
   - `build_gateway_command_spec`
   - `plan_gateway_lifecycle`
   - `build_heartbeat_summary`
   - `service_start_forbidden` / start guard，不执行命令
3. 创建 `tests/test_cr019_qmt_gateway_lifecycle.py`，至少覆盖：
   - gateway command、配置路径、bind、firewall、allowlist、heartbeat、redaction 字段覆盖率 100%
   - `0.0.0.0` / public exposure 默认 blocked，`public_exposure_allowed_count=0`
   - allowlist 空、firewall disabled、redaction 缺字段均 fail closed
   - 请求 start transition 返回 `service_start_forbidden`，`service_start_count=0`、`port_bind_count=0`
   - heartbeat unhealthy 返回 fail-closed reason，`qmt_api_call=0`
   - 文档无 secret/token/account/password/.env，使用 `<windows-host>`、`<port>`、`<config-path>` 等占位符
   - dependency_change、credential_read、qmt_api_call、real_order、real_cancel、account_query、provider_fetch、lake_write、publish、simulation_or_live_run 均为 0
4. 创建 `docs/QMT-GATEWAY-INSTALL.md`，只写安装 / 运行边界、命令结构、配置字段、禁止真实凭据和禁止启动声明；不得包含真实 host、secret、账户或私有路径。
5. 创建 CP6 自动检查结果 `process/checks/CP6-CR019-S04-windows-gateway-lifecycle-deployment-CODING-DONE.md`，必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、Validation Results、Forbidden Operation Counters 和写入范围复核。

## 建议验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr019_qmt_gateway_lifecycle.py tests/test_cr019_qmt_cside_client_cli.py
```

可追加：

```bash
PYTHONPYCACHEPREFIX=/tmp/cr019-s04-pycompile PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile trading/qmt_gateway_config.py trading/qmt_gateway_service.py tests/test_cr019_qmt_gateway_lifecycle.py
git diff --check -- trading/qmt_gateway_config.py trading/qmt_gateway_service.py tests/test_cr019_qmt_gateway_lifecycle.py docs/QMT-GATEWAY-INSTALL.md process/checks/CP6-CR019-S04-windows-gateway-lifecycle-deployment-CODING-DONE.md process/stories/CR019-S04-windows-gateway-lifecycle-deployment.md
git diff --name-only -- pyproject.toml uv.lock .env
git status --short -- .pytest_cache tests/__pycache__ engine/__pycache__ trading/__pycache__
```

如果目标文件未被 Git 跟踪，需用等价 `git diff --check --no-index /dev/null <file>` 检查 whitespace，并在 CP6 中说明退出码 1 只是文件差异预期。

## 完成后回复

请列出：

- 修改文件清单
- CP6 文件路径与结论
- 实际执行的验证命令和结果
- 是否触发任何 forbidden 操作，预期应为 0
- 是否存在 BLOCKING / OPEN 项；`O-CR019-S04-01` 是已知非阻断 OPEN，必须继续保留说明
