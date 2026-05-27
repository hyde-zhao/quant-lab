---
handoff_id: "META-DEV-CR005-BATCH-A-IMPLEMENT-2026-05-17"
from_agent: "meta-po"
to_agent: "meta-dev"
status: "completed"
created_at: "2026-05-17T19:50:57+08:00"
workflow_id: "local_backtest"
change_id: "CR-005"
story_id: "CR005-BATCH-A-IMPLEMENT"
wave_id: "CR005-CP6-BATCH-A"
batch_id: "CR005-BATCH-A"
dispatch:
  required: true
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".codex/agents/meta-dev.toml"
  tool_name: "spawn_agent"
  agent_id: "019e35c8-da0b-7652-85af-017dd422cc29"
  agent_name: "dev-you"
  thread_id: "019e35c8-da0b-7652-85af-017dd422cc29"
  spawned_at: "reported-by-main-thread; exact spawn time not provided"
  resumed_at: ""
  completed_at: "2026-05-17T20:06:02+08:00"
  evidence: "主线程真实 spawn_agent 调度 meta-dev/dev-you，agent_id/thread_id=019e35c8-da0b-7652-85af-017dd422cc29，completed then closed。meta-dev 已完成 CR005-S01/CR005-S02 Batch A 实现、离线回归和两个 CP6 自检。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# Handoff：CR-005 CP5 Batch A 实现

## 调度目标

请 `meta-dev` 只实现 CR-005 Batch A：

- `CR005-S01`：Tushare connector 真实写湖边界与 `hs300_index` backfill job spec
- `CR005-S02`：Tushare 多 dataset schema、PIT 字段与复权 normalization

本 handoff 已满足进入实现的前置门控：

- CP3 approved：`checkpoints/CP3-CR005-HLD-REVIEW.md`
- CP4 approved：`checkpoints/CP4-CR005-STORY-PLAN-REVIEW.md`
- CP5 Batch A approved：`checkpoints/CP5-CR005-BATCH-A-LLD-BATCH.md`
- S01/S02 Story 级 CP5 自动预检均 PASS
- S01/S02 LLD frontmatter 已 `confirmed=true`、`implementation_allowed=true`

## 串并行策略

Batch A 不应拆成两个并行 meta-dev 实现线程。

原因：

- `CR005-S01` 和 `CR005-S02` 都会修改 `market_data/source_registry.py`。
- S01 先冻结 `hs300_index.daily` 写湖 / backfill job interface。
- S02 后扩展多 dataset exact mapping、schema registry、normalization 和 typed status。

执行顺序必须为：

1. `CR005-S01`
2. `CR005-S02`
3. 统一运行 Batch A 最小回归
4. 写入两个 Story 级 CP6 自检结果

## 必须消费的输入

- `process/STATE.md`
- `checkpoints/CP5-CR005-BATCH-A-LLD-BATCH.md`
- `process/stories/CR005-S01-tushare-connector-real-lake-writer.md`
- `process/stories/CR005-S01-tushare-connector-real-lake-writer-LLD.md`
- `process/stories/CR005-S02-tushare-dataset-schema-normalization.md`
- `process/stories/CR005-S02-tushare-dataset-schema-normalization-LLD.md`
- `process/checks/CP5-CR005-S01-tushare-connector-real-lake-writer-LLD-IMPLEMENTABILITY.md`
- `process/checks/CP5-CR005-S02-tushare-dataset-schema-normalization-LLD-IMPLEMENTABILITY.md`
- `process/HLD.md`
- `process/ARCHITECTURE-DECISION.md`
- `process/changes/CR-005-TUSHARE-5000-DATA-LAYER-REMEDIATION-2026-05-17.md`

## 允许修改的实现范围

按 S01/S02 LLD 和 Story 卡片执行，限定在 Batch A：

- `market_data/connectors/tushare.py`
- `market_data/config.py`
- `market_data/source_registry.py`
- `market_data/runtime.py`，仅限 S01 LLD 允许的兼容扩展
- `market_data/storage.py`，仅限 S01 LLD 允许的敏感值扫描加强
- `market_data/cli.py`
- `market_data/contracts.py`
- `market_data/normalization.py`
- `.gitignore`
- `tests/test_market_data_tushare_connector.py`
- `tests/test_market_data_tushare_datasets.py`
- `tests/fixtures/**`，仅允许小型脱敏合成 fixture
- `pyproject.toml` / `uv.lock`，仅当 Batch A 实现确需新增 Tushare provider 依赖时，必须通过 `uv` 修改；不得新增 Backtrader 依赖
- `DEV-LOG.md`
- Story 状态文件 / CP6 检查结果文件

## O-S01-02 已确认决策

实现必须遵守：

- 真实行情数据、Tushare 拉取结果、raw/canonical/gold/quality/catalog 等 lake 数据不得归档到 GitHub。
- 不得默认写入仓库内真实 `data/**`。
- 真实 lake root 必须外置且可配置，优先通过显式 `--lake-root` 或环境变量 `MARKET_DATA_LAKE_ROOT` 指定。
- NAS 是推荐共享部署形态，例如 `/mnt/nas/quant_lake/local_backtest`，但实现不得硬编码 NAS。
- 当前只依赖 POSIX path；本机外置目录也可用；S3/MinIO 仅保留未来扩展点，不在 Batch A 实现。
- 仓库只保留 schema、contract、文档、job spec 示例和小型脱敏 fixture。
- `.gitignore` 必须阻止仓库内误放 raw/canonical/gold/quality/lake artifacts、本地 env 文件入库，同时允许 `tests/fixtures/` 小型样本。
- 未配置 lake root 时必须 fail fast / structured missing，不得静默写 `./data`。

## 禁止事项

- 不得实现 `CR005-S03` / `CR005-S04` / `CR005-S05` / `CR005-S06`。
- 不得实现 Backtrader adapter，不得新增 Backtrader 依赖。
- 不得修改 `engine/data_loader.py`、`engine/backtest.py`、`experiments/**`、`market_data/readers.py`。
- 不得写真实行情数据、真实 Tushare 返回样本、真实 token、真实 `data/**` 或 `reports/**` 产物。
- 默认测试不得联网、不得依赖 `TUSHARE_TOKEN`、不得依赖 NAS。
- 不得执行真实 Tushare fetch；真实联网只允许用户后续显式提供运行条件后另行执行。
- 不得进入 CP7；CP7 必须由 meta-qa 在 CP6 通过后执行。

## 必须输出

实现完成后，必须输出 Story 级 CP6 自检：

- `process/checks/CP6-CR005-S01-tushare-connector-real-lake-writer-CODING-DONE.md`
- `process/checks/CP6-CR005-S02-tushare-dataset-schema-normalization-CODING-DONE.md`

每个 CP6 文件必须包含：

- Agent Dispatch Evidence：`tool_name`、`agent_id`、`agent_name`、`thread_id`、`spawned_at`、`completed_at`
- 实现文件清单
- 禁止范围复核
- 默认离线测试命令和结果
- 是否修改 `pyproject.toml` / `uv.lock` 及 uv 命令依据
- lake root / `.gitignore` 决策落实情况
- token / 真实数据 / 真实联网边界复核
- 下一步交给 meta-qa 的 CP7 验证建议

## 推荐验证命令

默认验证必须离线、无 token、无网络。建议最小命令由 meta-dev 按实际实现细化，但至少覆盖：

```bash
TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q tests/test_market_data_tushare_connector.py tests/test_market_data_tushare_datasets.py
```

如涉及既有 market_data 契约，补充：

```bash
TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q tests/test_market_data_contracts.py tests/test_market_data_runtime_storage.py
```

## 完成回报

完成后请回填本文件 frontmatter `dispatch.tool_name`、`agent_id`、`agent_name`、`thread_id`、`spawned_at`、`completed_at` 和结果摘要，并报告：

- 修改文件清单
- 两个 CP6 文件路径
- 测试命令与结果
- 是否存在需要 meta-qa 在 CP7 阶段重点验证的风险
- 是否存在阻断进入 CP7 的项
