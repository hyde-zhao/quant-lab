---
story_id: "CR007-S05-data-quality-report-and-doc-guardrail"
title: "质量报告与文档护栏"
story_slug: "data-quality-report-and-doc-guardrail"
status: "verified"
priority: "P1"
wave: "CR007-BATCH-A"
depends_on:
  - "CR007-S01-prices-long-horizon-backfill-planner"
  - "CR007-S02-benchmark-calendar-backfill"
  - "CR007-S03-index-members-stock-basic-datasets"
  - "CR007-S04-experiment-real-benchmark-consumption"
dependency_contracts:
  - upstream: "CR007-S01-prices-long-horizon-backfill-planner"
    type: "contract"
    required: "long-horizon coverage 字段和 dry-run 边界已冻结"
  - upstream: "CR007-S02-benchmark-calendar-backfill"
    type: "contract"
    required: "benchmark/calendar coverage 与 BenchmarkResult missing 语义已冻结"
  - upstream: "CR007-S03-index-members-stock-basic-datasets"
    type: "contract"
    required: "dataset readiness 与 PIT 状态字段已冻结"
  - upstream: "CR007-S04-experiment-real-benchmark-consumption"
    type: "contract"
    required: "实验 benchmark 与 proxy_baseline 命名已冻结"
file_ownership:
  primary:
    - "tests/test_cr007_quality_report_doc_guardrail.py"
  shared:
    - "README.md"
    - "docs/USER-MANUAL.md"
    - ".gitignore"
  merge_owner: "CR007-S05-data-quality-report-and-doc-guardrail"
  forbidden:
    - "engine/**"
    - "experiments/**"
    - "market_data/connectors/**"
    - "market_data/runtime.py"
    - "market_data/storage.py"
    - "data/**"
    - "reports/**"
    - ".env"
    - "credentials"
    - "delivery/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#2413-gotchas"
    - "process/ARCHITECTURE-DECISION.md#adr-022旧质量报告作为-legacy当前质量真相源为-lake-qualitycatalog"
    - "process/stories/CR007-S05-data-quality-report-and-doc-guardrail.md"
  status: "cp5-approved"
  cp5_batch: "CR007-BATCH-A"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  blocked_by: ""
  unblock_condition: "satisfied: CR007-S01/S02/S03/S04 CP7 PASS and CR008-BATCH-A all stories verified"
  required_contracts:
    - "legacy quality report policy frozen"
    - "lake quality/catalog current truth wording frozen"
    - "CR007-BATCH-A CP5 approved"
  file_conflict_free: true
  cp5_required: true
  implementation_allowed: true
  implementation_scope: "offline-only"
  dev_handoff: "process/handoffs/META-DEV-CR007-S05-IMPLEMENT-2026-05-22.md"
  dev_agent_name: "dev-he the 2nd"
  dev_agent_id: "019e4c70-0aa3-77b2-8d98-415d8b4a19c8"
  dev_started_at: "2026-05-22T05:27:55+08:00"
  dev_completed_at: "2026-05-22T05:33:16+08:00"
  cp6_status: "PASS"
  cp6_checkpoint: "process/checks/CP6-CR007-S05-data-quality-report-and-doc-guardrail-CODING-DONE.md"
  cp6_completed_at: "2026-05-22T05:33:16+08:00"
  cp6_blocker: "resolved: CR008 experiment_15 report metadata missing conservative unavailable statement"
  blocker_fix_handoff: "process/handoffs/META-DEV-CR007-S05-CR008-REPORT-METADATA-BLOCKER-FIX-2026-05-22.md"
  blocker_fix_agent_name: "dev-you the 2nd"
  blocker_fix_agent_id: "019e4c83-9732-73f3-b60a-64ab6962d9f8"
  blocker_fix_started_at: "2026-05-22T05:49:18+08:00"
  blocker_fix_completed_at: "2026-05-22T05:51:44+08:00"
  blocker_fix_cp6_status: "PASS"
  blocker_fix_cp6_checkpoint: "process/checks/CP6-CR007-S05-CR008-REPORT-METADATA-BLOCKER-FIX-CODING-DONE.md"
  cp7_status: "PASS"
  cp7_handoff: "process/handoffs/META-QA-CR007-S05-CP7-VERIFY-2026-05-22.md"
  cp7_agent_name: "qa-he the 2nd"
  cp7_agent_id: "019e4c8d-025b-7e31-8c2e-e05648421a7c"
  cp7_started_at: "2026-05-22T05:59:32+08:00"
  cp7_completed_at: "2026-05-22T06:13:53+08:00"
  cp7_checkpoint: "process/checks/CP7-CR007-S05-data-quality-report-and-doc-guardrail-VERIFICATION-DONE.md"
  verified_at: "2026-05-22T06:16:28+08:00"
  upstream_cp7:
    - "process/checks/CP7-CR007-S01-prices-long-horizon-backfill-planner-VERIFICATION-DONE.md"
    - "process/checks/CP7-CR007-S02-benchmark-calendar-backfill-VERIFICATION-DONE.md"
    - "process/checks/CP7-CR007-S03-index-members-stock-basic-datasets-VERIFICATION-DONE.md"
    - "process/checks/CP7-CR007-S04-experiment-real-benchmark-consumption-VERIFICATION-DONE.md"
    - "process/checks/CP7-CR008-S06-factor-research-auxiliary-data-contract-VERIFICATION-DONE.md"
created_at: "2026-05-20"
updated_at: "2026-05-22T06:16:28+08:00"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-007"
---

# CR007-S05：质量报告与文档护栏

## 目标

更新 README、USER-MANUAL 和 guardrail，明确旧 `reports/data_quality_report.csv` 是 legacy old report，不再作为 canonical lake 当前质量真相源；当前质量真相源必须来自 configured lake root 下的 `quality/catalog`。该 Story 不覆盖旧报告、不读取旧报告内容、不操作旧 `data/**`。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | CR007-AC-012、CR007-AC-013 |
| HLD | §24.7、§24.10、§24.13 |
| ADR | ADR-022 |

## 开发上下文（dev_context）

**背景说明**：旧 `reports/data_quality_report.csv` 与当前 canonical/gold lake 不是同一质量面。CR-007 要求避免把旧报告当作当前 coverage 或 quality 证明，同时继续保留旧报告文件本身作为 legacy 线索。

**输入文件**：`README.md`、`docs/USER-MANUAL.md`、`.gitignore`、现有 guardrail 测试、CR007-S01..S04 Story。

**输出文件**：`README.md`、`docs/USER-MANUAL.md`、`.gitignore`、`tests/test_cr007_quality_report_doc_guardrail.py`。

**接口约定**：

| 接口 / 文档面 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| docs quality truth | CR007 dataset coverage policy | 文档说明 lake `quality/catalog` 是当前质量真相源 | 不读取旧报告内容 |
| legacy report notice | 旧报告路径文本 | legacy warning 和禁止用作 coverage proof | 不覆盖旧报告 |
| guardrail | allowlisted text files | 静态断言 required / forbidden phrases | 不扫描 `data/**` 或 `reports/**` 内容 |

**设计约束**：

- `reports/data_quality_report.csv` 可被提及为 legacy，但不得读取内容、覆盖或用作 fixture。
- 当前 coverage 声明必须要求 dataset、start/end、denominator、run_id/source/interface、quality_status 和 lineage。
- guardrail 只能扫描 allowlisted text 文件。
- 不修改 `engine/**`、`experiments/**`、`market_data` 数据层实现、真实 `data/**`、真实 `reports/**`、`.env` 或 `delivery/**`。

**命名规范**：使用 `legacy old report`、`lake quality/catalog`、`current quality truth`、`coverage proof forbidden`。

**平台目标**：文档与静态护栏。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR007-S05-T1 | 修改 | `README.md` | 增加 CR-007 coverage、benchmark、legacy report 和 quality/catalog 说明 |
| CR007-S05-T2 | 修改 | `docs/USER-MANUAL.md` | 增加用户运行边界、真实授权和 legacy report 注意事项 |
| CR007-S05-T3 | 修改 | `.gitignore` | 如缺少 reports/data/lake 相关忽略规则则补齐 |
| CR007-S05-T4 | 创建 | `tests/test_cr007_quality_report_doc_guardrail.py` | 覆盖 required/forbidden phrases、allowlist、no old data/no reports content scan |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr007_quality_report_doc_guardrail.py`。

**验证方式**：静态文本扫描、allowlist 检查、forbidden phrase 检查。

**依赖环境**：Python 3.11、uv、pytest；不需要 Tushare token、不需要 NAS、不联网。

**关键验证场景**：

- README / USER-MANUAL 声明旧报告是 legacy。
- 文档声明当前 quality truth 来自 lake `quality/catalog`。
- 文档禁止旧报告作为 coverage proof。
- guardrail 不读取 `data/**` 或 `reports/**` 内容。

## 量化验收标准（acceptance_criteria）

- [ ] 文档至少出现 3 类 required phrase：legacy quality report、lake quality/catalog current truth、coverage proof forbidden。
- [ ] 旧 `reports/data_quality_report.csv` 覆盖、读取或作为 fixture 的次数为 0。
- [ ] guardrail allowlist 中 `data/**` 和 `reports/**` 条目数量为 0。
- [ ] `.env`、token、NAS 凭据读取或打印次数为 0。
- [ ] 不修改 `engine/**`、`experiments/**`、`market_data/connectors/**`、真实 `data/**`、真实 `reports/**`、`delivery/**`。

## 阻塞说明

无 BLOCKING。若用户希望删除或覆盖旧质量报告，必须另行授权并新建变更；当前默认只做 legacy 标记和 guardrail。
