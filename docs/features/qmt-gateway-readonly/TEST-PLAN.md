---
status: "draft-current-index"
version: "1.0"
feature_id: "FEAT-05"
---

# Feature Test Plan: qmt-gateway-readonly

## 测试矩阵

| 测试域 | 关键场景 | 验证入口 |
|---|---|---|
| Windows gateway runtime | bind / run mode / no public default / diagnostics | `tests/test_cr020_windows_gateway_runtime_admission.py` |
| QMT login/session | session ready gate、credential_ref 脱敏 | `tests/test_cr020_server_qmt_login_session.py` |
| Linux REST client | C 侧不导入 xtquant，REST transport typed error | `tests/test_cr020_linux_client_rest_transport.py` |
| HMAC / allowlist / scope | nonce、timestamp、scope fail-closed | `tests/test_cr020_hmac_pairing_allowlist_scope.py` |
| query_positions readonly | 只读结果、blocked reason、no order | `tests/test_cr020_query_positions_readonly.py` |
| 文档不授权 | runbook 不授权真实交易 / simulation / live | `tests/test_cr020_docs_runbook_no_authorization.py` |
| 手工验证边界 | fixture/static pass 不等于实机 pass | `tests/test_cr020_runtime_manual_validation.py` |

## 手工验证

| 场景 | 证据要求 |
|---|---|
| Windows S 端 diagnostics | 脱敏命令输出，不能包含账户、密码、token、session、私有路径 |
| Linux C 端 query_positions | 脱敏 positions summary 或 blocked reason |
| 权限不足 | 记录 MiniQMT 权限缺失，不继续尝试真实查询 |

