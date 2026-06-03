---
handoff_id: "META-SE-CR025-MULTIFACTOR-POSITIONING-REVISION-2026-06-02"
from_agent: "meta-po"
to_agent: "meta-se"
status: "completed"
created_at: "2026-06-02T06:36:59+08:00"
change_id: "CR-025"
task_type: "hld-story-positioning-revision"
dispatch:
  required: true
  semantic: "stage-dispatch"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-se"
  agent_path: ".agents/agents/meta-se.md"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e8556-179f-7473-ad0c-cf1ce64981d5"
  agent_name: "se-jiang"
  thread_id: "019e8556-179f-7473-ad0c-cf1ce64981d5"
  spawned_at: "2026-06-02T06:36:59+08:00"
  resumed_at: ""
  completed_at: "2026-06-02T06:51:11+08:00"
  evidence: "spawn_agent returned agent_id=019e8556-179f-7473-ad0c-cf1ce64981d5 nickname=se-jiang for CR-025 HLD / Story / Plan multifactor positioning revision; wait_agent completed; close_agent called. meta-se revised HLD/ADR/STORY-BACKLOG/DEVELOPMENT-PLAN/S02/S04/S06 Story cards, kept 6 Story / 4 Wave / 1 LLD batch unchanged, and recommended refreshing S02/S04/S06 LLD plus S05 safety LLD before CP5 relaunch."
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-se"
  workflow_id: "local_backtest"
  change_id: "CR-025"
  story_id: "CR025-HLD-STORY-MULTIFACTOR-POSITIONING-REVISION"
  wave_id: "CR025-CP5-REVISION"
---

# Handoff: CR-025 多因子研究定位下的 HLD / Story 修订

## 1. 背景

用户在 CR-025 CP5 人工确认前补充：本系统主要做多因子策略研究和回测，并询问 Backtrader 是否仍有借鉴必要。meta-po 判断当前 CR-025 不需要推倒重做，但需要在 CP5 前做定位修订：

- Backtrader 不作为多因子研究主框架。
- Backtrader 仅作为 lightweight execution engine 的执行语义参考，覆盖 feed / broker / order / position / commission / slippage / analyzer 等执行层语义。
- 多因子研究主线应另起后续 CR，参考 Qlib / Alphalens / vnpy.alpha 等研究型框架。
- CR-025 继续收敛为 research-to-execution 的执行语义对齐、semantic diff、`order_intent_draft_v1` 和 no-copy / no-real-operation 边界。

## 2. 目标 Agent 任务

请以 `meta-se` 身份只修订 CR-025 的 HLD / ADR / Story / Plan 设计产物，不进入 LLD、代码实现、依赖变更或真实运行。

必须完成：

1. 修订 `process/HLD.md` 的 CR-025 §34，追加 post-CP3 / CP5 前定位澄清：
   - 本项目核心是多因子研究与回测。
   - 多因子研究主参考不是 Backtrader，而是后续研究路线参考 Qlib / Alphalens / vnpy.alpha。
   - Backtrader 只保留为执行语义参考，不负责 FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪或策略准入包。
   - CR-025 不扩展为多因子研究流水线建设；该方向进入后续 CR 候选。
2. 如需要，修订 `process/ARCHITECTURE-DECISION.md` 中 CR-025 相关 ADR，使 ADR-074..077 或新增 ADR 明确上述边界。
3. 修订 `process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml` 和必要的 CR025 Story 卡片：
   - 不新增 CR025 Story。
   - 不改变 6 Story / 4 Wave / 1 LLD batch 结构，除非发现严重一致性问题。
   - 在 S02 / S04 / S06 的 Story 文案中补充“多因子研究能力另起 CR，不属于 CR-025”。
4. 如 Story / Plan 文案变化会影响 CP5 Decision Brief，请在输出中列明需要 meta-po 后续同步的 CP5 决策项，不要直接发起 CP5。

## 3. 必读输入

| 路径 | 用途 |
|---|---|
| `process/STATE.md` | 当前 CR-025 状态与 CP5 pending 决策 |
| `process/changes/CR-025-BACKTRADER-OPTIONAL-EXECUTION-BACKEND-HARDENING-2026-05-31.md` | 活跃 CR 边界 |
| `process/HLD.md` §34 | CR-025 HLD 主体 |
| `process/ARCHITECTURE-DECISION.md` | CR-025 ADR |
| `process/STORY-BACKLOG.md` | Story 汇总 |
| `process/DEVELOPMENT-PLAN.yaml` | Wave / LLD 批次 / no-real-operation 边界 |
| `process/stories/CR025-S02-semantic-diff-schema-artifact.md` | S02 Story 卡片 |
| `process/stories/CR025-S04-backtrader-module-reference-no-copy-guardrail.md` | S04 Story 卡片 |
| `process/stories/CR025-S06-route-docs-and-follow-up-handoff.md` | S06 Story 卡片 |
| `checkpoints/CP5-CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT-BATCH-A-LLD-BATCH.md` | CP5 Decision Brief 当前稿 |

## 4. 禁止事项

- 不得修改任何 `*-LLD.md`。
- 不得修改代码、测试、`pyproject.toml`、`uv.lock` 或 `.env`。
- 不得运行 Backtrader、安装依赖、复制 / 裁剪 / 改写 / 源码级移植 Backtrader GPLv3 源码。
- 不得触发真实 broker、QMT / MiniQMT / XtQuant、gateway、provider fetch、lake write、broker lake、publish、simulation、live 或凭据读取。
- 不得将 CR-025 改成 Qlib / Alphalens / vnpy.alpha 实现 CR；只能登记为后续路线。

## 5. 期望输出

1. 直接修改上述 HLD / ADR / Story / Plan 文件。
2. 最终回复列出：
   - 修改文件清单。
   - 是否保持 6 Story / 4 Wave / 1 LLD batch 不变。
   - 是否需要 meta-dev 修订哪些 LLD。
   - 是否需要 meta-po 更新 CP5 Decision Brief / launch message。
3. 不得把本任务标记为 CP5 approved；完成后交回 meta-po。
