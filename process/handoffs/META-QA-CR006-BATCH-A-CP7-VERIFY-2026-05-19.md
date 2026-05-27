---
handoff_id: "META-QA-CR006-BATCH-A-CP7-VERIFY-2026-05-19"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-qa"
recommended_agent_name: "qa-wei"
status: "completed"
created_at: "2026-05-19T22:25:00+08:00"
change_id: "CR-006"
batch_id: "CR006-BATCH-A"
wave_id: "CR006-BATCH-A-CP7"
target_stories:
  - "CR006-S01-tushare-first-data-acquisition-runbook"
  - "CR006-S02-canonical-gold-lightweight-engine-adapter"
  - "CR006-S03-backtrader-clean-feed-contract"
  - "CR006-S04-old-data-reference-only-guardrail"
dispatch:
  required: true
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-qa"
  agent_name: "qa-wei"
  agent_path: ".codex/agents/meta-qa.toml"
  tool_name: "user-reported-main-thread-dispatch"
  agent_id: "not-provided-by-main-thread"
  thread_id: "not-provided-by-main-thread"
  spawned_at: ""
  resumed_at: "not-provided-by-main-thread"
  completed_at: "2026-05-19T22:32:37+08:00"
  evidence: "用户回报 meta-qa/qa-wei 已完成 CP7 验证；四份 Story CP7 与 batch summary 均为 PASS。CP7 文件自身说明当前工具上下文未暴露 spawn_agent/resume_agent/send_input 元数据，因此本 handoff 不伪造 agent_id/thread_id。"
---

# Handoff: CR006-BATCH-A CP7 Verification

## 目标

请 meta-qa 对 CR006-BATCH-A 四个已完成 CP6 的 Story 做 CP7 验证。当前四个 CP6 均为 PASS，且主线程已补跑 CR006 聚合验证和全量测试；CP7 仍必须由 meta-qa 独立复核并写入 CP7 检查结果，不得由 meta-po 直接标记 verified。

## 必读输入

- `process/changes/CR-006-LEGACY-DATA-DIRECTORY-EXTERNALIZATION-2026-05-18.md`
- `process/STATE.md`
- `checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md`
- `process/checks/CR006-DATA-CONTRACT-CP5-CONTEXT-2026-05-19.md`
- `process/stories/CR006-S01-tushare-first-data-acquisition-runbook-LLD.md`
- `process/stories/CR006-S02-canonical-gold-lightweight-engine-adapter-LLD.md`
- `process/stories/CR006-S03-backtrader-clean-feed-contract-LLD.md`
- `process/stories/CR006-S04-old-data-reference-only-guardrail-LLD.md`
- `process/checks/CP6-CR006-S01-tushare-first-data-acquisition-runbook-CODING-DONE.md`
- `process/checks/CP6-CR006-S02-canonical-gold-lightweight-engine-adapter-CODING-DONE.md`
- `process/checks/CP6-CR006-S03-backtrader-clean-feed-contract-CODING-DONE.md`
- `process/checks/CP6-CR006-S04-old-data-reference-only-guardrail-CODING-DONE.md`
- `process/handoffs/META-DEV-CR006-BATCH-A-DEV-W1-S01-2026-05-19.md`
- `process/handoffs/META-DEV-CR006-BATCH-A-DEV-W2-S02-2026-05-19.md`
- `process/handoffs/META-DEV-CR006-BATCH-A-DEV-W3-S03-2026-05-19.md`
- `process/handoffs/META-DEV-CR006-BATCH-A-DEV-W3-S04-2026-05-19.md`

## 允许写入范围

- `process/checks/CP7-CR006-S01-tushare-first-data-acquisition-runbook-VERIFICATION-DONE.md`
- `process/checks/CP7-CR006-S02-canonical-gold-lightweight-engine-adapter-VERIFICATION-DONE.md`
- `process/checks/CP7-CR006-S03-backtrader-clean-feed-contract-VERIFICATION-DONE.md`
- `process/checks/CP7-CR006-S04-old-data-reference-only-guardrail-VERIFICATION-DONE.md`
- `process/checks/CP7-CR006-BATCH-A-VERIFICATION-SUMMARY-2026-05-19.md`

如发现必须修改上述范围外文件，停止并回报 meta-po。CP7 不授权修改业务代码、测试代码、README、USER-MANUAL、`.gitignore`、LLD、CP5、CP6、HLD、ADR、Story Backlog 或 Development Plan。

## 禁止范围

- 不实现代码，不修测试，不改文档正文，不改 `.gitignore`。
- 不读取、列出、迁移、复制、比对或删除真实 `data/**`。
- 不读取、打印或记录 `.env`、Tushare token、NAS 用户名、NAS 密码或真实私有路径。
- 不执行真实 Tushare 抓取、真实 lake read/write、normalize、revalidate、replay 或 backfill job。
- 不把旧 repo `data/**` 作为 fallback、迁移源、覆盖证明、fixture、smoke 前置或运行时输入。

## 必验范围

请至少验证以下命令或等价更严格离线命令：

| 范围 | 命令 | 期望 |
|---|---|---|
| S01 focused | `uv run --python 3.11 pytest -q tests/test_cr006_tushare_first_acquisition.py` | PASS；开发回报为 4 passed |
| S02 focused | `uv run --python 3.11 pytest -q tests/test_cr006_lightweight_engine_adapter.py` | PASS；开发回报为 4 passed |
| S03 focused | `uv run --python 3.11 pytest -q tests/test_cr006_backtrader_clean_feed.py` | PASS；开发回报为 7 passed |
| S04 focused | `uv run --python 3.11 pytest -q tests/test_cr006_old_data_reference_guardrail.py` | PASS；开发回报为 5 passed |
| CR006 aggregate | `uv run --python 3.11 pytest -q tests/test_cr006_old_data_reference_guardrail.py tests/test_cr006_backtrader_clean_feed.py tests/test_cr006_lightweight_engine_adapter.py tests/test_cr006_tushare_first_acquisition.py` | PASS；主线程回报为 20 passed |
| full regression | `uv run --python 3.11 pytest -q` | PASS；主线程回报为 127 passed |

若 CP7 无法重跑某条命令，必须在对应 CP7 文件中写明原因、替代证据和风险判断，不得静默通过。

## 复核重点

- S01：默认 dry-run、无真实网络/写湖；相对 `data/**` lake root fail fast；runbook/manifest 输出不泄露 token 或真实路径。
- S02：canonical/gold reader 为 P0；optional `legacy_flat` 默认禁用；repo `data` 不作为 fallback；缺数据/质量失败返回结构化错误。
- S03：Backtrader 只消费 clean feed；不导入 connector/runtime/storage；不读取 env/token；不触发 fetch/backfill/normalize/revalidate/replay。
- S04：README、USER-MANUAL、`.gitignore` 和 guardrail 表达旧 repo `data/` reference-only；旧数据不作为 fallback、迁移源、覆盖证明、fixture 或 smoke 前置。
- 跨 Story：S02/S03 共享 `market_data/readers.py`、`engine/backtest.py` 的最终版本一致；S04 post-S03 聚合验证已覆盖；CR006 aggregate 与 full regression 均通过。

## CP7 输出要求

每个 CP7 文件和批次 summary 必须包含：

- Entry Criteria、Checklist、Exit Criteria、Deliverables。
- Agent Dispatch Evidence：主线程真实 `spawn_agent` / `resume_agent` / `send_input` 的 agent_id/thread_id、时间和完成状态。
- 执行命令、结果、失败重跑记录和最终结论。
- 安全确认：未触碰真实 `data/**`，未读取凭据，未执行真实 Tushare/lake/normalize/revalidate/replay/backfill。
- Story 结论：`PASS`、`FAIL`、`BLOCKED` 或 `WAIVED`；如任一 Story 非 PASS/WAIVED，批次不得标记 verified。

## 下一步

本 handoff 已完成。meta-po 已汇总 CP7 结果并将 `CR006-BATCH-A` 标记为 `verified`；由于 CR-006 自动终验授权=false，当前不得自动关闭 CR-006，下一步等待用户关闭确认。

## 完成回填

- 状态：`completed-cp7-pass`
- 执行 agent：`meta-qa/qa-wei`
- 完成时间：`2026-05-19T22:32:37+08:00`
- 说明：用户回报 meta-qa/qa-wei 已完成；CP7 文件未暴露平台 `spawn_agent` / `resume_agent` 元数据，本 handoff 不伪造 agent id。
- 输出：
  - `process/checks/CP7-CR006-S01-tushare-first-data-acquisition-runbook-VERIFICATION-DONE.md`
  - `process/checks/CP7-CR006-S02-canonical-gold-lightweight-engine-adapter-VERIFICATION-DONE.md`
  - `process/checks/CP7-CR006-S03-backtrader-clean-feed-contract-VERIFICATION-DONE.md`
  - `process/checks/CP7-CR006-S04-old-data-reference-only-guardrail-VERIFICATION-DONE.md`
  - `process/checks/CP7-CR006-BATCH-A-VERIFICATION-SUMMARY-2026-05-19.md`
- 结论：BATCH-A CP7 PASS，无 BLOCKING / REQUIRED，安全边界 PASS。
