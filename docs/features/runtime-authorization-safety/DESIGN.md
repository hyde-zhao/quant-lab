---
status: "draft-current-index"
version: "1.0"
feature_id: "FEAT-07"
source_matrix: "docs/design/FEATURE-DESIGN-MATRIX.md"
source_blueprint: "docs/design/BLUEPRINT.md"
change: "CR-031"
---

# Feature Design: runtime-authorization-safety

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-07 | meta-po | 新增运行授权与 no-real-operation 安全治理 Feature 设计索引 |

## Feature 摘要

| 项 | 内容 |
|---|---|
| Feature 目标 | 统一真实 provider、lake、publish、gateway、QMT、broker、凭据和账户操作的授权语义、脱敏规则、禁止依赖和 no-real-operation 证据 |
| Owner | FEAT-07 |
| 主要代码 / 文档面 | `trading/qmt_auth.py`、`trading/qmt_redaction.py`、safety tests、README、USER-MANUAL、QMT runbooks、CP launch messages |
| 主要设计来源 | `docs/design/BLUEPRINT.md`、`DEPENDENCY-MAP.md`、所有高风险 CR 的人工作业门禁 |
| 非授权声明 | 本 Feature 是安全治理入口，本身也不授权任何真实操作 |

## 安全边界

| 操作类别 | 默认状态 | 解除条件 |
|---|---|---|
| provider fetch | 0 / blocked | 明确 CR、CP5、source/interface allowlist、authorization_id |
| lake write | 0 / blocked | 明确 lake root、dataset、date range、run id、authorization_id |
| catalog publish | 0 / blocked | quality/readiness policy、publish gate、approver |
| gateway start / port bind | blocked unless scoped | CR-020 或后续 CR 明确 runtime authorization |
| QMT API call | 0 / blocked | endpoint scope、run mode、stage gate、authorization_id |
| account query | 0 / blocked | readonly scope、MiniQMT permission、query-specific authorization |
| real order / cancel | 0 / blocked | CR-021..024 对应 stage gate + per-run authorization |
| credential read | 0 / blocked | 本地未跟踪 `.env`，只记录 `credential_ref` |

## 授权语义

| 事件 | 不代表 |
|---|---|
| CP2 / CP3 approve | 不代表实现授权或真实运行授权 |
| CP5 approve | 不代表真实运行授权，除非 Decision Brief 显式包含 runtime_authorization |
| CP6 / CP7 PASS | 不代表真实操作已执行或可执行 |
| CP8 approve / closed | 不代表后续 CR 自动授权 |
| README / Runbook 存在 | 不代表用户已经授权执行 |
| gateway health / capabilities pass | 不代表 simulation/live/account/order/cancel 权限 |
| StrategyAdmissionPackage pass | 不代表 QMT-ready 或 trade-ready |

## 失败路径

| 失败点 | 行为 |
|---|---|
| 授权缺失或 scope 不匹配 | fail-closed，输出 blocked reason |
| 日志包含敏感值 | blocker；停止推进，清理日志，轮转凭据 |
| no-real-op counter 非 0 且无授权 | blocker；不得关闭 gate |
| 文档弱化不授权项 | docs guardrail FAIL |

## Gotchas

- “只读”仍然可能触达真实账户信息，必须受 scope、redaction 和 evidence 边界控制。
- `approve` 只接受当前门禁的推荐方案，不是对未来真实操作的永久授权。
- 任何真实 `.env` 内容不得进入 memory、对话、docs、checks、reports 或 git。

