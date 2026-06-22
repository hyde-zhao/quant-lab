# CR089 qmt_interface_smoke 离线 intake 检查清单

本清单用于交易主机或研究主机上的文件级检查。当前 CR089 批准不包含真实 NAS / QMT / 凭据 / 账户 / 交易动作。

## 1. 文件级检查

- [ ] `manifest.yaml` 存在，`schema_version=cr089-strategy-package-manifest-v1`。
- [ ] `strategy_id=qmt_interface_smoke`，`version=0.1.0`。
- [ ] `runtime_authorized=false`。
- [ ] `nas_operation_authorized=false`。
- [ ] `credential_read_authorized=false`。
- [ ] `account_query_authorized=false`。
- [ ] `trade_write_authorized=false`。
- [ ] `targets/qmt_terminal/README.md` 存在。
- [ ] `targets/miniqmt_runner/README.md` 存在。
- [ ] `evidence/redacted-smoke-result-template.yaml` 存在。
- [ ] `checksums/SHA256SUMS` 校验通过。

## 2. 推荐本地校验命令

在仓库根目录或交易主机本地缓存根目录运行：

```bash
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python scripts/check_cr089_qmt_interface_smoke_package.py --package-root packages/qmt_interface_smoke/0.1.0
```

交易主机若只收到包目录而没有仓库脚本，应先使用等价的 SHA256 工具核对 `checksums/SHA256SUMS`，并逐项检查 `manifest.yaml` 的禁止项。不要为了校验而读取 `.env`、启动 QMT 或访问账户。

## 3. 后续 runtime smoke 前置门禁

只有满足以下条件后，才可以进入真实只读 smoke：

- [ ] 独立 runtime authorization 已批准。
- [ ] 明确本次只允许 `query_positions`，scope 为 `qmt:positions:read`。
- [ ] 用户本人在交易主机上执行命令，不由 agent 代跑。
- [ ] 输出只保留脱敏摘要，不复制原始账户、证券、数量、市值、委托、成交或日志。
- [ ] 若任一 forbidden operation 发生或将要发生，立即停止并记录为 blocked。

## 4. 回填证据

使用 `evidence/redacted-smoke-result-template.yaml` 填写脱敏结果。禁止贴入：

- 账号、姓名、手机号、身份证、券商客户号。
- 原始证券代码、原始持仓数量、成本、市值、盈亏。
- QMT / MiniQMT / XtQuant 原始日志。
- token、cookie、session、密码、私钥、API key。
