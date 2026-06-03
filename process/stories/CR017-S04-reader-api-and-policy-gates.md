---
story_id: "CR017-S04-reader-api-and-policy-gates"
title: "reader API 与单口径 policy gates"
story_slug: "reader-api-and-policy-gates"
status: "verified"
priority: "P0"
wave: "CR017-W2-DERIVATION-READERS"
depends_on:
  - "CR017-S03-qfq-hfq-derived-view-normalization"
dependency_type:
  - upstream: "CR017-S03-qfq-hfq-derived-view-normalization"
    type: "contract"
cp5_batch: "CR017-ADJUSTMENT-DUAL-VIEW-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "market_data/adjustment_readers.py"
    - "tests/test_cr017_reader_policy_gates.py"
  shared:
    - "market_data/readers.py"
    - "engine/research_dataset.py"
  merge_owner: "CR017-S04-reader-api-and-policy-gates"
  forbidden:
    - "pyproject.toml"
    - "uv.lock"
    - "credential files or secret values"
lld_gate:
  required_inputs:
    - "process/HLD-DATA-LAKE.md#18.7"
    - "process/ARCHITECTURE-DECISION.md#ADR-054"
    - "process/stories/CR017-S04-reader-api-and-policy-gates.md"
  status: "approved"
  cp5_batch: "CR017-ADJUSTMENT-DUAL-VIEW-BATCH-A"
  lld_path: "process/stories/CR017-S04-reader-api-and-policy-gates-LLD.md"
  cp5_auto_precheck: "process/checks/CP5-CR017-S04-reader-api-and-policy-gates-LLD-IMPLEMENTABILITY.md"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  reason: "CR017-S03 已 CP7 PASS / verified；CP5 已 approved；当前无 dev_running 文件冲突，可进入 reader API 与 policy gate 离线实现。"
created_at: "2026-05-28"
updated_at: "2026-05-28T08:02:53+08:00"
verification_gate:
  cp7_status: "PASS"
  cp7_result: "process/checks/CP7-CR017-S04-reader-api-and-policy-gates-VERIFICATION-DONE.md"
  verification_handoff: "process/handoffs/META-QA-CR017-S04-CP7-VERIFY-2026-05-28.md"
  verified_by: "meta-qa/qa-hua"
  verified_at: "2026-05-28T08:00:02+08:00"
  agent_id: "019e6bdf-8f4b-7553-a3ad-7124fc7fb276"
  agent_name: "qa-hua"
change_id: "CR-017"
---

# CR017-S04：reader API 与单口径 policy gates

## 目标

为研究消费层提供显式 `research_adjustment_policy` reader API 和 single-policy gate，使同一 run 只能消费 raw、qfq、hfq 或 returns_adjusted 中的一类口径。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-12 |
| 需求 | REQ-101、REQ-102、REQ-104 |
| HLD | `process/HLD-DATA-LAKE.md` §18.7、§18.8 |
| ADR | ADR-054、ADR-055、ADR-058 |

## 开发上下文（dev_context）

**背景说明**：现有研究消费需要从单一 qfq 过渡到显式 policy。Reader 必须输出 view metadata、source_run_id 和 gate status；QMT 相关消费必须把复权口径作为 metadata，不得把复权价作为执行价。

**输入文件**：CR017-S03 派生 view 合同、CR015 order intent 合同输入、HLD-DATA-LAKE §18。

**输出文件**：`market_data/adjustment_readers.py`、`tests/test_cr017_reader_policy_gates.py`；共享 `market_data/readers.py`、`engine/research_dataset.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| read_adjusted_view | view_id、policy、date range、symbols | frame + metadata | 多 policy 输入 fail fast |
| single_policy_gate | frame metadata、requested policy | pass / blocked reason | policy 缺失或混用时 blocked |
| qmt_policy_handoff | research policy、raw price reference | metadata only | execution price 必须由 raw / broker reference 提供 |

**设计约束**：reader 不触发 backfill，不触发 provider，不修改 current pointer；研究 consumer 直接扫描未发布 candidate 的行为必须 blocked，除非 LLD 明确为 fixture 测试。

**命名规范**：`research_adjustment_policy`、`view_id`、`single_policy_gate_status`、`execution_price_policy=raw`。

**平台目标**：本地研究消费层和 QMT metadata handoff。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR017-S03 | contract | 派生 view schema 已冻结 | S03 实现或合同冻结后开发 | Reader 不自行定义 view schema |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR017-S04-T1 | 创建 | `market_data/adjustment_readers.py` | 提供显式 policy reader 和 gate result |
| CR017-S04-T2 | 修改 | `market_data/readers.py` | 按 LLD 接入调整视图读取入口 |
| CR017-S04-T3 | 创建 | `tests/test_cr017_reader_policy_gates.py` | 覆盖混用阻断、metadata 输出和 QMT raw handoff |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr017_reader_policy_gates.py`。

**验证方式**：fixture reader / metadata contract；不联网、不写 lake。

**依赖环境**：Python 3.11、uv、pytest。

**关键验证场景**：未指定 policy blocked；混用 raw/qfq/hfq blocked；指定 policy metadata 完整；QMT handoff 只输出 research metadata。

## 量化验收标准（acceptance_criteria）

- [ ] single-policy gate 对未指定或混用 policy 的 blocked 覆盖率 100%。
- [ ] reader metadata 必含 policy、view_id、source_run_id、quality_status、single_policy_gate_status。
- [ ] QMT handoff 中复权价作为执行价的通过次数为 0。
- [ ] 默认验证的 provider_fetch、lake_write、credential_read、current_pointer_publish、dependency_change 计数均为 0。

## 阻塞说明

CP5 前不得实现；真实生产 reader 切换和旧入口兼容必须等全量 LLD 确认。
