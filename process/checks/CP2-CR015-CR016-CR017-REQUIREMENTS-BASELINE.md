---
checkpoint_id: "CP2"
checkpoint_name: "CR-015/CR-016/CR-017 Requirements Baseline"
type: "auto_precheck"
status: "PASS"
owner: "meta-po"
created_at: "2026-05-27T23:10:03+08:00"
checked_at: "2026-05-27T23:10:03+08:00"
target:
  phase: "requirement-clarification"
  story_id: ""
  artifacts:
    - "process/REQUIREMENTS.md"
    - "process/USE-CASES.md"
    - "checkpoints/CP2-CR015-CR016-CR017-INTAKE-DECISION-BRIEF.md"
manual_checkpoint: "checkpoints/CP2-CR015-CR016-CR017-INTAKE-DECISION-BRIEF.md"
---

# CP2 CR-015 / CR-016 / CR-017 Requirements Baseline 检查结果

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| CP1 场景检查通过 | PASS | `process/checks/CP1-CR015-CR016-CR017-USE-CASE-COMPLETENESS.md` | 结论 PASS。 |
| 需求文档存在 | PASS | `process/REQUIREMENTS.md` | 文档已更新到 `version: "1.8"`。 |
| 人工 intake 决策已批准 | PASS | `checkpoints/CP2-CR015-CR016-CR017-INTAKE-DECISION-BRIEF.md` | 用户已 approve 全部推荐方案。 |

## Checklist

| # | 检查项 | 状态 | 证据 | 处理意见 |
|---|---|---|---|---|
| 1 | CR-017 需求已落地 | PASS | `REQ-098` 至 `REQ-104` | 覆盖 raw/qfq/hfq/returns_adjusted、qfq as-of、single-policy gate、QMT raw price、权限边界。 |
| 2 | CR-015 需求已落地 | PASS | `REQ-105` 至 `REQ-111` | 覆盖 QMT adapter、order intent、OMS state、broker lake、pre-trade hard risk、mock/shadow、凭据脱敏。 |
| 3 | CR-016 需求已落地 | PASS | `REQ-112` 至 `REQ-120` | 覆盖阶段激活、runbook、per-run 授权、T+1 限价/保护价、对账、kill switch、资金放大、blocked claims。 |
| 4 | 验证与 CP3 输入已落地 | PASS | `REQ-121`、`REQ-122` | 覆盖验证矩阵和 CP3 必须冻结的开放问题。 |
| 5 | 旧需求基线保留 | PASS | `REQ-001` 至 `REQ-097` | 未覆盖旧基线。 |
| 6 | 无实现授权误写 | PASS | `REQ-104`、`REQ-110`、`REQ-114` | 明确未授权真实抓取、写湖、发单、撤单、账户写操作和凭据读取。 |
| 7 | REQUIRED_FOR_CP3 问题完整 | PASS | `Q-030` 至 `Q-038` | 全部有 HLD/ADR 决策归属。 |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 可进入 HLD / ADR 设计 | PASS | `REQ-098` 至 `REQ-122` | CP3 仍需冻结 Q-030..Q-038。 |
| CP2 人工确认已回填 | PASS | `checkpoints/CP2-CR015-CR016-CR017-INTAKE-DECISION-BRIEF.md` | `结论：approved`。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| 需求文档 | `process/REQUIREMENTS.md` | PASS | v1.8 |
| 场景文档 | `process/USE-CASES.md` | PASS | v1.7 |
| 人工决策稿 | `checkpoints/CP2-CR015-CR016-CR017-INTAKE-DECISION-BRIEF.md` | PASS | approved |

## 结论

- 结论：`PASS`
- 阻断项：无
- 豁免项：无
- 下一步：拉起 `meta-se` 进入 CR-015 / CR-016 / CR-017 HLD / ADR。
