---
artifact: "CR006-BATCH-A LLD"
reviewer: "meta-qa"
lane: "lane-quality"
round: 1
status: "completed"
governance_mode: "review-gated"
reviewed_at: "2026-05-18"
outcome: "PASS_WITH_REQUIRED"
blocking_count: 0
required_count: 4
advisory_count: 1
---

# Review Findings

## 1. 审查范围

- 目标对象：
  - `process/stories/CR006-S01-tushare-first-data-acquisition-runbook-LLD.md`
  - `process/stories/CR006-S02-canonical-gold-lightweight-engine-adapter-LLD.md`
  - `process/stories/CR006-S03-backtrader-clean-feed-contract-LLD.md`
  - `process/stories/CR006-S04-old-data-reference-only-guardrail-LLD.md`
- 审查目标：检查四份 LLD 是否互相矛盾，是否覆盖 CR-006 变更需求与 HLD §23 / ADR-018，测试设计是否覆盖 Tushare-first、raw/manifest 非 runtime 依赖、轻量 engine / Backtrader 消费边界、old data reference-only 护栏，以及实现步骤是否可验证、可门控、不会绕过 CP6/CP7 或触碰真实数据。
- 审查依据：
  - `process/changes/CR-006-LEGACY-DATA-DIRECTORY-EXTERNALIZATION-2026-05-18.md`
  - `process/HLD.md` §23
  - `process/ARCHITECTURE-DECISION.md` ADR-018
  - `process/STORY-BACKLOG.md`
  - `process/DEVELOPMENT-PLAN.yaml`
  - `checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md`
  - 四份 CR006-BATCH-A LLD 与四份 CP5 自动预检

## 2. Findings

### 2.1 总体判断

四份 LLD 的主方向与 HLD §23、ADR-018、Story Backlog v0.8 一致：Tushare structured lake 是新事实源；raw/manifest 保留为采集审计、复现和质量追溯层；轻量 engine 只能消费 canonical/gold 或由 canonical/gold 派生的 external `legacy_flat`；Backtrader 只消费 quality gate 后 clean feed；旧 repo `data/` 为 reference-only，不作为 fallback、迁移源或覆盖证明。

未发现必须阻断 CP5 批量人工审查的 BLOCKING。发现 4 个 REQUIRED 和 1 个 ADVISORY，均应在进入实现前由 meta-po 路由收敛；其中 F-001 / F-002 / F-003 会直接影响 CP6/CP7 验收口径或实现选择，建议优先处理。

### 2.2 Findings Table

<!-- findings-table -->

| ID | Severity | Rule Ref | Evidence | Impact | Suggestion | Anchor |
|----|----------|----------|----------|--------|------------|--------|
| F-QA-CR006-LLD-001 | REQUIRED | `CR-006 acceptance traceability` | CR-006 顶部状态已声明当前执行口径为 Tushare-first，旧 repo `data/` 不作为 fallback、迁移源或覆盖证明：`process/changes/CR-006-LEGACY-DATA-DIRECTORY-EXTERNALIZATION-2026-05-18.md` §状态更新。但同一 CR 仍保留旧外置化基线与旧 AC：`CR006-AC-003` 要求未设置 legacy env 时旧默认 `data/` 可通过 smoke；`CR006-AC-004` 要求 legacy env 外置路径优先；`CR006-AC-006` 要求外置 legacy raw/manifest 可解析。Story Backlog v0.8 又将 S04 映射到 `CR006-AC-013/014`，但 CR 文件只定义到 `CR006-AC-012`。 | LLDs 与 HLD/ADR/Story Backlog 的 Tushare-first 方向一致，但与 CR 文件残留旧 AC 冲突。CP7 coverage checker 若以 CR AC 为真相源，会同时要求“旧 `data/` fallback 可用”和“旧 `data/` 默认消费次数为 0”，导致验收口径不可判定；也可能让 meta-dev 误按旧 AC 实现 fallback。 | meta-po 路由 meta-se / CR owner 修订 CR-006 验收口径，明确 Tushare-first 版本的权威 AC 编号；同步 Story Backlog 的 `CR006-AC-013/014` 映射或在四份 LLD 的测试追溯表中改为已定义 AC。修订前，不建议进入实现。 | `process/changes/CR-006-LEGACY-DATA-DIRECTORY-EXTERNALIZATION-2026-05-18.md#验收口径`; `process/STORY-BACKLOG.md#Story-列表` |
| F-QA-CR006-LLD-002 | REQUIRED | `Upstream gate consistency` | 四份 LLD 和 CP5 自动预检依赖 CR005-S01/S02/S03/S06 verified / CP7 PASS；对应 Story 文件和 STATE 中确有 verified / CP7 PASS 证据。但 `process/STORY-BACKLOG.md` frontmatter 仍保留 `cr005_status: "draft-pending-cp4-rerun"`、`cr005_confirmed: false`，且阻塞项表保留 `CR5-BLK-001..005` 为 OPEN；`process/DEVELOPMENT-PLAN.yaml` frontmatter 也保留相同 CR005 draft 状态。 | CR006-S01/S02/S03 的 dev_gate 建立在 CR005 契约已冻结之上。若调度器或 reviewer 读取 Story Backlog / Development Plan 的顶层状态，会得到“CR005 未确认”的相反结论，影响 CR006-BATCH-A 是否可实现、是否可进入 CP6/CP7 的门控判断。 | meta-po 路由 meta-se / state owner 对 Story Backlog 与 Development Plan 的 CR005 顶层状态和 CR5-BLK 阻塞项做一致性修订或显式标注为 superseded。若保持历史阻塞项，需补充“已由 Story 文件 / STATE / CP7 结果覆盖”的状态闭环。 | `process/STORY-BACKLOG.md#阻塞项`; `process/DEVELOPMENT-PLAN.yaml` frontmatter |
| F-QA-CR006-LLD-003 | REQUIRED | `S02 legacy_flat implementation decision` | HLD §23.14 将 external `legacy_flat` 是否必须产出列为 OPEN；S02 LLD §12 `O-S02-01` 也声明 `legacy_flat` 是否 must-have 未确认。但 S02 LLD §2、§6、§10、§11 同时把 `derive_external_legacy_flat`、`T-S02-04`、`T-S02-05`、`CR006-S02-T1B` 作为正式接口、测试和任务。 | 实现阶段存在两种相反解释：只实现 canonical/gold in-memory bundle 也算完成，或必须实现 external `legacy_flat` 派生入口。若未先收敛，CP6 可能因测试要求和 DoD 不一致而失败；也可能为了满足测试额外实现不必要的 flat 派生能力。 | meta-po 路由 `CR006-S02` 的 meta-dev 在实现前确认二选一：A. `legacy_flat` 是 S02 必交付，保留接口、任务和测试；B. `legacy_flat` 是可选兼容入口，将 T-S02-04/T-S02-05 和 T1B 改为条件测试 / future contract，并明确 canonical/gold-only 的 DoD。 | `process/stories/CR006-S02-canonical-gold-lightweight-engine-adapter-LLD.md#12-风险难点与预研建议`; `process/stories/CR006-S02-canonical-gold-lightweight-engine-adapter-LLD.md#10-测试设计` |
| F-QA-CR006-LLD-004 | REQUIRED | `S03 clean feed read boundary` | S03 LLD §1 写明 Backtrader 不触发 Tushare fetch/backfill/normalize/validate/read 或任何真实数据湖读写；但同一 LLD §2、§3、§6、§7 又要求 `market_data/readers.py` 暴露 `read_backtrader_clean_feed(...)`，Backtrader 显式 backend 读取 quality gate 后 clean feed。HLD §23.6 / ADR-018 要求 Backtrader 消费 clean feed，而不是完全禁止 reader 读取。 | “不得 read” 的措辞过宽，可能被实现者理解为 S03 不能读取任何 canonical/gold clean feed，只能接收预注入 bundle；这会削弱 reader 集成测试，也可能与 S02 reader surface 产生冲突。 | 路由 `CR006-S03` meta-dev 修订措辞：禁止的是 raw/manifest runtime read、connector/runtime/storage 调用、fetch/backfill、数据层 normalize/validate job 和默认测试中的真实私有 lake 读写；允许显式 Backtrader backend 通过只读 reader 消费 quality-gated canonical/gold clean feed fixture 或受控本地 clean feed。同步更新 `T-S03-NO-FETCH-01` / `T-S03-NO-WRITE-01` 的断言边界。 | `process/stories/CR006-S03-backtrader-clean-feed-contract-LLD.md#1-Goal`; `process/stories/CR006-S03-backtrader-clean-feed-contract-LLD.md#6-API--Interface-设计` |
| F-QA-CR006-LLD-005 | ADVISORY | `S04 guardrail scan scope` | S04 LLD §6 / §10 多次使用 “target source text”“目标源码文本”“S01/S02/S03/S04 实现文件存在” 作为静态扫描输入，但没有列出精确 allowlist；§9 只说“单测限定扫描文件集合”，未定义集合。 | 该 guardrail 方向正确，但实现时容易出现两类问题：扫描范围过宽导致误报或读取不相关大文件；扫描范围过窄导致漏掉 S02/S03 中的 fallback / migration / raw-manifest runtime 违规。 | 路由 `CR006-S04` meta-dev 在实现前补充精确扫描 allowlist：README、USER-MANUAL、`.gitignore`、S01-S03/S04 owned source 与 tests；明确排除 `data/**`、`.env`、外部 lake、reports、大型二进制和真实私有路径；violation 只输出文件路径、规则 ID 和脱敏摘要。 | `process/stories/CR006-S04-old-data-reference-only-guardrail-LLD.md#6-API--Interface-设计`; `process/stories/CR006-S04-old-data-reference-only-guardrail-LLD.md#10-测试设计` |

## 3. 汇总结论

### 3.1 覆盖评估

| 评审重点 | 评估结果 | 说明 |
|---|---|---|
| Tushare-first 功能 | PASS_WITH_REQUIRED | S01 覆盖 plan/dry-run/real gate、manifest、lineage、quality/catalog 和 no-old-data；但 CR AC 需要先从旧外置化口径收敛到 Tushare-first。 |
| raw/manifest 非 runtime 依赖 | PASS | S01/S02/S03/S04 都明确 raw/manifest 仅用于审计、复现、质量追溯，不作为轻量 engine / Backtrader 运行时输入；测试含 forbidden import/path/call spy。 |
| 轻量 engine 消费边界 | PASS_WITH_REQUIRED | S02 覆盖 canonical/gold、quality fail、required_missing、no fetch/backfill、no repo data fallback；需收敛 external `legacy_flat` 是否 must-have。 |
| Backtrader 消费边界 | PASS_WITH_REQUIRED | S03 覆盖 clean feed、PIT/复权/quality gate、optional backend、no connector/token/network；需澄清“不得 read”的过宽措辞。 |
| old data reference-only 护栏 | PASS_WITH_ADVISORY | S04 覆盖 README/USER-MANUAL/.gitignore/guardrail tests、no fallback、no silent migration、no credentials；建议补充精确扫描 allowlist。 |
| CP6/CP7 门控 | PASS | 四份 LLD 均保持 `confirmed=false` / `implementation_allowed=false`，明确 CP5 全量人工确认前不得实现，CP6/CP7 仍需独立记录。 |
| 离线默认 / 凭据安全 / 真实数据门禁 | PASS | 四份 LLD 均使用 fake/offline fixture、tmp_path、monkeypatch、静态扫描；均禁止读取 `.env`、token、NAS 凭据和真实私有路径，禁止真实抓取和旧 `data/**` 操作。 |

### 3.2 结论与路由

- 结论：`PASS_WITH_REQUIRED`
- blocking_count: 0
- required_count: 4
- advisory_count: 1
- optional_count: 0
- recommended_next_action: `revise-required-items-before-implementation`

需要 meta-po 路由的对象：

| 对象 | 建议路由 |
|---|---|
| CR-006 / Story Backlog AC 映射 | 路由 meta-se / CR owner 修订验收口径与 AC 编号，解除 Tushare-first 与旧 fallback AC 冲突。 |
| Story Backlog / Development Plan CR005 状态 | 路由 meta-po / meta-se 做状态闭环，避免 CR005 顶层 draft 状态与 CR005 Story verified 证据冲突。 |
| `CR006-S02` | 路由 meta-dev 收敛 external `legacy_flat` 是否 must-have，并同步测试和 DoD。 |
| `CR006-S03` | 路由 meta-dev 澄清 clean feed read 边界，避免禁止合法 reader 消费。 |
| `CR006-S04` | 路由 meta-dev 补充 guardrail 静态扫描 allowlist。 |

## 4. 待确认项

- 是否由 meta-po 在 CP5 批量人工确认前先处理 F-QA-CR006-LLD-001 和 F-QA-CR006-LLD-002 的上游追溯一致性。
- 是否将 S02 external `legacy_flat` 定义为 CR006-BATCH-A 必交付能力，还是作为后续兼容入口。
