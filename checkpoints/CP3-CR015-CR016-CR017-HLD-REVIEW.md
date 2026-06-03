---
checkpoint_id: "CP3"
checkpoint_name: "CR-015/CR-016/CR-017 HLD Review"
type: "auto_then_manual"
status: "approved"
owner: "meta-po"
created_at: "2026-05-27T23:29:20+08:00"
reviewed_by: "user"
reviewed_at: "2026-05-28T05:47:14+08:00"
auto_check_result: "process/checks/CP3-CR015-CR016-CR017-HLD-CONSISTENCY.md"
target:
  phase: "solution-design"
  story_id: ""
  artifacts:
    - "process/HLD.md"
    - "process/HLD-DATA-LAKE.md"
    - "process/HLD-QMT-TRADING.md"
    - "process/ARCHITECTURE-DECISION.md"
---

# CP3 CR-015 / CR-016 / CR-017 HLD 人工审查

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---|---|
| `process/checks/CP3-CR015-CR016-CR017-HLD-CONSISTENCY.md` | PASS | 0 | HLD 拆分、ADR、Q-030 至 Q-038 决策输入和权限边界均通过自动预检。 |

## Decision Brief

| 字段 | 内容 |
|---|---|
| 推荐决策 | `approve`：接受 CR-015 / CR-016 / CR-017 HLD / ADR 设计，允许进入 Story Plan。 |
| 备选方案 | `修改: <具体修改点>`：退回 HLD 修改指定决策；`reject`：不接受本轮 HLD，回退到需求 / intake 范围重新界定。 |
| 影响维度 | 用户价值、交易安全、复权研究可信度、实现复杂度、可验证性、维护成本、跨平台兼容、权限与凭据安全、后续交付影响。 |
| 优劣分析 | 推荐方案把 QMT 交易层拆成独立 companion HLD，复权派生层归入数据湖 HLD，主 HLD 只保留研究消费边界；优点是职责清晰、风险隔离、可验证，代价是 HLD/ADR 数量增加。 |
| 风险与回退 | 若不批准，不能进入 Story Plan / LLD / 实现；回退到 Q-030 至 Q-038 或 CR-015/016/017 范围重新设计。 |
| 用户需决策事项 | 是否接受 QMT companion HLD、CR-017 数据湖复权双视图设计、ADR-053..061，以及 Q-030..Q-038 的推荐方案。 |

## CP3 待决策项

| ID | 推荐方案 | 备选方案 A | 备选方案 B | 接受影响 | 不接受影响 |
|---|---|---|---|---|---|
| Q-030 | 冻结 raw + `adj_factor` 事实源；qfq 以 `as_of_trade_date` 为锚点，hfq 以 provider/base date 为锚点；`provider_factor_direction` 必填；异常价格进入 quality fail/warn | 先只支持 qfq，hfq 后置 | 只保存 provider 成品 qfq/hfq，不冻结公式 | 复权公式、as-of 和异常解释可验证，QMT raw 价边界清楚 | 公式方向可能写反，qfq 漂移不可追溯，CP5 Story 无法安全实现 |
| Q-031 | 独立 `prices_raw`、`adj_factor`、`prices_qfq`、`prices_hfq`、`returns_adjusted` view；旧 qfq 只读保留，兼容入口输出 migration summary | 单 `prices` 表按 `adjustment_policy` 分区混存 | 完全迁移旧 qfq 为新 view 并覆盖旧入口 | 单口径 gate 清晰，旧报告可追溯，QMT 不误读复权价 | 消费方容易混用，旧报告可能丢追溯，迁移风险高 |
| Q-032 | broker lake 外置 root，schema 覆盖 order/fill/position/asset/error/reconciliation/incident；默认 retention 3 年或用户配置；敏感字段脱敏 / 禁入库 | 只依赖 QMT 本地日志 | 写入仓库 `data/**` / `reports/**` | 交易事实可复盘、可对账，凭据风险低 | 无法审计交易事实或泄露敏感信息 |
| Q-033 | OMS 状态机覆盖 accepted/partial/filled/cancel_pending/canceled/rejected/failed/unknown/timeout/manual_review/frozen；unknown/timeout 不自动成功，需对账或人工确认 | 简化为 submitted/filled/failed 三态 | 直接以 QMT 返回值为唯一状态 | 部分成交、撤单失败和超时可审计 | 重复下单、误判成功、对账失真 |
| Q-034 | pre-trade risk hard block：现金、100 股整手、T+1 可卖、可用持仓、价格口径、重复 intent、单票 / 组合限额、异常价格；配置在交易配置 / run profile，失败 adapter_calls=0 | warn-only 记录但允许继续 | 只做 QMT 返回后校验 | 实盘风险受控，失败可解释 | 风控失败仍可能下单 |
| Q-035 | stage gate 固定 `shadow -> simulation -> live_readonly -> small_live -> scale_up`；每阶段有准入、退出、回退、观察窗口、资金上限和失败阈值；CR-017 未验证前阻断 scale_up | simulation 通过后直接 small_live | 长期停留 simulation，不设计 live gate | 可先验证技术链路又控制资金风险 | 直接实盘风险高或无法验证真实链路 |
| Q-036 | T 日收盘后信号，T+1 限价 / 保护价；保护带以 raw close 或 broker reference price 的可配置百分比表达；超时未成交默认撤可撤单，单 run 自动重试上限为 1，未成交归因为 cash / unfilled | T+1 市价或最优五档即时成交 | 当日盘中即时信号即时下单 | 控制追单和滑点，保持可解释 | 成交率下降但风险可控；不接受会增加未来函数和价格风险 |
| Q-037 | 盘前 / 盘中 / 盘后对账覆盖委托、成交、持仓、资产、现金；金额 / 持仓 / 委托差异阈值可配置，超阈值 manual_review 或 kill switch；恢复需对账 pass + 人工接管记录 | 只盘后对账 | 只靠 QMT 客户端人工查看 | 异常可早发现，恢复可审计 | 盘中风险持续扩大，事故不可复盘 |
| Q-038 | Linux 研究节点与 Windows QMT 节点解耦；保守默认 signed file drop + ack/error enum，后续可升级本地 RPC；adapter 只在 Windows；运维责任分为 research owner、trading node owner、approver | Linux 直接远程调用 Windows QMT API | 全部迁移到 Windows 单机运行 | 权限最小，失败可降级，节点职责清楚 | 通信延迟和文件投递复杂度上升；不接受会增加凭据和误操作风险 |

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| CP1 场景完整性通过 | 通过 | `process/checks/CP1-CR015-CR016-CR017-USE-CASE-COMPLETENESS.md` | 用户已通过 CP3 审批，接受作为 HLD 评审输入。 |
| CP2 需求基线通过 | 通过 | `process/checks/CP2-CR015-CR016-CR017-REQUIREMENTS-BASELINE.md` | 用户已通过 CP3 审批，接受作为 HLD 评审输入。 |
| CP2 人工 intake approved | 通过 | `checkpoints/CP2-CR015-CR016-CR017-INTAKE-DECISION-BRIEF.md` | 用户已通过 CP3 审批，接受作为 HLD 评审输入。 |
| CP3 自动预检通过 | 通过 | `process/checks/CP3-CR015-CR016-CR017-HLD-CONSISTENCY.md` | 用户已通过 CP3 审批，接受自动预检结论。 |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 是否接受新增 `process/HLD-QMT-TRADING.md` 作为 QMT companion HLD | 通过 | `process/HLD-QMT-TRADING.md` | 用户批准按推荐方案推进。 |
| 2 | 是否接受 CR-017 复权双视图归入 `process/HLD-DATA-LAKE.md` §18 | 通过 | `process/HLD-DATA-LAKE.md` §18 | 用户批准按推荐方案推进。 |
| 3 | 是否接受主 HLD 只同步研究消费和 order intent metadata 边界 | 通过 | `process/HLD.md` §31 | 用户批准按推荐方案推进。 |
| 4 | 是否接受 ADR-053 至 ADR-061 | 通过 | `process/ARCHITECTURE-DECISION.md` | 用户批准按推荐方案推进。 |
| 5 | 是否接受 Q-030 至 Q-038 的推荐方案 | 通过 | 本文件 Decision Brief | 用户批准按推荐方案推进。 |
| 6 | 是否确认 CP3 approve 仍不授权真实发单、抓取、写湖或代码实现 | 通过 | CR / HLD 禁止事项 | 本次审批仅允许进入 Story Plan，不授权实现或真实操作。 |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| HLD / ADR 可作为 Story Plan 输入 | 通过 | `process/HLD.md`、`process/HLD-DATA-LAKE.md`、`process/HLD-QMT-TRADING.md`、`process/ARCHITECTURE-DECISION.md` | 用户已批准进入 Story Plan。 |
| 用户已明确 approve / 修改 / reject | 通过 | 用户回复“@meta-po 通过审批，可以按照你推荐的方案，组织子agent推进项目。” | 结论为 approved。 |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| 主 HLD 增量 | `process/HLD.md` | 通过 | 用户批准。 |
| 数据湖 HLD 增量 | `process/HLD-DATA-LAKE.md` | 通过 | 用户批准。 |
| QMT companion HLD | `process/HLD-QMT-TRADING.md` | 通过 | 用户批准。 |
| ADR 增量 | `process/ARCHITECTURE-DECISION.md` | 通过 | 用户批准。 |
| CP3 自动预检 | `process/checks/CP3-CR015-CR016-CR017-HLD-CONSISTENCY.md` | 通过 | 用户接受 PASS 结论。 |

## 人工审查结果

- 结论：approved
- 审查人：user
- 审查时间：2026-05-28T05:47:14+08:00
- 修改意见：无
- 风险接受项：接受 Q-030 至 Q-038 推荐方案；确认本次 CP3 approve 仅授权进入 Story Plan / CP4，不授权 LLD、代码实现、真实 QMT API、真实发单、真实抓取、真实写湖、publish current pointer 或凭据读取。
