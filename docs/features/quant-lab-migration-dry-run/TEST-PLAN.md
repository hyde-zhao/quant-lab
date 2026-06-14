---
status: "draft-cp4"
version: "1.0"
feature_id: "FEAT-10-CR053"
change_id: "CR-053"
source_design: "docs/features/quant-lab-migration-dry-run/DESIGN.md"
---

# Test Plan: quant-lab Migration Inventory and Dry-run

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-14 | host-orchestrator | 初版 CR053 测试计划，覆盖静态报告、路径引用、NAS 映射、备份计划和不授权边界 |

## 测试矩阵

| Test ID | Story | 类型 | 验证点 | 通过标准 |
|---|---|---|---|---|
| TC-CR053-01 | S01 | contract | root map schema 覆盖 repo / hot / package exchange / archive / lake alias / cold / trading evidence | 7 类 root 100% 出现 |
| TC-CR053-02 | S01 | safety | `MARKET_DATA_LAKE_ROOT` 保持现状，`QUANT_LAB_MARKET_DATA_LAKE_ROOT` 只作 alias | 无替换现有 CLI 入口的声明 |
| TC-CR053-03 | S02 | static | inventory 分类包含 path、owner、class、move_action、risk、verification_rule | 字段覆盖率 100% |
| TC-CR053-04 | S03 | static | legacy alias dry-run 能标记 manual-review | 不自动批量改写历史 process / CR |
| TC-CR053-05 | S04 | contract | transfer manifest 包含 staging、checksum、promote、record、rollback | 字段覆盖率 100% |
| TC-CR053-06 | S04 | contract | backup plan 区分 hot / warm / cold / git bundle / package manifest / lake policy | 6 类对象 100% 覆盖 |
| TC-CR053-07 | S05 | gate | CR058 input 明确前置：inventory、references、backup plan、rollback_ref、CP5 approve | 缺任一项则 blocked |
| SEC-CR053-01 | all | safety | NAS / lake / runtime / credential / git push 等未授权操作计数 | 全部为 0 |

## 不授权验证

| 禁止操作 | 期望 |
|---|---|
| NAS scan / mount / mkdir / copy / delete | 0 |
| 真实目录移动 / 重命名 | 0 |
| git push / tag / history rewrite | 0 |
| `.env` / token / account / password / private key read | 0 |
| provider fetch / lake write / catalog publish | 0 |
| QMT / MiniQMT runtime / trading action | 0 |

## 验收策略

- CP5 只验证设计证据可实现性。
- CP6 若后续执行，只允许生成 Git 内静态报告；任何 NAS、lake、runtime 和真实迁移动作都必须保持 not-authorized。
- CP7 验证以静态报告、schema、guardrail 和 dry-run evidence 为主。
