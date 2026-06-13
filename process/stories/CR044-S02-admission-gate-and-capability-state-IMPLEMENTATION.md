---
status: complete
version: "1.0"
story_id: "CR044-S02"
story_slug: "admission-gate-and-capability-state"
feature_id: "feat-cr044-gate"
implementation_type: "mixed"
source_story: "process/stories/CR044-S02-admission-gate-and-capability-state.md"
source_design_evidence: "process/stories/CR044-S02-admission-gate-and-capability-state-LLD.md"
created_by: "meta-dev"
created_at: "2026-06-11T12:03:03+08:00"
updated_at: "2026-06-11T12:03:03+08:00"
---

# Implementation: CR044-S02 Admission Gate and Capability State

## 1. 实现摘要

| 项目 | 内容 |
|---|---|
| 实现目标 | 为 Goldminer stub 落地 CR044 admission decision、capability states 和 blocked-first capability 证据。 |
| 行为变化 | `GoldminerStubBrokerAdapter` 仍是唯一 Goldminer 运行态对象；新增 `cr044_admission_state()`，所有 CR044 action 输出 blocked/no-authorization。 |
| 范围边界 | 不替换真实 adapter，不导入 SDK，不连接 broker，不提升 `simulation_ready` / `live_ready`。 |
| CP6 证据 | `process/checks/CP6-CR044-S02-admission-gate-and-capability-state-CODING-DONE.md` |

## 2. 上游设计引用

| 来源 | 路径 / ID | 本次消费内容 |
|---|---|---|
| Story | `process/stories/CR044-S02-admission-gate-and-capability-state.md` | admission gate、capability state、共享文件 merge owner。 |
| LLD | `process/stories/CR044-S02-admission-gate-and-capability-state-LLD.md` | S02 第 5/6/7/10/11 节。 |
| S01 | `process/stories/CR044-S01-authorization-and-secret-boundary-LLD.md` | 授权和脱敏前置合同。 |
| CP5 | `process/checkpoints/CP5-CR044-ALL-STORIES-LLD-BATCH.md` | CP5 approved；blocked-first 风险已接受。 |

## 3. 实现前置检查

| 检查项 | 结果 | 证据 / 说明 |
|---|---|---|
| 上游 Feature 设计存在或 N/A | PASS | CR044 scoped Feature Matrix 已通过 CP5 batch。 |
| Story 范围明确 | PASS | S02 LLD confirmed。 |
| 待确认问题已关闭 | PASS | CP5 无 blocking LCQ。 |
| 影响范围可定位 | PASS | `engine/broker_adapter.py`、CR044 测试、本实现证据。 |
| 验证方式明确 | PASS | CR042 + CR044 pytest，AST scan，diff check。 |
| 当前 Wave / dev_gate 满足 | PASS | CP6 context ready。 |
| 文件所有权无冲突 | PASS | 按 S02 merge owner 串行合入。 |

## 4. 实现对象清单

| 对象 | 类型 | 目标 | 是否必须 | 验证方式 |
|---|---|---|---|---|
| `engine/broker_adapter.py` | code | capability state enum、admission dataclass、Goldminer adapter admission method。 | yes | pytest |
| `tests/test_cr044_goldminer_admission_guard.py` | guardrail-test | 验证 capability blocked-first 和 no runtime import/call。 | yes | pytest / AST |
| 本文件 | docs-handoff | 记录实现映射。 | yes | CP6 review |

## 5. 设计契约映射

| 设计要求 | 来源 | 实现位置 | 实现动作 | 验证 |
|---|---|---|---|---|
| capability states 六态可枚举 | S02 §2/§5 | `CR044GoldminerCapabilityState` | create | pytest |
| Goldminer capability 固定 no-runtime | S02 §6 | `GoldminerStubBrokerAdapter.capabilities()` | keep/extend adjacent evidence | CR042 + CR044 pytest |
| admission 输出 blocked/no-authorization | S02 §6/§7 | `evaluate_goldminer_admission()`、`cr044_admission_state()` | create | pytest |
| `simulation_ready=false`、`live_ready=false` | S02 §2/§10 | `BrokerAdapterResult.to_dict()`、CR044 decision | keep/assert | pytest |

## 6. 单元测试 / Fixture 计划

| 测试对象 | 测试类型 | 输入 / Fixture | 期望 | 覆盖风险 | 状态 |
|---|---|---|---|---|---|
| capability | contract | `GoldminerStubBrokerAdapter()` | can_query/submit/cancel false，ready flags false | capability 误读 | passed |
| admission | fixture | `cash_query` | blocked_no_authorization | gate 绕过 | passed |
| AST runtime scan | structure-check | `engine/broker_adapter.py` | 无真实 SDK / broker call | runtime 越权 | passed |

## 7. 最小实现切片

| Slice ID | 对应设计契约 | 改动对象 | 输出文件 | 局部验证 | 状态 |
|---|---|---|---|---|---|
| CR044-S02-IMPL-1 | capability state | broker adapter | `engine/broker_adapter.py` | pytest | done |
| CR044-S02-IMPL-2 | Goldminer method | adapter + tests | code/test | pytest | done |
| CR044-S02-IMPL-3 | CP6 evidence | docs/check | 本文件 + CP6 | review | done |

## 8. 变更说明

### 8.1 代码变更

| 文件 | 动作 | 说明 |
|---|---|---|
| `engine/broker_adapter.py` | modify | 新增 CR044 capability states、admission decision 和 Goldminer CR044 helper。 |

### 8.2 Guardrail / 测试变更

| 文件 / 命令 | 动作 | 说明 |
|---|---|---|
| `tests/test_cr044_goldminer_admission_guard.py` | create | 验证 Goldminer capability / admission blocked-first。 |

### 8.3 文档变更

| 文件 | 动作 | 说明 |
|---|---|---|
| 本文件 | create | Story 实现说明。 |
| `process/checks/CP6-CR044-S02-admission-gate-and-capability-state-CODING-DONE.md` | create | CP6 自检证据。 |

## 9. 平台差异处理

| 平台 | 检查项 | 预期 | 结果 |
|---|---|---|---|
| Claude Code | direct ask agent 有 `AskUserQuestion` | n/a | N/A |
| Codex | 不写 Claude-only `tools` schema | yes | PASS |
| install | dry-run 可执行 | n/a | N/A |

## 10. 验证结果

| 命令 / 检查 | 结果 | 证据 |
|---|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr042_broker_adapter_contract.py tests/test_cr044_goldminer_admission_guard.py` | PASS | 13 passed |
| `git diff --check -- engine/broker_adapter.py tests/test_cr044_goldminer_admission_guard.py process/stories/CR044-* process/checks/CP6-CR044-*` | PASS | 收尾验证执行。 |

## 11. 未覆盖项

| 未覆盖内容 | 原因 | 后续处理 |
|---|---|---|
| 真实 SDK static probe 或 runtime adapter | 当前 L2 不授权 | 未来 L3/L4/L5 逐 run 授权后新 CR。 |

## 12. 风险与回滚

| Risk ID | 风险 | 影响 | 缓解 | 回滚 / 切换条件 |
|---|---|---|---|---|
| CR044-S02-R1 | capability 字段被误读成真实 ready | 误触 runtime | `not_authorization=true` 且 ready flags false；测试断言 | 发现 ready flag true 立即回滚。 |

## 13. 设计缺口反馈

| Gap ID | 发现阶段 | 问题 | 应反馈到 | 是否阻塞 | 推荐处理 |
|---|---|---|---|---|---|
| N/A | implementation | 未发现阻塞设计缺口 | N/A | no | N/A |

## 14. QA / Review / Doc 后续交接

### QA 关注点

- 验证 `GoldminerStubBrokerAdapter` 仍不执行任何真实动作。

### Review 关注点

- 确认新增 CR044 helper 未影响 CR042 paper adapter 合同。

### Doc 关注点

- 继续将 CR044 关闭状态表述为 offline / blocked-first，而不是 simulation-ready。
