---
handoff_id: "META-PO-CR030-EXTERNAL-REFERENCE-RESEARCH-2026-06-03"
change_id: "CR-030"
status: "completed"
created_at: "2026-06-03T00:06:23+08:00"
owner: "meta-po"
dispatch_evidence:
  - agent_id: "019e890f-d0c5-7181-a436-64c770d6a65f"
    agent_name: "Curie"
    role: "explorer"
    tool_name: "multi_agent_v1.spawn_agent"
    task: "Alphalens / vectorbt / PyBroker / bt public web static research"
    completed_at: "2026-06-03T00:06:23+08:00"
  - agent_id: "019e890f-ea5e-7ea0-bcda-4ee21fc1b2c7"
    agent_name: "Ampere"
    role: "explorer"
    tool_name: "multi_agent_v1.spawn_agent"
    task: "Zipline Reloaded / QuantConnect LEAN / RQAlpha / vn.py public web static research"
    completed_at: "2026-06-03T00:06:23+08:00"
---

# CR-030 外部项目调研交接摘要

## 调研边界

本轮只做公开资料静态调研和本地 Qlib 静态读取，不安装、不运行、不 clone、不复制源码、不修改依赖。

## Explorer 结果摘要

| 项目 | 建议分类 | 关键结论 |
|---|---|---|
| Alphalens | 借鉴 | 借鉴因子评价指标、forward returns、IC / RankIC、分位数组合、turnover 和 tear sheet；不默认依赖 |
| vectorbt | 可选 Spike | 借鉴批量参数实验和向量化 shape；Commons Clause 合规风险，不默认依赖 |
| PyBroker | 可选 Spike | 借鉴 ML walk-forward、bootstrap、ranking / sizing；非商业口径和外部 broker / data 入口需隔离 |
| bt | 借鉴 | 借鉴组合 AlgoStack / rebalance / results；不是因子诊断核心 |
| Zipline Reloaded | 借鉴 | 借鉴 Pipeline Factor / Filter / Classifier、CustomFactor、rank / mask / groupby |
| QuantConnect LEAN | 借鉴 | 借鉴 Universe -> Alpha -> Portfolio -> Risk -> Execution 分层契约 |
| RQAlpha | 可选 Spike | 借鉴 A 股事件驱动、撮合、Mod、订单 API；许可证按限制性 / 需授权处理 |
| vn.py / vnpy.alpha | 可选 Spike | 借鉴 dataset / factor / model / signal / strategy / execution 流程；主框架过重，不默认集成 |

## 已沉淀产物

| 产物 | 路径 |
|---|---|
| 外部项目与 Qlib 适配分析 | `process/research/CR030-MULTIFACTOR-FRAMEWORK-REFERENCE-ANALYSIS-2026-06-03.md` |
| CP2 场景讨论日志 | `process/discussions/CP2-CR030-SCENARIO-DISCUSSION-LOG.md` |
| CP2 discussion checkpoint | `process/checks/CP2-CR030-DISCUSSION-CHECKPOINT.json` |

## 下游消费说明

meta-se 在 CP3/HLD 中应消费本文件和 analysis artifact，输出正式外部项目借鉴矩阵，至少覆盖 license、维护状态、依赖复杂度、数据事实源假设、可借鉴模块、不引入模块、迁移禁止项和后续 Spike 条件。
