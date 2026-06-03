---
story_id: "CR018-S08-production-current-truth-research-rerun"
title: "published current truth 研究重跑"
story_slug: "production-current-truth-research-rerun"
status: "verified"
priority: "P0"
wave: "CR018-W4-RERUN-QMT-ADMISSION"
depends_on:
  - "CR018-S07-explicit-publish-gate-and-current-reader-smoke"
dependency_type:
  - upstream: "CR018-S07-explicit-publish-gate-and-current-reader-smoke"
    type: "runtime"
cp5_batch: "CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "experiments/production_current_truth_rerun.py"
    - "reports/production_current_truth/README.md"
    - "tests/test_cr018_production_current_truth_rerun.py"
  shared:
    - "engine/research_dataset.py"
  merge_owner: "CR018-S08-production-current-truth-research-rerun"
  forbidden:
    - "overwrite old reports"
    - "use candidate or proxy as production rerun input"
    - "start QMT"
    - "pyproject.toml"
    - "uv.lock"
    - ".env"
    - "credential files or secret values"
    - "provider fetch"
    - "real lake write"
lld_gate:
  required_inputs:
    - "process/HLD.md#32"
    - "process/HLD-DATA-LAKE.md#19.13"
    - "process/ARCHITECTURE-DECISION.md#ADR-066"
    - "process/stories/CR018-S08-production-current-truth-research-rerun.md"
  status: "confirmed"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  qmt_operation_allowed: false
created_at: "2026-05-29"
updated_at: "2026-05-29T11:19:04+08:00"
change_id: "CR-018"
---

# CR018-S08：published current truth 研究重跑

## 目标

在 published release 后重跑阶段三到阶段五核心研究，输出 production pass/fail、差异摘要、benchmark / PIT / tradability / adjustment / blocked claims 证据，作为 QMT admission 前置。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-14 |
| 需求 | REQ-133、REQ-137 |
| HLD | `process/HLD.md` §32；`process/HLD-DATA-LAKE.md` §19.13 |
| ADR | ADR-066 |

## 开发上下文（dev_context）

**背景说明**：数据湖 publish 不等于策略可进入 QMT。必须用 published current truth，而不是 candidate 或 proxy，重跑阶段三到阶段五核心研究，并把结果作为 QMT simulation admission 的硬门。

**输入文件**：S07 publish/current reader smoke 合同、CR018 HLD / ADR、本 Story 卡片、现有 `engine/research_dataset.py` 和 experiments/reporting 约定。

**输出文件**：`experiments/production_current_truth_rerun.py`、`reports/production_current_truth/README.md`、`tests/test_cr018_production_current_truth_rerun.py`；共享修改 `engine/research_dataset.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| production rerun entry | release_id、strategy set、research phase list | rerun report、pass/fail、diff summary | 未 published release 必须 blocked |
| research dataset loader | release_id、realism mode | current truth dataset panel | 不得读 candidate 或 proxy |
| admission evidence | rerun status、blocked claims | qmt_admission_input | fail 时 QMT stage blocked |

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR018-S07 | runtime | LLD 可定义接口和 blocked path | 开发需 S07 current reader smoke 合同冻结 | 真实 rerun 仍需 published release |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `experiments/production_current_truth_rerun.py`、`reports/production_current_truth/README.md`、`tests/test_cr018_production_current_truth_rerun.py` | 当前 Story 独占 |
| shared | `engine/research_dataset.py` | 与 S04 共享，开发默认串行 |
| forbidden | 覆盖旧报告、使用 candidate/proxy、启动 QMT、真实抓取/写湖 | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR018-S08-T1 | 创建 | `experiments/production_current_truth_rerun.py` | 定义 published release 研究重跑入口 |
| CR018-S08-T2 | 修改 | `engine/research_dataset.py` | 增加 production current truth 读取门控和 metadata |
| CR018-S08-T3 | 创建 | `reports/production_current_truth/README.md` | 定义重跑报告结构，不覆盖旧报告 |
| CR018-S08-T4 | 创建 | `tests/test_cr018_production_current_truth_rerun.py` | 验证未 published / candidate / proxy 均 blocked |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr018_production_current_truth_rerun.py`。

**验证方式**：fixture-only 合同测试；不运行真实长任务。

**关键验证场景**：未 published release blocked；candidate/proxy 输入 blocked；报告包含 release_id、benchmark、PIT、tradability、adjustment、blocked claims。

## 量化验收标准（acceptance_criteria）

- [ ] rerun 报告必须记录 release_id、benchmark、PIT、tradability、adjustment、blocked claims。
- [ ] candidate 或 proxy 被作为 production rerun 输入的 allowed 次数为 0。
- [ ] S08 未 PASS 时 QMT admission allowed 次数为 0。
- [ ] old_report_overwrite、provider_fetch、lake_write、QMT operation 计数均为 0。

## 阻塞说明

CP5 已获批；真实 production rerun 需要 published release 和后续运行授权，本 Story 卡片不授权长任务或 QMT。
