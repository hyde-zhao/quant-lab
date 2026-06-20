---
status: ready
version: "1.0"
release_artifact_profile: compact
release_decision: READY_WITH_RISK
cr_id: CR-101
---

# CR099 Release Notes

## 1. 摘要

| 项目 | 内容 |
|---|---|
| 版本 | `cr099-runner-real-readonly-smoke-runtime-pass-rc` |
| 发布结论 | `READY_WITH_RISK` |
| 发布范围 | runner real readonly smoke per-run authorization、CR099 collector、redacted evidence checker、runtime PASS evidence |
| 主要风险 | 当前 evidence 为空持仓路径；非空持仓 / 交易日复测需要独立 follow-up |

## 2. 版本号决策

| 项目 | 内容 |
|---|---|
| 当前版本 | `cr098-runner-readonly-integration-ready-with-risk` |
| 目标版本 | `cr099-runner-real-readonly-smoke-runtime-pass-rc` |
| 变更类型 | rc |
| 兼容性 | compatible |
| 推荐原因 | 新增受控真实只读 smoke 证据和本地 collector；不改变交易写语义，不启用 NAS / publish / simulation/live。 |

## 3. 新增能力 / 用户可见变化

| Change ID | 内容 | 影响用户 | 来源 |
|---|---|---|---|
| REL-CR099-01 | 新增 CR099 WSL client-side collector | 可在逐 run 授权范围内采集 runner -> Windows gateway 只读 smoke 脱敏 evidence | CR099 CP7 |
| REL-CR099-02 | runner real readonly smoke 已通过 | health / capabilities / query_positions_readonly 均通过，forbidden counters 全 0 | CP7 runtime rerun |
| REL-CR099-03 | CR099 evidence checker 覆盖 runtime evidence | evidence schema、raw payload、forbidden counters 均可校验 | CP6 / CP7 |
| REL-CR099-04 | CR098-FU-01 转为正式 CR099 并完成当前目标 | 后续非空 / 交易日复测作为独立候选，不阻塞当前交付 | CP8 |

## 4. 行为变化 / 修复问题

| Change ID | 类型 | 内容 | 用户影响 |
|---|---|---|---|
| REL-CR099-05 | behavior-change | CR098 的“真实 runner runtime 未证明”风险在 CR099 当前授权范围内关闭 | runner 已证明能消费 Windows gateway readonly path |
| REL-CR099-06 | risk-boundary | session_expired 首次阻断后，用户重启 gateway session，复跑成功 | 记录了失败恢复路径，不扩大权限 |

## 5. 破坏性变更

| Breaking ID | 是否存在 | 内容 | 迁移引用 |
|---|---|---|---|
| BR-CR099-01 | no | 未改变 runner / gateway / strategy 执行语义；未启用交易写或 NAS | `docs/release/MIGRATION.md` |

## 6. 安装与升级

| 场景 | 方式 | 验证证据 |
|---|---|---|
| CR099 evidence checker | `uv run --python 3.11 python scripts/check_cr099_redacted_evidence.py --evidence <file> --json` | `docs/features/cr099-runner-real-readonly-smoke/TEST-REPORT.md` |
| CR099 collector | `uv run --python 3.11 python scripts/collect_cr099_runner_readonly_smoke.py --env-file <authorized-client-env> --base-url <gateway> ...` | `process/checks/CP7-CR099-RUNTIME-AUTHORIZED-SMOKE-RERUN-PASS-2026-06-19.md` |
| Regression | `uv run --python 3.11 pytest -q tests/test_cr099_runner_real_readonly_smoke_contract.py tests/test_cr098_runner_readonly_integration.py` | `16 passed` |

## 7. 迁移说明

| 是否需要迁移 | 影响对象 | 说明 |
|---|---|---|
| no | 状态 schema / 配置 / 安装路径 / 数据存储 | 本轮新增脚本、测试和过程证据；无自动迁移。 |

## 8. 已知问题与风险

| Risk ID | 严重度 | 状态 | 处理 |
|---|---|---|---|
| R-CR099-CP8-001 | MEDIUM | pending-CP8-acceptance | 当前 evidence 为空持仓路径，不证明非空持仓脱敏路径。 |
| R-CR099-CP8-002 | MEDIUM | pending-CP8-acceptance | 当前 run 不证明交易日路径；如需覆盖需另行授权。 |

## 9. 回滚方式

| 回滚触发 | 回滚入口 | 说明 |
|---|---|---|
| CR099 collector / checker 需要撤回 | `docs/release/ROLLBACK.md` | 文件级回滚 CR099 新增脚本、测试、docs/process evidence；runtime 外部副作用为 0。 |

## 10. 参考链接

| 类型 | 路径 |
|---|---|
| Release Context | `process/release/RELEASE-CONTEXT.yaml` |
| Verification | `docs/features/cr099-runner-real-readonly-smoke/VERIFICATION.md` |
| Test Report | `docs/features/cr099-runner-real-readonly-smoke/TEST-REPORT.md` |
| Review | `docs/features/cr099-runner-real-readonly-smoke/REVIEW.md` |
| CP7 Runtime PASS | `process/checks/CP7-CR099-RUNTIME-AUTHORIZED-SMOKE-RERUN-PASS-2026-06-19.md` |
| Runtime Evidence | `/home/hyde/.quant-lab/evidence/qmt/cr099/redacted/cr099-runner-readonly-smoke-20260619-sim-001/evidence.json` |

## CR100 Addendum - NAS Package Exchange Offline Readiness

| 项目 | 内容 |
|---|---|
| release_decision | READY_WITH_RISK |
| 新增能力 | 本地 fake package exchange root、CR100 manifest/hash/approval/permission 校验、fake publish/fake pull/check CLI、NAS 恢复 runbook |
| 代码入口 | `trading/strategy_runner/package_exchange.py`、`scripts/cr100_package_exchange.py` |
| 验证 | `tests/test_cr100_package_exchange.py`，7 个聚焦用例通过；py_compile 通过 |
| 已知风险 | 真实 NAS mount、权限、路径、publish/pull/copy/check 未验证 |
| 不授权项 | 真实 NAS access/list/read/copy/write/publish/delete、凭据/env/account 读取、QMT/MiniQMT/XtQuant/gateway/runner runtime、交易和 provider/lake/catalog publish |
| 后续 | 真实 NAS 恢复后必须另起独立授权 gate，参考 `docs/qmt/CR100-NAS-PACKAGE-EXCHANGE-RECOVERY-RUNBOOK.md` |

## CR101 Addendum - Cross-Platform Strategy Delivery and Adapter Realignment

| 项目 | 内容 |
|---|---|
| release_decision | READY_WITH_RISK |
| 新增能力 | 策略交付 target taxonomy、QMT direct-run 当前 target、quant-lab runner adapter boundary、MiniQMT gateway 当前 adapter、CR101 manifest/checker/evidence contract |
| 当前架构真相 | 策略在 QMT 可直接运行的 target 是当前唯一支持目标；quant-lab runner 是运行主体；MiniQMT 仅作为 API gateway adapter，不是 runner 宿主 |
| 代码 / 文档入口 | `docs/qmt/CR101-CROSS-PLATFORM-STRATEGY-DELIVERY-ADAPTER-REALIGNMENT-HLD.md`、`docs/qmt/CR101-VALIDATION-AND-FOLLOW-UP-GATES.md`、`trading/strategy_runner/*` |
| 验证 | CR101 S01-S04 CP6 / CP7 均 PASS；`meta-flow workspace check` 显示 process link 健康；CR tracking 需在本轮文档同步后复跑 |
| 已知风险 | 真实 QMT direct-run、MiniQMT gateway、NAS exchange、order-write / simulation / live 均未授权、未执行、未证明 |
| 不授权项 | 真实 NAS access/list/read/copy/write/publish/delete、凭据/env/account 读取、QMT/MiniQMT/XtQuant/gateway runtime、submit/cancel/buy/sell、simulation/live、provider/lake/catalog publish |
| 后续候选 | `RA-CR101-001` QMT direct-run、`RA-CR101-002` MiniQMT gateway adapter、`RA-CR101-003` NAS real exchange、`FU-CR101-001` order-write / simulation / live |
