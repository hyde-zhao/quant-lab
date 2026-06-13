---
status: complete
version: "1.0"
story_id: "CR044-S04"
story_slug: "submit-cancel-kill-switch-contract"
feature_id: "feat-cr044-kill"
implementation_type: "mixed"
source_story: "process/stories/CR044-S04-submit-cancel-kill-switch-contract.md"
source_design_evidence: "process/stories/CR044-S04-submit-cancel-kill-switch-contract-LLD.md"
created_by: "meta-dev"
created_at: "2026-06-11T12:03:03+08:00"
updated_at: "2026-06-11T12:03:03+08:00"
---

# Implementation: CR044-S04 Submit Cancel Kill Switch Contract

## 1. 实现摘要

| 项目 | 内容 |
|---|---|
| 实现目标 | 落地 Goldminer submit/cancel 三层 kill switch 默认 hard-off 和 no-side-effect blocked result。 |
| 行为变化 | `order_submit` / `order_cancel` admission 同时报告 global hard-off、per-run missing、whitelist missing；Goldminer cancel 返回 blocked result。 |
| 范围边界 | 不提交订单、不撤单、不重试、不补单、不保存真实 order ref。 |
| CP6 证据 | `process/checks/CP6-CR044-S04-submit-cancel-kill-switch-contract-CODING-DONE.md` |

## 2. 上游设计引用

| 来源 | 路径 / ID | 本次消费内容 |
|---|---|---|
| Story | `process/stories/CR044-S04-submit-cancel-kill-switch-contract.md` | kill switch、whitelist、no side effect 合同。 |
| LLD | `process/stories/CR044-S04-submit-cancel-kill-switch-contract-LLD.md` | S04 第 2/5/6/7/10 节。 |
| S01/S02 | S01/S02 LLD | 授权和 admission 前置合同。 |
| CP5 | `process/checkpoints/CP5-CR044-ALL-STORIES-LLD-BATCH.md` | L5 仍不授权。 |

## 3. 实现前置检查

| 检查项 | 结果 | 证据 / 说明 |
|---|---|---|
| 上游 Feature 设计存在或 N/A | PASS | CP5 batch approved。 |
| Story 范围明确 | PASS | S04 LLD confirmed。 |
| 待确认问题已关闭 | PASS | 无 blocking LCQ。 |
| 影响范围可定位 | PASS | broker adapter、CR044 tests、process evidence。 |
| 验证方式明确 | PASS | submit/cancel fixture tests。 |
| 当前 Wave / dev_gate 满足 | PASS | CP6 context ready。 |
| 文件所有权无冲突 | PASS | 串行合入。 |

## 4. 实现对象清单

| 对象 | 类型 | 目标 | 是否必须 | 验证方式 |
|---|---|---|---|---|
| `engine/broker_adapter.py` | code | kill switch state、submit/cancel admission reasons、Goldminer cancel override。 | yes | pytest |
| `tests/test_cr044_goldminer_admission_guard.py` | guardrail-test | 验证 submit/cancel blocked、counts zero、无敏感值泄漏。 | yes | pytest |
| 本文件 | docs-handoff | 记录实现映射。 | yes | CP6 review |

## 5. 设计契约映射

| 设计要求 | 来源 | 实现位置 | 实现动作 | 验证 |
|---|---|---|---|---|
| global hard switch 默认 false | S04 §2/§5 | `CR044_GOLDMINER_KILL_SWITCH_STATE` | create | pytest |
| per-run auth 缺失 blocked | S04 §6/§7 | `evaluate_goldminer_admission()` | create | pytest |
| whitelist 为空 blocked | S04 §5/§10 | `evaluate_goldminer_admission()` | create | pytest |
| submit/cancel no side effect | S04 §6/§10 | `submit_order_intents()`、`cancel_order()` | keep/override | pytest |

## 6. 单元测试 / Fixture 计划

| 测试对象 | 测试类型 | 输入 / Fixture | 期望 | 覆盖风险 | 状态 |
|---|---|---|---|---|---|
| submit | contract | fixture intent with token | blocked, no fills/orders, counts zero, no token value | 下单越权 / 泄漏 | passed |
| cancel | contract | synthetic ref | blocked, no fills/orders, counts zero, no ref value | 撤单越权 / 泄漏 | passed |
| kill switch admission | fixture | `order_submit` / `order_cancel` | 三层 blocked reason | kill switch 误开 | passed |

## 7. 最小实现切片

| Slice ID | 对应设计契约 | 改动对象 | 输出文件 | 局部验证 | 状态 |
|---|---|---|---|---|---|
| CR044-S04-IMPL-1 | kill switch state | broker adapter | `engine/broker_adapter.py` | pytest | done |
| CR044-S04-IMPL-2 | submit/cancel blocked | adapter + tests | code/test | pytest | done |
| CR044-S04-IMPL-3 | CP6 evidence | docs/check | 本文件 + CP6 | review | done |

## 8. 变更说明

### 8.1 代码变更

| 文件 | 动作 | 说明 |
|---|---|---|
| `engine/broker_adapter.py` | modify | 新增 CR044 kill switch 默认状态和 Goldminer cancel blocked override。 |

### 8.2 Guardrail / 测试变更

| 文件 / 命令 | 动作 | 说明 |
|---|---|---|
| `tests/test_cr044_goldminer_admission_guard.py` | create | submit/cancel blocked fixture tests。 |

### 8.3 文档变更

| 文件 | 动作 | 说明 |
|---|---|---|
| 本文件 | create | Story 实现说明。 |
| `process/checks/CP6-CR044-S04-submit-cancel-kill-switch-contract-CODING-DONE.md` | create | CP6 自检证据。 |

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
| L5 run manifest、真实白名单、过期时间 | 当前 L5 不授权 | 未来逐 run 授权后新增 Story。 |

## 12. 风险与回滚

| Risk ID | 风险 | 影响 | 缓解 | 回滚 / 切换条件 |
|---|---|---|---|---|
| CR044-S04-R1 | cancel override 被误读为可撤单接口 | 交易副作用风险 | result blocked、counts zero、无真实 ref | 若出现真实 cancel 调用，立即回滚并 FAIL。 |

## 13. 设计缺口反馈

| Gap ID | 发现阶段 | 问题 | 应反馈到 | 是否阻塞 | 推荐处理 |
|---|---|---|---|---|---|
| N/A | implementation | 未发现阻塞设计缺口 | N/A | no | N/A |

## 14. QA / Review / Doc 后续交接

### QA 关注点

- 验证 submit/cancel 均无 fills、无 order_requests、真实 counts 全 0。

### Review 关注点

- 确认新增 cancel override 不调用任何外部接口。

### Doc 关注点

- runbook 中继续声明 mismatch 不触发自动补单/撤单。
