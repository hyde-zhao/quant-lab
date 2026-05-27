---
artifact: "CR-005 Tushare 5000 + Backtrader quality review"
reviewer: "meta-qa"
lane: "lane-quality"
round: 2
status: "completed-updated"
governance_mode: "review-gated"
created_at: "2026-05-17"
updated_at: "2026-05-17"
source_handoff: "process/handoffs/META-QA-CR005-TUSHARE-BACKTRADER-QUALITY-2026-05-17.md"
change_id: "CR-005"
---

# Review Findings

## 1. 审查范围

- 目标对象：CR-005 Tushare 5000 数据层整改与 Backtrader optional backend 质量策略。
- 审查目标：默认离线、凭据安全、数据质量双状态、PIT as-of join、复权口径、Pandas 数据层与 Backtrader 边界、CP5 前回归策略。
- 审查依据：`AGENTS.md` 的质量 lane、CR-005 变更单、`process/STATE.md`、`process/TEST-STRATEGY.md`、CR005-S02/S03/S06 Story、现有 HLD/ADR/Backlog/Development Plan、`market_data/**` 与 `engine/**` 代码事实。
- 写入边界：仅更新 `process/TEST-STRATEGY.md` 和本 QA 检查文件；未修改 HLD、ADR、Backlog、Development Plan、STATE、handoff dispatch、CP3/CP4 检查结果或人工审查稿、业务代码、依赖声明或锁文件。

## 2. Findings

### 执行证据

| 证据 | 结果 | 说明 |
|---|---|---|
| `TUSHARE_TOKEN= uv run --python 3.11 pytest -q` | 初次未进入 pytest | sandbox 中 `uv` 默认 cache `<uv-cache-home>` 只读，报 `Could not acquire lock`。 |
| `UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q` | PASS | 56 passed in 4.12s；当前默认路径不需要 `TUSHARE_TOKEN`，且未安装 Backtrader optional 依赖。 |
| `rg -n "backtrader\|tushare" pyproject.toml uv.lock market_data engine tests` | PASS / GAP | 未发现 `backtrader` 依赖；Tushare 仅存在 fail-fast adapter、registry/env var 名和测试边界。 |
| 危险命令 / Prompt 注入扫描 | PASS | 未发现 `rm -rf`、`sudo`、`curl`、`wget`、`eval`、`subprocess`、`os.system`、Prompt 注入模式。 |
| 凭据模式扫描 | REQUIRED finding | 未发现真实凭据；但现有脱敏测试含 `plain-token`、`secret-value` 哨兵字面量，CR-005 新增测试不得继续引入 token-like fixture value。 |
| 2026-05-17 文档复核 | PASS / pending manual | `process/STATE.md` 显示 CR-005 CP3/CP4 自动预检 PASS，人工审查稿待用户确认；HLD/ADR/Backlog/Plan 已有 CR-005 增量，CR005-S02/S03/S06 Story 已存在且为 `draft`。 |
| CR005-S02/S03/S06 Story 复核 | REQUIRED finding | Story 已覆盖部分复权、quality gate、Backtrader optional 边界，但 PIT as-of join、`adj_factor` 与统一 adjusted price、Backtrader 仅消费干净 factor panel/score/feed 仍需进入 CP5 LLD。 |

### Findings 表

<!-- findings-table -->

| ID | Severity | Rule Ref | Evidence | Impact | Suggestion | Anchor |
|----|----------|----------|----------|--------|------------|--------|
| F-QA-CR005-001 | 严重 | `CP3/CP4 before CP5` | CP3/CP4 自动预检已 PASS 且人工稿已生成，但 `process/STATE.md` 明确仍等待用户审查 `checkpoints/CP3-CR005-HLD-REVIEW.md` 和 `checkpoints/CP4-CR005-STORY-PLAN-REVIEW.md`。 | 人工确认前进入 CP5 会绕过 Meta Flow 门控；后续 LLD 和实现授权无效。 | 保持 CR-005 阻断在 CP5 之前；用户人工确认 CP3/CP4 后才允许起草或确认 CR-005 LLD。 | `process/STATE.md` |
| F-QA-CR005-002 | 严重 | `PIT as-of join quality gate` | CR005-S02/S03/S06 已提到 `available_at` 和 quality gate，但未显式要求非行情数据按 `available_date` / `effective_date` / `available_at` 做 as-of join，也未列出 `available_at/effective_date > decision_date` 负例。 | 财报、成分、权重、事件或其他非行情数据可能穿越到当日输入，污染 factor panel、score 和 Backtrader feed。 | CP5 前要求相关 LLD 写入 PIT 决策表和测试：`available_at/effective_date > decision_date` 的记录不得进入当日输入；缺 PIT 字段 fail fast 或 structured unavailable。 | `process/stories/CR005-S02-tushare-dataset-schema-normalization.md`; `process/stories/CR005-S03-multidataset-quality-catalog-readers.md`; `process/stories/CR005-S06-backtrader-optional-backend.md` |
| F-QA-CR005-003 | 严重 | `adjusted price consistency` | CR005-S02 已要求复权冲突失败，但未明确数据层保存 `adj_factor` 与 adjusted price，也未要求收益、技术指标、forward return 统一使用 adjusted price。 | 同一次研究链路混用 `qfq` / `hfq` / `none` 或未复权价格，会导致收益、指标、候选分和回测结果不可比。 | CP5 前要求 LLD 固化 `adj_factor`、adjusted price、`adjustment_policy` 决策表；缺字段 fail fast 或 structured unavailable；混用复权口径必须 BLOCKING。 | `process/stories/CR005-S02-tushare-dataset-schema-normalization.md` |
| F-QA-CR005-004 | 严重 | `Backtrader clean input boundary` | CR005-S06 已要求只读 canonical/gold + quality gate，但未显式限定 Backtrader 输入必须是 Pandas 数据层完成 PIT/复权/quality gate 后的干净 factor panel / score / feed。 | Backtrader adapter 若直接读 Tushare、connector、raw parquet 或自行做 PIT/复权，会绕过 reader quality policy 并复制数据层职责。 | CP5 前要求 CR005-S06 LLD 明确 Backtrader 只负责调仓、成交、成本、仓位、净值和风险分析；禁止直接读 Tushare/connector/raw parquet，禁止绕过 reader quality policy。 | `process/stories/CR005-S06-backtrader-optional-backend.md` |
| F-QA-CR005-005 | 严重 | `quality gate cannot be bypassed` | `market_data/readers.py` 当前 `del quality_policy`，catalog 缺失也允许读取已有 canonical。 | 如果 Backtrader adapter 直接复用当前 reader，会绕过 CR-005 要求的 local canonical/gold quality gate。 | CP5 前要求 reader 或 Backtrader adapter 强制消费 quality/catalog：`dataset_status=fail` 阻断，`warn` 披露，缺 quality fail-fast。 | `market_data/readers.py` |
| F-QA-CR005-006 | 严重 | `fetch_status vs dataset_status separation` | `market_data/validation.py` 已有双状态；`engine/data_loader.py` 仍只读取 legacy `quality_status`，metadata 未披露 `fetch_status` / `dataset_status`。 | CR-005 要求远端失败不得直接阻断本地合规只读回测；当前轻量回测与未来 Backtrader 接入需要统一消费双状态，否则决策口径漂移。 | 在 CR-005 LLD 中固化双状态决策表，并要求 loader/backtrader adapter 测试覆盖 fetch failed + dataset pass、fetch success + dataset fail。 | `market_data/validation.py`; `engine/data_loader.py` |
| F-QA-CR005-007 | 一般 | `Tushare dataset contract` | `market_data/source_registry.py` 当前 Tushare 只登记 `prices.daily`；CR-005 目标包括 `hs300_index`、`index_weights`、`trade_calendar`、`adj_factor`、复权价格等。 | 真实 Tushare 接入若不先冻结 exact interface -> target_dataset 映射，会造成 normalization、quality、catalog 和 reader 反复返工。 | CP5 前在 LLD 中列出每个 dataset 的 exact 接口、字段、PIT 字段、复权口径、coverage 分母和质量阈值。 | `market_data/source_registry.py`; CR-005 `建议 dataset` |
| F-QA-CR005-008 | 一般 | `credential fixture boundary` | `tests/test_market_data_runtime_storage.py` 使用 `plain-token` / `secret-value` 作为脱敏哨兵；未发现真实凭据。 | CR-005 明确 token 不得进入测试 fixture 或文档示例值，未来凭据扫描会对这类字面量产生歧义。 | CR-005 新增测试不得写 token-like 示例值；历史哨兵可在后续整改中替换为非凭据语义 sentinel，并在扫描规则中区分 env var name 与 value。 | `tests/test_market_data_runtime_storage.py` |

### Findings 变化

| 旧 Finding | 当前状态 | 变化说明 |
|---|---|---|
| F-QA-CR005-001：CR-005 未回写 HLD/ADR/Backlog/Plan | SUPERSEDED | CR-005 设计与 Story Plan 已回写，CP3/CP4 自动预检已 PASS；当前阻断改为 CP3/CP4 人工确认未完成。 |
| F-QA-CR005-002：Backtrader 无正式 Story | SUPERSEDED | CR005-S06 Story 已存在；当前阻断改为 Backtrader LLD 必须硬化干净输入、no raw、no connector、no quality bypass。 |
| F-QA-CR005-003 / 004 | ACTIVE | reader quality gate 与 fetch/dataset 双状态消费仍需进入 CR005-S03/S06 LLD 和实现验证。 |
| 新增 PIT / 复权 findings | ACTIVE | 用户追加的 PIT as-of join、`adj_factor` / adjusted price 和 Backtrader 边界已升级为 CP5 前 BLOCKING 质量门。 |

## 3. 汇总结论

- blocking_count: 6
- required_count: 2
- optional_count: 0
- recommended_next_action: `cp3-cp4-manual-review-then-cp5-lld-with-required-qa-gates`

### 质量门结论

| 维度 | 结论 | 说明 |
|---|---|---|
| 默认离线 | 当前基线 PASS；CR-005 准入需继续保持 | 临时 uv cache 下 `TUSHARE_TOKEN=` 全量 pytest 通过，未安装 Backtrader 也不影响当前默认路径。 |
| 凭据安全 | REQUIRED GAP | 未发现真实凭据；但 CR-005 必须禁止新增 token-like fixture value，并确保 token 值不进入 manifest/quality/catalog/log/error/doc。 |
| PIT 防未来函数 | BLOCKED before CP5 | 非行情数据 as-of join 与 future leak 负例必须进入 CR005-S02/S03/S06 LLD。 |
| 复权一致性 | BLOCKED before CP5 | `adj_factor`、adjusted price、`adjustment_policy` 与统一指标/收益输入必须进入 LLD。 |
| 数据质量 | BLOCKED before CP5 | 双状态字段已存在，但 reader/loader/backtrader 质量门消费关系未固化。 |
| Backtrader optional backend | BLOCKED before CP5 | CR005-S06 Story 已存在，但 LLD 必须限定干净 factor panel/score/feed 输入和职责边界。 |
| 回归策略 | PASS with required additions | 已在 `process/TEST-STRATEGY.md` 增补 CP5 前最小测试集、PIT/复权负例、Backtrader 边界、泄漏扫描和依赖组策略。 |

**总评结论**：CR-005 当前质量门为 `BLOCKED before CP5`。阻断原因不是当前默认 pytest 失败，也不是缺少 CR-005 Story；当前必须先完成 CP3/CP4 人工确认，并在 CP5 LLD 中硬化 PIT as-of join、复权 adjusted price、reader quality gate 和 Backtrader 干净输入边界。

### CP5 前新增测试清单

必须进入对应 CR-005 LLD 的最小测试：

| 测试项 | 阻断等级 | 覆盖目标 |
|---|---|---|
| `TUSHARE_TOKEN= uv run --python 3.11 pytest -q` | BLOCKING | 默认离线、无 token、无 Backtrader optional 依赖。 |
| socket 禁用下执行默认 market_data / engine tests | BLOCKING | 默认路径不联网；真实 adapter 不被隐式调用。 |
| Tushare disabled / missing credential / interface not allowlisted | BLOCKING | 结构化 fail-fast，不写 raw/manifest，不泄露 token。 |
| manifest/quality/catalog/log/stdout/stderr 凭据泄漏断言 | BLOCKING | token 值不落盘、不出日志、不进错误消息。 |
| PIT as-of join 正负例 | BLOCKING | `available_at/effective_date <= decision_date` 可进入当日输入；`>` 决策日不得进入 factor panel/score/feed。 |
| PIT 必填字段缺失 | BLOCKING | 非行情数据缺 `available_date` / `effective_date` / `available_at` 时 fail fast 或 structured unavailable。 |
| `adj_factor` / `adjustment_policy` 缺失 | BLOCKING | adjusted price 无法生成时 fail fast 或 structured unavailable。 |
| 复权口径混用 | BLOCKING | 同一次回测混用 `qfq` / `hfq` / `none` 必须阻断。 |
| 收益/技术指标/forward return 输入 lineage | BLOCKING | 三类计算必须使用统一 adjusted price，不得混用 raw close。 |
| fetch failed + dataset pass 的只读回测 | BLOCKING | 本地 canonical/gold 合规时不因远端失败直接阻断。 |
| fetch success + dataset fail 的只读回测 | BLOCKING | `dataset_status=fail` 或 `quality_status=fail` 必须阻断。 |
| reader/Backtrader 缺 quality 或 quality fail | BLOCKING | Backtrader 不绕过 quality gate。 |
| Backtrader 未安装但显式选择 backend | BLOCKING | 返回 `backend_unavailable` 或等价结构化状态；轻量回测默认路径照常通过。 |
| Backtrader 直接读 Tushare/connector/raw parquet 负例 | BLOCKING | adapter 只能消费干净 factor panel/score/feed，不得触达 connector/runtime/storage/raw。 |
| Backtrader 已安装 optional group 定向测试 | REQUIRED | 只负责调仓、成交、成本、仓位、净值和风险分析，输出与轻量回测对照。 |
| `pyproject.toml` 依赖组审查与 `uv lock --check` | REQUIRED | `backtrader` / Tushare provider 不进入默认依赖，锁文件由 uv 维护。 |

## 4. 待确认项

- CR-005 的 `available_date` / `effective_date` / `available_at` 字段是否按 dataset 分别必填，还是允许部分 dataset 用 structured unavailable 表达暂不可用。
- `adj_factor` 与 adjusted price 的落库字段名、复权计算公式和 `qfq` / `hfq` / `none` 支持范围需在 CR005-S02 LLD 中冻结。
- Backtrader optional 依赖采用 uv `backtest` group、`optional-backends` group，还是 PEP 621 optional extra；质量建议是非默认安装面。
- 历史脱敏测试中的 token-like 哨兵是否在 CR-005 开发前同步替换，还是仅在 CR-005 新增测试中禁止延续。
