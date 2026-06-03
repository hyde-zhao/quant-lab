---
story_id: "CR015-S07-docs-and-foundation-runbook-boundary"
title: "foundation 文档与 runbook 边界"
story_slug: "docs-and-foundation-runbook-boundary"
status: "verified"
priority: "P1"
wave: "CR015-W3-SHADOW-RUNBOOK"
depends_on:
  - "CR015-S01-qmt-environment-and-interface-spike"
  - "CR015-S02-qmt-broker-adapter-contract"
  - "CR015-S03-oms-order-state-machine"
  - "CR015-S04-pretrade-risk-gate"
  - "CR015-S05-broker-lake-schema-and-writer"
  - "CR015-S06-target-portfolio-to-order-intent-shadow-mode"
  - "CR017-S06-research-qmt-consumer-docs-and-migration-guide"
dependency_type:
  - upstream: "CR015-S01-qmt-environment-and-interface-spike"
    type: "contract"
  - upstream: "CR015-S02-qmt-broker-adapter-contract"
    type: "contract"
  - upstream: "CR015-S03-oms-order-state-machine"
    type: "contract"
  - upstream: "CR015-S04-pretrade-risk-gate"
    type: "contract"
  - upstream: "CR015-S05-broker-lake-schema-and-writer"
    type: "contract"
  - upstream: "CR015-S06-target-portfolio-to-order-intent-shadow-mode"
    type: "runtime-contract"
  - upstream: "CR017-S06-research-qmt-consumer-docs-and-migration-guide"
    type: "contract"
cp5_batch: "CR015-QMT-FOUNDATION-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "docs/QMT-TRADING-RUNBOOK.md"
    - "tests/test_cr015_foundation_runbook_boundary.py"
  shared:
    - "README.md"
    - "docs/USER-MANUAL.md"
  merge_owner: "CR015-S07-docs-and-foundation-runbook-boundary"
  forbidden:
    - "pyproject.toml"
    - "uv.lock"
    - "credential files or secret values"
    - "real broker operation"
lld_gate:
  required_inputs:
    - "process/HLD-QMT-TRADING.md#11"
    - "process/HLD-DATA-LAKE.md#18"
    - "process/stories/CR015-S07-docs-and-foundation-runbook-boundary.md"
  status: "approved"
  cp5_batch: "CR015-QMT-FOUNDATION-BATCH-A"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  reason: "CR015-S01..S06 与 CR017-S06 均已 CP7 PASS / verified；CP5 已 approved；当前无 dev_running / verify_running 的 README、USER-MANUAL 或 docs/QMT-TRADING-RUNBOOK.md 文件冲突，可进入 foundation runbook 文档实现。"
created_at: "2026-05-28"
updated_at: "2026-05-28T09:54:11+08:00"
development_gate:
  implementation_handoff: "process/handoffs/META-DEV-CR015-S07-IMPLEMENT-2026-05-28.md"
  implementation_started_at: "2026-05-28T09:38:47+08:00"
  implementation_completed_at: "2026-05-28T09:44:33+08:00"
  implemented_by: "meta-dev/dev-kong the 2nd"
  agent_id: "019e6c3b-de29-77c3-92e3-91c9a82a3115"
  agent_name: "dev-kong the 2nd"
  cp6_result: "process/checks/CP6-CR015-S07-docs-and-foundation-runbook-boundary-CODING-DONE.md"
  test_result: "6 passed in 0.04s"
validation_gate:
  cp7_result: "process/checks/CP7-CR015-S07-docs-and-foundation-runbook-boundary-VERIFICATION-DONE.md"
  verified_at: "2026-05-28T09:54:11+08:00"
  verified_by: "meta-qa/qa-zhang the 2nd"
  agent_id: "019e6c45-42f0-7ad2-a5a0-4754f184eee9"
  agent_name: "qa-zhang the 2nd"
  test_result: "6 passed in 0.04s"
change_id: "CR-015"
---

# CR015-S07：foundation 文档与 runbook 边界

## 目标

输出 QMT foundation 的用户文档、运行边界和 runbook 草案，明确 CR-015 只允许 shadow / dry-run / mock，真实模拟盘和实盘激活归 CR-016。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-10、UC-12 |
| 需求 | REQ-105、REQ-110、REQ-111、REQ-120、REQ-121 |
| HLD | `process/HLD-QMT-TRADING.md` §11、§15 |
| ADR | ADR-055、ADR-056、ADR-058、ADR-061 |

## 开发上下文（dev_context）

**背景说明**：用户需要知道 foundation 能做什么、不能做什么、如何从 shadow 进入后续 simulation，以及哪些动作必须等待 CR-016 per-run 授权。

**输入文件**：CR015-S01..S06、CR017-S06、HLD-QMT-TRADING。

**输出文件**：`docs/QMT-TRADING-RUNBOOK.md`、`tests/test_cr015_foundation_runbook_boundary.py`；共享 `README.md`、`docs/USER-MANUAL.md`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| runbook checklist | foundation evidence | setup / shadow / mock checklist | 缺项时 simulation gate blocked |
| boundary docs | story outputs、blocked claims | allowed / forbidden scope | 不展示敏感值 |
| CP handoff summary | CP4/CP5 state | next-stage prerequisites | 不自动进入 CR016 |

**设计约束**：文档不得把 CR-015 写成已支持真实交易；不得解除真实 VWAP、minute、tick、Level2、order-match blocked claim。

**命名规范**：`foundation_mode`、`simulation_prerequisites`、`real_operation_authorization_required`。

**平台目标**：用户文档 / runbook；无安装脚本。

### 依赖与并行门控

上游 CR015-S01..S06 和 CR017-S06 的合同冻结后，方可实现本 Story。LLD 可与 CR016-S01/S04 并行设计，开发不得并行改同一文档段落。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR015-S07-T1 | 创建 | `docs/QMT-TRADING-RUNBOOK.md` | 写 foundation shadow / dry-run / mock 运行边界 |
| CR015-S07-T2 | 修改 | `README.md` / `docs/USER-MANUAL.md` | 写 QMT foundation 限制与 CR016 后续关系 |
| CR015-S07-T3 | 创建 | `tests/test_cr015_foundation_runbook_boundary.py` | 验证文档不声明真实交易或 blocked claim 解除 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr015_foundation_runbook_boundary.py`。

**验证方式**：文档 contract / static check。

**依赖环境**：Python 3.11、uv、pytest。

**关键验证场景**：文档声明 CR-015 不授权真实操作；runbook 包含 simulation 前置项；blocked execution claims 未解除。

## 量化验收标准（acceptance_criteria）

- [ ] runbook 覆盖 setup、shadow、dry-run、mock、handoff to CR016 5 类章节。
- [ ] 文档中真实交易支持声明次数为 0。
- [ ] 真实 VWAP / minute / tick / Level2 / order-match allowed claim 次数为 0。
- [ ] 默认验证 real_order_call、real_cancel_call、account_write_call、credential_read 均为 0。

## 阻塞说明

CP5 前不得实现；CR016 未通过前不得把 runbook 作为 simulation 授权。

## 实现完成记录

| TASK-ID | 状态 | 证据 |
|---|---|---|
| CR015-S07-T1 | DONE | `docs/QMT-TRADING-RUNBOOK.md` 覆盖 setup、shadow、dry-run、mock、handoff to CR016。 |
| CR015-S07-T2 | DONE | `README.md`、`docs/USER-MANUAL.md` 追加 QMT foundation 限制、CR016 后续关系和 blocked claims。 |
| CR015-S07-T3 | DONE | `tests/test_cr015_foundation_runbook_boundary.py` 覆盖文档章节、真实交易声明、微观结构 allowed claim、敏感值输出和安全计数。 |
| CR015-S07-T4 | DONE | 文档明确 CR015 只允许 `shadow` / `dry_run` / `mock`，不授权 simulation、live_readonly、small_live、scale_up、真实 QMT、真实发单、撤单、账户查询、凭据读取、真实 broker lake 写入、真实抓取、真实 lake 写入或 publish。 |
| CR015-S07-T5 | DONE | `process/checks/CP6-CR015-S07-docs-and-foundation-runbook-boundary-CODING-DONE.md` 写入 Agent Dispatch Evidence、LLD consumption、测试结果、safety counters 和 PASS 结论。 |
