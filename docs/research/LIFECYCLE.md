---
status: "implemented-cp6"
version: "1.0"
change_id: "CR-051"
story_id: "CR051-S01-lifecycle-and-taxonomy-framework"
owner: "host-orchestrator"
implemented_at: "2026-06-14T09:00:24+08:00"
canonical_project_name: "quant-lab"
legacy_project_alias: "local_backtest"
runtime_authorized: false
trading_authorized: false
---

# Strategy Research Lifecycle

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-14 | host-orchestrator | 初版策略研究生命周期合同，冻结 idea、project、protocol、run、validation、admission 和 claim boundary |

## 目标

本文定义 quant-lab 的研究生命周期主状态机。它只描述研究对象如何从信息来源和策略想法进入研究交付候选，不授权任何 provider fetch、lake write、archive migration、QMT / MiniQMT runtime、simulation、live trading 或真实下单。

`delivery_candidate` 是研究交付候选，不是 `runtime_candidate`、simulation-ready、live-ready 或 trade-ready。

## 核心对象

| 对象 | 主键 | 必填摘要 | 说明 |
|---|---|---|---|
| InformationSource | `source_id` | source_type、title、usage_boundary、redaction_status | 信息来源只保存摘要和引用边界，不保存凭据或敏感原文 |
| StrategyIdea | `idea_id` | hypothesis、source_refs、strategy_family、expected_edge、failure_mode | 策略想法，不代表已立项 |
| ResearchProject | `project_id` | objective、success_criteria、scope、owner、revisit_condition | 研究项目，必须有可验证目标 |
| ResearchProtocol | `protocol_id` | universe、data_release_ref、metric_suite、cost_model、risk_assumptions | 研究协议，冻结复验条件 |
| ResearchRun | `run_id` | commit、data_release、config_hash、seed、artifact_refs | 研究运行，必须可追溯 |
| ValidationEvidence | `evidence_id` | run_refs、metric_summary、bias_checks、claim_boundary、blocked_claims | 验证证据，只能声明证据支持的 claim |

## 状态机

| 状态 | 含义 | 进入条件 | 允许的下一状态 |
|---|---|---|---|
| `captured` | 来源或想法已记录 | 至少有 source summary 或 idea draft | `triaged`、`rejected` |
| `triaged` | 已完成初筛 | source_refs、hypothesis、strategy_family 初步齐备 | `chartered`、`research_only`、`rejected` |
| `chartered` | 已立项 | objective、success_criteria、scope、owner 齐备 | `protocol_ready`、`rejected` |
| `protocol_ready` | 研究协议可执行 | universe、data_release_ref、metric_suite、cost_model 冻结 | `research_running`、`rejected` |
| `research_running` | 研究运行中 | run plan 已建立 | `validation_ready`、`research_only`、`rejected` |
| `validation_ready` | 运行结果可验证 | run manifest 和 artifact refs 齐备 | `admission_review`、`research_only` |
| `admission_review` | 准入审查中 | ValidationEvidence 齐备，claim_boundary 明确 | `research_only`、`paper_candidate`、`delivery_candidate`、`rejected`、`retired` |
| `research_only` | 只保留研究价值 | 证据不足以进入交付候选，但可保留报告 | `retired`、`chartered` |
| `paper_candidate` | 可进入本地 paper / package 设计候选 | 研究证据支持 paper 级 claim | `delivery_candidate`、`retired` |
| `delivery_candidate` | 研究交付候选 | evidence、archive pointer、claim boundary 均通过 | `retired` |
| `rejected` | 已拒绝 | 缺少关键证据、风险不可接受或重复 | `retired` |
| `retired` | 已退役 | 用户或 owner 决定关闭 | 终态 |

## 转换规则

| 转换 | 必需证据 | 失败行为 |
|---|---|---|
| `captured -> triaged` | source_refs 或明确的 source_missing reason | `missing_source`，保留 captured 或 rejected |
| `triaged -> chartered` | 可验证 success_criteria、scope、owner | `charter_incomplete` |
| `chartered -> protocol_ready` | data_release_ref、metric_suite、cost_model、risk_assumptions | `protocol_missing_required_field` |
| `protocol_ready -> research_running` | run plan、config_hash 计划、artifact route | `run_plan_blocked` |
| `research_running -> validation_ready` | run_id、commit、data_release、config_hash、seed、artifact_refs | `run_manifest_incomplete` |
| `validation_ready -> admission_review` | ValidationEvidence、bias_checks、claim_boundary | `validation_evidence_missing` |
| `admission_review -> delivery_candidate` | allowed claims、blocked_claims、archive_manifest_ref、owner sign-off | `delivery_claim_blocked` |

## Claim Boundary

| Claim | CR051 允许状态 | 说明 |
|---|---|---|
| research documented | allowed | 研究文档和静态合同可声明 |
| paper_candidate | allowed only with evidence | 需要 run manifest 和 ValidationEvidence |
| delivery_candidate | allowed only after admission_review | 只表示研究交付候选 |
| runtime_candidate | blocked | 必须后续独立 CR 和 runtime authorization |
| simulation-ready | blocked | CR051 不授权 simulation |
| live-ready / trade-ready | blocked | CR051 不授权 live trading |
| QMT / MiniQMT verified | blocked | CR051 不连接、不导入、不运行 |

## 失败路径

| 错误码 | 触发条件 | 处理 |
|---|---|---|
| `missing_source` | idea 缺少来源或 usage boundary | 留在 captured 或 rejected |
| `duplicate_idea` | 与已有 idea 高度重复 | 合并引用或 rejected |
| `protocol_missing_required_field` | protocol 缺 universe / data release / metric suite | 阻断运行 |
| `run_manifest_incomplete` | run 缺 commit / config_hash / artifact refs | 阻断 validation_ready |
| `runtime_claim_not_authorized` | 文档声明 runtime verified / trade-ready | fail closed，必须修正文档 |
| `sensitive_source_blocked` | 来源含凭据、账户、broker facts 原文 | 不入 Git，只保留脱敏指针 |

## 后续 CR 消费

| 后续 CR | 消费方式 |
|---|---|
| CR052 多因子完整证明周期 | 以本状态机证明 idea -> delivery_candidate 的完整链路 |
| CR053 archive migration / inventory | 使用 source / run / artifact 的状态和 pointer 做 inventory |
| CR055 research consumption bridge | 消费 delivery_candidate 和 ValidationEvidence 进入 package contract |
| CR056 feedback loop | 消费 retired / rework / drift / incident 状态扩展 |

## 不授权项

- 不执行 provider fetch、lake write、catalog publish。
- 不执行 NAS scan、mount、copy、delete、migration。
- 不连接、不导入、不运行 QMT / MiniQMT。
- 不读取 `.env`、token、account_id、账号、密码、session、cookie 或 private key。
- 不 submit、cancel、simulation 或 live trading。

