---
story_id: "CR017-S01-adjustment-policy-requirements-and-adr-refresh"
title: "复权口径合同与迁移声明冻结"
story_slug: "adjustment-policy-requirements-and-adr-refresh"
status: "verified"
priority: "P0"
wave: "CR017-W1-ADJUSTMENT-CONTRACTS"
depends_on:
  - "CR014-S02-parquet-layout-manifest-catalog-publish-gate"
dependency_type:
  - upstream: "CR014-S02-parquet-layout-manifest-catalog-publish-gate"
    type: "contract"
cp5_batch: "CR017-ADJUSTMENT-DUAL-VIEW-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "market_data/adjustment_policy.py"
    - "docs/ADJUSTMENT-POLICY-MIGRATION.md"
    - "tests/test_cr017_adjustment_policy_contract.py"
  shared:
    - "market_data/contracts.py"
    - "README.md"
    - "docs/USER-MANUAL.md"
  merge_owner: "CR017-S01-adjustment-policy-requirements-and-adr-refresh"
  forbidden:
    - "process/REQUIREMENTS.md"
    - "process/ARCHITECTURE-DECISION.md"
    - "process/HLD.md"
    - "process/HLD-DATA-LAKE.md"
    - "pyproject.toml"
    - "uv.lock"
    - "credential files or secret values"
lld_gate:
  required_inputs:
    - "process/HLD-DATA-LAKE.md#18"
    - "process/ARCHITECTURE-DECISION.md#ADR-053"
    - "process/ARCHITECTURE-DECISION.md#ADR-054"
    - "process/stories/CR017-S01-adjustment-policy-requirements-and-adr-refresh.md"
  status: "approved"
  cp5_batch: "CR017-ADJUSTMENT-DUAL-VIEW-BATCH-A"
  lld_path: "process/stories/CR017-S01-adjustment-policy-requirements-and-adr-refresh-LLD.md"
  cp5_auto_precheck: "process/checks/CP5-CR017-S01-adjustment-policy-requirements-and-adr-refresh-LLD-IMPLEMENTABILITY.md"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  reason: "CP5 已 approved；CR014-S02 上游 catalog / publish gate 合同已 verified，可作为 CR017 首个实现 Story。"
created_at: "2026-05-28"
updated_at: "2026-05-28T07:26:01+08:00"
verification_gate:
  cp7_status: "PASS"
  cp7_result: "process/checks/CP7-CR017-S01-adjustment-policy-requirements-and-adr-refresh-VERIFICATION-DONE.md"
  verification_handoff: "process/handoffs/META-QA-CR017-W1-CP7-VERIFY-2026-05-28.md"
  verified_by: "meta-qa/qa-kong"
  verified_at: "2026-05-28T07:22:33+08:00"
  agent_id: "019e6bbd-714e-7621-ad55-06e96e061d35"
  agent_name: "qa-kong"
change_id: "CR-017"
---

# CR017-S01：复权口径合同与迁移声明冻结

## 目标

冻结 CR-017 的 raw、qfq、hfq、returns_adjusted 使用口径、旧 qfq 兼容声明和迁移说明输入。该 Story 不重写已批准的需求 / HLD / ADR，只把 CP3 决策转成后续可实现的合同、文档和测试入口。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-12 |
| 需求 | REQ-098、REQ-099、REQ-100、REQ-101、REQ-103、REQ-104 |
| HLD | `process/HLD-DATA-LAKE.md` §18.1-§18.7 |
| ADR | ADR-053、ADR-054 |

## 开发上下文（dev_context）

**背景说明**：CP3 已批准 raw + `adj_factor` 为事实源、qfq/hfq/returns_adjusted 独立 view、qfq `as_of_trade_date`、旧 qfq 只读保留和 QMT raw 执行价隔离。实现前需要把这些决策落成代码侧枚举、文档侧迁移声明和可测试的合同。

**输入文件**：`process/HLD-DATA-LAKE.md`、`process/ARCHITECTURE-DECISION.md`、`process/REQUIREMENTS.md`、`process/USE-CASES.md`、本 Story 卡片。

**输出文件**：`market_data/adjustment_policy.py`、`docs/ADJUSTMENT-POLICY-MIGRATION.md`、`tests/test_cr017_adjustment_policy_contract.py`；共享文件仅允许按 LLD 明确范围更新 `market_data/contracts.py`、`README.md`、`docs/USER-MANUAL.md`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| adjustment policy enum | `raw/qfq/hfq/returns_adjusted` | stable policy id、display label、consumer category | 未知 policy 返回 structured blocked reason |
| migration summary | legacy qfq baseline ref、new view id、compatibility status | `legacy_qfq_baseline_preserved`、migration impact、forbidden overwrite note | 不定位真实私有数据，不覆盖旧报告 |
| consumer policy matrix | consumer type、requested policy | allowed / blocked / warning reason | QMT execution consumer 只能返回 raw allowed |

**设计约束**：不修改 CP3 已批准的过程文档；不真实抓取、不写真实 lake、不发布 current pointer、不重算或覆盖旧 qfq；迁移声明只记录相对路径、脱敏标签或逻辑引用。

**命名规范**：policy id 使用 `raw`、`qfq`、`hfq`、`returns_adjusted`；迁移字段使用 `legacy_qfq_baseline_preserved`、`view_id`、`single_policy_gate_status`。

**平台目标**：本地 Python 研究 / 数据湖项目；Python 命令后续必须使用 `uv run`；本 Story 不引入依赖。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR014-S02 | contract | 可基于已验证 catalog / publish 合同设计 | CP5 后仍需避免覆盖 CR014 catalog 所有权 | 复权 view 必须派生于 Parquet/catalog 事实源 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR017-S01-T1 | 创建 | `market_data/adjustment_policy.py` | 定义复权口径枚举、consumer category 和 blocked reason |
| CR017-S01-T2 | 创建 | `docs/ADJUSTMENT-POLICY-MIGRATION.md` | 写旧 qfq 保留、新 view 和禁止覆盖声明 |
| CR017-S01-T3 | 创建 | `tests/test_cr017_adjustment_policy_contract.py` | 验证 policy enum、迁移声明和 QMT raw-only matrix |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr017_adjustment_policy_contract.py`。

**验证方式**：fixture / static contract test；不联网、不读凭据、不写真实 lake。

**依赖环境**：Python 3.11、uv、pytest；无 QMT 环境要求。

**关键验证场景**：四类 policy 均可识别；未知 policy fail fast；旧 qfq 保留声明存在；QMT execution consumer 对 qfq/hfq/returns_adjusted 返回 blocked。

## 量化验收标准（acceptance_criteria）

- [ ] policy id 覆盖 `raw/qfq/hfq/returns_adjusted` 4 类，未知 policy blocked reason 覆盖率 100%。
- [ ] 迁移声明包含 `legacy_qfq_baseline_preserved=true`、兼容入口和禁止覆盖说明。
- [ ] QMT execution consumer 使用非 raw policy 的 allowed 次数为 0。
- [ ] 默认验证的 provider_fetch、lake_write、credential_read、current_pointer_publish、dependency_change 计数均为 0。

## 阻塞说明

CP5 前不得实现；任一真实数据迁移、真实写湖或 current pointer 发布必须另行 Story / CP5 / 用户显式授权。
