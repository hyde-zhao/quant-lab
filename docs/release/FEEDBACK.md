---
status: ready
version: "1.0"
release_artifact_profile: compact
release_decision: READY_WITH_RISK
cr_id: CR-099
---

# CR099 Feedback

## 1. 反馈回流入口

| Feedback ID | 类型 | 来源 | 内容摘要 | 分流目标 | follow-up tracking 候选 | 状态 |
|---|---|---|---|---|---|---|
| FB-CR099-01 | scenario-gap | runtime evidence | 当前 run 是 zero-position path；非空持仓脱敏未证明 | CR097-FU-01 | yes | candidate |
| FB-CR099-02 | scenario-gap | runtime evidence | 当前 run 不证明交易日路径 | CR097-FU-01 | yes | candidate |
| FB-CR099-03 | reliability | runtime attempt | 首次 run 因 `session_expired` 阻断，重启 gateway session 后通过 | CR099-FU-01 | yes | candidate |
| FB-CR099-04 | new-requirement | user | 用户要求 NAS package exchange | CR091-FU-02 | yes | candidate |
| FB-CR099-05 | new-requirement | user | 用户要求 submit/cancel、order-write、simulation/live | ORDER-WRITE-FU | yes | candidate |

## 2. 发布后观察计划

| Signal ID | 观察信号 | 观察方式 | 触发阈值 | 分流 |
|---|---|---|---|---|
| OBS-CR099-01 | non-empty positions 需要证明 | user request / trading day evidence | explicit authorization intent | CR097-FU-01 |
| OBS-CR099-02 | session_expired 复发 | runtime evidence / user report | >=1 recurrence | CR099-FU-01 |
| OBS-CR099-03 | collector / checker false positive | checker JSON / user feedback | >=1 confirmed false positive | checker fix CR |
| OBS-CR099-04 | NAS 需求出现 | user request | explicit NAS intent | CR091-FU-02 |
| OBS-CR099-05 | order-write / live 需求出现 | user request | explicit trading intent | ORDER-WRITE-FU |

## 3. 台账边界

`FEEDBACK.md` 是反馈回流入口，不是正式 follow-up tracking 台账。`follow-up tracking 候选=yes` 的条目必须由 CP8 分流写入 `process/changes/CR-098-FOLLOW-UP-TRACKING-2026-06-19.md` 或后续专门 tracking，并同步 `STATE.md.cr_tracking` 后，才可作为后续 CR 候选推进。

默认不生成独立 `POST-RELEASE-OBSERVATION.md`；本轮 `release_artifact_profile=compact`。

## CR100 Addendum - Feedback

| Feedback ID | 类型 | 来源 | 内容摘要 | 分流目标 | follow-up tracking 候选 | 状态 |
|---|---|---|---|---|---|---|
| FB-CR100-01 | risk | CP8 | 真实 NAS path/mount/permission/publish/pull/copy/check 未验证 | future NAS validation gate | yes | candidate |
| FB-CR100-02 | usability | review | forbidden filename 规则可能误拒合法说明文件 | CR100 fix candidate | yes | candidate |
| FB-CR100-03 | authorization | user | 若需要真实 NAS 验证，必须另起独立 gate | future NAS authorization | yes | candidate |

CR100 feedback 不授权自动启动真实 NAS gate；只有用户明确选择并授权后才可推进。
