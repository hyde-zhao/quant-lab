---
status: "draft-current-index"
version: "1.0"
feature_id: "FEAT-05"
---

# Feature Tasks: qmt-gateway-readonly

| Task ID | 任务 | 输入 | 输出 | 文件范围 | 验证 |
|---|---|---|---|---|---|
| FEAT-05-T01 | 维护 gateway runtime admission | CR-020 HLD / LLD | run mode / bind / diagnostics 合同 | `trading/qmt_gateway_*` | runtime tests |
| FEAT-05-T02 | 维护 QMT login/session gate | credential_ref / session policy | session ready / blocked reason | `trading/qmt_gateway_session.py` | session tests |
| FEAT-05-T03 | 维护 C 侧 REST client / CLI | endpoint matrix | typed client / diagnostics | `trading/qmt_client*.py` | client tests |
| FEAT-05-T04 | 维护 HMAC / scope / redaction | auth policy | fail-closed auth | `trading/qmt_auth.py`、`trading/qmt_redaction.py` | auth tests |
| FEAT-05-T05 | 维护 query_positions readonly | MiniQMT permission / scope | readonly result / blocked reason | `trading/qmt_gateway_service.py` | query tests |

## 后续触发条件

- 用户完成 MiniQMT 权限申请并恢复 CR-020 实机验证。
- 新增只读 endpoint 或扩大 endpoint matrix。
- 将 gateway 从 readonly 扩展到 simulation / live 路线。

