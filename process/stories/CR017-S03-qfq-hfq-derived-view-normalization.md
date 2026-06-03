---
story_id: "CR017-S03-qfq-hfq-derived-view-normalization"
title: "qfq / hfq 派生 view normalization"
story_slug: "qfq-hfq-derived-view-normalization"
status: "verified"
priority: "P0"
wave: "CR017-W2-DERIVATION-READERS"
depends_on:
  - "CR017-S02-raw-prices-and-adj-factor-contract-hardening"
dependency_type:
  - upstream: "CR017-S02-raw-prices-and-adj-factor-contract-hardening"
    type: "contract"
cp5_batch: "CR017-ADJUSTMENT-DUAL-VIEW-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "market_data/adjustment_derivation.py"
    - "tests/test_cr017_qfq_hfq_derivation.py"
  shared:
    - "market_data/normalization.py"
    - "market_data/contracts.py"
  merge_owner: "CR017-S03-qfq-hfq-derived-view-normalization"
  forbidden:
    - "market_data/connectors/**"
    - "pyproject.toml"
    - "uv.lock"
    - "credential files or secret values"
lld_gate:
  required_inputs:
    - "process/HLD-DATA-LAKE.md#18.6"
    - "process/ARCHITECTURE-DECISION.md#ADR-053"
    - "process/stories/CR017-S03-qfq-hfq-derived-view-normalization.md"
  status: "approved"
  cp5_batch: "CR017-ADJUSTMENT-DUAL-VIEW-BATCH-A"
  lld_path: "process/stories/CR017-S03-qfq-hfq-derived-view-normalization-LLD.md"
  cp5_auto_precheck: "process/checks/CP5-CR017-S03-qfq-hfq-derived-view-normalization-LLD-IMPLEMENTABILITY.md"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  reason: "CR017-S02 已 CP7 PASS / verified；CP5 已 approved；当前无 dev_running 文件冲突，可进入 S03 离线 candidate derivation 实现。"
created_at: "2026-05-28"
updated_at: "2026-05-28T07:41:26+08:00"
verification_gate:
  cp7_status: "PASS"
  cp7_result: "process/checks/CP7-CR017-S03-qfq-hfq-derived-view-normalization-VERIFICATION-DONE.md"
  verification_handoff: "process/handoffs/META-QA-CR017-S03-CP7-VERIFY-2026-05-28.md"
  verified_by: "meta-qa/qa-wei"
  verified_at: "2026-05-28T07:38:23+08:00"
  agent_id: "019e6bcb-f813-7d71-bbcb-9a1091b0f96e"
  agent_name: "qa-wei"
change_id: "CR-017"
---

# CR017-S03：qfq / hfq 派生 view normalization

## 目标

实现 qfq、hfq 和 returns_adjusted 派生 view 的 normalization 合同，明确公式、as-of、base date、derivation_version 和 lineage，禁止同一 view 混用口径。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-12 |
| 需求 | REQ-099、REQ-100、REQ-104 |
| HLD | `process/HLD-DATA-LAKE.md` §18.5-§18.7 |
| ADR | ADR-053、ADR-054 |

## 开发上下文（dev_context）

**背景说明**：qfq 以 `as_of_trade_date` 为锚点，hfq 以 provider/base date 为锚点，returns_adjusted 面向严肃研究。派生实现必须先验证 factor direction，输出 deterministic lineage，不能真实写发布指针。

**输入文件**：CR017-S02 raw/factor 合同、HLD-DATA-LAKE §18.6、ADR-053、ADR-054。

**输出文件**：`market_data/adjustment_derivation.py`、`tests/test_cr017_qfq_hfq_derivation.py`；共享 `market_data/normalization.py`、`market_data/contracts.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| derive_qfq | raw price、adj_factor、as_of_trade_date | `prices_qfq` candidate rows | as-of 或 factor 缺失时 fail |
| derive_hfq | raw price、adj_factor、base_date policy | `prices_hfq` candidate rows | base policy 不可追溯时 fail |
| derive_returns | one adjusted view or raw+factor | `returns_adjusted` candidate rows | 输入混用或窗口缺失时 structured fail |

**设计约束**：只生成 candidate 或内存 / fixture 输出；publish current pointer 不属于本 Story；真实数据重算和覆盖旧 qfq 禁止。

**命名规范**：`view_id` 固定为 `prices_qfq`、`prices_hfq`、`returns_adjusted`；派生版本字段为 `derivation_version`。

**平台目标**：本地数据湖派生层；后续可被 reader 和 QMT metadata 只读消费。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR017-S02 | contract | raw/factor schema 和 direction 已冻结 | 合同冻结后才可实现派生 | 防止方向写反 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR017-S03-T1 | 创建 | `market_data/adjustment_derivation.py` | 实现 qfq/hfq/returns_adjusted 派生候选逻辑 |
| CR017-S03-T2 | 修改 | `market_data/normalization.py` | 按 LLD 将派生入口接入 candidate normalization |
| CR017-S03-T3 | 创建 | `tests/test_cr017_qfq_hfq_derivation.py` | 覆盖 qfq as-of、hfq base、returns 和异常 factor |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr017_qfq_hfq_derivation.py`。

**验证方式**：小型 fixture 数学 parity；不联网、不写 lake、不发布。

**依赖环境**：Python 3.11、uv、pytest。

**关键验证场景**：qfq 同一 as-of deterministic；不同 as-of 输出 lineage 不同；hfq base 可追溯；returns 不混用视图；异常跳变进入 warning / fail。

## 量化验收标准（acceptance_criteria）

- [ ] `prices_qfq`、`prices_hfq`、`returns_adjusted` 3 类 view 均输出 view_id、schema_version、derivation_version、source_run_id 和 quality_status。
- [ ] qfq 结果 100% 记录 `as_of_trade_date` 和 `input_snapshot_id`。
- [ ] factor direction 未确认时派生成功次数为 0。
- [ ] 默认验证的 provider_fetch、lake_write、credential_read、current_pointer_publish、dependency_change 计数均为 0。

## 阻塞说明

CP5 前不得实现；真实全量派生、真实写湖和 publish gate 均需后续授权。
