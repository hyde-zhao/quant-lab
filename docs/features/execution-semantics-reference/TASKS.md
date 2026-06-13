---
status: "draft-current-index"
version: "1.0"
feature_id: "FEAT-04"
---

# Feature Tasks: execution-semantics-reference

| Task ID | 任务 | 输入 | 输出 | 文件范围 | 验证 |
|---|---|---|---|---|---|
| FEAT-04-T01 | 维护 optional backend availability | backend selector / dependency state | available / unavailable | `engine/backtrader_adapter.py` | optional backend tests |
| FEAT-04-T02 | 维护 clean feed gate | ResearchDataset / quality / policy | clean feed / blocked reason | `engine/backtrader_adapter.py` | clean feed tests |
| FEAT-04-T03 | 维护 semantic diff schema | lightweight + optional run | semantic diff artifact | `engine/semantic_diff.py` | semantic diff tests |
| FEAT-04-T04 | 维护 order intent draft | portfolio / execution policy | draft contract | `engine/order_intent_draft.py` | order intent tests |
| FEAT-04-T05 | 维护 no-copy / source migration guardrail | external reference matrix | forbidden source copy evidence | tests / docs | no-copy tests |

## 后续触发条件

- 新增 optional backend 依赖或运行路径。
- 将 Backtrader / Qlib 从 reference 升级为 isolated runner。
- order intent draft 要进入 CR-021 或后续交易治理流程。

