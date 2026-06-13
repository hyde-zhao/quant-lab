---
status: complete
version: "1.0"
story_id: "CR044-S03"
story_slug: "readonly-query-field-mapping-blocked-first"
feature_id: "feat-cr044-readonly"
implementation_type: "mixed"
source_story: "process/stories/CR044-S03-readonly-query-field-mapping-blocked-first.md"
source_design_evidence: "process/stories/CR044-S03-readonly-query-field-mapping-blocked-first-LLD.md"
created_by: "meta-dev"
created_at: "2026-06-11T12:03:03+08:00"
updated_at: "2026-06-11T12:03:03+08:00"
---

# Implementation: CR044-S03 Readonly Query Field Mapping Blocked-First

## 1. 实现摘要

| 项目 | 内容 |
|---|---|
| 实现目标 | 落地 Goldminer readonly candidate mapping、mapping status 和 L4 未授权 blocked evidence。 |
| 行为变化 | cash/position/order/fill 仅输出静态候选 / unknown / redacted status；真实 readonly query 仍被 `query_cash()` / `query_positions()` 阻断。 |
| 范围边界 | 不执行 `get_cash` / `get_position(s)` / order / fill query，不保存真实 broker payload。 |
| CP6 证据 | `process/checks/CP6-CR044-S03-readonly-query-field-mapping-blocked-first-CODING-DONE.md` |

## 2. 上游设计引用

| 来源 | 路径 / ID | 本次消费内容 |
|---|---|---|
| Story | `process/stories/CR044-S03-readonly-query-field-mapping-blocked-first.md` | readonly mapping 和 L4 blocked 范围。 |
| LLD | `process/stories/CR044-S03-readonly-query-field-mapping-blocked-first-LLD.md` | 字段状态、unknown、redaction 和测试入口。 |
| S01/S02 | S01/S02 LLD | 授权与 admission 前置合同。 |
| CP6 context | `process/context/CP6-CR044-IMPLEMENTATION-CONTEXT.yaml` | L2 fixture-only 验证边界。 |

## 3. 实现前置检查

| 检查项 | 结果 | 证据 / 说明 |
|---|---|---|
| 上游 Feature 设计存在或 N/A | PASS | CP5 batch approved。 |
| Story 范围明确 | PASS | S03 LLD confirmed。 |
| 待确认问题已关闭 | PASS | 无 blocking LCQ。 |
| 影响范围可定位 | PASS | broker adapter / CR044 test / process evidence。 |
| 验证方式明确 | PASS | pytest validates mapping status and blocked query. |
| 当前 Wave / dev_gate 满足 | PASS | CP5 approved。 |
| 文件所有权无冲突 | PASS | 通过 S02 shared merge owner 串行合入。 |

## 4. 实现对象清单

| 对象 | 类型 | 目标 | 是否必须 | 验证方式 |
|---|---|---|---|---|
| `engine/broker_adapter.py` | code | `CR044ReadonlyMappingStatus`、mapping table、query blocked errors。 | yes | pytest |
| `tests/test_cr044_goldminer_admission_guard.py` | guardrail-test | 验证 mapping 不含 `real_verified` 且 readonly blocked。 | yes | pytest |
| 本文件 | docs-handoff | 记录实现映射。 | yes | CP6 review |

## 5. 设计契约映射

| 设计要求 | 来源 | 实现位置 | 实现动作 | 验证 |
|---|---|---|---|---|
| readonly query 类别与内部字段映射 | S03 §2/§5 | `CR044_GOLDMINER_READONLY_FIELD_MAPPING` | create | pytest |
| 字段状态不允许 real_verified | S03 §5/§10 | `CR044ReadonlyMappingStatus` | create | pytest |
| L4 未授权 query fail-closed | S03 §6/§10 | `query_cash()`、`query_positions()` | modify | pytest |
| 敏感 order/fill ref 标记 redacted | S03 §5 | mapping rows + sensitive patterns | create/modify | pytest |

## 6. 单元测试 / Fixture 计划

| 测试对象 | 测试类型 | 输入 / Fixture | 期望 | 覆盖风险 | 状态 |
|---|---|---|---|---|---|
| readonly mapping | fixture | `goldminer_readonly_candidate_mapping()` | status includes static/unknown/redacted, no real_verified | 候选误当真实 | passed |
| query fail-closed | contract | stub query methods | sanitized validation error | L4 越权 | passed |
| operation counts | fixture | admission decision | 全 0 | 真实 query 发生 | passed |

## 7. 最小实现切片

| Slice ID | 对应设计契约 | 改动对象 | 输出文件 | 局部验证 | 状态 |
|---|---|---|---|---|---|
| CR044-S03-IMPL-1 | mapping table | broker adapter | `engine/broker_adapter.py` | pytest | done |
| CR044-S03-IMPL-2 | readonly blocked | adapter + tests | code/test | pytest | done |
| CR044-S03-IMPL-3 | CP6 evidence | docs/check | 本文件 + CP6 | review | done |

## 8. 变更说明

### 8.1 代码变更

| 文件 | 动作 | 说明 |
|---|---|---|
| `engine/broker_adapter.py` | modify | 新增 readonly mapping table 和 `goldminer_readonly_candidate_mapping()`。 |

### 8.2 Guardrail / 测试变更

| 文件 / 命令 | 动作 | 说明 |
|---|---|---|
| `tests/test_cr044_goldminer_admission_guard.py` | create | 增加 readonly mapping 和 query blocked fixture。 |

### 8.3 文档变更

| 文件 | 动作 | 说明 |
|---|---|---|
| 本文件 | create | Story 实现说明。 |
| `process/checks/CP6-CR044-S03-readonly-query-field-mapping-blocked-first-CODING-DONE.md` | create | CP6 自检证据。 |

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
| 真实 Goldminer readonly 字段验证 | 当前 L4 不授权 | 未来 runtime probe Story。 |

## 12. 风险与回滚

| Risk ID | 风险 | 影响 | 缓解 | 回滚 / 切换条件 |
|---|---|---|---|---|
| CR044-S03-R1 | static candidate 被误用为真实字段 | 错误适配 | 测试断言无 `real_verified` | 真实查询需求出现时回设计门。 |

## 13. 设计缺口反馈

| Gap ID | 发现阶段 | 问题 | 应反馈到 | 是否阻塞 | 推荐处理 |
|---|---|---|---|---|---|
| N/A | implementation | 未发现阻塞设计缺口 | N/A | no | N/A |

## 14. QA / Review / Doc 后续交接

### QA 关注点

- 验证 readonly mapping 只能作为候选证据，不能当作真实验证。

### Review 关注点

- 关注 `query_cash()` / `query_positions()` 异常消息是否保持 sanitized。

### Doc 关注点

- CP8 结论不得写成 readonly query ready。
