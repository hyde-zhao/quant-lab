---
status: "draft-cp4"
version: "1.0"
feature_id: "FEAT-09"
---

# Feature Test Plan: QMT / MiniQMT Dual-Target Strategy Delivery Framework

## 测试范围

| Scope ID | 覆盖内容 | 来源 Story / Scenario | 测试层级 | 自动化状态 |
|---|---|---|---|---|
| TP-CR046-01 | StrategyCoreContract 字段完整性和平台无关性 | CR046-S01 / S02 | unit / static | planned |
| TP-CR046-02 | StrategyPackageContract 目录、manifest、target 列表和 docs bundle | CR046-S02 | unit / fixture | planned |
| TP-CR046-03 | QMT terminal target 入口、配置、导入说明和 shadow evidence schema | CR046-S03 | static / review | planned |
| TP-CR046-04 | MiniQMT runner install dry-run、uv、依赖隔离、rollback、kill switch | CR046-S04 | static / dry-run-design | planned |
| TP-CR046-05 | StrategyValidationEvidence 证据分级和 runtime claim guardrail | CR046-S05 | unit / docs guardrail | planned |
| TP-CR046-06 | CR047 / CR049 / CR051 follow-up gate 可追溯 | CR046-S06 / S07 | review | planned |

## 风险驱动测试

| Risk ID | 风险 | 测试方式 | 证据 | 未覆盖原因 |
|---|---|---|---|---|
| R-CR046-01 | core 导入 QMT / XtQuant / MiniQMT | 静态扫描 forbidden import | CP7 TEST-REPORT | N/A |
| R-CR046-02 | install design 读取真实凭据 | 配置模板和日志脱敏检查 | CP7 REVIEW | N/A |
| R-CR046-03 | fixture/static pass 被声明为 runtime verified | 文档 guardrail | CP7 REVIEW / CP8 | N/A |
| R-CR046-04 | follow-up CR 被遗漏 | 台账和 Story trace review | CP4 / CP8 | N/A |

## 权限 / 安全 / 失败路径

| Case ID | 触发条件 | 期望行为 | 测试入口 |
|---|---|---|---|
| SEC-TC-01 | strategy core 出现 `xtquant` / `qmt` native import | fail closed，CP7 blocked | static guardrail |
| SEC-TC-02 | runner config 示例包含真实账号、token、session、路径原文 | fail closed，redaction blocker | docs / config review |
| SEC-TC-03 | 文档把 fixture pass 写成 runtime verified | docs guardrail FAIL | docs test / review |
| SEC-TC-04 | target contract 包含 submit/cancel/simulation/live 默认可用 | safety review FAIL | CP7 / CP8 |

## 手工验收

| Check ID | 操作 | 期望结果 | 责任方 |
|---|---|---|---|
| MAN-CR046-01 | 审查策略包目录和 manifest 字段 | 至少覆盖 core、qmt_terminal、miniqmt_runner、validation、docs 六类对象 | human / qa |
| MAN-CR046-02 | 审查 MiniQMT runner install dry-run 设计 | 明确真实安装和连接均 not-authorized | human / qa |
| MAN-CR046-03 | 审查后续 CR gate | CR047 / CR049 / CR051 均有触发条件和消费对象 | human / qa |
