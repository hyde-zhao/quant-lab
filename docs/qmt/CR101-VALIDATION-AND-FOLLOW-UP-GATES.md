# CR101 Validation and Follow-Up Gates

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| v0.1 | 2026-06-20 | host-orchestrator | 首版 S04 收口文档，记录 CR101 离线验证矩阵、READY_WITH_RISK 条件和后续授权 gate。 |

## 1. 当前支持范围

| 范围 | 当前结论 | 证据 |
|---|---|---|
| QMT direct-run package contract | offline contract ready | `process/checks/CP7-CR101-S01-target-taxonomy-manifest-contract-VERIFICATION-DONE.md` |
| CR101 fake package exchange checker | offline checker ready | `process/checks/CP7-CR101-S02-package-checker-fixture-fail-closed-VERIFICATION-DONE.md` |
| MiniQMT readonly adapter contract | offline adapter/evidence contract ready | `process/checks/CP7-CR101-S03-runner-adapter-evidence-boundary-VERIFICATION-DONE.md` |
| Evidence redaction and forbidden counters | offline guardrail ready | `tests/test_cr091_strategy_runner_contracts.py`、`tests/test_cr098_runner_readonly_integration.py` |

当前支持范围只表示本地离线 contract、fixture、checker、adapter metadata 和 evidence summary 已通过测试。它不表示真实 QMT、MiniQMT gateway、NAS、账户或交易链路 ready。

## 2. 当前不支持 / 不授权范围

| 范围 | 状态 | 说明 |
|---|---|---|
| 真实 QMT direct-run proof | not-authorized | 未启动 QMT terminal，未加载策略，未读取 runtime log。 |
| 真实 MiniQMT gateway proof | not-authorized | 未连接 gateway，未查询真实账户、资金、持仓、委托或成交。 |
| 真实 NAS package exchange | not-authorized | 未 list/read/write/copy/publish/pull/delete/mount NAS。 |
| order-write / submit-cancel | not-authorized | 未 submit/cancel/buy/sell，未 simulation/live。 |
| 凭据与环境文件 | not-authorized | 未读取 `.env`、token、secret、HMAC key、cookie、session 或账号凭据。 |
| provider/lake/catalog publish | not-authorized | 未 provider fetch、lake write 或 catalog publish。 |

## 3. 离线验证矩阵

| 验证 ID | 验证对象 | 验证方式 | 通过标准 | 当前证据 |
|---|---|---|---|---|
| CR101-VM-01 | manifest target taxonomy | unit tests | implemented delivery target 数量为 1，且为 `qmt_terminal_direct` | `test_cr101_manifest_accepts_qmt_direct_target_and_miniqmt_readonly_adapter` |
| CR101-VM-02 | legacy target fail closed | unit tests | `miniqmt_runner` 作为 delivery target 被阻断 | `test_cr101_manifest_rejects_legacy_miniqmt_runner_delivery_target` |
| CR101-VM-03 | package checker fail closed | unit tests | schema / target / adapter / permission / checksum / path / sensitive / forbidden counter 均覆盖 | `tests/test_cr100_package_exchange.py` |
| CR101-VM-04 | adapter boundary | unit tests | unknown adapter 和 order-write capability 被阻断 | `tests/test_cr091_strategy_runner_contracts.py` |
| CR101-VM-05 | evidence boundary | unit tests | target / adapter / capabilities 写入 evidence，sensitive hits = 0 | `test_evidence_records_cr101_target_and_adapter_boundary` |
| CR101-VM-06 | readonly gateway no expansion | regression tests | order-like endpoint blocked，缺 authorization_ref 不发送请求 | `tests/test_cr098_runner_readonly_integration.py` |
| CR101-VM-07 | workflow consistency | meta-flow checks | CR tracking OK，workspace process link OK | `meta-flow check cr-tracking`、`meta-flow workspace check` |

## 4. 后续 Gate

| Gate ID | 决策类型 | 候选目标 | 启动前置 | 当前状态 |
|---|---|---|---|---|
| QMT-DIRECT-RUN-VALIDATION-FU | runtime_authorization | 用户手工或单独授权证明 QMT terminal 可加载 CR101 package target | 独立 CP2/CP3/CP5，明确 runtime path、证据脱敏和禁止账号原文 | candidate-not-started |
| MINIQMT-GATEWAY-ADAPTER-VALIDATION-FU | runtime_authorization | 证明 quant-lab runner 通过 MiniQMT gateway adapter 完成 readonly health/capabilities/query_positions | 独立 per-run authorization；只读 endpoint allowlist；redacted evidence schema | candidate-not-started |
| NAS-REAL-EXCHANGE-FU | runtime_authorization | 证明真实 NAS package exchange path、权限和交换流程 | 独立 NAS gate；明确 read/write/publish/pull/copy/delete 是否允许 | candidate-not-started |
| ORDER-WRITE-SIMULATION-LIVE-FU | risk_acceptance | 设计 submit/cancel/order-write/simulation/live 的安全门 | S01-S04 完成；用户明确接受高风险设计门禁；默认不执行真实交易 | candidate-not-started |

这些 gate 不会因 CR101 CP8 approve 自动启动。每个 gate 都必须重新生成 Decision Brief，并独立打印授权项与不授权项。

## 5. CP8 READY_WITH_RISK 条件

CR101 CP8 可关闭为 `READY_WITH_RISK` 的条件：

- S01-S04 均 CP6 / CP7 PASS。
- `meta-flow check cr-tracking --project-root /home/hyde/workspace/quant-lab --strict-warnings` 通过。
- `meta-flow workspace check --project-root /home/hyde/workspace/quant-lab` 显示 `process_link_health: ok`。
- CP8 Decision Brief 明确列出真实 QMT / MiniQMT gateway / NAS / order-write 未授权且未验证。
- 后续 gate 保持 candidate-not-started，不自动启动。

若用户要求真实验证，则 CR101 不应直接按 READY_WITH_RISK 关闭，应先停在 CP8 前并另起 runtime_authorization CR。

## 6. Guardrail 检查词

CP7 / CP8 文档必须包含以下语义：

- `not-authorized`
- `READY_WITH_RISK`
- `QMT-DIRECT-RUN-VALIDATION-FU`
- `MINIQMT-GATEWAY-ADAPTER-VALIDATION-FU`
- `NAS-REAL-EXCHANGE-FU`
- `ORDER-WRITE-SIMULATION-LIVE-FU`

CP7 / CP8 文档不得声明：

- `real QMT ready`
- `real NAS ready`
- `live ready`
- `order-write authorized`
- `simulation authorized`
