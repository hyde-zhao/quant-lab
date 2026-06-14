---
status: "draft-cp4"
version: "1.0"
feature_id: "FEAT-10-CR053"
change_id: "CR-053"
source_design: "docs/features/quant-lab-migration-dry-run/DESIGN.md"
---

# Tasks: quant-lab Migration Inventory and Dry-run

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-14 | host-orchestrator | 初版 CR053 任务清单，定义 CP5 设计证据批次和后续 dry-run 报告任务 |

## CP5 设计证据任务

| Task ID | Story | 任务 | 输出 |
|---|---|---|---|
| CR053-T01 | S01 | 编写 root map / host map LLD | `process/stories/CR053-S01-root-map-and-host-mapping-contract-LLD.md` |
| CR053-T02 | S02 | 编写 inventory classifier LLD | `process/stories/CR053-S02-repo-inventory-and-path-classification-LLD.md` |
| CR053-T03 | S03 | 编写 path reference dry-run LLD | `process/stories/CR053-S03-path-reference-and-legacy-alias-dry-run-LLD.md` |
| CR053-T04 | S04 | 编写 transfer / backup LLD | `process/stories/CR053-S04-manifest-transfer-and-backup-plan-LLD.md` |
| CR053-T05 | S05 | 编写 CR058 input technical note | `process/stories/CR053-S05-cr058-migration-input-and-close-gate.md` |

## 后续 CP6 候选任务

| Task ID | 任务 | 授权要求 |
|---|---|---|
| CR053-R01 | 生成 Git 内 path inventory 静态报告 | CP5 approved；不得扫 NAS / 读凭据 |
| CR053-R02 | 生成 path reference dry-run 报告 | CP5 approved；不得批量改写 |
| CR053-R03 | 生成 NAS logical map 报告 | CP5 approved；只写占位映射，不验证真实路径 |
| CR053-R04 | 生成 backup plan 报告 | CP5 approved；不执行备份 |
| CR053-R05 | 生成 CR058 migration input | CP5 approved；不移动文件 |

## 阻断条件

- 用户要求真实 NAS scan / mount / copy / delete。
- 用户要求真实目录移动、仓库重命名、git push / tag / rewrite history。
- 需要读取 `.env`、token、账号、密码或任意凭据。
- 需要触发 provider fetch、lake write、catalog publish、QMT / MiniQMT runtime 或交易动作。
