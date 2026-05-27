---
story_id: "CR005-S01"
title: "Tushare connector 真实写湖边界"
story_slug: "tushare-connector-real-lake-writer"
status: "verified"
priority: "P0"
wave: "CR5-W0"
depends_on: ["STORY-015"]
dependency_contracts:
  - upstream: "STORY-015"
    type: "contract"
    required: "ConnectorRequest/ConnectorResult、runtime、raw/manifest 写入契约已稳定"
file_ownership:
  primary:
    - "market_data/connectors/tushare.py"
    - "tests/test_market_data_tushare_connector.py"
  shared:
    - "market_data/config.py"
    - "market_data/source_registry.py"
    - "market_data/runtime.py"
    - "market_data/storage.py"
    - "market_data/cli.py"
    - "pyproject.toml"
    - "uv.lock"
  merge_owner: "CR005-S01"
  forbidden:
    - "engine/data_loader.py"
    - "engine/backtest.py"
    - "experiments/**"
    - "market_data/readers.py"
    - "data/**"
    - "reports/**"
    - "delivery/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#22-cr-005-tushare-真实写湖与-backtrader-可选后端增量设计"
    - "process/ARCHITECTURE-DECISION.md#adr-013tushare-只写入本地数据湖链路"
    - "process/stories/CR005-S01-tushare-connector-real-lake-writer.md"
  status: "approved"
  lld_path: "process/stories/CR005-S01-tushare-connector-real-lake-writer-LLD.md"
  cp5_precheck: "process/checks/CP5-CR005-S01-tushare-connector-real-lake-writer-LLD-IMPLEMENTABILITY.md"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  required_contracts:
    - "`hs300_index` backfill job spec frozen"
    - "plan/dry-run default no-network/no-write contract frozen"
    - "Tushare error enum and resume policy frozen"
  file_conflict_free: true
  cp5_required: true
  implementation_status: "completed"
  cp6_checkpoint: "process/checks/CP6-CR005-S01-tushare-connector-real-lake-writer-CODING-DONE.md"
  cp7_checkpoint: "process/checks/CP7-CR005-S01-tushare-connector-real-lake-writer-VERIFICATION-DONE.md"
  verification_status: "PASS"
created_at: "2026-05-17"
updated_at: "2026-05-17T20:18:14+08:00"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-005"
---

# CR005-S01：Tushare connector 真实写湖边界

## 目标

将当前 fail-fast 的 Tushare adapter 设计为可控真实写湖 source：只有显式启用、接口 allowlist 命中、`TUSHARE_TOKEN` 环境变量存在且用户执行真实抓取命令时，才允许 connector 在写湖链路中延迟导入真实 provider。同时冻结 `hs300_index` backfill job spec，使消费层返回的 remediation spec 有明确的数据层执行入口，但该入口只能由用户显式执行。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | CR005-AC-001、CR005-AC-002、CR005-AC-010、CR005-AC-015、CR005-AC-016 |
| HLD | §22.1、§22.6、§22.7、§22.8 |
| ADR | ADR-013 |

## 开发上下文（dev_context）

**背景说明**：当前 `market_data/connectors/tushare.py` 只返回结构化 fail-fast 错误；`market_data/config.py` 已声明 `TUSHARE_TOKEN` env var；`source_registry.py` 目前只给 Tushare 注册 `prices.daily`。本 Story 不让 Tushare 进入任何消费方，只升级写湖入口边界，并前置 `market_data/cli.py` 或等价 job 的 `hs300_index` backfill 契约，避免 CR005-S04 在补齐入口未冻结时进入开发。

**输入文件**：`process/HLD.md`、`process/ARCHITECTURE-DECISION.md`、`process/changes/CR-005-TUSHARE-5000-DATA-LAYER-REMEDIATION-2026-05-17.md`、`market_data/connectors/tushare.py`、`market_data/config.py`、`market_data/source_registry.py`、`market_data/connectors/protocol.py`、`market_data/runtime.py`、`market_data/storage.py`、`market_data/cli.py`、`pyproject.toml`。

**输出文件**：`market_data/connectors/tushare.py`、`market_data/cli.py` 或等价 job、`tests/test_market_data_tushare_connector.py`；如 CP5 明确批准真实 provider 依赖，再通过 uv 修改 `pyproject.toml` 和 `uv.lock`。本规划阶段不得修改依赖。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| `TushareAdapter(config).fetch(request)` | `ConnectorRequest(source="tushare", interface, params, run_id, batch_id)` | `ConnectorResult` 或 `ConnectorError` | `source_disabled`、`interface_not_allowed`、`missing_credential` 为非重试错误 |
| `plan/dry-run` | dataset、interface、date range、symbols、lake_root | 批次数、接口列表、目标路径、预计参数摘要 | 不读取 token 值、不联网、不写 raw |
| `hs300_index` backfill job | `dataset=hs300_index`、`source=tushare`、exact interface、`index_code`、start/end、lake_root、run_id、resume_policy、`dry_run=true` 默认 | job plan 或执行结果，包含 raw/manifest/canonical/quality/catalog/gold 目标路径 | 只有用户显式执行且 dry_run=false 时才允许联网和写湖；消费层不得调用 |
| runtime 写湖 | connector result、batch metadata | raw JSONL、manifest JSONL | token 值不得进入 raw/manifest/error_message |

**设计约束**：

- Tushare 只允许写 `raw` 和 `manifest`，不直接写 canonical/gold。
- `hs300_index` backfill job spec 必须覆盖 dataset、source、exact interface、index_code、start/end、lake_root、run_id、resume_policy、dry-run 默认、manifest / quality / catalog 路径和错误枚举。
- `dry_run=true` 为默认；dry-run 网络调用次数和写湖次数均为 0。
- 不修改 `engine/data_loader.py`、`engine/backtest.py`、实验入口或 Backtrader adapter。
- import `market_data.connectors.tushare` 不得导入真实 provider，不得联网。
- `TUSHARE_TOKEN` 只作为环境变量名引用，禁止记录 token 值。
- 默认 pytest 不需要 token、不联网。

**命名规范**：source exact 值为 `tushare`；接口命名使用 `prices.daily`、`hs300_index.daily` 等由 CR005-S02 冻结的 exact 值。

**平台目标**：本地 Python 研究工具；uv 管理依赖；无安装脚本。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR005-S01-T1 | 修改 | `market_data/connectors/tushare.py` | 保留 fail-fast，增加显式真实 fetch 分支的接口和错误映射设计 |
| CR005-S01-T2 | 修改 | `market_data/config.py` | 增加 Tushare allowlist、offline 默认和 token env 引用约束 |
| CR005-S01-T3 | 修改 | `market_data/source_registry.py` | 只登记已确认 exact interface；未知接口 fail fast |
| CR005-S01-T4 | 修改 | `market_data/cli.py` 或等价 job | 增加 `hs300_index` backfill plan/fetch job spec，默认 dry-run，输出 manifest/quality/catalog 规划路径和错误枚举 |
| CR005-S01-T5 | 创建 | `tests/test_market_data_tushare_connector.py` | 覆盖 import no-network、disabled、missing token、interface not allowed、dry-run no-network、hs300 backfill dry-run 输出 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_market_data_tushare_connector.py`。

**验证方式**：单元测试、monkeypatch 环境变量、静态扫描。

**依赖环境**：Python 3.11、uv、pytest；默认不需要 Tushare token、不需要网络。

**关键验证场景**：

- import Tushare adapter 不联网。
- 未启用 source 返回 `source_disabled`。
- 未 allowlist 返回 `interface_not_allowed`。
- 缺 `TUSHARE_TOKEN` 返回 `missing_credential`，消息不含 token 值。
- plan/dry-run 输出批次摘要但不调用 provider。
- `hs300_index` backfill dry-run 输出 dataset/source/interface/index_code/date range/lake_root/run_id/resume_policy/manifest_path/quality_path/catalog_path/error_enum，且不联网不写湖。

## 量化验收标准（acceptance_criteria）

- [ ] 默认路径网络调用次数为 0。
- [ ] `source_disabled`、`interface_not_allowed`、`missing_credential` 三类错误 100% 返回结构化 `ConnectorError`。
- [ ] `hs300_index` backfill job spec 至少包含 14 个字段：dataset、source、interface、index_code、start_date、end_date、lake_root、run_id、resume_policy、dry_run、manifest_path、quality_path、catalog_path、error_enum。
- [ ] dry-run 模式下 provider 调用次数为 0，raw/manifest/canonical/quality/catalog/gold 写入次数为 0。
- [ ] manifest、quality、catalog、日志和错误消息中出现 token 值的次数为 0。
- [ ] 不修改 `engine/**`、`experiments/**`、`market_data/readers.py`、`data/**`、`reports/**`、`delivery/**`。
- [ ] 未经 CP5 不修改 `pyproject.toml` / `uv.lock`。

## 阻塞说明

`CR5-Q1` 仍为 OPEN：Tushare 5000 档 exact 限频和字段细节未确认。该问题不阻塞 fail-fast、allowlist、dry-run、backfill job spec 和写湖边界设计，阻塞真实 provider 调用参数最终实现。
