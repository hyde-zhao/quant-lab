---
handoff_id: "META-SE-CR020-STORY-PLANNING-2026-06-05"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-se"
recommended_agent_name: "se-wei"
status: "agent-completed-closed"
created_at: "2026-06-05T06:49:15+08:00"
workflow_id: "local_backtest-cr020"
change_id: "CR-020"
phase: "story-planning"
semantic: "stage-dispatch"
reuse_key: "meta-se|local_backtest-cr020|CR-020|story-planning"
dispatch:
  required: true
  status: "agent-completed-closed"
  semantic: "stage-dispatch"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-se"
  agent_path: ".agents/agents/meta-se.md"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e94dd-15f2-7381-bb18-dba9fb302809"
  agent_name: "se-chu"
  thread_id: "019e94dd-15f2-7381-bb18-dba9fb302809"
  spawned_at: "2026-06-05T06:59:43+08:00"
  resumed_at: ""
  completed_at: "2026-06-05T07:03:10+08:00"
  closed_at: "2026-06-05T07:21:21+08:00"
  evidence: "main thread spawn_agent returned agent_id=019e94dd-15f2-7381-bb18-dba9fb302809 nickname=se-chu for CR-020 story-planning / CP4; wait_agent returned completed; close_agent closed the completed thread. CP4 result is PASS at process/checks/CP4-CR020-STORY-PLAN-PRECHECK.md."
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# META-SE Handoff: CR020 Story Planning / CP4

## 目标

在 `checkpoints/CP3-CR020-HLD-REVIEW.md` 已由用户批准后，完成 CR-020 的 Story Planning / CP4 产物：

- 正式 ADR 增量，落到 `process/ARCHITECTURE-DECISION.md`。
- 正式 Story Backlog 增量，落到 `process/STORY-BACKLOG.md`。
- 正式 Development Plan 增量，落到 `process/DEVELOPMENT-PLAN.yaml`。
- `CR020-S01` 至 `CR020-S06` 六张 Story 卡片。
- CP4 自动预检结果。

本任务只允许 story-planning / CP4，不允许实现、LLD、依赖变更或真实运行。

## 已批准输入

- `checkpoints/CP3-CR020-HLD-REVIEW.md`：用户已 approve，接受 DQ-CP3-CR020-01..07 推荐方案。
- `process/checks/CP3-CR020-HLD-CONSISTENCY.md`：CP3 自动预检 PASS。
- `process/HLD.md` §36：CR-020 HLD 增量。
- `process/discussions/CP3-CR020-HLD-DISCUSSION-LOG.md`
- `process/checks/CP3-CR020-DISCUSSION-CHECKPOINT.json`
- `process/changes/CR-020-QMT-WINDOWS-GATEWAY-SERVER-LOGIN-READONLY-QUERY-ADMISSION-2026-06-04.md`
- `checkpoints/CP2-CR020-REQUIREMENTS-BASELINE.md`
- `process/USE-CASES.md`
- `process/REQUIREMENTS.md`

## 必须产出

| 产物 | 路径 | 要求 |
|---|---|---|
| ADR 增量 | `process/ARCHITECTURE-DECISION.md` | 追加 CR-020 正式 ADR，覆盖 ADR-087..093 或等价编号；不得与 HLD §36 矛盾。 |
| Story Backlog 增量 | `process/STORY-BACKLOG.md` | 追加 CR020-S01..S06，Story 数、Wave 数、依赖和 HLD §36 候选保持一致。 |
| Development Plan 增量 | `process/DEVELOPMENT-PLAN.yaml` | 追加 CR020 Wave、DAG、文件 owner、CP4/CP5/CP6/CP7 gate；明确 CP5 前 implementation_allowed=false。 |
| S01 Story | `process/stories/CR020-S01-windows-gateway-runtime-admission.md` | Windows gateway runtime 与部署准入。 |
| S02 Story | `process/stories/CR020-S02-server-qmt-login-session.md` | 服务端 QMT 登录 / session ready / redacted credential_ref。 |
| S03 Story | `process/stories/CR020-S03-linux-client-rest-transport.md` | Linux C 端 Python REST transport 与 Typer CLI pairing/diagnostics/validation。 |
| S04 Story | `process/stories/CR020-S04-hmac-pairing-allowlist-scope.md` | HMAC / pairing / allowlist / scope / redaction fail-closed。 |
| S05 Story | `process/stories/CR020-S05-query-positions-readonly.md` | `query_positions` 只读接口和脱敏结果合同。 |
| S06 Story | `process/stories/CR020-S06-docs-runbook-cp7-real-machine-validation.md` | 文档、运行手册与 CP7 实机验收边界。 |
| CP4 自动预检 | `process/checks/CP4-CR020-STORY-PLAN-PRECHECK.md` | 必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables，结论 PASS/FAIL/BLOCKED。 |

## Story / Wave 建议

| Wave | Story | 并行建议 |
|---|---|---|
| W1 | CR020-S01、CR020-S02 | 可并行规划；实现阶段需由 S01 先冻结 gateway lifecycle / config contract。 |
| W2 | CR020-S03、CR020-S04 | 可并行规划；实现阶段需复核 `trading/qmt_client.py`、`trading/qmt_client_cli.py`、`trading/qmt_auth.py` 文件 owner。 |
| W3 | CR020-S05 | 依赖 S02/S03/S04 合同；实现阶段不得提前。 |
| W4 | CR020-S06 | 依赖 S01..S05 的 CP6/CP7 证据；文档验收阶段不得提前声明真实交易或 simulation。 |

请在 Development Plan 中明确后续 LLD 队列可并行上限建议，但 CP5 全量批准前不得进入实现。若文件 owner 允许，LLD 可分批并行；实现阶段必须按依赖和文件 owner 重新计算。

## 禁止范围

- 不实现代码，不写测试，不创建 LLD，不生成 CP5，不进入 CP6/CP7。
- 不修改 `pyproject.toml`、`uv.lock` 或安装依赖。
- 不读取、打印、解析或校验真实 `.env`，不输出账号、密码、token、session、交易密码、私钥或真实私有路径。
- 不启动 gateway，不绑定端口，不连接 QMT / MiniQMT / XtQuant。
- 不执行交易、发单、撤单、改单、账户写入、simulation、live、live-readonly、small-live 或 scale-up。
- 不执行 provider fetch、真实 lake write、catalog publish、current pointer publish、broker lake write 或 reports overwrite。
- 不把 CP3 approve 解释为实现授权、运行授权、依赖变更授权或 CR 关闭授权。
- 不启动 CR-021..CR-024；这些仍是后续候选 CR。

## 安全与一致性要求

- Story 卡片必须显式记录不授权边界和后续门禁。
- `.env` 策略只能写为本地未跟踪 `.env` + `.env.example` 占位 + redacted `credential_ref`，不得写真实值。
- `query_positions` 是本轮唯一只读接口，scope=`qmt:positions:read`；其他 endpoint later-gated。
- S 端和 C 端 CLI 均为 Typer；C 端 CLI 只用于 pairing / diagnostics / validation，业务 runtime 是 Python REST client direct gateway REST API。
- CP4 自动预检必须检查 Story 数 / Wave 数一致性、DAG、文件 owner、依赖、门禁、不授权项和 CP5 前 implementation_allowed=false。

## 完成标准

- 上述 `必须产出` 文件全部落盘。
- CP4 自动预检结论为 PASS，或若 BLOCKED/FAIL，明确阻断项、受影响文件、建议修订路径。
- `process/STATE.md`、CR-020 变更单、CR-INDEX / CR-019 follow-up 台账由 meta-po 回收后再统一更新；meta-se 不直接把 CP4 结果标记为人工 approved。
- 完成后返回给 meta-po，等待 CP4/CP5 后续门禁；不得进入实现。
