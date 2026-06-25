---
status: ready-for-review
cr_id: CR-095
---

# CR095 Rollback

## 回滚触发条件

| 条件 | 动作 |
|---|---|
| standalone summary 输出被认为不可接受 | 回退 `scripts/check_cr_tracking_consistency.py` 的 summary 输出切片，保留原深度检查 |
| CR095 active 索引需要撤回 | 将 CR095 标记为 blocked / superseded，并把 CR093 follow-up row 回退为 candidate |
| 测试覆盖不符合期望 | 回 CP6/CP7 修订测试 |

## 回滚范围

| 路径 | 回滚说明 |
|---|---|
| `scripts/check_cr_tracking_consistency.py` | 撤回 CR095 summary 输出和 CR095 active 支持 |
| `tests/test_cr093_cr_tracking_consistency.py` | 撤回 CR095 / summary 输出断言 |
| `process/changes/CR-095-*.md` | 标记为 blocked / superseded，不删除 |
| `process/STATE.md` / `process/changes/CR-INDEX.yaml` | 恢复为无 active formal CR 或下一正式 CR |

## 回滚后验证

- `uv run --python 3.11 meta-flow check cr-tracking --project-root . --strict-warnings`
- `uv run --python 3.11 python scripts/check_cr_tracking_consistency.py --project-root .`
- `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr093_cr_tracking_consistency.py`
