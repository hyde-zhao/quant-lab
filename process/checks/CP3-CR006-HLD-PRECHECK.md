---
checkpoint_id: "CP3"
checkpoint_name: "CR-006 HLD 架构一致性预检"
type: "auto_precheck"
status: "PASS"
owner: "meta-se"
created_at: "2026-05-18T21:30:00+08:00"
checked_at: "2026-05-18T22:10:00+08:00"
target:
  phase: "solution-design"
  story_id: ""
  artifacts:
    - "process/HLD.md"
    - "process/ARCHITECTURE-DECISION.md"
    - "process/changes/CR-006-LEGACY-DATA-DIRECTORY-EXTERNALIZATION-2026-05-18.md"
manual_checkpoint: "checkpoints/CP3-CR006-HLD-REVIEW.md"
---

# CP3 CR-006 HLD 架构一致性预检

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| CR-006 CP3 前修改意见已明确 | PASS | 用户明确“旧的data数据不删除也先放弃，建立一套从Tushare获取的数据的方案” | 允许在 CP3 人工确认前修订 HLD/ADR/Story Plan。 |
| HLD 草案已重写 CR-006 | PASS | `process/HLD.md` §23 | §23 已从 legacy 外置化改为 Tushare-first 数据方案。 |
| ADR 草案已重写 CR-006 | PASS | `process/ARCHITECTURE-DECISION.md` ADR-018 | ADR-018 已改为 Tushare structured lake 事实源、raw/manifest 审计层、运行时消费面分离。 |
| 安全边界已声明 | PASS | HLD §23.1/§23.8/§23.13；ADR-018 | 本轮不读取、列出、迁移、复制或删除真实 `data/**`；不读取或记录 `.env` / token / NAS 凭据。 |

## Checklist

| # | 检查项 | 状态 | 证据 | 处理意见 |
|---|---|---|---|---|
| 1 | 问题定义覆盖目标、成功标准、约束、非目标和假设 | PASS | HLD §23.1 | 明确旧 `data/` 来源不明、Tushare 不承诺完全覆盖旧数据、新链路采用 Tushare-first。 |
| 2 | 至少 2 个候选方案完成比较 | PASS | HLD §23.2 | CR6-A/B/C/D 四个方案覆盖 Tushare-first、旧数据 fallback、raw/manifest runtime、旧数据覆盖比对。 |
| 3 | 推荐方案与模块边界清晰 | PASS | HLD §23.3、§23.4 | Acquisition、normalization/quality/catalog、lightweight adapter、Backtrader feed、old data guardrail 职责分离。 |
| 4 | raw / manifest 评估明确 | PASS | HLD §23.4；ADR-018 | 结论为“需要 raw/manifest，但只属于采集审计、复现、质量追溯和 replay；不是回测运行时依赖”。 |
| 5 | 轻量回测输入契约明确 | PASS | HLD §23.4、§23.6、§23.7 | 当前轻量框架应消费 canonical/gold 或由其派生的 external `legacy_flat`，不得默认 fallback repo `data/`。 |
| 6 | Backtrader 输入契约明确 | PASS | HLD §23.6、§23.8；ADR-016/017/018 | Backtrader 只消费 quality gate 后 clean OHLCV/factor/score feed，不读 raw/manifest/token/connector。 |
| 7 | structured lake 与 legacy flat 关系明确 | PASS | HLD §23.4 | Tushare structured lake 是事实源；external `legacy_flat` 仅为派生兼容面；旧 repo `data/` reference-only。 |
| 8 | 集成契约显式 | PASS | HLD §23.6 | 覆盖调用方向、调用时机、输入、输出、错误/降级和调用方同步修改范围。 |
| 9 | 数据流和架构图清晰 | PASS | HLD §23.5、§23.7 | Mermaid 图覆盖 User / Application / Service / Data / Infrastructure；流程从 Tushare plan 到 old data reference-only。 |
| 10 | NFR、风险和 Gotchas 已覆盖 | PASS | HLD §23.9、§23.10、§23.13 | 覆盖安全、复现、离线性、兼容、Tushare 覆盖误解、raw/manifest 误用、旧 data fallback 误用。 |
| 11 | ADR 完整且回写 HLD | PASS | ADR-018；HLD §23.11 | ADR-018 的事实源、raw/manifest、轻量 engine、Backtrader 和旧 data 决策均回写 HLD 与 Story。 |
| 12 | 未越过实现边界 | PASS | 本轮修改文件清单 | 未修改 `engine/**`、`experiments/**`、`config/**`、README、docs、tests、`market_data/**`、真实数据或凭据。 |
| 13 | 待确认问题状态化 | PASS | HLD §23.14 | CR6-Q1..Q4 均标注 OPEN、影响和决策人。 |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| CP3 自动预检可进入人工审查 | PASS | 本文件 | 无未豁免 FAIL。 |
| 人工审查稿需重新发起 | PASS | `checkpoints/CP3-CR006-HLD-REVIEW.md` | 原 CP3 人工稿尚未 approved；meta-po 应基于本预检重发或更新人工确认。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| HLD 增量 | `process/HLD.md` | PASS | §23 已重写为 Tushare-first 数据方案。 |
| ADR 增量 | `process/ARCHITECTURE-DECISION.md` | PASS | ADR-018 已重写。 |
| CP3 自动预检 | `process/checks/CP3-CR006-HLD-PRECHECK.md` | PASS | 本文件。 |

## 结论

- 结论：`PASS`
- 阻断项：无。
- REQUIRED：CP3 人工确认通过前，不得进入 CR006-BATCH-A LLD；旧 `data/**` 读取/比对/迁移/删除仍需用户另行授权，不属于本 CP3 放行范围。
- 下一步：CP3 可由 meta-po 重新发起人工确认；确认对象应为本次 Tushare-first 修订稿，而不是旧 legacy 外置化方案。
