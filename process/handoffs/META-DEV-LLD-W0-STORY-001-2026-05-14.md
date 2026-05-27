---
handoff_id: "META-DEV-LLD-W0-STORY-001-2026-05-14"
from_agent: "meta-po"
to_agent: "meta-dev"
phase: "story-execution"
wave: "W0"
story_id: "STORY-001"
task_type: "story-lld-drafting"
status: "dispatched"
created_at: "2026-05-14"
---

# meta-dev 任务交接：STORY-001 LLD 起草

## 调度结论

用户已确认 Story Plan 通过。`DEVELOPMENT-PLAN.yaml` 中 W0 `parallel=false`，且 `STORY-002` 依赖 `STORY-001`、`STORY-003` 依赖 `STORY-001` 与 `STORY-002`，因此首个可执行 Story 仅为 `STORY-001`。

## 当前任务

请使用 `lld-designer` 为 `STORY-001：工程基线与数据契约骨架` 起草 Story 级 LLD。

## 必须读取

| 文件 | 用途 |
|---|---|
| `process/STATE.md` | 当前阶段、门控和下一步 |
| `process/HLD.md` | 已确认 HLD 设计约束 |
| `process/ARCHITECTURE-DECISION.md` | 已确认 ADR 约束 |
| `process/STORY-BACKLOG.md` | Story 边界、Wave 和依赖 |
| `process/DEVELOPMENT-PLAN.yaml` | W0 执行计划和输出文件边界 |
| `process/stories/STORY-001-engine-baseline-data-contracts.md` | 当前 Story 卡片、验收标准和 LLD 输入约束 |
| `AGENTS.md` | Python / uv、LLD 门控和输出隔离规则 |

## 允许修改

| 路径 | 允许动作 |
|---|---|
| `process/stories/STORY-001-engine-baseline-data-contracts-LLD.md` | 创建 LLD，必须保持 14 个可见章节 |
| `process/stories/STORY-001-engine-baseline-data-contracts.md` | 仅允许将状态从 `approved` 更新为 `ready-for-lld-review`，并记录 LLD 输出路径 |
| `process/STORY-STATUS.md` | 同步 STORY-001 状态 |
| `process/STATE.md` | 仅允许记录 STORY-001 LLD 已 ready-for-review、下一步等待 meta-po 发起 LLD 确认 |

## 禁止范围

- 不得创建或修改实现文件：`pyproject.toml`、`uv.lock`、`config/**`、`engine/**`、`strategies/**`、`data/**`、`reports/**`。
- 不得运行 `uv lock` 或安装依赖。
- 不得写入 `delivery/**`。
- 不得创建安装脚本。
- 不得起草 `STORY-002` 或 `STORY-003` 的 LLD。
- 不得把 Story 状态推进到 `lld-approved`、`in-development`、`ready-for-verification` 或 `verified`。

## LLD 输出要求

- 输出文件名必须为 `process/stories/STORY-001-engine-baseline-data-contracts-LLD.md`。
- LLD 必须覆盖 14 个可见章节，并显式消费 Story 卡片中的 `dev_context`、`validation_context` 和 `acceptance_criteria`。
- 必须明确 `pyproject.toml`、`uv.lock`、`config/data_prep.yaml`、`engine/contracts.py`、包初始化文件和 `.gitkeep` 的文件影响范围。
- 必须说明 `engine/contracts.py` 的对象形态选择、字段常量组织、配置解析策略、异常处理、测试设计、实施步骤、回滚策略。
- 必须在 LLD 末尾保留人工确认区；确认前停止，不进入实现。

## meta-qa 说明

当前不唤醒 `meta-qa` 执行验证。`meta-qa` 可在后续 STORY-001 进入 `ready-for-verification` 前读取 LLD 中的测试设计；本轮只需要 `meta-dev` 输出 LLD。
