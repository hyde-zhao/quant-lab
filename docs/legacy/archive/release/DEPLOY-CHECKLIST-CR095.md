---
status: ready-for-review
cr_id: CR-095
---

# CR095 Deploy Checklist

| 检查项 | 状态 | 命令 / 证据 | 说明 |
|---|---|---|---|
| 依赖同步 | N/A | `pyproject.toml` 未变更 | 不需要 `uv sync` |
| 安装脚本 | N/A | 无安装产物 | 不涉及部署 |
| standalone checker | PASS | `uv run --python 3.11 python scripts/check_cr_tracking_consistency.py --project-root .` | summary + PASS |
| 主 CLI checker | PASS | `uv run --python 3.11 meta-flow check cr-tracking --project-root . --strict-warnings` | summary + OK |
| 单元测试 | PASS | `pytest tests/test_cr093_cr_tracking_consistency.py` | 9 passed |
| 外部动作 | N/A | 不授权 | 不执行 runtime / NAS / publish |

## 部署结论

- release_decision：`READY`
- 真实发布执行：未授权，未执行
