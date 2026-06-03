# CP2 CR-015 / CR-016 / CR-017 Intake Decision Brief

| 字段 | 内容 |
|---|---|
| 检查点 | CP2 requirement / intake decision |
| 适用 CR | CR-015 QMT foundation；CR-016 QMT activation；CR-017 adjustment dual-view |
| 创建时间 | 2026-05-27T22:43:20+08:00 |
| 当前状态 | approved |
| 推荐回复 | `approve` / `修改: <具体修改点>` / `reject` |

## Entry Criteria

| 条目 | 状态 | 证据 |
|---|---|---|
| CR-015 已创建 | PASS | `process/changes/CR-015-QMT-TRADING-FOUNDATION-2026-05-27.md` |
| CR-016 已创建 | PASS | `process/changes/CR-016-QMT-SIMULATION-LIVE-ACTIVATION-2026-05-27.md` |
| CR-017 已创建 | PASS | `process/changes/CR-017-ADJUSTMENT-POLICY-DUAL-VIEW-SUPPORT-2026-05-27.md` |
| 缺口检查已完成 | PASS | `process/checks/CR015-CR016-CR017-GAP-REVIEW-2026-05-27.md` |
| 当前请求要求整理待决策问题 | PASS | 用户要求“整理待决策的问题，分析备选方案，让我决策” |

## Decision Brief

本轮只请求 intake / requirement 层面的决策，不授权实现、不授权真实发单、不授权真实抓取和写湖。

| ID | 决策问题 | 推荐方案 | 备选方案 A | 备选方案 B | 推荐理由 | 接受影响 | 不接受影响 |
|---|---|---|---|---|---|---|---|
| D-ALL-01 | CR-015 / CR-016 / CR-017 的推进顺序如何安排 | 混合推进：先冻结 CR-017 复权与 raw 交易价边界；CR-015 foundation 可并行做无真实发单设计；CR-016 真实激活等 CR-015 foundation 和 CR-017 口径边界后推进 | 严格串行：CR-017 全部完成后再做 CR-015，再做 CR-016 | QMT 优先：先完成 CR-015 / CR-016，CR-017 后置 | 推荐方案兼顾安全与效率；先冻结价格口径可避免 QMT 误用复权价，CR-015 的 adapter / OMS / mock 设计又不必等待 CR-017 全部代码完成 | 可并行设计 CR-017 与 CR-015，CR-016 真实发单保持后置；降低价格口径和交易风险 | 严格串行会拖慢 QMT 基础建设；QMT 优先会把复权价 / raw 价混淆风险前置 |
| D-CR15-01 | QMT 接入架构采用什么边界 | Windows QMT / MiniQMT 节点 + XtQuant 外部 Python API + OMS + QMT adapter；策略不得直接调用 QMT API | 策略直接调用 QMT API | 迁移到完整第三方交易平台统一接管研究与交易 | 推荐方案保留当前数据湖和研究资产，同时把真实交易接口收敛到 adapter/OMS | 可 mock 测试、可审计、可风控、可替换 broker；误下单和绕过风控风险低 | 直接调用 QMT 实现快但风险高；整体迁移成本高，会打散当前 market_data/engine 资产 |
| D-CR15-02 | CR-015 是否建立独立 OMS / broker lake / pre-trade hard risk gate | 建立本地订单状态机、外置 broker lake、pre-trade hard block，默认仅 shadow / dry-run / mock，不授权真实发单 | 只依赖 QMT 本地日志和返回值，不建 broker lake | 风控只 warn，不 hard block，并允许早期真实 API 试单 | 推荐方案是进入模拟盘和实盘前的最小安全底座 | 部分成交、撤单、unknown、失败、对账和回放可审计；真实 API 调用仍需单独授权 | 不建 broker lake 难以复盘；warn-only 会把风控失败变成可继续下单的实盘风险 |
| D-CR17-01 | 前复权 / 后复权如何进入数据湖 | `prices_raw` + `adj_factor` 为事实源；独立派生 `prices_qfq`、`prices_hfq`、`returns_adjusted`；qfq 必须记录 `as_of_trade_date`；QMT 使用 raw/broker price | 只存 qfq/hfq 成品表，不保留 raw + adj_factor 作为核心事实源 | 同一个 `prices` 表混存 qfq/hfq/raw，靠 `adjustment_policy` 过滤 | 推荐方案同时满足研究、图表、审计和 QMT 执行价格隔离 | 后续可同时支持 qfq/hfq，研究 run 仍单口径校验，QMT 不会误用复权价下单 | 成品表缺少重算和对账能力；同表混存容易被消费方误读，破坏现有复权一致性 gate |
| D-CR16-01 | 模拟盘 / 实盘激活路径和准入门槛如何定 | `shadow -> QMT 模拟盘 -> 实盘只读 -> 小资金实盘 -> 放大资金`；T 日收盘后信号，T+1 限价/保护价；必须有 runbook、对账、kill switch、per-run 授权；CR-017 不阻断技术模拟盘，但阻断生产策略复权治理声明和资金放大 | 模拟盘通过后直接小资金实盘，不做实盘只读阶段 | 长期只做 shadow/模拟盘，不进入实盘链路 | 推荐方案让交易链路验证和研究成熟度分层推进 | 可以先验证技术链路，又不把研究口径缺口包装成生产级策略；真实资金风险有阶段上限 | 直接实盘缺少只读核对和异常演练；长期不进实盘则无法验证真实成交、对账和运行压力 |

## Checklist

| 检查项 | 状态 | 说明 |
|---|---|---|
| 每个决策问题有推荐方案 | PASS | D-ALL-01 至 D-CR16-01 均已给出推荐 |
| 每个决策问题至少有一个备选方案 | PASS | 每项至少 2 个备选方案 |
| 每个决策问题有优劣和影响 | PASS | 已覆盖推荐理由、接受影响、不接受影响 |
| 未授权实现 | PASS | 本 brief 只作为 intake / requirement 决策 |
| 未授权真实发单 | PASS | CR-015/016 均保留 per-run 显式授权要求 |
| 未授权真实抓取 / 写湖 / publish | PASS | CR-017 保留真实数据操作单独授权要求 |

## Exit Criteria

| 条件 | 状态 |
|---|---|
| 用户回复 `approve` 或逐项批准 D-ALL-01 至 D-CR16-01 | PASS |
| 用户如需修改，明确给出 `修改: D-ID=<选择或修改点>` | pending |
| 用户如拒绝，明确 `reject` 并说明拒绝对象 | pending |

## Deliverables

| 产物 | 路径 |
|---|---|
| 决策稿 | `checkpoints/CP2-CR015-CR016-CR017-INTAKE-DECISION-BRIEF.md` |
| CR-015 | `process/changes/CR-015-QMT-TRADING-FOUNDATION-2026-05-27.md` |
| CR-016 | `process/changes/CR-016-QMT-SIMULATION-LIVE-ACTIVATION-2026-05-27.md` |
| CR-017 | `process/changes/CR-017-ADJUSTMENT-POLICY-DUAL-VIEW-SUPPORT-2026-05-27.md` |
| 缺口检查 | `process/checks/CR015-CR016-CR017-GAP-REVIEW-2026-05-27.md` |

## 人工审查结果

- 审查人：user
- 审查时间：2026-05-27T22:50:13+08:00
- 结论：approved
- 审查意见：`@meta-po approve 全部推荐方案。你可以组织子agent开始实现这几个CR了`
