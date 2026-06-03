---
story_id: "CR030-S06-experiment-manifest-report-catalog"
title: "ExperimentManifest / ResearchReportCatalog 追踪"
story_slug: "experiment-manifest-report-catalog"
status: "verified"
priority: "P0"
wave: "CR030-W3-COMBINATION-MANIFEST"
depends_on:
  - "CR030-S04-factor-evaluation-report"
dependency_type:
  - upstream: "CR030-S04-factor-evaluation-report"
    type: "evaluation-report-contract"
cp5_batch: "CR030-MULTIFACTOR-RESEARCH-LOOP-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "engine/research_manifest.py"
    - "reports/research_catalog/**"
    - "tests/test_cr030_experiment_manifest_catalog.py"
  shared:
    - "engine/factor_evaluation.py"
    - "reports/factor_evaluation/**"
  merge_owner: "CR030-S06-experiment-manifest-report-catalog"
  forbidden:
    - "MLflow default truth"
    - "pickle recorder default truth"
    - "catalog publish"
    - "old reports overwrite"
    - "pyproject.toml"
    - "uv.lock"
lld_gate:
  required_inputs:
    - "process/HLD.md#35.6"
    - "process/HLD.md#35.8"
    - "process/ARCHITECTURE-DECISION.md#ADR-084"
    - "process/stories/CR030-S06-experiment-manifest-report-catalog.md"
  status: "approved"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  dependency_change_allowed: false
  catalog_publish_allowed: false
  credential_read_allowed: false
task_count: 5
created_at: "2026-06-03T08:30:00+08:00"
updated_at: "2026-06-03T10:47:33+08:00"
change_id: "CR-030"
dev_dispatch:
  mode: "spawn_agent"
  agent_id: "019e8b4e-a6e3-71f0-9e60-df022490ef26"
  agent_name: "dev-xu"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-06-03T10:27:37+08:00"
  completed_at: "2026-06-03T10:34:13+08:00"
  closed_at: "2026-06-03T10:37:16+08:00"
  cp6_checkpoint: "process/checks/CP6-CR030-S06-experiment-manifest-report-catalog-CODING-DONE.md"
  handoff_path: "process/handoffs/META-DEV-CR030-S06-IMPLEMENT-2026-06-03.md"
  cp6_status: "PASS"
qa_dispatch:
  mode: "spawn_agent"
  agent_id: "019e8b5b-e30a-7641-aaf2-0aa22f9860cb"
  agent_name: "qa-cao"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-06-03T10:42:02+08:00"
  completed_at: "2026-06-03T10:44:24+08:00"
  closed_at: "2026-06-03T10:47:06+08:00"
  cp7_checkpoint: "process/checks/CP7-CR030-S06-experiment-manifest-report-catalog-VERIFICATION-DONE.md"
  handoff_path: "process/handoffs/META-QA-CR030-S06-CP7-VERIFY-2026-06-03.md"
  cp7_status: "PASS"
---

# CR030-S06：ExperimentManifest / ResearchReportCatalog 追踪

## 目标

定义 `ExperimentManifest` 与 `ResearchReportCatalog`，确保研究 run 可复跑、可比较、可审计，并能为 `StrategyAdmissionPackage` 提供来源证据。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-26、TS-030-07 |
| 需求 | REQ-180、REQ-182、REQ-185 |
| HLD | `process/HLD.md` §35.6、§35.8、§35.13 |
| ADR | ADR-084 |

## 开发上下文（dev_context）

**背景说明**：多因子研究输出需要保留 run_id、配置、数据 release、因子版本、标签窗口、成本、代码版本和 artifact 关系。CR-030 默认采用 JSON/CSV/Markdown artifact，不采用 MLflow / pickle recorder 作为事实源。

**输入文件**：CR030-S04 评价报告合同、HLD §35、ADR-084、本 Story 卡片。

**输出文件**：`engine/research_manifest.py`、`reports/research_catalog/**`、`tests/test_cr030_experiment_manifest_catalog.py`。

**接口约定**：

| 合同项 | 要求 |
|---|---|
| ExperimentManifest | `run_id`、`strategy_id`、`config_hash`、dataset/release、factor versions、label window、benchmark、cost、seed、code version |
| ResearchReportCatalog | report paths、artifact refs、allowed_claims、blocked_claims、limitations、evidence refs |
| admission gate | 缺 P0 字段不得进入 StrategyAdmissionPackage |
| artifact truth | JSON/CSV/Markdown + path refs；不采用 MLflow / pickle 默认 truth |

**设计约束**：不 publish current pointer；不覆盖旧 reports；不写真实 lake。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR030-S04 | evaluation-report-contract | 评价报告 artifact 字段冻结 | 报告 catalog 字段需与 S04 串行合并 | catalog 索引评价报告 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `engine/research_manifest.py`、`reports/research_catalog/**`、`tests/test_cr030_experiment_manifest_catalog.py` | 当前 Story 独占 |
| shared | `engine/factor_evaluation.py`、`reports/factor_evaluation/**` | 与 S04 合并 report path 字段 |
| forbidden | MLflow / pickle truth、publish、旧报告覆盖、依赖 | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR030-S06-T1 | 设计 | `engine/research_manifest.py` | 定义 manifest / catalog 数据合同 |
| CR030-S06-T2 | 设计 | `reports/research_catalog/**` | 设计 catalog JSON/CSV/Markdown artifact 形态 |
| CR030-S06-T3 | 设计 | `tests/test_cr030_experiment_manifest_catalog.py` | 设计 config hash、artifact refs、缺 P0 字段 blocked 测试 |
| CR030-S06-T4 | 约束 | old reports | 旧报告只读保留，不覆盖 |
| CR030-S06-T5 | 约束 | publish boundary | 明确 catalog 是研究报告索引，不 publish current pointer |

## 验证上下文（validation_context）

**验证入口**：后续 LLD 可建议 `uv run --python 3.11 pytest -q tests/test_cr030_experiment_manifest_catalog.py`，但本阶段不执行。

**验证方式**：manifest 字段完整性测试、catalog 查询测试、admission 前置字段缺失测试。

**依赖环境**：本地 artifact fixture；不得写真实 lake、publish 或读取凭据。

**关键验证场景**：

| 场景 | 预期 |
|---|---|
| 完整 run manifest | 可由 run_id 查询报告和 claims |
| 缺 config_hash / data release | 不得进入 admission |
| 旧 reports 存在 | 不覆盖，保留引用边界 |
| MLflow / pickle 默认 truth | 测试失败 |

## 量化验收标准（acceptance_criteria）

- [ ] manifest/catalog P0 字段覆盖率为 100%。
- [ ] 缺任一 P0 字段进入 StrategyAdmissionPackage 次数为 0。
- [ ] 旧报告 overwrite 次数为 0。
- [ ] catalog publish / lake write 次数为 0。
- [ ] MLflow / pickle recorder 作为默认 truth 次数为 0。

## 阻塞说明

本 Story 必须等待 S04 合同冻结和 CP5 全量 LLD 确认。若后续需要外部 recorder，应另起 adapter / Spike。
