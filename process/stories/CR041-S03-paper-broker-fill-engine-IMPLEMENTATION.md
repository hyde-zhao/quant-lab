---
story_id: "CR041-S03-paper-broker-fill-engine"
status: "implemented"
owner: "meta-po"
implemented_at: "2026-06-10T23:55:00+08:00"
cp6: "PASS"
---

# CR041-S03 Implementation

## 实现对象

| 对象 | 路径 | 说明 |
|---|---|---|
| Engine | `engine/paper_simulation.py` | 实现 `PaperBrokerConfig`、`simulate_fills`、`check_tradeability`、`calculate_costs`、`apply_participation_cap`。 |
| Tests | `tests/test_cr041_paper_simulation.py` | 覆盖滑点、佣金、印花税、过户费、volume cap partial、涨跌停、停牌、缺字段 fail-closed。 |

## 设计契约映射

| LLD 契约 | 实现位置 | 验证 |
|---|---|---|
| T+1 raw open 成交 | `simulate_fills` | `test_s03_fill_engine_applies_slippage_costs_and_volume_cap_without_mutating_ledger` |
| buy 正滑点 / sell 负滑点 | `simulate_fills` | 同上 |
| commission / min commission / stamp duty sell-only / transfer fee | `calculate_costs` | 同上 |
| volume participation partial | `apply_participation_cap` | 同上 |
| 涨跌停、停牌、缺字段 fail-closed | `check_tradeability` | `test_s03_fill_engine_rejects_limit_suspension_and_missing_market_fields_fail_closed` |

## 验证结果

```text
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr041_paper_simulation.py
21 passed in 0.11s
```

## 不授权边界

行情只来自传入本地 fixture，不导入 provider、网络、broker 或 trading runtime。

## 结论

S03 实现完成，CP6 PASS，可进入 CP7 验证。
