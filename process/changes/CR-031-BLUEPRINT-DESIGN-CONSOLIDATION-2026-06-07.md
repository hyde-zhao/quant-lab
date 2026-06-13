---
id: "CR-031"
title: "蓝图设计文档归一化补齐"
status: "doc-consolidation"
created_at: "2026-06-07T00:00:00+08:00"
created_by: "meta-po"
change_type: "design-documentation"
scope:
  - "docs/design/BLUEPRINT.md"
  - "docs/design/DOMAIN-MAP.md"
  - "docs/design/DEPENDENCY-MAP.md"
  - "docs/design/HLD.md"
  - "docs/design/ARCHITECTURE-DECISION.md"
  - "docs/design/FEATURE-DESIGN-MATRIX.md"
  - "docs/features/*"
runtime_authorization: "none"
real_operation_authorization: "none"
---

# CR-031 蓝图设计文档归一化补齐

## 背景

当前项目已经形成主 HLD、数据湖 companion HLD、QMT companion HLD、ADR、Story Backlog 和大量 Story 级 LLD / 验证证据，但长期设计入口仍主要停留在 `process/` legacy 路径。按当前 Meta Flow 规范，跨 Feature / Epic 的能力边界、领域对象、数据归属和依赖方向应沉淀到 `docs/design/`。

本 CR 只补齐蓝图层索引文档，不修改需求范围、不修改代码、不推进 CR-020，不触发 provider、lake、publish、QMT、gateway、凭据或真实账户操作。

## 范围

| 类别 | 本次处理 |
|---|---|
| 蓝图三件套 | 新增 `docs/design/BLUEPRINT.md`、`DOMAIN-MAP.md`、`DEPENDENCY-MAP.md` |
| HLD / ADR 长期入口 | 新增 `docs/design/HLD.md`、`ARCHITECTURE-DECISION.md`，作为 legacy `process/` 设计产物的 current index |
| Feature 设计入口 | 新增 `docs/design/FEATURE-DESIGN-MATRIX.md` 和重点 Feature 的简版设计索引 |
| 历史过程证据 | 保留 `process/HLD*.md`、`process/ARCHITECTURE-DECISION.md`、`process/STORY-BACKLOG.md`，不移动、不删除、不重写 |

## 非范围

- 不修改 `process/STATE.md` 的 active CR。
- 不修改 `pyproject.toml`、`uv.lock`、运行代码、测试代码或真实数据目录。
- 不生成新的实现 Story，不改变 CR-020 manual validation 状态。
- 不授权真实 provider fetch、lake write、catalog publish、QMT gateway 启动、端口绑定、QMT / MiniQMT / XtQuant 调用、真实 `.env` 读取、交易、账户查询、simulation / live。

## 文档处理决策

| 决策 ID | 类型 | 决策 |
|---|---|---|
| D-CR031-01 | architecture | `docs/design/` 作为长期蓝图与设计索引入口，legacy `process/` 文件继续作为历史审计证据 |
| D-CR031-02 | implementation | 本次只新增索引与归一化设计文档，不回写 134 个 Story 卡片，避免污染已完成证据 |
| D-CR031-03 | runtime_authorization | 文档补齐不构成任何真实运行授权；所有真实操作仍按原 CR / CP / per-run authorization 控制 |

## 验收

- `docs/design/BLUEPRINT.md` 覆盖当前主要 Feature / Epic、能力地图、跨 Feature 流程和共享能力。
- `docs/design/DOMAIN-MAP.md` 覆盖核心术语、领域对象、状态机和业务规则。
- `docs/design/DEPENDENCY-MAP.md` 覆盖允许依赖、禁止依赖和循环风险。
- `docs/design/FEATURE-DESIGN-MATRIX.md` 覆盖所有主要 Feature / Epic，并给出 required / waived 判定。
- 新增 Feature 设计索引能回链到 HLD / ADR / Story / 测试入口。

