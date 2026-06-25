# 场景案例：日常运维

本案例面向日常值守人员，覆盖盘前、盘中、盘后和异常恢复。它默认只处理 simulation 运行，不进入 `small_live` 或 `live`。

## 大步骤 1：盘前检查

### 1.1 文档和授权检查

小步骤：

1. 打开 [../README.md](../README.md) 的当前 QMT 模拟盘入口。
2. 阅读 [../USER-MANUAL.md](../USER-MANUAL.md) 的 runner 手动运行指南。
3. 确认本次 `<runtime-authorization-ref>` 有效。
4. 确认当天不包含 `small_live` 或 `live`。

检查：

| 检查项 | 通过标准 |
|---|---|
| 授权 | scope、时间、操作者、run id、回滚计划齐全。 |
| 环境 | Windows S 端和 WSL C 端 env 文件存在于用户私有路径。 |
| 禁止项 | 未脱敏日志、未知 endpoint、live 相关动作均禁止。 |

### 1.2 gateway 预检查

小步骤：

1. Windows 端打开 MiniQMT。
2. 运行 `server-diagnostics`。
3. 运行 `serve`。
4. C 端检查 health、capabilities、positions。

检查：

| 检查项 | 通过标准 |
|---|---|
| runtime identity | mode / account_kind / profile 均匹配 simulation。 |
| session | 未过期。 |
| redaction | positions 不输出 raw payload。 |

## 大步骤 2：盘中运行

### 2.1 运行 runner

小步骤：

1. 准备 `<private-spec-json>`。
2. 执行 simulation operator。
3. 记录 stdout。
4. 打开 evidence 摘要。

检查：

| 检查项 | 通过标准 |
|---|---|
| P1 | 目标组合已生成或明确 blocked。 |
| P2 | 订单计划和风险检查通过。 |
| P3 | submit/cancel 结果明确。 |
| P4 | 对账通过。 |

### 2.2 运行期间观察

小步骤：

1. 只观察 health / capabilities / redacted positions。
2. 不打开未知 endpoint。
3. 不手动补发非 runner 订单。

检查：

| 检查项 | 通过标准 |
|---|---|
| unknown_count | 为 0。 |
| manual action | 若发生，必须记录 takeover。 |
| evidence | 只保存脱敏 refs。 |

## 大步骤 3：盘后检查

### 3.1 日终撤未成和持仓核对

小步骤：

1. 查看 MiniQMT 未成订单。
2. 核对持仓变化和 runner evidence。
3. 确认撤单或未成交状态。
4. 记录日终摘要。

检查：

| 检查项 | 通过标准 |
|---|---|
| 未成订单 | 无未知遗留；若存在，进入 manual takeover。 |
| 持仓 | post positions digest 与对账摘要一致。 |
| 资金 | 不保存 fund detail，只记录脱敏状态。 |

### 3.2 停止 gateway

小步骤：

1. 在 Windows `serve` 终端按 `Ctrl+C`。
2. 确认 `/qmt/health` 不可达。
3. 归档脱敏 evidence refs。

检查：

| 检查项 | 通过标准 |
|---|---|
| gateway | 已停止。 |
| evidence | 只包含 digest、bucket、ref、counts。 |
| 下一次运行 | 必须重新授权或确认授权仍有效。 |

## 大步骤 4：异常恢复

| 异常 | 小步骤 | 恢复检查 |
|---|---|---|
| `session_expired` | 停止 runner；重启 gateway；重新做 positions 只读检查。 | session fresh，positions redaction pass。 |
| risk blocked | 不提交订单；修正 spec 或资金上限。 | P2 risk pass。 |
| cancel blocked | 停止新运行；人工核对 / 撤单。 | 未解决订单为 0。 |
| recon diff | manual takeover；记录差异和处理人。 | reconciliation pass。 |
| gateway unavailable | 停止 operator；检查 Windows 端进程。 | health / capabilities 恢复。 |
