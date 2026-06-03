---
story_id: "CR025-S01-clean-feed-gate-backend-selector"
title: "clean feed gate 与 backend selector"
story_slug: "clean-feed-gate-backend-selector"
status: "verified"
priority: "P0"
wave: "CR025-W1-FEED-GOVERNANCE"
depends_on:
  - "CR006-S03-backtrader-clean-feed-contract"
  - "CR005-S06-backtrader-optional-backend"
dependency_type:
  - upstream: "CR006-S03-backtrader-clean-feed-contract"
    type: "clean-feed-contract"
  - upstream: "CR005-S06-backtrader-optional-backend"
    type: "optional-backend-contract"
cp5_batch: "CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "engine/backtrader_adapter.py"
    - "engine/backtest.py"
    - "tests/test_cr025_clean_feed_gate.py"
  shared:
    - "market_data/readers.py"
    - "engine/research_dataset.py"
  merge_owner: "CR025-S01-clean-feed-gate-backend-selector"
  forbidden:
    - "pyproject.toml"
    - "uv.lock"
    - ".env"
    - "market_data/connectors/**"
    - "market_data/runtime.py"
    - "market_data/storage.py"
    - "provider fetch"
    - "lake write"
    - "Backtrader run before CP5"
    - "Backtrader GPLv3 source copy"
lld_gate:
  required_inputs:
    - "process/HLD.md#34.4"
    - "process/HLD.md#34.6"
    - "process/HLD.md#34.11"
    - "process/ARCHITECTURE-DECISION.md#ADR-074"
    - "process/stories/CR025-S01-clean-feed-gate-backend-selector.md"
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
task_count: 5
created_at: "2026-06-01T22:42:19+08:00"
updated_at: "2026-06-02T07:55:45+08:00"
change_id: "CR-025"
---

# CR025-S01：clean feed gate 与 backend selector

## 目标

冻结 CR-025 的 clean feed gate、lightweight 默认后端、Backtrader optional selector、未安装 / 未选择 Backtrader 时的 structured unavailable，以及 Backtrader lazy import 边界。该 Story 只为后续 LLD 提供合同输入，CP5 前不得实现。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-19、SM-33、SM-34、TS-025-01、TS-025-02、TS-025-05 |
| 需求 | REQ-161、REQ-162、REQ-163、REQ-167、RA-057、RA-058、RA-063 |
| HLD | `process/HLD.md` §34.4、§34.6、§34.11 |
| ADR | ADR-074 |

## 开发上下文（dev_context）

**背景说明**：CR-025 要把研究执行语义与后续 QMT 路线对齐，但不能让 Backtrader optional backend 变成默认执行路径。lightweight 引擎仍是默认结果基线；Backtrader 只能在后续 CP5 通过后作为可选 reference path 被显式选择。

**输入文件**：CR-025 HLD / ADR、CR006 clean feed contract、CR005 optional backend contract、本 Story 卡片。

**输出文件**：`engine/backtrader_adapter.py`、`engine/backtest.py`、`tests/test_cr025_clean_feed_gate.py`。

**接口约定**：

| 合同项 | 要求 |
|---|---|
| selector 输入 | backend 名称、dataset manifest、feature flags、clean feed evidence、lineage、limitations |
| selector 输出 | `selected_backend`、`availability_status`、`blocked_reasons[]`、`lineage`、`limitations`、`import_attempted` |
| unavailable | 未安装、未选择、clean feed 不满足或 CP5 未确认时返回结构化 blocked / unavailable，不抛裸异常 |
| lazy import | 默认路径不得 import Backtrader；仅显式选择且门控满足时才允许进入 optional import 分支 |

**设计约束**：不得生成 PIT / 复权 / benchmark / tradability / quality truth；不得联网补数；不得写 lake；不得新增依赖；不得运行 Backtrader。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR006-S03 | clean-feed-contract | 复用 clean feed 字段与失败原因 | 不修改 CR006 已验证合同 | CR-025 只消费，不重新定义数据真相 |
| CR005-S06 | optional-backend-contract | 复用 optional backend 不可用语义 | 不扩展依赖或运行 Backtrader | CR-025 增加 selector 与 semantic alignment 约束 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `engine/backtrader_adapter.py`、`engine/backtest.py`、`tests/test_cr025_clean_feed_gate.py` | 当前 Story 独占 LLD owner；实现需等 CP5 |
| shared | `market_data/readers.py`、`engine/research_dataset.py` | 仅允许按 LLD 定义读取现有合同；修改需 meta-po 串行合并 |
| forbidden | `pyproject.toml`、`uv.lock`、`.env`、provider fetch、lake write、Backtrader run、Backtrader GPLv3 source copy | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR025-S01-T1 | 设计 | `engine/backtrader_adapter.py` | 在 LLD 中定义 optional backend selector 与 structured unavailable schema |
| CR025-S01-T2 | 设计 | `engine/backtest.py` | 在 LLD 中定义 lightweight default 与 backend selection 调用边界 |
| CR025-S01-T3 | 设计 | `tests/test_cr025_clean_feed_gate.py` | 在 LLD 中设计 clean feed gate、lazy import、dependency diff 为 0 的测试场景 |
| CR025-S01-T4 | 约束 | `pyproject.toml`、`uv.lock` | 明确 CP5 前与本 Story 实现阶段不得修改依赖 |
| CR025-S01-T5 | 约束 | Backtrader runtime | 明确 CP5 前 Backtrader run / import count default 为 0 |

## 验证上下文（validation_context）

**验证入口**：后续 LLD 可建议 `uv run --python 3.11 pytest -q tests/test_cr025_clean_feed_gate.py`，但本阶段不执行。

**验证方式**：fixture-only 合同测试；验证 selector 输出 schema、clean feed gate、lazy import 默认不触发、dependency diff 为 0。

**依赖环境**：仅使用本地 fixture 和现有 Python 环境；不得安装依赖、不得读取凭据、不得访问 provider 或 lake。

**关键验证场景**：

| 场景 | 预期 |
|---|---|
| lightweight 默认路径 | selected_backend 为 lightweight，Backtrader import_attempted=false |
| Backtrader 未安装或未选择 | structured unavailable，blocked_reasons 可审计 |
| clean feed 缺 PIT / available_at / 复权 / benchmark / tradability / quality 字段 | fail closed，不生成 reference result |
| CP5 未确认 | implementation_allowed=false，后端选择不进入运行分支 |

## 量化验收标准（acceptance_criteria）

- [ ] PIT、available_at、复权、benchmark、tradability、quality、lineage、limitations gate 覆盖率为 100%。
- [ ] 默认 lightweight 路径 Backtrader import 次数为 0。
- [ ] 未安装或未选择 Backtrader 时返回 structured unavailable，裸异常泄漏次数为 0。
- [ ] `pyproject.toml` / `uv.lock` 修改次数为 0。
- [ ] provider fetch、lake write、credential read、QMT 调用、Backtrader run 均为 0。

## 阻塞说明

本 Story 已通过 CR-025 CP5 全量 LLD 批次确认，并已调度 `meta-dev/dev-zhang` 进入 `in-development`。实现仍只允许受控离线 / fixture / 静态合同范围，不得运行 Backtrader、不得修改依赖或触发任何真实操作。
