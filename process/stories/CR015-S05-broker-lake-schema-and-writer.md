---
story_id: "CR015-S05-broker-lake-schema-and-writer"
title: "broker lake schema 与 dry-run writer"
story_slug: "broker-lake-schema-and-writer"
status: "verified"
priority: "P0"
wave: "CR015-W2-OMS-RISK-LAKE"
depends_on:
  - "CR015-S03-oms-order-state-machine"
dependency_type:
  - upstream: "CR015-S03-oms-order-state-machine"
    type: "contract"
cp5_batch: "CR015-QMT-FOUNDATION-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "trading/broker_lake.py"
    - "tests/test_cr015_broker_lake_schema_writer.py"
  shared:
    - "trading/oms.py"
  merge_owner: "CR015-S05-broker-lake-schema-and-writer"
  forbidden:
    - "data/**"
    - "reports/**"
    - "pyproject.toml"
    - "uv.lock"
    - "credential files or secret values"
    - "real broker lake write"
lld_gate:
  required_inputs:
    - "process/HLD-QMT-TRADING.md#5"
    - "process/ARCHITECTURE-DECISION.md#ADR-056"
    - "process/stories/CR015-S05-broker-lake-schema-and-writer.md"
  status: "approved"
  cp5_batch: "CR015-QMT-FOUNDATION-BATCH-A"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  reason: "CR015-S03 与 CR015-S04 均已 CP7 PASS / verified；CP5 已 approved；当前无 dev_running / verify_running 的 `trading/oms.py` 冲突，可进入 broker lake schema / dry-run writer 离线实现。"
created_at: "2026-05-28"
updated_at: "2026-05-28T09:11:25+08:00"
development_gate:
  implementation_handoff: "process/handoffs/META-DEV-CR015-S05-IMPLEMENT-2026-05-28.md"
  implementation_started_at: "2026-05-28T08:53:21+08:00"
  implementation_completed_at: "2026-05-28T09:01:08+08:00"
  implemented_by: "meta-dev/dev-he the 2nd"
  agent_id: "019e6c12-451b-73e0-9621-09c8750e6b81"
  agent_name: "dev-he the 2nd"
  cp6: "process/checks/CP6-CR015-S05-broker-lake-schema-and-writer-CODING-DONE.md"
  cp6_status: "PASS"
  test_result: "29 passed in 0.13s"
  safety_counters_zero: true
verification_gate:
  cp7_status: "PASS"
  cp7_result: "process/checks/CP7-CR015-S05-broker-lake-schema-and-writer-VERIFICATION-DONE.md"
  verification_handoff: "process/handoffs/META-QA-CR015-S05-CP7-VERIFY-2026-05-28.md"
  verified_by: "meta-qa/qa-kong the 2nd"
  verified_at: "2026-05-28T09:07:31+08:00"
  agent_id: "019e6c1d-ab63-7130-98a8-ecf802425771"
  agent_name: "qa-kong the 2nd"
change_id: "CR-015"
---

# CR015-S05：broker lake schema 与 dry-run writer

## 目标

定义外置 broker lake 的 order_intent、broker_order、fill、position、asset、error、reconciliation、incident schema 和 dry-run writer。CR-015 不写真实 broker lake，只输出写入计划或 mock 审计。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-10 |
| 需求 | REQ-108、REQ-111、REQ-121 |
| HLD | `process/HLD-QMT-TRADING.md` §5、§7.1 |
| ADR | ADR-056 |

## 开发上下文（dev_context）

**背景说明**：broker lake 与 market data lake 隔离，默认外置 root；日志和报告只保留脱敏标签、run_id、schema_version 和 root label。未授权时不能写真实 broker lake。

**输入文件**：CR015-S03 OMS events、ADR-056、HLD-QMT-TRADING。

**输出文件**：`trading/broker_lake.py`、`tests/test_cr015_broker_lake_schema_writer.py`；共享 `trading/oms.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| broker schema registry | event type | schema fields、schema_version | 未知 event fail |
| dry_run_write_plan | event、root label、retention policy | write plan、redaction_status | 不写真实外置 root |
| redaction gate | event payload | sanitized event / blocked | 敏感字段命中时 blocked 或脱敏 |

**设计约束**：不得写仓库 `data/**` 或 `reports/**`；不得记录真实私有路径或凭据值；真实写入必须 CR016 / 后续 per-run 授权。

**命名规范**：`schema_version`、`redaction_status`、`retention_policy`、`broker_lake_root_label`、`event_type`。

**平台目标**：外置 broker lake contract；默认 dry-run。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR015-S03 | contract | order state / event schema 已定义 | broker lake 消费 OMS event | 不反向修改状态机 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR015-S05-T1 | 创建 | `trading/broker_lake.py` | 定义 broker lake schema registry、dry-run writer、redaction gate |
| CR015-S05-T2 | 创建 | `tests/test_cr015_broker_lake_schema_writer.py` | 覆盖 schema、dry-run plan、forbidden local write、redaction |
| CR015-S05-T3 | 修改 | `trading/oms.py` | 按 LLD 输出 broker event contract |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr015_broker_lake_schema_writer.py`。

**验证方式**：dry-run / fixture；不写真实 broker lake。

**依赖环境**：Python 3.11、uv、pytest。

**关键验证场景**：8 类 schema 覆盖；本地仓库 data/reports 写入 blocked；dry-run plan 输出；敏感字段 redaction gate 生效。

## 量化验收标准（acceptance_criteria）

- [x] broker lake schema 覆盖 order_intent、broker_order、fill、position、asset、error、reconciliation、incident 8 类对象。
- [x] 未授权真实写入时 broker_lake_write=0。
- [x] 仓库 `data/**` / `reports/**` 写入尝试 blocked。
- [x] redaction_status 必填，敏感字段原值输出次数为 0。

## 开发完成摘要

- CP6：`process/checks/CP6-CR015-S05-broker-lake-schema-and-writer-CODING-DONE.md`
- 测试：`PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr015_oms_state_machine.py tests/test_cr015_pretrade_risk_gate.py tests/test_cr015_broker_lake_schema_writer.py`，结果 `29 passed in 0.13s`
- 安全计数：QMT / broker / order / cancel / account / credential / lake / provider / publish / dependency / open-write / sensitive raw output 均为 0

## 阻塞说明

CP5 前不得实现；真实 broker lake root 和写入授权后置。
