---
handoff_id: "META-DEV-IMPLEMENT-STORY-004-013-2026-05-15"
from_agent: "meta-po"
to_agent: "meta-dev"
status: "completed"
created_at: "2026-05-15"
scope: "STORY-004..STORY-013"
delivery_write_allowed: false
data_generation_allowed: false
---

# META-DEV 实现交接记录：STORY-004 至 STORY-013

## 1. 执行依据

- 用户已于 2026-05-15 确认通过批量 LLD / Story Package。
- 主链依赖按 `STORY-004 -> STORY-005 -> STORY-006 -> STORY-007 -> STORY-008 -> STORY-009 -> STORY-010 -> STORY-011 -> STORY-012` 串行执行。
- `STORY-013` 依赖 `STORY-008`，与 W3 起点文件所有权无冲突，按用户“可并行则并行”要求在条件满足后纳入实现。
- W3 `UNRESOLVED` source/interface 未替换 exact 值前，只实现 fail-fast 防线，不伪造 provider，不做模糊匹配。

## 2. 修改文件

| Story | 文件 |
|---|---|
| STORY-004 | `engine/data_loader.py`、`engine/contracts.py` |
| STORY-005 | `strategies/momentum.py`、`engine/portfolio.py` |
| STORY-006 | `engine/backtest.py`、`engine/metrics.py`、`engine/reporting.py` |
| STORY-007 | `engine/scanner.py`、`engine/reporting.py` |
| STORY-008 | `engine/candidates.py`、`engine/reporting.py` |
| STORY-009 | `engine/source_registry.py`、`engine/universe.py`、`engine/data_prep.py`、`engine/normalizer.py`、`engine/quality.py`、`engine/data_loader.py`、`engine/contracts.py` |
| STORY-010 | `engine/trade_status.py`、`engine/portfolio.py`、`engine/source_registry.py` |
| STORY-011 | `engine/trading_constraints.py`、`engine/events.py`、`engine/source_registry.py` |
| STORY-012 | `engine/bias_audit.py`、`engine/reporting.py` |
| STORY-013 | `strategies/base.py`、`strategies/rsi.py`、`strategies/macd.py`、`engine/backtest.py`、`engine/scanner.py` |
| 测试 | `tests/conftest.py`、`tests/test_story_004_013.py` |

## 3. 边界执行结果

- 未写入 `delivery/**`。
- 未生成真实生产数据。
- 未生成或修改安装脚本。
- 测试仅使用 `tmp_path`、内存 DataFrame 和 fake runner。
- W3 未替换 exact source/interface，当前启用路径均按 `UNRESOLVED` fail fast。
