---
status: ready
cr_id: CR-093
---

# CR093 Rollback

## 回滚触发

| 触发条件 | 处理 |
|---|---|
| `meta-flow check cr-tracking` 对真实 current conflict 误放行 | 回滚 checker 语义补丁并恢复 CP6/CP7 为 NEEDS_REWORK |
| 状态归一导致 active / closed 判断误判 | 回滚 `normalize_status()` 相关改动并重新设计状态等价表 |
| warning-only 策略被认为不可接受 | 不回滚实现；启动后续 warning cleanup / strict-warnings 设计 CR |

## 回滚范围

| 路径 | 回滚方式 |
|---|---|
| `scripts/check_cr_tracking_consistency.py` | 撤回 CR093 checker 语义改动 |
| `tests/test_cr093_cr_tracking_consistency.py` | 删除或回滚 CR093 单测 |
| `/home/hyde/workspace/meta-flow/meta_flow/checks/cr_tracking.py` | 撤回状态归一和 nested active_change audit warning-only 改动 |
| `process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md` | 撤回 CR093 状态规范化说明 |

## 回滚验证

回滚后必须重新运行：

- `uv run --python 3.11 meta-flow check cr-tracking --project-root .`
- `uv run --python 3.11 pytest -q tests/test_cr093_cr_tracking_consistency.py`
- py_compile 和 scoped `git diff --check`

## 不可回滚项

无数据迁移、无外部状态、无 runtime 连接；不存在外部系统回滚。
