---
story_id: "CR017-S06-research-qmt-consumer-docs-and-migration-guide"
title: "研究 / QMT 消费边界与迁移指南"
story_slug: "research-qmt-consumer-docs-and-migration-guide"
status: "verified"
priority: "P0"
wave: "CR017-W3-CONSUMER-MIGRATION"
depends_on:
  - "CR017-S04-reader-api-and-policy-gates"
  - "CR017-S05-validation-quality-parity-and-leakage-tests"
dependency_type:
  - upstream: "CR017-S04-reader-api-and-policy-gates"
    type: "contract"
  - upstream: "CR017-S05-validation-quality-parity-and-leakage-tests"
    type: "validation-contract"
cp5_batch: "CR017-ADJUSTMENT-DUAL-VIEW-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "docs/ADJUSTMENT-POLICY-MIGRATION.md"
    - "tests/test_cr017_research_qmt_consumer_boundary.py"
  shared:
    - "README.md"
    - "docs/USER-MANUAL.md"
    - "engine/research_dataset.py"
  merge_owner: "CR017-S06-research-qmt-consumer-docs-and-migration-guide"
  forbidden:
    - "process/HLD.md"
    - "process/HLD-DATA-LAKE.md"
    - "process/ARCHITECTURE-DECISION.md"
    - "pyproject.toml"
    - "uv.lock"
    - "credential files or secret values"
lld_gate:
  required_inputs:
    - "process/HLD.md#31"
    - "process/HLD-DATA-LAKE.md#18"
    - "process/HLD-QMT-TRADING.md#7.1"
    - "process/stories/CR017-S06-research-qmt-consumer-docs-and-migration-guide.md"
  status: "approved"
  cp5_batch: "CR017-ADJUSTMENT-DUAL-VIEW-BATCH-A"
  lld_path: "process/stories/CR017-S06-research-qmt-consumer-docs-and-migration-guide-LLD.md"
  cp5_auto_precheck: "process/checks/CP5-CR017-S06-research-qmt-consumer-docs-and-migration-guide-LLD-IMPLEMENTABILITY.md"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  reason: "CR017-S04/S05 均已 CP7 PASS / verified；CP5 已 approved；当前无 dev_running 文件冲突，可进入 consumer boundary / migration docs 离线实现。"
created_at: "2026-05-28"
updated_at: "2026-05-28T08:48:50+08:00"
development_gate:
  implementation_handoff: "process/handoffs/META-DEV-CR017-S06-IMPLEMENT-2026-05-28.md"
  implementation_started_at: "2026-05-28T08:29:17+08:00"
  implementation_completed_at: "2026-05-28T08:36:51+08:00"
  implemented_by: "meta-dev/dev-lv the 2nd"
  agent_id: "019e6bfc-348d-7730-b9a1-cec5434a2646"
  agent_name: "dev-lv the 2nd"
  cp6: "process/checks/CP6-CR017-S06-research-qmt-consumer-docs-and-migration-guide-CODING-DONE.md"
  cp6_status: "PASS"
  test_result: "6 passed in 0.38s; CR017 related regression 39 passed in 0.44s"
  safety_counters:
    provider_fetch: 0
    lake_write: 0
    credential_read: 0
    current_pointer_publish: 0
    real_order_call: 0
    real_cancel_call: 0
    account_query_call: 0
    dependency_change: 0
    legacy_qfq_overwrite: 0
    non_raw_execution_allowed: 0
    production_adjustment_governance_claim_allowed: 0
    scale_up_allowed: 0
verification_gate:
  cp7_status: "PASS"
  cp7_result: "process/checks/CP7-CR017-S06-research-qmt-consumer-docs-and-migration-guide-VERIFICATION-DONE.md"
  verification_handoff: "process/handoffs/META-QA-CR017-S06-CP7-VERIFY-2026-05-28.md"
  verified_by: "meta-qa/qa-hua the 2nd"
  verified_at: "2026-05-28T08:45:04+08:00"
  agent_id: "019e6c08-720d-77c0-89e4-1d5c8a57a66b"
  agent_name: "qa-hua the 2nd"
change_id: "CR-017"
---

# CR017-S06：研究 / QMT 消费边界与迁移指南

## 目标

把复权双视图对研究、报告、QMT order intent 和用户文档的消费边界落成可实现 Story，明确图表可用 qfq、长期研究推荐 hfq / returns_adjusted、交易执行只用 raw / broker reference。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-10、UC-11、UC-12 |
| 需求 | REQ-101、REQ-102、REQ-103、REQ-118、REQ-119、REQ-120、REQ-121 |
| HLD | `process/HLD.md` §31；`process/HLD-DATA-LAKE.md` §18；`process/HLD-QMT-TRADING.md` §7.1 |
| ADR | ADR-054、ADR-055、ADR-058、ADR-059 |

## 开发上下文（dev_context）

**背景说明**：CR-017 完成前不阻断 QMT 技术模拟盘，但阻断生产策略复权治理完成声明和 scale_up。该 Story 为 CR015/016 提供可消费的口径边界、迁移指南和 blocked claims。

**输入文件**：CR017-S04/S05 输出、HLD-QMT-TRADING、主 HLD §31、用户文档。

**输出文件**：`docs/ADJUSTMENT-POLICY-MIGRATION.md`、`tests/test_cr017_research_qmt_consumer_boundary.py`；共享 `README.md`、`docs/USER-MANUAL.md`、`engine/research_dataset.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| consumer guidance matrix | consumer type、policy | recommended / allowed / blocked | QMT execution 对非 raw blocked |
| blocked claim builder | CR017 status、stage、policy | blocked_claims、解除条件 | CR017 未 verified 时 scale_up blocked |
| migration guide | old qfq ref、new views | user-facing migration summary | 不覆盖旧报告，不输出敏感信息 |

**设计约束**：本 Story 可刷新用户文档和 consumer boundary，但不得修改 CP3 过程文档；不授权真实运行；scale_up 必须检查 CR017 verified。

**命名规范**：claim 字段使用 `adjustment_governance_status`、`research_adjustment_policy`、`execution_price_policy`、`blocked_claims`。

**平台目标**：研究消费与 QMT Story 的共同合同输入。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR017-S04 | contract | reader policy gate 可引用 | 开发需避免共享 research_dataset 冲突 | 提供消费接口 |
| CR017-S05 | validation-contract | 验证矩阵已定义 | 阻断声明必须和测试矩阵一致 | 提供 quality / leakage 证据 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR017-S06-T1 | 修改 | `docs/ADJUSTMENT-POLICY-MIGRATION.md` | 补充研究 / QMT 消费矩阵和迁移步骤 |
| CR017-S06-T2 | 修改 | `README.md` / `docs/USER-MANUAL.md` | 按 LLD 写用户可见口径边界 |
| CR017-S06-T3 | 创建 | `tests/test_cr017_research_qmt_consumer_boundary.py` | 验证 blocked claims 和 QMT raw-only 文档合同 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr017_research_qmt_consumer_boundary.py`。

**验证方式**：文档片段 / metadata contract 检查；不真实交易。

**依赖环境**：Python 3.11、uv、pytest。

**关键验证场景**：研究消费矩阵完整；QMT 执行 raw-only；CR017 未 verified 时 scale_up blocked；旧 qfq 保留声明不覆盖旧报告。

## 量化验收标准（acceptance_criteria）

- [ ] consumer guidance 至少覆盖 chart、long-horizon research、factor research、QMT order intent 4 类消费方。
- [ ] QMT execution 非 raw allowed 次数为 0。
- [ ] CR017 未 verified 时 production adjustment governance claim 和 scale_up allowed 次数均为 0。
- [ ] 默认验证的 provider_fetch、lake_write、credential_read、current_pointer_publish、real_order_call、dependency_change 计数均为 0。

## 阻塞说明

CP5 前不得实现；CR016 scale_up 必须等待本 Story 及 CR017 批次实现验证通过。
