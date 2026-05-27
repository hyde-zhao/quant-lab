---
artifact: "CR-004 Batch A STORY-014/STORY-015 QA findings"
reviewer: "meta-qa"
lane: "quality-data-reliability"
round: 1
status: final
governance_mode: review-gated
created_at: "2026-05-17"
---

# Review Findings

## 1. 审查范围

- 目标对象：`process/stories/STORY-014-cr004-market-data-package-lake-contracts.md`
- 目标对象：`process/stories/STORY-014-cr004-market-data-package-lake-contracts-LLD.md`
- 目标对象：`process/stories/STORY-015-cr004-connector-runtime-raw-manifest.md`
- 目标对象：`process/stories/STORY-015-cr004-connector-runtime-raw-manifest-LLD.md`
- 关联依据：`process/TEST-STRATEGY.md` CR-004 增量、`process/HLD.md` §21、`process/ARCHITECTURE-DECISION.md` ADR-008..012
- 审查目标：质量与数据可靠性评审。重点检查数据拉取稳定性、数据准确性与质量可验性、可移植性与安全边界，以及 Story/LLD 是否足以支撑后续 CP5/CP6/CP7。
- 审查方式：只读静态检查；未运行测试；未修改被评审对象、源码、测试、依赖锁文件或真实数据。

## 2. Findings

<!-- findings-table -->

| ID | Severity | Rule Ref | Evidence | Impact | Suggestion | Anchor |
|----|----------|----------|----------|--------|------------|--------|
| F-QA-001 | 一般 | `contract-consistency` | STORY-014 LLD 冻结的 `CONNECTOR_ERROR_TYPES` 包含 `source_disabled,interface_not_allowed,missing_credential,network_error,rate_limited,provider_error,contract_error,circuit_open`，但 STORY-015 LLD 的 TickFlow fail-fast 测试期望 `source_unresolved`。 | STORY-015 编码时可能无法同时满足上游契约和下游测试，导致 CP6/CP7 对 TickFlow unresolved 路径的断言漂移；真实 adapter 默认关闭的准确失败类型不可稳定验收。 | 在 CP5 前二选一收敛：要么在 STORY-014 契约中加入 `source_unresolved`，要么将 STORY-015 的 TickFlow 预期映射为现有 `source_disabled` / `contract_error` 等明确枚举，并同步错误说明与测试名。 | `process/stories/STORY-014-cr004-market-data-package-lake-contracts-LLD.md:109`; `process/stories/STORY-015-cr004-connector-runtime-raw-manifest-LLD.md:257` |
| F-QA-002 | 一般 | `manifest-traceability` | STORY-015 LLD 主流程先写 raw JSONL，再 append manifest；异常路径只声明 raw 写入失败时失败、manifest 也失败时返回 `StorageWriteError` 并停止，未说明 raw 已落盘但 manifest append 失败时如何清理、补偿或标记 orphan raw。ADR-011 将 manifest 定义为批次和派生链路事实源。 | 若 raw 写成功而 manifest 写失败，数据湖可能出现不可追溯 raw 文件，破坏 raw/canonical 可追溯链路，也会影响后续 normalization、quality 和 resume 的准确性。 | 在 LLD 中补充 manifest/raw 写入一致性策略和测试：例如先写 pending manifest 再写 raw 并最终更新状态；或 manifest append 失败时删除本批 raw / 写入隔离目录 / 返回可审计 orphan 记录。增加一个 `T015-MANIFEST-FAIL-01` 或等价负向用例。 | `process/stories/STORY-015-cr004-connector-runtime-raw-manifest-LLD.md:191`; `process/stories/STORY-015-cr004-connector-runtime-raw-manifest-LLD.md:215`; `process/ARCHITECTURE-DECISION.md:215` |
| F-QA-003 | 一般 | `schema-scope-clarity` | HLD §21.4 说明 canonical 最小内容至少覆盖 `prices/index_members/trade_calendar` 或 fake 等价数据集；STORY-014/LLD 只冻结 `prices` 的 canonical 必需字段，STORY-015 又明确不设计 canonical normalization、quality validation、多源比对。 | Batch A 本身不必完成 canonical/quality，但当前 Story/LLD 对 `index_members`、`trade_calendar` 与 quality/multi-source 的延期边界不够显式，后续 CP5/CP7 可能误把 Batch A 的契约冻结理解为完整数据准确性契约。 | 在 CP5 批次 A 结论或 LLD 中明确：本批只冻结 prices 与 manifest/raw 基础契约；`index_members`、`trade_calendar`、字段缺失/重复/异常价格/覆盖缺口、多源比对接口由 STORY-016/017 冻结。若不延期，则 STORY-014 应增加 dataset registry 占位与必需字段表。 | `process/HLD.md:742`; `process/HLD.md:744`; `process/stories/STORY-014-cr004-market-data-package-lake-contracts-LLD.md:104`; `process/stories/STORY-015-cr004-connector-runtime-raw-manifest-LLD.md:50` |
| F-QA-004 | 轻微 | `runtime-boundary-coverage` | CR-004 测试策略要求边界值覆盖 `max_retries=0/1/N`、限速 0 与正数、状态转换覆盖 retry、partial_success、failed、circuit_open、resume/skip；STORY-015 LLD 已覆盖 fake failure plan、retry、non-retry、throttle 和 circuit，但测试表只显式覆盖 `max_retries=2` 持续失败与 threshold=1 的熔断。 | 稳定性主路径可验，但 retry/throttle/circuit 的边界值和状态恢复证据不足，可能在 CP7 才暴露 off-by-one、真实等待或熔断 reset 缺陷。 | 增补小范围边界测试：`max_retries=0` 只调用 1 次、`throttle_seconds=0` 不等待、backoff cap 生效、jitter 固定值可断言、连续失败阈值大于 1、成功后 `failure_count` reset。 | `process/TEST-STRATEGY.md:118`; `process/TEST-STRATEGY.md:119`; `process/stories/STORY-015-cr004-connector-runtime-raw-manifest-LLD.md:252`; `process/stories/STORY-015-cr004-connector-runtime-raw-manifest-LLD.md:263` |
| F-QA-005 | 轻微 | `repo-hygiene-portability` | CR-004 测试策略把无新增凭据、真实行情大文件、`__pycache__/`、`.pyc`、`.ipynb_checkpoints/` 列为 CP7 出口和当前准备态风险；STORY-014/015 的验收标准和 DoD 明确禁止真实数据、凭据、`engine/**` 等修改，但没有把缓存/pycache 禁入库扫描落到 Story/LLD 自身检查项。 | 可移植性和交付卫生主要依赖 TEST-STRATEGY，CP6 级别容易漏掉新增缓存文件，尤其是实现后运行 pytest/compileall 时可能生成缓存。 | 在 CP5/CP6 检查清单或 LLD DoD 中加入缓存扫描要求：`find . -path "./.venv" -prune -o -path "./.git" -prune -o \( -type d -name "__pycache__" -o -name "*.pyc" -o -path "*/.ipynb_checkpoints/*" \) -print` 应无新增交付项；如已有历史缓存，需确认不进入提交范围。 | `process/TEST-STRATEGY.md:155`; `process/TEST-STRATEGY.md:173`; `process/TEST-STRATEGY.md:217`; `process/stories/STORY-014-cr004-market-data-package-lake-contracts-LLD.md:273`; `process/stories/STORY-015-cr004-connector-runtime-raw-manifest-LLD.md:322` |

## 3. 汇总结论

- blocking_count: 0
- required_count: 3
- optional_count: 2
- recommended_next_action: `revise-and-resubmit`

本轮未发现必须阻断 CP5 审查的严重缺陷。STORY-014/015 及其 LLD 对 fake/offline 默认、真实 adapter fail-fast、no-network 默认、clock/sleeper/jitter 注入、tmp_path 写入、不依赖 `engine`、凭据不落盘等目标覆盖较充分，具备进入 CP5 复审的基础。

建议在 CP5 批准前处理 3 个 required 级问题：错误枚举契约对齐、raw/manifest 写入一致性策略、Batch A 数据契约范围边界。处理后，STORY-015 的数据拉取稳定性和 raw/manifest 可追溯性会更容易在 CP6/CP7 中自动化验收。

残余风险：真实 TickFlow/Tushare/AkShare 接口、凭据策略和真实多源比对仍为 OPEN；当前设计只能证明 fake/offline 最小闭环与真实 adapter fail-fast，不能证明真实联网抓取的准确性、配额稳定性或生产级数据完整性。

## 4. 待确认项

- CP5 是否接受 Batch A 只冻结 `prices` + raw/manifest 基础契约，并将 `index_members`、`trade_calendar`、quality gate 与多源比对接口显式延期到 STORY-016/017。
- TickFlow unresolved 路径应使用新的 `source_unresolved` 错误枚举，还是复用既有错误枚举并通过 `source_status=unresolved` 表达。
- manifest append 失败后的恢复策略采用清理 raw、pending/final manifest 双阶段，还是 orphan 记录隔离机制。
