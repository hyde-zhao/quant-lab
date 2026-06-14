---
story_id: "CR053-S01-root-map-and-host-mapping-contract"
title: "迁移 root map 与主机映射合同"
story_slug: "root-map-and-host-mapping-contract"
status: "verified"
priority: "P0"
implementation_allowed: true
implementation_allowed_until: "CP5 approved at 2026-06-14T11:52:15+08:00; static Markdown reports / guardrail evidence only"
wave: "CR053-W1-MAPPING-INVENTORY"
depends_on: []
dependency_type: []
cp5_batch: "CR053-MIGRATION-INVENTORY-BATCH-A"
feature_design_refs:
  - "docs/features/quant-lab-migration-dry-run/DESIGN.md"
  - "docs/features/quant-lab-migration-dry-run/TEST-PLAN.md"
lld_policy:
  required_level: "full-lld"
  trigger_reasons: ["nas-root-map", "linux-host-mapping", "windows-package-exchange", "lake-alias-boundary"]
  rationale: "root map 会影响后续 inventory、backup plan 和 CR058 输入，必须 full-lld 冻结字段、host role 和不授权边界。"
  waiver_reason: ""
  revisit_condition: "真实 NAS path binding、数据湖迁移或 Windows 交易机 package import 变更时。"
  evidence_path: "process/stories/CR053-S01-root-map-and-host-mapping-contract-LLD.md"
file_ownership:
  primary:
    - "docs/release/NAS-MAPPING-CR053.md"
  shared:
    - "docs/features/quant-lab-migration-dry-run/DESIGN.md"
  forbidden:
    - "NAS mount / scan / mkdir / copy / delete"
    - "MARKET_DATA_LAKE_ROOT replacement"
    - "Windows trading PC full archive mount"
lld_gate:
  design_evidence_type: "full-lld"
  design_evidence_path: "process/stories/CR053-S01-root-map-and-host-mapping-contract-LLD.md"
  status: "confirmed"
  confirmed: true
dev_gate:
  design_evidence_confirmed: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  not_authorized:
    - "NAS mount / scan / mkdir / copy / delete"
    - "MARKET_DATA_LAKE_ROOT replacement"
    - "Windows trading PC full archive mount"
change_id: "CR-053"
created_at: "2026-06-14T10:59:13+08:00"
updated_at: "2026-06-14T12:19:53+08:00"
implementation_evidence:
  path: "process/stories/CR053-BATCH-A-IMPLEMENTATION.md"
  cp6_check: "process/checks/CP6-CR053-MIGRATION-INVENTORY-BATCH-A-CODING-DONE.md"
  output: "docs/release/NAS-MAPPING-CR053.md"
  status: "implemented-cp6-static"
cp7_verification_evidence:
  path: "docs/quality/VERIFICATION-REPORT-CR053.md"
  cp7_check: "process/checks/CP7-CR053-MIGRATION-INVENTORY-BATCH-A-VERIFICATION-DONE.md"
  context: "process/context/CP7-CR053-VERIFICATION-CONTEXT.yaml"
  result: "PASS"
  verified_at: "2026-06-14T12:30:26+08:00"
---

# CR053-S01：迁移 root map 与主机映射合同

## 目标

定义 quant-lab migration dry-run 的 root map、Linux 研究机三分区统一视图、Windows 交易机 package exchange 窄映射，以及现有 market data lake 变量不调整的兼容策略。

## 技术说明

| 项目 | 内容 |
|---|---|
| 设计证据类型 | full-lld |
| 设计依据 | HLD-CR053 §5、ADR-CR053-001/006/007 |
| 文件影响 | 未来新增 `docs/release/NAS-MAPPING-CR053.md` 静态报告 |
| 接口 / 数据 / 权限变化 | 只定义逻辑映射；不执行挂载、扫描、创建目录或替换 `.env` |
| 测试入口 | TC-CR053-01、TC-CR053-02、SEC-CR053-01 |
| 风险与重访条件 | 真实路径绑定、数据湖迁移、Windows package import 方式变化时重访 |
