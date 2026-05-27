---
story_id: "STORY-004"
title: "离线 Data Loader 与合同校验"
story_slug: "offline-data-loader-contract-validator"
status: "verified"
priority: "P0"
wave: "W1"
depends_on: ["STORY-003"]
created_at: "2026-05-14"
updated_at: "2026-05-15"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
approved_by: "meta-po"
approved_at: "2026-05-15"
lld_handoff: "process/handoffs/META-DEV-LLD-W1-STORY-004-2026-05-15.md"
lld_path: "process/stories/STORY-004-offline-data-loader-contract-validator-LLD.md"
lld_checkpoint: "checkpoints/STORY-004-LLD-CHECKPOINT.md"
lld_checkpoint_status: "superseded-by-lld-batch-package"
batch_lld_plan: "process/LLD-BATCH-PLAN.md"
batch_lld_checkpoint: "checkpoints/STORY-PACKAGE-LLD-CHECKPOINT.md"
cr004_batch_d_lld_revision:
  status: "cp5-approved"
  lld_path: "process/stories/STORY-004-offline-data-loader-contract-validator-LLD.md"
  cp5_precheck: "process/checks/CP5-CR004-BATCH-D-DATALOADER-EXPERIMENT-READONLY-LLD-PRECHECK.md"
  cp5_review: "checkpoints/CP5-CR004-BATCH-D-DATALOADER-EXPERIMENT-READONLY-LLD-REVIEW.md"
  cp5_status: "approved"
  confirmed_by: "user"
  confirmed_at: "2026-05-17T15:53:20+08:00"
  implementation_allowed: true
  scope_note: "Data Loader first, no real fetch revision approved; only authorizes bounded implementation in engine/data_loader.py and pure constants in engine/contracts.py."
---

# STORY-004：离线 Data Loader 与合同校验

## 目标

实现回测主路径的数据加载和合同校验，确保只读取本地 parquet、manifest 和质量报告，不触发任何联网补数。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | REQ-002, REQ-003, REQ-016, REQ-034, REQ-037, REQ-038, REQ-057 |
| HLD | §8.3, §9.1, §9.3, §11, §12.2, §16 M1 |
| ADR | ADR-001, ADR-003, ADR-006 |

## 开发上下文（dev_context）

**背景说明**：Data Loader 是离线主路径的入口，必须拒绝不合规数据，并把 metadata 提供给回测、扫描和报告层。

**输入文件**：`data/prices.parquet`、`data/index_members.parquet`、`data/trade_calendar.parquet`、`data/manifests/data_prep_manifest.jsonl`、`reports/data_quality_report.*`、`engine/contracts.py`。

**输出文件**：`engine/data_loader.py`，必要时修改 `engine/contracts.py`。

**接口约定**：加载函数接收 start_date、end_date、adjustment_policy、quality_policy，返回 `close_df`、universe、calendar、metadata；metadata 包含复权口径、股票池 PIT 标记、覆盖区间、质量状态和数据新鲜度。

**错误约定**：缺必需字段、复权口径混用、交易日历不可排序、股票池缺 `symbol`、质量状态 fail 时拒绝运行；warn 可继续但必须返回披露字段。

**设计约束**：日线收盘价缺 `available_at` 时仅可按 HLD 批准的 T 日收盘后可用规则推导；事件字段不得进入第一版决策。

**命名规范**：加载输出命名为 `close_df`、`universe`、`calendar`、`metadata`；单次参数使用 `rebalance_freq`。

**平台目标**：本地 Python 研究工具；回测主路径网络调用次数目标值为 0。

### 文件布局边界

```text
engine/
├── data_loader.py
└── contracts.py
```

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| S004-T1 | 创建 | `engine/data_loader.py` | 实现 parquet 读取、schema 校验和 `close_df` 对齐 |
| S004-T2 | 创建 | `engine/data_loader.py` | 实现复权一致性和 `available_at` 校验 |
| S004-T3 | 创建 | `engine/data_loader.py` | 实现质量报告读取和 pass/warn/fail 启动策略 |
| S004-T4 | 修改 | `engine/contracts.py` | 补充 loader 返回 metadata 字段常量 |

## 验证上下文（validation_context）

**验证入口**：本地 parquet fixture、质量报告 fixture、无网络 monkeypatch 测试。

**验证方式**：单元测试 + 静态检查主路径未导入 AKShare adapter。

**依赖环境**：Python 3.11+、uv、pandas、pyarrow；不需要网络。

**关键验证场景**：合规数据返回 `close_df`；复权混用拒绝；`available_at > decision_time` 拒绝；quality warn 继续并披露；quality fail 拒绝。

## 量化验收标准（acceptance_criteria）

- [ ] 合规输入下返回 4 类对象：`close_df`、`universe`、`calendar`、`metadata`。
- [ ] `close_df.index` 按交易日升序排列，`close_df.columns` 来自股票池与价格数据交集。
- [ ] 回测加载路径对 AKShare、requests、httpx、urllib 等网络库的业务调用次数为 0。
- [ ] 复权口径混用时 100% 拒绝运行，并返回可定位错误。
- [ ] quality warn 时 metadata 必须包含 `quality_status`、覆盖区间、最近成功更新时间和新鲜度字段。

## 后续 LLD 输入约束

LLD 必须定义 Data Loader 函数签名、metadata schema、异常类型、质量报告定位方式、无网络测试策略和与 STORY-005 的接口。

## 阻塞说明

W0 已完成：`STORY-001`、`STORY-002`、`STORY-003` 均已由 meta-po 收敛为 `verified`。按 `process/DEVELOPMENT-PLAN.yaml`，W1/M1 为串行 Wave，首个可执行 Story 为 `STORY-004`。

meta-po 曾将本 Story 从 `draft` 推进到 `approved`，仅授权 meta-dev 起草 LLD。meta-dev 已输出 `process/stories/STORY-004-offline-data-loader-contract-validator-LLD.md`，frontmatter `confirmed=false`、`tier=L`、`open_items=4`，并将本 Story推进到 `ready-for-lld-review`。

用户已纠偏当前工作流：不再单独确认 STORY-004 LLD 后立即进入实现，而是先输出剩余 Story LLD，形成批量 LLD / Story Package 后统一人工确认。`checkpoints/STORY-004-LLD-CHECKPOINT.md` 已被 `process/LLD-BATCH-PLAN.md` 取代。

批量 LLD / Story Package 未确认前，不得实现 `engine/data_loader.py`、不得修改 `engine/contracts.py` 或任何实现代码、不得生成数据、不得写入 `delivery/**`、不得生成安装脚本、不得推进 `STORY-005+` 实现。

## CR-004 Batch D LLD 修订状态

2026-05-17，meta-dev 已按“Data Loader 先行，不真实抓取数据”约束修订 `process/stories/STORY-004-offline-data-loader-contract-validator-LLD.md`，并已由用户在 CP5 Batch D 回复“通过”。该修订只收紧 Data Loader 质量门禁、机器质量入口、PIT/non-PIT 披露、只读/无网络和 `engine/contracts.py` 纯常量边界；不改变本 Story 原目标，不回滚既有交付记录。后续实现只允许修改 `engine/data_loader.py` 和 `engine/contracts.py` 纯常量，测试必须使用临时 fixture，不得真实抓取数据或写真实 `data/**`、`reports/**`、`delivery/**`。
