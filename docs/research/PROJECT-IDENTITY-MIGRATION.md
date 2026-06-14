---
status: "implemented-cp6"
version: "1.0"
change_id: "CR-051"
story_id: "CR051-S06-project-identity-rename-and-legacy-alias"
owner: "host-orchestrator"
implemented_at: "2026-06-14T09:00:24+08:00"
canonical_project_name: "quant-lab"
legacy_project_alias: "local_backtest"
real_rename_authorized: false
git_push_authorized: false
---

# Project Identity Migration

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-14 | host-orchestrator | 初版项目身份迁移合同，冻结 `quant-lab` canonical name、`local_backtest` legacy alias 和迁移顺序 |

## 目标

`quant-lab` 是后续新文档和迁移目标的 canonical project name。`local_backtest` 保留为 legacy alias 和历史审计名。本文只定义命名合同和迁移顺序，不执行目录重命名、远端仓库改名、批量历史替换、git push 或 tag。

## Identity Contract

| 字段 | 主值 | legacy / 兼容 | 说明 |
|---|---|---|---|
| canonical_project_name | `quant-lab` | N/A | 新设计、新迁移目标和后续项目身份使用 |
| legacy_project_alias | `local_backtest` | 保留 | 历史审计名，不批量改写 |
| repo_root_env | `QUANT_LAB_REPO_ROOT` | `LOCAL_BACKTEST_REPO_ROOT` | 新变量主推，旧变量迁移期兼容 |
| default_linux_root | `~/workspace/quant-lab` | `~/workspace/local_backtest` | 后续 CR054 执行前只作为计划 |
| default_windows_root | `C:\\quant-lab` | `C:\\local_backtest` | 后续文档提供用户可覆盖路径 |
| package_name | 待 CR054 决策 | 当前 `pyproject.toml` 不改 | 改名需 uv lock / import / docs 回归 |

## 迁移顺序

| 顺序 | 对象 | 主选动作 | 验证 | 当前授权 |
|---|---|---|---|---|
| 1 | 新设计 / 新文档 | 使用 `quant-lab` | 文档 review | 已授权 |
| 2 | 历史 `process/` / CR / handoff | 保留 `local_backtest` | 不批量替换 | 已授权保留 |
| 3 | README / USER-MANUAL | 后续 CR054 增加显示名和 alias 说明 | docs guardrail | 未授权修改 |
| 4 | `pyproject.toml` / package metadata | 后续 CR054 评估 package name、import、uv lock | tests + uv lock check | 未授权修改 |
| 5 | 仓库目录 / 远端仓库 | 后续 migration gate 单独授权 | git status / path refs / rollback | 未授权 |
| 6 | Windows 默认路径 | 后续 CR049/CR054 与用户环境一起迁移 | 用户可覆盖路径 | 未授权 |

## Alias Policy

- 新增长期文档默认使用 `quant-lab`。
- 历史 process、CR、handoff、checkpoint 中的 `local_backtest` 是审计上下文，不批量改写。
- 对用户命令、旧路径、旧环境变量的引用应作为 legacy alias 说明保留。
- 任何真实改名必须先形成 MigrationInventory，包含 path、owner_feature、move_action、verification_rule 和 rollback_ref。

## 禁止项

- 不执行当前工作目录重命名。
- 不改远端仓库名。
- 不 git push、不 tag publish、不重写历史。
- 不批量替换历史 `process/`、handoff、CR 中的 `local_backtest`。
- 不修改 `pyproject.toml`、import path 或 package metadata。

## 后续 CR054 进入条件

| 条件 | 说明 |
|---|---|
| CR051 CP8 approved | 研究生命周期与 identity contract 已验证 |
| path reference inventory ready | 先 inventory，再决定修改范围 |
| rollback_ref ready | 每项移动或重命名都有回退引用 |
| user migration authorization | 用户明确授权具体路径、远端和发布动作 |

