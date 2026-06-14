---
story_id: "CR053-S05-cr058-migration-input-and-close-gate"
title: "CR058 真实迁移输入与关闭门禁"
story_slug: "cr058-migration-input-and-close-gate"
status: "verified"
priority: "P1"
implementation_allowed: true
implementation_allowed_until: "CP5 approved at 2026-06-14T11:52:15+08:00; static Markdown reports / guardrail evidence only"
wave: "CR053-W3-MIGRATION-GATE"
depends_on:
  - "CR053-S02-repo-inventory-and-path-classification"
  - "CR053-S03-path-reference-and-legacy-alias-dry-run"
  - "CR053-S04-manifest-transfer-and-backup-plan"
dependency_type:
  - "inventory-contract"
  - "path-reference-contract"
  - "backup-contract"
cp5_batch: "CR053-MIGRATION-INVENTORY-BATCH-A"
feature_design_refs:
  - "docs/features/quant-lab-migration-dry-run/DESIGN.md"
  - "docs/features/quant-lab-migration-dry-run/TASKS.md"
lld_policy:
  required_level: "technical-note"
  trigger_reasons: ["follow-up-gate", "migration-input", "low-code-planning"]
  rationale: "本 Story 聚合 S01..S04 输出并形成 CR058 输入，不直接实现复杂模块，可用 technical-note。"
  waiver_reason: ""
  revisit_condition: "CR058 范围、远端仓库改名、git push/tag 或真实 NAS 操作授权发生变化时。"
  evidence_path: "process/stories/CR053-S05-cr058-migration-input-and-close-gate.md"
file_ownership:
  primary:
    - "docs/release/MIGRATION-PLAN-CR053.md"
  shared:
    - "process/changes/CR-053-QUANT-LAB-MIGRATION-INVENTORY-AND-DRY-RUN-2026-06-14.md"
  forbidden:
    - "real file move"
    - "git push / tag"
    - "remote repo rename"
lld_gate:
  design_evidence_type: "technical-note"
  design_evidence_path: "process/stories/CR053-S05-cr058-migration-input-and-close-gate.md#技术说明"
  status: "confirmed"
  confirmed: true
dev_gate:
  design_evidence_confirmed: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  dependency_note: "依赖 S02/S03/S04 设计合同；CP5 已全量确认，可进入静态 Markdown 报告 / guardrail evidence 实现。"
  not_authorized:
    - "real file move"
    - "git push / tag"
    - "remote repo rename"
change_id: "CR-053"
created_at: "2026-06-14T10:59:13+08:00"
updated_at: "2026-06-14T12:19:53+08:00"
implementation_evidence:
  path: "process/stories/CR053-BATCH-A-IMPLEMENTATION.md"
  cp6_check: "process/checks/CP6-CR053-MIGRATION-INVENTORY-BATCH-A-CODING-DONE.md"
  output: "docs/release/MIGRATION-PLAN-CR053.md"
  status: "implemented-cp6-static"
cp7_verification_evidence:
  path: "docs/quality/VERIFICATION-REPORT-CR053.md"
  cp7_check: "process/checks/CP7-CR053-MIGRATION-INVENTORY-BATCH-A-VERIFICATION-DONE.md"
  context: "process/context/CP7-CR053-VERIFICATION-CONTEXT.yaml"
  result: "PASS"
  verified_at: "2026-06-14T12:30:26+08:00"
---

# CR053-S05：CR058 真实迁移输入与关闭门禁

## 目标

定义 CR053 dry-run 输出如何成为 CR058 repo-local mechanical move 的输入，并冻结 CR053 关闭时仍不授权真实迁移、git push/tag、远端仓库改名或 NAS 操作。

## 技术说明

| 项目 | 内容 |
|---|---|
| 设计证据类型 | technical-note |
| 设计依据 | HLD-CR053 §8 / §12 / §15、ADR-CR053-004、Feature DESIGN IF-CR053-05、TASKS CR053-T05 / CR053-R05 |
| 文件影响 | 未来新增 `docs/release/MIGRATION-PLAN-CR053.md`；消费 S02 `docs/release/MIGRATION-INVENTORY-CR053.md`、S03 `docs/release/PATH-REFERENCES-CR053.md`、S04 `docs/release/BACKUP-PLAN-CR053.md` 和 S01 `docs/release/NAS-MAPPING-CR053.md`；本 Story 不创建 LLD 文件 |
| 接口 / 数据 / 权限变化 | 只定义 CR058 输入门禁、缺失项阻断条件、rollback_ref 要求和关闭判断；不执行文件移动、远端仓库改名、git push/tag、NAS 操作、数据湖变量替换或真实迁移 |
| 异常和回退 | 缺 inventory / path references / backup plan / rollback_ref / CP5 approve 任一输入时，CR058 input 标记 `blocked_missing_input`；发现用户要求 CR053 内执行真实迁移、NAS copy 或远端操作时，回退 host-orchestrator 发起新 CR / 授权门；发现 S02-S04 合同偏差时回到对应 Story 设计证据修订 |
| 测试入口 | TC-CR053-07、SEC-CR053-01 |
| 风险 | CR053 dry-run 输出可能被误读为真实迁移授权；CR058 若缺 rollback_ref 或 backup evidence 会扩大迁移风险；历史 `local_backtest` 引用需保留审计语境，不得无差别改写 |
| 偏离记录 | 无偏离；按 lld_policy 保持 technical-note，不创建 S05 LLD 文件；当前 `open_items=0`、`blocks_lld=true` clarification=0 |

### CR058 输入门禁

| 输入项 | 来源 Story | 必填字段 / 证据 | 缺失时处理 |
|---|---|---|---|
| Root / host map | S01 | 逻辑 root、host_role、allowed_content、forbidden_content、lake alias、Windows package exchange read-only | 阻断 CR058，标记 `root_map_missing` |
| Repo inventory | S02 | path、owner、artifact_class、move_action、risk、verification_rule、forbidden_content_result | 阻断 CR058，标记 `inventory_missing` |
| Path references dry-run | S03 | reference、context、classification、proposed_action、manual_review_required | 阻断 CR058，标记 `references_missing` |
| Transfer / backup plan | S04 | manifest-first transfer contract、backup class、restore rehearsal requirement、rollback checkpoint | 阻断 CR058，标记 `backup_plan_missing` |
| CP5 / CP8 gate | Host-orchestrator | CR053 CP5 approved、后续 CP6/CP7/CP8 结论、not_authorized 边界 | 未确认则不得启动 CR058 |

### 实现灰区与取舍记录

| 项目 | 状态 | 说明 |
|---|---|---|
| blocking clarification | 0 | CP3 已确认：Linux 研究机只做 `/mnt/quant-lab/hot`、`archive`、`cold-backup` 逻辑视图；`MARKET_DATA_LAKE_ROOT` 不调整；Windows 只映射 package exchange。 |
| OPEN / Spike | 0 | 真实 repo-local migration 属于 CR058；NAS / archive 实迁属于 CR060+ 或独立授权，不阻塞 CR053 CP5。 |
| 不授权项 | active | CR053 不授权真实 file move、remote rename、git push/tag、NAS 操作、数据湖移动、凭据读取或 QMT/MiniQMT runtime。 |
