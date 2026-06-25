---
status: ready
cr_id: CR-093
release_decision: READY_WITH_RISK
---

# CR093 Deploy Checklist

## 部署范围

本轮无真实部署、安装、publish、runtime 或交易动作。CP8 approve 只确认交付就绪，不执行发布。

## 检查清单

| 检查项 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 目标 CLI | PASS | `uv run --python 3.11 meta-flow check cr-tracking --project-root .` | exit 0，保留 warning-only |
| 单元测试 | PASS | `tests/test_cr093_cr_tracking_consistency.py` | 4 passed |
| 语法检查 | PASS | py_compile 两组目标 | 本仓库 checker / tests 和外部 checker 均通过 |
| process 路由 | PASS | `meta-flow workspace check` | `process_link_health: ok` |
| 空白检查 | PASS | scoped `git diff --check` | 本仓库与外部 checker 均无 whitespace error |
| 安装步骤 | N/A | 无安装变更 | 不需要安装 / 迁移 |
| runtime 验证 | N/A | 不授权 | 不启动 QMT / MiniQMT / XtQuant / gateway / runner |

## 不授权项

- 不授权 NAS、凭据、账户、交易、simulation/live。
- 不授权 provider fetch、lake write、catalog publish。
- 不授权真实 release execution 或 publish。
