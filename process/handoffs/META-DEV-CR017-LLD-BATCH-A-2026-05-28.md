---
handoff_id: "META-DEV-CR017-LLD-BATCH-A-2026-05-28"
from_agent: "meta-po"
to_agent: "meta-dev"
created_at: "2026-05-28T06:20:01+08:00"
completed_at: "2026-05-28T06:34:27+08:00"
status: "completed"
workflow_id: "local_backtest-cr015-cr016-cr017"
change_id: "CR-017"
batch_id: "CR017-ADJUSTMENT-DUAL-VIEW-BATCH-A"
phase: "lld-design"
dispatch:
  required: true
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".agents/agents/meta-dev.md"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e6b87-a390-7921-86fb-9c573a924ff4"
  agent_name: "dev-kong"
  thread_id: "019e6b87-a390-7921-86fb-9c573a924ff4"
  spawned_at: "2026-05-28T06:22:10+08:00"
  resumed_at: ""
  completed_at: "2026-05-28T06:34:27+08:00"
  evidence: "spawn_agent"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# META-DEV CR017 LLD Batch A 交接

## Trigger

CR-015 / CR-016 / CR-017 CP3 已 approved，CP4 自动预检 `process/checks/CP4-CR015-CR016-CR017-STORY-DAG-PARALLEL-SAFETY.md` 结论为 PASS。当前只授权 CR017 LLD 设计与 Story 级 CP5 自动预检，不授权实现。

## Story Scope

| Story | Story 卡片 | LLD 输出 | CP5 自动预检 |
|---|---|---|---|
| CR017-S01-adjustment-policy-requirements-and-adr-refresh | `process/stories/CR017-S01-adjustment-policy-requirements-and-adr-refresh.md` | `process/stories/CR017-S01-adjustment-policy-requirements-and-adr-refresh-LLD.md` | `process/checks/CP5-CR017-S01-adjustment-policy-requirements-and-adr-refresh-LLD-IMPLEMENTABILITY.md` |
| CR017-S02-raw-prices-and-adj-factor-contract-hardening | `process/stories/CR017-S02-raw-prices-and-adj-factor-contract-hardening.md` | `process/stories/CR017-S02-raw-prices-and-adj-factor-contract-hardening-LLD.md` | `process/checks/CP5-CR017-S02-raw-prices-and-adj-factor-contract-hardening-LLD-IMPLEMENTABILITY.md` |
| CR017-S03-qfq-hfq-derived-view-normalization | `process/stories/CR017-S03-qfq-hfq-derived-view-normalization.md` | `process/stories/CR017-S03-qfq-hfq-derived-view-normalization-LLD.md` | `process/checks/CP5-CR017-S03-qfq-hfq-derived-view-normalization-LLD-IMPLEMENTABILITY.md` |
| CR017-S04-reader-api-and-policy-gates | `process/stories/CR017-S04-reader-api-and-policy-gates.md` | `process/stories/CR017-S04-reader-api-and-policy-gates-LLD.md` | `process/checks/CP5-CR017-S04-reader-api-and-policy-gates-LLD-IMPLEMENTABILITY.md` |
| CR017-S05-validation-quality-parity-and-leakage-tests | `process/stories/CR017-S05-validation-quality-parity-and-leakage-tests.md` | `process/stories/CR017-S05-validation-quality-parity-and-leakage-tests-LLD.md` | `process/checks/CP5-CR017-S05-validation-quality-parity-and-leakage-tests-LLD-IMPLEMENTABILITY.md` |
| CR017-S06-research-qmt-consumer-docs-and-migration-guide | `process/stories/CR017-S06-research-qmt-consumer-docs-and-migration-guide.md` | `process/stories/CR017-S06-research-qmt-consumer-docs-and-migration-guide-LLD.md` | `process/checks/CP5-CR017-S06-research-qmt-consumer-docs-and-migration-guide-LLD-IMPLEMENTABILITY.md` |

## Required Inputs

- `process/checks/CP4-CR015-CR016-CR017-STORY-DAG-PARALLEL-SAFETY.md`
- `process/HLD-DATA-LAKE.md` §18
- `process/HLD.md` §31
- `process/HLD-QMT-TRADING.md`
- `process/ARCHITECTURE-DECISION.md` ADR-053、ADR-054、ADR-055、ADR-058、ADR-059
- `process/DEVELOPMENT-PLAN.yaml`
- `process/STORY-BACKLOG.md`
- 本批次 6 张 Story 卡片

## Task

1. 按 `lld-designer` 规则为本批次 6 个 Story 各生成一份 14 章节 LLD。
2. 每份 LLD 必须 `confirmed=false`、`implementation_allowed=false`，并记录 CP5 前真实操作计数为 0。
3. 为每个 Story 写一份 CP5 自动预检文件，检查 LLD 可实现性、依赖、文件所有权、测试设计和安全边界。
4. CP5 自动预检结论只能是 `PASS` / `FAIL` / `BLOCKED` / `WAIVED`。
5. 本 handoff 的 Result Summary 可回填完成摘要。

## Allowed Files

- `process/stories/CR017-S*.md`
- `process/stories/CR017-S*-LLD.md`
- `process/checks/CP5-CR017-S*-LLD-IMPLEMENTABILITY.md`
- 本 handoff 文件

## Forbidden Scope

- 不修改 `process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml`、`process/STORY-STATUS.md`、HLD、ADR、需求或场景。
- 不修改业务代码、测试、`pyproject.toml`、`uv.lock`。
- 不读取或输出 `.env`、token、QMT 账号、session、cookie、交易密码或任何凭据。
- 不执行真实抓取、真实写湖、publish current pointer、QMT API、发单、撤单、账户查询或账户写操作。
- 不创建 CR015 / CR016 的 LLD 或 CP5 文件。
- 不回填 CP5 人工审查；统一 CP5 由 meta-po 在全部 LLD 完成后生成。

## Result Summary

status: completed
completed_at: 2026-05-28T06:34:27+08:00

本批次已完成 CR017-S01..S06 六份 Story LLD 与六份 Story 级 CP5 自动预检，所有 LLD 均保持 `confirmed=false`、`implementation_allowed=false`，并记录 CP5 前真实操作计数为 0。

输出 LLD：

- `process/stories/CR017-S01-adjustment-policy-requirements-and-adr-refresh-LLD.md`
- `process/stories/CR017-S02-raw-prices-and-adj-factor-contract-hardening-LLD.md`
- `process/stories/CR017-S03-qfq-hfq-derived-view-normalization-LLD.md`
- `process/stories/CR017-S04-reader-api-and-policy-gates-LLD.md`
- `process/stories/CR017-S05-validation-quality-parity-and-leakage-tests-LLD.md`
- `process/stories/CR017-S06-research-qmt-consumer-docs-and-migration-guide-LLD.md`

输出 CP5 自动预检：

- `process/checks/CP5-CR017-S01-adjustment-policy-requirements-and-adr-refresh-LLD-IMPLEMENTABILITY.md`：PASS
- `process/checks/CP5-CR017-S02-raw-prices-and-adj-factor-contract-hardening-LLD-IMPLEMENTABILITY.md`：PASS
- `process/checks/CP5-CR017-S03-qfq-hfq-derived-view-normalization-LLD-IMPLEMENTABILITY.md`：PASS
- `process/checks/CP5-CR017-S04-reader-api-and-policy-gates-LLD-IMPLEMENTABILITY.md`：PASS
- `process/checks/CP5-CR017-S05-validation-quality-parity-and-leakage-tests-LLD-IMPLEMENTABILITY.md`：PASS
- `process/checks/CP5-CR017-S06-research-qmt-consumer-docs-and-migration-guide-LLD-IMPLEMENTABILITY.md`：PASS

Story 卡片状态已更新为 `lld-ready-for-review`，`lld_gate.status=ready-for-review`，`dev_gate.implementation_allowed=false` 保持不变。未修改业务代码、测试代码、`pyproject.toml`、`uv.lock`、CR015 / CR016 文件、HLD / ADR / 需求 / 场景或 `STATE.md`。

注意：读取到 HLD / ADR 文件 frontmatter 仍保留历史 `confirmed: false` 标记，但 `checkpoints/CP3-CR015-CR016-CR017-HLD-REVIEW.md`、CP4 与本 handoff 均记录 CR015/016/017 CP3 已人工 approved；本批次按 handoff 授权进入 LLD，且无权修改 HLD / ADR frontmatter。
