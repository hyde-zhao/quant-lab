---
status: ready
version: "1.0"
release_artifact_profile: compact
release_decision: READY_WITH_RISK
cr_id: CR-093
---

# CR093 Release Notes

## 摘要

| 项目 | 内容 |
|---|---|
| 版本 | `cr093-ledger-hygiene-ready-with-risk` |
| 发布结论 | `READY_WITH_RISK` |
| 发布范围 | CR tracking checker 语义修复、CR093 单元测试、CR019 tracking 最小说明和过程证据 |
| 核心结果 | `meta-flow check cr-tracking --project-root .` exit 0；CR019 / CR025 旧账不再阻断当前 CR093 |
| 剩余风险 | `R-CR093-01`、`R-CR093-02` |

## 用户可见变化

| Change ID | 内容 | 影响 |
|---|---|---|
| REL-CR093-01 | `meta-flow check cr-tracking` 将 nested/history `active_change` 视为 audit warning，而不是当前 active CR 阻断 | 历史 CR025 / CR092 文本不再误伤当前 CR093 |
| REL-CR093-02 | `closed-current-delivery`、`closed-spike-complete`、`closed-cp8-approved`、`cancelled-user-deleted` 等状态按语义归一 | CR019 old follow-up tracking 不再因状态口径旧账失败 |
| REL-CR093-03 | 新增 CR093 单元测试 | 覆盖状态等价、history warning-only 和真实 current conflict 失败路径 |

## 兼容性

| 项目 | 结论 |
|---|---|
| 破坏性变更 | 无 |
| 配置 / 环境变量 | 无 |
| 安装 / 部署 | 无 |
| 数据迁移 | 无 |
| runtime 行为 | 无；未启动 runtime |

## 已知风险

| Risk ID | 等级 | 状态 | 处理 |
|---|---|---|---|
| R-CR093-01 | LOW | pending-CP8-acceptance | broader `source=cp8-follow-up` warning-only 项保留，不阻断本轮 DoD |
| R-CR093-02 | LOW | pending-CP8-acceptance | standalone checker warning 明细少于主 CLI，后续可另起 checker convergence |

## 参考

| 类型 | 路径 |
|---|---|
| Release Context | `process/release/RELEASE-CONTEXT-CR093.yaml` |
| CP6 | `process/checks/CP6-CR093-LEDGER-HYGIENE-CONSISTENCY-CODING-DONE.md` |
| CP7 | `process/checks/CP7-CR093-LEDGER-HYGIENE-CONSISTENCY-VERIFICATION-DONE.md` |
| Verification | `docs/features/CR093-ledger-hygiene/VERIFICATION.md` |
