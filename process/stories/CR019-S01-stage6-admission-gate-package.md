---
story_id: "CR019-S01-stage6-admission-gate-package"
title: "阶段六 admission gate 与 package 合同"
story_slug: "stage6-admission-gate-package"
status: "verified"
priority: "P0"
wave: "CR019-W1-ADMISSION-BENCHMARK"
depends_on:
  - "CR018-S08-production-current-truth-research-rerun"
  - "CR016-S04-simulation-live-runbook-and-approval-gates"
dependency_type:
  - upstream: "CR018-S08-production-current-truth-research-rerun"
    type: "runtime-evidence"
  - upstream: "CR016-S04-simulation-live-runbook-and-approval-gates"
    type: "contract"
cp5_batch: "CR019-STAGE6-QMT-BRIDGE-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "engine/stage6_admission.py"
    - "tests/test_cr019_stage6_admission_gate.py"
  shared:
    - "reports/stage6_admission/**"
    - "trading/stage_gate.py"
  merge_owner: "CR019-S01-stage6-admission-gate-package"
  forbidden:
    - "process/HLD.md"
    - "process/ARCHITECTURE-DECISION.md"
    - "pyproject.toml"
    - "uv.lock"
    - ".env"
    - "credential files or secret values"
    - "QMT / MiniQMT / XtQuant operation"
    - "provider fetch"
    - "lake write"
    - "broker lake write"
    - "publish"
    - "simulation/live run"
lld_gate:
  required_inputs:
    - "process/HLD.md#33.1"
    - "process/HLD.md#33.12"
    - "process/ARCHITECTURE-DECISION.md#ADR-067"
    - "process/stories/CR019-S01-stage6-admission-gate-package.md"
  status: "confirmed"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  qmt_operation_allowed: false
  provider_fetch_allowed: false
  lake_write_allowed: false
  broker_lake_write_allowed: false
  publish_allowed: false
  simulation_or_live_allowed: false
task_count: 4
created_at: "2026-05-30T18:24:00+08:00"
updated_at: "2026-05-30T19:25:30+08:00"
change_id: "CR-019"
---

# CR019-S01：阶段六 admission gate 与 package 合同

## 目标

冻结阶段六多因子 admission gate 与 admission package 合同，确保旧失败策略只能作为 blocked evidence，不能被包装成 simulation ready。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-15 |
| 需求 | REQ-138、REQ-144、REQ-154 |
| HLD | `process/HLD.md` §33.1、§33.4、§33.12 |
| ADR | ADR-067 |

## 开发上下文（dev_context）

**背景说明**：CR-019 要建立实验 49-66 到 QMT simulation 申请前的 admission 链路。该链路必须先输出 gate matrix、blocked claims、解除条件、pre-sim 和连续 5 个真实交易日 dry-run evidence schema。

**输入文件**：`process/HLD.md`、`process/ARCHITECTURE-DECISION.md`、`process/REQUIREMENTS.md`、`process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml`、本 Story 卡片。

**输出文件**：`engine/stage6_admission.py`、`tests/test_cr019_stage6_admission_gate.py`；共享输出为 `reports/stage6_admission/**` 和 `trading/stage_gate.py`。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR018-S08 | runtime-evidence | 可读取 verified 研究重跑合同 | 仅消费脱敏 evidence，不改写 CR018 报告 | published current truth rerun 是 admission 输入 |
| CR016-S04 | contract | 可引用 stage gate / runbook 字段 | 不授权 simulation/live | 5 日 dry-run 后仍需 per-run authorization |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `engine/stage6_admission.py`、`tests/test_cr019_stage6_admission_gate.py` | 当前 Story 独占 |
| shared | `reports/stage6_admission/**`、`trading/stage_gate.py` | merge owner 为当前 Story |
| forbidden | HLD / ADR / 需求正文、依赖、凭据、真实 QMT / provider / lake / broker / publish / simulation/live 操作 | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR019-S01-T1 | 创建 | `engine/stage6_admission.py` | 定义 admission gate matrix、blocked claims 和 admission package schema |
| CR019-S01-T2 | 创建 | `tests/test_cr019_stage6_admission_gate.py` | 覆盖旧失败策略 blocked、P0 gate fail 和 5 日 dry-run evidence 缺失场景 |
| CR019-S01-T3 | 修改 | `trading/stage_gate.py` | 按 LLD 指定范围接入 admission evidence ref，不改变既有 stage 语义 |
| CR019-S01-T4 | 创建 | `reports/stage6_admission/**` | 输出 schema / README 占位，禁止写真实运行报告 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr019_stage6_admission_gate.py`。

**验证方式**：离线单元测试与静态禁区检查；不联网、不读凭据、不调用 QMT、不写真实 lake。

## 量化验收标准（acceptance_criteria）

- [x] 实验 49-66 gate 字段覆盖率为 100%。
- [x] 任一 P0 gate 未过时 `admission_status=blocked`。
- [x] 旧失败策略标记为 `simulation_ready` 的次数为 0。
- [x] `qmt_api_call`、`provider_fetch`、`lake_write`、`broker_lake_write`、`publish`、`simulation_or_live_run` 均为 0。

## 阻塞说明

CP6 / CP7 均已通过；当前 Story 已收敛为 `verified`，仍不得启动 simulation 或调用 QMT。

## CP6 编码完成证据

| 项目 | 结果 | 证据 |
|---|---|---|
| CP6 | PASS | `process/checks/CP6-CR019-S01-stage6-admission-gate-package-CODING-DONE.md` |
| 验证命令 | PASS | `py_compile` 退出码 0；S01 + CR016 回归 `18 passed in 0.07s`；`git diff --check` 退出码 0 |
| 禁止操作 | PASS | dependency_change、service_start、credential_read、QMT / MiniQMT / XtQuant、provider_fetch、lake_write、broker_lake_write、publish、simulation_or_live_run 均为 0 |

## CP7 验证完成证据

| 项目 | 结果 | 证据 |
|---|---|---|
| CP7 | PASS | `process/checks/CP7-CR019-S01-stage6-admission-gate-package-VERIFICATION-DONE.md` |
| meta-qa 调度 | PASS | `process/handoffs/META-QA-CR019-S01-CP7-VERIFY-2026-05-30.md`；agent_id/thread_id=`019e789d-05c2-7b62-bb76-deab5c911c4b`，agent_name=`qa-cao` |
| 验证命令 | PASS | S01 + CR016 回归 `18 passed in 0.06s`；`py_compile`、`git diff --check`、依赖 diff、缓存状态检查均 PASS |
| 禁止操作 | PASS | dependency_change、service_start、credential_read、QMT / MiniQMT / XtQuant、provider_fetch、lake_write、broker_lake_write、publish、simulation_or_live_run 均为 0 |
