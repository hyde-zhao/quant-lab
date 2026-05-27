---
handoff_id: "META-PM-REQ-REFRESH-RATE-LIMIT-2026-05-14"
created_at: "2026-05-14"
created_by: "meta-po"
target_agent: "meta-pm"
current_phase: "requirement-clarification"
status: "assigned"
cr_required: false
reason_no_cr: "USE-CASES.md 与 REQUIREMENTS.md 仍为 draft，需求尚未通过人工确认；本轮属于需求确认前增量澄清，不变更已确认基线。"
supporting_agents:
  - "meta-qa"
  - "meta-se"
---

# meta-pm 需求阶段文档刷新分派：数据源限速与本地数据更新

## 分派结论

当前仍处于 `requirement-clarification`，`process/USE-CASES.md` 与 `process/REQUIREMENTS.md` 均为 v1.2 draft，`confirmed=false`，`ready_for_design=false`，且 `checkpoints/REQUIREMENTS-CHECKPOINT.md` 尚未获得用户确认。因此，本轮用户追加的“本地数据怎么获取/构造/更新周期还必须考虑数据源限速问题”属于需求确认前草稿增量澄清，不创建 CR，不推进 `solution-design`。

`meta-pm` 是本轮主写入方，负责刷新需求阶段正文。`meta-qa` 只补充可验证性要求，`meta-se` 只读提出后续 HLD 输入约束，不得生成 HLD、ADR、Story 或开发计划。

## 必须读取的上下文

| 文件 | 用途 |
|---|---|
| `process/STATE.md` | 确认当前阶段与不得推进的状态约束 |
| `process/REQUEST.md` | 原始目标、本地数据路线和第一版范围 |
| `process/USE-CASES.md` | 当前 v1.2 场景草稿，需增量刷新到下一版本 |
| `process/REQUIREMENTS.md` | 当前 v1.2 需求草稿，需增量刷新到下一版本 |
| `process/CLARIFICATION-LOG.md` | 追加本轮澄清记录和 HLD 前确认项 |
| `checkpoints/REQUIREMENTS-CHECKPOINT.md` | 当前已由 meta-po 回退为需刷新，刷新完成后由 meta-po 复核 |

## 本轮必须纳入的用户要求

| 主题 | 必须覆盖的需求语义 |
|---|---|
| 数据源限速 | 文档必须显式承认 AKShare 等数据源存在限速、字段变更、接口不可用和临时失败风险；数据准备脚本必须遵守限速，不得把高频重试压到数据源。 |
| 请求节流 | 数据获取/更新流程必须设计可配置节流参数，例如每请求间隔、单批大小、最大并发为 1 或明确限制；默认采取保守串行抓取。 |
| 重试退避 | 网络失败、限流、临时服务错误必须采用有限次数重试与指数退避或固定退避；重试耗尽后记录失败项，不得无限循环。 |
| 断点续传 | 数据准备任务必须支持从上次成功批次继续，避免因单次失败重复全量抓取。 |
| raw 缓存 | 原始响应或原始表格应进入 raw 缓存区，标准化 parquet 从 raw 缓存派生；不得让回测引擎直接依赖实时接口。 |
| 增量更新 | 已有本地缓存时，默认只更新缺失日期或最近窗口，不重复全量抓取。 |
| 回补最近 N 个交易日 | 为应对数据源迟到修正或复权数据变动，更新流程需要支持回补最近 N 个交易日；N 的默认值可留给 HLD 确认，但需求必须固定“可配置”。 |
| 失败降级 | 数据源接口不可用时，若本地 parquet 已满足回测区间和 schema，回测/扫描不应被阻塞；数据准备失败只影响数据新鲜度，并在报告中披露。 |
| 回测引擎不得直接联网 | 回测、扫描、候选筛选和差异分析主路径只能读取本地 parquet 与 manifest，不得在运行中请求 AKShare、聚宽或其他远程接口。 |
| manifest 记录 | 数据准备必须输出 manifest，记录抓取批次、数据源、接口名、股票/日期范围、请求时间、参数、成功项、失败项、重试次数、raw 缓存路径、标准化输出路径和数据覆盖范围。 |
| 质量报告 | 数据质量报告必须输出缺失统计、失败统计、覆盖区间、失败股票/日期、字段缺失、重复记录、异常价格、回补数量和数据新鲜度。 |

## meta-pm 修改范围

| 文件 | 操作 | 修改要点 |
|---|---|---|
| `process/USE-CASES.md` | 增量更新 | 升级到下一版本；在修订记录追加本轮内容；补强 UC-01 的本地缓存数据准备、raw 缓存、manifest、限速与失败降级；必要时补强 UC-03/UC-06 中扫描离线性和后续数据真实性增强。 |
| `process/REQUIREMENTS.md` | 增量更新 | 升级到下一版本；新增或修订 P0/P1 需求，覆盖限速、节流、退避、断点续传、raw 缓存、增量更新、最近 N 日回补、manifest、质量报告、失败降级和回测主路径离线硬约束。 |
| `process/CLARIFICATION-LOG.md` | 追加记录 | 追加本轮澄清记录；新增 HLD 前确认问题，建议从 Q-012 起，覆盖默认节流参数、重试次数/退避策略、最近 N 日回补默认值、raw 缓存保留策略、manifest schema 与质量报告阈值。 |

## 建议需求落点

| 主题 | 建议落点 |
|---|---|
| 数据准备与回测解耦 | 修订 `REQ-016` / `REQ-034`，强化“数据准备可联网，回测主路径不得联网”。 |
| 数据源限速与请求节流 | 新增 P0 数据准备需求，验收条件包含可配置请求间隔、单批大小、并发限制和默认保守策略。 |
| 重试退避与断点续传 | 新增 P0 数据准备可靠性需求，验收条件包含失败重试上限、退避记录、断点恢复和失败项不丢失。 |
| raw 缓存与标准化派生 | 新增 P0 数据缓存需求，区分 raw 缓存、标准化 parquet、manifest 三类产物。 |
| 增量更新与最近 N 日回补 | 新增 P0/P1 更新周期需求，验收条件包含已缓存数据只补缺口、最近 N 个交易日可配置回补。 |
| manifest 批次记录 | 新增 P0 可追溯需求，验收条件包含批次 ID、数据源、接口名、请求参数、日期范围、成功/失败项、重试次数、输出路径和覆盖范围。 |
| 质量报告缺失/失败统计 | 新增 P0 可验证需求，验收条件包含缺失率、失败数、失败 symbol/date、字段缺失、重复行、异常价格、回补数量和新鲜度统计。 |
| 数据源不可用降级 | 新增或修订 P0 离线验收需求，要求接口不可用时，只要本地 parquet 满足区间和 schema，回测/扫描继续运行并披露数据新鲜度。 |

## meta-qa 补充任务：可验证性要求

请 `meta-qa` 只提供需求阶段可验证性输入，不生成 `TEST-STRATEGY.md`，不执行验收，不推进阶段。

可直接转发给 `meta-qa` 的任务说明：

> 当前仍在 `requirement-clarification`。请只读 `process/USE-CASES.md`、`process/REQUIREMENTS.md`、`process/CLARIFICATION-LOG.md` 和本 handoff，为数据源限速与本地数据更新补充可验证性要求。重点输出可被 meta-pm 写入需求验收条件的检查点：限速参数可配置、请求节流生效、重试次数有上限、退避记录可追踪、断点续传不重复已完成批次、raw 缓存存在、标准化 parquet 可从 raw 派生、增量更新只补缺口、最近 N 个交易日可回补、接口不可用时回测主路径仍离线可跑、manifest 记录抓取批次和失败项、质量报告输出缺失/失败统计。不得创建测试策略、HLD、Story 或代码。

## meta-se 补充任务：只读 HLD 输入约束

请 `meta-se` 只提出后续 HLD 必须考虑的输入约束，不生成 HLD、ADR、Story 或开发计划。

可直接转发给 `meta-se` 的任务说明：

> 当前仍在 `requirement-clarification`，需求未确认。请只读 `process/USE-CASES.md`、`process/REQUIREMENTS.md`、`process/CLARIFICATION-LOG.md` 和本 handoff，列出后续 HLD 必须显式处理的数据链路约束：数据准备层与回测引擎物理隔离；回测引擎不得直接联网；raw 缓存、标准化 parquet、manifest、质量报告四类产物边界；限速/节流/退避/断点续传配置归属；数据源不可用时的降级策略；增量更新和最近 N 交易日回补的配置点；manifest schema 和质量报告 schema 应成为 HLD 输入。不得设计架构方案，不得创建 HLD/ADR/Story。

## 输出约束

- 保持需求阶段状态为 draft，不能把 `confirmed` 或 `ready_for_design` 改为 true。
- 不创建 HLD、ADR、Story 或开发计划。
- 不删除 v1.0/v1.1/v1.2 的历史修订记录；只能追加下一版本修订记录。
- 不创建 CR；理由是需求尚未人工确认，尚无已确认基线被变更。
- 刷新完成后交回 `meta-po`，由 `meta-po` 复核并重新刷新 `checkpoints/REQUIREMENTS-CHECKPOINT.md` 为等待用户确认。

## 完成判定

- `process/USE-CASES.md`、`process/REQUIREMENTS.md` 和 `process/CLARIFICATION-LOG.md` 已增量升版，修订记录完整。
- 数据源限速、请求节流、重试退避、断点续传、raw 缓存、增量更新、最近 N 交易日回补、失败降级、离线回测主路径、manifest 批次记录和质量报告缺失/失败统计均可从文档中追溯。
- `process/STATE.md` 仍停留在 `requirement-clarification`。
- 刷新后 `meta-po` 重新发起需求确认检查点，不推进 `solution-design`。
