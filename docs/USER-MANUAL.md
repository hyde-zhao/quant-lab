# quant-lab 用户使用手册

本手册按模块描述 quant-lab 的常用入口：环境、数据与引擎、实验、多因子研究、QMT gateway、runner、日常运维和参考归档。所有命令默认在仓库根目录执行，并优先使用 `uv run --python 3.11 ...`。本文档只说明操作路径和检查点，不提供真实交易许可。

## 1. 阅读顺序

| 目标 | 优先阅读 |
|---|---|
| 查看文档总结构 | [docs/README.md](README.md) |
| 了解数据、loader、portfolio、backtest、metrics | [components/ENGINE.md](components/ENGINE.md) |
| 了解实验与报告 | [components/EXPERIMENTS.md](components/EXPERIMENTS.md) |
| 研究多因子策略 | [components/MULTIFACTOR-RESEARCH.md](components/MULTIFACTOR-RESEARCH.md) 和 [scenarios/MULTIFACTOR-RESEARCH-TO-STRATEGY.md](scenarios/MULTIFACTOR-RESEARCH-TO-STRATEGY.md) |
| 运行多因子模拟盘链路 | [components/RUNNER.md](components/RUNNER.md) 和 [scenarios/MULTIFACTOR-SIMULATION-RUNNER-OPERATION.md](scenarios/MULTIFACTOR-SIMULATION-RUNNER-OPERATION.md) |
| 非交易窗口准备 runner | [scenarios/NON-TRADING-WINDOW-RUNNER-READINESS.md](scenarios/NON-TRADING-WINDOW-RUNNER-READINESS.md) |
| 配置和检查 QMT gateway | [components/QMT-GATEWAY.md](components/QMT-GATEWAY.md)、[QMT-GATEWAY-INSTALL.md](QMT-GATEWAY-INSTALL.md) |
| 处理日常运维 | [scenarios/DAILY-OPERATIONS.md](scenarios/DAILY-OPERATIONS.md) |
| 查看历史 CR 文档迁移 | [legacy/CR-DOCS-MIGRATION.md](legacy/CR-DOCS-MIGRATION.md) |

CR 编号文档不再作为用户主入口。已合并的旧文档位于 `docs/legacy/archive/`，只用于历史审计。

## 2. 模块一：环境与项目边界

### 2.1 Python 与依赖

1. 使用 `uv` 管理 Python 解释器、依赖和命令运行。
2. 不手工维护 `.venv/`，不把依赖直接写入锁文件。
3. 默认环境不安装 ML 可选依赖组。实验 23-29 的 ML 全流程和 `tests/test_experiment_23_29_ml_factor_suite.py` 需要 `pyproject.toml` 中的 `ml` dependency group，该组包含 `scikit-learn` 和 `LightGBM`。运行前使用：

```bash
uv sync --python 3.11 --group ml
uv run --python 3.11 --group ml pytest -q tests/test_experiment_23_29_ml_factor_suite.py
```

CR-139 S10 的 no-bypass / lake-as-of 合同测试是 static/fixture 范围，不要求安装 `ml` 组；ML 全流程运行仍不授权 provider、lake write、catalog publish、runtime 或交易操作。

4. 常用检查命令：

```bash
uv run --python 3.11 pytest -q
uv run --python 3.11 python -m py_compile <path>
```

### 2.2 配置文件边界

项目允许文档描述 `.env` 字段名，但不得把真实 token、password、cookie、session、private key、账户号或 broker 原始回执写入仓库。示例必须使用 `<redacted>`、`[REDACTED]` 或 digest/ref 形式。

QMT gateway、runner 和真实 provider 相关配置只在逐次授权窗口内读取；没有授权时，只能进行静态文档、fixture、mock、dry-run 或本地测试。

## 3. 模块二：数据与引擎

### 3.1 本机数据湖与 NAS 同步

默认数据湖和研究产物放在本机目录，项目通过 `MARKET_DATA_LAKE_ROOT` 或命令行 `--lake-root` 读取数据湖；推荐本机数据湖根目录为 `/home/hyde/data/quant-lab/data-lake`，并与 NAS 末级目录 `/data-lake` 保持一致；研究数据根目录为 `/home/hyde/data/quant-lab/research`。NAS 不作为默认实时读写路径，只作为 rsync daemon 同步目标。

本地 `.env` 使用以下数据湖配置；真实 NAS 用户名和密码只写入本机未跟踪 `.env`，不得提交：

```bash
MARKET_DATA_LAKE_ROOT=/home/hyde/data/quant-lab/data-lake
MARKET_DATA_LAKE_ARCHIVE_ROOT=/home/hyde/data/quant-lab/archive
MARKET_DATA_LAKE_BACKUP_ROOT=/home/hyde/data/quant-lab/backup
MARKET_DATA_LAKE_RESTORE_ROOT=/home/hyde/data/quant-lab/restore
QUANT_LAB_RESEARCH_ROOT=/home/hyde/data/quant-lab/research
QUANT_LAB_RESEARCH_REPORTS_ROOT=/home/hyde/data/quant-lab/research/reports
QUANT_LAB_RESEARCH_RUNS_ROOT=/home/hyde/data/quant-lab/research/runs
QUANT_LAB_EXPERIMENTS_ROOT=/home/hyde/data/quant-lab/research/experiments
QUANT_LAB_NOTEBOOK_OUTPUTS_ROOT=/home/hyde/data/quant-lab/research/notebooks
QUANT_LAB_RESEARCH_EXTRA_SOURCES="reports runs notebooks/outputs"
MARKET_DATA_NAS_IP=192.168.101.83
MARKET_DATA_NAS_USERNAME=<由用户本机填写>
MARKET_DATA_NAS_PASSWORD=<由用户本机填写>
MARKET_DATA_NAS_RSYNC_MODE=daemon
MARKET_DATA_NAS_RSYNC_PORT=873
MARKET_DATA_NAS_RSYNC_MODULE=<NAS rsync daemon 模块名>
MARKET_DATA_NAS_RSYNC_LAKE_TARGET=/data-lake
MARKET_DATA_NAS_RSYNC_RESEARCH_TARGET=/research
MARKET_DATA_NAS_RSYNC_DELETE=false
```

创建本机目录后，先 dry-run 检查同步计划，再执行：

```bash
mkdir -p /home/hyde/data/quant-lab/{lake,archive,backup,restore,research/{reports,runs,experiments,notebooks}}
scripts/sync_data_lake_to_nas.sh push all
scripts/sync_data_lake_to_nas.sh push all --execute
```

`--delete` 会删除 NAS 端本机主湖中不存在的文件，只能在确认 NAS 应与本机完全一致时使用。

### 3.2 数据准备

数据准备面向研究输入，不自动触发 provider fetch、lake write、catalog publish 或真实 lake 写入。执行前检查：

| 检查项 | 要求 |
|---|---|
| 数据集 | 明确 `dataset`、`start/end`、universe 和 benchmark。 |
| 来源 | 明确 `run_id/source/interface`，不能混用未知来源。 |
| 覆盖 | 明确 `denominator`，不能用样本行数替代覆盖证明。 |
| 质量 | 明确 `quality_status` 和质量检查结论。 |
| 追溯 | 明确 `catalog/lineage`，能追到发布来源和输入版本。 |

### 3.3 质量真相边界

legacy quality report、legacy old report、lake quality/catalog current truth、current quality truth、coverage proof forbidden 是固定边界词：

| 对象 | 可做什么 | 禁止做什么 |
|---|---|---|
| `reports/data_quality_report.csv` | 只能作为 legacy quality report 路径示例或历史边界说明。 | 不得作为 `current quality truth`、coverage proof、fixture、fallback。 |
| legacy old report | 只能说明旧报告不可继续作为当前证据。 | 不得用 legacy old report 或旧 `data/**` 补证。 |
| `quality/catalog` | 当前质量与 lineage 的入口说明。 | 不能绕过 catalog/lineage 直接补证。 |
| lake quality/catalog current truth | 当前质量真相应来自 lake quality/catalog 和可追溯 lineage。 | 不用旧 CSV、旧 flat data 或手工报告替代。 |

如果质量检查缺少 `dataset`、`start/end`、`denominator`、`run_id/source/interface`、`quality_status` 或 `catalog/lineage`，该数据不得进入策略研究或 runner 输入。

### 3.4 引擎执行

引擎模块覆盖 loader、portfolio、backtest 和 metrics。使用前先阅读 [components/ENGINE.md](components/ENGINE.md)，确认输入 schema、时间可得性、复权视图、成本假设和 PIT 检查。引擎结果是研究证据，不是 QMT admission pass。

## 4. 模块三：实验与报告

### 4.1 运行实验

实验模块用于 chapter 实验、参数扫描、候选报告和指标比较。典型步骤：

1. 确认数据质量检查通过。
2. 选择实验脚本和参数。
3. 运行本地实验。
4. 读取 `ExperimentManifest`、指标摘要和候选输出。
5. 检查是否存在数据泄漏、benchmark 缺失、成本假设缺失或 lineage 不完整。

### 4.2 报告检查

报告只能引用当前 run 的 manifest、quality/catalog、lineage 和指标输出。旧报告、旧数据目录、手工 CSV 和未发布 candidate 不得补成当前证据。

## 5. 模块四：多因子研究

### 5.1 研究对象

多因子研究以项目内部对象为准：

| 对象 | 用途 | 检查点 |
|---|---|---|
| `FactorSpec` | 描述因子定义、输入字段、窗口、方向和限制。 | 字段存在、时间可得、PIT 通过。 |
| `FactorRunSpec` | 描述一次因子运行的 universe、日期、数据版本和参数。 | `run_id`、lineage、dataset 明确。 |
| factor panel / label window | 生成因子值与标签。 | 缺失率、极值、对齐、停牌和复权视图检查。 |
| `FactorEvaluationReport` | 评价 IC / RankIC、分层收益、turnover、exposure。 | 指标口径、样本分母、成本假设完整。 |
| `MultiFactorPortfolioPlan` | 合成多因子目标组合。 | 权重、约束、换手、风险暴露检查。 |
| `StrategyAdmissionPackage` | 输出给 runner 的策略准入包。 | 只作为模拟盘入口审查输入，不自动下单。 |

### 5.2 典型研究案例

完整案例见 [scenarios/MULTIFACTOR-RESEARCH-TO-STRATEGY.md](scenarios/MULTIFACTOR-RESEARCH-TO-STRATEGY.md)。大步骤如下：

1. 数据准备：确认 `dataset`、`start/end`、质量状态和 catalog/lineage。
2. 因子定义：编写 `FactorSpec`，检查字段、窗口、方向和禁用字段。
3. 因子运行：生成 factor panel 和 label window，检查 PIT 和 available_at。
4. 单因子评价：输出 IC / RankIC、分层收益和稳定性。
5. 多因子组合：生成 `MultiFactorPortfolioPlan`，检查换手、集中度和行业暴露。
6. 准入包：生成 `StrategyAdmissionPackage`，作为 runner P1 的输入。

Backtrader 只作为 [reference/BACKTRADER-MODULE-REFERENCE.md](reference/BACKTRADER-MODULE-REFERENCE.md) 中定义的 execution semantic reference，不作为多因子研究主框架，不作为 production truth，不作为 simulation-ready，不作为 QMT admission pass。

#### CR-017 复权双视图与 QMT 消费边界

CR-017 将研究消费口径和 QMT 执行价口径分开。chart、long_horizon_research、factor_research / 因子研究可以显式选择 `qfq`、`hfq` 或 `returns_adjusted`；QMT order intent、成交回报和对账只能使用 raw-only / broker reference。

| 检查项 | 当前值 |
|---|---|
| non-raw execution allowed count | `0` |
| scale_up allowed count | `0` |
| QMT execution price policy | raw-only |

真实 VWAP、minute、tick、Level2、order-match 和 microstructure impact cost 均保持 blocked；研究视图通过不解除 QMT 执行边界。

## 6. 模块五：QMT Gateway

### 6.1 Gateway 组成

QMT gateway 文档分三层：

| 文档 | 用途 |
|---|---|
| [QMT-GATEWAY-INSTALL.md](QMT-GATEWAY-INSTALL.md) | Windows S 端安装、env 占位、diagnostics、serve、health、capabilities。 |
| [QMT C/S Bridge Runbook](QMT-C-S-BRIDGE-RUNBOOK.md) | HMAC / pairing、endpoint matrix、scope、No-real-operation。 |
| [reference/RUNNER-QMT-AUTHORIZATION.md](reference/RUNNER-QMT-AUTHORIZATION.md) | runtime authorization 模板、scope separation、evidence redaction。 |

### 6.2 手动启动与检查

只有在逐次 runtime authorization 包含 `gateway_start` / `port_bind` 时，才能启动 gateway。典型检查顺序：

1. 在 Windows S 端检查私有 env 字段均为占位或本机私密值，仓库不得保存真实值。
2. 运行 diagnostics，确认端口、依赖、session 和 endpoint 能力。
3. 启动 `serve`，只开放授权窗口内允许的地址和端口。
4. 调用 health / capabilities，确认 gateway 仍在授权窗口内。
5. 若授权包含 `account_readonly`，只读取脱敏持仓摘要。
6. 运行完成后停止 gateway，记录停止时间、进程状态和 evidence digest。

### 6.3 禁止边界

QMT gateway 文档不授权真实 QMT、真实发单、撤单、账户查询、凭据读取、真实 broker lake 写入、真实抓取、真实 lake 写入或 publish。`shadow`、`dry_run`、`mock`、gateway health、capabilities、CP5、CP6、CP7、Story verified 或文档存在都不是交易许可。

#### CR-019 QMT CS bridge runbook 与用户边界

[QMT C/S Bridge Runbook](QMT-C-S-BRIDGE-RUNBOOK.md) 是 QMT C/S bridge 的用户边界入口，说明 HMAC / pairing、endpoint matrix、fallback、No-real-operation 和 per-run authorization。CR019-S10 只提供文档边界和检查入口；没有逐次授权时，dependency_change、credential_read、provider_fetch、publish、simulation_run、真实 broker 操作和 QMT 调用都保持 blocked。

## 7. 模块六：Runner

### 7.1 Runner 阶段

Runner 当前面向 RUNNER-QMT simulation multifactor，阶段如下：

| 阶段 | 目标 | 检查点 |
|---|---|---|
| P0 | runtime profile、stage、authorization、kill-switch 检查。 | `runtime_authorization` 必须有效；授权缺失即 blocked。 |
| P1 | 只生成多因子目标组合。 | 不下单、不触达 QMT runtime、不读取凭据、不进入 `small_live` / `live`。 |
| P2 | 用脱敏持仓快照生成 simulation order plan。 | 持仓只保留 digest、bucket、instrument_ref。 |
| P3 | 在授权窗口内执行 simulation cancel/submit。 | stage/risk/kill-switch 通过；未知状态进入 manual takeover。 |
| P4 | 对账订单、撤单、成交 / 未成交、持仓变化和本地计划。 | 差异进入 manual takeover 或 kill-switch 候选。 |
| P5/P6 | readiness contract、runbook、稳定性窗口和 operator 入口。 | 仍不代表 daily scheduler 已生产化。 |

### 7.2 手动运行案例

完整步骤见 [scenarios/MULTIFACTOR-SIMULATION-RUNNER-OPERATION.md](scenarios/MULTIFACTOR-SIMULATION-RUNNER-OPERATION.md)。操作者按以下顺序执行：

1. 准备策略准入包：确认 `StrategyAdmissionPackage` 来自当前质量通过的研究 run。
2. 申请 runtime authorization：只申请本次 simulation 所需 scope，明确 time window、rollback plan、allowed commands 和 forbidden commands。
3. 启动 gateway：按 QMT gateway 模块完成 diagnostics、serve、health、capabilities。
4. 获取只读持仓快照：只保存脱敏摘要，不保存原始账户、原始证券代码、精确持仓或资金细节。
5. 运行 runner P1-P4：生成目标组合、订单计划、simulation submit/cancel 和对账结果。
6. 停止 gateway：确认进程停止、授权窗口关闭、evidence 已脱敏。
7. 检查结果：若有 unknown order、recon_diff、session_expired、risk_blocked 或 kill_switch_triggered，进入 manual takeover。

当前入口状态：

| 项目 | 状态 | 证据 |
|---|---|---|
| simulation stability window | `5/5 pass` | `process/evidence/RUNNER-QMT-SIMULATION-MULTIFACTOR-STABILITY-WINDOW-SUMMARY-2026-06-26-r6.json` |
| simulation readiness | `READY_WITH_RISK`，已接受 | `process/checks/RUNNER-QMT-SIMULATION-MULTIFACTOR-SIMULATION-OPERATIONAL-READINESS-CLOSURE-2026-06-26.md` |
| runtime input policy | `POLICY_DEFINED` | `process/policies/RUNNER-QMT-SIMULATION-MULTIFACTOR-RUNTIME-INPUT-GATEWAY-LIFECYCLE-POLICY-2026-06-26.md` |
| gateway lifecycle policy | `POLICY_DEFINED` | `process/checks/RUNNER-QMT-SIMULATION-MULTIFACTOR-OPS-POLICY-CLOSURE-2026-06-26.md` |
| `small_live` / `live` | `DEFERRED` | 必须独立 CR、独立人工决策、独立 runtime authorization |

因此当前已具备受控人工授权 simulation 模拟盘运行的入口条件；没有有效逐次授权时，仍只能进行 fixture / dry-run / mock 检查。长期自动化或无人值守模拟盘尚未就绪，仍需要额外的 preflight checker、运行日历、健康监控、日报和 incident 自动收敛。

### 7.3 非交易窗口模式

非交易窗口可以用同一个 operator 脚本完成 dry-run 准备，不读取 env、不构造 QMT client、不连接 gateway：

```bash
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python scripts/qmt/run_multifactor_simulation_operator.py \
  --mode fixture \
  --spec-json <operator-spec-json> \
  --output-dir process/evidence/runner-simulation
```

可用模式：

| mode | 用途 |
|---|---|
| `preflight-only` | 只检查必填字段和 evidence 输出结构。 |
| `plan-only` | 生成 P1 target 和 P2 order plan。 |
| `fixture` | 运行 P1/P2/P4 fixture，P3 submit/cancel 为 `no_op`。 |
| `reconcile-only` | 复核 P4 fixture 对账合同。 |

非交易窗口 evidence 必须满足：`runtime_authorization_granted=false`、`small_live_or_live_authorized=false`、`submitted_count=0`、`cancelled_count=0`，并通过 `validate_operator_evidence` 脱敏检查。

当前冻结输入和完成记录：

| 对象 | 路径 |
|---|---|
| StrategyAdmissionPackage | `process/context/RUNNER-QMT-SIMULATION-MULTIFACTOR-FORMAL-STRATEGY-ADMISSION-PACKAGE-2026-06-25.json` |
| operator spec | `process/context/RUNNER-QMT-SIMULATION-MULTIFACTOR-FORMAL-OPERATOR-SPEC-2026-06-25.json` |
| 非交易窗口完成记录 | `process/checks/RUNNER-QMT-SIMULATION-MULTIFACTOR-NON-TRADING-WINDOW-COMPLETION-2026-06-25.md` |

可重复执行的离线入口：

```bash
uv run --python 3.11 python scripts/qmt/run_multifactor_simulation_operator.py \
  --mode fixture \
  --spec-json process/context/RUNNER-QMT-SIMULATION-MULTIFACTOR-FORMAL-OPERATOR-SPEC-2026-06-25.json \
  --strategy-admission-json process/context/RUNNER-QMT-SIMULATION-MULTIFACTOR-FORMAL-STRATEGY-ADMISSION-PACKAGE-2026-06-25.json \
  --output-dir process/evidence/runner-simulation-formal-2026-06-25/fixture
```

非交易窗口不得传 `--env-file`，不得使用 `--mode runtime`。交易窗口 runtime 前必须重新取得逐次授权，并替换为授权窗口内生成的真实 current positions 脱敏输入。

### 7.4 交易窗口 runtime input 与 gateway lifecycle

交易窗口 runtime 输入必须通过私有 overlay 和 builder 生成，输出保存在私有 runtime 目录，不能写入 `process/` 或 Git tracked 路径：

```bash
uv run --python 3.11 python scripts/qmt/build_multifactor_runtime_inputs.py \
  --base-spec-json process/context/RUNNER-QMT-SIMULATION-MULTIFACTOR-FORMAL-OPERATOR-SPEC-2026-06-25.json \
  --strategy-admission-json process/context/RUNNER-QMT-SIMULATION-MULTIFACTOR-FORMAL-STRATEGY-ADMISSION-PACKAGE-2026-06-25.json \
  --runtime-overlay-json <private-runtime-overlay.json> \
  --readonly-evidence-ref <redacted-readonly-evidence-ref> \
  --run-id <authorized-run-id> \
  --runtime-authorization-ref <per-run-authorization-ref> \
  --expected-runtime-profile cr138-simulation \
  --output-dir /home/hyde/.quant-lab/runtime/qmt/cr138-simulation
```

Windows gateway 由操作者在 Windows 项目目录启动。推荐命令形态：

```powershell
uv run --with typer --python 3.11 python -m trading.qmt_runtime_cli serve `
  --env-file .env `
  --host 172.30.32.1 `
  --port 18765 `
  --runtime-authorization-ref <per-run-simulation-runtime-authorization-ref>
```

gateway 启动命令本身不等于 runtime 授权。每次 simulation runtime 仍必须从 P0 health / identity、P0 capabilities 和 P0.5 signed readonly 开始；若修改影响 gateway 的 `trading/*`，必须同步到 `/mnt/c/quant-lab-runtime`，由操作者重启 gateway 后重新验证。

### 7.5 安全计数

| Counter | Current value |
|---|---:|
| `default_real_operation_authorization_claim` | `0` |
| `qmt_api_call` | `0` |
| `real_order_call` | `0` |
| `real_cancel_call` | `0` |
| `account_query_call` | `0` |
| `account_write_call` | `0` |
| `credential_read` | `0` |
| `real_broker_operation` | `0` |
| `real_broker_lake_write` | `0` |
| `real_lake_write` | `0` |
| `provider_fetch` | `0` |
| `publish` | `0` |
| `simulation_run` | `0` |
| `live_run` | `0` |
| `small_live_run` | `0` |
| `scale_up_run` | `0` |
| `real_snapshot_pull` | `0` |
| `incident_persisted` | `0` |
| `unsupported_execution_claim_unblocked` | `0` |
| `sensitive_raw_value_output` | `0` |

Runbook、incident playbook、README、USER-MANUAL、CP5、CP6/CP7、Story verified 或文档存在均不自动授权 `simulation`、`live`、`small_live`、`scale_up`。文档合同不自动授权真实运行。

### 7.5 CR-015 / CR-016 边界

CR-015 只覆盖 QMT foundation 的 `shadow`、`dry_run`、`mock` 和 [QMT-TRADING-RUNBOOK.md](QMT-TRADING-RUNBOOK.md)。CR-016 承接后续 staged activation，但 `simulation`、`live_readonly`、`small_live`、`scale_up` 都必须经过 per-run authorization、stage gate、risk gate、reconciliation gate、kill switch 和 rollback plan。

缺少任一 gate 时，真实 QMT、真实发单、撤单、账户查询、凭据读取、真实 broker lake 写入、真实抓取、真实 lake 写入和 publish 都保持 blocked。

### 7.6 CR-013 full-history / unsupported 声明边界

CR-013 将 limited-window 研究证据和 full-history 声明边界分开：`2025-02-11..2026-02-18` 只表示 supported limited window；`2020-01-01..2024-12-31` 仍保持 blocked window，当前 full-history 状态为 `research_limited_only`，不能声明为 production strict pass。

unsupported register 中的 research_only / research-only、unsupported 和 blocked 项不进入正式 pass denominator。`real_vwap_execution`、VWAP fill、minute / tick / Level2 / order-match execution 和 microstructure impact cost 都保持 blocked / unsupported；任何解除 blocked 状态都需要独立 Story、CP5 和用户显式授权。

## 8. 模块七：日常运维

### 8.1 盘前

1. 阅读 [scenarios/DAILY-OPERATIONS.md](scenarios/DAILY-OPERATIONS.md)。
2. 检查数据质量、策略准入包、授权窗口、gateway session 和 kill-switch 状态。
3. 确认上一交易日无未关闭 incident、manual takeover 或对账差异。

### 8.2 盘中

1. 只在授权窗口内执行 runner。
2. 每次阶段切换检查 stage、risk、kill-switch 和 authorization expiry。
3. 出现 heartbeat_fail、risk_blocked、recon_diff、manual_trigger、recovery_required 时，停止继续推进并进入 incident 流程。

### 8.3 盘后

1. 停止 gateway。
2. 检查订单、撤单、成交 / 未成交和持仓变化对账。
3. 记录脱敏 evidence digest。
4. 未解决订单、未知状态或对账差异必须进入 manual takeover 或 kill-switch 候选。

### 8.4 QMT Incident Playbook

QMT incident 入口是 [QMT-INCIDENT-PLAYBOOK.md](QMT-INCIDENT-PLAYBOOK.md)，标题为 QMT Incident Playbook。该 playbook 覆盖 `shadow`、`simulation`、`live_readonly`、`small_live`、`scale_up`，并定义 heartbeat_fail、risk_blocked、recon_diff、manual_trigger、recovery_required 的 trigger、immediate action、owner、evidence required、recovery gate 和 rollback target。

## 9. 模块八：参考与归档

| 类别 | 文档 |
|---|---|
| 授权参考 | [reference/RUNNER-QMT-AUTHORIZATION.md](reference/RUNNER-QMT-AUTHORIZATION.md) |
| Backtrader no-copy | [reference/BACKTRADER-MODULE-REFERENCE.md](reference/BACKTRADER-MODULE-REFERENCE.md) |
| Research semantic alignment | [reference/RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md](reference/RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md) |
| CR 文档归档映射 | [legacy/CR-DOCS-MIGRATION.md](legacy/CR-DOCS-MIGRATION.md) |

归档文档只用于审计，不作为当前用户操作指南。当前用户应从 `docs/README.md`、本手册、`components/`、`scenarios/` 和 `reference/` 进入。

## 10. 故障排查

| 现象 | 处理 |
|---|---|
| `session_expired` | 刷新 Windows gateway session，重新执行 diagnostics；授权窗口过期则停止。 |
| authorization 缺失或过期 | 停止 runner 和 gateway，重新申请逐次授权。 |
| health 通过但 capabilities 缺失 | 不进入 P3；检查 gateway 配置、endpoint allowlist 和 stage scope。 |
| query positions 返回原始 payload | 丢弃结果，不落 evidence；修复 redaction 后重跑。 |
| order status unknown | 停止后续 submit/cancel，进入 manual takeover。 |
| reconciliation mismatch | 标记 recon_diff，执行 kill-switch 或人工接管。 |
| 质量报告缺字段 | 不进入研究或 runner；补齐 quality/catalog 和 lineage 后重新检查。 |
