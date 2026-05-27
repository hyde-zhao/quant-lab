---
handoff_id: "META-QA-DOCUMENTATION-POST-DOC-RECHECK-2026-05-16"
project_id: "local_backtest"
created_at: "2026-05-16"
created_by: "meta-po"
from_agent: "meta-po"
to_agent: "meta-qa"
scope: "post-documentation QA recheck after meta-doc output"
status: "blocked-until-meta-doc-output"
priority: "RECOMMENDED"
delivery_write_allowed: false
implementation_allowed: false
data_generation_allowed: false
install_script_generation_allowed: false
dispatch:
  required: true
  mode: "handoff-only"
  platform: "codex"
  agent_role: "meta-qa"
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
  note: "本文件仅为后置 QA 复核交接输入；不表示 meta-qa 已执行。必须等待 meta-doc 文档输出后再拉起。"
---

# Meta-qa Post-documentation Recheck Handoff

## 1. 任务目标

在 meta-doc 输出 README / USER-MANUAL 或用户确认的文档草案后，由 `meta-qa` 复核文档是否与当前验证结论、风险状态和交付边界一致。

## 2. 前置条件

- meta-doc 已输出文档，并将路径回写给 meta-po。
- 文档输出路径已由用户确认：`README.md` 与 `docs/USER-MANUAL.md`。
- 本 handoff 不授权 meta-qa 修改业务源码、测试源码、`delivery/**`、README、USER-MANUAL 或安装脚本。

## 3. 最小必要上下文

meta-qa 应读取：

- meta-doc 实际输出的文档路径：`README.md` 与 `docs/USER-MANUAL.md`。
- `process/DOCUMENTATION-READINESS-ROUTING-2026-05-16.md`
- `process/STATE.md`
- `process/STORY-STATUS.md`
- `process/VERIFICATION-REPORT.md`
- `process/TEST-STRATEGY.md`
- `process/handoffs/META-QA-DOCUMENTATION-READINESS-2026-05-16.md`
- `process/handoffs/META-QA-REGRESSION-F004-LOGGING-2026-05-16.md`

## 4. 复核重点

| 检查项 | 期望 |
|---|---|
| 当前质量结论 | 文档应写为 STORY-001..013 verified，F-004 CLOSED / REGRESSION_PASS |
| 历史 FAIL | 只能作为审计上下文，且必须说明已由后续 PASS / CLOSED 覆盖 |
| W3 `UNRESOLVED` | 必须写为真实数据启用前 ADVISORY / hard gate，不得写成已接入真实数据源 |
| 数据边界 | 不得声称仓库包含真实生产行情样本 |
| 命令口径 | Python 示例必须使用 `uv run --python 3.11` |
| 交付边界 | 不得新增安装脚本或未经授权的 `delivery/**` 内容 |
| CSV / 报告安全 | 不得绕过自由文本公式注入防护 |

## 5. 输出要求

meta-qa 输出复核结论到 `process/VERIFICATION-REPORT.md` 或 meta-po 指定的文档复核记录，结论分为：

- PASS：文档可进入 CP8 自动预检。
- REQUIRED：存在必须修订的文档误述，路由回 meta-doc。
- BLOCKING：存在交付边界、真实数据、安装脚本或当前质量结论的严重误述，阻断 CP8。

## 6. 复用键与关闭条件

复用键：

- role: `meta-qa`
- workflow_id: `local_backtest`
- change_id: null
- story_id: "documentation"
- wave_id: null

关闭条件：

- 已完成文档复核并写明 PASS / REQUIRED / BLOCKING。
- 若存在 REQUIRED/BLOCKING，已列出目标文档、章节和修订要求。
