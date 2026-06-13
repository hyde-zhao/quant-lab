---
story_id: "CR020-S04-hmac-pairing-allowlist-scope"
title: "HMAC pairing / allowlist / scope / nonce fail-closed"
story_slug: "hmac-pairing-allowlist-scope"
status: "verified-fixture-static-pending-manual-validation"
priority: "P0"
wave: "CR020-W2-CLIENT-AUTH"
depends_on:
  - "CR020-S01-windows-gateway-runtime-admission"
  - "CR020-S03-linux-client-rest-transport"
dependency_type:
  - "gateway-config-contract"
  - "client-auth-contract"
cp5_batch: "CR020-QMT-GATEWAY-READONLY-BATCH-A"
implementation_allowed: true
no_auth_default_allowed: false
credential_output_allowed: false
qmt_operation_allowed: false
file_ownership:
  primary:
    - "trading/qmt_auth.py"
    - "trading/qmt_redaction.py"
    - "tests/test_cr020_hmac_pairing_allowlist_scope.py"
  shared:
    - "trading/qmt_gateway_config.py"
    - "trading/qmt_client.py"
    - "trading/qmt_endpoint_matrix.py"
  merge_owner: "CR020-S04-hmac-pairing-allowlist-scope"
  forbidden:
    - "no-auth default"
    - "real secret values"
    - "pairing code logs"
    - "nonce replay accepted"
    - "scope bypass"
    - "redaction fallback-to-raw"
lld_gate:
  required_inputs:
    - "process/HLD.md#36.10"
    - "process/HLD.md#36.11"
    - "process/HLD.md#36.14"
    - "process/ARCHITECTURE-DECISION.md#ADR-091"
    - "process/stories/CR020-S04-hmac-pairing-allowlist-scope.md"
  status: "approved"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  dependency_change_allowed: false
  no_auth_default_allowed: false
  credential_output_allowed: false
  qmt_operation_allowed: false
task_count: 5
created_at: "2026-06-05T07:03:10+08:00"
updated_at: "2026-06-05T09:21:16+08:00"
change_id: "CR-020"
cp6_result: "process/checks/CP6-CR020-S04-hmac-pairing-allowlist-scope-CODING-DONE.md"
cp7_result: "process/checks/CP7-CR020-FIXTURE-STATIC-VERIFICATION-DONE.md"
manual_windows_qmt_validation: "pending-user"
---

# CR020-S04：HMAC pairing / allowlist / scope / nonce fail-closed

## 目标

定义 S/C pairing、client id、HMAC headers、timestamp、nonce replay、allowlist、scope matrix、redaction 和 no-auth 禁止边界。该 Story 必须让鉴权、授权范围和日志脱敏全部 fail-closed。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求基线 | `checkpoints/CP2-CR020-REQUIREMENTS-BASELINE.md` D4 |
| HLD | `process/HLD.md` §36.10、§36.11、§36.14、§36.17 |
| ADR | ADR-091 |
| CP3 决策 | DQ-CP3-CR020-04 |

## 开发上下文（dev_context）

**背景说明**：CR-020 的只读查询需要调用方识别和 scope 准入，但 HMAC 不替代 session ready、run gate 或后续运行授权。鉴权失败必须阻断 adapter call。

**输入文件**：`process/HLD.md` §36、`process/ARCHITECTURE-DECISION.md` ADR-091、`process/stories/CR020-S01-windows-gateway-runtime-admission.md`、`process/stories/CR020-S03-linux-client-rest-transport.md`、本 Story 卡片。

**输出文件**：`trading/qmt_auth.py`、`trading/qmt_redaction.py`、`tests/test_cr020_hmac_pairing_allowlist_scope.py`。

**接口约定**：

| 合同项 | 要求 |
|---|---|
| pairing | client id / secret 只通过受控流程建立；不得记录 pairing code 或 secret |
| HMAC | 必须校验 timestamp、nonce、signature、client id |
| allowlist | 未匹配调用方必须 fail-closed |
| scope | `query_positions` 仅接受 `qmt:positions:read` |
| redaction | 失败时不得 fallback 到 raw 输出 |

**设计约束**：no-auth 不能作为默认；不得生成或记录真实 secret；不得绕过 scope；不得输出 token、session、私钥、账号或 pairing code。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR020-S01 | gateway-config-contract | 需要配置和 bind/admission 合同 | CP5 前不得实现 | 鉴权配置与 gateway config 共用边界 |
| CR020-S03 | client-auth-contract | 需要 client header / transport 合同 | CP5 前不得实现 | HMAC header 与 client request schema 需一致 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `trading/qmt_auth.py`、`trading/qmt_redaction.py`、`tests/test_cr020_hmac_pairing_allowlist_scope.py` | 当前 Story 独占 LLD owner |
| shared | `trading/qmt_gateway_config.py`、`trading/qmt_client.py`、`trading/qmt_endpoint_matrix.py` | 与 S01/S03/S05 串行合并 |
| forbidden | no-auth default、真实 secret、pairing code logs、nonce replay accepted、scope bypass、raw fallback | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR020-S04-T1 | 设计 | `trading/qmt_auth.py` | 定义 pairing、HMAC、allowlist、scope、nonce contract |
| CR020-S04-T2 | 设计 | `trading/qmt_redaction.py` | 定义敏感字段和 raw fallback 禁止策略 |
| CR020-S04-T3 | 设计 | `tests/test_cr020_hmac_pairing_allowlist_scope.py` | 设计 auth fail、replay、scope、redaction tests |
| CR020-S04-T4 | 约束 | `trading/qmt_endpoint_matrix.py` | 标记 `qmt:positions:read` scope |
| CR020-S04-T5 | 门控 | CP5 / CP7 | 鉴权通过不等于交易或账户写入授权 |

## 验证上下文（validation_context）

**验证入口**：后续 LLD 可建议 `uv run --python 3.11 pytest -q tests/test_cr020_hmac_pairing_allowlist_scope.py`，但本阶段不执行。

**验证方式**：fixture-only HMAC、nonce、scope、allowlist 和 redaction tests；不得使用真实 secret。

**依赖环境**：不依赖真实 gateway、QMT、MiniQMT、XtQuant 或 `.env`。

**关键验证场景**：

| 场景 | 预期 |
|---|---|
| HMAC missing/mismatch/expired | adapter_call=0 |
| nonce replay | adapter_call=0 |
| scope 不足 | `query_positions` blocked |
| redaction 失败 | 不输出 raw |

## 量化验收标准（acceptance_criteria）

- [ ] HMAC 缺失、错误、过期、nonce replay、allowlist 不匹配、scope 不足时 adapter_call 为 0。
- [ ] no-auth 默认启用次数为 0。
- [ ] secret、pairing code、token、session、账号泄露次数为 0。
- [ ] redaction fallback-to-raw 次数为 0。
- [ ] HMAC pass 被解释为交易 / 账户写入授权的次数为 0。

## 阻塞说明

CP5 前不得实现；任何 no-auth 默认、真实 secret 记录、scope bypass 或真实操作请求都必须回退到 meta-po 门控。

## 实现状态回写

| 字段 | 内容 |
|---|---|
| 状态 | `verified-fixture-static-pending-manual-validation` |
| CP5 | `checkpoints/CP5-CR020-QMT-GATEWAY-READONLY-LLD-BATCH.md`，用户于 2026-06-05T08:25:46+08:00 approved |
| LLD | `process/stories/CR020-S04-hmac-pairing-allowlist-scope-LLD.md`，`confirmed=true` |
| CP6 | `process/checks/CP6-CR020-S04-hmac-pairing-allowlist-scope-CODING-DONE.md`，结论 `PASS` |
| 实现文件 | `trading/qmt_auth.py`、`trading/qmt_redaction.py`、`tests/test_cr020_hmac_pairing_allowlist_scope.py` |
| 验证入口 | `uv run --python 3.11 pytest -q tests/test_cr020_hmac_pairing_allowlist_scope.py tests/test_cr019_qmt_pairing_hmac_auth.py`；`uv run --python 3.11 pytest -q tests/test_cr019_qmt_gateway_run_gates.py` |
| 仍不授权 | 真实 `.env` 读取、gateway 启动、端口绑定、QMT / MiniQMT / XtQuant 连接、真实查询、交易、账户写入、simulation/live、provider/lake/publish |
