---
checkpoint_id: "CP2"
checkpoint_name: "CR-020 Requirements Baseline"
type: "auto_precheck"
status: "PASS"
owner: "meta-po"
created_at: "2026-06-04T22:28:31+08:00"
checked_at: "2026-06-04T22:28:31+08:00"
target:
  phase: "requirement-clarification"
  story_id: ""
  artifacts:
    - "process/changes/CR-020-QMT-WINDOWS-GATEWAY-SERVER-LOGIN-READONLY-QUERY-ADMISSION-2026-06-04.md"
    - "process/discussions/CP2-CR020-SCENARIO-DISCUSSION-LOG.md"
    - "process/checks/CP2-CR020-DISCUSSION-CHECKPOINT.json"
    - "checkpoints/CP2-CR020-REQUIREMENTS-BASELINE.md"
manual_checkpoint: "checkpoints/CP2-CR020-REQUIREMENTS-BASELINE.md"
---

# CP2 CR-020 Requirements Baseline 检查结果

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| CR-019 follow-up 台账可读 | PASS | `process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md` | CR-020 原候选项存在。 |
| CR 跟踪索引可读 | PASS | `process/changes/CR-INDEX.yaml` | 当前启动前为 no-active-formal-cr；CR-025 / CR-030 已 closed。 |
| STATE 可读且无 active_change | PASS | `process/STATE.md` | 启动前 `active_change: ""`，无 active formal CR。 |
| 用户明确启动 CR-020 | PASS | 当前对话 | 用户同意方案，并要求 meta-po 组织推行。 |
| 用户明确 S/C 调用边界 | PASS | 当前对话 | S 端 Windows 使用 `uv run` Typer CLI；C 端配对 / 诊断 / 验收使用 Linux `uv run` Typer CLI，实际业务调用由 Python REST client 直接调用 gateway REST API。 |
| 用户明确凭据形态 | PASS | 当前对话 | 登录账号和密码以 `.env` 形式存放到项目中。 |

## Checklist

| # | 检查项 | 状态 | 证据 | 处理意见 |
|---|---|---|---|---|
| 1 | CR-020 已从候选转正式 CR | PASS | `process/changes/CR-020-QMT-WINDOWS-GATEWAY-SERVER-LOGIN-READONLY-QUERY-ADMISSION-2026-06-04.md` | status=`active-cp2-intake`。 |
| 2 | 范围升级已记录 | PASS | CR 文件 §1、§5、§8 | 从 gateway health 升级为 server login + readonly query。 |
| 3 | Scenario Gray Areas 已处理 | PASS | `process/discussions/CP2-CR020-SCENARIO-DISCUSSION-LOG.md`、`process/checks/CP2-CR020-DISCUSSION-CHECKPOINT.json` | 直接来自用户确认；未留 blocking open item。 |
| 4 | 待人工决策项已形成 | PASS | `checkpoints/CP2-CR020-REQUIREMENTS-BASELINE.md` | 7 项 DQ 等待用户确认。 |
| 5 | `.env` 凭据策略未泄露真实值 | PASS | `.gitignore`、`.env.example` 计划、CP2 Decision Brief | 真实值只允许本地未跟踪 `.env`；入库只写占位变量。 |
| 6 | S/C 调用边界可验证 | PASS | CP2 Decision Brief DQ-CP2-CR020-04 | S 端 Windows 使用 `uv run` Typer CLI；C 端配对 / 诊断 / 验收使用 Linux `uv run` Typer CLI，实际业务调用由 Python REST client 调用 REST API。 |
| 7 | 首个查询接口候选明确 | PASS | CP2 Decision Brief DQ-CP2-CR020-05 | 推荐 `query_positions`。 |
| 8 | 不授权项已列出 | PASS | CR 文件 §12、CP2 人工审查稿 | 不授权交易、撤单、账户写入、simulation / live、provider / lake / publish、凭据泄露。 |
| 9 | workflow mode 判定 | PASS | CR 文件 §7 | 命中 high-risk runtime / external interface，必须 standard。 |
| 10 | 下游实现未提前启动 | PASS | 当前文件变更 | 本轮仅创建 CR、CP2 检查点、状态索引和 `.env.example`。 |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| CP2 自动预检结论可用于人工门禁 | PASS | 本文件 `status: "PASS"` | 无自动阻断项。 |
| 人工审查稿路径已准备 | PASS | `checkpoints/CP2-CR020-REQUIREMENTS-BASELINE.md` | 待用户回复 `approve / 修改: <具体修改点> / reject`。 |
| 待人工决策清单完整 | PASS | 7 项 DQ | 范围、运行授权、安全、实现、接口、风险、依赖策略均覆盖。 |
| 未扩大运行授权 | PASS | 不授权项 | CP2 approve 仅表示接受需求基线，不授权交易或凭据泄露。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| 正式 CR | `process/changes/CR-020-QMT-WINDOWS-GATEWAY-SERVER-LOGIN-READONLY-QUERY-ADMISSION-2026-06-04.md` | PASS | 已创建。 |
| CP2 discussion log | `process/discussions/CP2-CR020-SCENARIO-DISCUSSION-LOG.md` | PASS | 已创建。 |
| CP2 discussion checkpoint | `process/checks/CP2-CR020-DISCUSSION-CHECKPOINT.json` | PASS | 已创建。 |
| CP2 人工审查稿 | `checkpoints/CP2-CR020-REQUIREMENTS-BASELINE.md` | PASS | 已 approved，并按用户后续确认修订 DQ-CP2-CR020-04；当前 S / C 两端 CLI 均采用 Typer。 |
| CP2 门禁消息草稿 | `process/checks/CP2-CR020-HUMAN-GATE-LAUNCH-MESSAGE.md` | PASS | 已创建并按 S / C 两端 Typer CLI 口径修订。 |
| `.env` 样例 | `.env.example` | PASS | 仅占位变量；真实值不入库。 |

## 结论

- 结论：`PASS`
- 阻断项：无
- 豁免项：无
- 下一步：CP2 已 approved，且 DQ-CP2-CR020-04 已按用户后续确认修订为 S 端 Windows `uv run` Typer CLI、C 端 Linux `uv run` Typer CLI；进入 CP3 HLD 前仍不表示授权交易、账户写入、simulation / live、provider / lake / publish 或凭据泄露。
