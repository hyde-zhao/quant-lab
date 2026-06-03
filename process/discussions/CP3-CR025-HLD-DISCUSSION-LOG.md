---
discussion_id: "CP3-CR025-HLD-DISCUSSION"
change_id: "CR-025"
phase: "solution-design"
status: "draft-ready-for-cp3"
created_at: "2026-06-01T21:53:17+08:00"
owner: "meta-se"
handoff: "process/handoffs/META-SE-CR025-HLD-ADR-2026-06-01.md"
---

# CP3 CR-025 HLD 讨论日志

本日志记录 CR-025 HLD 形成前的 Architecture Gray Areas、advisor table-first 讨论输入和本轮设计选择。当前处于 meta-se 阶段委托；用户已在 CP2 approved 后追加要求：必须充分分析本地 Backtrader 项目 `/home/hyde/download/backtrader`，记录可借鉴、可适配、可移植候选和禁止移植模块。本轮未调度额外 reviewer subagent，也未伪造多角色审查结果；正式 CP3 人工确认仍由 meta-po 发起。

## 输入证据

| 输入 | 路径 | 结论 |
|---|---|---|
| CR-025 交接 | `process/handoffs/META-SE-CR025-HLD-ADR-2026-06-01.md` | 要求 meta-se 分析 Backtrader GPLv3 本地项目，仅允许设计/分析/检查点产物。 |
| CP2 人工确认 | `checkpoints/CP2-CR025-REQUIREMENTS-BASELINE.md` | 用户已批准进入 CP3；不授权实现、依赖变更、源码移植、Backtrader 运行或真实 QMT。 |
| 场景基线 | `process/USE-CASES.md` v1.13 | UC-19、SM-33 至 SM-41、TS-025-01 至 TS-025-11 已确认。 |
| 需求基线 | `process/REQUIREMENTS.md` v1.14 | REQ-161 至 REQ-173、RA-057 至 RA-066 已确认。 |
| 本地 Backtrader | `/home/hyde/download/backtrader` | 静态读取 license、setup metadata、module tree、核心类/接口；未运行 Backtrader，未复制源码。 |
| License | `/home/hyde/download/backtrader/LICENSE`、`setup.py` | 本地 LICENSE 为 GNU GPL v3；`setup.py` 标记 `GPLv3+`。 |

## Architecture Gray Areas

| 灰区 ID | 问题 | 为什么影响 HLD | 推荐处理 | 备选 | 状态 | 落点 |
|---|---|---|---|---|---|---|
| AGA-CR025-01 | Backtrader 是 optional semantic reference、adapter，还是主路径迁移候选？ | 改变默认入口、依赖策略、回归范围和用户对结果 truth 的理解。 | optional semantic reference + design reference；lightweight 仍为默认主路径。 | CP5 后 optional runtime；主路径迁移另起 CR。 | decision-item | HLD §34.3；ADR-074；DQ-CP3-CR025-01 |
| AGA-CR025-02 | 哪些 Backtrader 模块可借鉴、可适配、可移植候选、必须排除？ | 改变模块边界、文件 owner、验证策略和后续 LLD forbidden paths。 | 模块矩阵分类为 `reference_only` / `adapt_interface` / `exclude`；当前无默认源码级移植推荐。 | 标记源码级候选，但需 CP3/CP5 双门控。 | decision-item | HLD §34.5；ADR-075；DQ-CP3-CR025-02 |
| AGA-CR025-03 | GPLv3 对源码复制、裁剪、改写和分发的影响是什么？ | 决定是否可能引入 copyleft、源码开放、修改标记和分发义务。 | 默认 no-copy clean-room adaptation；源码级例外需 CP3 风险接受、CP5 授权和合规确认。 | optional dependency runtime；fork/vendor 子集。 | decision-item | HLD §34.5/§34.14；ADR-076；DQ-CP3-CR025-03 |
| AGA-CR025-04 | lightweight baseline、Backtrader semantic reference 与 QMT order intent 如何对齐？ | 决定 semantic diff 和 target portfolio / order intent draft 是否可作为生产执行路线输入。 | 冻结 clean feed gate、semantic diff schema 和 `order_intent_draft_v1`。 | 仅输出 diff，不输出 intent draft；或直接接 QMT。 | decision-item | HLD §34.6/§34.7；ADR-077；DQ-CP3-CR025-04/05 |
| AGA-CR025-05 | CR-025 与 CR-020 gateway health 的顺序和接口边界如何表达？ | 防止 CP3 设计通过被误读为服务启动、simulation 或 live 授权。 | CR-025 只提供 draft 和 evidence；CR-020..CR-024 独立启动和授权。 | CR-025 直接启动 gateway health；不推荐。 | decision-item | HLD §34.7；HLD-QMT §18；DQ-CP3-CR025-05/06 |

## Advisor Table

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| CR25-A Design reference + clean-room interface adaptation | 保留 lightweight 稳定性；降低 GPLv3 源码污染；CP5 前不改依赖；满足本地模块分析要求 | 不直接获得 Backtrader runtime 行为；后续 adapter 仍需实现 | HLD、ADR、clean feed、semantic diff、order intent、QA 合同 | 推荐默认 | 当前 CP3 阶段适用；若 CP5 后需要真实框架对照，可切 CR25-B。 |
| CR25-B Optional dependency runtime integration | 可在 CP5 后用外部包运行对照；不用复制源码 | 需 optional extra、lazy import、依赖版本、未安装回归和分发策略 | pyproject/uv.lock、adapter、测试矩阵、文档 | 条件备选 | 仅 CP5 approved 且 legal/package 策略清楚时采用。 |
| CR25-C Source migration / fork | 可深改事件循环或订单模型 | GPLv3/copyleft 风险、维护成本和回归面最高；偏离本 CR 目标 | 许可证、文件 owner、发布、QA、用户文档 | 不推荐默认 | 只有用户明确接受 GPLv3 风险并另起 CR / CP5 授权时考虑。 |
| CR25-D 不参考 Backtrader | 风险最低 | 不满足用户明确要求和 REQ-173 | HLD 完整性、用户信任 | 不采用 | 用户撤回本地 Backtrader 分析要求时才切换。 |

## 本轮设计选择

| 决策输入 | 推荐选择 | 影响 |
|---|---|---|
| Backtrader 定位 | CR25-A：optional semantic reference / design reference | 不替代 lightweight，不默认依赖。 |
| 模块处理 | reference-only / adapt-interface / exclude；默认无源码级移植推荐 | 后续 LLD 用 clean-room contract，不复制 GPLv3 源码。 |
| GPLv3 治理 | no-copy 默认，源码例外需 CP3/CP5 双门控 | 降低 copyleft、维护和发布风险。 |
| clean feed / semantic diff | 冻结 gate 与 diff 字段 | 后续 CP5 可实现，但 CP3 不运行。 |
| QMT 衔接 | 只输出 order intent draft | 不启动 CR-020，不授权 QMT。 |

## Deferred / Excluded

| 项 | 原因 | 后续触发 |
|---|---|---|
| Backtrader live broker / stores | 真实 broker、账户和权限风险，且不属于 CR-025 | 另起 broker / QMT CR。 |
| Backtrader 源码级移植 | GPLv3、维护、回归风险高 | 用户明确选择 CR25-C 并完成 CP3/CP5。 |
| 指标库 / Strategy 继承体系迁移 | 会把 CR-025 扩大为框架工程 | 独立研究框架迁移 CR。 |
| QMT gateway / simulation / live | 由 CR-020..CR-024 独立控制 | 用户明确启动后续 CR。 |

## CP3 决策项草案

| 决策 ID | 类型 | 推荐方案 | 备选方案 |
|---|---|---|---|
| DQ-CP3-CR025-01 | architecture | 接受 Backtrader optional semantic reference 默认定位 | CP5 后 optional runtime；主路径迁移另起 CR。 |
| DQ-CP3-CR025-02 | architecture | 接受模块矩阵分类，默认无源码级移植推荐 | 标记少数源码级候选并进入 GPL 风险接受。 |
| DQ-CP3-CR025-03 | risk_acceptance | 接受 GPLv3 no-copy 治理 | optional dependency；fork/vendor 子集。 |
| DQ-CP3-CR025-04 | implementation | 接受 clean feed gate 与 semantic diff schema | 只做 smoke；字段后置到 LLD。 |
| DQ-CP3-CR025-05 | architecture | 接受 order intent draft 与 QMT 边界 | 不输出 draft；或直接接 QMT（不推荐）。 |
| DQ-CP3-CR025-06 | runtime_authorization | 确认 CP3 不授权实现、依赖变更、运行、源码迁移或真实操作 | 为真实运行另起 CR / per-run authorization。 |

## 结论

- HLD 草案已收敛到 CR25-A 推荐方案。
- Backtrader 本地项目分析已进入 `process/HLD.md` §34.5。
- GPLv3 作为架构风险进入 ADR-076 与 CP3 决策项。
- CP3 自动预检输入可生成；正式 CP3 发起与人工确认由 meta-po 完成。
