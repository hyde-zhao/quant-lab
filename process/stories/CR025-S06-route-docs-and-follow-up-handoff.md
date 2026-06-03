---
story_id: "CR025-S06-route-docs-and-follow-up-handoff"
title: "QMT 后续路线衔接与用户文档边界"
story_slug: "route-docs-and-follow-up-handoff"
status: "verified"
priority: "P1"
wave: "CR025-W4-SAFETY-VERIFICATION-DOCS"
depends_on:
  - "CR025-S01-clean-feed-gate-backend-selector"
  - "CR025-S02-semantic-diff-schema-artifact"
  - "CR025-S03-order-intent-draft-qmt-boundary"
  - "CR025-S04-backtrader-module-reference-no-copy-guardrail"
  - "CR019-S09-deferred-capability-register"
dependency_type:
  - upstream: "CR025-S01-clean-feed-gate-backend-selector"
    type: "documentation-merge"
  - upstream: "CR025-S02-semantic-diff-schema-artifact"
    type: "documentation-merge"
  - upstream: "CR025-S03-order-intent-draft-qmt-boundary"
    type: "documentation-merge"
  - upstream: "CR025-S04-backtrader-module-reference-no-copy-guardrail"
    type: "documentation-merge"
  - upstream: "CR019-S09-deferred-capability-register"
    type: "follow-up-route-contract"
cp5_batch: "CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "docs/CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md"
  shared:
    - "README.md"
    - "docs/USER-MANUAL.md"
  merge_owner: "CR025-S06-route-docs-and-follow-up-handoff"
  forbidden:
    - "runtime authorization"
    - "real credential examples"
    - "run instructions suggesting true auth"
    - "gateway service start"
    - "dependency install"
    - "Backtrader run as default"
    - "Qlib / Alphalens / vnpy.alpha integration in CR-025"
    - "claim CR-025 implements multifactor research framework"
    - "simulation/live authorization"
    - "publish authorization"
lld_gate:
  required_inputs:
    - "process/HLD.md#34"
    - "process/HLD-QMT-TRADING.md#18"
    - "process/ARCHITECTURE-DECISION.md#ADR-074..ADR-078"
    - "process/stories/CR025-S06-route-docs-and-follow-up-handoff.md"
  status: "confirmed"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  dependency_change_allowed: false
  backtrader_run_allowed: false
  credential_read_allowed: false
  qmt_operation_allowed: false
  cp6_status: "PASS"
  cp6_result: "process/checks/CP6-CR025-S06-route-docs-and-follow-up-handoff-CODING-DONE.md"
  cp6_blocker_fix_status: "PASS"
  cp6_blocker_fix_result: "process/checks/CP6-CR025-S06-CP7-BLOCKER-FIX-CODING-DONE.md"
  cp7_status: "PASS"
  cp7_first_result: "process/checks/CP7-CR025-S06-route-docs-and-follow-up-handoff-VERIFICATION-DONE.md"
  cp7_result: "process/checks/CP7-CR025-S06-route-docs-and-follow-up-handoff-REVERIFY-DONE.md"
task_count: 4
created_at: "2026-06-01T22:42:19+08:00"
updated_at: "2026-06-02T22:26:23+08:00"
change_id: "CR-025"
---

# CR025-S06：QMT 后续路线衔接与用户文档边界

## 目标

把 CR-025 的 semantic diff、order_intent_draft_v1、Backtrader reference/no-copy、optional runtime boundary、no-real-operation safety、CR-020..CR-024 后续路线和多因子研究后续 CR 边界写入文档 / follow-up handoff。文档不得被解释为真实交易、gateway 启动、dependency install、Backtrader run、simulation/live、publish 授权或多因子研究闭环实现授权。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-19、SM-40、SM-41、TS-025-09、TS-025-10、TS-025-11 |
| 需求 | REQ-166、REQ-170、REQ-171、REQ-172、REQ-173 |
| HLD | `process/HLD.md` §34；`process/HLD-QMT-TRADING.md` §18 |
| ADR | ADR-074、ADR-075、ADR-076、ADR-077、ADR-078 |

## 开发上下文（dev_context）

**背景说明**：CR-025 是 research execution semantic alignment，不是 QMT 实盘入口，也不是多因子研究主框架建设 CR。后续 CR-020..CR-024 只能把 CR-025 的 artifact 和 draft 作为 later-gated 输入，不能继承任何运行授权。FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪和策略准入包需要另起后续 CR，参考 Qlib / Alphalens / vnpy.alpha。

**输入文件**：CR025-S01..S04 Story 合同、CR019-S09 deferred capability register、CR-025 HLD / QMT companion / ADR、本 Story 卡片。

**输出文件**：`docs/CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md`，共享 `README.md`、`docs/USER-MANUAL.md`。

**接口约定**：

| 文档对象 | 必须表达 |
|---|---|
| semantic diff | baseline / reference 双轨、unavailable、limitations、非 truth / 非 simulation-ready |
| order intent draft | `order_intent_draft_v1`、not order、not authorization、later-gated consumer |
| Backtrader boundary | optional dependency、lazy import、no-copy、migration_candidate=[] |
| QMT route | CR-020..CR-024 需独立 CR / CP / per-run authorization |
| multifactor research route | FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪和策略准入包另起后续 CR；参考 Qlib / Alphalens / vnpy.alpha；不继承 CR-025 授权 |
| no-real-operation | 不授权真实 broker / QMT / provider / lake / publish / simulation / live / credential |

**设计约束**：不得新增真实运行说明、真实凭据示例、gateway 启动步骤、dependency install 默认路径或 publish 操作步骤；不得引入 Qlib / Alphalens / vnpy.alpha 依赖或 runner；若必须提到后续路线，必须标注 later-gated / not-authorized / follow-up CR。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR025-S01 | documentation-merge | clean feed / selector 合同冻结 | 文档不修改 selector 行为 | 记录 optional runtime boundary |
| CR025-S02 | documentation-merge | semantic diff 合同冻结 | 文档不生成真实 report | 记录 diff artifact 语义 |
| CR025-S03 | documentation-merge | order intent draft 合同冻结 | 文档不启动 QMT | 记录 QMT handoff 边界 |
| CR025-S04 | documentation-merge | no-copy guardrail 冻结 | 文档不复制源码 | 记录 GPLv3 no-copy |
| CR019-S09 | follow-up-route-contract | deferred register 可引用 | 不扩展 CR019 已关闭范围 | 连接 Backtrader / QMT / 多因子研究后续路线 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `docs/CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md` | 当前 Story 独占 |
| shared | `README.md`、`docs/USER-MANUAL.md` | 当前 Story 为 CR-025 文档 merge owner；实现需等待 CP5 |
| forbidden | runtime authorization、真实凭据示例、gateway service start、dependency install、Backtrader run as default、Qlib / Alphalens / vnpy.alpha integration in CR-025、claim CR-025 implements multifactor research framework、simulation/live authorization、publish authorization | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR025-S06-T1 | 设计 | `docs/CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md` | 定义 CR-025 用户可读架构、artifact、draft、no-copy 和 no-real-operation 边界 |
| CR025-S06-T2 | 设计 | `README.md` | 设计最小入口说明，明确 CR-025 不授权真实运行 |
| CR025-S06-T3 | 设计 | `docs/USER-MANUAL.md` | 设计用户手册增量边界与故障说明 |
| CR025-S06-T4 | 约束 | follow-up handoff | 明确 CR-020..CR-024 独立授权和 CP 门控，并把多因子研究闭环登记为后续 CR 候选 |

## 验证上下文（validation_context）

**验证入口**：后续 LLD 可建议文档静态测试或 `uv run --python 3.11 pytest -q tests/test_cr025_schema_contracts.py` 中的文档边界用例，但本阶段不执行。

**验证方式**：文档静态扫描、语义禁止项扫描、Story 边界覆盖检查。

**依赖环境**：本地文档；不得读取凭据、不得启动服务、不得运行 Backtrader、不得 publish。

**关键验证场景**：

| 场景 | 预期 |
|---|---|
| 文档覆盖 CP3 DQ | DQ-CP3-CR025-01..06 均可追溯 |
| 文档覆盖 Story 边界 | CR025-S01..S06 均可追溯 |
| CR-020..CR-024 路线 | 明确 later-gated，不继承 CR-025 授权 |
| 多因子研究后续路线 | 明确 FactorSpec / IC / RankIC / 分层收益 / 多因子组合 / 实验追踪 / 策略准入包另起 CR，参考 Qlib / Alphalens / vnpy.alpha |
| forbidden authorization scan | “CR-025 verified 授权真实操作”语义匹配为 0 |

## 量化验收标准（acceptance_criteria）

- [x] 文档覆盖 6 个 CP3 DQ 和 6 个 CR-025 Story 边界。
- [x] CR-020..CR-024 不继承 CR-025 授权声明至少出现 1 处且位置可追溯。
- [x] 多因子研究闭环另起后续 CR 的声明至少出现 1 处，且包含 Qlib / Alphalens / vnpy.alpha 作为参考方向。
- [x] no-real-operation 表覆盖 LLD、实现、依赖变更、Backtrader run、Backtrader source copy、broker、QMT / MiniQMT / XtQuant、provider、lake、broker lake、publish、simulation/live、credential read。
- [x] “CR-025 verified 授权真实操作”语义匹配次数为 0。

## 阻塞说明

本 Story 已通过 CR-025 CP5 全量 LLD 批次确认，且 S01、S02、S03、S04、S05 与 CR019-S09 合同均已满足。S05 已 CP7 PASS 并 verified，W4 串行阻塞解除；meta-po 已调度 `meta-dev/dev-kong` 进入受控离线文档实现。文档在任何阶段都不能作为真实运行授权，也不能作为多因子研究闭环实现授权；多因子研究闭环已登记为 CR-030 候选。

## CP6 编码完成说明

本 Story 已完成受控离线文档实现，并写入 `process/checks/CP6-CR025-S06-route-docs-and-follow-up-handoff-CODING-DONE.md`，CP6 结论为 `PASS`。

| 项 | 结论 | 证据 |
|---|---|---|
| 专题文档 | PASS | `docs/CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md` |
| README 入口 | PASS | `README.md` CR-025 section |
| USER-MANUAL 边界 | PASS | `docs/USER-MANUAL.md` CR-025 section |
| Required Verification pytest | PASS | CR025 组合回归 `52 passed in 0.70s` |
| traceability scan | PASS | CR025-S01..S06、DQ-CP3-CR025-01..06、CR-020..CR-024、CR-030、多因子候选 token 均存在 |
| forbidden authorization / claim scan | PASS | 正向授权 / 正向集成模式命中 0 |
| dependency diff | PASS | `git diff --name-only -- pyproject.toml uv.lock` 无输出 |

真实操作 / 禁止项计数均为 `0`；本轮未修改源码、测试、依赖、STATE、STORY-STATUS、DEVELOPMENT-PLAN、CR index、HLD、ADR 或其他 Story，未读取外部 Backtrader 源码树或凭据，未运行 Backtrader、QMT / MiniQMT / XtQuant、provider、lake、publish、simulation/live，也未实现 FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪、策略准入包或 Qlib / Alphalens / vectorbt / vnpy.alpha 集成。

## CP7 Blocker Fix 说明

针对首轮 CP7 阻断项 `CR025-S06-CP7-F01`，本回修仅将 CR-030 候选参考对象表中的 `LEAN` 精确命名为 `QuantConnect LEAN`，用于满足 bounded static trace scan 的精确 token 要求。该命名仍只表示后续正式 CR 前的候选参考对象，不表示 CR-025 已集成、已实现、已授权运行或默认采用 QuantConnect LEAN。

## CP7 复验完成说明

`meta-qa/qa-wei` 已完成 CP7 复验并写入 `process/checks/CP7-CR025-S06-route-docs-and-follow-up-handoff-REVERIFY-DONE.md`，结论为 `PASS`。首轮 CP7 FAIL 文件保留为失败证据，复验文件关闭 `CR025-S06-CP7-F01`。

| 项 | 结论 | 证据 |
|---|---|---|
| CR025 组合回归 | PASS | `52 passed in 0.81s` |
| bounded static trace scan | PASS | `TRACE_TOTAL present=35 missing=0` |
| `QuantConnect LEAN` 精确 token | PASS | 限定文件集中 count=`28` |
| forbidden claim review | PASS | 正向 CR-025 授权声明计数 `0` |
| credential / private-path review | PASS | 凭据值、密钥形态、真实私有路径值均为 `0` |
| 禁止操作计数 | PASS | 依赖变更、Backtrader runtime、外部源码读取 / 扫描 / 复制、QMT / broker / provider / lake / publish / simulation / live / 凭据读取 / 多因子主框架实现均为 `0` |
