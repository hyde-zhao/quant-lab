---
story_id: "CR025-S02-semantic-diff-schema-artifact"
title: "semantic diff schema 与 artifact"
story_slug: "semantic-diff-schema-artifact"
status: "verified"
priority: "P0"
wave: "CR025-W2-SEMANTIC-DIFF"
depends_on:
  - "CR025-S01-clean-feed-gate-backend-selector"
  - "CR025-S04-backtrader-module-reference-no-copy-guardrail"
dependency_type:
  - upstream: "CR025-S01-clean-feed-gate-backend-selector"
    type: "feed-selector-contract"
  - upstream: "CR025-S04-backtrader-module-reference-no-copy-guardrail"
    type: "license-guardrail"
cp5_batch: "CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "engine/semantic_diff.py"
    - "reports/semantic_diff/**"
    - "tests/test_cr025_semantic_diff_contract.py"
  shared:
    - "engine/backtest.py"
    - "engine/backtrader_adapter.py"
  merge_owner: "CR025-S02-semantic-diff-schema-artifact"
  forbidden:
    - "report claims as production truth"
    - "report claims as simulation-ready"
    - "Backtrader result overwrites lightweight baseline"
    - "semantic diff as factor tear sheet / IC report / strategy admission package"
    - "provider fetch"
    - "lake write"
    - "Backtrader run before CP5"
lld_gate:
  required_inputs:
    - "process/HLD.md#34.6"
    - "process/HLD.md#34.9"
    - "process/HLD.md#34.13"
    - "process/ARCHITECTURE-DECISION.md#ADR-074"
    - "process/ARCHITECTURE-DECISION.md#ADR-075"
    - "process/ARCHITECTURE-DECISION.md#ADR-076"
    - "process/ARCHITECTURE-DECISION.md#ADR-078"
    - "process/stories/CR025-S02-semantic-diff-schema-artifact.md"
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
task_count: 4
created_at: "2026-06-01T22:42:19+08:00"
updated_at: "2026-06-02T08:21:16+08:00"
change_id: "CR-025"
---

# CR025-S02：semantic diff schema 与 artifact

## 目标

定义 lightweight baseline 与 Backtrader-style execution semantic reference 之间的 semantic diff schema 和 artifact 合同，覆盖成交、现金、成本、滑点、净值、仓位、差异原因、unavailable 与 limitations。该 Story 不把 Backtrader reference 结果提升为 production truth 或 simulation-ready 结论，也不把 semantic diff 扩展为 FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪或策略准入包。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-19、SM-35、SM-36、TS-025-03、TS-025-04、TS-025-08 |
| 需求 | REQ-164、REQ-166、RA-060、RA-061、RA-062 |
| HLD | `process/HLD.md` §34.6、§34.9、§34.13、§34.14 |
| ADR | ADR-074、ADR-075、ADR-076、ADR-078 |

## 开发上下文（dev_context）

**背景说明**：CR-025 的核心价值不是替换现有 lightweight 回测，而是把两类执行语义差异显式化。diff artifact 是研究解释和后续 QMT admission 的输入，不是交易授权、真实运行证据或多因子研究评价报告。多因子研究闭环另起后续 CR，参考 Qlib / Alphalens / vnpy.alpha。

**输入文件**：CR025-S01 selector 合同、CR025-S04 no-copy guardrail、CR-025 HLD / ADR、本 Story 卡片。

**输出文件**：`engine/semantic_diff.py`、`reports/semantic_diff/**`、`tests/test_cr025_semantic_diff_contract.py`。

**接口约定**：

| 字段组 | 最低字段 |
|---|---|
| metadata | `schema_version`、`baseline_backend`、`reference_backend`、`generated_at`、`source_run_id`、`lineage` |
| availability | `baseline_available`、`reference_available`、`blocked_reasons[]`、`limitations[]` |
| fills | fill count、fill timing、partial fill flag、price source、rounding policy |
| cash / cost | starting cash、ending cash、commission、tax、slippage、cash reconciliation |
| portfolio | holdings delta、position sizing delta、turnover delta、net value delta |
| explanation | `diff_reason[]`、`severity`、`requires_follow_up`、`qmt_relevance` |

**设计约束**：diff artifact 必须保留 baseline 与 reference 双轨，不允许 Backtrader result 覆盖 lightweight baseline；reference unavailable 是合法结果；报告不得声称 production truth、simulation-ready 或 QMT admission pass；不得新增 factor tear sheet、IC / RankIC report、分层收益报告、多因子组合结果、experiment tracker 或 strategy admission package。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR025-S01 | feed-selector-contract | selector / unavailable schema 先冻结 | 不直接运行 backend | diff 只消费结果或 unavailable evidence |
| CR025-S04 | license-guardrail | no-copy 范围先冻结 | 不复用 GPLv3 源码实现 diff | diff schema 自有实现，不迁移 Backtrader internals |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `engine/semantic_diff.py`、`reports/semantic_diff/**`、`tests/test_cr025_semantic_diff_contract.py` | 当前 Story 独占 |
| shared | `engine/backtest.py`、`engine/backtrader_adapter.py` | 与 S01 串行合并 selector 输出字段 |
| forbidden | production truth / simulation-ready claims、baseline overwrite、factor tear sheet / IC report / strategy admission package、provider fetch、lake write、Backtrader run before CP5 | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR025-S02-T1 | 设计 | `engine/semantic_diff.py` | 定义 semantic diff 数据模型、字段枚举和 severity / reason 规则 |
| CR025-S02-T2 | 设计 | `reports/semantic_diff/**` | 定义 artifact 路径、文件命名、schema version 和 limitations |
| CR025-S02-T3 | 设计 | `tests/test_cr025_semantic_diff_contract.py` | 设计 schema、unavailable、baseline/reference 双轨和禁用声明测试 |
| CR025-S02-T4 | 约束 | docs / reports | 禁止把 diff report 解释为真实交易、simulation-ready 授权或多因子研究评价报告 |

## 验证上下文（validation_context）

**验证入口**：后续 LLD 可建议 `uv run --python 3.11 pytest -q tests/test_cr025_semantic_diff_contract.py`，但本阶段不执行。

**验证方式**：fixture-only schema contract；可用静态 fixture 表达 baseline 与 reference 差异，不需要运行 Backtrader。

**依赖环境**：只读本地 fixture；不得联网、不得写 lake、不得读取凭据。

**关键验证场景**：

| 场景 | 预期 |
|---|---|
| reference unavailable | artifact 标记 unavailable 并保留 reason，不失败为裸异常 |
| fill / cash / cost / portfolio 差异 | 每类差异有字段与 reason |
| report 被下游消费 | 下游只能读 semantic evidence，不把 reference 作为 truth |
| forbidden claim scan | production truth、simulation-ready、QMT admission pass 声明为 0 |
| multifactor scope scan | FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪、策略准入包实现项为 0 |

## 量化验收标准（acceptance_criteria）

- [ ] semantic diff 字段不少于 10 类，覆盖成交、现金、成本、滑点、净值、仓位和 diff reason。
- [ ] 每类差异均有 `reason` 或 `unavailable`。
- [ ] Backtrader reference 覆盖 lightweight baseline 次数为 0。
- [ ] 报告声称 production truth、simulation-ready、QMT admission pass 的次数为 0。
- [ ] FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪和策略准入包实现项为 0。
- [ ] provider fetch、lake write、credential read、Backtrader run 均为 0。

## 阻塞说明

本 Story 已通过 CR-025 CP5 全量 LLD 批次确认，并已完成 CP6 / CP7：S01、S04 与 S02 均已 CP7 PASS 且 verified。S02 产出的 semantic diff schema / artifact 合同可作为 S03 `order_intent_draft_v1` 的离线输入；不得运行 Backtrader 或生成真实 diff artifact。若需要多因子研究评价合同，必须由 meta-po 启动 CR-030 或其他后续 CR，不得在本 Story 中扩展。
