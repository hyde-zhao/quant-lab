---
status: ready
version: "1.0"
release_artifact_profile: compact
release_decision: READY_WITH_RISK
cr_id: CR-092
---

# CR092 Feedback

## 1. 反馈回流入口

| Feedback ID | 类型 | 来源 | 内容摘要 | 分流目标 | follow-up tracking 候选 | 状态 |
|---|---|---|---|---|---|---|
| FB-CR092-01 | scenario-gap | user / runtime evidence | 用户提供实际模拟账户 evidence 文件后，需要只读取该文件并运行 checker | verification / follow-up | yes | candidate |
| FB-CR092-02 | new-requirement | user | 用户要求执行真实只读 runtime smoke | runtime authorization gate | yes | candidate |
| FB-CR092-03 | new-requirement | user | 用户要求 NAS package exchange | CR091-FU-02 | yes | candidate |
| FB-CR092-04 | new-requirement | user | 用户要求 submit/cancel、order-write、simulation/live | CR091-FU-03 | yes | candidate |
| FB-CR092-05 | tech-debt | cr-tracking | CR019 / CR025 历史账本旧账仍导致 consistency check exit 1 | CR091-FU-04 | yes | candidate |

## 2. 发布后观察计划

| Signal ID | 观察信号 | 观察方式 | 触发阈值 | 分流 |
|---|---|---|---|---|
| OBS-CR092-01 | checker 拒收用户 evidence | checker JSON / user feedback | >=1 confirmed false positive | CR092-FU-01 |
| OBS-CR092-02 | checker 放过敏感字段 | review / user feedback | >=1 confirmed false negative | security fix CR |
| OBS-CR092-03 | 用户要求真实 runtime smoke | user request | explicit authorization intent | per-run runtime gate |
| OBS-CR092-04 | NAS 需求出现 | user request | explicit NAS intent | CR091-FU-02 |
| OBS-CR092-05 | cr-tracking 旧账影响后续门禁 | `meta-flow check cr-tracking` | blocks active CR | CR091-FU-04 |

## 3. 台账边界

`FEEDBACK.md` 是反馈回流入口，不是正式 follow-up tracking 台账。`follow-up tracking 候选=yes` 的条目必须由 CP8 分流写入 `process/changes/CR-*-FOLLOW-UP-TRACKING-YYYY-MM-DD.md`，并同步 `STATE.md.cr_tracking` 后，才可作为后续 CR 候选推进。

默认不生成独立 `POST-RELEASE-OBSERVATION.md`；本轮 `release_artifact_profile=compact`。
