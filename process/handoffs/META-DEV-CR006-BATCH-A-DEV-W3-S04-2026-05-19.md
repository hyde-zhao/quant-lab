---
handoff_id: "META-DEV-CR006-BATCH-A-DEV-W3-S04-2026-05-19"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-dev"
recommended_agent_name: "dev-yang"
status: "completed"
created_at: "2026-05-19T21:45:00+08:00"
change_id: "CR-006"
batch_id: "CR006-BATCH-A"
story_id: "CR006-S04-old-data-reference-only-guardrail"
wave_id: "CR006-DEV-W3"
dispatch:
  required: true
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_name: "dev-yang"
  tool_name: "resume_agent"
  agent_id: "019e3b90-7cf6-7b32-9a77-45017825307e"
  thread_id: "019e3b90-7cf6-7b32-9a77-45017825307e"
  spawned_at: ""
  resumed_at: "not-provided-by-main-thread"
  completed_at: "2026-05-19T22:16:53+08:00"
  evidence_status: "completed-cp6-pass-post-s03-aggregate-verified"
  evidence: "用户回报主线程已真实调度 meta-dev/dev-yang，agent_id/thread_id=019e3b90-7cf6-7b32-9a77-45017825307e；CP6 文件 process/checks/CP6-CR006-S04-old-data-reference-only-guardrail-CODING-DONE.md status=PASS；S04 5 passed；S03 完成后主线程补跑 CR006 聚合验证 20 passed，全量 127 passed。"
---

# Handoff: CR006 DEV W3 / S04

## 目标

请 meta-dev 在 W2/S02 CP6 完成后实现 `CR006-S04-old-data-reference-only-guardrail`。CP5 已由用户人工批准，本 handoff 只授权按 S04 LLD 进入代码实现和 CP6 编码完成检查；不得跳过 CP6/CP7。

## 必读输入

- `process/stories/CR006-S04-old-data-reference-only-guardrail-LLD.md`
- `process/checks/CP5-CR006-S04-old-data-reference-only-guardrail-LLD-IMPLEMENTABILITY.md`
- `process/checks/CR006-DATA-CONTRACT-CP5-CONTEXT-2026-05-19.md`
- `checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md`
- `process/DEVELOPMENT-PLAN.yaml`
- `process/STATE.md`
- `process/changes/CR-006-LEGACY-DATA-DIRECTORY-EXTERNALIZATION-2026-05-18.md`

## 允许写入范围

- `README.md`
- `docs/USER-MANUAL.md`
- `.gitignore`
- `tests/test_cr006_old_data_reference_guardrail.py`
- `process/checks/CP6-CR006-S04-old-data-reference-only-guardrail-CODING-DONE.md`

如发现必须修改以上范围外文件，停止实现并回报 meta-po，不得自行扩大范围。

## 禁止范围

- 不修改 `engine/**`、`experiments/**`、`market_data/**`、`delivery/**`。
- 不读取、列出、迁移、复制、比对或删除真实 `data/**`。
- 不读取、打印或记录 `.env`、Tushare token、NAS 用户名、NAS 密码或真实私有路径。
- 不执行真实 Tushare 抓取、真实 lake read/write、normalize、revalidate、replay 或回补 job。
- 不把旧 repo `data/**` 作为 fallback、迁移源、覆盖证明、测试前提或 smoke 证明。

## 实现边界

- 只实现旧 repo `data/` reference-only 的文档、错误提示和静态 guardrail。
- S04 对 S01/S02/S03 的依赖类型统一为 `contract`；依赖对象是 LLD 合同冻结、边界术语一致和文件所有权可调度。
- README、USER-MANUAL、`.gitignore` 与 S04 专项测试必须表达同一条合同：旧 repo `data/` 保持现状，仅供以后人工参考或另行授权比对。

## CP6 要求

完成后写入 `process/checks/CP6-CR006-S04-old-data-reference-only-guardrail-CODING-DONE.md`，至少包含：

- Agent Dispatch Evidence：主线程真实 `spawn_agent` / `resume_agent` / `send_input` 的 agent_id/thread_id、时间和完成状态。
- 修改文件清单与是否超出允许范围。
- 执行命令与结果，最低要求：`uv run --python 3.11 pytest -q tests/test_cr006_old_data_reference_guardrail.py`。
- 安全声明：未触碰真实 `data/**`、未读取凭据、未执行真实 Tushare/lake 操作。
- 后续 CP7 建议验证范围。

## 调度门槛

- 本 handoff 是 CR006-BATCH-A 的 dev wave 3。
- 默认必须等待 W2/S02 CP6 PASS 后调度。
- S04 可与 W3/S03 并行，因为 S04 不写 `engine/**`、`experiments/**` 或 `market_data/**`；若 guardrail 测试需要扫描 S03 新代码，主线程需协调 S04 在 S03 完成后再做最终 CP6 测试确认。

## 完成回填

- 状态：`completed-cp6-pass-post-s03-aggregate-verified`
- 执行 agent：`meta-dev/dev-yang`
- agent_id / thread_id：`019e3b90-7cf6-7b32-9a77-45017825307e`
- CP6：`process/checks/CP6-CR006-S04-old-data-reference-only-guardrail-CODING-DONE.md`
- 测试：S04 5 passed；S03 完成后主线程补跑 CR006 聚合验证 20 passed；全量 127 passed。
- 安全声明：未读取、列出、迁移、复制、比对或删除真实 `data/**`；未读取/打印 `.env`、真实 token 或 NAS 凭据；未执行真实 Tushare/lake/normalize/revalidate/replay job。
