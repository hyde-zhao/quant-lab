---
story_id: "CR046-S01-dual-target-strategy-architecture"
title: "双目标策略交付架构与 FEAT-09 边界"
story_slug: "dual-target-strategy-architecture"
lld_version: "1.0"
tier: "L"
status: "ready-for-review"
confirmed: true
created_by: "host-orchestrator"
created_at: "2026-06-13T23:50:00+08:00"
confirmed_by: "user"
confirmed_at: "2026-06-14T00:16:26+08:00"
shared_fragments: []
feature_design_refs:
  - "docs/features/qmt-miniqmt-dual-target-framework/DESIGN.md"
  - "docs/features/qmt-miniqmt-dual-target-framework/TEST-PLAN.md"
lld_policy:
  required_level: "full-lld"
  trigger_reasons: ["architecture", "cross-feature", "security-boundary"]
  rationale: "FEAT-09 是 CR046 的新共享 Feature，承接 QMT terminal 与 MiniQMT runner 双目标合同，需 full-lld 冻结边界。"
open_items: 0
---

# LLD: CR046-S01 — 双目标策略交付架构与 FEAT-09 边界

## 0. 上游设计依据

| 来源 | 路径 / ID | 被本 LLD 消费的内容 |
|---|---|---|
| HLD | `docs/design/HLD-CR046-QMT-MINIQMT-DUAL-TARGET-FRAMEWORK.md` | FEAT-09 架构对象、双 target、验证分级、不授权项 |
| ADR | `docs/design/ARCHITECTURE-DECISION-CR046.md` | ADR-CR046-001/002/004/005/006 |
| Feature Matrix | `docs/design/FEATURE-DESIGN-MATRIX.md` | S01 full-lld、FEAT-09 required |
| Feature DESIGN | `docs/features/qmt-miniqmt-dual-target-framework/DESIGN.md` | StrategyCoreContract、Package、Target、Evidence 接口 |

## 1. Goal

创建 `docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md`，冻结 FEAT-09 的模块边界、调用方向、StrategyCoreContract 和 no-real-operation 约束，供 S02-S07 与后续 CR047 / CR049 / CR051 消费。

## 2. Requirements（Functional / Non-Functional）

### 2.1 Functional

- 定义至少 5 个架构对象：StrategyCoreContract、StrategyPackageContract、QMTTerminalTargetContract、MiniQMTRunnerTargetContract、StrategyValidationEvidence。
- 定义 QMT terminal 与 MiniQMT runner 两个 target 的调用方向。
- 定义研究策略到策略包再到目标 target 的 artifact 流转。
- 明确具体策略交付、runtime 验证和交易动作全部后置。

### 2.2 Non-Functional

- 安全：no-real-operation 计数目标为 0。
- 可审计：每个后续策略包必须有 package_id、layout_version、target、evidence path。
- 可移植：Strategy core 不依赖 QMT / XtQuant / MiniQMT。
- 可回滚：所有后续 runtime 行为只能通过独立 CR / authorization gate 打开。

## 3. 模块拆分与职责

| 模块 / 文件组 | 职责 | 说明 |
|---|---|---|
| StrategyCoreContract | 平台无关策略输入、输出、目标持仓、order intent、风险假设 | 禁止导入 QMT / XtQuant / MiniQMT |
| StrategyPackageContract | 策略包目录、manifest、artifact、checksum、target 列表 | S02 细化 |
| QMTTerminalTargetContract | QMT 终端入口、配置、人工导入、shadow plan | S03 细化 |
| MiniQMTRunnerTargetContract | Windows 安装目录、uv、依赖隔离、kill switch | S04 细化 |
| StrategyValidationEvidence | schema/static/fixture/manual/runtime 证据分级 | S05 细化 |

## 4. 代码结构与文件影响范围

| 动作 | 文件路径 | 变更内容 |
|---|---|---|
| 创建 | `docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md` | 双目标框架、对象合同、artifact 传输和不授权边界 |
| 创建 | `process/stories/CR046-S01-dual-target-strategy-architecture-LLD.md` | 本 LLD |

## 5. 数据模型与持久化设计

无新增运行时持久化。新增设计层合同对象：

| 对象 / 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| StrategyCoreContract | schema/object | 平台无关 | 后续 CR047 消费 |
| StrategyPackageContract | schema/object | 必含 manifest 和 artifact 字段 | S02 细化 |
| TargetContract | schema/object | target-specific | QMT / MiniQMT 分离 |
| StrategyValidationEvidence | schema/object | 不得声明 runtime verified | S05 细化 |

## 6. API / Interface 设计

| 接口 / 入口 | 输入 | 输出 | 调用方 | 说明 |
|---|---|---|---|---|
| IF-S01-01 StrategyCoreContract | research metadata、target portfolio、order intent draft | 平台无关 core 合同 | CR047 / CR051 | 对应测试 TP-CR046-01 |
| IF-S01-02 PackageContract | core contract、target list、validation suite | 策略包合同 | S02 / CR047 | 对应测试 TP-CR046-02 |
| IF-S01-03 TargetContract | package contract | QMT / MiniQMT target spec | S03 / S04 | 对应测试 TP-CR046-03/04 |
| IF-S01-04 EvidenceModel | package / target contracts | evidence model | S05 | 对应测试 TP-CR046-05 |

## 7. 核心处理流程

```mermaid
flowchart LR
  R[Research Admission Package] --> C[StrategyCoreContract]
  C --> P[StrategyPackageContract]
  P --> Q[QMTTerminalTargetContract]
  P --> M[MiniQMTRunnerTargetContract]
  Q --> E[StrategyValidationEvidence]
  M --> E
  E --> G[CP5/CP7/CP8 Gate]
```

1. 研究框架产出 strategy metadata、target portfolio、order intent draft。
2. StrategyCoreContract 统一平台无关语义。
3. StrategyPackageContract 把 core、targets、validation、docs 和 artifact 组织为包。
4. QMT / MiniQMT target contract 分别消费策略包。
5. StrategyValidationEvidence 只声明 design/schema/static/fixture/manual plan 证据。

## 8. 技术设计细节

- 关键规则：core 禁止平台 SDK；target 只定义合同；runtime 默认 false。
- 依赖复用：复用 FEAT-03 研究准入、FEAT-04 order intent、FEAT-07 no-real-operation 安全边界。
- 兼容性：若未来降级为 QMT-only，需要另起 CR 修改 FEAT-09。
- 图示类型：结构图，见第 7 节。

## 9. 安全与性能设计

| 维度 | 设计措施 | 验证方式 |
|---|---|---|
| 安全 | core 禁止导入 QMT / XtQuant / MiniQMT；所有 runtime 授权为 false | static guardrail / docs review |
| 性能 | 无运行时性能承诺；只定义合同 | N/A |

## 10. 测试设计

| 测试场景 | 前置条件 | 操作 | 预期结果 | 验证方式 |
|---|---|---|---|---|
| TP-S01-01 core 字段完整 | LLD 完成 | 审查 StrategyCoreContract 字段 | input、target_portfolio、order_intent、risk_assumption、evidence_required 均存在 | docs review |
| TP-S01-02 target 覆盖 | LLD 完成 | 审查 target contract | QMT terminal 与 MiniQMT runner 均覆盖 | docs review |
| TP-S01-03 不授权边界 | LLD 完成 | 审查不授权项 | 至少覆盖 10 类禁止操作 | docs guardrail |

## 11. 实施步骤

| TASK-ID | 动作 | 目标文件 | 详细描述 | 对应测试 |
|---|---|---|---|---|
| CR046-S01-T1 | 创建 | `docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md` | 写入架构对象和结构图 | TP-S01-01 |
| CR046-S01-T2 | 创建 | 同上 | 写入 StrategyCoreContract | TP-S01-01 |
| CR046-S01-T3 | 创建 | 同上 | 写入 target adapter 调用方向 | TP-S01-02 |
| CR046-S01-T4 | 创建 | 同上 | 写入不授权项和后续 CR gate | TP-S01-03 |

## 12. 风险、难点与预研建议

### 12.1 实现灰区与取舍记录

| Clarification ID | 问题 | 选项与推荐 | 决策 / 答案 | 影响面 | 证据 | 重访条件 |
|---|---|---|---|---|---|---|
| N/A | 无未回答阻断项 | N/A | 已由 CP2/CP3 和 DQ-CR046-07 确认 | N/A | STATE / CR046 | target 切换时 |

| 风险 / 难点 | 影响 | 缓解措施 / 预研建议 |
|---|---|---|
| 合同被误读为可运行策略 | 高 | 不授权项贯穿 HLD、LLD、CP5、CP8 |
| FEAT-09 与 FEAT-05/06 边界混淆 | 中 | 本 LLD 明确 FEAT-09 只管交付合同 |

### OPEN / Spike 跟踪

| ID | 类型（OPEN / Spike） | 问题 | 下一动作 | 责任方 |
|---|---|---|---|---|
| 无 | N/A | 无未决阻断项 | N/A | N/A |

## 13. 回滚与发布策略

- 发布方式：随 CR046 文档交付，CP8 后声明 framework-ready。
- 回滚触发条件：CP5 拒绝 FEAT-09 边界或用户要求 QMT-only。
- 回滚动作：回到 CP3 / CP4，重写 Feature Matrix 与 Story 拆分。

## 14. Definition of Done

- [x] 14 个章节全部填写完成
- [x] 文件影响范围、接口、测试与实施步骤可直接指导编码
- [x] 实现灰区与取舍记录已显式写“无”
- [x] `confirmed=false` 时不进入实现
- [x] OPEN / Spike 已清点

## 人工确认区

CP5 批次统一审查文件：`process/checkpoints/CP5-CR046-DUAL-TARGET-FRAMEWORK-BATCH-A-LLD-BATCH.md`。
