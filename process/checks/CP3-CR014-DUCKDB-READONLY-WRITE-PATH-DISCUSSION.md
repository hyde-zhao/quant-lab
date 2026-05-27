---
checkpoint_id: "CP3"
checkpoint_name: "CR-014 DuckDB 只读与数据写入路径方案讨论"
type: "auto_precheck"
status: "PASS"
owner: "meta-se"
created_at: "2026-05-26T23:18:00+08:00"
checked_at: "2026-05-26T23:18:00+08:00"
target:
  phase: "solution-design"
  story_id: ""
  artifacts:
    - "process/HLD-DATA-LAKE.md"
    - "process/HLD.md"
    - "process/ARCHITECTURE-DECISION.md"
manual_checkpoint: "checkpoints/CP3-CR014-A-SHARE-SINCE-INCEPTION-DATA-LAKE-HLD-REVIEW-R2.md"
---

# CP3 CR-014 DuckDB 只读与数据写入路径方案讨论

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| CP3 R1 人工反馈存在 | PASS | 用户反馈：“duckdb作为只读，那么数据在什么时候写入” | 需要补清 DuckDB 只读与 lake 写入链路的关系 |
| CP2 需求基线已确认 | PASS | `checkpoints/CP2-CR014-REQUIREMENTS-BASELINE.md` | `REQ-088..REQ-097` 继续作为设计输入 |
| 本轮仍处于 solution-design | PASS | `process/STATE.md` current phase 为 `solution-design`；用户明确禁止 Story Plan / LLD / 实现 | 本讨论只修订 HLD / ADR / CP3 自动预检 |

## 讨论问题

| 问题 | 讨论结论 | 落盘位置 |
|---|---|---|
| DuckDB 只读时，数据到底什么时候写入 | CP3 不写；CP5 + 用户显式授权后，lake production pipeline 才按 `plan -> run -> normalize/replay -> validate -> publish` 分阶段写入 | `process/HLD-DATA-LAKE.md` §17.7.1；ADR-052 |
| 谁负责写入 | Provider Adapter / Run Gate 写 `raw`、`manifest`、run metadata；Normalize / Replay 写 `canonical` / `gold` / `quality` candidate；Quality Gate 写 readiness / parity / audit evidence；Explicit Publish Gate 更新 catalog current pointer | `process/HLD-DATA-LAKE.md` §17.7.1 |
| 哪些阶段只生成 candidate | normalize、replay、validate、parity audit 均只生成 candidate 或 evidence，不更新 current pointer | `process/HLD-DATA-LAKE.md` §17.7.1；ADR-052 |
| DuckDB 什么时候读取 | publish 后读取 catalog current pointer 指向的 Parquet；validate/parity 阶段可在受控 candidate audit 中只读 candidate path | `process/HLD-DATA-LAKE.md` §17.7.1；`process/HLD.md` §30.3 |
| DuckDB 哪些输出不能成为事实源 | DuckDB query、view、parity report、feature result、audit report 均不得反向更新 catalog，不触发 publish，不替代 manifest/catalog source of truth | ADR-049、ADR-052 |

## 多视角评估

| 视角 | 关注点 | 评估 | 结论 |
|---|---|---|---|
| 架构可行性 | source of truth 是否清晰，写入和读取是否解耦 | Parquet lake + manifest/catalog 保持事实源；DuckDB 只读消费，避免 native DB 写入并发和事实源漂移 | 可行，继续推荐 CR14-A |
| 实现可行性 | 后续 Story 是否能拆出清晰职责 | 写入链路可按 Run Gate、Normalize/Replay、Validate、Publish Gate 拆分；DuckDB spike 可独立评估 parity | 可行，但必须在 CP4/CP5 后拆 Story |
| 易用性 | 用户如何理解“只读 DuckDB”和“数据写入” | 用户路径可表述为先写 lake、validate 产 candidate、publish 后 reader/DuckDB 读取 current truth | 易解释，需在后续 runbook 中保留状态词 |
| 扩展性 | 后续是否支持更大范围审计和查询 | Parquet 分区保持跨工具兼容；DuckDB 可扩展到 coverage audit、PIT join、feature extraction | 扩展性高，持久 `.duckdb` / DuckLake 另起 ADR |
| 安全与权限 | 是否会绕过授权写湖或读取凭据 | CP3/CP5 前真实写入为 0；真实 run 必须 CP5 + 用户显式授权；DuckDB 不读取凭据、不触发 provider | 权限边界可控 |

## 推荐结论

继续推荐 `CR14-A：Parquet lake + manifest/catalog source of truth + DuckDB 只读候选层`。

理由：

1. 数据写入路径清晰：写入由 lake production pipeline 单写者链路负责，不由 DuckDB 负责。
2. current truth 边界清晰：validate / parity / candidate audit 都不自动发布，只有 Explicit Publish Gate 更新 catalog current pointer。
3. DuckDB 定位清晰：只读 published current truth 或受控 candidate path，用于 query、audit、PIT join、feature extraction 和 parity，不反向成为事实源。
4. 扩展路径稳妥：后续可添加 DuckDB 只读查询能力；若需要持久 `.duckdb` cache、DuckLake 或外部 catalog，必须另起 ADR / CR。

## Checklist

| # | 检查项 | 状态 | 证据 | 处理意见 |
|---|---|---|---|---|
| 1 | 用户反馈是否被显式回答 | PASS | `process/HLD-DATA-LAKE.md` §17.7.1；ADR-052 | 已回答何时写、谁写、写到哪、何时 publish |
| 2 | DuckDB 只读边界是否与写入链路不冲突 | PASS | ADR-049、ADR-052 | DuckDB 只读消费；lake pipeline 写入 |
| 3 | Candidate 与 current pointer 是否区分 | PASS | `process/HLD-DATA-LAKE.md` §17.7.1 | normalize/replay/validate/parity audit 只生成 candidate/evidence |
| 4 | 可行性、易用性、扩展性是否完成讨论 | PASS | 本文件“多视角评估” | 继续推荐 CR14-A |
| 5 | 是否越过 CP3 门控 | PASS | 未生成 Story Plan、LLD 或实现 | 交回 meta-po 发起 CP3 R2 |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| R2 设计修订完成 | PASS | `process/HLD-DATA-LAKE.md` v0.6、`process/HLD.md` v2.4、`process/ARCHITECTURE-DECISION.md` v1.6 | 可作为 CP3 R2 人工审查输入 |
| 无禁止范围修改 | PASS | 修改范围限于 HLD / ADR / CP3 checks | 未触碰 Story、代码、测试、依赖、reports、旧 data |
| 可交回 meta-po | PASS | 本文件与 CP3 一致性预检均 PASS | meta-po 可生成 CP3 R2 Decision Brief |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| 方案讨论记录 | `process/checks/CP3-CR014-DUCKDB-READONLY-WRITE-PATH-DISCUSSION.md` | PASS | 本文件 |
| HLD-DATA-LAKE R2 | `process/HLD-DATA-LAKE.md` | PASS | 新增 §17.7.1、§17.7.2 |
| 主 HLD R2 | `process/HLD.md` | PASS | 补强 §30.3 |
| ADR R2 | `process/ARCHITECTURE-DECISION.md` | PASS | 新增 ADR-052、AD-Q49 |

## 结论

- 结论：`PASS`
- 阻断项：无
- 豁免项：无
- 下一步：交由 meta-po 生成 CP3 R2 人工审查稿；CP3 R2 approve 前不得拆 Story、写 LLD 或实现。
