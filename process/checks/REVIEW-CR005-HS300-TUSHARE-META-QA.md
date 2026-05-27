---
artifact: "CR-005 hs300_index missing benchmark + Tushare data-layer review"
reviewer: "meta-qa"
lane: "lane-quality"
round: 3
status: "completed"
governance_mode: "review-gated"
created_at: "2026-05-17"
change_id: "CR-005"
review_mode: true
---

# Review Findings

## 1. 审查范围

- 目标对象：CR-005 第三轮新增关注点：本地 `hs300_index` benchmark 缺失时，消费方必须返回 structured `unavailable` / `required_missing`，不得静默代理；同时数据层需要显式调用 Tushare 获取相关数据。
- 审查目标：数据准确性和可用性质量门、Tushare 显式 fetch/backfill 可验证性、消费层离线安全、Backtrader/实验/Data Loader 分层独立性、CP5 前测试清单和验收标准缺口。
- 审查依据：`AGENTS.md` review gate 与质量 lane 规则、`process/STATE.md`、`process/changes/CR-005-TUSHARE-5000-DATA-LAYER-REMEDIATION-2026-05-17.md`、`process/HLD.md`、`process/TEST-STRATEGY.md`、`process/checks/QA-CR005-QUALITY-REVIEW.md`、CR005-S01/S03/S04/S06 Story，以及 `market_data/readers.py`、`engine/data_loader.py`、`market_data/connectors/tushare.py` 代码事实。
- 写入边界：本文件为第三轮质量评审 findings；未修改 HLD、Story、测试策略、代码、依赖、数据或正式检查点。

## 2. Findings

### 执行证据

| 证据 | 结果 | 说明 |
|---|---|---|
| `process/STATE.md:11-12`、`:33-50` | 当前仍处 CP3/CP4 人工确认前 | CR-005 自动预检 PASS 但等待人工确认；CP5 前不得实现真实 Tushare、PIT/复权或真实数据写入。 |
| `process/changes/CR-005...md:24-35`、`:131-151`、`:157-170` | 方向正确 | CR 明确 Tushare 进入本地数据湖，消费方只读本地数据；默认测试离线；`hs300_index` 缺口进入 quality report。 |
| `process/HLD.md:969-974`、`:978-985`、`:1052-1079` | 方向正确但动作链不完整 | HLD 定义 Tushare 写湖、reader structured unavailable、benchmark 缺失 `unavailable/required_missing`；但缺少消费方返回状态到数据层 backfill/fetch 的可验证 next action 契约。 |
| `process/stories/CR005-S01...md:73-87`、`:110-124` | Tushare 安全边界明确 | S01 覆盖 import no-network、disabled、missing token、allowlist、dry-run no-network；但未要求 `hs300_index` backfill 正向链路。 |
| `process/stories/CR005-S03...md:76-89`、`:112-132` | 多 dataset quality/readers 有基础 | S03 要求双状态、coverage、quality gate 和 reader 不自动补数；但缺少 `hs300_index` 专项 coverage、缺口列表、重复键、日期分母、lineage 字段的硬门。 |
| `process/stories/CR005-S04...md:74-86`、`:107-120` | 消费方不代理基本满足 | S04 要求缺少 `hs300_index` 返回 `unavailable/required_missing` 且不联网、不静默代理；但 `旧路径可回退` 表述未排除回退到等权代理。 |
| `process/TEST-STRATEGY.md:290-308`、`:310-359` | CP5 前测试缺 hs300 专项 | 现有测试策略覆盖 Tushare、PIT、复权、quality、Backtrader，但没有 `hs300_index` 缺失状态、next action、backfill 后可用的端到端测试。 |
| `market_data/readers.py:26-60` | 当前 reader 只支持 prices 且忽略 quality_policy | 这是 CR-005 实现前事实；S03 已识别需扩展，但第三轮新增的 hs300 专项门仍需写入 CP5 LLD。 |
| `market_data/source_registry.py:86-90`、`market_data/connectors/tushare.py:19-53` | 当前 Tushare 仍 fail-fast 且 registry 仅 `prices.daily` | 这是正确的默认安全状态；但数据层真实 `hs300_index` fetch/backfill 尚无正向可验证契约。 |
| `engine/data_loader.py:128-157`、`experiments/run_experiment_13.py:313-318` | 旧消费层仍存在 legacy 质量口径和代理基准文字 | Data Loader 只消费 legacy `quality_status`；实验十三报告明确使用“基准代理”。CR005-S04 必须避免“旧路径回退”被解释为缺 hs300 时继续代理相对指标。 |

### Findings 表

<!-- findings-table -->

| ID | Severity | Rule Ref | Evidence | Impact | Suggestion | Anchor |
|----|----------|----------|----------|--------|------------|--------|
| F-QA-CR005-R3-001 | 严重 | `hs300_missing_next_action` | HLD 仅说明 `benchmark/read` 缺失时 structured unavailable、不联网、不补数，S04 仅要求 `available/unavailable/required_missing`；未定义返回体中的可操作 `next_action`、目标数据集、Tushare interface、日期范围、lake root、quality 重跑步骤。 | 消费方能正确失败，但用户或调度层无法从结构化状态稳定转入数据层 fetch/backfill；可用性质量门不可验证。 | 在 CR005-S04 LLD 和测试策略中要求 `unavailable/required_missing` payload 至少包含 `dataset=hs300_index`、`missing_range`、`quality_status`、`required`、`next_action.type=run_data_layer_backfill`、`source=tushare`、`interface=hs300_index.daily` 或 CP5 冻结等价值、`suggested_commands=[plan, fetch, normalize, validate/catalog]`；注意 next action 只提示数据层显式动作，消费方不得自动执行。 | `process/HLD.md:1066-1079`; `process/stories/CR005-S04-hs300-local-benchmark.md:74-86` |
| F-QA-CR005-R3-002 | 严重 | `data_layer_backfill_verifiability` | S01 验证场景止于 import no-network、disabled/missing token/allowlist、dry-run；S02/S03/S04 拆分了 schema、quality、resolver，但没有一条验收把 `hs300_index` 缺失 -> 数据层显式 Tushare plan/fetch -> raw/manifest -> canonical/gold -> quality/catalog -> resolver available 串起来。 | “此时需要让数据层调用 Tushare 获取相关数据”的变更需求没有可执行验收链；后续可能只实现 unavailable，却没有实现可控补数闭环。 | CP5 前补充跨 Story 验收：在禁网消费层用例中确认 resolver 只返回状态；在显式数据层命令用例中启用 source、allowlist、token spy/fake provider，验证 `hs300_index` 写入 raw/manifest、normalization 生成 canonical/gold、quality/catalog 记录 lineage，随后 resolver 从 `required_missing` 变为 `available`。真实网络测试仍应标记人工/显式环境，默认 pytest 使用 fake Tushare provider。 | `process/stories/CR005-S01-tushare-connector-real-lake-writer.md:73-124`; `process/stories/CR005-S04-hs300-local-benchmark.md:90-120`; `market_data/connectors/tushare.py:19-53` |
| F-QA-CR005-R3-003 | 严重 | `hs300_accuracy_gate` | CR005-AC-003 只写“coverage 缺口进入 quality report”；HLD `hs300_index` 最小字段为 `trade_date/index_code/close/pct_chg/source/source_run_id/available_at`；S03 验收使用“20 个字段或等价完整字段集”的泛化口径，S04 metadata 只要求 source/status/dataset/quality_status/coverage。 | hs300 基准可能覆盖不完整、重复、日期分母错误、字段类型或 pct_chg 不一致、lineage 不可追溯，但仍被消费方当成可用 benchmark。 | 对 `hs300_index` 增加专项 BLOCKING quality gate：coverage denominator 必须来自 `trade_calendar` open days；`index_code+trade_date` 唯一；请求区间缺口输出 gap list；日期可解析且在请求区间；`close/pct_chg` 数值合法；`source/source_run_id/interface/raw_path/checksum` 可追溯；`available_at <= decision_time`；benchmark 口径（价格指数/全收益等）进入 catalog 和 metadata。 | `process/changes/CR-005-TUSHARE-5000-DATA-LAYER-REMEDIATION-2026-05-17.md:157-164`; `process/HLD.md:978-985`; `process/stories/CR005-S03-multidataset-quality-catalog-readers.md:122-132`; `process/stories/CR005-S04-hs300-local-benchmark.md:114-120` |
| F-QA-CR005-R3-004 | 严重 | `no_silent_proxy_boundary` | S04 明确“缺少 `hs300_index` 时不得使用当前股票池等权代理静默替代”，但接口约定又写“旧路径可回退”；现有实验十三报告仍有“当前没有沪深300指数行情文件；表中‘基准代理’使用同股票池等权买入持有”。 | “旧路径回退”可能被实现为缺 benchmark 时继续输出代理基准，违反用户要求；实验、Backtrader 或报告层可能把 proxy 当相对收益基准。 | 在 CR005-S04 LLD 中把“旧路径回退”限定为保留旧 `--data-dir` / 本地价格数据读取，不得回退到代理 benchmark；若 legacy 报告保留等权买入持有，必须命名为 `proxy_baseline`，不得填充 `hs300_index` benchmark 字段，也不得计算声明为 hs300 的相对收益。 | `process/stories/CR005-S04-hs300-local-benchmark.md:74-86`; `process/stories/CR005-S04-hs300-local-benchmark.md:107-120`; `experiments/run_experiment_13.py:313-318` |
| F-QA-CR005-R3-005 | 严重 | `consumer_no_network_layering` | CR/S06/HLD 均禁止 Data Loader、实验、Backtrader 直接联网；代码事实中 `market_data/readers.py` 只读但当前仅支持 `prices` 且忽略 `quality_policy`，`engine/data_loader.py` 只消费 legacy `quality_status`，未消费 dataset-level `required_missing` 或 `fetch_status/dataset_status`。 | 分层方向正确，但消费层还没有统一处理 `hs300_index required_missing` 的 typed result；若用异常字符串或 legacy quality 迁就，Backtrader/实验/Data Loader 可能各自实现 fallback 或错误处理。 | CP5 LLD 应冻结一个消费层共享的 typed status/result 契约：消费方只接收 reader/benchmark resolver 的 `available/unavailable/required_missing/quality_failed`，不得导入 connector/runtime/storage；Data Loader 若不参与 benchmark 读取，也必须明确不处理 benchmark fetch，只透传或记录 structured metadata。 | `process/changes/CR-005-TUSHARE-5000-DATA-LAYER-REMEDIATION-2026-05-17.md:31-42`; `market_data/readers.py:26-60`; `engine/data_loader.py:128-157`; `process/stories/CR005-S06-backtrader-optional-backend.md:84-101` |
| F-QA-CR005-R3-006 | 一般 | `cp5_test_coverage_gap` | `process/TEST-STRATEGY.md` CP5 前测试矩阵覆盖 Tushare 启用、PIT、复权、reader quality gate 和 Backtrader，但没有 hs300 benchmark missing、next action、explicit backfill、proxy 禁止、post-backfill available 等专项测试。 | 第三轮新增关注点无法在 CP5 前被系统性验收，后续可能遗漏在 LLD 和 Story AC 之外。 | 在 TEST-STRATEGY 与 CR005-S04/S01/S03 LLD 中增加测试：缺 canonical/gold -> `unavailable`；`require_benchmark=true` -> `required_missing`；payload 带 next action；socket 禁用下消费方不联网；显式数据层 fake Tushare backfill 后 resolver available；coverage gap/duplicate/date invalid/source lineage fail；proxy fallback 命中数为 0。 | `process/TEST-STRATEGY.md:290-359`; `process/stories/CR005-S04-hs300-local-benchmark.md:99-120` |

### 已满足项

| 维度 | 当前判定 | 证据 |
|---|---|---|
| 消费方不得自动联网 | 基本满足，需在 LLD 测试中保持 | CR 明确 Data Loader/实验只读本地数据，Backtrader 不联网；S04 forbidden 包含 `market_data/connectors/**`，S06 禁止 connector/runtime/storage 与 `TUSHARE_TOKEN`。 |
| Tushare 默认安全 | 当前代码事实满足 fail-fast 默认 | `market_data/connectors/tushare.py` 当前未真实联网；缺 token、未 allowlist、source disabled 均返回结构化错误。 |
| Backtrader 分层 | 设计方向满足，需等待 CR005-S02/S03/S04 契约 | S06 依赖 S02/S03/S04，且明确 Backtrader 不做 PIT/复权、不读取 Tushare、不联网。 |
| CP5 前不得实现 | 满足 | `STATE.md` 与 CR-005 均显示 CP3/CP4 待人工确认，CP5 前不得实现真实调用或写真实数据。 |

## 3. 汇总结论

- blocking_count: 5
- required_count: 1
- optional_count: 0
- recommended_next_action: `revise-cp5-lld-and-test-strategy-before-implementation`

### Quality Gate 结论

| 质量门 | 结论 | 说明 |
|---|---|---|
| 数据准确性 | BLOCKED before CP5 | `hs300_index` 已列为 P0，但 coverage、缺口、重复、日期分母、字段合法性、source lineage、catalog/quality 专项字段不够硬。 |
| 可用性 | BLOCKED before CP5 | `unavailable/required_missing` 方向正确，但缺少可操作 next action 与显式数据层 backfill 后可用的验收链。 |
| 安全与离线 | PASS with required hardening | 默认离线、token 不泄漏、消费层不联网的规则充分；需增加 hs300 场景的 socket 禁用和 token spy 测试。 |
| 分层独立性 | PASS with blocking clarification | Tushare 写湖、reader 只读、Backtrader optional 的方向合理；但 S04 “旧路径回退”必须排除 proxy benchmark，消费层 typed status 契约要统一。 |
| CP5 前测试与验收 | REQUIRED GAP | 现有 TEST-STRATEGY 缺 hs300 专项测试，需要补入 CR005-S01/S03/S04/S06 LLD 的最小测试清单。 |

**总评结论**：相关文档“不静默代理、消费方不联网、Backtrader 不越层”的方向基本满足，但尚未完全满足用户新增变更需求。关键缺口是：`hs300_index` 缺失后的 structured 状态没有可操作 next action，且数据层显式 Tushare fetch/backfill 到 quality/catalog 再到 resolver available 的链路尚不可验证。CR-005 应在 CP5 LLD 前补强上述阻断项；补强前不建议进入实现。

### 建议补充的 CP5 前测试

| 测试项 | 阻断等级 | 覆盖目标 |
|---|---|---|
| `resolve_hs300_benchmark` 缺本地 canonical/gold | BLOCKING | 返回 `status=unavailable`，不使用 proxy，不联网，payload 含缺失 dataset/date range/quality。 |
| `require_benchmark=true` 缺本地基准 | BLOCKING | 返回 `status=required_missing` 或等价 typed error，且包含 `next_action`。 |
| structured next action schema | BLOCKING | `next_action` 指向数据层显式 backfill，不由消费方自动执行；包含 source/interface/lake_root/date_range/commands。 |
| 显式数据层 fake Tushare backfill | BLOCKING | plan/fetch/normalize/validate/catalog 后 `hs300_index` 从 missing 变 available。 |
| hs300 coverage gap | BLOCKING | 缺交易日进入 quality CSV/catalog，required 模式阻断，非 required 模式只返回 unavailable 并披露缺口。 |
| hs300 duplicate key | BLOCKING | `index_code+trade_date` 重复时 dataset_status fail，reader/resolver 不可用。 |
| hs300 lineage | BLOCKING | quality/catalog/metadata 包含 source、interface、source_run_id、manifest run、raw checksum 或等价 lineage。 |
| no silent proxy scan | BLOCKING | 缺 `hs300_index` 时实验/Backtrader/Data Loader 不调用等权代理填充 hs300 字段；proxy 只能作为显式 `proxy_baseline` 披露。 |
| consumer no-network socket block | BLOCKING | 禁用 socket 后实验、Data Loader、Backtrader benchmark 读取路径仍不尝试联网。 |
| token leak spy | BLOCKING | `TUSHARE_TOKEN` 值不进入 next_action、manifest、quality、catalog、stdout/stderr、日志或错误消息。 |

## 4. 待确认项

- `hs300_index` 的 benchmark 口径仍为 OPEN：价格指数、全收益指数或其他口径需在 CR005-S04 LLD 冻结，并写入 catalog/metadata。
- `hs300_index.daily` 是否作为最终 exact interface 名称，还是采用 Tushare 原生接口名 `index_daily` 映射为 target_dataset，需要 CP5 冻结。
- `required_missing` 是否作为异常抛出、typed result 返回，或二者并存，需要在 reader/benchmark resolver 契约中统一，避免实验和 Backtrader 各自解释。
