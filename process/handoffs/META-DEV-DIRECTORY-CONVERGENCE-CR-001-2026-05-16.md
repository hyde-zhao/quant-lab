---
handoff_id: "META-DEV-DIRECTORY-CONVERGENCE-CR-001-2026-05-16"
from_agent: "meta-po"
to_agent: "meta-dev"
created_at: "2026-05-16"
workflow_id: "local_backtest"
change_id: "CR-001"
story_id: ""
wave_id: "documentation"
status: "ready-for-doc-refresh"
dispatch:
  required: true
  mode: "handoff-only"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ""
  tool_name: ""
  agent_id: ""
  agent_name: "dev-zhao"
  thread_id: ""
  spawned_at: ""
  resumed_at: ""
  completed_at: "2026-05-16"
  evidence: "current tool surface has no spawn_agent/resume_agent/send_input"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# Handoff：CR-001 目录结构收敛执行

## 目标

执行 `CR-001` 的目录结构收敛，只处理空目录、引用清理和必要状态文件更新。不得修改业务逻辑、测试逻辑、真实数据、报告数据、安装脚本或 `delivery/**` 内容。

## 最小上下文

必须读取：

- `process/STATE.md`
- `process/STORY-STATUS.md`
- `process/changes/CR-001-DIRECTORY-STRUCTURE-CONVERGENCE-2026-05-16.md`
- `process/DOCUMENTATION-READINESS-ROUTING-2026-05-16.md`
- `checkpoints/CP8-DELIVERY-READINESS.md`
- `README.md`
- `docs/USER-MANUAL.md`
- `AGENTS.md`

可用事实：

- `work/` 当前仅显示旧骨架目录，`find work -type f -print` 无输出。
- `delivery/` 当前仅显示空子目录，`find delivery -type f -print` 无输出。
- 当前 production 项目正式文档出口是 `README.md` + `docs/USER-MANUAL.md`。
- `delivery/` 在 AGENTS.md 中仍是 meta-flow 通用交付包概念；本 CR 不要求改 AGENTS.md 的 managed 规则块。

## 允许范围

允许：

- 重新核验 `work/` 与 `delivery/` 是否仍无文件。
- 仅删除确认为空的目录：
  - `work/studies/quant-trading/local_backtest/` 及删除后变空的父目录。
  - `delivery/` 下空子目录及删除后变空的 `delivery/` 目录。
- 更新过程状态文件，记录执行结果与阻塞项：
  - `process/STATE.md`
  - `process/STORY-STATUS.md`
  - `process/DOCUMENTATION-READINESS-ROUTING-2026-05-16.md`
  - `checkpoints/CP8-DELIVERY-READINESS.md`
- 创建或更新执行记录，说明执行命令、结果、未删除原因。

禁止：

- 修改 `engine/**`、`strategies/**`、`tests/**`、`config/**`。
- 修改真实 `data/**`、真实 `reports/**` 或任何报告数据。
- 写入 `delivery/**` 内容。
- 生成安装脚本。
- 复制 `llm-wiki` 学习资料到本项目。
- 使用递归强删删除未经核验的非空目录。

## 安全步骤

1. 执行前核验：
   - `find work -type f -print`
   - `find delivery -type f -print`
   - `find work -type d -empty -print`
   - `find delivery -type d -empty -print`
2. 如果 `work/` 或 `delivery/` 任一目录下出现文件，立即停止删除，记录阻塞项：
   - 文件路径
   - 是否用户生成
   - 是否可能属于真实数据、报告、代码或过程产物
   - 建议路由
3. 如果仅存在空目录，使用只删除空目录的命令执行清理，例如 `rmdir` 或等价空目录删除方式。
4. 清理后再次执行：
   - `find work -maxdepth 6 -print`
   - `find delivery -maxdepth 6 -print`
   - `find work -type f -print`
   - `find delivery -type f -print`
5. 将结果写回过程状态；若目录已不存在，应明确记录为 `removed-empty-directory-tree`。

## 引用清理要求

只清理或标注当前治理文件中的“待清理 / 待废弃”状态，不得删除历史审计记录中的旧引用。

必须状态化：

- `work/studies/quant-trading/local_backtest/` 是否已删除，或为何保留。
- `delivery/` 是否已删除，或为何作为废弃空目录保留。
- CP8 是否仍需等待 meta-doc 文档刷新。

## 完成输出

交回时必须列出：

- 实际删除的目录。
- 跳过删除的目录与原因。
- 执行过的核验命令及摘要。
- 更新过的过程文件。
- 是否仍阻塞 CP8。

## 执行记录

### 核验命令与结果

| 阶段 | 命令 | 结果 |
|---|---|---|
| 清理前 | `find work -type f -print` | 无输出；`work/` 下未发现文件 |
| 清理前 | `find delivery -type f -print` | 无输出；`delivery/` 下未发现文件 |
| 清理前 | `find work -type d -empty -print` | 仅发现 `work/studies/quant-trading/local_backtest/{data,reports,notebooks,strategies,engine}` 五个空叶子目录 |
| 清理前 | `find delivery -type d -empty -print` | 仅发现 `delivery/{skills,agents,rules,doc,scripts}` 五个空叶子目录 |
| 清理前 | `find work -maxdepth 6 -print` | 仅显示旧骨架目录树 `work/studies/quant-trading/local_backtest/` 及其五个空子目录 |
| 清理前 | `find delivery -maxdepth 6 -print` | 仅显示 `delivery/` 及其五个空子目录 |
| 删除 | `rmdir work/studies/quant-trading/local_backtest/data work/studies/quant-trading/local_backtest/reports work/studies/quant-trading/local_backtest/notebooks work/studies/quant-trading/local_backtest/strategies work/studies/quant-trading/local_backtest/engine work/studies/quant-trading/local_backtest work/studies/quant-trading work/studies work delivery/skills delivery/agents delivery/rules delivery/doc delivery/scripts delivery` | 退出码 0，无输出；仅删除空目录 |
| 清理后 | `find work -maxdepth 6 -print` | 返回 `find: ‘work’: No such file or directory`；旧 `work/` 空目录树已删除 |
| 清理后 | `find delivery -maxdepth 6 -print` | 返回 `find: ‘delivery’: No such file or directory`；旧 `delivery/` 空目录树已删除 |
| 清理后 | `find work -type f -print` | 返回 `find: ‘work’: No such file or directory`；无残留文件 |
| 清理后 | `find delivery -type f -print` | 返回 `find: ‘delivery’: No such file or directory`；无残留文件 |

### 删除清单

- 已删除：`work/studies/quant-trading/local_backtest/data/`
- 已删除：`work/studies/quant-trading/local_backtest/reports/`
- 已删除：`work/studies/quant-trading/local_backtest/notebooks/`
- 已删除：`work/studies/quant-trading/local_backtest/strategies/`
- 已删除：`work/studies/quant-trading/local_backtest/engine/`
- 已删除：`work/studies/quant-trading/local_backtest/`
- 已删除：清理后变空的父目录 `work/studies/quant-trading/`、`work/studies/`、`work/`
- 已删除：`delivery/skills/`、`delivery/agents/`、`delivery/rules/`、`delivery/doc/`、`delivery/scripts/`
- 已删除：清理后变空的 `delivery/`

### 保留与阻塞

- 因非空保留的目录：无。
- 发现的文件：无。
- BLOCKING：无。
- 文档后续：可交给 meta-doc 按 `process/handoffs/META-DOC-DIRECTORY-DOCS-CR-001-2026-05-16.md` 刷新 `README.md` 与 `docs/USER-MANUAL.md` 的目录边界说明。

## 复用键与关闭条件

- 复用键：`role=meta-dev + workflow_id=local_backtest + change_id=CR-001 + story_id="" + wave_id=documentation`
- 完成后状态：`ready-for-doc-refresh` 或 `blocked`
- 关闭条件：目录清理结果已写入过程状态，且没有未状态化的文件或非空目录。
