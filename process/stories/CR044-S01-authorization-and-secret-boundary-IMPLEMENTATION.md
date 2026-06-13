---
status: complete
version: "1.0"
story_id: "CR044-S01"
story_slug: "authorization-and-secret-boundary"
feature_id: "feat-cr044-auth"
implementation_type: "mixed"
source_story: "process/stories/CR044-S01-authorization-and-secret-boundary.md"
source_design_evidence: "process/stories/CR044-S01-authorization-and-secret-boundary-LLD.md"
created_by: "meta-dev"
created_at: "2026-06-11T12:03:03+08:00"
updated_at: "2026-06-11T12:03:03+08:00"
---

# Implementation: CR044-S01 Authorization and Secret Boundary

## 1. 实现摘要

| 项目 | 内容 |
|---|---|
| 实现目标 | 在 `engine/broker_adapter.py` 中落地 CR044 授权层、未授权动作、敏感字段扩展、脱敏摘要和 fail-closed admission decision。 |
| 行为变化 | Goldminer 路径新增 L1/L2-only 结构化证据；真实凭据、账号、查询、submit/cancel、simulation/live 继续不授权。 |
| 范围边界 | 不读取 `.env`，不导入或调用 `gm` / `gmtrade` / broker / network / trading runtime，不运行 simulation/live。 |
| CP6 证据 | `process/checks/CP6-CR044-S01-authorization-and-secret-boundary-CODING-DONE.md` |

## 2. 上游设计引用

| 来源 | 路径 / ID | 本次消费内容 |
|---|---|---|
| Story | `process/stories/CR044-S01-authorization-and-secret-boundary.md` | 授权层、敏感字段、redaction 和 fail-closed 范围。 |
| Story 设计证据 | `process/stories/CR044-S01-authorization-and-secret-boundary-LLD.md` | S01 第 2/5/6/10/11 节合同。 |
| CP5 | `process/checkpoints/CP5-CR044-ALL-STORIES-LLD-BATCH.md` | CP5 approved；继续不授权 L3+ 真实 runtime。 |
| CP6 context | `process/context/CP6-CR044-IMPLEMENTATION-CONTEXT.yaml` | L2 blocked-first / fixture-only 实现范围和验证命令。 |

## 3. 实现前置检查

| 检查项 | 结果 | 证据 / 说明 |
|---|---|---|
| 上游 Feature 设计存在或 N/A | PASS | CR044 scoped matrix 已在 CP5 batch 消费。 |
| Story 范围明确 | PASS | S01 LLD confirmed。 |
| 待确认问题已关闭 | PASS | CP5 clarification blocking=0。 |
| 影响范围可定位 | PASS | 仅 `engine/broker_adapter.py`、CR044 测试和本实现证据。 |
| 验证方式明确 | PASS | CR042 回归 + CR044 fixture tests + `git diff --check`。 |
| 当前 Wave / dev_gate 满足 | PASS | CP5 approved；context `status=ready`。 |
| 文件所有权无冲突 | PASS | 按 CR044 串行合入；未修改禁止文件。 |

## 4. 实现对象清单

| 对象 | 类型 | 目标 | 是否必须 | 验证方式 |
|---|---|---|---|---|
| `engine/broker_adapter.py` | code | 新增授权层、未授权动作、敏感字段和 redaction helper。 | yes | pytest / AST scan |
| `tests/test_cr044_goldminer_admission_guard.py` | guardrail-test | 验证 S01 no-secret / redaction / no-runtime 合同。 | yes | pytest |
| 本文件 | docs-handoff | 记录实现映射和验证入口。 | yes | CP6 review |

## 5. 设计契约映射

| 设计要求 | 来源 | 实现位置 | 实现动作 | 验证 |
|---|---|---|---|---|
| 定义 L1-L5 authorization layers | S01 §2/§5 | `CR044AuthorizationLayer`、`CR044_AUTHORIZATION_LAYERS` | create | `test_cr044_authorization_layers_and_redaction_are_fixture_only` |
| 定义 not-authorized actions | S01 §2 | `CR044_NOT_AUTHORIZED_ACTIONS`、`cr044_not_authorized_actions()` | create | pytest |
| 扩展敏感字段并只输出 REDACTED | S01 §2/§6 | `SENSITIVE_FIELD_PATTERNS`、`redact_sensitive_payload()` | modify/create | pytest |
| fail-closed admission | S01 §6/§7 | `evaluate_goldminer_admission()` | create | pytest |

## 6. 单元测试 / Fixture 计划

| 测试对象 | 测试类型 | 输入 / Fixture | 期望 | 覆盖风险 | 状态 |
|---|---|---|---|---|---|
| authorization layers | fixture | L1-L5 静态结构 | L1/L2 authorized，L3-L5 not_authorized | 授权边界误读 | passed |
| redaction | fixture | 合成 account/token/session payload | 输出字段路径和 `REDACTED`，不含原值 | 敏感值泄漏 | passed |
| no runtime import/call | structure-check | AST | 无 Goldminer / broker / network runtime import/call | 未授权 runtime | passed |

## 7. 最小实现切片

| Slice ID | 对应设计契约 | 改动对象 | 输出文件 | 局部验证 | 状态 |
|---|---|---|---|---|---|
| CR044-S01-IMPL-1 | authorization + redaction | broker adapter constants/helpers | `engine/broker_adapter.py` | pytest CR044 S01 test | done |
| CR044-S01-IMPL-2 | fixture guard | test file | `tests/test_cr044_goldminer_admission_guard.py` | pytest | done |
| CR044-S01-IMPL-3 | CP6 handoff | docs/check | 本文件 + CP6 | review | done |

## 8. 变更说明

### 8.1 代码变更

| 文件 | 动作 | 说明 |
|---|---|---|
| `engine/broker_adapter.py` | modify | 新增 CR044 授权、脱敏和 admission 结构；扩展敏感字段模式。 |

### 8.2 Guardrail / 测试变更

| 文件 / 命令 | 动作 | 说明 |
|---|---|---|
| `tests/test_cr044_goldminer_admission_guard.py` | create | 新增 S01-S06 fixture-only 合同测试。 |

### 8.3 文档变更

| 文件 | 动作 | 说明 |
|---|---|---|
| 本文件 | create | Story 实现说明。 |
| `process/checks/CP6-CR044-S01-authorization-and-secret-boundary-CODING-DONE.md` | create | CP6 自检证据。 |

## 9. 平台差异处理

| 平台 | 检查项 | 预期 | 结果 |
|---|---|---|---|
| Claude Code | direct ask agent 有 `AskUserQuestion` | n/a | N/A；未改 Agent。 |
| Codex | 不写 Claude-only `tools` schema | yes | PASS |
| install | dry-run 可执行 | n/a | N/A；未改安装器。 |

## 10. 验证结果

| 命令 / 检查 | 结果 | 证据 |
|---|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr042_broker_adapter_contract.py tests/test_cr044_goldminer_admission_guard.py` | PASS | 13 passed |
| `git diff --check -- engine/broker_adapter.py tests/test_cr044_goldminer_admission_guard.py process/stories/CR044-* process/checks/CP6-CR044-*` | PASS | 收尾验证执行。 |

## 11. 未覆盖项

| 未覆盖内容 | 原因 | 后续处理 |
|---|---|---|
| L3+ 真实授权、凭据读取、登录连接 | 当前明确不授权 | 未来必须独立逐 run 授权并重进设计门。 |

## 12. 风险与回滚

| Risk ID | 风险 | 影响 | 缓解 | 回滚 / 切换条件 |
|---|---|---|---|---|
| CR044-S01-R1 | 脱敏字段列表仍可能不覆盖未来真实 broker 字段 | artifact 泄漏风险 | 字段列表只能扩展不可收窄；CP7 artifact scan | 发现真实字段需求时回 CP5 或新 CR。 |

## 13. 设计缺口反馈

| Gap ID | 发现阶段 | 问题 | 应反馈到 | 是否阻塞 | 推荐处理 |
|---|---|---|---|---|---|
| N/A | implementation | 未发现阻塞设计缺口 | N/A | no | N/A |

## 14. QA / Review / Doc 后续交接

### QA 关注点

- 检查 redaction summary 只含字段路径、`REDACTED` 和计数；不得含真实值。
- 检查所有真实 operation counts 仍为 0。

### Review 关注点

- 关注 `SENSITIVE_FIELD_PATTERNS` 扩展是否只增不减。

### Doc 关注点

- 用户可见文档继续声明 CP5/CP8 approve 不等于 L3+ 运行授权。
