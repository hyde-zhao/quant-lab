---
story_id: "CR008-S04-quality-adjustment-label-window-gates"
title: "质量、复权与 label window gate"
story_slug: "quality-adjustment-label-window-gates"
status: "verified"
priority: "P0"
wave: "CR008-BATCH-A"
change_id: "CR-008"
depends_on: ["CR008-S03-research-dataset-builder"]
dependency_contracts:
  - upstream: "CR008-S03-research-dataset-builder"
    type: "contract"
    required: "`ResearchDataset` 和 `GateResult` 基础合同已冻结"
  - upstream: "CR008-S03-research-dataset-builder"
    type: "file-conflict"
    required: "`engine/research_dataset.py` 共享文件必须串行合并"
file_ownership:
  primary:
    - "tests/test_cr008_quality_adjustment_label_gates.py"
  shared:
    - "engine/research_dataset.py"
    - "engine/quality.py"
  merge_owner: "CR008-S04-quality-adjustment-label-window-gates"
  forbidden:
    - "market_data/connectors/**"
    - "market_data/runtime.py"
    - "market_data/storage.py"
    - "data/**"
    - "reports/data_quality_report.csv"
    - ".env"
    - "credentials"
    - "delivery/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#25.8"
    - "process/ARCHITECTURE-DECISION.md#adr-028quality--adjustment--label-window-gate-是研究准入硬门"
    - "process/stories/CR008-S04-quality-adjustment-label-window-gates.md"
  status: "cp5-approved"
  cp5_batch: "CR008-BATCH-A"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  required_contracts:
    - "research_dataset_builder contract frozen"
    - "CR008-BATCH-A CP5 approved"
  file_conflict_free: true
  cp5_required: true
  implementation_allowed: true
  implementation_scope: "offline-only"
  dev_handoff: "process/handoffs/META-DEV-CR008-S04-IMPLEMENT-2026-05-21.md"
  dev_agent_name: "dev-shi the 2nd"
  dev_agent_id: "019e4b63-d14a-7012-b9c7-6145194f5e12"
  dev_started_at: "2026-05-22T00:34:57+08:00"
  previous_dev_agent_name: "dev-zhang the 2nd"
  previous_dev_agent_id: "019e4b51-bd69-7d63-ae69-69bd49288bbe"
  previous_dev_status: "stalled-closed-no-output"
cp6_status: "PASS"
cp6_checkpoint: "process/checks/CP6-CR008-S04-quality-adjustment-label-window-gates-CODING-DONE.md"
cp6_completed_at: "2026-05-22T00:38:13+08:00"
cp7_handoff: "process/handoffs/META-QA-CR008-S04-CP7-VERIFY-2026-05-22.md"
cp7_status: "PASS"
cp7_agent_name: "qa-kong the 2nd"
cp7_agent_id: "019e4b7a-2332-7ca1-9af7-6f412b686bfa"
cp7_started_at: "2026-05-22T00:59:19+08:00"
cp7_completed_at: "2026-05-22T01:02:05+08:00"
cp7_checkpoint: "process/checks/CP7-CR008-S04-quality-adjustment-label-window-gates-VERIFICATION-DONE.md"
verified_at: "2026-05-22T01:08:21+08:00"
previous_cp7_agent_name: "qa-cao the 2nd"
previous_cp7_agent_id: "019e4b69-f2cb-76a0-8483-e8b5715b4818"
previous_cp7_status: "stalled-closed-no-output"
created_at: "2026-05-21"
updated_at: "2026-05-22T01:08:18+08:00"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
---

# CR008-S04：质量、复权与 label window gate

## 目标

把 quality、单一复权口径和未来收益标签窗口变成研究准入硬门。严肃研究中，quality fail、复权混用或 label window 不足必须 fail；探索模式可截断，但必须写明 `label_available_end` 和样本损失。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | CR008-AC-007、CR008-AC-008 |
| HLD | §25.8、§25.10 |
| ADR | ADR-028 |

## 开发上下文（dev_context）

**背景说明**：实验十五默认 `forward_return_horizon=20` 时末端样本标签不足；复权口径和 quality 状态也不能靠报告人工阅读解决。

**输入文件**：CR008-S03 Story、`engine/research_dataset.py`、quality/readiness metadata 合同。

**输出文件**：`engine/research_dataset.py`、`engine/quality.py`、`tests/test_cr008_quality_adjustment_label_gates.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| quality gate | reader quality/readiness result | pass/warn/fail | 旧质量报告不得作为替代 |
| adjustment gate | price metadata / adjustment_policy | pass/fail | 同一 dataset 口径不唯一时 fail |
| label window gate | date index、horizon | `label_available_end`、truncated_count | 严肃模式不足时 fail |

**设计约束**：

- `quality_status=pass` 与 PIT available 分离。
- `adjustment_policy` 只能有一个。
- label window 不足不得静默保留末端样本。

**命名规范**：使用 `quality_status`、`adjustment_policy`、`forward_return_horizon`、`label_available_end`、`truncated_sample_count`。

**平台目标**：研究入口 gate engine。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR008-S03 | contract + file-conflict | 需引用 builder result | builder contract frozen；共享文件不可并行开发 | gate 写入 builder 输出 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR008-S04-T1 | 修改 | `engine/research_dataset.py` | 增加 quality/adjustment/label gate result |
| CR008-S04-T2 | 创建/修改 | `engine/quality.py` | 如需要，抽取 gate helper |
| CR008-S04-T3 | 创建 | `tests/test_cr008_quality_adjustment_label_gates.py` | 覆盖 fail、warn、truncate 和 no old report |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr008_quality_adjustment_label_gates.py`。

**验证方式**：tmp ResearchDataset fixture、date index fixture、metadata dict、path sentinel。

**依赖环境**：Python 3.11、uv、pytest；离线。

**关键验证场景**：

- quality fail 阻断严肃研究。
- 复权口径混用 fail。
- label window 不足 fail 或在探索模式截断并写样本损失。
- 旧报告内容读取次数为 0。

## 量化验收标准（acceptance_criteria）

- [ ] quality fail 在严肃研究中继续执行次数为 0。
- [ ] 复权口径混用通过次数为 0。
- [ ] label window 不足时 metadata 100% 写入 `label_available_end`。
- [ ] 旧 `reports/data_quality_report.csv` 内容读取次数为 0。
- [ ] gate 测试覆盖 pass、fail、warn/truncate。

## 阻塞说明

无 BLOCKING。开发需等待 CR008-S03 LLD confirmed 和 CP5 approved。
