---
story_id: "CR030-S01-external-reference-matrix-and-loop-contract"
title: "外部项目矩阵与多因子闭环总合同"
story_slug: "external-reference-matrix-and-loop-contract"
status: "verified"
priority: "P0"
wave: "CR030-W1-CONTRACT-GOVERNANCE"
depends_on: []
dependency_type: []
cp5_batch: "CR030-MULTIFACTOR-RESEARCH-LOOP-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "docs/CR030-MULTIFACTOR-REFERENCE-MATRIX.md"
    - "tests/test_cr030_external_reference_guardrails.py"
  shared:
    - "README.md"
    - "docs/USER-MANUAL.md"
  merge_owner: "CR030-S01-external-reference-matrix-and-loop-contract"
  forbidden:
    - "pyproject.toml"
    - "uv.lock"
    - ".env"
    - "/home/hyde/download/qlib/** source copy"
    - "external project clone/install/run"
    - "source migration or vendoring"
    - "provider fetch"
    - "lake write"
    - "catalog publish"
    - "QMT / simulation / live"
    - "credential files or secret values"
lld_gate:
  required_inputs:
    - "process/HLD.md#35.4"
    - "process/HLD.md#35.5"
    - "process/HLD.md#35.15"
    - "process/ARCHITECTURE-DECISION.md#ADR-079"
    - "process/ARCHITECTURE-DECISION.md#ADR-080"
    - "process/ARCHITECTURE-DECISION.md#ADR-086"
    - "process/stories/CR030-S01-external-reference-matrix-and-loop-contract.md"
  status: "approved"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  dependency_change_allowed: false
  external_project_run_allowed: false
  credential_read_allowed: false
  qmt_operation_allowed: false
task_count: 5
created_at: "2026-06-03T08:30:00+08:00"
updated_at: "2026-06-03T09:17:11+08:00"
change_id: "CR-030"
---

# CR030-S01：外部项目矩阵与多因子闭环总合同

## 目标

冻结 CR-030 的外部项目借鉴矩阵、自有多因子研究闭环主线、CR-026 Qlib runner 后置条件和全局不授权边界。该 Story 的 LLD 已通过 CP5，可作为 CR-030 story-execution 的第一批受控实现入口。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-20、UC-21、TS-030-01、TS-030-02、TS-030-09、TS-030-10 |
| 需求 | REQ-174、REQ-175、REQ-182、REQ-184、REQ-185 |
| HLD | `process/HLD.md` §35.4、§35.5、§35.15 |
| ADR | ADR-079、ADR-080、ADR-086 |

## 开发上下文（dev_context）

**背景说明**：CR-030 需要借鉴 Qlib、Alphalens、vectorbt、PyBroker、bt、Zipline Reloaded、QuantConnect LEAN、RQAlpha、vn.py / vnpy.alpha、Backtrader 等项目，但不能让任何外部项目成为本项目默认事实源、runner、provider、optimizer 或 report truth。

**输入文件**：`process/HLD.md` §35、`process/research/CR030-MULTIFACTOR-FRAMEWORK-REFERENCE-ANALYSIS-2026-06-03.md`、`checkpoints/CP3-CR030-HLD-REVIEW.md`、本 Story 卡片。

**输出文件**：`docs/CR030-MULTIFACTOR-REFERENCE-MATRIX.md`、`tests/test_cr030_external_reference_guardrails.py`。

**接口约定**：

| 合同项 | 要求 |
|---|---|
| reference matrix | 每个项目包含 license、dependency、provider/runtime boundary、可借鉴点、不可采用点、recommendation、切换条件 |
| classification | 只允许 `reference_only`、`optional_spike`、`exclude`、`forbidden_migration` 或组合分类 |
| CR-026 | 只记录 Qlib isolated runner 后置条件，不启动 CR-026 |
| forbidden scan | 外部默认 truth、runtime、provider、源码迁移、依赖变更、真实操作均必须可扫描 |

**设计约束**：不得 clone、install、run 外部项目；不得复制源码、样例、测试或数据；不得修改依赖；不得读取凭据。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| 无 | - | CP3 HLD / ADR 可引用 | CP5 前不得实现 | 本 Story 是 CR-030 的合同治理入口 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `docs/CR030-MULTIFACTOR-REFERENCE-MATRIX.md`、`tests/test_cr030_external_reference_guardrails.py` | 当前 Story 独占 LLD owner |
| shared | `README.md`、`docs/USER-MANUAL.md` | 后续由 S08 汇总合并 |
| forbidden | `pyproject.toml`、`uv.lock`、`.env`、外部源码树、provider/lake/QMT/凭据 | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR030-S01-T1 | 设计 | `docs/CR030-MULTIFACTOR-REFERENCE-MATRIX.md` | 定义 10 类外部项目矩阵和分类理由 |
| CR030-S01-T2 | 设计 | `tests/test_cr030_external_reference_guardrails.py` | 设计 forbidden runtime / source-copy / dependency / truth 声明扫描 |
| CR030-S01-T3 | 约束 | CR-026 route | 写明 Qlib runner 后置条件、启动门槛和不授权项 |
| CR030-S01-T4 | 约束 | dependency boundary | 明确 CP5 前 dependency diff 必须为 0 |
| CR030-S01-T5 | 约束 | no-real-operation | 明确 provider/lake/publish/QMT/simulation/live/credential 计数为 0 |

## 验证上下文（validation_context）

**验证入口**：后续 LLD 可建议 `uv run --python 3.11 pytest -q tests/test_cr030_external_reference_guardrails.py`，但本阶段不执行。

**验证方式**：静态文档扫描、矩阵字段完整性校验、forbidden claim scan。

**依赖环境**：仅使用本仓库文档和 fixture；不得访问外部项目运行时、provider、lake、QMT 或凭据。

**关键验证场景**：

| 场景 | 预期 |
|---|---|
| 10 类外部项目矩阵 | 每项分类、边界、切换条件完整 |
| Qlib runner 请求 | 输出 CR-026 后置条件，不启动 runner |
| 外部项目默认 truth | 扫描命中 0 |
| 源码迁移 / dependency install | 扫描命中 0 |

## 量化验收标准（acceptance_criteria）

- [ ] 外部项目矩阵覆盖 10 类项目，字段覆盖率为 100%。
- [ ] 每个项目至少 1 个 recommendation 和 1 个 when-to-switch 条件。
- [ ] 外部 runtime、provider、default truth、source migration、dependency change 正向授权命中次数为 0。
- [ ] CR-026 保持后续 Spike candidate，不并行启动。
- [ ] provider fetch、lake write、catalog publish、QMT / simulation / live、credential read 均为 0。

## 阻塞说明

CP5 全量 LLD 确认前，本 Story 不得进入实现；任何外部运行、源码迁移、依赖变更或真实操作请求都必须由 meta-po 另起 CR / Spike 并重新发起人工确认。
