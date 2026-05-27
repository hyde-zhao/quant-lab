---
constraint_id: "CR004-QUALITY-DATALOADER-CONFIRMATION-2026-05-17"
status: "approved-by-user"
created_at: "2026-05-17T13:00:54+08:00"
approved_by: "user"
applies_to:
  - "CR-004"
  - "STORY-003"
  - "STORY-004"
  - "STORY-016"
  - "STORY-017"
source_checkpoint:
  - "checkpoints/CP5-CR004-BATCH-A-LLD-REVIEW.md"
---

# CR-004 质量报告与 Data Loader 补充确认约束

本文记录用户在 CP5 批次 A 审查中给出的“带约束通过”协议。它不扩大 STORY-014 / STORY-015 的实现范围；它约束后续质量报告、canonical validation、reader、CLI、Data Loader 与相关测试的设计和实现。

## 1. 质量报告契约

| 编号 | 约束 | 执行要求 |
|---|---|---|
| Q-01 | 第一版质量报告固定输出 CSV 与 Markdown | CSV 是 canonical source；Markdown 仅作为人类可读渲染，不得作为机器解析入口。 |
| Q-02 | CSV 复杂列表字段使用 JSON 字符串 | 字段名必须以 `_json` 后缀命名，例如 `failed_symbol_dates_json`、`missing_required_fields_json`。 |
| Q-03 | raw 到 dataset 只允许显式映射 | 只允许 `target_dataset` 或 exact interface 映射；禁止模糊匹配、相似度匹配、contains 匹配或自动猜测。 |
| Q-04 | prices 缺失率主分母固定披露 | 第一版主分母为 `open_trade_dates_in_requested_range * target_symbols`；报告必须输出 `denominator_mode`。 |
| Q-05 | non-PIT 分母风险必须披露 | 当股票池不是 PIT 时，报告必须说明该口径可能把未上市、退市、停牌或非有效股票计入缺失。 |
| Q-06 | 区分 fetch 质量和 dataset 质量 | 报告必须同时输出 `fetch_status` 与 `dataset_status`；不得只输出一个泛化 `status`。 |
| Q-07 | 本地 parquet 合规时不因 fetch 失败一律 fail | 数据源失败但本地 parquet schema 合规、覆盖 requested range、缺失率低于阈值、freshness 满足要求时可 `pass`；部分覆盖或轻微影响时 `warn`；关键字段缺失、schema 不合规、覆盖不足或缺失率超阈值时 `fail`。 |
| Q-08 | 第一版接受 non-PIT 股票池 | 缺少 `is_pit_universe` 时不得静默处理，必须设置 `is_pit_universe=false`，并强制披露 `universe_mode`、`pit_status` 与 survivorship bias 风险。 |
| Q-09 | 阈值必须显式配置 | `prices_missing_rate_pass`、`prices_missing_rate_warn`、`prices_missing_rate_fail` 等阈值不得写死在代码里，必须来自配置或显式默认配置常量。 |
| Q-10 | 每个 dataset 必须输出 coverage 信息 | 至少包含 `requested_start`、`requested_end`、`actual_start`、`actual_end`、`requested_symbols_count`、`actual_symbols_count`、`open_trade_dates_count`、`expected_rows`、`actual_rows`、`missing_rows`、`missing_rate`。 |
| Q-11 | 质量报告必须可复现 | 至少输出 `run_id`、`generated_at`、`source_name`、`source_interface`、`target_dataset`、`input_config_hash`。 |

## 2. Data Loader 契约

| 编号 | 约束 | 执行要求 |
|---|---|---|
| L-01 | 质量报告缺失 fallback 只用于探索 | 缺质量报告时允许内存 `calculate_quality(...)` 重算摘要，但仅作为 exploratory fallback / 非验收主路径；fallback 结果必须标记 `derived_quality_summary=true`。 |
| L-02 | `quality_policy` 不允许放行 fail | 第一版 `allow_warn` 只能放宽 `warn`，不能放宽 `fail`；不得引入 `allow_fail`、`force_run`、`ignore_quality` 等绕过质量门禁的选项。 |
| L-03 | Markdown 不作为机器入口 | Data Loader 机器解析入口仅允许 CSV 或内存质量摘要；Markdown 仅为人工材料。 |
| L-04 | PIT 股票池声明必须完整 | 声称 PIT 的股票池如果缺 `snapshot_date` 或 `available_at`，第一版必须拒绝运行。 |
| L-05 | 固定非 PIT 股票池允许 warn 继续 | 必须披露 survivorship bias；若存在 `available_at`，还应校验 `available_at <= load_as_of`，避免未来函数。 |
| L-06 | 返回对象必须带质量决策原因 | 返回对象或 metadata 至少包含 `quality_status`、`quality_policy`、`allow_warn`、`quality_source`、`quality_decision_reason`。 |
| L-07 | Data Loader 不自动修复数据 | 只做加载、校验、拒绝或放行；不得补缺失、重采样、自动填充价格、自动修复股票池或自动生成质量报告。 |
| L-08 | warn 语义要细分 | 第一版至少区分 `warn_non_pit_universe`、`warn_source_fetch_failed_but_local_valid`、`warn_minor_missing_rate`、`warn_markdown_report_ignored`。 |

## 3. 文件与实现边界

| 编号 | 约束 | 执行要求 |
|---|---|---|
| B-01 | `engine/contracts.py` 只追加纯常量 | 不得引入 I/O、pandas、pyarrow、AKShare、dataclass、TypedDict、pydantic model 或业务逻辑。 |
| B-02 | STORY-004 实现范围固定 | LLD 确认后实现范围仅限 `engine/data_loader.py` 与 `engine/contracts.py`。 |
| B-03 | CR-004 批次 A 实现范围固定 | STORY-014/015 确认后仅允许按各自 LLD 的限定范围实现，不得进入 Data Loader、回测、扫描、候选报告、真实性增强、安装脚本或 `delivery/**`。 |
| B-04 | 测试只能使用临时 fixture | 确认后仍禁止写真实 `data/**`、`reports/**`、`delivery/**`；测试只能使用 `tmp_path` 下的 parquet fixture 和 `quality_report.csv` fixture。 |
| B-05 | 依赖顺序不得越级 | STORY-004 验证通过前，STORY-005/006 不得进入 active implementation；CR-004 后续 STORY 也必须按 DAG 和 CP5 门控推进。 |

## 4. 质量门禁

| 编号 | 门禁 | 通过条件 |
|---|---|---|
| G-01 | fetch/dataset 双状态门禁 | 所有质量报告和 loader metadata 必须同时披露 `fetch_status` 与 `dataset_status`，并按 dataset 质量而不是 fetch 成败单独决定是否可读。 |
| G-02 | 显式阈值门禁 | 缺失率、freshness、覆盖率等阈值必须可从配置或常量追溯，测试不得依赖代码内隐藏魔法数。 |
| G-03 | coverage 完整门禁 | 每个 dataset 必须输出请求覆盖、实际覆盖、预期行数、实际行数、缺失行数和缺失率，字段缺失即 fail。 |
| G-04 | 可复现性门禁 | 每份质量报告必须包含 `run_id`、`generated_at`、source/interface、target dataset 和 `input_config_hash`，缺失即 fail。 |

## 5. 审批结论

- 结论：接受，但必须按本文件约束执行。
- 对 STORY-014 / STORY-015：CP5 批次 A 可推进实现，前提是不得越过各自 LLD 的文件边界。
- 对 STORY-003 / STORY-004 / STORY-016 / STORY-017：后续修订、实现和验证必须消费本约束文件；若旧 LLD 与本文件冲突，以本文件为当前用户确认协议。
