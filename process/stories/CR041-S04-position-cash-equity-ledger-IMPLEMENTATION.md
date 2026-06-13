---
story_id: "CR041-S04-position-cash-equity-ledger"
status: "implemented"
owner: "meta-po"
implemented_at: "2026-06-10T23:55:00+08:00"
cp6: "PASS"
---

# CR041-S04 Implementation

## 实现对象

| 对象 | 路径 | 说明 |
|---|---|---|
| Engine | `engine/paper_simulation.py` | 实现 `PaperAccountState`、`PaperPosition`、`apply_fills_to_ledger`、`mark_to_market`、`reconcile_equity`、`roll_sellable_quantities`。 |
| Tests | `tests/test_cr041_paper_simulation.py` | 覆盖现金扣减、持仓更新、T+1 可卖释放、raw close 估值、缺 close blocked、负现金/负持仓边界。 |

## 设计契约映射

| LLD 契约 | 实现位置 | 验证 |
|---|---|---|
| filled/partial 更新现金和持仓 | `apply_fills_to_ledger` | `test_s04_ledger_updates_cash_positions_equity_and_t_plus_one_sellable_quantities` |
| T 日买入当日不可卖，T+1 释放 | `roll_sellable_quantities` | 同上 |
| raw close mark-to-market | `mark_to_market` | 同上 |
| 缺 raw close / 现金不足 blocked 或缩量 | `apply_fills_to_ledger` | `test_s04_ledger_never_allows_negative_cash_or_positions_and_blocks_missing_raw_close` |
| reconciliation 自检 | `reconcile_equity` | 同上 |

## 验证结果

```text
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr041_paper_simulation.py
21 passed in 0.11s
```

## 结论

S04 实现完成，CP6 PASS，可进入 CP7 验证。
