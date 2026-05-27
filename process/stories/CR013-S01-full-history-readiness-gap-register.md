---
story_id: "CR013-S01-full-history-readiness-gap-register"
title: "full-history readiness gap register"
story_slug: "full-history-readiness-gap-register"
status: "verified"
priority: "P0"
wave: "CR013-BATCH-A"
depends_on:
  - "CR011-S08-factor-panel-audit-and-robust-validation"
dependency_type:
  - "contract"
dependency_contracts:
  - upstream: "CR011-S08-factor-panel-audit-and-robust-validation"
    type: "contract"
    required: "CR011 closed 后的报告声明、allowed_claims / blocked_claims 和旧报告保护基线已冻结"
file_ownership:
  primary:
    - "reports/data_lake_readiness_2020_2024_cr013/full_history_gap_register.csv"
    - "reports/data_lake_readiness_2020_2024_cr013/full_history_gap_summary.md"
    - "tests/test_cr013_full_history_gap_register.py"
  shared: []
  merge_owner: "CR013-S01-full-history-readiness-gap-register"
  forbidden:
    - "reports/data_lake_readiness_2020_2024/readiness_summary.md"
    - "reports/data_lake_readiness_2020_2024/readiness_matrix.csv"
    - "reports/data_lake_readiness_2020_2024/data_validity_assessment.md"
    - "reports/data_lake_readiness_2020_2024/execution_price_audit.csv"
    - "reports/data_lake_readiness_limited_2025_2026/unsupported_data_register.csv"
    - "/mnt/ugreen-data-lake/**"
    - "data/**"
    - ".env"
lld_gate:
  required_inputs:
    - "process/HLD.md#29.1"
    - "process/HLD-DATA-LAKE.md#16.2"
    - "process/ARCHITECTURE-DECISION.md#adr-044cr-013-limited-window-pass-不得外推为-full-history-production-strict"
    - "process/ARCHITECTURE-DECISION.md#adr-047cr-013-证据保留与权限边界"
    - "process/stories/CR013-S01-full-history-readiness-gap-register.md"
  status: "approved"
  cp5_batch: "CR013-BATCH-A"
  required_before_dev: true
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  cp5_required: true
  implementation_allowed: true
  reason: "CP5 批次人工确认已通过；允许按 LLD 离线实现 S01，不授权 provider fetch、真实 lake 写入、凭据读取、旧 data 读取或旧报告覆盖。"
created_at: "2026-05-25"
updated_at: "2026-05-25"
cp6_status: "PASS"
cp6_checkpoint: "process/checks/CP6-CR013-S01-full-history-readiness-gap-register-CODING-DONE.md"
cp7_status: "PASS"
cp7_checkpoint: "process/checks/CP7-CR013-S01-full-history-readiness-gap-register-VERIFICATION-DONE.md"
source_hld: "process/HLD.md"
companion_hld: "process/HLD-DATA-LAKE.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-013"
---

# CR013-S01：full-history readiness gap register

## 目标

建立 `2020-01-01..2024-12-31` full-history readiness gap register，固化 10 个正式 dataset 的 `limited_window_only`、`target_window_not_covered` / `coverage_denominator_empty`、remediation 和 evidence paths。该 Story 保留 CR-012 limited-window pass 作为窗口级结论，但阻止它被外推为 2020-2024 full-history production strict。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-08 |
| 需求 | REQ-083、REQ-086、REQ-087 |
| HLD | `process/HLD.md` §29.1、§29.4、§29.6、§29.7；`process/HLD-DATA-LAKE.md` §16.1、§16.2、§16.3 |
| ADR | ADR-044、ADR-047 |
| Backlog / Plan | `process/STORY-BACKLOG.md` CR013-S01；`process/DEVELOPMENT-PLAN.yaml` wave `CR013-BATCH-A` |

## 开发上下文（dev_context）

**背景说明**：CR-012 limited-window 审计已通过，但 `reports/data_lake_readiness_2020_2024/readiness_summary.md` 显示 `overall_status=research_limited_only`，`readiness_matrix.csv` 中 10 个正式 dataset 均为 `limited_window_only`。研究报告和用户文档必须同时表达 supported window 与 blocked window，不能把 `2025-02-11..2026-02-18` 的通过结论外推到 `2020-01-01..2024-12-31`。

**输入文件**：

| 路径 | 用途 | 访问方式 |
|---|---|---|
| `process/HLD.md` | 读取 CR-013 研究消费边界 | 只读 |
| `process/HLD-DATA-LAKE.md` | 读取数据湖审计合同 | 只读 |
| `process/ARCHITECTURE-DECISION.md` | 读取 ADR-044 / ADR-047 | 只读 |
| `process/REQUIREMENTS.md` | 读取 REQ-083 / REQ-087 | 只读 |
| `reports/data_lake_readiness_2020_2024/readiness_summary.md` | full-history 总体证据 | 只读，不覆盖 |
| `reports/data_lake_readiness_2020_2024/readiness_matrix.csv` | 10 dataset 明细证据 | 只读，不覆盖 |
| `reports/data_lake_readiness_2020_2024/data_validity_assessment.md` | CR-012 pass 与 full-history blocked 边界 | 只读，不覆盖 |

**输出文件**：

| 路径 | 说明 |
|---|---|
| `reports/data_lake_readiness_2020_2024_cr013/full_history_gap_register.csv` | 新增版本化 gap register；不得覆盖旧报告 |
| `reports/data_lake_readiness_2020_2024_cr013/full_history_gap_summary.md` | 新增 full-history blocked 摘要 |
| `tests/test_cr013_full_history_gap_register.py` | 后续实现阶段的最小验证入口 |

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| gap register builder | readiness summary、readiness matrix | `dataset`、`final_status`、`issue_code`、`issue_category`、`remediation`、`evidence_path`、`target_window_covered` | 证据缺失或任一 dataset 不可判定时 fail-fast，不推断 pass |
| claim boundary summary | gap register、CR-012 limited-window metadata | `supported_window`、`blocked_window`、`full_history_status`、`dataset_status_counts` | full-history production strict allowed claim 必须为 0 |
| evidence guard | evidence paths、old baseline status | `old_baseline_preserved=true`、`old_report_overwrites=0` | 不覆盖 `reports/data_lake_readiness_2020_2024/*` |

**设计约束**：

- 10 个正式 dataset 固定为 `prices`、`adj_factor`、`hs300_index`、`trade_calendar`、`index_members`、`index_weights`、`stock_basic`、`trade_status`、`prices_limit`、`events`。
- `2025-02-11..2026-02-18` 可以声明为 supported limited window；`2020-01-01..2024-12-31` 必须声明为 blocked / research_limited_only。
- 不执行 provider fetch，不读取凭据，不写真实 lake，不读取旧 `data/**`，不覆盖旧证据报告。
- 本 Story 不修改 README、USER-MANUAL 或代码，除非后续 LLD / CP5 明确批准实现范围。

**命名规范**：保留 `supported_window`、`blocked_window`、`full_history_status`、`dataset_status_counts`、`target_window_covered`、`old_baseline_preserved`、`evidence_paths`。

**平台目标**：本地 Python 因子研究工具；uv 管理依赖；无安装脚本；无 `delivery/**` 输出。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR013-S01-T1 | 创建 | `reports/data_lake_readiness_2020_2024_cr013/full_history_gap_register.csv` | 从只读 readiness matrix 派生 10 dataset gap register |
| CR013-S01-T2 | 创建 | `reports/data_lake_readiness_2020_2024_cr013/full_history_gap_summary.md` | 输出 supported / blocked window 和 full-history claim boundary |
| CR013-S01-T3 | 创建 | `tests/test_cr013_full_history_gap_register.py` | 覆盖 10 dataset 完整性、full-history allowed claim=0、old evidence overwrite=0 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr013_full_history_gap_register.py`。

**验证方式**：只读 fixture / snapshot 检查 readiness summary 与 matrix；断言 10 个 dataset 全覆盖、status counts 正确、blocked window 正确、旧证据未覆盖。

**依赖环境**：Python 3.11、uv、pytest；不需要真实 lake、不需要 token、不联网。

**关键验证场景**：

- 10 个正式 dataset 均进入 gap register。
- `supported_window=2025-02-11..2026-02-18`，`blocked_window=2020-01-01..2024-12-31`。
- full-history production strict allowed claim 输出次数为 0。
- `provider_fetches=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_reads=0`、`old_report_overwrites=0`。

## 量化验收标准（acceptance_criteria）

- [ ] gap register 包含 10 个正式 dataset，且每行含 `dataset`、`final_status`、`issue_code`、`issue_category`、`remediation`、`evidence_path`。
- [ ] 10 个 dataset 的 `final_status` 均为 `limited_window_only` 或等价 blocked 状态，不输出 full-history pass。
- [ ] summary 明确同时输出 supported window 与 blocked window。
- [ ] `old_baseline_preserved=true`，旧 `reports/data_lake_readiness_2020_2024/*` 覆盖次数为 0。
- [ ] 默认验证路径的 provider / lake / credential / legacy data / old report 操作计数均为 0。

## 阻塞说明

RESOLVED（2026-05-25）：CR-013 CP3 / CP4 / CP5 已通过，S01 离线实现已完成且 CP6 PASS，当前进入 `ready-for-verification`。OPEN：任何真实 full-history backfill 必须另行 Story / CP5 / 用户授权。
