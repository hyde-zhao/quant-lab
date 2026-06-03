---
handoff_id: "META-SE-CR019-HLD-ADR-2026-05-30"
from_agent: "meta-po"
to_agent: "meta-se"
workflow_id: "local_backtest-cr019"
change_id: "CR-019"
phase: "solution-design"
created_at: "2026-05-30T17:12:54+08:00"
status: "agent_completed"
dispatch:
  required: true
  semantic: "stage-dispatch"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-se"
  agent_path: ".agents/agents/meta-se.md"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e782a-2097-7112-a0da-9f0a692a06fd"
  agent_name: "se-wei"
  thread_id: "019e782a-2097-7112-a0da-9f0a692a06fd"
  spawned_at: "2026-05-30T17:14:51+08:00"
  resumed_at: ""
  completed_at: "2026-05-30T17:31:52+08:00"
  evidence: "spawn_agent returned agent_id=019e782a-2097-7112-a0da-9f0a692a06fd nickname=se-wei; close_agent previous_status returned completed CP3 solution-design with CP3 auto PASS and review draft"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-se"
  workflow_id: "local_backtest-cr019"
  change_id: "CR-019"
  story_id: "CR019-HLD-ADR"
  wave_id: "CR019-G2-CP3"
---

# META-SE CR-019 HLD / ADR 交接

## 任务

请以 `meta-se` 身份执行 CR-019 的 CP3 solution-design 阶段，产出可供 meta-po 发起 CP3 人工审查的 HLD / ADR 设计输入。

本轮只允许设计与检查产物，不允许实现代码、修改依赖、启动服务、调用真实 QMT / MiniQMT / XtQuant、读取凭据、真实 provider fetch、写真实 lake、publish、写 broker lake 或执行 simulation / live run。

## 必读输入

| 文件 | 用途 |
|---|---|
| `AGENTS.md` | Meta Flow 阶段、检查点、子 agent 调度、人工门禁和设计评审规则 |
| `process/STATE.md` | 当前阶段、active_change、CP2 approve 状态、禁止真实操作边界 |
| `process/changes/CR-019-STAGE6-MULTIFACTOR-SIMULATION-ARCHITECTURE-2026-05-30.md` | CR-019 影响分析、QMT C/S bridge 草案、LLD 批次候选 |
| `process/USE-CASES.md` | UC-15 至 UC-18，尤其 UC-16 / UC-17 的 QMT C/S bridge 与完整 endpoint matrix |
| `process/REQUIREMENTS.md` | REQ-138 至 REQ-160，尤其 REQ-146 至 REQ-160 |
| `process/CLARIFICATION-LOG.md` | Q-039 至 Q-044 状态；Q-040 / Q-043 已 resolved；Q-044 推荐方案 |
| `checkpoints/CP2-CR019-REQUIREMENTS-BASELINE.md` | CP2 approved 结果和 DQ-01 至 DQ-07 决策 |
| `process/checks/CP1-CR019-USE-CASE-COMPLETENESS.md` | CP1 PASS 证据 |
| `process/checks/CP2-CR019-REQUIREMENTS-BASELINE.md` | CP2 自动预检 PASS 证据 |
| `process/discussions/CP2-CR019-SCENARIO-DISCUSSION-LOG.md` | Scenario Gray Areas 与用户纠偏记录 |
| `process/checks/CP2-CR019-DISCUSSION-CHECKPOINT.json` | CP2 discussion 恢复点 |
| `docs/QMT-SIMULATION-LIVE-RUNBOOK.md` | CR016 stage gate、per-run authorization、对账、kill switch |
| `docs/QMT-INCIDENT-PLAYBOOK.md` | gateway / QMT incident 和 recovery 边界 |
| `process/HLD.md` | 现有 HLD，按增量方式追加 CR-019，不重写旧基线 |
| `process/ARCHITECTURE-DECISION.md` | 现有 ADR，按增量方式追加 CR-019 ADR |

## 必须处理的设计问题

| ID | 问题 | 当前 CP2 结论 |
|---|---|---|
| Q-039 | 局域网无应用层鉴权 / 可选 token-HMAC、bind/firewall/log redaction 如何冻结 | CP2 推荐受控局域网默认无应用层鉴权；如需鉴权则最简 token/HMAC |
| Q-040 | benchmark / tracking / freeze fields | 已 resolved：多基准看板 + primary benchmark |
| Q-041 | 完整 QMT endpoint 的 run mode / stage gate / risk gate / kill-switch | 接口完整支持，真实转发由运行门控控制 |
| Q-042 | fallback 切换条件和责任边界 | 默认 blocked-only 或人工 dry-run file，不允许自动真实 QMT fallback |
| Q-043 | Backtrader / Qlib / minute / Level2 后置顺序 | 已 resolved：Backtrader W6、Qlib W7、minute/Level2 Spike 后置 |
| Q-044 | C 侧接口形态 | CP2 推荐 Python client / 函数调用为主 + 薄 CLI |

## 目标输出

请在完成后直接修改 / 新增必要文件，并在最终回复中列出变更文件。最低目标：

1. 增量更新 `process/HLD.md`，加入 CR-019 HLD 章节，覆盖：
   - QMT C/S bridge：local_backtest C 侧 client + Windows S 侧 gateway。
   - 完整 QMT endpoint matrix。
   - C 侧 Python client / 薄 CLI 边界。
   - S 侧 Windows 可运行 / 可安装命令边界。
   - 运行门控、fallback、日志脱敏、局域网无鉴权 / 可选 token-HMAC。
   - 多基准 + primary benchmark admission 设计。
2. 增量更新 `process/ARCHITECTURE-DECISION.md`，加入 CR-019 ADR，至少覆盖：
   - QMT C/S bridge 主选。
   - C 侧接口形态。
   - 完整 endpoint matrix 与运行门控分离。
   - 鉴权策略。
   - fallback 策略。
   - Backtrader / Qlib / minute / Level2 后置。
3. 生成或更新 CP3 discussion log / checkpoint：
   - `process/discussions/CP3-CR019-HLD-DISCUSSION-LOG.md`
   - `process/checks/CP3-CR019-DISCUSSION-CHECKPOINT.json`
4. 生成 CP3 自动预检：
   - `process/checks/CP3-CR019-HLD-CONSISTENCY.md`
5. 如 HLD 已足够收敛，可生成 CP3 人工审查稿草案：
   - `checkpoints/CP3-CR019-HLD-REVIEW.md`
   - 注意正式发起和回填仍由 meta-po 完成。

## 验收要求

- CP3 自动预检必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables。
- CP3 Decision Brief 必须包含推荐方案、备选方案、优劣、影响 / 风险、回退 / 切换条件。
- HLD / ADR 必须遵守设计评审规则：内部一致、目标量化、集成契约显式化、失败路径、回退决策可操作、遗留问题状态闭环、修订记录完整。
- 不得把“局域网运行 / 无应用层鉴权”写成“不需要 QMT 功能”。
- 不得把“完整 endpoint 可见”写成“真实 QMT 操作已授权”。
- 不得进入 Story LLD 或实现。
