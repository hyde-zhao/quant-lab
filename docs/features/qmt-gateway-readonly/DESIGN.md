---
status: "draft-current-index"
version: "1.0"
feature_id: "FEAT-05"
source_matrix: "docs/design/FEATURE-DESIGN-MATRIX.md"
source_blueprint: "docs/design/BLUEPRINT.md"
change: "CR-031"
---

# Feature Design: qmt-gateway-readonly

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-07 | meta-po | 新增 QMT C/S Gateway 与只读运行准入 Feature 设计索引 |

## Feature 摘要

| 项 | 内容 |
|---|---|
| Feature 目标 | 支持 Linux C 侧 client / CLI 通过受控 REST 调用 Windows S 侧 QMT gateway，并在 CR-020 范围内完成 `query_positions` 只读准入验证 |
| Owner | FEAT-05 |
| 主要代码面 | `trading/qmt_client*.py`、`trading/qmt_gateway*.py`、`trading/qmt_auth.py`、`trading/qmt_redaction.py` |
| 主要设计来源 | `process/HLD.md` §33/§36、`process/HLD-QMT-TRADING.md`、ADR-067..073、ADR-087..093 |
| 当前状态 | fixture/static verified，等待用户 MiniQMT 权限后的手工只读实机验证 |
| 非授权声明 | 不授权交易、撤单、账户写入、simulation/live、provider/lake/publish 或凭据输出 |

## Feature 边界与相邻对象

| 对象 | 本 Feature 负责 | 不负责 | 相邻 Feature / 模块 |
|---|---|---|---|
| Linux C 侧 client / CLI | pairing、diagnostics、smoke、query_positions 调用封装 | xtquant direct import | FEAT-07 |
| Windows S 侧 gateway | lifecycle、bind、redaction、login/session ready、endpoint matrix | OMS / stage gate 下单 | FEAT-06 |
| Pairing / HMAC | token、scope、nonce、timestamp、allowlist | 替代 run mode / risk gate | FEAT-07 |
| QueryPositionsResult | 只读 positions 查询合同和脱敏 evidence | live_readonly 全量账户准入 | FEAT-06 / FEAT-08 |

## 输入 / 输出契约

| 方向 | 契约 |
|---|---|
| 输入 | local untracked `.env` credential refs、gateway config、pairing token、HMAC headers、scope `qmt:positions:read` |
| 输出 | health / diagnostics / capabilities / login session status / query_positions readonly result / blocked reason |
| 错误输出 | `credential_missing`、`miniqmt_permission_missing`、`session_not_ready`、`scope_denied`、`nonce_replay`、`query_blocked` |

## 失败路径

| 失败点 | 行为 |
|---|---|
| 用户无 MiniQMT 权限 | CR-020 保持 manual validation pending，不继续排查凭据或 session |
| HMAC / scope / nonce 失败 | fail-closed，不触达 QMT query |
| gateway health pass 但 login 未 ready | capabilities 可见但 query blocked |
| query_positions 失败 | 记录脱敏 blocked reason，不升级 live_readonly |

## Gotchas

- C 侧不得导入 xtquant。
- `query_positions` 只读通过不等于 simulation、live_readonly 或 small_live 授权。
- `.env` 只允许本地未跟踪真实值，文档、日志、memory、检查点只能记录脱敏引用。

