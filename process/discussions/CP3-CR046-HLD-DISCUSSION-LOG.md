---
status: "ready-for-cp3"
change: "CR-046"
phase: "solution-design"
owner: "meta-po"
created_at: "2026-06-13T22:03:22+08:00"
source_hld: "docs/design/HLD-CR046-QMT-MINIQMT-DUAL-TARGET-FRAMEWORK.md"
---

# CP3 CR046 HLD Discussion Log

## 讨论边界

用户已在 CP2 批准 CR046 framework-first 范围：先定 QMT / MiniQMT 双目标策略交付框架、验证框架、MiniQMT runner 安装设计和策略包契约；不做具体策略交付、不做 QMT 运行验证、不连接 MiniQMT、不 submit/cancel。

本轮 CP3 讨论未授权真实运行，也未调度子 agent；由 host-orchestrator 基于 CP2 决策、现有蓝图和 HLD skill 规则完成设计收敛。

## Architecture Gray Areas

| Gray Area | 讨论问题 | 推荐方案 | 备选方案 | 结论 | 证据 |
|---|---|---|---|---|---|
| AGQ-CR046-01 | 双目标策略交付框架是否独立成 FEAT-09？ | 新增 FEAT-09 | 并入 FEAT-05 或 FEAT-06 | 推荐进入 CP3 决策 | `docs/design/BLUEPRINT.md`、ADR-CR046-001 |
| AGQ-CR046-02 | 策略核心是否允许平台 API？ | core 平台无关，target adapter 隔离平台能力 | core 直接调用 QMT/MiniQMT | 推荐进入 CP3 决策 | HLD §推荐架构、ADR-CR046-002 |
| AGQ-CR046-03 | MiniQMT runner 本轮做到什么程度？ | 只做安装设计和 install dry-run 方案 | 真实安装 / 连接 / 运行 | 推荐进入 CP3 决策 | HLD §MiniQMT Runner 安装设计、ADR-CR046-003 |
| AGQ-CR046-04 | 验证框架如何避免误导？ | 证据分级，CR046 不声明 runtime verified | fixture pass 即视为可运行 | 推荐进入 CP3 决策 | HLD §验证框架、ADR-CR046-004 |
| AGQ-CR046-05 | 首个具体策略何时交付？ | 后置 CR047 | 合并进 CR046 | 已由 CP2 批准，CP3 复核 | ADR-CR046-005 |
| AGQ-CR046-06 | 研究框架完善何时启动？ | 后置 CR051 | 合并进 CR046 | 已由 CP2 批准，CP3 复核 | ADR-CR046-006 |

## Advisor Table

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| FEAT-09 独立框架 | 策略交付合同、runner 安装设计和验证框架边界清晰 | 新增 Feature 和 ADR | 蓝图、领域、依赖、Story planning | 推荐 | MiniQMT 路线仍作为目标；若长期放弃可降级 |
| 并入 FEAT-05 QMT Gateway | Feature 数少，靠近 QMT 能力 | 容易把策略包误读为 gateway runtime | 安全、文档、后续 CR047/049 | 不推荐 | 仅在 QMT-only 且无 runner 时考虑 |
| 并入 FEAT-06 交易治理 | 靠近 OMS / stage gate | 容易把合同误读为 submit/cancel 能力 | OMS、风险、授权 | 不推荐 | 仅在进入真实交易治理实现时部分消费 |

## 结论

推荐 CP3 批准以下设计：

- 新增 FEAT-09 承载 QMT / MiniQMT 双目标策略交付框架。
- StrategyCoreContract 平台无关，target adapter 才能承载 QMT terminal / MiniQMT runner 差异。
- MiniQMT runner 本 CR 只做安装设计和 install dry-run 方案。
- StrategyValidationEvidence 必须区分 design/static/fixture/dry-run plan/runtime verified。
- 具体策略交付、QMT terminal shadow、MiniQMT install / connection 和 submit/cancel 全部后置独立 CR / runtime authorization。
