---
story_id: "CR030-S08-safety-docs-and-follow-up-boundary"
title: "安全验证、文档与后续 Spike 边界"
story_slug: "safety-docs-and-follow-up-boundary"
status: "verified"
priority: "P1"
wave: "CR030-W4-ADMISSION-SAFETY-DOCS"
depends_on:
  - "CR030-S01-external-reference-matrix-and-loop-contract"
  - "CR030-S02-factor-spec-run-spec-contract"
  - "CR030-S03-factor-panel-label-window-fail-closed"
  - "CR030-S04-factor-evaluation-report"
  - "CR030-S05-multifactor-combiner-portfolio-plan"
  - "CR030-S06-experiment-manifest-report-catalog"
  - "CR030-S07-strategy-admission-package-handoff"
dependency_type:
  - upstream: "CR030-S01-external-reference-matrix-and-loop-contract"
    type: "documentation-merge"
  - upstream: "CR030-S02-factor-spec-run-spec-contract"
    type: "documentation-merge"
  - upstream: "CR030-S03-factor-panel-label-window-fail-closed"
    type: "safety-input-contract"
  - upstream: "CR030-S04-factor-evaluation-report"
    type: "safety-input-contract"
  - upstream: "CR030-S05-multifactor-combiner-portfolio-plan"
    type: "safety-input-contract"
  - upstream: "CR030-S06-experiment-manifest-report-catalog"
    type: "documentation-merge"
  - upstream: "CR030-S07-strategy-admission-package-handoff"
    type: "qmt-boundary-contract"
cp5_batch: "CR030-MULTIFACTOR-RESEARCH-LOOP-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "docs/CR030-MULTIFACTOR-RESEARCH-LOOP.md"
    - "tests/test_cr030_no_real_operation_safety.py"
  shared:
    - "README.md"
    - "docs/USER-MANUAL.md"
    - "docs/CR030-MULTIFACTOR-REFERENCE-MATRIX.md"
  merge_owner: "CR030-S08-safety-docs-and-follow-up-boundary"
  forbidden:
    - "runtime authorization"
    - "external project run instructions as default"
    - "dependency install instructions as approved"
    - "provider fetch"
    - "lake write"
    - "catalog publish"
    - "QMT-ready claim"
    - "simulation-ready claim"
    - "live-ready claim"
    - "credential examples"
lld_gate:
  required_inputs:
    - "process/HLD.md#35.14"
    - "process/HLD.md#35.15"
    - "process/HLD.md#35.17"
    - "process/ARCHITECTURE-DECISION.md#ADR-079..ADR-086"
    - "process/stories/CR030-S08-safety-docs-and-follow-up-boundary.md"
  status: "approved"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  dependency_change_allowed: false
  external_project_run_allowed: false
  provider_fetch_allowed: false
  lake_write_allowed: false
  qmt_operation_allowed: false
  credential_read_allowed: false
task_count: 5
created_at: "2026-06-03T08:30:00+08:00"
updated_at: "2026-06-03T12:01:20+08:00"
change_id: "CR-030"
dependency_unlocked_by:
  - "CR030-S07-strategy-admission-package-handoff"
dependency_unlocked_at: "2026-06-03T11:12:22+08:00"
dev_dispatch:
  mode: "spawn_agent"
  agent_id: "019e8b93-eb3b-7d01-ae25-384a76e4713f"
  agent_name: "dev-you the 2nd"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-06-03T11:43:14+08:00"
  completed_at: "2026-06-03T11:48:38+08:00"
  closed_at: "2026-06-03T11:52:27+08:00"
  cp6_checkpoint: "process/checks/CP6-CR030-S08-safety-docs-and-follow-up-boundary-CODING-DONE.md"
  handoff_path: "process/handoffs/META-DEV-CR030-S08-IMPLEMENT-2026-06-03.md"
  cp6_status: "PASS"
previous_failed_dispatches:
  - mode: "spawn_agent"
    agent_id: "019e8b7d-bde1-74e1-b78c-d78d5ba3e12e"
    agent_name: "dev-zhu the 2nd"
    tool_name: "multi_agent_v1.spawn_agent"
    spawned_at: "2026-06-03T11:19:00+08:00"
    closed_at: "2026-06-03T11:42:39+08:00"
    status: "errored-usage-limit"
    evidence_note: "平台 usage limit 中断；不作为 CP6 完成证据。"
qa_dispatch:
  mode: "spawn_agent"
  agent_id: "019e8b9f-be55-7a20-9a87-611747604421"
  agent_name: "qa-shi the 2nd"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-06-03T11:55:29+08:00"
  completed_at: "2026-06-03T11:57:48+08:00"
  closed_at: "2026-06-03T12:01:20+08:00"
  cp7_checkpoint: "process/checks/CP7-CR030-S08-safety-docs-and-follow-up-boundary-VERIFICATION-DONE.md"
  handoff_path: "process/handoffs/META-QA-CR030-S08-CP7-VERIFY-2026-06-03.md"
  cp7_status: "PASS"
---

# CR030-S08：安全验证、文档与后续 Spike 边界

## 目标

汇总 CR-030 no-real-operation safety、external source-copy / runtime forbidden scan、CR-026 / optimizer / ML / vectorbt / PyBroker / RQAlpha / vn.py 后续 Spike 条件和用户文档边界。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-20、UC-21、UC-27、TS-030-08、TS-030-09、TS-030-10 |
| 需求 | REQ-175、REQ-182、REQ-184、REQ-185 |
| HLD | `process/HLD.md` §35.14、§35.15、§35.17 |
| ADR | ADR-079 至 ADR-086 |

## 开发上下文（dev_context）

**背景说明**：CR-030 会产出多因子研究合同、报告和准入包，但不授权外部运行、依赖变更、provider/lake/publish、QMT/simulation/live 或凭据读取。文档和安全测试必须防止用户把研究准入包误解为真实交易授权。

**输入文件**：CR030-S01..S07 Story 合同、HLD §35、ADR-079..086、CP3 Decision Brief、本 Story 卡片。

**输出文件**：`docs/CR030-MULTIFACTOR-RESEARCH-LOOP.md`、共享 `README.md`、`docs/USER-MANUAL.md`、`tests/test_cr030_no_real_operation_safety.py`。

**接口约定**：

| 文档 / 安全对象 | 必须表达 |
|---|---|
| no-real-operation | 实现、依赖、外部运行、source copy、provider、lake、publish、QMT、credential 均未授权 |
| CR-026 | Qlib isolated runner 后置条件，不能并行启动 |
| optimizer / ML | 后续 Spike 条件，P0 不启用 |
| QMT route | CR-020..CR-024 独立授权，`StrategyAdmissionPackage` 不是 QMT-ready |
| forbidden scan | QMT-ready / simulation-ready / live-ready / production truth 正向误导命中 0 |

**设计约束**：不得写默认外部项目运行命令、依赖安装已授权说明、真实凭据示例、真实 provider / lake / publish / QMT 操作步骤。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR030-S01..S07 | documentation / safety input | 全部 Story 合同冻结 | CP5 全量确认后才能实现 | S08 负责收敛安全与文档边界 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `docs/CR030-MULTIFACTOR-RESEARCH-LOOP.md`、`tests/test_cr030_no_real_operation_safety.py` | 当前 Story 独占 |
| shared | `README.md`、`docs/USER-MANUAL.md`、`docs/CR030-MULTIFACTOR-REFERENCE-MATRIX.md` | 当前 Story 为 CR-030 文档 merge owner |
| forbidden | runtime authorization、外部运行默认说明、依赖安装授权、QMT-ready claim、凭据示例 | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR030-S08-T1 | 设计 | `docs/CR030-MULTIFACTOR-RESEARCH-LOOP.md` | 定义用户可读研究闭环、合同、准入包和不授权边界 |
| CR030-S08-T2 | 设计 | `tests/test_cr030_no_real_operation_safety.py` | 设计 forbidden runtime / source-copy / QMT-ready claim scan |
| CR030-S08-T3 | 设计 | `README.md` | 设计最小入口说明，明确 CR-030 不授权真实运行 |
| CR030-S08-T4 | 设计 | `docs/USER-MANUAL.md` | 设计用户手册增量和故障说明 |
| CR030-S08-T5 | 约束 | follow-up Spike | 记录 CR-026、optimizer、ML、vectorbt、PyBroker、RQAlpha、vn.py 后续条件 |

## 验证上下文（validation_context）

**验证入口**：后续 LLD 可建议 `uv run --python 3.11 pytest -q tests/test_cr030_no_real_operation_safety.py`，但本阶段不执行。

**验证方式**：文档静态扫描、forbidden claim scan、no-real-operation 计数检查。

**依赖环境**：本地文档和 fixture；不得启动外部项目、QMT、provider、lake 或读取凭据。

**关键验证场景**：

| 场景 | 预期 |
|---|---|
| 文档覆盖 CP3 DQ | DQ-CP3-CR030-01..07 全部可追溯 |
| 文档覆盖 Story 边界 | CR030-S01..S08 全部可追溯 |
| CR-026 / optimizer 请求 | 后置 Spike，不进入 P0 |
| QMT-ready / simulation-ready / live-ready 声明 | 语义匹配次数为 0 |

## 量化验收标准（acceptance_criteria）

- [ ] 文档覆盖 7 个 CP3 DQ 和 8 个 CR-030 Story 边界。
- [ ] CR-026 后置条件至少 1 处可追溯，且不启动 CR-026。
- [ ] no-real-operation 表覆盖实现、依赖、外部运行、source copy、provider、lake、publish、QMT/simulation/live、credential。
- [ ] “CR-030 verified 授权真实操作 / QMT-ready / simulation-ready / live-ready / production truth”语义匹配次数为 0。
- [ ] dependency change、external project run、provider fetch、lake write、catalog publish、QMT operation、credential read 均为 0。

## 阻塞说明

本 Story 必须等待 S01..S07 合同冻结和 CP5 全量 LLD 确认。文档不得被视为真实运行授权；任何后续运行、依赖或 QMT 请求必须由 meta-po 另起 CR / Spike。
