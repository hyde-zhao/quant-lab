---
story_id: "CR018-S09-qmt-simulation-admission-boundary-after-data-lake"
title: "QMT admission 后置边界"
story_slug: "qmt-simulation-admission-boundary-after-data-lake"
status: "lld-approved-later-gated"
priority: "P0"
wave: "CR018-W4-RERUN-QMT-ADMISSION"
depends_on:
  - "CR018-S08-production-current-truth-research-rerun"
  - "CR015-S07-docs-and-foundation-runbook-boundary"
  - "CR016-S04-simulation-live-runbook-and-approval-gates"
dependency_type:
  - upstream: "CR018-S08-production-current-truth-research-rerun"
    type: "runtime"
  - upstream: "CR015-S07-docs-and-foundation-runbook-boundary"
    type: "runtime"
  - upstream: "CR016-S04-simulation-live-runbook-and-approval-gates"
    type: "runtime"
cp5_batch: "CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A"
implementation_allowed: false
file_ownership:
  primary:
    - "tests/test_cr018_qmt_admission_after_data_lake.py"
  shared:
    - "trading/stage_gate.py"
    - "trading/live_admission.py"
    - "docs/QMT-SIMULATION-LIVE-RUNBOOK.md"
  merge_owner: "CR018-S09-qmt-simulation-admission-boundary-after-data-lake"
  forbidden:
    - "real QMT startup"
    - "real broker order or cancel"
    - "account query"
    - "account write"
    - "small_live or scale_up unlock"
    - "pyproject.toml"
    - "uv.lock"
    - ".env"
    - "credential files or secret values"
lld_gate:
  required_inputs:
    - "process/HLD.md#32"
    - "process/HLD-DATA-LAKE.md#19.13"
    - "process/ARCHITECTURE-DECISION.md#ADR-066"
    - "process/stories/CR018-S09-qmt-simulation-admission-boundary-after-data-lake.md"
  status: "confirmed"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: false
  file_conflict_free: false
  implementation_allowed: false
  qmt_operation_allowed: false
  requires_research_rerun_pass: true
  requires_per_run_authorization: true
  later_gated_real_operation: true
created_at: "2026-05-29"
updated_at: "2026-05-29T08:25:12+08:00"
change_id: "CR-018"
---

# CR018-S09：QMT admission 后置边界

## 目标

将 QMT simulation、live_readonly、small_live、scale_up 的准入改为消费 S08 production rerun PASS 与 release readiness。该 Story 只定义 admission boundary 和 blocked reason，不启动真实 QMT。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-14 |
| 需求 | REQ-123、REQ-134、REQ-137 |
| HLD | `process/HLD.md` §32；`process/HLD-DATA-LAKE.md` §19.13 |
| ADR | ADR-066 |

## 开发上下文（dev_context）

**背景说明**：用户已明确数据湖 production 级优先于 QMT 模拟盘。CR015/CR016/CR017 的 QMT foundation 只能作为技术前置，不能替代 S08 production research rerun PASS。S09 负责把 QMT admission 明确后置。

**输入文件**：S08 rerun evidence contract、CR015/CR016/CR017 foundation 文档、CR018 HLD / ADR、本 Story 卡片。

**输出文件**：`tests/test_cr018_qmt_admission_after_data_lake.py`；共享修改 `trading/stage_gate.py`、`trading/live_admission.py`、`docs/QMT-SIMULATION-LIVE-RUNBOOK.md`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| QMT admission gate | release_id、S08 status、runbook readiness、authorization | stage allowed / blocked reason | S08 未 PASS 必须 blocked |
| stage boundary | requested stage | simulation/live_readonly/small_live/scale_up gate | small_live/scale_up 仍 later-gated |
| QMT no-op guard | adapter call intent | forbidden operation evidence | 不启动 QMT、不发单、不撤单、不查账户 |

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR018-S08 | runtime | LLD 可先定义 blocked path | 开发和任何 admission 解锁需 S08 PASS | production rerun 是硬前置 |
| CR015-S07 | runtime | 可读取 foundation runbook boundary | 不替代 S08 PASS | QMT 技术文档输入 |
| CR016-S04 | runtime | 可读取 simulation/live runbook gate | 不替代 S08 PASS | stage gate 文档输入 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `tests/test_cr018_qmt_admission_after_data_lake.py` | 当前 Story 独占 |
| shared | `trading/stage_gate.py`、`trading/live_admission.py`、`docs/QMT-SIMULATION-LIVE-RUNBOOK.md` | 与 CR015/CR016 共享，开发需串行 |
| forbidden | 真实 QMT 启动、发单、撤单、账户查询、小实盘/放大解锁 | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR018-S09-T1 | 修改 | `trading/stage_gate.py` | 增加 S08 PASS 和 release readiness admission gate |
| CR018-S09-T2 | 修改 | `trading/live_admission.py` | 输出 simulation/live_readonly/small_live/scale_up blocked reason |
| CR018-S09-T3 | 修改 | `docs/QMT-SIMULATION-LIVE-RUNBOOK.md` | 写入数据湖 publish + rerun PASS 前置 |
| CR018-S09-T4 | 创建 | `tests/test_cr018_qmt_admission_after_data_lake.py` | 验证 S08 未 PASS 时所有 QMT stage blocked |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr018_qmt_admission_after_data_lake.py`。

**验证方式**：fixture-only gate test；不需要 QMT 环境。

**关键验证场景**：S08 未 PASS 时 simulation/live_readonly/small_live/scale_up 均 blocked；小实盘和 scale_up 保持 later-gated；adapter calls=0。

## 量化验收标准（acceptance_criteria）

- [ ] S08 未 PASS 时 QMT stage allowed 次数为 0。
- [ ] simulation/live_readonly/small_live/scale_up 均输出 blocked reason。
- [ ] real_qmt_startup、order、cancel、account_query、account_write 计数均为 0。
- [ ] small_live / scale_up 解锁次数为 0。

## 阻塞说明

CP5 已获批；即便后续实现，本 Story 也不授权真实 QMT 操作。真实 QMT simulation 必须在数据湖 publish + S08 production rerun PASS + per-run authorization 后另行进入。
