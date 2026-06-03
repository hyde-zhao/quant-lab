---
story_id: "CR017-S02-raw-prices-and-adj-factor-contract-hardening"
title: "raw prices 与 adj_factor 事实源合同强化"
story_slug: "raw-prices-and-adj-factor-contract-hardening"
status: "verified"
priority: "P0"
wave: "CR017-W1-ADJUSTMENT-CONTRACTS"
depends_on:
  - "CR017-S01-adjustment-policy-requirements-and-adr-refresh"
  - "CR010-S02-prices-adj-factor-history-backfill-loop"
dependency_type:
  - upstream: "CR017-S01-adjustment-policy-requirements-and-adr-refresh"
    type: "contract"
  - upstream: "CR010-S02-prices-adj-factor-history-backfill-loop"
    type: "contract"
cp5_batch: "CR017-ADJUSTMENT-DUAL-VIEW-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "market_data/adjustment_contracts.py"
    - "tests/test_cr017_raw_adj_factor_contract.py"
  shared:
    - "market_data/contracts.py"
    - "market_data/validation.py"
  merge_owner: "CR017-S02-raw-prices-and-adj-factor-contract-hardening"
  forbidden:
    - "market_data/connectors/**"
    - "market_data/runtime.py"
    - "pyproject.toml"
    - "uv.lock"
    - "credential files or secret values"
lld_gate:
  required_inputs:
    - "process/HLD-DATA-LAKE.md#18.5"
    - "process/HLD-DATA-LAKE.md#18.6"
    - "process/ARCHITECTURE-DECISION.md#ADR-053"
    - "process/stories/CR017-S02-raw-prices-and-adj-factor-contract-hardening.md"
  status: "approved"
  cp5_batch: "CR017-ADJUSTMENT-DUAL-VIEW-BATCH-A"
  lld_path: "process/stories/CR017-S02-raw-prices-and-adj-factor-contract-hardening-LLD.md"
  cp5_auto_precheck: "process/checks/CP5-CR017-S02-raw-prices-and-adj-factor-contract-hardening-LLD-IMPLEMENTABILITY.md"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  reason: "CP5 已 approved；CR017-S01 合同由同一 CR017-W1 实现批次串行冻结，CR010-S02 上游合同已 verified。"
created_at: "2026-05-28"
updated_at: "2026-05-28T07:26:01+08:00"
verification_gate:
  cp7_status: "PASS"
  cp7_result: "process/checks/CP7-CR017-S02-raw-prices-and-adj-factor-contract-hardening-VERIFICATION-DONE.md"
  verification_handoff: "process/handoffs/META-QA-CR017-W1-CP7-VERIFY-2026-05-28.md"
  verified_by: "meta-qa/qa-kong"
  verified_at: "2026-05-28T07:22:33+08:00"
  agent_id: "019e6bbd-714e-7621-ad55-06e96e061d35"
  agent_name: "qa-kong"
change_id: "CR-017"
---

# CR017-S02：raw prices 与 adj_factor 事实源合同强化

## 目标

建立 `prices_raw` 与 `adj_factor` 的事实源字段、lineage、quality 和 provider factor direction 合同，使后续 qfq/hfq 派生不依赖猜测，也不覆盖原始交易价。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-12 |
| 需求 | REQ-098、REQ-100、REQ-104 |
| HLD | `process/HLD-DATA-LAKE.md` §18.5、§18.6 |
| ADR | ADR-053 |

## 开发上下文（dev_context）

**背景说明**：CR-017 要求 raw 与复权因子作为事实源。`adj_factor` 的方向、基准日、可用时间和 lineage 缺失时，派生 view 必须 fail-fast，不能发布或被 reader 静默消费。

**输入文件**：HLD-DATA-LAKE §18、ADR-053、CR010-S02 已验证的 prices / adj_factor 历史回补合同、CR017-S01 policy 合同。

**输出文件**：`market_data/adjustment_contracts.py`、`tests/test_cr017_raw_adj_factor_contract.py`；共享 `market_data/contracts.py`、`market_data/validation.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| raw price contract | OHLCV、source metadata、lineage | `prices_raw` schema result | raw OHLC 非法或 lineage 缺失时 fail |
| adj factor contract | factor value、direction、base/as-of metadata | `adj_factor` schema result | direction 未确认时 derivation blocked |
| source lineage check | source_run_id、batch_id、checksum | pass / fail / required_missing | 不读取真实私有路径，只记录逻辑 lineage |

**设计约束**：本 Story 不拥有 connector、runtime、真实抓取或 lake 写入；只冻结 schema / validation 合同。`prices_raw` 不得被 qfq/hfq 覆盖。

**命名规范**：字段使用 `provider_factor_direction`、`factor_base_date_policy`、`source_run_id`、`lineage_checksum`、`available_at`、`quality_status`。

**平台目标**：本地数据湖合同层；默认 fixture 验证。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR017-S01 | contract | policy enum 已定义 | S01 合同冻结后才可实现字段绑定 | 使用相同 policy id |
| CR010-S02 | contract | 已验证 prices / adj_factor 基线可引用 | 不修改 CR010 输出历史 | 只消费既有合同，不真实补数 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR017-S02-T1 | 创建 | `market_data/adjustment_contracts.py` | 定义 raw price 与 adj_factor 合同和校验结果 |
| CR017-S02-T2 | 修改 | `market_data/contracts.py` | 按 LLD 添加 view / schema 常量，避免破坏旧入口 |
| CR017-S02-T3 | 创建 | `tests/test_cr017_raw_adj_factor_contract.py` | 覆盖 direction 缺失、lineage 缺失、raw 非法价格失败 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr017_raw_adj_factor_contract.py`。

**验证方式**：纯 fixture schema / validation；不触发 provider，不写 lake。

**依赖环境**：Python 3.11、uv、pytest。

**关键验证场景**：raw 必需字段完整；raw 非法价格 fail；factor direction 缺失 fail；lineage 缺失 required_missing；qfq/hfq 不覆盖 raw。

## 量化验收标准（acceptance_criteria）

- [ ] `prices_raw` 必需字段和 metadata 覆盖率为 100%。
- [ ] `adj_factor` 必须包含 factor direction / base policy / source lineage，缺任一字段时派生允许次数为 0。
- [ ] raw OHLC 非法或 close 非法非缺失时 quality fail。
- [ ] 默认验证的 provider_fetch、lake_write、credential_read、current_pointer_publish、dependency_change 计数均为 0。

## 阻塞说明

CP5 前不得实现；真实 provider 字段复核、真实数据写入或历史迁移必须另行授权。
