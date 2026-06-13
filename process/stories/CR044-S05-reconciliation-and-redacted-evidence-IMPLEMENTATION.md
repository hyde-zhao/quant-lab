---
status: complete
version: "1.0"
story_id: "CR044-S05"
story_slug: "reconciliation-and-redacted-evidence"
feature_id: "feat-cr044-recon"
implementation_type: "mixed"
source_story: "process/stories/CR044-S05-reconciliation-and-redacted-evidence.md"
source_design_evidence: "process/stories/CR044-S05-reconciliation-and-redacted-evidence-LLD.md"
created_by: "meta-dev"
created_at: "2026-06-11T12:03:03+08:00"
updated_at: "2026-06-11T12:03:03+08:00"
---

# Implementation: CR044-S05 Reconciliation and Redacted Evidence

## 1. 实现摘要

| 项目 | 内容 |
|---|---|
| 实现目标 | 落地 CR044 redacted reconciliation evidence、discrepancy taxonomy 和 manual-review-only route。 |
| 行为变化 | `build_goldminer_reconciliation_evidence()` 可基于 blocked result / synthetic mapping 构造脱敏证据；unknown/mismatch 只进入 manual review。 |
| 范围边界 | 不查询真实成交，不 provider_fetch，不 lake_write，不 catalog_publish，不自动补单/撤单。 |
| CP6 证据 | `process/checks/CP6-CR044-S05-reconciliation-and-redacted-evidence-CODING-DONE.md` |

## 2. 上游设计引用

| 来源 | 路径 / ID | 本次消费内容 |
|---|---|---|
| Story | `process/stories/CR044-S05-reconciliation-and-redacted-evidence.md` | evidence schema、discrepancy、redaction 和 no compensation。 |
| LLD | `process/stories/CR044-S05-reconciliation-and-redacted-evidence-LLD.md` | S05 第 2/5/6/7/10 节。 |
| S03/S04 | S03/S04 LLD | readonly mapping 与 submit/cancel no-side-effect。 |
| CP5 | `process/checkpoints/CP5-CR044-ALL-STORIES-LLD-BATCH.md` | redaction-first 风险接受。 |

## 3. 实现前置检查

| 检查项 | 结果 | 证据 / 说明 |
|---|---|---|
| 上游 Feature 设计存在或 N/A | PASS | CP5 approved。 |
| Story 范围明确 | PASS | S05 LLD confirmed。 |
| 待确认问题已关闭 | PASS | 无 blocking LCQ。 |
| 影响范围可定位 | PASS | broker adapter、CR044 test、process evidence。 |
| 验证方式明确 | PASS | redacted evidence fixture test。 |
| 当前 Wave / dev_gate 满足 | PASS | CP6 context ready。 |
| 文件所有权无冲突 | PASS | 串行合入。 |

## 4. 实现对象清单

| 对象 | 类型 | 目标 | 是否必须 | 验证方式 |
|---|---|---|---|---|
| `engine/broker_adapter.py` | code | reconciliation evidence dataclass、taxonomy、builder。 | yes | pytest |
| `tests/test_cr044_goldminer_admission_guard.py` | guardrail-test | 验证 blocked evidence、manual review、无敏感值、counts zero。 | yes | pytest |
| 本文件 | docs-handoff | 记录实现映射。 | yes | CP6 review |

## 5. 设计契约映射

| 设计要求 | 来源 | 实现位置 | 实现动作 | 验证 |
|---|---|---|---|---|
| reconciliation status 四类 | S05 §2/§5 | `CR044ReconciliationStatus` | create | pytest |
| discrepancy taxonomy | S05 §2/§6 | `CR044DiscrepancyCode` | create | pytest |
| redacted evidence schema | S05 §5/§6 | `CR044ReconciliationEvidence` | create | pytest |
| mismatch manual review only | S05 §7/§10 | `build_goldminer_reconciliation_evidence()` | create | pytest |

## 6. 单元测试 / Fixture 计划

| 测试对象 | 测试类型 | 输入 / Fixture | 期望 | 覆盖风险 | 状态 |
|---|---|---|---|---|---|
| evidence builder | fixture | blocked result + synthetic sensitive payload | blocked/manual review/redacted/counts zero | 证据泄漏 / 自动补偿 | passed |
| mismatch route | fixture | `fixture_mismatch` discrepancy | status manual review | 自动补单/撤单 | passed |
| mapping summary | fixture | readonly mapping | unknown summary present | UNKNOWN 被吞掉 | passed |

## 7. 最小实现切片

| Slice ID | 对应设计契约 | 改动对象 | 输出文件 | 局部验证 | 状态 |
|---|---|---|---|---|---|
| CR044-S05-IMPL-1 | evidence schema | broker adapter | `engine/broker_adapter.py` | pytest | done |
| CR044-S05-IMPL-2 | redaction + manual review | adapter + tests | code/test | pytest | done |
| CR044-S05-IMPL-3 | CP6 evidence | docs/check | 本文件 + CP6 | review | done |

## 8. 变更说明

### 8.1 代码变更

| 文件 | 动作 | 说明 |
|---|---|---|
| `engine/broker_adapter.py` | modify | 新增 CR044 evidence dataclass 和 builder。 |

### 8.2 Guardrail / 测试变更

| 文件 / 命令 | 动作 | 说明 |
|---|---|---|
| `tests/test_cr044_goldminer_admission_guard.py` | create | redacted reconciliation evidence fixture。 |

### 8.3 文档变更

| 文件 | 动作 | 说明 |
|---|---|---|
| 本文件 | create | Story 实现说明。 |
| `process/checks/CP6-CR044-S05-reconciliation-and-redacted-evidence-CODING-DONE.md` | create | CP6 自检证据。 |

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
| 真实 broker payload 对账 | 当前不授权真实 query / fills | 未来 L4/L5 授权后新增 runtime probe。 |

## 12. 风险与回滚

| Risk ID | 风险 | 影响 | 缓解 | 回滚 / 切换条件 |
|---|---|---|---|---|
| CR044-S05-R1 | evidence 被误当真实对账通过 | CP8 结论误报 | source 固定 fixture/blocked；manual review flag | 若要求真实 payload，回设计门。 |

## 13. 设计缺口反馈

| Gap ID | 发现阶段 | 问题 | 应反馈到 | 是否阻塞 | 推荐处理 |
|---|---|---|---|---|---|
| N/A | implementation | 未发现阻塞设计缺口 | N/A | no | N/A |

## 14. QA / Review / Doc 后续交接

### QA 关注点

- evidence 中不得出现真实 account/order/fill/session/token 值。

### Review 关注点

- `build_goldminer_reconciliation_evidence()` 只能消费传入的合成对象，不触发任何 I/O。

### Doc 关注点

- 对账差异文档应写为 manual review，不得自动补偿。
