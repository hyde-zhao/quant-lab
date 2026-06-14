---
story_id: "CR053-S02-repo-inventory-and-path-classification"
title: "Git 内 inventory 与路径分类器"
story_slug: "repo-inventory-and-path-classification"
status: "lld-ready-for-review"
priority: "P0"
wave: "CR053-W1-MAPPING-INVENTORY"
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
  trigger_reasons: ["repo-inventory", "path-classification", "forbidden-content-boundary"]
  rationale: "inventory classifier 是 CR053 dry-run 的核心对象，必须 full-lld 冻结字段、分类、失败模型和安全边界。"
  waiver_reason: ""
  revisit_condition: "inventory surface 扩展到 NAS / untracked data / external archive 时。"
  evidence_path: "process/stories/CR053-S02-repo-inventory-and-path-classification-LLD.md"
file_ownership:
  primary:
    - "docs/release/MIGRATION-INVENTORY-CR053.md"
  shared:
    - "docs/features/quant-lab-migration-dry-run/DESIGN.md"
  forbidden:
    - "NAS scan"
    - "untracked data bulk scan"
    - "credential read"
lld_gate:
  design_evidence_type: "full-lld"
  design_evidence_path: "process/stories/CR053-S02-repo-inventory-and-path-classification-LLD.md"
  status: "ready-for-review"
  confirmed: false
dev_gate:
  design_evidence_confirmed: false
  lld_confirmed: false
  dependencies_satisfied: false
  file_conflict_free: true
  implementation_allowed: false
  dependency_note: "依赖 S01 root map 合同；CP5 全量确认前不得实现。"
  not_authorized:
    - "NAS scan"
    - "untracked data bulk scan"
    - "credential read"
change_id: "CR-053"
created_at: "2026-06-14T10:59:13+08:00"
updated_at: "2026-06-14T11:16:58+08:00"
---

# CR053-S02：Git 内 inventory 与路径分类器

## 目标

设计 repo-local inventory 报告合同，分类 Git 内路径、owner、artifact class、move_action、risk、verification_rule 和 forbidden content policy。

## 技术说明

| 项目 | 内容 |
|---|---|
| 设计证据类型 | full-lld |
| 设计依据 | HLD-CR053 §8、Feature DESIGN IF-CR053-01 |
| 文件影响 | 未来新增 `docs/release/MIGRATION-INVENTORY-CR053.md` |
| 接口 / 数据 / 权限变化 | 只处理 Git 内静态对象；不扫 NAS、不读取 `.env` |
| 测试入口 | TC-CR053-03、SEC-CR053-01 |
| 风险与重访条件 | 用户授权 NAS read-only inventory 或要求扫描 untracked data 时重访 |
