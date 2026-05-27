---
story_id: "CR008-S05-pit-universe-consumption-contract"
title: "PIT / fixed universe 消费合同"
story_slug: "pit-universe-consumption-contract"
status: "verified"
priority: "P0"
wave: "CR008-BATCH-A"
change_id: "CR-008"
depends_on: ["CR007-S03-index-members-stock-basic-datasets", "CR008-S03-research-dataset-builder"]
dependency_contracts:
  - upstream: "CR007-S03-index-members-stock-basic-datasets"
    type: "contract"
    required: "`index_members` / `stock_basic` readiness 与 PIT 状态已冻结"
  - upstream: "CR008-S03-research-dataset-builder"
    type: "contract"
    required: "`ResearchDataset` universe 字段已冻结"
  - upstream: "CR008-S03-research-dataset-builder"
    type: "file-conflict"
    required: "`engine/research_dataset.py` 共享文件必须串行合并"
file_ownership:
  primary:
    - "engine/universe.py"
    - "tests/test_cr008_pit_universe_contract.py"
  shared:
    - "engine/research_dataset.py"
    - "market_data/readers.py"
  merge_owner: "CR008-S05-pit-universe-consumption-contract"
  forbidden:
    - "market_data/connectors/**"
    - "market_data/runtime.py"
    - "market_data/storage.py"
    - "data/**"
    - "reports/data_quality_report.csv"
    - ".env"
    - "credentials"
    - "delivery/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#25.8"
    - "process/ARCHITECTURE-DECISION.md#adr-027pit--fixed-universe-必须显式声明"
    - "process/stories/CR008-S05-pit-universe-consumption-contract.md"
  status: "cp5-approved"
  cp5_batch: "CR008-BATCH-A"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  blocked_by: ""
  unblock_condition: "satisfied: CR007-S03 CP7 PASS"
  required_contracts:
    - "CR007-S03 readiness and PIT semantics frozen"
    - "research_dataset_builder contract frozen"
    - "CR008-BATCH-A CP5 approved"
  file_conflict_free: true
  cp5_required: true
  implementation_allowed: true
  implementation_scope: "offline-only"
  dev_handoff: "process/handoffs/META-DEV-CR008-S05-IMPLEMENT-2026-05-21.md"
  dev_agent_name: "dev-qin the 2nd"
  dev_agent_id: "019e4b9e-e3e8-7260-93dc-e64fb31e40b1"
  dev_started_at: "2026-05-22T01:39:29+08:00"
  dev_completed_at: "2026-05-22T01:49:22+08:00"
  cp6_status: "PASS"
  cp6_checkpoint: "process/checks/CP6-CR008-S05-pit-universe-consumption-contract-CODING-DONE.md"
  cp6_completed_at: "2026-05-22T01:49:22+08:00"
  qa_handoff: "process/handoffs/META-QA-CR008-S05-CP7-VERIFY-2026-05-22.md"
cp6_status: "PASS"
cp6_checkpoint: "process/checks/CP6-CR008-S05-pit-universe-consumption-contract-CODING-DONE.md"
cp6_completed_at: "2026-05-22T01:49:22+08:00"
cp7_handoff: "process/handoffs/META-QA-CR008-S05-CP7-VERIFY-2026-05-22.md"
cp7_status: "PASS"
cp7_agent_name: "qa-wei the 2nd"
cp7_agent_id: "019e4bac-11fc-7f23-86fb-e307a6004ba6"
cp7_started_at: "2026-05-22T01:53:54+08:00"
cp7_completed_at: "2026-05-22T04:26:11+08:00"
cp7_checkpoint: "process/checks/CP7-CR008-S05-pit-universe-consumption-contract-VERIFICATION-DONE.md"
verified_at: "2026-05-22T04:29:28+08:00"
created_at: "2026-05-21"
updated_at: "2026-05-22T04:29:28+08:00"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
---

# CR008-S05：PIT / fixed universe 消费合同

## 目标

定义研究入口股票池消费合同：`universe_mode`、`is_pit_universe`、`pit_status` 和 `survivorship_bias_note` 必须显式。严肃研究要求 PIT；固定快照只能用于探索并披露幸存者偏差。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | CR008-AC-009、CR008-AC-010 |
| HLD | §25.8、§25.13 |
| ADR | ADR-027 |

## 开发上下文（dev_context）

**背景说明**：当前 `index_members` 可能是固定快照，`stock_basic` 也可能缺历史 availability。CR008 要求不得伪装 PIT。

**输入文件**：CR007-S03 LLD、CR008-S03 Story、`market_data/readers.py`。

**输出文件**：`engine/universe.py`、`engine/research_dataset.py`、`market_data/readers.py`、`tests/test_cr008_pit_universe_contract.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| universe resolver | index_members / stock_basic reader result、mode | universe metadata | PIT required but unavailable => fail |
| fixed snapshot disclosure | fixed universe frame | survivorship warning | 不得写 `is_pit_universe=true` |

**设计约束**：

- `index_weights` 不得替代 `index_members`。
- `quality_status=pass` 不等于 PIT available。
- fixed snapshot 必须写幸存者偏差说明。

**命名规范**：使用 `universe_mode`、`pit_status`、`is_pit_universe`、`survivorship_bias_note`。

**平台目标**：research dataset universe contract。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR007-S03 | contract | 可基于 confirmed LLD 起草 | readiness/PIT contract frozen | 提供数据层 readiness |
| CR008-S03 | contract + file-conflict | 需引用 builder universe 字段 | builder contract frozen；共享文件不可并行开发 | 写入 ResearchDataset |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR008-S05-T1 | 创建 | `engine/universe.py` | 定义 PIT/fixed universe resolver 和 error contract |
| CR008-S05-T2 | 修改 | `engine/research_dataset.py` | 接入 universe metadata 与 gate result |
| CR008-S05-T3 | 修改 | `market_data/readers.py` | 如需暴露 readiness/PIT issue，保持只读 |
| CR008-S05-T4 | 创建 | `tests/test_cr008_pit_universe_contract.py` | 覆盖 PIT available、PIT missing、fixed snapshot、no weights substitute |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr008_pit_universe_contract.py`。

**验证方式**：reader fixture、universe mode parameter、metadata assertions、no substitute tests。

**依赖环境**：Python 3.11、uv、pytest；离线。

**关键验证场景**：

- PIT available 时 `is_pit_universe=true`。
- PIT required but unavailable 时 fail。
- fixed snapshot 时 `is_pit_universe=false` 且 survivorship note 非空。
- 只有 index_weights 时不得推导完整 universe。

## 量化验收标准（acceptance_criteria）

- [ ] PIT unavailable 时严肃研究 pass 次数为 0。
- [ ] fixed snapshot metadata 100% 包含 survivorship warning。
- [ ] `index_weights` 替代 `index_members` 次数为 0。
- [ ] quality pass 被当作 PIT available 的次数为 0。
- [ ] 旧数据、旧报告、凭据操作次数为 0。

## 阻塞说明

无 BLOCKING。CR007-S03 实现前需先清理 S02 文件冲突；CR008-S05 开发仍需 CP5。
