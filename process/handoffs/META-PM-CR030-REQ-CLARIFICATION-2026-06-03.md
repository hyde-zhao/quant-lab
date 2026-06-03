---
handoff_id: "META-PM-CR030-REQ-CLARIFICATION-2026-06-03"
change_id: "CR-030"
from_agent: "meta-po"
to_agent: "meta-pm"
status: "completed"
created_at: "2026-06-03T00:06:23+08:00"
completed_at: "2026-06-03T00:06:23+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e8912-6f55-7e61-9e76-4855d071a53d"
  thread_id: "019e8912-6f55-7e61-9e76-4855d071a53d"
  agent_name: "pm-chen"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "not-recorded-in-parent-summary"
  completed_at: "2026-06-03T00:06:23+08:00"
---

# META-PM CR-030 需求澄清交还摘要

## 交还结论

meta-pm 建议 CR-030 的 CP2 口径收敛为：

- CR-030 是项目自有多因子研究闭环主线，不是 Qlib-first runner 集成。
- 外部项目只进入静态借鉴矩阵和后续 Spike 候选，不作为默认依赖。
- CR-026 保留为 Qlib isolated runner 后续 Spike candidate，等待 factor panel、label window、report catalog 和 runner I/O 合同冻结。
- CP2 不授权实现、依赖变更、外部项目 clone / install / run、provider / lake / publish、QMT / simulation / live 或凭据读取。

## 建议写入 CP2 的 Use Cases

| 建议 UC | 场景名称 |
|---|---|
| UC-20 | 多因子研究闭环主线确认 |
| UC-21 | 外部项目静态借鉴矩阵 |
| UC-22 | 研究对象契约冻结 |
| UC-23 | 单因子评价与报告 |
| UC-24 | 多因子组合构建 |
| UC-25 | 实验追溯与报告目录 |
| UC-26 | 策略准入包与研究到执行交接 |
| UC-27 | CR-026 / Qlib runner 分流 |

## 建议写入 CP2 的 Requirements

| 建议 ID | 摘要 |
|---|---|
| REQ-174 | CR-030 必须以项目自有多因子研究闭环为主线 |
| REQ-175 | CP3 HLD 必须输出外部项目借鉴矩阵 |
| REQ-176 | 必须定义 `FactorSpec` 与 `FactorRunSpec` |
| REQ-177 | 必须定义 `FactorPanelContract` 与 `LabelWindowSpec` |
| REQ-178 | 必须输出单因子评价指标与 blocked claims |
| REQ-179 | 必须设计多因子组合构建流程 |
| REQ-180 | 必须生成 `ExperimentManifest` 和报告目录 |
| REQ-181 | 必须定义 `StrategyAdmissionPackage` 并映射 Stage6 gate |
| REQ-182 | CP2/CP3/CP5 前必须保持安全计数为 0 |
| REQ-183 | CP3/LLD 应复用现有 research dataset 与实验 17-21 能力 |
| REQ-184 | CP2 必须形成 CR-026 分流决策 |
| REQ-185 | 后续文档必须说明多因子闭环、借鉴边界、准入包和不授权项 |

## 需要进入人工决策队列的事项

meta-pm 建议 DQ-CP2-CR030-01 至 DQ-CP2-CR030-09 进入 CP2 Decision Brief。详见 `process/discussions/CP2-CR030-SCENARIO-DISCUSSION-LOG.md`。

## 下游建议

下一步由 meta-po 生成 CP2 正式基线和人工审查稿；若用户 approve，再调度 meta-se 进入 CP3/HLD。当前交还不构成 CP2 approved。
