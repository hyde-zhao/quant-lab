---
cr_id: CR-040
discussion_id: CP3-CR040-HLD-DISCUSSION
status: ready-for-review
owner: meta-po
created_at: 2026-06-10T22:45:00+08:00
---

# CP3 CR040 架构讨论日志

## 架构灰区

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| A. API-less Paper Simulation Runner | 不依赖 broker；可本地复跑；可验证 order/fill/position/equity 语义；权限最小 | 不能证明真实平台接口可用 | `engine/paper_simulation.py`、runner、fixture、报告 | 推荐 | 当 CR041 完成且需要外部平台语义时，再进入 BrokerAdapter / Goldminer Spike。 |
| B. Backtrader 默认 runtime | 生态成熟，事件驱动语义丰富 | 依赖与许可边界更复杂；CR025 已规定 no-copy / optional reference | 依赖管理、license、测试环境 | 不推荐本轮 | 只有用户明确接受依赖变更和运行授权时才考虑。 |
| C. 直接接入掘金量化 | 接近未来目标平台 | 账号、终端、凭据、SDK、仿真/实盘授权边界未确认 | 安全、运行授权、外部接口 | 不推荐本轮 | 仅在 CR043 Spike 中基于官方文档和终端实测重新确认。 |

## 推荐架构

CR040 只冻结路线：QMT 删除，本地 API-less paper simulation 优先。后续 CR041 的技术主线应是独立 `PaperBroker` / `PositionLedger` / `FillLedger` / `EquityReport`，输入为 CR039 策略准入包与 order intent draft 语义，输出为本地可审计 artifact。

## 不授权边界

本架构讨论不授权任何外部 SDK 安装、登录、连接、账户查询、委托/成交查询、下单或撤单。
