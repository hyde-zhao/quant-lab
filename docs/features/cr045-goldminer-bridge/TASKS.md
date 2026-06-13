---
status: draft-for-cp4
version: "1.0"
feature_id: "FEAT-CR045-GOLDMINER-BRIDGE"
source_design: "docs/features/cr045-goldminer-bridge/DESIGN.md"
---

# CR045 Feature Tasks

| TASK-ID | 顺序 | 任务 | 输入 | 输出文件 | 文件所有权 | 验证入口 | 状态 |
|---|---:|---|---|---|---|---|---|
| CR045-S01-T1 | 1 | 设计 Windows bridge security boundary、L1-L5 authorization model 和 not-authorized table。 | HLD、ADR、CP3 checkpoint、CR045 | `process/stories/CR045-S01-windows-bridge-security-boundary-LLD.md` | CR045-S01 primary | CP5 LLD review | pending-cp5 |
| CR045-S01-T2 | 2 | 定义敏感字段分类、zero secret custody、fail-closed decision table。 | `engine/broker_adapter.py` sensitive pattern concepts；Feature DESIGN | `process/stories/CR045-S01-windows-bridge-security-boundary-LLD.md` | CR045-S01 primary | CP5 / CP7 static review | pending-cp5 |
| CR045-S02-T1 | 3 | 设计 bridge health/capabilities schema、schema version 和 fixture response。 | S01 contract；Feature DESIGN | `process/stories/CR045-S02-bridge-health-capabilities-skeleton-LLD.md`；future `engine/goldminer_bridge_contract.py` | CR045-S02 primary / shared merge owner | CP5 LLD review | pending-cp5 |
| CR045-S02-T2 | 4 | 规划 capabilities false flags、not-authorization response 和 bridge contract tests。 | ADR-CR045-002/004 | future `tests/test_cr045_goldminer_bridge_contract.py` | CR045-S02 primary | CP7 fixture/static | pending-cp5 |
| CR045-S03-T1 | 5 | 设计 WSL / Linux client request/response、fixture transport 和 network precheck。 | S01 contract；S02 API schema | `process/stories/CR045-S03-wsl-linux-client-contract-and-network-precheck-LLD.md`；future `engine/goldminer_bridge_client.py` | CR045-S03 primary | CP5 LLD review | pending-cp5 |
| CR045-S03-T2 | 6 | 定义 runtime-not-started behavior，禁止真实 bridge connection。 | Feature DESIGN | future `tests/test_cr045_goldminer_bridge_client.py` | CR045-S03 primary | CP7 static review | pending-cp5 |
| CR045-S04-T1 | 7 | 设计 readonly probe skeleton allowlist、request/response 和 blocked reasons。 | S01/S02/S03 contracts | `process/stories/CR045-S04-readonly-probe-allowlist-and-blocked-first-LLD.md`；future `engine/goldminer_bridge_probe.py` | CR045-S04 primary | CP5 LLD review | pending-cp5 |
| CR045-S04-T2 | 8 | 规划 L4 未授权下 cash/position/order/fill/account state 的 blocked-first tests。 | HLD §15；TEST-PLAN TP-SEC-04 | future `tests/test_cr045_goldminer_readonly_probe.py` | CR045-S04 primary | CP7 fixture/static | pending-cp5 |
| CR045-S05-T1 | 9 | 设计 redaction evidence schema、artifact scan scope 和 zero operation counters。 | S01-S04 contracts；TEST-PLAN | `process/stories/CR045-S05-redaction-and-no-operation-static-validation-LLD.md` | CR045-S05 primary | CP5 LLD review | pending-cp5 |
| CR045-S05-T2 | 10 | 规划 no-operation static validation tests，不读取 `.env` 和凭据材料。 | Feature TEST-PLAN | future `tests/test_cr045_goldminer_no_operation_static.py` | CR045-S05 primary | CP7 static validation | pending-cp5 |
| CR045-S06-T1 | 11 | 在 Story technical-note 中收敛 user runbook、L3/L4/L5 follow-up gates 和 CP8 wording。 | S01-S05 design evidence | `process/stories/CR045-S06-user-runbook-and-follow-up-gates.md#技术说明`；future `docs/goldminer/CR045-BRIDGE-RUNBOOK.md` | CR045-S06 primary | CP5 technical-note review | pending-cp5 |
| CR045-S06-T2 | 12 | 判定 S06 是否因自动 manifest/schema/guard script 升级 full-lld。 | CP5 scope review | S06 Story or LLD if upgraded | CR045-S06 primary | CP5 decision | pending-cp5 |

## 阻塞项

| Blocker ID | 影响 TASK | 问题 | 需要谁决策 | 推荐处理 |
|---|---|---|---|---|
| BLK-CR045-L3 | 全部真实 runtime / readonly / trading tasks | 当前不授权 L3/L4/L5；不得启动 bridge、登录/连接 Goldminer、查询账户、下单/撤单、simulation/live、provider/lake/publish。 | meta-po / user，未来独立 gate | 当前不作为阻塞 CP4；如 CP5/CP6 需要真实行为，停止并发起 runtime_authorization。 |
| BLK-CR045-S06-UPGRADE | CR045-S06-T1/T2 | S06 若新增自动 manifest、schema、guard script 或状态机，technical-note 不足。 | meta-po at CP5 | 升级 S06 为 full-lld 或延后自动化。 |
