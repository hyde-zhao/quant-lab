---
cr_id: "CR-053"
status: "active-cp2-approved-ready-for-cp3"
impact_level: "high"
workflow_mode_before: "standard"
workflow_mode_after_change: "standard"
fast_lane_upgrade_reason: "命中项目身份迁移、仓库重布局、路径引用、归档边界、Git 归档点和未来真实迁移门禁；不得使用 fast-lane。"
rollback_to: "CR051 closed-current-delivery baseline"
approval_result: "cp2-approved"
created_at: "2026-06-14T09:39:26+08:00"
created_by: "host-orchestrator"
approved_by: "user"
approved_at: "2026-06-14T09:51:11+08:00"
source: "cp8-follow-up"
linked_issue: ""
parent_cr: "CR-051"
source_checkpoint: "process/checkpoints/CP8-CR051-DELIVERY-READINESS.md"
source_decision_id: "USER-20260614-START-CR053-MIGRATION-INVENTORY"
follow_up_type: "migration-inventory-dry-run"
risk_class: "project_identity_migration_repository_relayout_archive_boundary"
owner: "host-orchestrator"
revisit_condition: "CR053 CP2 / CP3 人工门禁、CR046 恢复 / 关闭、或用户要求立即执行真实目录迁移 / NAS 操作 / git push 时重访。"
acceptance_criteria: "完成 quant-lab 迁移前的 inventory / dry-run 范围定义、路径风险分类、Git 归档点策略、禁止操作边界、编号冲突处理和后续真实迁移门禁；不执行真实迁移。"
close_condition: "CR053 通过 CP8，且迁移 inventory / dry-run 设计、静态报告和后续真实迁移授权门禁均完成验证；不要求实际移动目录、访问 NAS 或 push。"
cr_index_path: "process/changes/CR-INDEX.yaml"
---

# CR-053 quant-lab Migration Inventory and Dry-run

## 变更描述

用户在 CR051 关闭后回复“cr053”。结合 CR051 CP8 关闭后的 `STATE.md.next_action` 与 `CR-INDEX.yaml.next_action`，本 CR 将 `CR053` 启动为 `quant-lab` 项目迁移前的 inventory / dry-run 设计与准入，而不是事件型策略研究流程。

本 CR 的目标是先把真实迁移前必须知道的对象盘清楚：当前 Git 仓库内有哪些目录、哪些路径引用、哪些文件属于运行态 / 过程态 / 长期文档 / 研究合同 / 未来归档出口、哪些内容不得进入 Git、哪些动作必须等后续人工授权。CR053 不执行真实目录重命名、不移动文件、不访问 NAS、不扫描外部 archive、不读取凭据、不 push、不启动 QMT / MiniQMT。

## CP8 Follow-up 来源

| 字段 | 内容 |
|---|---|
| 父级 CR | `CR-051` |
| 来源检查点 | `process/checkpoints/CP8-CR051-DELIVERY-READINESS.md` |
| 来源决策 ID | `USER-20260614-START-CR053-MIGRATION-INVENTORY` |
| follow-up 类型 | `migration-inventory-dry-run` |
| 风险等级 | `project_identity_migration_repository_relayout_archive_boundary` |
| owner | `host-orchestrator` |
| 重访条件 | CR053 CP2 / CP3 人工门禁、CR046 状态变化、或用户要求真实迁移 / NAS 操作 / git push |
| 验收标准 | inventory / dry-run 范围、路径风险分类、Git 归档点策略和不授权边界完成 |
| 关闭条件 | CR053 CP8 approved；真实迁移另起 CR 或 runtime_authorization gate |

## 编号冲突处理

CR051 原后续表中曾把 `CR053-candidate` 标为“事件型策略研究流程”。但 CR051 关闭时，最新 `STATE.md` 和 `CR-INDEX.yaml` 已将推荐下一步写为 `CR053 migration inventory / dry-run`，用户随后直接回复“cr053”。按当前用户指令和最新状态优先，本 CR 占用 `CR-053` 编号用于迁移盘点 / dry-run。

旧事件型策略研究流程候选不删除，改号为 `CR057-candidate` 并继续受 `CR052` 阻塞。

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `process/changes/CR-051-STRATEGY-RESEARCH-LIFECYCLE-FRAMEWORK-2026-06-14.md` | 原文档更新 | 保留 CR051 原后续路线，追加 CR053 编号冲突处理和事件型候选改号说明 | `## 后续事项台账` | updated |
| `docs/research/PROJECT-IDENTITY-MIGRATION.md` | 原文档更新 | 保留 CR051 设计基线；CR053 后续追加 inventory / dry-run 结果 | `## 修订记录` | pending-after-cp3 |
| `docs/research/ARCHIVE-GOVERNANCE.md` | 原文档更新 | 保留 CR051 archive boundary；CR053 后续追加迁移前 forbidden content / artifact 分类 | `## 修订记录` | pending-after-cp3 |
| `process/STATE.md` | 原文档更新 | 保留 CR046 paused recovery point 和 CR051 closed baseline；新增 CR053 CP2 approved 状态 | `history` | updated |
| `process/changes/CR-INDEX.yaml` | 原文档更新 | 保留 CR046 active paused 和 CR051 closed；新增 CR053 active CP2 approved | `active_crs` | updated |
| `process/context/CP2-CR053-REQUIREMENT-CONTEXT.yaml` | 新增 | N/A | capsule 文件 | approved |
| `process/discussions/CP2-CR053-SCENARIO-DISCUSSION-LOG.md` | 新增 | N/A | 讨论日志 | approved |
| `process/checks/CP2-CR053-REQUIREMENTS-BASELINE.md` | 新增 | N/A | 自动预检结果 | pass |
| `process/checkpoints/CP2-CR053-REQUIREMENTS-BASELINE.md` | 新增 | N/A | Decision Brief | approved |

## 旧基线映射

| 原基线对象 | 新增 / 修改对象 | 保留策略 | 映射说明 |
|---|---|---|---|
| CR051 项目身份迁移设计 | CR053 inventory / dry-run 准入 | 原文保留 | CR051 说明目标结构和原则；CR053 定义迁移前静态盘点与 dry-run 验证门。 |
| `local_backtest` legacy alias | `quant-lab` canonical migration plan | 原文保留 | CR053 只设计和盘点引用，不批量替换历史过程证据。 |
| CR051 `CR053-candidate` 事件型策略 | `CR057-candidate` 事件型策略 | 改号保留 | 避免 CR053 编号冲突；策略族扩展仍受 CR052 proof cycle 阻塞。 |
| CR046 paused CP6 recovery point | CR053 migration inventory scope | 原文保留 | CR053 不恢复 CR046，不修改 CR046 运行边界；后续真实迁移需检查 CR046 引用影响。 |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论（true/false） | 处理动作 |
|------|----------|-----------|--------------------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | quant-lab 迁移前 inventory / dry-run 范围 | true | 新增 CR053 范围基线和 CP2 决策；不改全局需求文档正文。 |
| 场景层 | 是否改变测试矩阵覆盖范围 | 路径引用盘点、dry-run 报告、禁止操作边界 | true | 在 CP2 讨论日志中登记 SC-CR053-01..06；后续 CP3 / CP4 再拆验证场景。 |
| 计划层 | 是否改变 Phase、Wave、Story / 任务依赖 | CR053、CR051 follow-up 编号、后续真实迁移 CR | true | CR053 进入 standard；真实迁移仍后置，不在本 CR CP2 自动执行。 |
| 安全层 | 是否引入新的高风险动作或权限要求 | repo relayout、NAS、archive、Git history、凭据边界 | true | 本 CR 首轮只授权设计门禁；真实移动、NAS、push、凭据读取均保持 not-authorized。 |
| 交付层 | 是否需要重新生成交付物或回归子集 | CR tracking、CP2 context/checkpoint、后续 migration docs | true | 新增 CR053 CP2 证据；后续交付 static inventory / dry-run 报告。 |

## 回退决策

- 影响范围：全局迁移治理，但当前只进入 CP2 门禁，不触碰真实文件移动。
- 回退到阶段：`CR051 closed-current-delivery baseline`。
- 需要重新确认的对象：
  - 是否允许 `CR053` 编号用于迁移 inventory / dry-run。
  - 是否将旧事件型策略候选改号为 `CR057-candidate`。
  - 是否继续禁止真实目录迁移、NAS 操作、外部 archive 扫描、git push 和凭据读取。
  - 是否允许后续 CR053 CP6 在 Git 内生成静态 inventory / dry-run 报告。

## fast-lane 判定

| 条件 | 是否命中 | 说明 |
|---|---|---|
| 仅低风险轻量实现 / 文档 / 规则修改 | false | 涉及项目重布局、路径引用、归档边界和后续真实迁移门禁。 |
| 修改架构、权限、安全边界或平台安装路径 | true | 迁移会影响 canonical 项目名、目录结构、外部 archive / NAS 边界。 |
| 修改外部接口契约、文件所有权或多 Story 依赖 | true | 后续可能影响 README、pyproject、process/docs 引用和迁移验证。 |
| 需要 HLD / LLD 才能解释影响 | true | 必须先设计 inventory / dry-run 合同和禁止操作边界。 |
| 是否保持 fast-lane | false | standard。 |

## LLD 设计批次门禁

- 是否需要 LLD 设计批次：true
- batch_id：`CR053-MIGRATION-INVENTORY-BATCH-A`
- 批次范围来源：CR053 CP3 / CP4 后确定
- 批次内 Story：
  - `TBD after CP4`
- 批次人工确认稿：`process/checkpoints/CP5-CR053-MIGRATION-INVENTORY-BATCH-A-LLD-BATCH.md`
- 开发启动条件：
  - [x] CR053 CP2 approved
  - [ ] CR053 CP3 approved
  - [ ] CR053 CP4 Story DAG PASS
  - [ ] 批次内全部 Story 设计证据已输出
  - [ ] 批次内全部 Story CP5 自动预检已通过
  - [ ] 批次 CP5 人工确认结论为 `approved`

## 执行链路

| 顺序 | 责任角色 | 动作 | 输入 | 输出 | 门控 | 完成后下一步 |
|---|---|---|---|---|---|---|
| 1 | `host-orchestrator` | 创建 CR053 与 CP2 门禁 | 用户回复“cr053”、CR051 CP8 closed、STATE / CR-INDEX | 正式 CR、context、discussion、CP2 auto check、CP2 checkpoint | 不执行真实迁移 | 已获 CP2 approve |
| 1.1 | `host-orchestrator` | 回填 CP2 approved | 用户回复“好的，同意” | CP2 checkpoint approved、CR053 ready-for-cp3、STATE / CR-INDEX updated | 不执行 inventory、不执行真实迁移 | 进入 CP3 HLD 设计 |
| 2 | `meta-pm` / `host-orchestrator` | 收敛迁移 inventory / dry-run 需求 | CP2 approved | requirements baseline / scenario matrix | CP2 approved | 进入 CP3 |
| 3 | `meta-se` | 设计 inventory / dry-run HLD | CP2 baseline、CR051 设计 | HLD / ADR / migration design | CP3 | 进入 story planning |
| 4 | `meta-se` / `meta-dev` | 拆 Story 与设计证据 | CP3 approved | CP4 / CP5 evidence | CP4 / CP5 | 进入 implementation |
| 5 | `meta-dev` | 生成静态 inventory / dry-run 报告 | CP5 approved | Git 内报告和验证脚本 / 文档 | 不访问 NAS、不移动文件 | 进入验证 |
| 6 | `meta-qa` | 验证报告和禁止操作边界 | CP6 evidence | CP7 verification | CP7 | 准备 CP8 |
| 7 | `host-orchestrator` | CP8 收敛 | 全部证据 | release readiness | 用户确认 | 关闭 CR053 |

## 后续事项台账

- 是否存在后续事项：true
- 台账路径：沿用本 CR 正式文件 §后续事项台账；必要时 CP8 拆独立 follow-up tracking
- CR 索引路径：`process/changes/CR-INDEX.yaml`
- 一致性检查：`uv run --python 3.11 python scripts/check_cr_tracking_consistency.py --project-root .`

| 候选编号 | 标题 | 状态 | 类型 | 优先级 | 正式 CR 路径 | 相关 active CR / blocked_by / superseded_by | 当前门控 | 阻塞原因 | 下一步 |
|---|---|---|---|---:|---|---|---|---|---|
| CR058-candidate | 真实 mechanical move / repo relayout | candidate | CR | 1 |  | blocked_by=CR053 | migration_execution_gate | 需 CR053 inventory / dry-run CP8 approved 和用户独立 runtime_authorization | 后续单独授权真实目录移动和引用修复 |
| CR059-candidate | remote repository rename / git tag / push plan | candidate | CR | 2 |  | blocked_by=CR053 | git_remote_gate | 需用户明确授权远端仓库操作 | 后续单独设计 tag / remote rename / push |

## 处理结论

- 审批结论：`cp2-approved`
- [ ] 自动批准（低风险）
- [ ] 待人工确认（中风险）
- [x] 人工审批已通过（高风险）

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| CR | `CR-051` | 策略研究生命周期框架和 quant-lab 命名 / 迁移设计基线 |
| CR | `CR-046` | QMT / MiniQMT 双目标策略交付框架；当前 paused CP6，不恢复 |
| DECISION | `DQ-CP3-CR051-06` | quant-lab 作为正式项目名，local_backtest 作为 legacy alias |
| CHECKPOINT | `process/checkpoints/CP8-CR051-DELIVERY-READINESS.md` | CR051 CP8 approved / READY |
| DOC | `docs/research/PROJECT-IDENTITY-MIGRATION.md` | CR051 项目身份迁移设计基线 |
