---
artifact: "CR-004 CP5 Batch A: STORY-014/STORY-015 and LLD"
reviewer: "meta-se"
lane: "lane-architecture"
round: 1
status: "final"
governance_mode: "review-gated"
created_at: "2026-05-17"
review_mode: true
blocking_count: 0
required_count: 5
optional_count: 2
recommended_next_action: "revise-and-resubmit"
---

# Review Findings

## 1. 审查范围

- 目标对象：`process/stories/STORY-014-cr004-market-data-package-lake-contracts.md`、`process/stories/STORY-014-cr004-market-data-package-lake-contracts-LLD.md`、`process/stories/STORY-015-cr004-connector-runtime-raw-manifest.md`、`process/stories/STORY-015-cr004-connector-runtime-raw-manifest-LLD.md`
- 关联依据：`process/HLD.md` §21、`process/ARCHITECTURE-DECISION.md` ADR-008..012、`process/STORY-BACKLOG.md` STORY-014/015、`process/DEVELOPMENT-PLAN.yaml` CR4-W0/W1、`process/TEST-STRATEGY.md` CR-004 增量
- 审查目标：架构与契约是否足以支撑稳定数据拉取、准确性、可移植性，以及 Story/LLD 是否存在不一致、缺口、过度设计或可改进点
- 审查边界：本轮只做架构评审，不修改被评审对象，不运行实现验证脚本，不修改 `market_data/**`、`engine/**`、`tests/**`、`pyproject.toml`、`uv.lock` 或真实数据

## 2. Findings

<!-- findings-table -->

| ID | Severity | Rule Ref | Evidence | Impact | Suggestion | Anchor |
|----|----------|----------|----------|--------|------------|--------|
| F-001 | 一般 | `CR004-STABILITY-RESUME` | HLD §21.4 明确 manifest 读取方包含 `resume`，但 STORY-015 LLD 的核心流程只定义按批次写 raw/manifest、熔断跳过和返回结果，未定义从既有 manifest 读取、判定已完成 batch、跳过/续跑 partial/failed batch 的断点续跑协议。 | 长时间或真实 provider 数据拉取中断后，重跑可能重复抓取、重复写 manifest，或无法稳定识别哪些 batch 已成功，影响数据拉取稳定性与可审计性。 | 在 STORY-015 LLD 中补充 `ResumePolicy` 或等价协议：以 `run_id + batch_id + source + interface + params_hash` 作为幂等键；启动时读取 manifest；`success` 默认跳过，`failed`/`partial_success` 按策略重试或重建；新增 resume/duplicate manifest 测试。 | `process/HLD.md:741`; `process/stories/STORY-015-cr004-connector-runtime-raw-manifest-LLD.md:183` |
| F-002 | 一般 | `CR004-ACCURACY-RUN-LINEAGE` | HLD canonical schema 要求 `source_run_id` 对应 manifest run；STORY-015 LLD 的 `ConnectorRequest` 只有 `source/interface/params/batch_id`，manifest 才有 `run_id`，fake rows 又要求至少包含 `source_run_id` 或 raw 等价字段。 | raw、manifest、canonical 三者的 run 血缘容易在实现中各自生成，后续 canonical 的 `source_run_id` 可能无法证明等于 manifest `run_id`，削弱 raw -> canonical 可重建与审计准确性。 | 将 `run_id` 提升为 runtime/request 的显式输入或 `RuntimeContext` 字段，并要求 raw metadata、manifest record、后续 canonical `source_run_id` 共用同一值；测试断言 fake raw metadata 与 manifest `run_id` 一致。 | `process/HLD.md:755`; `process/stories/STORY-015-cr004-connector-runtime-raw-manifest-LLD.md:113`; `process/stories/STORY-015-cr004-connector-runtime-raw-manifest-LLD.md:146`; `process/stories/STORY-015-cr004-connector-runtime-raw-manifest-LLD.md:222` |
| F-003 | 一般 | `CR004-CONTRACT-ERROR-ENUM` | STORY-014 LLD 的 `CONNECTOR_ERROR_TYPES` 不包含 `source_unresolved`，但 STORY-015 LLD 的 TickFlow unresolved 测试期望非重试 `source_unresolved`。同时 STORY-015 声明 `ConnectorError.error_type` 必须与 STORY-014 枚举对齐。 | 实现时无法同时满足 STORY-014 冻结枚举和 STORY-015 fail-fast 测试，导致真实 adapter 边界错误码漂移，影响调用方和 QA 对失败原因的稳定消费。 | 二选一收敛：在 STORY-014 枚举中加入 `source_unresolved`；或把 STORY-015 TickFlow unresolved 统一映射到已存在的 `source_disabled` / `contract_error`，并在 `SourceSpec.status=unresolved` 中保留细分状态。 | `process/stories/STORY-014-cr004-market-data-package-lake-contracts-LLD.md:109`; `process/stories/STORY-015-cr004-connector-runtime-raw-manifest-LLD.md:120`; `process/stories/STORY-015-cr004-connector-runtime-raw-manifest-LLD.md:257` |
| F-004 | 一般 | `CR004-ACCURACY-PIT-FIELDS` | HLD 与 ADR-011 要求价格数据携带或可推导 `adjustment_policy` 与 `available_at`；STORY-014 LLD 只把它们定义为 canonical 条件必需字段；STORY-015 fake rows 只要求至少含 `trade_date/symbol/close/source/source_run_id` 或 raw 等价字段，未冻结这些字段在 raw/manifest 中的来源或推导规则。 | STORY-016 在 normalizer 阶段可能临时选择不同推导口径，导致复权口径、可用时点和未来函数防护无法从 raw/manifest 稳定复现。 | 在 STORY-015 LLD 中要求 fake raw metadata 或 rows 明确包含 `adjustment_policy` 与 `available_at`，或在 manifest params 中冻结 deterministic derivation rule；新增测试覆盖 fake raw 到 canonical 时这两个字段可被稳定生成。 | `process/HLD.md:756`; `process/HLD.md:757`; `process/ARCHITECTURE-DECISION.md:222`; `process/stories/STORY-014-cr004-market-data-package-lake-contracts-LLD.md:105`; `process/stories/STORY-015-cr004-connector-runtime-raw-manifest-LLD.md:222` |
| F-005 | 一般 | `CR004-STABILITY-ATOMICITY` | STORY-015 LLD 定义成功或 partial success 时先写 raw JSONL 再 append manifest，manifest 原子性仅描述为单进程完整 JSON 行写入并 flush；未定义 raw 临时文件 rename、raw checksum、manifest 行校验或 raw/manifest 不一致时的恢复策略。 | 进程崩溃或文件系统异常可能留下 orphan raw、半写 raw 或 manifest 指向不可用 raw；后续 resume、normalization 与质量审计会缺少可靠依据。 | 明确 raw 写入采用 `*.tmp` 完整写入后原子 rename；manifest 增加 `raw_checksum`、`raw_row_count` 或等价校验字段；启动 resume/normalize 前校验 manifest 指向的 raw 存在且 hash/row_count 匹配。 | `process/stories/STORY-015-cr004-connector-runtime-raw-manifest-LLD.md:143`; `process/stories/STORY-015-cr004-connector-runtime-raw-manifest-LLD.md:191`; `process/stories/STORY-015-cr004-connector-runtime-raw-manifest-LLD.md:228`; `process/stories/STORY-015-cr004-connector-runtime-raw-manifest-LLD.md:302` |
| F-006 | 轻微 | `CR004-PLANNING-GATE-STATE` | `DEVELOPMENT-PLAN.yaml` 中 STORY-014/015 的 `lld_gate.status` 仍为 `not-started`，但对应 LLD 已存在且 frontmatter 为 `ready-for-review`；STORY-015 的 HLD anchor 还写成 `#216-真实-adapter-边界`，与实际 §21.6 不一致。 | 调度方后续计算 CP5 readiness 或追踪证据时可能把已生成 LLD 判定为未开始，或定位到错误锚点。 | 由 meta-po 在本轮评审后统一刷新计划状态和锚点；不影响本次架构语义判断，但应在 CP5 审查稿生成前修正。 | `process/DEVELOPMENT-PLAN.yaml:340`; `process/DEVELOPMENT-PLAN.yaml:345`; `process/DEVELOPMENT-PLAN.yaml:401`; `process/DEVELOPMENT-PLAN.yaml:406` |
| F-007 | 轻微 | `CR004-CONTRACT-TERMINOLOGY` | HLD §21.6 将 TickFlow 首轮默认写为 `disabled`，STORY-014 LLD 的 SourceRegistry 将 `tickflow` 写为 `unresolved`；两者语义可以兼容，但文档未显式说明 `unresolved` 是否也属于默认关闭状态。 | 实现者或 QA 可能把 `disabled` 与 `unresolved` 当作冲突状态，导致真实 adapter fail-fast 口径和错误码选择不一致。 | 在 STORY-014/015 LLD 中补一句状态映射：`unresolved` 是比 `disabled` 更强的默认关闭状态，表示 exact API 未确认；所有真实 source 默认都不得联网。 | `process/HLD.md:832`; `process/stories/STORY-014-cr004-market-data-package-lake-contracts-LLD.md:108`; `process/stories/STORY-014-cr004-market-data-package-lake-contracts-LLD.md:130` |

## 3. 汇总结论

- blocking_count: 0
- required_count: 5
- optional_count: 2
- recommended_next_action: `revise-and-resubmit`

架构方向总体正确：`market_data/` 独立于 `engine` 的边界、fake/offline 默认、真实 adapter fail-fast、限速/重试/熔断、raw/manifest 基础追溯、路径可配置与依赖最小化均已覆盖，能够支撑 CR-004 的最小离线闭环设计。

当前无“严重”阻断项，但不建议直接批准 CP5 Batch A。必须先修订 5 个“一般”问题，尤其是断点续跑、`run_id/source_run_id` 血缘、错误枚举一致性、`available_at/adjustment_policy` 来源以及 raw/manifest 原子性。这些问题不要求改动实现文件，但需要在 STORY-014/015 LLD 或对应 CP5 审查前收敛，否则会影响后续数据拉取稳定性和 canonical 准确性。

残余风险：真实 TickFlow/Tushare/AkShare 的 exact API、认证、限频和真实多源比对仍为 OPEN；这不阻塞 fake/offline 最小闭环，但必须继续保持真实 adapter 默认关闭，且不得在 STORY-014/015 中猜测真实接口。

## 4. 待确认项

- 是否将 `source_unresolved` 正式纳入 STORY-014 `CONNECTOR_ERROR_TYPES`，还是统一映射为既有错误类型并只在 `SourceSpec.status` 保留 `unresolved`。
- 是否要求 STORY-015 本轮就冻结 resume policy 与 raw checksum 字段，或允许 STORY-016 在 normalization LLD 中补充；架构建议前移到 STORY-015，因为 manifest 是 runtime/storage 事实源。
- `available_at` 的 fake 默认推导规则是否统一采用“交易日收盘后固定时间”，以及 `adjustment_policy` 是否固定为 `none` 还是沿用项目默认 `qfq`。
