---
handoff_id: "META-PO-CR015-CR016-CR017-CONTEXT-RESUME-2026-05-28"
from_agent: "meta-po"
to_agent: "meta-po"
created_at: "2026-05-28T05:42:52+08:00"
status: "ready-for-resume"
workflow_id: "local_backtest-cr015-cr016-cr017"
active_change: "CR-015, CR-016, CR-017"
current_phase: "solution-design"
pending_gate: "CP3"
pending_checklist_path: "checkpoints/CP3-CR015-CR016-CR017-HLD-REVIEW.md"
dispatch:
  required: false
  mode: "resume-context"
  platform: "codex"
  agent_role: "meta-po"
  agent_path: ""
  tool_name: ""
  agent_id: ""
  agent_name: ""
  thread_id: ""
  spawned_at: ""
  resumed_at: ""
  completed_at: ""
  evidence: "context handoff file for compaction/resume"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# CR-015 / CR-016 / CR-017 恢复交接

## 当前结论

当前项目推进不缺额外业务信息，唯一阻塞是 `CP3` 人工确认仍为 `pending`。用户需要审查：

- `checkpoints/CP3-CR015-CR016-CR017-HLD-REVIEW.md`

允许的回复只有：

- `approve`
- `修改: <具体修改点>`
- `reject`

在 `CP3` approve 前，不得进入 Story Plan、LLD、代码实现、真实 QMT 调用、真实发单、真实抓取、真实写湖、publish current pointer、读取凭据或引入依赖。

## 已完成事实

| 项 | 状态 | 证据 |
|---|---|---|
| CR-015 创建 | 完成 | `process/changes/CR-015-QMT-TRADING-FOUNDATION-2026-05-27.md` |
| CR-016 创建 | 完成 | `process/changes/CR-016-QMT-SIMULATION-LIVE-ACTIVATION-2026-05-27.md` |
| CR-017 创建 | 完成 | `process/changes/CR-017-ADJUSTMENT-POLICY-DUAL-VIEW-SUPPORT-2026-05-27.md` |
| CP2 intake 决策 | approved | `checkpoints/CP2-CR015-CR016-CR017-INTAKE-DECISION-BRIEF.md` |
| meta-pm 需求澄清 | completed | `process/handoffs/META-PM-CR015-CR016-CR017-REQ-CLARIFICATION-2026-05-27.md` |
| CP1 自动检查 | PASS | `process/checks/CP1-CR015-CR016-CR017-USE-CASE-COMPLETENESS.md` |
| CP2 自动检查 | PASS | `process/checks/CP2-CR015-CR016-CR017-REQUIREMENTS-BASELINE.md` |
| meta-se HLD / ADR | completed | `process/handoffs/META-SE-CR015-CR016-CR017-HLD-ADR-2026-05-27.md` |
| CP3 自动预检 | PASS | `process/checks/CP3-CR015-CR016-CR017-HLD-CONSISTENCY.md` |
| CP3 人工审查 | pending | `checkpoints/CP3-CR015-CR016-CR017-HLD-REVIEW.md` |

## 当前设计范围

| CR | 当前设计结论 |
|---|---|
| CR-015 | QMT foundation 使用 Windows QMT / MiniQMT 节点、XtQuant 外部 Python API、OMS、QMT adapter、broker lake、pre-trade hard risk gate；策略不得直接调用 QMT API。 |
| CR-016 | 激活路径为 `shadow -> simulation -> live_readonly -> small_live -> scale_up`，必须有 runbook、对账、kill switch、per-run 授权。 |
| CR-017 | `prices_raw` + `adj_factor` 为事实源，派生 `prices_qfq`、`prices_hfq`、`returns_adjusted`；QMT 委托、成交和对账只使用 raw / broker price。 |

## CP3 待确认问题

`checkpoints/CP3-CR015-CR016-CR017-HLD-REVIEW.md` 已列出 Q-030 至 Q-038，每项均包含推荐方案、备选方案、接受影响和不接受影响。恢复后不要重新整理一遍，直接以该文件为当前人工审查稿。

| ID | 主题 |
|---|---|
| Q-030 | qfq / hfq 公式、`adj_factor` 方向、复权因子可用时间和异常价格解释 |
| Q-031 | `prices_raw` / `adj_factor` / qfq / hfq / returns view schema 与旧 qfq 兼容 |
| Q-032 | broker lake root、schema、保留策略、脱敏字段和研究数据湖边界 |
| Q-033 | OMS 状态机与 QMT / mock adapter 事件映射 |
| Q-034 | pre-trade hard risk gate 的规则、阈值、配置位置和失败行为 |
| Q-035 | shadow / simulation / live_readonly / small_live / scale_up 阶段门控 |
| Q-036 | T+1 限价 / 保护价、超时撤单、失败重试和未成交处理 |
| Q-037 | 盘前 / 盘中 / 盘后对账、差异阈值、kill switch 触发和恢复 |
| Q-038 | Linux 研究节点与 Windows QMT 节点的部署、通信、鉴权、隔离和运维责任 |

## 清上下文后的恢复步骤

1. 先读取 `AGENTS.md`、本文件、`process/STATE.md`、`checkpoints/CP3-CR015-CR016-CR017-HLD-REVIEW.md`。
2. 若用户回复 `approve`，回填 CP3 人工审查为 `approved`，同步 `process/STATE.md`，并按门控组织 `meta-se` 进入 Story Plan / CP4。此时仍不得实现代码。
3. 若用户回复 `修改: <具体修改点>`，按修改点返回 HLD / ADR 修订，重跑 CP3 自动预检，并重新生成 CP3 人工审查稿。
4. 若用户回复 `reject`，回退到需求 / intake 范围重新界定。
5. CP4 PASS 后，才能组织全量 LLD / CP5；CP5 人工 approved 后，才能进入实现。

## 必读文件

| 目的 | 文件 |
|---|---|
| 当前状态 | `process/STATE.md` |
| CP3 人工门控 | `checkpoints/CP3-CR015-CR016-CR017-HLD-REVIEW.md` |
| CP3 自动预检 | `process/checks/CP3-CR015-CR016-CR017-HLD-CONSISTENCY.md` |
| CP2 已批准决策 | `checkpoints/CP2-CR015-CR016-CR017-INTAKE-DECISION-BRIEF.md` |
| 主 HLD 增量 | `process/HLD.md` |
| 数据湖 HLD 增量 | `process/HLD-DATA-LAKE.md` |
| QMT companion HLD | `process/HLD-QMT-TRADING.md` |
| ADR | `process/ARCHITECTURE-DECISION.md` |
| CR 范围 | `process/changes/CR-015-QMT-TRADING-FOUNDATION-2026-05-27.md`、`process/changes/CR-016-QMT-SIMULATION-LIVE-ACTIVATION-2026-05-27.md`、`process/changes/CR-017-ADJUSTMENT-POLICY-DUAL-VIEW-SUPPORT-2026-05-27.md` |

## 当前不需要补充的信息

暂时不需要用户再补 QMT 账号、token、交易密码、券商环境、真实资金规模、真实抓取窗口或 provider 凭据。这些属于后续 Story / LLD / CP5 或真实运行授权阶段的问题，不应在 CP3 前收集。

## 当前不能做的事

- 不能生成 `process/STORY-BACKLOG.md` 或 `process/DEVELOPMENT-PLAN.yaml` 的 CR-015 / CR-016 / CR-017 Story Plan。
- 不能生成 `process/stories/**` 的 LLD。
- 不能修改业务代码、测试、`pyproject.toml`、`uv.lock`。
- 不能读取 `.env`、token、QMT 账户、session、cookie、交易密码。
- 不能发单、撤单、查询真实账户、真实抓取、真实写湖或 publish current pointer。
