# qmt_interface_smoke 0.1.0

本目录是 CR089 批准范围内的本地离线策略包骨架。它只用于 package discovery、manifest 校验、SHA256 校验、目标说明检查和后续人工只读 smoke 的证据模板准备。

## 当前状态

| 项 | 值 |
|---|---|
| package_id | `strategy-package-qmt_interface_smoke-0.1.0` |
| strategy_id | `qmt_interface_smoke` |
| version | `0.1.0` |
| status | `skeleton-offline-intake-ready` |
| change_id | `CR-089` |
| parent_cr | `CR-046` |
| runtime_authorized | `false` |
| zip_status | `not_built` |

## 本包允许的离线动作

- 读取本目录内的 `manifest.yaml`、README、target 说明、人工 checklist、证据模板和 `checksums/SHA256SUMS`。
- 执行本地结构校验和 SHA256 校验。
- 在交易主机本地缓存目录中进行文件级 intake 复核。
- 在未来单独 runtime authorization 后，由用户手工执行 `query_positions` 只读 smoke，并只回填脱敏摘要。

## 明确不授权

- 不访问、挂载、列取、复制、发布或拉取 NAS 内容。
- 不读取 `.env`、token、API key、密码、HMAC secret、cookie、session、私钥、QMT 账号或交易密码。
- 不启动 QMT、MiniQMT、XtQuant 或 gateway。
- 不查询账户原文、资金原文、持仓原文、委托原文、成交原文或日志原文。
- 不执行 `submit_order`、`cancel_order`、simulation 或 live。
- 不恢复 CR020，不激活 CR089，不恢复 CR046 CP7。

## 目录说明

| 路径 | 用途 |
|---|---|
| `manifest.yaml` | 策略包结构、授权边界、目标平台和交付合同 |
| `checksums/SHA256SUMS` | 本目录关键文本文件的 SHA256 |
| `targets/qmt_terminal/README.md` | QMT terminal target 说明 |
| `targets/miniqmt_runner/README.md` | MiniQMT runner target 说明 |
| `validation/offline-intake-checklist.md` | 交易主机文件级 intake 检查清单 |
| `evidence/redacted-smoke-result-template.yaml` | 后续只读 smoke 的脱敏证据模板 |

## 本地校验命令

在当前仓库根目录运行：

```bash
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python scripts/check_cr089_qmt_interface_smoke_package.py --package-root packages/qmt_interface_smoke/0.1.0
```

该命令只读取传入目录内的文件，不读取 `.env`，不访问 NAS，不打开网络，不导入 QMT / MiniQMT / XtQuant。

## 交易主机 intake 原则

交易主机后续只能把已批准的包复制到本地不可变缓存后再运行离线校验。推荐合同路径是：

- 研究侧 package exchange：`${STRATEGY_PACKAGE_EXCHANGE_ROOT}/packages/qmt_interface_smoke/0.1.0`
- 交易主机本地缓存：`${TRADING_PACKAGE_CACHE_ROOT}/packages/qmt_interface_smoke/0.1.0`
- 交易主机 active pointer：`${TRADING_PACKAGE_CACHE_ROOT}/active/qmt_interface_smoke`

本仓库中的这些路径只是合同描述，不表示本轮已经访问或写入任何 NAS / 交易主机位置。
