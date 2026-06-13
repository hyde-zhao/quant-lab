---
story_id: "CR045-S05"
title: "Redaction and No-Operation Static Validation"
story_slug: "redaction-and-no-operation-static-validation"
status: "ready-for-verification"
priority: "P0"
wave: "W3"
implementation_allowed: true
implementation_allowed_until: "CP5 approved at 2026-06-11T23:16:11+08:00; L2 skeleton / fixture / static only"
depends_on:
  - "CR045-S01"
  - "CR045-S02"
  - "CR045-S03"
dependency_contracts:
  - upstream_story: "CR045-S01"
    type: "contract"
    required_for: "sensitive fields and authorization model"
  - upstream_story: "CR045-S02"
    type: "contract"
    required_for: "bridge schema and capability flags"
  - upstream_story: "CR045-S03"
    type: "contract"
    required_for: "client artifacts and forbidden Linux boundary"
  - upstream_story: "CR045-S04"
    type: "contract"
    required_for: "readonly probe evidence; can be co-designed in W3"
feature_design_refs:
  - "docs/features/cr045-goldminer-bridge/DESIGN.md#测试与验收策略"
  - "docs/features/cr045-goldminer-bridge/TEST-PLAN.md#风险驱动测试"
  - "docs/features/cr045-goldminer-bridge/TASKS.md#cr045-s05"
lld_policy:
  required_level: "full-lld"
  trigger_reasons:
    - "security"
    - "audit"
    - "validation"
    - "data-model"
  rationale: "redaction evidence、artifact scan 和 operation counts=0 是 CP7/CP8 的安全证明，必须完整设计。"
  waiver_reason: ""
  revisit_condition: "任何真实 broker payload 或敏感值需要保存时，暂停并发起安全决策；不得在 L2 中保存原值。"
  evidence_path: "process/stories/CR045-S05-redaction-and-no-operation-static-validation-LLD.md"
file_ownership:
  primary:
    - "process/stories/CR045-S05-redaction-and-no-operation-static-validation.md"
    - "process/stories/CR045-S05-redaction-and-no-operation-static-validation-LLD.md"
    - "tests/test_cr045_goldminer_no_operation_static.py"
  shared:
    - "engine/goldminer_bridge_contract.py"
    - "tests/test_cr045_goldminer_bridge_contract.py"
    - "tests/test_cr045_goldminer_readonly_probe.py"
  merge_owner: "CR045-S05"
  forbidden:
    - ".env"
    - ".env.*"
    - "reports/live"
    - "reports/simulation_runtime"
lld_gate:
  required_inputs:
    - "CR045-S01 design evidence"
    - "CR045-S02 design evidence"
    - "CR045-S03 design evidence"
    - "CR045-S04 design evidence for readonly artifacts, if already drafted"
  design_evidence_type: "full-lld"
  design_evidence_path: "process/stories/CR045-S05-redaction-and-no-operation-static-validation-LLD.md"
  status: "confirmed"
dev_gate:
  implementation_allowed: true
  allowed_after: "CP5 approved"
  design_evidence_confirmed: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  real_runtime_authorized: false
---

# CR045-S05 Redaction and No-Operation Static Validation

## 目标

定义 CR045 redaction evidence、artifact static scan 和 no-operation validation，使 CP7 能证明真实敏感值泄漏数为 0、真实操作计数为 0，并且未启动任何 runtime。

## 开发上下文（dev_context）

- 输入文件：S01-S04 设计证据、Feature TEST-PLAN、`engine/broker_adapter.py` 的敏感字段和 forbidden counter 概念。
- 输出文件：`process/stories/CR045-S05-redaction-and-no-operation-static-validation-LLD.md`；未来 CP6 可创建 `tests/test_cr045_goldminer_no_operation_static.py`。
- 接口约定：artifact scan 只读仓库非凭据产物，不读取 `.env`、token、account_id、Windows 凭据；operation counters 全 0。
- 设计约束：不保存真实敏感值；不生成 reports/live 或 simulation runtime artifacts；不 provider/lake/publish。
- 平台目标：static-only / fixture-only validation。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR045-S01 | contract | sensitive field and authorization declared | CP5 approved + confirmed | 根安全规则。 |
| CR045-S02 | contract | schema/capability fields declared | CP5 approved + confirmed | capabilities flags and contract tests。 |
| CR045-S03 | contract | client artifact boundary declared | CP5 approved + confirmed | Linux client scan scope。 |
| CR045-S04 | contract | readonly evidence co-design | CP5 approved + confirmed | W3 可与 S04 并行设计，但验证需消费 S04 artifacts。 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `tests/test_cr045_goldminer_no_operation_static.py` | CR045-S05 future primary owner。 |
| shared | `engine/goldminer_bridge_contract.py` | 只消费 schema；修改需与 CR045-S02 协调。 |
| shared | `tests/test_cr045_goldminer_bridge_contract.py` | 只追加 no-operation assertions，需 merge_owner 协调。 |
| forbidden | `.env`、`.env.*`、`reports/live`、`reports/simulation_runtime` | 禁止读取凭据和真实运行产物。 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR045-S05-T1 | 设计 | `CR045-S05-...-LLD.md` | 定义 redaction evidence schema 和 artifact scan allowlist/denylist。 |
| CR045-S05-T2 | 设计 | `CR045-S05-...-LLD.md` | 定义 forbidden operation counters 和 zero-count assertions。 |
| CR045-S05-T3 | 设计 | `CR045-S05-...-LLD.md` | 定义 CP7 no-operation report 的证据字段。 |

## 技术说明

本 Story 需要 `full-lld`。CP4 不写实现或 LLD。

## 验证上下文（validation_context）

| 项目 | 内容 |
|---|---|
| validation_mode | static-only + fixture-only |
| 验证入口 | CP6 后 `uv run --python 3.11 pytest -q tests/test_cr045_goldminer_no_operation_static.py`；CP7 manual review。 |
| 关键验证场景 | sensitive fields are redacted; no `.env` read; forbidden operation counters all 0; no provider/lake/publish. |
| 禁止验证方式 | 不读取凭据文件，不运行真实 bridge，不访问 Windows local credentials。 |

## 量化验收标准（acceptance_criteria）

- [ ] artifact scan 范围明确排除 `.env`、`.env.*`、Windows credential files、token/account/password/session/cookie/private key 材料。
- [ ] 敏感字段类别至少覆盖 S01 列出的 12 类字段，并只输出字段类别、规则 ID、count、`REDACTED`。
- [ ] forbidden operation counters 至少覆盖 real_broker_call、real_order_call、real_cancel_call、real_account_query、real_position_query、real_cash_query、credential_read、goldminer_import_or_call、gmtrade_import_or_call。
- [ ] no-operation validation 要求全部 forbidden counters 为 0。
- [ ] 任何 provider_fetch、lake_write、catalog_publish、simulation/live artifact 均为 FAIL。
- [ ] CP7 报告不得宣称 real-readonly-verified。

## 阻塞说明

无 CP4 阻塞。真实 broker payload 或敏感值保存需求是安全阻塞，必须另行授权。
