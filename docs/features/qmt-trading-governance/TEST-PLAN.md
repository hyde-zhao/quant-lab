---
status: "draft-current-index"
version: "1.0"
feature_id: "FEAT-06"
---

# Feature Test Plan: qmt-trading-governance

## 测试矩阵

| 测试域 | 关键场景 | 验证入口 |
|---|---|---|
| QMT environment / adapter | 策略层不直连 QMT，adapter 边界清晰 | `tests/test_cr015_qmt_environment_boundary.py`、`tests/test_cr015_qmt_adapter_contract.py` |
| OMS 状态机 | partial fill、cancel、reject、unknown、timeout | `tests/test_cr015_oms_state_machine.py` |
| Pre-trade risk | 任一失败 adapter_calls=0 | `tests/test_cr015_pretrade_risk_gate.py` |
| Broker lake | 外置 schema、redaction、未授权 write=0 | `tests/test_cr015_broker_lake_schema_writer.py` |
| Shadow pipeline | target portfolio -> intent -> risk -> mock event | `tests/test_cr015_shadow_order_intent_pipeline.py` |
| Stage gate | 不得跳阶段，缺授权 blocked | `tests/test_cr016_simulation_order_enable_gate.py`、`tests/test_cr016_runbook_approval_gates.py` |
| Reconciliation / kill switch | 对账报告、heartbeat、kill switch fail-closed | `tests/test_cr016_reconciliation_service_reports.py`、`tests/test_cr016_monitoring_kill_switch.py` |
| 文档 / incident | runbook、incident playbook 不授权真实操作 | `tests/test_cr016_docs_incident_playbooks.py` |

## 手工验证

| 场景 | 预期 |
|---|---|
| 启动 CR-021 simulation | 必须先重新执行 CP2/CP3/CP5，并明确账户、资金、日期、操作范围和回滚 |
| 真实 broker evidence | 必须脱敏，不记录账户号、密码、token、session、cookie、真实私有路径 |

