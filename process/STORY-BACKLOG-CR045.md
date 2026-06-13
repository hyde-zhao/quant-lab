---
version: "1.0"
last_updated: "2026-06-11T23:05:00+08:00"
cr_id: "CR-045"
status: "draft-for-cp4"
owner: "meta-se"
source_hld: "docs/design/HLD-CR045-GOLDMINER-WINDOWS-BRIDGE.md"
source_feature_matrix: "docs/design/FEATURE-DESIGN-MATRIX-CR045.md"
cp5_batch_id: "CR045-BRIDGE-BATCH-A"
---

# CR045 Story Backlog

## Story 列表

| Story ID | 标题 | 优先级 | Wave | lld_policy | 依赖 | 核心价值 | 主要输出 |
|---|---|---|---|---|---|---|---|
| CR045-S01 | Windows Bridge Security Boundary | P0 | W1 | full-lld | 无 | 冻结授权、凭据、hard-off 和不授权边界。 | Story card；CP5 LLD；authorization model。 |
| CR045-S02 | Bridge Health Capabilities Skeleton | P0 | W2 | full-lld | S01 | 冻结 health/capabilities schema 和 false capability flags。 | Story card；CP5 LLD；future bridge contract/test plan。 |
| CR045-S03 | WSL Linux Client Contract and Network Precheck | P0 | W2 | full-lld | S01 | 冻结 Linux 侧 client 角色、fixture transport 和 runtime-not-started 行为。 | Story card；CP5 LLD；future client contract/test plan。 |
| CR045-S04 | Readonly Probe Allowlist and Blocked-First | P0 | W3 | full-lld | S01/S02/S03 | 冻结 readonly skeleton 和 L4 未授权 blocked-first。 | Story card；CP5 LLD；future readonly probe contract/test plan。 |
| CR045-S05 | Redaction and No-Operation Static Validation | P0 | W3 | full-lld | S01/S02/S03 | 冻结 redaction evidence、artifact scan 和 operation counts=0。 | Story card；CP5 LLD；future static validation plan。 |
| CR045-S06 | User Runbook and Follow-up Gates | P1 | W4 | technical-note | S01-S05 | 把不授权边界、后续 L3/L4/L5 gate 和 CP8 文案收敛给用户。 | Story card technical-note；future runbook outline。 |

## Wave 分组

| Wave | Story | 并行策略 | 进入条件 | 退出条件 |
|---|---|---|---|---|
| W1 | CR045-S01 | 串行 | CP3 approved；Feature Design Matrix ready | S01 可进入 CP5 full-lld 写作。 |
| W2 | CR045-S02、CR045-S03 | LLD 可并行；开发需 CP5 后按 file owner 计算 | S01 合同已声明；Feature DESIGN 已冻结 API 边界 | S02/S03 可进入 CP5 full-lld 写作。 |
| W3 | CR045-S04、CR045-S05 | LLD 可并行；开发保守串行 | S01/S02/S03 合同已声明 | S04/S05 可进入 CP5 full-lld 写作。 |
| W4 | CR045-S06 | 串行收敛 | S01-S05 设计证据形成 | S06 technical-note 可进入 CP5 批量审查，或按升级条件转 full-lld。 |

## CP5 批次范围

| 批次 | 包含 Story | 设计证据类型 | 人工门禁 |
|---|---|---|---|
| CR045-BRIDGE-BATCH-A | CR045-S01..S06 | S01-S05 full-lld；S06 technical-note / 条件升 full-lld | `process/checkpoints/CP5-CR045-BRIDGE-BATCH-A-LLD-BATCH.md` |

## 阻塞项

| Blocker ID | 状态 | 影响范围 | 说明 | 处理方式 |
|---|---|---|---|---|
| BLK-CR045-RUNTIME | non-blocking-for-cp4 | CP6/CP7/CP8 真实运行、真实只读、交易 | L3/L4/L5 均未授权，不能启动 Windows bridge runtime、连接 Goldminer 或查询账户。 | 当前只做 L2 skeleton planning；任何真实需求交回 meta-po 发起 runtime_authorization。 |
| BLK-CR045-CREDENTIAL | non-blocking-for-cp4 | 全部 Story | 不读取 `.env`、token、account_id、账号、密码、session、cookie、private key。 | Story 和 TEST-PLAN 均要求 zero secret custody。 |
| BLK-CR045-S06-UPGRADE | conditional | CR045-S06 | 若 S06 引入自动 manifest/schema/guard script，则 technical-note 不足。 | CP5 前升级为 full-lld 或延后自动化。 |
