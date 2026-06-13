---
status: ready
version: "1.0"
release_artifact_profile: compact
release_decision: READY_WITH_RISK
cr_id: CR-044
---

# CR044 Release Notes

## 1. 摘要

| 项目 | 内容 |
|---|---|
| 版本 | `cr044-goldminer-admission-alpha` |
| 发布结论 | `READY_WITH_RISK` |
| 发布范围 | Goldminer Simulation Admission 的离线 blocked-first / fixture-only 工程资产 |
| 主要风险 | L3+ 未授权；readonly 字段未真实验证；`simulation_ready=false`、`live_ready=false` 保持不变 |

## 2. 版本号决策

| 项目 | 内容 |
|---|---|
| 当前版本 | `cr043-spike-complete` |
| 目标版本 | `cr044-goldminer-admission-alpha` |
| 变更类型 | alpha |
| 兼容性 | compatible |
| 推荐原因 | 新增本地离线 admission guard、redaction、kill switch、reconciliation evidence 和测试，不启用真实 broker runtime。 |

## 3. 新增能力 / 用户可见变化

| Change ID | 内容 | 影响用户 | 来源 |
|---|---|---|---|
| REL-CR044-01 | `engine/broker_adapter.py` 新增 CR044 Goldminer admission guard 和 capability state helper | 可审计地证明未授权时 fail-closed | CR044-S01/S02 |
| REL-CR044-02 | 新增 readonly field static/unknown mapping，明确不提升为 `real_verified` | 防止把静态候选误读为真实账户能力 | CR044-S03 |
| REL-CR044-03 | 新增 submit/cancel kill switch fixture 合同 | 保证未授权时 submit/cancel 只返回 blocked，无副作用 | CR044-S04 |
| REL-CR044-04 | 新增 redacted reconciliation evidence builder | 支持对账证据脱敏审查和 manual review route | CR044-S05 |
| REL-CR044-05 | 新增 CR044 fixture/static 测试和质量报告 | 可复跑 13 个 CR042+CR044 目标测试 | CR044-S06 / CP7 |

## 4. 行为变化 / 修复问题

| Change ID | 类型 | 内容 | 用户影响 |
|---|---|---|---|
| REL-CR044-06 | behavior-change | `GoldminerStubBrokerAdapter.cancel_order()` 现在返回 CR044 blocked result，而不是沿用通用 unsupported 行为 | 更清晰地区分未授权 submit/cancel 与通用 adapter unsupported |
| REL-CR044-07 | quality-fix | `.gitignore` 反忽略 `docs/quality/*.md`，避免正式质量报告被 `quality/` 数据湖忽略规则误伤 | 质量报告可进入版本跟踪；不放开数据湖 `quality/` 分区 |

## 5. 破坏性变更

| Breaking ID | 是否存在 | 内容 | 迁移引用 |
|---|---|---|---|
| BR-CR044-01 | no | 未启用真实 broker runtime；未改变 PaperBrokerAdapter 既有通过路径 | `docs/release/MIGRATION.md` |

## 6. 安装与升级

| 场景 | 方式 | 验证证据 |
|---|---|---|
| 本地代码 / 测试交付 | 无安装脚本变更；通过 uv 运行 pytest | `docs/release/DEPLOY-CHECKLIST.md` |
| 质量报告跟踪 | `.gitignore` 允许 `docs/quality/*.md` | `git check-ignore -v docs/quality/*CR044.md` 应不再命中 |

## 7. 迁移说明

| 是否需要迁移 | 影响对象 | 说明 |
|---|---|---|
| no | 状态 schema / 配置 / 安装路径 / 数据存储 | 本轮为新增离线 helper、测试和过程证据，无数据迁移。 |

## 8. 已知问题与风险

| Risk ID | 严重度 | 状态 | 处理 |
|---|---|---|---|
| CR044-RISK-01 | HIGH | accepted-pending-CP8 | L3+ credential/account permission 未授权；CP8 不授权真实运行。 |
| CR044-RISK-02 | MEDIUM | accepted-pending-CP8 | readonly mapping 仍为 `static_candidate` / `unknown_broker_field`，不是 `real_verified`。 |
| CR044-RISK-03 | HIGH | accepted-pending-CP8 | `simulation_ready=false`、`live_ready=false` 是本轮交付事实，不能在发布说明中提升。 |
| CR044-RISK-04 | LOW | accepted-pending-CP8 | S06 当前为 technical-note，后续若新增可执行 guard/script/schema 需升级 full-lld。 |

## 9. 回滚方式

| 回滚触发 | 回滚入口 | 说明 |
|---|---|---|
| CR044 helper 或测试导致回归 | `docs/release/ROLLBACK.md` | 回滚 `engine/broker_adapter.py` 的 CR044 新增块、`tests/test_cr044_goldminer_admission_guard.py` 和 CR044 过程证据；不涉及数据恢复。 |

## 10. 参考链接

| 类型 | 路径 |
|---|---|
| Release Context | `process/release/RELEASE-CONTEXT.yaml` |
| Verification Report | `docs/quality/VERIFICATION-REPORT-CR044.md` |
| Test Report | `docs/quality/TEST-REPORT-CR044.md` |
| Review | `docs/quality/REVIEW-CR044.md` |
| CP7 | `process/checks/CP7-CR044-FIXTURE-STATIC-VERIFICATION-DONE.md` |
