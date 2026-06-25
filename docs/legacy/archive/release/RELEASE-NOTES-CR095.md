---
status: ready-for-review
cr_id: CR-095
---

# CR095 Release Notes

| 字段 | 内容 |
|---|---|
| 版本 | `cr095-checker-output-convergence` |
| 发布范围 | standalone CR tracking checker 输出收敛 |
| 用户可见变化 | `scripts/check_cr_tracking_consistency.py` 现在先输出与 `meta-flow check cr-tracking` 同形态的四类 summary，再输出原 PASS/FAIL 结果 |
| 兼容性 | 命令参数和退出码语义不变 |
| 真实发布 | N/A；本轮只做交付就绪，不执行 publish / release |

## 变更摘要

| ID | 内容 | 影响 |
|---|---|---|
| REL-CR095-01 | standalone checker 新增 `CR tracking summary` 四类输出 | 主 CLI 与 standalone 日常使用口径一致 |
| REL-CR095-02 | 测试新增 CR095 active 和 summary 输出断言 | 防止后续输出形态退化 |
| REL-CR095-03 | CR093-FU-02 转为正式 CR095 active | follow-up 台账与 CR-INDEX / STATE 可追溯 |

## 验证摘要

| 命令 | 结果 |
|---|---|
| `uv run --python 3.11 meta-flow check cr-tracking --project-root . --strict-warnings` | PASS |
| `uv run --python 3.11 python scripts/check_cr_tracking_consistency.py --project-root .` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr093_cr_tracking_consistency.py` | PASS，9 passed |

## 不授权范围

不授权 runtime、NAS、`.env`、凭据、账户、资金、持仓、委托、成交、原始日志、submit / cancel / buy / sell、simulation / live、provider fetch、lake write、catalog publish 或真实 release execution / publish。
