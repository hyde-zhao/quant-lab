---
story_id: "CR019-S09-deferred-capability-register"
title: "Backtrader / Qlib / minute / Level2 后置能力 register"
story_slug: "deferred-capability-register"
status: "verified"
priority: "P1"
wave: "CR019-W4-FALLBACK-DEFERRED"
depends_on:
  - "CR019-S01-stage6-admission-gate-package"
  - "CR019-S02-primary-benchmark-dashboard"
dependency_type:
  - upstream: "CR019-S01-stage6-admission-gate-package"
    type: "scope-contract"
  - upstream: "CR019-S02-primary-benchmark-dashboard"
    type: "scope-contract"
cp5_batch: "CR019-STAGE6-QMT-BRIDGE-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "docs/CR019-DEFERRED-CAPABILITIES.md"
    - "tests/test_cr019_deferred_capabilities.py"
  shared:
    - "README.md"
  merge_owner: "CR019-S09-deferred-capability-register"
  forbidden:
    - "new dependency"
    - "Qlib provider_uri"
    - "Level2 entitlement claim"
    - "minute data fetch"
    - "stage6 P0 scope expansion"
lld_gate:
  required_inputs:
    - "process/HLD.md#33.14"
    - "process/HLD.md#33.16"
    - "process/ARCHITECTURE-DECISION.md#ADR-073"
    - "process/stories/CR019-S09-deferred-capability-register.md"
  status: "confirmed"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  credential_read_allowed: false
  qmt_operation_allowed: false
task_count: 3
created_at: "2026-05-30T18:24:00+08:00"
updated_at: "2026-05-31T09:50:40+08:00"
change_id: "CR-019"
dev_ready_at: "2026-05-31T09:23:13+08:00"
dev_ready_reason: "S01/S02 均已 verified；CP5/LLD 已确认，当前无 dev_running 文件冲突；只允许静态 deferred capability register / README 边界实现，不授权新增依赖、Qlib provider、minute/Level2 数据抓取或阶段六 P0 范围扩张。"
dev_handoff: "process/handoffs/META-DEV-CR019-S09-IMPLEMENT-2026-05-31.md"
dev_agent_id: "019e7ba4-f915-7df2-9443-99586f4e7676"
dev_agent_name: "dev-xu"
dev_started_at: "2026-05-31T09:27:52+08:00"
dev_completed_at: "2026-05-31T09:34:30+08:00"
dev_closed_at: "2026-05-31T09:38:44+08:00"
cp6_status: "PASS"
cp6_result: "process/checks/CP6-CR019-S09-deferred-capability-register-CODING-DONE.md"
cp6_completed_at: "2026-05-31T09:34:30+08:00"
ready_for_verification_at: "2026-05-31T09:34:30+08:00"
dev_agent_evidence: "spawn_agent returned agent_id=019e7ba4-f915-7df2-9443-99586f4e7676 nickname=dev-xu; wait_agent returned completed CR019-S09 CP6 PASS; close_agent previous_status returned completed CR019-S09 CP6 PASS"
main_thread_cp6_result: "PASS: py_compile; S09+S01/S02 regression 22 passed in 0.08s; dependency diff empty; cache status empty; focused real-config and enablement scans empty; dangerous scan only README existing uv sync examples; prompt scan empty; diff check PASS"
qa_handoff: "process/handoffs/META-QA-CR019-S09-CP7-VERIFY-2026-05-31.md"
qa_agent_id: "019e7bb2-d91e-7513-8a5e-a16a0e6528c9"
qa_agent_name: "qa-he"
qa_started_at: "2026-05-31T09:43:03+08:00"
qa_completed_at: "2026-05-31T09:45:23+08:00"
qa_closed_at: "2026-05-31T09:50:40+08:00"
cp7_status: "PASS"
cp7_result: "process/checks/CP7-CR019-S09-deferred-capability-register-VERIFICATION-DONE.md"
cp7_completed_at: "2026-05-31T09:45:23+08:00"
verified_at: "2026-05-31T09:50:40+08:00"
qa_agent_evidence: "spawn_agent returned agent_id=019e7bb2-d91e-7513-8a5e-a16a0e6528c9 nickname=qa-he; wait_agent returned completed CR019-S09 CP7 PASS; close_agent previous_status returned completed CR019-S09 CP7 PASS"
main_thread_cp7_result: "PASS: py_compile; S09+S01/S02 regression 22 passed in 0.08s; dependency diff empty; cache status empty; focused real-config and enablement scans empty; dangerous scan only README existing uv sync examples; prompt scan empty; diff check PASS"
---

# CR019-S09：Backtrader / Qlib / minute / Level2 后置能力 register

## 目标

固化 Backtrader W6、Qlib W7、minute Spike、Level2 Spike 的触发条件、阻断声明和后续 CR / CP 入口；确认这些能力不进入阶段六 P0 admission 与 QMT C/S bridge 的默认实现范围。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-15、UC-18 |
| 需求 | REQ-139、REQ-140、REQ-141、REQ-143、REQ-155、REQ-156、REQ-157、REQ-158 |
| HLD | `process/HLD.md` §33.14、§33.16 |
| ADR | ADR-073 |

## 开发上下文（dev_context）

**输入文件**：CR019-S01 admission gate package、CR019-S02 benchmark policy、HLD 后置能力决策、本 Story 卡片。

**输出文件**：`docs/CR019-DEFERRED-CAPABILITIES.md`、`tests/test_cr019_deferred_capabilities.py`；共享 `README.md`。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR019-S01 | scope-contract | admission P0 范围先冻结 | 不把后置能力加入 admission gate | 后置 register 不改变阶段六 P0 |
| CR019-S02 | scope-contract | primary benchmark / 多基准口径先冻结 | 不引入新 benchmark provider | 后置能力触发条件引用 benchmark readiness |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `docs/CR019-DEFERRED-CAPABILITIES.md`、`tests/test_cr019_deferred_capabilities.py` | 当前 Story 独占 |
| shared | `README.md` | merge owner 为当前 Story，S10 文档收敛时串行合并 |
| forbidden | 新增依赖、Qlib provider_uri、Level2 entitlement claim、minute data fetch、阶段六 P0 范围扩张 | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR019-S09-T1 | 创建 | `docs/CR019-DEFERRED-CAPABILITIES.md` | 定义 Backtrader、Qlib、minute、Level2 四类后置能力 register |
| CR019-S09-T2 | 创建 | `tests/test_cr019_deferred_capabilities.py` | 验证四类能力均有触发条件、blocked reason、后续 CR / CP 入口 |
| CR019-S09-T3 | 修改 | `README.md` | 按 LLD 增量记录后置能力非 P0、非默认授权边界 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr019_deferred_capabilities.py`。

**验证方式**：静态文档 / register 测试；不得新增依赖，不得连接 Qlib provider，不得抓 minute / Level2 数据。

## 量化验收标准（acceptance_criteria）

- [ ] Backtrader、Qlib、minute、Level2 四类后置能力均有触发条件、blocked reason、后续 CR / CP 入口。
- [ ] 阶段六 P0 admission / QMT C/S bridge 依赖新增次数为 0。
- [ ] `pyproject.toml` / `uv.lock` 修改次数为 0。
- [ ] Qlib provider_uri、Level2 entitlement claim、minute fetch 真实配置出现次数为 0。

## 阻塞说明

CP5 已通过；仍需等待 S01/S02 合同满足后按 dev_gate 调度，后置能力 register 只用于范围管理，不开启任何新依赖、数据抓取或交易能力。
