---
handoff_id: "META-DEV-CR006-BATCH-A-DEV-W1-S01-2026-05-19"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-dev"
recommended_agent_name: "dev-kong"
status: "completed"
created_at: "2026-05-19T21:45:00+08:00"
change_id: "CR-006"
batch_id: "CR006-BATCH-A"
story_id: "CR006-S01-tushare-first-data-acquisition-runbook"
wave_id: "CR006-DEV-W1"
dispatch:
  required: true
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_name: "dev-kong"
  tool_name: "resume_agent"
  agent_id: "019e3b8b-1448-74f0-adff-c217808e4374"
  thread_id: "019e3b8b-1448-74f0-adff-c217808e4374"
  spawned_at: ""
  resumed_at: "not-provided-by-main-thread"
  completed_at: "2026-05-19"
  evidence_status: "completed-cp6-pass"
  evidence: "用户回报主线程已真实调度 meta-dev/dev-kong，agent_id/thread_id=019e3b8b-1448-74f0-adff-c217808e4374；CP6 文件 process/checks/CP6-CR006-S01-tushare-first-data-acquisition-runbook-CODING-DONE.md status=PASS；S01 4 passed，扩展 27 passed。"
---

# Handoff: CR006 DEV W1 / S01

## 目标

请 meta-dev 实现 `CR006-S01-tushare-first-data-acquisition-runbook`。CP5 已由用户人工批准，本 handoff 只授权按 S01 LLD 进入代码实现和 CP6 编码完成检查；不得跳过 CP6/CP7。

## 必读输入

- `process/stories/CR006-S01-tushare-first-data-acquisition-runbook-LLD.md`
- `process/checks/CP5-CR006-S01-tushare-first-data-acquisition-runbook-LLD-IMPLEMENTABILITY.md`
- `process/checks/CR006-DATA-CONTRACT-CP5-CONTEXT-2026-05-19.md`
- `checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md`
- `process/DEVELOPMENT-PLAN.yaml`
- `process/STATE.md`
- `process/changes/CR-006-LEGACY-DATA-DIRECTORY-EXTERNALIZATION-2026-05-18.md`

## 允许写入范围

- `market_data/cli.py`
- `market_data/connectors/tushare.py`
- `market_data/storage.py`
- `market_data/normalization.py`
- `market_data/validation.py`
- `market_data/catalog.py`
- `tests/test_cr006_tushare_first_acquisition.py`
- `process/checks/CP6-CR006-S01-tushare-first-data-acquisition-runbook-CODING-DONE.md`

如发现必须修改以上范围外文件，停止实现并回报 meta-po，不得自行扩大范围。

## 禁止范围

- 不修改 `engine/**`、`experiments/**`、`README.md`、`docs/USER-MANUAL.md`、`delivery/**`。
- 不读取、列出、迁移、复制、比对或删除真实 `data/**`。
- 不读取、打印或记录 `.env`、Tushare token、NAS 用户名、NAS 密码或真实私有路径。
- 不执行真实 Tushare 抓取、真实 lake read/write、normalize、revalidate、replay 或回补 job。
- 不把旧 repo `data/**` 作为 fallback、覆盖证明、迁移源或测试前提。

## 实现边界

- 只实现 S01 LLD 中冻结的 Tushare-first acquisition/runbook、raw/manifest 审计边界、canonical/gold lineage 和 no-old-data 采集边界。
- 真实抓取入口只能以 dry-run / plan / 显式用户触发的代码路径形式存在；本轮验证不得触发真实网络抓取。
- raw/manifest 只能作为采集审计、断点续传、复现、replay 和质量追溯层，不得作为运行时回测输入。

## CP6 要求

完成后写入 `process/checks/CP6-CR006-S01-tushare-first-data-acquisition-runbook-CODING-DONE.md`，至少包含：

- Agent Dispatch Evidence：主线程真实 `spawn_agent` / `resume_agent` / `send_input` 的 agent_id/thread_id、时间和完成状态。
- 修改文件清单与是否超出允许范围。
- 执行命令与结果，最低要求：`uv run --python 3.11 pytest -q tests/test_cr006_tushare_first_acquisition.py`。
- 安全声明：未触碰真实 `data/**`、未读取凭据、未执行真实 Tushare/lake 操作。
- 后续 CP7 建议验证范围。

## 调度门槛

- 本 handoff 是 CR006-BATCH-A 的 dev wave 1。
- 主线程可立即真实调度一个 meta-dev 执行本 handoff。
- S02 不应与 S01 并行启动，除非主线程明确接受跨 Story contract-only 并发风险；默认按 `S01 -> S02 -> S03/S04` 执行。

## 完成回填

- 状态：`completed-cp6-pass`
- 执行 agent：`meta-dev/dev-kong`
- agent_id / thread_id：`019e3b8b-1448-74f0-adff-c217808e4374`
- CP6：`process/checks/CP6-CR006-S01-tushare-first-data-acquisition-runbook-CODING-DONE.md`
- 测试：S01 4 passed；扩展 27 passed。
- 安全声明：未读取、列出、迁移、复制、比对或删除真实 `data/**`；未读取/打印 `.env`、真实 token 或 NAS 凭据；未执行真实 Tushare/lake/normalize/revalidate/replay job。
