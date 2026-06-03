---
checkpoint_id: "CP5"
checkpoint_name: "CR-025 全量 LLD 批次人工确认"
type: "batch_auto_then_manual"
status: "approved"
owner: "meta-po"
created_at: "2026-06-01T23:11:56+08:00"
reviewed_by: "user"
reviewed_at: "2026-06-02T07:19:31+08:00"
auto_check_result: "6/6 PASS"
target:
  phase: "story-planning"
  change_id: "CR-025"
  batch_id: "CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT-BATCH-A"
  story_ids:
    - "CR025-S01-clean-feed-gate-backend-selector"
    - "CR025-S02-semantic-diff-schema-artifact"
    - "CR025-S03-order-intent-draft-qmt-boundary"
    - "CR025-S04-backtrader-module-reference-no-copy-guardrail"
    - "CR025-S05-no-real-operation-safety-verification"
    - "CR025-S06-route-docs-and-follow-up-handoff"
  artifacts:
    - "process/stories/CR025-S01-clean-feed-gate-backend-selector-LLD.md"
    - "process/stories/CR025-S02-semantic-diff-schema-artifact-LLD.md"
    - "process/stories/CR025-S03-order-intent-draft-qmt-boundary-LLD.md"
    - "process/stories/CR025-S04-backtrader-module-reference-no-copy-guardrail-LLD.md"
    - "process/stories/CR025-S05-no-real-operation-safety-verification-LLD.md"
    - "process/stories/CR025-S06-route-docs-and-follow-up-handoff-LLD.md"
    - "process/checks/CP5-CR025-S01-clean-feed-gate-backend-selector-LLD-IMPLEMENTABILITY.md"
    - "process/checks/CP5-CR025-S02-semantic-diff-schema-artifact-LLD-IMPLEMENTABILITY.md"
    - "process/checks/CP5-CR025-S03-order-intent-draft-qmt-boundary-LLD-IMPLEMENTABILITY.md"
    - "process/checks/CP5-CR025-S04-backtrader-module-reference-no-copy-guardrail-LLD-IMPLEMENTABILITY.md"
    - "process/checks/CP5-CR025-S05-no-real-operation-safety-verification-LLD-IMPLEMENTABILITY.md"
    - "process/checks/CP5-CR025-S06-route-docs-and-follow-up-handoff-LLD-IMPLEMENTABILITY.md"
---

# CP5 CR-025 全量 LLD 批次人工确认

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---:|---|
| `process/checks/CP4-CR025-STORY-DAG-PARALLEL-SAFETY.md` | PASS | 0 | 6 Story / 4 Wave / 1 LLD batch；DAG cycles=0；invalid references=0。 |
| `process/checks/CP5-CR025-S01-clean-feed-gate-backend-selector-LLD-IMPLEMENTABILITY.md` | PASS | 0 | clean feed gate、backend selector、lazy import / structured unavailable 可实现；禁止操作计数 0。 |
| `process/checks/CP5-CR025-S02-semantic-diff-schema-artifact-LLD-IMPLEMENTABILITY.md` | PASS | 0 | semantic diff schema / artifact 可实现；不覆盖 lightweight baseline；已按 ADR-078 明确不是 factor tear sheet / IC report / 策略准入包；禁止操作计数 0。 |
| `process/checks/CP5-CR025-S03-order-intent-draft-qmt-boundary-LLD-IMPLEMENTABILITY.md` | PASS | 0 | `order_intent_draft_v1` 可实现；draft 不是订单；不授权 QMT；禁止操作计数 0。 |
| `process/checks/CP5-CR025-S04-backtrader-module-reference-no-copy-guardrail-LLD-IMPLEMENTABILITY.md` | PASS | 0 | Backtrader module reference / no-copy guardrail 可实现；`migration_candidate=[]`；Backtrader 仅作为 execution semantic reference，不作为多因子研究框架；禁止操作计数 0。 |
| `process/checks/CP5-CR025-S05-no-real-operation-safety-verification-LLD-IMPLEMENTABILITY.md` | PASS | 0 | fixture-only safety verification 可实现；新增 ADR-078 forbidden-claim / scope scan；真实操作计数均为 0。 |
| `process/checks/CP5-CR025-S06-route-docs-and-follow-up-handoff-LLD-IMPLEMENTABILITY.md` | PASS | 0 | QMT 后续路线、文档边界和多因子研究后续 CR 边界可实现；CR-020..CR-024 不继承授权。 |

## Decision Brief

如果你回复 `approve`，表示你接受以下 5 项推荐方案；不表示授权下方“不授权项”中的任何操作。特别注意：`approve` 不表示授权或接受 CR-025 交付多因子研究主框架。

### 待人工决策清单

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣分析 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|---|
| DQ-CP5-CR025-01 | `implementation` | 是否接受 CR025-S01..S06 六份 LLD 作为后续受控离线实现输入？ | 接受 6 份 LLD 和 6 份 CP5 PASS，进入 story-execution；仅授权 LLD 指定的离线 / fixture / 静态合同实现，不授权多因子研究主框架实现。 | 1. 指定 Story 修改后重发 CP5；2. 拆分为 S01/S04/S02 先行、S03/S05/S06 后置。 | 推荐方案可保持全量契约一致；修改会延迟实现但可降低单点疑虑；拆分会增加跨 Story 版本漂移。 | 影响 engine adapter、semantic diff、order intent draft、文档和验证矩阵的实现启动条件；不会交付 FactorSpec、IC / RankIC 或策略准入包。 | 任一 LLD 边界需改时回到对应 LLD；若要拆批，回退到 CP4/CP5 批次规划；若要多因子研究闭环，另起 CR。 |
| DQ-CP5-CR025-02 | `architecture` | 是否接受 clean feed -> semantic diff -> order intent draft -> safety/docs 的 Story DAG 与 merge order？ | 接受当前 DAG：S01/S04 合同先行，S02 冻结 execution semantic diff，S03 冻结 draft，S05/S06 收敛验证与文档。 | 1. 先实现 S01/S04/S05，暂缓 S02/S03/S06；2. 先做文档与 no-copy，不做 runtime/diff 设计。 | 推荐方案覆盖 research-to-execution 执行语义闭环；备选能降低短期范围但会削弱 QMT 后续消费证据。 | 影响后续 QMT route 是否能消费 `order_intent_draft_v1`，以及 Backtrader reference 是否可解释执行差异；semantic diff 不承担因子评价。 | 若 diff 或 draft 暂缓，需把 S02/S03 转 deferred 并刷新 CP5；若要 factor tear sheet / IC report，另起研究 CR。 |
| DQ-CP5-CR025-03 | `risk_acceptance` | 是否继续接受 Backtrader GPLv3 no-copy 与 `migration_candidate=[]`？ | 接受 no-copy：仅 clean-room 定义本项目接口和文档矩阵，不复制 / 裁剪 / 改写 / 源码级移植 Backtrader，且不把 Backtrader 写成多因子研究主框架。 | 1. CP5 后仅 optional dependency + lazy import；2. 另起 legal / source migration CR。 | 推荐方案合规风险最低；optional dependency 仍需依赖与回归治理；source migration 风险最高且需许可证策略。 | 影响 GPLv3/copyleft、分发、维护和代码来源审计；避免把 Backtrader indicators / Strategy / analyzer 体系误迁为 FactorSpec / IC / RankIC 能力。 | 如用户指定源码迁移模块，停止当前实现并回退 CP3/另起 CR；如用户指定多因子研究能力，启动后续研究 CR。 |
| DQ-CP5-CR025-04 | `runtime_authorization` | CP5 通过后是否只授权受控离线实现，不授权依赖变更、Backtrader run 或真实外部操作？ | 确认只授权离线 / fixture / 静态合同实现；实现阶段真实操作计数仍必须为 0，且不授权 Qlib / Alphalens / vnpy.alpha 集成。 | 1. 单独发起 dependency Spike；2. 另起 QMT/gateway/真实运行 CR 或 per-run authorization。 | 推荐方案与当前安全边界一致；备选需要更高风险门控和额外审查。 | 防止 CP5 被误读为运行授权、依赖安装授权、账户操作授权或多因子研究框架集成授权。 | 任一真实操作、依赖安装或研究框架集成需求出现时停止 CR-025 当前实现路线，转独立 CR。 |
| DQ-CP5-CR025-05 | `follow_up_tracking` | 是否保持真实 QMT 路线、Qlib/minute/Level2 后续能力和多因子研究闭环独立推进？ | 保持 CR-020..CR-024、CR-026..CR-028 与 CR-030 多因子研究框架借鉴候选独立；CR-025 只提供 execution semantic diff / draft / no-copy / docs 证据。 | 1. 并行启动 CR-020 gateway health；2. 将 CR-030 多因子研究闭环作为新 CR 候选优先启动；3. 暂缓全部后续 route，先关闭 CR-025。 | 推荐方案保持三主线解耦；CR-020 并行会增加调度复杂度但不必授权交易；先启 CR-030 更贴近研究主线但会与 CR-025 CP5 / story-execution 抢占设计资源；暂缓会降低路线联动价值。 | 影响真实 QMT 路线启动顺序、后续研究主线 backlog，以及 FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪和策略准入包的独立立项。 | 用户明确优先 QMT 时，先做 CR-020 冲突预检；用户明确优先研究闭环时，启动 CR-030 冲突预检；否则 CR-025 完成后再推进。 |

### CP5 追加字段

| 字段 | 内容 |
|---|---|
| LLD clarification queue 收敛状态 | `items=[]`；未回答阻断问题 0；`blocks_lld=true` 未回答项 0。 |
| 跨 Story 契约 | S01/S04 冻结 clean feed 与 no-copy；S02 消费 S01/S04；S03 消费 S02 和既有 QMT 合同；S05/S06 消费 S01..S04。 |
| 文件 owner | S01 owner `engine/backtrader_adapter.py` / `engine/backtest.py`；S02 owner `engine/semantic_diff.py` / `reports/semantic_diff/**`；S03 owner `engine/order_intent_draft.py`；S04 owner `docs/CR025-BACKTRADER-MODULE-REFERENCE.md`；S05 owner `tests/test_cr025_*`；S06 owner `docs/CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md`。 |
| merge order | S01/S04 -> S02 -> S03 -> S05/S06；共享 README / USER-MANUAL 由 S06 后置合并。 |
| ADR-078 定位澄清 | Backtrader 只作为 lightweight execution engine 的 execution semantic reference；CR-025 不实现 FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪、策略准入包或 Qlib / Alphalens / vnpy.alpha 集成。 |
| 不授权项 | 依赖变更、Backtrader run、Backtrader GPLv3 源码复制 / 裁剪 / 改写 / 源码级移植、真实 broker / QMT / provider / lake / publish / simulation / live、凭据读取、多因子研究主框架实现和 Qlib / Alphalens / vnpy.alpha 集成均不授权。 |

### 不授权项

| 不授权 ID | 操作类别 | 本轮含义 |
|---|---|---|
| NA-CP5-CR025-01 | 修改 `pyproject.toml` / `uv.lock` 或安装 Backtrader | 不授权；如需 optional dependency，另行决策。 |
| NA-CP5-CR025-02 | 运行 Backtrader optional backend、样例或测试 | 不授权；实现和验证必须 fixture-only。 |
| NA-CP5-CR025-03 | 复制、裁剪、改写或源码级移植 Backtrader GPLv3 源码 / samples / tests / datas / live store / line runtime | 不授权；`migration_candidate=[]`。 |
| NA-CP5-CR025-04 | 真实 broker、Backtrader live store、QMT / MiniQMT / XtQuant、gateway 启动、端口绑定 | 不授权。 |
| NA-CP5-CR025-05 | 发单、撤单、账户查询、broker lake 写入 | 不授权。 |
| NA-CP5-CR025-06 | provider fetch、真实联网补数、真实 lake write、catalog publish | 不授权。 |
| NA-CP5-CR025-07 | simulation、live_readonly、small_live、scale_up | 不授权。 |
| NA-CP5-CR025-08 | 读取、打印、记录或保存凭据 / token / session / cookie / 交易密码 / 私钥 | 不授权。 |
| NA-CP5-CR025-09 | 将 Backtrader reference 输出声明为 production truth、simulation-ready 或 QMT admission pass | 不授权。 |
| NA-CP5-CR025-10 | 实现或授权多因子研究主框架、FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪、策略准入包，或集成 Qlib / Alphalens / vnpy.alpha | 不授权；后续必须独立 CR / CP 门控。 |

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| CP3 HLD 人工审查已通过 | 通过 | `checkpoints/CP3-CR025-HLD-REVIEW.md` status=`approved` | 用户当前指令继续推进 CR-025，接受 CP5 推荐方案。 |
| CP4 自动预检已通过 | 通过 | `process/checks/CP4-CR025-STORY-DAG-PARALLEL-SAFETY.md` 结论 PASS | 阻断项 0。 |
| 6 份 LLD 均已输出 | 通过 | `process/stories/CR025-S01..S06-*-LLD.md` | 全量 LLD 纳入本批确认。 |
| 6 份 CP5 自动预检均 PASS | 通过 | `process/checks/CP5-CR025-S01..S06-*-LLD-IMPLEMENTABILITY.md` | 6/6 PASS。 |
| 未回答阻断问题为 0 | 通过 | 子 agent completion summary；`open_items: 0` | LLD clarification queue 无阻断项。 |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 全量 LLD 覆盖 6 个 Story | 通过 | `CR025-S01..S06-*-LLD.md` | 覆盖完整。 |
| 2 | 每份 LLD 保持 14 个可见章节 | 通过 | LLD §1..§14 | 通过。 |
| 3 | CP5 自动预检 6/6 PASS | 通过 | CP5 自动预检文件 | 6/6 PASS。 |
| 4 | `implementation_allowed=false` 在 CP5 前保持 | 通过 | LLD frontmatter、Story Status | CP5 前已保持 false；本次批准后仅允许受控离线实现。 |
| 5 | Backtrader no-copy / `migration_candidate=[]` 明确 | 通过 | S04 LLD、ADR-076 | 继续接受 no-copy。 |
| 6 | `order_intent_draft_v1` 不是订单，不授权 QMT | 通过 | S03 LLD、HLD-QMT §18 | 不授权 QMT。 |
| 7 | no-real-operation safety 覆盖 16 类禁止项 | 通过 | S05/S06 LLD、CP4 | 禁止项继续有效。 |
| 8 | 文件 owner 与 merge order 可执行 | 通过 | Development Plan、6 份 LLD | W1 S01/S04 先行。 |
| 9 | CP5 通过含义与不授权项分离 | 通过 | Decision Brief、不授权项表 | `approve` / 继续推进不授权 10 项禁止操作。 |
| 10 | 子 agent 调度证据完整 | 通过 | 两份 LLD handoff、agent lifecycle | 已具备 LLD 子 agent 证据。 |
| 11 | ADR-078 多因子研究边界已落回 LLD / CP5 | 通过 | S02/S04/S05/S06 LLD 与 CP5 自动预检 | CR-030 已作为后续候选记录。 |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| CP5 人工确认可决定是否进入受控离线实现 | 通过 | 本 Decision Brief | 进入 story-execution；仅受控离线 / fixture / 静态合同实现。 |
| 阻断项为 0 | 通过 | 自动预检摘要 | 阻断项 0。 |
| 风险接受项已列明 | 通过 | DQ-CP5-CR025-03 / DQ-CP5-CR025-04 | 继续接受 no-copy 与 runtime no-real-operation。 |
| 不授权项已独立列出 | 通过 | NA-CP5-CR025-01..10 | 不授权边界继续有效。 |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| S01 LLD | `process/stories/CR025-S01-clean-feed-gate-backend-selector-LLD.md` | 通过 | 允许进入 W1 受控离线实现。 |
| S02 LLD | `process/stories/CR025-S02-semantic-diff-schema-artifact-LLD.md` | 通过 | 等待 S01/S04 合同实现后进入后续 Wave。 |
| S03 LLD | `process/stories/CR025-S03-order-intent-draft-qmt-boundary-LLD.md` | 通过 | 等待 S02。 |
| S04 LLD | `process/stories/CR025-S04-backtrader-module-reference-no-copy-guardrail-LLD.md` | 通过 | 允许进入 W1 受控离线实现。 |
| S05 LLD | `process/stories/CR025-S05-no-real-operation-safety-verification-LLD.md` | 通过 | 等待 S01..S04。 |
| S06 LLD | `process/stories/CR025-S06-route-docs-and-follow-up-handoff-LLD.md` | 通过 | 等待 S01..S04。 |
| CP5 自动预检 | `process/checks/CP5-CR025-S01..S06-*-LLD-IMPLEMENTABILITY.md` | 通过 | 6/6 PASS |
| CP5 发起消息 | `process/checks/CP5-CR025-HUMAN-GATE-LAUNCH-MESSAGE.md` | 通过 | 用户已在对话中要求继续推进 CR-025。 |

## 人工审查结果

- 结论：`approved`
- 审查人：user
- 审查时间：2026-06-02T07:19:31+08:00
- 修改意见：先把后续多因子框架借鉴其他 GitHub 项目的 CR 候选记录好，并继续推进 CR-025。
- 风险接受项：接受 DQ-CP5-CR025-03 的 Backtrader GPLv3 no-copy / `migration_candidate=[]`；接受 DQ-CP5-CR025-04 的受控离线实现边界；接受 DQ-CP5-CR025-05 的 CR-030 多因子研究闭环独立后续跟踪。
- 不授权确认：本次继续推进不授权 NA-CP5-CR025-01..10 中任何操作。
