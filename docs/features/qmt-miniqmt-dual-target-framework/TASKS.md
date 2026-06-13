---
status: "draft-cp4"
version: "1.1"
feature_id: "FEAT-09"
---

# Feature Tasks: QMT / MiniQMT Dual-Target Strategy Delivery Framework

| TASK-ID | 顺序 | 任务 | 输入 | 输出文件 | 文件所有权 | 验证入口 | 状态 |
|---|---:|---|---|---|---|---|---|
| FEAT-09-T01 | 1 | 冻结双目标架构和 StrategyCoreContract | HLD-CR046 / ADR-CR046 | `docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md` | primary | HLD / CP5 | pending |
| FEAT-09-T02 | 2 | 定义策略包目录、manifest 和 schema | FEAT-09-T01 | `docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md` | primary | schema review | pending |
| FEAT-09-T03 | 3 | 定义策略包 artifact、checksum、传输通道和 QMT terminal 人工导入合同 | FEAT-09-T02 | `docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md` | primary | transfer contract review | pending |
| FEAT-09-T04 | 4 | 定义 QMT terminal target contract | FEAT-09-T03 | `docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md` | primary | target review | pending |
| FEAT-09-T05 | 5 | 定义 MiniQMT runner install dry-run 设计 | FEAT-09-T02 | `docs/qmt/CR046-MINIQMT-RUNNER-INSTALL-DESIGN.md` | primary | install design review | pending |
| FEAT-09-T06 | 6 | 定义验证框架与证据分级 | FEAT-09-T01..T05 | `docs/qmt/CR046-VERIFICATION-FRAMEWORK.md` | primary | TEST-PLAN | pending |
| FEAT-09-T07 | 7 | 定义后续策略交付和 runner 实机 gate | FEAT-09-T06 | `process/changes/CR-046-FOLLOW-UP-TRACKING-2026-06-13.md` | shared | CP8 follow-up review | pending |
| FEAT-09-T08 | 8 | 定义研究框架反向完善合同 | FEAT-09-T01 / S07 | `docs/research/CR046-RESEARCH-FRAMEWORK-FOLLOWUP.md` | primary | CR051 readiness review | pending |

## 阻塞项

| Blocker ID | 影响 TASK | 问题 | 需要谁决策 | 推荐处理 |
|---|---|---|---|---|
| BLK-CR046-01 | T03 / T04 / T05 | 真实 QMT / MiniQMT runtime 未授权 | user / future runtime gate | 当前保持 design-only，后置 CR049 / runtime authorization |
| BLK-CR046-02 | T06 | 首个具体策略未选择 | user / future CR047 | CR046 只定义 gate，不选择策略 |
