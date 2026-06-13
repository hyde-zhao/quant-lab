---
status: ready
version: "1.0"
release_artifact_profile: compact
release_decision: READY_WITH_RISK
cr_id: CR-044
---

# CR044 Rollback

## 1. 回滚摘要

| 项目 | 内容 |
|---|---|
| 回滚目标版本 | `cr043-spike-complete` / CR042 broker adapter contract baseline |
| 回滚范围 | CR044 修改的 `engine/broker_adapter.py` 新增块、`tests/test_cr044_goldminer_admission_guard.py`、CR044 process/docs/release/docs/quality 文件、`.gitignore` 反忽略规则 |
| 是否涉及数据恢复 | no |
| 是否存在不可回滚项 | no |
| 决策人 | human / meta-po |

## 2. 回滚触发条件

| Trigger ID | 条件 | 监控 / 证据 | 决策人 |
|---|---|---|---|
| RB-CR044-01 | CR042 broker adapter 回归失败 | `tests/test_cr042_broker_adapter_contract.py` | meta-po / user |
| RB-CR044-02 | CR044 helper 被误读为真实 runtime ready | CP8 review / release review | user |
| RB-CR044-03 | `.gitignore` 反忽略导致非预期质量报告入库 | `git status --short docs/quality` | meta-po / user |

## 3. 回滚步骤

| Step | 操作 | 前置条件 | 验证 | 风险 |
|---|---|---|---|---|
| 1 | 回退 `engine/broker_adapter.py` 中 CR044 新增 helper / Goldminer cancel override | 人工批准回滚 | CR042 pytest PASS | 失去 CR044 offline admission guard |
| 2 | 删除或回退 `tests/test_cr044_goldminer_admission_guard.py` | Step 1 完成 | CR042 pytest PASS | CR044 测试覆盖消失 |
| 3 | 回退 CR044 process/docs/release/docs/quality 产物 | 保留审计备份或 Git 历史 | CR tracking consistency PASS | CR044 审计证据减少 |
| 4 | 如有必要，回退 `.gitignore` 反忽略规则 | 确认不再跟踪 `docs/quality/*.md` | `git check-ignore -v docs/quality/*CR044.md` 恢复命中 | 后续质量报告可能再次被忽略 |

## 4. 回滚验证

| 验证项 | 方法 | 结果 |
|---|---|---|
| CR042 回归 | `uv run --python 3.11 pytest -q tests/test_cr042_broker_adapter_contract.py` | 回滚时执行 |
| CR tracking | `uv run --python 3.11 python scripts/check_cr_tracking_consistency.py --project-root .` | 回滚时执行 |
| 空白检查 | `git diff --check -- <回滚文件>` | 回滚时执行 |

## 5. 不可回滚项

| 对象 | 是否存在 | 原因 | 处理 |
|---|---|---|---|
| 真实 broker 操作 | no | 本轮没有真实运行或外部副作用 | N/A |
| 数据写入 / catalog publish | no | 本轮未写 lake / catalog | N/A |
| 凭据读取 | no | 本轮未读取 `.env` 或凭据 | N/A |
