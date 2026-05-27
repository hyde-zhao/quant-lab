---
handoff_id: "META-DEV-CR006-BATCH-A-DEV-W3-S03-2026-05-19"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-dev"
recommended_agent_name: "dev-he"
status: "completed"
created_at: "2026-05-19T21:45:00+08:00"
change_id: "CR-006"
batch_id: "CR006-BATCH-A"
story_id: "CR006-S03-backtrader-clean-feed-contract"
wave_id: "CR006-DEV-W3"
dispatch:
  required: true
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_name: "dev-he"
  tool_name: "resume_agent"
  agent_id: "019e3b8b-953b-70e0-be88-c412fc25ed2d"
  thread_id: "019e3b8b-953b-70e0-be88-c412fc25ed2d"
  spawned_at: ""
  resumed_at: "not-provided-by-main-thread"
  completed_at: "2026-05-19T22:19:01+08:00"
  evidence_status: "completed-cp6-pass"
  evidence: "用户回报主线程已真实调度 meta-dev/dev-he，agent_id/thread_id=019e3b8b-953b-70e0-be88-c412fc25ed2d；CP6 文件 process/checks/CP6-CR006-S03-backtrader-clean-feed-contract-CODING-DONE.md status=PASS；S03 7 passed，相关 36 passed，import-boundary 8 passed，全量 127 passed。"
---

# Handoff: CR006 DEV W3 / S03

## 目标

请 meta-dev 在 W2/S02 CP6 完成后实现 `CR006-S03-backtrader-clean-feed-contract`。CP5 已由用户人工批准，本 handoff 只授权按 S03 LLD 进入代码实现和 CP6 编码完成检查；不得跳过 CP6/CP7。

## 必读输入

- `process/stories/CR006-S03-backtrader-clean-feed-contract-LLD.md`
- `process/checks/CP5-CR006-S03-backtrader-clean-feed-contract-LLD-IMPLEMENTABILITY.md`
- `process/checks/CR006-DATA-CONTRACT-CP5-CONTEXT-2026-05-19.md`
- `checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md`
- `process/DEVELOPMENT-PLAN.yaml`
- `process/STATE.md`
- `process/changes/CR-006-LEGACY-DATA-DIRECTORY-EXTERNALIZATION-2026-05-18.md`

## 允许写入范围

- `engine/backtrader_adapter.py`
- `engine/backtest.py`
- `market_data/readers.py`
- `tests/test_cr006_backtrader_clean_feed.py`
- `process/checks/CP6-CR006-S03-backtrader-clean-feed-contract-CODING-DONE.md`

如发现必须修改以上范围外文件，停止实现并回报 meta-po，不得自行扩大范围。

## 禁止范围

- 不修改 `market_data/connectors/**`、`market_data/runtime.py`、`market_data/storage.py`、`README.md`、`docs/USER-MANUAL.md`、`delivery/**`。
- 不读取、列出、迁移、复制、比对或删除真实 `data/**`。
- 不读取、打印或记录 `.env`、Tushare token、NAS 用户名、NAS 密码或真实私有路径。
- 不执行真实 Tushare 抓取、真实 lake read/write、normalize、revalidate、replay 或回补 job。
- 不导入数据层 connector/runtime/storage，不联网，不读取 token/env，不把旧 `data/**` 或 raw/manifest 作为 Backtrader runtime 输入。

## 实现边界

- Backtrader 只消费 quality gate 后的 clean feed。
- 允许 clean feed read/validation；禁止数据层 job/runtime/storage/connector、真实 lake、token/env、旧 data 等。
- 与 S02 的 `market_data/readers.py`、`engine/backtest.py` 共享文件必须基于 W2 完成后的版本继续修改。

## CP6 要求

完成后写入 `process/checks/CP6-CR006-S03-backtrader-clean-feed-contract-CODING-DONE.md`，至少包含：

- Agent Dispatch Evidence：主线程真实 `spawn_agent` / `resume_agent` / `send_input` 的 agent_id/thread_id、时间和完成状态。
- 修改文件清单与是否超出允许范围。
- 执行命令与结果，最低要求：`uv run --python 3.11 pytest -q tests/test_cr006_backtrader_clean_feed.py`。
- 安全声明：未触碰真实 `data/**`、未读取凭据、未执行真实 Tushare/lake 操作。
- 后续 CP7 建议验证范围。

## 调度门槛

- 本 handoff 是 CR006-BATCH-A 的 dev wave 3。
- 默认必须等待 W2/S02 CP6 PASS 后调度。
- S03 可与 W3/S04 并行，因为 S04 不写 `engine/**` 或 `market_data/**`；若 S04 guardrail 测试需要扫描 S03 新代码，主线程需协调 S04 在 S03 完成后再做最终 CP6 测试确认。

## 完成回填

- 状态：`completed-cp6-pass`
- 执行 agent：`meta-dev/dev-he`
- agent_id / thread_id：`019e3b8b-953b-70e0-be88-c412fc25ed2d`
- CP6：`process/checks/CP6-CR006-S03-backtrader-clean-feed-contract-CODING-DONE.md`
- 测试：S03 7 passed；相关 36 passed；import-boundary 8 passed；全量 127 passed。
- 安全声明：未读取、列出、迁移、复制、比对或删除真实 `data/**`；未读取/打印 `.env`、真实 token 或 NAS 凭据；未执行真实 Tushare/lake/normalize/revalidate/replay job。
