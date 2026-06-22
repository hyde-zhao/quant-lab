---
status: ready
version: "1.0"
release_artifact_profile: compact
release_decision: READY_WITH_RISK
cr_id: CR-101
---

# CR099 Deploy Checklist

## 1. 发布前输入检查

| 输入 | 状态 | 证据路径 | 说明 |
|---|---|---|---|
| Release Context Capsule | PASS | `process/release/RELEASE-CONTEXT.yaml` | CR099 scope、风险、不授权项和 follow-up 已汇总 |
| TEST-REPORT | PASS | `docs/features/cr099-runner-real-readonly-smoke/TEST-REPORT.md` | 定向 pytest / checker / collector / runtime evidence 通过 |
| REVIEW | PASS | `docs/features/cr099-runner-real-readonly-smoke/REVIEW.md` | 无阻断 finding |
| Runtime evidence | PASS | `/home/hyde/.quant-lab/evidence/qmt/cr099/redacted/cr099-runner-readonly-smoke-20260619-sim-001/evidence.json` | `overall_status=pass` |
| BLOCKER findings | 0 | Review | 无 P0 / P1 finding |
| HIGH findings | 0 | Review | 无高危实现缺陷 |

## 2. 发布候选快照

| 检查项 | 状态 | 证据 / 摘要 |
|---|---|---|
| 变更范围清楚 | PASS | CR099 HLD、checker、collector、tests、feature docs、runtime evidence、release/process evidence |
| 未跟踪文件已分类 | PASS | 新增文件均属于 CR099 交付或过程证据 |
| 缓存与临时文件清理 | PASS | 未新增 `.pytest_cache` / `__pycache__` 提交项 |
| 敏感信息检查 | PASS | 未输出 Windows `.env`、HMAC secret、账户原文、raw positions 或 raw logs |

## 3. 安装 / 升级 / 幂等验证矩阵

| 平台 | 组件 | Scope | 场景 | 是否适用 | 验证命令 / 方法 | 结果 | N/A 原因 |
|---|---|---|---|---|---|---|---|
| Local Python 3.11 | CR099 checker | project | evidence schema self-check | yes | `uv run --python 3.11 python scripts/check_cr099_redacted_evidence.py --evidence <file> --json` | PASS |  |
| Local Python 3.11 | CR099 tests | project | unit + regression | yes | `uv run --python 3.11 pytest -q tests/test_cr099_runner_real_readonly_smoke_contract.py tests/test_cr098_runner_readonly_integration.py` | PASS |  |
| WSL -> Windows gateway | CR099 collector | per-run authorized runtime | readonly smoke | yes | `scripts/collect_cr099_runner_readonly_smoke.py ...` | PASS |  |
| Codex / Claude | agents / skills / install | project / user | install dry-run | no | N/A | N/A | 本轮不交付 Agent / Skill / install script |
| Windows service install | gateway service | external | install / upgrade | no | N/A | N/A | gateway 由用户手动启动；CR099 不安装或修改服务 |
| NAS | package exchange | external | read / write / publish | no | N/A | N/A | 未授权 |

## 4. 平台和权限边界

| Check ID | 检查项 | 状态 | 证据 / 说明 | 阻断等级 |
|---|---|---|---|---|
| DEP-CR099-001 | 平台路径符合当前 scope | PASS | 只新增项目内 docs / scripts / tests / process evidence | REQUIRED |
| DEP-CR099-002 | 不需要 Claude direct ask tools | N/A | 非 Claude subagent 交付 | N/A |
| DEP-CR099-003 | 不包含 Codex / Claude 平台 schema 变更 | PASS | 无 Agent / Skill manifest 变化 | REQUIRED |
| DEP-CR099-004 | 不覆盖用户本地配置 | PASS | 未修改 Windows `.env`、用户配置、NAS 或 runtime 配置 | BLOCKING |
| DEP-CR099-005 | 回滚方案已确认 | PASS | `docs/release/ROLLBACK.md` | REQUIRED |

## 5. 发布结论

| 项目 | 内容 |
|---|---|
| release_artifact_profile | compact |
| release_decision | READY_WITH_RISK |
| 阻断项 | 0 |
| 风险接受项 | `R-CR099-CP8-001..002` |

## 6. 不授权项

| Item ID | 不授权操作 | 原因 | 需要的独立授权 |
|---|---|---|---|
| NA-CR099-01 | 额外 runtime run / gateway 操作 | 本轮只消费一次 CR099 授权 run | 独立逐 run runtime authorization |
| NA-CR099-02 | Windows `.env` / credentials / account originals / raw logs | CP8 只接受脱敏证据 | 独立 security / runtime evidence gate |
| NA-CR099-03 | NAS access / package exchange | 不在 CR099 范围 | 独立 NAS gate |
| NA-CR099-04 | submit/cancel、buy/sell、simulation/live | order-write 不在 CR099 范围 | 独立 order-write gate |
| NA-CR099-05 | provider fetch / lake write / catalog publish | 不在 CR099 范围 | 独立 data/publish gate |

## CR100 Addendum - Offline Readiness Deploy Checklist

| Check ID | 检查项 | 状态 | 证据 / 说明 | 阻断等级 |
|---|---|---|---|---|
| DEP-CR100-001 | 本地 fake exchange CLI 可运行 | PASS | `scripts/cr100_package_exchange.py` | REQUIRED |
| DEP-CR100-002 | 聚焦测试通过 | PASS | `tests/test_cr100_package_exchange.py`，7 passed | REQUIRED |
| DEP-CR100-003 | 真实 NAS 未访问 | PASS | 仅使用 `tmp_path` fixture；真实 NAS 不授权 | BLOCKING |
| DEP-CR100-004 | 凭据 / runtime / 交易未触碰 | PASS | AST 测试不导入 runtime/network/env 模块 | BLOCKING |
| DEP-CR100-005 | NAS 恢复 runbook 已生成 | PASS | `docs/qmt/CR100-NAS-PACKAGE-EXCHANGE-RECOVERY-RUNBOOK.md` | REQUIRED |

CR100 的 deploy 结论是 `READY_WITH_RISK`，不是 `RELEASED`；真实 NAS 验证需要独立授权。

## CR101 Addendum - Offline Delivery Deploy Checklist

| Check ID | 检查项 | 状态 | 证据 / 说明 | 阻断等级 |
|---|---|---|---|---|
| DEP-CR101-001 | 当前 release context 指向 CR101 | PASS | `process/release/RELEASE-CONTEXT-CR101.yaml` 与 `process/release/RELEASE-CONTEXT.yaml` | REQUIRED |
| DEP-CR101-002 | 当前需求基线包含 CR101 | PASS | `process/baseline/CURRENT-REQUIREMENT-BASELINE.yaml` | REQUIRED |
| DEP-CR101-003 | 后续 gate ID 使用 schema v2 | PASS | `RA-CR101-001..003` / `FU-CR101-001`，旧 ID 只保留为 legacy | REQUIRED |
| DEP-CR101-004 | 真实 runtime 未授权 | PASS | 当前只允许离线文档、fixture、checker 和本地测试证据 | BLOCKING |
| DEP-CR101-005 | 真实 NAS 未授权 | PASS | NAS 真实验证已拆为 `RA-CR101-003`，未启动 | BLOCKING |
| DEP-CR101-006 | 交易写未授权 | PASS | order-write / simulation / live 已拆为 `FU-CR101-001`，未启动 | BLOCKING |

CR101 的 deploy 结论是 `READY_WITH_RISK`，不是 `RELEASED` 或真实运行 ready；真实验证必须通过独立 gate。
