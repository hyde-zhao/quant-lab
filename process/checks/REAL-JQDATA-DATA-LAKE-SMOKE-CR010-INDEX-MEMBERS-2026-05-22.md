# REAL-JQDATA-DATA-LAKE-SMOKE-CR010-INDEX-MEMBERS-2026-05-22

## Entry Criteria

| 条目 | 状态 | 证据 |
|---|---|---|
| CR-010 仍 open，`index_members` 是 production_strict 阻断项 | PASS | `process/changes/CR-010-REALISTIC-PRODUCTION-DATA-LAKE-2026-05-22.md` |
| Tushare `index_member` 已确认对 HS300 相关代码 / 2024 窗口返回 0 行 | PASS | `process/checks/REAL-TUSHARE-DATA-LAKE-SMOKE-CR010-INDEX-MEMBERS-OPS-2026-05-22.md` |
| 用户计划要求新增 JQData `index_members` PIT source/interface | PASS | 本轮用户计划 |

## Checklist

| 检查项 | 结果 | 说明 |
|---|---|---|
| 契约注册 | PASS | `source=jqdata`，`interface=index_members.snapshot`，provider method `get_index_stocks`，`pit_required=true`。 |
| 默认安全门禁 | PASS | JQData 默认 disabled；真实执行必须同时满足 allowlist、环境变量凭据、`offline=false`、`explicit_real_execution=true`。 |
| 凭据边界 | PASS | 只读取 `JQDATA_USERNAME` / `JQDATA_PASSWORD` 环境变量；不接受 CLI 明文账号密码；manifest 敏感值扫描已覆盖这两个 env。 |
| 数据集边界 | PASS | 首版只允许 `dataset=index_members`；不替代 `index_weights`、`stock_basic`、prices 或 W3 数据集。 |
| PIT 字段 | PASS | adapter 输出 `is_pit_universe=true`、`pit_status=pit_available`、`readiness_status=available`、`available_at`、`effective_date`、`available_date`。 |
| replay 边界 | PASS | `replay` 继续从 manifest/raw 复核，`network_calls=0`，不触发 provider。 |
| 文档状态 | PASS | README / USER-MANUAL 记录 JQData source/interface、`jqdatasdk` dependency group 和 `limited_pit_window` 限制。 |

## Verification

| 命令 / 检查 | 结果 |
|---|---|
| `uv lock` | PASS，新增 `jqdatasdk` 与其依赖 |
| `uv run --python 3.11 python -m py_compile market_data/contracts.py market_data/source_registry.py market_data/config.py market_data/storage.py market_data/connectors/jqdata.py market_data/cli.py market_data/validation.py` | PASS |
| `uv run --python 3.11 pytest -q tests/test_cr010_jqdata_index_members_source.py` | PASS，4 passed |
| `uv run --env-file .env --group jqdata --python 3.11 python -m market_data.cli jqdata-acquire ... --dry-run true --json` | PASS，`network_calls=0`、`writes=0`、root label 脱敏 |
| `uv run --env-file .env --group jqdata --python 3.11 python -m market_data.cli jqdata-acquire ... --dry-run false --enable-real-source --json` | PASS，`network_calls=1`、`writes=1`、raw 相对路径为 `raw/jqdata/index_members.snapshot/20250211/run_id=run-jqdata-index-members-smoke-20260522/jqdata-hs300-20250211.jsonl` |
| `uv run --env-file .env --group jqdata --python 3.11 python -m market_data.cli normalize --dataset index_members --run-id run-jqdata-index-members-smoke-20260522` | PASS，`row_count=300` |
| `uv run --env-file .env --group jqdata --python 3.11 python -m market_data.cli validate --dataset index_members ...` | PASS，`quality_status=pass`、`dataset_status=available`、coverage 300/300 |
| `uv run --env-file .env --group jqdata --python 3.11 python -m market_data.cli publish --dataset index_members` | PASS，`publish_status=published`、`quality_status=pass`、`readiness_status=available`、`pit_status=pit_available` |
| `uv run --env-file .env --group jqdata --python 3.11 python -m market_data.cli read --dataset index_members ...` | PASS，`row_count=300`，样例行显示 `source=jqdata`、`source_interface=index_members.snapshot`、`pit_status=pit_available`、`readiness_status=available` |
| `uv run --env-file .env --group jqdata --python 3.11 python -m market_data.cli revalidate --dataset index_members ...` | PASS，`network_calls=0`、quality 仍为 pass |
| `uv run --env-file .env --group jqdata --python 3.11 python -m market_data.cli replay --dataset index_members ...` | PASS，`network_calls=0`、`writes=0`、`auto_execute=false` |
| `report-readiness --realism-mode production_strict` | PASS_EXECUTED，整体 `status=fail`；`index_members` 已 published/pass/available/pit_available，剩余阻断来自 `index_weights`、`stock_basic` 和 W3 缺口 |
| `report-readiness --realism-mode exploratory` | PASS_EXECUTED，整体 `status=warn`，allowed claims 为 `exploratory_analysis` / `fixture_regression` |

## Exit Criteria

| 条目 | 状态 | 说明 |
|---|---|---|
| 离线契约与 fake provider lake 链路通过 | PASS | fake provider 覆盖 acquire、raw/manifest、normalize、validate、publish、read、revalidate、replay。 |
| 真实 JQData smoke | PASS | `2025-02-11` HS300 JQData smoke 已抓取 300 行并发布为 `index_members` current truth。报告不得写入凭据或真实私有路径。 |
| production_strict | OPEN | `index_members` 阻断已关闭；整体仍因 `index_weights` PIT incomplete、`stock_basic` non-PIT snapshot、W3 missing 保持 fail。有限窗口 smoke 不等同完整历史 PIT universe complete。 |

## Deliverables

| 类型 | 路径 |
|---|---|
| adapter | `market_data/connectors/jqdata.py` |
| CLI / plan | `market_data/cli.py` |
| contracts / registry / config | `market_data/contracts.py`、`market_data/source_registry.py`、`market_data/config.py` |
| tests | `tests/test_cr010_jqdata_index_members_source.py` |
| docs | `README.md`、`docs/USER-MANUAL.md`、`process/changes/CR-010-REALISTIC-PRODUCTION-DATA-LAKE-2026-05-22.md` |
