---
story_id: "CR014-S08-w3-minute-tick-level2-vwap-blocked-decision-boundary"
title: "W3 / minute / tick / Level2 / VWAP blocked 决策边界"
status: "verified"
priority: "P0"
wave: "CR014-W4-CONSUMER-BOUNDARY"
depends_on:
  - "CR014-S05-full-history-readiness-gap-claim-boundary"
cp5_batch: "CR014-FULL-HISTORY-LAKE-BATCH-A"
implementation_allowed: true
created_at: "2026-05-27"
updated_at: "2026-05-27T09:40:46+08:00"
change_id: "CR-014"
---

# CR014-S08：W3 / minute / tick / Level2 / VWAP blocked 决策边界

## Story 摘要

固化 W3、minute、tick、Level2、order match、execution VWAP 与真实撮合执行价不进入 CR-014 P0 的 blocked / unsupported 决策边界。不得用 close proxy 或 amount/volume 派生真实 VWAP。

## dev_context

**输入依据**：`process/HLD-DATA-LAKE.md` §17.2、§17.10；`process/HLD.md` §30.1；ADR-045、ADR-046、ADR-050、ADR-051；REQ-084、REQ-095、REQ-096。

**未来实现候选文件**：`market_data/unsupported.py`、`engine/research_dataset.py`、`tests/test_cr014_unsupported_boundary.py`。

**开发合同**：

| 对象 | 状态 | 输出 | 解除条件 |
|---|---|---|---|
| W3 source/interface | blocked | unsupported / required_missing | 后续 source/interface + Story + CP5 + 用户授权 |
| minute/tick/Level2/order match | unsupported | blocked_claims | 后续真实数据源与权限门控 |
| execution VWAP / real fill | blocked | no production allowed claim | 真实 `vwap`、`vwap_status=available`、execution audit pass |
| close proxy / amount/volume | research-only 或 blocked | 不可替代真实 VWAP | 不得用于 production claim |

## validation_context

**验证方式**：unsupported decision matrix contract test；不接入微观结构数据，不构造伪数据。

**关键验证场景**：

| 场景 | 期望 |
|---|---|
| W3 未确认 | production allowed claim=0 |
| minute/tick/Level2 缺失 | blocked_claims 写解除条件 |
| amount/volume 派生 VWAP 请求 | fail-closed 或 blocked |
| close proxy 执行价 | 不声明真实 VWAP /真实撮合 |

## acceptance_criteria

| ID | 标准 | 验收方式 |
|---|---|---|
| AC-01 | W3/minute/tick/Level2/VWAP production allowed claim 输出次数为 0 | contract test |
| AC-02 | 解除条件 100% 指向后续 source/interface + Story + CP5 + 用户授权 | 静态检查 |
| AC-03 | close proxy 或 `amount/volume` 派生真实 VWAP 次数为 0 | 单元测试 |
| AC-04 | 不接入、不构造微观结构数据 | 文件范围检查 |

## 依赖与文件影响范围

| 类型 | 内容 |
|---|---|
| 上游依赖 | CR014-S05 |
| 下游依赖 | CR014-S07 / 后续真实微观结构数据 CR |
| 主所有权 | `market_data/unsupported.py`、`tests/test_cr014_unsupported_boundary.py` |
| 共享文件 | `engine/research_dataset.py`、`market_data/claims.py` |
| 禁止范围 | `.env`、`data/**`、`reports/**`、minute/tick/Level2/order book 构造、真实 VWAP 伪造、provider fetch |

## LLD 输入

- HLD-DATA-LAKE §17 unsupported / blocked boundary。
- HLD.md §30 研究消费声明边界。
- ADR-045 / ADR-046 / ADR-050 / ADR-051。
- CP5 前真实微观结构数据接入授权为 0。
