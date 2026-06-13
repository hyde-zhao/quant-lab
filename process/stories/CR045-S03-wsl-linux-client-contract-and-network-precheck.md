---
story_id: "CR045-S03"
title: "WSL Linux Client Contract and Network Precheck"
story_slug: "wsl-linux-client-contract-and-network-precheck"
status: "ready-for-verification"
priority: "P0"
wave: "W2"
implementation_allowed: true
implementation_allowed_until: "CP5 approved at 2026-06-11T23:16:11+08:00; L2 skeleton / fixture / static only"
depends_on:
  - "CR045-S01"
dependency_contracts:
  - upstream_story: "CR045-S01"
    type: "contract"
    required_for: "authorization and no-SDK/no-secret Linux boundary"
  - upstream_story: "CR045-S02"
    type: "contract"
    required_for: "health/capabilities schema from Feature DESIGN and S02 LLD"
feature_design_refs:
  - "docs/features/cr045-goldminer-bridge/DESIGN.md#feature-边界与相邻对象"
  - "docs/features/cr045-goldminer-bridge/TEST-PLAN.md#风险驱动测试"
  - "docs/features/cr045-goldminer-bridge/TASKS.md#cr045-s03"
lld_policy:
  required_level: "full-lld"
  trigger_reasons:
    - "cross-platform-contract"
    - "external-interface"
    - "failure-path"
  rationale: "WSL / Linux client 是跨 OS 调用边界，必须明确 fixture transport、network precheck、runtime-not-started 行为和禁止 SDK/凭据。"
  waiver_reason: ""
  revisit_condition: "任何真实 bridge connection、Windows local endpoint probing、SDK import 或凭据读取需求出现时，暂停并发起 L3 授权或 Spike。"
  evidence_path: "process/stories/CR045-S03-wsl-linux-client-contract-and-network-precheck-LLD.md"
file_ownership:
  primary:
    - "process/stories/CR045-S03-wsl-linux-client-contract-and-network-precheck.md"
    - "process/stories/CR045-S03-wsl-linux-client-contract-and-network-precheck-LLD.md"
    - "engine/goldminer_bridge_client.py"
    - "tests/test_cr045_goldminer_bridge_client.py"
  shared:
    - "engine/goldminer_bridge_contract.py"
  merge_owner: "CR045-S03"
  forbidden:
    - ".env"
    - ".env.*"
    - "gm"
    - "gmtrade"
lld_gate:
  required_inputs:
    - "CR045-S01 design evidence"
    - "docs/features/cr045-goldminer-bridge/DESIGN.md"
    - "CR045-S02 API contract"
  design_evidence_type: "full-lld"
  design_evidence_path: "process/stories/CR045-S03-wsl-linux-client-contract-and-network-precheck-LLD.md"
  status: "confirmed"
dev_gate:
  implementation_allowed: true
  allowed_after: "CP5 approved"
  design_evidence_confirmed: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  real_runtime_authorized: false
---

# CR045-S03 WSL Linux Client Contract and Network Precheck

## 目标

定义 WSL / Linux bridge client 的合同和 network precheck：Linux 侧只构造 allowlist request、处理 fixture/blocked response，不持有 Goldminer SDK 或凭据，不连接真实 Windows runtime。

## 开发上下文（dev_context）

- 输入文件：S01 设计证据、S02 API contract、Feature DESIGN / TEST-PLAN / TASKS。
- 输出文件：`process/stories/CR045-S03-wsl-linux-client-contract-and-network-precheck-LLD.md`；未来 CP6 可创建 `engine/goldminer_bridge_client.py` 和 `tests/test_cr045_goldminer_bridge_client.py`。
- 接口约定：client 只允许 action=`health|capabilities|readonly_probe_skeleton`；network precheck 在 L2 下只能返回 fixture/blocked，不尝试启动 runtime。
- 设计约束：不导入 `gm` / `gmtrade`；不读取 `.env`、token、account_id；不访问 Windows 凭据；不探测真实端口。
- 平台目标：WSL / Linux research server 只做 client、研究、回测、组合生成和 order intent。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR045-S01 | contract | S01 授权边界已声明 | CP5 approved + S01 confirmed | 根安全边界。 |
| CR045-S02 | contract | S02 API contract 可由 Feature DESIGN 和 LLD 冻结 | CP5 approved + S02 contract frozen | client 消费 health/capabilities schema。 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `engine/goldminer_bridge_client.py` | CR045-S03 future primary owner。 |
| primary | `tests/test_cr045_goldminer_bridge_client.py` | CR045-S03 future primary owner。 |
| shared | `engine/goldminer_bridge_contract.py` | 只消费 S02 contract；修改需与 CR045-S02 协调。 |
| forbidden | `.env`、`.env.*`、`gm`、`gmtrade` | 禁止 SDK/凭据路径。 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR045-S03-T1 | 设计 | `CR045-S03-...-LLD.md` | 定义 client request builder 和 JSON-safe response parsing。 |
| CR045-S03-T2 | 设计 | `CR045-S03-...-LLD.md` | 定义 fixture transport 和 network precheck 的 blocked 行为。 |
| CR045-S03-T3 | 设计 | `CR045-S03-...-LLD.md` | 定义禁止 SDK import、凭据读取和真实端口连接的验证方式。 |

## 技术说明

本 Story 需要 `full-lld`。CP4 不写实现或 LLD。

## 验证上下文（validation_context）

| 项目 | 内容 |
|---|---|
| validation_mode | static-only + fixture-only |
| 验证入口 | CP6 后 `uv run --python 3.11 pytest -q tests/test_cr045_goldminer_bridge_client.py`；静态扫描 forbidden imports/calls。 |
| 关键验证场景 | fixture transport；runtime-not-started；无 SDK import；无凭据读取。 |
| 禁止验证方式 | 不连接真实 Windows bridge endpoint，不运行 `socket`/网络探测，不登录 Goldminer。 |

## 量化验收标准（acceptance_criteria）

- [ ] LLD 必须声明 WSL / Linux client 不持有 Goldminer SDK、token、account_id 或 session。
- [ ] client allowlist action 数量为 3：health、capabilities、readonly_probe_skeleton。
- [ ] network precheck 在 L2 下不得启动 runtime、不得连接真实端口、不得读取真实 endpoint 配置。
- [ ] static validation 必须覆盖 `gm` / `gmtrade` runtime import/call 禁止项。
- [ ] 所有 fixture response 必须包含 `not_authorization=true` 或明确 blocked reason。
- [ ] CP5 approved 前 dev_gate 保持 false。

## 阻塞说明

无 CP4 阻塞。真实 bridge connection 属于 L3+，当前不授权。
