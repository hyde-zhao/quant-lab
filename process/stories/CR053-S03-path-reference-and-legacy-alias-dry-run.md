---
story_id: "CR053-S03-path-reference-and-legacy-alias-dry-run"
title: "路径引用与 legacy alias dry-run"
story_slug: "path-reference-and-legacy-alias-dry-run"
status: "lld-ready"
priority: "P0"
wave: "CR053-W2-REFERENCE-BACKUP"
depends_on:
  - "CR053-S02-repo-inventory-and-path-classification"
dependency_type:
  - "inventory-contract"
cp5_batch: "CR053-MIGRATION-INVENTORY-BATCH-A"
feature_design_refs:
  - "docs/features/quant-lab-migration-dry-run/DESIGN.md"
  - "docs/features/quant-lab-migration-dry-run/TEST-PLAN.md"
lld_policy:
  required_level: "full-lld"
  trigger_reasons: ["path-reference", "legacy-alias", "manual-review"]
  rationale: "路径引用 dry-run 会影响 CR058 mechanical move 和历史审计保留策略，必须 full-lld。"
  waiver_reason: ""
  revisit_condition: "执行真实 rename / path rewrite / package rename 时。"
  evidence_path: "process/stories/CR053-S03-path-reference-and-legacy-alias-dry-run-LLD.md"
file_ownership:
  primary:
    - "docs/release/PATH-REFERENCES-CR053.md"
  shared:
    - "docs/research/PROJECT-IDENTITY-MIGRATION.md"
  forbidden:
    - "bulk rewrite of historical process / CR / handoff evidence"
    - "git history rewrite"
change_id: "CR-053"
created_at: "2026-06-14T10:59:13+08:00"
updated_at: "2026-06-14T10:59:13+08:00"
---

# CR053-S03：路径引用与 legacy alias dry-run

## 目标

设计 `local_backtest`、legacy env、文档链接和路径引用的 dry-run 报告，区分可机械替换、需人工审查和必须保留的历史审计引用。

## 技术说明

| 项目 | 内容 |
|---|---|
| 设计证据类型 | full-lld |
| 设计依据 | HLD-CR053 §8、PROJECT-IDENTITY-MIGRATION |
| 文件影响 | 未来新增 `docs/release/PATH-REFERENCES-CR053.md` |
| 接口 / 数据 / 权限变化 | 只生成 dry-run 报告；不批量修改历史文件 |
| 测试入口 | TC-CR053-04、SEC-CR053-01 |
| 风险与重访条件 | 真实 repo relayout 或远端仓库改名时重访 |
