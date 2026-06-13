---
status: "draft-cp4"
version: "1.1"
feature_id: "FEAT-09"
feature_name: "QMT / MiniQMT Dual-Target Strategy Delivery Framework"
source_blueprint: "docs/design/BLUEPRINT.md"
source_hld: "docs/design/HLD-CR046-QMT-MINIQMT-DUAL-TARGET-FRAMEWORK.md"
source_adr: "docs/design/ARCHITECTURE-DECISION-CR046.md"
source_matrix: "docs/design/FEATURE-DESIGN-MATRIX.md"
related_stories:
  - "CR046-S01-dual-target-strategy-architecture"
  - "CR046-S02-strategy-package-contract-and-schema"
  - "CR046-S03-qmt-terminal-target-framework"
  - "CR046-S04-miniqmt-runner-install-and-runtime-boundary"
  - "CR046-S05-verification-framework-and-evidence-model"
  - "CR046-S06-follow-up-strategy-delivery-gate"
  - "CR046-S07-research-framework-follow-up-contract"
lld_policy_summary: "S01..S05 full-lld; S06..S07 technical-note"
confirmed_by: ""
confirmed_at: ""
---

# Feature Design: QMT / MiniQMT Dual-Target Strategy Delivery Framework

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-13 | meta-po | 初始 FEAT-09 设计，冻结双目标策略包、target adapter、runner 安装设计、验证证据和后续 CR gate |
| 1.1 | 2026-06-13 | meta-po | 记录用户确认的策略包传输形态：zip + sha256 + manifest.yaml + 人工/受控文件传输 + QMT 终端人工导入 |

## 摘要

| 项目 | 内容 |
|---|---|
| Feature 目标 | 定义同一研究策略核心交付到 QMT terminal 与 MiniQMT runner 的统一合同 |
| 推荐方案 | 平台无关 strategy core + 双 target adapter contract + validation evidence model |
| 关键取舍 | 优先冻结合同和安全边界，牺牲当前真实运行证据 |
| 下游 Story | CR046-S01..S07 |
| LLD 策略 | S01..S05 full-lld；S06..S07 technical-note |

## 上游依据与输入

| 来源 | 路径 / ID | 被本设计消费的内容 |
|---|---|---|
| Blueprint | `docs/design/BLUEPRINT.md` FEAT-09 | Feature 边界、共享能力、禁止依赖 |
| HLD | `docs/design/HLD-CR046-QMT-MINIQMT-DUAL-TARGET-FRAMEWORK.md` | 模块拆分、验证框架、安装设计 |
| ADR | `docs/design/ARCHITECTURE-DECISION-CR046.md` ADR-CR046-001..006 | 独立 FEAT-09、平台无关 core、证据分级、后续 CR 切分 |
| Requirements | `process/REQUIREMENTS.md` REQ-186..200 | framework-first 范围、交付包和 runner install design |

## 目标与非目标

| 类型 | 内容 | 来源 |
|---|---|---|
| Goal | 定义 StrategyCoreContract、StrategyPackageContract、QMTTerminalTargetContract、MiniQMTRunnerTargetContract 和 StrategyValidationEvidence | HLD-CR046 |
| Goal | 定义 MiniQMT runner install dry-run 设计，不触碰真实 Windows 环境 | ADR-CR046-003 |
| Goal | 把 CR047、CR049、CR051 的进入条件和消费对象固定下来 | ADR-CR046-005/006 |
| Non-Goal | 交付具体策略、运行 QMT terminal、真实安装 / 连接 MiniQMT、submit/cancel、simulation/live | CP2 / CP3 不授权项 |

## Feature 边界与相邻对象

| 对象 | 本 Feature 负责 | 不负责 | 相邻 Feature / 模块 | 边界判定依据 |
|---|---|---|---|---|
| StrategyCoreContract | 平台无关输入、输出、风险假设、order intent schema | 具体策略逻辑和参数选择 | FEAT-03 / FEAT-04 | ADR-CR046-002 |
| QMTTerminalTargetContract | 终端 target 入口、配置、导入步骤、shadow evidence schema | 执行终端运行验证 | FEAT-05 / FEAT-06 / FEAT-07 | HLD-CR046 |
| MiniQMTRunnerTargetContract | install layout、uv policy、配置、日志、kill switch、rollback | 真实安装、连接、行情订阅、下单撤单 | FEAT-05 / FEAT-07 | ADR-CR046-003 |
| StrategyValidationEvidence | schema/static/fixture/dry-run plan/runtime verified 的证据分级 | 伪造 runtime verified | FEAT-07 / FEAT-08 | ADR-CR046-004 |

## 现有代码位置

| 区域 | 路径 | 当前职责 | 变更方式 |
|---|---|---|---|
| 研究准入 | `engine/`、`strategies/`、`process/research/` | 已有研究结果和 admission package 线索 | 后续只读消费，不在 CR046 实现策略 |
| 交易治理 | `trading/` | 已有 QMT / gateway / broker governance 历史合同 | 本 Feature 只定义 target contract，不触发 runtime |
| 文档 | `docs/qmt/`、`docs/research/` | CR046 目标文档候选出口 | 后续 Story 实现时创建 |

## 推荐方案

| 设计点 | 推荐做法 | 理由 | 代价 |
|---|---|---|---|
| Strategy core | 平台无关，禁止导入 QMT / XtQuant / MiniQMT | 同一策略可双目标交付 | target adapter 需要额外合同 |
| Package layout | `strategy_core/`、`targets/qmt_terminal/`、`targets/miniqmt_runner/`、`validation/`、`docs/`、`manifest.yaml` | 目录清晰，便于后续 CR047 策略交付 | 当前只定义合同 |
| Package transfer | `strategy-package-<strategy_id>-<version>.zip` + `.sha256` + `manifest.yaml`，通过人工/受控文件通道传到交易运行 PC，再按 QMT terminal target 手工导入 | 隔离研究环境与交易 PC，便于审计和回滚 | 当前只冻结合同，不执行传输或导入 |
| MiniQMT install | Windows 目录 + uv + 依赖隔离 + redacted config + kill switch + rollback | 满足用户要求且不触碰真实环境 | 无真实安装证据 |
| Validation evidence | 分级声明，CR046 不产出 runtime verified | 防止误读 | 需要文档和测试 guardrail |

## 数据模型与状态

| Object | Owner | 新增 / 修改字段 | 状态变化 | 兼容性 |
|---|---|---|---|---|
| StrategyCoreContract | FEAT-09 | strategy_id、input_schema、target_portfolio_schema、order_intent_schema、risk_assumption | draft -> validated -> blocked | 后续 CR047 消费 |
| StrategyPackageContract | FEAT-09 | package_id、layout_version、targets、validation_suite、docs_bundle、artifact_name、checksum_sha256、transfer_channel、manual_import_steps | draft -> review_ready -> approved | 只定义 schema，不交付具体策略 |
| MiniQMTRunnerTargetContract | FEAT-09 | install_layout、uv_python_version、dependency_policy、log_paths、kill_switch | draft -> install_dry_run_ready -> runtime_deferred | 不真实安装 |
| StrategyValidationEvidence | FEAT-09 / FEAT-07 | fixture_result、schema_result、static_guardrail_result、manual_validation_plan | missing -> partial -> pass -> blocked | 不等于 runtime verified |

## API / 接口设计

| Interface ID | 调用方 | 被调用方 | 输入契约 | 输出契约 | 错误模型 |
|---|---|---|---|---|---|
| IF-CR046-01 | 研究框架 / admission package | StrategyCoreContract | strategy metadata、target portfolio、order intent draft | platform-neutral strategy core contract | missing_required_field / unsupported_claim |
| IF-CR046-02 | StrategyPackageContract | QMTTerminalTargetContract | core contract、target config | QMT terminal target package spec | terminal_runtime_not_authorized |
| IF-CR046-03 | StrategyPackageContract | MiniQMTRunnerTargetContract | core contract、runner install policy | runner install dry-run spec | miniqmt_permission_missing / install_not_authorized |
| IF-CR046-04 | validation framework | StrategyPackageContract | package layout、schemas、fixtures | StrategyValidationEvidence | runtime_evidence_required_but_missing |
| IF-CR046-05 | 研究环境 / release operator | 交易运行 PC | zip artifact、sha256、manifest.yaml、docs bundle | 人工/受控文件传输记录和 QMT terminal import input | checksum_mismatch / unapproved_transfer_channel / runtime_not_authorized |

## 权限与安全

| Rule ID | 规则 | 触发条件 | 失败行为 | 测试入口 |
|---|---|---|---|---|
| SEC-CR046-01 | Strategy core 不得导入 QMT / XtQuant / MiniQMT | 静态扫描 | CP7 / CP8 blocked | TEST-PLAN SEC-TC-01 |
| SEC-CR046-02 | MiniQMT install design 不得读取真实 `.env` 或凭据 | runner config / install plan | blocked | TEST-PLAN SEC-TC-02 |
| SEC-CR046-03 | 任何证据不得把 fixture/static pass 声明为 runtime verified | docs / evidence | docs guardrail fail | TEST-PLAN SEC-TC-03 |
| SEC-CR046-04 | submit/cancel、account query、simulation/live 默认 0 | target adapter contract | blocked | TEST-PLAN SEC-TC-04 |

## Story 拆分建议与 LLD 策略

| Story ID | feature_design_refs | lld_policy.required_level | 触发原因 | 必须进一步设计的问题 | 可用设计证据 |
|---|---|---|---|---|---|
| CR046-S01-dual-target-strategy-architecture | `docs/features/qmt-miniqmt-dual-target-framework/DESIGN.md` | full-lld | architecture / cross-feature | FEAT-09 模块边界与接口方向 | LLD |
| CR046-S02-strategy-package-contract-and-schema | `DESIGN.md` / `TEST-PLAN.md` | full-lld | schema / validation | manifest、目录、schema 版本 | LLD |
| CR046-S03-qmt-terminal-target-framework | `DESIGN.md` / FEAT-07 | full-lld | external terminal / safety | 终端 target 与 no-runtime 边界 | LLD |
| CR046-S04-miniqmt-runner-install-and-runtime-boundary | `DESIGN.md` / FEAT-07 | full-lld | install / external / credential | install dry-run、uv、rollback、kill switch | LLD |
| CR046-S05-verification-framework-and-evidence-model | `TEST-PLAN.md` | full-lld | evidence / safety claims | 证据分级与 guardrail | LLD |
| CR046-S06-follow-up-strategy-delivery-gate | `TASKS.md` | technical-note | follow-up gate | CR047/049 启动条件 | Story 技术说明 |
| CR046-S07-research-framework-follow-up-contract | `DESIGN.md` | technical-note | research handoff | CR051 消费合同 | Story 技术说明 |

## 下游消费契约

| 消费方 | 消费时机 | 输入契约 | 输出 / 状态要求 | 降级策略 |
|---|---|---|---|---|
| story-manager | CP4 | Story 拆分建议、lld_policy、file ownership | Story 卡片含 `feature_design_refs` / `lld_policy` | 缺失则 CP4 FAIL |
| lld-designer | CP5 前 | Feature DESIGN / TEST-PLAN / TASKS + Story 卡片 | S01..S05 full-lld，S06..S07 technical-note | 缺失 required 设计则 blocked |
| meta-qa | CP7 / CP8 | TEST-PLAN、证据分级规则、不授权项 | VERIFICATION / TEST-REPORT / REVIEW 追溯 | 缺失则补测试计划或 WAIVED |

## 风险与回退

| Risk ID | 风险 | 影响 | 缓解 | 回退 |
|---|---|---|---|---|
| R-CR046-01 | 策略包合同被误读为可交易策略包 | 高 | 不授权项写入 Story、CP4、CP5、文档 guardrail | 回退到 CP3 / CP5 修改声明 |
| R-CR046-02 | MiniQMT install design 被误执行 | 高 | 只设计 install dry-run，真实 install 后置 CR049 | 停止并转 runtime authorization |
| R-CR046-03 | 研究输出合同不足 | 中 | S07 记录 CR051 消费合同 | 转 CR051 或 Spike |
