---
story_id: "CR051-S06-project-identity-rename-and-legacy-alias"
title: "项目身份改名与 legacy alias 兼容"
story_slug: "project-identity-rename-and-legacy-alias"
status: "lld-ready"
priority: "P0"
wave: "CR051-W1-LIFECYCLE-ARCHIVE-IDENTITY"
depends_on: []
dependency_type: []
cp5_batch: "CR051-STRATEGY-RESEARCH-LIFECYCLE-BATCH-A"
feature_design_refs:
  - "docs/features/strategy-research-lifecycle/DESIGN.md"
  - "docs/features/strategy-research-lifecycle/TASKS.md"
lld_policy:
  required_level: "technical-note"
  trigger_reasons: ["project-identity", "alias-compatibility", "migration-safety"]
  rationale: "用户已确认 canonical name 为 `quant-lab`；本 Story 冻结命名迁移顺序和 legacy alias 策略，但不执行真实重命名。"
  waiver_reason: ""
  revisit_condition: "开始 README / pyproject / package / repository 真实改名时。"
  evidence_path: "process/stories/CR051-S06-project-identity-rename-and-legacy-alias.md#技术说明"
file_ownership:
  primary:
    - "docs/research/PROJECT-IDENTITY-MIGRATION.md"
  shared:
    - "README.md"
    - "docs/USER-MANUAL.md"
    - "pyproject.toml"
    - "process/STATE.md"
  merge_owner: "CR051-S06-project-identity-rename-and-legacy-alias"
  forbidden:
    - "directory rename before migration authorization"
    - "remote repository rename"
    - "bulk rewrite historical process / CR / handoff evidence"
    - "git push"
lld_gate:
  required_inputs:
    - "docs/design/HLD-CR051-STRATEGY-RESEARCH-LIFECYCLE-FRAMEWORK.md"
    - "DQ-CP3-CR051-06"
  design_evidence_type: "technical-note"
  design_evidence_path: "process/stories/CR051-S06-project-identity-rename-and-legacy-alias.md#技术说明"
  status: "not-started"
implementation_gate:
  evidence_required: false
  evidence_path: ""
  evidence_type: "story-summary"
  implementation_objects: ["docs-handoff", "migration-plan"]
  test_plan_refs:
    - "docs/features/strategy-research-lifecycle/TEST-PLAN.md"
  local_validation_results: []
  status: "not-started"
dev_gate:
  design_evidence_confirmed: false
  lld_confirmed: false
  dependencies_satisfied: true
  file_conflict_free: true
task_count: 2
created_at: "2026-06-14T08:19:09+08:00"
updated_at: "2026-06-14T08:19:09+08:00"
change_id: "CR-051"
---

# CR051-S06：项目身份改名与 legacy alias 兼容

## 目标

冻结 `quant-lab` canonical project name、`local_backtest` legacy alias、文档 / package / repo 命名迁移顺序和历史审计保留策略。

## 技术说明

| 项目 | 内容 |
|---|---|
| 设计证据类型 | technical-note |
| 设计依据 | DQ-CP3-CR051-06、HLD-CR051、FEAT-10 DESIGN |
| 文件影响 | 后续新增 `docs/research/PROJECT-IDENTITY-MIGRATION.md`；README、USER-MANUAL、pyproject 等只作为未来候选 |
| 接口 / 数据 / 权限变化 | 无真实改名；不改变当前仓库路径、远端、包名或历史审计证据 |
| 异常、失败与回退 | 若真实改名造成测试或导入风险，保留 alias 兼容层并拆出独立迁移 CR |
| 测试入口 | TC-CR051-04、SEC-TC-04 |
| 风险与重访条件 | 进入实际 package / directory / remote rename 前重访 |

## 不授权项

- 不执行目录重命名。
- 不改远端仓库名、不 git push。
- 不批量替换历史 `process/`、handoff、CR 中的 `local_backtest`。
- 不把 canonical name 决策理解为迁移执行授权。
