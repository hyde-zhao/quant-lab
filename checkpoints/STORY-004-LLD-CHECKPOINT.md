---
checkpoint_id: "STORY-004-LLD"
checkpoint_type: "story-lld-confirmation"
story_id: "STORY-004"
story_title: "离线 Data Loader 与合同校验"
story_slug: "offline-data-loader-contract-validator"
status: "superseded-by-lld-batch-package"
confirmed: false
created_by: "meta-po"
created_at: "2026-05-15"
updated_at: "2026-05-15"
lld_path: "process/stories/STORY-004-offline-data-loader-contract-validator-LLD.md"
story_path: "process/stories/STORY-004-offline-data-loader-contract-validator.md"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
superseded_by: "process/LLD-BATCH-PLAN.md"
superseded_reason: "用户纠偏工作流：Story 分解后应先输出各 Story LLD 并统一人工确认，再进入 Story 开发；不再单独确认 STORY-004 后立即实现"
---

# STORY-004 LLD 人工确认检查点

> 状态更新：本检查点已被 `process/LLD-BATCH-PLAN.md` 取代，不再作为单独放行 STORY-004 实现的活动检查点。`STORY-004` LLD 将与 STORY-005 至 STORY-013 的 LLD 一起纳入批量 LLD / Story Package 检查点统一确认。

> 历史检查点 ④：本文件仅保留 STORY-004 LLD 的复核记录；当前活动门控已切换为批量 LLD / Story Package 确认，不允许实现代码、生成数据、写入 `delivery/**` 或生成安装脚本。

## 1. 门控结论

`STORY-004` LLD 已完成 meta-po 门控复核，但由于工作流纠偏，本检查点结论改为：**不再单独确认 STORY-004 后进入实现；等待剩余 LLD 批量输出后统一确认**。

当前状态事实：

| 对象 | 当前状态 | 结论 |
|---|---|---|
| `process/STATE.md` | `current_phase=story-planning`，`active_story=null`，`story_lld_status=batch-lld-output-required`，`story_lld_confirmed=false` | 单张 LLD 门控已暂停，等待批量 LLD 包 |
| `process/STORY-STATUS.md` | `current_gate=batch-lld-output-before-implementation` | 单张 LLD 确认门控已被批量 LLD 包门控取代 |
| `process/stories/STORY-004-offline-data-loader-contract-validator.md` | `status=ready-for-lld-review` | 等待批量 LLD / Story Package 统一确认 |
| `process/stories/STORY-004-offline-data-loader-contract-validator-LLD.md` | `status=ready-for-review`，`confirmed=false`，`tier=L`，`open_items=4` | 将纳入批量 LLD 包确认 |
| W0 前置依赖 | `STORY-001`、`STORY-002`、`STORY-003` 均为 `verified` | STORY-004 前置依赖满足 |

本 checkpoint 不代表 LLD 已通过，也不再接受单独确认。只有后续批量 LLD / Story Package 检查点确认通过后，meta-po 才能按确认后的调度规则进入对应 Story 实现。

## 2. 复核对象

| 对象 | 路径 | 复核结果 |
|---|---|---|
| 运行态状态 | `process/STATE.md` | 当前阶段、活跃 Story、LLD 门控和禁止范围一致 |
| Story 状态汇总 | `process/STORY-STATUS.md` | 当前门控为批量 LLD 输出；STORY-004 已有 LLD，STORY-005 至 STORY-013 缺 LLD |
| Story 卡片 | `process/stories/STORY-004-offline-data-loader-contract-validator.md` | 包含目标、REQ/HLD/ADR 映射、开发上下文、验证上下文、验收标准和禁止范围 |
| LLD 文档 | `process/stories/STORY-004-offline-data-loader-contract-validator-LLD.md` | 存在且进入 `ready-for-review`；保留 4 个 OPEN 待确认项 |
| 开发计划 | `process/DEVELOPMENT-PLAN.yaml` | W1/M1 串行，STORY-004 输出范围为 `engine/data_loader.py` 与 `engine/contracts.py` |
| HLD | `process/HLD.md` | 相关章节覆盖离线 Data Loader、标准化 parquet schema、复权、`available_at`、质量报告、失败路径和 M1 |
| ADR | `process/ARCHITECTURE-DECISION.md` | ADR-001、ADR-003、ADR-006 分别约束离线只读、复权口径、质量状态与降级边界 |
| 已完成前置 Story | STORY-001/002/003 卡片、`process/VERIFICATION-REPORT.md`、`DEV-LOG.md` | 三者均已 verified；STORY-003 bugfix 已回归通过并关闭 |

## 3. Frontmatter 契约复核

| 字段 | 期望 | 实际 | 结论 |
|---|---|---|---|
| `story_id` | `STORY-004` | `STORY-004` | 通过 |
| `status` | `ready-for-review` | `ready-for-review` | 通过 |
| `confirmed` | 确认前为 `false` | `false` | 通过 |
| `tier` | 必填 | `L` | 通过 |
| `shared_fragments` | 必填且指向 HLD/ADR/上游 Story 依据 | HLD §8.3、§9.1、§9.3、§11、§12.2、§12.4；ADR-001、ADR-003、ADR-006；STORY-003 LLD 相关接口 | 通过 |
| `open_items` | 必填；如有则必须在 checkpoint 中整理并提交人工确认 | `4` | 通过，需人工确认 O-01/O-02/O-03/O-04 |
| `source_story` | Story 卡片路径 | `process/stories/STORY-004-offline-data-loader-contract-validator.md` | 通过 |
| `source_hld` | HLD 路径 | `process/HLD.md` | 通过 |
| `source_adr` | ADR 路径 | `process/ARCHITECTURE-DECISION.md` | 通过 |
| `depends_on` | 前置设计与实现依据 | STORY-003 卡片、STORY-003 LLD、`engine/contracts.py`、`engine/quality.py` | 通过 |

## 4. 14 章节契约复核

LLD 文档包含 14 个编号可见章节，并保留独立人工确认区。

| # | 章节 | 复核结论 |
|---:|---|---|
| 1 | Goal | 通过 |
| 2 | Requirements（Functional / Non-Functional） | 通过 |
| 3 | 模块拆分与职责 | 通过 |
| 4 | 代码结构与文件影响范围 | 通过 |
| 5 | 数据模型与持久化设计 | 通过 |
| 6 | API / Interface 设计 | 通过 |
| 7 | 核心处理流程 | 通过 |
| 8 | 技术设计细节 | 通过 |
| 9 | 安全与性能设计 | 通过 |
| 10 | 测试设计 | 通过 |
| 11 | 实施步骤 | 通过 |
| 12 | 风险、难点与预研建议 | 通过，含 4 个 OPEN |
| 13 | 回滚与发布策略 | 通过 |
| 14 | Definition of Done | 通过 |

## 5. LLD 摘要

`STORY-004` 设计目标是在 M1/W1 中创建离线 Data Loader 与合同校验层，让后续动量信号、组合成交和报告层只通过稳定接口消费本地数据，不绕过质量、复权、`available_at` 和离线边界。

允许的实现文件限定为：

| 文件 | 允许内容 |
|---|---|
| `engine/data_loader.py` | 创建 Data Loader 主入口、parquet reader、schema validator、calendar validator、复权校验、`available_at` 校验、质量摘要消费、过滤构造、metadata 构造、结构化异常 |
| `engine/contracts.py` | 仅追加 loader metadata、quality policy、available_at policy、decision time rule 等纯常量，并更新 `__all__` |

关键设计点：

| 设计点 | LLD 结论 |
|---|---|
| 主入口 | `load_backtest_data(config: LoaderConfig | None = None, **kwargs)` 返回 `LoadedBacktestData(close_df, universe, calendar, metadata)` |
| 本地输入 | 只读 `data/prices.parquet`、`data/index_members.parquet`、`data/trade_calendar.parquet`、`data/manifests/data_prep_manifest.jsonl`、`reports/data_quality_report.csv` |
| 必需 schema | `prices.trade_date/symbol/close`、`index_members.symbol`、`trade_calendar.trade_date` |
| `close_df` | index 为请求区间开市日，columns 为股票池与价格数据交集，缺失 close 保留 `NaN` |
| 复权口径 | 默认 `qfq`；同一次加载混用或请求口径不一致时拒绝运行 |
| 未来函数防护 | 显式 `available_at` 必须满足 `available_at <= decision_time`；日线 close 缺字段时仅可按 `trade_date_close_after` 推导 |
| 质量策略 | `pass` 允许；`warn` 允许但必须披露；`fail` 默认拒绝 |
| metadata | 覆盖质量状态、复权、可用时点规则、覆盖区间、新鲜度、manifest、source paths、PIT/固定池标记和过滤统计 |
| 结构化异常 | 文件缺失、合同失败、质量失败、网络边界失败均需暴露可定位字段 |
| 测试策略 | 使用临时 parquet/manifest/quality report fixture；静态扫描和 monkeypatch 确保无联网、只读边界 |

## 6. HLD / ADR 一致性复核

| 依据 | 要求 | LLD 覆盖情况 | 结论 |
|---|---|---|---|
| HLD §8.3 | 三类标准化 parquet schema 与失败行为 | LLD §2、§5、§6、§7、§10 覆盖必需字段、日期、股票池、复权和错误路径 | 通过 |
| HLD §9.1 / ADR-003 | 默认 `qfq`，同一次运行不得混用复权口径 | LLD §2、§6、§7、§8、§10 明确混用或请求不一致均拒绝 | 通过 |
| HLD §9.3 | `available_at <= decision_time`；日线 close 缺字段仅可按收盘后可用推导 | LLD §2、§6、§7、§8、§10 覆盖显式失败与推导披露 | 通过 |
| HLD §11 | Backtest -> Data Loader 集成契约 | LLD §5、§6、§10 定义 `close_df/universe/calendar/metadata` 作为 STORY-005 输入 | 通过 |
| HLD §12.2 | 离线回测流程先读取 parquet、manifest、质量报告，再进入信号/组合 | LLD §7 主流程与时序图保持一致 | 通过 |
| HLD §12.4 | 数据契约 fail 拒绝，warn 强制披露 | LLD §7、§9、§10、§13 覆盖 fail/warn 行为和错误路径 | 通过 |
| ADR-001 | 数据准备与回测主路径物理隔离；回测只读本地产物，不调用数据准备 | LLD §1、§2、§4、§8、§9 明确不导入 AKShare、data_prep、adapter 或网络客户端 | 通过 |
| ADR-006 | `warn` 可继续但披露；`fail` 阻塞；无质量报告主路径失败，除非 LLD 明确探索模式且不作为验收路径 | LLD 主体明确 fail 拒绝；O-01 需要用户确认是否允许“内存重算但不写报告”的探索降级 | 需人工确认 O-01 的边界 |

## 7. 越界与禁止范围复核

| 范围 | 复核结论 |
|---|---|
| 代码实现 | 本轮未实现代码；确认前禁止创建 `engine/data_loader.py` 或修改 `engine/contracts.py` |
| 已完成 Story | 不修改 `engine/normalizer.py`、`engine/quality.py`、`engine/manifest.py`、`engine/data_prep.py`、`engine/akshare_adapter.py`；保持 STORY-001/002/003 已验证行为不变 |
| 数据生成 | 禁止生成真实 `data/*.parquet`、`data/raw/**`、`data/manifests/**`、`reports/data_quality_report.*` |
| 下游 Story | 禁止创建或修改 `engine/backtest.py`、`engine/portfolio.py`、`engine/metrics.py`、`engine/reporting.py`、`engine/scanner.py`、`engine/candidates.py`、`strategies/**` |
| 增强 Story | 禁止实现 PIT provider、交易状态、涨跌停、事件字段、偏差审计等 STORY-009+ 范围 |
| 网络调用 | Data Loader 不得导入或调用 AKShare、requests、httpx、urllib、`engine.data_prep`、`engine.akshare_adapter` |
| 交付目录 | 禁止写入 `delivery/**`，禁止生成安装脚本 |

## 8. Review Findings 聚合

| 严重度 | 数量 | 结论 |
|---|---:|---|
| 严重 | 0 | 未发现阻断人工确认的结构或范围问题 |
| 一般 | 0 | 未发现必须退回 meta-dev 修订后才能确认的问题 |
| 轻微 | 2 | O-01 需要确认其“内存重算”只能作为非验收主路径探索降级；LLD 人工确认区用“批准 / 需要修改 / 拒绝”措辞，本 checkpoint 已映射为元工作流标准选项 |

## 9. O-01/O-02/O-03/O-04 默认建议与影响

| ID | 问题 | 建议默认选项 | 影响 |
|---|---|---|---|
| O-01 | 质量报告缺失时，是否允许 Data Loader 在内存中调用 `calculate_quality(...)` 重算摘要，但不写 `reports/**` | **默认：允许，但仅作为探索降级；验收主路径仍要求提供 `reports/data_quality_report.csv` 或等价质量摘要 fixture。** metadata 必须写 `source_quality_report_path=""` 与 warning，且不得调用 `render_quality_reports(...)` | 优点：本地已有 parquet/manifest 时可临时检查数据质量，不因缺报告完全无法探索。风险：若不限定为非验收主路径，会削弱 ADR-006 “无质量报告主路径失败”的约束。实现和 QA 必须区分验收主路径与探索降级路径 |
| O-02 | `quality_policy` 第一版是否只允许 pass/warn 成功，fail 永远拒绝，不提供允许 fail 的探索模式 | **默认：确认 fail 永远拒绝。** `fail_on_fail` 为默认策略；`allow_warn` 只放宽 warn，不放宽 fail；不提供 `allow_fail` | 优点：与 ADR-006 和 HLD §12.4 完全一致，降低误用风险。代价：用户不能用明显不合格数据跑“仅看一下”的回测；如后续确需允许 fail，必须通过变更或后续 Story 增加强警示探索模式 |
| O-03 | `.md` 质量报告是否不作为机器解析入口，第一版仅解析 CSV 或内存 `QualitySummary` | **默认：确认 Markdown 只作人工材料，机器入口仅 CSV 或内存摘要对象。** | 优点：解析契约稳定，减少 Markdown 格式漂移造成的隐性错误。代价：如果只保留 Markdown 报告，loader 会认为机器质量报告缺失，并按 O-01 或 fail 策略处理 |
| O-04 | 未来 PIT 股票池 `is_pit_universe=true` 但缺 `snapshot_date` 或 `available_at` 时，第一版 loader 是拒绝还是警示 | **默认：拒绝合同不完整的 PIT 声明。** 非 PIT/固定股票池可警示继续；声称 PIT 但缺关键时点字段应失败 | 优点：防止把不完整历史成分数据误标为 PIT，保护未来函数边界。代价：真实 PIT 数据接入初期要求更高，后续 STORY-009 需要同步补齐 `snapshot_date`/`available_at` 契约 |

## 10. 本轮需人工确认的问题

本节保留为 STORY-004 LLD 的历史复核记录，不再作为当前活动确认协议。当前活动确认协议应在 STORY-004 至 STORY-013 的 LLD 包齐全后，由 meta-po 新建批量 LLD / Story Package 检查点。

请用户确认以下问题，确认后 meta-po 才能把 STORY-004 推进到 `lld-approved`：

1. 是否接受 O-01 默认选项：质量报告缺失时允许内存 `calculate_quality(...)` 重算摘要，但仅作为非验收主路径探索降级；验收主路径仍要求质量报告 CSV 或等价 fixture。
2. 是否接受 O-02 默认选项：第一版 `quality_policy` 不允许 fail 成功返回，`allow_warn` 也不能放宽 fail。
3. 是否接受 O-03 默认选项：Markdown 质量报告只作人工材料，Data Loader 机器解析入口仅为 CSV 或内存质量摘要。
4. 是否接受 O-04 默认选项：声称 PIT 的股票池若缺 `snapshot_date` 或 `available_at`，第一版拒绝运行；固定非 PIT 股票池则警示继续并披露幸存者偏差。
5. 是否接受 LLD 确认后实现范围仅限 `engine/data_loader.py` 与 `engine/contracts.py`，且 `engine/contracts.py` 只允许追加纯常量。
6. 是否接受确认后仍禁止写真实 `data/**`、`reports/**`、`delivery/**`，测试只能使用临时目录 fixture。
7. 是否接受 STORY-005/006 在 STORY-004 验证通过前不得推进。

## 11. 确认后允许的下一步

若用户选择“确认通过”，meta-po 后续允许执行的流程动作仅包括：

1. 将 `process/stories/STORY-004-offline-data-loader-contract-validator-LLD.md` 更新为 `confirmed=true`、`status=confirmed`，并记录确认人和确认时间。
2. 将 `process/stories/STORY-004-offline-data-loader-contract-validator.md` 的状态从 `ready-for-lld-review` 推进到 `lld-approved`。
3. 更新 `process/STORY-STATUS.md` 与 `process/STATE.md`，记录 STORY-004 LLD 人工确认通过。
4. 创建 meta-dev 实现 handoff，限定实现只覆盖 `engine/data_loader.py` 和 `engine/contracts.py` 的 STORY-004 范围。
5. 要求 meta-dev 实现完成后进入 `ready-for-verification`，再由 meta-qa 按 LLD 第 10 节验证。

## 12. 禁止范围

在用户确认通过前，以下行为继续禁止：

- 禁止创建 `engine/data_loader.py`。
- 禁止修改 `engine/contracts.py`。
- 禁止修改 `engine/normalizer.py`、`engine/quality.py`、`engine/manifest.py`、`engine/data_prep.py`、`engine/akshare_adapter.py`。
- 禁止生成真实 `data/prices.parquet`、`data/index_members.parquet`、`data/trade_calendar.parquet`。
- 禁止写入真实 `data/raw/**`、`data/manifests/**`。
- 禁止生成 `reports/data_quality_report.csv` 或 `reports/data_quality_report.md`。
- 禁止调用真实 AKShare、聚宽或其他远程数据源。
- 禁止创建或修改 `engine/backtest.py`、`engine/portfolio.py`、`engine/metrics.py`、`engine/reporting.py`、`engine/scanner.py`、`engine/candidates.py`、`strategies/**`。
- 禁止实现 PIT provider、交易状态、涨跌停、事件字段或偏差审计。
- 禁止写入 `delivery/**`。
- 禁止生成安装脚本。
- 禁止推进 `STORY-005+`。

确认通过后，禁止范围也不会自动解除到下游 Story；只能解除 STORY-004 LLD 明确允许的 `engine/data_loader.py` 与 `engine/contracts.py` 实现范围。

## 13. 用户确认选项

1. 确认通过 - 当前 Story LLD 可进入实现；同时接受 O-01/O-02/O-03/O-04 的默认建议，或在回复中覆盖具体选项。
2. 需要修改 - 请说明需要调整的实现设计；meta-po 将交由 meta-dev 修订 LLD 后重新确认。
3. 确认不通过 - 当前 Story 回退至 `approved`，重新组织 LLD 设计。

建议确认语句：

```text
确认通过。O-01/O-02/O-03/O-04 均采用 checkpoint 默认建议。
```

如需覆盖某项，可使用：

```text
需要修改：O-01 改为质量报告缺失必 fail；其他项采用默认建议。
```

## 14. 确认记录

| 日期 | 用户回复 | meta-po 判定 | 状态更新 |
|---|---|---|---|
| 2026-05-15 | 待确认 | 等待用户人工确认 | 暂不推进；LLD `confirmed=false`；Story 保持 `ready-for-lld-review` |
