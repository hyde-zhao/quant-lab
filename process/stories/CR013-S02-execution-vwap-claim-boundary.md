---
story_id: "CR013-S02-execution-vwap-claim-boundary"
title: "execution / VWAP claim boundary"
story_slug: "execution-vwap-claim-boundary"
status: "verified"
priority: "P0"
wave: "CR013-BATCH-A"
depends_on:
  - "CR011-S04-ohlcv-vwap-clean-execution-feed"
dependency_type:
  - "contract"
dependency_contracts:
  - upstream: "CR011-S04-ohlcv-vwap-clean-execution-feed"
    type: "contract"
    required: "execution_price_policy exact 四值语义、close_proxy 降级和 blocked claims 基线已 verified"
file_ownership:
  primary:
    - "reports/data_lake_readiness_2020_2024_cr013/execution_claim_boundary.md"
    - "tests/test_cr013_execution_vwap_claim_boundary.py"
  shared:
    - "engine/research_dataset.py"
    - "experiments/reporting.py"
  merge_owner: "CR013-S02-execution-vwap-claim-boundary"
  forbidden:
    - "reports/data_lake_readiness_2020_2024/execution_price_audit.csv"
    - "market_data/connectors/**"
    - "/mnt/ugreen-data-lake/**"
    - "data/**"
    - ".env"
lld_gate:
  required_inputs:
    - "process/HLD.md#29.5"
    - "process/HLD-DATA-LAKE.md#16.3"
    - "process/ARCHITECTURE-DECISION.md#adr-045cr-013-execution--vwap--minute-execution-claims-必须保持-blocked"
    - "process/ARCHITECTURE-DECISION.md#adr-047cr-013-证据保留与权限边界"
    - "process/stories/CR013-S02-execution-vwap-claim-boundary.md"
  status: "approved"
  cp5_batch: "CR013-BATCH-A"
  required_before_dev: true
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  cp5_required: true
  implementation_allowed: true
  reason: "CP5 批次人工确认已通过；允许按 LLD 离线实现 S02，不授权 provider fetch、真实 lake 写入、凭据读取、旧 data 读取或旧报告覆盖。"
created_at: "2026-05-25"
updated_at: "2026-05-25"
cp6_status: "PASS"
cp6_checkpoint: "process/checks/CP6-CR013-S02-execution-vwap-claim-boundary-CODING-DONE.md"
cp7_status: "PASS"
cp7_checkpoint: "process/checks/CP7-CR013-S02-execution-vwap-claim-boundary-VERIFICATION-DONE.md"
source_hld: "process/HLD.md"
companion_hld: "process/HLD-DATA-LAKE.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-013"
---

# CR013-S02：execution / VWAP claim boundary

## 目标

加固 execution / VWAP claim boundary：当 execution feed 仍为 `required_missing` 且 `true_vwap_available_count=0` 时，真实 VWAP、VWAP fill、分钟线、逐笔、盘口、委托、成交明细和真实撮合执行价必须保持 blocked / unsupported。close proxy 只能作为研究降级口径，不能被写成真实 VWAP 或 production strict 真实执行价。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-08 |
| 需求 | REQ-084、REQ-086、REQ-087 |
| HLD | `process/HLD.md` §29.1、§29.5、§29.6、§29.7；`process/HLD-DATA-LAKE.md` §16.2、§16.3、§16.4 |
| ADR | ADR-045、ADR-047 |
| Backlog / Plan | `process/STORY-BACKLOG.md` CR013-S02；`process/DEVELOPMENT-PLAN.yaml` wave `CR013-BATCH-A` |

## 开发上下文（dev_context）

**背景说明**：CR011-S04 已把 `open`、`close`、`vwap`、`close_proxy` 执行价 policy 做成 exact 合同，并修复过非 exact policy 输入问题。CR-013 证据进一步显示当前 full-history execution feed 仍缺真实 VWAP 支撑：`execution_price_status=required_missing`、`missing_ohlcv_columns=volume;amount`、`true_vwap_available_count=0`、`blocked_claims=real_vwap_execution;vwap_fill_claim`。本 Story 要把这些证据转成声明边界。

**输入文件**：

| 路径 | 用途 | 访问方式 |
|---|---|---|
| `process/HLD.md` | CR-013 研究消费边界 | 只读 |
| `process/HLD-DATA-LAKE.md` | 数据湖 execution audit 合同 | 只读 |
| `process/ARCHITECTURE-DECISION.md` | ADR-045 / ADR-047 | 只读 |
| `process/stories/CR011-S04-ohlcv-vwap-clean-execution-feed.md` | execution policy 上游合同 | 只读 |
| `reports/data_lake_readiness_2020_2024/execution_price_audit.csv` | execution / VWAP 证据 | 只读，不覆盖 |

**输出文件**：

| 路径 | 说明 |
|---|---|
| `reports/data_lake_readiness_2020_2024_cr013/execution_claim_boundary.md` | 新增 execution claim boundary 摘要 |
| `tests/test_cr013_execution_vwap_claim_boundary.py` | 后续实现阶段的最小验证入口 |

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| execution audit reader | `execution_price_status`、`missing_ohlcv_columns`、`true_vwap_available_count`、`blocked_claims` | structured audit result | 缺字段时默认 blocked，不允许真实 VWAP claim |
| claim boundary resolver | audit result、requested execution claim | `blocked_claims`、`unsupported_claims`、`allowed_claims` | real VWAP / VWAP fill / minute execution allowed count 必须为 0 |
| remediation writer | audit result、ADR-045 | 解除条件：`vwap` + `vwap_status=available` + execution audit pass + CP5 approved | 不输出真实 provider 命令或 lake 写入动作 |

**设计约束**：

- `real_vwap_execution` 和 `vwap_fill_claim` 必须进入 blocked claims。
- `minute_tick_level2_order_match` 必须声明为 unsupported，不得用 close proxy 代替。
- 不得由 `amount/volume`、close proxy 或任何日频派生方式声明真实 VWAP。
- 不读取 `.env`，不触发真实 provider，不写真实 lake，不读取旧 `data/**`，不覆盖 execution audit 证据。

**命名规范**：保留 `execution_price_status`、`missing_ohlcv_columns`、`true_vwap_available_count`、`vwap_status`、`blocked_claims`、`unsupported_claims`、`execution_claim_boundary`。

**平台目标**：本地 Python 因子研究工具；uv 管理依赖；无安装脚本；无 `delivery/**` 输出。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR013-S02-T1 | 创建 | `reports/data_lake_readiness_2020_2024_cr013/execution_claim_boundary.md` | 输出真实 VWAP / VWAP fill / minute execution blocked 摘要和解除条件 |
| CR013-S02-T2 | 修改 | `experiments/reporting.py` | 后续实现阶段将 execution blocked claims 纳入报告声明消费面 |
| CR013-S02-T3 | 修改 | `engine/research_dataset.py` | 后续实现阶段将 execution claim boundary 与 close_proxy 降级 metadata 对齐 |
| CR013-S02-T4 | 创建 | `tests/test_cr013_execution_vwap_claim_boundary.py` | 覆盖真实 VWAP claim=0、amount/volume 派生禁止、old audit overwrite=0 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr013_execution_vwap_claim_boundary.py`。

**验证方式**：execution audit fixture、claim boundary snapshot、forbidden path sentinel、invalid derived VWAP probe。

**依赖环境**：Python 3.11、uv、pytest；不需要真实 VWAP 数据、不需要真实 lake、不需要 token、不联网。

**关键验证场景**：

- `execution_price_status=required_missing` 时 `real_vwap_execution` 与 `vwap_fill_claim` 必须 blocked。
- `true_vwap_available_count=0` 时真实 VWAP allowed claim 输出次数为 0。
- close proxy 可作为 `research_degradation`，但不能进入真实 VWAP / production strict execution allowed claims。
- `amount/volume` 派生真实 VWAP claim 的尝试必须 fail。

## 量化验收标准（acceptance_criteria）

- [ ] `blocked_claims` 包含 `real_vwap_execution` 和 `vwap_fill_claim`。
- [ ] 分钟 / 逐笔 / 盘口 / 委托 / 成交明细 / 真实撮合执行价均进入 unsupported 或 blocked 声明。
- [ ] 真实 VWAP / VWAP fill / minute execution allowed claim 输出次数为 0。
- [ ] `amount/volume` 派生真实 VWAP claim 次数为 0。
- [ ] 默认验证路径的 provider / lake / credential / legacy data / old report 操作计数均为 0。

## 阻塞说明

RESOLVED（2026-05-25）：CR-013 CP3 / CP4 / CP5 已通过，S02 离线实现已完成且 CP6 PASS，当前进入 `ready-for-verification`。OPEN：真实 VWAP 或分钟数据接入必须另行 Story / CP5 / 用户授权。
