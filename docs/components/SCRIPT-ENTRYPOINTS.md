# 组件说明：脚本入口与命名治理

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| v1.0 | 2026-07-11 | meta-doc | 增量补充 CR-163 mature multifactor research lineage CLI 参数和 fail-closed 行为。 |

脚本入口按长期能力域组织，根目录中的 `cr*`、`chapter*`、`stage*` 命名只作为历史兼容入口保留。新文档和新自动化应优先使用稳定路径。

## 1. 设计刷新判断

| 文档类型 | 本轮判断 | 原因 |
|---|---|---|
| Blueprint | 不重开完整蓝图 | 本轮不改变产品能力边界，只收敛脚本入口、公共 CLI helper 和命名治理。 |
| HLD | 不新建完整 HLD | 不引入新外部系统、权限边界或运行时架构；只增加稳定 facade 和 guardrail。 |
| Feature design | 需要轻量刷新 | 脚本入口属于用户可见操作面，需要记录稳定入口、legacy 兼容和新增质量检查。 |

若后续把数据湖回填、异象研究、多因子策略搜索的实现真正合并为一个 orchestrator，再补充独立 HLD。

## 2. 稳定入口目录

| 目录 | 责任 |
|---|---|
| `scripts/data_lake/` | 数据湖回填、修复、发布和 readiness。 |
| `scripts/research/` | 因子实证、因子模型、异象研究、稳健性、多因子策略研究。 |
| `scripts/qmt/` | QMT runtime 输入、preflight、readonly smoke、simulation operator。 |
| `scripts/quality/` | 文档、证据、包结构和脚本命名检查。 |

## 3. 兼容策略

| 规则 | 说明 |
|---|---|
| 旧入口归档 | `scripts/cr*.py`、`scripts/run_chapter*.py`、`scripts/run_stage*.py` 已移动到 `scripts/legacy/cr/`。 |
| 新入口优先 | 新文档、测试和人工命令应使用稳定目录。 |
| 新增根层不稳定入口被阻断 | `scripts/quality/check_script_entrypoints.py` 禁止根层出现 `cr*`、`chapter*`、`stage*` 主入口，并检查归档脚本存在。 |
| CR 编号保留为历史来源 | CR 编号可出现在 archive、run id、manifest lineage、过程证据中，不作为长期入口名。 |

## 4. 当前稳定入口

| 能力 | 稳定入口 | legacy 来源 |
|---|---|---|
| 市场数据回填 | `scripts/data_lake/backfill_market_data.py` | `scripts/legacy/cr/cr034_chapter3_backfill.py` |
| 缺口补数 | `scripts/data_lake/backfill_missing_market_data.py` | `scripts/legacy/cr/cr018_real_backfill_missing_data.py` |
| 数据 readiness | `scripts/data_lake/check_market_data_readiness.py` | `scripts/legacy/cr/chapter3_real_data_readiness.py` |
| production_strict readiness audit | `scripts/data_lake/run_data_lake_readiness_audit.py` | CR140 迁移前的实验侧审计脚本 |
| 重复键画像 | `scripts/data_lake/profile_duplicate_keys.py` | `scripts/legacy/cr/cr139_gateb_batch0_duplicate_profile.py` |
| 重复键拆分规划 | `scripts/data_lake/plan_duplicate_resolution.py` | `scripts/legacy/cr/cr139_gateb_batch2_remaining_split_planning.py` |
| catalog current truth 画像 | `scripts/data_lake/profile_current_truth.py` | 新稳定入口；不扫描历史 run_id，除非 catalog 显式指向 |
| 物理分区迁移规划 | `scripts/data_lake/plan_physical_partition_migration.py` | 新稳定入口；不依赖 legacy |
| 物理分区迁移执行 | `scripts/data_lake/execute_physical_partition_migration.py` | 新稳定入口；默认 dry-run；执行 copy/catalog 更新必须带 approval id 和 created_at；支持 `--datasets` canary 分批执行 |
| 价格涨跌停清理 | `scripts/data_lake/cleanup_price_limit_lifecycle.py` | `scripts/legacy/cr/cr018_price_limit_lifecycle_cleanup.py` |
| release 发布 | `scripts/data_lake/publish_market_data_release.py` | `scripts/legacy/cr/cr018_release_catalog_publish.py` |
| 数据修复 | `scripts/data_lake/repair_market_data.py` | `scripts/legacy/cr/cr012_limited_window_lake_repair.py` |
| 因子实证 | `scripts/research/run_factor_empirical_research.py` | `scripts/legacy/cr/run_chapter3_empirical.py` |
| 因子模型验证 | `scripts/research/run_factor_model_validation.py` | `scripts/legacy/cr/run_chapter4_factor_models.py` |
| 异象发现 | `scripts/research/run_anomaly_discovery.py` | `scripts/run_anomaly_discovery.py` |
| 异象研究 | `scripts/research/run_anomaly_research.py` | `scripts/legacy/cr/run_chapter5_anomalies.py` |
| 因子稳健性 | `scripts/research/run_factor_robustness.py` | `scripts/legacy/cr/run_chapter6_factor_robustness.py` |
| 因子组合实践 | `scripts/research/run_factor_practice.py` | `scripts/legacy/cr/run_chapter7_factor_practice.py` |
| 多因子策略候选 | `scripts/research/run_multifactor_strategy_candidates.py` | `scripts/run_multifactor_strategy_candidates.py` |
| 多因子策略研究 | `scripts/research/run_multifactor_strategy_research.py` | `scripts/legacy/cr/run_stage3_mature_multifactor_research.py` |
| QMT runtime 输入 | `scripts/qmt/build_multifactor_runtime_inputs.py` | `scripts/build_qmt_multifactor_runtime_inputs.py` |
| runtime preflight | `scripts/qmt/build_runtime_preflight_evidence.py` | `scripts/legacy/cr/build_cr104_runtime_preflight_evidence.py` |
| readonly smoke evidence | `scripts/qmt/collect_readonly_smoke_evidence.py` | `scripts/legacy/cr/collect_cr099_runner_readonly_smoke.py` |
| QMT simulation operator | `scripts/qmt/run_multifactor_simulation_operator.py` | `scripts/run_qmt_multifactor_simulation_operator.py` |

## 5. 公共函数抽象

研究 CLI 共享的内存预算、JSON 安全转换和浮点列表解析收敛到 `engine/research_cli.py`。脚本不应继续复制 `_json_safe`、`max_rss_bytes`、`memory_budget_summary`、`enforce_memory_budget` 等工具函数。

## 6. Mature Multifactor Research Lineage 参数

稳定入口 `scripts/research/run_multifactor_strategy_research.py` 接受以下成对参数：

| 参数 | 含义 | 约束 |
|---|---|---|
| `--lineage-spec <path>` | experiment-family lineage spec 路径。 | 必须与 `--lineage-root <path>` 同时提供；无效 spec 必须 `blocked`。 |
| `--lineage-root <path>` | family recorder / seal 的根路径。 | 必须与 `--lineage-spec <path>` 同时提供。 |

参数行为是严格的三态边界：

- 两个参数都不提供：允许兼容运行，但 admission lineage 为 `typed_unavailable`。
- 只提供任意一个参数，或提供的 lineage spec 无效：fail-closed 为 `blocked`，不启动或恢复一个不完整 family。
- 两个参数均有效：仍不能仅凭参数存在就声明 lineage `present`；未来 instrumented run 必须完成 family seal 和完整 validation，准入投影才可为 `present`。

发生 crash 或发现 malformed tail 时，CLI 不对原 family 做 resume、尾部截断修复或继续追加；应保留失败 family，并以新的 family identity 重启。10,000 trial 路径仅用于 characterization，不构成吞吐量、容量或恢复 SLA。该入口不计算 `effective_trial_count` 或 C1，也不回填 CR155。
