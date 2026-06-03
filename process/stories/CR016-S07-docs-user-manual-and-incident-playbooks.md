---
story_id: "CR016-S07-docs-user-manual-and-incident-playbooks"
title: "用户文档与 incident playbooks"
story_slug: "docs-user-manual-and-incident-playbooks"
status: "verified"
priority: "P1"
wave: "CR016-W2-LIVE-SCALE-DOCS-GATED"
depends_on:
  - "CR016-S04-simulation-live-runbook-and-approval-gates"
  - "CR016-S05-live-readonly-and-small-live-admission"
  - "CR016-S06-scale-up-and-research-maturity-gates"
dependency_type:
  - upstream: "CR016-S04-simulation-live-runbook-and-approval-gates"
    type: "contract"
  - upstream: "CR016-S05-live-readonly-and-small-live-admission"
    type: "contract"
  - upstream: "CR016-S06-scale-up-and-research-maturity-gates"
    type: "contract"
cp5_batch: "CR016-QMT-ACTIVATION-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "docs/QMT-INCIDENT-PLAYBOOK.md"
    - "tests/test_cr016_docs_incident_playbooks.py"
  shared:
    - "README.md"
    - "docs/USER-MANUAL.md"
    - "docs/QMT-SIMULATION-LIVE-RUNBOOK.md"
  merge_owner: "CR016-S07-docs-user-manual-and-incident-playbooks"
  forbidden:
    - "pyproject.toml"
    - "uv.lock"
    - "credential files or secret values"
    - "real broker operation"
lld_gate:
  required_inputs:
    - "process/HLD-QMT-TRADING.md#11"
    - "process/HLD-QMT-TRADING.md#15"
    - "process/stories/CR016-S07-docs-user-manual-and-incident-playbooks.md"
  status: "approved"
  cp5_batch: "CR016-QMT-ACTIVATION-BATCH-A"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  status: "ready-for-verification"
  reason: "CR016-S04 已 verified；CR016-S05/S06 仅作为 CP5 approved later-gated contract 输入且 implementation_allowed=false，不进入实现。当前无 README、USER-MANUAL、QMT-SIMULATION-LIVE-RUNBOOK、QMT-INCIDENT-PLAYBOOK 或 test 文件冲突；S07 只允许文档 / 静态测试实现。"
development_gate:
  implementation_handoff: "process/handoffs/META-DEV-CR016-S07-IMPLEMENT-2026-05-28.md"
  started_at: "2026-05-28T11:47:11+08:00"
  completed_at: "2026-05-28T11:52:52+08:00"
  closed_at: "2026-05-28T11:56:41+08:00"
  implemented_by: "meta-dev/dev-zhu the 2nd"
  agent_id: "019e6cb1-70eb-72c2-bdf7-94a59009789f"
  agent_name: "dev-zhu the 2nd"
  dispatch: "multi_agent_v1.spawn_agent"
  cp6_result: "process/checks/CP6-CR016-S07-docs-user-manual-and-incident-playbooks-CODING-DONE.md"
  cp6_status: "PASS"
validation_gate:
  cp7: "process/checks/CP7-CR016-S07-docs-user-manual-and-incident-playbooks-VERIFICATION-DONE.md"
  status: "PASS"
  verified_at: "2026-05-28T12:04:05+08:00"
  verified_by: "meta-qa/qa-he the 2nd"
  agent_id: "019e6cbc-5bed-7273-87a7-a6d11a36ac88"
  agent_name: "qa-he the 2nd"
  dispatch: "multi_agent_v1.spawn_agent"
  completed_at: "2026-05-28T12:01:00+08:00"
  closed_at: "2026-05-28T12:04:05+08:00"
  test_result: "29 passed in 0.16s"
  safety_counters_zero: true
created_at: "2026-05-28"
updated_at: "2026-05-28T12:04:05+08:00"
change_id: "CR-016"
---

# CR016-S07：用户文档与 incident playbooks

## 目标

补齐 CR-016 面向用户的 staged activation、故障处理、暂停 / 恢复、人工接管和 incident playbook 文档，同时保持真实操作不授权的边界。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-11 |
| 需求 | REQ-113、REQ-114、REQ-116、REQ-117、REQ-119、REQ-120、REQ-121 |
| HLD | `process/HLD-QMT-TRADING.md` §11、§15 |
| ADR | ADR-059、ADR-060、ADR-061 |

## 开发上下文（dev_context）

**背景说明**：CR-016 的实用价值取决于用户能否按阶段执行、识别阻断、处理事故并恢复。文档必须清楚区分 simulation、live_readonly、small_live、scale_up 与授权边界。

**输入文件**：CR016-S04/S05/S06、HLD-QMT-TRADING。

**输出文件**：`docs/QMT-INCIDENT-PLAYBOOK.md`、`tests/test_cr016_docs_incident_playbooks.py`；共享 `README.md`、`docs/USER-MANUAL.md`、`docs/QMT-SIMULATION-LIVE-RUNBOOK.md`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| incident playbook | incident type、stage | action list、owner、recovery gate | 不执行真实动作 |
| user manual section | stage gates、blocked claims | user-facing instructions | 不包含敏感值 |
| docs guard | markdown files | forbidden claim scan result | 真实执行能力不得被误声明 |

**设计约束**：本 Story 只改用户文档 / playbook；不得修改业务代码，除非 LLD 明确需要文档测试 helper。不得写真实运行报告。

**命名规范**：incident 类型使用 `heartbeat_fail`、`risk_blocked`、`recon_diff`、`manual_trigger`、`recovery_required`。

**平台目标**：用户文档与运行手册。

### 依赖与并行门控

S04/S05/S06 合同冻结后可写 LLD；开发需与 CR015-S07、CR017-S06 文档共享文件串行合并。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR016-S07-T1 | 创建 | `docs/QMT-INCIDENT-PLAYBOOK.md` | 写 incident 类型、处理步骤、owner 和恢复 gate |
| CR016-S07-T2 | 修改 | `README.md` / `docs/USER-MANUAL.md` | 写 staged activation 与真实操作授权边界 |
| CR016-S07-T3 | 创建 | `tests/test_cr016_docs_incident_playbooks.py` | 验证文档章节、blocked claims 和无敏感值 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr016_docs_incident_playbooks.py`。

**验证方式**：文档静态检查。

**依赖环境**：Python 3.11、uv、pytest。

**关键验证场景**：5 阶段说明完整；incident 类型完整；recovery gate 有人工接管记录要求；文档无误授权。

## 量化验收标准（acceptance_criteria）

- [x] 文档覆盖 shadow、simulation、live_readonly、small_live、scale_up 5 个阶段。
- [x] incident playbook 覆盖 heartbeat fail、risk blocked、recon diff、manual trigger、recovery required 5 类事件。
- [x] 文档中无授权真实操作的默认声明，真实操作 allowed 次数为 0。
- [x] 默认验证 real_order_call、real_cancel_call、account_write_call、credential_read 均为 0。

## 阻塞说明

已完成 CP7 验证并收敛为 `verified`。文档完成、CP6 / CP7 PASS 或 Story verified 均不授权真实运行；simulation、live_readonly、small_live、scale_up 和任何真实 broker 操作仍需后续 per-run authorization。
