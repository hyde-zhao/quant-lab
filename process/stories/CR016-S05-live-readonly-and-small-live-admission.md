---
story_id: "CR016-S05-live-readonly-and-small-live-admission"
title: "live_readonly 与 small_live 准入门"
story_slug: "live-readonly-and-small-live-admission"
status: "lld-approved"
priority: "P0"
wave: "CR016-W2-LIVE-SCALE-DOCS-GATED"
depends_on:
  - "CR016-S04-simulation-live-runbook-and-approval-gates"
  - "CR015-S07-docs-and-foundation-runbook-boundary"
dependency_type:
  - upstream: "CR016-S04-simulation-live-runbook-and-approval-gates"
    type: "runtime"
  - upstream: "CR015-S07-docs-and-foundation-runbook-boundary"
    type: "runtime"
cp5_batch: "CR016-QMT-ACTIVATION-BATCH-A"
implementation_allowed: false
file_ownership:
  primary:
    - "trading/live_admission.py"
    - "tests/test_cr016_live_readonly_small_live_admission.py"
  shared:
    - "trading/stage_gate.py"
    - "docs/QMT-SIMULATION-LIVE-RUNBOOK.md"
  merge_owner: "CR016-S05-live-readonly-and-small-live-admission"
  forbidden:
    - "pyproject.toml"
    - "uv.lock"
    - "credential files or secret values"
    - "real broker operation without explicit authorization"
lld_gate:
  required_inputs:
    - "process/HLD-QMT-TRADING.md#7.4"
    - "process/ARCHITECTURE-DECISION.md#ADR-059"
    - "process/ARCHITECTURE-DECISION.md#ADR-060"
    - "process/stories/CR016-S05-live-readonly-and-small-live-admission.md"
  status: "approved"
  cp5_batch: "CR016-QMT-ACTIVATION-BATCH-A"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: false
  file_conflict_free: false
  implementation_allowed: false
  requires_cr015_verified: true
  requires_per_run_authorization: true
  later_gated_real_operation: true
created_at: "2026-05-28"
updated_at: "2026-05-28T06:24:15+08:00"
change_id: "CR-016"
---

# CR016-S05：live_readonly 与 small_live 准入门

## 目标

定义 live_readonly 和 small_live 的准入、退出、回退、资金上限、观察窗口和失败阈值。该 Story 不是当前可直接实现真实操作的项，只能作为 later-gated 合同。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-11 |
| 需求 | REQ-112、REQ-114、REQ-116、REQ-117、REQ-119、REQ-121 |
| HLD | `process/HLD-QMT-TRADING.md` §7.4、§11 |
| ADR | ADR-059、ADR-060 |

## 开发上下文（dev_context）

**背景说明**：simulation 通过后仍不能直接 small_live。live_readonly 用于核对真实只读事实；small_live 必须资金上限、kill switch 演练、对账和授权均满足。

**输入文件**：CR016-S04 runbook / approval gates、CR015 foundation verified evidence。

**输出文件**：`trading/live_admission.py`、`tests/test_cr016_live_readonly_small_live_admission.py`；共享 `trading/stage_gate.py`、`docs/QMT-SIMULATION-LIVE-RUNBOOK.md`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| live_readonly_gate | simulation evidence、read-only authorization、recon policy | pass / blocked | 不允许账户写操作 |
| small_live_gate | live_readonly evidence、capital cap、kill switch drill | pass / blocked | 缺资金上限或演练 blocked |
| rollback evaluator | live stage result | rollback target、reason | 不自动放大资金 |

**设计约束**：本 Story 只定义 gate；真实 live_readonly / small_live 运行必须后续 per-run 授权，不得从 CP4/CP5 默认获得。

**命名规范**：`live_readonly_gate_status`、`small_live_gate_status`、`capital_cap`、`observation_window`、`rollback_target`。

**平台目标**：CR016 real-stage governance。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR016-S04 | runtime | runbook / approval gate 已定义 | 真实阶段 later-gated | runbook 前置 |
| CR015-S07 | runtime | foundation 文档和证据已定义 | CR015 verified 后才可实现 | foundation 前置 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR016-S05-T1 | 创建 | `trading/live_admission.py` | 定义 live_readonly / small_live gate |
| CR016-S05-T2 | 创建 | `tests/test_cr016_live_readonly_small_live_admission.py` | 覆盖缺授权、缺资金上限、缺 kill switch drill |
| CR016-S05-T3 | 修改 | `docs/QMT-SIMULATION-LIVE-RUNBOOK.md` | 写 live stage 准入 / 回退矩阵 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr016_live_readonly_small_live_admission.py`。

**验证方式**：gate fixture；不真实运行。

**依赖环境**：Python 3.11、uv、pytest。

**关键验证场景**：simulation 未通过 blocked；live_readonly 缺授权 blocked；small_live 缺资金上限 blocked；缺 kill switch 演练 blocked。

## 量化验收标准（acceptance_criteria）

- [ ] live_readonly 和 small_live gate 均定义准入、退出、回退、观察窗口、失败阈值。
- [ ] 缺 per-run authorization 时真实调用次数为 0。
- [ ] small_live 缺资金上限或 kill switch 演练时 allowed 次数为 0。
- [ ] 本 Story 在 CP5 后仍默认 later-gated，必须由用户另行授权真实运行。

## 阻塞说明

当前为 later-gated，不属于当前可直接实现真实操作项；CP5 前不得实现。
