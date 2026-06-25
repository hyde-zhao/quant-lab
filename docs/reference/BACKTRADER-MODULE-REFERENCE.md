# Backtrader Module Reference

本文件是 Backtrader no-copy 的 canonical reference。旧 `docs/CR025-BACKTRADER-MODULE-REFERENCE.md` 已归档到 [../legacy/archive/CR025-BACKTRADER-MODULE-REFERENCE.md](../legacy/archive/CR025-BACKTRADER-MODULE-REFERENCE.md)；新用户不应再把 CR 编号文档作为入口。

## 1. Purpose

Backtrader 在本项目中只作为 `execution semantic reference`，用于理解 lightweight execution engine 的 feed、broker、order、trade、position、commission、sizer、slippage、analyzer、observer、writer 和 strategy lifecycle 语义。它可以帮助解释 semantic diff，但不作为多因子研究主框架，不作为 production truth，不作为 simulation-ready，不作为 QMT admission pass。

## 2. Classification Model

| Classification | Meaning | Current decision |
|---|---|---|
| `reference_only` | 只参考概念、术语和执行语义。 | Cerebro orchestration、broker/order/trade/position、analyzer/observer、strategy lifecycle。 |
| `adapt_interface` | 可用 clean-room 方式适配接口语义。 | clean feed gate、commission/sizer/fill assumption、semantic diff 字段。 |
| `migration_candidate` | 源码级候选。 | 当前为空：`migration_candidate=[]`。 |
| `exclude` | 禁止进入本项目。 | source、samples、tests、datas、live store、line/metaclass runtime。 |

YAML contract:

```yaml
migration_candidate: []
```

当前无默认源码级候选，源码级迁移候选为空。任何非空 `migration_candidate`、源码级复制、裁剪、改写、vendor 或 fork 都必须另起 CR，经过 legal review，并回到 CP3 和 CP5。

任何候选从空集合变为非空，都必须停止当前 Story，另起 CR 或回退到 CP3 / CP5 重新确认 legal review、license 风险和源码迁移边界。

## 3. No-Copy Guardrail

Backtrader is GPLv3. 当前策略是 `no-copy`、`no-source-migration`、`no-vendored-source`。

当前合同要求不复制、裁剪、改写或源码级移植以下对象：

| Forbidden class | Examples |
|---|---|
| source | `backtrader/**` |
| source | `vendor/backtrader/**` |
| source | `vendors/backtrader/**` |
| source | `third_party/backtrader/**` |
| source | `external/backtrader/**` |
| samples | Backtrader samples。 |
| tests | Backtrader tests。 |
| datas | Backtrader test datas / sample datas。 |
| live store | live broker / live data store。 |
| line/metaclass runtime | Backtrader line runtime、metaclass runtime、indicator runtime。 |

## 4. Multifactor Boundary

Backtrader 不承接以下多因子研究能力：`FactorSpec`、`FactorRunSpec`、`IC / RankIC`、分层收益、多因子组合、实验追踪、策略准入包、Qlib、Alphalens、vnpy.alpha。CR-030 才是这些能力的研究入口。

不得从 CR-025 自动继承依赖变更、provider fetch、lake write、catalog publish、凭据读取、QMT / MiniQMT / XtQuant operation 或 broker / simulation / live 能力。

## 5. Forbidden Operation Counts

| Operation | Count |
|---|---:|
| Backtrader run | `0` |
| Backtrader source copy / source migration | `0` |
| provider fetch | `0` |
| lake write | `0` |
| catalog publish | `0` |
| credential read | `0` |
| QMT / MiniQMT / XtQuant operation | `0` |
| broker / simulation / live | `0` |
| multifactor framework implementation | `0` |
| Qlib / Alphalens / vnpy.alpha integration | `0` |
