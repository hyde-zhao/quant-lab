---
discussion_id: "CP2-CR025-SCENARIO-DISCUSSION"
change_id: "CR-025"
phase: "requirement-clarification"
status: "desk-review-revised"
created_at: "2026-05-31T22:08:28+08:00"
owner: "meta-pm"
handoff: "process/handoffs/META-PM-CR025-REQ-CLARIFICATION-2026-05-31.md"
---

# CP2 CR-025 场景讨论日志

本日志记录 CR-025 的 Scenario Gray Areas desk review。用户当前要求按既定顺序推进研究路线，随后在 CP2 前澄清目标不是开发框架级 Backtrader/lightweight 回测框架，而是生产级策略研究回测、模拟盘和实盘框架。meta-po 已基于该修改意见修订 CR-025 场景、需求和 Decision Brief，保留旧基线并增量更新。

## 讨论输入

| 输入 | 路径 | 结论 |
|---|---|---|
| CR-025 正式 CR | `process/changes/CR-025-BACKTRADER-OPTIONAL-EXECUTION-BACKEND-HARDENING-2026-05-31.md` | CR-025 已修订为 research execution semantic alignment；Backtrader 仅为 optional semantic reference，CP5 前不得实现或改依赖。 |
| CR-019 follow-up 台账 | `process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md` | `backtrader_w6` 已转 active；本轮需补充三条主线 tracking 视图，CR-020..CR-024 仍为 QMT 生产执行候选。 |
| 既有场景基线 | `process/USE-CASES.md` | 保留 UC-01 至 UC-18，新增 UC-19。 |
| 既有需求基线 | `process/REQUIREMENTS.md` | 保留 REQ-001 至 REQ-172，修订 REQ-172 并新增 REQ-173。 |

## Scenario Gray Areas

| 灰区 ID | 问题 | 推荐处理 | 备选 | 状态 | 落点 |
|---|---|---|---|---|---|
| SGA-025-01 | Backtrader 是 optional semantic reference，还是替代 lightweight 主路径？ | Backtrader 仅作为显式选择的 optional execution realism / semantic reference，默认 lightweight 不变。 | 迁移到 Backtrader 主路径，但需另起设计决策。 | resolved-from-CR | UC-19、REQ-161、REQ-166、REQ-167 |
| SGA-025-02 | Backtrader 依赖是否立即引入？ | CP5 前不改 `pyproject.toml` / `uv.lock`；后续如实现采用 optional extra / lazy import。 | 现在引入依赖，但会越过 CP5。 | resolved-from-CR | REQ-162、REQ-167、REQ-168 |
| SGA-025-03 | clean feed 与执行语义差异如何验收？ | 后续 HLD 冻结 clean feed gate 和 semantic diff report 字段。 | 只做 smoke 测试，不足以解释差异。 | non-blocking-open-for-CP3 | REQ-163、REQ-164 |
| SGA-025-04 | 是否授权真实 broker / QMT / provider / lake / publish / credential？ | 不授权，所有相关计数保持 0。 | 单独新 CR / per-run 授权。 | resolved-from-CR | REQ-165、REQ-168 |
| SGA-025-05 | CR-025 是开发框架级回测内核，还是服务生产级 research-to-execution 路线？ | 服务 production-grade research-to-execution 路线；CR-025 负责研究执行语义对照与 target portfolio / order intent 衔接，并在 CP3/HLD 分析本地 Backtrader 项目模块级取舍。 | 迁移 / 自研完整回测或事件驱动框架。 | resolved-by-user | REQ-161、REQ-169、REQ-172、REQ-173 |

## 结论

- 当前无阻断 CP2 的场景灰区。
- Q-048 / SGA-025-03 和 Q-051 / order intent 字段合同是 CP3/HLD 设计输入，不阻断 CP2。
- CP2 人工确认只确认 CR-025 需求 / 场景基线，不授权实现、依赖变更、真实运行、provider、lake、publish 或凭据读取。
