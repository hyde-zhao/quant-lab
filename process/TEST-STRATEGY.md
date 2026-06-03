---
project_id: "local_backtest"
wave_scope: "STORY-001..STORY-013 / STORY-004..STORY-013 independent acceptance, F-004 regression, documentation readiness, CR-011 factor research data completion, CR-014 BATCH-A CP7 preparation, CR-015/CR-016/CR-017 controlled offline CP7 completion"
created_at: "2026-05-15"
updated_at: "2026-05-28"
target_story_range: "STORY-004..STORY-013 / CR011-S01..CR011-S08 / CR013-S01..CR013-S04 / CR014-S01..CR014-S08 / CR017-S01..CR017-S06 / CR015-S01..CR015-S07 / CR016-S01..CR016-S04,CR016-S07"
regression_scope: "STORY-001..STORY-013 / CR011-S01..CR011-S08 / CR013-S01..CR013-S04 / CR014-S01..CR014-S08 / CR017-S01..CR017-S06 / CR015-S01..CR015-S07 / CR016-S01..CR016-S04,CR016-S07; CR016-S05/S06 later-gated excluded"
owner: "meta-qa"
source_handoff:
  - "process/handoffs/META-DEV-IMPLEMENT-STORY-004-013-2026-05-15.md"
  - "process/handoffs/META-QA-VERIFY-STORY-004-013-2026-05-15.md"
  - "process/handoffs/META-QA-INDEPENDENT-ACCEPTANCE-STORY-004-013-2026-05-15.md"
  - "process/handoffs/META-QA-REGRESSION-F004-LOGGING-2026-05-16.md"
  - "process/handoffs/META-QA-CR004-MARKET-DATA-VERIFY-2026-05-17.md"
  - "process/handoffs/META-DOC-CR011-DOCUMENTATION-2026-05-24.md"
  - "process/handoffs/META-QA-CR013-BATCH-A-CP7-VERIFY-2026-05-25.md"
  - "process/handoffs/META-DOC-CR015-CR016-CR017-DOCUMENTATION-2026-05-28.md"
source_checkpoint:
  - "checkpoints/CP5-ALL-STORIES-LLD-BATCH.md"
  - "process/checks/CP7-CR016-S07-docs-user-manual-and-incident-playbooks-VERIFICATION-DONE.md"
  - "process/checks/CP7-CR016-S04-simulation-live-runbook-and-approval-gates-VERIFICATION-DONE.md"
  - "process/checks/CP7-CR017-S06-research-qmt-consumer-docs-and-migration-guide-VERIFICATION-DONE.md"
  - "process/checks/CP7-CR015-S07-docs-and-foundation-runbook-boundary-VERIFICATION-DONE.md"
---

# 测试策略

## 测试目标

本策略用于独立 meta-qa 对当前仓库状态执行总体验收、F-004 回归验证与 QA 文档收敛。范围覆盖 STORY-001 至 STORY-013 当前状态，重点验证 STORY-004 至 STORY-013 的实现、F-001 至 F-007 风险闭环、W3 `UNRESOLVED` source/interface fail-fast 门禁、Story DAG、边界约束与进入 documentation 前的过程文档一致性。

本轮只允许使用现有测试、临时目录、fixture 与 fake adapter；不得联网获取真实行情，不得生成真实生产数据，不得写入 `delivery/**`，不得生成安装脚本，不得修改 `engine/`、`strategies/`、`tests/` 业务源码。

CR-011 文档刷新阶段追加覆盖因子研究生产级数据补齐验证口径：`CR011-S01` 至 `CR011-S08` 均已 CP7 PASS，文档刷新已完成，CP8 人工终验已 approved，CR-011 已关闭。本策略只增量记录测试矩阵和验证摘要，不重新运行真实联网、真实 lake 写入、凭据读取、旧 `data/**` 操作或旧报告覆盖。

CR-015 / CR-016 / CR-017 文档收敛阶段追加覆盖 QMT foundation、staged activation runbook 和复权双视图消费边界的 CP7 完成事实：`CR017-S01` 至 `CR017-S06`、`CR015-S01` 至 `CR015-S07`、`CR016-S01` 至 `CR016-S04` 与 `CR016-S07` 均已完成受控离线 / mock / fixture / 文档范围 CP7 验证；`CR016-S05` 和 `CR016-S06` 仍为 later-gated，`implementation_allowed=false`，不进入 implemented 或 verified 分母。本策略只记录当前验证口径、later-gated 例外和真实操作禁止边界，不授权 QMT / MiniQMT / GUI、broker API、真实发单、撤单、账户查询、凭据读取、provider fetch、真实 lake 写入、broker lake 写入、publish、simulation、live_readonly、small_live、scale_up 或真实 incident 持久化。

## 测试设计方法选择

| 方法 | 适用场景 | 本项目适用性 | 应用说明 |
|------|---------|------------|---------|
| 等价分区 | Story 产物、数据集、策略类型、增强门禁、报告输出存在明确分类 | 高 | 按 STORY-004..013 分区验证 loader、portfolio、backtest、scanner、candidates、W3 增强、bias audit、RSI/MACD |
| 边界值分析 | 调仓 schedule、warm-up、参数网格、候选数量、CSV 文本前缀、W3 `UNRESOLVED` 启用边界 | 高 | 覆盖 2019-2025 schedule 边界、60 组参数网格、`<=4` 候选、公式注入前缀、未解析 source/interface |
| 状态转换测试 | 数据准备到 loader、信号到组合、扫描到候选、baseline/enhanced 审计、W3 启用路径 | 中 | 验证主链 `STORY-004 -> ... -> STORY-012` 串行依赖，`STORY-013` 从 STORY-008 后可独立接入 |
| 错误推测 | 常见缺陷包括模糊匹配、真实网络调用、真实目录污染、delivery 写入、日志契约遗漏、缓存残留 | 高 | 使用 `rg`/`find` 静态扫描、命令回归、目录边界复核和 LLD 风险对照表 |

## ISO 25010 质量特征优先级

| 质量特征 | 优先级 | 验证重点 | 对应验收维度 |
|---------|--------|---------|------------|
| 功能适合性 | P0 | STORY-004..013 是否覆盖 LLD §6/§7/§10 的主路径和关键异常路径 | 完整性、验收标准覆盖 |
| 可靠性 | P0 | `pytest`、`compileall`、W3 fail-fast、DAG 串行记录和缓存清理是否稳定 | 平台适配、可安装性 |
| 安全性 | P0 | 不联网、不写真实生产数据、不写 `delivery/**`、无危险命令、无模糊 source/interface 路由 | 安全合规 |
| 可维护性 | P1 | F-001..F-007 风险是否有实现或硬门禁证据；日志契约是否可审计 | 命名规范、Frontmatter 完整性 |
| 可移植性 | P1 | Python 3.11 + uv 下测试与语法检查可运行 | 平台适配、可安装性 |
| 易用性 | P2 | 报告、候选、审计和策略输出是否保留人工可读字段与降级说明 | 文档覆盖 |
| 兼容性 | P2 | STORY-001..003 回归不被 STORY-004..013 破坏；`STORY-010 -> STORY-011` 保持 | 回归风险 |
| 性能效率 | P3 | 使用小规模 fixture 与 fake runner，不引入真实大规模行情数据 | 验证执行效率 |

## 质量门定义

### 入口准则（Entry Criteria）

- [x] `process/VALIDATION-ENV.yaml` 存在且 `approval.confirmed=true`
- [x] `process/STORY-STATUS.md` 记录 STORY-001 至 STORY-013 均为 `verified`
- [x] STORY-004 至 STORY-013 LLD frontmatter 为 `confirmed=true`
- [x] 已读取 LLD 第 6 节接口设计、第 7 节核心流程、第 10 节测试设计、第 13 节回滚与发布策略
- [x] 已读取实现与既有验证 handoff
- [x] 本轮禁止修改业务源码、写 `delivery/**`、生成真实生产数据或安装脚本

### 出口准则（Exit Criteria）

- [x] `uv run --python 3.11 pytest -q` 已执行并记录结果
- [x] `uv run --python 3.11 python -m compileall engine strategies tests` 已执行并记录结果
- [x] 静态扫描已覆盖 `UNRESOLVED`、模糊匹配风险、真实网络调用、`delivery/**` 写入、真实数据文件和缓存残留
- [x] F-001 至 F-007 已逐项判定为已实现、硬门禁控制或存在缺口
- [x] Story DAG 已复核，`STORY-010 -> STORY-011` 仍存在
- [x] `process/VERIFICATION-REPORT.md` 已写入独立 meta-qa 总体验收结论
- [x] `process/handoffs/META-QA-INDEPENDENT-ACCEPTANCE-STORY-004-013-2026-05-15.md` 已写入本轮可审计事实
- [x] `QA-IND-REQ-001 / F-004` 已由 2026-05-16 最小回归验证关闭，状态为 `CLOSED / REGRESSION_PASS`
- [x] QA 文档收敛已复核 `STATE.md`、`STORY-STATUS.md`、`DEVELOPMENT-PLAN.yaml`、`VERIFICATION-REPORT.md` 与本策略的一致性

## 验证矩阵

| 验证主题 | 代表 Story | 方法 | 关键断言 |
|---|---|---|---|
| 离线 loader 与质量门禁 | STORY-004 | 等价分区、错误推测 | 仅读本地 parquet 与质量报告；缺质量报告 fail fast；不触发 data_prep 或网络 |
| 组合会计与 T+1 | STORY-005 | 状态转换、边界值 | 先卖后买、T+1 执行、现金缩放、幂等键、每日会计恒等式 |
| 调仓 schedule 与指标 | STORY-006 | 边界值 | warm-up 后首个信号日、执行日大于信号日、2019-2025 边界、指标输出 |
| 参数扫描与候选 | STORY-007/008 | 等价分区、错误推测 | 默认 60 组、失败行不丢失、候选 `<=4`、选择理由非空、CSV 文本防护 |
| W3 exact registry 与 fail fast | STORY-009/010/011 | 错误推测、边界值 | `UNRESOLVED` source/interface 禁止启用；未知组合 fail fast；禁止模糊匹配 |
| 偏差审计 | STORY-012 | 等价分区、错误推测 | 对象优先输入、baseline/enhanced delta、缺 candidate rank warning 降级 |
| 策略扩展 | STORY-013 | 边界值、错误推测 | RSI/MACD 默认参数、warm-up 后输出、非法参数失败、tie-breaker 稳定 |
| 边界与安全 | 全部 | 错误推测 | 不写 `delivery/**`；不生成真实数据；测试只使用 `tmp_path`、fixture、fake runner；缓存清理完成 |
| 可观测性日志 | STORY-004..013 | 错误推测 | LLD 要求最小 CLI 诊断日志；实现和测试需覆盖 start/end、warning、structured_error |
| CR-011 因子研究数据补齐 | CR011-S01..S08 | 等价分区、边界值、状态转换、错误推测 | 真实 benchmark、PIT / lifecycle、可交易性 / 涨跌停、OHLCV/VWAP、复权 / 公司行动、暴露、容量成本、factor panel audit、robust validation 均按 CP7 证据验证；旧报告不覆盖，默认安全计数为 0。 |
| CR-013 unsupported data 与 claim boundary | CR013-S01..S04 | 等价分区、边界值、状态转换、错误推测 | limited-window supported 与 2020-2024 full-history blocked 分区验证；真实 VWAP/VWAP fill/minute/tick/level2/order-match blocked/unsupported；unsupported register 9 行 excluded 不进分母；roadmap-only 不含可执行真实命令；五类 forbidden counters 均为 0。 |
| CR-014 全 A since-inception 数据湖 BATCH-A 准备 | CR014-S01..S08 | 等价分区、边界值、状态转换、错误推测 | 仅准备 CP6/CP7 口径；正式 CP7 等各 Story CP6 后执行。验证必须使用离线 fixture / `tmp_path`、静态 forbidden-op 扫描、monkeypatch sentinel、真实操作计数 0；DuckDB optional/lazy fallback；publish gate 不自动更新 current pointer；S09 不在本批验证。 |

## 当前判定口径

命令回归、W3 fail-fast、防真实数据/交付边界均按 BLOCKING 维度处理。F-004 最小 CLI 诊断日志属于 REQUIRED 维度，已在 `process/handoffs/META-QA-REGRESSION-F004-LOGGING-2026-05-16.md` 中回归通过并关闭 `QA-IND-REQ-001`；后续若相关入口新增或重构，必须继续覆盖 `event_name`、`run_id`、`module`、`story_id`、`status`、`params_summary`、`elapsed_seconds` 与错误路径 `structured_error`。

W3 `UNRESOLVED` source/interface 风险不再按当前验收阻塞处理，因为当前实现以 exact registry 与 fail-fast 硬门禁控制，且测试未伪造真实数据源。该风险保留为 ADVISORY：真实数据源启用前必须替换为已确认的 exact source/interface，并重新执行对应数据准备、normalizer、quality、loader 与约束路径回归。

## CR-013 BATCH-A CP7 验证策略增量

### 当前状态与验证边界

本节用于 CR013-S01 至 CR013-S04 的 CP7 独立验证。四张 Story 均已通过 CP5 批次人工确认和 CP6 编码完成门，当前验证只允许离线读取 Story、LLD、CP6、实现文件、测试、README / USER-MANUAL / roadmap 和 CR-013 新报告；不得 provider fetch、联网抓取真实数据、真实 lake 写入、读取或打印凭据、读取或列出旧 `data/**`、覆盖旧报告证据、生成真实 backfill/token/lake/provider 命令或修改实现代码。

### 测试设计方法选择

| 方法 | CR-013 适用性 | 应用说明 |
|------|--------------|---------|
| 等价分区 | 高 | 按窗口分区验证 `2025-02-11..2026-02-18` supported limited window 与 `2020-01-01..2024-12-31` blocked full-history；按声明类型分区验证 supported、research-only、unsupported、blocked。 |
| 边界值分析 | 高 | 验证 10 个正式 dataset 的完整集合、unsupported register 9 行完整集合、allowed claim count 为 0、excluded denominator 计数为 0、forbidden counters 为 0。 |
| 状态转换测试 | 中 | 验证 S01/S02 合同冻结后被 S03/S04 消费：gap register -> claim boundary summary -> docs/report summary -> roadmap-only release criteria。 |
| 错误推测 | 高 | 构造或扫描 limited-window 外推、derived VWAP、close proxy 误写真实 VWAP、roadmap 可执行命令、凭据/token/lake 命令、旧报告覆盖和旧 data 操作风险。 |

### ISO 25010 质量优先级

| 质量特征 | 优先级 | CR-013 验证重点 |
|---------|--------|----------------|
| 功能适合性 | P0 | 四张 Story 的验收标准均有测试或静态证据；full-history、execution/VWAP、unsupported register、roadmap 四类声明边界正确。 |
| 可靠性 | P0 | `py_compile` 和四个 CR-013 pytest 文件稳定通过；缺字段、derived VWAP、excluded denominator 等异常路径 fail closed。 |
| 安全性 | P0 | provider/lake/credential/legacy data/old report 五类 forbidden counters 均为 0；roadmap 不含真实执行命令或 token/lake 写入指令。 |
| 可维护性 | P1 | 声明边界集中体现在结构化 metadata、报告摘要、README/USER-MANUAL 和测试中，字段名沿用 LLD 合同。 |
| 兼容性 | P1 | 不放宽 CR011 execution policy；CR-012 limited-window pass 不外推；旧报告仅作为只读证据基线。 |
| 可移植性 | P1 | 所有验证命令通过 `uv run --python 3.11` 执行，不依赖真实网络、私有 lake 或凭据。 |

### CR-013 CP7 质量门

#### 入口准则

- [x] `process/VALIDATION-ENV.yaml` 存在且 `approval.confirmed=true`。
- [x] CR013-S01..S04 Story 状态为 `ready-for-verification`。
- [x] 四份 LLD frontmatter `confirmed=true`，且第 6 / 7 / 10 / 13 节可消费。
- [x] 四份 CP6 结论均为 `PASS`，且含子 agent 调度证据。
- [x] 交接文件 `process/handoffs/META-QA-CR013-BATCH-A-CP7-VERIFY-2026-05-25.md` 存在并声明本轮 forbidden boundaries。

#### 出口准则

- [x] 必跑 `py_compile` 命令退出码为 0。
- [x] 必跑四个 CR-013 pytest 文件结果为 `14 passed`。
- [x] S01 确认 limited-window pass 不外推到 2020-2024 full-history production strict。
- [x] S02 确认真实 VWAP/VWAP fill/minute/tick/level2/order-match execution 保持 blocked/unsupported。
- [x] S03 确认 unsupported register 9 行完整且 `excluded` 不计 formal pass denominator。
- [x] S04 确认 roadmap-only，不含可直接执行的 provider/lake/token/backfill 命令。
- [x] README、USER-MANUAL、roadmap 和 CR-013 报告摘要声明一致。
- [x] provider_fetches / lake_writes / credential_reads / legacy_data_reads / old_report_overwrites 均为 0。

### CR-013 必跑命令

```bash
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile engine/research_dataset.py experiments/reporting.py
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 pytest -q tests/test_cr013_full_history_gap_register.py tests/test_cr013_execution_vwap_claim_boundary.py tests/test_cr013_unsupported_register_claim_boundary.py tests/test_cr013_backfill_roadmap_boundaries.py
```

### CR-013 静态边界扫描

| 扫描主题 | 目标 | 预期 |
|---|---|---|
| 可执行命令扫描 | `docs/DATA-LAKE-FULL-HISTORY-BACKFILL-ROADMAP.md`、`reports/data_lake_readiness_2020_2024_cr013/backfill_roadmap.md` | 不包含 `uv run`、provider CLI、`--execute`、token 设置、真实 lake root 写入命令。 |
| forbidden counters | 四份 CR-013 报告摘要和 roadmap | 不出现非 0 的 provider/lake/credential/legacy data/old report counter。 |
| 结构化边界 | 四份 CR-013 报告摘要 | full-history allowed claim、真实 VWAP/VWAP fill/minute execution allowed claim、derived VWAP allowed claim、excluded denominator 均为 0；unsupported item count 为 9。 |

## 文档收敛检查策略

2026-05-16 QA 文档收敛不修改业务源码或测试源码，不重复运行完整测试，理由是同日 F-004 回归已完成定向日志测试、全量 pytest 与 compileall，且本轮只更新过程/QA 文档。文档收敛的验证重点为：

- 当前结论是否从历史 FAIL / REQUIRED 缺口正确收敛到 PASS / CLOSED / REGRESSION_PASS。
- `current_gate`、`next_action`、Story 状态、开发计划状态与 `VERIFICATION-REPORT.md` 是否一致。
- 历史失败记录是否保留为审计事实，并由后续回归 PASS 明确覆盖，避免误判为当前阻塞。
- W3 `UNRESOLVED` 是否保留为 ADVISORY，而不是被删除或误写为已真实接入数据源。
- `VALIDATION-ENV.yaml` 的历史 `story_id=STORY-001` 元数据是否作为非阻断观察项保留，避免误作当前验证范围真相源。

## CR-004 可移植市场数据组件验收准备增量

### 当前状态与边界

本节为 CR-004 的测试策略和验收准备，不构成实现验收结论，不生成 `VERIFICATION-REPORT.md` 或 `CP7-*` 检查结果。正式 CP7 只能在以下条件满足后启动：

- `meta-dev` 已完成 CR-004 实现并提供 `process/checks/CP6-...` 证据。
- CR-004 对应 Story/LLD 已完成 CP5 人工确认，且 LLD 可供 meta-qa 消费第 6、7、10、13 节。
- `market_data/`、新增测试、依赖变更和实验接入均已落地，且未提交真实私有行情、凭据、缓存大文件、`__pycache__/`、`.pyc` 或 notebook checkpoint。
- `process/VALIDATION-ENV.yaml` 仍需在正式 CP7 前刷新 `validation_scope` / `story_id` 到 CR-004；当前 `approval.confirmed=true` 可作为环境确认事实，但 `story_id=STORY-001` 仅能作为历史观察项。

当前只允许 QA 修改过程质量文档。不得修改 `market_data/**`、`engine/**`、`experiments/**`、`tests/**`、真实数据、依赖声明或锁文件。

### 测试设计方法选择

| 方法 | CR-004 适用性 | 应用说明 |
|------|--------------|---------|
| 等价分区 | 高 | 按 connector 类型划分 `fake`、真实 adapter 边界、无凭据配置、异常源；按数据湖层划分 raw、manifest、canonical、quality、catalog；按入口划分 API、reader、CLI、实验十、实验十二。 |
| 边界值分析 | 高 | 覆盖空 symbol/date、单交易日、缺字段、重复键、负价格、覆盖缺口、`max_retries=0/1/N`、限速为 0 与正数、空 manifest、只读目录和路径不存在。 |
| 状态转换测试 | 高 | 覆盖 `plan -> fetch(fake) -> raw/manifest -> normalize -> canonical -> validate -> read -> experiment` 主路径，以及 retry、partial_success、failed、circuit_open、resume/skip 的异常路径。 |
| 错误推测 | 高 | 针对隐式联网、真实 adapter 被默认调用、凭据泄露、manifest 不可追溯、reader 触发 connector、canonical schema 漂移、uv lock 不一致和 pycache 入库构造检查。 |

### ISO 25010 质量优先级

| 质量特征 | 优先级 | CR-004 验证重点 |
|---------|--------|----------------|
| 功能适合性 | P0 | fake/offline 最小闭环、raw/manifest/canonical/quality/read/CLI/API 均可被自动化验证。 |
| 可靠性 | P0 | 默认路径无真实网络，限速/重试/熔断可用 fake 时钟或 monkeypatch 稳定验证，不造成长时间等待。 |
| 安全性 | P0 | 不提交凭据，不读取环境 token 作为默认行为，不把真实行情或缓存入库，静态扫描无高风险命令和隐式网络默认路径。 |
| 可维护性 | P1 | manifest、canonical schema、quality result、多源比对结果均有结构化字段和可追溯 run/batch 标识。 |
| 可移植性 | P1 | `market_data/` 独立于 `engine/` 可导入；依赖由 `pyproject.toml` / `uv.lock` 管理；命令通过 `uv run --python 3.11` 执行。 |
| 兼容性 | P1 | 既有 `engine.data_loader`、实验十、实验十二、CR-002 图表、CR-003 Notebook 边界不回退；接入只读 reader 时不改成联网主路径。 |
| 易用性 | P2 | CLI smoke 覆盖 plan/fetch/normalize/validate/read 或等价最小命令；错误信息能定位数据集、字段、批次和路径。 |
| 性能效率 | P3 | 测试使用小样本 fixture，不抓取全量行情，不引入慢速真实等待。 |

### CR-004 质量门

#### 入口准则（正式 CP7 前）

- [ ] CR-004 Story 状态为 `ready-for-verification`。
- [ ] CP6 编码完成门结论为 `PASS` 或 `WAIVED`，且含真实子 agent 调度证据。
- [ ] CR-004 LLD frontmatter `confirmed=true`，并具备接口设计、核心流程、测试设计、回滚与发布策略。
- [ ] `process/VALIDATION-ENV.yaml` 已刷新 CR-004 验证对象，且 `approval.confirmed=true`。
- [ ] `market_data/` 文件清单存在，且 `pyproject.toml` / `uv.lock` 若有变更则由 `uv` 维护。
- [ ] 默认测试路径无需真实 TickFlow / AkShare / Tushare 网络和凭据。

#### 出口准则（正式 CP7）

- [ ] CR-004 验收项 CR-004-AC-001 至 CR-004-AC-009 均有验证记录。
- [ ] fake/offline 闭环自动化测试通过，且网络阻断场景下仍通过。
- [ ] manifest 字段、canonical parquet schema、quality gate、多源比对接口均有正向和负向测试。
- [ ] reader 只读 canonical parquet，不触发 connector、fetch、normalize 或网络。
- [ ] CLI smoke 通过，失败路径无 Python traceback，错误文本可定位原因。
- [ ] `uv lock --check`、聚焦 pytest、全量 pytest、静态边界扫描全部通过。
- [ ] 实验十 / 十二若接入 `market_data`，仅调用 reader 或显式传入离线 parquet，不直接调用 connector。
- [ ] 仓库无新增凭据、真实行情大文件、`__pycache__/`、`.pyc`、`.ipynb_checkpoints/`。

### CR-004 测试矩阵

| 验证主题 | 方法 | 阻断等级 | 设计断言 | 建议证据 |
|---|---|---|---|---|
| 包骨架与可移植边界 | 等价分区 | BLOCKING | `market_data/` 至少包含 planner/runtime/connectors/storage/normalization/validation/readers/cli 或等价职责；包导入不依赖 `engine/` 运行态。 | `uv run --python 3.11 python -c "import market_data"`；文件清单审查。 |
| fake/offline 默认 | 错误推测 | BLOCKING | CLI/API 默认 source 为 fake/offline；不传真实 provider、token 或联网参数时不发起网络。 | pytest monkeypatch `socket.socket/connect` 或 provider spy；CLI smoke。 |
| 无真实网络 | 错误推测 | BLOCKING | 全量测试在禁用 socket 后通过；真实 TickFlow/AkShare/Tushare adapter 只验证边界和配置错误，不在默认测试调用。 | `pytest` 网络阻断 fixture；`rg` 检查默认入口。 |
| manifest 可追溯 | 状态转换 | BLOCKING | 每个 batch 记录 `run_id/batch_id/source/interface/params/requested_at/status/attempts/raw_path/canonical_path/success_items/failed_items/error/backoff` 或 LLD 等价字段。 | manifest JSON/JSONL/parquet schema 测试；失败重试测试。 |
| raw 到 canonical 派生 | 状态转换 | BLOCKING | fake raw 可确定性派生 canonical parquet；删除 canonical 后可由 raw + manifest 重建等价 schema。 | tmp_path 端到端测试。 |
| canonical parquet schema | 边界值 | BLOCKING | `prices` 至少覆盖 `trade_date/symbol/close`，并保留 `available_at/adjustment_policy` 可审计字段；如覆盖 `index_members/trade_calendar`，需满足既有 REQ 最小 schema。 | schema 校验正负例：缺字段、类型不可转换、空交易日。 |
| quality gate | 边界值 | BLOCKING | 字段缺失、重复 `symbol/trade_date`、负价或零价异常、覆盖区间缺口、manifest 与 canonical 不一致能产生结构化 `pass/warn/fail`。 | quality result 对象/文件断言；CLI validate 负例。 |
| 多源比对接口 | 等价分区 | REQUIRED | 至少支持 fake/fake 或 fake/reference 比对，不依赖真实网络；差异输出包含 dataset/key/field/source_a/source_b/delta/severity。 | 单元测试和 CLI/API smoke。 |
| reader 只读 | 错误推测 | BLOCKING | reader 只读取 canonical parquet 和必要 catalog/quality，不调用 connector、fetch、normalize、storage write。 | monkeypatch connector 抛错仍可 read；目标目录 mtime 不变。 |
| CLI smoke | 状态转换 | REQUIRED | 离线 fake 路径可完成 plan/fetch/normalize/validate/read 或等价最小闭环；输出路径均在 tmp_path。 | `uv run --python 3.11 python -m market_data.cli ...` 系列命令。 |
| uv 依赖一致性 | 错误推测 | REQUIRED | 依赖只通过 `pyproject.toml` / `uv.lock` 管理；锁文件一致。 | `uv lock --check`；必要时 `uv sync --python 3.11 --all-groups`。 |
| 实验十/十二只读接入 | 错误推测 | BLOCKING | 若改动实验入口，只允许读取 reader/canonical parquet；不得在运行时 fetch 或调用真实 adapter。 | `rg` 静态扫描；禁网下实验 smoke 或单测。 |
| 凭据/缓存/pycache 禁入库 | 错误推测 | BLOCKING | 无 token/key/cookie/session；无真实行情大文件；无 `__pycache__/`、`.pyc`、`.ipynb_checkpoints/` 新增。 | `rg` 凭据模式；`find` 缓存扫描；`git status --short` 审查。 |

### 正式 CP7 建议命令

正式验证时按以下顺序执行，所有命令都必须在仓库根目录运行：

```bash
uv lock --check
uv run --python 3.11 pytest -q tests/test_market_data*.py
uv run --python 3.11 pytest -q
uv run --python 3.11 python -m compileall market_data engine experiments tests
uv run --python 3.11 python -m market_data.cli --help
```

若 CLI 采用子命令形式，补充离线 smoke：

```bash
uv run --python 3.11 python -m market_data.cli plan --source fake --offline --output-dir <tmp>
uv run --python 3.11 python -m market_data.cli fetch --source fake --offline --output-dir <tmp>
uv run --python 3.11 python -m market_data.cli normalize --input-dir <tmp> --output-dir <tmp>
uv run --python 3.11 python -m market_data.cli validate --data-dir <tmp>
uv run --python 3.11 python -m market_data.cli read --data-dir <tmp>
```

静态边界扫描建议：

```bash
rg -n "TickFlow|Tushare|akshare|requests|urllib|socket|http|token|secret|password|cookie|session" market_data experiments tests pyproject.toml
find . -path "./.venv" -prune -o -path "./.git" -prune -o \( -type d -name "__pycache__" -o -name "*.pyc" -o -path "*/.ipynb_checkpoints/*" \) -print
git status --short
```

若 CR-004 接入实验十/十二，增加只读 smoke 或定向测试：

```bash
uv run --python 3.11 pytest -q tests/test_market_data*.py -k "experiment_10 or experiment_12 or reader"
```

### 当前准备态风险

| 风险 | 等级 | 当前事实 | CP7 处理要求 |
|---|---|---|---|
| 实现尚未落地 | BLOCKING | 当前未发现 `market_data/` 文件清单，且无 CR-004 CP6。 | 不得生成 CP7 PASS；等待 meta-dev 实施与 CP6。 |
| 验证环境元数据滞后 | REQUIRED | `VALIDATION-ENV.yaml` 仍记录 `story_id=STORY-001`，但 `approval.confirmed=true`。 | 正式 CP7 前刷新验证对象，避免审计歧义。 |
| 缓存文件存在 | BLOCKING | 当前 `engine/`、`experiments/`、`tests/`、`strategies/` 下已有 `__pycache__/` / `.pyc` 命中，且 `notebooks/.ipynb_checkpoints/` 已命中。 | CP7 前必须清理或确认未进入提交范围；最终 `find` 扫描无输出。 |
| 真实 adapter 默认联网 | BLOCKING | CR-004 计划引入 TickFlow/AkShare/Tushare 边界。 | 默认路径必须 fake/offline；真实 provider 必须显式配置且测试不调用真实网络。 |
| 实验十/十二接入回退 | BLOCKING | 当前实验十/十二通过 `engine.data_loader` 读取本地 parquet。 | 若改为 `market_data` reader，必须保持只读，不得在实验运行中 fetch。 |
| canonical schema 漂移 | BLOCKING | 既有需求已有最小 parquet schema，CR-004 需另行固化 canonical schema。 | LLD 与实现必须声明 schema_version 和字段契约；测试覆盖缺字段与类型错误。 |

## CR-005 Tushare 5000 + Backtrader 质量策略增量

### 当前状态与边界

本节用于 CR-005 在 CP3/CP4 人工确认前追加 PIT、复权和 Backtrader 数据边界质量口径，并作为进入 CP5 LLD 批次前的 QA 输入。本节不是 CP7 验证报告，不授权实现真实 Tushare 调用、不新增依赖、不生成真实行情数据。

当前事实：

- `process/changes/CR-005-TUSHARE-5000-DATA-LAYER-REMEDIATION-2026-05-17.md` 已将 Tushare 5000 数据层整改与 Backtrader optional backend 纳入同一 CR。
- `process/HLD.md`、`process/ARCHITECTURE-DECISION.md`、`process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml` 已包含 CR-005 增量，CP3/CP4 自动预检为 PASS，但仍待用户人工确认；确认前不得进入 CP5 或实现。
- `process/stories/CR005-S02-tushare-dataset-schema-normalization.md`、`process/stories/CR005-S03-multidataset-quality-catalog-readers.md`、`process/stories/CR005-S06-backtrader-optional-backend.md` 已存在且状态为 `draft`；三者仍需在 LLD 中消费本节质量门。
- 当前 `pyproject.toml` 未包含 `tushare` 或 `backtrader` 依赖；默认依赖路径仍未把 Backtrader 变成必装项。
- 当前 `market_data/connectors/tushare.py` 仍为 fail-fast 边界；`market_data/source_registry.py` 只登记 Tushare `prices.daily`，尚未覆盖 CR-005 目标 dataset。
- 当前 `market_data/validation.py` 已输出 `fetch_status` 与 `dataset_status`，但 `market_data/readers.py` 暂未强制消费 quality gate；Backtrader 接入前必须补齐只读质量门。

### CP5 前新增质量口径

| 口径 | 阻断等级 | CP5 前必须固化的设计断言 | 主要消费 Story |
|---|---|---|---|
| PIT as-of join | BLOCKING | 非行情数据必须在 Pandas 数据层按 `available_date` / `effective_date` / `available_at` 做 as-of join；任何 `available_at > decision_date` 或 `effective_date > decision_date` 的记录不得进入当日输入、factor panel、score、股票池或 Backtrader feed。 | CR005-S02、CR005-S03、CR005-S06 |
| 复权数据层生成 | BLOCKING | 数据层必须保存 `adj_factor` 与 adjusted price；同一次回测不得混用 `qfq` / `hfq` / `none`；收益、技术指标、forward return 必须使用统一 adjusted price；缺 `adj_factor` 或 `adjustment_policy` 必须 fail fast 或返回 structured unavailable。 | CR005-S02、CR005-S03、CR005-S06 |
| Pandas 数据层先清洗 | BLOCKING | PIT 对齐、复权价格生成、quality gate 和 factor/score 生成必须先在 Pandas 数据层完成；交给回测层的是干净 factor panel / score / feed。 | CR005-S02、CR005-S03 |
| Backtrader 职责边界 | BLOCKING | Backtrader 只负责调仓、成交、成本、仓位、净值和风险分析；输入只能是经过 PIT、复权和 quality gate 的干净 factor panel / score / feed。 | CR005-S06 |
| Backtrader 禁止绕过数据层 | BLOCKING | Backtrader adapter 不得直接读取 Tushare、connector、runtime、storage、raw parquet 或未经 quality policy 放行的 canonical/gold；不得绕过 reader quality policy。 | CR005-S03、CR005-S06 |

### 测试设计方法选择

| 方法 | CR-005 适用性 | 应用说明 |
|------|--------------|---------|
| 等价分区 | 高 | 按 Tushare 启用状态划分 disabled、enabled-no-token、enabled-token-no-allowlist、enabled-allowlisted-dry-run、enabled-real-fetch；按数据消费状态划分 PIT pass、PIT future leak、复权完整、复权缺失、复权混用；按 Backtrader 状态划分未安装、已安装但未启用、显式启用。 |
| 边界值分析 | 高 | 覆盖空 token、空 allowlist、单日/跨年数据、5000 积分配额下分页批次、`available_at == decision_date`、`available_at > decision_date`、`effective_date == decision_date`、`effective_date > decision_date`、空 canonical、缺 quality、缺 `adj_factor`、缺 `adjustment_policy`、`dataset_status=fail`、`fetch_status=failed` 但本地 dataset 合规。 |
| 状态转换测试 | 高 | 覆盖 `plan -> fetch(Tushare) -> raw/manifest -> normalize -> adjusted price -> validate -> catalog -> read -> PIT factor panel/score -> lightweight/backtrader backtest`，以及 fetch failed、partial_success、resume、quality fail、PIT future leak、adjustment unavailable、backend_unavailable 路径。 |
| 错误推测 | 高 | 重点构造 token 泄漏、默认联网、as-of join 误用报告期/生效日、复权口径混用、Backtrader 直接导入 connector、Backtrader 直接读 raw parquet、reader 绕过 quality gate、测试因 optional 依赖缺失失败、真实数据或缓存入库。 |

### ISO 25010 质量优先级

| 质量特征 | 优先级 | CR-005 验证重点 |
|---------|--------|----------------|
| 功能适合性 | P0 | Tushare 真实 connector 只写入本地数据湖；Pandas 数据层完成 PIT as-of join、复权价格和干净 factor panel/score；Backtrader optional backend 只消费本地干净输入。 |
| 可靠性 | P0 | 默认 `uv run --python 3.11 pytest -q` 无 token、无网络、无 Backtrader optional 依赖仍通过；PIT future leak、复权缺失、quality fail 均稳定阻断。 |
| 安全性 | P0 | token 只来自环境变量引用；不得进入 manifest、quality、catalog、日志、错误消息、测试 fixture 或文档示例值；Backtrader 不读取凭据、不联网。 |
| 可维护性 | P1 | `fetch_status`、`dataset_status`、`quality_status`、PIT 字段、`adj_factor`、`adjustment_policy`、factor panel lineage 和依赖组策略可追溯。 |
| 可移植性 | P1 | `tushare`、`backtrader` 均不得进入默认必装依赖；通过 uv 非默认依赖组显式启用。 |
| 兼容性 | P1 | 既有轻量回测主路径继续默认可用；Backtrader 不替代 `engine/backtest.py`，且不重做 Pandas 数据层职责。 |
| 易用性 | P2 | 未安装 Backtrader 时返回结构化 `backend_unavailable`；PIT/复权不可用时返回可定位字段、日期、dataset 和 policy 的结构化错误。 |
| 性能效率 | P3 | 默认测试使用 fixture/fake 数据；真实抓取测试仅 dry-run 或显式人工环境，不进入默认 CI。 |

### CR-005 质量门

#### CP5 前入口准则

- [ ] CP3/CP4 人工确认已通过；确认前不得进入 CR-005 CP5 LLD 批次。
- [ ] CR-005 Story LLD 已逐项消费本节 PIT、复权、Pandas 数据层与 Backtrader 边界口径。
- [ ] CR005-S02 LLD 已声明 `available_date` / `effective_date` / `available_at` 字段语义、as-of join 规则、`adj_factor` 与 adjusted price 字段/生成策略。
- [ ] CR005-S03 LLD 已声明 reader quality policy、PIT/复权不可用时的 fail fast 或 structured unavailable 行为。
- [ ] CR005-S06 LLD 已声明 Backtrader 只消费干净 factor panel / score / feed，不直接读取 Tushare、connector、raw parquet 或绕过 quality policy。
- [ ] 默认测试命令仍为 `uv run --python 3.11 pytest -q`，不要求 `TUSHARE_TOKEN`、真实网络或 Backtrader optional 依赖。

#### CP5 前出口准则

- [ ] Tushare token 策略只允许环境变量名引用；任何产物不得出现 token 值、示例 token、fixture token 或日志 token。
- [ ] `fetch_status` 与 `dataset_status` 的决策表已固化：远端失败不得直接阻断本地 canonical/gold 合规的只读回测，`dataset_status=fail` 必须阻断。
- [ ] PIT 决策表已固化：`available_at/effective_date > decision_date` 的非行情数据不得出现在当日输入；缺必要 PIT 字段必须 fail fast 或 structured unavailable。
- [ ] 复权决策表已固化：同一次回测只允许一种 `adjustment_policy`；收益、技术指标、forward return 使用统一 adjusted price；缺 `adj_factor` 或 `adjustment_policy` 必须 fail fast 或 structured unavailable。
- [ ] Backtrader adapter 的 import 和输入边界已固化：不得导入 `market_data.connectors`、不得读取 `TUSHARE_TOKEN`、不得联网、不得读取 raw parquet、不得绕过 quality gate；仅消费干净 factor panel / score / feed。
- [ ] optional 依赖策略已固化：`backtrader` 与真实 Tushare provider 依赖仅进入非默认 uv dependency group 或等价 optional extra；默认 pytest 不安装、不导入。
- [ ] 最小回归测试清单已写入对应 LLD，且覆盖离线负向测试、凭据泄漏扫描、PIT future leak、复权缺失/混用、依赖组策略和 Backtrader 降级路径。

### CR-005 测试矩阵

| 验证主题 | 方法 | 阻断等级 | 设计断言 | 建议证据 |
|---|---|---|---|---|
| 默认离线 pytest | 错误推测 | BLOCKING | `TUSHARE_TOKEN` 为空、禁用 socket、未安装 Backtrader optional 依赖时全量 pytest 通过。 | `TUSHARE_TOKEN= uv run --python 3.11 pytest -q`；网络阻断 fixture。 |
| Tushare import 安全 | 错误推测 | BLOCKING | import `market_data.connectors.tushare` 不联网、不读取 token、不导入真实 provider。 | monkeypatch `os.environ` 与 socket；静态 import 扫描。 |
| Tushare 启用门禁 | 等价分区 | BLOCKING | disabled、missing token、interface not allowlisted 均结构化 fail-fast；真实 fetch 只在显式启用命令中发生。 | adapter 单测、CLI 负向用例、错误 JSON 不含 token。 |
| 凭据泄漏扫描 | 错误推测 | BLOCKING | token 值不得出现在 manifest、quality、catalog、stdout/stderr、日志、错误消息、测试 fixture、文档示例。 | `rg` 凭据模式；manifest/quality/catalog 内容断言；日志捕获断言。 |
| 多 dataset schema | 等价分区 | BLOCKING | `prices`、`hs300_index`、`index_weights`、`trade_calendar`、`adj_factor` 至少有 exact schema 与接口映射；PIT 字段和复权字段语义明确。 | source registry/schema registry 测试；缺字段负例。 |
| PIT as-of join | 边界值、状态转换 | BLOCKING | 非行情数据按 `available_date` / `effective_date` / `available_at` as-of join；`available_at/effective_date > decision_date` 记录不得进入当日输入。 | 构造 T-1、T、T+1 三类 fixture；断言当日 factor panel/score/feed 不含未来记录。 |
| adjusted price 生成 | 边界值 | BLOCKING | 数据层保存 `adj_factor` 与 adjusted price；缺 `adj_factor` 或 `adjustment_policy` fail fast 或 structured unavailable。 | 缺字段、空值、不可转换、复权口径缺失负例。 |
| 复权口径一致性 | 错误推测 | BLOCKING | 同一次回测不得混用 `qfq` / `hfq` / `none`；收益、技术指标、forward return 使用统一 adjusted price。 | 混合 policy fixture 阻断；指标/收益/forward return 输入列 lineage 断言。 |
| fetch/dataset 双状态 | 状态转换 | BLOCKING | `fetch_status` 反映远端获取事实，`dataset_status` 反映本地 dataset 合规性；二者不可互相覆盖。 | fetch failed + 本地 pass 用例；fetch success + dataset fail 用例。 |
| reader quality gate | 错误推测 | BLOCKING | reader/Backtrader 读取 canonical/gold 前必须验证 quality/catalog；不得静默忽略 `quality_policy`。 | `dataset_status=fail` 阻断、`warn` 披露、缺 quality fail-fast。 |
| Pandas factor panel 边界 | 状态转换 | BLOCKING | PIT 对齐、复权价格生成、quality gate 和 factor/score 生成均在 Pandas 数据层完成，回测层不重新对齐原始数据。 | factor panel lineage 字段；Backtrader 输入 fixture 只含干净 feed/score。 |
| Backtrader 未安装降级 | 等价分区 | BLOCKING | 默认轻量回测继续可用；显式选择 Backtrader 但未安装时返回 `backend_unavailable` 或等价结构化状态。 | 不安装 optional group 的单测；错误类型断言。 |
| Backtrader 输入边界 | 错误推测 | BLOCKING | Backtrader 只消费干净 factor panel / score / feed；不得直接读 Tushare、connector、runtime、storage、raw parquet 或未通过 quality policy 的 canonical/gold。 | 静态 import 扫描；monkeypatch connector/raw path 访问为失败；adapter 输入类型断言。 |
| Backtrader 已安装路径 | 状态转换 | REQUIRED | 启用后只负责调仓、成交、成本、仓位、净值和风险分析，输出与轻量回测对照报告。 | `uv run --group backtest ...` 定向测试；socket/token spy；对照报告断言。 |
| 依赖组策略 | 错误推测 | REQUIRED | `backtrader` 与真实 Tushare provider 不进入默认 `[project].dependencies`；默认 pytest 不同步 optional group。 | `pyproject.toml` 审查；`uv lock --check`；默认/带 group 两套命令。 |

### CP5 前最小测试清单

默认离线回归：

```bash
TUSHARE_TOKEN= uv run --python 3.11 pytest -q
uv run --python 3.11 pytest -q tests/test_market_data*.py tests/test_story_004_013.py
```

PIT / 复权 / quality 负向测试：

```bash
uv run --python 3.11 pytest -q tests/test_market_data*.py -k "asof or available_at or effective_date or pit or adj_factor or adjustment_policy or adjusted or quality"
uv run --python 3.11 pytest -q tests/test_story_004_013.py -k "data_loader or quality or available_at or adjustment"
```

Backtrader 边界测试：

```bash
uv run --python 3.11 pytest -q tests/test_backtrader_optional_backend.py -k "unavailable or quality or no_connector or no_raw or clean_feed"
uv run --python 3.11 --group backtest pytest -q tests/test_backtrader_optional_backend.py
```

凭据泄漏、网络与边界扫描：

```bash
rg -n "TUSHARE_TOKEN|token|secret|password|cookie|session|api[_-]?key" market_data engine tests docs README.md pyproject.toml
rg -n "requests|urllib|httpx|socket|tushare|backtrader|market_data.connectors|market_data.runtime|market_data.storage|raw" engine market_data tests pyproject.toml
find . -path "./.venv" -prune -o -path "./.git" -prune -o \( -type d -name "__pycache__" -o -name "*.pyc" -o -path "*/.ipynb_checkpoints/*" \) -print
```

依赖组策略建议：

- 默认依赖不得加入 `backtrader` 或真实 Tushare provider。
- 若需要真实 Tushare provider，使用非默认 dependency group，如 `real-data` 或 `tushare`。
- 若需要 Backtrader，使用非默认 dependency group，如 `backtest`。
- 默认 CI / 默认本地验证只运行 `uv run --python 3.11 pytest -q`。
- optional backend 验证单独运行，例如 `uv run --python 3.11 --group backtest pytest -q tests/test_backtrader_optional_backend.py`。

### CP5 前阻断项

| 阻断项 | 等级 | 当前事实 | CP5 处理要求 |
|---|---|---|---|
| CP3/CP4 人工确认未完成 | BLOCKING | CP3/CP4 自动预检已 PASS，人工审查稿待用户确认。 | 人工确认通过前不得进入 CR-005 CP5 LLD 批次或实现。 |
| PIT as-of join 未进入 LLD | BLOCKING | CR005-S02/S03/S06 Story 已有 `available_at` 和 quality gate 口径，但未显式要求非行情数据按 `available_date` / `effective_date` / `available_at` as-of join。 | CP5 前把 PIT join 规则、future leak 负例和 structured unavailable 写入相关 LLD。 |
| 复权生成与消费口径未进入 LLD | BLOCKING | Story 已要求复权冲突失败，但未显式要求保存 `adj_factor`、生成 adjusted price，并让收益、技术指标、forward return 统一使用 adjusted price。 | CP5 前把 `adj_factor`、adjusted price、`adjustment_policy` 决策表和混用阻断测试写入 CR005-S02/S03/S06 LLD。 |
| Backtrader 输入边界需硬化 | BLOCKING | CR005-S06 已要求只读 canonical/gold + quality gate，但未显式限定输入必须是 Pandas 数据层生成的干净 factor panel / score / feed。 | CP5 前明确 Backtrader 不直接读 Tushare、connector、raw parquet，不做 PIT/复权生成，只处理调仓、成交、成本、仓位、净值和风险分析。 |
| reader 暂未强制质量门 | BLOCKING | `market_data.readers.read_canonical` 当前忽略 `quality_policy`，catalog 缺失也允许读取。 | Backtrader 接入前必须补齐 quality/catalog gate 或设计受控 adapter，防止绕过质量门。 |
| Tushare dataset 覆盖不足 | REQUIRED | 当前 registry 仅登记 Tushare `prices.daily`。 | CP5 前明确 `hs300_index`、`index_weights`、`trade_calendar`、`adj_factor`、复权价格等 exact interface 与 target_dataset。 |
| 测试中存在 token-like 哨兵字面量 | REQUIRED | 现有脱敏测试含 `plain-token`、`secret-value` 字符串，未发现真实凭据。 | CR-005 凭据扫描需区分历史脱敏哨兵；新增 CR-005 测试不得引入 token 示例值。 |

## CR-005 Batch A CP7 验证策略增量

### 当前状态与边界

本节记录 2026-05-17 对 `CR005-S01` / `CR005-S02` Batch A 的 CP7 验证策略执行口径。验证只覆盖 Tushare 写湖边界、`hs300_index` job spec、多 dataset schema、PIT 字段与复权 normalization；不进入 S03/S04/S05/S06，不执行真实联网，不真实写 lake，不实现代码。

### 测试设计方法选择

| 方法 | Batch A 适用性 | 执行说明 |
|---|---|---|
| 等价分区 | 高 | 按 lake root 缺失/环境变量、Tushare disabled/no-token/allowlist、P0 dataset、exact interface、prices/adj_factor 输入形态分区。 |
| 边界值分析 | 高 | 覆盖空 lake root、dry-run true、非法日期格式、非法日历日期、index code mismatch、checksum mismatch、缺 PIT 字段。 |
| 状态转换测试 | 中 | 覆盖 `hs300-backfill` missing lake root -> structured error、dry-run -> plan/no-write、manifest success -> normalization、lineage mismatch -> fail fast。 |
| 错误推测 | 高 | 构造 token 泄漏、provider 默认导入、unknown/fuzzy interface、非法日期、separate `prices.adj_factor` 未 join、禁区依赖、真实数据误写。 |

### 质量门定义

#### 入口准则

- [x] `process/VALIDATION-ENV.yaml` 存在且 `approval.confirmed=true`
- [x] CP7 验证开始时 `CR005-S01` / `CR005-S02` Story 状态为 `ready-for-verification`；验证完成后 S01 更新为 `verified`，S02 因 BLOCKING 失败退回 `in-development`
- [x] 两个 Story 的 CP6 均为 `PASS`
- [x] 两个 LLD frontmatter 均 `confirmed=true` 且 `implementation_allowed=true`
- [x] 已读取 QA handoff、DEV handoff、Story、LLD、CP6 与相关实现/测试文件

#### 出口准则

- [x] 推荐离线 pytest 命令已执行
- [x] `hs300-backfill` missing lake root 与 dry-run no-write 已验证
- [x] token/no-network/no-real-data/禁区静态扫描已执行
- [x] `hs300_index` exact mapping、index code mismatch、lineage checksum 负向已验证
- [x] PIT 字段与 unknown/fuzzy interface 已验证
- [x] `prices` adjusted price 与 `adjustment_policy_conflict` 已验证
- [x] 已发现并记录 S02 BLOCKING 缺口；CP7 结论不放行 Batch A 整体 verified

### Batch A CP7 阻断项

| ID | 等级 | 当前事实 | 处理要求 |
|---|---|---|---|
| CR005-S02-BLOCKER-001 | BLOCKING | `trade_date=20261340` 被 normalization 接受，没有 fail fast。 | 使用真实日期解析校验 `%Y%m%d` / ISO 输入；补非法日历日期回归。 |
| CR005-S02-BLOCKER-002 | BLOCKING | `prices.daily` 与 separate `prices.adj_factor` manifest 不能 join 生成 adjusted OHLC，当前仅接受 prices 行内 `adj_factor`。 | 支持 exact `prices.adj_factor` records 与 `prices.daily` 按 key join；补缺因子、duplicate key、policy 冲突回归。 |

## CR-010 剩余批次 CP7 验证策略增量

### 当前状态与边界

本节记录 2026-05-22 对 CR-010 剩余能力 `OPS-BATCH-D`、`DL-BATCH-B`、`QF-BATCH-C` 的独立 meta-qa 验证口径，用于补齐上一轮 QA 子进程 shutdown 导致的正式 CP7 evidence gap。本轮只验证已落地代码、测试和文档，不触发真实备份、真实恢复、真实删除、真实 Tushare 新抓取，不读取或打印 `.env`、token、NAS 凭据或真实敏感路径，不读取、列出、迁移、复制、比对或删除旧 `data/**`。

### 测试设计方法选择

| 方法 | 适用性 | 执行说明 |
|---|---|---|
| 等价分区 | 高 | 按 backup / restore / retention CLI、W3 dataset、production_strict / exploratory、consumer 类型划分分区。 |
| 边界值分析 | 高 | 覆盖 dry-run 与 `--execute` 边界、checksum same / mismatch、`restore-root == lake-root`、W3 缺 `available_at`、缺 exact source/interface。 |
| 状态转换测试 | 中 | 覆盖 backup plan -> run -> verify -> report、restore plan -> run -> drill、catalog coverage -> production readiness、research dataset -> experiments realism matrix。 |
| 错误推测 | 高 | 构造敏感路径泄漏、默认联网、自动 backfill、consumer 导入 connector/runtime/storage、裸命令入口、旧 `data/**` 被当 current truth。 |

### 质量门定义

#### 入口准则

- [x] 用户明确要求重新拉起 meta-qa 独立验证并补齐 CP7 evidence gap。
- [x] `process/VALIDATION-ENV.yaml` 存在且 `approval.confirmed=true`；其中历史 `story_id=STORY-001` 作为非阻断观察项，不作为本轮 CR-010 范围真相源。
- [x] 上一轮两个 meta-qa 线程状态为 shutdown / previous_status=running，不能作为 QA PASS 或 CP7 PASS 证据。
- [x] 已读取 CR-010 主线程实现验证记录、关键实现文件、专项测试和 README / USER-MANUAL 文档入口。

#### 出口准则

- [x] `uv run --python 3.11 python -m py_compile market_data/*.py engine/*.py experiments/*.py` 已执行并通过。
- [x] CR-010 四个专项测试文件已执行并通过。
- [x] 关联回归测试集已执行并通过。
- [x] `uv run --python 3.11 pytest -q` 已执行并通过。
- [x] `git diff --check` 已执行并通过。
- [x] 文档 / 测试中不存在裸 `python -m market_data.cli backup-*` 或 `restore-*` 入口。
- [x] CP7 正式证据文件已写入，并明确区分本轮 meta-qa PASS 与上一轮 shutdown 不作证据。

## CR-011 因子研究生产级数据补齐测试策略增量

### 当前状态与边界

本节记录 CR-011 文档刷新阶段对测试策略的增量收敛。CR-011 目标是将实验 17-21 从 fixed snapshot / proxy benchmark baseline 升级为具备真实 benchmark、PIT 股票池、可交易性、执行价、复权、暴露、容量成本、factor panel audit 与 robust validation 的研究输入。当前 `CR011-S01` 至 `CR011-S08` 均为 `verified / CP7 PASS`，CP8 人工终验已 approved，CR-011 已关闭。

本节不授权重新执行真实抓取、不写真实 lake、不读取或打印 `.env` / token / 密码 / 私钥 / cookie / session、不读取或列出旧 `data/**`、不覆盖旧 `reports/experiment_17_21/factor_strategy_report.md`。新版研究报告、panel 和 robust validation 的输出根为 `reports/experiment_17_21_cr011/**`。

### 测试设计方法选择

| 方法 | CR-011 适用性 | 应用说明 |
|---|---|---|
| 等价分区 | 高 | 按 benchmark policy、PIT / fixed universe、可交易 / 不可交易、OHLCV / VWAP / close proxy、复权可用 / 不可用、暴露可用 / blocked、容量成本敏感性、panel stage 和 validation view 划分分区。 |
| 边界值分析 | 高 | 覆盖 exact policy、`available_at <= decision_time`、上市天数、涨跌停边界、单一成本点、缺 panel stage、缺 validation view、旧报告路径和 run_id 跳转。 |
| 状态转换测试 | 高 | 覆盖 benchmark / PIT / tradability / adjustment / exposure / capacity 输入进入 factor panel audit，再进入 robust validation、claims gate 和 metadata merge 的 pass / fail 转换。 |
| 错误推测 | 高 | 构造 proxy benchmark 误填真实字段、future leak、旧 report overwrite、默认联网、真实 lake 写入、凭据读取、旧 `data/**` 操作、blocked claims 被 S08 放宽等风险。 |

### ISO 25010 质量优先级

| 质量特征 | 优先级 | CR-011 验证重点 |
|---|---|---|
| 功能适合性 | P0 | S01..S08 的数据补齐、factor panel audit 和 robust validation 输出是否覆盖验收项。 |
| 可靠性 | P0 | S08 定向测试、上游和实验回归、fail-closed probe 均通过；缺阶段 / 缺视图 / invalid grid 不生成强声明。 |
| 安全性 | P0 | `network_calls=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_operations=0`、`old_report_overwrites=0`。 |
| 可维护性 | P1 | panel stage、validation view、allowed / blocked claims、known limitations 和 metadata 字段可追溯。 |
| 可移植性 | P1 | Python 3.11 + uv 离线验证路径可运行，不依赖真实 provider、真实 lake 或本机私有数据。 |
| 兼容性 | P1 | S01/S02/S05/S07 的 blocked claims 不被 S08 allowed claims 放宽；旧实验 17-21 baseline 不被覆盖。 |
| 易用性 | P2 | 报告路径、缺口、blocked claims、next action 和安全计数对用户可读。 |
| 性能效率 | P3 | 验证使用小规模 fixture、临时目录和静态扫描，不触发大规模真实数据处理。 |

### CR-011 质量门

#### 入口准则

- [x] CR-011 变更单已 approved，状态为 `closed`。
- [x] `CR011-S01` 至 `CR011-S08` 均已完成 CP6 / CP7，Story 状态为 `verified`。
- [x] `process/DEVELOPMENT-PLAN.yaml` 记录 CR011 三个批次：`CR011-DATA-BATCH-A`、`CR011-RESEARCH-BATCH-B`、`CR011-VALIDATION-BATCH-C`。
- [x] S08 CP7 证据为 PASS，且记录 factor panel、robust validation、fail-closed、安全边界和回归摘要。
- [x] 文档刷新只允许写 `README.md`、`docs/USER-MANUAL.md`、`process/TEST-STRATEGY.md`。

#### 出口准则

- [x] README 说明 CR-011 已验证能力、报告路径、旧报告只读 baseline、安全边界和 CP8 approved / closed 状态。
- [x] 用户手册说明 factor panel 四阶段、robust validation 五视图、默认安全计数和排障方式。
- [x] 本测试策略补充 CR-011 矩阵与 CP7 验证摘要。
- [x] 未复制 CP7 大段内容；只保留用户可读摘要和可追溯链接。
- [x] 未修改代码、测试、实验脚本、真实数据、旧报告、`delivery/**`、`process/STATE.md`、`process/STORY-STATUS.md` 或 `process/DEVELOPMENT-PLAN.yaml`。

### CR-011 测试矩阵

| 验证主题 | 覆盖 Story | 方法 | 阻断等级 | 关键断言 | 证据摘要 |
|---|---|---|---|---|---|
| 真实 benchmark 与 policy 消费 | CR011-S01 | 等价分区、错误推测 | BLOCKING | 真实 `hs300_index` 与 proxy benchmark 字段隔离，policy 不混淆。 | S01 CP7 PASS；定向 `6 passed`，相关回归 `74 passed`。 |
| PIT 股票池与 lifecycle | CR011-S02 | 边界值、状态转换 | BLOCKING | 历史成分、权重、上市退市、股票状态进入 as-of universe gate。 | S02 CP7 PASS；定向 `7 passed`，相关回归 `35 passed`。 |
| 可交易性与涨跌停门控 | CR011-S03 | 等价分区、错误推测 | BLOCKING | 停牌、ST、无成交、上市天数、涨跌停和事件状态进入门控。 | S03 CP7 PASS；定向 `8 passed`，相关回归 `33 passed`，安全扫描 PASS。 |
| OHLCV / VWAP clean feed | CR011-S04 | 边界值、错误推测 | BLOCKING | execution price policy 使用 exact 语义；非法空白或空字符串被拒绝。 | 首次 CP7 blocker 已修复，CP7 reverify PASS。 |
| 复权与公司行动审计 | CR011-S05 | 状态转换、错误推测 | BLOCKING | `adj_factor`、公司行动 available_at 和异常解释不产生 future leak。 | S05 CP7 PASS；定向 `7 passed`，回归 `57 passed`，available_at probe PASS。 |
| 行业 / 市值 / 风格暴露 | CR011-S06 | 等价分区、错误推测 | BLOCKING | 暴露缺失时 blocked claims 保留；行业市值中性声明受输入约束。 | 首次 CP7 blocker 已修复，CP7 reverify PASS。 |
| 流动性 / 容量 / 成本敏感性 | CR011-S07 | 边界值、状态转换 | BLOCKING | 成交额、换手、容量模型、冲击成本和 cost grid 不放宽风险。 | S07 CP7 PASS；定向 `7 passed`，相关回归 `40 passed`，benchmark / 实验回归 `8 passed`。 |
| factor panel audit 与 robust validation | CR011-S08 | 等价分区、边界值、状态转换、错误推测 | BLOCKING | panel stage exact 四阶段；validation view exact 五类；缺阶段 / 缺视图 / invalid grid fail closed；旧报告不覆盖。 | S08 CP7 PASS；定向 `3 passed`，上游和实验回归 `29 passed`，fail-closed probe PASS。 |

### S08 验证摘要

| 项 | 结论 | 追溯 |
|---|---|---|
| 四阶段 factor panel exact | PASS：`raw`、`directional`、`winsorized`、`zscore` | `process/checks/CP7-CR011-S08-factor-panel-audit-and-robust-validation-VERIFICATION-DONE.md` |
| 五类 robust validation exact | PASS：`rolling`、`annual`、`market_state`、`parameter_grid`、`cost_grid` | 同上 |
| fail-closed probe | PASS：缺 view、invalid cost grid、缺 market state、缺 panel stage 均 fail closed | 同上 |
| 上游 blocked claims | PASS：S01/S02/S05/S07 blocked claims 不被 S08 allowed claims 放宽 | 同上 |
| 输出隔离 | PASS：新版输出根为 `reports/experiment_17_21_cr011/**`，旧报告覆盖次数为 0 | 同上 |
| 安全计数 | PASS：`network_calls=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_operations=0`、`old_report_overwrites=0` | 同上 |

### 文档风险判定

| 风险 | 等级 | 当前结论 | 后续处理 |
|---|---|---|---|
| CP8 人工终验完成 | PASS | 用户已 approve `checkpoints/CP8-CR011-DELIVERY-READINESS.md`，CR-011 已关闭。 | 若后续变更 CR-011 口径，需创建新的 CR 或重开变更流程。 |
| 旧报告误覆盖 | BLOCKING | README、USER-MANUAL 和本策略均写明旧报告只作 baseline，新输出使用 `reports/experiment_17_21_cr011/**`。 | 若后续发现输出指向旧目录，必须阻断并改回隔离目录。 |
| 默认安全边界被误解为真实执行授权 | BLOCKING | 文档明确默认五项安全计数为 0，不授权联网、写湖、读凭据、旧数据操作或旧报告覆盖。 | 真实执行必须另走用户显式授权和 dry-run / 外置 lake runbook。 |

## CR-014 BATCH-A CP7 验证准备策略增量

### 当前状态与边界

本节记录 2026-05-27 对 `CR014-S01` 至 `CR014-S08` 的测试策略准备。用户已批准 `checkpoints/CP5-ALL-STORIES-LLD-BATCH.md` 中全部推荐决策，BATCH-A 的 8 份 LLD 已 `confirmed=true`、`implementation_allowed=true`。本节不是正式 CP7 验证报告，不生成 `CP7-*` 结论，也不把任何 Story 标记为 `verified`。正式 CP7 必须等待对应 Story 完成 CP6 编码完成门，并在 CP6 证据可读后逐 Story 执行。

本批批准范围只覆盖 S01..S08 的离线合同实现和验证准备，不授权 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 操作、旧 reports 覆盖、DuckDB 依赖引入、DuckDB 写入或 catalog current pointer 自动发布。`CR014-S09-windowed-real-fetch-lake-write-run` 属于后续 BATCH-B，不在本批 CP6/CP7 验证范围内；任何真实抓取 / raw / manifest 写湖都必须等 S01..S08 verified、S09 LLD/CP5/CP6 就绪并获得用户 per-run authorization 后再验证。

### 测试设计方法选择

| 方法 | CR-014 BATCH-A 适用性 | 应用说明 |
|---|---|---|
| 等价分区 | 高 | 按 lifecycle / catalog / runtime / DuckDB audit / readiness / replay / research consumer / unsupported capability 八类 Story 分区；按 published current truth、candidate audit、blocked claim、required missing 分区。 |
| 边界值分析 | 高 | 覆盖最近已闭市交易日、lifecycle 缺字段、catalog pointer 缺字段、publish intent 缺失、source/interface allowlist 缺失、retention `dry_run=true/false`、release condition 完整度。 |
| 状态转换测试 | 高 | 覆盖 `plan -> run gate -> normalize/replay candidate -> validate -> explicit publish -> read/query`，并验证 Validate / parity PASS 不会自动 publish。 |
| 错误推测 | 高 | 构造 provider / credential / old data / old report / lake write / direct DuckDB / forbidden SQL / derived VWAP / docs direct write 等越界路径，并使用 monkeypatch sentinel 证明未触发。 |

### ISO 25010 质量优先级

| 质量特征 | 优先级 | CR-014 验证重点 |
|---|---|---|
| 功能适合性 | P0 | S01..S08 LLD 第 6 / 7 / 10 / 13 节的接口、主流程、异常路径和回滚边界均可被测试追溯。 |
| 可靠性 | P0 | 所有验证默认使用离线 fixture、内存对象和 `tmp_path`；不依赖真实网络、真实 lake、凭据或旧 `data/**`。 |
| 安全性 | P0 | 静态 forbidden-op 扫描、monkeypatch sentinel 和 permission counters 必须共同证明真实操作计数为 0。 |
| 可维护性 | P1 | lifecycle、manifest、catalog pointer、readiness matrix、claim boundary、unsupported matrix 和 docs refresh contract 字段结构化。 |
| 可移植性 | P1 | DuckDB 为 optional / lazy-import；未安装或未批准依赖时 fallback 到 pandas / pyarrow evidence，测试仍可通过。 |
| 兼容性 | P1 | Parquet / catalog 是 source of truth；DuckDB evidence、candidate audit 和研究消费 metadata 不反向更新 pointer 或 allowed claim。 |
| 易用性 | P2 | 错误输出包含 typed code、evidence ref、release condition 和解除条件，不输出 token、私有路径或 provider payload。 |
| 性能效率 | P3 | CP7 使用小 fixture 与 `tmp_path`，不扫描全历史真实 lake，不处理真实全 A 数据。 |

### 准备态质量门

#### 当前准备态入口准则

- [x] 已读取 `AGENTS.md` 中 Story 执行、CP6/CP7、输出隔离、uv、测试策略和 LLD 消费契约。
- [x] 已读取 `process/TEST-STRATEGY.md` 当前版本。
- [x] 已读取 `CR014-S01` 至 `CR014-S08` 八份 LLD 的 frontmatter、第 6 节接口、第 7 节核心流程、第 10 节测试设计和第 13 节回滚策略。
- [x] 已读取 `checkpoints/CP5-ALL-STORIES-LLD-BATCH.md`，确认 CP5 状态为 `approved` 且 S09 不属于当前 BATCH-A。
- [x] 本轮只修改测试策略；不修改业务代码、测试代码、依赖文件、真实数据、报告、README/docs 或 Story 文件。

#### 正式 CP7 入口准则

- [ ] 对应 Story 状态为 `ready-for-verification`。
- [ ] 对应 Story 的 CP6 编码完成门结论为 `PASS` 或有明确 `WAIVED`，且含 Agent Dispatch Evidence。
- [ ] CP6 证据列出实际实现文件、测试文件、静态扫描和自检结果。
- [ ] `process/VALIDATION-ENV.yaml` 存在且 `approval.confirmed=true`；验证对象与 CR014 Story 范围一致。
- [ ] 验证命令只使用离线 fixture / `tmp_path` / monkeypatch sentinel，不需要真实网络、真实 lake、凭据或旧数据。

#### 正式 CP7 出口准则

- [ ] Story LLD 验收项逐条有测试或静态证据，BLOCKING 断言全部 PASS。
- [ ] permission counters 明确为 0：`provider_fetches=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_reads=0`、`old_report_overwrites=0`；涉及 DuckDB 的 Story 追加 `duckdb_dependency_changes=0`、`.duckdb_source_of_truth_files=0`。
- [ ] 静态 forbidden-op 扫描无越界命中：provider SDK 默认调用、`.env` 读取、真实 lake 写入、旧 `data/**` 操作、旧 reports 覆盖、direct DuckDB 写入、README/docs 非授权修改。
- [ ] monkeypatch sentinel 未触发：connector、credential reader、filesystem write、publish pointer update、DuckDB write path、docs direct writer 均按 Story 边界验证。
- [ ] publish gate 断言通过：Validate PASS、DuckDB parity PASS、candidate audit PASS 均不自动更新 catalog current pointer。
- [ ] S09 / BATCH-B 相关真实抓取和 raw / manifest 写湖不进入本批验证命令、测试 fixture 或 allowed claim。

### CR-014 统一验证原则

| 原则 | 阻断等级 | CP6 自检要求 | CP7 验证要求 |
|---|---|---|---|
| 离线 fixture / `tmp_path` | BLOCKING | 新增测试只构造内存对象、临时目录和小型 fixture；不得依赖真实 lake root、旧 `data/**` 或 `.env`。 | 复核测试路径和 fixture；必要时 monkeypatch 真实路径访问为 fail sentinel。 |
| 静态 forbidden-op 扫描 | BLOCKING | CP6 必须列出 `rg` 扫描范围和越界命中解释；命中 provider、credential、old data、old report、direct DuckDB write、docs direct write 时不得隐瞒。 | CP7 复跑或抽查扫描；任何未豁免越界命中均 FAIL。 |
| monkeypatch sentinel | BLOCKING | 对 connector、credential reader、publish pointer update、filesystem write、DuckDB write、docs writer 设置 fail sentinel。 | 执行定向测试并确认 sentinel call count 为 0；若 Story 允许 dry-run result，必须区分真实写入与 dry-run 计数。 |
| 真实操作计数为 0 | BLOCKING | 实现输出或测试断言 permission counters 全 0。 | CP7 报告逐 Story 记录 counters；任一真实计数非 0 即 FAIL。 |
| DuckDB optional / lazy fallback | BLOCKING for S04，REQUIRED for consumers | 不修改 `pyproject.toml` / `uv.lock`；DuckDB import 失败或 read-only open failed 时输出 pandas / pyarrow fallback evidence。 | monkeypatch `import duckdb` 失败和 read-only open 失败；确认 fallback 字段与 DuckDB evidence 等价，且不创建 `.duckdb` source-of-truth 文件。 |
| Publish gate 不自动更新 pointer | BLOCKING | Validate / parity / candidate audit 测试必须断言 `current_pointer_changes=0`，只有 explicit publish gate 且 dry-run / 授权满足时才返回 pointer update 结果。 | 对 S02/S03/S04/S05/S06/S07 的相关路径设置 publish sentinel；确认 PASS evidence 不触发 pointer update。 |
| Candidate 与 published 隔离 | BLOCKING | candidate path 含 `run_id`，published current truth 只能通过 catalog pointer 暴露。 | 断言 reader / DuckDB / research consumer 默认拒绝未发布 candidate lake scan。 |
| S09 不在本批验证 | BLOCKING | CP6 不新增真实 provider run、windowed real fetch、raw / manifest write lake 执行入口。 | CP7 静态扫描和测试清单不得包含 S09 实现或真实执行断言；若发现 S09 命令或 fixture，应退回 meta-po 重新路由。 |

### Story 级最小回归集建议

| Story | 正式 CP7 最小回归集 | BLOCKING 断言 |
|---|---|---|
| CR014-S01 | `tests/test_cr014_universe_lifecycle_contract.py`；lifecycle required fields、code-change chain、recent closed trade date、denominator。 | 缺 lifecycle / calendar / code-change 字段时 full-A allowed claim 为 0；provider / credential / old data / lake counters 为 0。 |
| CR014-S02 | `tests/test_cr014_catalog_publish_gate.py`；manifest completeness、catalog pointer required fields、candidate / published path separation、publish gate dry-run。 | Validate PASS 不自动 publish；无 publish intent 时 `pointer_changes=0`；candidate path 不等于 published path；真实 lake 写入为 0。 |
| CR014-S03 | `tests/test_cr014_p0_pipeline_contract.py`；plan / run gate / normalize / replay / validate / publish / read 状态机。 | 无 authorization 或 source/interface allowlist 时 connector call count 为 0；normalize / replay / validate 均不更新 pointer；S09 真实 run 不进入本 Story。 |
| CR014-S04 | `tests/test_cr014_duckdb_readonly_boundary.py`；readonly SQL 模板、published / candidate mode、fallback、parity evidence、side-effect sentinel。 | DuckDB 未安装或 read-only open failed 时 lazy fallback；forbidden SQL 被拒绝；parity PASS 不 publish；`.duckdb` source-of-truth 文件数为 0。 |
| CR014-S05 | `tests/test_cr014_readiness_claim_boundary.py`；readiness matrix、gap register、claim boundary、legacy baseline ref、permission violation。 | 任一 P0 / lifecycle / catalog / evidence 缺口 blocked；candidate audit PASS 但未 publish 时 allowed current truth claim 为 0；旧 report 只作 ref，不读取或覆盖。 |
| CR014-S06 | `tests/test_cr014_incremental_replay_retention.py`；incremental plan、resume conflict、replay source missing、retention dry-run、published truth protection。 | replay 不触发 provider / credential / raw write / pointer change；resume conflict 不 silent overwrite；retention 默认 dry-run，不删除或迁移。 |
| CR014-S07 | `tests/test_cr014_research_consumer_boundary.py`；published current truth consumer、claim metadata、DuckDB evidence ref、docs refresh contract、forbidden imports。 | 研究层不得 provider fetch、lake write、credential read、legacy data access、direct DuckDB 或 candidate lake scan；README / docs 修改次数为 0。 |
| CR014-S08 | `tests/test_cr014_unsupported_boundary.py`；exact unsupported capability matrix、release conditions、real VWAP blocked、derived substitute denied、metadata merge。 | W3 / minute / tick / Level2 / order match / real VWAP / VWAP fill allowed production claim 为 0；close proxy 和 `amount/volume` 不得派生真实 VWAP claim。 |

### 正式 CP7 建议静态扫描

正式 CP7 可在读取 CP6 后按 Story 影响文件裁剪扫描范围。默认建议至少覆盖新增 CR014 实现文件、对应测试文件和 `engine/research_dataset.py` / `experiments/reporting.py` 的相关 diff：

```bash
rg -n "requests|urllib|httpx|socket|tushare|akshare|TickFlow|TOKEN|token|secret|password|cookie|session|dotenv|os\\.environ" market_data engine experiments tests
rg -n "data/|reports/|README\\.md|docs/|USER-MANUAL|publish_current|current_pointer|duckdb|COPY|EXPORT|ATTACH|INSTALL|LOAD|CREATE|INSERT|UPDATE|DELETE" market_data engine experiments tests
rg -n "CR014-S09|windowed-real-fetch|real fetch|raw/manifest write|provider fetch|authorization_id" market_data engine experiments tests process/stories
git status --short
```

上述命令仅作为 CP7 准备口径；当前准备阶段不运行测试、不运行真实网络、不读取凭据、不触碰真实数据湖。若正式 CP7 执行时命中误报，CP7 报告必须逐项记录命中位置、豁免理由和剩余风险；不得用模糊匹配自动放行。

## CR-015 / CR-016 / CR-017 CP7 验证完成策略增量

### 当前状态与验证边界

本节记录 2026-05-28 对 CR-015 / CR-016 / CR-017 受控离线范围的测试策略收敛。当前事实源为 `process/STORY-STATUS.md`、`process/STATE.md` 和已完成的 CP7 结果文件；本节只更新当前测试策略口径，不改写历史 CR 过程记录。

| 范围 | 当前状态 | 验证边界 |
|---|---|---|
| `CR017-S01..S06` | verified / CP7 PASS | 覆盖复权策略、raw prices / adj_factor、qfq / hfq 派生视图、reader policy gate、质量 / 泄漏验证、research / QMT consumer 文档与迁移指南；不授权真实 QMT 或 scale_up。 |
| `CR015-S01..S07` | verified / CP7 PASS | 覆盖 QMT foundation、adapter contract、OMS、pre-trade risk gate、broker lake schema dry-run、shadow order intent、foundation runbook；只允许 `shadow` / `dry_run` / `mock`。 |
| `CR016-S01..S04` | verified / CP7 PASS | 覆盖 simulation enable gate、reconciliation、monitoring / kill switch、simulation / live runbook 与 approval gates；不启动 simulation / live。 |
| `CR016-S07` | verified / CP7 PASS | 覆盖用户手册、incident playbook、recovery gate 和 unsupported claim boundary；只验证文档合同和静态测试。 |
| `CR016-S05` / `CR016-S06` | later-gated | `implementation_allowed=false`；不得计入 implemented / verified；live_readonly、small_live、scale_up 必须等待后续独立审批、research maturity gate、CP5/CP6/CP7 和 per-run authorization。 |

文档、runbook、incident playbook、CP5、CP6、CP7、Story `verified` 或本策略条目均不是 standing approval。它们不授权 QMT / MiniQMT / GUI、broker API、真实发单、撤单、账户查询、凭据读取、真实 snapshot 拉取、provider fetch、真实 lake 写入、broker lake 写入、publish、simulation、live_readonly、small_live、scale_up 或真实 incident 持久化。

### 测试设计方法选择

| 方法 | CR-015 / CR-016 / CR-017 适用性 | 应用说明 |
|---|---|---|
| 等价分区 | 高 | 按 CR017 研究消费、CR015 foundation、CR016 staged activation、later-gated scope 和 forbidden operation 分区。 |
| 边界值分析 | 高 | 验证所有真实操作计数、默认授权声明、unsupported claim unblocked、sensitive raw value output、non-raw execution allowed、scale_up allowed 的 0 边界。 |
| 状态转换测试 | 高 | 验证 `shadow -> simulation -> live_readonly -> small_live -> scale_up` 只能按相邻阶段申请；recovery gate 只解除 incident blocked 状态，不启动真实运行。 |
| 错误推测 | 高 | 针对 CP7 PASS 被误写为真实授权、S05/S06 被误写为 implemented / verified、CR017 verified 被误解为 scale_up 解禁、真实 VWAP / minute / tick / Level2 / order-match claim 被解除等风险做静态扫描。 |

### ISO 25010 质量优先级

| 质量特征 | 优先级 | 验证重点 |
|---|---|---|
| 功能适合性 | P0 | 已 verified Story 的 AC、LLD §6 / §7 / §10 / §13 和文档合同均有 CP7 证据；S05/S06 later-gated 例外明确排除。 |
| 可靠性 | P0 | 验证只使用离线 fixture、静态文档扫描、fake / mock adapter 和 `uv run --python 3.11` 测试；不依赖真实 QMT 环境。 |
| 安全性 | P0 | 必测安全计数全部为 0；文档不输出敏感原值；CP5/CP6/CP7/Story verified 不被解释为真实操作授权。 |
| 可维护性 | P1 | runbook、incident playbook、README、USER-MANUAL 和测试策略使用固定 stage、counter、blocked claim 和 later-gated 术语。 |
| 兼容性 | P1 | CR017 raw-only 执行价边界不放宽 CR016 scale_up；CR015 foundation 不自动进入 CR016 live path。 |
| 可移植性 | P1 | 验证命令统一通过 `uv run --python 3.11`，不修改 `pyproject.toml` / `uv.lock`。 |
| 易用性 | P2 | 用户文档明确每个 stage 能做什么、不能做什么、需要哪些后续授权和证据。 |

### CP7 完成证据摘要

| 证据 | 结论 | 关键安全结论 |
|---|---|---|
| `process/checks/CP7-CR015-S07-docs-and-foundation-runbook-boundary-VERIFICATION-DONE.md` | PASS，`6 passed in 0.04s` | QMT / broker API、真实发单、撤单、账户查询、凭据读取、真实写湖、provider fetch、publish、simulation / live activation 均为 0。 |
| `process/checks/CP7-CR016-S04-simulation-live-runbook-and-approval-gates-VERIFICATION-DONE.md` | PASS，`41 passed in 0.19s` | runbook、approval gate、rollback / recovery matrix 通过；simulation / live / small_live / scale_up run 均为 0。 |
| `process/checks/CP7-CR016-S07-docs-user-manual-and-incident-playbooks-VERIFICATION-DONE.md` | PASS，`29 passed in 0.16s` | incident playbook、manual takeover record、unsupported claim boundary、sensitive raw value scan 通过；真实 incident 持久化为 0。 |
| `process/checks/CP7-CR017-S06-research-qmt-consumer-docs-and-migration-guide-VERIFICATION-DONE.md` | PASS，`6 passed` + CR017 回归 `39 passed` | QMT execution raw-only、legacy qfq read-only、unsupported execution blocked；provider / lake / credential / publish / dependency / scale_up allowed 均为 0。 |

### 必测安全计数

下列计数是 CR-015 / CR-016 / CR-017 后续文档、验证或终验必须继续复核的 P0 安全边界；任一计数非 0 均不得把真实运行、S05/S06 或 scale_up 标记为已授权。

| 计数项 | 期望值 | 覆盖范围 |
|---|---:|---|
| `qmt_api_call` / `real_broker_operation` | `0` | 禁止调用 QMT / MiniQMT / XtQuant / broker API。 |
| `real_order_call` / `real_cancel_call` | `0` | 禁止真实发单和撤单。 |
| `account_query_call` / `account_write_call` | `0` | 禁止查询或写入真实账户状态。 |
| `credential_read` / `sensitive_raw_value_output` | `0` | 禁止读取或输出 `.env`、token、password、cookie、session、private key、真实账户、持仓或 broker root 原值。 |
| `real_broker_lake_write` / `real_lake_write` | `0` | 禁止写真实 broker lake、market-data lake、`data/**` 或 `reports/**`。 |
| `provider_fetch` / `publish` | `0` | 禁止 provider fetch 和 current pointer / 运行产物 publish。 |
| `dependency_change` | `0` | 禁止修改 `pyproject.toml` / `uv.lock` 或执行依赖变更。 |
| `simulation_run` / `live_run` / `small_live_run` / `scale_up_run` | `0` | 禁止启动 simulation、live_readonly、small_live 或 scale_up。 |
| `real_snapshot_pull` / `incident_persisted` | `0` | 禁止拉取真实 broker snapshot 或持久化真实 incident。 |
| `default_real_operation_authorization_claim` | `0` | 禁止把文档、runbook、CP5、CP6、CP7 或 Story verified 写成默认真实操作授权。 |
| `unsupported_execution_claim_unblocked` / `microstructure_allowed_claim_count` | `0` | 禁止解除真实 VWAP、minute、tick、Level2、order-match 或 microstructure execution blocked claim。 |
| `non_raw_execution_allowed` / `adjusted_execution_price_pass_count` | `0` | QMT execution 只能使用 `raw` / broker reference；`qfq`、`hfq`、`returns_adjusted` 不得进入执行价。 |
| `legacy_qfq_overwrite` / `old_report_overwrite_allowed` | `0` | legacy qfq 和旧报告只读保留，不覆盖、不替换、不提升为 current truth。 |
| `production_adjustment_governance_claim_allowed` / `scale_up_allowed` | `0` | CR017 S01-S06 已 verified，但 production governance 和 scale_up 仍需后续 gate 与用户授权。 |

### 质量门

#### 当前文档收敛入口准则

- [x] 已读取 `process/STORY-STATUS.md` 和 `process/STATE.md`，确认 CR017 S01..S06、CR015 S01..S07、CR016 S01..S04 / S07 的 verified 状态，以及 CR016 S05/S06 later-gated。
- [x] 已读取 CR015-S07、CR016-S04、CR016-S07、CR017-S06 的 CP7 PASS 文件。
- [x] 写入范围限定为 `README.md`、`docs/USER-MANUAL.md`、`process/TEST-STRATEGY.md`。
- [x] 本轮不修改源码、测试、依赖、`data/**`、`reports/**`、`delivery/**`、`DEV-LOG.md` 或凭据。

#### 当前文档收敛出口准则

- [x] README 顶部能力表不再使用旧 pending-CP7 状态词描述 CR015 / CR016 / CR017。
- [x] README 与 USER-MANUAL 不再使用旧版 CR017 整体验证前置句式作为当前事实；改为 CR017 S01..S06 已 verified，但 scale_up 仍受 CR016-S06 later-gated、research maturity gate 和用户后续显式授权控制。
- [x] 文档明确 runbook、incident playbook、CP5、CP6、CP7、Story verified 不授权真实运行。
- [x] TEST-STRATEGY frontmatter 和本增量章节记录 CP7 完成事实、later-gated 例外、必测安全计数和真实操作禁止边界。

#### 后续真实运行入口准则

- [ ] 目标 Story 不属于 `CR016-S05` / `CR016-S06` later-gated，或已有新的人工审批明确解除 later-gated 状态。
- [ ] 对应 Story 已完成 LLD、CP5、CP6、CP7，并有真实子 agent 调度证据。
- [ ] 每次 run 都有用户显式 per-run authorization，且授权文本至少包含 `authorization_id`、stage、mode、strategy、run_id、capital limit、order scope、approver、expiry 和 rollback plan ref。
- [ ] reconciliation gate、kill switch readiness、recovery gate 和 rollback target 均已满足。
- [ ] 上述必测安全计数中与真实运行无关的默认授权、unsupported claim、敏感输出、依赖变更、非 raw execution、legacy overwrite 等仍为 0。
