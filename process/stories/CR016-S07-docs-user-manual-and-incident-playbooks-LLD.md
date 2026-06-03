---
story_id: "CR016-S07-docs-user-manual-and-incident-playbooks"
title: "用户文档与 incident playbooks"
story_slug: "docs-user-manual-and-incident-playbooks"
lld_version: "1.0"
tier: "S"
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
  - "process/HLD-QMT-TRADING.md#15"
  - "process/ARCHITECTURE-DECISION.md#ADR-059"
  - "process/ARCHITECTURE-DECISION.md#ADR-060"
  - "process/ARCHITECTURE-DECISION.md#ADR-061"
open_items: 0
---

# LLD: CR016-S07 — 用户文档与 incident playbooks

本文档只定义用户文档和 incident playbook 的文件、章节、静态验证和禁止声明。`confirmed=false` 且 `implementation_allowed=false` 时不得进入实现；文档完成不授权真实模拟盘、实盘、账户查询、发单、撤单或凭据读取。

## 1. Goal

创建 `docs/QMT-INCIDENT-PLAYBOOK.md` 并补充 README / USER-MANUAL 的 staged activation 用户入口，使用户能识别 shadow、simulation、live_readonly、small_live、scale_up 5 个阶段，按 heartbeat fail、risk blocked、recon diff、manual trigger、recovery required 5 类 incident 执行暂停 / 接管 / 恢复流程，同时保持真实操作不授权边界。

## 2. Requirements（Functional / Non-Functional）

### 2.1 Functional

- 文档覆盖 shadow、simulation、live_readonly、small_live、scale_up 5 个阶段。
- incident playbook 覆盖 `heartbeat_fail`、`risk_blocked`、`recon_diff`、`manual_trigger`、`recovery_required` 5 类事件。
- 每类 incident 必须包含 trigger、immediate action、owner、evidence required、recovery gate、rollback target。
- README / USER-MANUAL 必须说明 CP5 / runbook / 文档不授权真实操作。
- 文档 guard 必须扫描 blocked claims：真实操作默认 allowed 次数为 0，VWAP / minute / tick / Level2 / order-match 不得被解除。

### 2.2 Non-Functional

- 安全：文档不得包含真实账号、token、session、cookie、交易密码、真实私有路径或未脱敏资产值。
- 可读性：用户入口简洁，详细事故步骤集中在 incident playbook。
- 可维护：incident type 与 CR016-S03 kill switch reason 枚举一致。
- 可测试：通过 markdown static check 验证章节、事件、禁止声明和敏感值。

## 3. 模块拆分与职责

| 模块 / 文件组 | 职责 | 说明 |
|---|---|---|
| `docs/QMT-INCIDENT-PLAYBOOK.md` | 创建 incident 类型、处理步骤、owner、恢复 gate 和 rollback target | 本 Story primary owner |
| `tests/test_cr016_docs_incident_playbooks.py` | 验证文档章节、blocked claims、无敏感值、真实操作默认 allowed=0 | primary test |
| `README.md` | 增加 staged activation 用户入口和禁止事项摘要 | shared；需与 CR015/CR017 文档串行合并 |
| `docs/USER-MANUAL.md` | 增加用户手册章节，链接 runbook 和 incident playbook | shared；不写真实运行报告 |
| `docs/QMT-SIMULATION-LIVE-RUNBOOK.md` | 引用 incident playbook 和 recovery gate | shared；由 CR016-S04/S07 串行合并 |

## 4. 代码结构与文件影响范围

| 动作 | 文件路径 | 变更内容 |
|---|---|---|
| 创建 | `docs/QMT-INCIDENT-PLAYBOOK.md` | 写 5 类 incident、处理步骤、owner、recovery gate、rollback target 和禁止事项 |
| 创建 | `tests/test_cr016_docs_incident_playbooks.py` | 静态检查 5 stage、5 incident、blocked claims、无敏感值和真实操作默认 allowed=0 |
| 修改 | `README.md` | 增加 staged activation 文档入口和默认不授权声明 |
| 修改 | `docs/USER-MANUAL.md` | 增加用户手册入口、阶段边界、incident playbook 链接 |
| 修改 | `docs/QMT-SIMULATION-LIVE-RUNBOOK.md` | 增加 incident playbook 引用和恢复门说明 |

## 5. 数据模型与持久化设计

本 Story 无新增业务数据模型和无持久化写入。文档 contract 通过 markdown headings / tables 表达。

| 对象 / 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `StageDocSection` | Markdown heading | 5 stage 必须全部存在 | 缺失则 docs test fail |
| `IncidentPlaybookRow` | Markdown table row | incident type、trigger、immediate action、owner、evidence required、recovery gate、rollback target | 5 类事件必填 |
| `RecoveryGateDoc` | Markdown section/table | recon pass、manual takeover record、kill switch state、stage rollback target | 与 S03/S04 合同一致 |
| `ForbiddenClaimScan` | Test result | 默认真实操作 allowed 声明次数为 0 | 文档 guard |
| `SensitiveValueScan` | Test result | 凭据 / session / token / cookie / 账号明文次数为 0 | 文档 guard |

## 6. API / Interface 设计

| 接口 / 入口 | 输入 | 输出 | 调用方 | 说明 |
|---|---|---|---|---|
| `incident playbook contract` | incident type、stage | action list、owner、recovery gate、rollback target | user manual、runbook、docs tests | 测试 T-S07-01 / T-S07-02 覆盖 |
| `user manual stage section` | stage gates、blocked claims | user-facing instructions | README / USER-MANUAL | 测试 T-S07-03 覆盖 |
| `docs guard` | markdown files | forbidden claim scan、sensitive scan | CP7 docs tests | 测试 T-S07-04 至 T-S07-06 覆盖 |

错误暴露使用稳定枚举：`stage_doc_missing`、`incident_playbook_missing`、`recovery_gate_missing`、`default_authorization_forbidden`、`unsupported_claim_unblocked`、`sensitive_value_forbidden`。

## 7. 核心处理流程

1. 创建 incident playbook，先声明真实操作不授权和 later-gated 边界。
2. 写入 5 stage 概览，说明每个阶段的 allowed / blocked claims。
3. 写入 5 类 incident 表格：trigger、immediate action、owner、evidence required、recovery gate、rollback target。
4. README 和 USER-MANUAL 只提供用户入口、阶段说明和链接，不复制敏感值。
5. runbook 引用 incident playbook，形成 simulation / live runbook 与 incident playbook 的双向导航。
6. 静态测试扫描章节、事件、恢复门、blocked claims、默认授权声明和敏感值。

## 8. 技术设计细节

- 关键规则：文档测试使用 exact heading / table columns；不使用模糊匹配判断合规。
- blocked claims：文档必须继续声明真实 VWAP、minute、tick、Level2、order-match 不因 QMT 接入自动解除。
- 依赖复用：CR016-S04/S05/S06 的 runbook / live gate / scale_up gate 合同作为文档输入。
- 兼容性处理：README / USER-MANUAL 与 CR015/CR017 文档共享文件，开发时需串行合并。
- 图示类型选择：文档 contract 不需要 Mermaid；如实现阶段新增流程图，必须保持不含敏感值。

## 9. 安全与性能设计

| 维度 | 设计措施 | 验证方式 |
|---|---|---|
| 安全 | 文档禁止敏感值；禁止默认授权真实操作；保留 unsupported claims blocked | markdown static scan |
| 性能 | 文档检查按文件行数线性扫描 | pytest 静态检查 |
| 可维护 | incident type 与 kill switch reason 一致，减少文档 / 代码偏差 | exact enum scan |

## 10. 测试设计

| 测试场景 | 前置条件 | 操作 | 预期结果 | 验证方式 |
|---|---|---|---|---|
| T-S07-01 文档覆盖 5 stage | docs 存在 | 扫描 stage headings | shadow/simulation/live_readonly/small_live/scale_up 均存在 | pytest |
| T-S07-02 incident 覆盖 5 类事件 | playbook 存在 | 扫描 incident table | 5 类事件均存在 | pytest |
| T-S07-03 recovery gate 有人工接管 | playbook 存在 | 扫描 recovery section | 包含 recon pass + manual takeover record | pytest |
| T-S07-04 文档无默认授权 | markdown files | forbidden claim scan | 真实操作默认 allowed 次数为 0 | pytest |
| T-S07-05 unsupported claims 未解除 | markdown files | blocked claim scan | VWAP/minute/tick/Level2/order-match 仍 blocked | pytest |
| T-S07-06 无敏感值 | markdown files | sensitive scan | 凭据、账号、session、cookie 明文次数为 0 | pytest |

## 11. 实施步骤

| TASK-ID | 动作 | 目标文件 | 详细描述 | 对应测试 |
|---|---|---|---|---|
| CR016-S07-T1 | 创建 | `docs/QMT-INCIDENT-PLAYBOOK.md` | 写 5 stage、5 incident、owner、action、recovery gate 和 rollback target | T-S07-01 至 T-S07-03 |
| CR016-S07-T2 | 修改 | `README.md` / `docs/USER-MANUAL.md` | 增加 staged activation 与 incident playbook 用户入口、禁止事项 | T-S07-03 至 T-S07-06 |
| CR016-S07-T3 | 修改 | `docs/QMT-SIMULATION-LIVE-RUNBOOK.md` | 增加 incident playbook 引用和恢复门链接 | T-S07-02 / T-S07-03 |
| CR016-S07-T4 | 创建 | `tests/test_cr016_docs_incident_playbooks.py` | 写 markdown contract、blocked claims 和敏感字段静态测试 | T-S07-01 至 T-S07-06 |

## 12. 风险、难点与预研建议

| 风险 / 难点 | 影响 | 缓解措施 / 预研建议 |
|---|---|---|
| 文档误解除真实操作门控 | 可能被用户当成授权 | forbidden claim scan 保证默认授权次数为 0 |
| incident 枚举与 kill switch 偏离 | 运行时和文档不一致 | exact enum scan 与 S03 reason 对齐 |
| 文档共享文件冲突 | CR015/CR017 同时修改 README / USER-MANUAL | CP5 后串行合并，保留 merge_owner |

### OPEN / Spike 跟踪

| ID | 类型（OPEN / Spike） | 问题 | 下一动作 | 责任方 |
|---|---|---|---|---|
| 无 | N/A | 无未决项；真实 incident 演练和真实运行报告不属于本 Story | 后续按 per-run 授权和 QA 策略执行 | meta-po / user |

## 13. 回滚与发布策略

- 发布方式：CP5 全量人工确认后，等待 S04/S05/S06 合同冻结，再串行更新文档和测试。
- 回滚触发条件：文档缺 5 stage / 5 incident、缺 recovery gate、包含敏感值或默认授权真实操作。
- 回滚动作：回退文档修改，Story 回到 LLD 修订态；涉及真实操作授权边界变更时交回 meta-po。

## 14. Definition of Done

- [ ] 14 个章节全部填写完成。
- [ ] 文档覆盖 5 个 stage 和 5 类 incident。
- [ ] `confirmed=false` 且 `implementation_allowed=false` 时不进入实现。
- [ ] 文档中真实操作默认 allowed 次数为 0。
- [ ] 文档无敏感值，unsupported claims 未被解除。
- [ ] OPEN / Spike 已清点为无。

## 人工确认区

> **CP5 — Story LLD 可实现性门**
> meta-dev 先写入 `process/checks/CP5-CR016-S07-docs-user-manual-and-incident-playbooks-LLD-IMPLEMENTABILITY.md` 自动预检结果。
> meta-po 收齐全部目标 Story 的 LLD、CP4 自动预检摘要和 CP5 自动预检后，再生成并提示用户审查 `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md`。
> 用户统一确认全部目标 Story 的 LLD 后，仍需满足当前 Wave、依赖门控和文件所有权门控；文档仍不授权真实运行。

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
