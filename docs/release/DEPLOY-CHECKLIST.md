---
status: ready
version: "1.0"
release_artifact_profile: compact
release_decision: READY_WITH_RISK
cr_id: CR-044
---

# CR044 Deploy Checklist

## 1. 发布前输入检查

| 输入 | 状态 | 证据路径 | 说明 |
|---|---|---|---|
| Release Context Capsule | PASS | `process/release/RELEASE-CONTEXT.yaml` | CR044 compact capsule 已生成。 |
| TEST-REPORT | PASS_WITH_RISK | `docs/quality/TEST-REPORT-CR044.md` | 13 个目标测试通过，剩余风险为真实运行未授权。 |
| REVIEW | PASS_WITH_RISK | `docs/quality/REVIEW-CR044.md` | findings none-found，风险列明。 |
| BLOCKER findings | 0 | `docs/quality/REVIEW-CR044.md` | 无需回修。 |
| HIGH findings | 0 / accepted risk | `process/checks/CP7-CR044-FIXTURE-STATIC-VERIFICATION-DONE.md` | 高风险来自不授权边界，进入 CP8 风险接受。 |

## 2. 发布候选快照

| 检查项 | 状态 | 证据 / 摘要 |
|---|---|---|
| 变更范围清楚 | PASS | `engine/broker_adapter.py`、`tests/test_cr044_goldminer_admission_guard.py`、CR044 process/docs/release/quality 文件、`.gitignore` 反忽略规则 |
| 未跟踪文件已分类 | PASS_WITH_RISK | 当前工作区存在大量历史未跟踪文件；CR044 目标文件已明确列入 release scope |
| 缓存与临时文件清理 | PASS | 本轮未生成 `__pycache__` / `.pytest_cache` 交付物；pytest 使用 `PYTHONDONTWRITEBYTECODE=1` |
| 敏感信息检查 | PASS | CR044 测试覆盖敏感值 redaction；本轮未读取 `.env` 或凭据 |
| 质量报告跟踪 | PASS | `.gitignore` 已添加 `!docs/quality/` 与 `!docs/quality/*.md`，不再误忽略 CR044 质量报告 |

## 3. 安装 / 升级 / 幂等验证矩阵

| 平台 | 组件 | Scope | 场景 | 是否适用 | 验证命令 / 方法 | 结果 | N/A 原因 |
|---|---|---|---|---|---|---|---|
| Local Python | `engine/broker_adapter.py` / tests | project | pytest regression | yes | `uv run --python 3.11 pytest -q tests/test_cr042_broker_adapter_contract.py tests/test_cr044_goldminer_admission_guard.py` | PASS | N/A |
| Codex / Claude | agents / skills / rules | project / user | install dry-run | no | N/A | N/A | CR044 未修改交付安装器、Agent 或 Skill。 |
| All | install / uninstall | project / user | rollback / uninstall | no | N/A | N/A | 无安装产物或服务进程。 |

## 4. 平台和权限边界

| Check ID | 检查项 | 状态 | 证据 / 说明 | 阻断等级 |
|---|---|---|---|---|
| DEP-CR044-01 | 平台路径符合 contract | PASS | CR044 仅修改仓库内 engine/tests/docs/process；无平台安装路径变更 | REQUIRED |
| DEP-CR044-02 | Claude direct ask tools 权限正确 | N/A | 未修改 Claude agent | REQUIRED |
| DEP-CR044-03 | Codex 不包含 Claude-only schema | PASS | 未新增 Agent/Skill schema；测试与 process 文档为普通 Markdown/YAML | REQUIRED |
| DEP-CR044-04 | 不覆盖用户本地配置 | PASS | 未修改 `.env` 或本地配置；`.gitignore` 仅反忽略 `docs/quality/*.md` | BLOCKING |
| DEP-CR044-05 | 回滚方案已确认 | PASS | `docs/release/ROLLBACK.md` | REQUIRED |

## 5. 发布结论

| 项目 | 内容 |
|---|---|
| release_artifact_profile | compact |
| release_decision | READY_WITH_RISK |
| 阻断项 | 0 |
| 风险接受项 | DQ-CP8-CR044-01..05 |

## 6. 不授权项

| Item ID | 不授权操作 | 原因 | 需要的独立授权 |
|---|---|---|---|
| NA-CR044-01 | 读取凭据、登录、连接 | 当前只交付 L2 离线准入资产 | L3+ 逐 run 授权 |
| NA-CR044-02 | 账户 / 资金 / 持仓 / 委托 / 成交真实查询 | readonly mapping 未 real verified | L4 readonly probe 授权 |
| NA-CR044-03 | 下单、撤单、simulation/live | kill switch 继续 blocked，ready flags false | L5 runtime 授权 |
| NA-CR044-04 | provider fetch / lake write / catalog publish | 不属于 CR044 | 独立数据 / publish 授权 |
