---
status: "implemented-cp6-static"
version: "1.0"
change_id: "CR-053"
title: "Path References and Legacy Alias Dry-run"
created_by: "meta-dev"
created_at: "2026-06-14T12:19:53+08:00"
source_story: "process/stories/CR053-S03-path-reference-and-legacy-alias-dry-run.md"
source_lld: "process/stories/CR053-S03-path-reference-and-legacy-alias-dry-run-LLD.md"
bulk_rewrite_authorized: false
git_history_rewrite_authorized: false
---

# Path References CR053

## 1. 范围和方法

本文输出 `local_backtest` / `quant-lab` / legacy alias 的 dry-run 分类，不批量改写任何文件。

| 项目 | 处理 |
|---|---|
| 输入面 | Git 跟踪文本中的路径 / alias 参考；已排除 `.env`、`*.env`、key、secret、token、pem 类路径。 |
| 静态摘要 | 参考文件数约 310：`process/` 约 260、`docs/` 约 37、`checkpoints/` 约 6、其他少量 README / DEV-LOG / tests / engine / runs / notebooks。 |
| 输出动作 | 只写 `proposed_action`，不执行替换。 |
| 历史证据策略 | `process/`、`checkpoints/`、handoff、DEV-LOG 中的历史 `local_backtest` 默认 preserve-audit 或 manual-review。 |
| CR058 关系 | 面向未来的 README / USER-MANUAL / release 文档可作为 CR058 候选，仍需人工确认和 rollback_ref。 |

## 2. 分类模型

| classification | proposed_action | manual_review_required | 适用对象 |
|---|---|---:|---|
| `canonical_quant_lab` | keep | false | 新增 CR053 / CR051 后面向未来的 `quant-lab` 口径。 |
| `legacy_alias_keep` | keep | false | 明确说明 `local_backtest` 是 legacy alias 的文档。 |
| `mechanical-candidate` | replace_in_cr058 | true | 面向未来的用户文档、路径示例、项目根说明。 |
| `manual-review` | manual_review | true | 语义不确定的 docs、代码注释、notebook、reports pointer。 |
| `preserve-audit` | keep | true | 历史 `process/`、CR、handoff、checkpoint、DEV-LOG、旧审计证据。 |
| `blocked_sensitive` | block | true | 凭据、账号、token、secret、private key 或未脱敏账户信息；本轮未读取正文。 |

## 3. Reference Dry-run 分类清单

| reference_family | 示例范围 | context_kind | classification | proposed_action | reason | CR058 gate |
|---|---|---|---|---|---|---|
| `quant-lab` canonical name | CR053 HLD / ADR / Feature / Story / release docs | design_doc / release_doc | canonical_quant_lab | keep | 新迁移目标和后续文档主名。 | 无阻断。 |
| `local_backtest` legacy alias in BLUEPRINT / DOMAIN-MAP | `docs/design/BLUEPRINT.md`、`docs/design/DOMAIN-MAP.md` | design_doc | legacy_alias_keep | keep | 已明确 legacy alias 和审计名。 | 不改写。 |
| `local_backtest` in README / USER-MANUAL project root descriptions | `README.md`、`docs/USER-MANUAL.md` | user_doc | mechanical-candidate | replace_in_cr058 | 面向用户的项目根说明未来可切到 `quant-lab`，但需保留兼容段。 | 需人工确认替换范围。 |
| historical CR / process references | `process/**`、`checkpoints/**`、`process/handoffs/**`、`DEV-LOG.md` | process_evidence | preserve-audit | keep | 历史记录中的项目名是当时事实，批量改写会破坏追溯。 | 不允许 mechanical rewrite。 |
| old workspace path references | `work/studies/quant-trading/local_backtest` in historical docs | process_evidence / user_doc | preserve-audit 或 manual-review | keep / manual_review | CR001 历史清理证据应保留；面向未来文档可独立修订。 | 人工区分历史与用户说明。 |
| QMT C/S references to local_backtest C side | QMT docs / stories / handoffs | design_doc / runtime_doc | manual-review | manual_review | 可能是组件边界名，不应无差别改成新 repo 名。 | CR058 前由 QMT owner 审查。 |
| `LOCAL_BACKTEST_*` env aliases | historical design references | runtime_config | manual-review | manual_review | 可能涉及兼容变量，不可在 CR053 替换。 | 需要兼容期策略。 |
| `MARKET_DATA_LAKE_ROOT` references | data lake docs / code / HLD | runtime_config / source_code | legacy_alias_keep | keep | ADR-CR053-006 明确保持现有入口。 | 不替换为 `QUANT_LAB_MARKET_DATA_LAKE_ROOT`。 |
| `QUANT_LAB_*_ROOT` logical vars | CR053 HLD / NAS mapping | design_doc | canonical_quant_lab | keep | 新 root map 合同变量。 | 真实绑定需后续授权。 |
| sensitive-looking path terms | `secret-boundary` governance docs 等 | process_evidence | manual-review | manual_review | 路径名可能是安全治理文档，不代表读取凭据正文。 | 不输出敏感正文；人工确认。 |

## 4. Mechanical Candidate 规则

| 候选范围 | 可机械替换的前置条件 | 当前状态 |
|---|---|---|
| README 的未来项目名、路径示例 | CR058 CP5 approved、rollback_ref、人工确认保留 legacy alias 段 | not-authorized in CR053 |
| USER-MANUAL 的未来项目根说明 | 与 README 同步，确认不破坏旧命令说明 | not-authorized in CR053 |
| release docs 中的新交付名 | CP8 终验前由 meta-doc / meta-qa 审查 | not-authorized in CR053 |
| pyproject package name | 需要独立 packaging / import compatibility design | out-of-scope |
| remote repository name | 需要独立 runtime_authorization / git remote gate | out-of-scope |

## 5. Preserve-audit 规则

| 范围 | 必须保留原因 |
|---|---|
| `process/checkpoints/**` | 人工门禁和用户确认证据不可重写语境。 |
| `process/checks/**` | 自动检查结果是历史审计证据。 |
| `process/stories/**` historical non-CR053 | Story 设计和实现证据必须保留当时项目名。 |
| `process/handoffs/**` | 子 Agent 调度证据需要保留原 workflow_id 和 agent_id 语境。 |
| `DEV-LOG.md` historical entries | 旧日志是时间线证据，不做机械改写。 |
| legacy `checkpoints/**` | legacy fallback 读取证据，不批量重写。 |

## 6. CR058 References Gate

| Gate | 通过条件 | 缺失 / 失败处理 |
|---|---|---|
| candidate list | README / USER-MANUAL / release docs 的候选替换项已列出 | `references_missing` |
| preserve-audit allowlist | 历史 process / checkpoint / handoff / DEV-LOG 已明确 preserve-audit | `historical_guard_missing` |
| sensitive filter | `.env` / token / key / account 等未进入替换输入 | `blocked_sensitive` |
| rollback_ref | 替换前存在 git commit / bundle checkpoint | `rollback_ref_missing` |
| no bulk rewrite | CR058 仍不得 git history rewrite | `rewrite_scope_blocked` |

## 7. 不授权边界与 guardrail evidence

| 禁止操作 | CR053 CP6 结果 |
|---|---|
| bulk rewrite of historical process / CR / handoff evidence | 未执行。 |
| git history rewrite | 未执行。 |
| remote repo rename / git push / tag | 未执行。 |
| `.env` / token / account / private key read | 未执行。 |
| repo-local mechanical move | 未执行。 |

