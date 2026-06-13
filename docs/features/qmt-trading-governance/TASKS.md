---
status: "draft-current-index"
version: "1.0"
feature_id: "FEAT-06"
---

# Feature Tasks: qmt-trading-governance

| Task ID | 任务 | 输入 | 输出 | 文件范围 | 验证 |
|---|---|---|---|---|---|
| FEAT-06-T01 | 维护 OMS 状态机 | order intent draft / broker event | order state / transition | `trading/oms.py` | OMS tests |
| FEAT-06-T02 | 维护 pre-trade risk gate | raw price / cash / position / config | pass / blocked reason | `trading/pretrade_risk.py` | risk tests |
| FEAT-06-T03 | 维护 broker lake contract | broker facts / redaction | external broker lake schema | `trading/broker_lake.py` | broker lake tests |
| FEAT-06-T04 | 维护 stage gate | evidence / authorization / runbook | stage result / rollback | `trading/stage_gate.py` | stage gate tests |
| FEAT-06-T05 | 维护 reconciliation / kill switch | broker snapshot / OMS state | recon report / incident | `trading/reconciliation.py`、`trading/kill_switch.py` | recon / kill tests |

## 后续触发条件

- 启动 CR-021 QMT simulation 账号接入准入。
- 启动 live_readonly / small_live / scale_up。
- 修改 broker lake root、retention、redaction 或 risk threshold。

