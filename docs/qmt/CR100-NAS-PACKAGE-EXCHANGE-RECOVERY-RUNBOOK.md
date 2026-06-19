# CR100 NAS Package Exchange Recovery Runbook

## 目的

当真实 NAS 恢复且用户另行授权后，按本 runbook 验证 package exchange 链路。本文件不是执行授权，也不包含真实 NAS 路径、凭据、账号或账户信息。

## 前置授权

执行任何真实 NAS 步骤前，必须另起独立 gate 并明确：

- 授权范围：只读 preflight、publish、pull、copy 或校验中的哪一项。
- 执行主机：research_pc / trading_pc / 其他。
- 路径来源：由用户手工提供，不从 `.env` 或凭据文件读取。
- 证据格式：只记录脱敏摘要、hash pass/fail、计数和状态。

## 人工验证步骤

| 步骤 | 动作 | 通过条件 | 禁止项 |
|---|---|---|---|
| 1 | 用户确认 NAS 已恢复并提供授权范围 | 有单独 gate 记录 | 不自动探测 NAS |
| 2 | 在本地重新运行 CR100 fake fixture 回归 | 聚焦测试 PASS | 不读取真实 NAS |
| 3 | 对真实 package root 做 manifest/hash 本地检查 | `check-package` PASS | 不读取凭据 |
| 4 | 若授权 publish，在用户指定 NAS exchange root 执行受控 publish | 只写 approved package 和 index | 不覆盖 active、不删除旧包 |
| 5 | 若授权 pull，在 trading_pc 指定 cache 执行受控 pull | hash pass 后写本地 immutable cache | 不启动 QMT runtime |
| 6 | 记录脱敏 evidence | 只含 package_id、version、hash_status、counts、status | 不保存账户 / 日志原文 |

## 真实验证证据 Schema

```yaml
schema_version: cr100-real-nas-validation-evidence-v1
run_id: ""
authorization_gate: ""
package_id: ""
package_version: ""
nas_connectivity_status: unknown|pass|blocked|fail
publish_status: not_authorized|not_run|pass|blocked|fail
pull_status: not_authorized|not_run|pass|blocked|fail
hash_status: not_run|pass|fail
redaction_status: pass|fail
counts:
  packages_checked: 0
  packages_published: 0
  packages_pulled: 0
forbidden_operation_counters:
  credential_read: 0
  runtime_start: 0
  trade_write: 0
raw_paths_included: false
raw_account_data_included: false
```

## 回退

- publish 失败：不更新 approved index；保留旧 index。
- pull 失败：不更新 active pointer。
- hash mismatch：package 进入 quarantine 或 blocked 记录，不能启用。
- 权限不清：停止执行并回到人工 gate。
