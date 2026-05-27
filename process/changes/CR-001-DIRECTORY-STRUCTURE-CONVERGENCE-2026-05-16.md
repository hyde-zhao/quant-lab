---
cr_id: "CR-001"
status: "closed"
impact_level: "medium"
rollback_to: "documentation"
approval_result: "accepted"
completion_result: "completed"
created_at: "2026-05-16"
created_by: "meta-po"
approved_by: "user"
approved_at: "2026-05-16"
closed_by: "meta-po"
closed_at: "2026-05-16"
source: "user"
linked_issue: ""
---

# CR-001 目录结构收敛

## 变更描述

用户确认采用目录组织建议，并要求完成 `local_backtest` 目录改造与相关文档写作。

已确认目标结构：

- `local_backtest` 仓库根目录是唯一 canonical 工具项目根。
- `llm-wiki` 继续作为学习知识库，不把学习资料拷贝进 `local_backtest`。
- `work/studies/quant-trading/local_backtest/` 是空的旧建议路径 / 误创建骨架，应由执行 agent 先确认空目录后清理；若发现非空内容，必须停止删除并状态化。
- 当前 production 项目正式文档出口为 `README.md` + `docs/USER-MANUAL.md`。
- 当前 production 项目不使用 `delivery/` 作为交付包出口；`delivery/` 当前没有文件，应由执行 agent 先确认空目录后清理，或在阻塞时由文档明确废弃。

本 CR 不授权修改业务逻辑、测试逻辑、真实数据、报告数据、安装脚本或 `delivery/**` 内容。

## 当前事实核对

| 对象 | 核对结论 | 证据 |
|---|---|---|
| 当前阶段 | `delivered`，CP8 人工终验已通过 | `process/STATE.md`; `checkpoints/CP8-DELIVERY-READINESS.md` |
| Story 状态 | `STORY-001` 至 `STORY-013` 均为 `verified` | `process/STORY-STATUS.md` |
| 正式文档出口 | 用户已确认 `README.md` + `docs/USER-MANUAL.md` | `process/DOCUMENTATION-READINESS-ROUTING-2026-05-16.md` |
| `work/` | 旧骨架目录已确认无文件并清理，当前不存在 | `process/checks/CP8-DELIVERY-READINESS.md`; `process/STATE.md` |
| `delivery/` | 空目录树已确认无文件并清理，当前不存在 | `process/checks/CP8-DELIVERY-READINESS.md`; `process/STATE.md` |
| README / 手册 | 已明确 canonical 根、`llm-wiki` 分工、`work/` / `delivery/` 清理或废弃状态 | `README.md`; `docs/USER-MANUAL.md` |
| AGENTS.md | 仍包含 meta-flow 通用 `delivery/` 规则；不等同于本 production 项目的正式用户文档出口 | `AGENTS.md` |

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `README.md` | 原文档更新 | 保留既有用户文档内容，在目录结构 / 项目定位相关章节增量说明 canonical 根、`llm-wiki` 分工、`work/` / `delivery/` 状态 | 由 meta-doc 判断是否新增 `## 修订记录`；若新增，记录本 CR | approved |
| `docs/USER-MANUAL.md` | 原文档更新 | 保留既有用户操作手册内容，在开始之前 / 验证状态与限制 / 参考过程证据等相关位置增量说明目录边界 | 由 meta-doc 判断是否新增 `## 修订记录`；若新增，记录本 CR | approved |
| `process/STATE.md` | 原文档更新 | 保留 CP8 历史状态，追加本 CR 活跃状态、handoff 与历史记录 | `history` | approved |
| `process/STORY-STATUS.md` | 原文档更新 | 保留 Story 验证状态，追加 documentation 阶段目录收敛门控 | 不适用 | approved |
| `process/DOCUMENTATION-READINESS-ROUTING-2026-05-16.md` | 原文档更新 | 保留原 documentation readiness 结论，追加本 CR 导致 CP8 前置收敛要求 | 不适用 | approved |
| `checkpoints/CP8-DELIVERY-READINESS.md` | 原文档更新 | 保留 CP8 人工终验稿，已回填用户 2026-05-16 `通过` 结论 | 人工审查结果区 / checklist | approved |
| `process/USE-CASES.md` | 不变 | 需求 / 场景基线不变 | 不适用 | approved |
| `process/REQUIREMENTS.md` | 不变 | 需求 / 场景基线不变 | 不适用 | approved |
| `process/HLD.md` | 不变 | 架构设计不变；本 CR 是交付组织与文档收敛 | 不适用 | approved |
| `process/DEVELOPMENT-PLAN.yaml` | 不变 | Story DAG 与实现计划不变 | 不适用 | approved |

## 旧基线映射

| 原基线对象 | 新增 / 修改对象 | 保留策略 | 映射说明 |
|---|---|---|---|
| `work/studies/quant-trading/local_backtest/` 空骨架 | 无新目录；canonical 根为仓库根 `local_backtest/` | CR 记录旧路径，执行后删除空目录或状态化阻塞 | 旧路径是误创建骨架，不作为正式项目根 |
| `delivery/` 空目录骨架 | 正式用户文档出口仍为 `README.md` + `docs/USER-MANUAL.md` | CR 记录旧空目录，执行后删除空目录或文档标注废弃 | 当前 production 项目不使用 meta-flow `delivery/` 交付包出口 |
| `llm-wiki` 学习知识库 | 不拷贝进 `local_backtest` | 文档说明边界 | `llm-wiki` 与本工具项目保持分工隔离 |
| README / 手册既有目录说明 | README / 手册增量目录边界说明 | 原文保留并增量更新 | 不重写业务能力说明，只补目录组织和协作边界 |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论（true/false） | 处理动作 |
|------|----------|-----------|--------------------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | `process/REQUIREMENTS.md` | false | 不修改需求基线 |
| 场景层 | 是否改变测试矩阵覆盖范围 | `process/STORY-STATUS.md`; `process/TEST-STRATEGY.md` | false | 不改变测试矩阵；仅记录 CP8 前目录治理门控 |
| 计划层 | 是否改变 Phase、Wave、任务依赖 | `process/STATE.md`; handoff | true | 已在 `documentation` 阶段完成 CR 收敛与 CP8 终验，最终推进为 `delivered` |
| 安全层 | 是否引入新的高风险动作或权限要求 | 空目录删除；引用清理 | true | 只允许 `rmdir` / 等价空目录删除；发现任何文件或非空目录即停止并状态化，不得删除数据、代码、报告或安装脚本 |
| 交付层 | 是否需要重新生成交付物或回归子集 | `README.md`; `docs/USER-MANUAL.md`; `checkpoints/CP8-DELIVERY-READINESS.md` | true | meta-doc 刷新文档；CP8 在 CR 收敛后重新审查 |

## 回退决策

- 影响范围：局部，限定在目录骨架、过程状态和用户文档说明。
- 回退到阶段：`documentation`。
- 需要重新确认的对象：
  - `README.md`
  - `docs/USER-MANUAL.md`
  - `checkpoints/CP8-DELIVERY-READINESS.md`
- 回滚方式：
  - 若目录清理误删空目录需求发生变化，可由 meta-dev 重新创建空目录骨架；不得恢复任何未记录文件。
  - 若文档说明不符合用户预期，由 meta-doc 按本 CR 修订 README / 手册并重新提交 CP8。
  - 若发现 `work/` 或 `delivery/` 非空，停止删除，保留现场，更新 `process/STATE.md` 与本 CR 的阻塞说明。

## 处理结论

- 审批结论：`accepted`
- 完成结论：`completed`
- meta-dev 执行结论：`directory-cleanup-pass-no-blocking`
- [ ] 自动批准（低风险）
- [x] 已完成并关闭（中风险）
- [ ] 待人工审批（高风险）

本 CR 已获得用户对目录组织建议的确认；meta-dev 已完成空目录核验与清理，meta-doc 已刷新 README / USER-MANUAL 的目录边界说明。当前无 BLOCKING，用户已在 CP8 人工终验中回复 `通过`，本 CR 于 2026-05-16 关闭为 `closed / accepted / completed`。

## meta-dev 执行结果

| 项 | 结果 |
|---|---|
| 清理前文件核验 | `find work -type f -print` 与 `find delivery -type f -print` 均无输出 |
| 清理前空目录核验 | `work/` 仅含 `work/studies/quant-trading/local_backtest/` 旧骨架及五个空子目录；`delivery/` 仅含五个空子目录 |
| 删除方式 | 使用 `rmdir`，只删除空目录 |
| 已删除 `work/` 范围 | `work/studies/quant-trading/local_backtest/{data,reports,notebooks,strategies,engine}/`、`work/studies/quant-trading/local_backtest/`、清理后变空的 `work/studies/quant-trading/`、`work/studies/`、`work/` |
| 已删除 `delivery/` 范围 | `delivery/{skills,agents,rules,doc,scripts}/` 与清理后变空的 `delivery/` |
| 清理后核验 | `find work -maxdepth 6 -print`、`find delivery -maxdepth 6 -print`、`find work -type f -print`、`find delivery -type f -print` 均返回目录不存在 |
| 因非空保留目录 | 无 |
| BLOCKING | 无 |
| 下一步 | 已完成；进入 CP8 终验结果归档与项目 delivered 收敛 |

## meta-doc 执行结果

| 项 | 结果 |
|---|---|
| 文档输出 | `README.md` 与 `docs/USER-MANUAL.md` 已刷新 |
| canonical 根 | 已明确 `local_backtest/` 仓库根是唯一 canonical 工具项目根 |
| `llm-wiki` 分工 | 已明确 `llm-wiki` 是外部学习知识库，不复制进本项目、不作为运行输入或交付产物 |
| `work/` 状态 | 已明确 `work/studies/quant-trading/local_backtest/` 是旧建议路径 / 误创建空骨架，CR-001 中确认无文件并已清理 |
| `delivery/` 状态 | 已明确 `delivery/` 不是当前 production 项目正式出口，CR-001 中确认无文件并已清理；当前项目不生成 `delivery/**`、安装脚本或 meta-flow 交付包 |
| agent 协作边界 | 已明确 meta-po / meta-dev / meta-doc 的职责边界，且不越权修改代码、测试、真实数据、报告数据或安装脚本 |
| BLOCKING | 无 |
| 下一步 | 已完成；CP8 人工终验已通过，CR-001 已关闭 |

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| Handoff | `process/handoffs/META-DEV-DIRECTORY-CONVERGENCE-CR-001-2026-05-16.md` | 空目录核验与清理、过程状态更新 |
| Handoff | `process/handoffs/META-DOC-DIRECTORY-DOCS-CR-001-2026-05-16.md` | README 与用户手册目录边界刷新 |
| Checkpoint | `checkpoints/CP8-DELIVERY-READINESS.md` | CP8 人工终验已通过并回填 |

## 收敛状态

- 当前状态：`closed`
- 阻塞项：无。
- 关闭结论：CP8 人工终验已于 2026-05-16 `approved`，本 CR 已关闭为 `closed / accepted / completed`。
- meta-qa 后置复核：当前不是必须前置项。理由是 CR-001 只涉及空目录清理与 README / USER-MANUAL 目录边界说明，未修改代码、测试、真实数据、报告数据、安装脚本或 `delivery/**`；且已有文档后置 QA 复核 PASS 作为 CP8 前置证据。若用户在 CP8 中要求额外独立复核，再创建新的 meta-qa handoff。
