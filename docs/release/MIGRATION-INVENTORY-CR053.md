---
status: "implemented-cp6-static"
version: "1.0"
change_id: "CR-053"
title: "Migration Inventory for quant-lab Dry-run"
created_by: "meta-dev"
created_at: "2026-06-14T12:19:53+08:00"
source_story: "process/stories/CR053-S02-repo-inventory-and-path-classification.md"
source_lld: "process/stories/CR053-S02-repo-inventory-and-path-classification-LLD.md"
inventory_surface: "git-tracked-paths-only"
nas_scan_authorized: false
credential_read_authorized: false
---

# Migration Inventory CR053

## 1. 范围和方法

本文是 Git 内静态 inventory 分类合同和人工分类清单，不是文件系统扫描报告。

| 项目 | 处理 |
|---|---|
| 输入面 | `git ls-files` 的 repo-relative tracked paths。 |
| 未跟踪文件 | 不纳入；不做 bulk scan untracked data。 |
| NAS / data lake | 不扫描、不读取、不统计真实内容。 |
| `.env` / token / password / private key | 不读取正文；不作为 inventory 输入。 |
| 输出动作 | 只给 dry-run `move_action`；不移动、重命名、删除或复制文件。 |
| 当前静态摘要 | tracked paths = 2102；docs = 97；process = 1559；代码目录 = 155；tests = 141；reports = 8；release docs = 15。 |

## 2. Inventory 字段合同

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `path_scope` | enum | yes | `repo_tracked` / `generated_release_doc` / `manual_review_only`。 |
| `path_pattern` | string | yes | repo-relative 路径或路径族。 |
| `owner` | string | yes | 当前治理 owner；未知时为 `unknown-owner`。 |
| `artifact_class` | enum | yes | `source_code` / `process_evidence` / `design_doc` / `release_doc` / `test_fixture` / `report_pointer` / `runtime_config_sample` / `large_artifact_pointer` / `sensitive_candidate`。 |
| `storage_root` | enum | yes | S01 root_id；不写真实 NAS 路径。 |
| `move_action` | enum | yes | `keep` / `candidate_move_cr058` / `manual_review` / `do_not_move` / `blocked_sensitive`。 |
| `risk` | enum | yes | `low` / `medium` / `high` / `blocked`。 |
| `verification_rule` | string | yes | CP7 或 CR058 前的验证入口。 |
| `forbidden_content_result` | enum | yes | `path_clear` / `manual_review_required` / `blocked_sensitive` / `not_checked_runtime`。 |

## 3. 路径族人工分类清单

| path_pattern | owner | artifact_class | storage_root | move_action | risk | verification_rule | forbidden_content_result | 说明 |
|---|---|---|---|---|---|---|---|---|
| `docs/design/**` | meta-se / host-orchestrator | design_doc | repo_workspace | keep | low | static review against HLD / ADR / Feature matrix | path_clear | 设计基线保留在 Git。 |
| `docs/features/**` | meta-se / meta-dev | design_doc | repo_workspace | keep | low | feature design / test plan / tasks present | path_clear | Feature 三件套作为 Story 下游输入。 |
| `docs/research/**` | meta-se / meta-doc | design_doc | repo_workspace | keep | low | static review | path_clear | 研究治理、archive 和 identity migration 文档保留。 |
| `docs/qmt/**` | meta-dev / meta-doc | release_doc | repo_workspace | manual_review | medium | QMT no-runtime boundary review | manual_review_required | QMT 相关 runbook 保留，但 CR053 不触发 runtime。 |
| `docs/release/*-CR053.md` | meta-dev | release_doc | repo_workspace | keep | low | CP6 / CP7 static report review | path_clear | 本轮新增静态报告。 |
| `process/stories/CR053-*.md` | meta-dev | process_evidence | repo_workspace | keep | low | CP5/CP6 traceability check | path_clear | 当前 CR053 Story 与 LLD 证据。 |
| `process/checks/CP5-CR053-*` | meta-dev / host-orchestrator | process_evidence | repo_workspace | keep | low | CP5 PASS evidence | path_clear | 设计可实现性证据，必须保留。 |
| `process/checks/CP6-CR053-*` | meta-dev | process_evidence | repo_workspace | keep | low | CP6 checklist | path_clear | 本轮 CP6 自动检查。 |
| `process/checkpoints/CP5-CR053-*` | host-orchestrator | process_evidence | repo_workspace | keep | low | approved checkpoint review | path_clear | CP5 人工批准证据。 |
| `process/context/CP5-CR053-*` / `process/context/CP6-CR053-*` | host-orchestrator / meta-dev | process_evidence | repo_workspace | keep | low | YAML parse + capsule review | path_clear | 胶囊化上下文，不含长日志或凭据。 |
| `process/handoffs/META-DEV-CR053-CP6-*` | host-orchestrator | process_evidence | repo_workspace | keep | low | dispatch evidence review | path_clear | 子 Agent 调度证据；completed_at 由 host 回填。 |
| `process/**` historical non-CR053 | host-orchestrator | process_evidence | repo_workspace | keep | medium | preserve historical audit | manual_review_required | 历史审计证据不批量移动或改写。 |
| `engine/**` | meta-dev | source_code | repo_workspace | keep | medium | existing pytest / code review | path_clear | 本轮不改代码，不纳入 CR053 move。 |
| `market_data/**` | meta-dev | source_code | repo_workspace | keep | high | lake contract / no publish review | path_clear | 数据湖代码保留；CR053 不执行 lake write / publish。 |
| `trading/**` | meta-dev | source_code | repo_workspace | keep | high | no runtime / no account query review | path_clear | 交易模块保留；CR053 不启动 QMT/MiniQMT。 |
| `strategies/**` | meta-dev | source_code | repo_workspace | keep | medium | existing tests | path_clear | 策略代码保留；本轮不迁移。 |
| `experiments/**` | meta-dev | source_code | repo_workspace | keep | medium | existing tests / manual review | path_clear | 实验入口保留；CR053 不运行 provider fetch。 |
| `scripts/**` | meta-dev | source_code | repo_workspace | keep | medium | script-specific review | path_clear | 本轮只运行允许的静态检查，不新增脚本。 |
| `tests/**` | meta-dev / meta-qa | test_fixture | repo_workspace | keep | low | pytest subset when needed | path_clear | 本轮无 Python 代码变更，不跑全量 pytest。 |
| `reports/**` tracked samples | meta-dev / meta-qa | report_pointer | repo_workspace | manual_review | medium | confirm sample size and fixture intent | manual_review_required | 当前 tracked 报告样本保留；不扫描 untracked reports。 |
| `notebooks/**` | meta-dev / meta-doc | report_pointer | repo_workspace | manual_review | medium | notebook scope review | manual_review_required | 不执行 notebook。 |
| `config/data_prep.yaml` | meta-dev | runtime_config_sample | repo_workspace | keep | medium | config static review, no secrets | path_clear | 不读取 `.env`，不替换 lake root。 |
| `.env.example` | meta-dev | runtime_config_sample | repo_workspace | keep | medium | sample-only review | manual_review_required | 仅样例路径；不得推断真实 `.env`。 |
| `pyproject.toml` / `uv.lock` | meta-dev | source_code | repo_workspace | keep | low | uv sync / lock consistency if dependencies change | path_clear | 本轮无依赖变更。 |
| `README.md` / `docs/USER-MANUAL.md` | meta-doc | user_doc | repo_workspace | candidate_move_cr058 | medium | CR058 docs rename review | manual_review_required | 面向未来的 project identity 更新可进入 CR058 候选；CR053 不改写。 |

## 4. Move Action 策略

| move_action | 含义 | 当前数量判定 |
|---|---|---|
| `keep` | 当前 Git 内位置继续保留。 | 主要适用于代码、设计、过程证据、测试和本轮 release docs。 |
| `candidate_move_cr058` | 后续 CR058 可作为 repo-local mechanical move 候选。 | 仅限面向未来的用户文档、项目身份文档或明确迁移文档；本轮不执行。 |
| `manual_review` | 需要人工确认 owner、语义或历史价值。 | 适用于历史 `process/**`、tracked reports、notebook、legacy alias 引用。 |
| `do_not_move` | 不应进入迁移动作。 | 外置 data lake、NAS archive、broker facts 等不在 Git 内的对象。 |
| `blocked_sensitive` | 命中敏感内容边界，必须 fail closed。 | 本轮未读取敏感正文；仅保留规则。 |

## 5. Forbidden Content Policy

| 规则 | 分类 | 行为 |
|---|---|---|
| `.env`、token、password、private key、cookie、session | `blocked_sensitive` | 不读取、不迁移、不入报告正文。 |
| broker raw facts、未脱敏账户、资金、持仓、委托、成交 | `blocked_sensitive` | 不纳入 Git / archive / backup dry-run。 |
| 外置 lake 正文、NAS archive 正文、untracked data | `not_checked_runtime` | CR053 不扫描；后续必须独立授权。 |
| 文件名包含 security / secret boundary 的治理文档 | `manual_review_required` | 路径名可能是治理证据，不代表敏感内容；不读取敏感正文。 |

## 6. CR058 输入阻断项

| Gate | 阻断条件 | 当前处理 |
|---|---|---|
| owner completeness | `unknown-owner` 或 `manual_review` 未清零 | CR058 前人工归类。 |
| forbidden content | 任一 `blocked_sensitive` 被标为 `candidate_move_cr058` | 阻断 CR058。 |
| historical evidence | `process/` / handoff / checkpoint 被批量改写 | 阻断 CR058。 |
| rollback readiness | 缺 rollback_ref / git bundle checkpoint | 阻断 CR058。 |
| runtime authorization | 需要 NAS / lake / QMT / provider / git push | 交回 host-orchestrator 发起独立授权或 CR。 |

## 7. 不授权边界与 guardrail evidence

| 禁止操作 | CR053 CP6 结果 |
|---|---|
| NAS scan / mount / mkdir / copy / delete | 未执行。 |
| untracked data bulk scan | 未执行。 |
| `.env` / token / account / password / private key read | 未执行。 |
| provider fetch / lake write / catalog publish | 未执行。 |
| QMT / MiniQMT runtime / trading action | 未执行。 |
| file move / rename / delete / migration | 未执行。 |
| git push / tag / history rewrite | 未执行。 |

