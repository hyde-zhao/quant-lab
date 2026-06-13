---
story_id: "CR046-S04-miniqmt-runner-install-and-runtime-boundary"
title: "MiniQMT runner 安装设计与运行边界"
story_slug: "miniqmt-runner-install-and-runtime-boundary"
status: "ready-for-verification"
priority: "P0"
wave: "CR046-W2-TARGETS-INSTALL"
depends_on:
  - "CR046-S02-strategy-package-contract-and-schema"
dependency_type:
  - "contract"
cp5_batch: "CR046-DUAL-TARGET-FRAMEWORK-BATCH-A"
feature_design_refs:
  - "docs/features/qmt-miniqmt-dual-target-framework/DESIGN.md"
  - "docs/features/runtime-authorization-safety/DESIGN.md"
lld_policy:
  required_level: "full-lld"
  trigger_reasons: ["install-design", "external-runtime", "credential-boundary"]
  rationale: "MiniQMT runner 触及 Windows 安装、uv、依赖隔离、日志、kill switch 和真实连接边界，必须 full-lld。"
  waiver_reason: ""
  revisit_condition: "MiniQMT 权限开通或 CR049 启动时。"
  evidence_path: "process/stories/CR046-S04-miniqmt-runner-install-and-runtime-boundary-LLD.md"
file_ownership:
  primary:
    - "docs/qmt/CR046-MINIQMT-RUNNER-INSTALL-DESIGN.md"
  shared:
    - "docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md"
    - "docs/qmt/CR046-VERIFICATION-FRAMEWORK.md"
  merge_owner: "CR046-S04-miniqmt-runner-install-and-runtime-boundary"
  forbidden:
    - "real MiniQMT install"
    - "MiniQMT / XtQuant connection"
    - "credential read"
    - "market subscription"
    - "submit/cancel"
lld_gate:
  required_inputs:
    - "CR046-S02-strategy-package-contract-and-schema"
    - "docs/features/qmt-miniqmt-dual-target-framework/DESIGN.md"
  design_evidence_type: "full-lld"
  design_evidence_path: "process/stories/CR046-S04-miniqmt-runner-install-and-runtime-boundary-LLD.md"
  status: "confirmed"
dev_gate:
  design_evidence_confirmed: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
task_count: 5
created_at: "2026-06-13T22:57:34+08:00"
updated_at: "2026-06-14T00:16:26+08:00"
change_id: "CR-046"
---

# CR046-S04：MiniQMT runner 安装设计与运行边界

## 目标

定义 MiniQMT runner 的 Windows 目录、uv 管理、依赖隔离、配置模板、日志、kill switch、start/stop/status 合同、upgrade/uninstall/rollback 和 install dry-run 方案。

## 开发上下文（dev_context）

**输入文件**：CR046-S02、FEAT-09 DESIGN、FEAT-07 runtime safety。

**输出文件**：`docs/qmt/CR046-MINIQMT-RUNNER-INSTALL-DESIGN.md`。

**设计约束**：本 Story 不真实安装、不连接 MiniQMT / XtQuant、不读取凭据、不订阅行情、不启动 runner runtime。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR046-S04-T1 | 设计 | `docs/qmt/CR046-MINIQMT-RUNNER-INSTALL-DESIGN.md` | 定义 Windows 目录和 uv policy |
| CR046-S04-T2 | 设计 | 同上 | 定义依赖隔离和 xtquant 后置策略 |
| CR046-S04-T3 | 设计 | 同上 | 定义 redacted config / log / kill switch |
| CR046-S04-T4 | 设计 | 同上 | 定义 upgrade / uninstall / rollback |
| CR046-S04-T5 | 校验 | 同上 | 明确真实 install / connection not-authorized |

## 技术说明

| 项目 | 内容 |
|---|---|
| 设计证据类型 | full-lld |
| 文件影响 | 新增 MiniQMT runner install design 文档 |
| 接口 / 数据 / 权限变化 | 只定义 install dry-run 合同，不新增 runtime |
| 测试入口 | install design review / redaction review |

## 量化验收标准（acceptance_criteria）

- [ ] 安装设计覆盖 Windows root、uv、dependency_policy、config、logs、kill_switch、upgrade/uninstall/rollback 至少 8 类字段。
- [ ] 明确 `xtquant` / MiniQMT 依赖不进入 Linux 主依赖。
- [ ] credential_read、real_install、MiniQMT connection、market_subscription 均为 false。

## 阻塞说明

真实安装和只读连接必须后置 CR049 或独立 runtime_authorization gate。
