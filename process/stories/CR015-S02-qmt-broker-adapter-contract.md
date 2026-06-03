---
story_id: "CR015-S02-qmt-broker-adapter-contract"
title: "QMT broker adapter 合同"
story_slug: "qmt-broker-adapter-contract"
status: "verified"
priority: "P0"
wave: "CR015-W1-FOUNDATION-CONTRACTS"
depends_on:
  - "CR015-S01-qmt-environment-and-interface-spike"
  - "CR017-S01-adjustment-policy-requirements-and-adr-refresh"
dependency_type:
  - upstream: "CR015-S01-qmt-environment-and-interface-spike"
    type: "contract"
  - upstream: "CR017-S01-adjustment-policy-requirements-and-adr-refresh"
    type: "contract"
cp5_batch: "CR015-QMT-FOUNDATION-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "trading/qmt_adapter.py"
    - "tests/test_cr015_qmt_adapter_contract.py"
  shared:
    - "trading/qmt_transport.py"
  merge_owner: "CR015-S02-qmt-broker-adapter-contract"
  forbidden:
    - "pyproject.toml"
    - "uv.lock"
    - "credential files or secret values"
    - "real broker order or cancel call"
lld_gate:
  required_inputs:
    - "process/HLD-QMT-TRADING.md#5"
    - "process/HLD-QMT-TRADING.md#7.1"
    - "process/ARCHITECTURE-DECISION.md#ADR-055"
    - "process/stories/CR015-S02-qmt-broker-adapter-contract.md"
  status: "approved"
  cp5_batch: "CR015-QMT-FOUNDATION-BATCH-A"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  reason: "CR015-S01 已 CP7 PASS / verified；CR017-S01 已 verified；CP5 已 approved；当前无 dev_running 文件冲突，可进入 adapter contract 离线实现。"
created_at: "2026-05-28"
updated_at: "2026-05-28T08:06:26+08:00"
verification_gate:
  cp7_status: "PASS"
  cp7_result: "process/checks/CP7-CR015-S02-qmt-broker-adapter-contract-VERIFICATION-DONE.md"
  verification_handoff: "process/handoffs/META-QA-CR015-S02-CP7-VERIFY-2026-05-28.md"
  verified_by: "meta-qa/qa-zhang"
  verified_at: "2026-05-28T08:03:39+08:00"
  agent_id: "019e6be3-369f-7f11-bed0-7e01d3555089"
  agent_name: "qa-zhang"
change_id: "CR-015"
---

# CR015-S02：QMT broker adapter 合同

## 目标

定义唯一 broker 触达 adapter 的输入、输出、mode、error enum 和 mock event 合同。CR-015 阶段只允许 shadow / dry-run / mock，不允许真实发单、撤单或账户写操作。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-10 |
| 需求 | REQ-105、REQ-110、REQ-111、REQ-121 |
| HLD | `process/HLD-QMT-TRADING.md` §5、§7.1 |
| ADR | ADR-055、ADR-061 |

## 开发上下文（dev_context）

**背景说明**：adapter 是唯一 broker API boundary。它只能接收 risk-passed intent，按 mode 输出 broker event 或 blocked reason；真实模式必须由 CR-016 stage gate 和 per-run 授权控制。

**输入文件**：CR015-S01 environment / transport 合同、CR017-S01 policy 合同、HLD-QMT-TRADING。

**输出文件**：`trading/qmt_adapter.py`、`tests/test_cr015_qmt_adapter_contract.py`；共享 `trading/qmt_transport.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| adapter.submit_intent | risk-passed intent、adapter_mode | broker_order_event / dry_run_plan | mode 未授权时 blocked |
| adapter.cancel_order | cancel request、stage gate status | cancel_event | CR-015 默认不触达真实 cancel |
| mock event factory | scenario id | accepted / partial / filled / rejected / timeout / unknown | 只生成 fixture event |

**设计约束**：adapter 不读取凭据、不发真实指令、不写真实 broker lake；真实 XtQuant 签名和连接细节在 LLD 中以受控引用描述，不在 Story Plan 阶段固化。

**命名规范**：事件字段使用 `broker_event_type`、`broker_order_ref`、`adapter_mode`、`adapter_calls`、`blocked_reason`。

**平台目标**：Windows QMT 节点 adapter contract + Linux 研究节点 mock contract。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR015-S01 | contract | transport / env mode 已定义 | adapter 实现需复用 transport enum | 不直接远程调用 |
| CR017-S01 | contract | raw execution boundary 已定义 | 非 raw execution policy blocked | 防止复权价下单 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR015-S02-T1 | 创建 | `trading/qmt_adapter.py` | 定义 adapter mode、submit/cancel contract 和 mock events |
| CR015-S02-T2 | 创建 | `tests/test_cr015_qmt_adapter_contract.py` | 覆盖 mode gate、mock event、blocked reason |
| CR015-S02-T3 | 修改 | `trading/qmt_transport.py` | 按 LLD 对齐 payload / ack enum |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr015_qmt_adapter_contract.py`。

**验证方式**：mock adapter fixture；不需要真实 QMT。

**依赖环境**：Python 3.11、uv、pytest。

**关键验证场景**：shadow/dry_run/mock 不触达真实 API；未授权 live mode blocked；非 raw execution policy blocked；mock event 枚举完整。

## 量化验收标准（acceptance_criteria）

- [x] adapter mode gate 覆盖 shadow、dry_run、mock、simulation、live_readonly、small_live 6 类状态。
- [x] 未授权真实 order / cancel / account write 调用次数均为 0。
- [x] 非 raw execution policy 进入 adapter 的通过次数为 0。
- [x] mock event 至少覆盖 accepted、partial、filled、rejected、timeout、unknown。

## 阻塞说明

CP5 前不得实现；真实 adapter 依赖、连接和运行必须由 CR-016 后续 stage gate 与用户授权控制。
