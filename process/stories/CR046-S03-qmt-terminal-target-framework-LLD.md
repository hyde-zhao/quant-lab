---
story_id: "CR046-S03-qmt-terminal-target-framework"
title: "QMT terminal target 框架"
story_slug: "qmt-terminal-target-framework"
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
  - "docs/features/runtime-authorization-safety/DESIGN.md"
lld_policy:
  required_level: "full-lld"
  trigger_reasons: ["external-terminal", "security-boundary", "no-runtime"]
  rationale: "QMT terminal target 接近真实交易终端，必须 full-lld 冻结导入步骤、配置和 shadow evidence 边界。"
open_items: 0
---

# LLD: CR046-S03 — QMT terminal target 框架

## 0. 上游设计依据

| 来源 | 路径 / ID | 被本 LLD 消费的内容 |
|---|---|---|
| HLD | `docs/design/HLD-CR046-QMT-MINIQMT-DUAL-TARGET-FRAMEWORK.md` | QMT terminal target 和 shadow plan |
| ADR | `docs/design/ARCHITECTURE-DECISION-CR046.md` | runtime 不授权、证据分级 |
| Feature Matrix | `docs/design/FEATURE-DESIGN-MATRIX.md` | S03 full-lld |
| Feature DESIGN | `docs/features/qmt-miniqmt-dual-target-framework/DESIGN.md` | QMTTerminalTargetContract |
| S02 LLD | `process/stories/CR046-S02-strategy-package-contract-and-schema-LLD.md` | package artifact 和 manifest |

## 1. Goal

定义 QMT 终端策略入口、配置 schema、人工导入步骤、shadow 报告 schema 和 no-runtime 边界，使后续 CR047 能交付具体 QMT terminal target，但 CR046 不执行终端验证。

## 2. Requirements（Functional / Non-Functional）

### 2.1 Functional

- QMT target 至少覆盖 entry_file、config_schema、import_steps、shadow_report_schema。
- import_steps 必须消费已校验 sha256 的策略包 artifact。
- 明确人工导入不等于运行授权。
- submit/cancel/account query 均为 false。

### 2.2 Non-Functional

- 安全：任何真实 QMT 操作转 runtime_authorization gate。
- 可审计：import_steps 记录 artifact、manifest 和 checksum。
- 可回滚：导入失败时回到上一已校验 package。

## 3. 模块拆分与职责

| 模块 / 文件组 | 职责 | 说明 |
|---|---|---|
| qmt target manifest | QMT target 元数据 | 位于策略包 targets/qmt_terminal |
| entry file contract | 终端策略入口形态 | 后续 CR047 填具体代码 |
| config schema | 参数和路径配置 | 不含真实账户 |
| import steps | 人工导入流程 | 不执行 |
| shadow report schema | 后续 shadow 证据格式 | CR046 只定义 |

## 4. 代码结构与文件影响范围

| 动作 | 文件路径 | 变更内容 |
|---|---|---|
| 修改 | `docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md` | QMTTerminalTargetContract |
| 修改 | `docs/qmt/CR046-VERIFICATION-FRAMEWORK.md` | QMT shadow plan 证据分级 |
| 创建 | `process/stories/CR046-S03-qmt-terminal-target-framework-LLD.md` | 本 LLD |

## 5. 数据模型与持久化设计

无运行时持久化。设计对象：

| 对象 / 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `entry_file` | path | required | QMT 终端策略入口 |
| `config_schema` | path | required | 参数 schema |
| `import_steps` | path | required | 人工导入说明 |
| `shadow_report_schema` | path | required | 后续 shadow 计划 |
| `runtime_authorized` | bool | false | CR046 固定 false |

## 6. API / Interface 设计

| 接口 / 入口 | 输入 | 输出 | 调用方 | 说明 |
|---|---|---|---|---|
| IF-S03-01 import plan | zip + sha256 + manifest | import-ready checklist | 人工操作者 | 对应 TP-S03-01 |
| IF-S03-02 target config | target config yaml | QMT target 参数 | QMT 终端策略 | 对应 TP-S03-02 |
| IF-S03-03 shadow report | QMT shadow run result | shadow evidence | 后续 CR048 | CR046 不执行；对应 TP-S03-03 |

## 7. 核心处理流程

1. 人工操作者在交易 PC 接收 artifact。
2. 校验 sha256。
3. 打开 manifest，确认 target `qmt_terminal` 可用。
4. 按 import_steps 复制 / 导入目标文件。
5. 若没有 runtime authorization，停止在导入前或导入计划层，不运行。

## 8. 技术设计细节

- 关键规则：sha256 校验通过是 import 前置。
- 依赖复用：消费 S02 StrategyPackageContract。
- 兼容性：不同 QMT 终端导入方式由 CR047 / CR048 细化。
- 图示类型：流程图不必要，线性人工步骤足够。

## 9. 安全与性能设计

| 维度 | 设计措施 | 验证方式 |
|---|---|---|
| 安全 | runtime、account query、submit/cancel 均 false | docs guardrail |
| 性能 | 不承诺运行性能 | N/A |

## 10. 测试设计

| 测试场景 | 前置条件 | 操作 | 预期结果 | 验证方式 |
|---|---|---|---|---|
| TP-S03-01 import 入口完整 | QMT target 草案 | 审查 entry/config/import/shadow 字段 | 全部存在 | docs review |
| TP-S03-02 checksum 前置 | import_steps 草案 | 审查步骤顺序 | sha256 校验先于导入 | docs review |
| TP-S03-03 runtime 禁止 | target contract | 搜索授权字段 | 全部 false | safety review |

## 11. 实施步骤

| TASK-ID | 动作 | 目标文件 | 详细描述 | 对应测试 |
|---|---|---|---|---|
| CR046-S03-T1 | 修改 | `docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md` | 定义 QMT target 字段 | TP-S03-01 |
| CR046-S03-T2 | 修改 | 同上 | 定义 import_steps 与 sha256 前置 | TP-S03-02 |
| CR046-S03-T3 | 修改 | `docs/qmt/CR046-VERIFICATION-FRAMEWORK.md` | 定义 shadow plan 证据层级 | TP-S03-03 |
| CR046-S03-T4 | 修改 | 同上 | 写入不授权项 | TP-S03-03 |

## 12. 风险、难点与预研建议

### 12.1 实现灰区与取舍记录

| Clarification ID | 问题 | 选项与推荐 | 决策 / 答案 | 影响面 | 证据 | 重访条件 |
|---|---|---|---|---|---|---|
| N/A | 无未回答阻断项 | N/A | 当前不执行 QMT 验证 | runtime / docs | CP2/CP3 | 启动 CR048 时 |

| 风险 / 难点 | 影响 | 缓解措施 / 预研建议 |
|---|---|---|
| 导入步骤被误读为运行授权 | 高 | 文档必须写“人工导入不等于运行授权” |
| QMT 终端版本差异 | 中 | 后续 CR047/048 做具体终端适配 |

### OPEN / Spike 跟踪

| ID | 类型（OPEN / Spike） | 问题 | 下一动作 | 责任方 |
|---|---|---|---|---|
| O-S03-01 | OPEN | 具体 QMT 终端目录和导入 UI 未在 CR046 实机确认 | CR047/CR048 按用户环境补充 | host-orchestrator / user |

## 13. 回滚与发布策略

- 发布方式：框架文档和 target contract 随 CR046 发布。
- 回滚触发条件：CP5 要求 QMT-only 或删除人工导入路径。
- 回滚动作：修改 S03 LLD 和框架文档。

## 14. Definition of Done

- [x] 14 个章节全部填写完成
- [x] QMT target 字段、import_steps、shadow_report_schema 已定义
- [x] 不授权项已写入
- [x] OPEN 已清点

## 人工确认区

CP5 批次统一审查文件：`process/checkpoints/CP5-CR046-DUAL-TARGET-FRAMEWORK-BATCH-A-LLD-BATCH.md`。
