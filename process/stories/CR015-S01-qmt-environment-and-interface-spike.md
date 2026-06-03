---
story_id: "CR015-S01-qmt-environment-and-interface-spike"
title: "QMT 环境与接口边界 spike"
story_slug: "qmt-environment-and-interface-spike"
status: "verified"
priority: "P0"
wave: "CR015-W1-FOUNDATION-CONTRACTS"
depends_on: []
dependency_type: []
cp5_batch: "CR015-QMT-FOUNDATION-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "trading/qmt_environment.py"
    - "trading/qmt_transport.py"
    - "tests/test_cr015_qmt_environment_boundary.py"
  shared:
    - "docs/QMT-TRADING-RUNBOOK.md"
  merge_owner: "CR015-S01-qmt-environment-and-interface-spike"
  forbidden:
    - "pyproject.toml"
    - "uv.lock"
    - "credential files or secret values"
    - "real QMT process invocation"
lld_gate:
  required_inputs:
    - "process/HLD-QMT-TRADING.md#3"
    - "process/HLD-QMT-TRADING.md#6"
    - "process/ARCHITECTURE-DECISION.md#ADR-055"
    - "process/ARCHITECTURE-DECISION.md#ADR-061"
    - "process/stories/CR015-S01-qmt-environment-and-interface-spike.md"
  status: "approved"
  cp5_batch: "CR015-QMT-FOUNDATION-BATCH-A"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  reason: "CP5 已 approved；本 Story 无上游依赖，且文件所有权与 CR017-W1 不冲突，可并行进入受控离线实现。"
created_at: "2026-05-28"
updated_at: "2026-05-28T07:48:21+08:00"
verification_gate:
  cp7_status: "PASS"
  cp7_result: "process/checks/CP7-CR015-S01-qmt-environment-and-interface-spike-VERIFICATION-DONE.md"
  verification_handoff: "process/handoffs/META-QA-CR015-S01-CP7-VERIFY-2026-05-28.md"
  verified_by: "meta-qa/qa-shi"
  verified_at: "2026-05-28T07:46:49+08:00"
  agent_id: "019e6bd3-3ab0-7672-8f95-0ca4ed22fa48"
  agent_name: "qa-shi"
change_id: "CR-015"
---

# CR015-S01：QMT 环境与接口边界 spike

## 目标

定义 Linux 研究节点与 Windows QMT 节点的环境、接口发现、transport、ack/error enum 和 forbidden boundary。该 Story 只做 shadow / dry-run / mock 设计，不调用真实 QMT。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-10 |
| 需求 | REQ-105、REQ-110、REQ-111、REQ-121 |
| HLD | `process/HLD-QMT-TRADING.md` §3、§4、§6、§7.1 |
| ADR | ADR-055、ADR-061 |

## 开发上下文（dev_context）

**背景说明**：QMT adapter 只能在 Windows QMT / MiniQMT 节点运行；Linux 研究节点不得直接调用 broker API。保守默认为 signed file drop + ack/error enum，RPC 只作为后续扩展。

**输入文件**：HLD-QMT-TRADING、ADR-055、ADR-061、UC-10、REQ-105。

**输出文件**：`trading/qmt_environment.py`、`trading/qmt_transport.py`、`tests/test_cr015_qmt_environment_boundary.py`、`docs/QMT-TRADING-RUNBOOK.md`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| environment probe | configured mode、node role | environment_status、capability enum | 不启动真实 QMT，不读取凭据 |
| file-drop transport contract | signed payload metadata | ack / error enum | payload 只含脱敏 metadata 和 run_id |
| forbidden import scan hook | source path list | no direct broker import status | 策略层出现 broker API 直连时 fail |

**设计约束**：不安装依赖、不运行 GUI、不调用真实 API、不读取凭据；真实 adapter 细节必须在 LLD 中以官方文档或本地环境事实复核。

**命名规范**：`node_role=research|trading`、`adapter_mode=shadow|dry_run|mock|simulation|live_readonly|small_live`、`transport_status=accepted|rejected|timeout|unknown`。

**平台目标**：Linux 研究节点 + Windows QMT 节点解耦。

### 依赖与并行门控

无上游 Story；可与 CR017-S01/S02 并行写 LLD。开发仍需 CP5 全量确认。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR015-S01-T1 | 创建 | `trading/qmt_environment.py` | 定义节点角色、adapter mode 和环境状态枚举 |
| CR015-S01-T2 | 创建 | `trading/qmt_transport.py` | 定义 signed file drop payload / ack / error enum |
| CR015-S01-T3 | 创建 | `tests/test_cr015_qmt_environment_boundary.py` | 验证 no real API、no credential read、no direct broker import |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr015_qmt_environment_boundary.py`。

**验证方式**：离线静态 / fixture 检查；不需要 QMT 客户端。

**依赖环境**：Python 3.11、uv、pytest。

**关键验证场景**：研究节点不允许真实 adapter mode；transport ack/error enum 完整；策略目录 direct broker import 次数为 0；credential_read=0。

## 量化验收标准（acceptance_criteria）

- [ ] node role、adapter mode、ack/error enum 覆盖 HLD-QMT-TRADING §6 和 §7.1。
- [ ] 策略层直接 broker API import / call 允许次数为 0。
- [ ] 默认验证 real_order_call、real_cancel_call、account_write_call、credential_read 均为 0。
- [ ] 不修改 `pyproject.toml` / `uv.lock`。

## 阻塞说明

CP5 前不得实现；真实 QMT 环境探测、依赖引入和 adapter 实测必须后续单独授权。
