---
checkpoint_id: "CP2"
checkpoint_name: "CR018 Production Data Lake Closure Requirements Baseline"
type: "auto_then_manual"
status: "approved"
owner: "meta-po"
created_at: "2026-05-29T06:48:42+08:00"
reviewed_by: "user"
reviewed_at: "2026-05-29T06:48:42+08:00"
auto_check_result: "process/checks/CP2-CR018-REQUIREMENTS-BASELINE.md"
target:
  phase: "requirement-clarification"
  story_id: ""
  artifacts:
    - "process/USE-CASES.md"
    - "process/REQUIREMENTS.md"
    - "process/changes/CR-018-PRODUCTION-DATA-LAKE-CLOSURE-2026-05-29.md"
---

# CP2 CR018 Production Data Lake Closure 需求基线人工审查

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---|---|
| `process/checks/CP1-CR018-USE-CASE-COMPLETENESS.md` | PASS | 0 | 已新增 UC-13、UC-14 和 TS-018-01 至 TS-018-06。 |
| `process/checks/CP2-CR018-REQUIREMENTS-BASELINE.md` | PASS | 0 | 已新增 REQ-123 至 REQ-137，覆盖 D1-D6。 |

## Decision Brief

### 待人工决策清单

| 决策 ID | 待确认问题 | 推荐方案 | 备选方案 | 优劣分析 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|
| D1 | CR018 第一版 production current truth 时间范围如何定义。背景：CR014 S14 已拉取 2015-01-05..2026-05-28 `prices` / `adj_factor` candidate，但 since-inception 到 2015 前仍可能需要更复杂历史源。 | 先发布 `2015-01-05..latest_closed_trade_date` scoped release，2015 前列为 blocked/future backfill。 | A. since-inception 一次性关闭；B. 只发布 2026 YTD。 | 推荐方案优势是能用已验证的 S14 candidate 快速进入生产闭环，同时如实保留 2015 前缺口；代价是不能声明 2015 前全历史。备选 A 最完整但周期长、provider 风险高；备选 B 风险低但研究价值不足。 | 用户价值：高；复杂度：中高；可验证性：高；风险：范围声明必须严格。 | 若用户要求完整上市以来声明，切换到备选 A 并新增历史源 Spike；若 publish 风险过高，切换到备选 B。 |
| D2 | CR018 P0 dataset denominator 应包含哪些数据。背景：只发布 `prices` / `adj_factor` 会留下 PIT/W3/benchmark 缺口。 | P0 包含 prices_raw、adj_factor、qfq/hfq/returns_adjusted、trade_calendar、PIT universe/lifecycle/code-change、trade_status、prices_limit/ST/suspend、四类 benchmark 行情/成分/权重。 | A. core only：prices_raw + adj_factor + trade_calendar；B. data-rich：把行业/市值/流动性也升为 P0。 | 推荐方案能支撑真实 benchmark、PIT 和可交易性，适合作为生产 current truth 核心；代价是 Story 和抓取量较大。备选 A 上线快但不能严肃研究；备选 B 研究解释更强但会拖慢 publish。 | 用户价值：高；复杂度：高；可验证性：高；风险：provider 限流和字段稳定性。 | 若 provider 权限不足，降级为 core only 并保留 blocked claims；若用户要求行业中性/容量声明，升为 data-rich。 |
| D3 | benchmark 范围是只补 HS300 还是一次性纳入宽基指数。背景：用户后续需要真实超额、指数增强和大小盘暴露判断。 | 同时纳入 HS300、ZZ500、ZZ1000 和中证全指行情、历史成分、权重。 | A. 先只做 HS300；B. 先做行情不做成分/权重。 | 推荐方案能支持真实 benchmark、风格暴露和指数增强前置判断；代价是数据面更大。备选 A 简单但无法解释低波是否只是小盘/宽基暴露；备选 B 能算指数收益但不能做 PIT 成分或权重分析。 | 用户价值：高；复杂度：中高；维护：中；风险：指数权重接口可用性。 | 若接口不可用，先保留行情，成分/权重进入 required_missing；若只做沪深300策略，可临时切备选 A。 |
| D4 | 行业、市值、风格、流动性和容量数据列 P0 还是 P1。背景：这些数据对纯 alpha、行业中性、容量和资金放大很关键，但不是 current truth 最小发布必需。 | 列 P1，但作为中性化、纯 alpha、容量、scale_up 和资金放大声明的前置。 | A. 全部升 P0；B. 全部延后且不阻断任何声明。 | 推荐方案平衡生产发布速度和声明边界：核心 current truth 可先闭环，但不允许过度声明。备选 A 更严谨但明显延迟数据湖 publish；备选 B 快但会制造研究解释风险。 | 用户价值：中高；复杂度：中；风险：P1 被误读为不重要。 | 若用户要行业中性 / 容量 / scale_up 作为近期目标，切换到备选 A；若只做探索报告，可保留 P1 blocked claims。 |
| D5 | publish 粒度和 rollback 单位如何设计。背景：多 dataset 独立 publish 容易让 current truth 不一致。 | release-level 总门 + dataset-level 明细；current pointer 和 rollback 以 release 为单位。 | A. dataset 独立 publish / rollback；B. 不 publish，只保留 candidate reader。 | 推荐方案保证跨 dataset 一致、可审计和可回滚；代价是 release gate 较重。备选 A 灵活但一致性和回滚复杂；备选 B 风险最低但无法进入 production current truth。 | 用户价值：高；维护：中；安全：高；风险：release gate 需要严格字段和 smoke。 | 若某个 dataset 更新频率差异很大，可在 HLD 中设计子 release 但仍由总门协调；若质量不足，退回 candidate reader。 |
| D6 | QMT simulation 何时解禁。背景：CR015/016/017 foundation 已完成离线受控成果，但用户当前最高优先级是数据湖生产级。 | simulation / live_readonly / small_live / scale_up 全部等数据湖 publish + production research rerun PASS 后再申请解禁。 | A. 技术 simulation 先行，live/small/scale 后置；B. 仅 live/small/scale 后置，simulation 不受数据湖约束。 | 推荐方案避免把 proxy/fixed-snapshot 下成立的策略接入交易链路；代价是 QMT simulation 推迟。备选 A 能早测技术链路但容易让用户误读策略已可运行；备选 B 速度最快但治理风险最高。 | 用户价值：高；安全：高；复杂度：中；风险：延迟 QMT 实盘前准备。 | 若用户只想做无策略含义的 adapter 技术 smoke，可另开明确授权的技术 Spike；任何策略型 simulation 仍需 publish + rerun。 |

| 字段 | 内容 |
|---|---|
| 推荐决策 | `approve`：接受 D1-D6 全部推荐方案，先闭环数据湖 production current truth，再申请 QMT simulation。 |
| 备选方案 | 见 D1-D6 各行，均至少包含 2 个可执行备选。 |
| 影响维度 | 用户价值、实现复杂度、可验证性、维护成本、平台兼容、安全 / 权限、交付影响。 |
| 优劣分析 | 推荐方案优先保持生产 current truth、publish/rollback 和 QMT 后置边界；备选方案主要在速度、范围完整度和治理风险之间取舍。 |
| 风险与回退 | 真实 provider fetch / lake write / publish / QMT operation 均未在 CP2 授权；后续必须走 CP3/CP4/CP5 和单次真实运行授权。 |
| 用户需决策事项 | D1、D2、D3、D4、D5、D6。用户已在当前对话批准全部推荐方案。 |

### CP2 追加 Decision Brief 字段

| 字段 | 内容 |
|---|---|
| 用户真实意图 | 用户将最高优先级调整为数据湖 production current truth，QMT simulation 放在数据湖 publish + 研究重跑通过之后。 |
| 场景覆盖 | `UC-13` 覆盖 candidate -> readiness -> publish -> rollback；`UC-14` 覆盖 publish 后研究重跑与 QMT 后置。 |
| 认知盲区补充 | candidate / validate PASS / parity PASS 不等于 published current truth；P1 行业市值流动性缺失不阻断核心 publish，但阻断中性化、纯 alpha、容量和 scale_up 声明。 |
| Scenario Gray Areas 处理结果 | 用户直接批准 D1-D6；本轮未另建异步讨论日志，CP2 自动检查记录为 N/A。 |
| Deferred Ideas | 2015 前 since-inception backfill、行业市值流动性升 P0、QMT 技术 simulation 先行 Spike 均延后到后续决策。 |
| 用户选择影响 | 进入 CR018 solution-design；QMT simulation/live_readonly/small_live/scale_up 在 publish + research rerun PASS 前保持 blocked。 |
| 回退方式 | 若 CP3 发现架构不可行，回退到 requirement-clarification 调整 P0/P1、publish 粒度或 QMT 后置策略。 |
| discussion log / checkpoint | N/A：当前对话中的 D1-D6 批准为 CP2 人工决策证据。 |

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| CP1 自动检查通过 | 通过 | `process/checks/CP1-CR018-USE-CASE-COMPLETENESS.md` | 场景完整。 |
| CP2 自动预检通过 | 通过 | `process/checks/CP2-CR018-REQUIREMENTS-BASELINE.md` | 需求完整。 |
| 待决策项均有推荐、备选和优劣分析 | 通过 | 本文件 D1-D6 | 满足项目规则。 |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 是否接受 D1 时间范围推荐方案 | 通过 | 用户批准 D1-D6 | 接受 scoped release。 |
| 2 | 是否接受 D2 P0 dataset denominator 推荐方案 | 通过 | 用户批准 D1-D6 | 接受核心 P0 group。 |
| 3 | 是否接受 D3 benchmark 范围推荐方案 | 通过 | 用户批准 D1-D6 | 接受四类宽基 benchmark。 |
| 4 | 是否接受 D4 行业 / 市值 / 流动性 P1 声明边界 | 通过 | 用户批准 D1-D6 | 接受 P1 + blocked claims。 |
| 5 | 是否接受 D5 release-level publish / rollback | 通过 | 用户批准 D1-D6 | 接受 release-level 总门。 |
| 6 | 是否接受 D6 QMT 全阶段后置 | 通过 | 用户批准 D1-D6 | 接受 publish + rerun PASS 后再申请解禁。 |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| 需求基线已确认 | 通过 | `process/REQUIREMENTS.md` v1.9 | 可进入 HLD。 |
| 人工决策项已关闭 | 通过 | D1-D6 | 无剩余 CP2 阻断决策。 |
| 安全边界未越权 | 通过 | CR018、REQ-123 至 REQ-137 | CP2 不授权真实抓取、写湖、publish 或 QMT 操作。 |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| 使用场景 | `process/USE-CASES.md` | 通过 | v1.8。 |
| 结构化需求 | `process/REQUIREMENTS.md` | 通过 | v1.9。 |
| CP2 自动预检 | `process/checks/CP2-CR018-REQUIREMENTS-BASELINE.md` | 通过 | PASS。 |
| CP2 人工审查稿 | `checkpoints/CP2-CR018-PRODUCTION-DATA-LAKE-CLOSURE-DECISION-BRIEF.md` | 通过 | 本文件。 |

## 人工审查结果

- 结论：`approved`
- 审查人：user
- 审查时间：2026-05-29T06:48:42+08:00
- 修改意见：无。用户已批准 D1 到 D6 按推荐方案推进。
- 风险接受项：接受 QMT simulation 后置；接受 CR018 第一版采用 2015-01-05..latest_closed_trade_date scoped release；接受行业 / 市值 / 流动性作为 P1 但阻断相关声明。
