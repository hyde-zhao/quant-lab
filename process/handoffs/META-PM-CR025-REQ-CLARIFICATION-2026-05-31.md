---
handoff_id: META-PM-CR025-REQ-CLARIFICATION-2026-05-31
change_id: CR-025
phase: requirement-clarification
agent_role: meta-pm
status: completed
created_at: "2026-05-31T22:08:28+08:00"
cp2_manual_status: not_launched
cp2_approval_status: not_approved
---

# META-PM CR-025 Requirement Clarification Handoff

## Dispatch

| 字段 | 值 |
|---|---|
| mode | spawn_agent |
| agent_role | meta-pm |
| agent_id | 019e7e51-2769-70e1-a681-c404519ca304 |
| thread_id | 019e7e51-2769-70e1-a681-c404519ca304 |
| tool_name | multi_agent_v1.spawn_agent |
| spawned_at | 2026-05-31T21:43:48+08:00 |
| completed_at | 2026-05-31T22:08:28+08:00 |
| handoff_path | `process/handoffs/META-PM-CR025-REQ-CLARIFICATION-2026-05-31.md` |

## 读取输入

| 输入 | 处理结果 |
|---|---|
| `AGENTS.md` | 已读取；遵守中文输出、uv 优先、过程文件分层、CR 增量追溯、CP 门控和安全边界。 |
| `process/STATE.md` | 已读取；确认当前 active_change 为 `CR-025`，当前阶段为 requirement-clarification，CR-026 和真实 QMT 路线仍为候选 / 后置。 |
| `process/changes/CR-025-BACKTRADER-OPTIONAL-EXECUTION-BACKEND-HARDENING-2026-05-31.md` | 已读取；确认文档处理决策、旧基线映射、验收标准、禁止事项和 CP5 前不得实现 / 改依赖。 |
| `process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md` | 已读取；确认 `backtrader_w6` 已转 active，目标为 optional execution backend hardening，不授权真实 broker / QMT / provider / lake / publish。 |
| `process/USE-CASES.md` | 已读取并增量更新；保留 UC-01 至 UC-18，新增 UC-19。 |
| `process/REQUIREMENTS.md` | 已读取并增量更新；保留 REQ-001 至 REQ-160，新增 REQ-161 至 REQ-168。 |
| `process/CLARIFICATION-LOG.md` | 已读取并追加 CR-025 阶段零调研、Scenario Gray Areas desk review、Q-045 至 Q-049、场景与需求摘要和 CP2 Decision Brief 输入。 |

## 修改 / 新增文件

| 路径 | 类型 | 说明 |
|---|---|---|
| `process/USE-CASES.md` | 修改 | 升级到 v1.11 draft；新增 P-08、SM-33 至 SM-37、CR-025 Out of Scope / 边界说明、UC-19、Scenario Gray Areas、Deferred Ideas、TS-025-01 至 TS-025-07、覆盖自检和治理变更记录。 |
| `process/REQUIREMENTS.md` | 修改 | 升级到 v1.12 draft；`ready_for_design=false`；新增 CR-025 上下文、路径归属、Backtrader optional backend 契约、REQ-161 至 REQ-168、RA-057 至 RA-062、M19、A-054 至 A-058 和 Out of Scope。 |
| `process/CLARIFICATION-LOG.md` | 修改 | 追加 CR-025 调研发现、灰区 desk review、默认决策 / 开放项、场景与需求增量摘要和 CP2 Decision Brief 输入。 |
| `process/checks/CP1-CR025-USE-CASE-COMPLETENESS.md` | 新增 | CP1 用户场景完备门自动检查，结论 PASS。 |
| `process/handoffs/META-PM-CR025-REQ-CLARIFICATION-2026-05-31.md` | 新增 | 本交接摘要。 |

## 需求 / 场景摘要

| 类别 | 内容 |
|---|---|
| 用户真实意图 | 推进研究路线中的 Backtrader optional execution backend hardening，使后续 HLD/LLD 能评审可选后端边界、依赖隔离、clean feed、执行语义差异和安全禁区。 |
| 核心范围 | Backtrader 仅作为显式选择的 optional research backend；默认 lightweight engine 不变；未安装 Backtrader 时返回 structured unavailable；只消费本地 clean feed；输出 lightweight vs Backtrader semantic diff report。 |
| 明确排除 | 不替代 lightweight 主路径；不新增依赖；不实现代码；不运行 Backtrader；不接真实 broker / live store；不触发 QMT / MiniQMT / XtQuant；不 provider fetch、不写 lake / broker lake、不 publish、不读取凭据。 |
| 旧基线保留 | UC-01 至 UC-18 和 REQ-001 至 REQ-160 均保留；CR-025 只追加 UC-19 与 REQ-161 至 REQ-168。 |
| 文档状态 | `USE-CASES.md` 与 `REQUIREMENTS.md` 已切回 `draft`，表示 CR-025 增量待 CP2 人工确认；未标记 approved。 |

## Scenario Gray Areas

| 灰区 ID | 处理结果 | 落点 |
|---|---|---|
| SGA-025-01 | Backtrader 采用 optional research backend，不替代 lightweight 主路径。 | UC-19；REQ-161；RA-057 |
| SGA-025-02 | 依赖采用隔离与 lazy import，CP5 前不改 `pyproject.toml` / `uv.lock`。 | UC-19；REQ-162；RA-058 |
| SGA-025-03 | clean feed gate 与 semantic diff report 作为核心验收输入。 | UC-19；REQ-163；REQ-164；RA-059；RA-060 |
| SGA-025-04 | 真实 broker / QMT / provider / lake / publish / credential 全部不授权。 | REQ-165；REQ-168；RA-061；Out of Scope |

## 开放项

| ID | 状态 | 问题 | 推荐处理 | 是否阻断 CP2 |
|---|---|---|---|---|
| Q-045 | RESOLVED_FROM_CR | Backtrader 是否替代 lightweight engine？ | 不替代，默认 lightweight，Backtrader 显式选择。 | 否 |
| Q-046 | RESOLVED_FROM_CR | Backtrader 依赖是否现在引入？ | CP5 前不引入；后续 optional extra / lazy import。 | 否 |
| Q-047 | RESOLVED_FROM_DESK_REVIEW | Backtrader 输入如何约束？ | 只消费本地 clean feed，不合规 structured blocked。 | 否 |
| Q-048 | REQUIRED_FOR_CP3 | semantic diff report 的最终 schema 和阈值如何冻结？ | CP3/HLD 冻结字段、阈值和对照口径。 | 否 |
| Q-049 | RESOLVED_FROM_CR | 是否授权真实 broker / QMT / provider / lake / publish / credential？ | 不授权，计数必须为 0。 | 否 |

## 检查结论

| 检查点 | 结论 | 路径 |
|---|---|---|
| CP1 用户场景完备门 | PASS | `process/checks/CP1-CR025-USE-CASE-COMPLETENESS.md` |

## 安全声明

- 未实现任何代码。
- 未新增依赖，未修改 `pyproject.toml` 或 `uv.lock`。
- 未运行 Backtrader，未启动任何服务。
- 未调用真实 broker、QMT / MiniQMT / XtQuant、simulation、live、account query、cancel 或 order submit。
- 未读取 `.env`、token、账户、session、cookie、交易密码或任何凭据。
- 未执行真实 provider fetch。
- 未写真实 `data/`、`reports/`、`delivery/`、lake、broker lake 或 catalog current pointer。
- 未发起 CP2 人工门禁，未把 CP2 人工确认标为 approved。

## 建议给 Meta-PO

1. 基于 `process/checks/CP1-CR025-USE-CASE-COMPLETENESS.md`、`process/USE-CASES.md` v1.11 和 `process/REQUIREMENTS.md` v1.12 生成 CR-025 CP2 Decision Brief。
2. CP2 人工确认需要明确：回复 `approve` 只表示接受 CR-025 需求 / 场景推荐范围，不授权实现、依赖变更、真实 broker、QMT、provider、lake、publish 或凭据读取。
3. 若 CP2 通过，再委托 meta-se 进入 CR-025 CP3，冻结 optional extra / lazy import 策略、Backtrader adapter 边界、clean feed schema、semantic diff report 和最小回归范围。
4. CP5 前仍不得实现 Backtrader backend、修改依赖、运行 Backtrader 或触发任何真实数据 / 真实交易 / publish 行为。
