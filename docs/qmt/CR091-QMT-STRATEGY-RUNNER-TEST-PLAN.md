# CR091 QMT Strategy Runner Test Plan

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| v0.1 | 2026-06-18 | host-orchestrator | 定义只读 runner 的离线测试策略、fixture 范围和禁止操作断言。 |

## 测试目标

CR091 测试只证明 runner 合同、adapter、package intake、脱敏 evidence 和只读 gateway 边界满足设计。不证明真实 QMT / MiniQMT / XtQuant / gateway / runner runtime 可用，不证明策略可交易。

## 测试层级

| 层级 | 覆盖对象 | 验收点 |
|---|---|---|
| Static guardrail | 新增 runner 文件、测试文件、fixture manifest | 不出现 `xtquant` 直接 import；不读取 `.env`；不包含 submit / cancel / simulation / live 执行入口。 |
| Contract unit tests | `StrategyAdapter`、`TargetPortfolioSnapshot`、`OrderIntentDraftV1` | 多因子、legacy、future package adapter 均输出统一合同；`qmt_allowed=false`、`not_authorization=true`。 |
| Package intake tests | manifest、checksum、immutable cache、active pointer | schema、checksum、forbidden_operations 和 runtime flags fail closed。 |
| Multifactor fixture tests | `multifactor_strategy_admission_package_v1` fixture | 至少 1 个 PASS / WATCH 候选可转成 target portfolio；风险 / 成本 / 因子贡献 refs 保留。 |
| Legacy strategy fixture tests | RSI / MACD / momentum `StrategyResult` | 目标标的和 score 能转成统一 target portfolio；空目标 fail closed。 |
| Readonly gateway fake tests | fake `QmtRestTransport` | 只允许 health / capabilities / query_positions；其他 endpoint 被 scope 阻断。 |
| Redaction tests | evidence writer | 输出不含 token / secret / account / raw positions / raw order / qmt logs；forbidden counters 全为 0。 |

## Fixture 策略

| Fixture | 来源 | 约束 |
|---|---|---|
| `cr091_multifactor_admission_package_pass.json` | 由本地 CR039 schema 手工构造最小样例 | operation counts 全 0；不含真实标的持仓、账户或凭据。 |
| `cr091_legacy_strategy_result_momentum.json` | 由 `StrategyResult` 结构手工构造 | 只含 symbol-like fixture id 和 score，不含真实账户信息。 |
| `cr091_strategy_package_manifest.yaml` | 基于 CR089 manifest 缩小扩展 | runtime / NAS / credential / account / trade_write flags 全 false。 |
| `cr091_fake_query_positions_response.json` | fake transport response | 只含脱敏 bucket / digest，不含原始持仓。 |

## 禁止操作断言

每个自动化测试 summary 必须包含下列字段且值为 0：

- `nas_read`
- `nas_write`
- `nas_list`
- `nas_copy`
- `nas_publish`
- `nas_pull`
- `credential_read`
- `env_file_read`
- `qmt_start`
- `miniqmt_start`
- `xtquant_import`
- `gateway_start`
- `gateway_socket_open`
- `account_raw_query`
- `raw_positions_emit`
- `submit_order`
- `cancel_order`
- `simulation`
- `live`
- `provider_fetch`
- `lake_write`
- `catalog_publish`

## 允许的验证命令

以下命令只有在 CP5 approved 且代码实现后才执行：

```bash
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 pytest -q tests/test_cr091_strategy_runner_contracts.py
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python scripts/check_cr091_strategy_runner_package.py --package-root tests/fixtures/cr091_strategy_package
```

当前 CR091 方案阶段不执行上述未来命令。

## CP5 通过条件

- 测试范围覆盖多因子、legacy strategy、package intake、fake readonly gateway、redaction 和 forbidden counters。
- 所有测试均可在不访问 NAS、不读 `.env`、不启动 QMT / gateway 的环境下运行。
- 测试不需要真实行情 provider、data lake、catalog publish 或账户数据。
- 真实交易主机 smoke 不纳入自动 CP5，通过后也只能作为后续逐 run runtime authorization。

