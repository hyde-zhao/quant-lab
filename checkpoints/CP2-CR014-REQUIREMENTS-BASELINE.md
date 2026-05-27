---
checkpoint_id: "CP2"
checkpoint_name: "CR-014 需求基线人工审查"
type: "auto_then_manual"
status: "approved"
owner: "meta-po"
created_at: "2026-05-26T22:36:57+08:00"
reviewed_by: "user"
reviewed_at: "2026-05-26T22:51:23+08:00"
auto_check_result: "process/checks/CP2-CR014-REQUIREMENTS-BASELINE.md"
target:
  phase: "requirement-clarification"
  story_id: ""
  artifacts:
    - "process/USE-CASES.md"
    - "process/REQUIREMENTS.md"
    - "process/CLARIFICATION-LOG.md"
    - "process/checks/CP1-CR014-USE-CASE-COMPLETENESS.md"
    - "process/checks/CP2-CR014-REQUIREMENTS-BASELINE.md"
---

# CP2 CR-014 需求基线人工审查

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---|---|
| `process/checks/CP1-CR014-USE-CASE-COMPLETENESS.md` | PASS | 0 | UC-09、SM-14..SM-18、TS-014-01..TS-014-07 已形成场景基线 |
| `process/checks/CP2-CR014-REQUIREMENTS-BASELINE.md` | PASS | 0 | REQ-088..REQ-097 已形成需求基线草案；本结果不替代人工确认 |

## Decision Brief

| 字段 | 内容 |
|---|---|
| 推荐决策 | `approve`：接受 CR-014 需求基线，按默认假设进入 HLD / ADR / Story Plan 设计；CP3 前仍不得拆 LLD，CP5 前仍不得实现 |
| 备选方案 | `修改: <具体修改点>`：调整全 A 覆盖边界、P0 dataset 清单、当前交易日口径、DuckDB 定位或真实执行授权边界后重跑 CP1 / CP2；`reject`：停止 CR-014 推进并保持 CR-010/012/013 旧基线 |
| 影响维度 | 用户价值：把数据湖目标从 limited-window / roadmap-only 升级为全 A since-inception production current truth；实现复杂度：高，后续需要 HLD、ADR、Story、LLD、CP5 和分 Wave 实现；可验证性：新增 TS-014-01..07；维护成本：新增 catalog current pointer、lifecycle、replay 和 claim boundary 长期治理；平台兼容：Python / uv 规则不变，DuckDB 仅候选；安全 / 权限：默认 provider/lake/credential/legacy data/old report/dependency 操作均为 0；交付影响：后续 README / USER-MANUAL / TEST-STRATEGY 需要刷新 |
| 优劣分析 | 推荐方案优势是完整匹配用户“自存在日起至今”的目标，并保留旧 limited-window / blocked 证据；代价是不能直接实现，必须经过 CP3/CP5。修改方案适合改变 universe、P0 dataset 或 DuckDB 定位。拒绝方案成本最低，但继续保留全历史 production current truth 缺口 |
| 风险与回退 | 风险等级：高。接受条件：本次批准只覆盖需求基线和默认假设，不授权真实 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 操作、旧 reports 覆盖或 DuckDB 依赖修改。若后续发现设计不可行，回退到 `requirement-clarification` 并修订 CR-014 需求基线 |
| 用户需决策事项 | Q-020：全 A 覆盖边界；Q-021：P0 dataset 清单与 lifecycle/code-change 是否 P0；Q-022：“当前交易日”是否采用最近已闭市交易日；Q-023：DuckDB 是否仅为只读候选且依赖引入等 CP3/CP5；Q-024：真实 provider/lake/credential/old data/old report 操作是否均需单独授权 |

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| CR-014 已获批准进入 standard 变更流程 | 通过 | `process/changes/CR-014-A-SHARE-SINCE-INCEPTION-PRODUCTION-DATA-LAKE-2026-05-26.md`；`approval_result=approved` | 用户选择 `approve` |
| meta-pm 需求澄清完成并有调度证据 | 通过 | `process/handoffs/META-PM-CR014-REQ-CLARIFICATION-2026-05-26.md` | 用户选择 `approve` |
| CP1 自动检查通过 | 通过 | `process/checks/CP1-CR014-USE-CASE-COMPLETENESS.md` | 用户选择 `approve` |
| CP2 自动预检通过 | 通过 | `process/checks/CP2-CR014-REQUIREMENTS-BASELINE.md` | 用户选择 `approve` |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 是否接受 CR-014 的目标为 A 股证券自存在 / 上市日起至当前交易日的 production current truth，而不是固定 2020-2024 或 limited-window pass | 通过 | `REQ-088`、`UC-09`、`SM-14` | 用户选择 `approve` |
| 2 | 是否接受全 A universe 默认包含沪深北全部 A 股、科创板、创业板、北交所、退市 / 摘牌证券和历史代码变更，缺口进入 `required_missing` / `blocked_claims` | 通过 | `Q-020`、`REQ-088`、`REQ-089` | 用户选择 `approve` |
| 3 | 是否接受 P0 dataset 默认沿用 `prices`、`adj_factor`、`hs300_index`、`trade_calendar`、`index_members`、`index_weights`、`stock_basic`，并把 lifecycle / code-change 作为全 A current truth 必需能力 | 通过 | `Q-021`、`REQ-090`、`A-022` | 用户选择 `approve` |
| 4 | 是否接受“当前交易日”默认定义为最近已闭市且交易日历 `is_open=true` 的交易日，盘中或未闭市数据不进入 production current truth | 通过 | `Q-022`、`REQ-097`、`A-021` | 用户选择 `approve` |
| 5 | 是否接受 raw / manifest / canonical / gold / quality / catalog 分层，以及 validate pass 不自动更新 catalog current pointer | 通过 | `REQ-090`、`REQ-091`、`TS-014-03` | 用户选择 `approve` |
| 6 | 是否接受增量刷新 / 最近 N 个交易日回补 / replay 的边界：replay 不触发 provider、不读凭据、不污染 current pointer | 通过 | `REQ-092`、`TS-014-04` | 用户选择 `approve` |
| 7 | 是否接受 DuckDB 仅作为 HLD 待决策的 read-only query / audit / feature extraction 候选；未经 CP3/CP5 不改 `pyproject.toml` / `uv.lock`，不写 `.duckdb` 事实源 | 通过 | `Q-023`、`REQ-093`、`SM-18` | 用户选择 `approve` |
| 8 | 是否接受后续真实 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 操作和旧 reports 覆盖均需单独授权 | 通过 | `Q-024`、`REQ-094`、`A-025` | 用户选择 `approve` |
| 9 | 是否接受 allowed_claims / blocked_claims / required_missing 作为声明边界，阻止 CR-010/012/013 旧基线被外推为全 A 全历史 production current truth | 通过 | `REQ-095`、`TS-014-07` | 用户选择 `approve` |
| 10 | 是否接受 TS-014-01 至 TS-014-07 作为后续测试策略和 CP7 验证矩阵的输入 | 通过 | `REQ-096`、`USE-CASES.md` CR-014 验证场景矩阵 | 用户选择 `approve` |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| CR-014 需求基线可作为 HLD 输入 | 通过 | `process/REQUIREMENTS.md` v1.7，REQ-088..REQ-097 | 用户选择 `approve` |
| CR-014 场景基线可作为 HLD 输入 | 通过 | `process/USE-CASES.md` v1.6，UC-09 / TS-014 | 用户选择 `approve` |
| Q-020 至 Q-024 的默认假设被接受或明确修改 | 通过 | `process/CLARIFICATION-LOG.md` | 用户选择 `approve`；默认假设 A-021..A-025 生效 |
| 安全与权限边界被用户接受 | 通过 | `REQ-094`、`A-025` | 用户选择 `approve` |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| 场景基线草案 | `process/USE-CASES.md` | 通过 | v1.6，新增 UC-09、SM-14..SM-18、TS-014-01..07；用户选择 `approve` |
| 需求基线草案 | `process/REQUIREMENTS.md` | 通过 | v1.7，新增 REQ-088..REQ-097；用户选择 `approve` |
| 澄清日志 | `process/CLARIFICATION-LOG.md` | 通过 | Q-020..Q-024、A-021..A-025；用户选择 `approve` |
| CP1 自动检查 | `process/checks/CP1-CR014-USE-CASE-COMPLETENESS.md` | 通过 | PASS；用户选择 `approve` |
| CP2 自动预检 | `process/checks/CP2-CR014-REQUIREMENTS-BASELINE.md` | 通过 | PASS；用户选择 `approve` |

## 人工审查结果

- 结论：`approved`
- 审查人：user
- 审查时间：2026-05-26T22:51:23+08:00
- 原始审批文本：`approve`（UI 选择：`approve (Recommended)`）
- 修改意见：无
- 风险接受项：
  - 本次批准只覆盖 CR-014 场景 / 需求基线。
  - CP3 人工确认前不得进入 Story / LLD。
  - CP5 批次人工确认前不得实现任何 CR014 Story。
  - 不授权 provider fetch、真实 lake 写入、凭据读取。
  - 不授权读取、列出、迁移、复制、比对或删除旧 `data/**`。
  - 不授权覆盖或重写旧 reports。
  - 不授权修改 `pyproject.toml` / `uv.lock` 引入 DuckDB。
