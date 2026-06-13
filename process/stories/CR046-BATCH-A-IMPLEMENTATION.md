---
change_id: "CR-046"
batch_id: "CR046-DUAL-TARGET-FRAMEWORK-BATCH-A"
phase: "story-execution"
status: "ready-for-verification"
owner: "host-orchestrator"
created_at: "2026-06-14T00:16:26+08:00"
source_context: "process/context/CP6-CR046-IMPLEMENTATION-CONTEXT.yaml"
source_cp5: "process/checkpoints/CP5-CR046-DUAL-TARGET-FRAMEWORK-BATCH-A-LLD-BATCH.md"
runtime_authorization: "framework-first only"
real_runtime_authorized: false
---

# CR046 Dual Target Framework Batch A Implementation

## 实现前置检查

| 检查项 | 状态 | 证据 | 说明 |
|---|---|---|---|
| CP3 / CP4 / CP5 已通过 | PASS | `process/checkpoints/CP5-CR046-DUAL-TARGET-FRAMEWORK-BATCH-A-LLD-BATCH.md` | 用户于 2026-06-14T00:16:26+08:00 回复“同意”，CP5 approved。 |
| Story 设计证据已确认 | PASS | S01-S05 LLD frontmatter；S06/S07 `lld_gate.status=confirmed` | S01-S05 full-lld confirmed，S06-S07 technical-note confirmed。 |
| 文件所有权可执行 | PASS | `process/context/CP6-CR046-IMPLEMENTATION-CONTEXT.yaml` | 本批只更新 CR046 scoped docs/process artifacts。 |
| 运行授权边界 | PASS | DQ-CP5-CR046-03 | 不授权真实运行、连接、传输、导入、账户查询、submit/cancel、simulation/live。 |
| 验证命令明确 | PASS | CP6 context `validation_commands` | 使用 CR tracking consistency、YAML parse、diff whitespace。 |

## 实现对象清单

| 对象 | 路径 | 类型 | Owner Story | 实现结果 | 验证入口 |
|---|---|---|---|---|---|
| 双目标策略交付框架 | `docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md` | docs / contract | CR046-S01/S02/S03 | 标记 `implemented-cp6`，冻结 core/package/target/artifact transfer 合同。 | docs review / CP7 |
| MiniQMT runner 安装设计 | `docs/qmt/CR046-MINIQMT-RUNNER-INSTALL-DESIGN.md` | docs / install design | CR046-S04 | 标记 `implemented-cp6`，冻结 Windows 目录、uv、依赖隔离、配置、日志、kill switch、rollback。 | docs review / CP7 |
| 验证框架与证据模型 | `docs/qmt/CR046-VERIFICATION-FRAMEWORK.md` | docs / evidence model | CR046-S05 | 标记 `implemented-cp6`，冻结 schema/static/fixture/manual plan/runtime evidence 分级。 | docs review / CP7 |
| 研究框架 follow-up 合同 | `docs/research/CR046-RESEARCH-FRAMEWORK-FOLLOWUP.md` | docs / follow-up contract | CR046-S07 | 标记 `implemented-cp6`，冻结 CR051 研究输出字段缺口。 | docs review / CP7 |
| 后续策略交付门禁 | `process/stories/CR046-S06-follow-up-strategy-delivery-gate.md#技术说明` | process / technical-note | CR046-S06 | 已 confirmed，登记 CR047/CR048/CR049/CR051 后续 gate。 | CP5 / CP7 |
| 实现上下文 | `process/context/CP6-CR046-IMPLEMENTATION-CONTEXT.yaml` | process | batch | 记录允许范围、禁止范围和验证命令。 | YAML parse |
| 实现证据 | `process/stories/CR046-BATCH-A-IMPLEMENTATION.md` | process | batch | 本文件。 | CP6 checklist |
| CP6 检查 | `process/checks/CP6-CR046-DUAL-TARGET-FRAMEWORK-BATCH-A-CODING-DONE.md` | process | batch | 自动检查结果。 | meta-flow / CP7 |

## 设计契约映射

| 契约 | 来源 | 实现位置 | 验证 |
|---|---|---|---|
| FEAT-09 独立承载 QMT / MiniQMT 双目标策略交付 | S01 LLD；DQ-CP3-CR046-01 | `docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md` | 文档状态与修订记录；CP7 docs review |
| StrategyCoreContract 平台无关，禁止 QMT / XtQuant / MiniQMT import | S01 LLD；DQ-CP3-CR046-02 | framework doc `StrategyCoreContract` | CP7 wording / forbidden import plan review |
| 策略包默认 zip + sha256 + manifest + docs bundle | S02 LLD；DQ-CR046-07；DQ-CP5-CR046-04 | framework doc `StrategyPackageContract` 与 artifact transfer section | CP7 schema/docs review |
| QMT terminal target 只定义人工导入和 shadow plan | S03 LLD | framework doc `QMTTerminalTargetContract` | CP7 boundary review |
| MiniQMT runner 只做 install design | S04 LLD；DQ-CP3-CR046-03 | install design doc | CP7 install design review |
| StrategyValidationEvidence 不声明 runtime_verified | S05 LLD；DQ-CP3-CR046-04 | verification framework doc | CP7 wording guardrail |
| 具体策略交付和实机验证后置 | S06 technical-note；DQ-CP5-CR046-05 | S06 technical-note / follow-up tracking | CP7 / CP8 follow-up review |
| 研究框架完善后置 CR051 | S07 technical-note；DQ-CP3-CR046-06 | research follow-up doc | CP7 / CP8 follow-up review |

## 单元测试与 Fixture 计划

| 验证对象 | 测试 / 检查形态 | 当前结果 |
|---|---|---|
| YAML process artifacts | YAML parse | 待 CP6 check 执行 |
| CR tracking consistency | `scripts/check_cr_tracking_consistency.py` | 待 CP6 check 执行 |
| Markdown / process docs | `git diff --check` | 待 CP6 check 执行 |
| Runtime / QMT / MiniQMT | N/A | 明确不授权，不运行 |

## 最小实现切片

| Slice ID | 对应 Story | 改动对象 | 局部验证 | 状态 |
|---|---|---|---|---|
| CR046-IMPL-1 | S01/S02/S03 | `docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md` | 修订记录、frontmatter 状态、contract review | done |
| CR046-IMPL-2 | S04 | `docs/qmt/CR046-MINIQMT-RUNNER-INSTALL-DESIGN.md` | 修订记录、frontmatter 状态、install design review | done |
| CR046-IMPL-3 | S05 | `docs/qmt/CR046-VERIFICATION-FRAMEWORK.md` | 修订记录、frontmatter 状态、runtime claim review | done |
| CR046-IMPL-4 | S06/S07 | follow-up Story technical-note / research follow-up doc | CP5 confirmed、frontmatter 状态 | done |
| CR046-IMPL-5 | batch evidence | CP6 context、IMPLEMENTATION、CP6 check | YAML / consistency / diff check | in-progress |

## 平台差异处理

| 平台 | 当前处理 | N/A / 限制 |
|---|---|---|
| QMT terminal | 只定义目标合同、人工导入和 shadow plan。 | 不真实导入、不运行、不查询账户、不 submit/cancel。 |
| MiniQMT / XtQuant | 只定义 Windows runner install design 和 dry-run plan。 | 不安装、不连接、不订阅行情、不启动 runner。 |
| Linux research workspace | 只维护文档 / 契约资产。 | 不读取 `.env`，不写真实数据湖，不 publish。 |
| Python / uv | CP6 只运行本地结构检查和一致性检查。 | 未新增依赖，未修改 `pyproject.toml` / `uv.lock`。 |

## 验证结果

| 命令 | 结果 | 说明 |
|---|---|---|
| `uv run --python 3.11 python scripts/check_cr_tracking_consistency.py --project-root .` | PASS | 修正状态枚举为 `active-cp6-pass-ready-for-verification` 后通过。 |
| YAML parse | PASS | `CR-INDEX`、`DEVELOPMENT-PLAN`、CP6 context 均可解析。 |
| `git diff --check -- <CR046 scoped files>` | PASS | whitespace / conflict marker 检查通过。 |

## 未覆盖项

| 项 | 原因 | 后续入口 |
|---|---|---|
| 具体策略交付 | CR046 framework-first 明确排除 | CR047 |
| 真实传输到交易运行 PC / QMT terminal 导入 | CP5 不授权 | CR047/CR048 runtime gate |
| QMT terminal shadow / 模拟盘验证 | CP5 不授权 | CR048 |
| MiniQMT runner install / readonly connection | 用户当前未授权且未具备权限事实 | CR049 |
| submit/cancel/simulation/live | 高风险运行操作，当前不授权 | 独立 runtime authorization / future CR |
| 研究框架代码修改 | CR046 只定义 follow-up 合同 | CR051 |

## 设计缺口反馈

| 缺口 | 状态 | 处理 |
|---|---|---|
| 真实 QMT terminal evidence schema 需等具体策略包和 runtime gate | non-blocking-open | 后置 CR048。 |
| MiniQMT 实际安装路径、权限和 Python / XtQuant 版本需真实机器确认 | non-blocking-open | 后置 CR049。 |
| 研究框架输出字段需在代码层落地 | non-blocking-open | 后置 CR051。 |

## Agent Dispatch Evidence

| 字段 | 内容 |
|---|---|
| dispatch.mode | `inline-host-orchestrator` |
| agent_id | N/A |
| agent_name | host-orchestrator |
| thread_id | N/A |
| tool_name | N/A |
| handoff_path | N/A |
| started_at | `2026-06-14T00:16:26+08:00` |
| completed_at | `2026-06-14T00:16:26+08:00` |
| fallback_reason | N/A；本次未声称由 meta-dev 子 agent 独立完成。 |

## 后续交接

- CP7 应重点复核 CR046 文档是否仍保持 framework-first，不出现 QMT-ready、MiniQMT-ready、trade-ready 或 runtime_verified=true。
- CP7 应复核 artifact transfer 合同只是设计合同，不授权真实传输、导入或运行。
- CP8 前应确认 CR047/CR048/CR049/CR051 后续候选项继续在 follow-up tracking 中保留。
