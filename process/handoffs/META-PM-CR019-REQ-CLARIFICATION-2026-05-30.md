---
handoff_id: META-PM-CR019-REQ-CLARIFICATION-2026-05-30
change_id: CR-019
phase: requirement-clarification
agent_role: meta-pm
status: completed
created_at: "2026-05-30T15:03:02+08:00"
---

# META-PM CR-019 Requirement Clarification Handoff

## Dispatch

| 字段 | 值 |
|---|---|
| mode | spawn_agent |
| agent_role | meta-pm |
| agent_id | 019e77ac-22e1-7d22-b75d-0a18cfcb9744 |
| thread_id | 019e77ac-22e1-7d22-b75d-0a18cfcb9744 |
| tool_name | multi_agent_v1.spawn_agent |
| spawned_at | 2026-05-30T15:08:00+08:00（来自 `process/STATE.md`；父线程可回填校正） |
| completed_at | 2026-05-30T15:17:38+08:00 |
| handoff_path | `process/handoffs/META-PM-CR019-REQ-CLARIFICATION-2026-05-30.md` |

## 读取输入

| 输入 | 处理结果 |
|---|---|
| `AGENTS.md` | 已读取；遵守中文输出、Meta Flow 目录约定、CR 增量追溯、CP1/CP2 检查点结构和安全边界 |
| `process/changes/CR-019-STAGE6-MULTIFACTOR-SIMULATION-ARCHITECTURE-2026-05-30.md` | 已读取；确认 D1-D7、文档处理决策、旧基线映射、FastAPI bridge 主选和本轮禁止真实操作范围 |
| `process/USE-CASES.md` | 已读取并增量更新；保留 UC-01 至 UC-14，新增 UC-15 至 UC-18 |
| `process/REQUIREMENTS.md` | 已读取并增量更新；保留 REQ-001 至 REQ-137，新增 REQ-138 至 REQ-158 |
| `process/CLARIFICATION-LOG.md` | 已读取并追加 CR-019 调研、D1-D7、Q-039 至 Q-043 和 CP2 Decision Brief 输入 |
| `process/STATE.md` | 已读取；确认当前 active_change 为 CR-019，当前阶段为 requirement-clarification |
| `docs/QMT-SIMULATION-LIVE-RUNBOOK.md` | 已读取；继承 stage gate、per-run authorization、runbook、对账、kill switch 和 no-real-op 边界 |
| `docs/QMT-INCIDENT-PLAYBOOK.md` | 已读取；继承 incident、recovery、blocked execution claims 和安全处理边界 |
| `docs/ROADMAP.md` | 已读取；确认 Backtrader optional backend、Qlib isolated runner、minute / Level2 后置定位 |
| `阶段六学习目标和计划.md` | 已读取；确认阶段六目标扩展和旧策略 admission 当前 blocked |
| `MULTIFACTOR-SIMULATION-ADMISSION-PLAN.md` | 已读取；确认多因子 admission package、5 日 dry-run 和 per-run authorization 前置 |
| `DATA-GAP-SOURCE-ACQUISITION-PLAN.md` | 已读取；确认行业、市值、财务、可交易性、benchmark、流动性、minute / Level2 等数据缺口和优先级 |
| `LOCAL-BACKTEST-IMPROVEMENT-PLAN.md` | 已读取；确认 W1-W8 改进路径、Backtrader W6、Qlib W7、admission W8 |
| `迅投QMT极速策略交易系统说明文档.md` | 已读取相关能力背景；仅作为能力说明，不推断当前真实账户或权限 |

## 修改 / 新增文件

| 路径 | 类型 | 说明 |
|---|---|---|
| `process/USE-CASES.md` | 修改 | 升级到 v1.9；追加 CR-019 修订记录、P-07、SM-27 至 SM-32、Out of Scope、边界说明、UC-15 至 UC-18、TS-019-01 至 TS-019-09、覆盖自检和治理变更记录 |
| `process/REQUIREMENTS.md` | 修改 | 升级到 v1.10；追加 CR-019 修订记录、需求上下文、路径归属、FastAPI Bridge 候选契约、REQ-138 至 REQ-158、RA-048 至 RA-055、M16 至 M18、A-041 至 A-050 和 Out of Scope |
| `process/CLARIFICATION-LOG.md` | 修改 | 追加 CR-019 调研发现、D1-D7 已确认决策、Q-039 至 Q-043、场景与需求增量摘要和 CP2 Decision Brief 输入 |
| `process/discussions/CP2-CR019-SCENARIO-DISCUSSION-LOG.md` | 新增 | 记录 CR-019 Scenario Gray Areas、推荐方案、备选、D1-D7、Deferred Ideas 和 N/A 原因 |
| `process/checks/CP2-CR019-DISCUSSION-CHECKPOINT.json` | 新增 | 记录 CP2 discussion 恢复点、已处理灰区、开放项和安全范围 |
| `process/checks/CP1-CR019-USE-CASE-COMPLETENESS.md` | 新增 | CP1 用户场景完备门自动检查，结论 PASS |
| `process/checks/CP2-CR019-REQUIREMENTS-BASELINE.md` | 新增 | CP2 需求基线自动预检，结论 PASS |
| `process/handoffs/META-PM-CR019-REQ-CLARIFICATION-2026-05-30.md` | 新增 | 本交接摘要 |

## 关键决策

| ID | 决策 | 状态 | 落点 |
|---|---|---|---|
| D1 | Backtrader 后置 optional execution backend | RESOLVED | UC-18；REQ-139；REQ-155 |
| D2 | Qlib 后置 isolated runner | RESOLVED | UC-18；REQ-140；REQ-156 |
| D3 | 分钟数据不作为 P0，只做后置 Spike | RESOLVED | UC-18；REQ-141；REQ-157 |
| D4 | QMT xtdata 不进入 WSL 主路径；最终 simulation 前采用 Windows QMT bridge | RESOLVED | UC-16；REQ-142；REQ-149 |
| D5 | 暂不申请 QMT Level2 | RESOLVED | UC-18；REQ-143；REQ-158 |
| D6 | shadow + 连续 5 个真实交易日 dry-run 后再申请 QMT simulation | RESOLVED | UC-15；UC-17；REQ-144；REQ-154 |
| D7 | WSL / Windows QMT 第一版桥接采用 FastAPI 本地服务，signed file drop fallback | RESOLVED | UC-16；UC-17；REQ-145 至 REQ-150 |

## 开放项

| ID | 状态 | 问题 | 推荐处理 | 是否阻断 CP2 |
|---|---|---|---|---|
| Q-039 | REQUIRED_FOR_CP3 | FastAPI bind/firewall/endpoint schema/auth/log redaction | CP3 HLD/ADR 冻结本机或受控绑定、短期 token/HMAC、Windows 防火墙和日志脱敏 | 否 |
| Q-040 | REQUIRED_FOR_CP3 | 阶段六 admission benchmark / tracking / freeze fields | CP3 冻结 HS300/ZZ500/ZZ1000/中证全指评估口径、准入阈值和策略冻结字段 | 否 |
| Q-041 | REQUIRED_FOR_CP3 | FastAPI simulation later gate 的 per-run authorization schema | 继承 runbook 字段并由 HLD 冻结状态枚举、过期策略和缺字段行为 | 否 |
| Q-042 | REQUIRED_FOR_CP3 | signed file drop fallback 切换条件和 schema | CP3 冻结 FastAPI 不可达 / 鉴权失败 / heartbeat fail 时的 dry-run 或 blocked fallback | 否 |
| Q-043 | REQUIRED_FOR_CP3 | Backtrader/Qlib/minute/Level2 后置 Story 顺序和 Spike 退出标准 | CP3 / Story Plan 作为范围控制与 Deferred Ideas 消费 | 否 |

## 检查结论

| 检查点 | 结论 | 路径 |
|---|---|---|
| CP1 用户场景完备门 | PASS | `process/checks/CP1-CR019-USE-CASE-COMPLETENESS.md` |
| CP2 需求基线自动预检 | PASS | `process/checks/CP2-CR019-REQUIREMENTS-BASELINE.md` |

## 验证命令 / 静态检查

| 命令 | 结果 | 说明 |
|---|---|---|
| `uv run --python 3.11 python -m json.tool process/checks/CP2-CR019-DISCUSSION-CHECKPOINT.json` | PASS | JSON checkpoint 可解析 |
| `rg -n "UC-15|UC-16|UC-17|UC-18|TS-019|SM-27|P-07" process/USE-CASES.md` | PASS | CR-019 场景、指标、测试矩阵已落入场景文档 |
| `rg -n "REQ-138|REQ-145|REQ-146|REQ-147|REQ-148|REQ-152|REQ-158|RA-048|A-041|M16" process/REQUIREMENTS.md` | PASS | CR-019 新需求、风险、假设和里程碑已落入需求文档 |
| `git status --short -- process/USE-CASES.md process/REQUIREMENTS.md process/CLARIFICATION-LOG.md process/discussions/CP2-CR019-SCENARIO-DISCUSSION-LOG.md process/checks/CP2-CR019-DISCUSSION-CHECKPOINT.json process/checks/CP1-CR019-USE-CASE-COMPLETENESS.md process/checks/CP2-CR019-REQUIREMENTS-BASELINE.md pyproject.toml uv.lock` | PASS | 仅需求 / 场景 / 日志 / 检查 / discussion 文件变化；`pyproject.toml` 与 `uv.lock` 未变更 |

## 安全声明

- 未实现任何代码。
- 未新增依赖，未修改 `pyproject.toml` 或 `uv.lock`。
- 未启动 FastAPI 或任何本地服务。
- 未调用真实 QMT / MiniQMT / XtQuant。
- 未读取 `.env`、token、账户、session、cookie、交易密码或任何凭据。
- 未执行真实 provider fetch。
- 未写真实 `data/`、`reports/`、`delivery/`。
- 未写 broker lake、未发单、未撤单、未做账户查询或账户写操作。
- 迅投 QMT 系统说明文档仅作为能力背景，不作为当前项目真实权限证明。

## 建议给 Meta-PO

1. 基于 `process/checks/CP1-CR019-USE-CASE-COMPLETENESS.md` 与 `process/checks/CP2-CR019-REQUIREMENTS-BASELINE.md` 发起 CR-019 CP2 人工确认。
2. CP2 人工确认建议只暴露三个回复：`approve`、`修改: <具体修改点>`、`reject`。
3. 若用户 `approve`，可进入 CR-019 CP3，由 meta-se 基于 UC-15 至 UC-18、REQ-138 至 REQ-158、Q-039 至 Q-043 输出 HLD / ADR / Story Plan。
4. CP3 前仍不得实现 FastAPI、修改依赖、调用真实 QMT、读取凭据、真实 provider fetch 或写真实 data/reports/delivery。
