---
story_id: "CR053-S04-manifest-transfer-and-backup-plan"
title: "manifest-first transfer 与 backup plan"
story_slug: "manifest-transfer-and-backup-plan"
status: "verified"
priority: "P0"
implementation_allowed: true
implementation_allowed_until: "CP5 approved at 2026-06-14T11:52:15+08:00; static Markdown reports / guardrail evidence only"
wave: "CR053-W2-REFERENCE-BACKUP"
depends_on:
  - "CR053-S01-root-map-and-host-mapping-contract"
dependency_type:
  - "root-map-contract"
cp5_batch: "CR053-MIGRATION-INVENTORY-BATCH-A"
feature_design_refs:
  - "docs/features/quant-lab-migration-dry-run/DESIGN.md"
  - "docs/features/quant-lab-migration-dry-run/TEST-PLAN.md"
lld_policy:
  required_level: "full-lld"
  trigger_reasons: ["manifest-first-transfer", "backup-plan", "restore-rehearsal"]
  rationale: "transfer / backup 设计影响后续 CR058 / CR060 的安全执行前置，必须 full-lld。"
  waiver_reason: ""
  revisit_condition: "真实备份、恢复演练、NAS copy / sync 或数据湖迁移时。"
  evidence_path: "process/stories/CR053-S04-manifest-transfer-and-backup-plan-LLD.md"
file_ownership:
  primary:
    - "docs/release/BACKUP-PLAN-CR053.md"
  shared:
    - "docs/release/NAS-MAPPING-CR053.md"
  forbidden:
    - "real backup execute"
    - "real restore execute"
    - "NAS copy / delete"
lld_gate:
  design_evidence_type: "full-lld"
  design_evidence_path: "process/stories/CR053-S04-manifest-transfer-and-backup-plan-LLD.md"
  status: "confirmed"
  confirmed: true
dev_gate:
  design_evidence_confirmed: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  dependency_note: "依赖 S01 root map 合同；CP5 已全量确认，可进入静态 Markdown 报告 / guardrail evidence 实现。"
  not_authorized:
    - "real backup execute"
    - "real restore execute"
    - "NAS copy / delete"
change_id: "CR-053"
created_at: "2026-06-14T10:59:13+08:00"
updated_at: "2026-06-14T12:19:53+08:00"
implementation_evidence:
  path: "process/stories/CR053-BATCH-A-IMPLEMENTATION.md"
  cp6_check: "process/checks/CP6-CR053-MIGRATION-INVENTORY-BATCH-A-CODING-DONE.md"
  output: "docs/release/BACKUP-PLAN-CR053.md"
  status: "implemented-cp6-static"
cp7_verification_evidence:
  path: "docs/quality/VERIFICATION-REPORT-CR053.md"
  cp7_check: "process/checks/CP7-CR053-MIGRATION-INVENTORY-BATCH-A-VERIFICATION-DONE.md"
  context: "process/context/CP7-CR053-VERIFICATION-CONTEXT.yaml"
  result: "PASS"
  verified_at: "2026-06-14T12:30:26+08:00"
---

# CR053-S04：manifest-first transfer 与 backup plan

## 目标

设计 staging -> checksum -> promote -> record 的传输 manifest，以及 Git bundle、warm archive、cold backup、package exchange manifest 和现有 market data lake backup policy 的关系。

## 技术说明

| 项目 | 内容 |
|---|---|
| 设计证据类型 | full-lld |
| 设计依据 | HLD-CR053 §6 / §7、ADR-CR053-002/003/006 |
| 文件影响 | 未来新增 `docs/release/BACKUP-PLAN-CR053.md` |
| 接口 / 数据 / 权限变化 | 只设计备份和恢复演练合同；不执行真实备份 / restore |
| 测试入口 | TC-CR053-05、TC-CR053-06、SEC-CR053-01 |
| 风险与重访条件 | 14T cold backup 不可用或需要移动真实 lake 时重访 |
