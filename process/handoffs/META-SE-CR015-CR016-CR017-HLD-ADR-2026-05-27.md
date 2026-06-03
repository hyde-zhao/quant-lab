---
handoff_id: "META-SE-CR015-CR016-CR017-HLD-ADR-2026-05-27"
from_agent: "meta-po"
to_agent: "meta-se"
created_at: "2026-05-27T23:10:03+08:00"
status: "completed"
workflow_id: "local_backtest-cr015-cr016-cr017"
change_ids:
  - "CR-015"
  - "CR-016"
  - "CR-017"
dispatch:
  mode: "spawned"
  agent_id: "019e69ff-0806-7741-a078-3f126c84b31b"
  thread_id: "019e69ff-0806-7741-a078-3f126c84b31b"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-27T23:10:03+08:00"
  resumed_at: ""
  completed_at: "2026-05-27T23:29:20+08:00"

## 完成摘要

- 修改 `process/HLD.md`：新增 CR-015 / CR-016 / CR-017 拆分判定和 §31，回链 QMT companion HLD。
- 修改 `process/HLD-DATA-LAKE.md`：新增 §18，承载 CR-017 复权双视图设计。
- 新增 `process/HLD-QMT-TRADING.md`：承载 CR-015 / CR-016 QMT 交易接入与阶段激活 HLD。
- 修改 `process/ARCHITECTURE-DECISION.md`：新增 ADR-053 至 ADR-061，补齐 AD-Q50 至 AD-Q58。
- 新增 `process/checks/CP3-CR015-CR016-CR017-HLD-CONSISTENCY.md`，结论 PASS。
- 未进入 Story Plan、LLD 或代码实现。
---

# Meta-SE Handoff: CR-015 / CR-016 / CR-017 HLD / ADR

## 目标

基于已批准的 CR-015 / CR-016 / CR-017 需求基线，输出可 CP3 评审的高层设计和架构决策。不得进入 Story Plan、LLD 或代码实现。

## 输入

| 输入 | 路径 |
|---|---|
| CP2 intake 决策稿 | `checkpoints/CP2-CR015-CR016-CR017-INTAKE-DECISION-BRIEF.md` |
| CP1 自动检查 | `process/checks/CP1-CR015-CR016-CR017-USE-CASE-COMPLETENESS.md` |
| CP2 自动检查 | `process/checks/CP2-CR015-CR016-CR017-REQUIREMENTS-BASELINE.md` |
| 场景基线 | `process/USE-CASES.md` v1.7 |
| 需求基线 | `process/REQUIREMENTS.md` v1.8 |
| 澄清日志 | `process/CLARIFICATION-LOG.md`，重点 Q-030 至 Q-038 |
| CR-015 | `process/changes/CR-015-QMT-TRADING-FOUNDATION-2026-05-27.md` |
| CR-016 | `process/changes/CR-016-QMT-SIMULATION-LIVE-ACTIVATION-2026-05-27.md` |
| CR-017 | `process/changes/CR-017-ADJUSTMENT-POLICY-DUAL-VIEW-SUPPORT-2026-05-27.md` |
| 主 HLD | `process/HLD.md` |
| 数据湖 HLD | `process/HLD-DATA-LAKE.md` |
| ADR | `process/ARCHITECTURE-DECISION.md` |

## 已批准边界

| 决策 | 结论 |
|---|---|
| 推进顺序 | 混合推进：CR-017 先冻结复权与 raw 交易价边界；CR-015 foundation 可并行设计；CR-016 真实激活后置。 |
| QMT 接入 | Windows QMT / MiniQMT 节点 + XtQuant 外部 Python API + OMS + QMT adapter；策略不得直接调用 QMT API。 |
| CR-015 foundation | 建立订单状态机、外置 broker lake、pre-trade hard block；默认仅 shadow / dry-run / mock，不授权真实发单。 |
| CR-017 adjustment | `prices_raw` + `adj_factor` 为事实源；独立派生 `prices_qfq`、`prices_hfq`、`returns_adjusted`；qfq 必须记录 `as_of_trade_date`；QMT 使用 raw/broker price。 |
| CR-016 activation | `shadow -> QMT 模拟盘 -> 实盘只读 -> 小资金实盘 -> 放大资金`；T 日收盘后信号，T+1 限价 / 保护价；必须有 runbook、对账、kill switch、per-run 授权。 |

## 必须冻结的 CP3 问题

| ID | 问题 |
|---|---|
| Q-030 | qfq/hfq 公式、provider `adj_factor` 字段方向、复权因子可用时间和异常价格解释。 |
| Q-031 | dataset/view schema、旧 qfq 兼容入口和迁移策略。 |
| Q-032 | broker lake root、schema、保留策略、脱敏字段和研究数据湖边界。 |
| Q-033 | OMS 状态机与 QMT / mock adapter 事件映射、unknown / timeout / partial fill 处理。 |
| Q-034 | pre-trade hard risk gate 的规则、阈值、配置位置和失败行为。 |
| Q-035 | 模拟盘、实盘只读、小资金实盘、资金放大的阶段准入 / 退出 / 回退阈值。 |
| Q-036 | T+1 限价 / 保护价、超时撤单、失败重试和未成交处理。 |
| Q-037 | 盘前 / 盘中 / 盘后对账阈值、责任归属和 kill switch 触发 / 恢复条件。 |
| Q-038 | Linux 研究节点与 Windows QMT / MiniQMT 交易节点之间的部署、通信、鉴权、隔离和运维责任。 |

## 任务

1. 按 `hld-designer` skill 规则执行 HLD 拆分判断：
   - 如果 QMT 交易层足以成为独立 companion HLD，创建 `process/HLD-QMT-TRADING.md` 或等价 companion HLD，并在 `process/HLD.md` frontmatter / 修订记录中回链。
   - CR-017 数据湖复权派生层优先追加到 `process/HLD-DATA-LAKE.md`；研究消费和 QMT raw 执行价格影响需要在主 HLD 或 QMT companion 中交叉引用。
2. 更新 `process/ARCHITECTURE-DECISION.md`：
   - 新增 CR-015 / CR-016 / CR-017 ADR。
   - 每个 ADR 必须有决策、理由、接受影响、不接受影响、备选方案和回退点。
3. 为 Q-030 至 Q-038 输出 CP3 Decision Brief 输入：
   - 每个问题至少 1 个备选方案，能给 2 个时给 2 个。
   - 明确推荐方案、接受影响、不接受影响、风险和后续 Story / LLD 影响。
4. 生成 CP3 自动预检结果：
   - `process/checks/CP3-CR015-CR016-CR017-HLD-CONSISTENCY.md`
   - 必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables。
5. 不生成 Story Plan，不修改 `process/STORY-BACKLOG.md` 或 `process/DEVELOPMENT-PLAN.yaml`；这些等 CP3 approved 后再做。

## 输出约束

- 允许修改 / 新增：
  - `process/HLD.md`
  - `process/HLD-DATA-LAKE.md`
  - `process/HLD-QMT-TRADING.md`（如拆分判断需要）
  - `process/ARCHITECTURE-DECISION.md`
  - `process/checks/CP3-CR015-CR016-CR017-HLD-CONSISTENCY.md`
- 不允许修改：
  - `process/STORY-BACKLOG.md`
  - `process/DEVELOPMENT-PLAN.yaml`
  - `process/stories/**`
  - 代码、测试、README、docs、pyproject、uv.lock、数据、reports。
- 不读取或输出 `.env` / token / QMT 账户 / session / cookie / 交易密码。
- 不执行真实抓取、写湖、publish、QMT API、发单或撤单。
