---
handoff_id: "META-DOC-DIRECTORY-DOCS-CR-001-2026-05-16"
from_agent: "meta-po"
to_agent: "meta-doc"
created_at: "2026-05-16"
workflow_id: "local_backtest"
change_id: "CR-001"
story_id: ""
wave_id: "documentation"
status: "docs-ready-for-cp8-recheck-by-user-report"
dispatch:
  required: true
  mode: "handoff-only"
  platform: "codex"
  agent_role: "meta-doc"
  agent_path: ""
  tool_name: ""
  agent_id: ""
  agent_name: "doc-zheng"
  thread_id: ""
  spawned_at: ""
  resumed_at: ""
  completed_at: "2026-05-16"
  evidence: "handoff-only; user reported meta-doc refresh completed and artifacts verified by meta-po"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# Handoff：CR-001 README 与用户手册刷新

## 目标

刷新正式用户文档，明确本项目目录组织已经收敛到仓库根 `local_backtest/`，并说明 `llm-wiki`、`work/`、`delivery/` 与 agent 协作边界。

## 前置条件

- 优先等待 `process/handoffs/META-DEV-DIRECTORY-CONVERGENCE-CR-001-2026-05-16.md` 执行完成，读取其目录清理结果。
- 如果 meta-dev 发现 `work/` 或 `delivery/` 非空并阻塞删除，文档必须写成“保留并待处理”，不得写成“已清理”。
- 如果 meta-dev 已确认空目录删除完成，文档可写成“旧骨架已清理”。

## 最小上下文

必须读取：

- `process/STATE.md`
- `process/STORY-STATUS.md`
- `process/changes/CR-001-DIRECTORY-STRUCTURE-CONVERGENCE-2026-05-16.md`
- `process/handoffs/META-DEV-DIRECTORY-CONVERGENCE-CR-001-2026-05-16.md`
- `process/DOCUMENTATION-READINESS-ROUTING-2026-05-16.md`
- `checkpoints/CP8-DELIVERY-READINESS.md`
- `README.md`
- `docs/USER-MANUAL.md`
- `AGENTS.md`

## 允许输出

只允许修改：

- `README.md`
- `docs/USER-MANUAL.md`
- 必要的过程状态引用文件：
  - `process/STATE.md`
  - `process/STORY-STATUS.md`
  - `process/DOCUMENTATION-READINESS-ROUTING-2026-05-16.md`
  - `checkpoints/CP8-DELIVERY-READINESS.md`

禁止：

- 写入 `delivery/**`。
- 生成安装脚本。
- 修改业务代码、测试代码、真实数据、报告数据。
- 复制 `llm-wiki` 内容到 `local_backtest`。
- 将 AGENTS.md 的 meta-flow 通用 `delivery/` 规则误写成本 production 项目的用户交付出口。

## 文档必须说明的内容

README 与 `docs/USER-MANUAL.md` 至少补充：

- `local_backtest/` 仓库根是唯一 canonical 工具项目根。
- `llm-wiki` 是学习知识库；本项目不复制学习资料，不把学习材料作为运行输入或交付产物。
- `work/studies/quant-trading/local_backtest/` 是旧建议路径 / 误创建骨架；根据 meta-dev 执行结果说明已清理或保留待处理。
- `delivery/` 不是当前 production 项目的正式交付包出口；正式用户文档出口为 `README.md` + `docs/USER-MANUAL.md`。
- 若 `delivery/` 已清理，应说明当前项目不生成 `delivery/**`、安装脚本或 meta-flow 交付包。
- 若 `delivery/` 因阻塞保留，应说明它是废弃 / 非当前交付出口，不应向其中写入本项目交付物。
- agent 协作边界：meta-po 只编排 CR 与检查点；meta-dev 只做空目录与过程状态收敛；meta-doc 只写正式用户文档；不越权改代码、测试、数据和安装脚本。

## 建议位置

README：

- 在“项目定位”或“目录结构”前后补充 canonical 根与外部知识库边界。
- 在“目录结构”代码块中避免列出已清理的 `work/` 或 `delivery/`；如保留未删除，则明确标注为废弃 / 非交付出口。
- 在“验证状态与限制”中补充本 CR 的目录收敛状态。

`docs/USER-MANUAL.md`：

- 在“开始之前”补充用户应在仓库根 `local_backtest/` 执行命令。
- 在“验证状态与限制”补充目录组织边界。
- 在“参考过程证据”中加入本 CR 或目录收敛 handoff 的引用。

## 完成输出

交回时必须列出：

- 修改的文档章节。
- 对 `work/` 与 `delivery/` 状态的最终表述。
- 是否新增修订记录。
- 是否仍阻塞 CP8。

## 执行记录

### 文档刷新结果

| 检查项 | 结果 | 证据 |
|---|---|---|
| `local_backtest/` canonical 根 | 已写入 README 与 USER-MANUAL | `README.md` §项目根与目录边界；`docs/USER-MANUAL.md` §项目根与协作边界 |
| `llm-wiki` 分工 | 已写为外部学习知识库，不复制进本项目 | `README.md`; `docs/USER-MANUAL.md` |
| `work/` 清理状态 | 已写明旧建议路径 / 误创建空骨架，CR-001 中确认无文件并清理 | `README.md`; `docs/USER-MANUAL.md` |
| `delivery/` 清理状态 | 已写明不是当前 production 项目正式出口，CR-001 中确认无文件并清理；不生成 `delivery/**` 或安装脚本 | `README.md`; `docs/USER-MANUAL.md` |
| agent 协作边界 | 已写明 meta-po / meta-dev / meta-doc 责任边界，不越权修改代码、测试、真实数据、报告数据或安装脚本 | `README.md`; `docs/USER-MANUAL.md` |

### 状态

- 完成状态：`docs-ready-for-cp8-recheck-by-user-report`
- BLOCKING：无。
- CP8：可由 meta-po 刷新自动预检与人工终验稿。

说明：当前 Codex 工具面没有 `spawn_agent` / `resume_agent` / `send_input`，本文件的 `dispatch.mode` 仍为 `handoff-only`；上述完成状态基于用户报告、文件存在性与 meta-po 复核，不表述为有平台级子 agent 调度证据。

## 复用键与关闭条件

- 复用键：`role=meta-doc + workflow_id=local_backtest + change_id=CR-001 + story_id="" + wave_id=documentation`
- 完成后状态：`docs-ready-for-cp8-recheck-by-user-report` 或 `blocked`
- 关闭条件：README 与用户手册均完成目录边界刷新，并且过程状态指向 CP8 重新审查。
