---
handoff_id: "META-SE-CR025-HLD-ADR-2026-06-01"
from_agent: "meta-po"
to_agent: "meta-se"
workflow_id: "local_backtest-cr025"
change_id: "CR-025"
phase: "solution-design"
created_at: "2026-06-01T21:43:54+08:00"
status: "completed-closed"
dispatch:
  required: true
  semantic: "stage-dispatch"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-se"
  agent_path: ".agents/agents/meta-se.md"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e8373-266b-7212-a2a9-76c74a2410f5"
  agent_name: "se-chu"
  thread_id: "019e8373-266b-7212-a2a9-76c74a2410f5"
  spawned_at: "2026-06-01T21:43:54+08:00"
  resumed_at: ""
  completed_at: "2026-06-01T22:10:17+08:00"
  evidence: "spawn_agent returned agent_id=019e8373-266b-7212-a2a9-76c74a2410f5 nickname=se-chu; wait_agent completed; close_agent called. meta-se wrote HLD §34, ADR-074..077, CP3 discussion/checkpoint, CP3 auto precheck PASS and CP3 review draft with Backtrader local project analysis."
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-se"
  workflow_id: "local_backtest-cr025"
  change_id: "CR-025"
  story_id: "CR025-HLD-ADR"
  wave_id: "CR025-CP3"
---

# META-SE CR-025 HLD / ADR 交接

## 完成回执

| 字段 | 内容 |
|---|---|
| 完成状态 | `completed-closed` |
| 完成时间 | `2026-06-01T22:10:17+08:00` |
| 子 agent | `se-chu` / `019e8373-266b-7212-a2a9-76c74a2410f5` |
| 关闭证据 | `multi_agent_v1.wait_agent` 返回 completed；`multi_agent_v1.close_agent` 已调用。 |
| 产出 | `process/HLD.md` §34、`process/ARCHITECTURE-DECISION.md` ADR-074..077、`process/HLD-QMT-TRADING.md` §18、`process/discussions/CP3-CR025-HLD-DISCUSSION-LOG.md`、`process/checks/CP3-CR025-DISCUSSION-CHECKPOINT.json`、`process/checks/CP3-CR025-HLD-CONSISTENCY.md`、`checkpoints/CP3-CR025-HLD-REVIEW.md`。 |
| 自动预检 | `process/checks/CP3-CR025-HLD-CONSISTENCY.md` status=`PASS`，阻断项 0。 |
| 边界 | 未运行 Backtrader，未新增依赖，未复制 / 移植 GPLv3 源码，未触发 broker / QMT / provider / lake / publish / simulation / live，未读取凭据。 |

## 任务

请以 `meta-se` 身份执行 CR-025 的 CP3 solution-design 阶段，产出可供 meta-po 发起 CP3 人工审查的 HLD / ADR / Story Plan 设计输入。

本轮只允许设计、分析、检查点和计划产物，不允许实现代码、修改依赖、复制 / 移植 Backtrader 源码、启动服务、运行 Backtrader、调用真实 broker / QMT / MiniQMT / XtQuant、读取凭据、真实 provider fetch、写真实 lake、publish、写 broker lake 或执行 simulation / live run。

## CP2 结论

用户已在 2026-06-01 批准 CR-025 进入 CP3/HLD，并追加硬性要求：

> meta-se 必须充分分析本地 Backtrader 项目 `/home/hyde/download/backtrader`，对比哪些模块可以借鉴或者移植到本项目，哪些模块移植也需要在 HLD 中有记录。

meta-po 对该要求的门控解释：

- 允许 CP3/HLD 做模块级借鉴 / 适配 / 源码级移植候选 / 禁止移植分析。
- 不授权 CP3 或 CP5 前实施任何源码级移植。
- 若 HLD 推荐任何源码级移植，必须形成 CP3 决策项，记录 GPLv3 / copyleft 影响、维护成本、回归范围、替代方案、切换条件和 CP5 实现授权条件。
- 默认优先借鉴设计和接口适配，不默认复制源码。

## 必读输入

| 文件 / 路径 | 用途 |
|---|---|
| `AGENTS.md` | Meta Flow 阶段、检查点、子 agent 调度、人工门禁和设计评审规则 |
| `process/STATE.md` | 当前阶段、active_change、CP2 approved 状态、禁止真实操作边界 |
| `process/changes/CR-025-BACKTRADER-OPTIONAL-EXECUTION-BACKEND-HARDENING-2026-05-31.md` | CR-025 影响分析、文档处理决策、执行链路与 LLD 批次门禁 |
| `process/USE-CASES.md` | UC-19、SM-33 至 SM-41、TS-025-01 至 TS-025-11 |
| `process/REQUIREMENTS.md` | REQ-161 至 REQ-173、RA-057 至 RA-066 |
| `process/CLARIFICATION-LOG.md` | Q-045 至 Q-051、CP2 用户批准和 Backtrader 分析要求 |
| `checkpoints/CP2-CR025-REQUIREMENTS-BASELINE.md` | CP2 approved 结果和 DQ-CP2-CR025-01 至 DQ-CP2-CR025-04 |
| `process/checks/CP1-CR025-USE-CASE-COMPLETENESS.md` | CP1 PASS 证据 |
| `process/checks/CP2-CR025-REQUIREMENTS-BASELINE.md` | CP2 自动预检 PASS 证据 |
| `process/discussions/CP2-CR025-SCENARIO-DISCUSSION-LOG.md` | Scenario Gray Areas 与用户纠偏记录 |
| `process/checks/CP2-CR025-DISCUSSION-CHECKPOINT.json` | CP2 discussion 恢复点 |
| `/home/hyde/download/backtrader` | Backtrader 本地项目根，必须分析 |
| `/home/hyde/download/backtrader/LICENSE` | Backtrader license，当前本地文件显示为 GNU GPL v3 |
| `process/HLD.md` | 现有 HLD，按增量方式追加 CR-025，不重写旧基线 |
| `process/HLD-QMT-TRADING.md` | 既有 QMT companion HLD，必要时只同步 order intent 接口边界 |
| `process/ARCHITECTURE-DECISION.md` | 现有 ADR，按增量方式追加 CR-025 ADR |

## 必须处理的 Architecture Gray Areas

| ID | 问题 | 当前 CP2 结论 / 约束 |
|---|---|---|
| AGA-CR025-01 | Backtrader 在生产级 research-to-execution 路线中是 optional semantic reference、adapter、还是主路径迁移候选？ | 默认主路径仍为 lightweight engine；Backtrader 只作为显式可选 reference，主路径迁移不作为推荐默认。 |
| AGA-CR025-02 | `/home/hyde/download/backtrader` 中哪些模块可借鉴、可适配、可移植候选、必须排除？ | 必须形成模块对比表；源码级移植不自动授权。 |
| AGA-CR025-03 | GPLv3 license 对源码级移植、复制、裁剪、改写和分发有什么架构影响？ | HLD 必须记录 license 风险和默认治理策略；默认优先 reference-only / clean-room design adaptation。 |
| AGA-CR025-04 | lightweight baseline、Backtrader semantic reference 与 QMT order intent 如何对齐字段和执行语义？ | CP3 必须冻结 semantic diff schema、clean feed gate、target portfolio / order intent draft 字段。 |
| AGA-CR025-05 | CR-025 与 CR-020 gateway health 的顺序和接口边界如何表达？ | CR-025 CP3 可为 CR-020 提供 order intent draft；不授权 QMT gateway、simulation 或 live。 |

## Backtrader 分析最低范围

请至少扫描并归类以下模块族。不要粘贴大段源码；只做结构、职责、设计取舍和风险摘要。

| 模块族 | 需分析内容 |
|---|---|
| `cerebro.py` | 编排模型、事件循环、strategy/broker/data/analyzer 接入点；是否只借鉴编排概念 |
| `broker.py` / `brokers/` | broker 抽象、回测 broker、真实 broker store；哪些必须 exclude |
| `order.py` / `trade.py` / `position.py` | order/trade/position 状态模型与本项目 order intent / OMS 的映射 |
| `feed.py` / `feeds/` / `dataseries.py` | data feed / line 数据结构；与 clean feed / PIT / available_at 的适配边界 |
| `comminfo.py` / `sizer.py` / `sizers/` / `fillers.py` | 佣金、sizer、成交填充假设；可借鉴的抽象与不适配点 |
| `analyzer.py` / `analyzers/` | returns、drawdown、sharpe、transactions 等分析器；可参考指标输出而非复制源码 |
| `observer.py` / `observers/` | observer 模型对报告 / semantic diff 的借鉴价值 |
| `indicator.py` / `indicators/` | indicator 体系与本项目研究因子 / signal 的边界；避免把指标库迁移成主目标 |
| `strategy.py` / `signal.py` / `strategies/` | 策略接口与本项目策略纯函数 / target portfolio 的差异 |
| `store.py` / `stores/` | live store / 外部 broker 接入必须默认 exclude |
| `plot/` / `writer.py` | 输出、可视化和 writer 的可借鉴点与非目标 |
| `samples/` / `tests/` | 可用于理解行为的样例和测试类别；不要复制测试数据或源码 |

## 目标输出

请在完成后直接修改 / 新增必要文件，并在最终回复中列出变更文件。最低目标：

1. 增量更新 `process/HLD.md`，加入 CR-025 HLD 章节，覆盖：
   - production-grade research-to-execution 三条主线。
   - lightweight baseline、Backtrader optional semantic reference、QMT order intent 的关系。
   - clean feed gate。
   - semantic diff schema。
   - target portfolio / order intent draft schema。
   - `/home/hyde/download/backtrader` 模块级分析矩阵。
   - GPLv3 / 源码级移植风险与治理策略。
   - 明确推荐方案、备选方案、切换条件和不授权边界。
2. 增量更新 `process/ARCHITECTURE-DECISION.md`，加入 CR-025 ADR，至少覆盖：
   - Backtrader 默认定位：optional semantic reference，不替代 lightweight 主路径。
   - Backtrader 模块处理策略：reference-only / adapt-interface / migration-candidate / exclude。
   - 源码级移植治理：license / CP3 decision / CP5 authorization。
   - order intent 与 QMT 路线边界。
3. 如需要同步 QMT 接口边界，可增量更新 `process/HLD-QMT-TRADING.md`，但只能同步 order intent draft 消费边界，不得启动 CR-020 或授权真实 QMT。
4. 生成或更新 CP3 discussion log / checkpoint：
   - `process/discussions/CP3-CR025-HLD-DISCUSSION-LOG.md`
   - `process/checks/CP3-CR025-DISCUSSION-CHECKPOINT.json`
5. 生成 CP3 自动预检：
   - `process/checks/CP3-CR025-HLD-CONSISTENCY.md`
6. 如 HLD 已足够收敛，可生成 CP3 人工审查稿草案：
   - `checkpoints/CP3-CR025-HLD-REVIEW.md`
   - 正式发起和回填仍由 meta-po 完成。

## 验收要求

- CP3 自动预检必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables。
- CP3 Decision Brief 必须包含推荐方案、备选方案、优劣、影响 / 风险、回退 / 切换条件。
- HLD / ADR 必须遵守设计评审规则：内部一致、目标量化、集成契约显式化、失败路径、回退决策可操作、遗留问题状态闭环、修订记录完整。
- Backtrader 模块对比表必须包含模块、职责、可借鉴点、移植可行性、license 风险、维护成本、推荐分类、验证策略、是否需要 CP3/CP5 决策。
- 不得把 GPLv3 本地源码分析写成“可以直接复制到本项目”。
- 不得进入 Story LLD 或实现。
- 不得新增依赖或修改 `pyproject.toml` / `uv.lock`。
- 不得触发真实 broker / QMT / provider / lake / publish / simulation / live。
