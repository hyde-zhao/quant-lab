---
checkpoint_id: "CP2"
checkpoint_name: "CR041 Requirements Baseline"
type: "auto_then_manual"
status: "approved"
owner: "meta-po"
created_at: "2026-06-10T23:05:00+08:00"
reviewed_by: "user"
reviewed_at: "2026-06-10T23:05:00+08:00"
auto_check_result: "process/checks/CP2-CR041-REQUIREMENTS-BASELINE.md"
auto_final_authorization: false
target:
  phase: "requirement-clarification"
  story_id: ""
  artifacts:
    - "process/changes/CR-041-API-LESS-PAPER-SIMULATION-RUNNER-2026-06-10.md"
---

# CP2 CR041 Requirements Baseline 人工审查

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---|---|
| `process/checks/CP2-CR041-REQUIREMENTS-BASELINE.md` | PASS | 0 | CR041 日频 realistic paper simulation 需求已明确。 |

## Decision Brief

### Context Capsule Summary

| 字段 | 内容 |
|---|---|
| capsule 路径 | `process/context/CP2-CR041-REQUIREMENT-CONTEXT.yaml` |
| capsule 状态 | ready |
| read_profile | minimal |
| 默认读取策略 | 先读 capsule；仅在缺失、冲突、字段不足、人工审计或深度评审时读取完整文档 |
| 全文档读取扩展 | 0 次 |
| 缺失 / waived 理由 | N/A |

### Decision Collection Coverage

| 来源 | 路径 / 对象 | 扫描状态 | 候选问题数 | 纳入待决策数 | 分类 / N/A 原因 |
|---|---|---:|---:|---:|---|
| 用户显式确认 | 当前对话 | scanned | 3 | 3 | 用户回复“同意”。 |
| 自动预检结果 | `process/checks/CP2-CR041-REQUIREMENTS-BASELINE.md` | scanned | 0 | 0 | 无阻断项。 |
| discussion log | `process/discussions/CP2-CR041-SCENARIO-DISCUSSION-LOG.md` | scanned | 4 | 3 | 3 项进入已确认决策。 |
| 正式 CR | `process/changes/CR-041-*.md` | scanned | 3 | 3 | 真实度目标、成交模型和运行授权边界纳入决策。 |

### 待人工决策清单

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣分析 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|---|
| DQ-CP2-CR041-01 | scope | 是否接受 CR041 目标为日频 realistic paper simulation（L2-minus），不承诺盘口级真实撮合？ | 接受 L2-minus：日频真实约束模拟。 | A: 简单 paper trading；B: 直接追求 minute/tick/Level2。 | 推荐方案能覆盖主要交易约束且可在 CR041 内落地；A 不够真实；B 需要额外数据和权限。 | 决定 CR041 的验收边界。 | 若后续要求盘口级真实撮合，转后续 minute/tick/Level2 Spike。 |
| DQ-CP2-CR041-02 | implementation | 是否接受 T+1 raw open 成交、raw close 估值、fixed bps 滑点、participation cap、A 股基础账户规则作为第一版基线？ | 接受该基线。 | A: T+1 close；B: VWAP proxy；C: 无滑点/无容量约束。 | 推荐方案避免未来函数且可复跑；A/B 可作为后续配置；C 过度乐观。 | 决定成交和成本真实性。 | 若数据具备 minute/VWAP，可在后续 CR 增强。 |
| DQ-CP2-CR041-03 | runtime_authorization | 是否保持无 broker / 无 SDK / 无账户 / 无订单运行授权？ | 保持不授权。 | A: 允许 Backtrader runtime；B: 允许掘金 SDK Spike。 | 推荐方案权限最小；A/B 需要独立 CR。 | 防止误读为真实 simulation/live 授权。 | 未来真实平台仿真必须走 CR043/CR044。 |

### 用户视角复述

用户回复“同意”，表示接受以上 3 项推荐方案。该确认不授权任何 broker、Backtrader、掘金、QMT、账户、凭据、下单、撤单或 simulation/live 运行。

自动终验授权：false。CR041 CP2 通过不构成 CP8 终验授权，也不构成任何运行授权。

### 推荐回复

- `approve`
- `修改: <具体修改点>`
- `reject`

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| 自动预检 PASS | PASS | `process/checks/CP2-CR041-REQUIREMENTS-BASELINE.md` | 通过。 |
| 待决策项已列出 | PASS | 本文件 Decision Brief | 通过。 |

## Checklist

| # | 检查项 | 审查结果 | 备注 |
|---|---|---|---|
| 1 | 是否接受 L2-minus 真实度目标 | 通过 | 用户回复“同意”。 |
| 2 | 是否接受 T+1 raw open / raw close / 成本 / 滑点 / 容量 / A 股账户规则 | 通过 | 用户回复“同意”。 |
| 3 | 是否接受不授权边界 | 通过 | 用户回复“同意”。 |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 人工结论为 approved | PASS | 用户回复“同意” | 可进入 CP3 HLD。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| CP2 人工审查稿 | `process/checkpoints/CP2-CR041-REQUIREMENTS-BASELINE.md` | approved | 用户已同意。 |

## 人工审查结果

| 字段 | 内容 |
|---|---|
| 结论 | approved |
| 审查人 | user |
| 审查时间 | 2026-06-10T23:05:00+08:00 |
| 备注 | 用户回复“同意”；不授权任何 broker / SDK / 账户 / 凭据 / 下单 / 撤单 / simulation/live。 |
