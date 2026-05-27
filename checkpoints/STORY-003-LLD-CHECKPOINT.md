---
checkpoint_id: "STORY-003-LLD"
checkpoint_type: "story-lld-confirmation"
story_id: "STORY-003"
story_title: "标准化 parquet 与数据质量报告"
story_slug: "parquet-quality-report"
status: "confirmed"
confirmed: true
created_by: "meta-po"
created_at: "2026-05-14"
updated_at: "2026-05-15"
lld_path: "process/stories/STORY-003-parquet-quality-report-LLD.md"
story_path: "process/stories/STORY-003-parquet-quality-report.md"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
---

# STORY-003 LLD 人工确认检查点

> 检查点 ④：Story LLD 确认。用户已确认通过，允许 STORY-003 按 LLD 限定范围进入实现。

## 1. 门控结论

`STORY-003` LLD 人工确认已通过。

用户明确回复 `确认通过`，语义记录为 `STORY-003` LLD 人工确认通过。meta-po 已将 LLD `confirmed=true`，并将 Story 推进到 `lld-approved`，分派 meta-dev 开始实现。

实现范围严格限定为：`engine/normalizer.py`、`engine/quality.py`，以及仅追加 parquet schema version、dataset 名称、质量报告字段和格式常量的 `engine/contracts.py`。测试可使用临时目录生成 parquet 与质量报告样例；禁止写入真实 `data/*.parquet`、真实 `reports/data_quality_report.*`、`delivery/**` 或安装脚本。

## 2. 复核对象

| 对象 | 路径 | 复核结果 |
|---|---|---|
| 运行态状态 | `process/STATE.md` | 当前阶段为 `story-execution`，active Story 为 `STORY-003`，`story_lld_confirmed=true` |
| Story 状态汇总 | `process/STORY-STATUS.md` | 当前门控为 `implementation`，`STORY-003` 状态为 `lld-approved` |
| Story 卡片 | `process/stories/STORY-003-parquet-quality-report.md` | 存在，映射 REQ/HLD/ADR，frontmatter 已更新为 `status=lld-approved` |
| LLD 文档 | `process/stories/STORY-003-parquet-quality-report-LLD.md` | 存在，frontmatter 已更新为 `status=confirmed`、`confirmed=true` |
| 开发计划 | `process/DEVELOPMENT-PLAN.yaml` | W0 为串行 Wave，`STORY-003` 依赖 `STORY-001` 与 `STORY-002` |
| HLD | `process/HLD.md` | 相关章节覆盖标准化 parquet、质量报告、数据准备流程、失败路径和 M0 落地 |
| ADR | `process/ARCHITECTURE-DECISION.md` | ADR-003 与 ADR-006 分别约束复权口径、质量阈值和降级行为 |

## 3. Frontmatter 契约复核

| 字段 | 期望 | 实际 | 结论 |
|---|---|---|---|
| `story_id` | `STORY-003` | `STORY-003` | 通过 |
| `status` | `confirmed` | `confirmed` | 通过 |
| `confirmed` | `true` | `true` | 通过 |
| `tier` | 必填 | `L` | 通过 |
| `shared_fragments` | 必填且指向 HLD/ADR 依据 | HLD §8.3、§8.5、§12.1、§12.4；ADR-003、ADR-006 | 通过 |
| `open_items` | 必填，若有阻塞项不得进入确认 | `0` | 通过 |
| `source_story` | Story 卡片路径 | `process/stories/STORY-003-parquet-quality-report.md` | 通过 |
| `source_hld` | HLD 路径 | `process/HLD.md` | 通过 |
| `source_adr` | ADR 路径 | `process/ARCHITECTURE-DECISION.md` | 通过 |

## 4. 14 章节契约复核

LLD 文档包含 14 个编号可见章节，并保留独立人工确认区。

| # | 章节 |
|---:|---|
| 1 | Goal |
| 2 | Requirements（Functional / Non-Functional） |
| 3 | 模块拆分与职责 |
| 4 | 代码结构与文件影响范围 |
| 5 | 数据模型与持久化设计 |
| 6 | API / Interface 设计 |
| 7 | 核心处理流程 |
| 8 | 技术设计细节 |
| 9 | 安全与性能设计 |
| 10 | 测试设计 |
| 11 | 实施步骤 |
| 12 | 风险、难点与预研建议 |
| 13 | 回滚与发布策略 |
| 14 | Definition of Done |

## 5. LLD 摘要

`STORY-003` 设计目标是从 `data/raw/**` 与 `data/manifests/data_prep_manifest.jsonl` 派生三类标准化 parquet，并输出机器可读 CSV 与人工可读 Markdown 质量报告，作为后续 `STORY-004` 离线 Data Loader 的输入门槛。

允许的后续实现模块限定为：

| 模块 / 文件 | 允许内容 |
|---|---|
| `engine/normalizer.py` | raw JSONL 读取、exact interface/dataset 映射、字段别名转换、schema 校验、重复键和异常价格处理、parquet 原子写入 |
| `engine/quality.py` | parquet/manifest 质量计算、缺失率分母、新鲜度算法、数据源失败降级、未来函数和幸存者偏差披露、CSV/Markdown 报告渲染 |
| `engine/contracts.py` | 仅追加 parquet schema version、dataset 名称、质量报告字段和格式常量；不得加入 I/O 或运行逻辑 |
| `data/*.parquet` | 仅在 LLD 确认后的实现运行或测试隔离目录中生成标准化 parquet |
| `reports/data_quality_report.csv` / `.md` | 仅在 LLD 确认后的实现运行或测试隔离目录中生成质量报告 |

关键设计点已覆盖：

| 设计点 | LLD 结论 |
|---|---|
| parquet schema | `prices` 必含 `trade_date,symbol,close`；`index_members` 必含 `symbol`；`trade_calendar` 必含 `trade_date` |
| 质量状态 | 仅允许 `pass`、`warn`、`fail` |
| fail 条件 | 必需字段缺失、覆盖缺口、未解决重复键、异常价格、请求区间缺失率 `> 5%` |
| warn 条件 | `0 < missing_rate <= 5%`，或失败批次不影响请求区间但需披露 |
| 缺失率分母 | `open_trade_dates_in_requested_range * target_symbols` |
| 新鲜度 | 同时计算交易日新鲜度和自然日新鲜度，测试需注入固定 `as_of_date` |
| 复权口径 | 默认 `qfq`，同一次运行混用 `adjustment_policy` 为 fail |
| 偏差披露 | 缺 PIT 字段时 `is_pit_universe=false`，报告必须包含 `survivorship_bias_note` |
| 失败回滚 | parquet/report 写入失败时保留旧 parquet，删除临时文件，不清理 raw/manifest |

## 6. HLD / ADR 一致性复核

| 依据 | 要求 | LLD 覆盖情况 | 结论 |
|---|---|---|---|
| HLD §8.3 | 三类 parquet 必需字段、可选字段和失败行为 | LLD §2、§5、§8 明确字段、类型、缺省与 fail 行为 | 通过 |
| HLD §8.5 | 质量报告 `pass/warn/fail` 规则 | LLD §2、§6、§7、§8 覆盖 schema、覆盖、缺失率、重复键、异常价格、失败和新鲜度 | 通过 |
| HLD §12.1 | 数据准备流程中 raw -> normalizer -> quality report | LLD §7 主流程与时序图保持一致 | 通过 |
| HLD §12.4 | 前置校验、失败路径和可降级条件 | LLD §7、§9、§13 定义失败路径、结构化错误和降级策略 | 通过 |
| HLD §16 M0 | M0 交付标准化 parquet、manifest、质量报告 | LLD 限定在 W0/M0 的标准化 parquet 与质量报告范围 | 通过 |
| ADR-003 | 默认 `qfq`，混用复权口径必须拒绝运行，报告记录 `adjustment_policy` | LLD §2、§5、§8、§10 覆盖默认值、混用 fail 和报告字段 | 通过 |
| ADR-006 | `warn` 可继续但披露，`fail` 阻塞请求区间，无质量报告主路径失败 | LLD §2、§7、§8、§13 覆盖质量阈值、降级和 STORY-004 拒绝运行条件 | 通过 |

## 7. 越界与禁止范围复核

| 范围 | 复核结论 |
|---|---|
| 代码实现 | 本轮未实现代码；LLD 确认前仍禁止实现 `engine/normalizer.py`、`engine/quality.py` 或修改 `engine/contracts.py` |
| 数据生成 | 本轮未生成 parquet、raw、manifest 或质量报告；LLD 确认前禁止生成 `data/*.parquet`、`reports/data_quality_report.*` |
| 下游 Story | LLD 明确不实现 `engine/data_loader.py`、回测、扫描、候选、策略、PIT provider、交易状态、涨跌停和偏差审计 |
| 网络调用 | LLD 明确不导入或调用 AKShare；测试必须使用 fixture、fake 或临时目录 |
| 交付目录 | LLD 明确不写 `delivery/**`，不生成安装脚本 |
| raw 清理 | LLD 明确不自动清理 `data/raw/**`，保留 raw/manifest 以支持重新派生 |

## 8. Review Findings 聚合

| 严重度 | 数量 | 结论 |
|---|---:|---|
| 严重 | 0 | 未发现阻断项 |
| 一般 | 0 | 未发现需要修订后重提的问题 |
| 轻微 | 1 | LLD 自带人工确认区使用“批准 / 需要修改 / 拒绝”措辞；本 checkpoint 已按元工作流标准选项映射为“确认通过 / 需要修改 / 确认不通过”，不阻断确认 |

## 9. 本轮需人工确认的问题

请用户确认以下设计点是否可作为实现边界：

- 是否接受第一版质量报告固定输出 CSV 与 Markdown 两种形态，CSV 中复杂列表字段使用 JSON 字符串。
- 是否接受 raw 到 dataset 只采用显式 `target_dataset` 或 exact interface 映射，不做模糊匹配。
- 是否接受 prices 缺失率主分母为 `open_trade_dates_in_requested_range * target_symbols`。
- 是否接受数据源失败但本地 parquet 合规时，质量报告披露失败批次，并可按影响范围输出 `warn` 或 `pass`，而不是一律 `fail`。
- 是否接受第一版非 PIT 股票池策略：缺 `is_pit_universe` 时填充 `false`，并在质量报告中强制披露幸存者偏差。
- 是否接受 `engine/contracts.py` 只追加常量，不引入 I/O、pandas、pyarrow、AKShare、dataclass、TypedDict 或 pydantic model。
- 是否接受 LLD 确认后仅允许按 §5 和 §7 限定范围实现，不进入 Data Loader、回测、扫描、候选报告、真实性增强、安装脚本或 `delivery/**`。

## 10. 确认后允许的下一步

用户已确认通过，meta-po 已执行以下流程动作：

1. 将 `process/stories/STORY-003-parquet-quality-report-LLD.md` 更新为 `confirmed=true`、`status=confirmed`。
2. 将 `process/stories/STORY-003-parquet-quality-report.md` 的 Story 状态推进到 `lld-approved`。
3. 更新 `process/STORY-STATUS.md` 和 `process/STATE.md`，记录 LLD 人工确认通过。
4. 创建 `process/handoffs/META-DEV-IMPLEMENT-W0-STORY-003-2026-05-15.md`，限定 meta-dev 只能实现 `engine/normalizer.py`、`engine/quality.py`、`engine/contracts.py` 的 STORY-003 范围，并在测试隔离目录中验证 parquet/report 行为。

## 11. 禁止范围

在用户确认通过前，以下行为继续禁止：

- 禁止实现 `engine/normalizer.py`、`engine/quality.py`，禁止修改 `engine/contracts.py`。
- 禁止生成 `data/prices.parquet`、`data/index_members.parquet`、`data/trade_calendar.parquet`。
- 禁止生成 `reports/data_quality_report.csv` 或 `reports/data_quality_report.md`。
- 禁止写入真实 `data/raw/**`、`data/manifests/**`。
- 禁止调用真实 AKShare、聚宽或其他远程数据源。
- 禁止创建或修改 `engine/data_loader.py`、`engine/backtest.py`、`engine/scanner.py`、`engine/candidates.py`、`strategies/**`。
- 禁止写入 `delivery/**`。
- 禁止生成安装脚本。

确认通过后，禁止范围仍不自动解除到下游 Story；只能解除 STORY-003 LLD 中明确允许的实现范围。

## 12. 用户确认选项

1. 确认通过 - 当前 Story LLD 可进入实现；meta-po 后续才可将 Story 状态推进到 `lld-approved`。
2. 需要修改 - 请说明需要调整的实现设计；meta-po 将交由 meta-dev 修订 LLD 后重新确认。
3. 确认不通过 - 当前 Story 回退至 `approved`，重新组织 LLD 设计。

## 13. 确认记录

| 日期 | 用户回复 | meta-po 判定 | 状态更新 |
|---|---|---|---|
| 2026-05-14 | 待确认 | 等待用户人工确认 | 暂不推进；LLD `confirmed=false`；Story 保持 `ready-for-lld-review` |
| 2026-05-15 | 确认通过 | STORY-003 LLD 人工确认通过 | LLD `confirmed=true`；Story `status=lld-approved`；已创建 meta-dev 实现交接 |
