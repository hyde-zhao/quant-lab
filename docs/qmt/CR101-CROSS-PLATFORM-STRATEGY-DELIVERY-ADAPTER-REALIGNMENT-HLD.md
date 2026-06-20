# CR101 Cross-Platform Strategy Delivery and Adapter Layer Realignment HLD

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| v0.1 | 2026-06-20 | host-orchestrator | 首版 HLD，冻结 cross-platform target taxonomy、runner adapter protocol、manifest/checker/evidence 双边界和不授权运行边界。 |
| v0.2 | 2026-06-20 | host-orchestrator | 补充 S01-S03 离线实现/验证落地命名、S04 validation/follow-up gate 收口和 READY_WITH_RISK 边界。 |

## 1. 问题定义

CR091 已交付 quant-lab 侧 strategy runner 的离线合同；CR098 将 runner 到 readonly gateway 的 facade 明确为 adapter；CR100 交付了本地 fake package exchange readiness。但历史包结构和 manifest 仍残留 `miniqmt_runner` 作为策略运行 target 的表达，容易把 MiniQMT 误读为 runner 宿主。

CR101 的目标是把两条架构线重新对齐：

- 策略交付按跨平台 `delivery_targets[]` 建模；当前唯一 implemented target 是 `qmt_terminal_direct`。
- `trading.strategy_runner` 是 quant-lab 侧 runner；MiniQMT 只是当前 broker / execution adapter target，不承载策略运行职责。
- manifest、checker、fixture、package layout 和 evidence 从历史 `miniqmt_runner` 默认假设改为 target + adapter 双边界。
- 本轮只做设计、schema、fixture、checker 和本地离线包结构重对齐；不访问真实 NAS、不读凭据、不启动 runtime、不交易、不 publish。

## 2. Architecture Gray Areas

| 灰区 ID | 问题 | 结论 |
|---|---|---|
| AGA-CR101-01 | target taxonomy 应该是 QMT 专用还是跨平台？ | 采用跨平台 taxonomy，但 CP6 只实现 `qmt_terminal_direct`。 |
| AGA-CR101-02 | MiniQMT 是 runner host 还是 adapter target？ | MiniQMT 固定为 gateway / broker adapter target，不是 runner host。 |
| AGA-CR101-03 | manifest / checker 应该围绕 `miniqmt_runner` 还是 target + adapter？ | 改为 target + adapter 双边界，历史字段进入迁移风险。 |
| AGA-CR101-04 | evidence 是否可引用真实 runtime？ | 默认只允许离线 redacted evidence；真实 runtime evidence 需后续逐 run gate。 |

### Advisor Table

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| A. Cross-platform target taxonomy + QMT direct-run current target | 解除 `miniqmt_runner` 混淆；保留 Goldminer / generic future slot；当前实现范围可控 | 需要改 manifest、checker、fixture 和 HLD 追溯 | package manifest、checker、strategy package layout、docs/qmt、tests | 推荐 | 假设当前可离线定义 QMT direct-run entrypoint；若 QMT target 无法稳定建模，切到 Spike。 |
| B. QMT / MiniQMT 双 target taxonomy | 贴近历史字段，迁移量较小 | 继续把 MiniQMT 误读为策略运行宿主；验证矩阵膨胀 | manifest、runner、adapter、runtime authorization | 不推荐 | 仅当未来明确要在 MiniQMT host 内运行策略，另起 architecture CR。 |
| C. 抽象-only taxonomy，不实现当前 target | 权限最小，代码变更少 | 无法解除 CR089 / order-write 阻塞；缺少可验证包结构 | docs、process、future CR | 不推荐 | 仅当用户要求暂停所有实现，只保留文档勘误。 |
| D. MiniQMT-hosted runner | 与部分历史命名一致 | 与 CR091/CR098 runner-owned 边界冲突；容易触发 runtime / credential / account 风险 | runner、gateway、credential、runtime、trading safety | 禁止本轮采用 | 需要真实平台宿主和独立 runtime authorization 才能重新评估。 |

## 3. 候选架构方案

| 方案 | 描述 | 优点 | 代价 / 风险 | 结论 |
|---|---|---|---|---|
| A. Target + Adapter 双边界重对齐 | `delivery_targets[]` 定义策略交付 target；`execution_adapters[]` 定义 runner 到 broker/gateway 的 adapter。当前 target 为 `qmt_terminal_direct`，当前 adapter 为 `miniqmt_gateway_readonly` contract。 | 职责最清晰；能保留 future target；不把设计批准解释为 runtime 授权 | 需要迁移 CR100 的 `miniqmt_runner` 字段和 checker | 推荐 |
| B. QMT direct-run 单目标固化 | 只保留 QMT direct-run，不设计 future slot。 | 实现最窄 | 很快再次遇到 Goldminer / generic Python 扩展问题 | 不推荐 |
| C. 沿用 CR100 `qmt_terminal + miniqmt_runner` | 变更小 | 继续制造 runner host 混淆；与 baseline 冲突 | 不推荐 |
| D. 只写文档，不改 schema/checker | 风险低 | 不能让 CP5/CP6 得到可执行验收对象 | 不推荐 |

推荐方案：A。

## 4. 推荐架构

```text
Strategy Package
  manifest.yaml
    delivery_targets[]
      - id: qmt_terminal_direct
        implemented: true
        entrypoint: targets/qmt_terminal_direct/entry.py
    execution_adapters[]
      - id: miniqmt_gateway_readonly
        implemented: contract_only
        owner: trading.strategy_runner.readonly_gateway
    permissions: all runtime / credential / trade / NAS / publish flags false
        |
        v
Package Loader / Checker
  - schema + checksum + permission fail-closed
  - target entrypoint boundary
  - adapter contract boundary
  - sensitive filename / evidence scan
        |
        v
quant-lab Strategy Runner
  - AdapterRegistry
  - TargetPortfolioSnapshot
  - ReadonlyGatewayClient facade
  - EvidenceSummary
        |
        v
Offline Evidence
  - fake transport only by default
  - forbidden_operation_counters all zero
  - not_authorization=true
```

## 5. 模块职责

| 模块 / 对象 | 职责 | 禁止职责 |
|---|---|---|
| `delivery_targets[]` | 声明策略包可交付的运行形态；当前实现 `qmt_terminal_direct`。 | 不承诺真实 QMT 已运行；不声明 MiniQMT runner host。 |
| `execution_adapters[]` | 声明 runner 到 broker / gateway 的 adapter contract；当前 MiniQMT 仅为 readonly gateway adapter contract。 | 不承载策略运行；不授权 submit / cancel。 |
| `trading.strategy_runner.adapters` | 保持策略输入到 `TargetPortfolioSnapshot` / `OrderIntentDraftResult` 的 broker-neutral 转换。 | 不 import XtQuant；不读取 `.env`；不访问 NAS。 |
| `trading.strategy_runner.readonly_gateway` | 维持 health / capabilities / query_positions allowlist 和 fake default。 | 不启动 gateway；不隐式读取 HMAC env。 |
| `trading.strategy_runner.package_loader` | 继续 fail-closed 校验 manifest、checksum、permission false flags。 | 不从 NAS 读取；不 publish；不覆盖 immutable cache。 |
| `trading.strategy_runner.package_exchange` | 后续从 CR100 fake exchange manifest 迁移到 CR101 target taxonomy。 | 不把 fake exchange 当真实 NAS。 |
| `trading.strategy_runner.evidence` | 输出 redacted evidence summary，合并 forbidden counters。 | 不输出 token、secret、account、raw positions、raw orders、qmt logs。 |
| checker / fixture | 验证 target + adapter 双边界、负向用例和敏感词扫描。 | 不连接真实 QMT / MiniQMT / gateway。 |

## 6. 集成契约

| 调用方向 | 调用时机 | 输入契约 | 输出契约 | 降级策略 | 调用方需同步修改 |
|---|---|---|---|---|---|
| strategy package -> package checker | CP6 离线包生成后 | `manifest.yaml`，含 `delivery_targets[]`、`execution_adapters[]`、checksum、permission false flags | PASS / blocked reason、checked file list、forbidden counters | schema / checksum / permission / sensitive scan 任一失败则 fail closed | package generator、tests、docs/qmt smoke guide |
| package checker -> package loader | checker PASS 后 | 本地 package root；无 NAS path；无 `.env` | `StrategyPackage.to_adapter_payload()` 或 blocked | 缺 payload / checksum mismatch / path escape 阻断 | `package_loader` schema 常量和 fixture |
| runner -> adapter protocol | runner intake | strategy payload、run_id、target taxonomy refs | `AdapterResult`、`TargetPortfolioSnapshot`、order intent drafts | unknown adapter 或 forbidden operation 非 0 阻断 | adapter registry tests |
| runner -> MiniQMT gateway adapter | CP6/CP7 默认离线；真实只读另起 gate | `ReadonlyGatewayClient` fake transport；future real transport 需 explicit authorization_ref | redacted readonly summary | runtime_config 缺失或 endpoint 不在 allowlist 则 blocked | CR098 follow-up / runtime authorization docs |
| evidence -> CP7 / CP8 | 每次离线验证结束 | adapter result、readonly result、target id、adapter id、forbidden counters | `EvidenceSummary` with `not_authorization=true` | redaction failed 或 forbidden counters 非 0 阻断 | CP7 report、CP8 READY_WITH_RISK 风险项 |

## 7. 非功能与可量化成功标准

| ID | 标准 | 可验证阈值 |
|---|---|---|
| SC-CR101-01 | 当前 implemented target 固定 | `delivery_targets[]` 中 `implemented=true` 的 target 数量等于 1，且 id 等于 `qmt_terminal_direct`。 |
| SC-CR101-02 | future target 只保留扩展位 | future / deferred target 可出现 2 个 schema slot；implemented flag 必须为 false。 |
| SC-CR101-03 | runner 与 runtime 解耦 | strategy runner core 对 `xtquant` / QMT SDK 的直接 import 数量等于 0。 |
| SC-CR101-04 | MiniQMT 不再是 runner host | 新 manifest / fixture 中 `miniqmt_runner` 作为 delivery target 的出现次数等于 0。 |
| SC-CR101-05 | fail-closed 覆盖 | checker 至少覆盖 8 类失败：schema、target missing、adapter missing、permission nonfalse、checksum、path escape、sensitive filename、forbidden counter。 |
| SC-CR101-06 | 不授权边界可审计 | NAS / credential / account / runtime / submit_cancel / simulation_live / publish 计数全部等于 0。 |
| SC-CR101-07 | evidence 脱敏 | evidence 中 token、secret、password、account、raw_positions、raw_orders、qmt_log 命中数量等于 0。 |

## 8. Use Case -> Architecture Traceability

| Use Case / 场景 | 架构对象 | 异常路径 | 验证方式 |
|---|---|---|---|
| UC-CR101-01 离线生成 QMT direct-run 策略包 | `delivery_targets[].id=qmt_terminal_direct`、entrypoint | target 缺失 / entrypoint 越界 -> blocked | manifest checker + fixture |
| UC-CR101-02 runner 消费策略包并产出目标组合 | `PackageLoader`、`AdapterRegistry`、`TargetPortfolioSnapshot` | unknown adapter / forbidden count 非 0 -> blocked | unit tests |
| UC-CR101-03 MiniQMT 只作为 readonly gateway adapter | `execution_adapters[]`、`ReadonlyGatewayClient` | endpoint 非 allowlist / runtime 未授权 -> blocked | CR098 regression |
| UC-CR101-04 fake exchange 离线包流转 | CR100 fake root + CR101 manifest bridge | 缺 marker / permission nonfalse -> blocked | package exchange tests |
| UC-CR101-05 后续 Goldminer / generic target | future target schema slot | 用户要求实现 -> new CR | follow-up tracking |

## 9. 关键场景模拟

| 场景 | 输入 | 推荐架构路径 | 预期结果 |
|---|---|---|---|
| SIM-CR101-01 QMT direct-run package pass | 本地 package root，target=`qmt_terminal_direct`，permissions 全 false | checker -> loader -> adapter -> evidence | PASS，`not_authorization=true`，forbidden counters 全 0。 |
| SIM-CR101-02 历史 `miniqmt_runner` target | manifest 仍声明 `miniqmt_runner` delivery target | checker target taxonomy validation | blocked，提示迁移为 `execution_adapters[].id=miniqmt_gateway_readonly`。 |
| SIM-CR101-03 未授权真实 gateway | runner 传入 real transport 但无 `authorization_ref` | `ReadonlyGatewayClient._call_qmt_client` | blocked_runtime_authorization_missing，不打开默认 runtime。 |
| SIM-CR101-04 evidence 含敏感字段 | evidence 或 payload 出现 token / account / raw positions | `assert_redacted` | blocked_redaction_failed。 |

## 10. 风险矩阵

| 风险 ID | 风险 | 等级 | 缓解 | 回退 / 切换条件 |
|---|---|---|---|---|
| R-CR101-01 | 历史 CR100 `miniqmt_runner` 字段被下游继续消费 | HIGH | CP5 明确迁移 schema 和 negative tests；HLD 把该字段列为 banned delivery target | 若影响面超出本轮，拆成 manifest migration 子 CR。 |
| R-CR101-02 | QMT direct-run 离线 target 被误读为真实 QMT ready | HIGH | 所有 evidence 和 CP8 标注 `not_authorization=true` / READY_WITH_RISK | 若用户要求真实验证，另起 QMT direct-run runtime gate。 |
| R-CR101-03 | MiniQMT adapter contract 被扩展成 order-write | HIGH | endpoint allowlist、trade flags false、order-write follow-up 独立 | 出现 submit/cancel 需求时路由到独立 CR。 |
| R-CR101-04 | future target slot 过早抽象化 | MEDIUM | CP6 只实现 1 个 target，future slot 只保留 schema | 如果抽象阻碍实现，降级为 QMT-only schema 并记录 ADR。 |
| R-CR101-05 | 子 agent HLD 超时导致设计证据不足 | LOW | 主进程接管并记录 spawn/close 证据；CP3 人工确认前跑 human gate 校验 | 若用户要求 meta-se 复审，重开 meta-se-critical review。 |

## 11. ADR 候选

| ADR | 决策 | 状态 |
|---|---|---|
| ADR-CR101-01 | 策略交付采用 cross-platform target taxonomy，当前 only implemented target 为 `qmt_terminal_direct`。 | proposed |
| ADR-CR101-02 | MiniQMT 不作为 runner host，只作为 `execution_adapters[]` 中的 gateway / broker adapter contract。 | proposed |
| ADR-CR101-03 | Manifest / checker / fixture 按 target + adapter 双边界重对齐，禁止新包使用 `miniqmt_runner` delivery target。 | proposed |
| ADR-CR101-04 | CP3 / CP5 / CP8 设计批准均不授权真实 NAS、凭据、runtime、simulation/live、交易或 publish。 | proposed |

## 12. HLD 拆分判定

| 判定项 | 结论 | 说明 |
|---|---|---|
| 核心产物数量 | 1 | 目标是 strategy delivery + adapter boundary realignment。 |
| Story 预计数量 | 3-4 | target taxonomy / manifest checker / fixture evidence 可在同一 HLD 管理。 |
| ADR 聚类 | 单一聚类 | target taxonomy、adapter protocol、manifest checker 强耦合。 |
| 风险集中度 | medium-high | 主要风险是权限误读和历史字段漂移，可由 CP5/CP7 验证收敛。 |
| 结论 | 不拆分 HLD | 若 CP5 发现 manifest migration 与 adapter protocol 文件冲突，再拆 Story，不拆 HLD。 |

## 13. 非目标与不授权范围

- 不访问、列取、读取、复制、写入、挂载、发布或删除真实 NAS。
- 不读取 `.env`、token、API key、password、HMAC secret、cookie、session、private key 或 QMT 凭据。
- 不读取账户、资金、持仓明细、委托、成交或原始日志。
- 不启动、连接、安装或运行 QMT / MiniQMT / XtQuant / gateway runtime。
- 不执行 submit / cancel / buy / sell / simulation / live。
- 不执行 provider fetch、lake write 或 catalog publish。
- 不实现 Goldminer、generic Python runtime target 或 order-write adapter；只保留 schema / follow-up slot。

## 14. CP3 待决策项草案

| 决策 ID | 决策类型 | 问题 | 推荐 |
|---|---|---|---|
| DQ-CP3-CR101-01 | architecture | 是否采用 target + adapter 双边界推荐架构？ | 采用方案 A。 |
| DQ-CP3-CR101-02 | architecture | 当前 implemented target 是否固定为 `qmt_terminal_direct`？ | 固定为唯一 implemented target。 |
| DQ-CP3-CR101-03 | implementation | CP5 是否按 manifest / checker / fixture / evidence 重对齐推进？ | 推进离线实现设计，不触碰 runtime。 |
| DQ-CP3-CR101-04 | runtime_authorization | CP3 approve 是否授权 NAS / 凭据 / QMT / MiniQMT / XtQuant / gateway / simulation/live / 交易 / publish？ | 不授权。 |
| DQ-CP3-CR101-05 | risk_acceptance | 是否接受历史 `miniqmt_runner` 字段迁移风险和 READY_WITH_RISK 路线？ | 接受，并要求 CP5/CP7 负向验证。 |

## 15. 自审记录

| 检查项 | 结论 | 说明 |
|---|---|---|
| 候选方案数量 >= 2 | PASS | 已列 4 个方案。 |
| advisor table-first | PASS | 使用固定表头。 |
| 集成契约显式化 | PASS | 覆盖调用方向、时机、输入、输出、降级和调用方修改。 |
| NFR 量化 | PASS | 成功标准均含明确计数或阈值。 |
| 场景模拟 2-3 个 | PASS | 已列 4 个关键场景。 |
| 不授权边界 | PASS | 已独立列出。 |

## 16. S01-S03 离线实现落地摘要

| Story | 落地对象 | 离线验证结论 | 真实系统边界 |
|---|---|---|---|
| S01 Target taxonomy and manifest contract | `trading/strategy_runner/package_loader.py`、`tests/test_cr091_strategy_runner_contracts.py` | CP6/CP7 PASS；`delivery_targets[]` / `execution_adapters[]` 双边界已实现；legacy `miniqmt_runner` delivery target fail closed。 | 不证明真实 QMT direct-run 已可运行。 |
| S02 Package checker and fixture fail-closed | `trading/strategy_runner/package_exchange.py`、`tests/test_cr100_package_exchange.py` | CP6/CP7 PASS；fake exchange fixture 已迁移为 CR101 contract；8 类 fail-closed 覆盖。 | 不证明真实 NAS publish / pull / copy / 校验可用。 |
| S03 Runner adapter and evidence boundary | `trading/strategy_runner/adapters.py`、`trading/strategy_runner/evidence.py`、相关 tests | CP6/CP7 PASS；adapter result 和 evidence summary 显式记录 target / adapter / capabilities。 | 不证明真实 MiniQMT gateway 或账户只读链路可用。 |

验证证据只覆盖本地离线 contract、fake transport、临时目录 fixture、静态检查和单元回归。所有 CP6/CP7 证据均不包含真实 NAS、凭据、账户、持仓、委托、成交、原始日志、QMT/MiniQMT/XtQuant/gateway runtime、simulation/live、交易或 publish。

## 17. S04 Validation Matrix and Follow-Up Gates

S04 的收口文档为 `docs/qmt/CR101-VALIDATION-AND-FOLLOW-UP-GATES.md`。该文档是 CR101 CP7 / CP8 的默认验证摘要输入，必须与本 HLD、`process/changes/CR-091-FOLLOW-UP-TRACKING-2026-06-18.md` 和 `process/changes/CR-INDEX.yaml` 保持一致。

| Candidate ID | Legacy ID | 状态 | 启动条件 | 不授权边界 |
|---|---|---|---|---|
| RA-CR101-001 | QMT-DIRECT-RUN-VALIDATION-FU | candidate-not-started | 用户明确发起 runtime_authorization gate，并提供可脱敏 evidence 方案。 | 当前 CR101 不授权 agent 代跑 QMT terminal、读取账号/日志或声明真实 ready。 |
| RA-CR101-002 | MINIQMT-GATEWAY-ADAPTER-VALIDATION-FU | candidate-not-started | 用户明确发起 readonly gateway validation gate，限定 health / capabilities / query_positions。 | 当前 CR101 不授权 gateway connect、账户原文、订单写入或 runtime 启动。 |
| RA-CR101-003 | NAS-REAL-EXCHANGE-FU | candidate-not-started | 用户明确发起 NAS exchange gate，单独列出 path、权限、读写范围和脱敏 evidence。 | 当前 CR101 不授权 NAS list/read/write/copy/publish/pull/delete 或 mount。 |
| FU-CR101-001 | ORDER-WRITE-SIMULATION-LIVE-FU | candidate-not-started | S01-S04 完成且用户明确接受高风险 order-write design gate。 | 当前 CR101 不授权 submit/cancel、buy/sell、simulation/live 或资金放大。 |

CR101 的 CP8 推荐结论若不执行真实验证，应为 `READY_WITH_RISK`：ready 仅指离线 contract / checker / evidence / docs readiness，risk 指真实 QMT、MiniQMT gateway、NAS exchange 和 order-write 均未验证且未授权。
