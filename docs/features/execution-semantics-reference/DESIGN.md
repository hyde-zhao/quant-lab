---
status: "draft-current-index"
version: "1.0"
feature_id: "FEAT-04"
source_matrix: "docs/design/FEATURE-DESIGN-MATRIX.md"
source_blueprint: "docs/design/BLUEPRINT.md"
change: "CR-031"
---

# Feature Design: execution-semantics-reference

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-07 | meta-po | 新增执行语义对齐与可选后端参考 Feature 设计索引 |

## Feature 摘要

| 项 | 内容 |
|---|---|
| Feature 目标 | 在保持 lightweight engine 默认主路径的前提下，用 Backtrader optional semantic reference 和 semantic diff 解释执行语义差异，并输出 target portfolio / order intent draft 衔接 |
| Owner | FEAT-04 |
| 主要代码面 | `engine/backtrader_adapter.py`、`engine/semantic_diff.py`、`engine/order_intent_draft.py` |
| 主要设计来源 | `process/HLD.md` §34、ADR-074..078、CR-025 Story / LLD |
| 非授权声明 | 不授权 Backtrader 默认依赖、源码复制 / 移植、真实 broker、QMT / MiniQMT / XtQuant、provider/lake/publish 或凭据读取 |

## Feature 边界与相邻对象

| 对象 | 本 Feature 负责 | 不负责 | 相邻 Feature / 模块 |
|---|---|---|---|
| OptionalBackendAvailability | 判断 optional backend 是否可用并结构化降级 | 修改默认依赖 | FEAT-07 |
| CleanFeedGate | 检查 PIT、available_at、单一复权口径、benchmark、calendar、tradability、cost、quality | 生产数据事实源生成 | FEAT-02 |
| SemanticDiffReport | 对比 lightweight 与 optional backend 的调仓、现金、成本、滑点、净值差异 | 把 optional backend 作为 production truth | FEAT-01 |
| OrderIntentDraft | 把研究输出转为可审查草稿 | 真实 OMS order / QMT order | FEAT-06 |
| ExternalReferenceMatrix | 记录可借鉴、可适配、禁止移植、后续 Spike | 运行外部项目或复制源码 | FEAT-03 / FEAT-07 |

## 输入 / 输出契约

| 方向 | 契约 |
|---|---|
| 输入 | lightweight run output、clean feed、strategy config、cost config、optional backend availability |
| 输出 | semantic diff artifact、structured backend unavailable、order_intent_draft_v1、reference matrix |
| 错误输出 | `backend_unavailable`、`clean_feed_failed`、`dependency_not_installed`、`source_copy_forbidden`、`real_operation_blocked` |

## 失败路径

| 失败点 | 行为 |
|---|---|
| Backtrader 未安装 | 返回 `backend_unavailable`，lightweight 主路径不受影响 |
| clean feed gate 失败 | 不运行 optional backend，不生成误导性 diff |
| 用户请求源码移植 | 进入单独 CP3 / CP5 决策，不在默认路径执行 |
| 输出 order intent draft | 只能 draft，不触发 OMS adapter 或 gateway |

## Gotchas

- Backtrader 是 semantic reference，不是默认框架。
- semantic diff 解释差异，不证明任一路径为 production truth。
- optional backend 的依赖、运行、源码移植都必须另行授权。

