---
handoff_id: "META-DEV-CR025-LLD-MULTIFACTOR-POSITIONING-REVISION-2026-06-02"
from_agent: "meta-po"
to_agent: "meta-dev"
status: "completed"
created_at: "2026-06-02T06:51:43+08:00"
change_id: "CR-025"
task_type: "lld-positioning-revision"
batch_id: "CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT-BATCH-A"
target_story_ids:
  - "CR025-S02-semantic-diff-schema-artifact"
  - "CR025-S04-backtrader-module-reference-no-copy-guardrail"
  - "CR025-S05-no-real-operation-safety-verification"
  - "CR025-S06-route-docs-and-follow-up-handoff"
dispatch:
  required: true
  semantic: "stage-dispatch"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".agents/agents/meta-dev.md"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e8563-8539-7563-92cf-f0fdd6f46806"
  agent_name: "dev-he"
  thread_id: "019e8563-8539-7563-92cf-f0fdd6f46806"
  spawned_at: "2026-06-02T06:51:43+08:00"
  resumed_at: ""
  completed_at: "2026-06-02T07:02:32+08:00"
  evidence: "spawn_agent returned agent_id=019e8563-8539-7563-92cf-f0fdd6f46806 nickname=dev-he for CR-025 S02/S04/S05/S06 LLD and CP5 precheck positioning revision; wait_agent completed; close_agent called. meta-dev refreshed four LLD files and four CP5 implementability prechecks; S02/S04/S05/S06 remain PASS with blockers=0, waived=0, forbidden operation counts=0."
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-dev"
  workflow_id: "local_backtest"
  change_id: "CR-025"
  story_id: "CR025-LLD-MULTIFACTOR-POSITIONING-REVISION"
  wave_id: "CR025-CP5-REVISION"
---

# Handoff: CR-025 多因子研究定位下 LLD / CP5 自动预检修订

## 1. 背景

`meta-se` 已完成 CR-025 CP5 前 HLD / ADR / Story / Plan 定位修订，核心结论：

- 系统核心定位是多因子策略研究和回测。
- Backtrader 不作为多因子研究主框架，只作为 lightweight execution engine 的 execution semantic reference。
- FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪、策略准入包，以及 Qlib / Alphalens / vnpy.alpha 集成均不并入 CR-025。
- 多因子研究闭环应作为后续 CR 独立推进。
- CR-025 继续保持 6 Story / 4 Wave / 1 LLD batch，不新增 Story，不拆批。

## 2. 目标 Agent 任务

请以 `meta-dev` 身份只修订下列 LLD 与 CP5 自动预检，不进入代码实现。

### 必须修订的 LLD

| Story | LLD 路径 | 修订要求 |
|---|---|---|
| S02 | `process/stories/CR025-S02-semantic-diff-schema-artifact-LLD.md` | 加入 ADR-078；明确 semantic diff 不是 factor tear sheet / IC report / strategy admission package；不新增 FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪字段。 |
| S04 | `process/stories/CR025-S04-backtrader-module-reference-no-copy-guardrail-LLD.md` | 加入 ADR-078；明确 Backtrader 模块矩阵只用于 feed / broker / order / position / commission / slippage / analyzer 等执行语义参考，不作为多因子研究框架评估或迁移依据。 |
| S06 | `process/stories/CR025-S06-route-docs-and-follow-up-handoff-LLD.md` | 加入后续多因子研究 CR 边界；文档需说明 FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪和策略准入包另起 CR，参考 Qlib / Alphalens / vnpy.alpha。 |

### 建议轻量修订的 LLD

| Story | LLD 路径 | 修订要求 |
|---|---|---|
| S05 | `process/stories/CR025-S05-no-real-operation-safety-verification-LLD.md` | 补充 forbidden-claim / scope scan：CR-025 文档、报告或 artifact 声称“已实现多因子研究主框架”或授权 FactorSpec / IC / RankIC / 多因子组合等能力的匹配次数必须为 0。 |

### 必须刷新对应 CP5 自动预检

- `process/checks/CP5-CR025-S02-semantic-diff-schema-artifact-LLD-IMPLEMENTABILITY.md`
- `process/checks/CP5-CR025-S04-backtrader-module-reference-no-copy-guardrail-LLD-IMPLEMENTABILITY.md`
- `process/checks/CP5-CR025-S05-no-real-operation-safety-verification-LLD-IMPLEMENTABILITY.md`
- `process/checks/CP5-CR025-S06-route-docs-and-follow-up-handoff-LLD-IMPLEMENTABILITY.md`

预期结论仍为 PASS，除非发现新的阻断项。若发现阻断项，不得自行假设通过，必须写清 blocking finding 并交回 meta-po。

## 3. 必读输入

| 路径 | 用途 |
|---|---|
| `process/HLD.md` §34 | ADR-078 对应 HLD 落点 |
| `process/ARCHITECTURE-DECISION.md` ADR-074..078 | 新增多因子研究边界 |
| `process/STORY-BACKLOG.md` CR025-S02/S04/S06、CR25-SP-Q6 | Story 级边界 |
| `process/DEVELOPMENT-PLAN.yaml` CR025 policy / multifactor boundary | Wave / LLD batch / no-real-operation 输入 |
| `process/stories/CR025-S02-semantic-diff-schema-artifact.md` | S02 Story 修订后输入 |
| `process/stories/CR025-S04-backtrader-module-reference-no-copy-guardrail.md` | S04 Story 修订后输入 |
| `process/stories/CR025-S05-no-real-operation-safety-verification.md` | S05 Story 输入 |
| `process/stories/CR025-S06-route-docs-and-follow-up-handoff.md` | S06 Story 修订后输入 |
| `process/handoffs/META-SE-CR025-MULTIFACTOR-POSITIONING-REVISION-2026-06-02.md` | meta-se 调度与完成摘要 |

## 4. 禁止事项

- 不得修改 `process/HLD.md`、`process/ARCHITECTURE-DECISION.md`、`process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml` 或 Story 卡片；这些由 meta-se 已处理。
- 不得修改 S01 / S03 LLD，除非只读检查发现它们显式越界，并先在最终回复中报告。
- 不得修改源码、测试、README、USER-MANUAL、`pyproject.toml`、`uv.lock`、`.env`。
- 不得运行 Backtrader、安装依赖、复制 / 裁剪 / 改写 / 源码级移植 Backtrader GPLv3 源码。
- 不得触发真实 broker、QMT / MiniQMT / XtQuant、gateway、provider fetch、lake write、broker lake、publish、simulation、live 或凭据读取。
- 不得把 CR-025 扩展成 Qlib / Alphalens / vnpy.alpha 集成或多因子研究框架实现。

## 5. 期望输出

1. 直接修改 4 份 LLD 和 4 份 CP5 自动预检。
2. 保持每份 LLD 的 14 个可见章节结构不变。
3. 最终回复列出：
   - 修改文件清单。
   - 每个 Story 的 CP5 预检结论。
   - 是否仍保持 6 Story / 4 Wave / 1 LLD batch。
   - 是否存在需要 meta-po 写入 CP5 Decision Brief 的新决策项。
4. 不得把本任务标记为 CP5 approved；完成后交回 meta-po。
