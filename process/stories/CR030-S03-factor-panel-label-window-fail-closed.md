---
story_id: "CR030-S03-factor-panel-label-window-fail-closed"
title: "FactorPanelContract / LabelWindowSpec 防泄漏合同"
story_slug: "factor-panel-label-window-fail-closed"
status: "verified"
priority: "P0"
wave: "CR030-W2-PANEL-EVALUATION"
depends_on:
  - "CR030-S02-factor-spec-run-spec-contract"
  - "CR011-S08-factor-panel-audit-and-robust-validation"
dependency_type:
  - upstream: "CR030-S02-factor-spec-run-spec-contract"
    type: "schema-contract"
  - upstream: "CR011-S08-factor-panel-audit-and-robust-validation"
    type: "factor-panel-audit-contract"
cp5_batch: "CR030-MULTIFACTOR-RESEARCH-LOOP-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "engine/factor_panel_contracts.py"
    - "tests/test_cr030_factor_panel_label_window_gates.py"
  shared:
    - "engine/research_dataset.py"
    - "market_data/readers.py"
  merge_owner: "CR030-S03-factor-panel-label-window-fail-closed"
  forbidden:
    - "external PIT/label truth"
    - "available_at missing accepted"
    - "provider fetch"
    - "lake write"
    - "pyproject.toml"
    - "uv.lock"
    - ".env"
lld_gate:
  required_inputs:
    - "process/HLD.md#35.7.3"
    - "process/HLD.md#35.8"
    - "process/ARCHITECTURE-DECISION.md#ADR-081"
    - "process/ARCHITECTURE-DECISION.md#ADR-082"
    - "process/stories/CR030-S03-factor-panel-label-window-fail-closed.md"
  status: "approved"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  dependency_change_allowed: false
  provider_fetch_allowed: false
  lake_write_allowed: false
  credential_read_allowed: false
task_count: 5
created_at: "2026-06-03T08:30:00+08:00"
updated_at: "2026-06-03T09:58:35+08:00"
change_id: "CR-030"
---

# CR030-S03：FactorPanelContract / LabelWindowSpec 防泄漏合同

## 目标

冻结因子面板、标签窗口、可用时点、lineage、复权口径、quality status 和 fail-closed 错误码，防止前视和标签泄漏进入评价、组合或准入。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-23、TS-030-03、TS-030-04 |
| 需求 | REQ-177、REQ-182、REQ-183、REQ-185 |
| HLD | `process/HLD.md` §35.7.3、§35.8、§35.10 |
| ADR | ADR-081、ADR-082 |

## 开发上下文（dev_context）

**背景说明**：多因子研究若缺少 `available_at`、`decision_time`、label availability、lineage 或复权口径证明，会产生假 alpha。CR-030 必须把这些风险前置为 hard gate。

**输入文件**：CR030-S02 合同、CR-011 factor panel audit、`research_input_v1`、HLD §35、本 Story 卡片。

**输出文件**：`engine/factor_panel_contracts.py`、`tests/test_cr030_factor_panel_label_window_gates.py`。

**接口约定**：

| 合同项 | 要求 |
|---|---|
| FactorPanelContract | `trade_date`、`symbol`、factor value、factor version、`available_at`、source dataset、quality status、preprocessing metadata |
| LabelWindowSpec | `label_window_start`、`label_window_end`、`label_available_at`、收益口径、复权口径、成本口径 |
| blocked reason | `MF_AVAILABLE_AT_VIOLATION`、`MF_LABEL_OVERLAP_RISK`、`MF_LINEAGE_MISSING` 等结构化错误码 |
| fail-closed | gate fail 时评价、组合和 admission 均不得继续 |

**设计约束**：不得用外部框架自动生成 PIT universe、复权或 label truth；不得接受缺 `available_at` 的字段。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR030-S02 | schema-contract | FactorSpec / FactorRunSpec 已冻结 | S02 合同冻结后才能实现 | 面板和标签消费因子运行合同 |
| CR011-S08 | factor-panel-audit-contract | 只读引用 audit 口径 | 不回滚 CR011 | 复用既有 factor panel audit 经验 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `engine/factor_panel_contracts.py`、`tests/test_cr030_factor_panel_label_window_gates.py` | 当前 Story 独占 |
| shared | `engine/research_dataset.py`、`market_data/readers.py` | 修改需 LLD 标明 merge order |
| forbidden | provider fetch、lake write、外部 PIT truth、`.env` | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR030-S03-T1 | 设计 | `engine/factor_panel_contracts.py` | 定义 panel / label 合同和错误码 |
| CR030-S03-T2 | 设计 | `tests/test_cr030_factor_panel_label_window_gates.py` | 设计 available_at、label overlap、lineage、复权混用测试 |
| CR030-S03-T3 | 兼容 | `engine/research_dataset.py` | 说明 `research_input_v1` 到 panel/label 的只读映射 |
| CR030-S03-T4 | 约束 | quality gate | 定义 quality fail / no trade / suspension blocked reason |
| CR030-S03-T5 | 约束 | fail-closed flow | 定义下游评价、组合和 admission 的阻断合同 |

## 验证上下文（validation_context）

**验证入口**：后续 LLD 可建议 `uv run --python 3.11 pytest -q tests/test_cr030_factor_panel_label_window_gates.py`，但本阶段不执行。

**验证方式**：fixture-only 合同测试、leakage gate 测试、blocked reason 测试。

**依赖环境**：本地 fixture 和已发布读合同；不得 provider fetch、lake write 或读取凭据。

**关键验证场景**：

| 场景 | 预期 |
|---|---|
| `available_at > decision_time` | fail-closed，评价不继续 |
| label overlap | fail-closed，组合不继续 |
| lineage / quality 缺失 | structured blocked reason |
| 外部 PIT truth 替代内部 gate | 测试失败 |

## 量化验收标准（acceptance_criteria）

- [ ] available_at、label overlap、lineage、复权口径、quality status P0 校验覆盖率为 100%。
- [ ] gate fail 时评价、组合、admission 继续次数为 0。
- [ ] 每类 fail-closed 错误码至少 1 个 fixture。
- [ ] 外部框架 label / PIT truth 直接接管次数为 0。
- [ ] provider fetch、lake write、credential read、QMT 调用均为 0。

## 阻塞说明

本 Story 的开发必须等待 CP5 全量 LLD 确认。若数据字段无法证明时点或 lineage，后续 LLD 必须保持 blocked / research_limited，不得降级为 warn-only。
