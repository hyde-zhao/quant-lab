---
story_id: "CR013-S04-full-history-backfill-roadmap"
title: "full-history backfill roadmap"
story_slug: "full-history-backfill-roadmap"
status: "verified"
priority: "P1"
wave: "CR013-BATCH-A"
depends_on:
  - "CR013-S01-full-history-readiness-gap-register"
  - "CR013-S02-execution-vwap-claim-boundary"
dependency_type:
  - "contract"
dependency_contracts:
  - upstream: "CR013-S01-full-history-readiness-gap-register"
    type: "contract"
    required: "10 dataset remediation、blocked window 和 evidence path 合同冻结"
  - upstream: "CR013-S02-execution-vwap-claim-boundary"
    type: "contract"
    required: "真实 VWAP / minute execution 解除条件和 blocked claims 合同冻结"
file_ownership:
  primary:
    - "docs/DATA-LAKE-FULL-HISTORY-BACKFILL-ROADMAP.md"
    - "reports/data_lake_readiness_2020_2024_cr013/backfill_roadmap.md"
    - "tests/test_cr013_backfill_roadmap_boundaries.py"
  shared: []
  merge_owner: "CR013-S04-full-history-backfill-roadmap"
  forbidden:
    - "market_data/connectors/**"
    - "market_data/storage.py"
    - "/mnt/ugreen-data-lake/**"
    - "data/**"
    - ".env"
    - "reports/data_lake_readiness_2020_2024/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#29.11"
    - "process/HLD-DATA-LAKE.md#16.4"
    - "process/ARCHITECTURE-DECISION.md#adr-044cr-013-limited-window-pass-不得外推为-full-history-production-strict"
    - "process/ARCHITECTURE-DECISION.md#adr-045cr-013-execution--vwap--minute-execution-claims-必须保持-blocked"
    - "process/ARCHITECTURE-DECISION.md#adr-047cr-013-证据保留与权限边界"
    - "process/stories/CR013-S04-full-history-backfill-roadmap.md"
  status: "approved"
  cp5_batch: "CR013-BATCH-A"
  required_before_dev: true
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  cp5_required: true
  implementation_allowed: true
  reason: "CP5 批次人工确认已通过；允许按 LLD 离线实现路线图产物，真实 provider/lake/credential/old data 操作仍必须另行授权。"
created_at: "2026-05-25"
updated_at: "2026-05-25"
cp6_status: "PASS"
cp6_checkpoint: "process/checks/CP6-CR013-S04-full-history-backfill-roadmap-CODING-DONE.md"
cp7_status: "PASS"
cp7_checkpoint: "process/checks/CP7-CR013-S04-full-history-backfill-roadmap-VERIFICATION-DONE.md"
source_hld: "process/HLD.md"
companion_hld: "process/HLD-DATA-LAKE.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-013"
---

# CR013-S04：full-history backfill roadmap

## 目标

制定 2020-2024 full-history backfill roadmap，列出后续补齐 10 个正式 dataset、重新 readiness audit、刷新 unsupported register 和接入真实 VWAP / 分钟数据的授权门、阶段顺序和验收条件。该 Story 只能输出路线图，不授权真实 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 读取或旧报告覆盖。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-08 |
| 需求 | REQ-083、REQ-084、REQ-086、REQ-087 |
| HLD | `process/HLD.md` §29.7、§29.9、§29.11；`process/HLD-DATA-LAKE.md` §16.3、§16.4、§16.5 |
| ADR | ADR-044、ADR-045、ADR-047 |
| Backlog / Plan | `process/STORY-BACKLOG.md` CR013-S04；`process/DEVELOPMENT-PLAN.yaml` wave `CR013-BATCH-A` |

## 开发上下文（dev_context）

**背景说明**：CR-013 当前只证明 full-history blocked 和 execution / unsupported claim boundary，不执行补数。后续如果用户希望解除 `2020-01-01..2024-12-31` blocked 状态，必须先明确补齐范围、权限授权、run/report 命名、证据保留和 readiness audit 解除条件。S04 负责路线图，不负责执行真实数据操作。

**输入文件**：

| 路径 | 用途 | 访问方式 |
|---|---|---|
| `process/HLD.md` | CR-013 阶段和权限边界 | 只读 |
| `process/HLD-DATA-LAKE.md` | 数据湖审计和 future authorization 分类 | 只读 |
| `process/ARCHITECTURE-DECISION.md` | ADR-044 / ADR-045 / ADR-047 | 只读 |
| `process/stories/CR013-S01-full-history-readiness-gap-register.md` | 10 dataset gap register 合同 | 只读 |
| `process/stories/CR013-S02-execution-vwap-claim-boundary.md` | execution / VWAP 解除条件 | 只读 |
| `process/stories/CR013-S03-unsupported-register-and-doc-refresh.md` | unsupported register 声明合同 | 只读 |

**输出文件**：

| 路径 | 说明 |
|---|---|
| `docs/DATA-LAKE-FULL-HISTORY-BACKFILL-ROADMAP.md` | 后续实现阶段新增路线图文档 |
| `reports/data_lake_readiness_2020_2024_cr013/backfill_roadmap.md` | 新增路线图摘要，不覆盖旧报告 |
| `tests/test_cr013_backfill_roadmap_boundaries.py` | 后续实现阶段的最小验证入口 |

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| roadmap builder | S01 gap register、S02 execution boundary、S03 unsupported summary | backfill stages、authorization gates、release criteria、evidence retention policy | 不输出真实 provider 命令、token 或 lake 写入动作 |
| authorization matrix | dataset list、operation kind、risk level | required approval、CP5 gate、forbidden until approved | 未授权时所有真实操作状态为 `not_authorized` |
| evidence retention plan | current evidence paths、future run pattern | new run_id / new report dir rule、`old_baseline_preserved=true` | 禁止覆盖 `reports/data_lake_readiness_2020_2024/*` |

**设计约束**：

- S04 不得把路线图写成可直接执行的 backfill command。
- 任何真实 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 读取、旧报告覆盖都必须另起 Story / CP5 并由用户显式授权。
- full-history pass 的解除条件必须包括：10 个正式 dataset 覆盖 `2020-01-01..2024-12-31`、new readiness audit pass、新 run_id / 新报告、evidence preserved。
- 真实 VWAP / 分钟数据解除条件必须包括：真实 `vwap` 字段、`vwap_status=available`、execution audit pass、对应数据合同和 CP5 批次通过。

**命名规范**：保留 `authorization_required`、`not_authorized`、`future_run_id`、`old_baseline_preserved`、`full_history_release_criteria`、`vwap_release_criteria`。

**平台目标**：本地 Python 因子研究工具；uv 管理依赖；无安装脚本；无 `delivery/**` 输出。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR013-S04-T1 | 创建 | `docs/DATA-LAKE-FULL-HISTORY-BACKFILL-ROADMAP.md` | 输出后续补齐 10 dataset、复验、发布和声明解除条件路线图 |
| CR013-S04-T2 | 创建 | `reports/data_lake_readiness_2020_2024_cr013/backfill_roadmap.md` | 输出路线图摘要和证据保留策略 |
| CR013-S04-T3 | 创建 | `tests/test_cr013_backfill_roadmap_boundaries.py` | 覆盖 roadmap-only、no provider/lake/credential/old data、old evidence preserved |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr013_backfill_roadmap_boundaries.py`。

**验证方式**：roadmap 文档 snapshot、authorization matrix fixture、forbidden command scan、evidence retention sentinel。

**依赖环境**：Python 3.11、uv、pytest；不需要真实 lake、不需要 token、不联网。

**关键验证场景**：

- 路线图列出 10 个正式 dataset 的补齐和新审计解除条件。
- 路线图列出真实 VWAP / 分钟执行价解除条件，且不包含派生真实 VWAP claim。
- 文档中所有真实执行动作状态均为 `authorization_required` 或 `not_authorized`，不包含可直接执行的 provider/lake 命令。
- `old_baseline_preserved=true`，旧证据报告覆盖次数为 0。

## 量化验收标准（acceptance_criteria）

- [ ] 路线图覆盖 10 个正式 dataset 的 2020-2024 补齐、复验、publish 和 release criteria。
- [ ] 路线图覆盖真实 VWAP / 分钟执行价的解除条件，且明确 close proxy / `amount/volume` 不可解除 blocked。
- [ ] 路线图包含新 run_id、新目录或版本化报告规则，并写 `old_baseline_preserved=true`。
- [ ] 路线图中 provider fetch、lake write、credential read、legacy data read、old report overwrite 的当前授权状态均为 `not_authorized`。
- [ ] 默认验证路径的 provider / lake / credential / legacy data / old report 操作计数均为 0。

## 阻塞说明

RESOLVED（2026-05-25）：CR-013 CP3 / CP4 / CP5 已通过，S04 离线实现已完成且 CP6 PASS，当前进入 `ready-for-verification`。OPEN：S04 只制定路线图；真实 backfill、VWAP / 分钟数据接入或 unsupported register 刷新必须另行授权。
