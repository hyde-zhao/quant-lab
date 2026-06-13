---
checkpoint_id: "CP6"
checkpoint_name: "CR020-S06 文档、runbook 与手工实机验证手册编码完成检查"
type: "rolling_auto"
status: "PASS"
owner: "meta-dev"
created_at: "2026-06-05T09:09:18+08:00"
checked_at: "2026-06-05T09:09:18+08:00"
target:
  phase: "story-execution"
  change_id: "CR-020"
  story_id: "CR020-S06-docs-runbook-cp7-real-machine-validation"
  artifacts:
    - "docs/QMT-GATEWAY-INSTALL.md"
    - "docs/QMT-C-S-BRIDGE-RUNBOOK.md"
    - "tests/test_cr020_docs_runbook_no_authorization.py"
manual_checkpoint: "checkpoints/CP5-CR020-QMT-GATEWAY-READONLY-LLD-BATCH.md"
manual_windows_validation_required: true
docs_as_runtime_authorization_allowed: false
---

# CP6 CR020-S06 编码完成检查结果

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| CP5 全量 LLD 已通过 | PASS | `checkpoints/CP5-CR020-QMT-GATEWAY-READONLY-LLD-BATCH.md` | 用户批准实现 S01..S06。 |
| S01-S05 合同已实现 | PASS | CP6 S01..S05 | 文档消费 runtime admission、session、client、auth、query_positions 合同。 |
| 文档目标存在 | PASS | `docs/QMT-GATEWAY-INSTALL.md`、`docs/QMT-C-S-BRIDGE-RUNBOOK.md` | 在保留 CR019 历史边界基础上追加 CR020 手工手册。 |
| 禁止范围关闭 | PASS | 本文件 No-Real-Operation 声明 | 未读取真实 `.env`，未执行文档中的手工命令。 |

## Checklist

| # | 检查项 | 状态 | 证据 | 说明 |
|---|---|---|---|---|
| 1 | Windows S 端安装 / 配置 / 启动手册完整 | PASS | `docs/QMT-GATEWAY-INSTALL.md` §CR020 | 覆盖 uv、Typer、`.env`、MiniQMT 路径、server diagnostics、serve、health、停止与回滚。 |
| 2 | Linux C 端 CLI 验证手册完整 | PASS | `docs/QMT-C-S-BRIDGE-RUNBOOK.md` §9 | 覆盖 client diagnostics、query-positions、Python REST client 示例和 C/S 排障。 |
| 3 | 明确 CLI 与业务 runtime 分工 | PASS | Runbook §9.1 / §9.6 | CLI 用于手工验证；业务代码直接使用 `QmtClient` + REST transport。 |
| 4 | CP7 evidence schema 只覆盖 `query_positions` | PASS | 两个文档 CP7 schema 表 | endpoint=`query_positions`，scope=`qmt:positions:read`。 |
| 5 | no-authorization 表覆盖交易 / 写入 / simulation/live / provider/lake/publish / raw positions / credential output | PASS | 文档 no-authorization 表 + tests | 禁止项明确为 not-authorized。 |
| 6 | 真实凭据样例为 0 | PASS | `tests/test_cr020_docs_runbook_no_authorization.py` | 只允许 `<...>` placeholder、hash/ref、`[REDACTED]`。 |
| 7 | CR019 文档边界未破坏 | PASS | `tests/test_cr019_docs_runbook_boundary.py`、`tests/test_cr019_qmt_gateway_lifecycle.py` | 旧 runbook heading 和 no-real-operation 表仍通过。 |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 手工安装调试手册完成 | PASS | `docs/QMT-GATEWAY-INSTALL.md`、`docs/QMT-C-S-BRIDGE-RUNBOOK.md` | Windows / Linux 步骤均可读。 |
| 文档静态测试通过 | PASS | `tests/test_cr020_docs_runbook_no_authorization.py` | 覆盖章节、命令、scope、no-authorization、凭据占位、CP7 schema。 |
| 受影响旧测试通过 | PASS | `22 passed in 0.15s` | CR019 docs + gateway lifecycle tests。 |
| CR020 目标回归通过 | PASS | `75 passed in 0.33s` | 与 S05 一致。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| S 端安装手册 | `docs/QMT-GATEWAY-INSTALL.md` | PASS | CR020 Windows 手工安装、启动、排障、evidence。 |
| C/S runbook | `docs/QMT-C-S-BRIDGE-RUNBOOK.md` | PASS | Linux C 端 CLI 验证、Python REST client 调用、排障。 |
| 文档测试 | `tests/test_cr020_docs_runbook_no_authorization.py` | PASS | 静态扫描和边界断言。 |
| 兼容测试更新 | `tests/test_cr019_qmt_gateway_lifecycle.py` | PASS | 旧敏感字面量测试升级为真实值禁止、占位符允许。 |

## Verification Commands

| 命令 | 结果 |
|---|---|
| `uv run --python 3.11 pytest -q tests/test_cr020_docs_runbook_no_authorization.py tests/test_cr019_docs_runbook_boundary.py tests/test_cr019_qmt_gateway_lifecycle.py` | PASS：`22 passed in 0.15s` |
| `uv run --python 3.11 pytest -q tests/test_cr020_windows_gateway_runtime_admission.py tests/test_cr020_server_qmt_login_session.py tests/test_cr020_linux_client_rest_transport.py tests/test_cr020_hmac_pairing_allowlist_scope.py tests/test_cr020_query_positions_readonly.py tests/test_cr020_runtime_manual_validation.py tests/test_cr020_docs_runbook_no_authorization.py tests/test_cr019_qmt_gateway_lifecycle.py tests/test_cr019_docs_runbook_boundary.py` | PASS：`75 passed in 0.33s` |
| `rg -n "QMT_CLIENT_SECRET=|QMT_LOGIN_PASSWORD=|QMT_ACCOUNT_REF=|-----BEGIN|secret-fixture|account-fixture|000001\\.SZ|123456789012" docs/QMT-GATEWAY-INSTALL.md docs/QMT-C-S-BRIDGE-RUNBOOK.md .env.example trading/qmt_runtime.py trading/qmt_runtime_cli.py` | PASS：仅命中 `.env.example` 和文档占位符 |

## No-Real-Operation 声明

文档实现未执行其中任何 Windows / Linux 手工命令；未读取真实 `.env`，未启动 gateway，未绑定端口，未连接 QMT / MiniQMT / XtQuant，未执行真实查询，未输出凭据或 raw positions。

## Agent Dispatch Evidence

| 字段 | 值 |
|---|---|
| role | `meta-dev` |
| dispatch_mode | `meta-po orchestrated main-thread docs implementation` |
| cp5_manual_checkpoint | `checkpoints/CP5-CR020-QMT-GATEWAY-READONLY-LLD-BATCH.md` |
| cp6_path | `process/checks/CP6-CR020-S06-docs-runbook-cp7-real-machine-validation-CODING-DONE.md` |

## 结论

`PASS`。S06 文档、runbook 和静态测试完成。真实 Windows 运行和 QMT 查询验证仍等待用户手工执行后提交脱敏 evidence。
