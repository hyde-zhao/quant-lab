---
checkpoint_id: "CP2-CR030-REQUIREMENTS-BASELINE"
change_id: "CR-030"
type: "manual"
status: "approved"
created_at: "2026-06-03T06:51:19+08:00"
created_by: "meta-po"
reviewed_by: "user"
reviewed_at: "2026-06-03T06:51:19+08:00"
approval_text: "@meta-po 你可以组织meta-se输出HLD了，输出HLD后发起人工确认。"
auto_precheck: "process/checks/CP2-CR030-REQUIREMENTS-BASELINE.md"
auto_final_authorization: false
---

# CP2 CR-030 Requirements Baseline 人工审查

## 自动预检摘要

| 项目 | 结论 | 证据 |
|---|---|---|
| CP1 use-case completeness | PASS | `process/checks/CP1-CR030-USE-CASE-COMPLETENESS.md` |
| CP2 requirements baseline | PASS | `process/checks/CP2-CR030-REQUIREMENTS-BASELINE.md` |
| CP2 discussion checkpoint | PASS | `process/checks/CP2-CR030-DISCUSSION-CHECKPOINT.json` |
| 正式场景基线 | PASS | `process/USE-CASES.md` v1.14，新增 `UC-20` 至 `UC-27` |
| 正式需求基线 | PASS | `process/REQUIREMENTS.md` v1.15，新增 `REQ-174` 至 `REQ-185` |

## Decision Brief

推荐决策：批准 CR-030 CP2 需求 / 场景基线，并进入 CP3/HLD。批准含义仅为允许 meta-se 输出 HLD 和 CP3 人工审查稿；不表示授权实现、依赖变更、外部项目运行、源码迁移、provider/lake/publish、QMT/simulation/live 或凭据读取。

### 待人工决策清单

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 推荐 / 备选优劣摘要 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|---|
| DQ-CP2-CR030-01 | scope | CR-030 是否确认为自有多因子研究闭环主线？ | 确认 CR-030 为项目自有闭环主线；外部项目不作为默认框架 | A. Qlib runner-first；B. 仅做文档调研 | 推荐方案与现有数据湖、研究契约和 Stage6 gate 一致；Qlib-first 依赖和 provider 假设更重；仅文档调研无法支撑后续实现 | 若直接接入外部 runner，可能产生双 truth、依赖扩散和授权风险 | CP3 证明 runner 必要且合同冻结后，另启 CR-026 |
| DQ-CP2-CR030-02 | scope | 是否确认 UC-20 至 UC-27 为本轮场景基线？ | 确认并写入正式 `USE-CASES.md` | A. 收窄为 Qlib + Alphalens；B. 延后外部项目矩阵 | 推荐方案覆盖准确性、合理性和易分析性；收窄会漏成熟实践；延后会削弱 HLD 证据 | 场景过宽会增加 HLD 工作量，但不扩大实现授权 | 若用户要求删减，回退到 CP2 修改后重发 |
| DQ-CP2-CR030-03 | follow_up_tracking | CR-026 Qlib isolated runner 如何分流？ | 保留为合同冻结后的后续 Spike candidate，不并行启动 | A. 合并为 CR-030 P0 Story；B. 取消 CR-026 | 推荐方案避免 runner 先行绑架 schema；合并会扩大依赖和运行面；取消会丢失 Qlib runner 价值 | 并行启动会和 CR-030 合同冻结冲突 | FactorPanel / LabelWindow / ReportCatalog / runner I/O 冻结后可启动 CR-026 |
| DQ-CP2-CR030-04 | implementation | 多因子 schema 与校验如何设计？ | 采用项目自有契约，但不从零设计：以 `research_input_v1`、实验 17-21 `FactorDefinition`、CR-011 factor panel audit、label window gate、Stage6 admission gate 为基线；用 Qlib / Alphalens / Zipline / LEAN cross-check；CP3 输出字段字典、校验规则、错误码、failure policy 和外部映射，CP5 用 fixture 证明 fail-closed | A. 直接采用 Qlib / Alphalens / Zipline 对象；B. 从零设计全新 schema | 推荐方案兼顾本项目事实源和成熟项目经验；直接采用外部对象会引入依赖和语义迁移；从零设计遗漏风险高 | 若 HLD 无法证明字段覆盖和 fail-closed，CP3 应要求修改 | CP3 发现既有基线不足时，只允许以增量字段和兼容策略补齐 |
| DQ-CP2-CR030-05 | runtime_authorization | CP2 是否授权安装、运行、克隆外部项目或真实 provider / QMT 操作？ | 不授权 | A. 授权隔离运行 Spike；B. 授权安装但不运行 | 推荐方案权限面最小；运行 Spike 可增加实证但扩大许可证 / 依赖 / 安全面 | 任何运行授权都需要额外环境、日志脱敏和回滚策略 | 需要运行时另起 CR / Spike 并通过 CP3/CP5 或 per-run 授权 |
| DQ-CP2-CR030-06 | scope | 外部项目调研面是否采用 CR-030 候选清单？ | 采用完整候选清单，CP3 逐项复核 | A. 只保留 Qlib、Alphalens、Zipline；B. 只保留本地 Qlib | 完整矩阵能避免单项目偏见；收窄工作量低但准确性不足 | HLD 篇幅和分析工作量增加 | CP3 可按推荐等级折叠低优先级项目，但不得删除边界结论 |
| DQ-CP2-CR030-07 | implementation | 现有 research dataset 与实验 17-21 是否作为基线能力复用？ | 复用并标准化，不重做平行框架 | A. 从零重写多因子框架；B. 仅保留旧实验报告 | 推荐方案减少双 truth；重写风险和回归面高；只保留旧报告无法进入准入闭环 | 现有对象若缺字段，需设计兼容和迁移 | CP3 如发现现有能力不足，列增量补齐 Story |
| DQ-CP2-CR030-08 | runtime_authorization | 研究到执行交接是否只允许报告和 `order_intent_draft_v1` 草稿？ | 是，不生成真实交易信号、不声明 QMT-ready | A. 允许生成可执行 order；B. 完全不设计执行交接 | 推荐方案保留生产路线衔接且不越权；可执行 order 会绕过 QMT CR；不设计交接会削弱 Stage6 闭环 | 用户可能误读准入包为交易授权，需在 CP3 明示不授权项 | 后续 CR-020..CR-024 单独授权后才可进入真实 QMT |
| DQ-CP2-CR030-09 | risk_acceptance | CP2 approve 是否接受“静态调研但不授权运行”的风险边界？ | 接受 | A. 要求立即运行外部项目验证；B. 完全不参考外部项目 | 推荐方案用静态调研降低依赖风险；立即运行证据更强但授权面大；不参考外部项目准确性不足 | 静态调研可能遗漏运行时细节，HLD 需明确为待 Spike 风险 | 后续如运行时细节成为阻塞，转 bounded Spike |

## Entry Criteria

| 条目 | 结果 | 证据 |
|---|---|---|
| CR-030 已创建正式 CR | PASS | `process/changes/CR-030-MULTIFACTOR-RESEARCH-FRAMEWORK-REFERENCE-AND-RESEARCH-LOOP-STANDARDIZATION-2026-06-02.md` |
| 场景基线完成 | PASS | `process/USE-CASES.md` v1.14 |
| 需求基线完成 | PASS | `process/REQUIREMENTS.md` v1.15 |
| 自动预检通过 | PASS | `process/checks/CP2-CR030-REQUIREMENTS-BASELINE.md` |

## Checklist

| 检查项 | 结果 | 说明 |
|---|---|---|
| Decision Brief 包含推荐和备选 | PASS | `DQ-CP2-CR030-01` 至 `DQ-CP2-CR030-09` 均含推荐、备选、优劣、风险和回退 |
| schema 缺点已处理 | PASS | DQ-CP2-CR030-04 明确基线复用、外部 cross-check 和 fail-closed |
| 不授权边界明确 | PASS | 实现、依赖、外部项目运行、源码迁移、provider/lake/publish、QMT/simulation/live、凭据读取均未授权 |
| CR-026 分流明确 | PASS | 保留为后续 Spike candidate，不并行启动 |
| 可进入 CP3/HLD | PASS | 用户已要求组织 meta-se 输出 HLD |

## Exit Criteria

| 条目 | 结果 | 说明 |
|---|---|---|
| CP2 人工确认 | PASS | 用户当前指令视为接受 CP2 推荐方案并要求进入 HLD |
| CP3 前置输入 | PASS | `USE-CASES.md` v1.14、`REQUIREMENTS.md` v1.15、analysis artifact、discussion log 可供 meta-se 消费 |
| 权限边界 | PASS | CP2 通过不构成任何实现或运行授权 |

## Deliverables

| 产物 | 状态 |
|---|---|
| `process/USE-CASES.md` v1.14 | confirmed |
| `process/REQUIREMENTS.md` v1.15 | confirmed |
| `process/checks/CP1-CR030-USE-CASE-COMPLETENESS.md` | PASS |
| `process/checks/CP2-CR030-REQUIREMENTS-BASELINE.md` | PASS |
| `checkpoints/CP2-CR030-REQUIREMENTS-BASELINE.md` | approved |

## 人工审查结果

| 字段 | 内容 |
|---|---|
| 审查结论 | approved |
| 审查人 | user |
| 审查时间 | 2026-06-03T06:51:19+08:00 |
| 用户原文 | `@meta-po 你可以组织meta-se输出HLD了，输出HLD后发起人工确认。` |
| 接受的推荐决策 | `DQ-CP2-CR030-01` 至 `DQ-CP2-CR030-09` |
| 自动终验授权 | auto_final_authorization: false |
| 不授权项 | 不授权实现、依赖变更、外部项目 clone/install/run、源码迁移、provider fetch、lake write、catalog publish、QMT / simulation / live、凭据读取 |
