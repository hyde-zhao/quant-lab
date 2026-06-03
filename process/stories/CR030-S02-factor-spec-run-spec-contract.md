---
story_id: "CR030-S02-factor-spec-run-spec-contract"
title: "FactorSpec / FactorRunSpec 契约"
story_slug: "factor-spec-run-spec-contract"
status: "verified"
priority: "P0"
wave: "CR030-W1-CONTRACT-GOVERNANCE"
depends_on:
  - "CR030-S01-external-reference-matrix-and-loop-contract"
dependency_type:
  - upstream: "CR030-S01-external-reference-matrix-and-loop-contract"
    type: "reference-boundary-contract"
cp5_batch: "CR030-MULTIFACTOR-RESEARCH-LOOP-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "engine/multifactor_contracts.py"
    - "tests/test_cr030_factor_spec_run_spec_contract.py"
  shared:
    - "engine/research_dataset.py"
    - "experiments/run_experiment_17_21_factor_suite.py"
  merge_owner: "CR030-S02-factor-spec-run-spec-contract"
  forbidden:
    - "external object as internal truth"
    - "Qlib qrun/provider_uri"
    - "pyproject.toml"
    - "uv.lock"
    - ".env"
    - "credential files or secret values"
lld_gate:
  required_inputs:
    - "process/HLD.md#35.6"
    - "process/HLD.md#35.7"
    - "process/ARCHITECTURE-DECISION.md#ADR-081"
    - "process/stories/CR030-S02-factor-spec-run-spec-contract.md"
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
updated_at: "2026-06-03T09:37:08+08:00"
change_id: "CR-030"
---

# CR030-S02：FactorSpec / FactorRunSpec 契约

## 目标

冻结 `FactorSpec` 与 `FactorRunSpec` 的字段、校验、错误码、基线复用和外部对象映射边界。该 Story 不实现 schema 类，只为 LLD 提供可执行合同。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-20、UC-22、TS-030-03 |
| 需求 | REQ-176、REQ-183、REQ-185 |
| HLD | `process/HLD.md` §35.6、§35.7 |
| ADR | ADR-081 |

## 开发上下文（dev_context）

**背景说明**：实验 17-21 的探索性因子定义需要升级为可复查、可复跑、可组合的合同，但不能直接采用 Qlib Alpha、Alphalens factor_data、Zipline Pipeline 或 LEAN Alpha Model 作为内部 truth。

**输入文件**：CR-030 HLD / ADR、`CR030-S01` reference matrix、实验 17-21 因子定义基线、`research_input_v1` 相关合同、本 Story 卡片。

**输出文件**：`engine/multifactor_contracts.py`、`tests/test_cr030_factor_spec_run_spec_contract.py`。

**接口约定**：

| 合同项 | 要求 |
|---|---|
| FactorSpec | `factor_id`、`name`、`version`、`direction`、`input_fields`、`window`、`params`、`preprocessing`、`universe`、`availability_policy`、`data_lineage`、`blocked_claims` |
| FactorRunSpec | `run_id`、factor id/version、date range、dataset release、benchmark、cost config、seed、code version、config hash、output root、failure policy |
| 校验输出 | structured blocked reason，不抛裸异常 |
| 外部映射 | 只 cross-check 字段，不替换内部对象 |

**设计约束**：不得实现 Qlib qrun / provider_uri；不得改依赖；不得从零绕开现有基线；不得读取凭据。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR030-S01 | reference-boundary-contract | 外部对象只能 cross-check | S01 合同冻结后才能实现 | 避免外部对象变成 internal truth |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `engine/multifactor_contracts.py`、`tests/test_cr030_factor_spec_run_spec_contract.py` | 当前 Story 独占 |
| shared | `engine/research_dataset.py`、`experiments/run_experiment_17_21_factor_suite.py` | 只允许按 LLD 引用或最小适配 |
| forbidden | `pyproject.toml`、`uv.lock`、`.env`、Qlib runtime/provider | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR030-S02-T1 | 设计 | `engine/multifactor_contracts.py` | 定义 FactorSpec / FactorRunSpec 数据合同和错误码 |
| CR030-S02-T2 | 设计 | `tests/test_cr030_factor_spec_run_spec_contract.py` | 设计必填字段、config hash、lineage 和外部对象不接管测试 |
| CR030-S02-T3 | 兼容 | `experiments/run_experiment_17_21_factor_suite.py` | 在 LLD 中说明现有 FactorDefinition 映射方式 |
| CR030-S02-T4 | 约束 | `engine/research_dataset.py` | 在 LLD 中说明 `research_input_v1` 只读消费边界 |
| CR030-S02-T5 | 约束 | failure policy | 定义 blocked reason 和 fail-closed 入口 |

## 验证上下文（validation_context）

**验证入口**：后续 LLD 可建议 `uv run --python 3.11 pytest -q tests/test_cr030_factor_spec_run_spec_contract.py`，但本阶段不执行。

**验证方式**：合同字段测试、缺字段 fail-closed 测试、外部对象 truth 替代禁止扫描。

**依赖环境**：本地 fixture；不得运行 Qlib / Alphalens / Zipline / LEAN。

**关键验证场景**：

| 场景 | 预期 |
|---|---|
| 合法 FactorSpec / FactorRunSpec | 字段完整，可生成 config hash |
| 缺 direction / lineage / dataset release | 返回 structured blocked reason |
| 外部对象直接进入内部 truth | 测试失败 |
| CP5 未确认 | implementation_allowed=false |

## 量化验收标准（acceptance_criteria）

- [ ] `FactorSpec` / `FactorRunSpec` P0 字段覆盖率为 100%。
- [ ] 缺必填字段、方向未知、lineage 不完整、config_hash 缺失均返回 structured blocked reason。
- [ ] 外部对象作为 internal truth 次数为 0。
- [ ] `pyproject.toml` / `uv.lock` 修改次数为 0。
- [ ] Qlib qrun/provider_uri、provider fetch、credential read、QMT 调用均为 0。

## 阻塞说明

本 Story 依赖 S01 的外部项目边界。CP5 全量 LLD 确认前不得实现；若需要新增字段，LLD 必须说明相对现有实验和 `research_input_v1` 的增量理由。
