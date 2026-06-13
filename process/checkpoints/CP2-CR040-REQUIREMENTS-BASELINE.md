---
checkpoint_id: "CP2"
checkpoint_name: "CR040 Requirements Baseline"
type: "auto_then_manual"
status: "approved"
owner: "meta-po"
created_at: "2026-06-10T22:45:00+08:00"
reviewed_by: "user"
reviewed_at: "2026-06-10T22:46:00+08:00"
auto_check_result: "process/checks/CP2-CR040-REQUIREMENTS-BASELINE.md"
auto_final_authorization: false
target:
  phase: "requirement-clarification"
  story_id: ""
  artifacts:
    - "process/changes/CR-040-QMT-ROUTE-DELETION-BACKTRADER-PAPER-SIM-GOLDMINER-ADAPTER-2026-06-10.md"
---

# CP2 CR040 Requirements Baseline 人工审查

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---|---|
| `process/checks/CP2-CR040-REQUIREMENTS-BASELINE.md` | PASS | 0 | CR040 范围、删除路线、新路线与不授权边界已明确。 |

## Decision Brief

### Context Capsule Summary

| 字段 | 内容 |
|---|---|
| capsule 路径 | `process/context/CP2-CR040-REQUIREMENT-CONTEXT.yaml` |
| capsule 状态 | ready |
| read_profile | minimal |
| 默认读取策略 | 先读 capsule；仅在缺失、冲突、字段不足、人工审计或深度评审时读取完整文档 |
| 全文档读取扩展 | 0 次 |
| 缺失 / waived 理由 | N/A |

### Decision Collection Coverage

| 来源 | 路径 / 对象 | 扫描状态 | 候选问题数 | 纳入待决策数 | 分类 / N/A 原因 |
|---|---|---:|---:|---:|---|
| STATE pending queue | `process/STATE.md` | scanned | 0 | 0 | 当前无结构化 pending queue；本轮从 CR 与 discussion 聚合。 |
| 自动预检结果 | `process/checks/CP2-CR040-REQUIREMENTS-BASELINE.md` | scanned | 0 | 0 | 无阻断项。 |
| discussion log | `process/discussions/CP2-CR040-SCENARIO-DISCUSSION-LOG.md` | scanned | 3 | 2 | 2 项需要用户接受推荐方案。 |
| 正式 CR | `process/changes/CR-040-*.md` | scanned | 2 | 2 | 路线拆分与运行授权边界纳入决策。 |

### 待人工决策清单

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣分析 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|---|
| DQ-CP2-CR040-01 | scope | 是否接受 CR040 只关闭 / 删除 QMT 路线并规划新路线，而不直接写 paper simulation 代码？ | 接受；CR040 只做路线与状态变更，代码拆到 CR041。 | A: 在 CR040 中直接实现 paper simulation；B: 暂停新路线，仅关闭 QMT。 | 推荐方案门禁清楚、可追溯；A 会混合删除和新增实现，风险高；B 会阻断策略研究向本地模拟盘推进。 | 影响后续 Story 拆分、验证范围和 CR tracking。 | 若用户要求直接实现，则重新生成 CR040 范围与 CP3/CP5；若暂停，则 CR040 关闭为路线删除。 |
| DQ-CP2-CR040-02 | runtime_authorization | 是否授权任何 broker、Backtrader、掘金量化、QMT 或账号相关运行？ | 不授权；当前只允许静态文档、状态同步和本地代码阅读。 | A: 允许安装 Backtrader；B: 允许掘金 SDK Spike 前置安装。 | 推荐方案最小权限且不产生交易副作用；A/B 会引入依赖、凭据和运行边界，需要单独 CR。 | 防止误读为下单、撤单、账户查询或真实仿真授权。 | 未来如需真实运行，必须另起 CR043/CR044 并逐 run 授权。 |

### 用户视角复述

如果你回复 `approve`，表示你接受以上 2 项推荐方案：CR040 只确认 QMT 路线删除和新路线规划，paper simulation 代码实现另起 CR041；当前不授权任何 broker、Backtrader、掘金、QMT、账户、凭据、下单或撤单操作。

自动终验授权：false。CR040 的 CP2/CP3 通过不构成 CP8 终验授权，也不构成任何运行授权。

### 推荐回复

- `approve`
- `修改: <具体修改点>`
- `reject`

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| 自动预检 PASS | 待审查 | `process/checks/CP2-CR040-REQUIREMENTS-BASELINE.md` |  |
| 待决策项已列出 | 待审查 | 本文件 Decision Brief |  |

## Checklist

| # | 检查项 | 审查结果 | 备注 |
|---|---|---|---|
| 1 | 是否接受 CR040 范围边界 | 通过 | 用户回复“同意”。 |
| 2 | 是否接受不授权边界 | 通过 | 用户回复“同意”；不授权项保持生效。 |
| 3 | 是否同意后续优先 CR041 API-less Paper Simulation Runner | 通过 | 用户回复“同意”。 |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 人工结论为 approved | PASS | 用户回复“同意” | CR040 路线门禁可关闭；CR041 仍需正式启动 CR 与独立门禁。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| CP2 人工审查稿 | `process/checkpoints/CP2-CR040-REQUIREMENTS-BASELINE.md` | approved | 用户已同意推荐方案。 |

## 人工审查结果

| 字段 | 内容 |
|---|---|
| 结论 | approved |
| 审查人 | user |
| 审查时间 | 2026-06-10T22:46:00+08:00 |
| 备注 | 用户回复“同意”，按 approve 处理；不授权 broker / Backtrader / 掘金 / QMT / 账户 / 凭据 / 下单 / 撤单 / simulation/live 运行。 |
