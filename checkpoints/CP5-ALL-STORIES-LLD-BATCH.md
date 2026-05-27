---
checkpoint_id: "CP5"
checkpoint_name: "CR-014 全 A since-inception 数据湖 LLD 批次人工审查"
type: "batch_auto_then_manual"
status: "approved"
owner: "meta-po"
created_at: "2026-05-27T00:37:26+08:00"
reviewed_by: "user"
reviewed_at: "2026-05-27T07:22:46+08:00"
auto_check_result:
  - "process/checks/CP4-CR014-STORY-DAG-PARALLEL-SAFETY.md"
  - "process/checks/CP4-CR014-BATCH-B-WINDOWED-REAL-FETCH-WRITE-DAG-ADDENDUM.md"
  - "process/checks/CP5-CR014-S01-a-share-universe-lifecycle-contract-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR014-S02-parquet-layout-manifest-catalog-publish-gate-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR014-S03-p0-plan-run-normalize-validate-publish-contract-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR014-S04-duckdb-readonly-query-audit-parity-boundary-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR014-S05-full-history-readiness-gap-claim-boundary-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR014-S06-incremental-refresh-replay-retention-contract-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR014-S07-research-consumer-readonly-docs-runbook-boundary-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR014-S08-w3-minute-tick-level2-vwap-blocked-decision-boundary-LLD-IMPLEMENTABILITY.md"
target:
  phase: "story-planning"
  story_id: ""
  batch_id: "CR014-FULL-HISTORY-LAKE-BATCH-A"
  future_batch_id: "CR014-REAL-RUN-BATCH-B"
  future_story_id: "CR014-S09-windowed-real-fetch-lake-write-run"
  artifacts:
    - "process/stories/CR014-S01-a-share-universe-lifecycle-contract-LLD.md"
    - "process/stories/CR014-S02-parquet-layout-manifest-catalog-publish-gate-LLD.md"
    - "process/stories/CR014-S03-p0-plan-run-normalize-validate-publish-contract-LLD.md"
    - "process/stories/CR014-S04-duckdb-readonly-query-audit-parity-boundary-LLD.md"
    - "process/stories/CR014-S05-full-history-readiness-gap-claim-boundary-LLD.md"
    - "process/stories/CR014-S06-incremental-refresh-replay-retention-contract-LLD.md"
    - "process/stories/CR014-S07-research-consumer-readonly-docs-runbook-boundary-LLD.md"
    - "process/stories/CR014-S08-w3-minute-tick-level2-vwap-blocked-decision-boundary-LLD.md"
---

# CP5 CR-014 全 A since-inception 数据湖 LLD 批次人工审查

## Decision Brief

| 字段 | 内容 |
|---|---|
| 推荐决策 | `approve`：批准 CR014-S01..S08 八份 LLD 作为后续 Story 执行输入；同时接受真实 provider 抓取与 raw/manifest 写湖拆分为后续 `CR014-S09-windowed-real-fetch-lake-write-run` / `CR014-REAL-RUN-BATCH-B`；本 CP5 不批准 S09 实现或真实执行 |
| 不代表的授权 | CP5 批准不等同于 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 操作、旧报告覆盖、catalog current pointer 发布、DuckDB 依赖引入、DuckDB 写入、S09 实现或 S09 真实执行授权 |
| 备选方案 | 见下方“本次 CP5 待决策问题、备选方案与优劣”的 24 项决策矩阵；每项均至少给出 1 个备选方案，多数给出 2 个备选方案 |
| 影响维度 | 用户价值：将 CP3 已批准的 D1-D12 架构决策落为可执行合同；实现复杂度：8 Story、4 Waves、跨 catalog / pipeline / DuckDB read-only / research consumer 多边界；可验证性：8 个 Story 均有 CP5 自动预检和后续 CP6/CP7 门控；维护成本：需要长期保持 Parquet/catalog 事实源、publish gate、DuckDB read-only 与研究消费边界一致；安全 / 权限：继续保持真实操作计数为 0，真实执行另行授权 |
| 推荐理由 | 8 份 BATCH-A LLD 均已通过自动可实现性检查，三条 review lane 已补齐 CP5 决策备选方案；S09 已作为后续真实执行 Story 登记，可避免把真实抓取/写湖副作用混入当前合同实现批次 |
| 回退策略 | 若实现中发现某份 LLD 合同错误，回退到 story-planning 重开对应 LLD 与 CP5；若发现 S09 拆分不合适，回退到 story-planning 重写 S03/S06/S09 边界并重新发起 CP4/CP5；若发现 D1-D12 任一基础决策需要改变，回退到 solution-design 重写 HLD/ADR/ADR 映射 |

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---|---|
| `process/checks/CP4-CR014-STORY-DAG-PARALLEL-SAFETY.md` | PASS | 0 | 8 Story、4 Waves、DAG、文件所有权、LLD 批次和 forbidden operation 计数均通过 |
| `process/checks/CP4-CR014-BATCH-B-WINDOWED-REAL-FETCH-WRITE-DAG-ADDENDUM.md` | PASS | 0 | S09 后续 BATCH-B DAG addendum 通过；S09 依赖 S01..S08 verified，不释放当前真实执行授权 |
| `process/checks/CP5-CR014-S01-a-share-universe-lifecycle-contract-LLD-IMPLEMENTABILITY.md` | PASS | 0 | S01 LLD 可审查；覆盖全 A universe / lifecycle / code-change 合同 |
| `process/checks/CP5-CR014-S02-parquet-layout-manifest-catalog-publish-gate-LLD-IMPLEMENTABILITY.md` | PASS | 0 | S02 LLD 可审查；覆盖 Parquet layout、manifest、catalog current pointer 与 explicit publish gate |
| `process/checks/CP5-CR014-S03-p0-plan-run-normalize-validate-publish-contract-LLD-IMPLEMENTABILITY.md` | PASS | 0 | S03 LLD 可审查；覆盖 plan -> run -> normalize/replay -> validate -> publish 合同 |
| `process/checks/CP5-CR014-S04-duckdb-readonly-query-audit-parity-boundary-LLD-IMPLEMENTABILITY.md` | PASS | 0 | S04 LLD 可审查；覆盖 DuckDB read-only 查询、审计、parity 与 fallback 边界 |
| `process/checks/CP5-CR014-S05-full-history-readiness-gap-claim-boundary-LLD-IMPLEMENTABILITY.md` | PASS | 0 | S05 LLD 可审查；覆盖 full-history readiness、gap register 和 claim boundary |
| `process/checks/CP5-CR014-S06-incremental-refresh-replay-retention-contract-LLD-IMPLEMENTABILITY.md` | PASS | 0 | S06 LLD 可审查；覆盖 incremental refresh、replay、retention 与 current pointer 隔离 |
| `process/checks/CP5-CR014-S07-research-consumer-readonly-docs-runbook-boundary-LLD-IMPLEMENTABILITY.md` | PASS | 0 | S07 LLD 可审查；覆盖研究消费只读合同、文档和 runbook 边界 |
| `process/checks/CP5-CR014-S08-w3-minute-tick-level2-vwap-blocked-decision-boundary-LLD-IMPLEMENTABILITY.md` | PASS | 0 | S08 LLD 可审查；覆盖 W3 / minute / tick / Level2 / VWAP blocked 决策边界 |

## CP3 已批准基础决策

| ID | 已接受结论 | 对 CP5 的约束 |
|---|---|---|
| D1 | 接受 DuckDB read-only 与 lake pipeline 写入并存 | LLD 必须保持写入和查询职责分离 |
| D2 | 接受 CP3 / CP4 / CP5 前真实操作计数为 0 | 本检查点不得释放提前试写或真实抓取 |
| D3 | 接受 CP5 + 用户显式授权后才写 raw / manifest / run metadata | CP5 批准 LLD 后，真实写入仍需 Story 执行阶段的显式授权 |
| D4 | 接受 Normalize / Replay 只生成 candidate，不更新 current pointer | S03 / S06 不得把 candidate 自动发布为 current truth |
| D5 | 接受 Validate / parity PASS 也不自动 publish | S04 parity PASS 不得触发发布 |
| D6 | 接受只有 Explicit Publish Gate 能更新 catalog current pointer | S02 / S03 必须把 publish gate 作为 current truth 单入口 |
| D7 | 接受 DuckDB 输出不反向成为 source of truth | S04 输出只能作为审计 / 查询 / parity 产物 |
| D8 | 接受 CR14-A 可行性判断 | 本批 LLD 按 CR14-A 继续，不重选 CR14-B/C/D |
| D9 | 接受 plan -> run -> normalize/replay -> validate -> publish -> read/query 用户模型 | S03 / S06 / S07 的 CLI 和状态模型必须遵循该顺序 |
| D10 | 接受 Parquet/catalog 为事实源，DuckDB 做只读扩展 | S02 与 S04 必须共同维护事实源和 read-only query 边界 |
| D11 | 接受研究消费层不得直接 DuckDB 写入 / 发布 / 扫未发布 lake | S07 是研究侧硬边界，不得绕过生产门控 |
| D12 | 接受 CP3 R2 只批准 HLD / ADR，不批准实现或依赖引入 | 本 CP5 只审查 LLD；实现和依赖引入仍受后续门控 |

## 子 Agent 决策评审摘要

| Lane | Agent | 结论摘要 | Handoff 证据 |
|---|---|---|---|
| 架构 | `meta-se / se-wei` | 识别 20 个架构决策项，重点是 Parquet/catalog 事实源、publish gate、DuckDB read-only、状态机、claim boundary、研究消费边界和 CP6/CP7 门控 | `process/handoffs/META-REVIEW-CR014-CP5-DECISION-OPTIONS-2026-05-27.md` |
| 实现 | `meta-dev / dev-qin` | 识别 13 个实现决策项，重点是 S03/S04/S06 串行顺序、S05/S08/S07 顺序、DuckDB 依赖门控、真实授权拆分、文件所有权和 CP5 后状态同步 | `process/handoffs/META-REVIEW-CR014-CP5-DECISION-OPTIONS-2026-05-27.md` |
| 质量 | `meta-qa / qa-kong` | 识别 22 个质量与风险决策项，重点是真实操作计数、旧数据禁区、OPEN/Spike 风险接受、docs 后置、W3/VWAP blocked 和离线 CP7 验证 | `process/handoffs/META-REVIEW-CR014-CP5-DECISION-OPTIONS-2026-05-27.md` |

## 本次 CP5 待决策问题、备选方案与优劣

> 下面 24 项为 meta-po 合并三条 review lane 后的去重决策矩阵，并按用户要求新增真实抓取 / 写湖拆分决策。推荐列均为本批 CP5 的默认建议；若用户不接受任一标记为“阻断”的推荐，需要回到对应 Story LLD 或 HLD / ADR 修改后重新发起 CP5。

| ID | 决策问题 | 推荐 | 备选方案 A：优劣与适用条件 | 备选方案 B：优劣与适用条件 | 接受影响 | 不接受影响 | 是否阻断 CP5 |
|---|---|---|---|---|---|---|---|
| CP5-D01 | 本次 CP5 批准范围是什么 | 只批准 S01..S08 八份 LLD 作为实现输入；不授权 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 操作、旧 reports 覆盖、DuckDB 依赖引入、DuckDB 写入或 catalog current pointer 发布 | CP5 同时批准隔离 smoke：优点是较早暴露真实源 / schema / lake 问题；缺点是需要新增 sandbox root、authorization_id、回滚和证据清单；适用于用户愿意单独确认小窗口真实验证 | CP5 直接批准全量真实写入：优点是推进最快；缺点是污染、凭据、回滚和审计风险最高；不建议 | 设计批准与执行授权分离；后续实现只做离线合同、fixture、tmp_path、dry-run、只读验证 | 需要重写 CP5 Decision Brief、S03/S06/S02 publish 授权模型和运行授权边界 | 是 |
| CP5-D02 | 是否统一批准 S01..S08 全量 LLD 批次，而不是只批部分 Wave / Story | 统一批准或统一要求修改；本批共享事实源、claim 和研究消费接口，部分批准风险高 | 只批准 W1/W2，延后 S05..S08：优点是可早启动底层合同；缺点是事实源能写但 claim / research 边界未确认；适用于明确禁止输出 full-A claim 的内部重构 | 逐 Story 单独审批：优点是粒度细；缺点是跨 Story 字段一致性靠人工维护；适用于低耦合 Story，不适合本批 | 一次性冻结完整数据湖、publish、DuckDB、claim、research 边界，CP5 后 dev_gate 可计算 | 部分确认会导致实现方不清楚哪些声明、接口和边界已冻结 | 是 |
| CP5-D03 | 全 A since-inception 分母是否以 S01 lifecycle / code-change / 最近已闭市交易日合同为统一基准 | 接受 S01：以稳定 `security_id`、lifecycle 字段、code-change 链路和最近已闭市开市交易日作为统一 denominator | 只用当前股票快照 / `stock_basic`：优点是实现快；缺点是退市、改名、代码变更缺失，幸存者偏差明显；适用于只声明“当前在市股票” | 只以价格数据出现过的 symbol 作为分母：优点是依赖少；缺点是 symbol 变更和退市口径不稳定；适用于探索性、非生产声明 | S02 catalog、S05 claim、S07 report 可共享同一 denominator，full-A claim 有可审计前置 | 下游每个 Story 自行推断 universe，readiness 和 claim boundary 不可信 | 是 |
| CP5-D04 | P0 dataset 范围是否限定为 7 类日线 / 基础数据，并把 W3 / 高频 / VWAP 留在 blocked 边界 | 接受 S03：P0 为 `prices`、`adj_factor`、`hs300_index`、`trade_calendar`、`index_members`、`index_weights`、`stock_basic`；lifecycle/code-change 是必需合同输入，不单列 P0 | 先只做 `prices` / `adj_factor`：优点是范围小；缺点是无法支持指数成分、日历、复权、全 A claim；适用于单一行情链路快速验证 | 把 W3 / minute / tick / Level2 / VWAP 纳入 P0：优点是能力完整；缺点是新增数据源、权限、成本和验收复杂度；适用于已有高频接口与授权 | plan/run/publish 模型范围可控，S08 blocked 边界与 P0 边界一致 | P0 边界不清会导致补数、claim 和研究消费范围漂移 | 是 |
| CP5-D05 | Parquet/catalog 是否继续作为 source of truth，DuckDB 是否只做只读扩展 | 接受 S02/S04：Parquet + manifest + catalog current pointer 是事实源；DuckDB 只作为 query/audit/parity evidence，不反向成为事实源 | 持久 `.duckdb` / DuckLake 做事实源：优点是查询强；缺点是双写、恢复、跨工具兼容和 lineage 更复杂；适用于未来另起 ADR/CR | 只用 raw / manifest / candidate，不设 catalog current pointer：优点是少一个对象；缺点是读者无法知道可信版本，candidate 易污染研究 | lineage、回滚、publish、研究读取边界清晰，DuckDB 可替换为 fallback | 事实源多头或无 current pointer，会破坏 publish gate 与研究消费边界 | 是 |
| CP5-D06 | Catalog pointer 是否以 CR014 必填字段为 canonical，并保持旧 catalog 兼容 | 接受字段集：dataset、schema_version、coverage_start/end、coverage_denominator、latest_manifest_run_id、lineage_checksum、published_at、known_limitations、universe_scope、as_of_trade_date；旧 `CatalogEntry` 兼容读取 | 原地扩展现有 `CatalogEntry`：优点是调用路径短；缺点是可能影响 CR010/CR013 既有读者；适用于现有模型可接纳字段 | CR014 独立 sidecar pointer schema：优点是隔离强；缺点是读者要处理两套 catalog；适用于现有 catalog 难兼容扩展 | S02/S04/S05/S07/S08 可按同一字段集实现，字段缺失时 fail-closed | 字段未定会让 S07/S08 OPEN 项在实现期变成接口冲突 | 是，条件性 |
| CP5-D07 | Candidate path、published path、candidate audit path 是否必须物理 / 语义分离，manifest 是否 append-only | 接受 S02：candidate 含 `run_id`，published 只能经 catalog pointer 暴露，candidate audit path 只做 evidence，manifest append-only | 同一路径加 status 字段区分 candidate/published：优点是路径简单；缺点是误读和覆盖风险高；适用于单用户临时实验 | 完全独立 lake root：优点是隔离最强；缺点是部署和迁移复杂；适用于生产多租户或强隔离环境 | 未发布候选不会被 reader / DuckDB / research 误当 current truth | candidate 与 published 混淆会破坏 publish gate 和 claim boundary | 是 |
| CP5-D08 | Explicit Publish Gate 是否为唯一 current pointer 更新入口 | 接受 S02/S03：quality/readiness PASS、manifest 完整、S01 denominator 完整、publish intent / approval token 同时满足才允许 atomic pointer update；Validate/parity PASS 不自动 publish | Validate PASS 自动 publish：优点是自动化强；缺点是质量检查被副作用化，误发布风险高；适用于低风险沙箱 | 人工逐文件替换 current pointer：优点是控制强；缺点是不可审计、不可测试、易绕过 gate；适用于临时应急 | current truth 单入口、可审计、可回滚；S04/S05/S07 可依赖 publish 状态 | candidate、parity evidence 或人工变更可能绕过事实源门控 | 是 |
| CP5-D09 | 用户 / CLI 状态模型是否固定为 plan -> run -> normalize/replay -> validate -> publish -> read/query | 接受 S03 状态机；`publish` 是独立显式阶段，`read/query` 只读 published pointer 或受控 candidate audit evidence | one-shot backfill：优点是短期快；缺点是失败恢复、重放、审计和授权边界弱；适用于小范围一次性补数 | 多个无统一状态脚本：优点是局部简单；缺点是用户模型不一致，CP6/CP7 难验证；适用于临时运维脚本 | 每阶段副作用、输入输出和授权点清晰，runbook 可解释 | provider fetch、normalize、validate、publish 边界会混杂 | 是 |
| CP5-D10 | 真实写入 / 发布 / retention 授权是否拆分 | 接受拆分为 `run raw/manifest`、`normalize/replay candidate`、`publish current pointer`、`retention execute` 四类；每类需要 authorization_id、scope、dataset/date/source/interface、permission counters 和回滚说明 | 合并为一次“真实补数授权”：优点是操作简单；缺点是 run、candidate、publish、retention 风险混杂；适用于小范围内部实验 | 只允许 plan/dry-run，暂不允许任何真实写入：优点是最安全；缺点是生产数据湖目标无法进入真实闭环；适用于先交付合同和工具 | 用户可分别批准抓取、候选产物、发布和删除 / 归档，高风险动作不会互相搭车 | publish 或 retention 可能被误包含在 run 授权里，回滚和污染风险上升 | 是 |
| CP5-D11 | 真实 run gate 是否必须 exact 化 | 接受 S03 run gate：CP5 approved、LLD confirmed、依赖满足、文件无冲突、authorization_id、source/interface allowlist 缺一不可；缺任一项 connector 不可调用 | CP5 approved 后默认允许所有 P0 run：优点是执行快；缺点是 provider/lake 范围过宽；适用于已有外部授权系统覆盖 dataset/date/source | 逐 dataset/date 手工确认，不做机器 gate：优点是人工细；缺点是不可自动验证、易漏记录；适用于极低频人工运行 | 权限边界可计算，CP6/CP7 可检查 connector call count 与 counters | 设计批准和真实抓取 / 写湖授权混淆 | 是 |
| CP5-D12 | 实现顺序和共享文件所有权如何控制 | 接受保守顺序：S01/S02 -> S03 verified -> S04 -> S06；S05 verified 后先 S08，再 S07；共享文件按主所有权串行写入，非 owner 只消费，需写 shared 即停止回 meta-po | S03 CP6 PASS 后并行 S04/S06：优点是缩短周期；缺点是 S03 CP7 失败会牵连 DuckDB audit 与 replay/retention | 抽出共享 schema / integration Story：优点是边界最干净；缺点是需重开 Story/LLD/CP5；适用于用户要求零共享冲突 | 降低 runtime/catalog/claims/research 接口漂移风险，CP7 失败可定位单 Story | 并行漂移和文件冲突会在实现阶段阻塞或扩大回修面 | 是 |
| CP5-D13 | S04 是否在本批直接引入 DuckDB Python 依赖并修改 `pyproject.toml` / `uv.lock` | 不授权依赖修改；S04 先实现 optional lazy-import、`duckdb_dependency_unavailable` 和 pandas/pyarrow fallback，DuckDB 依赖另行显式批准 | CP5 直接批准 `uv add duckdb`：优点是真实 DuckDB parity 可直接验证；缺点是依赖锁、平台兼容、安装风险进入本批；适用于用户明确接受依赖变更 | 完全取消 DuckDB，仅保留 pandas/pyarrow：优点是依赖最少；缺点是大范围审计 / query / parity 扩展能力弱；适用于范围收缩 | S04 可无新依赖落地 read-only 边界，后续引入 DuckDB 回滚成本低 | 需要重写 S04/ADR 或补依赖授权，否则实现会自我阻塞 | 是 |
| CP5-D14 | DuckDB SQL / 路径边界是否必须采用只读模板、路径白名单和 side-effect sentinel | 接受 S04：只允许 SELECT / WITH SELECT 模板；禁止 DDL/DML/COPY/EXPORT/ATTACH/INSTALL/LOAD/写风险 PRAGMA；读取对象只允许 catalog pointer 或受控 candidate audit path | 允许自由 SQL + read-only connection：优点是灵活；缺点是模板审计弱，仍可能写文件或 attach 外部对象；适用于可信内部分析环境 | 禁用 DuckDB，只保留 fallback audit：优点是边界简单；缺点是性能和表达能力下降；适用于不愿承担 SQL 模板治理成本 | DuckDB 可作为只读审计层，不污染事实源、不绕过 catalog | S04 可能成为潜在写入或绕过 publish 的入口 | 是 |
| CP5-D15 | DuckDB parity / audit evidence 是否只能作为 evidence，不能生成 allowed claim 或更新 pointer | 接受 S04/S05：parity PASS 仍是 evidence-only；allowed claim 由 S05 在 publish/current truth 前提下判定 | parity PASS 自动提升为 allowed claim：优点是报告更快；缺点是未发布 candidate 会被当成 current truth；适用于非生产探索且报告降级 | parity PASS 触发 publish gate：优点是接近自动化；缺点是审计与发布耦合；适用于未来独立 ADR 中定义自动发布流水线 | evidence、publish、claim 三层职责清楚 | DuckDB 可能被误解为事实源或 claim 生成方，研究报告过度声明 | 是 |
| CP5-D16 | Full-history readiness / gap / claim boundary 是否结构化且 exact schema 化 | 接受 S05：`ReadinessMatrix`、`GapRegister`、`ClaimBoundarySummary.allowed_claims/blocked_claims/required_missing/release_condition/evidence_path/permission_counters` 为 canonical；任一 gate 未过时 full-A allowed production claim 为 0 | 只在文档中人工声明缺口：优点是实现轻；缺点是不可机器验证，报告声明漂移；适用于临时说明 | 允许 warn 状态输出 full-A claim：优点是用户体验顺滑；缺点是生产声明不严谨；适用于明确 research degradation 的非生产报告 | full-A claim 可追溯、可阻断、可解释，S07/S08 可消费 | claim boundary 不可验证，W3/VWAP blocked 可能漏挡 | 是 |
| CP5-D17 | 旧 CR010/CR012/CR013 evidence、旧 reports 和旧 `data/**` 是否只可作为引用字符串 / baseline ref | 接受：旧 evidence 只进入 `evidence_path` / `legacy_baseline_ref` 字段；不读取、不覆盖、不迁移、不作为 current truth | 读取旧 reports 抽取 evidence：优点是可复用历史信息；缺点是违反当前禁止项且可能引入未脱敏 / 过期证据；适用于另行授权审计迁移 | 迁移旧 data/reports 到新 lake：优点是保留历史资产；缺点是范围大、风险高，需专门 CR；适用于独立数据迁移项目 | 防止旧实验 / 旧数据污染全 A since-inception claim | 违反旧 `data/**` 操作和旧报告覆盖边界，当前 CP5 设计不足 | 是 |
| CP5-D18 | S06 replay / incremental / retention 是否保持无 provider、无 credential、无 raw write、无 current pointer change，retention 默认 dry-run | 接受 S06：replay 只从 raw/manifest refs 重放派生链路；retention 只输出 recommendation，不自动删除、迁移或覆盖 | replay 缺 raw 时自动补抓 provider：优点是恢复方便；缺点是越权抓取和凭据读取风险；适用于另有明确运行授权 | retention 自动 delete/archive：优点是节省空间；缺点是可能丢失审计证据或误删 published 引用；适用于单独 ops Story 和执行授权 | 增量、重放、保留策略可实现但不越权，published truth 受保护 | S06 引入真实副作用，突破当前 CP5 权限边界 | 是 |
| CP5-D19 | 研究消费层和 docs/runbook 边界如何处理 | 接受 S07：研究层只消费 published current truth、S05 claim summary、DuckDB evidence ref；不得 provider fetch、lake write、direct DuckDB、publish、candidate scan；README/USER-MANUAL 当前阶段不修改，只产出后续 refresh contract | 研究层可直接扫 candidate lake 做实验：优点是研究迭代快；缺点是绕过 publish 和 claim boundary；适用于沙箱实验且不产出 production claim | 本批同步修改 README/USER-MANUAL：优点是用户材料更早对齐；缺点是文件所有权和文档阶段边界扩大；适用于 CP5 后另行路由 meta-doc | 实验报告只基于已发布事实源和结构化声明，文档刷新后置不越界 | 研究侧绕过生产门控，claim boundary 失真，文档阶段混入实现批次 | 是，docs 同步本身不阻断但需另行路由 |
| CP5-D20 | W3 / minute / tick / Level2 / order book / order match / real VWAP / VWAP fill 是否保持 blocked，close proxy 或 `amount/volume` 是否可解除真实 VWAP blocked | 接受 S08：上述能力 production allowed claim 为 0；release condition 必须指向后续 source/interface + Story + CP5 + 用户授权；close proxy、`amount/volume` 只能是 research degradation 或 denied substitute | 把 W3/高频数据纳入本批：优点是能力完整；缺点是新增 provider、权限、成本、schema、验证环境；适用于新 CR | 允许 `amount/volume` 或 close proxy 作为真实 VWAP 近似：优点是报告更完整；缺点是误导真实执行价 claim；不建议 | “全 A since-inception”不会被误读为全粒度 / 真实执行价覆盖 | 高频和真实 VWAP claim 越界，报告真实性被高估 | 是 |
| CP5-D21 | S04-S08 的 OPEN / Spike 是否可作为非阻断风险进入 CP5 | 接受，但只接受为“实现前对齐 / 后续路由问题”，不得视为实现授权、依赖授权或真实执行授权 | 要求所有 OPEN/Spike 关闭后再 approve：优点是 CP5 更干净；缺点是阻塞批次，部分 OPEN 依赖 CP5 才能关闭；适用于零 OPEN 放行偏好 | 全部开放项无条件放行：优点是推进快；缺点是字段 / 依赖 / docs 路由风险滑入 CP6；不建议 | CP5 可批准 LLD，CP6 前仍必须验证字段名、依赖策略、docs 路由和共享文件所有权 | S04-S08 至少需返工关闭 OPEN/Spike，批次延期 | 否，但必须写入风险接受项 |
| CP5-D22 | CP6/CP7 验证策略是否保持离线 fixture、tmp_path、静态扫描和 monkeypatch sentinel，不使用真实 lake/provider/凭据/旧数据 | 接受；每个 Story 仍需 CP6/CP7，CP7 失败不得标记 verified | 增加可选真实 smoke：优点是更接近生产；缺点是需要凭据、写入边界和单独授权；适用于 CP6/CP7 后的授权验证 | 只做人工代码审查，不跑测试：优点是成本低；缺点是权限计数和 fail-closed 路径不可验证；不符合当前验收 | CP7 可断言 network/lake/credential/legacy ops 为 0，claim boundary 可机器验证 | CP5 批准被误用为实现质量批准，无法证明 forbidden ops 生效 | 是 |
| CP5-D23 | CP5 人工结果是否必须显式写入风险接受项，而不是只记录 `approve` | 要求写入标准风险接受项：非阻断 OPEN/Spike、真实操作 0、publish 分离、research read-only、W3/VWAP blocked、CP6/CP7 不跳过、真实授权拆分 | 用户只回复 `approve`，由 meta-po 回填标准风险接受项：优点是交互简单；缺点是必须确保回填完整；适用于用户接受默认推荐 | 用户逐项勾选每个风险：优点是确认最强；缺点是审批成本高；适用于更高风险审查 | 后续争议少，CP6/CP7 可按风险接受边界执行 | `approve` 语义可能被误解为真实执行、publish 或依赖授权 | 否，但作为 CP5 通过条件 |
| CP5-D24 | 是否接受真实 provider 抓取与 raw/manifest 写湖拆分为后续 `CR014-S09-windowed-real-fetch-lake-write-run`，在 S01..S08 完成后按 dataset/date window 分时段执行 | 接受；S09 属于 `CR014-REAL-RUN-BATCH-B`，必须等 S01..S08 verified、S09 LLD approved、S09 CP5 approved、用户提供 per-run authorization_id 和 dataset/date/source/lake/window 范围后执行；raw/manifest 写湖不自动 publish current pointer | 将真实抓取/写湖并入 S03：优点是流程少；缺点是 S03 同时承担合同和真实副作用，CP5/CP7 边界混乱，风险高 | 将真实执行完全延后到人工运维，不建 Story：优点是当前开发更轻；缺点是缺少可审计 run gate、window policy、manifest/resume 追踪，难以生产化 | 真实执行时机明确，BATCH-A 可先稳定合同和边界，BATCH-B 按窗口可审计执行 | 不接受则需要重写 S03/S06/S02 的授权和 publish 边界，或继续没有真实执行 Story | 是 |

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| CP3 R2 人工审查 approved | 通过 | `checkpoints/CP3-CR014-A-SHARE-SINCE-INCEPTION-DATA-LAKE-HLD-REVIEW-R2.md` | 用户已接受 D1-D12 推荐决策 |
| CP4 自动预检 PASS | 通过 | `process/checks/CP4-CR014-STORY-DAG-PARALLEL-SAFETY.md` | Story DAG、Wave、文件所有权和 forbidden operation 计数通过 |
| 8 张 Story 卡片进入 LLD review 状态 | 通过 | `process/stories/CR014-S01..S08-*.md` | 8 张均为 `lld-ready-for-review` |
| 8 份 LLD 已输出 | 通过 | `process/stories/CR014-S01..S08-*-LLD.md` | 8 份均为 `ready-for-review`、`confirmed=false`、`implementation_allowed=false` |
| 8 个 Story 级 CP5 自动预检 PASS | 通过 | `process/checks/CP5-CR014-S01..S08-*-LLD-IMPLEMENTABILITY.md` | 8 个均为 PASS |
| 子 agent 调度证据完整 | 通过 | `process/handoffs/META-DEV-CR014-LLD-BATCH-A-2026-05-27.md` | 3 个 meta-dev 分片均 completed / closed |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 是否接受 S01 LLD 作为 universe / lifecycle / code-change 合同实现输入 | 通过 | `process/stories/CR014-S01-a-share-universe-lifecycle-contract-LLD.md` | 用户已按推荐全部允许 |
| 2 | 是否接受 S02 LLD 作为 Parquet layout / manifest / catalog current pointer / publish gate 实现输入 | 通过 | `process/stories/CR014-S02-parquet-layout-manifest-catalog-publish-gate-LLD.md` | 用户已按推荐全部允许 |
| 3 | 是否接受 S03 LLD 作为 P0 dataset plan/run/normalize/validate/publish 合同实现输入 | 通过 | `process/stories/CR014-S03-p0-plan-run-normalize-validate-publish-contract-LLD.md` | 用户已按推荐全部允许 |
| 4 | 是否接受 S04 LLD 作为 DuckDB read-only query/audit/parity 边界实现输入，并保留 DuckDB 依赖引入显式门控 | 通过 | `process/stories/CR014-S04-duckdb-readonly-query-audit-parity-boundary-LLD.md` | 用户已按推荐全部允许；本批仍不引入 DuckDB 依赖 |
| 5 | 是否接受 S05 LLD 作为 readiness / gap / claim boundary 实现输入 | 通过 | `process/stories/CR014-S05-full-history-readiness-gap-claim-boundary-LLD.md` | 用户已按推荐全部允许 |
| 6 | 是否接受 S06 LLD 作为 incremental refresh / replay / retention 实现输入 | 通过 | `process/stories/CR014-S06-incremental-refresh-replay-retention-contract-LLD.md` | 用户已按推荐全部允许 |
| 7 | 是否接受 S07 LLD 作为 research consumer read-only / docs / runbook 边界实现输入 | 通过 | `process/stories/CR014-S07-research-consumer-readonly-docs-runbook-boundary-LLD.md` | 用户已按推荐全部允许 |
| 8 | 是否接受 S08 LLD 作为 W3 / minute / tick / Level2 / VWAP blocked claim boundary 实现输入 | 通过 | `process/stories/CR014-S08-w3-minute-tick-level2-vwap-blocked-decision-boundary-LLD.md` | 用户已按推荐全部允许 |
| 9 | 是否确认 8 份 LLD 均保留 14 个可见章节，且强输入字段 `tier`、`shared_fragments`、`open_items` 均存在 | 通过 | meta-po 复核；8 份 LLD frontmatter | 用户已按推荐全部允许 |
| 10 | 是否确认 CP5 批准不授权真实联网、provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 操作或旧报告覆盖 | 通过 | Decision Brief；D2 / D3 / D12；8 份 LLD §14 | 用户已按推荐全部允许 |
| 11 | 是否确认 Validate/parity PASS 不自动 publish，只有 explicit publish gate 能更新 catalog current pointer | 通过 | D4 / D5 / D6；S02 / S03 / S04 / S06 LLD | 用户已按推荐全部允许 |
| 12 | 是否确认研究消费层不得直接 DuckDB 写入、发布或扫未发布 lake | 通过 | D11；S07 LLD | 用户已按推荐全部允许 |
| 13 | 是否确认后续每个 Story 仍必须通过 CP6 / CP7，CP7 失败不得标记 verified | 通过 | Meta Flow 编码与验证门控；8 张 Story dev_gate | 用户已按推荐全部允许 |
| 14 | 是否接受真实抓取 / 写湖已拆分为 S09 后续 BATCH-B，不属于当前 BATCH-A CP5 实现或真实执行授权 | 通过 | `process/stories/CR014-S09-windowed-real-fetch-lake-write-run.md`；`process/checks/CP4-CR014-BATCH-B-WINDOWED-REAL-FETCH-WRITE-DAG-ADDENDUM.md`；CP5-D24 | 用户已按推荐全部允许 |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| 8 份 LLD 可作为后续实现输入 | 通过 | 8 份 LLD + 8 个 CP5 自动预检 | 用户已按推荐全部允许 |
| dev_gate 仍受 Story DAG、文件所有权和授权边界控制 | 通过 | `process/DEVELOPMENT-PLAN.yaml`；8 张 Story 卡片；8 份 LLD §14 | 用户已按推荐全部允许 |
| 安全与权限边界继续有效 | 通过 | Decision Brief；D2 / D3 / D12；forbidden operation 计数 | 用户已按推荐全部允许 |
| 不跳过 CP6 / CP7 | 通过 | Meta Flow 规则；Story acceptance criteria | 用户已按推荐全部允许 |
| DuckDB 仍为 read-only 扩展，不反向成为 source of truth | 通过 | D1 / D7 / D10；S02 / S04 LLD | 用户已按推荐全部允许 |
| 真实抓取 / 写湖执行时机已拆到后续 S09 | 通过 | S09 Story 卡片；CP5-D24；BATCH-B CP4 addendum | 用户已按推荐全部允许 |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| S01 LLD | `process/stories/CR014-S01-a-share-universe-lifecycle-contract-LLD.md` | 通过 | 用户已按推荐全部允许 |
| S02 LLD | `process/stories/CR014-S02-parquet-layout-manifest-catalog-publish-gate-LLD.md` | 通过 | 用户已按推荐全部允许 |
| S03 LLD | `process/stories/CR014-S03-p0-plan-run-normalize-validate-publish-contract-LLD.md` | 通过 | 用户已按推荐全部允许 |
| S04 LLD | `process/stories/CR014-S04-duckdb-readonly-query-audit-parity-boundary-LLD.md` | 通过 | 用户已按推荐全部允许 |
| S05 LLD | `process/stories/CR014-S05-full-history-readiness-gap-claim-boundary-LLD.md` | 通过 | 用户已按推荐全部允许 |
| S06 LLD | `process/stories/CR014-S06-incremental-refresh-replay-retention-contract-LLD.md` | 通过 | 用户已按推荐全部允许 |
| S07 LLD | `process/stories/CR014-S07-research-consumer-readonly-docs-runbook-boundary-LLD.md` | 通过 | 用户已按推荐全部允许 |
| S08 LLD | `process/stories/CR014-S08-w3-minute-tick-level2-vwap-blocked-decision-boundary-LLD.md` | 通过 | 用户已按推荐全部允许 |
| CP4 自动预检 | `process/checks/CP4-CR014-STORY-DAG-PARALLEL-SAFETY.md` | 通过 | PASS |
| S09 Story 卡片 | `process/stories/CR014-S09-windowed-real-fetch-lake-write-run.md` | 通过 | 后续 BATCH-B，不属于当前 S01..S08 LLD artifact；用户已接受拆分策略 |
| S09 CP4 addendum | `process/checks/CP4-CR014-BATCH-B-WINDOWED-REAL-FETCH-WRITE-DAG-ADDENDUM.md` | 通过 | PASS；S09 依赖 S01..S08 verified 后才可进入后续 LLD/CP5 |
| CP5 自动预检 | `process/checks/CP5-CR014-S01..S08-*-LLD-IMPLEMENTABILITY.md` | 通过 | 8 个均 PASS |
| LLD 批次 handoff | `process/handoffs/META-DEV-CR014-LLD-BATCH-A-2026-05-27.md` | 通过 | 3 个 meta-dev 分片 completed / closed |

## Agent Dispatch Evidence

| 分片 | Agent | Agent ID / Thread ID | 工具 | spawned_at | completed_at / closed_at | 状态 |
|---|---|---|---|---|---|---|
| S01-S03 | meta-dev / dev-zhu | `019e6518-2b00-7bc0-8bba-af719b7dde20` | `spawn_agent` / `close_agent` | `2026-05-27T00:23:06+08:00` | `2026-05-27T00:34:33+08:00` | completed / closed |
| S04-S06 | meta-dev / dev-you | `019e6518-767e-7f50-9946-2f8e645e75cf` | `spawn_agent` / `close_agent` | `2026-05-27T00:23:06+08:00` | `2026-05-27T00:34:33+08:00` | completed / closed |
| S07-S08 | meta-dev / dev-xu | `019e6518-bc63-74b2-82c5-9d8cae622e21` | `spawn_agent` / `close_agent` | `2026-05-27T00:23:06+08:00` | `2026-05-27T00:34:33+08:00` | completed / closed |

## 人工审查结果

- 结论：`approved`
- 审查人：user
- 审查时间：2026-05-27T07:22:46+08:00
- 原始审批文本：@meta-po CP5全部允许，按照你的建议实施。你可以组织子agent推荐项目了。能并行的时候需要并行。
- 修改意见：无
- 风险接受项：
  - CP5 只批准 CR014-FULL-HISTORY-LAKE-BATCH-A 的 S01..S08 八份 LLD 作为实现输入。
  - CP5 批准不授权 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 操作、旧报告覆盖、DuckDB 依赖引入、DuckDB 写入或 catalog current pointer 发布。
  - 真实 provider 抓取和 raw/manifest 写湖已拆分到 CR014-S09 / CR014-REAL-RUN-BATCH-B；当前 CP5 批准不授权 S09 实现或真实执行。
  - 后续每个 Story 仍必须完成 CP6 编码完成检查和 CP7 验证完成检查；CP7 失败不得标记 verified。
