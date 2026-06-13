---
story_id: "CR041-S02-target-portfolio-order-intent-builder"
status: "implemented"
owner: "meta-po"
implemented_at: "2026-06-10T23:55:00+08:00"
cp6: "PASS"
---

# CR041-S02 Implementation

## 实现对象

| 对象 | 路径 | 说明 |
|---|---|---|
| Engine | `engine/paper_simulation.py` | 实现 `build_order_intents`、`resolve_target_trade_date`、`apply_lot_and_sellable_rules`。 |
| Tests | `tests/test_cr041_paper_simulation.py` | 覆盖 T+1、raw open policy、100 股 lot、卖出可卖 cap、broker/account 字段污染 fail-closed。 |

## 设计契约映射

| LLD 契约 | 实现位置 | 验证 |
|---|---|---|
| target portfolio 显式输入 | `build_order_intents` | `test_s02_target_portfolio_builds_t_plus_one_raw_order_intents_without_broker_fields` |
| T+1 第一个 open day | `resolve_target_trade_date` | 同上 |
| 买入 100 股 lot，卖出不超过可卖 | `apply_lot_and_sellable_rules` | 同上 |
| qfq/hfq 执行价或 broker 字段污染阻断 | `build_order_intents` | `test_s02_target_portfolio_builder_fails_closed_for_broker_pollution_non_raw_or_missing_targets` |
| 不生成真实 broker payload | `PaperOrderIntent.to_dict` | 静态 payload forbidden key 检查 |

## 验证结果

```text
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr041_paper_simulation.py
21 passed in 0.11s
```

## 并行实现说明

S02 核心在主线程实现，测试由并行 worker `Euclid` 提供；未并行修改 `engine/paper_simulation.py`，避免共享文件冲突。

## 结论

S02 实现完成，CP6 PASS，可进入 CP7 验证。
