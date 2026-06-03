---
checkpoint_id: "CP7"
checkpoint_name: "CR017-S06 研究 / QMT 消费边界与迁移指南验证完成门"
type: "rolling_auto"
status: "PASS"
owner: "meta-qa/qa-hua the 2nd"
created_at: "2026-05-28T08:45:04+08:00"
checked_at: "2026-05-28T08:45:04+08:00"
target:
  phase: "story-execution"
  change_id: "CR-017"
  story_id: "CR017-S06-research-qmt-consumer-docs-and-migration-guide"
  story_slug: "research-qmt-consumer-docs-and-migration-guide"
  artifacts:
    - "docs/ADJUSTMENT-POLICY-MIGRATION.md"
    - "README.md"
    - "docs/USER-MANUAL.md"
    - "engine/research_dataset.py"
    - "tests/test_cr017_research_qmt_consumer_boundary.py"
manual_checkpoint: "checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md"
handoff: "process/handoffs/META-QA-CR017-S06-CP7-VERIFY-2026-05-28.md"
cp6: "process/checks/CP6-CR017-S06-research-qmt-consumer-docs-and-migration-guide-CODING-DONE.md"
lld: "process/stories/CR017-S06-research-qmt-consumer-docs-and-migration-guide-LLD.md"
---

# CP7 CR017-S06 研究 / QMT 消费边界与迁移指南验证完成门

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 验证环境已确认 | PASS | `process/VALIDATION-ENV.yaml` `approval.confirmed=true` | 环境文件仍引用历史 STORY-001 范围；本轮以 meta-po handoff 的 CR017-S06 Verification Scope 作为目标范围，记录为非阻断元数据偏差。 |
| QA handoff 已读取 | PASS | `process/handoffs/META-QA-CR017-S06-CP7-VERIFY-2026-05-28.md` | handoff 明确只读验证范围、必跑测试、禁止真实操作和唯一写入目标。 |
| Story 可验证 | PASS | `process/stories/CR017-S06-research-qmt-consumer-docs-and-migration-guide.md` | frontmatter `status=ready-for-verification`、`implementation_allowed=true`，依赖 S04/S05 已满足。 |
| LLD 已确认 | PASS | `process/stories/CR017-S06-research-qmt-consumer-docs-and-migration-guide-LLD.md` | frontmatter `tier=M`、`confirmed=true`、`open_items=0`。 |
| CP5 批次人工确认通过 | PASS | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | `status=approved`，`reviewed_at=2026-05-28T07:03:27+08:00`。 |
| 上游 S04/S05 已验证 | PASS | `process/checks/CP7-CR017-S04-reader-api-and-policy-gates-VERIFICATION-DONE.md`、`process/checks/CP7-CR017-S05-validation-quality-parity-and-leakage-tests-VERIFICATION-DONE.md` | 两个上游 CP7 均为 `PASS`。 |
| CP6 编码完成门通过 | PASS | `process/checks/CP6-CR017-S06-research-qmt-consumer-docs-and-migration-guide-CODING-DONE.md` | frontmatter `status=PASS`，包含 LLD 消费、测试、安全计数和 dev dispatch 证据。 |
| 写入范围受控 | PASS | 当前用户指令与 handoff | 本轮仅允许写入本 CP7 文件；未修改代码、文档、测试、Story、CP6、LLD、handoff、DEV-LOG、依赖、data、reports 或 delivery。 |
| TEST-STRATEGY 写入 | WAIVED | 当前用户指令“只允许写入 CP7” | 本轮不新写或更新 `process/TEST-STRATEGY.md`；测试设计方法在本 CP7 内记录执行证据。 |

## Agent Dispatch Evidence

### CP7 QA Invocation

| 字段 | 值 | 说明 |
|---|---|---|
| invocation_source | `spawn_agent` | meta-po 通过平台子 agent 调度能力启动本 Story CP7 验证。 |
| agent_id | `019e6c08-720d-77c0-89e4-1d5c8a57a66b` | Codex spawn_agent 返回的 QA 子 agent id。 |
| thread_id | `019e6c08-720d-77c0-89e4-1d5c8a57a66b` | 平台无独立 thread 时与 agent_id 一致。 |
| agent_name | `qa-hua the 2nd` | QA 子 agent 昵称。 |
| tool_name | `multi_agent_v1.spawn_agent` | 实际调度工具。 |
| qa_handoff_dispatch_mode | `spawn_agent` | `process/handoffs/META-QA-CR017-S06-CP7-VERIFY-2026-05-28.md` 已由 meta-po 回收补齐 dispatch / completed / closed。 |
| inline_fallback | `false` | 本轮按用户直接调用的 meta-qa 身份执行，不声明为 meta-po 代执行，也不修改 handoff。 |
| write_scope | `CP7 only` | 符合用户和 handoff 的唯一写入目标。 |
| checked_at | `2026-05-28T08:45:04+08:00` | CP7 验证完成时间。 |
| closed_at | `2026-05-28T08:48:50+08:00` | meta-po 回收后关闭 QA 子 agent 时间。 |

### CP6 Dev Dispatch 复核

| 字段 | 值 | 说明 |
|---|---|---|
| CP6 status | `PASS` | `process/checks/CP6-CR017-S06-research-qmt-consumer-docs-and-migration-guide-CODING-DONE.md`。 |
| dispatch_source | `spawn_agent` | CP6 Agent Dispatch Evidence 明确为平台子 agent 调度。 |
| agent_id | `019e6bfc-348d-7730-b9a1-cec5434a2646` | CP6 与 dev handoff 一致。 |
| thread_id | `019e6bfc-348d-7730-b9a1-cec5434a2646` | 平台无独立 thread 时与 agent_id 一致。 |
| agent_name | `dev-lv the 2nd` | meta-dev 子 agent。 |
| tool_name | `multi_agent_v1.spawn_agent` | 实际调度工具。 |
| spawned_at | `2026-05-28T08:29:17+08:00` | dev handoff frontmatter。 |
| completed_at | `2026-05-28T08:36:51+08:00` | CP6 完成时间。 |
| closed_at | `2026-05-28T08:40:12+08:00` | meta-po 关闭子 agent 时间。 |
| inline_fallback | `false` | CP6 非 inline fallback。 |

## LLD 消费证据

| LLD 契约 | 状态 | 验证入口 | 结论 |
|---|---|---|---|
| Frontmatter 上下文 | PASS | `tier=M`、`confirmed=true`、`open_items=0` | 满足 CP7 验证输入条件。 |
| 第 6 节 API / Interface | PASS | `build_consumer_guidance_matrix()`、`build_adjustment_blocked_claims()`、`research_dataset_policy_metadata()`、`render_migration_guide_sections()` | 四个入口均存在并被 S06 测试和静态复核覆盖。 |
| 第 7 节核心流程 | PASS | S04/S05 输入 -> consumer matrix -> docs / metadata；CR017 status -> blocked claims | 主路径和异常路径均覆盖：CR017 未 verified、QMT non-raw、unsupported execution claim。 |
| 第 10 节测试设计 | PASS | `tests/test_cr017_research_qmt_consumer_boundary.py` 6 个测试 + CR017 回归 39 个测试 | 覆盖 consumer matrix、raw-only、scale_up blocked、legacy qfq、unsupported claim 和安全计数。 |
| 第 13 节回滚与发布策略 | PASS | safety scan、operation counters、pytest 离线结果 | 未触发 QMT non-raw allowed、scale_up allowed、unsupported support claim、真实 provider/lake/publish/broker 操作或 legacy overwrite。 |

## 测试策略执行

| 测试设计方法 | 是否执行 | 发现数量 | 说明 |
|---|---|---:|---|
| 等价分区 | PASS | 0 | 覆盖 chart、long-horizon research、factor research、QMT order intent 四类 consumer 分区。 |
| 边界值分析 | PASS | 0 | 验证 non-raw execution allowed、adjusted execution pass、production governance allowed、scale_up allowed 的 0 边界。 |
| 状态转换测试 | PASS | 0 | 验证 CR017 `ready-for-verification/not_verified` 到 production governance / scale_up blocked；verified 后仍需下游 gate 的设计边界在 helper 中保留。 |
| 错误推测 | PASS | 0 | 针对 legacy qfq overwrite、旧报告覆盖、unsupported execution supported 声明、真实操作和依赖变更做负向扫描。 |

## ISO 25010 质量评估

| 质量特征 | 优先级 | 评估结果 | 说明 |
|---|---|---|---|
| 功能适合性 | P0 | PASS | Story AC 与 handoff 验证重点全部有测试或静态证据。 |
| 可靠性 | P0 | PASS | 指定 S06 测试 `6 passed in 0.44s`，CR017 回归 `39 passed in 0.45s`。 |
| 安全性 | P0 | PASS | dangerous-command-scan 未发现阻断级实际调用；所有真实操作、凭据、provider、lake、publish、dependency、legacy overwrite 计数为 0。 |
| 可维护性 | P1 | PASS | helper、dataclass、metadata 字段和测试名称与 LLD 命名对齐。 |
| 可移植性 | P1 | PASS | 通过 `uv run --python 3.11 pytest` 在离线 Python 3.11 环境验证；本 Story 无安装脚本。 |
| 易用性 | P2 | PASS | README、USER-MANUAL、migration guide 均提供用户可见的 consumer matrix、raw-only 和 blocked claim 说明。 |
| 兼容性 | P2 | PASS | 回归覆盖 S04 reader/policy、S05 quality/leakage、S02/S03 adjustment contract 与 qfq/hfq derivation。 |
| 性能效率 | P3 | PASS | 常量级 helper 和小样本文档测试，单轮回归在 1 秒内完成。 |

## 8 维度验收矩阵

| # | 维度 | 阻断等级 | 状态 | 说明 |
|---|---|---|---|---|
| 1 | 完整性 | BLOCKING | PASS | 5/5 个目标产物存在：migration guide、README、USER-MANUAL、metadata helper、S06 测试。 |
| 2 | 平台适配 | BLOCKING | PASS | Python 3.11 + uv 离线验证通过；本 Story 不生成跨平台安装目标。 |
| 3 | 验收标准覆盖 | BLOCKING | PASS | Story 4 条 AC 全覆盖；额外覆盖 handoff 指定 legacy qfq、旧报告、unsupported execution、blocked governance/scale_up。 |
| 4 | 安全合规 | BLOCKING | PASS | 危险命令 / Prompt 注入 / 真实操作扫描无阻断；安全计数全为 0。 |
| 5 | 命名规范 | REQUIRED | PASS | `test_cr017_research_qmt_consumer_boundary.py`、`research_dataset_policy_metadata`、`build_consumer_guidance_matrix` 等命名符合 Python / Story 约定。 |
| 6 | Frontmatter 完整性 | REQUIRED | PASS | Story、LLD、CP6、handoff frontmatter 可消费；LLD `tier`、`confirmed`、`open_items` 满足契约。 |
| 7 | 可安装性 | REQUIRED | N/A | 本 Story 不生成安装器或交付包；可执行性由指定 pytest 命令证明。 |
| 8 | 文档覆盖 | OPTIONAL | PASS | `docs/ADJUSTMENT-POLICY-MIGRATION.md`、README、USER-MANUAL 均覆盖消费矩阵、raw-only、blocked claims、legacy qfq 和 unsupported execution 边界。 |

## 验收标准覆盖

| 验收标准 / 验证重点 | 状态 | 证据 | 结果 |
|---|---|---|---|
| consumer guidance 覆盖 chart / long-horizon research / factor research / QMT order intent | PASS | `build_consumer_guidance_matrix()`、README、USER-MANUAL、migration guide、`test_consumer_guidance_covers_required_consumers` | 四类 consumer 全部存在。 |
| QMT execution 非 raw allowed 次数为 0 | PASS | `qmt_non_raw_execution_allowed_count=0`、`non_raw_execution_allowed=0`、`test_qmt_order_intent_is_raw_only` | QMT execution `raw-only`；`qfq/hfq/returns_adjusted` 作为执行价 blocked。 |
| CR017 未 verified 时 production governance 和 scale_up blocked | PASS | `build_adjustment_blocked_claims(cr017_status="ready-for-verification", stage="scale_up")`、`test_cr017_unverified_blocks_production_governance_and_scale_up` | `production_adjustment_governance_claim_allowed_count=0`、`scale_up_allowed_count=0`。 |
| legacy qfq 保留且旧报告不覆盖 | PASS | `migration_contract`、migration guide、`test_migration_contract_preserves_legacy_qfq_and_old_reports` | `legacy_qfq_baseline_preserved=true`、`old_report_overwrite_allowed=false`、`new_prices_qfq_replaces_legacy_qfq=false`。 |
| unsupported execution features 不声明为 supported | PASS | migration guide unsupported table、README / USER-MANUAL CR017 section、`test_docs_expose_consumer_boundary_without_unsupported_execution_claims` | true VWAP、minute、tick、Level2、order-match、microstructure impact cost 均为 unsupported / blocked。 |
| 真实操作 / 凭据 / provider / lake / publish / dependency / legacy overwrite 计数为 0 | PASS | metadata `operation_counts`、文档零计数、`test_rendered_sections_and_safety_counters_are_zero` | 所有指定计数为 0。 |

## 测试结果

| 命令 | 状态 | 输出 |
|---|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr017_research_qmt_consumer_boundary.py` | PASS | `6 passed in 0.44s` |
| `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr017_reader_policy_gates.py tests/test_cr017_adjustment_leakage_gates.py tests/test_cr017_adjustment_quality_parity.py tests/test_cr017_adjustment_policy_contract.py tests/test_cr017_raw_adj_factor_contract.py tests/test_cr017_qfq_hfq_derivation.py` | PASS | `39 passed in 0.45s` |

## Dangerous Command Scan

| 扫描对象 | 状态 | 结果 | 说明 |
|---|---|---|---|
| `docs/ADJUSTMENT-POLICY-MIGRATION.md` | PASS | 阻断风险 0 | 命中内容均为 forbidden operation 零计数、raw-only / unsupported / blocked 声明；无可执行危险命令。 |
| README CR017 section | PASS | 阻断风险 0 | 命中内容为零计数和禁止声明；未声明 unsupported execution supported。 |
| USER-MANUAL CR017 section | PASS | 阻断风险 0 | 命中内容为“不读取凭据、不调用 QMT / MiniQMT / broker API、不发单、不撤单、不查询账户、不抓取、不写湖、不 publish”。 |
| `engine/research_dataset.py` CR017 helper | PASS | 阻断风险 0 | 命中内容为常量、metadata 字段和 blocked claims；未发现 `subprocess`、`os.system`、`eval`、真实 broker/order/cancel/account 调用。 |
| `tests/test_cr017_research_qmt_consumer_boundary.py` | PASS | 阻断风险 0 | 仅离线读取 allowlisted 文档和 helper，不读凭据、不访问 provider、不写数据湖。 |
| 信息性命中 | PASS | 非阻断 | `docs/USER-MANUAL.md` 中存在“不要裸 pip install”的否定性说明；不构成本 Story 阻断风险。 |

## 安全计数

| 计数项 | 结果 | 证据 |
|---|---:|---|
| provider_fetch | 0 | metadata `operation_counts.provider_fetch=0`；本轮未调用 provider。 |
| lake_write | 0 | metadata `operation_counts.lake_write=0`；未写真实 lake。 |
| credential_read | 0 | metadata `operation_counts.credential_read=0`；未读取 `.env`、token、password、private key、cookie、session、账户或持仓。 |
| current_pointer_publish | 0 | metadata `operation_counts.current_pointer_publish=0`；未 publish catalog pointer。 |
| real_order_call | 0 | metadata `operation_counts.real_order_call=0`；未发单。 |
| real_cancel_call | 0 | metadata `operation_counts.real_cancel_call=0`；未撤单。 |
| account_query_call | 0 | metadata `operation_counts.account_query_call=0`；未查询账户。 |
| dependency_change | 0 | metadata `operation_counts.dependency_change=0`；未执行依赖变更，未修改 `pyproject.toml` / `uv.lock`。 |
| legacy_qfq_overwrite | 0 | metadata `operation_counts.legacy_qfq_overwrite=0`；legacy qfq 保持 read-only。 |
| non_raw_execution_allowed | 0 | metadata `operation_counts.non_raw_execution_allowed=0`；QMT execution raw-only。 |
| production_adjustment_governance_claim_allowed | 0 | metadata `operation_counts.production_adjustment_governance_claim_allowed=0`。 |
| scale_up_allowed | 0 | metadata `operation_counts.scale_up_allowed=0`。 |
| unsupported_execution_feature_allowed_count | 0 | `research_dataset_policy_metadata(... )` 输出为 0。 |
| old_report_overwrite_allowed | 0 | migration contract `old_report_overwrite_allowed=false`。 |

## Scope Deviation / 已知风险

| 项 | 状态 | 说明 |
|---|---|---|
| QA handoff dispatch 未回填 | RESOLVED_AFTER_QA | meta-po 回收 CP7 后已补齐 QA handoff 的 `dispatch.mode=spawn_agent`、agent id、completed_at 与 closed_at；CP6 dev dispatch 也已复核为 `spawn_agent`。 |
| `VALIDATION-ENV.yaml` 目标范围陈旧 | NON_BLOCKING | 文件 `approval.confirmed=true`，但 validation_scope 指向历史 STORY-001；本轮以 CR017-S06 handoff 为验证范围真相源。 |
| TEST-STRATEGY 未写入 | WAIVED | 用户明确“只允许写入”本 CP7 文件；本 CP7 内记录测试设计方法执行结果。 |
| 缓存 / 工作树既有状态 | NON_BLOCKING | 本轮 pytest 使用 `PYTHONDONTWRITEBYTECODE=1` 和 `-p no:cacheprovider`；未写 `.pytest_cache` 新证据，不清理既有缓存或无关脏文件。 |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| BLOCKING 维度全部通过 | PASS | 8 维度验收矩阵 | 完整性、平台适配、验收标准覆盖、安全合规均 PASS。 |
| REQUIRED 维度通过或不适用 | PASS | 8 维度验收矩阵 | 命名规范、Frontmatter 完整性 PASS；可安装性 N/A 且有理由。 |
| LLD 指定接口 / 流程 / 测试 / 回滚已消费 | PASS | LLD 消费证据 | §6、§7、§10、§13 均有验证记录。 |
| 指定测试全部通过 | PASS | 测试结果 | 6 + 39 个测试通过。 |
| 安全禁止项未触发 | PASS | 安全计数与扫描 | QMT/MiniQMT/broker API、凭据、真实发单/撤单/账户查询、真实写湖、provider fetch、publish、依赖变更、legacy overwrite 均为 0。 |
| CP7 输出已生成 | PASS | 本文件 | 写入唯一允许目标路径。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| CP7 验证完成门 | `process/checks/CP7-CR017-S06-research-qmt-consumer-docs-and-migration-guide-VERIFICATION-DONE.md` | PASS | 本文件。 |

## 结论

- 结论：`PASS`
- 阻断项：0
- 豁免项：`TEST-STRATEGY.md` 本轮未写入，原因是用户明确限制唯一写入目标为 CP7 文件。
- 非阻断风险：VALIDATION-ENV 目标范围陈旧；QA handoff dispatch 已由 meta-po 回收补齐，不影响本 Story 的功能、测试和安全验收结论。
- 下一步：meta-po 可基于本 CP7 将 `CR017-S06-research-qmt-consumer-docs-and-migration-guide` 路由到后续状态；真实 QMT、真实发单、撤单、账户查询、provider fetch、真实写湖、publish、依赖变更和 legacy qfq overwrite 仍未授权且计数保持 0。
