---
checkpoint_id: "CP6"
checkpoint_name: "CR020-S04 HMAC pairing / allowlist / scope / nonce fail-closed 编码完成检查"
type: "rolling_auto"
status: "PASS"
owner: "meta-dev"
created_at: "2026-06-05T08:37:58+08:00"
checked_at: "2026-06-05T08:37:58+08:00"
target:
  phase: "story-execution"
  change_id: "CR-020"
  story_id: "CR020-S04-hmac-pairing-allowlist-scope"
  story_slug: "hmac-pairing-allowlist-scope"
  artifacts:
    - "trading/qmt_auth.py"
    - "trading/qmt_redaction.py"
    - "tests/test_cr020_hmac_pairing_allowlist_scope.py"
    - "process/stories/CR020-S04-hmac-pairing-allowlist-scope-LLD.md"
manual_checkpoint: "checkpoints/CP5-CR020-QMT-GATEWAY-READONLY-LLD-BATCH.md"
cp5_approved_at: "2026-06-05T08:25:46+08:00"
real_env_read_allowed: false
gateway_start_allowed: false
port_bind_allowed: false
qmt_operation_allowed: false
dependency_change_allowed: false
---

# CP6 CR020-S04 编码完成检查结果

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| Story LLD 已确认 | PASS | `process/stories/CR020-S04-hmac-pairing-allowlist-scope-LLD.md` frontmatter `confirmed=true` | CP5 全量 LLD 批次已由用户在 2026-06-05T08:25:46+08:00 approve。 |
| CP5 全量人工确认已通过 | PASS | `checkpoints/CP5-CR020-QMT-GATEWAY-READONLY-LLD-BATCH.md` status=`approved` | 接受 DQ-CP5-CR020-01..06 推荐方案；仍不授权真实运行。 |
| 文件 owner 可执行 | PASS | Story `file_ownership.primary` + 用户本轮指定主写入范围 | 仅修改 `trading/qmt_auth.py`、`trading/qmt_redaction.py`，创建 S04 测试；未修改 S01/S03/S05 shared runtime 文件。 |
| 禁止范围关闭 | PASS | 本文件 No-Real-Operation 声明 + 测试命令 | 未读取真实 `.env`，未启动 gateway，未绑定端口，未连接 QMT/MiniQMT/XtQuant，未发单 / 账户写入 / provider / lake / publish。 |
| 依赖不变 | PASS | `git diff -- pyproject.toml uv.lock` 无本 Story 变更 | 未修改 `pyproject.toml` / `uv.lock`。 |

## Checklist

| # | 检查项 | 状态 | 证据 | 处理意见 |
|---|---|---|---|---|
| 1 | `qmt_auth.py` 提供 request source context | PASS | `QmtRequestSourceContext`、`build_qmt_request_source_context` | 公开输出只包含 source hash/ref，不输出 raw source IP。 |
| 2 | allowlist decision fail-closed | PASS | `QmtAllowlistDecision`、`validate_qmt_allowlist`、S04 tests | source missing、mismatch、公网来源均 typed blocked。 |
| 3 | scope decision exact | PASS | `QmtScopeDecision`、`resolve_required_scope`、`validate_qmt_scope`、endpoint matrix 测试 | `query_positions` 固定 `qmt:positions:read`，scope 不足 blocked。 |
| 4 | nonce replay store | PASS | `QmtNonceReplayStore`、`QmtNonceDecision`、replay/TTL 测试 | 进程内 TTL store 不保存 raw nonce，重复 nonce 返回 `auth_nonce_replay`。 |
| 5 | S03-compatible HMAC header provider | PASS | `QmtHmacHeaderProvider`、`QmtHmacHeaderBuildResult`、provider no-env 测试 | provider 只使用显式参数，不读取 `.env` / 文件 / 环境；diagnostics 不输出 raw signature / secret。 |
| 6 | auth admission decision | PASS | `QmtAuthAdmissionDecision`、`evaluate_qmt_auth_admission` | allowlist -> HMAC -> scope -> optional redaction gate；失败时 adapter/QMT/trading flags 全 false。 |
| 7 | CR019 API 兼容 | PASS | `tests/test_cr019_qmt_pairing_hmac_auth.py` | 旧 pairing、HMAC、no-auth、redaction helper 测试通过。 |
| 8 | redaction response/error/diagnostics gate | PASS | `QmtRedactionDecision`、`redact_qmt_response_payload`、`redact_qmt_error_payload`、`redact_qmt_diagnostics_payload` | 结构化响应、错误、diagnostics 均先脱敏再输出。 |
| 9 | redaction failed 禁止 raw fallback | PASS | `test_redaction_failure_blocks_raw_fallback` | scanner 失败 / leak_count>0 时返回 blocked 摘要，不返回 raw payload。 |
| 10 | HMAC pass 不授权交易或账户写入 | PASS | `test_hmac_pass_identifies_caller_but_does_not_authorize_qmt_or_trading` | `adapter_call_allowed=false`、`qmt_api_call_allowed=false`、交易 / 账户写入 / simulation / live 均 false。 |
| 11 | fixture-only 测试 | PASS | S04 测试源码与运行命令 | 测试未读取 `.env`，未导入 XtQuant，未打开 socket，未连接 gateway/QMT。 |
| 12 | 格式与语法 | PASS | `py_compile`、`git diff --check` | 三个目标文件语法与 whitespace 检查通过。 |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 所有目标文件存在且非空 | PASS | `trading/qmt_auth.py`、`trading/qmt_redaction.py`、`tests/test_cr020_hmac_pairing_allowlist_scope.py` | S04 primary 产物已完成。 |
| 最小测试通过 | PASS | `uv run --python 3.11 pytest -q tests/test_cr020_hmac_pairing_allowlist_scope.py tests/test_cr019_qmt_pairing_hmac_auth.py` | 26 passed in 0.10s。 |
| 运行门控回归通过 | PASS | `uv run --python 3.11 pytest -q tests/test_cr019_qmt_gateway_run_gates.py` | 14 passed in 0.08s。 |
| 语法检查通过 | PASS | `uv run --python 3.11 python -m py_compile trading/qmt_auth.py trading/qmt_redaction.py tests/test_cr020_hmac_pairing_allowlist_scope.py` | 退出码 0。 |
| diff whitespace 检查通过 | PASS | `git diff --check -- trading/qmt_auth.py trading/qmt_redaction.py tests/test_cr020_hmac_pairing_allowlist_scope.py` | 退出码 0，无输出。 |
| Story 可交给 CP7 | PASS | 本 CP6 status=`PASS` | 等待 meta-po 路由 meta-qa 执行 CP7；不得由 meta-dev 直接标记 verified。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| Auth 合同实现 | `trading/qmt_auth.py` | PASS | CR020 S04 request source / allowlist / scope / nonce / HMAC provider / admission decision 已实现。 |
| Redaction gate 实现 | `trading/qmt_redaction.py` | PASS | response/error/diagnostics gate 与 raw fallback 禁止已实现。 |
| Fixture-only 测试 | `tests/test_cr020_hmac_pairing_allowlist_scope.py` | PASS | 覆盖 HMAC fail、allowlist、scope、nonce、redaction、provider no-env、no-auth、zero counters。 |
| CP6 编码完成检查 | `process/checks/CP6-CR020-S04-hmac-pairing-allowlist-scope-CODING-DONE.md` | PASS | 当前文件。 |
| DEV-LOG 记录 | `DEV-LOG.md` | PASS | 已追加 CR020-S04 实现摘要、测试结果和限制。 |
| Story 状态 | `process/stories/CR020-S04-hmac-pairing-allowlist-scope.md` | PASS | 已推进到 `ready-for-verification`。 |

## Agent Dispatch Evidence

| 字段 | 值 |
|---|---|
| role | `meta-dev` |
| dispatch_mode | `user-direct-codex-agent` |
| agent/thread | 当前 Codex 实现线程，用户直接指定“CR-020 的 meta-dev 实现子任务 C” |
| source_user_instruction_time | 2026-06-05 本轮用户消息 |
| cp5_manual_review | `checkpoints/CP5-CR020-QMT-GATEWAY-READONLY-LLD-BATCH.md` |
| lld_path | `process/stories/CR020-S04-hmac-pairing-allowlist-scope-LLD.md` |
| implementation_files | `trading/qmt_auth.py`; `trading/qmt_redaction.py`; `tests/test_cr020_hmac_pairing_allowlist_scope.py` |
| inline_fallback_used | `false` |
| real_gateway_started | `false` |
| real_env_read | `false` |
| qmt_connected | `false` |

## Validation Results

| 命令 | 结果 | 说明 |
|---|---|---|
| `uv run --python 3.11 pytest -q tests/test_cr020_hmac_pairing_allowlist_scope.py tests/test_cr019_qmt_pairing_hmac_auth.py` | PASS | 26 passed in 0.10s。 |
| `uv run --python 3.11 pytest -q tests/test_cr019_qmt_gateway_run_gates.py` | PASS | 14 passed in 0.08s。 |
| `uv run --python 3.11 python -m py_compile trading/qmt_auth.py trading/qmt_redaction.py tests/test_cr020_hmac_pairing_allowlist_scope.py` | PASS | 退出码 0。 |
| `git diff --check -- trading/qmt_auth.py trading/qmt_redaction.py tests/test_cr020_hmac_pairing_allowlist_scope.py` | PASS | 退出码 0，无输出。 |

## Forbidden Operation Counters

| 操作类别 | 状态 | 证据 |
|---|---|---|
| `.env` / credential read | PASS | provider no-env monkeypatch 测试；本轮未读取真实 `.env` / `.env.*`。 |
| gateway start / port bind / socket | PASS | 未执行 gateway 命令；测试只做 fixture / static / py_compile。 |
| QMT / MiniQMT / XtQuant | PASS | 未导入或连接；测试静态扫描无 `import xtquant` / `from xtquant`。 |
| trading / account write | PASS | auth/admission counters 全 0；HMAC pass 仍不授权交易或账户写入。 |
| provider/lake/publish | PASS | 未运行 provider、lake write、broker lake write、publish 或 current pointer publish。 |
| dependency change | PASS | 未修改 `pyproject.toml` / `uv.lock`。 |
| raw fallback | PASS | redaction failure 测试确认 blocked 摘要不包含 raw payload。 |

## 状态不一致记录

| 项 | 观察 | 处理 |
|---|---|---|
| Story 卡片初始状态 | 本轮读取时仍为 `planned-pending-cp5` / `implementation_allowed=false` | 用户本轮明确给出 CP5 approved，且 CP5 人工稿 status=`approved`；本 CP6 将 Story 推进到 `ready-for-verification`。 |
| ADR frontmatter | 聚合 ADR 文件顶层仍为 `confirmed=false` | S04 CP5 自动预检已记录 CR020 局部 ADR-091 / ADR-087..093 已由 CP3/CP5 批准；本轮未修改 ADR 文件。 |

## No-Real-Operation 声明

本轮只做代码合同和 fixture-only 测试。未读取真实 `.env` 或 `.env.*`，未启动 gateway，未绑定端口，未打开 socket，未连接 QMT / MiniQMT / XtQuant，未执行真实 `query_positions`，未发单、撤单、账户写入，未 provider/lake/publish，未修改依赖。

## 结论

- 结论：`PASS`
- 阻断项：0
- 豁免项：0
- OPEN / clarification：沿用 CP5 已接受的 `OPEN-CR020-S04-01`，nonce 第一版为进程内 TTL store，多进程 / 多实例持久防重放另起 CR 或回到 CP5 修订。
- 下一步：等待 meta-po 路由 meta-qa 执行 CR020-S04 CP7。CP7 失败时仅在 S04 原写入范围内回修并重新生成 CP6。
