---
story_id: "CR005-S05"
title: "多源 comparison 与回补文档"
story_slug: "comparison-backfill-docs"
status: "verified"
priority: "P1"
wave: "CR5-W4"
depends_on: ["CR005-S03"]
dependency_contracts:
  - upstream: "CR005-S03"
    type: "contract"
    required: "dataset quality/catalog/readers 输出字段稳定"
file_ownership:
  primary:
    - "tests/test_market_data_tushare_comparison.py"
  shared:
    - "market_data/comparison.py"
    - "README.md"
    - "docs/USER-MANUAL.md"
  merge_owner: "CR005-S05"
  forbidden:
    - "engine/**"
    - "market_data/connectors/tushare.py"
    - "data/**"
    - "reports/**"
    - "delivery/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#227-关键流程"
    - "process/ARCHITECTURE-DECISION.md#adr-012多源校验先稳定接口真实多源比对后置启用"
    - "process/stories/CR005-S05-comparison-backfill-docs.md"
  status: "approved"
  lld_path: "process/stories/CR005-S05-comparison-backfill-docs-LLD.md"
  cp5_auto_result: "process/checks/CP5-CR005-S05-comparison-backfill-docs-LLD-IMPLEMENTABILITY.md"
  cp5_batch: "CR005-BATCH-C-S05-LLD"
  cp5_manual_review: "checkpoints/CP5-CR005-BATCH-B2C-S04-S05-LLD-BATCH.md"
  confirmed_by: "user"
  confirmed_at: "2026-05-17T23:10:12+08:00"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  required_contracts:
    - "CR005-S01 backfill job spec frozen; CR005-S05 does not own job entry implementation"
    - "CR005-S03 quality/catalog fields frozen"
  file_conflict_free: true
  cp5_required: true
  cp5_confirmed: true
  implementation_allowed: true
  implementation_handoff: "process/handoffs/META-DEV-CR005-S05-IMPLEMENT-2026-05-17.md"
created_at: "2026-05-17"
updated_at: "2026-05-17T23:26:20+08:00"
verification_gate:
  cp7_status: "PASS"
  cp7_result: "process/checks/CP7-CR005-S05-comparison-backfill-docs-VERIFICATION-DONE.md"
  verification_handoff: "process/handoffs/META-QA-CR005-S05-CP7-VERIFY-2026-05-17.md"
  verified_by: "meta-po"
  verified_at: "2026-05-17T23:26:20+08:00"
  agent_id: "019e368a-3ad8-7331-b077-0795de00839c"
  agent_name: "qa-hua the 2nd"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-005"
---

# CR005-S05：多源 comparison 与回补文档

## 目标

扩展多源 comparison 输出和用户文档，说明 Tushare 真实启用、显式 backfill、quality gate、catalog、reader 消费边界、`proxy_baseline` 边界和 Backtrader optional backend 的禁用/启用口径。本 Story 不拥有 backfill job 主入口；`market_data/cli.py` 或等价 job 的主契约由 CR005-S01 冻结。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | CR005-AC-009、CR005-AC-010、CR005-AC-015、CR005-AC-016、CR005-AC-019 |
| HLD | §22.7、§22.9 |
| ADR | ADR-012、ADR-013、ADR-016 |

## 开发上下文（dev_context）

**背景说明**：当前 `market_data/comparison.py` 已有 fake/reference 比对契约。CR-005 要把 Tushare 作为可选真实源纳入比对报告和文档，但默认测试仍必须离线。

**输入文件**：`market_data/comparison.py`、`README.md`、`docs/USER-MANUAL.md`、CR005-S01/S03/S04 Story/LLD。

**输出文件**：`market_data/comparison.py`、`README.md`、`docs/USER-MANUAL.md`、`tests/test_market_data_tushare_comparison.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 约束 |
|---|---|---|---|
| comparison | left/right local frames 或 local files | comparison rows / CSV | 默认 fixture，不联网 |
| backfill runbook | CR005-S01 的 job spec、plan/fetch/normalize/validate/catalog/read/compare 流程 | 文档步骤与失败路径 | 只描述用户显式执行；不得写成 resolver 自动触发 |

**设计约束**：

- comparison 只比较本地数据，不在 compare 阶段调用 Tushare。
- backfill runbook 必须说明 `required_missing` 只产生 `remediation_job_spec`，真实写湖只由用户显式执行数据层 job。
- 文档必须说明旧代理只能命名为 `proxy_baseline`，不得填充 `hs300_index` benchmark 字段。
- 文档不得把 Backtrader 描述为默认主框架。
- 文档必须说明 token 不写入文件、默认 pytest 不联网、真实数据不提交。
- 不新增安装脚本，不写 `delivery/**`。

**命名规范**：comparison 字段沿用 `dataset/key/field/left_source/right_source/left_value/right_value/diff/tolerance/status`。

**平台目标**：本地数据湖运维说明与离线 comparison。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR005-S05-T1 | 修改 | `market_data/comparison.py` | 支持 CR-005 dataset 的本地比对字段和状态汇总 |
| CR005-S05-T2 | 修改 | `README.md` | 记录 Tushare 写湖边界、显式 backfill、quality gate、Backtrader optional 和 proxy_baseline 边界 |
| CR005-S05-T3 | 修改 | `docs/USER-MANUAL.md` | 增加真实回补 runbook 和常见失败路径 |
| CR005-S05-T4 | 创建 | `tests/test_market_data_tushare_comparison.py` | 覆盖本地 comparison no-network 和文档 forbidden path 静态检查 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_market_data_tushare_comparison.py`；文档人工审查。

**验证方式**：本地 fixture、CSV 字段断言、静态扫描。

**依赖环境**：Python 3.11、uv、pytest；不需要 token、不联网。

**关键验证场景**：

- 本地 Tushare fixture 与 reference fixture 可输出 comparison rows。
- compare 阶段不导入 connector。
- 文档包含启用条件、显式 backfill、失败路径、回退策略、proxy_baseline 限制和 forbidden path。

## 量化验收标准（acceptance_criteria）

- [x] comparison 输出至少 10 个字段，字段名与 ADR-012 对齐。
- [x] 默认 comparison 测试网络调用次数为 0。
- [x] 文档至少列出 4 类真实启用前置条件：enabled、allowlist、token env、explicit command。
- [x] 文档明确 `required_missing` 不自动联网、不自动 backfill、不自动写湖。
- [x] 文档明确 backfill job 主入口来自 CR005-S01，字段至少覆盖 dataset/source/interface/index_code/date range/lake root/run_id/resume_policy/dry_run/path/error enum。
- [x] 文档至少列出 3 类 Backtrader 限制：optional、不联网、不读 token/connector。
- [x] 文档中将旧代理写为 `proxy_baseline`，且不声明为 hs300 相对收益。
- [x] 不修改 `engine/**`、`market_data/connectors/tushare.py`、真实 `data/**` 或 `reports/**`。

## 阻塞说明

无 BLOCKING。真实多源联网比对仍需用户确认数据源配额和字段口径；本 Story 只稳定本地 comparison 与文档。

## LLD / CP5 状态

- 状态：CP5 批次人工确认已通过，S05 已完成实现、CP6 与 CP7，并收敛为 `verified`。
- LLD：`process/stories/CR005-S05-comparison-backfill-docs-LLD.md`。
- CP5 自动预检：`process/checks/CP5-CR005-S05-comparison-backfill-docs-LLD-IMPLEMENTABILITY.md`，结论 `PASS`，OPEN 项 4 个。
- CP5 批次人工确认：`checkpoints/CP5-CR005-BATCH-B2C-S04-S05-LLD-BATCH.md`，结论 `approved`，reviewed_by=`user`，reviewed_at=`2026-05-17T23:10:12+08:00`。
- 调度证据：`process/handoffs/META-DEV-CR005-S05-LLD-2026-05-17.md` 记录主线程真实 `spawn_agent` 调度 meta-dev/dev-he the 2nd，agent_id/thread_id=`019e3670-7370-7690-a15d-5debb33342ad`。
- 边界：实现范围严格限定为 `market_data/comparison.py`、`README.md`、`docs/USER-MANUAL.md`、`tests/test_market_data_tushare_comparison.py`、S05 CP6、S05 Story 和本 handoff；未修改 S04 文件、STATE、STORY-STATUS、DEV-LOG、真实 `data/**`、`reports/**`、`delivery/**`、`pyproject.toml` 或 `uv.lock`。

## 实现 / CP6 状态

- 状态：CP6 `PASS`，已进入并完成 CP7 验证。
- CP6：`process/checks/CP6-CR005-S05-comparison-backfill-docs-CODING-DONE.md`，结论 `PASS`。
- 实现文件：`market_data/comparison.py`、`README.md`、`docs/USER-MANUAL.md`、`tests/test_market_data_tushare_comparison.py`。
- 验证命令：
  - `UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_market_data_tushare_comparison.py`：`5 passed in 0.90s`。
  - `UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_market_data_tushare_comparison.py tests/test_market_data_multidataset_quality_readers.py`：`14 passed in 0.59s`。
  - `UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_market_data_cli_comparison.py`：`6 passed in 0.55s`。
- 交接：meta-qa 已完成 CP7，Story 已标记为 `verified`。

## 验证完成状态

| 项目 | 内容 |
|---|---|
| CP7 | `process/checks/CP7-CR005-S05-comparison-backfill-docs-VERIFICATION-DONE.md` |
| QA handoff | `process/handoffs/META-QA-CR005-S05-CP7-VERIFY-2026-05-17.md` |
| QA agent | `qa-hua the 2nd` / `019e368a-3ad8-7331-b077-0795de00839c` |
| 目标测试 | `5 passed` |
| 最小回归 | `14 passed` |
| comparison CLI 回归 | `6 passed` |
| 全量离线回归 | `90 passed` |
| 结论 | `PASS`；无 BLOCKING / REQUIRED 失败项 |
