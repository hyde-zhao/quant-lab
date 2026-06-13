---
story_id: "CR046-S07-research-framework-follow-up-contract"
title: "研究框架反向完善合同"
story_slug: "research-framework-follow-up-contract"
status: "ready-for-verification"
priority: "P1"
wave: "CR046-W4-FOLLOW-UP-HANDOFF"
depends_on:
  - "CR046-S01-dual-target-strategy-architecture"
  - "CR046-S05-verification-framework-and-evidence-model"
dependency_type:
  - "contract"
  - "contract"
cp5_batch: "CR046-DUAL-TARGET-FRAMEWORK-BATCH-A"
feature_design_refs:
  - "docs/features/qmt-miniqmt-dual-target-framework/DESIGN.md"
lld_policy:
  required_level: "technical-note"
  trigger_reasons: ["research-handoff", "follow-up-contract"]
  rationale: "本 Story 只定义 CR051 研究框架需消费的交易交付合同字段，低风险但需 CP5 审查。"
  waiver_reason: ""
  revisit_condition: "启动 CR051 或修改研究输出合同时。"
  evidence_path: "process/stories/CR046-S07-research-framework-follow-up-contract.md#技术说明"
file_ownership:
  primary:
    - "docs/research/CR046-RESEARCH-FRAMEWORK-FOLLOWUP.md"
  shared:
    - "docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md"
  merge_owner: "CR046-S07-research-framework-follow-up-contract"
  forbidden:
    - "research framework implementation"
    - "factor engine code change"
    - "strategy delivery"
lld_gate:
  required_inputs:
    - "CR046-S01-dual-target-strategy-architecture"
    - "CR046-S05-verification-framework-and-evidence-model"
  design_evidence_type: "technical-note"
  design_evidence_path: "process/stories/CR046-S07-research-framework-follow-up-contract.md#技术说明"
  status: "confirmed"
dev_gate:
  design_evidence_confirmed: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
task_count: 2
created_at: "2026-06-13T22:57:34+08:00"
updated_at: "2026-06-14T00:16:26+08:00"
change_id: "CR-046"
---

# CR046-S07：研究框架反向完善合同

## 目标

定义 CR051 研究框架完善需要消费的 StrategyCoreContract、StrategyValidationEvidence、风险假设、成本假设、order intents 和准入证据字段。

## 技术说明

| 项目 | 内容 |
|---|---|
| 设计证据类型 | technical-note |
| 设计依据 | ADR-CR046-006、FEAT-09 DESIGN、S01 StrategyCoreContract、S05 StrategyValidationEvidence |
| 文件影响 | 新增 `docs/research/CR046-RESEARCH-FRAMEWORK-FOLLOWUP.md` |
| 接口 / 数据 / 权限变化 | 只定义研究输出合同缺口，不改研究代码、不改因子引擎、不生成策略包 |
| CR051 最小字段 | strategy metadata、target portfolio、order intents、risk assumptions、cost assumptions、validation evidence、authorization boundary |
| 异常、失败与回退 | 若研究框架必须立即实现，另起 CR051；若 StrategyAdmissionPackage 被误读为 QMT-ready / trade-ready，回退修正文档 |
| 测试入口 | CP5 technical-note implementability review、follow-up contract review |
| 风险与重访条件 | CR051 启动或研究输出合同变更时重访 |

### CR051 合同字段草案

| 字段组 | 必填内容 | 说明 |
|---|---|---|
| Strategy Metadata | `strategy_id`、`strategy_version`、research source、run_id | 只读引用研究证据 |
| Target Portfolio | target weights / holdings schema、rebalance date、universe scope | 不代表订单 |
| Order Intents | side、symbol、target_delta、constraint refs | order intent draft，不可 submit |
| Risk Assumptions | capacity、turnover、drawdown、exposure、liquidity assumptions | 后续策略准入使用 |
| Cost Assumptions | commission、slippage、tax、impact assumptions | 必须注明来源和日期 |
| Validation Evidence | schema/static/fixture/manual plan refs、runtime_verified=false | 消费 S05 证据分级 |
| Authorization Boundary | forbidden actions、required future gates | 明确不等于 QMT-ready / trade-ready |

### 完成判定

- 技术说明明确 CR051 需要补哪些研究输出字段。
- StrategyAdmissionPackage 与 StrategyPackageContract 的边界清晰：前者是研究准入证据，后者是后续交易交付包合同。
- 当前 Story 不修改研究框架代码、不运行研究任务、不交付具体策略。

## 量化验收标准（acceptance_criteria）

- [ ] CR051 follow-up 合同至少列出策略元数据、target portfolio、order intents、风险假设、成本假设、验证证据 6 类字段。
- [ ] 明确 CR046 不修改研究框架代码。
- [ ] 明确 StrategyAdmissionPackage 不等于 QMT-ready / trade-ready。

## 阻塞说明

本 Story 不实施研究框架完善，只为 CR051 留出可追溯合同。
