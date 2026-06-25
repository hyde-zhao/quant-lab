# Research Execution Semantic Alignment

本文件是 research execution semantic alignment 的 canonical reference。旧 `docs/CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md` 已归档到 [../legacy/archive/CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md](../legacy/archive/CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md)；详细历史专题仍保留在 `process/docs/source-archive/docs/CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md`。

本参考只说明 research execution semantic alignment、Backtrader optional / no-copy 边界、`order_intent_draft_v1` 和后续 QMT 路线。它不是运行开关，不授权依赖安装、Backtrader runtime、QMT gateway、simulation、live、provider fetch、lake write、broker lake write 或 publish。

## 用户应如何理解

| 对象 | 可以理解为 | 不能理解为 |
|---|---|---|
| semantic diff | lightweight baseline 与 Backtrader-style reference 的 research comparison。 | production truth 或 QMT admission pass。 |
| `order_intent_draft_v1` | 后续 CR 可审查的 draft。 | 订单、下单指令、撤单指令或 broker write 触发器。 |
| Backtrader module reference | optional reference 和 no-copy 合同。 | 复制源码、运行 Backtrader runtime 或改成主框架。 |

多因子研究主流程见 [../components/MULTIFACTOR-RESEARCH.md](../components/MULTIFACTOR-RESEARCH.md)，端到端场景见 [../scenarios/MULTIFACTOR-RESEARCH-TO-STRATEGY.md](../scenarios/MULTIFACTOR-RESEARCH-TO-STRATEGY.md)。
