---
story_id: "CR011-S02-pit-universe-and-stock-lifecycle-completion"
title: "PIT 股票池与股票生命周期"
story_slug: "pit-universe-and-stock-lifecycle-completion"
status: "verified"
priority: "P0"
wave: "CR011-DATA-BATCH-A"
depends_on:
  - "CR010-S04-index-members-weights-stock-basic-readiness"
  - "CR010-S06-pit-source-interface-spike-readiness"
  - "CR008-S05-pit-universe-consumption-contract"
dependency_contracts:
  - upstream: "CR010-S04-index-members-weights-stock-basic-readiness"
    type: "runtime"
    required: "index_members、index_weights、stock_basic readiness 和 lifecycle 字段可被只读 reader 消费"
  - upstream: "CR010-S06-pit-source-interface-spike-readiness"
    type: "contract"
    required: "PIT source/interface 未确认时返回 source_unresolved / required_missing，不伪造 available"
  - upstream: "CR008-S05-pit-universe-consumption-contract"
    type: "contract"
    required: "research_input_v1 的 PIT / fixed universe 声明和 allowed/blocked claims 语义已冻结"
file_ownership:
  primary:
    - "tests/test_cr011_pit_universe_lifecycle.py"
  shared:
    - "market_data/readers.py"
    - "engine/research_dataset.py"
  merge_owner: "CR011-S02-pit-universe-and-stock-lifecycle-completion"
  forbidden:
    - "market_data/connectors/**"
    - "data/**"
    - ".env"
    - "reports/experiment_17_21/factor_strategy_report.md"
    - "delivery/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#27.5"
    - "process/HLD-DATA-LAKE.md#14.2"
    - "process/ARCHITECTURE-DECISION.md#adr-037cr-011-pit-universe-与股票生命周期采用-as-of-gate"
    - "process/stories/CR011-S02-pit-universe-and-stock-lifecycle-completion.md"
  status: "approved"
  cp5_batch: "CR011-DATA-BATCH-A"
  cp5_precheck: "process/checks/CP5-CR011-S02-pit-universe-and-stock-lifecycle-completion-LLD-IMPLEMENTABILITY.md"
  manual_review: "checkpoints/CP5-CR011-DATA-BATCH-A-LLD-BATCH.md"
  confirmed_by: "user"
  confirmed_at: "2026-05-24T10:24:02+08:00"
  preconditions:
    - "CR-011 CP3 人工确认通过"
    - "CR-011 CP4 自动预检通过并由 meta-po 汇入 CP5"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  required_contracts:
    - "PIT membership/readiness schema frozen"
    - "stock lifecycle missing behavior frozen"
    - "CR011-DATA-BATCH-A CP5 approved"
  file_conflict_free: true
  cp5_required: true
  implementation_allowed: true
  reason: "S01 已 verified，CR010-S04 为 verified，CR010-S06 已完成 meta-qa CP7 PASS，CR008-S05 已 verified；replacement meta-dev/dev-zhang 已完成 CP6 接管复核并 PASS，meta-qa/qa-shi 已完成 CP7 PASS；真实 PIT source/interface 未冻结时必须 fail-fast，不得伪造 available。"
created_at: "2026-05-23"
updated_at: "2026-05-24T12:01:25+08:00"
source_hld: "process/HLD.md"
companion_hld: "process/HLD-DATA-LAKE.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-011"
---

# CR011-S02：PIT 股票池与股票生命周期

## 目标

基于 PIT membership、权重和生命周期字段建立 as-of universe gate，使新版实验 17-21 可以区分 `production_strict` 的 PIT 股票池与 `exploratory` 的 fixed snapshot。该 Story 不授权真实补数，不允许用 `index_weights` 或 `stock_basic` 当前快照证明 PIT。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-08 |
| 需求 | REQ-072、REQ-080、REQ-081、REQ-082、CR011-AC-002 |
| HLD | `process/HLD.md` §27.1、§27.4、§27.5、§27.7；`process/HLD-DATA-LAKE.md` §14.2、§14.4、§14.5 |
| ADR | ADR-037 |
| Backlog / Plan | `process/STORY-BACKLOG.md` CR011-S02；`process/DEVELOPMENT-PLAN.yaml` wave `CR011-DATA-BATCH-A` |

## 开发上下文（dev_context）

**背景说明**：固定当前沪深 300 成分股快照会引入幸存者偏差。CR-011 需要把 PIT membership、`effective_date`、`available_at`、上市退市状态和 `pit_status` 变成 research gate 的强输入，缺失时阻断生产级结论。

**输入文件**：`process/HLD.md`、`process/HLD-DATA-LAKE.md`、`process/ARCHITECTURE-DECISION.md`、`process/REQUIREMENTS.md`、`process/USE-CASES.md`、`process/changes/CR-011-FACTOR-RESEARCH-DATA-COMPLETION-2026-05-23.md`、`market_data/readers.py`、`engine/research_dataset.py`。

**输出文件**：`market_data/readers.py`、`engine/research_dataset.py`、`tests/test_cr011_pit_universe_lifecycle.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| PIT universe reader | index code、as-of date、catalog/readiness、quality policy | membership rows、`effective_date`、`available_at`、`is_pit_universe`、`pit_status`、lineage | 缺 membership 时返回 `pit_incomplete` / `required_missing` |
| lifecycle gate | symbol、decision date、`stock_basic` / `stock_lifecycle` fields | `list_date`、`delist_date`、`list_status`、上市天数、可参与状态 | lifecycle 缺失不得默认可参与生产级研究 |
| research universe gate | `universe_mode=pit|required`、reader result、fixed snapshot fallback | as-of universe、`as_of_join_violation_count`、`survivorship_bias_note`、blocked claims | fixed snapshot 只能 exploratory |

**设计约束**：

- CP3 / CP4 未通过前不得进入 LLD；`CR011-DATA-BATCH-A` CP5 批次确认前不得实现。
- `index_members` 是完整 membership 主证据；`index_weights` 只提供权重信息；`stock_basic` / lifecycle 只辅助状态判断。
- as-of join 必须满足 `available_at <= decision_time`，违规不得进入 production_strict。
- 不读取 `.env`，不触发真实 source，不操作旧 `data/**`，不覆盖旧报告，不写 `delivery/**`。

**命名规范**：保留 `universe_mode`、`is_pit_universe`、`pit_status`、`as_of_join_violation_count`、`survivorship_bias_note`、`list_status`、`lifecycle_status`。

**平台目标**：本地 Python 因子研究工具；uv 管理依赖；无安装脚本；无 `delivery/**` 输出。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR011-S02-T1 | 修改 | `market_data/readers.py` | 增加或扩展 PIT universe / stock lifecycle 只读结果，保留 readiness、lineage 和 missing reason |
| CR011-S02-T2 | 修改 | `engine/research_dataset.py` | 增加 as-of universe gate，fixed snapshot 只进入 exploratory 并写 blocked claims |
| CR011-S02-T3 | 创建 | `tests/test_cr011_pit_universe_lifecycle.py` | 覆盖 PIT pass、PIT incomplete、fixed snapshot 降级、as-of 违规和 no credential/no old data |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr011_pit_universe_lifecycle.py`。

**验证方式**：fixture catalog、PIT membership / lifecycle 小样本、as-of join 断言、blocked claims 快照和 forbidden path 扫描。

**依赖环境**：Python 3.11、uv、pytest；不需要真实 PIT provider、不需要 token、不联网。

**关键验证场景**：

- `universe_mode=pit` 且 PIT readiness pass 时返回 as-of universe。
- PIT membership 缺失、`available_at` 越界或 `pit_status != pass` 时 production_strict fail。
- `index_weights` 或 `stock_basic` 单独存在时不能证明 PIT。
- 默认路径 `.env`、旧 `data/**`、`market_data/connectors/**`、`delivery/**` 和旧报告写入次数为 0。

## 量化验收标准（acceptance_criteria）

- [ ] production_strict 必须同时满足 `universe_mode=pit`、`is_pit_universe=true`、`pit_status=pass`、`as_of_join_violation_count=0`。
- [ ] 使用 fixed snapshot 进入 production_strict 的次数为 0；exploratory 必须写 `survivorship_bias_note`。
- [ ] `index_weights` 或 `stock_basic` 当前快照被单独用作 PIT membership 证明的次数为 0。
- [ ] lifecycle 缺失时输出结构化 `lifecycle_missing` 或等价 missing reason。
- [ ] 默认验证路径 `network_calls=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_operations=0`。

## 阻塞说明

RESOLVED：CR-011 CP3 人工审查 approved、CP4 自动预检 PASS，`CR011-DATA-BATCH-A` CP5 已 approved。RESOLVED：S01 已 verified，CR010-S04 为 verified，CR010-S06 已完成 meta-qa CP7 PASS，CR008-S05 已 verified。S02 已由 replacement meta-dev/dev-zhang 完成 CP6 接管复核并 PASS，并由 meta-qa/qa-shi 完成 CP7 PASS；真实 PIT source/interface 未冻结时必须 fail-fast 并输出 `required_missing` / `source_unresolved`，不得伪造 available。
