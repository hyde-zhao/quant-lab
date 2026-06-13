---
story_id: "CR041-S01-strategy-admission-package-reader"
title: "StrategyAdmissionPackage Reader"
story_slug: "strategy-admission-package-reader"
lld_version: "1.0"
tier: "M"
status: "confirmed"
confirmed: true
created_by: "meta-po-inline-fallback"
created_at: "2026-06-10T22:48:00+08:00"
confirmed_by: "user"
confirmed_at: "2026-06-10T23:23:00+08:00"
shared_fragments:
  - "process/context/CP3-CR041-DESIGN-CONTEXT.yaml"
  - "process/research/multifactor_strategy_candidates/run-cr039-multifactor-strategy-candidates-20260610/STRATEGY-ADMISSION-PACKAGE.json"
feature_design_refs: []
lld_policy:
  required_level: "full-lld"
  trigger_reasons:
    - "research-to-simulation boundary"
    - "fail-closed package validation"
    - "no-real-operation guardrail"
  rationale: "CR039 package 是 CR041 的唯一策略输入边界，必须校验后才能进入本地 paper simulation。"
open_items: 0
---

# LLD: CR041-S01 - StrategyAdmissionPackage Reader

## 0. 上游设计依据

| 来源 | 路径 / ID | 被本 LLD 消费的内容 |
|---|---|---|
| CR041 | `process/changes/CR-041-API-LESS-PAPER-SIMULATION-RUNNER-2026-06-10.md` | CR041 目标、Story 批次、不授权边界。 |
| CP2 | `process/checkpoints/CP2-CR041-REQUIREMENTS-BASELINE.md` | L2-minus、T+1 raw open、成本/滑点/容量和 no broker 决策。 |
| CP3 | `process/context/CP3-CR041-DESIGN-CONTEXT.yaml` | StrategyAdmissionPackageReader -> OrderIntentBuilder -> PaperBroker -> Ledger -> Reports 架构。 |
| CR039 package | `process/research/multifactor_strategy_candidates/run-cr039-multifactor-strategy-candidates-20260610/STRATEGY-ADMISSION-PACKAGE.json` | `research_baseline`、`simulation_candidate=false`、blocked claims、operation counts。 |

## 1. Goal

创建 `engine/paper_simulation.py` 中的 admission package reader 设计，读取并校验 CR039 策略准入包，输出 `PaperSimulationAdmissionView`。该视图只表示“允许进入本地 paper simulation 设计链路”，不表示 simulation-ready、live-ready 或 broker-ready。

## 2. Requirements（Functional / Non-Functional）

### 2.1 Functional

- 读取 JSON package，要求 `schema_version=multifactor_strategy_admission_package_v1`、`status=PASS`、`overall_admission=research_baseline`。
- 选择唯一或指定 `strategy_id=strategy_equal_weight_baseline` 的候选；候选必须 `admission=research_baseline` 且 `simulation_candidate=false`。
- 校验 package 顶层 `not_authorization=true`、`not_simulation_authorization=true`、`not_live_authorization=true`、`not_broker_order=true`。
- 校验 `operation_counts` 所有禁止操作为 0，任一非 0 fail-closed。
- 保留 `input_refs`、`blocked_claims`、`allowed_claims`、`unlock_conditions`，供报告和安全说明消费。

### 2.2 Non-Functional

- 安全：不得读取凭据、账户、broker 状态，不得 import 或调用 QMT / 掘金 / Backtrader runtime。
- 可审计：输出视图必须包含 source path、run_id、strategy_id、package hash 和校验结果。
- 稳定性：字段缺失、schema mismatch、多个候选歧义、forbidden counter 非 0 均返回 blocked result，不抛裸异常作为唯一结果。

## 3. 模块拆分与职责

| 模块 / 文件组 | 职责 | 说明 |
|---|---|---|
| `engine/paper_simulation.py` | 定义 package reader、admission view、validation result 和 forbidden counter 校验 | 当前 Story primary owner。 |
| `tests/test_cr041_paper_simulation.py` | 覆盖 package 正常读取、字段缺失、候选不合格、counter 非 0 和敏感字段扫描 | S05 统一落测试文件；S01 定义测试合同。 |

## 4. 代码结构与文件影响范围

| 动作 | 文件路径 | 变更内容 |
|---|---|---|
| 创建 | `engine/paper_simulation.py` | 新增 `PaperSimulationAdmissionView`、`PaperSimulationValidation`、`load_strategy_admission_package`、`validate_strategy_admission_package`、`assert_no_forbidden_operations`。 |
| 创建 | `tests/test_cr041_paper_simulation.py` | 新增 S01 相关 fixture 和校验测试。 |

## 5. 数据模型与持久化设计

| 对象 / 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `PaperSimulationAdmissionView.schema_version` | str | 固定 `paper_simulation_admission_view_v1` | CR041 内部视图版本。 |
| `strategy_id` | str | 必填 | 默认 `strategy_equal_weight_baseline`。 |
| `source_portfolio_id` | str | 必填 | 来自 CR039 candidate。 |
| `source_run_id` | str | 必填 | CR039 run id。 |
| `simulation_candidate` | bool | 必须 false | 保留 CR039 边界，不升级授权。 |
| `package_hash` | str | 必填 | package 内容 SHA256。 |
| `blocked_claims` | list[dict] | 必填 | 不可声明项。 |
| `operation_counts` | dict[str,int] | 全部为 0 | 禁止操作计数。 |

无新增持久化；实现阶段只读 JSON 文件并返回内存对象。

## 6. API / Interface 设计

| 接口 / 入口 | 输入 | 输出 | 调用方 | 说明 |
|---|---|---|---|---|
| `load_strategy_admission_package(path)` | `PathLike` | `Mapping[str, Any]` | CLI / tests | 只读 JSON，不写文件。 |
| `validate_strategy_admission_package(payload, expected_strategy_id)` | package dict、策略 ID | `PaperSimulationValidation` | reader / tests | fail-closed 校验。 |
| `build_admission_view(payload, source_path, expected_strategy_id)` | package dict、路径、策略 ID | `PaperSimulationAdmissionView` 或 blocked result | S02 | 成功后作为 S02 输入。 |
| `assert_no_forbidden_operations(operation_counts)` | counter dict | `None` 或 validation violation | reader / tests | 任一非 0 阻断。 |

## 7. 核心处理流程

1. 读取 package JSON 并计算 hash。
2. 校验 schema、status、overall admission、not authorization flags。
3. 扫描 `operation_counts`，任一禁止项非 0 时返回 blocked。
4. 在 `strategy_candidates` 中定位 expected strategy。
5. 校验 candidate 为 `research_baseline` 且 `simulation_candidate=false`。
6. 输出 admission view；保留 blocked claims，供 S05 报告明确“不授权”。

## 8. 技术设计细节

- 关键规则：CR041 允许消费 `simulation_candidate=false` 的 research baseline，是为了本地模拟设计，不代表 CR039 本身已 simulation-ready。
- 依赖选择：只使用标准库 `json`、`hashlib`、`dataclasses`、`pathlib`、`typing`。
- 敏感字段扫描：字段名包含 token/password/cookie/session/account_id/credential 时阻断，避免 package 被污染。
- 图示类型选择：流程较短，不需要 Mermaid。

## 9. 安全与性能设计

| 维度 | 设计措施 | 验证方式 |
|---|---|---|
| 安全 | 所有真实操作 counters 必须为 0 | 单元测试构造非 0 counter。 |
| 安全 | forbidden import / SDK 关键词扫描 | 测试扫描 `engine/paper_simulation.py`。 |
| 性能 | 单文件 JSON 读取和 O(n) candidate 扫描 | 小 fixture 单测。 |

## 10. 测试设计

| 测试场景 | 前置条件 | 操作 | 预期结果 | 验证方式 |
|---|---|---|---|---|
| S01-T01 正常 CR039 package | fixture 含 research baseline candidate | build admission view | passed，strategy_id 正确，simulation_candidate false | `uv run --python 3.11 pytest -q tests/test_cr041_paper_simulation.py` |
| S01-T02 counter 非 0 | `credential_read=1` | validate | blocked，reason 指向 forbidden operation | 同上 |
| S01-T03 错误声明 | `simulation_ready` 被 allowed | validate | blocked | 同上 |
| S01-T04 敏感字段 | package 含 token 字段 | validate | blocked | 同上 |

## 11. 实施步骤

| TASK-ID | 动作 | 目标文件 | 详细描述 | 对应测试 |
|---|---|---|---|---|
| CR041-S01-T1 | 创建 | `engine/paper_simulation.py` | 定义 admission view / validation dataclass 和 blocked reason | S01-T01 |
| CR041-S01-T2 | 创建 | `engine/paper_simulation.py` | 实现 package 读取、hash、schema 和 candidate 校验 | S01-T01、S01-T03 |
| CR041-S01-T3 | 创建 | `engine/paper_simulation.py` | 实现 forbidden counter 与敏感字段扫描 | S01-T02、S01-T04 |
| CR041-S01-T4 | 创建 | `tests/test_cr041_paper_simulation.py` | 添加 S01 fixture 和测试 | S01-T01..S01-T04 |

## 12. 风险、难点与预研建议

### 12.1 实现灰区与取舍记录

| Clarification ID | 问题 | 选项与推荐 | 决策 / 答案 | 影响面 | 证据 | 重访条件 |
|---|---|---|---|---|---|---|
| N/A | 无阻断澄清项 | 按 CR039 package 当前 schema 消费 | 已由 CR041 CP2/CP3 同意 | 接口 / 安全 | CP2/CP3 checkpoint | CR039 package schema 变更时重访。 |

| 风险 / 难点 | 影响 | 缓解措施 / 预研建议 |
|---|---|---|
| CR039 package 字段未来变化 | S01 reader 可能误判 | 版本化 schema，未知版本 fail-closed。 |
| 用户误读 research_baseline | 授权风险 | admission view 保留 not_authorization 和 blocked_claims。 |

### OPEN / Spike 跟踪

| ID | 类型（OPEN / Spike） | 问题 | 下一动作 | 责任方 |
|---|---|---|---|---|
| N/A | OPEN | 无 | 无 | N/A |

## 13. 回滚与发布策略

- 发布方式：随 CR041 实现提交本地模块和测试，不触发真实运行。
- 回滚触发条件：package 校验误放行、发现敏感字段未阻断、counter 非 0 未阻断。
- 回滚动作：回退 `engine/paper_simulation.py` 中 S01 reader 相关实现，保留 LLD 作为修复依据。

## 14. Definition of Done

- [ ] 14 个章节全部填写完成
- [ ] 文件影响范围、接口、测试与实施步骤可直接指导编码
- [ ] 实现灰区与取舍记录已写明无阻断项
- [ ] `confirmed=false` 时不进入实现
- [ ] OPEN / Spike 已清点

## 人工确认区

CP5 批次人工确认文件：`process/checkpoints/CP5-CR041-ALL-STORIES-LLD-BATCH.md`。
