---
status: "draft-current-index"
version: "1.1"
source_blueprint: "docs/design/BLUEPRINT.md"
change: "CR-046"
---

# Domain Map

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-07 | meta-po | 新增领域对象、状态机、术语和核心业务规则索引 |
| 1.1 | 2026-06-13 | meta-po | 按 CR-046 增补双目标策略交付框架领域对象、状态机和规则 |

## 术语表

| Term | 定义 | 来源 | 备注 |
|---|---|---|---|
| current truth | 经 Explicit Publish Gate 发布并由 catalog current pointer 指向的数据真相 | CR-014 / CR-018 | validate pass 不等于 current truth |
| candidate | 尚未发布的候选数据、候选报告或候选 release | CR-014 / CR-018 | 可验证、可审计，但不得默认消费为生产事实 |
| publish gate | 将 candidate 显式升级为 catalog current truth 的唯一门禁 | HLD-DATA-LAKE | 必须可回滚 |
| readiness | 数据或研究对象是否满足 production strict 消费的准入状态 | CR-010..018 | 与 quality 相关但不等同 |
| blocked claim | 因缺数据、未授权、未通过 gate 或后置能力未满足而禁止声明的能力 | CR-013..030 | 必须写解除条件 |
| allowed claim | 在证据和 gate 支持下允许对外声明的能力 | CR-013..030 | 必须可追溯 |
| order_intent_draft_v1 | 研究输出到交易治理的草稿合同 | CR-025 / CR-030 | 不等于真实订单或授权 |
| runtime authorization | 对真实运行、真实数据、真实账户、真实 gateway / QMT 操作的逐项授权 | CR-020 / CR-021..024 | CP approval 不自动授权 runtime |
| no-real-operation | 默认安全状态，真实 provider / lake / QMT / broker / credential 相关计数必须为 0 | 全部高风险 CR | 有授权时必须记录 authorization_id |
| simulation | QMT 模拟盘阶段 | CR-016 / CR-021 candidate | 需要独立 CR、stage gate 和 per-run authorization |
| live_readonly | 真实账户只读阶段 | CR-022 candidate | 不等于 small_live |
| small_live | 小资金实盘阶段 | CR-023 candidate | 需要更高门槛和回滚策略 |
| strategy core contract | 研究策略可复用核心的输入、输出、风控和证据合同 | CR-046 | 不得导入 QMT / XtQuant |
| QMT terminal target | 面向 QMT 终端内运行的策略包目标形态 | CR-046 | 本 CR 只设计，不执行终端验证 |
| MiniQMT runner target | 面向外部 Python runner 的策略包目标形态和安装设计 | CR-046 | 本 CR 只设计 install dry-run，不真实安装或连接 |
| strategy package contract | 双目标策略交付包的目录、schema、配置、文档和验证证据约束 | CR-046 | 后续 CR047 具体策略必须消费 |
| strategy validation evidence | 策略包静态、fixture、dry-run 和人工验证计划证据集合 | CR-046 | 不等于 QMT / MiniQMT runtime verified |

## 领域对象

| Object ID | 对象 | Owner Feature | 关键字段 / 属性 | 状态 | 规则来源 |
|---|---|---|---|---|---|
| OBJ-01 | MarketDataRun | FEAT-02 | run_id、dataset、source、interface、date_range、lake_root、authorization_ref | planned / running / success / partial_success / failed / blocked | REQ-088..137、ADR-048..066 |
| OBJ-02 | ManifestBatch | FEAT-02 | batch_id、idempotency_key、raw_path、checksum、attempts、error_enum | pending / running / success / skipped / failed / resume_conflict | ADR-005、ADR-051 |
| OBJ-03 | DatasetCandidate | FEAT-02 | dataset、schema_version、coverage、lineage、quality_status、readiness_status | candidate / validated / rejected | CR-014 / CR-018 |
| OBJ-04 | CatalogCurrentTruth | FEAT-02 | dataset、release_id、current_pointer、published_at、rollback_target | unpublished / published / rolled_back | ADR-048、ADR-052、ADR-064 |
| OBJ-05 | ClaimBoundary | FEAT-02 / FEAT-07 | allowed_claims、blocked_claims、required_missing、release_condition | open / allowed / blocked / waived | CR-013..030 |
| OBJ-06 | AdjustmentView | FEAT-02 | prices_raw、adj_factor、prices_qfq、prices_hfq、returns_adjusted、as_of_trade_date | raw / derived / published / blocked | ADR-053、ADR-054 |
| OBJ-07 | ResearchDataset | FEAT-01 / FEAT-03 | research_input_v1、benchmark、universe、quality、lineage、blocked_claims | available / unavailable / required_missing | ADR-024..029、ADR-079..086 |
| OBJ-08 | FactorSpec | FEAT-03 | factor_id、direction、lookback、source_fields、preprocess、version | draft / valid / invalid | CR-030 |
| OBJ-09 | FactorRunSpec | FEAT-03 | run_id、factor_ids、dataset_release、label_window、cost_config、random_seed | planned / executed / failed | CR-030 |
| OBJ-10 | FactorPanelContract | FEAT-03 | raw、directional、winsorized、zscore、coverage、filter_reason | complete / incomplete / blocked | CR-011 / CR-030 |
| OBJ-11 | LabelWindowSpec | FEAT-03 | horizon、decision_time、available_at_rule、leakage_policy | valid / leakage_blocked | CR-030 |
| OBJ-12 | FactorEvaluationReport | FEAT-03 | IC、RankIC、ICIR、layered_returns、turnover、cost_sensitivity | pass / warn / fail | CR-030 |
| OBJ-13 | ExperimentManifest | FEAT-03 | config_hash、dataset_release、factor_version、code_version、report_path | recorded / incomplete | CR-030 |
| OBJ-14 | StrategyAdmissionPackage | FEAT-03 / FEAT-07 | gate_results、blocked_reasons、order_intent_draft_ref、no_real_op_counters | draft / pass / blocked / follow_up_required | CR-019 / CR-030 |
| OBJ-15 | SemanticDiffReport | FEAT-04 | lightweight_result、optional_backend_result、diff_reason、fallback_status | generated / backend_unavailable / blocked | CR-025 |
| OBJ-16 | OrderIntentDraft | FEAT-04 / FEAT-06 | strategy_id、target_trade_date、research_adjustment_policy、execution_price_policy | draft / invalid / handed_off | CR-025 / CR-030 |
| OBJ-17 | PairingToken | FEAT-05 | token_id、scope、nonce、approved_by、expires_at、redaction_status | requested / approved / completed / revoked / expired | CR-019 / CR-020 |
| OBJ-18 | QMTGatewaySession | FEAT-05 | bind_host、port、run_mode、session_ready、capabilities、redaction | not_started / healthy / session_ready / blocked | CR-019 / CR-020 |
| OBJ-19 | QueryPositionsResult | FEAT-05 | account_label、positions_count、readonly_scope、blocked_reason | available / blocked / unavailable | CR-020 |
| OBJ-20 | OMSOrder | FEAT-06 | order_id、intent_id、state、broker_ref、risk_result、idempotency_key | pending / accepted / partially_filled / filled / cancel_pending / canceled / rejected / failed / unknown / timeout | CR-015 / CR-016 |
| OBJ-21 | BrokerLakeRecord | FEAT-06 | run_id、strategy_id、event_type、redacted_account_label、retention_policy | planned / dry_run / written / blocked | CR-015 / CR-016 |
| OBJ-22 | StageGate | FEAT-06 / FEAT-07 | stage、entry_criteria、exit_criteria、rollback、authorization_ref | shadow / simulation / live_readonly / small_live / scale_up / blocked | CR-016 |
| OBJ-23 | AuthorizationRecord | FEAT-07 | authorization_id、scope、actor、approved_at、expires_at、operation_allowlist | missing / active / expired / revoked | 全部高风险 CR |
| OBJ-24 | NoRealOpCounter | FEAT-07 | provider_fetch、lake_write、catalog_publish、qmt_api_call、real_order、credential_read | zero / nonzero_authorized / violation | CR-014..030 |
| OBJ-25 | Runbook | FEAT-08 | runbook_id、scope、operator_steps、not_authorized_items、evidence_required | draft / active / stale | docs/QMT-*.md |
| OBJ-26 | StrategyCoreContract | FEAT-09 | strategy_id、input_schema、target_portfolio_schema、order_intent_schema、risk_assumption、evidence_required | draft / validated / blocked | CR-046 |
| OBJ-27 | StrategyPackageContract | FEAT-09 | package_id、layout_version、targets、validation_suite、docs_bundle、authorization_boundary | draft / review_ready / approved / blocked | CR-046 |
| OBJ-28 | QMTTerminalTargetContract | FEAT-09 | entry_file、config_schema、import_steps、shadow_report_schema、manual_evidence_required | draft / validated / runtime_deferred | CR-046 |
| OBJ-29 | MiniQMTRunnerTargetContract | FEAT-09 | install_layout、uv_python_version、dependency_policy、start_stop_contract、log_paths、kill_switch | draft / install_dry_run_ready / runtime_deferred | CR-046 |
| OBJ-30 | StrategyValidationEvidence | FEAT-09 / FEAT-07 | fixture_result、schema_result、static_guardrail_result、dry_run_plan、manual_validation_plan | missing / partial / pass / blocked | CR-046 |
| OBJ-31 | RunnerInstallPlan | FEAT-09 / FEAT-08 | windows_root、venv_policy、upgrade_plan、rollback_plan、uninstall_plan、redaction_policy | draft / dry_run_reviewed / blocked | CR-046 |
| OBJ-32 | FollowUpStrategyDeliveryGate | FEAT-09 / FEAT-07 | candidate_cr、required_strategy_selection、runtime_authorization_required、evidence_prerequisites | open / ready_for_cr / blocked | CR047 / CR049 / CR051 candidates |

## 状态机

| State Machine ID | 对象 | 状态 | 合法转换 | 非法转换处理 |
|---|---|---|---|---|
| SM-01 | DatasetCandidate -> CatalogCurrentTruth | candidate -> validated -> published -> rolled_back | 只能由 validate / publish / rollback 触发 | validate pass 自动 current pointer 更新必须 blocked |
| SM-02 | ClaimBoundary | required_missing -> blocked_claim -> allowed_claim | 只有补齐证据、quality/readiness pass、授权满足后可 allowed | 缺证据的 allowed claim 必须 fail |
| SM-03 | FactorRunSpec | planned -> executed -> report_recorded | 任一输入 gate 失败则 blocked | 不得生成 admission pass |
| SM-04 | OrderIntentDraft | draft -> validated -> handed_off | 只传给 OMS / 后续 CR 审查 | 不得直接提交 QMT / adapter |
| SM-05 | PairingToken | requested -> approved -> completed -> revoked/expired | scope、timestamp、nonce 均需通过 | nonce replay / scope mismatch fail-closed |
| SM-06 | QMTGatewaySession | not_started -> healthy -> session_ready -> readonly_query_available | 需要本地启动、HMAC、QMT login/session ready | health pass 不得升级 simulation/live |
| SM-07 | OMSOrder | pending -> accepted -> partially_filled -> filled/cancel_pending/canceled/rejected/failed/unknown/timeout | 事件必须可审计 | unknown / timeout 不得静默成功 |
| SM-08 | StageGate | shadow -> simulation -> live_readonly -> small_live -> scale_up | 必须逐阶段满足 entry/exit 和 authorization | 跳阶段请求 blocked |
| SM-09 | AuthorizationRecord | missing -> active -> expired/revoked | active 需要 scope、actor、时间、操作白名单 | scope 外操作 blocked |
| SM-10 | StrategyPackageContract | draft -> review_ready -> approved -> delivered_by_followup | CP3/CP5/CP8 只批准合同；具体策略交付必须后续 CR | approved 不得自动生成可交易策略包 |
| SM-11 | QMTTerminalTargetContract | draft -> validated -> runtime_deferred | 本 CR 只能到设计和静态验证计划 | terminal shadow / 模拟盘运行请求必须 blocked |
| SM-12 | MiniQMTRunnerTargetContract | draft -> install_dry_run_ready -> runtime_deferred | 本 CR 只能到 install dry-run 设计 | 真实安装、连接、行情订阅或 submit/cancel 必须 blocked |

## 业务规则

| Rule ID | 规则 | Owner | 影响场景 | 验证入口 |
|---|---|---|---|---|
| RULE-01 | 回测、扫描、候选和研究消费主路径不得联网、不得自动补数、不得读取凭据 | FEAT-01 / FEAT-07 | UC-01..UC-09、UC-20..27 | consumer boundary tests |
| RULE-02 | catalog current truth 只能由 Explicit Publish Gate 更新 | FEAT-02 | CR-014 / CR-018 | `tests/test_cr014_catalog_publish_gate.py` |
| RULE-03 | `prices_raw` 和 broker price 是 QMT 执行价格唯一来源，qfq/hfq 只能作为研究 metadata | FEAT-02 / FEAT-06 | CR-017 / CR-015 | `tests/test_cr017_adjustment_leakage_gates.py` |
| RULE-04 | Factor / Label / Report 任一 production gate 未通过时，StrategyAdmissionPackage 不得 pass | FEAT-03 | CR-030 | `tests/test_cr030_strategy_admission_package.py` |
| RULE-05 | Backtrader / Qlib / external projects 只能作为参考或后续 Spike，不默认成为依赖或 truth | FEAT-04 / FEAT-07 | CR-025 / CR-030 | external reference guardrail tests |
| RULE-06 | Linux C 侧不得导入 xtquant，只能通过受控 REST client 调 Windows gateway | FEAT-05 | CR-019 / CR-020 | QMT client tests |
| RULE-07 | gateway health / capabilities / endpoint matrix 可见不等于真实 QMT / simulation / live 授权 | FEAT-05 / FEAT-07 | CR-019 / CR-020 | run gate and docs tests |
| RULE-08 | pre-trade risk 失败时 adapter 调用次数必须为 0 | FEAT-06 | CR-015 / CR-016 | risk gate tests |
| RULE-09 | CP2 / CP3 / CP5 / CP8 approved、Story verified、runbook 存在均不得隐式授权真实运行 | FEAT-07 / FEAT-08 | 全部高风险 CR | no-real-operation safety tests |
| RULE-10 | 文档必须同时说明已验证能力和不授权项 | FEAT-08 / FEAT-07 | README、USER-MANUAL、QMT runbook | docs guardrail tests |
| RULE-11 | 策略核心合同不得导入或直接调用 QMT / XtQuant / MiniQMT API | FEAT-09 / FEAT-07 | CR-046、CR047-candidate | static guardrail |
| RULE-12 | QMT terminal target 本 CR 只能定义策略入口、配置、导入步骤和 shadow 证据格式，不执行终端运行 | FEAT-09 | CR-046 | CP3/CP5/CP7 evidence review |
| RULE-13 | MiniQMT runner target 本 CR 只能定义安装设计、uv 隔离、启动/停止合同、日志和 kill switch，不真实安装或连接 | FEAT-09 / FEAT-07 | CR-046 | install dry-run design review |
| RULE-14 | 策略包验证证据必须区分 fixture/static/design pass 与 runtime verified | FEAT-09 / FEAT-08 | CR-046、后续 CR047 | docs guardrail |
| RULE-15 | CR047 首个具体策略交付必须消费 CR046 策略包合同，不得在 CR046 内提前交付 | FEAT-09 | CR047-candidate | follow-up gate |
| RULE-16 | CR051 研究框架完善必须反向消费 StrategyCoreContract 和 StrategyValidationEvidence，不得扩大 CR046 范围 | FEAT-03 / FEAT-09 | CR051-candidate | follow-up tracking |
