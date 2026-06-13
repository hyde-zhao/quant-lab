---
story_id: "CR046-S06-follow-up-strategy-delivery-gate"
title: "后续具体策略交付门禁"
story_slug: "follow-up-strategy-delivery-gate"
status: "ready-for-verification"
priority: "P1"
wave: "CR046-W4-FOLLOW-UP-HANDOFF"
depends_on:
  - "CR046-S05-verification-framework-and-evidence-model"
dependency_type:
  - "contract"
cp5_batch: "CR046-DUAL-TARGET-FRAMEWORK-BATCH-A"
feature_design_refs:
  - "docs/features/qmt-miniqmt-dual-target-framework/TASKS.md"
lld_policy:
  required_level: "technical-note"
  trigger_reasons: ["follow-up-tracking", "low-implementation-risk"]
  rationale: "本 Story 只冻结 CR047 / CR049 后续门禁和台账状态，不新增外部接口或运行能力。"
  waiver_reason: ""
  revisit_condition: "启动 CR047 或 CR049 时。"
  evidence_path: "process/stories/CR046-S06-follow-up-strategy-delivery-gate.md#技术说明"
file_ownership:
  primary:
    - "process/changes/CR-046-FOLLOW-UP-TRACKING-2026-06-13.md"
  shared:
    - "docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md"
  merge_owner: "CR046-S06-follow-up-strategy-delivery-gate"
  forbidden:
    - "concrete strategy delivery"
    - "runtime authorization"
lld_gate:
  required_inputs:
    - "CR046-S05-verification-framework-and-evidence-model"
  design_evidence_type: "technical-note"
  design_evidence_path: "process/stories/CR046-S06-follow-up-strategy-delivery-gate.md#技术说明"
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

# CR046-S06：后续具体策略交付门禁

## 目标

冻结 CR047 首个具体策略交付和 CR049 MiniQMT runner 实机验证的进入条件、消费对象、不授权边界和台账状态。

## 技术说明

| 项目 | 内容 |
|---|---|
| 设计证据类型 | technical-note |
| 设计依据 | ADR-CR046-005、FEAT-09 TASKS、CR046 follow-up tracking、S05 StrategyValidationEvidence |
| 文件影响 | 更新 `process/changes/CR-046-FOLLOW-UP-TRACKING-2026-06-13.md` 和相关文档引用 |
| 接口 / 数据 / 权限变化 | 无新增 runtime 接口；只冻结后续 CR gate 的进入条件、消费对象、输出证据和不授权项 |
| 后续门禁 | CR047 首个具体策略交付、CR048 QMT terminal shadow / 最小 submit-cancel gate、CR049 MiniQMT install / readonly、CR051 研究框架反向完善 |
| 异常、失败与回退 | 若用户要求当前 CR046 交付策略或实机验证，回退 CP2/CP3 修改范围；若后续 CR 缺少策略包或授权，fail closed |
| 测试入口 | CP5 technical-note implementability review、CP8 follow-up tracking review |
| 风险与重访条件 | CR047 / CR048 / CR049 / CR051 启动时重访；任何 runtime authorization 都必须独立决策 |

### 后续 CR 进入条件

| 后续 CR | 进入条件 | 消费对象 | CR046 不授权项 |
|---|---|---|---|
| CR047 首个具体策略交付 | 策略选择、StrategyCoreContract、StrategyPackageContract、验证框架、用户确认策略范围 | `docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md`、`docs/qmt/CR046-VERIFICATION-FRAMEWORK.md` | 不自动生成真实策略包、不传输到交易 PC |
| CR048 QMT terminal shadow / 最小 submit-cancel gate | CR047 策略包、QMT target、独立 runtime_authorization、回滚和操作者确认 | qmt_terminal target、manual_import_steps、shadow_report_schema | 不由 CR046 授权 terminal 导入、shadow、submit/cancel |
| CR049 MiniQMT install / readonly | MiniQMT 权限、Windows runner 机器、install dry-run 授权、只读连接授权、脱敏证据路径 | `docs/qmt/CR046-MINIQMT-RUNNER-INSTALL-DESIGN.md` | 不真实安装、不连接、不查询账户 |
| CR051 研究框架反向完善 | 研究框架需要输出交易交付字段，且 CR046 合同已 CP8 通过 | StrategyCoreContract、EvidenceModel、order intent / risk / cost assumptions | 不在 CR046 修改研究代码 |

### 完成判定

- 技术说明足以让后续 CR 使用 CR046 产物作为输入。
- 后续 CR 的进入条件与不授权项均可追溯。
- 当前 Story 不创建具体策略文件、不提交 CR047/CR049/CR051 实施任务、不触发任何 runtime。

## 量化验收标准（acceptance_criteria）

- [ ] CR047-candidate 至少列出策略选择、策略包合同、验证框架和运行授权 4 个进入条件。
- [ ] CR049-candidate 至少列出 MiniQMT 权限、install dry-run、只读连接授权和脱敏证据 4 个进入条件。
- [ ] 本 Story 不新增具体策略文件或 runtime 命令。

## 阻塞说明

本 Story 不启动 CR047 / CR049；只登记门禁。
