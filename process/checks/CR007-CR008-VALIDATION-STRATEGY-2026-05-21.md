---
check_id: "CR007-CR008-VALIDATION-STRATEGY-2026-05-21"
type: "validation-strategy-analysis"
status: "STRATEGY_ONLY_NO_GATE_APPROVAL"
owner: "meta-qa"
created_at: "2026-05-21T07:06:29+08:00"
workflow_id: "local_backtest"
active_change: "CR-007"
secondary_change: "CR-008"
priority_rule: "CR008-over-CR007-on-conflict"
source_handoff: "process/handoffs/META-QA-CR007-CR008-MERGED-VALIDATION-STRATEGY-2026-05-21.md"
tests_run: false
network_used: false
gate_approval: false
---

# CR007 / CR008 合并验证策略

## 结论

本文件只产出验证策略，不批准 CP5、CP6、CP7 或任何人工 / 自动门禁，不运行测试，不读取凭据，不联网，不读取旧 `data/**`，不读取旧 `reports/data_quality_report.csv`。

当前 QA 策略结论：

- `CR007-S02-benchmark-calendar-backfill` 可在 CP6 通过后立即进入最小 CP7 验证，验证范围必须限于离线 tmp fixture、只读 reader / benchmark / validation 合同、安全边界和既有 hs300 CLI 回归。
- `CR007-S03` 可以继续作为 S02 后续候选，但 CP7 必须新增 CR008 研究消费侧兼容检查，尤其是 PIT / fixed snapshot、readiness / quality 分离和 `index_weights` 不得替代 `index_members`。
- `CR007-S04` 与 `CR007-S05` 在 CR008 设计影响结论输出前不宜进入实现或 CP7，因为 benchmark 字段、报告 metadata、legacy report、文档口径与 CR008 高度重叠。
- `CR008-S01..S06` 目前没有正式 LLD 和 CP5 结果；QA 只能定义 CP5 自动预检重点与未来 CP7 验证重点，不能写任何 PASS / verified 结论。
- 合并回归最小集必须覆盖 `market_data` readers、benchmark、validation、experiment 13、experiment 15、docs guardrail 六个面，并坚持 no network / no credential / no old data / no legacy report read / no real lake write。

## 已消费输入

| 输入 | 状态 | QA 使用方式 |
|---|---|---|
| `process/handoffs/META-QA-CR007-CR008-MERGED-VALIDATION-STRATEGY-2026-05-21.md` | 已读取 | 确认任务边界、禁止事项、必读输入和输出路径 |
| `process/STATE.md` | 已读取相关 CR007 / CR008 状态 | 确认当前阶段、S01 verified、S02 dev_ready、S03/S04/S05 队列状态、CR008 priority rule |
| `process/checks/CR007-CR008-INTEGRATED-INTAKE-ROUTING-2026-05-21.md` | 已读取 | 确认 CR007 / CR008 串并行路由和冲突矩阵 |
| `process/changes/CR-007-CANONICAL-DATA-COVERAGE-BACKFILL-AND-BENCHMARK-2026-05-20.md` | 已读取 | 提取 CR007 目标、Story 拆分、安全边界和 S01 CP6/CP7 状态 |
| `process/changes/CR-008-RESEARCH-DATA-LAYER-HARDENING-2026-05-20.md` | 已读取 | 提取 CR008 S01..S06、priority rule、研究数据合同和准入门禁 |
| `process/stories/CR007-S02-benchmark-calendar-backfill-LLD.md` | 已读取 | 转换 S02 CP6 / CP7 最小验证集 |
| `process/stories/CR007-S03-index-members-stock-basic-datasets-LLD.md` | 已读取 | 提取 S03 在 CR008 介入后的 PIT / readiness / reader 关注点 |
| `process/stories/CR007-S04-experiment-real-benchmark-consumption-LLD.md` | 已读取 | 提取 S04 与 CR008 benchmark 字段拆分冲突面 |
| `process/stories/CR007-S05-data-quality-report-and-doc-guardrail-LLD.md` | 已读取 | 提取 S05 与 CR008 report metadata / legacy report / docs 口径冲突面 |
| `process/checks/CP6-CR007-S01-prices-long-horizon-backfill-planner-CODING-DONE.md` | 已读取 | 作为 S02 上游合同和安全基线 |
| `process/checks/CP7-CR007-S01-prices-long-horizon-backfill-planner-VERIFICATION-DONE.md` | 已读取 | 作为 S02 CP7 最小结构和安全验证参考 |

未读取旧 `data/**`，未读取旧 `reports/data_quality_report.csv`，未读取 `.env` 或任何凭据文件。

## 当前状态判断

| 对象 | QA 状态判断 | 验证影响 |
|---|---|---|
| `CR007-S01` | CP6 PASS，CP7 PASS，Story 已 verified | 可作为 S02 的上游验证基线，不需要本轮重验 |
| `CR007-S02` | `dev_ready`，允许离线实现 | CP6 通过后可立即做最小 CP7 |
| `CR007-S03` | blocked by S02 CP6 与共享文件冲突 | 等 S02 CP6 PASS 和文件冲突清理；CP7 需加入 CR008 研究合同兼容验证 |
| `CR007-S04` | hold-for-CR008-impact | benchmark 字段与 CR008-S02 冲突，CR008 设计前不建议实现 |
| `CR007-S05` | hold-for-CR008-impact | docs / report metadata / legacy report 与 CR008-S01/S02/S06 冲突，CR008 设计前不建议实现 |
| `CR008` | `intake-accepted-parallel-design-routing`，`implementation_allowed=false` | 只能做 CP5 预检策略，不能做 CP7 或通过结论 |

## CR007-S02 CP6 最小验证集

S02 CP6 目标不是证明真实数据已补齐，而是证明 benchmark/calendar 离线合同、只读消费和安全边界已实现。

| # | CP6 最小项 | 等级 | 必要证据 |
|---|---|---|---|
| 1 | CP5 / dev gate 合法 | BLOCKING | S02 LLD `confirmed=true`、`implementation_allowed=true`，S01 CP7 PASS，S02 handoff 有真实 meta-dev 调度证据 |
| 2 | 文件范围受控 | BLOCKING | 只允许 S02 LLD 范围：`market_data/cli.py`、`normalization.py`、`validation.py`、`catalog.py`、`readers.py`、`benchmarks.py`、S02 测试；不得修改 `experiments/**`、`engine/**`、`reports/**`、`data/**` |
| 3 | dry-run plan 无副作用 | BLOCKING | `benchmark-calendar-backfill --dry-run true` 或等价入口输出 `network_calls=0`、`writes=0`、`old_data_operations=0` |
| 4 | benchmark denominator 固定为交易日历 | BLOCKING | `denominator_mode=trade_calendar_open_dates`；自然日 denominator pass 次数为 0 |
| 5 | typed missing 路径完整 | BLOCKING | `calendar_missing`、`coverage_gap`、`policy_unconfirmed`、`quality_failed`、`price_benchmark_overlap_missing` 均返回结构化非 available |
| 6 | `BenchmarkResult.to_metadata()` 增量兼容 | REQUIRED | 至少含 `status`、`dataset`、`index_code`、`start_date`、`end_date`、`coverage`、`quality_status`、`missing_reason`、`lineage`；不得删除 CR005 已验证字段 |
| 7 | reader / resolver 不自动补数 | BLOCKING | `market_data/readers.py`、`market_data/benchmarks.py` 不导入 connector/runtime/storage，不触发 fetch/backfill |
| 8 | proxy 隔离 | BLOCKING | hs300 不可用时不得用 `proxy_baseline` 填充真实 `hs300_index` 字段 |
| 9 | 安全边界 | BLOCKING | 不读 `.env`、token、NAS 凭据；不读、列出、迁移、复制、比对、删除旧 `data/**`；不读或覆盖旧 `reports/data_quality_report.csv` |
| 10 | 测试记录 | REQUIRED | CP6 记录 S02 专属离线测试、必要 hs300 CLI 回归和安全检查结果；偏离 LLD 必须有差异说明 |

## CR007-S02 CP7 最小验证集

S02 CP7 可以在 S02 CP6 PASS 后立即执行，但只能验证离线合同，不得执行真实 Tushare 抓取、真实 lake 写入或旧数据读取。

| 维度 | 最小 CP7 检查 | 等级 |
|---|---|---|
| Entry Criteria | CP6 PASS；S02 LLD / CP5 已确认；QA handoff 有真实调度证据；禁止事项继续有效 | BLOCKING |
| LLD §6 接口验证 | CLI plan、validate/read、`validate_benchmark_calendar_coverage` 或等价接口、`read_dataset(trade_calendar/hs300_index)`、`resolve_hs300_benchmark` 均有测试入口 | BLOCKING |
| LLD §7 主流程验证 | calendar-first、hs300-second、coverage gate、catalog、reader、resolver available / missing 路径均可由 tmp fixture 复现 | BLOCKING |
| LLD §7 异常路径验证 | calendar missing、coverage gap、price overlap missing、policy unconfirmed、quality failed、lineage missing | BLOCKING |
| LLD §10 测试设计执行 | 未来 CP7 应执行 S02 专属测试：`tests/test_cr007_benchmark_calendar_backfill.py` 中 T01-T06；S02 现有回归 T07 | BLOCKING |
| 回归 | 至少执行既有 hs300 CLI 回归：`tests/test_market_data_cli_comparison.py::test_hs300_index_cli_normalize_validate_and_read`；如 S02 触碰 `BenchmarkResult`，补跑 `tests/test_market_data_hs300_benchmark.py` 相关用例 | REQUIRED |
| 安全合规 | AST / monkeypatch / tmp_path 证据证明 no network、no connector/runtime/storage import、no credential、no old data、no legacy report、no real lake write | BLOCKING |
| 输出结论 | 只可对 S02 Story 验证结论表态，不得把 CR008 或 CR007-S04/S05 视为已验证 | BLOCKING |

可立即执行的 S02 CP7 子集：S02 CP6 PASS 后的 Story 专属离线测试、hs300 CLI 兼容回归、reader/benchmark import 边界、安全 sentinel 检查。

必须等待 CR008 的部分：S02 是否完全满足 `research_input_v1` / CR008-S02 字段拆分，只能在 CR008 CP5 形成正式 LLD 后复核。

## CR007-S03/S04/S05 的新增验证关注点

| Story | 原 CR007 验证重点 | CR008 介入后的新增重点 | QA 判定 |
|---|---|---|---|
| `CR007-S03` | `index_members`、`index_weights`、`stock_basic` schema / registry / normalizer / validator / reader readiness | 必须支撑 CR008 的 `universe_mode=fixed_snapshot|pit`、`is_pit_universe`、`survivorship_bias_note`、`pit_status`；PIT required 不可用时必须结构化失败；`stock_basic` 不得伪装 historical availability；`index_weights` 不得替代完整成分集 | S02 CP6 后可继续，但 CP7 若早于 CR008 CP5，只能标注“CR008 兼容性待复核” |
| `CR007-S04` | 实验十三真实 hs300 benchmark 优先，缺失时 proxy fallback | CR008 要求 `proxy_*` 与 `hs300_*` 字段硬隔离；不得继续使用含混的 `benchmark_total_return` / `excess_return` 让 proxy 被误读为真实指数；实验十/十二/十三 metadata 需要统一 | CR008 设计前应保持 hold；提前实现属于 BLOCKING 返工风险 |
| `CR007-S05` | README / USER-MANUAL / `.gitignore` / guardrail，旧质量报告 legacy 化 | CR008 要求新报告强制 metadata：manifest/source run id、coverage、universe、benchmark、adjustment、label window、known limitations；旧 `reports/data_quality_report.csv` 不能作为 current truth，也不能作为 research report coverage proof | CR008 设计前应保持 hold；文档提前落旧口径属于 HIGH 返工风险 |

## CR008-S01..S06 CP5 自动预检重点与后续 CP7 重点

CR008 当前没有正式 LLD，以下是 QA 对未来 CP5 自动预检和 CP7 的策略要求，不代表任何 Story 已通过。

| Story | CP5 自动预检重点 | 后续 CP7 验证重点 |
|---|---|---|
| `CR008-S01-research-input-contract-and-report-metadata` | LLD 必须定义 `research_input_v1` 请求 / 输出合同、强制 report metadata 字段、与 CR007 S02/S03/S04 的依赖；§6 接口、§7 流程、§10 测试、§13 回滚完整；不得把旧报告或旧 `data/**` 作为输入事实源 | 新报告 / metadata 必含 `manifest_run_id` 或 `source_run_id`、coverage start/end、universe、benchmark、adjustment、`label_available_end`、quality/readiness、known limitations；缺字段必须 fail 或 structured warn |
| `CR008-S02-proxy-real-benchmark-field-separation` | LLD 必须列清旧字段迁移或兼容策略：`benchmark_*`、`excess_return`、`proxy_*`、`hs300_*`；必须说明实验 13 / 15 和既有报告影响；不能删除既有兼容字段而无迁移方案 | proxy 不得填 `hs300_*`；真实 hs300 unavailable 时不得声明真实超额收益；required benchmark 缺失必须受控失败；CSV/Markdown/metadata 文案一致 |
| `CR008-S03-research-dataset-builder` | LLD 必须规定 `engine/research_dataset.py` 或等价入口只消费 readers，不导入 connector/runtime/storage，不自动 backfill；明确 `ResearchDatasetRequest`、`ResearchDataset`、`gate_result` | tmp fixture 覆盖 available / missing / quality fail / PIT unavailable / benchmark unavailable；no network、no write、no old data、no credential；builder 输出 gate result 和 remediation `auto_execute=false` |
| `CR008-S04-quality-adjustment-label-window-gates` | LLD 必须定义 `quality_status` fail、复权口径 mismatch、`forward_return_horizon`、`label_available_end`、coverage 与交易日历的 fail / truncate 策略；不得静默继续 | 复权混用必须 fail；label window 不足必须 fail 或显式截断并写 metadata；quality fail 阻断实验；错误包含 status / reason |
| `CR008-S05-pit-universe-consumption-contract` | LLD 必须定义 PIT / fixed snapshot / missing 的状态枚举、as-of gate、survivorship bias note、严肃研究模式与探索模式差异；明确依赖 CR007-S03 | PIT required 且不可用时 fail；fixed snapshot 只能 warn / exploratory；`is_pit_universe=false` 不得支撑严肃因子结论；`index_weights` 不得替代 `index_members` |
| `CR008-S06-factor-research-auxiliary-data-contract` | LLD 必须定义可交易性、OHLCV/VWAP、行业、市值、流动性、公司行动、风格暴露等辅助数据的 required / optional / unavailable 语义；不能授权新增真实抓取 | 实验 15 报告缺行业 / 市值 / 可交易性 / 风格暴露时不得声明中性化、容量、真实可成交或纯 alpha；factor schema 必披露依赖字段和缺失降级 |

CR008 CP5 自动预检的 BLOCKING 共性项：

- LLD frontmatter 必须有 `tier`、`confirmed=false` 或待确认状态、`implementation_allowed=false`，直到 CP5 人工确认。
- 每份 LLD 必须保留 14 个可见章节，且第 6 / 7 / 10 / 13 节可直接转 CP7 验证入口。
- 每份 LLD 必须显式写安全边界：no network、no credential、no old data、no legacy report read、no real lake write。
- 每份 LLD 必须标注与 CR007-S02/S03/S04/S05 的依赖与冲突处理，冲突以 CR008 为主。
- 若 LLD 要修改 `market_data/readers.py`、`market_data/benchmarks.py`、`experiments/run_experiment_13.py`、`experiments/run_experiment_15_factor_framework.py`、README / USER-MANUAL，必须说明文件所有权和串行开发策略。

## 合并回归最小集

以下是未来 CP7 / 合并验证应使用的最小回归面。命令只作为后续 CP7 策略，不在本次执行。

| 回归面 | 最小目标 | 可立即执行时机 | 必须等待项 |
|---|---|---|---|
| `market_data readers` | `read_dataset` 对 `trade_calendar`、`hs300_index`、`index_members`、`index_weights`、`stock_basic` 的 available / required_missing / quality_failed / pit_failed；reader 不导入 connector/runtime/storage | S02 CP6 后可执行 hs300/calendar 子集；S03 CP6 后执行 universe 子集 | CR008-S03/S05 实现后补 research builder / PIT 消费回归 |
| `benchmark` | `resolve_hs300_benchmark` metadata、coverage denominator、price overlap、policy unconfirmed、proxy / hs300 隔离 | S02 CP6 后执行 | CR008-S02 实现后补字段拆分与报告语义回归 |
| `validation` | calendar denominator、quality/readiness 分离、PIT fields、复权 mismatch、label window gate | S02/S03 分别完成后执行对应子集 | CR008-S04 实现后补 label / adjustment hard gate |
| `experiment 13` | 真实 hs300 available、required missing fail-fast、optional proxy fallback、CSV/Markdown label、no old data/report | CR007-S04 CP6 后执行 | CR008-S02 CP5/实现若改变字段语义，S04 必须返工或重验 |
| `experiment 15` | factor panel / report 必披露 PIT、proxy benchmark、close-only、tradability、industry / market cap / style limitations | CR008-S06 CP6 后执行 | 依赖 CR008-S01/S03/S04/S05 合同 |
| `docs guardrail` | README / USER-MANUAL / `.gitignore` required phrases、forbidden claims、allowlist/denylist、legacy report 不读取 | CR007-S05 CP6 后可执行基础子集 | CR008-S01/S02/S06 metadata 口径定稿后补研究文档回归 |

合并回归最小顺序建议：

1. S02 CP7：benchmark/calendar + hs300 CLI regression。
2. S03 CP7：readers / validation / PIT readiness。
3. CR008 CP5 完成后：静态复核 CR007-S04/S05 LLD 是否需要修订。
4. S04 CP7：experiment 13 benchmark / proxy 分支。
5. CR008 S01..S06 各 Story CP7：research input、benchmark fields、builder、gates、PIT、factor auxiliary。
6. 最终合并回归：experiment 13 + experiment 15 + docs guardrail + no forbidden IO。

## 安全边界

| 边界 | QA 策略要求 | 违反后果 |
|---|---|---|
| no network | CP6 / CP7 仅允许离线 pytest、tmp fixture、monkeypatch fake provider；不得真实 Tushare fetch/backfill | BLOCKING，Story 退回实现或设计 |
| no credential | 不读取 `.env`；不打印 token、NAS 用户名、NAS 密码或真实私有路径；测试只使用 fake sentinel | BLOCKING |
| no old data | 不读取、列出、迁移、复制、比对、删除旧 `data/**`；不得把旧 `data/**` 当 fixture 或 fallback | BLOCKING |
| no legacy report read | 不打开、不读取、不覆盖 `reports/data_quality_report.csv`；文档 / 测试只可字符串提及并标 legacy | BLOCKING |
| no real lake write | 不写 `<configured-lake-root>` 或真实 configured lake；测试只写 `tmp_path` | BLOCKING |
| no auto backfill | reader / benchmark / research builder remediation 只能声明 `auto_execute=false`，不能触发补数 | BLOCKING |
| dispatch evidence | CP6 / CP7 必须记录真实 `spawn_agent` / `resume_agent` / `send_input` 或用户批准 inline fallback | REQUIRED；缺失不得推进 Story 状态 |

## CR008 优先时的返工判定

当 CR008 与 CR007 发生冲突时，QA 按下列规则判定 CR007 旧口径是否必须返工。

| CR007 旧口径表现 | CR008 新口径 | QA 判定 | 等级 |
|---|---|---|---|
| 用 `benchmark_total_return` / `excess_return` 含混表达 proxy 与真实 hs300 | 字段必须拆为 `proxy_*` 与 `hs300_*` | CR007-S04 必须返工，或至少补迁移字段和报告文案 | BLOCKING |
| hs300 不可用时用 `proxy_baseline` 填充 `hs300_index` 或声明沪深300超额收益 | proxy 只能作为 proxy，真实 benchmark unavailable 必须显式 | 必须返工 | BLOCKING |
| benchmark coverage 使用自然日 denominator 或无 `trade_calendar.is_open=true` 分母 | CR008 / CR007-S02 均要求交易日历分母 | 必须返工 | BLOCKING |
| `quality_status=pass` 被当作 PIT available 或 research ready | CR008 要求 quality / readiness / PIT 分离 | 必须返工 S03 reader / validator / metadata | BLOCKING |
| `index_weights` 被当作完整 `index_members` | CR008 要求二者语义分离 | 必须返工 | BLOCKING |
| `stock_basic` 当前快照被标为 PIT 历史过滤可用 | CR008 要求 non-PIT / historical availability 显式 | 必须返工 | BLOCKING |
| README / USER-MANUAL 把旧 `reports/data_quality_report.csv` 作为 current quality truth 或 coverage proof | CR008 要求新 report metadata 和 current truth 来自 lake quality/catalog | 必须返工 S05 文档 / guardrail | BLOCKING |
| 实验 15 缺行业 / 市值 / 可交易性 / PIT，却声称严肃因子结论、中性化、容量或真实可成交 | CR008-S06 要求缺失时阻断对应结论 | 必须返工实验 15 报告 / metadata | BLOCKING |
| LLD 未把 CR008 作为优先冲突源，仍按 CR007 旧字段实现 S04/S05 | priority rule 为 CR008-over-CR007-on-conflict | CR007-S04/S05 不得通过 CP7，退回设计修订 | BLOCKING |
| 仅缺 metadata 透传字段，但核心行为已安全 | CR008 要求强制 metadata | 记录 REQUIRED 修复，可由 meta-po 判断是否阻断 | REQUIRED |
| 文案术语不统一但不误导行为 | CR008 要求报告 / 文档一致 | 记录 ADVISORY 或 REQUIRED，视是否影响用户理解 | ADVISORY / REQUIRED |

## CP7 Handoff 拆分建议

不创建 CP7 文件，仅建议后续 handoff 拆分：

| Handoff | 触发条件 | 范围 | 说明 |
|---|---|---|---|
| `META-QA-CR007-S02-CP7-VERIFY` | S02 CP6 PASS | S02 benchmark/calendar、readers、benchmark resolver、安全边界、hs300 CLI 回归 | 可立即执行，不等待 CR008 CP5；但需标注 CR008 兼容性待复核 |
| `META-QA-CR007-S03-CP7-VERIFY` | S03 CP6 PASS 且 S02/S03 文件冲突清理 | index_members / stock_basic / index_weights readiness、PIT / non-PIT、reader no substitute、安全边界 | 若早于 CR008 CP5，只能验证 CR007 合同并记录 CR008 compatibility pending |
| `META-QA-CR007-S04-S05-CP7-VERIFY` | CR008 CP5 完成并确认 S04/S05 是否需修订；S04/S05 CP6 PASS | experiment 13 benchmark / proxy、docs guardrail、legacy report、report metadata | 不建议拆成 CR008 前的早期 CP7，返工风险高 |
| `META-QA-CR008-S01-S02-CP7-VERIFY` | CR008-S01/S02 CP6 PASS | research_input metadata 和 proxy/hs300 字段拆分 | 两个 Story 字段强耦合，可合并验证报告或分别 CP7 后做小聚合 |
| `META-QA-CR008-S03-S05-CP7-VERIFY` | CR008-S03/S05 CP6 PASS | research dataset builder 与 PIT universe contract | 共享 reader / universe / gate_result，建议串行验证 |
| `META-QA-CR008-S04-S06-CP7-VERIFY` | CR008-S04/S06 CP6 PASS | quality/adjustment/label gates 与 factor auxiliary data limitations | 重点覆盖 experiment 15 的报告声明边界 |
| `META-QA-CR007-CR008-MERGED-REGRESSION` | CR007 S04/S05 与 CR008 S01..S06 全部 CP7 PASS 后 | 六面合并回归与安全边界聚合 | 只做聚合验证，不替代单 Story CP7 |

## 风险分级清单

| 风险 | 等级 | 当前处理 |
|---|---|---|
| CR008 未完成 CP3/CP4/CP5 前被实现 | BLOCKING | QA 不接受任何 CR008 CP6 / CP7 输入，直到门禁完成 |
| CR007-S04/S05 提前按旧口径实现 | BLOCKING | 建议 hold；若已实现，按 CR008 priority rule 返工审查 |
| S02/S03 共享文件并行修改冲突 | REQUIRED | S03 CP7 前必须有 S02 CP6 和文件冲突清理证据 |
| 旧 `data/**` 或旧质量报告被作为验证证据 | BLOCKING | 一律判失败 |
| 真实 Tushare / lake 写入被误认为 CP5 授权 | BLOCKING | CP5 只授权离线实现，真实执行需用户显式授权 |
| CR008 对 CR007 已 verified S01 的 planner 字段提出新增 metadata 要求 | REQUIRED | 不重开 S01 CP7，除非 CR008 改变 S01 输出合同；新增字段可由下游适配 |
| CR008 外部方案参考被误当作运行依赖 | REQUIRED | CP5 必须声明外部项目仅参考；实现若引入依赖需新设计和许可 / 版本确认 |

## 本次未执行项

- 未运行 pytest、guardrail、静态扫描脚本或任何测试命令。
- 未联网，未访问外部链接。
- 未读取 `.env`、token、NAS 凭据或真实私有路径。
- 未读取、列出、迁移、复制、比对或删除旧 `data/**`。
- 未读取、打开或覆盖旧 `reports/data_quality_report.csv`。
- 未修改业务代码、测试代码、README、USER-MANUAL、`.gitignore`、reports 或 data。
- 未批准 CP5 / CP6 / CP7 / CP8。

## 输出结论

- 策略结论：`COMPLETE`
- 门禁结论：`N/A - strategy only`
- BLOCKING 建议：CR008 未完成 CP5 前不得实现；CR007-S04/S05 在 CR008 影响结论前不得通过 CP7；任何旧 data / legacy report / credential / network / real lake 行为均阻断。
- REQUIRED 建议：S02 CP7 可先行，但必须在报告中记录 CR008 compatibility pending；S03 若早于 CR008 CP5 验证，也必须记录后续复核条件。
- 下一步建议：主线程继续调度 CR007-S02 实现、CR008 design lane 和 meta-dev 冲突分析；QA 等 S02 CP6 后接收单独 CP7 handoff。
