---
story_id: "CR016-S02-reconciliation-service-and-reports"
title: "盘前 / 盘中 / 盘后 reconciliation 服务与报告"
story_slug: "reconciliation-service-and-reports"
status: "verified"
priority: "P0"
wave: "CR016-W1-SIMULATION-OPS-GATES"
depends_on:
  - "CR015-S03-oms-order-state-machine"
  - "CR015-S05-broker-lake-schema-and-writer"
  - "CR016-S01-simulation-account-order-enable-gate"
dependency_type:
  - upstream: "CR015-S03-oms-order-state-machine"
    type: "runtime"
  - upstream: "CR015-S05-broker-lake-schema-and-writer"
    type: "runtime"
  - upstream: "CR016-S01-simulation-account-order-enable-gate"
    type: "contract"
cp5_batch: "CR016-QMT-ACTIVATION-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "trading/reconciliation.py"
    - "tests/test_cr016_reconciliation_service_reports.py"
  shared:
    - "trading/broker_lake.py"
    - "trading/oms.py"
  merge_owner: "CR016-S02-reconciliation-service-and-reports"
  forbidden:
    - "data/**"
    - "reports/** old baseline overwrite"
    - "pyproject.toml"
    - "uv.lock"
    - "credential files or secret values"
lld_gate:
  required_inputs:
    - "process/HLD-QMT-TRADING.md#7.2"
    - "process/ARCHITECTURE-DECISION.md#ADR-060"
    - "process/stories/CR016-S02-reconciliation-service-and-reports.md"
  status: "approved"
  cp5_batch: "CR016-QMT-ACTIVATION-BATCH-A"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  requires_cr015_verified: true
  requires_per_run_authorization: true
  per_run_authorization_scope: "not required for offline reconciliation contract implementation; required before any real account query, real broker snapshot pull, real broker lake write, old report overwrite, real order/cancel, or simulation/live run"
  reason: "CR015-S03/S05 与 CR016-S01 均已 CP7 PASS / verified；CP5 已 approved；当前无 trading/reconciliation.py、trading/broker_lake.py 或 trading/oms.py 文件冲突，可进入 fixture-only reconciliation contract 实现。任何真实 snapshot/account/report write/run 操作仍需后续 per-run authorization。"
development_gate:
  implementation_handoff: "process/handoffs/META-DEV-CR016-S02-IMPLEMENT-2026-05-28.md"
  started_at: "2026-05-28T10:18:52+08:00"
  implemented_by: "meta-dev/dev-yang the 2nd"
  agent_id: "019e6c5e-da6a-71c2-a7ef-71f49245c2e7"
  agent_name: "dev-yang the 2nd"
  dispatch: "multi_agent_v1.spawn_agent"
validation_gate:
  cp7_result: "process/checks/CP7-CR016-S02-reconciliation-service-and-reports-VERIFICATION-DONE.md"
  status: "PASS"
  verified_at: "2026-05-28T10:37:45+08:00"
  verified_by: "meta-qa/qa-cao the 2nd"
  agent_id: "019e6c6b-0c7e-7183-988f-251715d88a47"
  agent_name: "qa-cao the 2nd"
  test_result: "38 passed in 0.19s"
  security_risk_count: 0
  safety_counters_zero: true
created_at: "2026-05-28"
updated_at: "2026-05-28T10:37:45+08:00"
change_id: "CR-016"
---

# CR016-S02：盘前 / 盘中 / 盘后 reconciliation 服务与报告

## 目标

定义 reconciliation 服务与报告合同，覆盖委托、成交、持仓、资产、现金和 broker lake facts 差异；超阈值进入 manual_review 或 kill switch。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-11 |
| 需求 | REQ-116、REQ-117、REQ-121 |
| HLD | `process/HLD-QMT-TRADING.md` §7.2、§8 |
| ADR | ADR-060 |

## 开发上下文（dev_context）

**背景说明**：对账是 live_readonly、小资金和恢复的前置。该 Story 只使用 mock / dry-run broker facts 或后续授权的脱敏 snapshot，不主动查询真实账户。

**输入文件**：CR015-S03 OMS state、CR015-S05 broker lake schema、CR016-S01 stage gate。

**输出文件**：`trading/reconciliation.py`、`tests/test_cr016_reconciliation_service_reports.py`；共享 `trading/broker_lake.py`、`trading/oms.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| reconcile | phase、local state、broker facts、thresholds | reconciliation report | facts 缺失时 required_missing |
| threshold evaluator | diff rows、threshold config | pass / warn / manual_review / kill_switch | 超阈值不得自动继续 |
| report writer contract | reconciliation result | versioned report candidate | 不覆盖旧报告 |

**设计约束**：不查询真实账户；真实 broker snapshot 只由后续授权输入提供；报告不得包含敏感值。

**命名规范**：`recon_phase=pre_market|intraday|post_market`、`diff_type`、`threshold`、`owner`、`action`、`status`。

**平台目标**：QMT simulation/live ops reconciliation。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR015-S03 | runtime | OMS state contract 可引用 | dev 等 CR015 verified | 本地状态源 |
| CR015-S05 | runtime | broker lake schema 可引用 | dev 等 CR015 verified | broker facts 源 |
| CR016-S01 | contract | stage gate 状态可引用 | 同批可设计，开发默认串行 | 对账进入 gate |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR016-S02-T1 | 创建 | `trading/reconciliation.py` | 定义对账输入、阈值、报告和状态 |
| CR016-S02-T2 | 创建 | `tests/test_cr016_reconciliation_service_reports.py` | 覆盖三阶段、阈值、manual_review、kill switch trigger |
| CR016-S02-T3 | 修改 | `trading/broker_lake.py` | 按 LLD 暴露对账事件 schema |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr016_reconciliation_service_reports.py`。

**验证方式**：fixture reconciliation；不真实查询。

**依赖环境**：Python 3.11、uv、pytest。

**关键验证场景**：盘前、盘中、盘后均可输出报告；超阈值进入 manual_review；缺 facts required_missing；报告不覆盖旧基线。

## 量化验收标准（acceptance_criteria）

- [ ] reconciliation 覆盖 pre_market、intraday、post_market 3 个阶段。
- [ ] report 字段覆盖 broker snapshot ref、local state ref、diff、threshold、owner、action、status。
- [ ] 超阈值后继续下单 allowed 次数为 0。
- [ ] 默认验证 real_order_call、real_cancel_call、account_write_call、credential_read 均为 0。

## 阻塞说明

当前为 later-gated：真实 snapshot / 真实报告写入必须后续授权；CP5 前不得实现。
