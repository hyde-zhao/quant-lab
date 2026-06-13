---
handoff_id: "META-SE-CR045-STORY-PLANNING-2026-06-11"
from_agent: "meta-po"
to_agent: "meta-se"
change_id: "CR-045"
phase: "story-planning"
status: "completed"
created_at: "2026-06-11T22:28:46+08:00"
completed_at: "2026-06-11T23:05:00+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019eb71b-8a9a-7af2-a12f-e9ac8f7cc238"
  thread_id: "019eb71b-8a9a-7af2-a12f-e9ac8f7cc238"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-06-11T22:28:46+08:00"
  completed_at: "2026-06-11T23:05:00+08:00"
context_policy:
  read_profile: "compact"
  must_read:
    - "process/context/CP3-CR045-DESIGN-CONTEXT.yaml"
    - "process/checkpoints/CP3-CR045-HLD-REVIEW.md"
    - "docs/design/HLD-CR045-GOLDMINER-WINDOWS-BRIDGE.md"
    - "docs/design/ARCHITECTURE-DECISION-CR045.md"
    - "process/changes/CR-045-GOLDMINER-WINDOWS-BRIDGE-READONLY-PROBE-2026-06-11.md"
  read_if_needed:
    - "process/checks/CP3-CR045-HLD-CONSISTENCY.md"
    - "process/discussions/CP3-CR045-HLD-DISCUSSION-LOG.md"
    - "process/checks/CP3-CR045-DISCUSSION-CHECKPOINT.json"
    - "engine/broker_adapter.py"
    - "process/changes/CR-044-GOLDMINER-SIMULATION-ADMISSION-2026-06-11.md"
  do_not_read_by_default:
    - ".env"
    - "*.env"
    - "Windows local credential files"
    - "token/account_id/account/password/session/cookie/private key material"
---

# META-SE CR045 Story Planning Handoff

## 目标

为 CR045 Goldminer Windows Bridge Readonly Probe 在 CP3 approved 后生成 story-planning / CP4 所需设计规划产物。

## 必须产出

| 产物 | 路径 |
|---|---|
| CR045 Feature Design Matrix | `docs/design/FEATURE-DESIGN-MATRIX-CR045.md` |
| CR045 Feature Design | `docs/features/cr045-goldminer-bridge/DESIGN.md` |
| CR045 Feature Test Plan | `docs/features/cr045-goldminer-bridge/TEST-PLAN.md` |
| CR045 Feature Tasks | `docs/features/cr045-goldminer-bridge/TASKS.md` |
| CR045 Story Backlog | `process/STORY-BACKLOG-CR045.md` |
| CR045 Development Plan | `process/DEVELOPMENT-PLAN-CR045.yaml` |
| CR045 Story Cards | `process/stories/CR045-S01-*.md` 到 `process/stories/CR045-S06-*.md` |
| CP4 自动预检 | `process/checks/CP4-CR045-STORY-DAG-PARALLEL-SAFETY.md` |

## 已确认架构边界

- CP3 已 approved，用户接受 DQ-CP3-CR045-01..06。
- Windows trading PC 是唯一 Goldminer SDK runtime / 交易执行边界。
- WSL / 未来高性能 Linux research server 只做研究、回测、组合生成、order intent 和 bridge client。
- 当前只授权 L2 bridge skeleton / fixture-only / static validation。
- 不授权读取 token/account_id，不授权启动 Windows bridge runtime，不授权登录 / 连接 Goldminer，不授权查询账户，不授权下单 / 撤单，不授权 simulation/live。

## Story 建议基线

- `CR045-S01-windows-bridge-security-boundary`：full-lld。
- `CR045-S02-bridge-health-capabilities-skeleton`：full-lld。
- `CR045-S03-wsl-linux-client-contract-and-network-precheck`：full-lld。
- `CR045-S04-readonly-probe-allowlist-and-blocked-first`：full-lld。
- `CR045-S05-redaction-and-no-operation-static-validation`：full-lld。
- `CR045-S06-user-runbook-and-follow-up-gates`：technical-note；若引入自动 manifest/schema/guard script 则升 full-lld。

## 验收要求

- CP4 必须只做 Story / Feature 设计矩阵和 DAG / 并行安全预检，不进入 LLD 写作和实现。
- 每个 Story 必须明确 `lld_policy.required_level`、`feature_design_refs`、依赖、文件 owner、dev_gate 和不授权边界。
- CP4 自动预检必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables，并说明 CP4 摘要将汇入 CP5。
- 不得新增依赖，不得启动 runtime，不得读取凭据，不得连接 Goldminer。
