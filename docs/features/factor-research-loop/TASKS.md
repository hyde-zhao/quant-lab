---
status: "draft-current-index"
version: "1.0"
feature_id: "FEAT-03"
---

# Feature Tasks: factor-research-loop

| Task ID | 任务 | 输入 | 输出 | 文件范围 | 验证 |
|---|---|---|---|---|---|
| FEAT-03-T01 | 维护 FactorSpec / FactorRunSpec 合同 | CR-030 HLD / ADR | schema 和错误码 | `engine/multifactor_contracts.py` | CR030 contract tests |
| FEAT-03-T02 | 维护 FactorPanel / LabelWindow gates | CR-011 + CR-030 | fail-closed panel / label policy | `engine/factor_panel_contracts.py` | label window tests |
| FEAT-03-T03 | 维护评价报告与组合器 | factor panel / benchmark / cost | report 和 portfolio plan | `engine/factor_evaluation.py`、`engine/multifactor_combiner.py` | evaluation / combiner tests |
| FEAT-03-T04 | 维护 ExperimentManifest / ReportCatalog | run spec / report path | 可复跑 manifest | `engine/research_manifest.py` | manifest catalog tests |
| FEAT-03-T05 | 维护 StrategyAdmissionPackage | reports / blocked claims | admission package / handoff | `engine/strategy_admission_package.py` | admission package tests |

## 后续触发条件

- 新增因子类别、标签窗口或组合器。
- 将 Qlib / external runner 从 reference 升级为 Spike。
- admission package 要进入 CR-021 simulation 申请输入。

