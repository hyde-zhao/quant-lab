---
checkpoint_name: "CR034 chapter3 real data readiness and backfill 编码完成门"
status: "PASS"
checked_at: "2026-06-10"
owner: "codex"
change_id: "CR-034"
---

# CP6 CR034 chapter3 real data readiness and backfill 编码完成门

## Entry Criteria

| 条目 | 状态 | 证据 |
|---|---|---|
| 用户授权读取 `.env` 和调用 Tushare | PASS | `process/changes/CR-034-CHAPTER3-REAL-DATA-READINESS-PIT-AUDIT-2026-06-09.md` |
| 禁止 publish / QMT / simulation / live | PASS | CR-034 用户授权记录和脚本输出计数 |
| 第三章离线因子适配层已存在 | PASS | `engine/chapter3_factor_replication.py` |

## Checklist

| # | 检查项 | 状态 | 证据 |
|---|---|---|---|
| 1 | CR-034 决策回填 | PASS | CR 文件 frontmatter 和 D-CR034 表已更新为 approved |
| 2 | readiness 工具实现 | PASS | `engine/chapter3_real_data_readiness.py` |
| 3 | readiness CLI 实现 | PASS | `scripts/chapter3_real_data_readiness.py` |
| 4 | CR-034 补数脚本实现 | PASS | `scripts/cr034_chapter3_backfill.py` |
| 5 | 后复权 candidate 支持 | PASS | `prices_hfq` run-scoped canonical candidate 已写入 |
| 6 | 财务 PIT candidate 支持 | PASS | `financial_pit` 已写入 audited run；具备公告日 `available_at`、`revision_as_of`、`revision_sequence` 和 `pit_policy` |
| 7 | W3/ST/停牌/涨跌停覆盖 | PASS | `run-cr034-chapter3-constraints-2000-2019` 派生 `trade_status`、`prices_limit`、`events` 并覆盖目标窗口 |
| 8 | 禁止操作计数 | PASS | 所有补数 summary 均 `catalog_current_pointer_publish=0`、`qmt_operation=0`、`simulation_or_live_run=0` |
| 9 | 第三章真实实证 runner | PASS | `scripts/run_chapter3_empirical.py`；默认 `chunked` 分年分块，支持 `--resume` |
| 10 | 内存预算门控 | PASS | 默认 `--max-memory-gb 16`；大窗口 `full` 模式默认阻断，避免全量 pandas 矩阵压力 |
| 11 | 2020-2026 YTD 数据源选择 | PASS | runner 已支持 2020-2025 年度 prices/adj_factor、2026 YTD、CR018 市值/流动性/交易状态/涨跌停和 2020-2026 audited financial_pit |
| 12 | Tushare 财务补数重试 | PASS | `scripts/cr034_chapter3_backfill.py` 为 provider 临时断连增加 5 次指数退避重试 |

## Verification Commands

| 命令 | 结果 |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_chapter3_real_data_readiness.py tests/test_cr034_chapter3_backfill.py` | PASS，`10 passed` |
| `PYTHONPYCACHEPREFIX=/tmp/cr034-readiness-effective-start-pycompile uv run --python 3.11 python -m py_compile engine/chapter3_real_data_readiness.py scripts/chapter3_real_data_readiness.py scripts/cr034_chapter3_backfill.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_chapter3_empirical_runner.py tests/test_chapter3_factor_replication.py tests/test_chapter3_real_data_readiness.py tests/test_cr034_chapter3_backfill.py tests/test_factor_library.py tests/test_factor_calculators.py tests/test_factor_statistics.py` | PASS，`34 passed` |
| `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_chapter3_empirical_runner.py tests/test_cr034_chapter3_backfill.py` | PASS，`6 passed` |

## Deliverables

| 交付物 | 路径 | 状态 |
|---|---|---|
| readiness 模块 | `engine/chapter3_real_data_readiness.py` | PASS |
| readiness CLI | `scripts/chapter3_real_data_readiness.py` | PASS |
| CR-034 补数脚本 | `scripts/cr034_chapter3_backfill.py` | PASS |
| 第三章真实实证 runner | `scripts/run_chapter3_empirical.py` | PASS |
| 第三章真实实证测试 | `tests/test_chapter3_empirical_runner.py` | PASS |
| readiness 报告 | `process/research/chapter3_real_data_readiness/READINESS-REPORT.md` | PASS |
| 实证报告 | `process/research/chapter3_empirical/run-chapter3-empirical-2000-2019/EMPIRICAL-RUN-REPORT.md` | PASS |
| 2020-2026 YTD 实证报告 | `process/research/chapter3_empirical/run-chapter3-empirical-2020-2026-ytd/EMPIRICAL-RUN-REPORT.md` | PASS |
| 2020-2026 YTD readiness 摘要 | `process/research/chapter3_real_data_readiness/READINESS-REPORT-2020-2026-YTD.md` | PASS |
| README | `process/research/chapter3_real_data_readiness/README.md` | PASS |

## Exit Criteria

| 条目 | 状态 | 说明 |
|---|---|---|
| 编码对象可导入 / 可测试 | PASS | 单测和 py_compile 已通过 |
| 真实补数已留痕 | PASS | run-id 已记录在 README |
| 严格第三章 readiness 可关闭 | PASS | 第三章真实数据 readiness 已通过 |
| 第三章真实实证可关闭 | PASS | 2000-2019 全样本实证已通过，报告 status=`PASS` |
| 2020-2026 YTD 第三章实证可关闭 | PASS | 2020-2026 YTD 实证已通过，报告 status=`PASS` |

## 结论

CR-034 编码、真实补数、第三章 2000-2019 全样本实证和 2020-2026 YTD 实证均完成到 `PASS`：核心价格、后复权、市值、流动性、历史交易状态、ST/生命周期事件、涨跌停和 audited 财务 PIT 均已补齐到 candidate 层；实证 runner 已按 16GB 内存预算使用分年分块执行，并生成多因子研究准入输入。
