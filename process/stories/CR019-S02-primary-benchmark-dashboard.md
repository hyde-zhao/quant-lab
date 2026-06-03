---
story_id: "CR019-S02-primary-benchmark-dashboard"
title: "多基准看板与 primary benchmark policy"
story_slug: "primary-benchmark-dashboard"
status: "verified"
priority: "P0"
wave: "CR019-W1-ADMISSION-BENCHMARK"
depends_on:
  - "CR019-S01-stage6-admission-gate-package"
  - "CR018-S03-real-benchmark-index-components-weights-backfill"
dependency_type:
  - upstream: "CR019-S01-stage6-admission-gate-package"
    type: "contract"
  - upstream: "CR018-S03-real-benchmark-index-components-weights-backfill"
    type: "benchmark-readiness"
cp5_batch: "CR019-STAGE6-QMT-BRIDGE-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "engine/benchmark_policy.py"
    - "tests/test_cr019_primary_benchmark_policy.py"
  shared:
    - "reports/stage6_admission/**"
  merge_owner: "CR019-S02-primary-benchmark-dashboard"
  forbidden:
    - "proxy benchmark as real benchmark"
    - "provider fetch"
    - "lake write"
    - "publish"
    - "credential files or secret values"
lld_gate:
  required_inputs:
    - "process/HLD.md#33.4"
    - "process/HLD.md#33.6"
    - "process/ARCHITECTURE-DECISION.md#ADR-067"
    - "process/stories/CR019-S02-primary-benchmark-dashboard.md"
  status: "confirmed"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  provider_fetch_allowed: false
  lake_write_allowed: false
  publish_allowed: false
task_count: 3
cp6:
  status: "PASS"
  result: "process/checks/CP6-CR019-S02-primary-benchmark-dashboard-CODING-DONE.md"
  checked_at: "2026-05-30T19:37:42+08:00"
  validation:
    pytest: "PASS: 17 passed in 0.06s"
    py_compile: "PASS"
    diff_check: "PASS"
    dependency_diff: "PASS: pyproject.toml / uv.lock / .env unchanged"
    forbidden_operation_counters: "all_zero"
created_at: "2026-05-30T18:24:00+08:00"
updated_at: "2026-05-30T19:51:32+08:00"
change_id: "CR-019"
---

# CR019-S02：多基准看板与 primary benchmark policy

## 目标

定义阶段六 admission 的多基准看板和 primary benchmark 选择规则，覆盖 HS300、ZZ500、ZZ1000、中证全指，并避免 proxy benchmark 冒充真实 benchmark。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-15 |
| 需求 | REQ-138、REQ-154 |
| HLD | `process/HLD.md` §33.4、§33.6 |
| ADR | ADR-067 |

## 开发上下文（dev_context）

**输入文件**：`process/HLD.md`、`process/ARCHITECTURE-DECISION.md`、CR018 benchmark readiness Story、本 Story 卡片。

**输出文件**：`engine/benchmark_policy.py`、`tests/test_cr019_primary_benchmark_policy.py`，共享 `reports/stage6_admission/**`。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR019-S01 | contract | admission package 字段先冻结 | 依赖 S01 字段合同 | benchmark 字段进入 admission package |
| CR018-S03 | benchmark-readiness | 可读取四类 benchmark readiness 合同 | 不触发真实补 benchmark | 缺失时输出 unavailable / blocked |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `engine/benchmark_policy.py`、`tests/test_cr019_primary_benchmark_policy.py` | 当前 Story 独占 |
| shared | `reports/stage6_admission/**` | merge owner 为当前 Story |
| forbidden | proxy benchmark 写入真实字段、真实 provider fetch、lake write、publish | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR019-S02-T1 | 创建 | `engine/benchmark_policy.py` | 定义四基准字段、primary 选择规则和 unavailable 语义 |
| CR019-S02-T2 | 创建 | `tests/test_cr019_primary_benchmark_policy.py` | 验证四基准覆盖、primary 选择和 proxy 禁用 |
| CR019-S02-T3 | 修改 | `reports/stage6_admission/**` | 按 LLD 增加 benchmark dashboard schema，不写真实报告 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr019_primary_benchmark_policy.py`。

**验证方式**：离线合同测试；不联网、不读凭据、不写 lake。

## 量化验收标准（acceptance_criteria）

- [x] HS300、ZZ500、ZZ1000、中证全指 4 类 benchmark 字段覆盖率为 100%。
- [x] primary benchmark 选择规则有 universe / 风格依据。
- [x] proxy benchmark 写入真实 benchmark 字段次数为 0。
- [x] provider_fetch、lake_write、publish 均为 0。

## 阻塞说明

CP6 / CP7 均已通过；当前 Story 已收敛为 `verified`，仍不得真实补 benchmark、provider fetch、lake write 或 publish。

## CP6 状态证据

| 字段 | 值 |
|---|---|
| 结论 | `PASS` |
| CP6 文件 | `process/checks/CP6-CR019-S02-primary-benchmark-dashboard-CODING-DONE.md` |
| checked_at | `2026-05-30T19:37:42+08:00` |
| 测试结果 | `tests/test_cr019_primary_benchmark_policy.py` + `tests/test_cr019_stage6_admission_gate.py`：`17 passed in 0.06s` |
| py_compile | `PASS` |
| diff check | `PASS` |
| 依赖 / 凭据 diff | `pyproject.toml` / `uv.lock` / `.env` 输出为空 |
| forbidden operation counters | 全部为 0 |
| 下一状态 | `ready-for-verification` |

## CP7 验证完成证据

| 字段 | 值 |
|---|---|
| 结论 | `PASS` |
| CP7 文件 | `process/checks/CP7-CR019-S02-primary-benchmark-dashboard-VERIFICATION-DONE.md` |
| meta-qa 调度 | `process/handoffs/META-QA-CR019-S02-CP7-VERIFY-2026-05-30.md`；agent_id/thread_id=`019e78b4-95cb-7e53-b841-719d0f0f530b`，agent_name=`qa-zhang` |
| checked_at | `2026-05-30T19:48:27+08:00` |
| 验证结果 | S02 + S01 回归 `17 passed in 0.06s`；`py_compile`、diff check、no-index schema whitespace、依赖 diff、缓存检查、counter probe、check-ignore 和禁区扫描均 PASS |
| forbidden operation counters | 全部为 0 |
| 当前状态 | `verified` |
