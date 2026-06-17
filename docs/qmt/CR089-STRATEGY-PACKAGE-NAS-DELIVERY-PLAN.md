---
change_id: CR-089
status: draft-readiness-approved-no-runtime-authorization
created_at: "2026-06-17T22:03:03+08:00"
created_by: host-orchestrator
source_gate: CP2/CP3/CP5-CR089-QMT-INTERFACE-VALIDATION
package_root: packages/qmt_interface_smoke/0.1.0
runtime_authorized: false
nas_operation_authorized: false
credential_read_authorized: false
---

# CR089 策略包输出与 NAS 交付规划

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 0.1 | 2026-06-17 | host-orchestrator | 新增 CR089 `qmt_interface_smoke` 离线策略包骨架、交付合同、交易主机 intake 边界和不授权项。 |

## 1. 状态

本文件定义 CR089 下 `qmt_interface_smoke` 策略包的输出规范、策略交付位置合同和交易主机 intake 流程。当前状态是 `draft-readiness-approved-no-runtime-authorization`：

- CR089 CP2 / CP3 / CP5 推荐方案已由用户批准。
- CR089 仍是 `blocked-readiness-approved`，不设为 active。
- CR046 仍是当前 active formal CR，保持 `active-cp6-pass-ready-for-verification`。
- CR020 仍是 `deleted-by-user`，只可审计复用代码和 runbook 边界。
- 本轮未访问 NAS、未读取 `.env` 或凭据、未启动 QMT / MiniQMT / XtQuant / gateway、未查询账户、未 submit/cancel/simulation/live。

## 2. 策略包输出位置

当前本地离线包骨架写入：

```text
packages/qmt_interface_smoke/0.1.0/
```

该目录是源码仓库内的离线交付材料，不是 NAS 目录，也不是交易主机运行缓存。

## 3. 策略包规范

| 对象 | 路径 | 规范 |
|---|---|---|
| manifest | `packages/qmt_interface_smoke/0.1.0/manifest.yaml` | `schema_version=cr089-strategy-package-manifest-v1`，记录授权边界、target、只读接口合同和交付合同 |
| checksum | `packages/qmt_interface_smoke/0.1.0/checksums/SHA256SUMS` | 关键文本文件的 SHA256，全部使用相对路径 |
| target: QMT terminal | `packages/qmt_interface_smoke/0.1.0/targets/qmt_terminal/README.md` | 只描述 QMT terminal 后续手工只读 smoke 边界 |
| target: MiniQMT runner | `packages/qmt_interface_smoke/0.1.0/targets/miniqmt_runner/README.md` | 只描述 MiniQMT runner 后续消费边界 |
| intake checklist | `packages/qmt_interface_smoke/0.1.0/validation/offline-intake-checklist.md` | 文件级 intake 检查，不包含 runtime 执行 |
| evidence template | `packages/qmt_interface_smoke/0.1.0/evidence/redacted-smoke-result-template.yaml` | 后续用户手工 runtime smoke 的脱敏结果模板 |

首个策略包不包含真实交易策略逻辑，不包含终端脚本，不包含 runner 安装器，不包含账号、凭据或环境变量。

## 4. NAS package exchange 合同

CR089 推荐的 NAS 只作为 package exchange，不作为默认执行根。合同路径如下：

| 合同对象 | 路径模板 | 当前动作 |
|---|---|---|
| package root | `${STRATEGY_PACKAGE_EXCHANGE_ROOT}/packages/qmt_interface_smoke/0.1.0` | 仅记录合同，未访问 |
| package index | `${STRATEGY_PACKAGE_EXCHANGE_ROOT}/index/package-index.yaml` | 仅记录合同，未访问 |
| approval record | `${STRATEGY_PACKAGE_EXCHANGE_ROOT}/approvals/qmt_interface_smoke-0.1.0.yaml` | 仅记录合同，未访问 |
| quarantine record | `${STRATEGY_PACKAGE_EXCHANGE_ROOT}/quarantine/qmt_interface_smoke-0.1.0/rejection.yaml` | 仅记录合同，未访问 |

默认规则：

- 研究侧只发布不可变 package 版本，不覆盖同名版本目录。
- NAS 目录只用于已批准包的交换与审计。
- 交易主机不从 NAS 原地运行策略。
- 交易主机必须先校验 package，再复制到本地不可变缓存。

## 5. 交易主机交付位置

交易主机推荐使用本地不可变缓存：

| 合同对象 | 路径模板 | 规则 |
|---|---|---|
| local cache | `${TRADING_PACKAGE_CACHE_ROOT}/packages/qmt_interface_smoke/0.1.0` | checksum 通过后才允许放入 |
| active pointer | `${TRADING_PACKAGE_CACHE_ROOT}/active/qmt_interface_smoke` | 指向已校验版本；切换必须可回滚 |
| evidence | `${TRADING_PACKAGE_CACHE_ROOT}/evidence/qmt_interface_smoke/<run_id>/redacted-smoke-result.yaml` | 仅保存脱敏摘要 |

本轮没有在交易主机执行任何命令，也没有写入上述路径。

## 6. 本地离线校验

仓库内提供只读本地 checker：

```bash
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python scripts/check_cr089_qmt_interface_smoke_package.py --package-root packages/qmt_interface_smoke/0.1.0
```

checker 只验证：

- 目录结构。
- manifest schema 和关键字段。
- 禁止操作列表。
- target 文档存在。
- 脱敏证据模板存在且 raw 输出关闭。
- `checksums/SHA256SUMS` 与文件内容一致。

checker 不读取 `.env`，不访问 NAS，不打开网络，不导入 trading runtime，不导入 QMT / MiniQMT / XtQuant。

## 7. 后续 runtime smoke 边界

后续真实接口验证仍需单独 runtime authorization。授权后也只允许：

- 用户本人在交易主机手工执行。
- endpoint 限定为 `query_positions`。
- scope 限定为 `qmt:positions:read`。
- 输出限定为脱敏摘要。
- 结果回填到 `evidence/redacted-smoke-result-template.yaml` 的副本中。

授权前不允许执行任何真实 QMT / MiniQMT / XtQuant / gateway 动作。

## 8. 明确不授权项

- 不访问、挂载、列取、复制、发布、拉取或删除 NAS 内容。
- 不读取 `.env`、token、API key、密码、HMAC secret、cookie、session、私钥、QMT 账号或交易密码。
- 不启动 QMT、MiniQMT、XtQuant 或 gateway。
- 不查询真实账户、资金、持仓、委托、成交或日志原文。
- 不 submit/cancel，不 simulation/live。
- 不恢复 CR020，不激活 CR089，不恢复 CR046 CP7。
