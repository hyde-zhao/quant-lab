---
story_id: "CR051-S06-project-identity-rename-and-legacy-alias"
title: "项目身份改名与 legacy alias 兼容"
story_slug: "project-identity-rename-and-legacy-alias"
status: "verified"
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
  status: "approved"
implementation_gate:
  evidence_required: true
  evidence_path: "process/stories/CR051-S06-project-identity-rename-and-legacy-alias-IMPLEMENTATION.md"
  evidence_type: "implementation-md"
  implementation_objects: ["docs-handoff", "migration-plan"]
  test_plan_refs:
    - "docs/features/strategy-research-lifecycle/TEST-PLAN.md"
  local_validation_results:
    - "process/checks/CP6-CR051-S06-project-identity-rename-and-legacy-alias-CODING-DONE.md"
  status: "PASS"
dev_gate:
  design_evidence_confirmed: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  cp6_status: "PASS"
  cp6_result: "process/checks/CP6-CR051-S06-project-identity-rename-and-legacy-alias-CODING-DONE.md"
  cp7_status: "PASS"
  cp7_result: "process/checks/CP7-CR051-S06-project-identity-rename-and-legacy-alias-VERIFICATION-DONE.md"
task_count: 2
created_at: "2026-06-14T08:19:09+08:00"
updated_at: "2026-06-14T09:00:24+08:00"
change_id: "CR-051"
---

# CR051-S06：项目身份改名与 legacy alias 兼容

## 目标

冻结 `quant-lab` canonical project name、`local_backtest` legacy alias、文档 / package / repo 命名迁移顺序和历史审计保留策略。

## 技术说明

| 项目 | 内容 |
|---|---|
| 设计证据类型 | technical-note |
| 设计依据 | DQ-CP3-CR051-06、HLD-CR051 §2 / §5.4 / §14、FEAT-10 DESIGN、CP5 context |
| 文件影响 | 后续新增 `docs/research/PROJECT-IDENTITY-MIGRATION.md`；README、USER-MANUAL、pyproject、Windows 默认路径和环境变量只作为未来候选修改对象 |
| 接口 / 数据 / 权限变化 | 无真实改名；不改变当前仓库路径、远端、包名、导入路径或历史审计证据；新文档默认使用 `quant-lab`，历史证据保留 `local_backtest` |
| 异常、失败与回退 | 若真实改名造成测试、导入或路径引用风险，保留 alias 兼容层并拆出独立迁移 CR；若用户要求批量替换历史文件，必须回退 CP3/CP5 重新决策 |
| 测试入口 | TC-CR051-04、SEC-TC-04、路径引用检查、frontmatter / README / pyproject review |
| 风险与重访条件 | 进入实际 package / directory / remote rename、Windows 默认路径迁移或环境变量切换前重访 |
| 偏离记录 | 当前无偏离；本 Story 只冻结 alias policy，不执行任何 rename / push / history rewrite |

### 命名迁移顺序

| 顺序 | 对象 | 主选动作 | 验证 | 本 Story 授权 |
|---|---|---|---|---|
| 1 | 新设计 / 新文档 | 使用 `quant-lab` | 文档 review | 是，文档口径 |
| 2 | 历史 `process/` / CR / handoff | 保留 `local_backtest` 作为当时审计名 | 不批量替换 | 是，保留策略 |
| 3 | README / USER-MANUAL | 后续 CR054 更新显示名和 alias 说明 | docs guardrail | 否，当前只计划 |
| 4 | `pyproject.toml` / package metadata | 后续 CR054 评估 `name`、import、uv lock 影响 | tests + uv lock check | 否，当前只计划 |
| 5 | 仓库目录 / 远端仓库 | 后续迁移 gate 单独授权 | git status / path refs / rollback | 否 |
| 6 | Windows 默认路径 | 后续 CR049/CR054 与用户环境一起迁移 | 用户可覆盖路径 | 否 |

### Alias contract

| 字段 | 主值 | legacy / 兼容 | 说明 |
|---|---|---|---|
| canonical_project_name | `quant-lab` | N/A | 后续新文档和迁移目标使用 |
| legacy_project_alias | `local_backtest` | 保留 | 历史审计名，不批量替换 |
| repo_root_env | `QUANT_LAB_REPO_ROOT` | `LOCAL_BACKTEST_REPO_ROOT` | 新变量主推，旧变量迁移期兼容 |
| default_windows_root | `C:\\quant-lab` | `C:\\local_backtest` | 后续文档提供覆盖项 |

### Clarification / OPEN

| 项目 | 状态 | 说明 |
|---|---|---|
| blocking clarification | 0 | 用户已指定项目名 `quant-lab` |
| non-blocking OPEN | 0 | 实际改名顺序在后续 CR054 / migration gate 细化 |

## 不授权项

- 不执行目录重命名。
- 不改远端仓库名、不 git push。
- 不批量替换历史 `process/`、handoff、CR 中的 `local_backtest`。
- 不把 canonical name 决策理解为迁移执行授权。

## 实现摘要

| 项目 | 内容 |
|---|---|
| 实现证据 | `process/stories/CR051-S06-project-identity-rename-and-legacy-alias-IMPLEMENTATION.md` |
| CP6 结果 | `process/checks/CP6-CR051-S06-project-identity-rename-and-legacy-alias-CODING-DONE.md`，PASS |
| 输出文件 | `docs/research/PROJECT-IDENTITY-MIGRATION.md` |
| 剩余风险 | CP7 需验证未改目录、远端、package metadata、README、USER-MANUAL 或历史审计文件 |
