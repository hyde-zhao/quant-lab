---
status: "draft-current-index"
version: "1.0"
feature_id: "FEAT-07"
---

# Feature Test Plan: runtime-authorization-safety

## 测试矩阵

| 测试域 | 关键场景 | 验证入口 |
|---|---|---|
| no-real-operation | 未授权时 provider/lake/publish/QMT/broker/credential 计数为 0 | `tests/test_cr025_no_real_operation_safety.py`、`tests/test_cr030_no_real_operation_safety.py`、CR020 tests |
| HMAC / scope | timestamp、nonce、scope、allowlist fail-closed | `tests/test_cr019_qmt_pairing_hmac_auth.py`、`tests/test_cr020_hmac_pairing_allowlist_scope.py` |
| redaction | 日志 / docs / evidence 不含 token、账户、密码、session、私有路径 | QMT redaction tests / docs tests |
| forbidden dependency | C 侧不导入 xtquant，consumer 不导入 provider/runtime | CR019 / CR020 / CR010 consumer boundary tests |
| docs authorization guardrail | README / runbook 不把 verified 写成真实授权 | `tests/test_cr020_docs_runbook_no_authorization.py`、CR016 docs tests |
| stage / runtime gate | health / capabilities / CP pass 不升级权限 | CR019 run gate tests、CR020 runtime tests |

## 手工验证

| 场景 | 证据要求 |
|---|---|
| 用户提交真实运行 evidence | 必须脱敏；只接受摘要、计数、scope、blocked reason，不接受凭据原文 |
| 恢复 CR-020 | 必须重新确认 MiniQMT 权限、只读 scope 和不授权交易项 |

