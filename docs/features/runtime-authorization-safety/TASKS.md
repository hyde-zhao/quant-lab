---
status: "draft-current-index"
version: "1.0"
feature_id: "FEAT-07"
---

# Feature Tasks: runtime-authorization-safety

| Task ID | 任务 | 输入 | 输出 | 文件范围 | 验证 |
|---|---|---|---|---|---|
| FEAT-07-T01 | 维护授权语义表 | CP / CR / runbook | authorization meaning matrix | docs / process checks | docs guardrail |
| FEAT-07-T02 | 维护 no-real-operation counters | high-risk CR | safety counters | tests / reports / docs | no-real-op tests |
| FEAT-07-T03 | 维护凭据脱敏策略 | `.env.example` / credential_ref | redaction policy | `trading/qmt_redaction.py`、docs | redaction tests |
| FEAT-07-T04 | 维护 HMAC / scope / nonce guardrail | gateway scope | fail-closed auth | `trading/qmt_auth.py` | auth tests |
| FEAT-07-T05 | 维护禁止依赖扫描 | dependency map | forbidden import checks | tests / scripts | boundary tests |

## 后续触发条件

- 用户恢复 CR-020 真实只读验证。
- 启动 CR-021..024。
- 新增 provider、lake write、publish、gateway endpoint、account query、simulation/live 能力。

