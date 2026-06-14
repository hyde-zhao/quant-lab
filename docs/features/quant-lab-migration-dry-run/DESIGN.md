---
status: "draft-cp4"
version: "1.0"
feature_id: "FEAT-10-CR053"
feature_name: "quant-lab Migration Inventory and Dry-run"
source_hld: "docs/design/HLD-CR053-QUANT-LAB-MIGRATION-INVENTORY-AND-DRY-RUN.md"
source_adr: "docs/design/ARCHITECTURE-DECISION-CR053.md"
source_matrix: "docs/design/FEATURE-DESIGN-MATRIX.md"
change_id: "CR-053"
confirmed_by: ""
confirmed_at: ""
---

# Feature Design: quant-lab Migration Inventory and Dry-run

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-14 | host-orchestrator | 初版 CR053 Feature 设计，冻结迁移 inventory / dry-run、NAS 逻辑映射、数据湖 alias、Windows / Linux 主机边界和后续 CR058 输入 |

## 摘要

| 项目 | 内容 |
|---|---|
| Feature 目标 | 在真实项目迁移前，生成 Git 内静态 inventory、路径引用 dry-run、NAS logical map、backup plan 和 CR058 输入合同 |
| 推荐方案 | 只做 repo-local / docs-local 静态证据；NAS、真实 lake、真实迁移和 git push 均后置到独立授权 |
| 下游 Story | CR053-S01..S05 |
| LLD 策略 | S01..S04 full-lld；S05 technical-note |

## 上游依据

| 来源 | 被消费内容 |
|---|---|
| CR053 HLD | 逻辑 root、manifest-first transfer、warm/cold backup、Linux / Windows 映射边界 |
| CR053 ADR | ADR-CR053-001..007 |
| CR051 Archive Governance | Git / research archive / market data lake / broker facts 分离原则 |
| README 数据湖合同 | `MARKET_DATA_LAKE_ROOT` / `--lake-root` 保持现状 |

## Feature 边界

| 对象 | 本 Feature 负责 | 不负责 |
|---|---|---|
| MigrationInventory | Git 内路径分类、owner、move_action、risk、verification_rule | 真实文件移动、目录重命名 |
| PathReferenceReport | `local_backtest` / legacy env / docs link 引用扫描计划与报告合同 | 自动批量改写历史 process / CR |
| NasLogicalMap | Linux 研究机三分区逻辑视图、Windows package exchange 窄映射、数据湖 alias | NAS scan / mount / mkdir / copy / delete |
| BackupPlan | Git bundle、manifest snapshot、warm / cold 备份策略和 restore rehearsal 计划 | 执行真实备份或恢复 |
| MigrationPlanInput | CR058 mechanical move 输入、rollback_ref、blocking conditions | CR058 真实迁移实施 |

## 接口 / 文件契约

| Interface ID | 输入 | 输出 | 失败模型 |
|---|---|---|---|
| IF-CR053-01 inventory plan | repo root、allowlist、denylist、path classifier | `MIGRATION-INVENTORY-CR053.md` | unknown_owner / forbidden_path |
| IF-CR053-02 reference dry-run | text files、legacy alias rules | `PATH-REFERENCES-CR053.md` | manual_review_required |
| IF-CR053-03 NAS map | logical roots、host roles、existing lake env contract | `NAS-MAPPING-CR053.md` | real_path_unverified |
| IF-CR053-04 backup plan | artifact classes、retention policy | `BACKUP-PLAN-CR053.md` | restore_drill_required |
| IF-CR053-05 CR058 input | inventory、references、backup plan、rollback_ref | `MIGRATION-PLAN-CR053.md` | migration_not_authorized |

## 权限与安全

| Rule ID | 规则 | 失败行为 |
|---|---|---|
| SEC-CR053-01 | 不读取 `.env`、token、账号、密码、session、cookie、private key | fail closed |
| SEC-CR053-02 | 不执行 NAS mount / scan / mkdir / copy / delete | fail closed |
| SEC-CR053-03 | 不移动真实目录、不重命名仓库、不 git push / tag / rewrite history | fail closed |
| SEC-CR053-04 | 不触发 provider fetch / lake write / catalog publish | fail closed |
| SEC-CR053-05 | Windows 交易机只映射 package exchange，默认 read-only | fail closed |

## Story 拆分

| Story ID | 标题 | lld_policy | 说明 |
|---|---|---|---|
| CR053-S01 | 迁移 root map 与主机映射合同 | full-lld | 冻结 Linux / Windows / NAS / lake alias 映射 schema |
| CR053-S02 | Git 内 inventory 与路径分类器 | full-lld | 设计 repo-local inventory 报告，不扫 NAS |
| CR053-S03 | 路径引用与 legacy alias dry-run | full-lld | 设计引用扫描和 manual-review 合同 |
| CR053-S04 | manifest-first transfer 与 backup plan | full-lld | 设计 transfer manifest、backup plan、restore rehearsal |
| CR053-S05 | CR058 真实迁移输入与关闭门禁 | technical-note | 汇总 dry-run 输出到 CR058 / CR059 后续 gate |

## Gotchas

| 场景 | 风险 | 规避 |
|---|---|---|
| 把 `/mnt/quant-lab/*` 当成已存在真实路径 | 误授权 mount / mkdir | 文档始终声明 logical view；真实路径绑定后置 |
| 用 `QUANT_LAB_MARKET_DATA_LAKE_ROOT` 替换现有数据湖变量 | 破坏已验证 CLI / backup / restore | 现阶段只保留 alias / pointer |
| Windows 交易机映射 full archive | 扩大交易主机暴露面 | 仅 package exchange read-only |
| CR053 输出被误读为真实迁移授权 | 误移动 / 删除文件 | CP4/CP5/CP6/CP8 均列 not-authorized |

## 完成准则

- CR053-S01..S05 均有 Story 卡片、feature refs、lld_policy 和文件所有权。
- CP4 自动预检证明 DAG 无环、无无效引用、无文件 owner 冲突。
- CP5 前实现授权为 false，真实操作计数为 0。
