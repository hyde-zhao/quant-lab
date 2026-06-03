---
story_id: "CR019-S05-pairing-hmac-auth-redaction"
title: "配对式 token/HMAC 与日志脱敏合同"
story_slug: "pairing-hmac-auth-redaction"
status: "verified"
priority: "P0"
wave: "CR019-W3-AUTH-ENDPOINT-GATE"
depends_on:
  - "CR019-S03-qmt-cside-client-cli-contract"
  - "CR019-S04-windows-gateway-lifecycle-deployment"
dependency_type:
  - upstream: "CR019-S03-qmt-cside-client-cli-contract"
    type: "contract"
  - upstream: "CR019-S04-windows-gateway-lifecycle-deployment"
    type: "contract"
cp5_batch: "CR019-STAGE6-QMT-BRIDGE-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "trading/qmt_auth.py"
    - "trading/qmt_redaction.py"
    - "tests/test_cr019_qmt_pairing_hmac_auth.py"
  shared:
    - "trading/qmt_gateway_config.py"
  merge_owner: "CR019-S05-pairing-hmac-auth-redaction"
  forbidden:
    - "real secret values"
    - "pairing code in logs"
    - ".env"
    - "credential files or secret values"
    - "no-auth as default"
lld_gate:
  required_inputs:
    - "process/HLD.md#33.10.1"
    - "process/HLD-QMT-TRADING.md#17.3"
    - "process/ARCHITECTURE-DECISION.md#ADR-071"
    - "process/stories/CR019-S05-pairing-hmac-auth-redaction.md"
  status: "confirmed"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  credential_read_allowed: false
  qmt_operation_allowed: false
task_count: 4
created_at: "2026-05-30T18:24:00+08:00"
updated_at: "2026-05-31T08:00:26+08:00"
change_id: "CR-019"
dev_handoff: "process/handoffs/META-DEV-CR019-S05-IMPLEMENT-2026-05-30.md"
cp6_status: "PASS"
cp6_result: "process/checks/CP6-CR019-S05-pairing-hmac-auth-redaction-CODING-DONE.md"
ready_for_verification_at: "2026-05-30T21:08:16+08:00"
cp7_handoff: "process/handoffs/META-QA-CR019-S05-CP7-VERIFY-2026-05-30.md"
cp7_status: "PASS"
cp7_result: "process/checks/CP7-CR019-S05-pairing-hmac-auth-redaction-VERIFICATION-DONE.md"
qa_agent_id: "019e7905-1ec5-77d3-b270-784c0fb0a48f"
qa_agent_name: "qa-yan"
qa_started_at: "2026-05-30T21:14:03+08:00"
qa_completed_at: "2026-05-30T21:17:14+08:00"
qa_closed_at: "2026-05-30T21:21:14+08:00"
verified_at: "2026-05-31T08:00:26+08:00"
---

# CR019-S05：配对式 token/HMAC 与日志脱敏合同

## 目标

定义 pairing request / list / approve / complete、HMAC headers、timestamp、nonce、scope、redaction 和 no-auth 临时模式边界；确认 HMAC 只识别调用方，不授权真实交易。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-16、UC-17 |
| 需求 | REQ-148、REQ-151、REQ-152 |
| HLD | `process/HLD.md` §33.10、§33.10.1、§33.13；`process/HLD-QMT-TRADING.md` §17.3 |
| ADR | ADR-071 |

## 开发上下文（dev_context）

**输入文件**：DQ-04 approved 决策、HLD §33.10.1、QMT companion §17.3、本 Story 卡片。

**输出文件**：`trading/qmt_auth.py`、`trading/qmt_redaction.py`、`tests/test_cr019_qmt_pairing_hmac_auth.py`；共享 `trading/qmt_gateway_config.py`。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR019-S03 | contract | C 侧 pair request / complete 入口合同先冻结 | 不读取真实 secret | client id / secret 只以引用和脱敏标签表达 |
| CR019-S04 | contract | S 侧 gateway config 合同先冻结 | 不启动服务 | auth config 不包含真实值 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `trading/qmt_auth.py`、`trading/qmt_redaction.py`、`tests/test_cr019_qmt_pairing_hmac_auth.py` | 当前 Story 独占 |
| shared | `trading/qmt_gateway_config.py` | merge owner 为当前 Story |
| forbidden | 真实 secret、pairing code 日志、`.env`、凭据文件、no-auth 默认 | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR019-S05-T1 | 创建 | `trading/qmt_auth.py` | 定义 pairing 状态、HMAC 签名校验、timestamp / nonce / scope 失败语义 |
| CR019-S05-T2 | 创建 | `trading/qmt_redaction.py` | 定义 secret、pairing code、token、账户、session、`.env` 脱敏规则 |
| CR019-S05-T3 | 创建 | `tests/test_cr019_qmt_pairing_hmac_auth.py` | 验证 HMAC mismatch、replay、过期、scope 不足和日志脱敏 |
| CR019-S05-T4 | 修改 | `trading/qmt_gateway_config.py` | 按 LLD 接入 auth mode 配置，no-auth 仅 debug / fixture / 显式临时 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr019_qmt_pairing_hmac_auth.py`。

**验证方式**：fixture-only 合同测试；不得生成、读取或打印真实 secret。

## 量化验收标准（acceptance_criteria）

- [ ] pair request / list / approve / complete 四步合同覆盖率为 100%。
- [ ] timestamp 偏移、nonce replay、scope 不足、signature mismatch 均 hard block。
- [ ] secret、pairing code、token、账户号、session、`.env` 日志泄露次数为 0。
- [ ] HMAC pass 直接授权 simulation/live/account/cancel 的次数为 0。

## 阻塞说明

CP5 已通过；S03/S04 合同实现与验证均已 CP7 PASS 并收敛为 verified。当前 Story 已通过 `process/handoffs/META-DEV-CR019-S05-IMPLEMENT-2026-05-30.md` 调度给 `meta-dev/dev-yang` 执行受控离线实现。任何真实 secret 或凭据均不得进入仓库或检查点。

## CP6 状态证据

| 字段 | 值 |
|---|---|
| 状态 | `ready-for-verification` |
| CP6 结果 | `process/checks/CP6-CR019-S05-pairing-hmac-auth-redaction-CODING-DONE.md` |
| CP6 结论 | `PASS` |
| 验证边界 | 仅离线 / fixture / dry-run 合同验证；未读取 `.env` 或凭据，未启动服务，未打开 socket，未调用真实 QMT / provider / lake / broker / publish / simulation / live。 |
