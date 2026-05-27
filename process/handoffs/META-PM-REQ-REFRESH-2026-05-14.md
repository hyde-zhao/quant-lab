---
handoff_id: "META-PM-REQ-REFRESH-2026-05-14"
created_at: "2026-05-14"
created_by: "meta-po"
target_agent: "meta-pm"
current_phase: "requirement-clarification"
status: "assigned"
cr_required: false
---

# meta-pm 需求阶段文档刷新分派

## 分派结论

当前仍处于 `requirement-clarification`，`process/USE-CASES.md` 与 `process/REQUIREMENTS.md` 均为 draft，`confirmed=false`，且尚未生成 HLD、ADR、Story 或代码实现。因此，本轮用户补充内容属于需求确认前的草稿增量澄清，不创建 CR，不推进到 `solution-design`。

`meta-pm` 负责刷新需求阶段文档；`meta-po` 只维护状态、分派和检查点，不直接改写需求正文。

## 必须读取的上下文

| 文件 | 用途 |
|---|---|
| `process/STATE.md` | 确认当前阶段、不得推进状态 |
| `process/REQUEST.md` | 原始目标与第一版范围 |
| `process/USE-CASES.md` | 场景草稿，需增量刷新到下一版本 |
| `process/REQUIREMENTS.md` | 需求草稿，需增量刷新到下一版本 |
| `process/CLARIFICATION-LOG.md` | 追加 HLD 前必须确认的问题和默认待确认项 |
| `checkpoints/REQUIREMENTS-CHECKPOINT.md` | 刷新完成后由 meta-po 更新，不由 meta-pm 标记确认 |

## 本轮必须纳入的用户结论

### 第一版必须守住的硬约束

- 复权口径一致。
- T 日收盘后生成信号，T+1 或之后成交。
- 任一数据字段的 `available_at` 必须小于等于 `decision_time`。
- 历史窗口不足的股票必须剔除，不得参与排名。
- 缺失价格或无成交不得静默填充。
- 固定当前沪深 300 股票池必须显式标记为非 PIT，并披露幸存者偏差。
- 报告 metadata 必须强制输出限制项。

### 第一版可先不精确建模但必须警示的限制

- 完整停牌状态。
- 涨跌停撮合。
- 新股上市初期特殊规则。
- 退市整理与摘牌。
- ST 历史状态。
- 财报披露日。
- 沪深 300 历史成分变化。

### 后续增强优先级

- PIT universe provider。
- 交易状态表。
- 涨跌停约束。
- 事件 `available_at`。
- 偏差审计报告。

### HLD 前必须确认的问题

- 默认复权口径。
- 成交假设。
- 股票池表达。
- 缺失价/停牌处理。
- 数据字段最低要求。
- 涨跌停字段是否强制。
- 未来函数校验层级。
- 财报是否第一版 Out of Scope。

## meta-pm 修改范围

| 文件 | 操作 | 修改要点 |
|---|---|---|
| `process/USE-CASES.md` | 增量更新 | 升级版本号；在修订记录追加 2026-05-14；补强 UC-01、UC-02、UC-06 中的数据时点、复权、缺失数据、非 PIT 股票池、报告限制项和后续真实性增强；同步更新 Out of Scope 与边界说明。 |
| `process/REQUIREMENTS.md` | 增量更新 | 升级版本号；追加或修订 P0 需求，覆盖复权口径一致、T 日信号/T+1 成交、`available_at <= decision_time`、历史窗口不足剔除、缺失价格/无成交不静默填充、非 PIT/幸存者偏差标记、报告 metadata 限制项；追加 P1/P2 增强需求。 |
| `process/CLARIFICATION-LOG.md` | 追加记录 | 追加本轮澄清记录；新增 HLD 前必须确认的问题，建议编号从 Q-004 起，状态保持 OPEN 或 REQUIRED_FOR_HLD，不能标记 confirmed。 |

## 建议需求落点

| 主题 | 建议落点 |
|---|---|
| 复权口径一致 | `REQUIREMENTS.md` 的数据与报告需求；`USE-CASES.md` UC-01/UC-02 前置条件 |
| T 日收盘后信号、T+1 或之后成交 | `REQUIREMENTS.md` 的策略时点与组合成交需求；`USE-CASES.md` UC-02 处理逻辑 |
| `available_at <= decision_time` | `REQUIREMENTS.md` 新增未来函数防护需求；`CLARIFICATION-LOG.md` 新增 HLD 前确认校验层级 |
| 历史窗口不足剔除 | `REQUIREMENTS.md` 动量排名验收条件；`USE-CASES.md` UC-02 异常/过滤规则 |
| 缺失价格/无成交不静默填充 | `REQUIREMENTS.md` 数据质量与组合成交异常需求；`USE-CASES.md` UC-01/UC-02 |
| 固定沪深 300 非 PIT 与幸存者偏差 | 修订现有 REQ-003/REQ-031 或新增报告 metadata 需求；`USE-CASES.md` 股票池偏差边界 |
| 必须警示但不精确建模项 | `REQUIREMENTS.md` Out of Scope 与风险假设；`USE-CASES.md` UC-06 |
| 后续增强优先级 | `REQUIREMENTS.md` 里程碑 M3 或新增增强需求；`USE-CASES.md` UC-06 |
| HLD 前确认项 | `CLARIFICATION-LOG.md` Q-004 起；需求检查点重点确认清单 |

## 输出约束

- 保持需求阶段状态为 draft，不能把 `confirmed` 或 `ready_for_design` 改为 true。
- 不创建 HLD、ADR、Story 或开发计划。
- 不删除 v1.0/v1.1 的历史修订记录；只能追加 v1.2 或下一版本记录。
- 不用 CR 包裹本轮修改；理由是需求尚未人工确认，尚无已确认基线被变更。
- 刷新完成后通知 `meta-po`，由 `meta-po` 刷新 `checkpoints/REQUIREMENTS-CHECKPOINT.md` 并继续等待用户确认。

## 完成判定

- `process/USE-CASES.md` 与 `process/REQUIREMENTS.md` 已增量升版，修订记录完整。
- `process/CLARIFICATION-LOG.md` 已追加 HLD 前必须确认项。
- 第一版必须守住的硬约束、可延后但必须警示的限制、后续增强优先级均可从文档中追溯。
- `process/STATE.md` 仍停留在 `requirement-clarification`。
