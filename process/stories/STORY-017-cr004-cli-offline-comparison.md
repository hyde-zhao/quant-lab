---
story_id: "STORY-017"
title: "CR-004 CLI offline 闭环与多源比对接口"
story_slug: "cr004-cli-offline-comparison"
status: "verified"
priority: "P0"
wave: "CR4-W3"
depends_on: ["STORY-016"]
dependency_contracts:
  - upstream: "STORY-016"
    type: "contract"
    required: "reader、validation、catalog contract frozen"
file_ownership:
  primary:
    - "market_data/cli.py"
    - "market_data/comparison.py"
    - "tests/test_market_data_cli_comparison.py"
  shared:
    - "pyproject.toml"
    - "uv.lock"
  merge_owner: "STORY-017"
  forbidden:
    - "engine/**"
    - "experiments/**"
    - "delivery/**"
    - "credentials"
    - "real data"
lld_gate:
  required_inputs:
    - "process/HLD.md#217-关键流程"
    - "process/ARCHITECTURE-DECISION.md#adr-010真实联网-adapter-默认关闭fakeoffline-为默认测试路径"
    - "process/ARCHITECTURE-DECISION.md#adr-012多源校验先稳定接口真实多源比对后置启用"
    - "process/stories/STORY-017-cr004-cli-offline-comparison.md"
  status: "ready-for-review"
  lld_path: "process/stories/STORY-017-cr004-cli-offline-comparison-LLD.md"
  cp5_precheck: "process/checks/CP5-CR004-BATCH-C-STORY-017-LLD-PRECHECK.md"
  cp5_review: "checkpoints/CP5-CR004-BATCH-C-STORY-017-LLD-REVIEW.md"
  confirmed: true
  confirmed_by: "user"
  confirmed_at: "2026-05-17T14:25:58+08:00"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  cp5_required: true
  cp5_status: "approved"
  implementation_allowed: true
  cp6_status: "PASS"
  cp6_checkpoint: "process/checks/CP6-STORY-017-cr004-cli-offline-comparison-CODING-DONE.md"
  verification_status: "PASS"
  cp7_checkpoint: "process/checks/CP7-STORY-017-cr004-cli-offline-comparison-VERIFICATION-DONE.md"
created_at: "2026-05-17"
updated_at: "2026-05-17"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-004"
---

# STORY-017：CR-004 CLI offline 闭环与多源比对接口

## 目标

提供 `market_data` 的 offline CLI 闭环和 fake/reference 多源比对接口，使用户可以在无网络默认路径完成 plan/fetch/normalize/validate/read 或等价流程。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | CR-004-AC-006, CR-004-AC-007 |
| HLD | §21.7 关键流程；§21.8 非功能需求；§21.9 风险与应对 |
| ADR | ADR-010, ADR-012 |

## 开发上下文（dev_context）

**背景说明**：Story-014..016 形成包契约、fake 获取、canonical、quality 和 reader。本 Story 把这些能力串成用户可执行入口，并为真实多源比对前稳定 comparison 输出形态。

**输入文件**：STORY-014..016 Story/LLD、`market_data/runtime.py`、`market_data/storage.py`、`market_data/normalization.py`、`market_data/validation.py`、`market_data/readers.py`、`market_data/catalog.py`。

**输出文件**：`market_data/cli.py`、`market_data/comparison.py`、`tests/test_market_data_cli_comparison.py`；如需 CLI entry point，允许修改 `pyproject.toml` / `uv.lock`，但必须通过 uv 管理。

**接口约定**：

| 接口 | 输入 | 输出 | 约束 |
|---|---|---|---|
| CLI `plan` | dataset、source、date range、symbols | plan summary | 不调用 connector |
| CLI `fetch` | 默认 source=fake/offline | raw + manifest summary | 真实 source 必须显式 `--enable-real-source` 或等价配置 |
| CLI `normalize` | manifest/lake root | canonical summary | 不联网 |
| CLI `validate` | dataset/lake root | quality summary | 不联网 |
| CLI `read` | dataset/filter | 行数/样例或输出路径 | 只读 reader |
| `compare_sources(left, right, keys, fields, tolerance)` | 两个 canonical/reference frame | comparison result | 默认 fake/reference；真实多源后置 |

comparison 输出字段至少包含：`dataset`、`key`、`field`、`left_source`、`right_source`、`left_value`、`right_value`、`diff`、`tolerance`、`status`。

**设计约束**：

- CLI 默认路径必须 fake/offline。
- CLI smoke test 不访问网络、不需要凭据、不写真实数据目录。
- 真实 source 未启用时，命令必须 fail fast 并说明需要显式启用。
- CLI `validate` 的第一版质量报告输出必须遵守 `process/constraints/CR004-QUALITY-DATALOADER-CONFIRMATION-CONSTRAINTS-2026-05-17.md`：CSV 为 canonical source，Markdown 只做人类渲染；输出 `fetch_status`、`dataset_status`、coverage、显式阈值、denominator 和可复现字段。
- 多源比对默认只用 fake/reference fixture。
- 不修改 `engine/**` 或 `experiments/**`。

**命名规范**：CLI 命令名用小写动词：`plan`、`fetch`、`normalize`、`validate`、`read`、`compare`；测试文件名保持 `test_market_data_cli_comparison.py`。

**平台目标**：本地命令行数据湖操作入口。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| STORY-016 | contract | reader/validation/catalog API 已冻结 | STORY-016 CP5 通过；开发默认等待 STORY-016 verified | 本 Story 串联前面接口，不重新定义 schema |

### 文件系统布局

```text
market_data/
├── cli.py
└── comparison.py
tests/
└── test_market_data_cli_comparison.py
```

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| S017-T1 | 创建 | `market_data/cli.py` | 实现 plan/fetch/normalize/validate/read 或等价子命令 |
| S017-T2 | 创建 | `market_data/comparison.py` | 实现 fake/reference 多源比对接口 |
| S017-T3 | 修改 | `pyproject.toml`, `uv.lock` | 如需要 console script，使用 uv 管理依赖和锁定 |
| S017-T4 | 创建 | `tests/test_market_data_cli_comparison.py` | 覆盖 CLI offline smoke、多源比对、真实 source 默认关闭 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_market_data_cli_comparison.py`；CLI smoke 可通过 `uv run --python 3.11 python -m market_data.cli ...` 或 console script。

**验证方式**：单元测试 + CLI smoke + 临时目录。

**依赖环境**：Python 3.11、uv、pytest；不需要网络或凭据。

**关键验证场景**：

- plan 不调用 connector。
- fetch 默认 fake，写 raw + manifest。
- normalize/validate/read 串联完成。
- compare 输出字段完整。
- validate 输出或消费的质量报告满足 CSV canonical、Markdown human-only、fetch/dataset 双状态、coverage 和可复现字段约束。
- 指定真实 source 但未启用时 fail fast。

## 量化验收标准（acceptance_criteria）

- [ ] CLI 至少覆盖 5 个动作或等价闭环：plan、fetch、normalize、validate、read。
- [ ] CLI offline smoke 在临时目录完成 raw -> manifest -> canonical -> quality -> read。
- [ ] comparison 输出至少 10 个字段，覆盖 dataset/key/field/source/value/diff/tolerance/status。
- [ ] validate 输出或消费的质量报告满足 CSV canonical、Markdown human-only、fetch/dataset 双状态、coverage 和可复现字段约束。
- [ ] 默认 CLI 网络调用次数为 0。
- [ ] 真实 AkShare/Tushare/TickFlow 未启用时全部 fail fast。
- [ ] 不修改 `engine/**`、`experiments/**`、`delivery/**`，不写真实数据或凭据。

## 后续 LLD 输入约束

LLD 必须明确 CLI 参数、退出码、错误消息、临时目录测试策略和是否需要 console script，并消费 `process/constraints/CR004-QUALITY-DATALOADER-CONFIRMATION-CONSTRAINTS-2026-05-17.md` 中与质量报告和实现边界相关的约束。若新增 console script，必须说明 `pyproject.toml` / `uv.lock` 修改与回滚方式。

## 阻塞说明

无 BLOCKING；真实多源比对需等 source/interface、凭据和字段口径确认后另行启用。
