---
cr_id: "CR-004"
status: "closed"
impact_level: "high"
rollback_to: "solution-design"
approval_result: "closed-cp8-approved"
created_at: "2026-05-17T12:01:04+08:00"
created_by: "meta-po"
approved_by: "user"
approved_at: "2026-05-17T12:01:04+08:00"
source: "user"
linked_issue: ""
updated_at: "2026-06-05T23:11:48+08:00"
closed_by: "user"
closed_at: "2026-06-05T23:11:48+08:00"
cp8_manual_status: "approved"
cp8_manual_review: "checkpoints/CP8-CR004-DELIVERY-READINESS.md"
cp8_auto_check: "process/checks/CP8-CR004-DELIVERY-READINESS.md"
---

# CR-004：可移植市场数据获取组件

> 2026-06-05T23:11:48+08:00 关闭记录：用户确认 CR004 相关问题应已解决并接受推荐关闭方案，CR-004 总 CR 关闭。关闭范围包含已验证的 market_data 阶段性交付、STORY-004 Data Loader first / no real fetch、STORY-018 实验十/十二只读 benchmark 接入和 Batch D / G1 聚合回归；不声明真实沪深 300 全面 available、production current truth 已补齐或任何真实 provider fetch、lake write、publish、credential read、QMT 操作已授权。

## 变更描述

用户已批准开始实施“可移植市场数据获取组件”，并要求由 `meta-po` 组织 `meta-se`、`meta-dev`、`meta-qa` 协同完成开发。

目标是在当前仓库内建设独立包 `market_data/`，后续可迁移到其他项目。组件采用 Parquet 数据湖，支持 TickFlow / AkShare / Tushare 连接器边界、限速重试熔断、raw + manifest、标准化 canonical parquet、质量校验、多源比对、只读 reader 和 CLI，并逐步接入实验十 / 十二与真实沪深 300 基准。

本 CR 优先落地最小可运行版本：

1. `market_data/` 包骨架。
2. fake connector 离线测试路径。
3. planner / runtime / storage / normalization / validation / readers / cli 最小闭环。
4. 单元测试。
5. TickFlow / AkShare / Tushare 真实 adapter 的边界和可配置入口，但默认测试路径必须 fake / offline。
6. 回测、实验和研究入口只读 parquet，不在主路径直接联网。

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `process/USE-CASES.md` | 原文档更新 | 既有 UC-01 / UC-03 / UC-06 数据准备、离线回测、真实性增强场景作为旧基线保留；本 CR 增量补充“可移植市场数据组件”和真实基准接入场景 | `## 修订记录` | approved-for-meta-se/meta-pm-sync |
| `process/REQUIREMENTS.md` | 原文档更新 | 既有 REQ-016、REQ-047 至 REQ-058 作为数据准备基线保留；本 CR 增量扩展为独立 `market_data/` 包、数据湖分层、多源连接器、reader 和实验接入需求 | `## 修订记录` | approved-for-meta-se/meta-pm-sync |
| `process/HLD.md` | 原文档更新 | 既有“分层轻量本地日频回测层 + 独立数据准备管道”保留；新增 `market_data/` 作为独立可迁移数据组件，不把回测主路径改为联网 | `## 修订记录` | pending-meta-se |
| `process/ARCHITECTURE-DECISION.md` | 原文档更新 | 保留既有数据准备与回测隔离 ADR；新增或修订关于 `market_data/` 包边界、数据湖层级、connector 默认 fake/offline 的 ADR | `## 修订记录` | pending-meta-se |
| `process/STORY-BACKLOG.md` | 原文档更新 | STORY-001..013 作为已交付基线保留；新增 CR-004 Story 或追加 Story 组，不改写旧 Story 完成状态 | `## 修订记录` | pending-meta-se |
| `process/DEVELOPMENT-PLAN.yaml` | 原文档更新 | 已完成 W0..W4 作为历史基线保留；新增 CR-004 Wave / Story DAG 与文件所有权 | 不适用 | pending-meta-se |
| `process/stories/` | 新增 | 不适用 | Story 卡片与 LLD frontmatter / 修订记录 | pending-meta-se/meta-dev |
| `market_data/` | 新增 | 不适用 | 包内模块文档或 docstring | pending-meta-dev |
| `tests/` | 原文档更新 | 既有测试保留；新增 fake connector、数据湖、reader、CLI 和离线实验接入测试 | 不适用 | pending-meta-dev/meta-qa |
| `pyproject.toml` / `uv.lock` | 原文档更新 | 保留既有 pandas / pyarrow / akshare / exploration 依赖；新增依赖必须通过 uv 管理并保持测试路径 offline | 不适用 | pending-meta-dev/meta-qa |
| `README.md` / `docs/USER-MANUAL.md` | 原文档更新 | 保留已交付本地回测和 Notebook 边界；后续追加 `market_data/` 使用、fake/offline 默认和真实 adapter 配置说明 | 文档修订记录或相关章节 | pending-after-validation |

## 旧基线映射

| 原基线对象 | 新增 / 修改对象 | 保留策略 | 映射说明 |
|---|---|---|---|
| REQ-016：数据准备与回测主路径物理隔离 | CR-004-REQ-001：`market_data/` 独立包生成标准化数据湖，实验和回测只读 parquet | 原文保留 + CR 摘录保留 | CR-004 强化隔离边界，不允许实验十 / 十二在主路径联网抓数 |
| REQ-047 至 REQ-055：限速、重试、断点续传、raw、manifest | CR-004-REQ-002：连接器 runtime 统一限速、重试、熔断、manifest | 原文保留 + 增量扩展 | 从单一 AKShare 数据准备升级为 TickFlow / AkShare / Tushare / fake connector 统一边界 |
| REQ-052 / REQ-056：raw 可派生与质量报告 | CR-004-REQ-003：raw / manifest / canonical / gold / quality / catalog 数据湖分层 | 原文保留 + 增量扩展 | canonical parquet 为下游唯一标准读取面，quality/catalog 记录质量和可发现性 |
| STORY-002 / STORY-003：现有 engine 内数据准备能力 | CR-004 Story 组：独立 `market_data/` 包 | 历史 Story 保留 | 新组件不直接重写已交付 Story；meta-se 需定义迁移和兼容边界 |
| 实验十 / 实验十二现有入口 | CR-004 接入计划 | 原文保留 | 先接入只读 reader 和 fake/offline 测试，再逐步切换真实沪深 300 基准数据 |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论（true/false） | 处理动作 |
|------|----------|-----------|--------------------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | `process/REQUIREMENTS.md`、数据准备需求、真实基准接入需求 | true | 需要增量补充 `market_data/` 包、数据湖分层、多源 connector、熔断、多源比对、reader、CLI、fake/offline 默认和实验接入验收；不得删除 REQ-016 / REQ-047..058 旧基线 |
| 场景层 | 是否改变测试矩阵覆盖范围 | `process/USE-CASES.md`、实验十 / 十二、真实沪深 300 基准 | true | 新增“数据工程组件构建者 / 本地研究者使用只读 reader 读取 canonical parquet / 多源一致性校验”场景；保留回测主路径离线场景 |
| 计划层 | 是否改变 Phase、Wave、任务依赖 | `process/HLD.md`、`process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml`、`process/stories/` | true | 回退到 `solution-design`，由 meta-se 修订 HLD 和 Story 计划；之后按 CP3 / CP4 / CP5 门控进入 LLD 与实现 |
| 安全层 | 是否引入新的高风险动作或权限要求 | TickFlow / AkShare / Tushare adapter、配置、凭据、联网边界、data lake 写入 | true | 默认测试和 CI 必须 fake/offline；真实 adapter 只实现边界和可配置入口，不提交凭据，不真实联网抓全量行情；配置必须 fail fast，避免隐式联网 |
| 交付层 | 是否需要重新生成交付物或回归子集 | `market_data/`、`tests/`、`pyproject.toml`、README、USER-MANUAL、实验入口、CP6/CP7/CP8 | true | 需要新增实现、单元测试、离线回归、文档更新和最终 CP8；验收前必须确认没有真实私有数据、凭据、缓存大文件或联网依赖进入默认测试路径 |

## 回退决策

- 影响范围：全局结构性变更，但首轮实施范围限定为最小可运行闭环。
- 回退到阶段：`solution-design`
- 需要重新确认的对象：
  - HLD 增量修订：`market_data/` 独立包边界、数据湖层级、connector 接口、offline 默认、实验接入路线。
  - Story 计划：最小闭环 Story、文件所有权、依赖 DAG、CP5 LLD 批次策略。
  - 安全边界：真实 TickFlow / AkShare / Tushare 默认不联网、不提交凭据、不抓全量行情。
  - 验证策略：fake connector 单元测试、数据湖读写闭环、质量校验、多源比对、reader 只读、CLI dry-run / offline。

## 最小可交付范围

必须包含：

1. `market_data/` 包骨架与清晰模块边界。
2. fake connector，可稳定生成小样本 raw 数据和 manifest。
3. planner / runtime：任务拆分、限速、有限重试、熔断状态和可测试时间控制。
4. storage：raw、manifest、canonical parquet 的最小写入与目录约定；预留 gold / quality / catalog。
5. normalization：fake/raw 到 canonical schema 的确定性转换。
6. validation：字段、重复、价格非负、覆盖区间、source manifest 一致性检查。
7. readers：只读读取 canonical parquet，不触发联网。
8. CLI：至少支持离线 fake 路径的 plan / fetch / normalize / validate / read 或等价最小命令。
9. 单元测试：不联网、不卡限速等待、覆盖失败重试、manifest、canonical parquet、reader 和 CLI。

暂不包含：

1. 不真实联网抓全量行情。
2. 不提交 TickFlow、Tushare token 或任何凭据。
3. 不把实验十 / 十二改成运行时自动联网。
4. 不把 `market_data/` 与 `engine/` 紧耦合为不可迁移实现。
5. 不生成真实生产行情数据入库；测试数据必须是 fake / fixture / 小样本离线文件。

## 验收口径

| 编号 | 验收项 | 通过标准 |
|---|---|---|
| CR-004-AC-001 | 包骨架 | `market_data/` 存在 planner / runtime / connectors / storage / normalization / validation / readers / cli 等最小模块或等价职责拆分 |
| CR-004-AC-002 | fake connector | 离线 fake connector 可生成 deterministic raw + manifest，测试不发起网络请求 |
| CR-004-AC-003 | raw + manifest | 每个批次记录 source、interface、params、requested_at、status、attempts、raw_path、canonical_path 或等价字段 |
| CR-004-AC-004 | canonical parquet | 可从 raw 派生标准 schema parquet；reader 只读 parquet 且不会触发 connector |
| CR-004-AC-005 | 质量校验 | 字段缺失、重复记录、异常价格或覆盖缺口能形成结构化质量结果 |
| CR-004-AC-006 | 多源比对边界 | 至少定义 fake/fake 或 fake/reference 的差异比对接口；真实 AkShare/Tushare/TickFlow 默认不参与测试联网 |
| CR-004-AC-007 | CLI | CLI 可在 offline fake 路径完成最小闭环，并有 pytest 或命令证据 |
| CR-004-AC-008 | 实验接入边界 | 实验十 / 十二接入计划明确为只读 reader，未在默认路径直接联网 |
| CR-004-AC-009 | uv 与依赖 | 依赖变更通过 `pyproject.toml` / `uv.lock` 维护；验证命令使用 `uv run` |
| CR-004-AC-010 | 质量报告 canonical source | 第一版质量报告固定输出 CSV 与 Markdown；CSV 是 canonical source，Markdown 仅为人类可读渲染；复杂列表字段以 `_json` 后缀 JSON 字符串输出 |
| CR-004-AC-011 | raw 到 dataset 精确映射 | raw 标准化只允许显式 `target_dataset` 或 exact interface 映射；禁止模糊匹配、相似度匹配、contains 匹配或自动猜测 |
| CR-004-AC-012 | fetch/dataset 双状态 | 质量报告必须同时披露 `fetch_status` 与 `dataset_status`；数据源失败但本地 parquet 合规时不得一律 fail |
| CR-004-AC-013 | coverage 与可复现性 | 每个 dataset 必须输出 coverage 字段、`denominator_mode`、显式阈值和 `run_id/generated_at/source/interface/target_dataset/input_config_hash` |
| CR-004-AC-014 | non-PIT 风险披露 | 第一版接受 non-PIT 股票池，但必须设置并披露 `is_pit_universe=false`、`universe_mode`、`pit_status` 和 survivorship bias 风险 |

## CP5 批次 A 补充确认约束

用户于 2026-05-17 对 CP5 批次 A 给出“接受，但按约束执行”的人工审查结论。约束文件为：

- `process/constraints/CR004-QUALITY-DATALOADER-CONFIRMATION-CONSTRAINTS-2026-05-17.md`

执行要求：

1. STORY-014 / STORY-015 可进入实现，但不得越过各自 LLD 文件边界；不得进入 Data Loader、回测、扫描、候选报告、真实性增强、安装脚本或 `delivery/**`。
2. STORY-016 / STORY-017 的 LLD、实现和验证必须消费该约束文件中的质量报告、coverage、fetch/dataset 双状态、non-PIT 披露、阈值配置和可复现性门禁。
3. 既有 STORY-004 Data Loader 后续如需重开实现或修订，必须遵守该约束文件中的 Data Loader 边界：只加载、校验、拒绝或放行；不自动修复数据；不放行 fail；返回质量决策原因。

## CP5 批次 D 人工确认结果

用户于 2026-05-17T15:53:20+08:00 回复“通过”，批准 `checkpoints/CP5-CR004-BATCH-D-DATALOADER-EXPERIMENT-READONLY-LLD-REVIEW.md`。

本批次批准范围：

1. STORY-003 legacy quality 与 CR-004 quality 字段对齐 addendum。
2. STORY-004 Data Loader first / no real fetch LLD 修订。
3. STORY-018 实验十/十二只读接入与真实沪深 300 基准 unavailable 路线。

后续实现仍受以下限制：

1. 不真实抓取数据，不联网补齐沪深 300，不提交凭据。
2. 不写真实 `data/**`、`reports/**`、`delivery/**`。
3. STORY-004 只允许修改 `engine/data_loader.py` 与 `engine/contracts.py` 纯常量。
4. STORY-018 只允许修改 `market_data/benchmarks.py`、两个实验脚本和专用测试。
5. `quality_status=fail` / `dataset_status=fail` 不得通过 Data Loader 放行；Markdown 质量报告仍为 human-only。

## CP6 / CP7 批次 D 验证结果

2026-05-30，CR-004 Batch D / G1 已完成 STORY-004 与 STORY-018 的实现、编码完成检查和独立验证，结论为 `PASS`。

| 对象 | CP6 | CP7 | 结论 | 说明 |
|---|---|---|---|---|
| STORY-004 Data Loader first / no real fetch | `process/checks/CP6-STORY-004-cr004-batch-d-dataloader-CODING-DONE.md` | `process/checks/CP7-STORY-004-cr004-batch-d-dataloader-VERIFICATION-DONE.md` | PASS | 默认 warn 阻断、`allow_warn` 仅放行 warn、fail / `dataset_status=fail` 不放行、quality CSV 必需字段、manifest fail fast、Markdown human-only、metadata 决策字段和 non-PIT 警示均通过。 |
| STORY-018 实验十/十二只读接入 | `process/checks/CP6-STORY-018-cr004-experiment-readonly-benchmark-CODING-DONE.md` | `process/checks/CP7-STORY-018-cr004-experiment-readonly-benchmark-VERIFICATION-DONE.md` | PASS | `--market-data-root` alias、`--benchmark-path` 本地只读、缺 benchmark 结构化 `unavailable/required_missing`、不静默 proxy 成 `hs300_index`、CR007 proxy_baseline 兼容均通过。 |
| G1 聚合回归 | 不适用 | `process/checks/CP7-CR004-BATCH-D-VERIFICATION-SUMMARY-2026-05-30.md` | PASS | 聚合命令 `48 passed in 3.28s`，py_compile、diff check、forbidden import / no network、no real side effect 均通过。 |

本批次未授权且未执行真实 provider fetch、真实 lake 写入、current pointer publish、凭据读取、真实 QMT / MiniQMT / XtQuant 操作、真实发单 / 撤单 / 账户查询、真实 broker lake 写入或 simulation run。用户已于 2026-06-05T23:11:48+08:00 接受总关闭方案，CR-004 总体关闭；关闭不代表真实沪深 300 全面 available、production current truth 已补齐或任何真实补抓 / publish 已获授权。

## 执行链路

| 顺序 | 责任角色 | 动作 | 输入 | 输出 | 门控 | 完成后下一步 |
|---|---|---|---|---|---|---|
| 1 | `meta-po` | 创建 CR 并登记 active_change | 用户请求、`STATE.md`、已交付基线 | 本 CR、handoff、阻断状态 | CR 已登记 | 等待真实子 agent 调度 |
| 2 | `meta-se` | HLD / Story 规划增量修订 | 本 CR、已确认 HLD / ADR / Story Plan、当前代码边界 | HLD/ADR/Story Plan 修订、Story 卡片、DAG | CP3 / CP4 | 交给 meta-dev 做 LLD |
| 3 | `meta-dev` | LLD 与实现 | 已确认 Story、CP5、CR、meta-se 设计 | `market_data/`、tests、必要依赖和 CP6 证据 | CP5 / CP6 | 交给 meta-qa |
| 4 | `meta-qa` | 测试策略与验证 | CR、实现结果、LLD、测试命令 | TEST-STRATEGY / VERIFICATION-REPORT、CP7 证据 | CP7 | 交回 meta-po |
| 5 | `meta-po` | 收敛文档与终验 | 下游结果、CR、检查点 | CP8 自动预检和人工审查稿 | CP8 人工确认 | 关闭 CR 或路由返工 |

## 自动终验授权

- 是否启用：false
- 授权范围：不适用
- 适用检查点：CP8
- 自动通过条件：
  - [ ] 自动预检结论为 `PASS`
  - [ ] 无 `BLOCKING`
  - [ ] 无 `REQUIRED`
  - [ ] 授权动作明确包含关闭 CR 和 / 或推进 `delivered`
- 授权原文：
- 授权时间：
- 回填要求：若生效，人工审查稿必须标注 `approval_source=user-preauthorized`

## 子 Agent 调度状态

当前 Codex 主线程已具备并使用 `spawn_agent` / `resume_agent` / `send_input` 调度能力。Codex 进程异常退出后，旧子 agent 句柄不可再等待，状态以已落盘产物、CP5 预检和此前返回结果为准；不得伪造新的完成证据。

| Agent | Handoff | 当前状态 |
|---|---|---|
| meta-po | `process/STATE.md` / CP5 Batch D | completed；曾通过 `resume_agent/send_input` 组织 Batch D 收敛 |
| meta-se | `process/handoffs/META-SE-CR004-MARKET-DATA-HLD-STORY-2026-05-17.md` | completed；已评审 Batch D 影响范围 |
| meta-dev | `process/handoffs/META-DEV-CR004-MARKET-DATA-LLD-IMPLEMENT-2026-05-17.md` | partial-file-output-then-closed；产出 STORY-003/004 修订与 STORY-018 LLD 主要内容，主线程补齐 CP5 |
| meta-qa | `process/handoffs/META-QA-CR004-MARKET-DATA-VERIFY-2026-05-17.md` | completed；已评审质量门与可验证性 |

## 处理结论

- 审批结论：`closed-cp8-approved`
- [ ] 自动批准（低风险）
- [ ] 待人工确认（中风险）
- [x] CP5 Batch D 已人工通过，允许后续按 LLD 限定范围进入实现；仍不得真实联网抓数或写真实数据/报告/交付目录
- [x] CP6 / CP7 Batch D 已通过，STORY-004 与 STORY-018 的 G1 范围 verified；CR-004 总 CR 已经用户确认关闭，仍不得把缺失真实沪深 300 口径视为已授权补抓或 publish

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| 需求 | REQ-016、REQ-047..REQ-058 | 既有数据准备、离线边界、manifest、质量报告基线 |
| Story | STORY-002、STORY-003、STORY-004 | 既有 engine 内数据准备、标准化、loader 基线 |
| 变更 | CR-003 | Notebook 探索入口；CR-004 不得把 notebook 改成联网抓数入口 |
| 目标包 | `market_data/` | 本 CR 新增的可移植市场数据组件 |
| 实验 | `experiments/run_experiment_10.py`、`experiments/run_experiment_12.py` | 后续只读 reader 接入目标 |
