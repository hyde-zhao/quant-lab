---
status: ready
version: "1.0"
release_artifact_profile: compact
release_decision: READY_WITH_RISK
cr_id: CR-092
---

# CR092 Rollback

## 1. 回滚摘要

| 项目 | 内容 |
|---|---|
| 回滚目标版本 | `cr091-offline-runner-ready-with-risk` |
| 回滚范围 | CR092 guide/template/checker/tests/quality/release/process evidence |
| 是否涉及数据恢复 | no |
| 是否存在不可回滚项 | no |
| 决策人 | human |

## 2. 回滚触发条件

| Trigger ID | 条件 | 监控 / 证据 | 决策人 |
|---|---|---|---|
| RB-CR092-01 | checker 合同被确认不适合模拟账户 evidence | 用户反馈 / review | human |
| RB-CR092-02 | release 文档误导为 runtime 已授权或已成功 | CP8 review / user feedback | human |
| RB-CR092-03 | 后续真实 evidence gate 决定采用不同 schema | future CR decision | human |

## 3. 回滚步骤

| Step | 操作 | 前置条件 | 验证 | 风险 |
|---|---|---|---|---|
| 1 | 撤销 CR092 新增 guide/template/checker/tests/quality/release/process evidence | 用户明确要求回滚 | `git diff --check` / targeted tests 不再引用 CR092 | 回滚会丢失 readiness guardrail |
| 2 | 将 STATE / CR-INDEX 回退到 CR091 follow-up candidate 或标记 CR092 cancelled/superseded | 新 CR 或人工门禁批准 | `meta-flow check cr-tracking` 仅剩既有旧账 | 需谨慎避免破坏历史追溯 |
| 3 | 保留 CR091 closure 和 CR091-FU-04 ledger hygiene 旧账 | 始终保留 | CR091 follow-up tracking 可读 | 无 |

## 4. 回滚验证

| 验证项 | 方法 | 结果 |
|---|---|---|
| 安装 / 加载恢复 | N/A，本轮无 installer / runtime service | N/A |
| 状态 / 配置恢复 | 检查 `process/STATE.md`、`process/changes/CR-INDEX.yaml` | pending only if rollback requested |
| 敏感边界 | 确认未读取 runtime / NAS / credentials / real account | PASS in current delivery |

## 5. 不可回滚项

| 对象 | 是否存在 | 原因 | 处理 |
|---|---|---|---|
| runtime side effect | no | 本轮未执行真实 runtime | N/A |
| NAS side effect | no | 本轮未访问 NAS | N/A |
| credential / account read side effect | no | 本轮未读取凭据或真实账户 | N/A |
