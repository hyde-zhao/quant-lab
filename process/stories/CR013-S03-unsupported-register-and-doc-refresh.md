---
story_id: "CR013-S03-unsupported-register-and-doc-refresh"
title: "unsupported register and docs refresh"
story_slug: "unsupported-register-and-doc-refresh"
status: "verified"
priority: "P0"
wave: "CR013-BATCH-A"
depends_on:
  - "CR013-S01-full-history-readiness-gap-register"
  - "CR013-S02-execution-vwap-claim-boundary"
dependency_type:
  - "contract"
dependency_contracts:
  - upstream: "CR013-S01-full-history-readiness-gap-register"
    type: "contract"
    required: "supported_window / blocked_window / full_history_status 合同冻结"
  - upstream: "CR013-S02-execution-vwap-claim-boundary"
    type: "contract"
    required: "execution/VWAP blocked claims 与解除条件冻结"
file_ownership:
  primary:
    - "README.md"
    - "docs/USER-MANUAL.md"
    - "reports/data_lake_readiness_2020_2024_cr013/unsupported_claim_boundary_summary.md"
    - "tests/test_cr013_unsupported_register_claim_boundary.py"
  shared:
    - "experiments/reporting.py"
  merge_owner: "CR013-S03-unsupported-register-and-doc-refresh"
  forbidden:
    - "reports/data_lake_readiness_limited_2025_2026/unsupported_data_register.csv"
    - "reports/data_lake_readiness_2020_2024/**"
    - "/mnt/ugreen-data-lake/**"
    - "data/**"
    - ".env"
lld_gate:
  required_inputs:
    - "process/HLD.md#29.5"
    - "process/HLD-DATA-LAKE.md#16.2"
    - "process/ARCHITECTURE-DECISION.md#adr-046cr-013-unsupported-register-是正式声明边界输入"
    - "process/ARCHITECTURE-DECISION.md#adr-047cr-013-证据保留与权限边界"
    - "process/stories/CR013-S03-unsupported-register-and-doc-refresh.md"
  status: "approved"
  cp5_batch: "CR013-BATCH-A"
  required_before_dev: true
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  cp5_required: true
  implementation_allowed: true
  reason: "CP5 批次人工确认已通过；允许在 S01/S02 合同冻结后按 LLD 离线实现 S03，不授权 provider fetch、真实 lake 写入、凭据读取、旧 data 读取或旧报告覆盖。"
created_at: "2026-05-25"
updated_at: "2026-05-25"
cp6_status: "PASS"
cp6_checkpoint: "process/checks/CP6-CR013-S03-unsupported-register-and-doc-refresh-CODING-DONE.md"
cp7_status: "PASS"
cp7_checkpoint: "process/checks/CP7-CR013-S03-unsupported-register-and-doc-refresh-VERIFICATION-DONE.md"
source_hld: "process/HLD.md"
companion_hld: "process/HLD-DATA-LAKE.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-013"
---

# CR013-S03：unsupported register and docs refresh

## 目标

把 `unsupported_data_register.csv` 的 research-only / unsupported / contract-supported-but-unavailable 项纳入 README、USER-MANUAL、readiness summary 和新版研究报告的正式声明边界。所有 `pass_denominator=excluded` 项不得计入正式 dataset pass 分母或 allowed production claim。本轮只定义 Story 和后续 LLD 输入，不修改 README、docs 或报告证据。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-08 |
| 需求 | REQ-085、REQ-086、REQ-087 |
| HLD | `process/HLD.md` §29.1、§29.5、§29.6、§29.8；`process/HLD-DATA-LAKE.md` §16.2、§16.3、§16.4 |
| ADR | ADR-046、ADR-047 |
| Backlog / Plan | `process/STORY-BACKLOG.md` CR013-S03；`process/DEVELOPMENT-PLAN.yaml` wave `CR013-BATCH-A` |

## 开发上下文（dev_context）

**背景说明**：unsupported register 当前包含 9 行，其中行业、市值、风格暴露是 `research_contract_only`，capacity、完整公司行动、非 HS300 benchmark、分钟 / tick / Level2 / 撮合、microstructure impact cost 是 `unsupported`，真实 VWAP 是 `contract_supported_but_unavailable`。这些项均为 `pass_denominator=excluded`。若文档和报告没有统一消费 register，用户会把它们误读为已发布 production dataset 或 production strict supported capability。

**输入文件**：

| 路径 | 用途 | 访问方式 |
|---|---|---|
| `process/HLD.md` | CR-013 声明边界 | 只读 |
| `process/HLD-DATA-LAKE.md` | unsupported register 数据湖合同 | 只读 |
| `process/ARCHITECTURE-DECISION.md` | ADR-046 / ADR-047 | 只读 |
| `process/stories/CR013-S01-full-history-readiness-gap-register.md` | supported / blocked window 合同 | 只读 |
| `process/stories/CR013-S02-execution-vwap-claim-boundary.md` | execution / VWAP blocked 合同 | 只读 |
| `reports/data_lake_readiness_limited_2025_2026/unsupported_data_register.csv` | unsupported register 证据 | 只读，不覆盖 |

**输出文件**：

| 路径 | 说明 |
|---|---|
| `README.md` | 后续实现阶段刷新用户可见声明 |
| `docs/USER-MANUAL.md` | 后续实现阶段刷新用户手册声明 |
| `reports/data_lake_readiness_2020_2024_cr013/unsupported_claim_boundary_summary.md` | 新增 register 摘要，不覆盖旧证据 |
| `tests/test_cr013_unsupported_register_claim_boundary.py` | 后续实现阶段的最小验证入口 |

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| unsupported register reader | `data_item`、`status`、`reason`、`pass_denominator` | 9 行 structured register | 缺行或缺字段时 fail，不用自由文本补齐 |
| claim summary builder | register rows、S01/S02 claim boundary | supported / research-only / unsupported / blocked 摘要 | excluded 项不计 formal pass denominator |
| docs/report consumer | claim summary、evidence paths、permission counters | README / USER-MANUAL / report summary 文案和 metadata | 不覆盖旧证据；不声明 unsupported 项 available |

**设计约束**：

- 必须覆盖 9 个 data_item：`industry_classification`、`market_cap`、`style_exposure_beta_size_value_quality`、`capacity_inputs_turnover_adv_constraints`、`corporate_actions_full`、`non_hs300_benchmark`、`minute_tick_level2_order_match`、`microstructure_impact_cost`、`real_vwap_execution`。
- `research_contract_only` 只能声明为研究合同候选，不是正式 current truth。
- `unsupported` 和 `contract_supported_but_unavailable` 必须进入 unsupported / blocked claim。
- `pass_denominator=excluded` 不得计入 10 个正式 dataset 的 pass 分母。
- 本轮不修改 README、USER-MANUAL、报告证据、代码或测试；真实实现需等 CP5。

**命名规范**：保留 `unsupported_data_items`、`research_only_items`、`blocked_claims`、`pass_denominator_policy`、`excluded_from_pass_denominator`、`claim_boundary_summary`。

**平台目标**：本地 Python 因子研究工具；uv 管理依赖；无安装脚本；无 `delivery/**` 输出。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR013-S03-T1 | 创建 | `reports/data_lake_readiness_2020_2024_cr013/unsupported_claim_boundary_summary.md` | 输出 9 行 register 的 research-only / unsupported / blocked 摘要 |
| CR013-S03-T2 | 修改 | `README.md` | 后续实现阶段刷新 supported / unsupported / blocked claim 用户可见说明 |
| CR013-S03-T3 | 修改 | `docs/USER-MANUAL.md` | 后续实现阶段刷新用户手册的 full-history、VWAP 和 unsupported register 边界 |
| CR013-S03-T4 | 修改 | `experiments/reporting.py` | 后续实现阶段将 register 摘要纳入新版研究报告 metadata |
| CR013-S03-T5 | 创建 | `tests/test_cr013_unsupported_register_claim_boundary.py` | 覆盖 9 行 register 完整性、excluded denominator、old evidence overwrite=0 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr013_unsupported_register_claim_boundary.py`。

**验证方式**：register fixture、docs/report metadata snapshot、denominator policy probe、forbidden path sentinel。

**依赖环境**：Python 3.11、uv、pytest；不需要真实 lake、不需要 token、不联网。

**关键验证场景**：

- 9 行 register 全部进入 supported / research-only / unsupported / blocked 摘要。
- 所有 `pass_denominator=excluded` 项不计入 formal dataset pass denominator。
- README / USER-MANUAL / report summary 同时显示 limited-window supported、2020-2024 blocked、execution/VWAP blocked 和 unsupported register。
- 旧 register 和 2020-2024 证据报告覆盖次数为 0。

## 量化验收标准（acceptance_criteria）

- [ ] `unsupported_claim_boundary_summary` 覆盖 9 个 data_item，且每项保留 `status`、`reason`、`pass_denominator`。
- [ ] `pass_denominator=excluded` 项计入 formal pass denominator 次数为 0。
- [ ] README、USER-MANUAL 和 report summary 均包含 supported / research-only / unsupported / blocked 四类声明。
- [ ] register 缺行、缺 `status`、缺 `reason` 或缺 `pass_denominator` 时 fail。
- [ ] 默认验证路径的 provider / lake / credential / legacy data / old report 操作计数均为 0。

## 阻塞说明

RESOLVED（2026-05-25）：CR-013 CP3 / CP4 / CP5 已通过，S03 离线实现已完成且 CP6 PASS，当前进入 `ready-for-verification`。OPEN：真实 provider / lake / credential / old data / old report 操作仍未授权。
