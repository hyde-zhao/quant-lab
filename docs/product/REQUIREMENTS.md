---
status: draft
version: "0.3"
confirmed: false
confirmed_by: ""
confirmed_at: ""
---

# Product Requirements

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| v0.1 | 2026-07-05 | host-orchestrator | 新建 CR157 Stage 2 多因子研究框架升级需求基线草案。 |
| v0.2 | 2026-07-05 | host-orchestrator | 补充 frontmatter，并把成功标准改为可量化字段集和计数。 |
| v0.3 | 2026-07-05 | host-orchestrator | 追加 CR158 event + ML strategy adapter unified implementation 需求；保留 CR157 adapter backlog boundary 为历史基线。 |

## 状态

- 文档状态：draft
- 关联 CR：`CR-157` / `CR-158`
- 当前门禁：CR158 CP2 pending user review
- 旧基线保留：当前仓库未发现既有 `docs/product/REQUIREMENTS.md`；既有组件文档和检查证据作为输入，不被替换。

## Requirement Summary

| REQ ID | 标题 | 优先级 | 状态 | 验收要点 |
|---|---|---|---|---|
| REQ-CR157-001 | Mature admission package builder scope | P0 | draft | 能定义从 mature research package、validation report、offline preflight、observation plan 到准入包的字段与校验边界。 |
| REQ-CR157-002 | Stage 2/Stage 3 handoff hardening | P0 | draft | Handoff 必须显式区分 Stage 2 no-lake 支撑、Stage 3 真实研究输入和 Stage 4 观察候选。 |
| REQ-CR157-003 | Research evidence index traceability | P0 | draft | 每个 package 必须追溯 data release、run manifest、metric refs、lineage refs 和 typed unavailable / blocked reason。 |
| REQ-CR157-004 | Fail-closed no-runtime guard | P0 | draft | provider、lake write、catalog publish、credential、QMT、gateway、simulation、live 和 trading 计数非 0 时阻断。 |
| REQ-CR157-005 | Portfolio risk policy compatibility | P1 | draft | 准入包必须携带 top_n、max_weight、turnover、行业/风格/容量/费用/停止条件等风险策略引用。 |
| REQ-CR157-006 | Backlog strategy adapter boundary | P1 | draft | event/ML adapters 不进入 CR157 first slice；仅保留 adapter 合同兼容性和后续 CR 入口。 |
| REQ-CR157-007 | CP2-before-design gate | P0 | draft | CP2 未 approved 前不得启动 HLD、Story 拆分、LLD 或实现。 |
| REQ-CR158-001 | Unified adapter scope | P0 | draft | CR158 必须同时覆盖 event adapter 与 ML adapter，并明确共享 core 与 type-specific extension 边界。 |
| REQ-CR158-002 | Event strategy adapter contract | P0 | draft | Event adapter 必须能表达事件输入 refs、event-time alignment、signal output refs 和 blocked reasons，且不读取真实 event feed。 |
| REQ-CR158-003 | ML strategy adapter contract | P0 | draft | ML adapter 必须能表达 training snapshot refs、model artifact refs、prediction signal refs、validation refs 和 blocked reasons，且不训练真实模型或写 registry。 |
| REQ-CR158-004 | Evidence index typed extensions | P0 | draft | Event/ML adapter evidence 必须保持 refs-only，并为 event-specific 与 ML-specific refs 提供 typed extension。 |
| REQ-CR158-005 | No-runtime authorization guard | P0 | draft | CR158 不授权真实 feed、training、provider/lake/NAS/credential、runtime、trading、publish 或 registry/store/catalog write；禁用计数非 0 必须 blocked。 |
| REQ-CR158-006 | CP2/CP5 gate enforcement | P0 | draft | CP2 前不得 HLD/Story/LLD/实现；CP5 前不得实现；CP7 必须验证 no-runtime。 |
| REQ-CR158-007 | Release wording boundary | P1 | draft | CP8 release wording 必须区分 fixture/static adapter readiness 与 production/runtime/trading readiness。 |

## Functional Requirements

### REQ-CR157-001 Mature Admission Package Builder Scope

CR157 应定义 mature admission package builder 的产品范围。Builder 后续实现应只消费研究产物引用和验证证据引用，不读取真实数据湖、不触发 provider、不导入 QMT、不调用 gateway，也不发布 registry/store/catalog。

成功标准：

- 字段清单固定为 11 类：strategy id、run id、data release ref、factor model validation report ref、mature research package ref、runner offline preflight ref、observation plan ref、risk policy ref、evidence index ref、blocked reasons、authorization flags；11/11 缺一即 blocked。
- 缺失 P0 evidence、`typed_unavailable:*`、placeholder 或 runtime flags 冲突时 fail-closed。
- 输出不能声明 simulation-ready、paper-ready、live-ready 或 trading-ready。

### REQ-CR157-002 Stage 2/Stage 3 Handoff Hardening

CR157 应把现有历史命名中的 `stage3` 兼容对象解释清楚：Stage 2 输出框架支撑和 handoff contract，Stage 3 研究机生产真实研究证据，Stage 4 才是观察候选审查。

成功标准：

- Handoff 文档或 schema 必须包含输入、输出、证据、边界、下一阶段消费方式和降级策略。
- 任一真实 runtime 或交易需求必须另开 authorization gate。

### REQ-CR157-003 Research Evidence Index Traceability

准入包必须能从轻量 package 引用追溯到完整研究证据，不复制大型证据正文。

成功标准：

- Evidence index 固定包含 7 类引用：data release ref、manifest ref、metric refs、lineage refs、risk policy ref、validation report ref、runner offline preflight ref；7/7 缺一即 blocked。
- blocked / unavailable 必须结构化表达，不能通过空字符串或自然语言隐藏。

### REQ-CR157-004 Fail-Closed No-Runtime Guard

CR157 必须延续 Stage 2 no-lake/no-runtime 防线。

成功标准：

- 禁用面包括 NAS access、provider fetch、credential/env read、lake write、catalog/store/registry write、QMT/MiniQMT/xtquant、gateway、simulation、paper/live trading、broker/order/account 操作、Git remote write、publish。
- 禁用计数非 0 时阻断，并给出 machine-readable reason。

### REQ-CR158-001 Unified Adapter Scope

CR158 必须把 CR157 延后的 event strategy adapter 与 ML strategy adapter 作为一个统一 adapter Change Package 推进。统一不等于强行相同：共享 core 只承载 strategy type、input refs、output signal refs、evidence refs、blocked reasons、authorization flags 和 handoff refs；event-only 与 ML-only 字段必须通过 type-specific extension 显式表达。

成功标准：

- CP2 Decision Brief 必须列出 3 个 scope 选项：统一 event+ML、只做 event、只做 ML；推荐方案为统一 event+ML。
- CP3 HLD 必须明确 shared core 字段不少于 7 类，type-specific extension 至少区分 event 与 ML 两类。
- 任何 Story 或 schema 不得把 event-only 字段设为 ML 必填，或把 ML-only 字段设为 event 必填。

### REQ-CR158-002 Event Strategy Adapter Contract

Event adapter 应将离散事件类策略输入转化为统一 signal / evidence / handoff refs。CR158 只允许 fixture/static event refs，不允许接入真实 feed、live listener、provider 或 gateway。

成功标准：

- Event adapter contract 至少包含 6 类字段：event source ref、event time ref、event payload schema ref、alignment policy ref、signal output ref、blocked reason ref。
- 真实 event feed、live listener、provider fetch、gateway call 计数必须为 0。
- 缺少 event source ref、alignment policy ref 或 signal output ref 时必须 fail-closed。

### REQ-CR158-003 ML Strategy Adapter Contract

ML adapter 应将模型类策略的训练/验证/预测引用转化为统一 signal / evidence / handoff refs。CR158 只允许 fixture/static model artifact refs，不允许训练真实模型、调用外部模型服务或写 model registry。

成功标准：

- ML adapter contract 至少包含 7 类字段：training snapshot ref、feature set ref、label policy ref、model artifact ref、validation report ref、prediction signal ref、blocked reason ref。
- real model training、external model service、model registry write/promotion 计数必须为 0。
- 缺少 training snapshot ref、validation report ref 或 prediction signal ref 时必须 fail-closed。

### REQ-CR158-004 Evidence Index Typed Extensions

CR158 必须延续 CR157 refs-only evidence index 基线，新增 event/ML typed extension 时只能记录引用和短元数据，不复制报告正文、模型文件、event payload 全文、diff、transcript 或大型矩阵正文。

成功标准：

- Event extension 至少能引用 event source、alignment policy 和 signal output refs。
- ML extension 至少能引用 training snapshot、model artifact、validation report 和 prediction signal refs。
- Evidence index 中大型正文复制计数必须为 0。

### REQ-CR158-005 No-Runtime Authorization Guard

CR158 的任何 CP2 / CP3 / CP5 / CP6 / CP7 / CP8 approve 都不授权真实运行时或生产写入。

成功标准：

- 禁用面包括 real event feed、real model training、external model service、model registry write、provider fetch、NAS access、credential/env/session read、lake write、catalog/store/registry/prediction write、QMT/MiniQMT/xtquant/gateway、simulation/paper/live/trading/broker、external framework run、Git remote write、publish。
- CP7 evidence 必须报告禁用操作计数；每个禁用计数必须为 0。
- 任一禁用计数非 0 时，CP7 不得 PASS。

### REQ-CR158-006 CP2/CP5 Gate Enforcement

CR158 是 architecture-major product-scope CR，必须保留 CP2 / CP3 / CP5 / CP8 人工门禁。

成功标准：

- CP2 approved 前不得创建 dev-ready Story、LLD 或实现。
- CP5 approved 前不得修改 adapter source/test implementation。
- CP2 approve 只授权进入 solution-design；不授权 implementation、runtime 或 publish。

### REQ-CR158-007 Release Wording Boundary

CR158 的 release notes、verification report 和 component docs 必须明确区分 local/static/fixture adapter readiness 与 production/runtime readiness。

成功标准：

- CP8 release wording 必须包含 “not authorized” 清单，覆盖真实 feed、训练、registry、runtime、trading、publish。
- 不得出现 simulation-ready、paper-ready、live-ready、trading-ready、production-ready 或 registry-published 声明，除非后续独立授权 CR 明确批准。

## Non-Functional Requirements

| NFR ID | 维度 | 要求 | 度量 |
|---|---|---|---|
| NFR-CR157-001 | 可追溯性 | Package 不复制大证据正文，只引用 evidence index。 | P0 evidence refs 覆盖率 100%。 |
| NFR-CR157-002 | 安全性 | 禁用外部运行时和真实交易。 | 禁用计数必须为 0。 |
| NFR-CR157-003 | 可测试性 | 所有 P0 场景可用 fixture/static/no-lake 方式验证。 | P0 scenario 覆盖率 100%。 |
| NFR-CR157-004 | 可扩展性 | Adapter 合同不阻断 event/ML 后续扩展。 | `docs/product/BACKLOG.md` 必须保留 2 个 adapter follow-up：`BL-CR157-001` 和 `BL-CR157-002`。 |
| NFR-CR158-001 | 可追溯性 | Event/ML adapter evidence 只引用 refs，不复制大型正文。 | 大型正文复制计数为 0；P0 refs 覆盖率 100%。 |
| NFR-CR158-002 | 安全性 | Event/ML adapter 实现必须保持 no-runtime/no-publish。 | 禁用操作计数全部为 0。 |
| NFR-CR158-003 | 可演进性 | Shared core 与 type-specific extension 分离。 | event-only 与 ML-only 字段互不成为对方必填项。 |
| NFR-CR158-004 | 可测试性 | 所有 P0 CR158 场景可用 fixture/static 方式验证。 | P0 scenario 覆盖率 100%。 |

## Open Decisions

| 决策 ID | 类型 | 问题 | 推荐方案 | 状态 |
|---|---|---|---|---|
| DQ-CP2-CR157-FIRST-SLICE | scope | CR157 first slice 是否纳入 event/ML adapters？ | 不纳入；event/ML adapters 作为 backlog 或后续 CR。 | pending user review |
| DQ-CP2-CR158-UNIFIED-SCOPE | scope | CR158 是否把 event 与 ML adapter 合并为一个统一 adapter CR？ | 合并为一个 CR，shared core + type-specific extension。 | pending user review |
| DQ-CP2-CR158-NO-RUNTIME | security | CR158 CP2 approve 是否授权真实 feed、训练、registry、runtime、trading或 publish？ | 不授权；只允许 local/static/fixture 设计和后续验证。 | pending user review |
| DQ-CP2-CR158-GATE-SEQUENCE | implementation | CP2 approve 后是否允许直接实现？ | 不允许；CP2 后进入 CP3 HLD，CP5 批准后才实现。 | pending user review |
