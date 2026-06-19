---
status: ready
version: "1.0"
release_artifact_profile: compact
release_decision: READY_WITH_RISK
cr_id: CR-092
---

# CR092 Release Notes

## 1. 摘要

| 项目 | 内容 |
|---|---|
| 版本 | `cr092-readonly-runtime-smoke-readiness-alpha` |
| 发布结论 | `READY_WITH_RISK` |
| 发布范围 | 真实只读 runtime smoke 的 readiness / evidence guardrail：manual guide、模拟账户 evidence template、静态 checker、测试和验证报告 |
| 主要风险 | `R-CR092-CP7-001..004`；真实 runtime 未证明，实际模拟账户 evidence 未验证，未启动独立 meta-qa 子代理，CR019/CR025 旧账仍存在 |

## 2. 版本号决策

| 项目 | 内容 |
|---|---|
| 当前版本 | `cr091-offline-runner-ready-with-risk` |
| 目标版本 | `cr092-readonly-runtime-smoke-readiness-alpha` |
| 变更类型 | alpha |
| 兼容性 | compatible |
| 推荐原因 | 新增 readiness / evidence guardrail，不启用真实 runtime，不改变交易执行语义。 |

## 3. 新增能力 / 用户可见变化

| Change ID | 内容 | 影响用户 | 来源 |
|---|---|---|---|
| REL-CR092-01 | 新增真实只读 runtime smoke manual guide | 用户可按边界准备模拟账户 evidence | CR092 CP6 |
| REL-CR092-02 | 新增模拟账户 evidence template | 用户可用固定 schema 填写 health / capabilities / query_positions_readonly 证据 | CR092 CP6 |
| REL-CR092-03 | 新增显式单文件静态 checker | 可在不接触 runtime / NAS / 凭据的前提下检查 evidence 是否越界 | CR092 CP6 / CP7 |
| REL-CR092-04 | 新增 CP7 verification / test / review / fixes 报告 | 明确 readiness 通过但 runtime 未证明 | CR092 CP7 |

## 4. 行为变化 / 修复问题

| Change ID | 类型 | 内容 | 用户影响 |
|---|---|---|---|
| REL-CR092-05 | behavior-change | CR091-FU-01 已升级为正式 CR092 并推进到 CP8 readiness | 后续真实 runtime smoke 必须另起逐 run 授权 |
| REL-CR092-06 | quality-fix | checker 允许 `forbidden_counters.*` 字段名存在，但要求值为 0 | 避免模板所需计数字段被误判为敏感 marker |

## 5. 破坏性变更

| Breaking ID | 是否存在 | 内容 | 迁移引用 |
|---|---|---|---|
| BR-CR092-01 | no | 未改变既有 runner / gateway / strategy 执行语义；未启用真实 runtime | `docs/release/MIGRATION.md` |

## 6. 安装与升级

| 场景 | 方式 | 验证证据 |
|---|---|---|
| 本地静态 checker | `uv run --python 3.11 python scripts/check_cr092_simulated_evidence.py --evidence <file> --json` | `docs/quality/CR092-REAL-QMT-READONLY-RUNTIME-SMOKE-TEST-REPORT.md` |
| 单元测试 | `uv run --python 3.11 pytest -q tests/test_cr092_simulated_evidence_checker.py` | `process/checks/CP7-CR092-READONLY-RUNTIME-SMOKE-VERIFICATION-DONE.md` |

## 7. 迁移说明

| 是否需要迁移 | 影响对象 | 说明 |
|---|---|---|
| no | 状态 schema / 配置 / 安装路径 / 数据存储 | 本轮新增文档、模板、checker 和测试；无自动迁移。 |

## 8. 已知问题与风险

| Risk ID | 严重度 | 状态 | 处理 |
|---|---|---|---|
| R-CR092-CP7-001 | HIGH | pending-CP8-acceptance | 静态 CP7 不证明真实 runtime readiness；真实 smoke 需独立逐 run 授权。 |
| R-CR092-CP7-002 | MEDIUM | pending-CP8-acceptance | 当前只验证模板，未读取用户实际模拟账户 evidence。 |
| R-CR092-CP7-003 | MEDIUM | pending-CP8-acceptance | 本轮未启动独立 meta-qa 子代理，使用 host-orchestrator inline fallback。 |
| R-CR092-CP7-004 | LOW | pending-CP8-acceptance | CR019 / CR025 历史账本旧账仍由 CR091-FU-04 单独处理。 |

## 9. 回滚方式

| 回滚触发 | 回滚入口 | 说明 |
|---|---|---|
| checker 或模板需要撤回 | `docs/release/ROLLBACK.md` | 移除 CR092 guide/template/checker/tests/quality/release/process evidence；不涉及数据恢复或 runtime 停机。 |

## 10. 参考链接

| 类型 | 路径 |
|---|---|
| Release Context | `process/release/RELEASE-CONTEXT.yaml` |
| Verification Report | `docs/quality/CR092-REAL-QMT-READONLY-RUNTIME-SMOKE-VERIFICATION-REPORT.md` |
| Test Report | `docs/quality/CR092-REAL-QMT-READONLY-RUNTIME-SMOKE-TEST-REPORT.md` |
| Review | `docs/quality/CR092-REAL-QMT-READONLY-RUNTIME-SMOKE-REVIEW.md` |
| CP7 | `process/checks/CP7-CR092-READONLY-RUNTIME-SMOKE-VERIFICATION-DONE.md` |
