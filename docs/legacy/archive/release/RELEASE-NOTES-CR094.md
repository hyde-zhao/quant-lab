---
status: ready
cr_id: CR-094
release_artifact_profile: minimal
release_decision: READY
---

# CR094 Release Notes

## 摘要

| 项目 | 内容 |
|---|---|
| 版本 | `cr094-strict-warnings-ready` |
| 发布结论 | `READY` |
| 发布范围 | CR tracking warning cleanup / strict-warnings readiness |
| 用户可见变化 | `meta-flow check cr-tracking --project-root . --strict-warnings` 当前可 exit 0 |

## 变化

| Change ID | 内容 | 影响 |
|---|---|---|
| REL-CR094-01 | 新增 CR093 follow-up tracking 台账，补齐历史 `source=cp8-follow-up` tracking rows | strict-warnings 不再因缺 row 失败 |
| REL-CR094-02 | 主 CLI checker 将历史嵌套 `active_change` 视为审计历史，不作为 strict warning | strict-warnings 聚焦 current state |
| REL-CR094-03 | CR094 active 状态同步到 `STATE.md` 和 `CR-INDEX.yaml` | 当前 CR tracking 可解释 |

## 已知限制

| ID | 内容 | 处理 |
|---|---|---|
| R-CR094-01 | 未处理 CR093-FU-02 standalone checker 与主 CLI 输出收敛 | 保持 candidate-not-started |
| R-CR094-02 | 未启动 subagent，按当前工具策略 inline 执行 | CP8 中作为低风险决策项确认 |
