---
status: "draft-current-index"
version: "1.0"
feature_id: "FEAT-04"
---

# Feature Test Plan: execution-semantics-reference

## 测试矩阵

| 测试域 | 关键场景 | 验证入口 |
|---|---|---|
| optional backend availability | 未安装时结构化 unavailable，lightweight 主路径继续 | `tests/test_cr025_clean_feed_gate.py`、`tests/test_backtrader_optional_backend.py` |
| clean feed gate | PIT、available_at、复权、benchmark、tradability、quality gate | `tests/test_cr025_clean_feed_gate.py` |
| semantic diff | lightweight / optional backend 差异字段完整 | `tests/test_cr025_semantic_diff_contract.py` |
| order intent draft | draft 包含研究口径、raw execution policy 和非授权声明 | `tests/test_cr025_order_intent_draft_contract.py` |
| no-copy guardrail | Backtrader 源码不得复制 / 裁剪 / 改写 | `tests/test_cr025_backtrader_no_copy_guardrail.py`、`tests/test_cr025_forbidden_source_copy.py` |
| no-real-operation | 不触发真实 broker / QMT / provider / lake / publish / credential | `tests/test_cr025_no_real_operation_safety.py` |

## 手工验证

| 场景 | 预期 |
|---|---|
| 外部后端升级为 Spike | 必须新建 CR，明确依赖、license、运行授权和回滚 |
| diff 被用于 QMT 后续路线 | 只能作为审查证据，不提供 simulation/live 授权 |

