---
discussion_id: "CP3-CR018-HLD-DISCUSSION"
change_id: "CR-018"
phase: "solution-design"
status: "recorded"
owner: "meta-po"
created_at: "2026-05-29T07:22:03+08:00"
source:
  - "checkpoints/CP2-CR018-PRODUCTION-DATA-LAKE-CLOSURE-DECISION-BRIEF.md"
  - "process/HLD-DATA-LAKE.md#19"
  - "process/HLD.md#32"
  - "process/ARCHITECTURE-DECISION.md#ADR-062"
---

# CP3 CR018 HLD Discussion Log

## 背景

用户已在 CP2 批准 D1-D6 推荐方案：数据湖 production current truth 优先、CR018 承接 CR014 S14 candidate、candidate 不直接 publish、真实抓取窗口化、QMT 后置、publish 后研究重跑。CP3 讨论不重复打开 D1-D6，而是检查 HLD / ADR / Story Plan 是否正确落实这些决策。

## Architecture Gray Areas

| 灰区 ID | 问题 | 处理结果 | 证据 |
|---|---|---|---|
| AGA-CR018-01 | release scope 是 scoped release、since-inception 还是 2026 YTD | 采用 CP2 D1：`2015-01-05..latest_closed_trade_date` scoped release，2015 前 blocked/future backfill | `process/HLD-DATA-LAKE.md#19.3`、ADR-062 |
| AGA-CR018-02 | P0/P1 dataset group 如何划分 | 采用 CP2 D2-D4：P0 核心生产组，P1 行业 / 市值 / 流动性阻断对应声明 | `process/HLD-DATA-LAKE.md#19.3`、ADR-063 |
| AGA-CR018-03 | publish 粒度和 rollback 单位 | 采用 CP2 D5：release-level 总门 + dataset-level 明细，rollback 以 release 为单位 | `process/HLD-DATA-LAKE.md#19.3`、ADR-065 |
| AGA-CR018-04 | 研究重跑与 QMT 后置关系 | 采用 CP2 D6：publish + production research rerun PASS 后才申请 QMT stage gate | `process/HLD.md#32`、ADR-066 |

## Advisor Table 摘要

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| CR18-A：scoped production release + P0 core group + release-level publish/rollback + rerun-before-QMT | 复用 CR014 S14 candidate；PIT/W3/benchmark 不缺席；rollback 一致；QMT 不提前消费不稳定研究结论 | Story 数量较多；provider 限流和质量门较重；QMT simulation 推迟 | 数据湖 production、research rerun、QMT stage gate、文档声明 | 推荐 | CP2 已批准 D1-D6；若用户要求 2015 前完整历史或 QMT 技术 smoke 先行，需另起 CR 或切换备选 |
| CR18-B：core-only 快速 publish | 最快形成 current pointer | PIT/W3/benchmark 缺失，严肃研究和 QMT admission 仍 blocked | catalog、reader、研究声明 | 不推荐，降级备选 | provider 权限不足且用户只需要 candidate reader 时切换 |
| CR18-C：data-rich 全量 P0 | 研究解释最完整 | 周期长、接口风险高、publish 延迟 | 数据回补、研究、QMT scale_up | 条件推荐 | 用户近期要求行业中性、纯 alpha、容量或 scale_up 声明时切换 |
| CR18-D：QMT technical simulation 先行 | 可早测 Windows/QMT 技术链路 | 容易误读为策略可运行；违反当前 D6 优先级 | QMT / 安全 / runbook | 不推荐，治理备选 | 仅在用户明确要求无策略含义 adapter smoke 且另行授权时作为独立 Spike |

## 结论

推荐进入 CP3 人工审查：接受 CR18-A HLD / ADR 增量、接受 CR018-S01..S09 Story Plan 作为后续 LLD 输入、继续保持本阶段无真实抓取 / 写湖 / publish / QMT 授权。
