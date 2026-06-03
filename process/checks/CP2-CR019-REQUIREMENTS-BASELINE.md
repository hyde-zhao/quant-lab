---
checkpoint_id: CP2-CR019-REQUIREMENTS-BASELINE
change_id: CR-019
checkpoint_name: 需求基线自动预检
checkpoint_type: automatic
status: PASS
created_at: "2026-05-30T15:03:02+08:00"
created_by: meta-pm
artifacts:
  - process/REQUIREMENTS.md
  - process/USE-CASES.md
  - process/CLARIFICATION-LOG.md
  - process/checks/CP1-CR019-USE-CASE-COMPLETENESS.md
  - process/discussions/CP2-CR019-SCENARIO-DISCUSSION-LOG.md
  - process/checks/CP2-CR019-DISCUSSION-CHECKPOINT.json
---

# CP2 CR-019 需求基线自动预检

## Entry Criteria

| ID | 检查项 | 结果 | 证据 | 处理意见 |
|---|---|---|---|---|
| EC-01 | CP1 用户场景完备门已完成 | PASS | `process/checks/CP1-CR019-USE-CASE-COMPLETENESS.md` | CP1 结论 PASS |
| EC-02 | `USE-CASES.md` 已增量覆盖 CR-019 | PASS | `process/USE-CASES.md` v1.9；UC-15 至 UC-18 | 可作为需求提取输入 |
| EC-03 | `REQUIREMENTS.md` 保留旧基线并追加 CR-019 修订记录 | PASS | `process/REQUIREMENTS.md` v1.11 修订记录 | REQ-001 至 REQ-137 保留，新增 REQ-138 至 REQ-160 |
| EC-04 | `CLARIFICATION-LOG.md` 已记录 D1-D7、Q40 确认和开放问题状态 | PASS | `process/CLARIFICATION-LOG.md` CR-019 调研、D1-D7、Q-039 至 Q-044 | 无 CP2 blocker |
| EC-05 | 本轮安全范围符合用户限制 | PASS | `REQUIREMENTS.md` A-046 / REQ-152；handoff 安全声明 | 未实现代码、未新增依赖、未真实 QMT / provider / 数据写入 |

## Checklist

| ID | 检查项 | 结果 | 证据 | 处理意见 |
|---|---|---|---|---|
| C-01 | CR-019 新需求条目编号连续且不重排旧编号 | PASS | REQ-138 至 REQ-160 | 保留 REQ-001 至 REQ-137 |
| C-02 | 每条新增功能 / 约束 / 后置需求均有来源场景 | PASS | REQ-138 至 REQ-160 的来源列 | 来源覆盖 UC-15 至 UC-18、CR-019 D1-D7 与用户 C/S 模块补充 |
| C-03 | 每条新增需求有可检查验收条件 | PASS | REQ-138 至 REQ-160 验收条件 | 均为 Given / When / Then 或可检查条件 |
| C-04 | D1 Backtrader 后置 optional backend 已覆盖 | PASS | REQ-139；REQ-155 | 不作为阶段六 P0 |
| C-05 | D2 Qlib 后置 isolated runner 已覆盖 | PASS | REQ-140；REQ-156 | 不作为默认依赖或事实源 |
| C-06 | D3 分钟数据后置 Spike 已覆盖 | PASS | REQ-141；REQ-157 | 不阻断日频多因子 admission |
| C-07 | D4 QMT xtdata 不进 WSL 主路径、Windows QMT bridge 已覆盖 | PASS | REQ-142；REQ-149 | WSL 不直接依赖 xtquant |
| C-08 | D5 QMT Level2 后置触发已覆盖 | PASS | REQ-143；REQ-158 | 不首轮申请 Level2 |
| C-09 | D6 shadow + 5 日 dry-run 后再申请 simulation 已覆盖 | PASS | REQ-144；REQ-154 | 通过后仍需 per-run authorization |
| C-10 | D7 FastAPI local bridge 主选、signed file drop fallback 已覆盖 | PASS | REQ-145；REQ-150 | fallback 不能自动真实 QMT |
| C-11 | FastAPI 完整 QMT endpoint matrix 与运行门控已覆盖 | PASS | CR-019 FastAPI Bridge 契约；REQ-146；REQ-147 | simulation / live / account / cancel / query 等完整接口类别必须支持；真实转发由 run mode / stage gate / risk gate 控制 |
| C-12 | 局域网无应用层鉴权与可选最简 token/HMAC 已覆盖 | PASS | REQ-148；Q-039 | CP3 需冻结无鉴权或 token/HMAC 的具体条件；鉴权策略不削减 QMT 功能 |
| C-13 | Windows gateway 独立命令、WSL / Windows 部署、绑定、防火墙、heartbeat 已覆盖 | PASS | REQ-149；Q-039 | CP3 需冻结 Windows 安装/启动/停止合同 |
| C-13A | QMT 独立 C/S 模块与 C 侧接口形态已覆盖 | PASS | REQ-159；REQ-160；Q-044 | C 侧推荐 Python client / 函数调用为主 + 薄 CLI；S 侧为 Windows gateway |
| C-14 | fallback 行为已覆盖 | PASS | REQ-150；Q-042 | blocked-only 或人工 dry-run / signed file drop，禁止自动绕过 gateway 触发真实 QMT |
| C-15 | 日志脱敏和敏感信息禁入库已覆盖 | PASS | REQ-151；RA-049 | 覆盖 token、账户、session、cookie、交易密码、`.env`、真实私有路径 |
| C-16 | CP2/设计阶段禁止真实操作，后续真实调用必须经 gateway 审计 | PASS | REQ-152；A-046 | CP2/CP3/CP4/CP5 前真实调用计数为 0；后续批准的 simulation/live 调用必须经 gateway、run_id、stage、mode 和脱敏日志 |
| C-17 | QMT 文档能力背景边界已覆盖 | PASS | REQ-153；TS-019-09 | 不推断当前真实账户或 Level2 权限 |
| C-18 | Backtrader / Qlib / minute / Level2 后置触发条件已覆盖 | PASS | REQ-155 至 REQ-158 | Deferred Ideas 已记录 |
| C-19 | 风险与假设已补齐 | PASS | RA-048 至 RA-055；A-041 至 A-050 | 关键风险有缓解措施 |
| C-20 | 里程碑建议已更新 | PASS | M16 至 M18 | 支撑 meta-se 做 HLD / Story Plan |
| C-21 | 明确排除项已更新 | PASS | `REQUIREMENTS.md` Out of Scope CR-019 条目 | 覆盖无实现、无依赖、无真实 QMT、无凭据、无 fetch、无真实 data/reports/delivery |
| C-22 | CP2 discussion 追溯材料完整 | PASS | discussion log；checkpoint JSON | 可供 meta-po 写 CP2 Decision Brief |
| C-23 | 是否存在未豁免 FAIL | PASS | 本 checklist | 无 FAIL |
| C-24 | 是否存在 CP2 blocker | PASS | `CLARIFICATION-LOG.md` Q-039 至 Q-044；`checkpoints/CP2-CR019-REQUIREMENTS-BASELINE.md` | 无自动预检 blocker；Q-040 已按用户确认采用推荐方案，Q-044 进入 CP2/CP3 决策 |

## Exit Criteria

| ID | 检查项 | 结果 | 证据 | 处理意见 |
|---|---|---|---|---|
| XC-01 | 新增需求覆盖所有新增场景 | PASS | UC-15 至 UC-18；REQ-138 至 REQ-160 | 场景到需求追溯完整 |
| XC-02 | BLOCKING 未决项为 0 | PASS | `CLARIFICATION-LOG.md` Q-039 至 Q-044 | 无 CP2 blocker；未决细节推迟到 CP3/HLD |
| XC-03 | 新增功能需求均有验收条件 | PASS | REQ-138 至 REQ-160 | 可用于 HLD、Story 和 QA 策略 |
| XC-04 | 风险与假设表已覆盖 CR-019 关键风险 | PASS | RA-048 至 RA-055；A-041 至 A-050 | 风险可追溯到需求 |
| XC-05 | CP2 Decision Brief 输入充分 | PASS | `CLARIFICATION-LOG.md` CP2 Decision Brief 输入；discussion log | meta-po 可据此发起人工确认 |
| XC-06 | 需求基线不授权实现或真实操作 | PASS | REQ-152；A-046；Out of Scope | 后续 CP3/CP4/CP5 前不得实现或真实运行 |

## Deliverables

| 交付物 | 状态 | 路径 |
|---|---|---|
| CR-019 增量需求基线 | PASS | `process/REQUIREMENTS.md` |
| CR-019 增量场景基线 | PASS | `process/USE-CASES.md` |
| 澄清与调研日志 | PASS | `process/CLARIFICATION-LOG.md` |
| CP1 自动检查 | PASS | `process/checks/CP1-CR019-USE-CASE-COMPLETENESS.md` |
| CP2 discussion log | PASS | `process/discussions/CP2-CR019-SCENARIO-DISCUSSION-LOG.md` |
| CP2 discussion checkpoint | PASS | `process/checks/CP2-CR019-DISCUSSION-CHECKPOINT.json` |
| CP2 自动预检 | PASS | `process/checks/CP2-CR019-REQUIREMENTS-BASELINE.md` |

## 结论

**PASS**。CR-019 需求基线已覆盖 D1-D7、阶段六多因子模拟盘准入、Q40 多基准 + primary benchmark、QMT 独立 C/S 模块、C 侧 Python client 主接口 + 薄 CLI 推荐、Windows QMT FastAPI gateway、完整 QMT endpoint matrix、Windows 独立 gateway 命令、受控局域网无应用层鉴权 / 可选最简 token-HMAC、WSL / Windows 部署、运行门控、fallback、日志脱敏、CP2/设计阶段禁止真实操作，以及 Backtrader / Qlib / minute / Level2 后置触发条件。

不存在阻断 CP2 自动预检的 BLOCKING 问题。用户已纠正 Q-039/Q-041/Q-042，同意 Q-043，并确认 Q-040 推荐方案；Q-044 的 C 侧接口形态推荐方案已纳入 Decision Brief。建议 meta-po 基于本文件发起修订后的 CP2 人工确认；CP2 approve 后可进入 CR-019 CP3。
