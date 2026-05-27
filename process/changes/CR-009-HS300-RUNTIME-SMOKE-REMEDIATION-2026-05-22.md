---
cr_id: "CR-009"
status: "closed"
impact_level: "medium"
rollback_to: "story-execution"
approval_result: "approved"
created_at: "2026-05-22T07:08:25+08:00"
created_by: "meta-po"
approved_by: "user"
approved_at: "2026-05-22T07:08:25+08:00"
approval_text: "你可以按照计划执行了"
source: "run-exec"
linked_issue: "ISSUE-001"
linked_change: "CR-007+CR-008"
source_run_exec: "process/checks/REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22.md"
batch_id: "CR009-BUGFIX-A"
implementation_allowed: true
implementation_scope: "offline-code-fix-and-regression; real-smoke-only-if-existing-env-permits"
current_dev_agent_name: "Ampere"
current_dev_agent_id: "019e4cce-b36a-7cb3-8519-e02fec3ceb35"
current_dev_handoff: "process/handoffs/META-DEV-CR009-RUNTIME-SMOKE-REMEDIATION-2026-05-22.md"
current_dev_started_at: "2026-05-22T07:11:25+08:00"
current_dev_completed_at: "2026-05-22T07:14:17+08:00"
cp6_status: "PASS"
cp6_checkpoint: "process/checks/CP6-CR009-RUNTIME-SMOKE-REMEDIATION-CODING-DONE.md"
cp6_completed_at: "2026-05-22T07:14:17+08:00"
current_verify_agent_name: "qa-shi"
current_verify_agent_id: "019e4cd4-02de-7353-9a08-96b6aa5e948f"
current_verify_handoff: "process/handoffs/META-QA-CR009-RUNTIME-SMOKE-REMEDIATION-VERIFY-2026-05-22.md"
current_verify_started_at: "2026-05-22T07:17:07+08:00"
current_verify_completed_at: "2026-05-22T07:19:51+08:00"
cp7_status: "PASS"
cp7_checkpoint: "process/checks/CP7-CR009-RUNTIME-SMOKE-REMEDIATION-VERIFICATION-DONE.md"
cp7_completed_at: "2026-05-22T07:19:51+08:00"
real_smoke_status: "PASS"
real_smoke_required_for_close: true
real_smoke_authorization_required_text: "必须由用户再次明确授权真实 Tushare 小窗口复验；未授权前不得使用 --env-file .env、--enable-real-source 或写真实 lake。"
real_smoke_authorized_by: "user"
real_smoke_authorized_at: "2026-05-22T07:53:31+08:00"
real_smoke_authorization_text: "授权真实复验"
real_smoke_handoff: "process/handoffs/META-QA-CR009-REAL-TUSHARE-RUNTIME-RESMOKE-2026-05-22.md"
real_smoke_check_result: "process/checks/REAL-TUSHARE-RUNTIME-RESMOKE-CR009-2026-05-22.md"
real_smoke_agent_name: "qa-kong"
real_smoke_agent_id: "019e4cf7-4f22-7030-974c-85f92218d0ad"
real_smoke_started_at: "2026-05-22T07:55:40+08:00"
real_smoke_completed_at: "2026-05-22T07:57:32+08:00"
real_smoke_blocker_issue: "issues/ISSUE-002.md"
real_smoke_blocker_summary: "validate/read/revalidate 已通过，但 replay 按约定命令因必填 --lake-root 退出 2。"
current_dev_handoff: "process/handoffs/META-DEV-CR009-REPLAY-LAKE-ROOT-CONTRACT-FIX-2026-05-22.md"
current_dev_agent_name: "dev-lv"
current_dev_agent_id: "019e4cfd-7c50-77a2-b933-2f0541ffff63"
current_dev_started_at: "2026-05-22T08:02:25+08:00"
current_dev_completed_at: "2026-05-22T08:05:23+08:00"
replay_fix_cp6_status: "PASS"
replay_fix_cp6_checkpoint: "process/checks/CP6-CR009-REPLAY-LAKE-ROOT-CONTRACT-FIX-CODING-DONE.md"
replay_fix_qa_handoff: "process/handoffs/META-QA-CR009-REPLAY-LAKE-ROOT-CONTRACT-FIX-VERIFY-2026-05-22.md"
replay_fix_qa_agent_name: "qa-hua"
replay_fix_qa_agent_id: "019e4d02-d57a-7bc1-a4d9-a54c21d3b3e7"
replay_fix_qa_started_at: "2026-05-22T08:08:16+08:00"
replay_fix_qa_completed_at: "2026-05-22T08:09:37+08:00"
replay_fix_cp7_status: "PASS"
replay_fix_cp7_checkpoint: "process/checks/CP7-CR009-REPLAY-LAKE-ROOT-CONTRACT-FIX-VERIFICATION-DONE.md"
real_replay_fix_check_result: "process/checks/REAL-TUSHARE-RUNTIME-RESMOKE-CR009-REPLAY-FIX-2026-05-22.md"
closed_at: "2026-05-22T08:12:50+08:00"
close_result: "PASS"
close_summary: "CR-009 duplicate_key/read/revalidate 真实小窗口复验通过；ISSUE-002 replay lake-root 合同修复后真实 replay 复验通过。"
---

# CR-009：hs300_index 真实烟测缺陷修复与 revalidate/replay CLI 补齐

## 变更描述

用户已授权按计划处理真实 Tushare 运行态烟测失败。烟测证据显示：`hs300-backfill` 与 `normalize` 成功，但 `validate` 因 `duplicate_key` 判定失败，`read` 被 `quality_failed` 阻断；同时 CLI 不支持正式 `revalidate` / `replay` 子命令，导致后续复验只能以近似方式执行。

本 CR 目标是最小化关闭运行态缺陷：

| 目标 | 范围 | 验收口径 |
|---|---|---|
| 修复 `hs300_index` 跨 run 重复键误判 | `validate --run-id` 只读取对应 run 的 canonical parquet | 两个不同 run、相同日期的离线 fixture 中，指定目标 run 后质量 PASS |
| 补齐 `revalidate` | 复用现有 validate 质量门，命令输出标识为 `revalidate` | `python -m market_data.cli --help` 包含子命令，定向测试 PASS |
| 补齐 `replay` | 对已成功 idempotency key 返回 `status=skipped`、`attempts=0`、`network_calls=0`、`writes=0` | 离线 manifest fixture 验证不触发网络、不新增 manifest/raw/canonical 文件 |
| 保持安全边界 | 不读取、不打印、不记录 `.env`、token、NAS 凭据或私有真实路径 | 测试与报告只使用 tmp_path / 脱敏路径 |

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `process/USE-CASES.md` | 不变 | 既有基线保留；本 CR 为运行态缺陷修复，不新增用户场景 | 不适用 | approved |
| `process/REQUIREMENTS.md` | 不变 | 既有基线保留；不新增 REQ，只修复已验证链路缺陷 | 不适用 | approved |
| `process/HLD.md` | 不变 | 既有设计保留；本 CR 不改变架构边界 | 不适用 | approved |
| `process/ARCHITECTURE-DECISION.md` | 不变 | 既有 ADR 保留；不新增平台或数据源决策 | 不适用 | approved |
| `process/STORY-BACKLOG.md` | 不变 | 既有 Story 保留；以 CR009 bugfix 记录，不新增 Story | 不适用 | approved |
| `process/DEVELOPMENT-PLAN.yaml` | 不变 | 既有计划保留；本 CR 作为 story-execution 后置缺陷修复 | 不适用 | approved |
| `README.md` / `docs/USER-MANUAL.md` | 不变 | 若真实复验最终 PASS，可后续单独决定是否刷新运行手册 | 不适用 | approved |

## 旧基线映射

| 原基线对象 | 新增 / 修改对象 | 保留策略 | 映射说明 |
|---|---|---|---|
| CR-007 真实 benchmark 能力 | CR-009 bugfix | 原文保留 | CR-009 只关闭 CR-007/CR-008 后置真实烟测暴露的实现缺陷。 |
| CR-008 研究数据层质量门 | CR-009 bugfix | 原文保留 | CR-009 不放宽质量门；只修正输入选择与复验命令能力。 |
| `REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22` | 新复验检查结果 | 原文保留 | 原 FAIL 报告保留为失败基线，修复后新增检查结果，不覆盖原文。 |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论（true/false） | 处理动作 |
|------|----------|-----------|--------------------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | `REQUIREMENTS.md` | false | 不修改需求基线。 |
| 场景层 | 是否改变测试矩阵覆盖范围 | 运行态 QA / CLI 回归 | true | 新增多 run `hs300_index`、`revalidate`、`replay` 离线回归；真实复验需用户环境授权。 |
| 计划层 | 是否改变 Phase、Wave、任务依赖 | `story-execution` 后置缺陷修复 | true | 作为 `CR009-BUGFIX-A` 串行执行：meta-dev 修复 -> meta-qa 验证。 |
| 安全层 | 是否引入新的高风险动作或权限要求 | Tushare / lake / `.env` 边界 | false | 默认只允许离线 fixture 与 tmp_path；不得读取或打印凭据。真实复验仅沿用用户已授权的小窗口命令且输出脱敏。 |
| 交付层 | 是否需要重新生成交付物或回归子集 | CP6/CP7 / QA 检查结果 | true | 新增 CP6、CP7 与复验报告；README/USER-MANUAL 暂不刷新。 |

## 回退决策

- 影响范围：局部。
- 回退到阶段：`story-execution`。
- 需要重新确认的对象：无新增 HLD/Story 人工确认；若修复扩大到数据模型、真实数据迁移或文档承诺，则升级为新的设计 CR。

## LLD 设计批次门禁

- 是否需要 LLD 设计批次：false。
- batch_id：`CR009-BUGFIX-A`。
- 批次范围来源：运行态 QA 失败基线 + 用户授权。
- 批次内 Story：不新增 Story；关联 `CR007-S02`、`CR007-S05`、`CR008-S03/S04` 的已确认质量/readiness 合同。
- 批次人工确认稿：不适用。
- 开发启动条件：
  - [x] 用户已授权执行缺陷修复。
  - [x] 失败基线已记录为 `process/checks/REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22.md`。
  - [x] 禁止读取/打印凭据与私有路径。

## 执行链路

| 顺序 | 责任角色 | 动作 | 输入 | 输出 | 门控 | 完成后下一步 |
|---|---|---|---|---|---|---|
| 1 | `meta-po` | 创建 ISSUE/CR 并分派 | 烟测 FAIL、用户授权 | `ISSUE-001`、本 CR、meta-dev handoff | CR 已登记 | 调度 meta-dev |
| 2 | `meta-dev` | 实施最小代码修复 | 本 CR、失败基线、CLI/validation/readers 代码 | 代码与测试变更、CP6 | 离线测试通过，不触发网络/真实 lake 写入 | 交回 meta-po |
| 3 | `meta-qa` | 执行回归验证 | 修复 diff、CP6、回归范围 | CP7 与 QA 检查结果 | 离线回归 PASS；真实复验若执行必须脱敏 | 交回 meta-po |
| 4 | `meta-po` | 收敛 CR 状态 | CP6/CP7/复验证据 | STATE / STORY-STATUS / CR 更新 | 无 BLOCKING/REQUIRED | 关闭或保留等待真实复验 |

## 自动终验授权

- 是否启用：false。
- 授权范围：不适用。
- 适用检查点：不适用。
- 自动通过条件：
  - [ ] 自动预检结论为 `PASS`
  - [ ] 无 `BLOCKING`
  - [ ] 无 `REQUIRED`
  - [ ] 授权动作明确包含关闭 CR 和 / 或推进 `delivered`
- 授权原文：
- 授权时间：
- 回填要求：不适用。

## 处理结论

- 审批结论：`approved`
- [x] 自动批准（运行态缺陷修复，用户已明确授权）
- [ ] 待人工确认（中风险）
- [ ] 待人工审批（高风险）

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| ISSUE | `ISSUE-001` | 真实烟测缺陷工单。 |
| RUN-EXEC | `process/checks/REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22.md` | FAIL 基线。 |
| Handoff | `process/handoffs/META-DEV-CR009-RUNTIME-SMOKE-REMEDIATION-2026-05-22.md` | meta-dev 实施交接。 |

## 状态更新：离线验证通过，等待真实复验授权

| 时间 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 2026-05-22T07:14:17+08:00 | CP6 PASS | `process/checks/CP6-CR009-RUNTIME-SMOKE-REMEDIATION-CODING-DONE.md` | meta-dev/Ampere 完成 CLI 修复与定向测试。 |
| 2026-05-22T07:19:51+08:00 | CP7 PASS | `process/checks/CP7-CR009-RUNTIME-SMOKE-REMEDIATION-VERIFICATION-DONE.md` | meta-qa/qa-shi 完成离线回归：CLI 定向 `9 passed`，关联回归 `35 passed`，compileall 通过。 |
| 2026-05-22T07:23:42+08:00 | pending real smoke authorization | 本 CR | 真实 Tushare 小窗口复验仍建议执行，但涉及 `.env`、Tushare 网络调用与外部 lake 写入；需用户再次明确授权后再调度。 |
| 2026-05-22T07:53:31+08:00 | real smoke running | `process/handoffs/META-QA-CR009-REAL-TUSHARE-RUNTIME-RESMOKE-2026-05-22.md` | 用户明确授权“授权真实复验”，已创建真实复验 handoff，等待 meta-qa 执行并写入新检查结果。 |
| 2026-05-22T07:55:40+08:00 | real smoke dispatched | `spawn_agent` / `019e4cf7-4f22-7030-974c-85f92218d0ad` | 已调度 meta-qa/qa-kong 执行真实小窗口复验。 |
| 2026-05-22T07:57:32+08:00 | real smoke FAIL | `process/checks/REAL-TUSHARE-RUNTIME-RESMOKE-CR009-2026-05-22.md` | validate/read/revalidate 均 PASS；replay 因 CLI 强制 `--lake-root` 导致指定命令退出 2，已登记 `ISSUE-002` 并路由 meta-dev 修复。 |
| 2026-05-22T08:02:25+08:00 | replay contract fix dispatched | `spawn_agent` / `019e4cfd-7c50-77a2-b933-2f0541ffff63` | 已调度 meta-dev/dev-lv 修复 `replay --lake-root` 环境变量 fallback 合同。 |
| 2026-05-22T08:05:23+08:00 | replay contract fix CP6 PASS | `process/checks/CP6-CR009-REPLAY-LAKE-ROOT-CONTRACT-FIX-CODING-DONE.md` | `replay --lake-root` 已可选化，补充 env fallback / 显式覆盖 / 缺 manifest 负向回归；离线验证 11 passed、15 passed、compileall 通过。 |
| 2026-05-22T08:08:16+08:00 | replay fix verification dispatched | `spawn_agent` / `019e4d02-d57a-7bc1-a4d9-a54c21d3b3e7` | 已调度 meta-qa/qa-hua 执行离线 CP7 与真实 replay 复验。 |
| 2026-05-22T08:09:37+08:00 | replay fix verification PASS | `process/checks/CP7-CR009-REPLAY-LAKE-ROOT-CONTRACT-FIX-VERIFICATION-DONE.md` / `process/checks/REAL-TUSHARE-RUNTIME-RESMOKE-CR009-REPLAY-FIX-2026-05-22.md` | 离线回归 PASS，真实 replay 未传 `--lake-root` 返回 `status=skipped`、`attempts=0`、`network_calls=0`、`writes=0`。 |
| 2026-05-22T08:12:50+08:00 | CR closed | 本 CR | `ISSUE-001` 与 `ISSUE-002` 均已 resolved，CR-009 关闭。 |
