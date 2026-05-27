---
project_id: "local_backtest"
change_id: "CR-005"
validation_type: "real_data_acquisition_smoke"
agent: "meta-qa"
nickname: "qa-shi"
dispatch:
  mode: "spawn_agent"
  tool_name: "spawn_agent"
  agent_id: "019e384a-0127-7071-a531-d24cf916c116"
  thread_id: "019e384a-0127-7071-a531-d24cf916c116"
created_at: "2026-05-18T07:07:12+08:00"
updated_at: "2026-05-18T20:01:26+08:00"
result: "PASS"
---

# CR-005 真实数据获取链路验证记录

## 最新结论

**结论：PASS**

最新复验时间：`2026-05-18T20:01:26+08:00`。用户明确确认按仓库根 `.env` 开展验证，因此本轮将 `.env` 中的 `MARKET_DATA_LAKE_ROOT` 作为运行时真相源，不再要求 exact match 文档中的固定路径。Preflight 通过：`.env` 可加载，`TUSHARE_TOKEN` 存在但未打印值，lake root 来自 `.env` 且存在、是目录、可写探针可创建并删除。Dry-run 通过：`hs300-backfill --dry-run true` 在 `2024-01-02` 至 `2024-01-05` 小窗口返回 `network_calls=0`、`writes=0`。失败原因已定位并修复到正式依赖入口：新增 `tushare` dependency group 后，`uv run --env-file .env --group tushare --python 3.11 ...` 可导入 `tushare==1.4.29`，真实 `hs300-backfill` 小窗口写出 success raw 与 success manifest。本次 run 随后完成 `hs300_index` normalize、quality、catalog、reader 最小链路：canonical 4 行、quality `pass`、dataset_status `available`、reader `available` 且读回 4 行。相关离线回归 35 passed。后续 REQUIRED 已关闭：CLI 的 `normalize` / `validate` / `read` 已支持 `dataset=hs300_index`，未显式传 `--lake-root` 时优先使用 `.env` 中的 `MARKET_DATA_LAKE_ROOT`；真实 CLI 复验通过，仓库内 `data/market_data` 未重新生成。CR-005 真实数据获取和运维 CLI 最小链路结论为 PASS。

## 首轮结论（2026-05-18T07:07:12+08:00）

**结论：BLOCKING**

CR-005 Tushare -> 本地数据湖最小真实数据获取链路未进入 dry-run 或真实 fetch/write。验证在 preflight 阶段停止，原因是按要求使用 `uv run --env-file .env --python 3.11 ...` 时，`uv` 返回 `.env` 文件不存在。由于前置环境加载失败，未继续执行 dry-run、真实 Tushare fetch/write、normalize、quality/catalog 或 reader 验证。

本轮未打印、记录、写入或提交真实 `TUSHARE_TOKEN`、NAS 用户名、NAS 密码；未 echo `.env` 原文；未读取、列出或写入真实 lake 数据内容。

## 执行顺序与结果

| 步骤 | 状态 | 结果 |
|---|---|---|
| 上下文读取 | PASS | 已读取 README、USER-MANUAL、STATE、QA handoff、`market_data/cli.py` 和相关 `market_data` 实现。 |
| Preflight | BLOCKING | `uv run --env-file .env --python 3.11 python - ...` 失败：仓库根未发现 `.env`。 |
| Dry-run | SKIP | 因 preflight 未通过，未执行 hs300-backfill dry-run。 |
| 极小窗口真实 fetch/write | SKIP | 因 preflight 未通过，未执行真实 Tushare 调用，也未写 lake。 |
| 读取/校验产物 | SKIP | 因未产生本轮真实产物，未读取 manifest、raw、canonical、quality、catalog 或 parquet。 |
| 最小离线回归 | SKIP | 因 preflight 阻断，未进入产物校验和 reader/benchmark 回归。 |

## 命令类别与结果

| 类别 | 命令形态 | 结果 |
|---|---|---|
| 文档/实现定位 | `rg` / `sed` 读取 README、USER-MANUAL、STATE、handoff、`market_data` 代码和测试 | PASS |
| Preflight | `uv run --env-file .env --python 3.11 python - ...` | FAIL，`uv` 报告 `.env` 不存在 |
| `.env` 存在性确认 | `test -f .env` | FAIL，返回码为 1 |
| Git 工作区观察 | `git status --short` | PASS，仅用于确认本轮修改边界；未回滚或清理用户既有未跟踪文件 |

## 关键实现事实

- 文档入口是 `python -m market_data.cli hs300-backfill`。
- `hs300-backfill --dry-run true` 只返回 job spec、路径规划、错误枚举、`network_calls=0`、`writes=0`。
- `hs300-backfill --dry-run false` 必须显式传 `--enable-real-source`，且依赖 `TUSHARE_TOKEN` 存在。
- 当前 CLI 的 `normalize` / `validate` / `read` 子命令仍通过 `_require_prices(args.dataset)` 限制为 `prices`；若 preflight 和真实 fetch 后需要完成 hs300 canonical/quality/catalog，需使用 `market_data.normalization.normalize_run`、`market_data.validation.validate_hs300_index`、`market_data.validation.write_quality_reports`、`market_data.catalog.CatalogStore` 等 Python API 做最小链路校验，或后续修复 CLI 对 `hs300_index` 的支持。

## 安全边界确认

| 边界 | 状态 | 说明 |
|---|---|---|
| 不打印 token/NAS 凭据 | PASS | 未读取或输出真实凭据值。 |
| 不 echo `.env` 原文 | PASS | 未执行 `.env` 内容输出。 |
| lake 数据最小化 | PASS | preflight 未通过，未创建真实 lake 数据产物。 |
| 禁止全量回补 | PASS | 未执行任何 backfill。 |
| 禁止修改业务代码/测试/Story/依赖/delivery | PASS | 本轮只新增本验证记录并更新 `process/STATE.md`。 |

## Remediation Next Action

1. 在仓库根创建或恢复被 `.gitignore` 忽略的本机 `.env`，仅包含本机实际值，不提交：
   - `TUSHARE_TOKEN=<local-token-placeholder>`
   - `MARKET_DATA_LAKE_ROOT=<configured-lake-root>`
2. 确认 `<configured-lake-root>` 已挂载、是目录、当前用户可写。
3. 重新从 preflight 开始执行，不跳过任何步骤。
4. 预期下一轮使用不超过 5 个交易日的历史窗口，优先 `2024-01-02` 至 `2024-01-05`，按顺序执行：
   - preflight 环境与路径写入探针；
   - `hs300-backfill --dry-run true`；
   - `hs300-backfill --dry-run false --enable-real-source`；
   - manifest/raw 存在性与状态校验；
   - hs300 normalize / quality / catalog / reader 最小校验。

## 修改文件

- `process/checks/CR005-REAL-DATA-ACQUISITION-VALIDATION-2026-05-18.md`
- `process/STATE.md`

---

## 2026-05-18T07:20:29+08:00 复验记录

### 调度证据

| 字段 | 值 |
|---|---|
| agent | `meta-qa` |
| nickname | `qa-jin` |
| dispatch.mode | `spawn_agent` |
| tool_name | `spawn_agent` |
| agent_id / thread_id | `019e383c-86e2-7e90-b19c-a98348fe19e4` |

### 结论

**结论：BLOCKING**

用户已准备仓库根 `.env` 后，按要求从上一轮 BLOCKING 的 preflight 步骤重新开始。`.env` 文件已可由 `uv run --env-file .env --python 3.11 ...` 加载，且 `TUSHARE_TOKEN` 存在；但 `MARKET_DATA_LAKE_ROOT` 未与要求值 `<configured-lake-root>` exact match。由于 preflight 未通过，本轮按门控停止，未执行 dry-run、真实 Tushare fetch/write、normalize、quality/catalog 或 reader 校验。

本轮未打印、记录、写入或提交真实 `TUSHARE_TOKEN`、NAS 用户名、NAS 密码；未 echo `.env` 原文；未输出 `MARKET_DATA_LAKE_ROOT` 的实际错误值；未列出或读取真实 lake 数据内容。preflight 仅创建并删除无敏感内容的 `.preflight_write_test` 探针文件。

### 执行顺序与结果

| 步骤 | 状态 | 结果 |
|---|---|---|
| 上下文读取 | PASS | 已读取上一轮验证记录、`process/STATE.md`、`README.md`、`docs/USER-MANUAL.md`、`market_data/cli.py` 以及 `normalization` / `validation` / `catalog` / `readers` 等必要实现。 |
| Preflight | BLOCKING | `uv run --env-file .env --python 3.11 python -c ...` 已能加载 `.env`；`TUSHARE_TOKEN` 存在；lake root 路径存在、是目录、可创建并删除 `.preflight_write_test`；但 `MARKET_DATA_LAKE_ROOT` 与 `<configured-lake-root>` 不完全相等。 |
| Dry-run | SKIP | 因 preflight 未通过，未执行 `hs300-backfill --dry-run true`。 |
| 极小窗口真实 fetch/write | SKIP | 因 preflight 未通过，未执行 `hs300-backfill --dry-run false --enable-real-source`；未联网调用 Tushare；未写入真实数据产物。 |
| 读取/校验产物 | SKIP | 因本轮未产生真实 run 产物，未读取 manifest/raw/canonical/quality/catalog/parquet。 |
| hs300 API 最小校验 | SKIP | 因未进入真实 fetch/write，不调用 Python API 做 `hs300_index` normalize/validate/read 校验。 |

### 命令类别与结果

| 类别 | 命令形态 | 结果 |
|---|---|---|
| 记忆与上下文读取 | `memory_recall`、`sed`、`rg` | PASS，未发现相关项目记忆；已确认上一轮仅因 `.env` 缺失阻断。 |
| `.env` 存在性确认 | `test -f .env` | PASS，仓库根 `.env` 已存在。 |
| Preflight | `uv run --env-file .env --python 3.11 python -c ...` | FAIL/BLOCKING；token 存在、目录存在且可写探针通过，但 lake root 环境变量不是 exact expected value。 |
| Dry-run | `uv run --env-file .env --python 3.11 python -m market_data.cli hs300-backfill --dry-run true ...` | SKIP，preflight 未通过。 |
| 真实 fetch/write | `uv run --env-file .env --python 3.11 python -m market_data.cli hs300-backfill --dry-run false --enable-real-source ...` | SKIP，preflight 未通过。 |

### 关键实现事实复核

- `hs300-backfill --dry-run true` 仍提供 `network_calls=0`、`writes=0` 的 dry-run 语义，但本轮未进入该步骤。
- `hs300-backfill --dry-run false` 仍要求显式 `--enable-real-source` 与环境变量 `TUSHARE_TOKEN`，但本轮未进入该步骤。
- 当前 CLI 的 `normalize` / `validate` / `read` 子命令仍通过 `_require_prices(args.dataset)` 限制为 `prices`；若后续 preflight 和真实 fetch/write 通过，`hs300_index` 的最小校验应使用现有 Python API：`normalize_run(..., dataset=DATASET_HS300_INDEX)`、`validate_hs300_index(...)`、`write_quality_reports(...)`、`CatalogStore.upsert(...)`、`read_dataset(DATASET_HS300_INDEX, ...)`。

### 安全边界确认

| 边界 | 状态 | 说明 |
|---|---|---|
| 不打印 token/NAS 凭据 | PASS | 仅验证 `TUSHARE_TOKEN` 是否存在，未输出真实值；未请求或输出 NAS 用户名/密码。 |
| 不 echo `.env` 原文 | PASS | 未读取或输出 `.env` 原文。 |
| lake root exact 校验 | BLOCKING | `MARKET_DATA_LAKE_ROOT` 未 exact match `<configured-lake-root>`；未记录实际错误值。 |
| lake 数据最小化 | PASS | 未执行 dry-run 后续步骤；未读取、遍历或输出 lake 数据内容；仅创建并删除无敏感探针。 |
| 禁止全量回补 | PASS | 未执行任何 backfill。 |
| 禁止修改业务代码/测试/Story/依赖/delivery | PASS | 本轮只更新本验证记录与 `process/STATE.md`。 |

### Remediation Next Action

1. 修改仓库根本机 `.env`，确保 `MARKET_DATA_LAKE_ROOT` 的值与 `<configured-lake-root>` 完全一致；不要提交 `.env`，不要在对话或日志中粘贴真实 token。
2. 重新从 preflight 开始执行；preflight 通过前不得执行 dry-run 或真实 fetch/write。
3. preflight 通过后，按固定顺序执行：
   - `hs300-backfill --dry-run true`，窗口仍限制为 `2024-01-02` 至 `2024-01-05`；
   - `hs300-backfill --dry-run false --enable-real-source`，同一极小窗口；
   - 只检查本次 run 相关 manifest/raw/quality/catalog/parquet 或 API 输出；
   - 如 CLI 不支持 `hs300_index` normalize/validate/read，使用现有 Python API 做最小校验。

---

## 2026-05-18T07:38:19+08:00 复验记录

### 调度证据

| 字段 | 值 |
|---|---|
| agent | `meta-qa` |
| nickname | `qa-shi` |
| dispatch.mode | `spawn_agent` |
| tool_name | `spawn_agent` |
| agent_id / thread_id | `019e384a-0127-7071-a531-d24cf916c116` |

### 本轮环境口径

用户明确确认：如果配置没有功能问题，就按照仓库根 `.env` 开展验证。本轮因此将 `.env` 中的 `MARKET_DATA_LAKE_ROOT` 作为运行时真相源，不再要求它 exact match 文档中的固定路径。验证记录不打印、不记录、不回显 lake root 实际值。

### 结论

**结论：BLOCKING**

Preflight 和 dry-run 均已通过；真实 fetch/write 已在 `2024-01-02` 至 `2024-01-05` 极小窗口执行一次，未执行全量回补。真实执行返回 `network_calls=1`，但 batch 状态为 `failed`、错误类型为 `remote_error`，未生成成功 raw 数据，因此未能进入 `hs300_index` normalize / quality / catalog / reader 成功路径。当前 `uv run --python 3.11` 环境中 `tushare` 模块不可导入，是 provider 调用失败的直接环境缺口；本轮不修改依赖或业务代码。

### 执行顺序与结果

| 步骤 | 状态 | 结果 |
|---|---|---|
| 上下文读取 | PASS | 已读取上一轮验证记录、`process/STATE.md`、`README.md`、`docs/USER-MANUAL.md`、`market_data/cli.py` 以及必要 `market_data` 实现。 |
| Preflight | PASS | `uv run --env-file .env --python 3.11 python -c ...` 可加载 `.env`；`TUSHARE_TOKEN` 存在但未输出值；lake root 来自 `.env`，存在、是目录、可创建并删除 `.preflight_write_test`。 |
| Dry-run | PASS | `hs300-backfill --dry-run true` 使用 `2024-01-02` 至 `2024-01-05`，返回 `network_calls=0`、`writes=0`，路径规划字段为相对路径。 |
| 极小窗口真实 fetch/write | BLOCKING | 同一窗口执行 `hs300-backfill --dry-run false --enable-real-source`，返回 `network_calls=1`，结果状态 `failed`，错误类型 `remote_error`，未产生 raw_path。 |
| 本次 run 产物核验 | BLOCKING | 本次 run 仅有 1 条 manifest 失败记录：`status=failed`、`error_type=remote_error`、`raw_path` 为空、`raw_row_count` 为空、`success_items=0`。未发现本次 run 的 canonical 目录或 quality 目录。 |
| hs300 CLI / API 最小校验 | REQUIRED | CLI `normalize` / `validate` / `read` 对 `dataset=hs300_index` 均返回 `usage_error`，与已知实现限制一致；Python API `normalize_run(..., dataset=hs300_index, run_id=<本次 run>)` 因本次 run 没有 success manifest 返回 `ManifestLineageError`，未写入 canonical。 |

### 命令类别与结果

| 类别 | 命令形态 | 结果 |
|---|---|---|
| 记忆与上下文读取 | `memory_recall`、`sed`、`rg` | PASS，未发现相关项目记忆；已确认上一轮 BLOCKING 来自 lake root exact match 门控。 |
| Preflight | `uv run --env-file .env --python 3.11 python -c ...` | PASS，token 存在、lake root 存在且可写探针通过；未输出真实 token、凭据或 lake root 值。 |
| Dry-run | `uv run --env-file .env --python 3.11 python -m market_data.cli hs300-backfill --dry-run true ...` | PASS，`network_calls=0`、`writes=0`。 |
| 真实 fetch/write | `uv run --env-file .env --python 3.11 python -m market_data.cli hs300-backfill --dry-run false --enable-real-source ...` | BLOCKING，`network_calls=1`，batch `failed`，`error_type=remote_error`，未写成功 raw。 |
| 本次 run manifest 核验 | Python API：`read_manifest_records` 过滤本次 `run_id` | PASS/OBSERVED，存在 1 条失败记录，未包含真实 token 值。 |
| 环境缺口核验 | `importlib.util.find_spec("tushare")` | BLOCKING，当前 `uv` 环境中 `tushare` 模块不可导入。 |
| hs300 CLI 负向确认 | `normalize` / `validate` / `read` 使用 `dataset=hs300_index` | REQUIRED，均返回 `usage_error`。 |
| hs300 Python API | `normalize_run(..., dataset=DATASET_HS300_INDEX, run_id=<本次 run>)` | BLOCKING，因本次 run 没有 success manifest 返回 `ManifestLineageError`。 |

### 安全边界确认

| 边界 | 状态 | 说明 |
|---|---|---|
| 不打印 token/NAS 凭据 | PASS | 仅验证 `TUSHARE_TOKEN` 是否存在，未输出真实值；未请求或输出 NAS 用户名/密码。 |
| 不 echo `.env` 原文 | PASS | 未读取或输出 `.env` 原文。 |
| 不输出 lake root 实际值 | PASS | 本轮记录只说明 lake root 来自 `.env`、存在且可写，不记录实际路径。 |
| 小窗口限制 | PASS | 真实 fetch/write 限制在 `2024-01-02` 至 `2024-01-05`，不超过 5 个交易日。 |
| 禁止全量回补 | PASS | 未执行全量回补。 |
| lake 数据最小化 | PASS | 仅写入本次失败 manifest 记录；未大范围遍历 lake，未输出敏感路径下大量文件名。 |
| 禁止修改业务代码/测试/Story/依赖/delivery | PASS | 本轮只更新本验证记录与 `process/STATE.md`；未修改业务代码、测试、Story LLD、checkpoint、delivery 或依赖文件。 |

### Remediation Next Action

1. 在项目依赖策略中明确 Tushare provider 的安装方式，例如将 `tushare` 作为显式可选依赖或运行环境前置依赖；本轮不代改 `pyproject.toml` / `uv.lock`。
2. 在安装好 `tushare` 且不暴露 token 的前提下，重新使用同一安全顺序执行：preflight -> dry-run -> `2024-01-02` 至 `2024-01-05` 极小窗口真实 fetch/write。
3. 真实 fetch/write 成功后，再使用现有 Python API 执行 `hs300_index` 的 normalize、`validate_hs300_index`、`write_quality_reports`、`CatalogStore.upsert`、`read_dataset` 最小成功链路；CLI 对 `hs300_index` 的 `normalize` / `validate` / `read` 支持缺口应作为 REQUIRED remediation 单独处理。

---

## 2026-05-18T19:26:03+08:00 失败原因定位记录

### 结论

**结论：BLOCKING，根因已定位**

本轮只定位失败原因，不回显 `.env` 原文，不输出 token、NAS 用户名或 NAS 密码。定位结果如下：

- Tushare 基础接口单独验证通过：临时 `--with tushare` 环境中 `trade_cal(exchange="SSE", start_date="20240102", end_date="20240105")` 返回 4 行。
- 项目实际使用的 Tushare 接口单独验证通过：`index_daily(ts_code="399300.SZ", start_date="20240102", end_date="20240105")` 返回 4 行，字段包含 `ts_code,trade_date,close,open,high,low,pre_close,change,pct_chg,vol`。
- 项目适配层验证通过：`TushareAdapter.fetch(...)` 在临时 `--with tushare` 环境中返回 `ConnectorResult`，`row_count=4`，`provider_interface=index_daily`。
- 项目 `hs300-backfill` 真实链路在临时 `--with tushare` 环境中验证通过：同一 `.env`、同一 `2024-01-02` 至 `2024-01-05` 窗口返回 `status=success`，写出 `raw_path`，对应 manifest 记录 `status=success`、`error_type=None`、`raw_row_count=4`。

因此，上一轮 `remote_error` 的直接原因不是 Tushare token、网络、接口权限、`index_daily` 参数、`TushareAdapter` 或 lake 写入逻辑，而是默认项目运行环境未安装 `tushare`。当前 `pyproject.toml` 依赖声明中也未包含 `tushare`。

### 命令类别与结果

| 类别 | 结果 |
|---|---|
| 默认项目环境 import 检查 | `tushare_installed=False`，确认默认环境缺少 provider 依赖。 |
| 临时 Tushare 基础接口探针 | PASS，`trade_cal` 返回 4 行。 |
| 临时 Tushare 实际接口探针 | PASS，`index_daily` 返回 4 行。 |
| 项目适配层探针 | PASS，`TushareAdapter.fetch` 返回 `ConnectorResult` 与 4 行。 |
| 项目 CLI 真实链路探针 | PASS，临时 `--with tushare` 后 `hs300-backfill` 写出 success raw 与 manifest。 |

### 安全边界确认

| 边界 | 状态 |
|---|---|
| 不打印 token/NAS 凭据 | PASS |
| 不 echo `.env` 原文 | PASS |
| 不输出 lake root 实际值 | PASS |
| 小窗口限制 | PASS，仍为 `2024-01-02` 至 `2024-01-05` |
| 禁止全量回补 | PASS |

### Remediation Next Action

1. 将 `tushare` 纳入项目依赖策略，建议作为可选 dependency group，例如 `tushare = ["tushare==1.4.29"]` 或兼容范围版本。
2. 使用项目正式依赖入口重跑 `hs300-backfill` 小窗口真实 fetch/write，不能依赖一次性 `--with tushare` 作为长期运行方式。
3. 真实 raw 成功后继续补齐 `hs300_index` normalize / quality / catalog / reader 最小链路；CLI 对 `dataset=hs300_index` 的 normalize / validate / read 支持仍是 REQUIRED remediation。

---

## 2026-05-18T19:32:16+08:00 正式依赖入口复验记录

### 结论

**结论：PASS**

本轮已将 `tushare` 纳入项目正式 dependency group，并通过 `uv lock` 与 `uv sync --group tushare`。随后使用正式入口 `uv run --env-file .env --group tushare --python 3.11 ...` 重跑 CR-005 小窗口真实链路。

### 执行顺序与结果

| 步骤 | 状态 | 结果 |
|---|---|---|
| 依赖声明 | PASS | `pyproject.toml` 新增 `tushare = ["tushare==1.4.29"]` dependency group；`uv.lock` 已更新。 |
| 依赖同步 | PASS | `uv sync --group tushare` 成功。 |
| Provider import | PASS | 正式 `--group tushare` 环境中 `tushare_installed=True`，版本为 `1.4.29`。 |
| Dry-run | PASS | `hs300-backfill --dry-run true` 返回 `network_calls=0`、`writes=0`。 |
| 极小窗口真实 fetch/write | PASS | `2024-01-02` 至 `2024-01-05` 小窗口返回 `status=success`，写出 raw 与 success manifest。 |
| Manifest 核验 | PASS | 本次正式 run 过滤到 1 条 success manifest；`raw_row_count=4`，`error_type=None`。 |
| Normalize | PASS | `normalize_run(..., dataset=hs300_index)` 写出 1 个 canonical parquet，`row_count=4`。 |
| Quality | PASS | `validate_hs300_index(...)` 返回 `quality_status=pass`、`dataset_status=available`、`issue_count=0`。 |
| Catalog | PASS | `CatalogStore.upsert(...)` 写入 `hs300_index` catalog entry。 |
| Reader | PASS | `read_dataset(hs300_index, required=True)` 返回 `available`，读回 4 行。 |
| 离线回归 | PASS | `tests/test_market_data_runtime_storage.py tests/test_market_data_normalization_validation_readers.py tests/test_market_data_hs300_benchmark.py tests/test_market_data_tushare_comparison.py` 共 35 passed。 |

### 安全边界确认

| 边界 | 状态 |
|---|---|
| 不打印 token/NAS 凭据 | PASS |
| 不 echo `.env` 原文 | PASS |
| 小窗口限制 | PASS，真实 fetch/write 仍为 `2024-01-02` 至 `2024-01-05` |
| 禁止全量回补 | PASS |
| 真实 lake 写入范围 | PASS，仅写入本次 run 的 raw / manifest / canonical / quality / catalog 产物 |

### 后续 REQUIRED

已于 `2026-05-18T20:01:26+08:00` 关闭。CLI 对 `dataset=hs300_index` 的 `normalize` / `validate` / `read` 子命令已支持，且未显式传 `--lake-root` 时优先使用 `MARKET_DATA_LAKE_ROOT`，不再误写仓库内 `data/market_data`。

---

## 2026-05-18T20:01:26+08:00 hs300_index 运维 CLI 支持复验记录

### 结论

**结论：PASS**

本轮完成 REQUIRED 项：`normalize` / `validate` / `read` 三个 CLI 子命令支持 `dataset=hs300_index`。同时修正默认 lake root 解析：这三个子命令未显式传 `--lake-root` 时优先读取 `.env` 中的 `MARKET_DATA_LAKE_ROOT`，与 `hs300-backfill` 入口保持一致。

### 执行顺序与结果

| 步骤 | 状态 | 结果 |
|---|---|---|
| 仓库误写产物清理 | PASS | 已按用户确认删除 `data/market_data`；保留 `data/` 下其他历史本地文件。 |
| 定向测试 | PASS | `tests/test_market_data_cli_comparison.py tests/test_market_data_tushare_datasets.py tests/test_market_data_multidataset_quality_readers.py tests/test_market_data_hs300_benchmark.py` 共 31 passed。 |
| CLI normalize | PASS | `python -m market_data.cli normalize --dataset hs300_index --run-id cr005-official-tushare-20260518` 返回 `row_count=4`，canonical 路径位于外部 lake。 |
| CLI validate | PASS | `python -m market_data.cli validate --dataset hs300_index ... --open-trade-dates ...` 返回 `quality_status=pass`、`dataset_status=available`、`missing_rows=0`。 |
| CLI read | PASS | `python -m market_data.cli read --dataset hs300_index ... --columns trade_date,index_code,close` 返回 `row_count=4`。 |
| 写入边界 | PASS | 复验后 `data/market_data` 不存在；CLI 未再写仓库内默认 lake root。 |

### 安全边界确认

| 边界 | 状态 |
|---|---|
| 不打印 token/NAS 凭据 | PASS |
| 不 echo `.env` 原文 | PASS |
| CLI 默认 lake root 使用外部 `.env` 值 | PASS |
| 不重新生成仓库内 `data/market_data` | PASS |
