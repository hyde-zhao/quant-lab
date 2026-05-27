---
checkpoint_type: "requirements"
status: "confirmed"
created_at: "2026-05-13"
created_by: "meta-po"
updated_at: "2026-05-14"
updated_by: "meta-po"
confirmed_at: "2026-05-14"
confirmed_by: "user"
user_decision: "确认通过"
source_artifacts:
  - "process/USE-CASES.md"
  - "process/REQUIREMENTS.md"
  - "process/CLARIFICATION-LOG.md"
source_versions:
  use_cases: "1.3"
  requirements: "1.3"
review_round: 3
confirmation_required: false
refresh_handoff: "process/handoffs/META-PM-REQ-REFRESH-RATE-LIMIT-2026-05-14.md"
refresh_reason: "用户在需求确认前追加数据源限速、节流、退避、断点续传、raw 缓存、增量更新、最近 N 交易日回补、失败降级、manifest 和质量报告统计要求；meta-pm 已刷新正文至 v1.3。"
---

# 需求确认检查点

## 当前状态

用户已明确回复“确认通过”。`meta-po` 已将 `meta-pm` 刷新的需求阶段正文标记为确认：

- `process/USE-CASES.md` 已升至 v1.3，状态为 `confirmed`。
- `process/REQUIREMENTS.md` 已升至 v1.3，状态为 `confirmed`，`confirmed=true`，`ready_for_design=true`，`review_round=3`。
- `process/CLARIFICATION-LOG.md` 已追加 2026-05-14 数据源限速刷新摘要，更新 Q-001，并新增 Q-012 至 Q-019 作为 HLD 前确认项。

本检查点已从 `waiting_user_confirmation` 更新为 `confirmed`。Q-004 至 Q-019 已被用户接受按当前默认边界进入 HLD，由 `meta-se` 在 `solution-design` 阶段明确设计决策。当前只允许推进到 `solution-design` 并输出 HLD 草稿；不得进入 `story-planning`，不得创建 Story、LLD 或代码。

## 本轮复核结论

| 复核项 | 结论 | 依据 |
|---|---|---|
| `process/USE-CASES.md` 版本与状态 | 通过 | frontmatter 为 `status: confirmed`、`version: "1.3"`，已设置 `confirmed_by` / `confirmed_at` |
| `process/REQUIREMENTS.md` 版本与状态 | 通过 | frontmatter 为 `status: confirmed`、`confirmed: true`、`ready_for_design: true`、`version: "1.3"`、`review_round: 3` |
| `process/CLARIFICATION-LOG.md` 刷新范围 | 通过 | 已追加数据源限速需求刷新记录，Q-012 至 Q-019 均为 `REQUIRED_FOR_HLD` |
| v1.3 修订记录 | 通过 | USE-CASES 与 REQUIREMENTS 均新增 2026-05-14 / v1.3 修订记录，说明为需求确认前增量修订 |
| 修订需求编号 | 通过 | REQUIREMENTS 需求级变更记录列明 REQ-016、REQ-034 已在 v1.3 修订 |
| 新增需求编号 | 通过 | REQUIREMENTS 已新增 REQ-047 至 REQ-058 |
| 数据准备契约 | 通过 | 已新增数据准备产物契约、配置契约、manifest/checkpoint 要求和质量报告 schema |
| 风险、假设、里程碑 | 通过 | 已新增 RA-010 至 RA-012、A-010 至 A-012，并新增 M0 数据准备与缓存可追溯里程碑 |
| 不误推进设计 | 通过 | STATE 仅推进到 `solution-design`；HLD 前确认项已获准带入 HLD，但 Story/LLD/代码仍未启动 |

## v1.3 刷新摘要

本轮需求草稿新增或强化以下内容：

- 数据链路边界：数据准备/更新流程可联网；回测、参数扫描、候选筛选和本地差异分析主路径必须物理隔离，并且只读本地 parquet、manifest 和质量报告摘要。
- 数据源限速与节流：显式考虑 AKShare 等接口限速、字段变更、临时不可用和失败风险；支持 `request_interval_seconds`、`batch_size`、`max_concurrency`，默认保守串行抓取。
- 重试退避与断点续传：`max_retries` 必须有上限，`backoff_policy` 必须可记录；断点续传基于 manifest/checkpoint，不重复已成功批次，除非显式强制刷新或最近 N 个交易日回补。
- raw 缓存与标准化派生：成功批次必须保留 raw 缓存，标准化 parquet 必须可从 raw 派生。
- 增量更新与最近 N 个交易日回补：默认只补缺失日期或缺失 symbol/date；最近 N 个交易日回补必须基于交易日历而不是自然日。
- manifest/checkpoint：记录批次、数据源、接口名、请求参数、日期/股票范围、请求时间、成功项、失败项、错误信息、重试次数、退避记录、raw 缓存路径、标准化输出路径、覆盖范围和最终状态。
- 数据质量报告：记录覆盖区间、缺失统计、失败统计、失败 symbol/date、字段缺失、重复记录、异常价格、回补数量、最近成功更新时间和数据新鲜度。
- 失败降级：数据源不可用或数据准备部分失败时，若本地 parquet 覆盖区间和 schema 合规，回测、扫描和候选筛选继续离线运行，并披露数据新鲜度、失败项和风险。
- 后续真实性增强：新增数据字段时，必须同步扩展 raw 缓存、manifest、质量报告和离线回测读取契约。

## v1.3 需求变更摘录

| ID | 主题 | 用户确认时需关注的点 |
|---|---|---|
| REQ-047 | 数据源限速与失败风险 | 数据准备必须节流、有限重试，重试耗尽后记录失败项，不允许回测主路径直接补抓 |
| REQ-048 | 请求节流配置 | `request_interval_seconds`、`batch_size`、`max_concurrency` 可配置，默认保守串行 |
| REQ-049 | 节流可验证 | manifest 或日志必须证明相邻请求间隔满足配置 |
| REQ-050 | 有限重试退避 | `max_retries` 有上限，退避策略和每次重试时间可追踪 |
| REQ-051 | 断点续传 | 基于 manifest/checkpoint 跳过已成功批次，除强制刷新或回补窗口外不重复抓取 |
| REQ-052 | raw 缓存 | raw 缓存必须存在，标准化 parquet 必须可从 raw 再派生 |
| REQ-053 | 增量更新 | 默认只补缺失日期或缺失 symbol/date，不重复全量抓取 |
| REQ-054 | 最近 N 个交易日回补 | N 可配置，并基于交易日历而不是自然日 |
| REQ-055 | manifest/checkpoint | manifest 至少记录批次、数据源、接口、范围、请求时间、成功/失败项、错误、重试、退避、raw 路径、标准化输出路径、覆盖范围和最终状态 |
| REQ-056 | 数据质量报告 | 必须记录覆盖、缺失、失败、字段缺失、重复、异常价格、回补数量、最近成功更新时间和数据新鲜度 |
| REQ-057 | 数据源不可用降级 | 本地 parquet 合规时，回测/扫描/候选筛选继续离线运行并披露新鲜度和失败项 |
| REQ-058 | 后续增强链路契约 | 新增 PIT、交易状态、涨跌停或事件字段时，同步扩展 raw、manifest、质量报告和离线读取契约 |

## HLD 前必须确认的问题

以下问题来自 `process/CLARIFICATION-LOG.md`。用户已确认这些问题按当前默认边界进入 HLD；`meta-se` 必须在 HLD 中给出明确设计决策，不能绕过或延后到 Story 拆解。

| ID | 必须确认的问题 | 当前默认边界 | HLD 需要落实 |
|---|---|---|---|
| Q-004 | 默认复权口径采用前复权、后复权还是不复权？本地回测与聚宽候选验证是否必须使用同一口径？ | 需求只固化同一运行口径一致、不得混用、报告记录实际口径；默认值未指定 | 默认复权口径、配置项、报告字段 |
| Q-005 | 第一版成交假设采用 T+1 开盘、T+1 收盘、VWAP 近似，还是仅按收盘到收盘收益归属？ | 已固定 T 日收盘后信号、T+1 或之后成交；成交价口径未指定 | 成交价、成交日期、成本扣除、收益归属 |
| Q-006 | 股票池表达采用固定当前沪深 300 快照文件，还是需要日期维度或 PIT 接口占位？ | 第一版固定当前沪深 300 快照，标记 `is_pit_universe=false`，PIT provider 后续增强 | `index_members.parquet` schema、快照日期字段、PIT 扩展点 |
| Q-007 | 缺失价、停牌和无成交如何处理？ | 禁止静默填充；历史窗口不足和信号端点缺失剔除；成交价缺失或无成交的细分规则待定 | 数据加载、信号排名、组合成交三层处理表 |
| Q-008 | 第一版 parquet 最低字段是否强制包含 `available_at`、`adjustment_policy`、成交状态或成交量？ | 日线价格可在 HLD 批准后用收盘后可用规则推导 `available_at`；事件字段第一版不纳入 | 最小 schema、可选字段、缺字段失败行为 |
| Q-009 | 涨跌停字段是否第一版强制输入？ | 当前作为第一版可延后但必须警示的限制项，涨跌停约束为后续 P1 增强 | 是否进入第一版 schema，或仅进入 metadata 限制项 |
| Q-010 | 未来函数校验做到哪个层级？ | 所有参与决策字段必须满足 `available_at <= decision_time`；具体层级待定 | 校验边界、失败策略、测试样例 |
| Q-011 | 财报披露日和财报/公告事件是否明确列为第一版 Out of Scope？ | 当前默认第一版 Out of Scope；若纳入则必须提供事件级 `available_at` 并调整范围 | 是否保持 Out of Scope，避免设计阶段误引入事件数据 |
| Q-012 | 数据准备默认节流参数如何取值：`request_interval_seconds`、`batch_size`、`max_concurrency` 的默认值分别是多少？ | 三项均可配置，默认保守串行抓取；`max_concurrency` 建议默认 1，但默认值仍待确认 | 默认节流参数、配置位置、覆盖测试方式 |
| Q-013 | `max_retries` 默认上限和 `backoff_policy` 采用固定退避还是指数退避？退避细节记录到 manifest 还是日志？ | 重试必须有限、不可无限循环，退避过程必须可记录到 manifest 或日志 | 默认重试次数、退避算法、最大等待边界、记录字段 |
| Q-014 | 断点续传状态由 manifest、独立 checkpoint 文件还是二者共同承载？批次状态枚举如何定义？ | 断点续传基于 manifest/checkpoint，跳过已成功批次，除 `force_refresh` 或最近 N 交易日回补外不重复抓取 | checkpoint 载体、批次 ID、状态枚举、恢复算法 |
| Q-015 | 最近 N 个交易日回补的默认 N 取值是多少，是否对价格、复权因子、成分股和交易日历采用同一窗口？ | N 可配置，且必须基于交易日历而不是自然日 | 默认 N、适用数据类型、与增量缺口补齐的优先级 |
| Q-016 | raw 缓存保留策略是什么：长期保留、按批次滚动保留、按大小清理，还是由用户手动清理？ | raw 缓存必须存在，标准化 parquet 必须可从 raw 派生；保留周期和清理策略待确认 | raw 路径组织、命名、保留/清理策略、复现边界 |
| Q-017 | manifest schema 的文件格式、字段类型、路径、状态枚举和版本字段如何定义？ | 已列出 manifest 至少记录字段，但未锁定 JSON、JSONL、YAML 或 parquet 等格式 | manifest schema、兼容升级规则、与质量报告的关联方式 |
| Q-018 | 数据质量报告阈值如何定义：缺失率、失败率、重复记录、异常价格达到什么条件时阻塞数据准备或仅警告？ | 质量报告必须记录统计和异常定位；阻塞阈值与质量状态枚举待确认 | 质量阈值、`quality_status` 枚举、失败/警告策略、报告字段 |
| Q-019 | 数据源不可用时，本地缓存新鲜度如何披露：按自然日、交易日、最近成功批次还是覆盖区间缺口计算？ | 本地 parquet 合规时回测/扫描继续离线运行，并披露最近成功更新时间、数据新鲜度、失败批次和可能影响 | 新鲜度计算方式、报告展示字段、不可用数据源降级提示 |

## 人工确认结果

| 字段 | 值 |
|---|---|
| 用户回复 | 确认通过 |
| 确认范围 | 接受 `process/USE-CASES.md` v1.3、`process/REQUIREMENTS.md` v1.3，以及 Q-004 至 Q-019 按当前默认边界进入 HLD |
| 确认时间 | 2026-05-14 |
| 后续阶段 | `solution-design` |

## 后续动作

`meta-po` 已执行以下动作：

- 将 `process/USE-CASES.md` 标记为 confirmed。
- 将 `process/REQUIREMENTS.md` 标记为 `confirmed: true` 与 `ready_for_design: true`。
- 回写 `process/STATE.md`，将 `requirement_confirmed` 置为 `true` 并推进到 `solution-design`。
- 创建 `process/handoffs/META-SE-HLD-2026-05-14.md`，交接给 `meta-se` 输出 HLD 设计，不创建 Story 或实现产物。
