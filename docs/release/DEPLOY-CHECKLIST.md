---
status: ready
version: "1.0"
release_artifact_profile: compact
release_decision: READY_WITH_RISK
cr_id: CR-092
---

# CR092 Deploy Checklist

## 1. 发布前输入检查

| 输入 | 状态 | 证据路径 | 说明 |
|---|---|---|---|
| Release Context Capsule | PASS | `process/release/RELEASE-CONTEXT.yaml` | CR092 scope、风险、不授权项和 follow-up 已汇总 |
| TEST-REPORT | PASS | `docs/quality/CR092-REAL-QMT-READONLY-RUNTIME-SMOKE-TEST-REPORT.md` | 定向 pytest / checker / py_compile 通过 |
| REVIEW | PASS_WITH_RISK | `docs/quality/CR092-REAL-QMT-READONLY-RUNTIME-SMOKE-REVIEW.md` | 无阻断 finding；inline fallback 风险待 CP8 接受 |
| BLOCKER findings | 0 | Review | 无 P0 / P1 / P2 finding |
| HIGH findings | 0 accepted risk | `R-CR092-CP7-001` | 高风险是 runtime 未证明，不是实现缺陷 |

## 2. 发布候选快照

| 检查项 | 状态 | 证据 / 摘要 |
|---|---|---|
| 变更范围清楚 | PASS | CR092 guide/template/checker/tests/quality/release/process evidence |
| 未跟踪文件已分类 | PASS | 新增文件均属于 CR092 交付或过程证据 |
| 缓存与临时文件清理 | PASS | 未新增 `.pytest_cache` / `__pycache__` 提交项 |
| 敏感信息检查 | PASS | 未读取或写入 `.env`、凭据、真实账户、NAS 或 runtime logs |

## 3. 安装 / 升级 / 幂等验证矩阵

| 平台 | 组件 | Scope | 场景 | 是否适用 | 验证命令 / 方法 | 结果 | N/A 原因 |
|---|---|---|---|---|---|---|---|
| Local Python 3.11 | static checker | project | checker self-check | yes | `uv run --python 3.11 python scripts/check_cr092_simulated_evidence.py --evidence docs/qmt/CR092-REAL-QMT-READONLY-RUNTIME-SMOKE-EVIDENCE-TEMPLATE.yaml --json` | PASS |  |
| Local Python 3.11 | tests | project | unit test | yes | `uv run --python 3.11 pytest -q tests/test_cr092_simulated_evidence_checker.py` | PASS |  |
| Codex / Claude | agents / skills / install | project / user | install dry-run | no | N/A | N/A | 本轮不交付 Agent / Skill / install script |
| QMT / MiniQMT | runtime | external | startup / connection | no | N/A | N/A | 未授权 |
| NAS | package exchange | external | read / write / publish | no | N/A | N/A | 未授权 |

## 4. 平台和权限边界

| Check ID | 检查项 | 状态 | 证据 / 说明 | 阻断等级 |
|---|---|---|---|---|
| DEP-CR092-001 | 平台路径符合当前 scope | PASS | 只新增项目内 docs / scripts / tests / process evidence | REQUIRED |
| DEP-CR092-002 | 不需要 Claude direct ask tools | N/A | 非 Claude subagent 交付 | N/A |
| DEP-CR092-003 | 不包含 Codex / Claude 平台 schema 变更 | PASS | 无 Agent / Skill manifest 变化 | REQUIRED |
| DEP-CR092-004 | 不覆盖用户本地配置 | PASS | 未修改 `.env`、用户配置、NAS 或 runtime 配置 | BLOCKING |
| DEP-CR092-005 | 回滚方案已确认 | PASS | `docs/release/ROLLBACK.md` | REQUIRED |

## 5. 发布结论

| 项目 | 内容 |
|---|---|
| release_artifact_profile | compact |
| release_decision | READY_WITH_RISK |
| 阻断项 | 0 |
| 风险接受项 | `R-CR092-CP7-001..004` |

## 6. 不授权项

| Item ID | 不授权操作 | 原因 | 需要的独立授权 |
|---|---|---|---|
| NA-CR092-01 | QMT/MiniQMT/XtQuant/gateway/runner startup / connection / install / runtime | 当前只确认 readiness / evidence guardrail | 独立逐 run runtime authorization |
| NA-CR092-02 | NAS access / list / read / copy / pull / write / publish / delete | 用户已确认当前 CR092 不需要 NAS | CR091-FU-02 或独立 NAS gate |
| NA-CR092-03 | `.env` / credentials / real account / real funds / real positions / real orders / real fills / raw logs | CP5 只允许用户提供的模拟账户 evidence | 独立 security / runtime evidence gate |
| NA-CR092-04 | submit/cancel、buy/sell、simulation/live | order-write 不在 CR092 当前范围 | CR091-FU-03 或独立 order-write gate |
| NA-CR092-05 | provider fetch / lake write / catalog publish | 不在 CR092 范围 | 独立 data/publish gate |
