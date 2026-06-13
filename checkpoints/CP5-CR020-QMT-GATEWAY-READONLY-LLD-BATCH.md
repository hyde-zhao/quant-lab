---
checkpoint_id: "CP5"
checkpoint_name: "CR-020 QMT Gateway Readonly 全量 LLD 批次人工审查"
type: "batch_auto_then_manual"
status: "approved"
owner: "meta-po"
created_at: "2026-06-05T08:04:08+08:00"
reviewed_by: "user"
reviewed_at: "2026-06-05T08:25:46+08:00"
auto_check_result: "process/checks/CP5-CR020-S01-windows-gateway-runtime-admission-LLD-IMPLEMENTABILITY.md"
auto_final_authorization: false
target:
  phase: "story-planning"
  change_id: "CR-020"
  batch_id: "CR020-QMT-GATEWAY-READONLY-BATCH-A"
  artifacts:
    - "process/checks/CP4-CR020-STORY-PLAN-PRECHECK.md"
    - "process/stories/CR020-S01-windows-gateway-runtime-admission-LLD.md"
    - "process/stories/CR020-S02-server-qmt-login-session-LLD.md"
    - "process/stories/CR020-S03-linux-client-rest-transport-LLD.md"
    - "process/stories/CR020-S04-hmac-pairing-allowlist-scope-LLD.md"
    - "process/stories/CR020-S05-query-positions-readonly-LLD.md"
    - "process/stories/CR020-S06-docs-runbook-cp7-real-machine-validation-LLD.md"
---

# CP5 CR-020 QMT Gateway Readonly 全量 LLD 批次人工审查

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---:|---|
| `process/checks/CP4-CR020-STORY-PLAN-PRECHECK.md` | PASS | 0 | Story Plan 为 6 个 Story、4 个 Wave、1 个全量 LLD 批次；DAG 无环；CP5 前 `implementation_allowed=false`。 |
| `process/checks/CP5-CR020-S01-windows-gateway-runtime-admission-LLD-IMPLEMENTABILITY.md` | PASS | 0 | Windows S 端 gateway runtime / Typer CLI / lifecycle / runtime admission LLD 可实现；存在非阻断 `LCQ-CR020-S01-01`。 |
| `process/checks/CP5-CR020-S02-server-qmt-login-session-LLD-IMPLEMENTABILITY.md` | PASS | 0 | QMT login / session ready gate / `.env.example` placeholder / credential redaction LLD 可实现；存在非阻断 `OPEN-CR020-S02-01`。 |
| `process/checks/CP5-CR020-S03-linux-client-rest-transport-LLD-IMPLEMENTABILITY.md` | PASS | 0 | Linux C 端 Python REST client 与 Typer validation CLI LLD 可实现；无 OPEN。 |
| `process/checks/CP5-CR020-S04-hmac-pairing-allowlist-scope-LLD-IMPLEMENTABILITY.md` | PASS | 0 | HMAC / pairing / allowlist / scope / nonce / redaction fail-closed LLD 可实现；存在非阻断 `OPEN-CR020-S04-01`。 |
| `process/checks/CP5-CR020-S05-query-positions-readonly-LLD-IMPLEMENTABILITY.md` | PASS | 0 | `query_positions` 唯一只读 endpoint、scope=`qmt:positions:read`、redacted response LLD 可实现；存在非阻断 `OPEN-CR020-S05-01`。 |
| `process/checks/CP5-CR020-S06-docs-runbook-cp7-real-machine-validation-LLD-IMPLEMENTABILITY.md` | PASS | 0 | 文档 / runbook / CP7 实机只读验收边界 LLD 可实现；S06 无新增阻断项。 |

## Decision Brief

### 待人工决策清单

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣分析 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|---|
| DQ-CP5-CR020-01 | implementation | 是否批准 CR020-S01..S06 六份 LLD 作为后续受控实现输入。 | 批准全部 6 份 LLD；CP5 通过后允许进入 story-execution，并按 S01 -> S02/S03 -> S04 -> S05 -> S06 的依赖 / 文件 owner 顺序调度实现。 | A. 只批准 S01..S04，S05/S06 返工后再确认；B. 要求全部 LLD 返工后重新 CP5。 | 推荐方案一次冻结 Windows gateway、login/session、Linux REST client、HMAC/scope、query_positions 和 runbook 合同；分批批准风险更低但拖慢跨 Story 契约；全部返工最保守但重复消耗已通过预检。 | 影响 CR-020 能否进入实现、后续 dev_gate、文件合并顺序和 CP6/CP7 验证。 | 若实现或验证发现 LLD 合同错误，按 Story 回退到 LLD 修订并重跑对应 CP5 自动预检。 |
| DQ-CP5-CR020-02 | runtime_authorization | CP5 通过后授权边界是什么，是否允许真实运行或真实 QMT 连接。 | CP5 仅授权受控代码 / 文档实现和 fixture / static 验证输入；继续禁止 gateway 启动、端口绑定、真实 `.env` 读取、QMT / MiniQMT / XtQuant 连接、真实 `query_positions`、交易、账户写入、simulation/live、provider/lake/publish。 | A. 仅批准 LLD，不进入实现；B. 同时授权 Windows gateway / QMT readonly smoke。 | 推荐方案能推进实现且保持权限最小；只批准 LLD 会停在设计；真实 smoke 可更早暴露实机问题但需要主机、端口、凭据、日志脱敏和回滚授权。 | 影响安全、运行权限、凭据边界和 CP6/CP7 调度；误读 CP5 为运行授权会造成高风险。 | 如需真实运行，必须由 meta-po / meta-qa 在 CP6/CP7 阶段单独发起 per-run authorization。 |
| DQ-CP5-CR020-03 | implementation | 如何处理 Typer CLI 依赖尚未落地的问题。 | 接受 S01 推荐：实现可静态测试的 command matrix + optional Typer adapter；Typer 缺失时 fail-closed 为 `typer_dependency_missing`。本 CP5 不改 `pyproject.toml` / `uv.lock`。 | A. 本 CP5 同时授权修改依赖加入 Typer；B. 切换 argparse 以避免 CLI 依赖。 | 推荐方案符合依赖最小化和双端 Typer 设计意图；直接加依赖交付更完整但扩大变更面；argparse 零依赖但偏离 CP2/CP3 口径。 | 影响 S 端 Windows CLI、C 端 Linux 验收 CLI、文档命令、安装说明和 CP7 验证。 | Typer 不兼容时回退 CP5 改 Click 或 argparse；依赖组可接受时另行授权依赖更新。 |
| DQ-CP5-CR020-04 | risk_acceptance | 如何接受 QMT login/session 与 query_positions 原始字段仍需 CP7 Windows 实机确认的不确定性。 | 接受 adapter protocol + fixture-only gate：S02 冻结 login/session ready 协议，S05 冻结 `query_positions` redacted summary schema；真实 API、ready/expiry 信号和 raw payload 字段在 CP7 Windows 实机只读授权下确认。 | A. CP5 前先做 Windows 实机 Spike；B. 收窄 CR-020 为 health/login only。 | 推荐方案保持当前无真实运行边界且可推进实现；Spike 更早验证事实但需要运行授权和凭据；health/login only 风险低但不满足首个查询接口目标。 | 影响 S02 session adapter、S05 response schema、CP7 验证计划和回修成本。 | CP7 发现 API 不稳定、ready 不可判定或 payload 无法脱敏时，回退对应 Story 修订，必要时转 Spike。 |
| DQ-CP5-CR020-05 | security | 是否接受 nonce replay store 第一版为进程内 TTL，不覆盖多进程持久防重放。 | 接受 S04 推荐：第一版使用单 gateway 进程内 TTL replay store；多进程 / 多实例 gateway 或更强防重放需求另起 CR 或回到 CP5 修改 LLD。 | A. 本轮引入持久 nonce store；B. 仅校验 timestamp 不记录 nonce。 | 推荐方案简单、安全边界清晰且不新增依赖；持久 store 更强但扩大实现和运维复杂度；只校验 timestamp 简单但 replay 防护不足。 | 影响 HMAC 安全、并发模型、测试和未来多实例部署。 | 若 CP7 要求多进程 gateway、多人跨网段访问、live endpoint 默认启用或 replay 测试证明不足，则转新 CR 或 CP5 返工。 |
| DQ-CP5-CR020-06 | risk_acceptance | 是否接受 S06 文档 / CP7 evidence 边界：文档只描述运行前置和验收边界，不形成运行授权。 | 接受 S06 推荐：文档实现只写 placeholder、redaction、no-real-operation、不授权表和 CP7 evidence schema；CP7 evidence 仅允许 `query_positions` / `qmt:positions:read` 的脱敏只读证据，真实运行授权后续独立发起。 | A. 文档只写离线实现，不写 CP7 实机章节；B. 文档同时写入真实运行命令和授权模板。 | 推荐方案可让用户准备 Windows / Linux 操作步骤但不越权；只写离线实现会缺少实机验收衔接；写真实运行命令更完整但容易被误读为已授权。 | 影响 docs、CP7 证据、用户操作安全和审计。 | 若用户要求暂不出现实机章节，S06 实现收窄为离线文档；若需要真实运行命令，必须配套 per-run authorization 模板和不授权边界。 |

| 字段 | 内容 |
|---|---|
| 推荐决策 | `approve`：批准 CR020-S01..S06 六份 LLD，接受 DQ-CP5-CR020-01..06 推荐方案，进入受控 story-execution；仍不授权任何真实运行或交易。 |
| 备选方案 | `修改: <具体修改点>`：指定 DQ 或 Story 返工；`reject`：拒绝本批 LLD，停留在 story-planning。 |
| 影响维度 | 用户价值、实现复杂度、可验证性、维护成本、Windows / Linux 平台兼容、安全 / 权限、交付影响。 |
| 优劣分析 | 推荐方案推进最小只读闭环且权限最小；分批或返工降低局部风险但推迟端到端联通；真实 smoke 前置暴露事实更早但运行风险最高。 |
| 风险与回退 | 风险等级 high。接受条件是 CP5 只批准 LLD 和受控实现输入，不授权真实 QMT / 凭据 / 交易。回退方式为按 Story 回退 LLD / CP5，或将实机不确定性转 Spike。 |
| 用户需决策事项 | DQ-CP5-CR020-01、DQ-CP5-CR020-02、DQ-CP5-CR020-03、DQ-CP5-CR020-04、DQ-CP5-CR020-05、DQ-CP5-CR020-06。 |

### CP5 追加 Decision Brief 字段

| 字段 | 内容 |
|---|---|
| LLD clarification queue 收敛状态 | 阻断项为 0；所有 `blocks_lld=true` 未回答项为 0；S01/S02/S04/S05 非阻断 OPEN 已状态化。 |
| 已回答问题 | CP2 / CP3 已批准 S/C Typer CLI、Python REST runtime、`.env` 本地未跟踪、`query_positions` 首个只读接口、pairing_hmac / allowlist / scope / redaction fail-closed。 |
| 转 OPEN / Spike 的问题 | `LCQ-CR020-S01-01` Typer optional adapter；`OPEN-CR020-S02-01` QMT login/ready/expiry 实机信号；`OPEN-CR020-S04-01` nonce 进程内 TTL；`OPEN-CR020-S05-01` `query_positions` raw payload 字段。 |
| 未回答阻断项为 0 的证据 | 6 个 Story 级 CP5 自动预检均 PASS，S06 CP5 明确 `blocking_open_items=0`，各 LLD frontmatter `confirmed=false` 且 `status=ready-for-review`。 |
| 跨 Story 契约 | S01 gateway runtime / Typer / runtime admission；S02 credential_ref / session ready；S03 Python REST client + C 端 Typer validation CLI；S04 HMAC / allowlist / scope / redaction；S05 `query_positions` only；S06 docs / CP7 evidence boundary。 |
| 文件 owner / merge order | 实现推荐顺序：S01 -> S02/S03 -> S04 -> S05 -> S06。共享文件按 Story owner 串行合并；`trading/qmt_client.py` 由 S03/S05 顺序处理，auth/redaction 由 S04 owner，docs 由 S06 owner。 |
| CP4 摘要 | CP4 PASS；DAG 单向无环；CP5 前 `implementation_allowed=false`；CP4 的文件 owner、DAG、禁止项全部纳入本 Decision Brief。 |

## 不授权项

如果你回复 `approve`，只表示接受上面 6 项推荐方案，不表示授权以下 12 项禁止操作：

- 不授权启动 gateway、绑定端口、打开 socket 或启动 Windows 服务进程。
- 不授权读取真实 `.env`、`.env.*`、账号、密码、token、session、交易密码、私钥或任何未脱敏凭据。
- 不授权连接 QMT / MiniQMT / XtQuant，或执行真实 `query_positions`。
- 不授权发单、撤单、改单、账户写入或任何 broker 写操作。
- 不授权 simulation、live-readonly、small-live、scale-up 或任何真实交易准入。
- 不授权 provider fetch、真实联网补数、真实 lake write、broker lake write、catalog publish / current pointer publish 或 reports overwrite。
- 不授权把 `query_positions` 以外的真实 QMT 查询接口纳入默认白名单。
- 不授权把 CP5 通过解释为 CP6 / CP7 / CP8 自动通过或 CR 自动关闭。
- 不授权把真实账号、密码、token、session、交易密码、私钥写入 Git、对话、日志、检查点、memory 或入库文档。
- 不授权修改 `pyproject.toml` / `uv.lock` 或安装依赖；依赖变更仍需后续明确门禁。
- 不授权把 C 端 Typer CLI 配对 / 验收命令误当成实际业务 runtime，业务 runtime 仍是 Python REST client。
- 不授权启动 CR-021..CR-024 或扩大到 simulation / live 路线。

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| CP4 自动预检通过 | 待审查 | `process/checks/CP4-CR020-STORY-PLAN-PRECHECK.md` | CP4 结论 PASS。 |
| 六份 Story LLD 均存在 | 待审查 | `process/stories/CR020-S01...LLD.md` 至 `CR020-S06...LLD.md` | 六份均 `status=ready-for-review`、`confirmed=false`。 |
| 六份 CP5 自动预检均 PASS | 待审查 | `process/checks/CP5-CR020-S0*-...-IMPLEMENTABILITY.md` | 六份均 PASS。 |
| clarification 阻断项为 0 | 待审查 | S06 CP5、STATE CP5 open items | 非阻断 OPEN 为 4；阻断 OPEN 为 0。 |
| 真实运行边界关闭 | 待审查 | 各 LLD / CP5 No-Real-Operation 声明 | 当前未授权实现、运行、QMT 连接或凭据读取。 |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| 1 | LLD 覆盖 Story AC | 待审查 | 六份 LLD §2 / §10 / §14 | 每个 Story AC 均映射到设计与测试。 |
| 2 | 与 HLD / ADR 一致 | 待审查 | HLD §36、ADR-087..093 | 未违背 CP3 已批准架构。 |
| 3 | 文件影响范围明确 | 待审查 | 六份 LLD §4 / §11 | primary/shared/forbidden 与 Story 卡一致。 |
| 4 | 接口契约完整 | 待审查 | 六份 LLD §6 | CLI、REST、session、auth、endpoint、docs 接口均定义。 |
| 5 | 数据结构明确 | 待审查 | 六份 LLD §5 | credential_ref、session、HMAC、positions response、CP7 evidence 均有 schema。 |
| 6 | 控制流明确 | 待审查 | 六份 LLD §7 / §8 | 失败路径均 fail-closed。 |
| 7 | 依赖输入明确 | 待审查 | CP4 DAG、六份 LLD depends_on | S01 -> S02/S03 -> S04 -> S05 -> S06。 |
| 8 | 并发和一致性考虑 | 待审查 | CP4 file owner、S04 nonce OPEN | 多实例 nonce 为非阻断风险；实现串行合并共享文件。 |
| 9 | 安全设计明确 | 待审查 | S02/S04/S05/S06 LLD | 凭据、HMAC、allowlist、scope、redaction、no-order safety 均覆盖。 |
| 10 | 可测试性明确 | 待审查 | 六份 LLD §10 | 后续测试入口均为 fixture/static；CP7 实机另行授权。 |
| 11 | dev_gate 可计算 | 待审查 | Story 卡与 LLD §14 | CP5 approve 后仍需依赖、文件 owner、运行授权重新判定。 |
| 12 | 偏差记录机制明确 | 待审查 | 六份 LLD §11 / §13 | 实现偏离需记录并回修。 |
| 13 | CP4 摘要已纳入 | 待审查 | 本文件 Decision Brief | DAG、并行安全、文件 owner、OPEN 已汇总。 |
| 14 | clarification 队列已收敛 | 待审查 | 本文件 Decision Brief | 阻断项 0，非阻断 OPEN 4。 |
| 15 | Agent Dispatch Evidence 完整 | 待审查 | 六个 handoff + STATE agent_lifecycle | S01..S06 均由真实 `spawn_agent` 子 agent 完成并关闭。 |
| 16 | 不授权边界明确 | 待审查 | 本文件“不授权项” | CP5 approve 不授权运行、QMT、凭据、交易、publish 或依赖变更。 |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| 自动预检通过 | 待审查 | 六份 CP5 自动预检 PASS | 无阻断 FAIL。 |
| clarification 队列收敛 | 待审查 | 本文件 Decision Brief | `blocks_lld=true` 未回答项为 0。 |
| 人工确认完成 | 待审查 | 本文件“人工审查结果” | 等待用户 `approve` / `修改: ...` / `reject`。 |
| dev_gate 可更新 | 待审查 | STATE / Story 卡 / LLD | 用户 approve 后可将六份 LLD 标记 confirmed，并进入受控 story-execution。 |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| CP4 自动预检 | `process/checks/CP4-CR020-STORY-PLAN-PRECHECK.md` | 待审查 | PASS。 |
| S01 LLD | `process/stories/CR020-S01-windows-gateway-runtime-admission-LLD.md` | 待审查 | ready-for-review。 |
| S02 LLD | `process/stories/CR020-S02-server-qmt-login-session-LLD.md` | 待审查 | ready-for-review。 |
| S03 LLD | `process/stories/CR020-S03-linux-client-rest-transport-LLD.md` | 待审查 | ready-for-review。 |
| S04 LLD | `process/stories/CR020-S04-hmac-pairing-allowlist-scope-LLD.md` | 待审查 | ready-for-review。 |
| S05 LLD | `process/stories/CR020-S05-query-positions-readonly-LLD.md` | 待审查 | ready-for-review。 |
| S06 LLD | `process/stories/CR020-S06-docs-runbook-cp7-real-machine-validation-LLD.md` | 待审查 | ready-for-review。 |
| S01..S06 CP5 自动预检 | `process/checks/CP5-CR020-S0*-*-LLD-IMPLEMENTABILITY.md` | 待审查 | 六份均 PASS。 |
| CP5 人工审查稿 | `checkpoints/CP5-CR020-QMT-GATEWAY-READONLY-LLD-BATCH.md` | 待审查 | 当前文件。 |

## 人工审查结果

- 结论：`approved`
- 审查人：user
- 审查时间：2026-06-05T08:25:46+08:00
- 用户回复：`@meta-po，你需要完成所有代码开发。我手动安装到Windows电脑后，使用cli手动验证qmt接口是否可用。你需要写完善的手动安装调试手册`
- 修改意见：接受 DQ-CP5-CR020-01..06 推荐方案；补充执行要求为由 meta-po 组织完成 CR-020 全部代码开发与手动安装调试手册，Windows 实机安装和 QMT CLI 验证由用户手动执行。
- 风险接受项：接受 Typer optional adapter / no dependency change、QMT login/session 与 `query_positions` raw payload 字段需 CP7 Windows 实机确认、nonce 第一版进程内 TTL、文档不形成运行授权。CP5 approved 仍不授权 meta-po / 子 agent 启动 gateway、绑定端口、读取真实 `.env`、连接 QMT / MiniQMT / XtQuant、执行真实 `query_positions`、交易、账户写入、simulation/live、provider/lake/publish 或输出任何未脱敏凭据 / 持仓。
