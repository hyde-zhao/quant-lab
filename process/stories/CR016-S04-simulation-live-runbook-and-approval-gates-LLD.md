---
story_id: "CR016-S04-simulation-live-runbook-and-approval-gates"
title: "simulation / live runbook 与审批门"
story_slug: "simulation-live-runbook-and-approval-gates"
lld_version: "1.0"
tier: "M"
status: "approved"
confirmed: true
implementation_allowed: true
real_operation_authorized: false
created_by: "meta-dev"
created_at: "2026-05-28T06:24:15+08:00"
confirmed_by: "user"
confirmed_at: "2026-05-28T07:03:27+08:00"
shared_fragments:
  - "process/HLD-QMT-TRADING.md#11"
  - "process/ARCHITECTURE-DECISION.md#ADR-059"
  - "process/ARCHITECTURE-DECISION.md#ADR-060"
  - "process/ARCHITECTURE-DECISION.md#ADR-061"
open_items: 0
---

# LLD: CR016-S04 — simulation / live runbook 与审批门

本文档只定义 simulation、live_readonly、small_live 的 runbook 与审批门合同。`confirmed=false` 且 `implementation_allowed=false` 时不得进入实现；runbook 完成不等于真实模拟盘或实盘授权。

## 1. Goal

创建 `docs/QMT-SIMULATION-LIVE-RUNBOOK.md` 和文档检查测试，明确 staged activation 的启动、审批、异常处理、对账、kill switch、暂停 / 恢复、回滚 7 类 P0 章节，以及 per-run approval gate 的必需字段和阻断行为。

## 2. Requirements（Functional / Non-Functional）

### 2.1 Functional

- runbook 必须覆盖启动、审批、异常处理、对账、kill switch、暂停 / 恢复、回滚 7 类章节。
- approval gate 必须校验 per-run authorization 字段覆盖率 100%。
- 文档必须声明：runbook、CP5 或 Story 状态均不自动授权真实操作。
- 缺任一 P0 章节时 `runbook_status=fail`。
- rollback playbook 必须按 incident type 和 stage 输出 owner、action、rollback target、recovery gate。
- CR016-S05/S06 的 live_readonly / small_live / scale_up 只作为 later-gated 后续门控引用。

### 2.2 Non-Functional

- 安全：文档不得包含真实账号、token、session、cookie、交易密码或未脱敏路径。
- 可审计：审批字段、owner role、rollback target 使用固定表格，方便 CP7 静态检查。
- 可维护：README / USER-MANUAL 只提供入口和禁止事项，详细操作集中在 runbook。
- 可测试：通过 markdown contract 测试验证章节、字段和禁止声明。

## 3. 模块拆分与职责

| 模块 / 文件组 | 职责 | 说明 |
|---|---|---|
| `docs/QMT-SIMULATION-LIVE-RUNBOOK.md` | 创建 staged activation runbook、approval gate、rollback playbook | 本 Story primary owner |
| `tests/test_cr016_runbook_approval_gates.py` | 验证 runbook 章节、授权字段、禁止默认授权声明和敏感字段 | primary test |
| `docs/QMT-TRADING-RUNBOOK.md` | 连接 CR015 foundation runbook 与 CR016 activation runbook | shared；需与 CR015-S07 串行合并 |
| `README.md` / `docs/USER-MANUAL.md` | 提供用户入口、阶段边界和禁止事项 | shared；不写真实运行报告 |

## 4. 代码结构与文件影响范围

| 动作 | 文件路径 | 变更内容 |
|---|---|---|
| 创建 | `docs/QMT-SIMULATION-LIVE-RUNBOOK.md` | 写 staged activation runbook、approval gate、rollback / recovery matrix |
| 创建 | `tests/test_cr016_runbook_approval_gates.py` | 静态检查 P0 章节、审批字段、禁止默认授权和敏感字段 |
| 修改 | `docs/QMT-TRADING-RUNBOOK.md` | 增加 CR016 runbook 链接、simulation 准入入口和 CR015/CR016 边界 |
| 修改 | `README.md` | 增加 QMT staged activation 文档入口和默认不授权声明 |
| 修改 | `docs/USER-MANUAL.md` | 增加用户可读的阶段门控、审批和事故恢复入口 |

## 5. 数据模型与持久化设计

本 Story 无新增业务数据模型和无持久化写入。文档 contract 通过 markdown 表格表达。

| 对象 / 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `RunbookSection` | Markdown heading/table | 7 类 P0 章节必须存在 | 缺任一章节 `runbook_status=fail` |
| `ApprovalGateFields` | Markdown table | 字段覆盖 authorization_id、mode、strategy_id、run_id、stage、capital_limit、order_scope、approver、approved_at、expires_at、rollback_plan_ref | 只记录脱敏摘要 |
| `RollbackMatrix` | Markdown table | incident type、stage、owner、action、rollback target、recovery gate | 不执行真实动作 |
| `OwnerRole` | Enum text | `research_owner|trading_node_owner|approver` | 与 ADR-061 一致 |
| `ForbiddenClaimScan` | Test result | 默认授权真实操作声明次数为 0 | 文档 guard 消费 |

## 6. API / Interface 设计

| 接口 / 入口 | 输入 | 输出 | 调用方 | 说明 |
|---|---|---|---|---|
| `runbook readiness checker` | markdown sections、target stage | `pass|fail`、missing sections | tests、stage gate docs guard | 测试 T-S04-01 / T-S04-02 覆盖 |
| `approval gate contract` | per-run authorization summary 字段表 | `pass|missing_fields` | stage gate、runbook | 测试 T-S04-03 覆盖 |
| `rollback playbook contract` | incident type、stage | rollback steps、owner、recovery gate | incident playbook、operator | 测试 T-S04-04 覆盖 |
| `forbidden claim scan` | markdown files | forbidden claim count | CP7 static docs test | 测试 T-S04-05 覆盖 |

错误暴露使用稳定枚举：`runbook_section_missing`、`approval_field_missing`、`default_authorization_forbidden`、`sensitive_value_forbidden`、`rollback_owner_missing`。

## 7. 核心处理流程

1. 文档实现创建 `docs/QMT-SIMULATION-LIVE-RUNBOOK.md`，先写明“不授权真实操作”的总边界。
2. 写入 5 个阶段路径和 7 类 P0 runbook 章节。
3. 写入 per-run authorization 字段表和审批记录格式，字段缺失即 blocked。
4. 写入 incident / rollback matrix：不同 stage 下的暂停、恢复、回退目标和 owner。
5. README / USER-MANUAL 只链接 runbook 并说明阶段边界，不复制敏感材料。
6. 文档测试扫描章节、字段、禁止默认授权声明和敏感词。

## 8. 技术设计细节

- 关键规则：runbook readiness checker 以 heading exact match 和必需表格列检查为默认策略，不使用模糊匹配。
- 文档边界：runbook 描述操作步骤和审批字段，但所有真实动作使用“需要后续 per-run 授权”措辞。
- 依赖复用：CR016-S01/S02/S03 的 gate、reconciliation、kill switch 输出作为 runbook 章节输入。
- 兼容性处理：README / USER-MANUAL 的共享修改需与 CR015/CR017 文档 Story 串行合并。
- 图示类型选择：当前为文档 contract，无跨模块异步流程，不新增 Mermaid 图。

## 9. 安全与性能设计

| 维度 | 设计措施 | 验证方式 |
|---|---|---|
| 安全 | 文档禁止账号、密码、token、session、cookie 和真实私有路径；禁止默认授权语句 | markdown static scan |
| 性能 | 文档检查按文件行数线性扫描 | pytest 静态检查 |
| 可用性 | runbook 使用固定章节和表格，owner / action 可直接定位 | 文档 contract 测试 |

## 10. 测试设计

| 测试场景 | 前置条件 | 操作 | 预期结果 | 验证方式 |
|---|---|---|---|---|
| T-S04-01 runbook 覆盖 7 类章节 | runbook 存在 | 扫描 headings | 7 类 P0 章节均存在 | pytest |
| T-S04-02 缺 P0 章节 fail | fixture 缺 kill switch 章节 | readiness checker | `runbook_status=fail` | pytest |
| T-S04-03 approval 字段覆盖率 100% | 字段表存在 | 扫描必需字段 | 无 missing fields | pytest |
| T-S04-04 rollback matrix 完整 | incident matrix 存在 | 扫描 owner/action/recovery gate | 均存在 | pytest |
| T-S04-05 文档不自动授权 | markdown files | forbidden claim scan | 默认授权真实操作声明次数为 0 | pytest |
| T-S04-06 无敏感值 | markdown files | sensitive scan | 凭据 / session / 账号明文出现次数为 0 | pytest |

## 11. 实施步骤

| TASK-ID | 动作 | 目标文件 | 详细描述 | 对应测试 |
|---|---|---|---|---|
| CR016-S04-T1 | 创建 | `docs/QMT-SIMULATION-LIVE-RUNBOOK.md` | 写 5 stage、7 类章节、approval gate、rollback matrix 和禁止事项 | T-S04-01 至 T-S04-04 |
| CR016-S04-T2 | 创建 | `tests/test_cr016_runbook_approval_gates.py` | 写 markdown contract、敏感字段和 forbidden claim 静态测试 | T-S04-01 至 T-S04-06 |
| CR016-S04-T3 | 修改 | `docs/QMT-TRADING-RUNBOOK.md` | 连接 CR015 foundation 与 CR016 activation runbook | T-S04-01 / T-S04-05 |
| CR016-S04-T4 | 修改 | `README.md` / `docs/USER-MANUAL.md` | 增加用户入口、阶段边界和默认不授权声明 | T-S04-05 / T-S04-06 |

## 12. 风险、难点与预研建议

| 风险 / 难点 | 影响 | 缓解措施 / 预研建议 |
|---|---|---|
| 文档把 runbook 写成授权 | 可能绕过 per-run approval | forbidden claim scan 强制真实操作默认授权次数为 0 |
| 文档共享文件冲突 | README / USER-MANUAL 与 CR015/CR017 并行修改冲突 | CP5 后由 merge_owner 串行合并 |
| runbook 章节不可测试 | CP7 难以验收 | 使用 exact heading 和表格列 contract |

### OPEN / Spike 跟踪

| ID | 类型（OPEN / Spike） | 问题 | 下一动作 | 责任方 |
|---|---|---|---|---|
| 无 | N/A | 无未决项；真实运行审批流程的具体审批人由 per-run 授权填写 | CP5 后仍需逐 run 授权 | meta-po / user |

## 13. 回滚与发布策略

- 发布方式：CP5 全量人工确认后，等待 CR016-S01/S02/S03 合同稳定，再串行更新文档和测试。
- 回滚触发条件：文档包含默认授权真实操作、敏感值、缺 P0 章节或与 ADR-059/060/061 冲突。
- 回滚动作：回退文档修改，Story 回到 LLD 修订态；涉及审批流程变更时交回 meta-po。

## 14. Definition of Done

- [ ] 14 个章节全部填写完成。
- [ ] runbook 7 类 P0 章节和 approval gate 字段均可静态验证。
- [ ] `confirmed=false` 且 `implementation_allowed=false` 时不进入实现。
- [ ] 文档不包含敏感值，不声明默认授权真实操作。
- [ ] README / USER-MANUAL 只提供入口和边界，不复制凭据或真实运行材料。
- [ ] OPEN / Spike 已清点为无。

## 人工确认区

> **CP5 — Story LLD 可实现性门**
> meta-dev 先写入 `process/checks/CP5-CR016-S04-simulation-live-runbook-and-approval-gates-LLD-IMPLEMENTABILITY.md` 自动预检结果。
> meta-po 收齐全部目标 Story 的 LLD、CP4 自动预检摘要和 CP5 自动预检后，再生成并提示用户审查 `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md`。
> 用户统一确认全部目标 Story 的 LLD 后，仍需满足当前 Wave、依赖门控、文件所有权门控和 per-run authorization 方可进入实现或运行。

**CP5 checklist 摘要**：

| # | 检查项 | 状态 | 证据 |
|---|---|---|---|
| 1 | LLD 覆盖 AC | 待检查 | 第 2 / 10 / 14 节 |
| 2 | 与 HLD / ADR 一致 | 待检查 | 第 3 / 8 / 12 节 |
| 3 | 文件影响范围明确 | 待检查 | 第 4 / 11 节 |
| 4 | 接口契约完整 | 待检查 | 第 6 节 |
| 5 | 测试与 dev_gate 可计算 | 待检查 | 第 10 / 14 节 |

**人工审查结果回填**：

- 结论：`approved | changes_requested | rejected`
- 审查人：
- 审查时间：
- 修改意见：
- 风险接受项：
