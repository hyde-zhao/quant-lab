---
handoff_id: "META-DOC-DOCUMENTATION-README-USER-MANUAL-2026-05-16"
project_id: "local_backtest"
created_at: "2026-05-16"
created_by: "meta-po"
from_agent: "meta-po"
to_agent: "meta-doc"
scope: "documentation execution: write README.md and docs/USER-MANUAL.md after delivery route authorization"
status: "ready-for-dispatch"
priority: "REQUIRED"
delivery_write_allowed: false
documentation_write_allowed: true
authorized_output_paths:
  - "README.md"
  - "docs/USER-MANUAL.md"
implementation_allowed: false
data_generation_allowed: false
install_script_generation_allowed: false
dispatch:
  required: true
  mode: "handoff-only"
  platform: "codex"
  agent_role: "meta-doc"
  agent_path: ""
  tool_name: ""
  agent_id: ""
  agent_name: ""
  thread_id: ""
  spawned_at: ""
  resumed_at: ""
  completed_at: ""
  evidence: "handoff-created-only; current tool surface has no spawn_agent/resume_agent/send_input"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
  note: "本文件仅为 meta-po 创建的交接输入；不表示 meta-doc 已执行。用户已确认文档出口为 README.md + docs/USER-MANUAL.md，可拉起 meta-doc 写入这两个路径；仍不得写 delivery/**、安装脚本、代码、测试或真实数据。"
---

# Meta-doc Documentation Handoff

## 1. 任务目标

由 `meta-doc` 输出本地离线量化回测器的正式用户文档。用户已确认文档输出路径采用选项 2：仓库根 `README.md` + `docs/USER-MANUAL.md`。当前 handoff 可执行，但只授权写入这两个文档路径。

## 2. 当前前置门控

| 门控 | 状态 | 说明 |
|---|---|---|
| Story 验证 | PASS | `STORY-001` 至 `STORY-013` 均为 `verified` |
| 批量 LLD / Story Package | PASS | `checkpoints/STORY-PACKAGE-LLD-CHECKPOINT.md` 已由用户于 2026-05-15 确认通过 |
| QA documentation readiness | PASS | `process/handoffs/META-QA-DOCUMENTATION-READINESS-2026-05-16.md` 建议进入 documentation |
| 文档交付出口 | PASS | 用户已于 2026-05-16 确认采用选项 2：仓库根 `README.md` + `docs/USER-MANUAL.md` |

## 2.1 授权输出路径

meta-doc 可写入：

- `README.md`
- `docs/USER-MANUAL.md`

meta-doc 不得写入：

- `delivery/**`
- `delivery/scripts/**`
- 业务源码或测试源码
- 真实生产行情数据、raw 数据、parquet 数据或报告数据样本
- 安装脚本

## 3. 最小必要上下文

meta-doc 应读取：

- `process/DOCUMENTATION-READINESS-ROUTING-2026-05-16.md`
- `process/STATE.md`
- `process/STORY-STATUS.md`
- `process/REQUIREMENTS.md`
- `process/USE-CASES.md`
- `process/HLD.md`
- `process/ARCHITECTURE-DECISION.md`
- `process/STORY-BACKLOG.md`
- `process/DEVELOPMENT-PLAN.yaml`
- `process/VERIFICATION-REPORT.md`
- `process/TEST-STRATEGY.md`
- `process/handoffs/META-QA-DOCUMENTATION-READINESS-2026-05-16.md`
- `process/handoffs/META-QA-REGRESSION-F004-LOGGING-2026-05-16.md`

不应默认加载：

- 完整历史会话 transcript。
- 与 documentation 无关的中间失败草稿。
- 全量 Story LLD 正文；如需核对能力边界，优先读取 `STORY-BACKLOG.md`、`DEVELOPMENT-PLAN.yaml` 和 QA handoff 摘要。

## 4. 文档输出要求

文档至少覆盖：

- 本地离线回测器能力边界：数据准备、标准化、质量报告、loader、组合、回测、参数扫描、候选报告、W3 增强契约、偏差审计、策略扩展。
- README 应覆盖项目定位、能力范围、目录结构、快速开始、核心命令、数据边界、典型工作流、验证状态和风险提示。
- `docs/USER-MANUAL.md` 应覆盖面向用户的完整操作手册：环境准备、配置、数据准备、运行回测、参数扫描、候选报告、质量报告、日志诊断、故障排查、风险与限制。
- Python/uv 运行口径：命令示例必须使用 `uv run --python 3.11`，不得改写为裸 `pip` 或系统 Python。
- 数据边界：不得声称仓库内包含真实行情数据；示例只能使用 fixture、临时目录或用户自备本地数据。
- W3 增强：`UNRESOLVED` source/interface 代表真实数据源尚未确认，启用前必须替换 exact source/interface 并重新回归。
- 日志契约：最小 CLI 诊断日志字段包括 `event_name`、`run_id`、`module`、`story_id`、`status`、`params_summary`、`elapsed_seconds`，错误路径包含 `structured_error`。
- 报告与 CSV 安全：自由文本字段存在公式注入防护，文档示例不得绕过该约束。
- 验证证据索引：链接到 `process/VERIFICATION-REPORT.md`、`process/TEST-STRATEGY.md` 和 F-004 回归 handoff。
- 遗留风险：以 ADVISORY 表述 W3 真实数据源启用、`VALIDATION-ENV.yaml` 历史元数据和 git worktree 审计限制。

## 5. 禁止事项

- 不要生成安装脚本。
- 不要写入 `delivery/**`。
- 不要生成或引用真实生产行情样本。
- 不要把 `UNRESOLVED` 风险描述为已接入真实 PIT / 交易状态 / 涨跌停 / 事件数据。
- 不要把历史 FAIL 写成当前状态；应说明已由后续回归 PASS 覆盖。
- 不要修改业务源码、测试源码、Story LLD、检查点文件或安装脚本。

## 6. 复用键与关闭条件

复用键：

- role: `meta-doc`
- workflow_id: `local_backtest`
- change_id: null
- story_id: null
- wave_id: null

关闭条件：

- `README.md` 与 `docs/USER-MANUAL.md` 已输出。
- 文档中不包含 BLOCKING 误述。
- 已把文档路径回写给 meta-po，由 meta-po 组织后置 QA 复核和 CP8。
