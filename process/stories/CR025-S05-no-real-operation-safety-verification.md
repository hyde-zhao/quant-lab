---
story_id: "CR025-S05-no-real-operation-safety-verification"
title: "no-real-operation safety 与验证策略"
story_slug: "no-real-operation-safety-verification"
status: "verified"
priority: "P0"
wave: "CR025-W4-SAFETY-VERIFICATION-DOCS"
depends_on:
  - "CR025-S01-clean-feed-gate-backend-selector"
  - "CR025-S02-semantic-diff-schema-artifact"
  - "CR025-S03-order-intent-draft-qmt-boundary"
  - "CR025-S04-backtrader-module-reference-no-copy-guardrail"
dependency_type:
  - upstream: "CR025-S01-clean-feed-gate-backend-selector"
    type: "safety-input-contract"
  - upstream: "CR025-S02-semantic-diff-schema-artifact"
    type: "schema-contract"
  - upstream: "CR025-S03-order-intent-draft-qmt-boundary"
    type: "qmt-boundary-contract"
  - upstream: "CR025-S04-backtrader-module-reference-no-copy-guardrail"
    type: "license-guardrail"
cp5_batch: "CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "tests/test_cr025_no_real_operation_safety.py"
    - "tests/test_cr025_forbidden_source_copy.py"
    - "tests/test_cr025_schema_contracts.py"
  shared:
    - "engine/backtrader_adapter.py"
    - "engine/semantic_diff.py"
    - "engine/order_intent_draft.py"
  merge_owner: "CR025-S05-no-real-operation-safety-verification"
  forbidden:
    - "tests requiring real Backtrader run"
    - "tests requiring QMT / MiniQMT / XtQuant"
    - "tests requiring provider fetch"
    - "tests requiring lake write"
    - "tests requiring credentials"
lld_gate:
  required_inputs:
    - "process/HLD.md#34.8"
    - "process/HLD.md#34.13"
    - "process/HLD.md#34.14"
    - "process/ARCHITECTURE-DECISION.md#ADR-074..ADR-077"
    - "process/stories/CR025-S05-no-real-operation-safety-verification.md"
  status: "confirmed"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  dependency_change_allowed: false
  backtrader_run_allowed: false
  credential_read_allowed: false
  qmt_operation_allowed: false
task_count: 4
created_at: "2026-06-01T22:42:19+08:00"
updated_at: "2026-06-02T09:18:42+08:00"
change_id: "CR-025"
---

# CR025-S05：no-real-operation safety 与验证策略

## 目标

建立 CR-025 的 fixture-only 验证矩阵和安全扫描策略，覆盖 forbidden import、forbidden source copy、schema contract、semantic diff contract、order intent draft contract、dependency diff 和真实操作计数。该 Story 本身仍处于规划状态，不执行验证。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-19、TS-025-01 至 TS-025-11 |
| 需求 | REQ-165、REQ-168、REQ-172、REQ-173、RA-057 至 RA-066 |
| HLD | `process/HLD.md` §34.8、§34.13、§34.14 |
| ADR | ADR-074、ADR-075、ADR-076、ADR-077 |

## 开发上下文（dev_context）

**背景说明**：CR-025 的安全目标是证明 research semantic alignment 不会越界成真实交易、真实数据写入或 Backtrader 源码迁移。验证策略必须默认 fixture-only，并把所有真实运行能力计数为 0。

**输入文件**：CR025-S01..S04 Story 合同、HLD / ADR、USE-CASES TS-025-01..11、本 Story 卡片。

**输出文件**：`tests/test_cr025_no_real_operation_safety.py`、`tests/test_cr025_forbidden_source_copy.py`、`tests/test_cr025_schema_contracts.py`。

**接口约定**：

| 验证域 | 必须覆盖 |
|---|---|
| no real operation | broker、QMT、MiniQMT、XtQuant、provider fetch、lake write、broker lake write、publish、simulation/live、credential read |
| no dependency change | `pyproject.toml` / `uv.lock` diff 为 0 |
| no Backtrader run | planning / CP5 前 run count 为 0；默认 import count 为 0 |
| no source copy | Backtrader GPLv3 source / samples / tests / datas / live store / line runtime 不进入仓库 |
| schema contracts | selector、semantic diff、order_intent_draft_v1 字段与 blocked reason |

**设计约束**：测试必须能离线运行；不得要求真实 Backtrader 安装、真实 QMT 环境、真实 provider、真实 lake、真实凭据或真实交易账户。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR025-S01 | safety-input-contract | selector / clean feed 合同冻结 | 测试只验证合同，不运行 backend |
| CR025-S02 | schema-contract | semantic diff schema 冻结 | 不生成真实 report |
| CR025-S03 | qmt-boundary-contract | order intent draft schema 冻结 | 不调用 QMT |
| CR025-S04 | license-guardrail | no-copy guardrail 冻结 | 不读取或复制 Backtrader 源码 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `tests/test_cr025_no_real_operation_safety.py`、`tests/test_cr025_forbidden_source_copy.py`、`tests/test_cr025_schema_contracts.py` | 当前 Story 独占 |
| shared | `engine/backtrader_adapter.py`、`engine/semantic_diff.py`、`engine/order_intent_draft.py` | 根据 S01/S02/S03 的实现输出做只读合同验证 |
| forbidden | 需要真实 Backtrader / QMT / provider / lake / credential 的测试 | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR025-S05-T1 | 设计 | `tests/test_cr025_no_real_operation_safety.py` | 设计真实操作计数、dependency diff 和 no credential tests |
| CR025-S05-T2 | 设计 | `tests/test_cr025_forbidden_source_copy.py` | 设计 Backtrader forbidden source-copy / migration scan |
| CR025-S05-T3 | 设计 | `tests/test_cr025_schema_contracts.py` | 设计 selector、semantic diff、order_intent_draft_v1 schema 合同测试 |
| CR025-S05-T4 | 约束 | validation matrix | 明确 TS-025-01..11 覆盖与 fixture-only 入口 |

## 验证上下文（validation_context）

**验证入口**：后续 LLD 可建议 `uv run --python 3.11 pytest -q tests/test_cr025_no_real_operation_safety.py tests/test_cr025_forbidden_source_copy.py tests/test_cr025_schema_contracts.py`，但本阶段不执行。

**验证方式**：fixture-only 单元 / 合同测试、静态扫描、dependency diff 复核。

**依赖环境**：本地仓库与 fixture；不得读取 `.env` 或任何凭据文件。

**关键验证场景**：

| 场景 | 预期 |
|---|---|
| TS-025-01..11 | 每个测试场景有对应合同或扫描 |
| Backtrader source scan | 源码复制 / vendoring / samples / tests / datas 命中为 0 |
| real operation scan | QMT / broker / provider / lake / publish / simulation/live / credential 命中为 0 |
| dependency diff | `pyproject.toml` / `uv.lock` 修改为 0 |

## 量化验收标准（acceptance_criteria）

- [ ] fixture-only 验证覆盖 TS-025-01 至 TS-025-11 共 11 个测试场景。
- [ ] real broker、QMT、MiniQMT、XtQuant、provider、lake、broker lake、publish、simulation/live、credential read 计数均为 0。
- [ ] Backtrader GPLv3 source copy / source migration / vendored source 命中为 0。
- [ ] `pyproject.toml` / `uv.lock` 修改次数为 0。
- [ ] 测试不要求真实 Backtrader 安装、真实 QMT 环境或真实凭据。

## CP6 编码完成说明

| 项 | 结论 | 证据 |
|---|---|---|
| CP6 状态 | PASS | `process/checks/CP6-CR025-S05-no-real-operation-safety-verification-CODING-DONE.md` |
| 实现文件 | 完成 | `tests/test_cr025_no_real_operation_safety.py`、`tests/test_cr025_forbidden_source_copy.py`、`tests/test_cr025_schema_contracts.py` |
| S05 定向验证 | PASS | `19 passed in 0.43s` |
| CR025 组合回归 | PASS | `52 passed in 0.75s` |
| no-real-operation counters | PASS | real broker / QMT / MiniQMT / XtQuant / provider fetch / lake write / broker lake write / publish / simulation/live / credential read 均为 0 |
| source-copy scan | PASS | Backtrader GPLv3 source copy / source migration / vendored source / samples / tests / datas / live store / line-metaclass runtime 命中 0 |
| 边界说明 | PASS | 本 Story 未修改 engine、docs、README、USER-MANUAL、STATE、计划、CR index、`pyproject.toml` 或 `uv.lock`；未读取 `/home/hyde/download/backtrader/**`、`.env`、真实 lake 或 broker lake |

## CP7 验证完成说明

| 项 | 结论 | 证据 |
|---|---|---|
| CP7 状态 | PASS | `process/checks/CP7-CR025-S05-no-real-operation-safety-verification-VERIFICATION-DONE.md` |
| 验证 agent | PASS | `meta-qa/qa-yan`，agent_id/thread_id=`019e85e4-1880-7c21-bc65-1efc837ed5b8` |
| S05 定向验证 | PASS | `19 passed in 0.45s` |
| CR025 组合回归 | PASS | `52 passed in 0.74s` |
| py_compile | PASS | 3 个 S05 测试文件语法检查通过 |
| dependency diff | PASS | `git diff --name-only -- pyproject.toml uv.lock` 无输出 |
| no-real-operation counters | PASS | broker / QMT / MiniQMT / XtQuant / provider fetch / lake write / broker lake write / publish / simulation/live / credential read 均为 0 |
| source-copy scan | PASS | Backtrader GPLv3 source copy / source migration / vendored source / samples / tests / datas / live store / line runtime migration 均为 0 |
| 多因子 / QMT 越界声明 | PASS | 未声明已实现 FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪、策略准入包、Qlib / Alphalens / vnpy.alpha 集成或 production QMT readiness |

## 阻塞说明

本 Story 已通过 CR-025 CP6 / CP7 并收敛为 `verified`。实现和验证均只覆盖 fixture-only / 静态扫描测试文件，未升级为真实运行授权，未读取 Backtrader 外部源码树、凭据、provider、lake、QMT 或 broker 环境。
