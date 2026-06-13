---
cr_id: "CR-020"
title: "QMT Windows Gateway 服务端登录与只读查询接口准入"
status: "deleted-by-user"
impact_level: "high"
workflow_mode_before: "standard"
workflow_mode_after_change: "standard"
fast_lane_upgrade_reason: "该变更涉及 Windows 服务启动、端口监听、QMT / MiniQMT / XtQuant 外部接口、服务端账号登录、凭据 `.env`、HMAC / allowlist、安全脱敏、只读真实查询和多 Story 依赖，必须按 standard 模式执行。"
rollback_to: "requirement-clarification"
approval_result: "deleted-by-user-after-miniqmt-permission-unavailable"
created_at: "2026-06-04T22:28:31+08:00"
created_by: "meta-po"
approved_by: "user"
approved_at: "2026-06-04T22:53:33+08:00"
source: "cp8-follow-up"
linked_issue: ""
parent_cr: "CR-019"
source_checkpoint: "checkpoints/CP8-CR019-DELIVERY-READINESS.md"
source_decision_id: "D-CP8-CR019-02"
follow_up_type: "qmt-windows-gateway-server-login-readonly-query-admission"
risk_class: "high-runtime-credential-and-qmt-readonly-boundary"
owner: "meta-po"
revisit_condition: "用户后续明确恢复 QMT / MiniQMT / XtQuant 路线，并重新发起 CR；默认不再推进。"
acceptance_criteria: "Windows gateway 可按 S 端 `uv run` Python CLI 启动并绑定授权端口，CLI 库采用 Typer；C 端 Linux `uv run` Typer CLI 可完成配对 / 诊断 / CP7 验收；实际业务调用由 Python REST client 调用 health / capabilities / query_positions；服务端 QMT 登录和会话检查 ready；HMAC / allowlist / scope / redaction 全部 PASS；至少一次 `query_positions` 只读查询返回脱敏结果；禁止发单、撤单、账户写入、simulation / live、provider / lake / publish、broker lake 和凭据泄露。"
close_condition: "CR020-S01..S06 全部通过 CP6 / CP7；CP8 用户确认关闭；没有越过只读范围的真实交易、写账户、写 lake、publish 或凭据泄露。"
cr_index_path: "process/changes/CR-INDEX.yaml"
source_tracking: "process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md"
cp2_auto_check: "process/checks/CP2-CR020-REQUIREMENTS-BASELINE.md"
cp2_manual_review: "checkpoints/CP2-CR020-REQUIREMENTS-BASELINE.md"
cp2_discussion_log: "process/discussions/CP2-CR020-SCENARIO-DISCUSSION-LOG.md"
cp2_discussion_checkpoint: "process/checks/CP2-CR020-DISCUSSION-CHECKPOINT.json"
cp2_approval_text: "@meta-po 所有决策都同意你的备选方案。继续推进项目"
cp2_approval_interpretation: "accepted recommended CP2 decisions after DQ-CP2-CR020-04 revision"
cp2_revision_text: "好的同意你的方案"
cp2_revision_at: "2026-06-04T23:10:18+08:00"
cp2_revision_interpretation: "accepted recommended S-side Windows uv-run Python CLI with Typer; PowerShell/CMD is only the shell host, not the formal CLI contract"
cp2_revision2_text: "@meta-po 调度meta-se开始hld设计，设计时保持一致性，c端的cli也需要使用typer框架"
cp2_revision2_at: "2026-06-04T23:23:58+08:00"
cp2_revision2_interpretation: "accepted CLI consistency policy: both S-side Windows CLI and C-side Linux CLI use Typer; C-side CLI remains pairing/diagnostics/validation only, while business runtime remains Python REST client"
cp3_hld_handoff: "process/handoffs/META-SE-CR020-HLD-2026-06-04.md"
cp3_hld_dispatch_status: "completed-closed"
cp3_hld_agent_id: "019e9341-e1c1-7d91-9432-2df92264f1dc"
cp3_hld_agent_name: "se-han"
cp3_hld_spawned_at: "2026-06-04T23:30:39+08:00"
cp3_hld_completed_at: "2026-06-04T23:32:09+08:00"
cp3_hld_closed_at: "2026-06-04T23:50:59+08:00"
cp3_hld_result: "process/HLD.md#36-cr-020-qmt-windows-gateway-服务端登录与只读查询接口准入-hld-增量"
cp3_discussion_log: "process/discussions/CP3-CR020-HLD-DISCUSSION-LOG.md"
cp3_discussion_checkpoint: "process/checks/CP3-CR020-DISCUSSION-CHECKPOINT.json"
cp3_auto_check: "process/checks/CP3-CR020-HLD-CONSISTENCY.md"
cp3_auto_status: "PASS"
cp3_manual_review: "checkpoints/CP3-CR020-HLD-REVIEW.md"
cp3_manual_status: "approved"
cp3_approved_by: "user"
cp3_approved_at: "2026-06-05T06:49:15+08:00"
cp3_approval_text: "同意，你需要拉起meta-po 组织子agent完成任务，可以并行的时候需要并行拉起子agent进行"
cp3_approval_interpretation: "accepted DQ-CP3-CR020-01..07 recommended options; design-layer approval only; no implementation, dependency change, gateway start, QMT connection, real .env read, trading, account write, simulation/live, provider/lake/publish or credential output authorized"
cp3_decision_count: 7
cp4_story_planning_handoff: "process/handoffs/META-SE-CR020-STORY-PLANNING-2026-06-05.md"
cp4_story_planning_dispatch_status: "completed-closed"
cp4_story_planning_agent_id: "019e94dd-15f2-7381-bb18-dba9fb302809"
cp4_story_planning_agent_name: "se-chu"
cp4_story_planning_spawned_at: "2026-06-05T06:59:43+08:00"
cp4_story_planning_completed_at: "2026-06-05T07:03:10+08:00"
cp4_story_planning_closed_at: "2026-06-05T07:21:21+08:00"
cp4_auto_check: "process/checks/CP4-CR020-STORY-PLAN-PRECHECK.md"
cp4_auto_status: "PASS"
cp5_lld_batch_id: "CR020-QMT-GATEWAY-READONLY-BATCH-A"
cp5_lld_batch_status: "approved"
cp5_lld_batch_approved_by: "user"
cp5_lld_batch_approved_at: "2026-06-05T08:25:46+08:00"
cp5_lld_batch_approval_text: "@meta-po，你需要完成所有代码开发。我手动安装到Windows电脑后，使用cli手动验证qmt接口是否可用。你需要写完善的手动安装调试手册"
cp5_lld_batch_approval_interpretation: "accepted DQ-CP5-CR020-01..06; authorizes controlled code/doc implementation and fixture/static verification only; user will manually install on Windows and validate QMT CLI; no real .env read, gateway start, QMT connection, real query_positions, trading, account write, simulation/live, provider/lake/publish or credential output authorized for agents."
cp5_lld_max_parallel: 3
cp5_lld_wave_1_story_ids:
  - "CR020-S01-windows-gateway-runtime-admission"
  - "CR020-S02-server-qmt-login-session"
  - "CR020-S03-linux-client-rest-transport"
cp5_lld_wave_1_handoffs:
  - "process/handoffs/META-DEV-CR020-S01-LLD-2026-06-05.md"
  - "process/handoffs/META-DEV-CR020-S02-LLD-2026-06-05.md"
  - "process/handoffs/META-DEV-CR020-S03-LLD-2026-06-05.md"
cp5_lld_wave_1_dispatch_status: "completed-closed"
cp5_lld_wave_1_completed_at: "2026-06-05T07:31:38+08:00"
cp5_lld_wave_1_llds:
  - "process/stories/CR020-S01-windows-gateway-runtime-admission-LLD.md"
  - "process/stories/CR020-S02-server-qmt-login-session-LLD.md"
  - "process/stories/CR020-S03-linux-client-rest-transport-LLD.md"
cp5_lld_wave_1_cp5_checks:
  - "process/checks/CP5-CR020-S01-windows-gateway-runtime-admission-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR020-S02-server-qmt-login-session-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR020-S03-linux-client-rest-transport-LLD-IMPLEMENTABILITY.md"
cp5_lld_wave_1_cp5_status: "PASS"
cp5_lld_wave_2_story_ids:
  - "CR020-S04-hmac-pairing-allowlist-scope"
cp5_lld_wave_2_handoffs:
  - "process/handoffs/META-DEV-CR020-S04-LLD-2026-06-05.md"
cp5_lld_wave_2_dispatch_status: "completed-closed"
cp5_lld_wave_2_agent_id: "019e94fb-60a1-7082-bc27-9221e114b774"
cp5_lld_wave_2_agent_name: "dev-he"
cp5_lld_wave_2_spawned_at: "2026-06-05T07:32:48+08:00"
cp5_lld_wave_2_completed_at: "2026-06-05T07:35:14+08:00"
cp5_lld_wave_2_closed_at: "2026-06-05T07:41:30+08:00"
cp5_lld_wave_2_llds:
  - "process/stories/CR020-S04-hmac-pairing-allowlist-scope-LLD.md"
cp5_lld_wave_2_cp5_checks:
  - "process/checks/CP5-CR020-S04-hmac-pairing-allowlist-scope-LLD-IMPLEMENTABILITY.md"
cp5_lld_wave_2_cp5_status: "PASS"
cp5_lld_wave_3_story_ids:
  - "CR020-S05-query-positions-readonly"
cp5_lld_wave_3_handoffs:
  - "process/handoffs/META-DEV-CR020-S05-LLD-2026-06-05.md"
cp5_lld_wave_3_dispatch_status: "completed-closed"
cp5_lld_wave_3_agent_id: "019e9504-69a0-74d1-8377-75225fe20c94"
cp5_lld_wave_3_agent_name: "dev-qin"
cp5_lld_wave_3_spawned_at: "2026-06-05T07:42:40+08:00"
cp5_lld_wave_3_completed_at: "2026-06-05T07:47:43+08:00"
cp5_lld_wave_3_closed_at: "2026-06-05T07:54:36+08:00"
cp5_lld_wave_3_llds:
  - "process/stories/CR020-S05-query-positions-readonly-LLD.md"
cp5_lld_wave_3_cp5_checks:
  - "process/checks/CP5-CR020-S05-query-positions-readonly-LLD-IMPLEMENTABILITY.md"
cp5_lld_wave_3_cp5_status: "PASS"
cp5_lld_wave_4_story_ids:
  - "CR020-S06-docs-runbook-cp7-real-machine-validation"
cp5_lld_wave_4_handoffs:
  - "process/handoffs/META-DEV-CR020-S06-LLD-2026-06-05.md"
cp5_lld_wave_4_dispatch_status: "completed-closed"
cp5_lld_wave_4_agent_id: "019e9510-71cd-7240-ab95-ffb97f78afe9"
cp5_lld_wave_4_agent_name: "dev-kong"
cp5_lld_wave_4_spawned_at: "2026-06-05T07:55:49+08:00"
cp5_lld_wave_4_completed_at: "2026-06-05T08:04:08+08:00"
cp5_lld_wave_4_closed_at: "2026-06-05T08:04:08+08:00"
cp5_lld_wave_4_llds:
  - "process/stories/CR020-S06-docs-runbook-cp7-real-machine-validation-LLD.md"
cp5_lld_wave_4_cp5_checks:
  - "process/checks/CP5-CR020-S06-docs-runbook-cp7-real-machine-validation-LLD-IMPLEMENTABILITY.md"
cp5_lld_wave_4_cp5_status: "PASS"
cp5_lld_batch_llds:
  - "process/stories/CR020-S01-windows-gateway-runtime-admission-LLD.md"
  - "process/stories/CR020-S02-server-qmt-login-session-LLD.md"
  - "process/stories/CR020-S03-linux-client-rest-transport-LLD.md"
  - "process/stories/CR020-S04-hmac-pairing-allowlist-scope-LLD.md"
  - "process/stories/CR020-S05-query-positions-readonly-LLD.md"
  - "process/stories/CR020-S06-docs-runbook-cp7-real-machine-validation-LLD.md"
cp5_lld_batch_cp5_checks:
  - "process/checks/CP5-CR020-S01-windows-gateway-runtime-admission-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR020-S02-server-qmt-login-session-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR020-S03-linux-client-rest-transport-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR020-S04-hmac-pairing-allowlist-scope-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR020-S05-query-positions-readonly-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR020-S06-docs-runbook-cp7-real-machine-validation-LLD-IMPLEMENTABILITY.md"
cp5_lld_batch_cp5_status: "PASS"
cp5_lld_batch_manual_review: "checkpoints/CP5-CR020-QMT-GATEWAY-READONLY-LLD-BATCH.md"
cp5_lld_batch_pending_decision_count: 6
cp5_lld_batch_blocking_open_count: 0
cp5_lld_batch_non_blocking_open_count: 4
cp6_status: "PASS"
cp6_results:
  - "process/checks/CP6-CR020-S01-windows-gateway-runtime-admission-CODING-DONE.md"
  - "process/checks/CP6-CR020-S02-server-qmt-login-session-CODING-DONE.md"
  - "process/checks/CP6-CR020-S03-linux-client-rest-transport-CODING-DONE.md"
  - "process/checks/CP6-CR020-S04-hmac-pairing-allowlist-scope-CODING-DONE.md"
  - "process/checks/CP6-CR020-S05-query-positions-readonly-CODING-DONE.md"
  - "process/checks/CP6-CR020-S06-docs-runbook-cp7-real-machine-validation-CODING-DONE.md"
cp7_fixture_static_status: "PASS"
cp7_fixture_static_result: "process/checks/CP7-CR020-FIXTURE-STATIC-VERIFICATION-DONE.md"
cp7_fixture_static_handoff: "process/handoffs/META-QA-CR020-CP7-FIXTURE-STATIC-2026-06-05.md"
cp7_fixture_static_completed_at: "2026-06-05T09:13:41+08:00"
manual_windows_qmt_validation_status: "pending-miniqmt-permission"
manual_windows_qmt_validation_docs:
  - "docs/QMT-GATEWAY-INSTALL.md#cr020-windows-s-端手工安装调试手册"
  - "docs/QMT-C-S-BRIDGE-RUNBOOK.md#9-cr020-manual-install-debug-guide"
runtime_authorization: "cp2-approved-readonly-scope; Windows gateway start via uv-run Typer Python CLI, port bind, QMT server login/session check, Linux uv-run Typer CLI pairing/validation, Python REST client health/capabilities/query_positions readonly only; no order/cancel/account-write/simulation/live/provider/lake/publish"
credential_policy: "real values only in local untracked .env; tracked artifacts may contain .env.example placeholders and redacted credential_ref only"
server_command_surface: "uv run Python CLI on Windows"
server_cli_library: "Typer"
server_shell_surface: "PowerShell/CMD only as uv run host; not CLI contract"
client_command_surface: "uv run Typer Python CLI on Linux for pairing/diagnostics/validation"
client_cli_library: "Typer"
client_runtime_surface: "Python REST client direct gateway REST API calls"
cli_consistency_policy: "S and C command surfaces both use Typer; C CLI is not the business runtime surface"
first_query_interface: "query_positions"
---

# CR-020 QMT Windows Gateway 服务端登录与只读查询接口准入

> 2026-06-10 删除记录：用户确认无法获取 MiniQMT 权限，并要求“将 qmt 相关的 CR 全部标记为删除，不再做了”。CR-020 状态更新为 `deleted-by-user`。本记录不物理删除历史设计、代码、文档或 CP2-CP7 证据；但 CR-020 不再等待 MiniQMT 权限，不再进行 Windows/QMT gateway 实机验证，不再作为后续 simulation / live 路线前置。

> 2026-06-05T23:11:48+08:00 权限阻断更新：用户已验证当前只有 QMT 权限、没有 MiniQMT 权限，并决定先申请 MiniQMT 权限后再进行下一步。CR-020 保持 `active-manual-validation-pending`，但手工验证状态从 `pending-user` 更新为 `pending-miniqmt-permission`。在 MiniQMT 权限开通前，不继续排查 `userdata_mini` / `connect_result=-1`，不关闭 CR-020，也不启动 CR-021 simulation。

> 2026-06-05T06:49:15+08:00 状态更新：用户回复“同意，你需要拉起meta-po 组织子agent完成任务，可以并行的时候需要并行拉起子agent进行”，已按 `checkpoints/CP3-CR020-HLD-REVIEW.md` 的 `approve` 回填。CP3 七项 DQ 推荐方案均 accepted，当前进入 `story-planning` / CP4，下一步为调度 `meta-se` 产出正式 ADR 增量、STORY-BACKLOG 增量、DEVELOPMENT-PLAN 增量、CR020-S01..S06 Story 卡片和 CP4 自动预检。CP3 approve 仅为设计层风险接受，不授权实现、依赖变更、gateway 启动、QMT 连接、真实 `.env` 读取、交易、账户写入、simulation/live、provider/lake/publish 或凭据输出。

> 2026-06-05T06:59:43+08:00 调度更新：主线程已真实 `spawn_agent` 调度 `meta-se/se-chu` 执行 `process/handoffs/META-SE-CR020-STORY-PLANNING-2026-06-05.md`，agent_id=`019e94dd-15f2-7381-bb18-dba9fb302809`。本调度只覆盖 story-planning / CP4，不授权实现、LLD、依赖变更、gateway 启动、QMT 连接、真实 `.env` 读取、交易、账户写入、simulation/live、provider/lake/publish 或凭据输出。

> 2026-06-05T07:21:21+08:00 CP4 回收：`meta-se/se-chu` 已完成并关闭，`process/checks/CP4-CR020-STORY-PLAN-PRECHECK.md` 结论 PASS。CR-020 进入单一全量 LLD 批次 `CR020-QMT-GATEWAY-READONLY-BATCH-A`；按 `max_parallel_lld=3` 第一轮并行调度 `meta-dev/dev-lv` 负责 S01、`meta-dev/dev-shi` 负责 S02、`meta-dev/dev-zhu` 负责 S03。当前只授权 LLD 与 CP5 自动预检，不授权实现、依赖变更、gateway 启动、QMT 连接、真实 `.env` 读取、交易、账户写入、simulation/live、provider/lake/publish 或凭据输出。

> 2026-06-05T07:32:48+08:00 CP5 LLD 更新：第一轮 `CR020-S01` / `CR020-S02` / `CR020-S03` 的 LLD 与 CP5 自动预检已完成并关闭，三项 CP5 结论均为 PASS。按 CP4 依赖，主线程已真实 `spawn_agent` 调度 `meta-dev/dev-he` 执行 `CR020-S04-hmac-pairing-allowlist-scope` LLD 与 CP5 自动预检，agent_id=`019e94fb-60a1-7082-bc27-9221e114b774`。当前仍只授权 LLD 与 CP5 自动预检，不授权实现、依赖变更、gateway 启动、QMT 连接、真实 `.env` 读取、交易、账户写入、simulation/live、provider/lake/publish 或凭据输出。

> 2026-06-05T07:42:40+08:00 CP5 LLD 更新：`CR020-S04` LLD 与 CP5 自动预检已完成并关闭，CP5 结论 PASS。按依赖，主线程已真实 `spawn_agent` 调度 `meta-dev/dev-qin` 执行 `CR020-S05-query-positions-readonly` LLD 与 CP5 自动预检，agent_id=`019e9504-69a0-74d1-8377-75225fe20c94`。当前仍只授权 LLD 与 CP5 自动预检，不授权实现、依赖变更、gateway 启动、QMT 连接、真实 `.env` 读取、交易、账户写入、simulation/live、provider/lake/publish 或凭据输出。

> 2026-06-05T07:55:49+08:00 CP5 LLD 更新：`CR020-S05` LLD 与 CP5 自动预检已完成并关闭，CP5 结论 PASS。按依赖，主线程已真实 `spawn_agent` 调度 `meta-dev/dev-kong` 执行 `CR020-S06-docs-runbook-cp7-real-machine-validation` LLD 与 CP5 自动预检，agent_id=`019e9510-71cd-7240-ab95-ffb97f78afe9`。当前仍只授权 LLD 与 CP5 自动预检，不授权实现、依赖变更、gateway 启动、QMT 连接、真实 `.env` 读取、交易、账户写入、simulation/live、provider/lake/publish 或凭据输出。

> 2026-06-05T08:04:08+08:00 CP5 LLD 批次收敛：`CR020-S01`..`CR020-S06` 六份 LLD 与六份 CP5 自动预检已全部完成，CP5 自动预检全部 PASS；阻断 OPEN 为 0，非阻断 OPEN 为 4。下一步生成 `checkpoints/CP5-CR020-QMT-GATEWAY-READONLY-LLD-BATCH.md` 并发起 CP5 全量人工确认。CP5 approve 前仍不授权实现、依赖变更、gateway 启动、QMT 连接、真实 `.env` 读取、交易、账户写入、simulation/live、provider/lake/publish 或凭据输出。

> 2026-06-05T09:21:16+08:00 实现与 fixture/static 验证收敛：`CR020-S01`..`CR020-S06` 代码与文档开发已完成，六份 CP6 均为 PASS；`meta-qa/qa-he` 已完成 `process/checks/CP7-CR020-FIXTURE-STATIC-VERIFICATION-DONE.md`，结论 PASS，验证结果为 `75 passed`、`py_compile` PASS、`git diff --check` PASS，真实 `.env` 读取、gateway 启动、端口绑定、QMT 连接和真实 `query_positions` 均为 0。当前 CR-020 状态为 `active-manual-validation-pending`：等待用户按 `docs/QMT-GATEWAY-INSTALL.md` 与 `docs/QMT-C-S-BRIDGE-RUNBOOK.md` 在 Windows / Linux 环境手工验证 `query_positions` 只读链路并回填脱敏 evidence；本状态不关闭 CR、不授权交易、账户写入、simulation/live、provider/lake/publish 或凭据输出。

## 0. 本 CR 的作用

本 CR 将 `process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md` 中的 `CR-020` 候选项转为正式 active CR。原候选项只描述“QMT Windows gateway 实机部署准入”；本轮用户已明确要求打通 `local_backtest` 与 QMT 的连接，服务端需要实现 QMT 账号登录，并至少完成一个查询接口。

本 CR 只启动 CR-020 的标准门控和需求基线确认。创建本文件不等于已经授权实现、启动服务、读取真实凭据、连接 QMT、查询真实账户或执行交易。真实运行授权必须通过 CP2 / CP3 / CP5 / CP6 / CP7 / CP8 分阶段落地。

## 1. 变更描述

CR-020 的目标升级为：在 Windows 侧提供可运行的 QMT Gateway 服务端，服务端负责读取本地未跟踪 `.env` 中的 QMT 登录账号和密码，完成 QMT / MiniQMT / XtQuant 登录和会话检查；Linux C 侧通过 `uv run` Typer CLI 完成配对、诊断和 CP7 验收，实际业务运行时由 Python REST client 直接调用 gateway REST API，至少完成 `query_positions` 只读查询接口。

本 CR 的最小可关闭范围包括：

| 范围 | 要求 |
|---|---|
| S 端运行形态 | Windows 机器上运行 gateway；正式命令面为 `uv run` 启动的 Python CLI，CLI 库采用 Typer；PowerShell / CMD 只作为执行 `uv run` 的宿主 shell，不作为业务 CLI 合同。 |
| C 端调用形态 | Linux 机器调用 gateway；配对、诊断、连通性和 CP7 验收命令使用 `uv run` Typer CLI；实际业务调用由 Python REST client 直接调用 gateway REST API。 |
| 服务端登录 | gateway 服务端读取本地未跟踪 `.env`，完成 QMT 账号登录、会话 ready 检查和 fail-closed。 |
| 首个查询接口 | 推荐 `query_positions`，只读、脱敏、可审计，不产生交易或账户写入副作用。 |
| 安全边界 | HMAC / allowlist / scope / redaction 必须通过；账号、密码、token、session、交易密码和私钥不得进入 Git、对话、日志、检查点或 memory。 |

## 2. CP8 Follow-up 来源

| 字段 | 内容 |
|---|---|
| 父级 CR | `CR-019` |
| 来源检查点 | `checkpoints/CP8-CR019-DELIVERY-READINESS.md` |
| 来源决策 ID | `D-CP8-CR019-02` |
| follow-up 类型 | `qmt-windows-gateway-server-login-readonly-query-admission` |
| 风险等级 | `high-runtime-credential-and-qmt-readonly-boundary` |
| owner | `meta-po` |
| 重访条件 | CP2 / CP3 / CP5 任一门禁要求缩小范围、改变首个查询接口、改变凭据策略、改变 S / C 命令边界或 S / C 端 CLI 库，或发现 QMT 登录 / 只读查询无法在 fail-closed 条件下验证。 |
| 验收标准 | S 端 `uv run` Typer CLI 完成 gateway 启停与 health；C 端 `uv run` Typer CLI 完成 HMAC 配对 / 诊断 / CP7 验收；Python REST client 完成 `query_positions` 脱敏只读查询；服务端 QMT 登录 / 会话 ready；禁止交易、写账户、写 lake、publish 和凭据泄露。 |
| 关闭条件 | CR020-S01..S06 全部通过 CP6 / CP7，CP8 用户确认关闭，且无越权运行或秘密泄露。 |

## 3. 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `process/USE-CASES.md` | 原文档更新 | 保留既有 CR-019 / CR-030 场景基线，追加 CR-020 QMT gateway 登录与只读查询场景 | `## 修订记录` | pending |
| `process/REQUIREMENTS.md` | 原文档更新 | 保留既有离线合同与 later-gated QMT 基线，追加 CR-020 运行授权、凭据、只读查询需求 | `## 修订记录` | pending |
| `process/HLD.md` | 原文档更新 | 保留 CR-019 离线 gateway 合同，追加 CR-020 Windows gateway runtime、登录、REST transport 和安全边界设计 | `## 修订记录` | approved by CP3 |
| `process/ARCHITECTURE-DECISION.md` | 原文档更新 | 保留既有 no-real-QMT / later-gated 决策，追加 CR-020 只读实机准入 ADR | `## 修订记录` | story-planning pending |
| `process/STORY-BACKLOG.md` | 原文档更新 | 保留旧 Story，追加 CR020-S01..S06 | `## 修订记录` | story-planning pending |
| `process/DEVELOPMENT-PLAN.yaml` | 原文档更新 | 保留旧 Wave，追加 CR-020 Wave / file owner / gate | 不适用或计划内修订记录 | story-planning pending |
| `docs/QMT-GATEWAY-INSTALL.md` | 原文档更新 | 保留 CR-019 离线安装边界，新增 CR-020 已授权运行章节；未通过 CP2 前不得改写为默认真实运行 | `## 修订记录` | pending |
| `.env.example` | 新增 | 不适用；只写占位变量，不写真实凭据 | 不适用 | pending |
| `trading/qmt_client.py` | 原文档更新 / 代码变更候选 | 保留现有 later-gated offline transport 合同，CP5 后才允许接入真实 REST transport | 不适用 | pending |
| `trading/qmt_gateway_config.py` / `trading/qmt_gateway_service.py` | 原文档更新 / 代码变更候选 | 保留 CR-019 no-service-start 合同，CP5 后按 CR-020 改为显式运行授权下可启动 | 不适用 | pending |
| `trading/qmt_auth.py` | 原文档更新 / 代码变更候选 | 保留 HMAC / pairing 合同，CP5 后接入真实 gateway scope | 不适用 | pending |

## 4. 旧基线映射

| 原基线对象 | 新增 / 修改对象 | 保留策略 | 映射说明 |
|---|---|---|---|
| CR-019 QMT C/S bridge 离线合同 | CR-020 Windows gateway runtime + server login + readonly query | 原文保留并作为前置安全基线 | CR-020 只能在显式门禁通过后放开服务启动、端口绑定和 QMT 只读调用。 |
| CR-019 `later_gated` QMT endpoints | CR-020 `query_positions` 首个只读接口 | 原文保留；CR-020 只解锁 `query_positions` 最小范围 | `query_account` / `query_orders` / `query_trades` 后置或另行授权。 |
| docs 中“不得启动真实服务 / 不得访问 QMT” | CR-020 已授权章节 | 历史区保留；新增章节标明仅 CR-020 范围生效 | 防止把后续 CR 授权误读为全局默认运行许可。 |
| CR-030 策略侧模拟盘入口 | CR-020 QMT 接口 ready 输入 | 原文保留 | CR-030 关闭不代表 QMT-ready；CR-020 只补接口和只读查询，不授权 simulation order。 |

## 5. 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论 | 处理动作 |
|------|----------|-----------|------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | `REQUIREMENTS.md`、CP2 Decision Brief | true | 新增 server login、`.env` 凭据、S 端 `uv run` Typer CLI、C 端 `uv run` Typer CLI 配对 / 验收、Python REST client 运行时调用、只读查询、禁止交易需求。 |
| 场景层 | 是否改变测试矩阵覆盖范围 | `USE-CASES.md`、CP2 discussion、后续 TEST-STRATEGY | true | 新增 Windows S 端 `uv run` Typer CLI、Linux C 端 `uv run` Typer CLI 配对 / 验收、Python REST client 调用、QMT 登录、`query_positions`、redaction、fail-closed 场景。 |
| 计划层 | 是否改变 Phase、Wave、任务依赖 | `STORY-BACKLOG.md`、`DEVELOPMENT-PLAN.yaml`、CP4/CP5 | true | 建议拆为 CR020-S01..S06，全部 LLD 批次 CP5 approved 后再实现。 |
| 安全层 | 是否引入新的高风险动作或权限要求 | `.env`、QMT 登录、HMAC、allowlist、日志、端口 | true | 高风险；必须 standard；真实凭据只在本地未跟踪 `.env`，输出只记录脱敏 `credential_ref`。 |
| 交付层 | 是否需要重新生成交付物或回归子集 | `docs/QMT-GATEWAY-INSTALL.md`、README / USER-MANUAL、验证脚本 | true | 更新运行手册、S 端 `uv run` Typer CLI、C 端 `uv run` Typer CLI 配对 / 验收、Python REST client 调用示例、回滚方案和 CP7 实机证据。 |

## 6. 回退决策

- 影响范围：全局运行边界变更，局部实现范围限定在 QMT gateway / qmt client / docs / tests。
- 回退到阶段：`requirement-clarification`。
- 需要重新确认的对象：CP2 决策清单、HLD / ADR、Story / LLD 批次、`.env` 凭据策略、Windows host / port / MiniQMT / XtQuant 版本、S 端 `uv run` Typer CLI 命令、C 端 `uv run` Typer CLI 配对 / 验收、Python REST client 运行时调用合同、首个查询接口。
- 回退触发条件：
  - 用户要求取消服务端登录或取消 `.env` 凭据策略。
  - Windows S 端无法满足 `uv run` Typer CLI 启停和回滚。
  - QMT / XtQuant API 无法提供 fail-closed 的只读 `query_positions`。
  - 发现日志、checkpoint、memory 或仓库文本泄露真实账号 / 密码 / token / session。

## 7. fast-lane 判定

| 条件 | 是否命中 | 说明 |
|---|---|---|
| 仅低风险轻量实现 / 文档 / 规则修改 | false | 不是文档小改，涉及真实 runtime 与外部接口。 |
| 修改架构、权限、安全边界或平台安装路径 | true | Windows gateway、端口、凭据、HMAC / allowlist 均命中。 |
| 修改外部接口契约、文件所有权或多 Story 依赖 | true | QMT / XtQuant、REST transport、query endpoint 和多 Story 依赖命中。 |
| 需要 HLD / LLD 才能解释影响 | true | 登录、会话、transport、安全、脱敏和验证都需要 LLD。 |
| 是否保持 fast-lane | false | 必须 standard。 |

## 8. 建议 Story 拆分

| Story | 标题 | 目标 | 主要文件 / 产物 | 门控 |
|---|---|---|---|---|
| CR020-S01 | Windows gateway runtime 与部署准入 | 让 S 端 `uv run` Typer CLI 安装 / 启动 / 停止 / health / 回滚可验证 | `trading/qmt_gateway_*`、`docs/QMT-GATEWAY-INSTALL.md` | CP5 后实现，CP6/CP7 验证 `uv run` Typer CLI 命令 |
| CR020-S02 | 服务端 QMT 登录 / 会话管理 | 读取本地 `.env`，完成 QMT 登录、session ready、fail-closed、日志脱敏 | gateway login/session 模块、`.env.example` | 凭据不入库；日志和 checkpoint 不含真实值 |
| CR020-S03 | C 侧 Python REST transport 与 Typer CLI | Linux C 端的实际业务调用从 offline transport 切换到受控 Python REST client；C 端 `uv run` Typer CLI 仅用于配对、诊断和 CP7 验收 | `trading/qmt_client.py`、`trading/qmt_client_cli.py`、transport tests、CLI pairing smoke tests | 默认 fail-closed；未授权 endpoint 阻断 |
| CR020-S04 | HMAC / pairing / allowlist / scope 实机准入 | 让 C 侧调用具备身份、来源和 scope 检查 | `trading/qmt_auth.py`、gateway auth middleware | HMAC PASS、allowlist PASS、wrong scope blocked |
| CR020-S05 | `query_positions` 只读查询接口 | 完成至少一次真实只读持仓查询，结果脱敏 | endpoint matrix、gateway endpoint、client method、tests | 不发单、不撤单、不账户写入 |
| CR020-S06 | 文档、运行手册与 CP7 实机验收 | 形成 S/C 分平台命令、回滚、日志、redaction 和不授权说明 | README / USER-MANUAL / docs / TEST-STRATEGY | CP7 实机证据和 CP8 人工确认 |

## 9. LLD 设计批次门禁

- 是否需要 LLD 设计批次：true
- batch_id：`CR020-LDD-BATCH-A-QMT-GATEWAY-READONLY`
- 批次范围来源：CR 影响分析 + CP2 决策清单
- 批次内 Story：
  - `CR020-S01-windows-gateway-runtime-admission`
  - `CR020-S02-server-qmt-login-session`
  - `CR020-S03-linux-client-rest-transport`
  - `CR020-S04-hmac-pairing-allowlist-scope`
  - `CR020-S05-query-positions-readonly`
  - `CR020-S06-docs-runbook-cp7-real-machine-validation`
- 批次人工确认稿：`checkpoints/CP5-CR020-QMT-GATEWAY-READONLY-LLD-BATCH.md`
- 开发启动条件：
  - [ ] 批次内全部 Story LLD 已输出
  - [ ] 批次内全部 Story CP5 自动预检已通过
  - [ ] 批次 CP5 人工确认结论为 `approved`
  - [ ] 批次内每个 Story 的 `dev_gate` 已满足
  - [ ] CP2 已确认 `.env` 凭据边界、S 端 `uv run` Typer CLI、C 端 `uv run` Typer CLI 配对 / 验收、Python REST client 运行时调用和不授权项
  - [ ] CP3 已确认 gateway / session / transport / auth / redaction 架构

## 10. 执行链路

| 顺序 | 责任角色 | 动作 | 输入 | 输出 | 门控 | 完成后下一步 |
|---|---|---|---|---|---|---|
| 1 | `meta-po` | 创建 CR-020，完成冲突预检，发起 CP2 | 用户确认、CR-019 follow-up 台账、STATE、CR-INDEX | 本 CR、CP2 自动预检、CP2 人工审查稿、门禁消息 | CP2 launch valid | 等待用户 `approve / 修改 / reject` |
| 2 | `meta-pm` | 根据 CP2 结论更新 USE-CASES / REQUIREMENTS | 本 CR、CP2 决策 | CR-020 场景与需求基线 | CP2 approved 后调度 | 交还 meta-po |
| 3 | `meta-se` | 完成 HLD / ADR / Story Plan / CP4 | CR-020 需求、现有 QMT 合同 | HLD / ADR / STORY-BACKLOG / DEVELOPMENT-PLAN / CP3 / CP4 | CP3 approved，CP4 PASS | 进入全量 LLD 批次 |
| 4 | `meta-dev` | 完成 CR020-S01..S06 全量 LLD 与实现 | CP5 approved LLD 批次 | 代码、脚本、文档、CP6 | CP5 approved；CP6 PASS | 交给验证 |
| 5 | `meta-qa` | 完成 TEST-STRATEGY 与 CP7 实机 / 安全验证 | CP6、Windows S 端、Linux C 端 `uv run` Typer CLI 配对 / 验收、Python REST client 调用、脱敏日志 | TEST-STRATEGY、CP7 PASS / FAIL | CP7 PASS | 交回 meta-po |
| 6 | `meta-doc` | 刷新用户文档和运行手册 | CP7 结果、实现产物 | README / USER-MANUAL / docs | 文档自检 | 交回 meta-po |
| 7 | `meta-po` | 发起 CP8 终验并关闭或回退 | 下游结果、检查点 | CP8 自动预检、人工审查稿、CR closed 或回退 | CP8 approved | 更新 STATE / CR-INDEX / follow-up 台账 |

## 11. 自动终验授权

- 是否启用：false
- 授权范围：不适用
- 适用检查点：CP8
- 自动通过条件：
  - [ ] 自动预检结论为 `PASS`
  - [ ] 无 `BLOCKING`
  - [ ] 无 `REQUIRED`
  - [ ] 授权动作明确包含关闭 CR 和 / 或推进 `delivered`
- 授权原文：无
- 授权时间：无
- 回填要求：不适用

本 CR 没有自动终验授权。即使 CP6 / CP7 全部通过，仍必须等待 CP8 人工确认后才能关闭。

## 12. 不授权项

本 CR 创建和 CP2 发起不授权以下动作：

| 不授权项 | 说明 |
|---|---|
| 发单 / 撤单 / 改单 | CR-020 只允许只读查询接口设计和验证，不允许任何交易动作。 |
| 账户写入 / broker lake 写入 | 不允许修改账户、不允许写 broker lake。 |
| simulation / live / live-readonly / small-live / scale-up | 这些仍由 CR-021..CR-024 单独授权。 |
| provider fetch / lake write / publish | 不允许真实补数、写 lake、发布 catalog 或 current pointer。 |
| 凭据泄露 | 账号、密码、token、session、交易密码、私钥不得进入 Git、对话、日志、检查点、memory。 |
| 扩大接口白名单 | CP2 推荐只解锁 `query_positions`；其他接口后置。 |

## 13. 后续事项台账

- 是否存在后续事项：true
- 台账路径：`process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md`
- CR 索引路径：`process/changes/CR-INDEX.yaml`
- 一致性检查：`uv run --python 3.11 python scripts/check_cr_tracking_consistency.py --project-root .`
- 状态取值：`candidate` / `active` / `blocked` / `spike_candidate` / `converted-to-spike` / `closed` / `cancelled` / `superseded`

| 候选编号 | 标题 | 状态 | 类型 | 优先级 | 正式 CR 路径 | 相关 active CR / blocked_by / superseded_by | 当前门控 | 阻塞原因 | 下一步 |
|---|---|---|---|---:|---|---|---|---|---|
| CR-020 | QMT Windows Gateway 服务端登录与只读查询接口准入 | active | CR | 1 | `process/changes/CR-020-QMT-WINDOWS-GATEWAY-SERVER-LOGIN-READONLY-QUERY-ADMISSION-2026-06-04.md` | active_change=`CR-020` | manual Windows/QMT readonly validation evidence | CP5 approved、S01..S06 代码与文档、六份 CP6、CP7 fixture/static 均已完成；真实 Windows/QMT 只读实机验证尚未执行 | 用户按手册执行 Windows S 端 `server-diagnostics` / `serve` 和 Linux C 端 `client-diagnostics` / `query-positions`，提交脱敏 evidence 后再判断 CP8 / 关闭 |
| CR-021 | QMT simulation 账号接入准入 | candidate | CR | 2 | N/A | blocked_by=CR-020 not closed | not-started | CR-020 未关闭 | CR-020 closed 后单独启动 |
| CR-022 | Live-readonly 准入 | candidate | CR | 3 | N/A | blocked_by=CR-021 not closed | not-started | CR-021 未关闭 | CR-021 closed 后单独启动 |
| CR-023 | Small-live 准入 | candidate | CR | 4 | N/A | blocked_by=CR-022 not closed | not-started | CR-022 未关闭 | CR-022 closed 后单独启动 |
| CR-024 | Scale-up 准入 | candidate | CR | 5 | N/A | blocked_by=CR-023 not closed | not-started | CR-023 未关闭 | CR-023 closed 后单独启动 |

## 14. 处理结论

- 审批结论：`cp5-lld-batch-ready-for-manual-review`
- [ ] 自动批准（低风险）
- [ ] 待人工确认（中风险）
- [x] 待人工审批（高风险）

CP3 HLD 人工确认已 approved。下一步是 Story Planning / CP4：调度 meta-se 产出正式 ADR 增量、Story Backlog 增量、Development Plan 增量、CR020-S01..S06 Story 卡片和 CP4 自动预检。该 approve 不表示授权实现、启动 gateway、连接 QMT、读取真实 `.env`、交易、写账户、simulation / live、provider / lake / publish 或凭据泄露。

## 15. 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| Follow-up tracking | `process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md` | CR-020 候选来源。 |
| CR index | `process/changes/CR-INDEX.yaml` | CR-020 active formal CR 索引。 |
| STATE | `process/STATE.md` | active_change / human_gate_decisions / cr_tracking 状态。 |
| CP2 auto check | `process/checks/CP2-CR020-REQUIREMENTS-BASELINE.md` | CP2 自动预检。 |
| CP2 manual review | `checkpoints/CP2-CR020-REQUIREMENTS-BASELINE.md` | CP2 人工确认稿。 |
| CP3 HLD handoff | `process/handoffs/META-SE-CR020-HLD-2026-06-04.md` | meta-se HLD 真实调度、完成和关闭证据。 |
| CP3 auto check | `process/checks/CP3-CR020-HLD-CONSISTENCY.md` | CP3 自动预检，结论 PASS。 |
| CP3 manual review | `checkpoints/CP3-CR020-HLD-REVIEW.md` | CP3 HLD 人工确认稿。 |
| Existing QMT client | `trading/qmt_client.py` | 当前 offline / later-gated client 合同。 |
| Existing endpoint matrix | `trading/qmt_endpoint_matrix.py` | 当前 QMT endpoint scope 和 later-gated 定义。 |
| Existing gateway contract | `trading/qmt_gateway_config.py` / `trading/qmt_gateway_service.py` | 当前 gateway lifecycle 合同。 |
| Existing auth contract | `trading/qmt_auth.py` | 当前 HMAC / pairing 合同。 |
| Gateway docs | `docs/QMT-GATEWAY-INSTALL.md` | 后续需更新 S/C 分平台命令和 CR-020 运行边界。 |
