# CR025 Research Execution Semantic Alignment

本文件是 CR-025 的历史归档摘要。新用户优先阅读 [../reference/RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md](../reference/RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md)。详细历史专题已归档到 `process/docs/source-archive/docs/CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md`。

CR-025 只说明 research execution semantic alignment、Backtrader optional / no-copy 边界、`order_intent_draft_v1` 和后续 QMT 路线。它不是运行开关，不授权依赖安装、Backtrader runtime、QMT gateway、simulation、live、provider fetch、lake write、broker lake write 或 publish。

## 用户应如何理解

| 对象 | 可以理解为 | 不能理解为 |
|---|---|---|
| semantic diff | lightweight baseline 与 Backtrader-style reference 的 research comparison。 | production truth 或 QMT admission pass。 |
| `order_intent_draft_v1` | 后续 CR 可审查的 draft。 | 订单、下单指令、撤单指令或 broker write 触发器。 |
| Backtrader module reference | optional reference 和 no-copy 合同。 | 复制源码、运行 Backtrader runtime 或改成主框架。 |

当前多因子模拟盘操作入口见 [../USER-MANUAL.md](../USER-MANUAL.md)。
