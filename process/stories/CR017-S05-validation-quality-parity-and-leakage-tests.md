---
story_id: "CR017-S05-validation-quality-parity-and-leakage-tests"
title: "复权 quality / parity / leakage 验证矩阵"
story_slug: "validation-quality-parity-and-leakage-tests"
status: "verified"
priority: "P0"
wave: "CR017-W2-DERIVATION-READERS"
depends_on:
  - "CR017-S02-raw-prices-and-adj-factor-contract-hardening"
  - "CR017-S03-qfq-hfq-derived-view-normalization"
  - "CR017-S04-reader-api-and-policy-gates"
dependency_type:
  - upstream: "CR017-S02-raw-prices-and-adj-factor-contract-hardening"
    type: "contract"
  - upstream: "CR017-S03-qfq-hfq-derived-view-normalization"
    type: "contract"
  - upstream: "CR017-S04-reader-api-and-policy-gates"
    type: "contract"
cp5_batch: "CR017-ADJUSTMENT-DUAL-VIEW-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "tests/test_cr017_adjustment_quality_parity.py"
    - "tests/test_cr017_adjustment_leakage_gates.py"
  shared:
    - "market_data/validation.py"
    - "market_data/quality.py"
  merge_owner: "CR017-S05-validation-quality-parity-and-leakage-tests"
  forbidden:
    - "pyproject.toml"
    - "uv.lock"
    - "credential files or secret values"
lld_gate:
  required_inputs:
    - "process/USE-CASES.md#CR-015--CR-016--CR-017-验证场景矩阵"
    - "process/HLD-DATA-LAKE.md#18.6"
    - "process/HLD-DATA-LAKE.md#18.9"
    - "process/stories/CR017-S05-validation-quality-parity-and-leakage-tests.md"
  status: "approved"
  cp5_batch: "CR017-ADJUSTMENT-DUAL-VIEW-BATCH-A"
  lld_path: "process/stories/CR017-S05-validation-quality-parity-and-leakage-tests-LLD.md"
  cp5_auto_precheck: "process/checks/CP5-CR017-S05-validation-quality-parity-and-leakage-tests-LLD-IMPLEMENTABILITY.md"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  reason: "CR017-S02/S03/S04 均已 CP7 PASS / verified；CP5 已 approved；当前无 dev_running 文件冲突，可进入 quality / parity / leakage 离线验证矩阵实现。"
created_at: "2026-05-28"
updated_at: "2026-05-28T08:21:43+08:00"
verification_gate:
  cp7_status: "PASS"
  cp7_result: "process/checks/CP7-CR017-S05-validation-quality-parity-and-leakage-tests-VERIFICATION-DONE.md"
  verification_handoff: "process/handoffs/META-QA-CR017-S05-CP7-VERIFY-2026-05-28.md"
  verified_by: "meta-qa/qa-yan"
  verified_at: "2026-05-28T08:19:49+08:00"
  agent_id: "019e6bf1-96ce-7f02-ae98-50bd7cbc86db"
  agent_name: "qa-yan"
change_id: "CR-017"
---

# CR017-S05：复权 quality / parity / leakage 验证矩阵

## 目标

建立 CR-017 的质量、公式 parity、qfq as-of、单 run 口径和 QMT raw 执行价泄漏验证矩阵，使 CP7 后续能量化证明双视图边界有效。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-12、TS-017-01、TS-017-02、TS-017-03 |
| 需求 | REQ-098、REQ-099、REQ-100、REQ-101、REQ-102、REQ-121 |
| HLD | `process/HLD-DATA-LAKE.md` §18.6、§18.9 |
| ADR | ADR-053、ADR-054、ADR-058 |

## 开发上下文（dev_context）

**背景说明**：CR-017 风险集中在公式方向、as-of 漂移、混用口径和复权价进入执行链路。该 Story 负责把这些风险转为固定测试矩阵和 quality gate。

**输入文件**：CR017-S02/S03/S04 合同、UC 验证场景矩阵、HLD-DATA-LAKE §18。

**输出文件**：`tests/test_cr017_adjustment_quality_parity.py`、`tests/test_cr017_adjustment_leakage_gates.py`；共享 `market_data/validation.py`、`market_data/quality.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| adjustment quality gate | raw/factor/derived view metadata | pass / warn / fail | 缺 lineage、as-of 或 factor direction 时 fail |
| parity check | fixture raw/factor/output | parity status、mismatch reason | 不使用真实 provider 数据 |
| leakage guard | reader metadata、order intent sample | blocked reason | qfq/hfq 进入 execution field 必须 fail |

**设计约束**：测试只用 fixture；不得读取真实数据、旧报告内容或凭据；不得把 warning 视为 production pass。

**命名规范**：测试场景 ID 保持 `TS-017-01`、`TS-017-02`、`TS-017-03` 可追溯。

**平台目标**：本地 pytest 验证矩阵；默认离线。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR017-S02/S03/S04 | contract | schema、派生和 reader gate 已定义 | 共享 validation 文件，开发默认串行 | 质量矩阵消费上游合同 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR017-S05-T1 | 创建 | `tests/test_cr017_adjustment_quality_parity.py` | 覆盖 qfq/hfq/returns parity 和 as-of |
| CR017-S05-T2 | 创建 | `tests/test_cr017_adjustment_leakage_gates.py` | 覆盖 single-policy 与 QMT raw execution leakage |
| CR017-S05-T3 | 修改 | `market_data/validation.py` | 按 LLD 接入质量失败枚举与 blocked reason |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr017_adjustment_quality_parity.py tests/test_cr017_adjustment_leakage_gates.py`。

**验证方式**：离线 fixture；无真实 provider / broker 依赖。

**依赖环境**：Python 3.11、uv、pytest。

**关键验证场景**：TS-017-01 raw/factor/derived lineage；TS-017-02 qfq as-of；TS-017-03 单 run 口径和 raw execution boundary。

## 量化验收标准（acceptance_criteria）

- [ ] TS-017-01 至 TS-017-03 均有至少 1 个正向和 1 个失败场景。
- [ ] 缺 factor direction、缺 as-of、混用 policy、复权价进入 execution 字段均 fail。
- [ ] parity mismatch 输出结构化 reason，不能只输出自由文本。
- [ ] 默认验证的 provider_fetch、lake_write、credential_read、current_pointer_publish、dependency_change 计数均为 0。

## 阻塞说明

CP5 前不得实现；真实数据 parity 或迁移验证必须另行授权。
