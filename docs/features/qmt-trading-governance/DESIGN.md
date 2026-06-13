---
status: "draft-current-index"
version: "1.0"
feature_id: "FEAT-06"
source_matrix: "docs/design/FEATURE-DESIGN-MATRIX.md"
source_blueprint: "docs/design/BLUEPRINT.md"
change: "CR-031"
---

# Feature Design: qmt-trading-governance

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-07 | meta-po | 新增 QMT 交易治理 Feature 设计索引 |

## Feature 摘要

| 项 | 内容 |
|---|---|
| Feature 目标 | 为后续 QMT simulation / live_readonly / small_live / scale_up 提供 OMS、pre-trade risk、broker lake、stage gate、reconciliation 和 kill switch 的统一治理边界 |
| Owner | FEAT-06 |
| 主要代码面 | `trading/oms.py`、`trading/pretrade_risk.py`、`trading/broker_lake.py`、`trading/stage_gate.py`、`trading/reconciliation.py`、`trading/kill_switch.py` |
| 主要设计来源 | `process/HLD-QMT-TRADING.md`、ADR-055..061、CR-015 / CR-016 Story / LLD |
| 非授权声明 | 本文不授权 simulation、live_readonly、small_live、scale_up、真实发单、撤单、账户写入、账户查询或 broker lake 真实写入 |

## Feature 边界与相邻对象

| 对象 | 本 Feature 负责 | 不负责 | 相邻 Feature / 模块 |
|---|---|---|---|
| OrderIntent / OMSOrder | 状态机、幂等、manual_review、unknown/timeout 处理 | 生成因子信号 | FEAT-03 / FEAT-04 |
| PreTradeRisk | cash、整手、T+1、持仓、价格口径、限额、异常价格 hard block | 研究评分 | FEAT-02 / FEAT-07 |
| BrokerLakeRecord | 外置 broker facts schema、retention、redaction | 市场数据 lake | FEAT-02 |
| StageGate | shadow -> simulation -> live_readonly -> small_live -> scale_up | 授权替代品 | FEAT-07 |
| Reconciliation / KillSwitch | 对账、差异、暂停 / 恢复、人工接管 | 自动放大资金 | FEAT-08 |

## 输入 / 输出契约

| 方向 | 契约 |
|---|---|
| 输入 | StrategyAdmissionPackage、OrderIntentDraft、raw execution price、cash/position snapshot、stage authorization |
| 输出 | OMS state、risk result、broker event、dry-run plan、reconciliation report、kill switch event |
| 错误输出 | `risk_blocked`、`stage_blocked`、`authorization_missing`、`unknown_timeout_manual_review`、`broker_lake_write_blocked` |

## 失败路径

| 失败点 | 行为 |
|---|---|
| 缺 stage authorization | adapter call = 0 |
| 风控失败 | hard block，写 blocked reason，不触达 QMT |
| broker event unknown / timeout | manual_review，不静默成功 |
| 对账差异超阈值 | kill switch 或人工接管 |
| CR-017 raw execution policy 不满足 | production / scale_up blocked |

## Gotchas

- CR-015 / CR-016 verified 只是离线 / 文档 / mock 范围，不解禁真实 broker 操作。
- gateway 存在不等于 OMS 可以提交订单。
- broker lake 默认不得写仓库 `data/**` / `reports/**`。

