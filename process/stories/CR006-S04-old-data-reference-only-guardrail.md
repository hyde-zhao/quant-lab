---
story_id: "CR006-S04-old-data-reference-only-guardrail"
title: "旧 data reference-only 护栏"
story_slug: "old-data-reference-only-guardrail"
status: "lld-ready"
priority: "P1"
wave: "CR006-BATCH-A"
depends_on:
  - "CR006-S01-tushare-first-data-acquisition-runbook"
  - "CR006-S02-canonical-gold-lightweight-engine-adapter"
  - "CR006-S03-backtrader-clean-feed-contract"
dependency_contracts:
  - upstream: "CR006-S01-tushare-first-data-acquisition-runbook"
    type: "contract"
    required: "Tushare-first 事实源与 no-old-data 采集边界已冻结"
  - upstream: "CR006-S02-canonical-gold-lightweight-engine-adapter"
    type: "runtime"
    required: "轻量 engine 不默认 fallback repo data 的行为已冻结"
  - upstream: "CR006-S03-backtrader-clean-feed-contract"
    type: "runtime"
    required: "Backtrader clean feed 与 no raw/manifest/token 运行边界已冻结"
file_ownership:
  primary:
    - "tests/test_cr006_old_data_reference_guardrail.py"
  shared:
    - "README.md"
    - "docs/USER-MANUAL.md"
    - ".gitignore"
  merge_owner: "CR006-S04-old-data-reference-only-guardrail"
  forbidden:
    - "engine/**"
    - "experiments/**"
    - "market_data/**"
    - "data/**"
    - ".env"
    - "credentials"
    - "delivery/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#2313-gotchas"
    - "process/ARCHITECTURE-DECISION.md#adr-018tushare-first-structured-lake-与运行时消费面分离"
    - "process/stories/CR006-S01-tushare-first-data-acquisition-runbook.md"
    - "process/stories/CR006-S02-canonical-gold-lightweight-engine-adapter.md"
    - "process/stories/CR006-S03-backtrader-clean-feed-contract.md"
    - "process/stories/CR006-S04-old-data-reference-only-guardrail.md"
  status: "ready"
  cp5_batch: "CR006-BATCH-A"
dev_gate:
  lld_confirmed: false
  dependencies_satisfied: false
  required_contracts:
    - "old repo data reference-only wording frozen"
    - "no default fallback to repo data behavior frozen"
    - "future old data comparison requires separate authorization"
  file_conflict_free: false
  cp5_required: true
  implementation_allowed: false
created_at: "2026-05-18"
updated_at: "2026-05-18T22:33:23+08:00"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-006"
---

# CR006-S04：旧 data reference-only 护栏

## 目标

固化旧 repo `data/` 的 reference-only 状态：旧数据保持现状，仅供以后人工参考/比对；不删除、不迁移、不复制、不读取、不列出；不作为 Tushare-first 新链路的默认 fallback、迁移源、覆盖证明或测试前提。S04 负责文档、错误提示和 guardrail 的边界，不执行任何真实数据操作。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | CR006-AC-012、CR006-AC-013、CR006-AC-014 |
| HLD | §23.1、§23.4、§23.10、§23.13 |
| ADR | ADR-018 |

## 开发上下文（dev_context）

**背景说明**：用户已明确旧 `data/` 数据来源不明，Tushare 不能被承诺完全覆盖旧数据。因此旧 `data/` 不能继续以 fallback 或兼容入口形式进入默认运行链路。它只能作为人工参考样本，未来如需比对必须另行授权和设计。

**输入文件**：`process/HLD.md`、`process/ARCHITECTURE-DECISION.md`、S01/S02/S03 Story/LLD、`README.md`、`docs/USER-MANUAL.md`、`.gitignore`。

**输出文件**：后续实现可修改 `README.md`、`docs/USER-MANUAL.md`、`.gitignore` 和 `tests/test_cr006_old_data_reference_guardrail.py`。本规划阶段不修改这些交付/代码文件。

**接口约定**：

| 对象 | 输入 | 输出 | 约束 |
|---|---|---|---|
| README / USER-MANUAL | S01/S02/S03 冻结契约、ADR-018 | Tushare-first 数据主线说明、旧 `data/` reference-only 说明 | 只使用占位路径，不写真实路径/凭据 |
| guardrail test | 文档文本、静态配置、错误消息 | 检查 no old data fallback、no credentials、no silent migration | 不读取真实 `data/**` 内容 |
| future comparison note | 用户另行授权状态 | 待授权说明 | 当前 CR 不执行比对 |

**设计约束**：

- 文档必须说明旧 repo `data/` 保持现状，仅供人工参考/比对。
- 文档必须说明新链路以 Tushare structured lake 为事实源。
- 文档必须说明 raw/manifest 是审计层，轻量 engine / Backtrader 不直接消费。
- 文档必须说明缺 Tushare canonical/gold 时应返回 required_missing/remediation spec，而不是 fallback 旧 `data/`。
- 文档不得包含 token、NAS 用户名、密码、真实私有路径。
- 不新增安装脚本，不写 `delivery/**`，不改 engine/experiments/market_data。

**命名规范**：统一使用 `reference-only`、`Tushare-first`、`canonical/gold`、`external legacy_flat`；避免把 repo `data/` 称为 fallback、默认目录或兼容数据源。

**平台目标**：用户文档和 guardrail；默认离线；无真实数据操作。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR006-S04-T1 | 修改 | `README.md` | 增加 Tushare-first 数据主线和旧 `data/` reference-only 说明 |
| CR006-S04-T2 | 修改 | `docs/USER-MANUAL.md` | 增加 runbook：如何使用 Tushare structured lake、如何理解 raw/manifest、何时需要另行授权比对旧数据 |
| CR006-S04-T3 | 修改 | `.gitignore` | 如现有 ignore 不足，补充真实数据形态不入库规则；不得触碰真实 `data/**` |
| CR006-S04-T4 | 创建 | `tests/test_cr006_old_data_reference_guardrail.py` | 静态检查文档/错误消息无旧 data fallback、无真实路径/凭据、无 silent migration |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr006_old_data_reference_guardrail.py`；文档人工审查。

**验证方式**：静态文档扫描、占位路径检查、人工阅读。

**依赖环境**：Python 3.11、uv、pytest；不需要 token、不需要 NAS、不联网；不得读取真实 `data/**` 内容。

**关键验证场景**：

- README 和 USER-MANUAL 均说明 Tushare-first 事实源。
- README 和 USER-MANUAL 均说明旧 repo `data/` reference-only。
- 文档不存在“旧 `data/` 是默认 fallback”的描述。
- 文档不存在 token、NAS 用户名、密码或真实私有路径。
- guardrail 不读取、列出或统计真实 `data/**` 内容。

## 量化验收标准（acceptance_criteria）

- [ ] README 和 USER-MANUAL 均至少各 1 处说明旧 repo `data/` reference-only。
- [ ] 文档中把 repo `data/` 作为默认 fallback、迁移源或覆盖证明的次数为 0。
- [ ] 文档中说明 Tushare structured lake 是新链路事实源。
- [ ] 文档中说明 raw/manifest 是审计层，不是回测运行时输入。
- [ ] 文档中真实 token、NAS 用户名、密码或真实私有路径出现次数为 0。
- [ ] 自动读取、列出、迁移、复制、删除真实 `data/**` 的次数为 0。
- [ ] 不修改 `engine/**`、`experiments/**`、`market_data/**`、真实 `data/**`、`.env`、`delivery/**`。

## 阻塞说明

无 BLOCKING。未来是否读取旧 `data/**` 做覆盖性比对为 OPEN，当前未授权；该问题不阻塞 Tushare-first 设计，但阻塞任何旧数据读取、列出、迁移、复制、删除或覆盖分析。
