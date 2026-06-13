---
story_id: "CR046-S02-strategy-package-contract-and-schema"
title: "策略包合同、目录结构与 schema"
story_slug: "strategy-package-contract-and-schema"
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
  trigger_reasons: ["schema", "contract", "validation"]
  rationale: "策略包 manifest、目录和 schema 是 CR047 具体策略交付的合同前置。"
open_items: 0
---

# LLD: CR046-S02 — 策略包合同、目录结构与 schema

## 0. 上游设计依据

| 来源 | 路径 / ID | 被本 LLD 消费的内容 |
|---|---|---|
| HLD | `docs/design/HLD-CR046-QMT-MINIQMT-DUAL-TARGET-FRAMEWORK.md` | 策略包契约 |
| ADR | `docs/design/ARCHITECTURE-DECISION-CR046.md` | ADR-CR046-002/004/005 |
| Feature Matrix | `docs/design/FEATURE-DESIGN-MATRIX.md` | S02 full-lld |
| Feature DESIGN | `docs/features/qmt-miniqmt-dual-target-framework/DESIGN.md` | StrategyPackageContract 字段 |
| Story | `process/stories/CR046-S02-strategy-package-contract-and-schema.md` | artifact / sha256 / transfer_channel AC |

## 1. Goal

细化 `StrategyPackageContract`，使后续 CR047 可以按固定目录、manifest、artifact、checksum、target 和 validation suite 生成首个具体策略包。

## 2. Requirements（Functional / Non-Functional）

### 2.1 Functional

- 策略包目录至少包含 `strategy_core`、`targets/qmt_terminal`、`targets/miniqmt_runner`、`validation`、`docs`、`manifest.yaml`。
- `manifest.yaml` 至少覆盖 package_id、layout_version、targets、validation_suite、authorization_boundary。
- artifact 合同覆盖 zip 文件名、sha256、manifest、transfer_channel、manual_import_steps。
- 缺必填字段 fail closed。

### 2.2 Non-Functional

- 可审计：每个策略包版本必须可通过 manifest 和 sha256 追溯。
- 安全：artifact 合同不包含凭据或真实账户数据。
- 可回滚：版本化 zip 可回退到上一包。

## 3. 模块拆分与职责

| 模块 / 文件组 | 职责 | 说明 |
|---|---|---|
| manifest schema | 定义 package 元数据和授权边界 | 后续可实现为 YAML schema |
| artifact contract | 定义 zip / sha256 / transfer_channel | 用户已确认 DQ-CR046-07 |
| target index | 记录 qmt_terminal / miniqmt_runner 是否包含 | target 可 design-only |
| validation suite | 记录 schema/static/fixture/manual plan | S05 消费 |

## 4. 代码结构与文件影响范围

| 动作 | 文件路径 | 变更内容 |
|---|---|---|
| 修改 | `docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md` | StrategyPackageContract 和 artifact 传输合同 |
| 修改 | `docs/qmt/CR046-VERIFICATION-FRAMEWORK.md` | schema validation 输入输出 |
| 创建 | `process/stories/CR046-S02-strategy-package-contract-and-schema-LLD.md` | 本 LLD |

## 5. 数据模型与持久化设计

无运行时持久化。设计 schema 如下：

| 对象 / 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `package_id` | string | required | 策略包稳定 ID |
| `layout_version` | string | required | 初始 `1.0` |
| `targets[]` | list | required | 至少包含 target id 和 status |
| `validation_suite` | object | required | 指向验证入口 |
| `authorization_boundary` | object | required | 全部 runtime 默认 false |
| `artifact_name` | string | required | zip 文件名 |
| `checksum_sha256` | string | required | artifact 校验 |
| `transfer_channel` | enum | required | 人工/受控传输枚举 |
| `manual_import_steps` | path | required | QMT 导入步骤 |

## 6. API / Interface 设计

| 接口 / 入口 | 输入 | 输出 | 调用方 | 说明 |
|---|---|---|---|---|
| IF-S02-01 manifest validation | `manifest.yaml` | pass/fail + missing fields | validation framework | 对应 TP-S02-01 |
| IF-S02-02 artifact validation | zip + sha256 | checksum pass/fail | release operator / QMT import | 对应 TP-S02-02 |
| IF-S02-03 target index validation | targets list | enabled / design-only 状态 | QMT / MiniQMT target | 对应 TP-S02-03 |

## 7. 核心处理流程

1. 后续 CR047 生成策略包目录。
2. 生成 `manifest.yaml`。
3. 打包为 zip。
4. 生成 sha256。
5. 通过人工/受控通道传到交易运行 PC。
6. 交易 PC 校验 sha256 后才能进入 QMT 人工导入。
7. 任一字段缺失或 checksum 不匹配时 fail closed。

## 8. 技术设计细节

- 关键规则：manifest 是单一入口，zip 只是承载，不替代 manifest。
- 依赖选择：CR046 只写 Markdown / YAML 合同，不引入依赖。
- 兼容性：transfer_channel 可枚举扩展，但默认不自动同步。
- 图示类型：线性流程，无异步补偿。

## 9. 安全与性能设计

| 维度 | 设计措施 | 验证方式 |
|---|---|---|
| 安全 | manifest 不包含凭据；artifact 校验失败禁止导入 | schema / checksum review |
| 性能 | artifact 大小不做运行承诺 | N/A |

## 10. 测试设计

| 测试场景 | 前置条件 | 操作 | 预期结果 | 验证方式 |
|---|---|---|---|---|
| TP-S02-01 manifest 必填字段 | manifest 草案 | 删除 package_id | validation fail | schema review |
| TP-S02-02 checksum mismatch | zip + 错误 sha256 | 执行校验计划 | fail closed | fixture plan |
| TP-S02-03 target 状态 | targets list | 审查 qmt / miniqmt target | 状态明确且 runtime false | docs review |

## 11. 实施步骤

| TASK-ID | 动作 | 目标文件 | 详细描述 | 对应测试 |
|---|---|---|---|---|
| CR046-S02-T1 | 修改 | `docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md` | 写入策略包目录结构 | TP-S02-01 |
| CR046-S02-T2 | 修改 | 同上 | 写入 manifest 字段和 layout_version | TP-S02-01 |
| CR046-S02-T3 | 修改 | 同上 | 写入 artifact / sha256 / transfer_channel | TP-S02-02 |
| CR046-S02-T4 | 修改 | `docs/qmt/CR046-VERIFICATION-FRAMEWORK.md` | 写入缺字段 fail-closed 行为 | TP-S02-03 |

## 12. 风险、难点与预研建议

### 12.1 实现灰区与取舍记录

| Clarification ID | 问题 | 选项与推荐 | 决策 / 答案 | 影响面 | 证据 | 重访条件 |
|---|---|---|---|---|---|---|
| DQ-CR046-07 | 策略以什么形式传到交易运行 PC | 推荐 zip + sha256 + manifest + docs，经人工/受控通道传输 | 用户已同意 | manifest / transfer / import | STATE / CR046 | 交易 PC 传输通道变化 |

| 风险 / 难点 | 影响 | 缓解措施 / 预研建议 |
|---|---|---|
| artifact 被误认为已可运行 | 高 | manifest 和 docs 明确 runtime_authorized=false |
| 自动同步绕过人工审计 | 高 | transfer_channel 默认 manual_controlled_file_transfer |

### OPEN / Spike 跟踪

| ID | 类型（OPEN / Spike） | 问题 | 下一动作 | 责任方 |
|---|---|---|---|---|
| 无 | N/A | 无未决阻断项 | N/A | N/A |

## 13. 回滚与发布策略

- 发布方式：CP8 后以框架文档发布；具体 zip artifact 由 CR047 生成。
- 回滚触发条件：CP5 不接受 artifact 传输合同。
- 回滚动作：回到 S02 LLD 修改 manifest / transfer_channel 字段。

## 14. Definition of Done

- [x] 14 个章节全部填写完成
- [x] artifact、manifest、checksum、transfer_channel 和 import_steps 已定义
- [x] 缺字段 fail-closed 已定义
- [x] `confirmed=false` 时不进入实现
- [x] OPEN / Spike 已清点

## 人工确认区

CP5 批次统一审查文件：`process/checkpoints/CP5-CR046-DUAL-TARGET-FRAMEWORK-BATCH-A-LLD-BATCH.md`。
