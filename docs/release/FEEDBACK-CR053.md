---
status: "final"
version: "1.0"
change_id: "CR-053"
release_artifact_profile: "full"
release_decision: "READY_WITH_RISK"
created_at: "2026-06-14T13:05:00+08:00"
---

# Feedback CR053

## 1. 反馈回流入口

| Feedback ID | 类型 | 来源 | 内容摘要 | 分流目标 | follow-up tracking 候选 | 状态 |
|---|---|---|---|---|---|---|
| FB-CR053-01 | risk_acceptance | CP8 | 真实 NAS path / capacity / permission 未验证。 | risk_acceptance / runtime_authorization | yes | candidate |
| FB-CR053-02 | risk_acceptance | CP8 | backup / restore rehearsal 和 rollback_ref 仍是 planned-only。 | risk_acceptance / follow-up | yes | candidate |
| FB-CR053-03 | follow_up_tracking | CP8 | CR058 manual review / rollback gates 为未来前置，不自动启动。 | follow-up-tracking | yes | candidate |
| FB-CR053-04 | scope-boundary | user / review | 用户希望把静态 inventory 升级为真实 NAS / lake / repo-local 迁移。 | new CR / runtime_authorization | yes | candidate |
| FB-CR053-05 | safety-boundary | review | 任一后续流程把 CR053 close 误读为真实执行授权。 | incident / checkpoint correction | yes | candidate |

## 2. 发布后观察计划

| Signal ID | 观察信号 | 观察方式 | 触发阈值 | 分流 |
|---|---|---|---|---|
| OBS-CR053-01 | CR053 close 被误读为真实迁移授权 | 后续 CR / handoff / checkpoint 文档审查 | 出现 mount / scan / copy / move / lake write / trading runtime 的授权暗示 | blocking / runtime_authorization |
| OBS-CR053-02 | CR058 在 rollback_ref 或 manual_review 未关闭前启动 | CR058 checkpoint / development plan 审查 | 任一前置缺失仍进入 dev / execution | blocking |
| OBS-CR053-03 | NAS root map 需要真实路径绑定 | 用户反馈 / 后续 planning | 用户提供 NAS 路径并要求验证 | CR060+ candidate |
| OBS-CR053-04 | `MARKET_DATA_LAKE_ROOT` 需要切换 | 用户反馈 / data lake planning | 出现真实 lake move / publish 诉求 | independent data lake migration CR |
| OBS-CR053-05 | 交易主机需要 package import 或 QMT / MiniQMT runtime | 用户反馈 / trading planning | 出现账户查询、连接或交易诉求 | trading runtime authorization CR |

## 3. 台账边界

`FEEDBACK-CR053.md` 是反馈入口，不是正式变更单。需要推进的候选项已进入 `process/changes/CR-053-FOLLOW-UP-TRACKING-2026-06-14.md`，但除非用户在后续门禁明确批准，否则不得自动创建 CR058 / CR060+、不得授权真实迁移，也不得执行凭据、数据湖、交易或 git remote 操作。

## 4. 分流原则

| 类别 | 处理方式 | owner | 关闭条件 |
|---|---|---|---|
| `blocking` | 立即停止后续执行，回到 host-orchestrator 人工门禁。 | host-orchestrator | 阻断原因被移除或用户明确拒绝推进。 |
| `risk_acceptance` | 汇入 CP8 Decision Brief，由用户接受或退回返工。 | human / host-orchestrator | DQ-CP8-CR053-01 明确结果。 |
| `follow_up_candidate` | 进入 follow-up tracking，不自动启动。 | host-orchestrator | 后续用户明确转正式 CR 或取消。 |
| `not_authorized` | 保持禁止；不得由 CR053 approve 继承。 | host-orchestrator | 独立 runtime_authorization 或 security decision。 |
| `cancelled_or_deferred` | 保留记录，等待重访条件。 | owner TBD | 重访条件满足或用户取消。 |
