---
checkpoint_id: "CP6"
checkpoint_name: "CR020-S05 query_positions 单接口只读准入编码完成检查"
type: "rolling_auto"
status: "PASS"
owner: "meta-dev"
created_at: "2026-06-05T09:09:18+08:00"
checked_at: "2026-06-05T09:09:18+08:00"
target:
  phase: "story-execution"
  change_id: "CR-020"
  story_id: "CR020-S05-query-positions-readonly"
  artifacts:
    - "trading/qmt_endpoint_matrix.py"
    - "trading/qmt_gateway_contracts.py"
    - "trading/qmt_gateway_service.py"
    - "trading/qmt_client.py"
    - "trading/qmt_runtime.py"
    - "trading/qmt_runtime_cli.py"
    - "tests/test_cr020_query_positions_readonly.py"
    - "tests/test_cr020_runtime_manual_validation.py"
manual_checkpoint: "checkpoints/CP5-CR020-QMT-GATEWAY-READONLY-LLD-BATCH.md"
real_env_read_allowed: false
gateway_start_allowed_by_agent: false
qmt_operation_allowed_by_agent: false
manual_windows_validation_required: true
---

# CP6 CR020-S05 编码完成检查结果

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| CP5 全量 LLD 已通过 | PASS | `checkpoints/CP5-CR020-QMT-GATEWAY-READONLY-LLD-BATCH.md` status=`approved` | 用户已批准 S01..S06 实现；仍不授权 agent 真实运行。 |
| S02/S03/S04 依赖已完成 CP6 | PASS | `process/checks/CP6-CR020-S02-*`、`S03-*`、`S04-*` | S05 消费 session ready、REST client、HMAC/scope/redaction 合同。 |
| 当前 LLD 已确认 | PASS | `process/stories/CR020-S05-query-positions-readonly-LLD.md` frontmatter `confirmed=true` | LLD 作为实现强输入。 |
| 禁止范围关闭 | PASS | 本文件 No-Real-Operation 声明 | 未读取真实 `.env`，未启动 gateway，未绑定端口，未连接 QMT / MiniQMT / XtQuant。 |

## Checklist

| # | 检查项 | 状态 | 证据 | 说明 |
|---|---|---|---|---|
| 1 | endpoint overlay 只允许 `query_positions` + `qmt:positions:read` | PASS | `get_cr020_query_positions_spec()`、`is_cr020_readonly_endpoint_allowed()` | 其他 account/orders/live/simulation endpoint 均 blocked。 |
| 2 | `query_positions` request / redacted payload / safety counters 合同完成 | PASS | `QmtQueryPositionsRequest`、`QmtQueryPositionsPayload`、`collect_query_positions_safety_counters()` | raw positions 不进入 public payload。 |
| 3 | gateway dispatcher 串联 endpoint/auth/session/redaction/adapter gate | PASS | `dispatch_qmt_gateway_endpoint()`、`handle_query_positions()` | 任一 gate fail 时 adapter 不被调用。 |
| 4 | 成功路径只返回脱敏摘要 | PASS | `redact_query_positions_payload()` + S05 tests | 输出 count/digest/ref/bucket，不输出账号、证券代码、精确数量或市值。 |
| 5 | C 端 REST request body 与 HMAC provider 对齐 | PASS | `QmtRestRequest.body`、`QmtHmacHeaderProvider` dataclass request support | 真实 runtime transport 和 S 端 HMAC 校验使用同一 body bytes。 |
| 6 | 手工 runtime 模块具备 Windows S 端 server 和 Linux C 端 HTTP transport | PASS | `trading/qmt_runtime.py`、`trading/qmt_runtime_cli.py` | runtime 模块仅在用户显式 CLI 调用时读取 `.env` / 启动 server / 懒加载 XtQuant。 |
| 7 | fixture runtime 验证覆盖 fake XtQuant 全链路 | PASS | `tests/test_cr020_runtime_manual_validation.py` | fake adapter 登录、HMAC、allowlist、query_positions、redaction 通过。 |
| 8 | 不修改依赖 | PASS | `git diff --check` 和 scoped status | 未修改 `pyproject.toml` / `uv.lock`；Typer 通过 `uv run --with typer` 手工注入。 |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| S05 代码产物存在 | PASS | `trading/qmt_endpoint_matrix.py`、`qmt_gateway_contracts.py`、`qmt_gateway_service.py`、`qmt_runtime.py`、`qmt_runtime_cli.py` | 查询准入和手工 runtime 已落地。 |
| S05 专项测试通过 | PASS | `tests/test_cr020_query_positions_readonly.py` | `5 passed in 0.06s`。 |
| runtime fixture 测试通过 | PASS | `tests/test_cr020_runtime_manual_validation.py` | 覆盖 fake XtQuant 与 stdlib HTTP transport normalization。 |
| CR020 目标回归通过 | PASS | `75 passed in 0.33s` | 含 S01-S06 及 CR019 受影响边界测试。 |
| 语法检查通过 | PASS | `py_compile` | 退出码 0。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| endpoint overlay | `trading/qmt_endpoint_matrix.py` | PASS | CR020 readonly matrix。 |
| query_positions 合同 | `trading/qmt_gateway_contracts.py` | PASS | request / payload / redaction / counters / result builder。 |
| gateway dispatcher | `trading/qmt_gateway_service.py` | PASS | gate chain 和 adapter protocol。 |
| C 端 body/HMAC 兼容 | `trading/qmt_client.py`、`trading/qmt_auth.py` | PASS | REST body bytes 和 dataclass request HMAC。 |
| 手工 runtime | `trading/qmt_runtime.py`、`trading/qmt_runtime_cli.py` | PASS | Windows S 端 serve、Linux C 端 query CLI。 |
| 测试 | `tests/test_cr020_query_positions_readonly.py`、`tests/test_cr020_runtime_manual_validation.py` | PASS | fixture-only，不连接真实 QMT。 |

## Verification Commands

| 命令 | 结果 |
|---|---|
| `uv run --python 3.11 pytest -q tests/test_cr020_query_positions_readonly.py tests/test_cr020_runtime_manual_validation.py` | PASS：`9 passed in 0.11s` |
| `uv run --python 3.11 pytest -q tests/test_cr020_windows_gateway_runtime_admission.py tests/test_cr020_server_qmt_login_session.py tests/test_cr020_linux_client_rest_transport.py tests/test_cr020_hmac_pairing_allowlist_scope.py tests/test_cr020_query_positions_readonly.py tests/test_cr020_runtime_manual_validation.py tests/test_cr020_docs_runbook_no_authorization.py tests/test_cr019_qmt_gateway_lifecycle.py tests/test_cr019_docs_runbook_boundary.py` | PASS：`75 passed in 0.33s` |
| `uv run --python 3.11 python -m py_compile trading/qmt_gateway_contracts.py trading/qmt_endpoint_matrix.py trading/qmt_gateway_service.py trading/qmt_client.py trading/qmt_auth.py trading/qmt_runtime.py trading/qmt_runtime_cli.py tests/test_cr020_query_positions_readonly.py tests/test_cr020_runtime_manual_validation.py tests/test_cr020_docs_runbook_no_authorization.py` | PASS：退出码 0 |
| `git diff --check -- <CR020 target files>` | PASS：退出码 0 |

## No-Real-Operation 声明

本轮未读取真实 `.env` / `.env.*`，未启动 Windows gateway，未绑定端口，未打开真实 socket，未连接 QMT / MiniQMT / XtQuant，未执行真实 `query_positions`，未输出真实凭据或 raw positions，未发单 / 撤单 / 改单 / 账户写入，未 provider/lake/publish/simulation/live。

## Agent Dispatch Evidence

| 字段 | 值 |
|---|---|
| role | `meta-dev` |
| dispatch_mode | `meta-po orchestrated main-thread integration after parallel S01-S04 agents` |
| upstream_agents | `dev-yang` S01/S02、`dev-zhang` S03、`dev-you` S04 |
| cp5_manual_checkpoint | `checkpoints/CP5-CR020-QMT-GATEWAY-READONLY-LLD-BATCH.md` |
| cp6_path | `process/checks/CP6-CR020-S05-query-positions-readonly-CODING-DONE.md` |

## 结论

`PASS`。S05 代码完成并通过 fixture/static 验证。Windows 实机安装、S 端启动、QMT 登录和真实 `query_positions` 调用仍按用户要求由用户手工执行，不能由本 CP6 记录代替。
