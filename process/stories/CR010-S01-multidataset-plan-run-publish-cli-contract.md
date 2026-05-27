---
story_id: "CR010-S01-multidataset-plan-run-publish-cli-contract"
title: "multi-dataset plan/run/publish CLI contract"
story_slug: "multidataset-plan-run-publish-cli-contract"
status: "verified"
priority: "P0"
wave: "CR010-DL-BATCH-A"
depends_on: ["CR009-CLOSED", "CR007-S01-prices-long-horizon-backfill-planner", "CR007-S02-benchmark-calendar-backfill"]
dependency_contracts:
  - upstream: "CR009-CLOSED"
    type: "runtime"
    required: "revalidate/replay CLI 基线已修复并验证"
  - upstream: "CR007-S01-prices-long-horizon-backfill-planner"
    type: "contract"
    required: "长期 prices planner、resume policy、coverage gate 语义已冻结"
  - upstream: "CR007-S02-benchmark-calendar-backfill"
    type: "contract"
    required: "benchmark/calendar backfill 与 reader quality policy 已冻结"
file_ownership:
  primary:
    - "market_data/cli.py"
    - "market_data/catalog.py"
    - "market_data/readers.py"
    - "tests/test_cr010_data_lake_publish_and_contracts.py"
  shared:
    - "market_data/contracts.py"
    - "market_data/runtime.py"
    - "market_data/validation.py"
  forbidden:
    - "engine/**"
    - "experiments/**"
    - "data/**"
    - "reports/**"
    - ".env"
    - "credentials"
    - "delivery/**"
lld_gate:
  status: "approved"
  cp5_batch: "CR010-DL-BATCH-A"
  lld_path: "process/stories/CR010-S01-multidataset-plan-run-publish-cli-contract-LLD.md"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  safety_boundary: "offline-only; no real source, no real lake write, no credentials"
created_at: "2026-05-22T15:13:28+08:00"
updated_at: "2026-05-22T15:13:28+08:00"
source_hld: "process/HLD-DATA-LAKE.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-010"
execution:
  cp6_status: "PASS"
  cp6_checkpoint: "process/checks/CP6-CR010-S01-multidataset-plan-run-publish-cli-contract-CODING-DONE.md"
  cp7_status: "PASS"
  cp7_checkpoint: "process/checks/CP7-CR010-S01-multidataset-plan-run-publish-cli-contract-VERIFICATION-DONE.md"
  verified_at: "2026-05-22T15:30:00+08:00"
---

# CR010-S01：multi-dataset plan/run/publish CLI contract

## 目标

统一 `market_data` 的 `plan -> run -> normalize -> validate -> publish -> read -> revalidate -> replay` CLI 合同，使 validate 只生成候选，publish 才能成为 catalog current truth。默认只允许离线 / fixture / tmp lake 验证，真实 source 与真实 lake 写入继续保持未授权。

## 映射

| 类型 | 映射 |
|---|---|
| CR | CR-010 P0 数据湖生产化、publish gate、恢复审计 |
| HLD | `process/HLD-DATA-LAKE.md` §3.3、§5、§6 |
| ADR | ADR-031、ADR-034、ADR-035 |

## 验收标准

- `plan` 不联网、不写湖，只输出 deterministic plan 和 idempotency 输入。
- `run` 默认 dry-run；真实 source 必须显式 `--enable-real-source`，本批次不授权执行。
- `validate` 不自动更新 current truth；`publish` 后 reader 才可见。
- `read/revalidate/replay` 都基于已发布 catalog 或已存在 manifest/raw，不重新联网。
- `quality_status=fail` 阻断 publish；`warn` 默认阻断 production strict，exploratory 需显式 allow。

## 安全边界

不读取 `.env`、token、NAS 凭据、旧 `data/**` 或旧 `reports/data_quality_report.csv` 内容；不执行真实 Tushare 抓取；不写真实 `/mnt/ugreen-data-lake`。
