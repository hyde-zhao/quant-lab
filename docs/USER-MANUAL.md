# 用户使用手册

## 1. 开始之前

本手册面向希望在本地研究日频股票策略的用户。当前工具定位是“本地离线量化回测层”：数据准备可以联网，回测、参数扫描、候选筛选和偏差审计默认离线读取本地文件。

所有命令默认在当前仓库根执行。`quant-lab/` 是本工具项目的 future-facing canonical 根目录；`local_backtest/` 是历史仓库名 / legacy alias，仅用于兼容旧路径、旧过程证据和历史审计语境。`README.md` 与 `docs/USER-MANUAL.md` 是当前 production 项目的正式用户文档出口。

### 项目根与协作边界

| 对象 | 定位 | 用户应如何处理 |
|---|---|---|
| `quant-lab/` | 本地回测工具项目 canonical 根 | 在这里运行命令、维护工具代码、必要示例、报告占位和用户文档。 |
| `local_backtest/` | 历史仓库名 / legacy alias | 仅用于兼容旧本地目录、历史 CR、过程证据和审计引用；不再作为 future-facing canonical 项目名。 |
| `llm-wiki` | 外部学习知识库 | 不复制进本项目；学习复盘、长篇学习资料和知识库整理继续留在 `llm-wiki`。 |
| `work/studies/quant-trading/local_backtest/` | 旧建议路径 / 误创建空骨架 | CR-001 中已确认无文件并清理；不要再把它当作项目根。 |
| `delivery/` | meta-flow 通用交付包概念，不是本 production 项目出口 | CR-001 中已确认无文件并清理；本项目不向 `delivery/**` 写交付物，不生成安装脚本。 |

不要把学习资料大规模拷贝进 `quant-lab`。本项目只保留工具代码、配置、必要示例、报告占位、过程证据和用户手册；学习笔记任务在 `llm-wiki` 中处理，工具代码任务在 `quant-lab` 中处理。历史文档中的 `local_backtest` 仍按 legacy alias 理解。

Agent 协作边界：`meta-po` 负责编排 CR 与检查点，`meta-dev` 负责目录和过程状态收敛，`meta-doc` 负责 README 与用户手册刷新。上述角色不越权修改代码、测试、真实数据、报告数据或安装脚本。

### 你需要准备的材料

| 材料 | 格式 | 必填 | 说明 |
|---|---|---:|---|
| Python 环境 | Python 3.11 | 是 | 项目要求 `>=3.11,<3.13`，示例统一使用 Python 3.11。 |
| 依赖环境 | `uv` | 是 | 使用 `uv sync --python 3.11` 和 `uv run --python 3.11 ...`。 |
| 价格数据 | `data/prices.parquet` | 是 | 必需字段：`trade_date`, `symbol`, `close`。 |
| 股票池 | `data/index_members.parquet` | 是 | 必需字段：`symbol`；固定池需披露非 PIT 与幸存者偏差。 |
| 交易日历 | `data/trade_calendar.parquet` | 是 | 必需字段：`trade_date`；可选 `is_open`。 |
| manifest | `data/manifests/data_prep_manifest.jsonl` | 是 | 数据准备批次事实源，用于断点续传和审计。 |
| 数据质量报告 | `reports/data_quality_report.csv` | 否 | 这是 `legacy quality report` / `legacy old report`，只保留旧 flat/report 链路说明；CR-007 后 current quality truth 来自 configured lake root 下的 `quality/catalog`。 |
| CR-011 新版研究输出 | `reports/experiment_17_21_cr011/**` | 运行后生成 | 新版实验 17-21 研究报告、四阶段 factor panel audit 与五类 robust validation 的隔离输出目录。 |
| 真实行情数据 | 用户自备或数据准备生成 | 否 | 仓库不包含真实生产行情样本。 |
| 旧 repo `data/` | reference-only | 否 | 只能作为人工历史线索；不能作为 fallback、迁移源、覆盖证明、fixture、smoke 前置条件或运行时输入。 |

### Python 环境（uv）

- 依赖声明来源：`pyproject.toml`。
- 锁定结果来源：`uv.lock`。
- 日常命令入口：统一使用 `uv run --python 3.11`。
- 安装依赖：使用 `uv sync --python 3.11`。
- 一次性工具：优先使用 `uvx`；需要临时依赖时使用 `uv run --with <package>`。
- 不建议把裸 `pip install` 或系统 Python 作为默认工作流入口。

```bash
uv sync --python 3.11
uv run --python 3.11 pytest -q
```

## 2. 完整工作流程

```text
用户操作                         工具内部                                  是否等待确认
────────────────────────────────────────────────────────────────────────────────────
准备数据源配置                    读取 config/data_prep.yaml                 否
运行数据准备                      AKShare adapter、节流、重试、raw、manifest  否
标准化 raw cache                  normalizer 派生三类 parquet                否
生成质量报告                      quality 输出 pass/warn/fail 和新鲜度        否
加载本地数据                      data_loader 离线校验 parquet 和质量门禁     否
运行单次回测                      backtest + strategy + portfolio + metrics   否
运行参数扫描                      scanner 默认执行 60 组参数                  否
输出候选参数                      candidates 选择 <=4 组候选                  否
生成报告图表                      charts 输出 PNG 图表和 Markdown 索引        否
人工平台验证                      用户手动把候选回填聚宽                     是，人工执行
真实性增强扩展/换源前             确认 exact source/interface 与可用时点并回归 是，建议评审
CR-011 因子研究报告刷新            输出新版报告、panel、robust validation 到隔离目录 是，CP8 已通过
CR-014 Batch-A 合同/护栏            验证 source of truth、publish gate、DuckDB 只读、研究消费边界 是，S01..S08 已 verified
CR-014 S09 真实抓取/写湖            后续 Batch-B 分时段 provider fetch 与 raw/manifest 写湖 是，需 S09 LLD+CP5+per-run authorization
CR-015 QMT foundation              S01..S07 已 CP7 verified；仅 shadow / dry-run / mock runbook 和边界静态测试 是，不进入 simulation/live
CR-016 staged activation runbook    S01..S04 与 S07 已 CP7 verified；S05/S06 later-gated 且 implementation_allowed=false 是，文档不自动授权任何运行
CR-017 复权双视图消费边界           S01..S06 已 CP7 verified；QMT raw-only 与迁移指南已收敛 是，scale_up 仍受 CR016-S06 和研究成熟度门控
CR-019 S09 deferred register        S01/S02 上游已 verified；后置能力 register 已 CP7 verified 是，不新增依赖或抓取 minute/Level2
CR-019 S10 QMT C/S bridge runbook   汇总 Stage 6 admission、QMT C/S bridge、gate、fallback 与用户边界 是，只读文档，不提供真实操作许可
CR-025 research execution semantic alignment 汇总 semantic diff、order_intent_draft_v1、Backtrader no-copy、no-real-operation、QMT 后续路线和 CR-030 候选边界 是，只读文档，不提供依赖安装、Backtrader run、QMT、publish、simulation/live 或多因子研究主框架许可
CR-030 多因子策略研究入口          从 FactorSpec 到 StrategyAdmissionPackage 的本地离线研究与实验闭环 是，达到策略侧模拟盘入口审查输入；不提供 QMT-ready、simulation-ready 或真实运行授权
```

## 3. 环境准备

1. 同步依赖：

```bash
uv sync --python 3.11
```

2. 运行测试确认环境：

```bash
uv run --python 3.11 pytest -q
```

3. 可选语法检查：

```bash
uv run --python 3.11 python -m compileall engine strategies tests
```

当前已验证结果为全量 pytest `10 passed`，compileall 通过；详见 `process/VERIFICATION-REPORT.md`。

## 4. 数据准备与更新

### 4.1 数据源与更新周期

当前已注册的真实数据准备 source/interface：

| 数据集 | source | interface | 状态 |
|---|---|---|---|
| 价格 | `akshare` | `stock_zh_a_hist` | 已解析 |
| 交易日历 | `akshare` | `tool_trade_date_hist_sina` | 已解析 |
| 固定指数成分 | `akshare` | `index_stock_cons` | 已解析 |
| PIT 股票池 | `tushare` 探测中 | `index_members.snapshot` / provider `index_member` | 2026-05-22 对 HS300 相关代码和 2024 窗口返回 0 行，当前不能发布 current truth；不得用 `index_weight` 或 `stock_basic` 替代 |
| PIT 股票池 | `jqdata` | `index_members.snapshot` / package `jqdatasdk` / provider `get_index_stocks` | `2025-02-11..2026-02-18` limited window 曾发布为 `published/pass/available/pit_available`；CR-012 后当前 strict readiness 需按 `snapshot_asof` 复验 |
| PIT 权重 | `jqdata` | `index_weights.snapshot` / provider `get_index_weights` | limited window 曾发布为 `published/pass/available/pit_available`；只证明权重与 as-of membership 对齐，不替代 PIT membership |
| 股票主数据 | `jqdata` | `stock_basic.snapshot` / provider `get_all_securities` | limited window 曾发布为 `published/pass/available/pit_available`；只作为 lifecycle gate，不证明 PIT universe |
| 交易状态 | `jqdata` | `trade_status.daily` / provider `get_price + get_extras` | limited window 曾发布为 `published/pass/available`；当前 strict 复验需结合 PIT denominator 和缺口归因 |
| 涨跌停价格 | `jqdata` | `prices_limit.daily` / provider `get_price` | limited window 曾发布为 `published/pass/available`；换窗口或换源需复验 |
| 事件数据 | `jqdata` | `events.disclosure` / provider `get_extras` | 当前事件口径为 ST 状态变更；空事件表在 source/interface 与 `available_at_rule` 冻结时允许通过 |

更新策略：

- 默认增量补缺口，不重复已成功批次。
- 最近 N 个交易日回补由 `recent_trade_days_backfill` 控制，默认 `5`，语义上应按交易日历理解。
- `force_refresh=True` 才允许重复抓取已成功批次。
- 数据源失败时，如果本地 parquet 和质量报告仍覆盖请求区间且质量合规，回测主路径继续离线运行并披露数据新鲜度与失败项。

### 4.2 AKShare 限速、重试和缓存策略

[config/data_prep.yaml](../config/data_prep.yaml) 默认配置：

| 配置项 | 默认值 | 行为 |
|---|---:|---|
| `request_interval_seconds` | `2` | 相邻请求间隔至少 2 秒。 |
| `batch_size` | `50` | 单批最多 50 个 symbol 或等价请求单位。 |
| `max_concurrency` | `1` | 保守串行抓取。 |
| `max_retries` | `3` | 最多 1 次初始请求 + 3 次重试。 |
| `backoff_policy` | `exponential_jitter` | 指数退避，最多 `backoff_max_seconds`。 |
| `raw_cache_retention` | `keep_forever` | raw cache 保留，用于复现 parquet。 |

### 4.3 运行数据准备

价格数据示例：

```bash
uv run --python 3.11 python - <<'PY'
from engine.data_prep import DataPrepRequest, run_data_prep

summary = run_data_prep(
    DataPrepRequest(
        source="akshare",
        interface="stock_zh_a_hist",
        params={"adjust": "qfq", "target_dataset": "prices"},
        symbols=["000001", "000002"],
        date_range={"start": "2019-01-01", "end": "2025-12-31"},
    )
)
print(summary.run_id)
print(summary.statuses)
PY
```

固定沪深 300 成分示例：

```bash
uv run --python 3.11 python - <<'PY'
from engine.data_prep import DataPrepRequest, run_data_prep

summary = run_data_prep(
    DataPrepRequest(
        source="akshare",
        interface="index_stock_cons",
        params={
            "target_dataset": "index_members",
            "index_code": "000300",
            "snapshot_date": "2025-12-31",
            "is_pit_universe": False,
        },
    )
)
print(summary)
PY
```

交易日历示例：

```bash
uv run --python 3.11 python - <<'PY'
from engine.data_prep import DataPrepRequest, run_data_prep

summary = run_data_prep(
    DataPrepRequest(
        source="akshare",
        interface="tool_trade_date_hist_sina",
        params={"target_dataset": "trade_calendar"},
        date_range={"start": "2019-01-01", "end": "2025-12-31"},
    )
)
print(summary)
PY
```

说明：这些命令会访问 AKShare。免费接口可能变化或限流；出现失败时先查看 manifest，不要提高并发压测数据源。

### 4.4 Tushare `hs300_index` 显式回补 runbook

Tushare 真实源默认关闭。真实启用必须同时满足四个前置条件：`enabled=true`、exact interface `allowlist` 命中、`TUSHARE_TOKEN` 只从环境变量读取、用户执行显式真实抓取命令（`explicit command`）。缺任一条件时，数据层 job 必须 fail fast；回测、reader、comparison、Notebook 和 Backtrader optional backend 不会替用户联网。

#### 准备本地环境变量

本轮用户运维决策是用仓库根的本地 `.env` 配置 `TUSHARE_TOKEN` 和 `MARKET_DATA_LAKE_ROOT`。`.env` / `.env.*` 已由 `.gitignore` 忽略，不提交；不要创建或传播包含真实值的样例文件。文档中只允许使用以下占位形式：

```bash
TUSHARE_TOKEN=<由用户本机填写，不提交>
JQDATA_USERNAME=<由用户本机填写，不提交>
JQDATA_PASSWORD=<由用户本机填写，不提交>
MARKET_DATA_LAKE_ROOT=<外置 lake root，由用户本机填写，不提交>
MARKET_DATA_LAKE_ARCHIVE_ROOT=<外置 archive root，由用户本机填写，不提交>
MARKET_DATA_LAKE_BACKUP_ROOT=<外置 backup root，由用户本机填写，不提交>
MARKET_DATA_LAKE_RESTORE_ROOT=<外置 restore root，由用户本机填写，不提交>
```

项目代码只读取环境变量；`pyproject.toml` / `uv.lock` 已落地 `tushare==1.4.29` 和 `jqdatasdk` dependency group。Tushare 正式命令入口通过 `uv run --env-file .env --group tushare --python 3.11 ...` 加载本机 `.env` 并启用该 group。一种方式是让 `uv run` 读取该文件：

```bash
uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli hs300-backfill --help
```

另一种方式是先加载到当前 shell，再执行 dry-run 或真实命令：

```bash
set -a
. ./.env
set +a
```

凭据边界：

- `TUSHARE_TOKEN` 不写入 README、用户手册、配置样例、日志、manifest、quality、catalog、测试 fixture 或对话。
- `JQDATA_USERNAME` / `JQDATA_PASSWORD` 只作为环境变量读取，不写入命令、raw、manifest、quality、catalog、测试 fixture 或对话。
- 外部存储用户名和密码由用户在系统层挂载配置或凭据管理器中处理，不进入 README、用户手册、`.env.example`、日志、manifest、quality、catalog、测试 fixture 或对话。
- agent 不请求、记录或回显外部存储用户名、外部存储密码和真实 token。

#### 当前验证状态

截至 `2026-05-18T20:01:26+08:00`，CR-005 已完成 `2024-01-02` 至 `2024-01-05` 小窗口真实 Tushare 链路验证，结论为 PASS：

| 环节 | 状态 | 说明 |
|---|---|---|
| preflight | PASS | `.env` 可加载，token 只做存在性检查，lake root 来自 `.env` 且通过路径前置检查。 |
| dry-run | PASS | `hs300-backfill --dry-run true` 网络调用为 0、写入为 0。 |
| 真实 fetch/write | PASS | 正式 `--group tushare` 入口使用 `tushare==1.4.29`，小窗口写出 success raw 与 manifest。 |
| normalize / quality / catalog / reader | PASS | `hs300_index` canonical 4 行、quality `pass`、dataset `available`、reader 读回 4 行。 |
| CLI REQUIRED | PASS | `normalize` / `validate` / `read` 已支持 `dataset=hs300_index`。 |
| 仓库写入边界 | PASS | 复验后 `data/market_data` 未重新生成；真实 lake root 仍应是外置路径。 |

该 PASS 只覆盖上述小窗口。更大窗口、2015-2025 长区间或全量回补仍必须由用户另行显式授权；agent 不得把本次 PASS 扩大解释为全量数据已完成或已授权。

#### Tushare-only limited PIT / W3 smoke runbook

当前 strict 研究窗口为 `2025-02-11..2026-02-18`。截至 2026-05-22，该窗口曾完成 Tushare-only 发布收敛：`index_members` 由 `index_weight` 派生，`index_weights` 来自同一 Tushare `index_weight`，`stock_basic` 来自 Tushare `stock_basic`，`trade_status` 由 `suspend_d + stock_st + daily` 合成，`prices_limit` 来自 `stk_limit`，`events` 第一版仅覆盖 `stock_st` 派生 ST 进入 / 退出事件。CR-012 后这条记录只作为 historical pass；当前 `production_strict_research` 必须按新 readiness audit 重新审计，不声明完整历史或持续生产 `production_current_truth`。

#### JQData limited PIT / W3 historical runbook

JQData 真实源默认关闭，当前仅保留为历史 runbook 和对照来源，不作为当前 `production_strict_research` 的 pass 证明或 blocker：`source=jqdata`、package `jqdatasdk`，已注册 `index_members.snapshot`、`index_weights.snapshot`、`stock_basic.snapshot`、`trade_status.daily`、`prices_limit.daily`、`events.disclosure`。`index_weights` 或 `stock_basic` 不能替代 `index_members` 的 PIT membership 合同。

历史 JQData smoke 窗口同为 `2025-02-11..2026-02-18`；该窗口曾完成 `index_members`、`index_weights`、`stock_basic`、`trade_status`、`prices_limit`、`events` 全链路真实 smoke。该记录仅用于审计追溯，当前 Tushare-only current truth 已替换该路径。limited window 不能写成 2005 起完整历史覆盖。

```bash
UV_CACHE_DIR=.cache/uv uv run --env-file .env --group jqdata --python 3.11 python -m market_data.cli jqdata-acquire \
  --dataset index_members \
  --index-code 399300.SZ \
  --start-date 2025-02-11 \
  --end-date 2025-02-11 \
  --run-id run-jqdata-index-members-smoke \
  --batch-id jqdata-hs300-20250211 \
  --dry-run true \
  --json
```

真实执行必须显式传 `--enable-real-source`；凭据只从 `.env` 或进程环境中的 `JQDATA_USERNAME` / `JQDATA_PASSWORD` 读取。执行后沿用现有链路：`normalize --dataset index_members`、`validate --dataset index_members`、`publish --dataset index_members`、`read`、`revalidate`、`replay`。`replay` 必须保持 `network_calls=0`，只从 manifest/raw 复核，不补数。

```bash
UV_CACHE_DIR=.cache/uv uv run --env-file .env --group jqdata --python 3.11 python -m market_data.cli jqdata-acquire \
  --dataset index_members \
  --index-code 399300.SZ \
  --start-date 2025-02-11 \
  --end-date 2025-02-11 \
  --run-id run-jqdata-index-members-smoke \
  --batch-id jqdata-hs300-20250211 \
  --dry-run false \
  --enable-real-source \
  --json

UV_CACHE_DIR=.cache/uv uv run --env-file .env --group jqdata --python 3.11 python -m market_data.cli normalize \
  --dataset index_members \
  --run-id run-jqdata-index-members-smoke

UV_CACHE_DIR=.cache/uv uv run --env-file .env --group jqdata --python 3.11 python -m market_data.cli validate \
  --dataset index_members \
  --index-code 399300.SZ \
  --start-date 2025-02-11 \
  --end-date 2025-02-11 \
  --run-id run-jqdata-index-members-smoke
```

#### 数据湖备份、恢复与演练

备份 / 恢复命令只处理本地已挂载的数据湖路径，不读取 `TUSHARE_TOKEN`，不联网，不触发 backfill。默认 dry-run；只有 `backup-run --execute`、`restore-run --execute` 和 `restore-drill --execute` 会复制文件。报告只输出 root label、相对路径、file count、bytes 和 checksum 状态，不输出 `.env` 内容、token、外部存储凭据或真实私有路径。

可用命令：

| 命令 | 用途 | 默认是否写文件 |
|---|---|---:|
| `backup-plan` | 规划指定 release 的备份范围 | 否 |
| `backup-run` | 执行备份；未传 `--execute` 时只 dry-run | 否 |
| `backup-verify` | 对比 lake 源文件与备份副本 checksum | 否 |
| `backup-report` | 汇总备份 release 的文件、大小和 checksum 状态 | 否 |
| `restore-plan` | 规划从备份恢复到 restore root | 否 |
| `restore-run` | 执行恢复；未传 `--execute` 时只 dry-run | 否 |
| `restore-drill` | 恢复到临时 root 后执行 read / revalidate / replay 演练 | 是，写临时目录 |

备份计划和执行：

```bash
UV_CACHE_DIR=.cache/uv uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli backup-plan \
  --release-id <release-id> \
  --json
```

```bash
UV_CACHE_DIR=.cache/uv uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli backup-run \
  --release-id <release-id> \
  --execute \
  --json
```

备份校验和报告：

```bash
UV_CACHE_DIR=.cache/uv uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli backup-verify \
  --release-id <release-id> \
  --json
```

```bash
UV_CACHE_DIR=.cache/uv uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli backup-report \
  --release-id <release-id> \
  --json
```

恢复计划、执行和演练：

```bash
UV_CACHE_DIR=.cache/uv uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli restore-plan \
  --release-id <release-id> \
  --json
```

```bash
UV_CACHE_DIR=.cache/uv uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli restore-run \
  --release-id <release-id> \
  --execute \
  --json
```

```bash
UV_CACHE_DIR=.cache/uv uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli restore-drill \
  --release-id <release-id> \
  --execute \
  --json
```

安全规则：

- `restore-root == lake-root` 会 fail fast，不允许把恢复目标设为正在使用的 hot lake。
- checksum 相同会 skip；checksum mismatch 会失败并拒绝覆盖。
- `restore-drill` 的 replay 段固定 `network_calls=0`、`auto_execute=false`。
- 可用 `--run-id <run-id>`、`--dataset <dataset>`、`--no-include-raw`、`--no-include-canonical`、`--no-include-gold`、`--no-include-quality` 收敛范围。
- 保留策略当前是只读预检：published run 受保护，failed / candidate run 保留用于审计，成功 run 清理前仍要求备份校验和人工确认；本版本不提供自动删除命令。

2026-05-22 真实运维 smoke 已用已发布 `prices` run 验证：backup plan/run/verify/report 覆盖 4 个文件、78,772 bytes；首次 backup execute copied=4，二次 same checksum skip=4；restore drill 返回 read available、revalidate pass、replay `network_calls=0`；恢复到 configured restore root 后，`read` 返回 3 行，`revalidate.network_calls=0`，`replay.network_calls=0` 且 `writes=0`。`restore-root == lake-root` 已返回 `restore_root_conflict`。

#### CR-010 production_strict 当前状态

截至 2026-05-22，真实 lake 在 `2025-02-11..2026-02-18` limited window 内曾完成 Tushare-only current truth 发布：Tushare 发布 `prices`、`adj_factor`、`hs300_index`、`trade_calendar`、`index_members`、`index_weights`、`stock_basic`、`trade_status`、`prices_limit`、`events`。

CR-012 后不要把这条历史 `PASS` 直接理解为当前 strict readiness pass。当前复验必须使用新 readiness audit 口径：`index_members` 默认按 `snapshot_asof` 展开到 open trade dates；`daily_materialized` 只用于每日物化 membership；`index_weights` 只校验权重与 as-of membership 对齐；`trade_calendar.available_at` 表示日历已知时间，`next_open` 必须单独存储；`adj_factor.available_at` 继续 strict PIT 检查，ex-post 复权只能保留 blocked claim。

`2025-02-11..2026-02-18` limited window 不能外推为 `2020-01-01..2024-12-31` 或完整历史覆盖。`production_current_truth` 仍按更强口径 blocked；`production_strict_research` 也必须以 CR-012 新审计输出为准，明确区分 `data_gap`、`metadata_semantics_gap`、`audit_mode_mismatch` 和 `unsupported_claim`。

#### CR-013 full-history 与 unsupported 声明边界

阅读 readiness 或研究报告时，先区分两个窗口：

| 窗口 | 当前声明 | 说明 |
|---|---|---|
| `2025-02-11..2026-02-18` | supported limited window | 可用于 limited-window 研究说明，不代表完整历史。 |
| `2020-01-01..2024-12-31` | blocked / `research_limited_only` | 当前 10 个正式 dataset 均为 `limited_window_only`，不能声明 full-history production strict pass。 |

正式 dataset 分母固定为 10 项：`prices`、`adj_factor`、`hs300_index`、`trade_calendar`、`index_members`、`index_weights`、`stock_basic`、`trade_status`、`prices_limit`、`events`。CR-013 新 gap register 写入 `reports/data_lake_readiness_2020_2024_cr013/full_history_gap_register.csv`；旧 `reports/data_lake_readiness_2020_2024/*` 只作为只读证据基线。

真实执行价声明保持 fail-closed：`real_vwap_execution`、`vwap_fill_claim`、`vwap_execution`、`minute_execution` 和 `order_match_execution` 当前均为 blocked / unsupported。close proxy 只能表达研究降级，不能写成真实 VWAP 或 production strict 真实执行价；`amount/volume` 也不能派生为真实 VWAP。

unsupported register 的 9 项必须按以下四类理解：

| 类别 | 项 |
|---|---|
| supported | limited-window supported |
| research-only | `industry_classification`、`market_cap`、`style_exposure_beta_size_value_quality` |
| unsupported | `capacity_inputs_turnover_adv_constraints`、`corporate_actions_full`、`non_hs300_benchmark`、`minute_tick_level2_order_match`、`microstructure_impact_cost` |
| blocked | `real_vwap_execution` 以及 execution / VWAP blocked claims |

所有 `pass_denominator=excluded` 项进入正式 dataset pass denominator 的次数为 0。当前 provider fetch、lake write、credential read、legacy data read、old report overwrite 均为 0；任何真实补数、VWAP / 分钟数据接入或 allowed claim 解除，都必须另起 Story、CP5 和用户显式授权。路线图只在 `docs/DATA-LAKE-FULL-HISTORY-BACKFILL-ROADMAP.md` 中描述后续授权门，不是可执行 runbook。

#### CR-014 Batch-A 全 A 数据湖合同与护栏状态

CR-014 把长期目标定义为全 A 股证券自存在 / 上市日起至最近已闭市交易日的 production current truth。当前完成的是 `CR014-FULL-HISTORY-LAKE-BATCH-A`：`CR014-S01` 至 `CR014-S08` 已全部 verified，但它们是离线合同和护栏，不是全 A 真实数据回补或生产发布。

用户侧应按以下模型理解数据湖链路：

```text
plan -> run -> normalize/replay -> validate -> publish -> read/query
```

| 阶段 | 用户应如何理解 | 写入 / 发布边界 |
|---|---|---|
| `plan` | 生成 dataset、date range、source/interface、lake root、窗口和缺口计划 | 不联网、不写湖、不读凭据。 |
| `run` | 后续 S09 才允许在授权后真实 provider fetch | 只在 S09 Batch-B 且 per-run 授权齐全时写 raw、manifest、run metadata。 |
| `normalize/replay` | 从 raw / manifest 生成 normalized candidate 或重放 evidence | 不更新 catalog current pointer；raw 缺失时返回 `replay_source_missing`，不补抓。 |
| `validate` / parity | 生成 quality/readiness/parity candidate 或 audit evidence | PASS 不自动 publish；parity PASS 也只是 evidence。 |
| `publish` | 唯一能更新 catalog current pointer 的门 | 必须通过 Explicit Publish Gate；没有明确 publish intent / approval 时 pointer changes 为 0。 |
| `read/query` | 读取已发布 current truth 或受控 audit evidence | reader / DuckDB 默认只能读 catalog pointer 指向的 published truth；candidate 不会被提升为事实源。 |

CR-014 的事实源仍是外置 Parquet lake、manifest 和 catalog current pointer。DuckDB 仅是 read-only query / audit / parity 候选层：当前不引入 DuckDB 依赖，不打开或写入 `.duckdb`，不把 DuckDB view、SQL result、parity report 或 feature result 当作 source of truth。DuckDB 不负责写生产事实；真实写入由 lake production pipeline 的单写者链路负责。

研究消费层只能读取以下三类输入：

| 允许输入 | 说明 |
|---|---|
| published current truth | catalog current pointer 指向的 canonical / gold / quality truth。 |
| clean reader output | reader / clean feed 已完成 schema、PIT、quality、复权和 claim boundary 校验。 |
| structured claim metadata | `allowed_claims`、`blocked_claims`、`required_missing`、permission counters 和 audit evidence refs。 |

研究消费层不得扫描 candidate lake、不得 publish、不得 fetch provider data、不得读取凭据、不得写 DuckDB、不得打开 `.duckdb` 作为事实源，也不得使用旧 reports 或旧 `data/**` 作为 current truth。缺 published truth 时，正确输出是 typed `required_missing` / `blocked_claims` 和 remediation，不是自动补数。

真实 provider 抓取与 raw / manifest / run metadata 写湖被拆到 `CR014-S09-windowed-real-fetch-lake-write-run`，属于后续 `CR014-REAL-RUN-BATCH-B`。S09 执行前必须同时满足：

| 门禁 | 必须状态 |
|---|---|
| 上游 Story | `CR014-S01` 至 `CR014-S08` 已 verified。 |
| S09 设计 | S09 LLD approved。 |
| S09 检查点 | S09 CP5 approved。 |
| per-run 授权 | 用户为每次真实 run 提供 `authorization_id`。 |
| 授权范围 | 明确 dataset、date range、source/interface allowlist、lake root、window policy、resume policy、rollback policy。 |

没有上述任一条件时，真实 provider fetch、lake write、credential read、current pointer publish 和 S09 real execution 都必须保持 0。即使 S09 完成 raw / manifest 写湖，后续 normalize、validate 和 publish 也必须按独立 gate 执行，不能自动连跳。

W3 / minute / tick / Level2 / VWAP 的 production allowed claim 仍为 0。解除这些 blocked claim 必须另有 source/interface、独立 Story、CP5、用户显式授权；真实 VWAP 还必须具备真实 `vwap` 字段、`vwap_status=available` 和 execution audit pass。close proxy 与 `amount/volume` 派生 VWAP 不能解除真实 VWAP 或微观结构数据边界。

#### CR-018 S01 production current truth scoped release 与 dataset group

CR-018 S01 production current truth 是合同层变更：它定义第一版 production current truth 的 release scope、P0 dataset group、P1 dataset group 和 blocked claims，不发布 catalog current pointer，也不把 CR014 S14 candidate 自动提升为 production current truth。

| 合同项 | 用户应如何理解 | 失败 / blocked 输出 |
|---|---|---|
| scoped release | 第一版只覆盖 `2015-01-05..latest_closed_trade_date`。 | 2015 年前或 since-inception 完整声明输出 `blocked/future_backfill`。 |
| P0 dataset group | `prices_raw`、`adj_factor`、`prices_qfq`、`prices_hfq`、`returns_adjusted`、`trade_calendar`、`pit_universe`、`lifecycle_code_change`、`trade_status`、`prices_limit_st_suspend`、`benchmark_group` 是 required_for_publish。 | 任一 P0 缺失时 core release 和 `production_current_truth_scoped_release` blocked。 |
| P1 dataset group | `industry_classification`、`market_cap_total`、`market_cap_float`、`beta_style_factors`、`adv`、`turnover_rate`、`liquidity_capacity`、`market_impact_cost` 是辅助组。 | P1 缺失不阻断 core release，但阻断 neutralized、pure-alpha、capacity、scale_up 和资金放大声明。 |
| unknown dataset | readiness 只接受登记过的 exact dataset id。 | 未登记 dataset 输出 `unregistered_dataset`，进入 publish readiness 的通过次数为 `0`。 |

该合同是离线 / fixture 可验证的结构化边界。provider fetch、lake write、credential read、current pointer publish、QMT operation 计数均为 `0`；`market_data.catalog` 只允许挂接只读 metadata helper，不会触发 publish 或 current pointer 写入。

#### CR-015 QMT foundation runbook 边界

CR-015 只交付 QMT foundation 的离线合同和文档化运行边界。用户可阅读 [QMT Trading Foundation Runbook](QMT-TRADING-RUNBOOK.md)，但该 runbook 不是 simulation 或 live 授权文件。

当前 CR-015 允许的操作只有：

| Mode | 用户能做什么 | 必须保持的边界 |
|---|---|---|
| `shadow` | 用本地 target portfolio、policy metadata 和 fixture snapshot 生成 order intent、risk result、state transition 与 audit summary。 | 不调用 QMT、MiniQMT、XtQuant 或 broker API。 |
| `dry_run` | 查看 broker lake schema / write plan / reconciliation prerequisites。 | 不打开、不创建、不写入真实 broker lake，也不写 `data/**` 或 `reports/**`。 |
| `mock` | 用本地 mock broker event 验证 OMS 状态变化。 | 不触达真实账户、柜台、交易节点或真实 broker 事件。 |

CR-015 保持以下 blocked claims：

| Blocked item | Current value | 后续归属 |
|---|---:|---|
| `simulation_activation` | `0` | CR016-S01 / CR016-S04 + per-run authorization |
| `live_activation`、`live_readonly`、`small_live`、`scale_up` | `0` | CR016-S05 / CR016-S06 + per-run authorization |
| `qmt_api_call` | `0` | CR016 受控 adapter / runbook |
| `real_order_call` / `real_cancel_call` | `0` | CR016 逐次授权 |
| `account_query_call` / `account_write_call` | `0` | CR016 逐次授权 |
| `credential_read` | `0` | 文档和测试中始终禁止输出敏感值；生产运行需另行受控 secret handling |
| `real_broker_lake_write` / `real_lake_write` / `provider_fetch` / `publish` | `0` | 对应真实运行 Story、Explicit Publish Gate 和用户授权 |
| `real_trading_supported_claim_count` | `0` | 不由 CR-015 解除 |
| `microstructure_allowed_claim_count` | `0` | 真实 VWAP、minute、tick、Level2、order-match 仍为 blocked / unsupported |

如果用户准备推进 CR-016 的后续真实运行阶段，需要先确认目标阶段不属于 later-gated 范围，且具备对应 LLD / CP5 / CP6 / CP7、per-run authorization、stage gate、reconciliation gate、kill switch / recovery gate，并为每次运行提供账户模式、策略、日期、资金上限、操作范围、审批人、回滚策略和停止条件。当前 `CR016-S01` 至 `CR016-S04` 与 `CR016-S07` 已 verified，但只覆盖受控离线 / 文档范围；`CR016-S05` 和 `CR016-S06` 仍为 later-gated，`implementation_allowed=false`。缺任一项时，不要启动 QMT / MiniQMT / GUI，不要调用 broker API，不要发单、撤单、查询账户、读取凭据、真实抓取、真实写湖、写真实 broker lake 或 publish。

#### CR-016 QMT staged activation runbook 边界

CR-016 的 staged activation 用户入口是 [QMT Simulation / Live Activation Runbook](QMT-SIMULATION-LIVE-RUNBOOK.md) 和 [QMT Incident Playbook](QMT-INCIDENT-PLAYBOOK.md)。runbook 覆盖启动、审批、异常处理、对账、kill switch、暂停 / 恢复和回滚；incident playbook 覆盖 `shadow`、`simulation`、`live_readonly`、`small_live`、`scale_up` 的 incident 处理，并定义 `heartbeat_fail`、`risk_blocked`、`recon_diff`、`manual_trigger`、`recovery_required` 的 trigger、immediate action、owner、evidence required、recovery gate 和 rollback target。`CR016-S01` 至 `CR016-S04` 与 `CR016-S07` 已 verified，但 `CR016-S05` 和 `CR016-S06` 仍为 later-gated，`implementation_allowed=false`。该 runbook、incident playbook、CP5、CP6/CP7、Story verified 或文档存在均不自动授权 `simulation`、`live`、`small_live`、`scale_up` 或真实 broker 操作。

用户应按下表理解阶段：

| Stage | 用户动作 | 必要边界 |
|---|---|---|
| `shadow` | 继续使用 CR-015 foundation 离线证据 | 只允许 `shadow` / `dry_run` / `mock` |
| `simulation` | 准备后续模拟盘 gate 申请 | 需要 CR016-S01/S02/S03 evidence、runbook readiness 和 per-run authorization |
| `live_readonly` | 准备后续只读核对申请 | later-gated，需要对账通过和只读准入 |
| `small_live` | 准备后续小资金申请 | later-gated，需要资金上限、kill switch drill、审批和 rollback ref |
| `scale_up` | 准备后续资金放大申请 | later-gated；CR017 S01-S06 已 verified，但仍需要 CR016-S06 解禁、研究成熟度 gate 和用户后续显式授权 |

Per-run authorization 摘要至少包含 `authorization_id`、`mode`、`strategy_id`、`run_id`、`stage`、`capital_limit`、`order_scope`、`approver`、`approved_at`、`expires_at`、`rollback_plan_ref`。这些字段只允许记录脱敏摘要；不要写账户号、token、password、cookie、session、private key、真实持仓、真实 broker root 或私有路径。

默认安全计数保持：

| Counter | Current value |
|---|---:|
| `simulation_run` | `0` |
| `live_run` | `0` |
| `small_live_run` | `0` |
| `scale_up_run` | `0` |
| `real_broker_operation` | `0` |
| `default_real_operation_authorization_claim` | `0` |

Recovery gate 至少要求 `reconciliation_status=pass`、`manual_takeover_record=recorded`、kill switch ready 或 shadow 不适用、授权仍有效或已刷新，并保留 rollback target。该 gate 只把 incident blocked 状态转成可重新申请的候选状态，不启动真实运行。

如果任何人要求直接启动 simulation/live、打开 QMT / MiniQMT / GUI、调用 broker API、发单、撤单、查询账户、读取凭据、拉取真实 snapshot、写真实 broker lake、provider fetch、写真实 lake 或 publish，应停止当前流程，回到对应 stage gate 和 meta-po 授权路径。

#### CR-019 QMT CS bridge runbook 与用户边界

CR-019 S10 的用户入口是 [QMT C/S Bridge Runbook](QMT-C-S-BRIDGE-RUNBOOK.md)。该 runbook 汇总 Stage 6 admission、QMT C/S bridge、pairing/HMAC、完整 endpoint matrix、run gate、fallback、deferred capability register 和 No-real-operation 表。

用户应按下表理解当前边界：

| 用户动作 | 当前允许的理解 | 必须保持的边界 |
|---|---|---|
| 阅读 QMT C/S bridge runbook | 了解 C 侧 client、Windows gateway、endpoint、gate 和 fallback 合同 | 文档不是运行开关，不提供真实 QMT 或 broker 操作许可 |
| 查看 Story `verified`、CP5、CP6 或 CP7 | 确认离线 / fixture / 静态合同通过对应门禁 | 不替代 per-run authorization、stage gate、risk gate、kill switch 或 reconciliation gate |
| 使用 pairing / HMAC 说明 | 理解调用方识别、scope、timestamp、nonce 和防重放 | HMAC pass 之后仍要继续执行所有运行门控 |
| 使用 fallback / signed file candidate | 进行人工 dry-run 演练、排障或脱敏候选复核 | 不绕过 gateway、endpoint matrix、run gate 或 per-run authorization |
| 查看 deferred register | 理解 Backtrader W6、Qlib W7、minute Spike、Level2 Spike 的后续入口 | 不新增依赖、不抓取 provider、不改变 Stage 6 P0 |

No-real-operation 计数在本阶段必须保持：

| Counter | Current value |
|---|---:|
| dependency_change | `0` |
| service_start | `0` |
| credential_read | `0` |
| qmt_miniqmt_xtquant_operation | `0` |
| provider_fetch | `0` |
| lake_or_broker_lake_write | `0` |
| publish | `0` |
| simulation_live_run | `0` |

如果用户准备把 QMT C/S bridge 从合同推进到真实运行，必须先新建或恢复对应 CR / CP 链路，并逐次给出 per-run authorization。授权摘要只能记录脱敏 ref、角色、阶段、run id、回滚方案和有效期；不要把账户号、token、password、cookie、session、private-key material、真实持仓、真实 broker root 或私有路径写入文档、日志或检查点。

#### CR-025 research execution semantic alignment 用户边界

CR-025 的专题入口是 [CR025 Research Execution Semantic Alignment](CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md)。它用于理解 CR025-S01..S06、DQ-CP3-CR025-01..06、semantic diff、`order_intent_draft_v1`、Backtrader optional / no-copy / `migration_candidate=[]`、no-real-operation 表、CR-020..CR-024 独立 QMT 路线，以及 CR-030 多因子研究框架借鉴候选上下文。

用户应按下表理解当前边界：

| 用户动作 | 可以理解为 | 不能理解为 |
|---|---|---|
| 阅读 CR-025 专题文档 | 了解 research execution semantic alignment 和后续路线关系 | 依赖安装、Backtrader run、QMT gateway 启动或真实交易授权 |
| 查看 semantic diff | lightweight baseline 与 Backtrader-style reference 的 research comparison | production truth、simulation-ready、QMT admission pass、factor tear sheet 或 IC report |
| 查看 `order_intent_draft_v1` | 后续 CR-020..CR-024 可审查的 later-gated draft | 订单、下单指令、撤单指令、账户查询请求或 broker lake 写入触发器 |
| 查看 Backtrader module reference | optional reference、lazy import、no-copy 和 `migration_candidate=[]` 合同 | 复制源码、迁移 samples/tests/datas、运行 Backtrader runtime 或把 Backtrader 当多因子研究主框架 |
| 查看 CR-030 候选上下文 | 后续可独立评估 FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪和策略准入包 | 本轮已经具备多因子研究主框架运行许可 |

故障处理规则：

| 现象 | 处理方式 |
|---|---|
| 文档或报告声称 CR-025 可直接启动 QMT、gateway、simulation 或 live | 视为越界声明，回到 CR-020..CR-024 的独立 CR / CP / stage gate / per-run authorization。 |
| semantic diff 被当成生产真相或模拟盘准入证据 | 改回 research comparison；必须保留 baseline / reference 双轨、unavailable 和 limitations。 |
| `order_intent_draft_v1` 被当成可提交订单 | blocked；draft 保持 `not_authorization=true`、`qmt_allowed=false`。 |
| Backtrader optional reference 被要求复制源码或运行 runtime | blocked；当前 `migration_candidate=[]`，源码级例外需新 CR、legal review、CP3 和 CP5。 |
| 用户要求 FactorSpec、IC / RankIC、分层收益、多因子组合、实验追踪或策略准入包 | 路由到 CR-030 或后续正式 CR；正式启动前重新验证 Qlib / Alphalens / vectorbt / Zipline Reloaded / LEAN / RQAlpha / vn.py / PyBroker / bt / Backtrader 等参考对象的 license、维护状态和 clean-room 边界。 |
| 出现凭据、真实账号、token、cookie、session、private key、交易密码或真实私有路径 | 停止写入；只允许脱敏 ref、授权摘要和边界说明。 |

#### CR-030 多因子策略研究入口

CR-030 的快速开始手册是 [CR030 因子研究快速开始](CR030-FACTOR-RESEARCH-QUICKSTART.md)。它给出从 `FactorSpec` / `FactorRunSpec`、factor panel / label window、`FactorEvaluationReport`、`MultiFactorPortfolioPlan`、`ExperimentManifest` / `ResearchReportCatalog` 到 `StrategyAdmissionPackage` 的本地离线研究路径。

用户现在可以做：

| 用户动作 | 允许范围 | 禁止解释 |
|---|---|---|
| 新增因子定义 | 使用 `engine.multifactor_contracts.FactorSpec` 和 `FactorRunSpec` 定义项目内部合同。 | 不把 Qlib / Alphalens / Zipline / LEAN 对象作为 truth。 |
| 准备本地 factor panel 和 label | 使用 `FactorPanelContract` / `LabelWindowSpec`，确保 no-lookahead、label 不重叠、lineage 完整。 | 不触发 provider fetch、lake write 或 publish。 |
| 生成单因子评价 | 使用 `build_factor_evaluation_report()` 输出 IC / RankIC / 分层收益 / turnover / cost / exposure。 | 不声明 production truth、QMT-ready、simulation-ready 或 live-ready。 |
| 组合多个因子 | 使用 `build_multifactor_portfolio_plan()` 的 `rule_weight` / `linear_score` 路线。 | 不启用 optimizer、cvxpy、ML workflow 或外部 runtime。 |
| 形成模拟盘入口审查输入 | 使用 `build_strategy_admission_package()` 汇总研究证据、manifest、catalog 和 handoff 草稿。 | 不把它当真实交易许可或真实模拟盘运行许可。 |

CR-030 的出口语义是完成多因子策略研究与实验闭环，达到策略侧模拟盘入口审查输入。QMT 接口 ready、simulation 账号、gateway、账户 / 订单和运行授权仍需 CR-020 / CR-021 等后续 CR 单独通过。

CR-025 当前 no-real-operation 用户可见计数保持：

| Counter | Current value |
|---|---:|
| dependency_change | `0` |
| Backtrader run | `0` |
| Backtrader source copy | `0` |
| broker_operation | `0` |
| QMT / MiniQMT / XtQuant operation | `0` |
| provider_fetch | `0` |
| lake_or_broker_lake_write | `0` |
| publish | `0` |
| simulation_live_run | `0` |
| credential_read | `0` |
| multifactor_framework_implementation | `0` |
| Qlib / Alphalens / vectorbt / vnpy.alpha integration | `0` |

#### CR-017 复权双视图与 QMT 消费边界

CR-017 将研究消费口径和 QMT 执行价口径分开。研究侧可以按用途选择 `qfq`、`hfq` 或 `returns_adjusted`，但 QMT order intent、下单意图、成交回报和对账只能使用 `raw` / broker reference。`CR017-S01` 至 `CR017-S06` 已完成 CP7 验证；其中 `CR017-S06` 只提供离线文档和 metadata helper。CR017 不读取凭据、不调用 QMT / MiniQMT / broker API、不发单、不撤单、不查询账户、不真实抓取、不写湖、不 publish，也不解除 CR016 scale_up later-gated 边界。

消费方选择规则如下：

| 消费方 | 推荐口径 | 允许事项 | 禁止事项 |
|---|---|---|---|
| chart | `qfq` | 展示图表时可用前复权，并在标题或 metadata 中标明 `research_adjustment_policy=qfq`。 | 不把图表价格写成执行价。 |
| long-horizon research | `hfq_or_returns_adjusted` | 长周期价格连续性优先 `hfq`，收益序列优先 `returns_adjusted`。 | 不把 raw price 结果声明为已完成复权治理。 |
| factor research | `returns_adjusted` | 因子研究默认用调整后收益；同一 run 只能有一个 `research_adjustment_policy`。 | 不混用 `qfq` / `hfq` / `returns_adjusted` 后继续声明 production pass。 |
| QMT order intent | `raw` | 只携带研究口径 metadata；执行价、委托价、成交价和对账价都使用 `raw` / broker reference。 | `qfq`、`hfq`、`returns_adjusted` 进入执行价。 |

QMT execution raw-only 的用户可见计数必须保持：

| 计数 | 当前值 |
|---|---:|
| non-raw execution allowed count | `0` |
| adjusted execution price pass count | `0` |
| real_order_call | `0` |
| real_cancel_call | `0` |
| account_query_call | `0` |

CR017 S01-S06 已完成 CP7 验证，但 production adjustment governance claim allowed count 和 scale_up allowed count 仍必须为 `0`。如果用户看到 scale-up、资金放大或 production adjustment governance 完成声明，应继续检查 CR016-S06 scale-up gate 是否已从 later-gated 解禁、研究成熟度 gate 是否通过、对应 CP5/CP6/CP7 是否存在，以及用户后续显式授权是否存在；缺任一项都应按 blocked claims 处理。

迁移时保留 legacy qfq：旧 qfq 基线仍是 `legacy_qfq_readonly`，旧报告不覆盖、不迁移为新报告、不作为 current truth。新的 `prices_qfq`、`prices_hfq` 和 `returns_adjusted` 是带 lineage 的派生视图，不替换旧报告证据。当前不声明真实 VWAP、minute、tick、Level2、order-match 或 microstructure impact cost execution 已支持；这些项保持 unsupported / blocked，解除需要独立 Story、CP5、验证证据和用户授权。

#### CR-011 因子研究生产级数据补齐状态

CR-011 已完成 `S01` 至 `S08` 的 Story 级实现与 CP7 验证，文档刷新也已完成，CP8 人工终验已 `approved`，当前状态是 `closed`。这表示真实 benchmark、PIT 股票池 / lifecycle、可交易性 / 涨跌停、OHLCV/VWAP clean feed、复权 / 公司行动、行业 / 市值 / 风格暴露、流动性 / 容量 / 成本敏感性、factor panel audit 与 robust validation 均已有验证证据，并已通过本轮终验收敛。

新版实验 17-21 输出必须写入 `reports/experiment_17_21_cr011/**`。旧 `reports/experiment_17_21/factor_strategy_report.md` 只作为 fixed-snapshot / proxy benchmark baseline 引用，不得覆盖、复制为新版报告或作为当前质量证明。

用户阅读 CR-011 报告时应先确认这些字段或视图是否齐全：

| 检查项 | 必须值 | 缺失时的处理 |
|---|---|---|
| factor panel stages | `raw`、`directional`、`winsorized`、`zscore` | fail closed；不得声明 `factor_panel_audited`。 |
| robust validation views | `rolling`、`annual`、`market_state`、`parameter_grid`、`cost_grid` | fail closed；不得生成强 allowed claim。 |
| 安全计数 | `network_calls=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_operations=0`、`old_report_overwrites=0` | 先定位触发路径；未授权时不得继续真实联网、写湖、读凭据、操作旧数据或覆盖旧报告。 |
| blocked claims | 上游 S01/S02/S05/S07 blocked claims 不被 S08 放宽 | blocked 优先级高于同名 allowed claim；必须先补齐上游数据或审计证据。 |

当前验证摘要：S08 定向测试 `3 passed`，上游和实验回归 `29 passed`，fail-closed probe 为 PASS。完整追溯见 `process/checks/CP7-CR011-S08-factor-panel-audit-and-robust-validation-VERIFICATION-DONE.md`，全量 Story 状态见 `process/STORY-STATUS.md`。

#### CR-006 旧 repo `data/` reference-only 边界

旧 repo `data/` 不属于 Tushare-first 数据合同的运行时输入。它只可作为 reference-only 的人工线索：用户另行授权后可以手动查看历史口径，但 agent、测试、reader、comparison、Backtrader optional backend、Notebook 和数据层 job 默认不得读取、列出、复制、迁移、比对或删除旧 repo `data/**`。

运行时缺口必须按新数据合同处理：缺少 `hs300_index`、canonical/gold、benchmark 或 quality/catalog 时返回结构化 `required_missing` / unavailable，并给出 dry-run 优先的 `remediation_job_spec` / `next_action`。不得用旧 repo `data/` 当 fallback，不得用旧 repo `data/` 证明覆盖率，不得把旧数据复制进测试 fixture 或 smoke 流程。

授权门禁如下：

| 场景 | 默认行为 | 用户需要做什么 |
|---|---|---|
| 只在文档中提到旧 repo `data/` | 允许 | 必须同时写明 reference-only 和不可 fallback / 不可迁移 / 不可覆盖证明。 |
| 想读取、列出、复制、迁移、比对或删除旧 `data/**` | 禁止 | 给出具体、显式、当次授权；未授权时次数为 0。 |
| 缺真实 Tushare / canonical / gold / benchmark 数据 | 返回缺口状态 | 先执行 dry-run，确认外置 lake root、dataset、interface、date range 和 run_id。 |
| 想把真实 lake 或报告写回仓库默认目录 | 禁止 | 使用仓库外 `MARKET_DATA_LAKE_ROOT` 或显式 `--lake-root`。 |

#### CR-007 质量报告 legacy 与 lake quality/catalog current truth

旧 `reports/data_quality_report.csv` 在 CR-007 后只能作为 `legacy quality report` / `legacy old report` 保留。它的 `coverage proof forbidden`：不得作为 `current quality truth`、coverage proof、fixture、fallback、smoke 前置条件或严肃研究准入证据，也不得覆盖旧报告来制造当前质量通过记录。旧 `data/**` 也同样 coverage proof forbidden。

当前质量真相源必须来自 configured lake root 下的 `quality/catalog`，即 `lake quality/catalog current truth` / `current quality truth`。可接受的 coverage proof 至少要写明 `dataset`、`start/end`、`denominator`、`run_id/source/interface`、`quality_status` 和 `catalog/lineage`。如果这些字段缺失，用户应先执行 dry-run 或查看 remediation，而不是用 legacy old report、旧 repo `data/**` 或测试 fixture 代替。

S05 文档和 guardrail 只允许在字符串中提及 `reports/data_quality_report.csv` 并标记 legacy/forbidden；不得读取、打开、覆盖该文件内容。静态测试也只扫描 README、USER-MANUAL、`.gitignore` 和测试自身，不进入 `data/**`、`reports/**`、`.env`、credentials 或真实 lake 路径。

#### 挂载外置数据湖

外部存储路径和本地挂载目标由用户环境决定。用户需要先在系统层完成挂载，并确认该本地路径可用；项目命令只把 `.env` 中的 `MARKET_DATA_LAKE_ROOT` 或显式 `--lake-root` 当作外置 `lake root` 使用。

未显式传 `--lake-root` 时，`hs300-backfill`、`normalize`、`validate` 和 `read` 优先使用 `.env` 中的 `MARKET_DATA_LAKE_ROOT`。不要把真实 lake root 改成仓库内默认目录；复验后 `data/market_data` 未重新生成，真实 raw、manifest、canonical、quality、catalog 或 gold 数据不应写回 Git 工作区。

#### dry-run / path preflight

先执行 dry-run，确认 job spec、路径和错误枚举。dry-run 网络调用为 0，写湖次数为 0：

```bash
UV_CACHE_DIR=.cache/uv uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli hs300-backfill \
  --index-code 399300.SZ \
  --start-date 2024-01-02 \
  --end-date 2024-01-05 \
  --run-id run-hs300-small-window \
  --dry-run true
```

dry-run 返回的 `remediation_job_spec` / job spec 至少应覆盖以下字段：

| 字段 | 必填 | 说明 |
|---|---:|---|
| `dataset` | 是 | `hs300_index`。 |
| `source` | 是 | `tushare`。 |
| `interface` | 是 | exact `hs300_index.daily`，必须在 allowlist 中。 |
| `index_code` | 是 | 默认候选 `399300.SZ`。 |
| `date range` | 是 | `start_date` / `end_date`，来自用户请求或缺口区间。 |
| `lake root` | 是 | 外置数据湖路径，来自显式 `--lake-root` 或 `.env` / 环境变量中的 `MARKET_DATA_LAKE_ROOT`；不要写入仓库真实 `data/**`。 |
| `run_id` | 是 | 进入 manifest、quality、catalog 和 lineage。 |
| `resume_policy` | 是 | `success=skip`、`failed=retry`、`partial_success=retry`、`duplicate_manifest=fail`。 |
| `dry_run` | 是 | 默认 `true`；确认后才允许真实执行。 |
| `path` | 是 | raw、manifest、canonical、quality、catalog、gold 的规划路径。 |
| `error enum` | 是 | 至少包含 `source_disabled`、`interface_not_allowed`、`missing_credential`、`quota_or_rate_limited`、`network_error`、`provider_error`、`schema_mismatch`、`quality_failed`、`lake_root_invalid`、`resume_conflict`。 |

#### 真实执行门控

确认 dry-run 后，真实抓取必须由用户显式授权，并同时具备有效 token、外置 lake root 和 `--enable-real-source`。凭据来自用户本机已显式加载的 `.env` 或系统环境变量，不在命令、文档或日志中展开：

```bash
UV_CACHE_DIR=.cache/uv uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli hs300-backfill \
  --index-code 399300.SZ \
  --start-date 2024-01-02 \
  --end-date 2024-01-05 \
  --run-id run-hs300-small-window \
  --dry-run false \
  --enable-real-source
```

真实写出 success raw 与 manifest 后，可以用同一正式入口执行 `hs300_index` 运维 CLI。以下命令未显式传 `--lake-root` 时优先使用 `.env` 中的 `MARKET_DATA_LAKE_ROOT`：

```bash
UV_CACHE_DIR=.cache/uv uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli normalize \
  --dataset hs300_index \
  --run-id run-hs300-small-window

UV_CACHE_DIR=.cache/uv uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli validate \
  --dataset hs300_index \
  --index-code 399300.SZ \
  --start-date 2024-01-02 \
  --end-date 2024-01-05 \
  --run-id run-hs300-small-window \
  --open-trade-dates 2024-01-02,2024-01-03,2024-01-04,2024-01-05

UV_CACHE_DIR=.cache/uv uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli read \
  --dataset hs300_index \
  --index-code 399300.SZ \
  --start-date 2024-01-02 \
  --end-date 2024-01-05 \
  --columns trade_date,index_code,close
```

真实执行后的顺序是 plan/fetch/normalize/validate/catalog/read/compare：先由 CR005-S01 数据层 job 写 raw/manifest/canonical/quality/catalog/gold，再由 CR005-S03 reader 只读本地 catalog 和 parquet，最后由 comparison 比较本地 left/right 文件。comparison 不调用 Tushare，不导入 connector/runtime/storage，不联网，不写 raw/manifest/canonical/quality/catalog/gold。

`required_missing` 只表示必需数据缺失。它不自动联网、不自动 backfill、不自动写湖；消费层只能返回 `remediation_job_spec` 和 `next_action`，提示用户按本 runbook 显式执行数据层 job。默认 `next_action` 应先建议 dry-run，不能静默拉取真实数据。

失败处理：

| 失败状态 | 处理方式 |
|---|---|
| `missing_credential` | 检查是否在 shell 环境中设置 `TUSHARE_TOKEN`；不要把 token 写入配置文件、README、日志、quality、catalog 或测试 fixture。 |
| `interface_not_allowed` | 检查 exact `interface` 是否进入 allowlist；不要用模糊匹配或相近接口替代。 |
| `quota_or_rate_limited` / `network_error` | 降低频率或稍后重试；不要提高并发压测数据源。 |
| `quality_failed` | 查看 quality CSV/Markdown 的缺口、重复键、lineage 和覆盖率；未通过前不要交给回测或 Backtrader。 |
| `required_missing` | 保持回测/reader/comparison 离线，只返回 `remediation_job_spec` / `next_action`。 |

`proxy_baseline` 是旧代理基准的唯一命名。`proxy_baseline` 不能填充 `hs300_index` benchmark 字段，也不得声明沪深 300 相对收益；缺真实 `hs300_index` 时应返回结构化 unavailable / required_missing。

Backtrader 是 `optional backend`，不默认替代轻量主路径。它只消费本地 canonical/gold + quality gate 派生的干净 feed；不联网、不读 token/connector、不导入数据源 connector、不绕过 quality gate。Backtrader 未安装、benchmark 缺失、PIT/复权/quality gate 失败时，应返回结构化不可用并回退轻量主路径，不触发补数。

### 4.5 Backtrader 可选后端

Backtrader 是显式启用的对照后端，不是默认回测框架。日常单次回测继续使用 `engine.backtest.run_backtest(...)`；该路径不需要安装 Backtrader，也不会导入 Backtrader。

安装可选依赖：

```bash
uv sync --python 3.11 --group backtrader
```

验证 Backtrader 本身可以在 Python 3.11 下实例化：

```bash
UV_CACHE_DIR=.cache/uv TUSHARE_TOKEN= uv run --python 3.11 --group backtrader python -c "import backtrader as bt; cerebro = bt.Cerebro(); print(type(cerebro).__name__)"
```

显式启用时，调用方必须传入 `BacktraderRequest`，其中 `ohlcv` 已经由 reader/quality gate 完成 PIT 对齐、复权价格生成和质量校验；adapter 不会替你生成 PIT、不计算复权因子、不读取外部数据源、不补齐 benchmark。

最小示例：

```bash
uv run --python 3.11 --group backtrader python - <<'PY'
import pandas as pd

from engine.backtest import run_backtest_with_backend
from engine.backtrader_adapter import BacktraderRequest

ohlcv = pd.DataFrame(
    {
        "trade_date": pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06"] * 2),
        "symbol": ["A", "A", "A", "B", "B", "B"],
        "open": [10.0, 10.5, 11.0, 20.0, 19.5, 20.5],
        "high": [10.5, 11.0, 11.5, 20.5, 20.0, 21.0],
        "low": [9.8, 10.2, 10.8, 19.8, 19.0, 20.0],
        "close": [10.0, 11.0, 12.0, 20.0, 19.0, 21.0],
        "adjustment_policy": ["qfq"] * 6,
    }
)
request = BacktraderRequest(
    ohlcv=ohlcv,
    calendar=["2020-01-02", "2020-01-03", "2020-01-06"],
    benchmark_result={"status": "available", "dataset": "hs300_index"},
    config={"initial_cash": 1_000_000.0, "benchmark_required": False},
    input_contract={
        "quality_status": "pass",
        "pit_checked": True,
        "pit_status": "pass",
        "adjusted_price_ready": True,
        "adjustment_policy": "qfq",
    },
)
result = run_backtest_with_backend(pd.DataFrame(), backend="backtrader", backtrader_request=request)
print(result.status)
PY
```

状态和处理方式：

| 状态 | 典型触发 | 用户处理 |
|---|---|---|
| `completed` | Backtrader 依赖可用，clean feed、PIT、复权和 benchmark policy 通过 | 可把结果作为轻量主路径的对照，不覆盖轻量结果。 |
| `backend_unavailable` | 未安装 Backtrader 或版本不符合固定依赖 | 使用轻量主路径；如需对照，先安装 `backtrader` group。 |
| `input_rejected` | quality fail、PIT fail、`available_at > decision_time`、adjusted price 缺失、`adj_factor` 冲突、`adjustment_policy` 混用 | 回到数据层修复 reader/quality/PIT/复权契约；不要在 adapter 中补数据。 |
| `benchmark_unavailable` | `benchmark_required=True` 且 benchmark 为 `required_missing` / `unavailable` / `quality_failed` | 查看 `missing_reason`、`next_action`、`remediation_job_spec`，按 4.4 的数据层 runbook 显式 dry-run / backfill。 |
| `failed` | Backtrader 运行期异常 | 保留轻量结果，检查 adapter 输入和 Backtrader 版本；不要临时切换未确认 fork。 |

边界：

- adapter 不读取 `TUSHARE_TOKEN`，不联网，不导入数据源 connector/runtime/storage。
- benchmark 缺失只返回 metadata 和 remediation spec，不 fetch、不 backfill、不写湖。
- `proxy_baseline` 不能填充 `hs300_index` benchmark 字段，也不能声明沪深 300 相对收益。
- adapter 不写真实 `data/**`、`reports/**` 或 `delivery/**`。

## 5. 标准化与质量报告

### 5.1 从 raw 派生 parquet

```bash
uv run --python 3.11 python - <<'PY'
from engine.normalizer import run_normalization

result = run_normalization(
    manifest_path="data/manifests/data_prep_manifest.jsonl",
    raw_root="data/raw",
    output_dir="data",
)
print(result.parquet_paths)
print(result.failed_batches)
print(result.mapping_failures)
PY
```

标准化只消费本地 raw cache 和 manifest，不导入 AKShare adapter，不联网。

### 5.2 生成质量报告

```bash
uv run --python 3.11 python - <<'PY'
from engine.quality import run_quality_report

result = run_quality_report(
    parquet_paths=None,
    manifest_path="data/manifests/data_prep_manifest.jsonl",
    report_dir="reports",
    requested_range={"start": "2019-01-01", "end": "2025-12-31"},
)
print(result.csv_path)
print(result.markdown_path)
print(result.quality_status)
PY
```

质量状态语义：

| 状态 | 是否允许回测 | 典型原因 |
|---|---|---|
| `pass` | 允许 | 覆盖、schema、缺失、重复、异常价格均满足门禁。 |
| `warn` | 允许，但报告披露 | 少量缺失、数据源失败但本地 parquet 合规、数据新鲜度需注意。 |
| `fail` | 阻断 | schema 缺失、覆盖缺口、未解决重复键、异常价格或请求区间缺失率大于 5%。 |

## 6. 离线加载数据

```bash
uv run --python 3.11 python - <<'PY'
from engine.data_loader import LoaderConfig, load_backtest_data

loaded = load_backtest_data(
    LoaderConfig(
        data_dir="data",
        manifest_path="data/manifests/data_prep_manifest.jsonl",
        quality_report_path="reports/data_quality_report.csv",
        start_date="2019-01-01",
        end_date="2025-12-31",
        adjustment_policy="qfq",
        quality_policy="pass_warn",
    )
)

print(loaded.close_df.shape)
print(loaded.universe[:5])
print(loaded.metadata)
PY
```

关键规则：

- loader 不会自动运行数据准备。
- 缺 parquet、缺质量报告、质量 `fail`、复权口径不匹配都会失败。
- `quality_policy="pass_only"` 时，`warn` 也会阻断。
- `allow_exploratory_recompute=True` 可在缺质量报告时尝试即时质量计算，但不建议作为正式验收路径。

## 7. 运行单次回测

```bash
uv run --python 3.11 python - <<'PY'
from engine.data_loader import LoaderConfig, load_backtest_data
from engine.backtest import BacktestConfig, run_backtest
from engine.portfolio import PortfolioConfig

loaded = load_backtest_data(
    LoaderConfig(
        data_dir="data",
        quality_report_path="reports/data_quality_report.csv",
        start_date="2019-01-01",
        end_date="2025-12-31",
    )
)

result = run_backtest(
    loaded.close_df,
    BacktestConfig(
        lookback_days=20,
        rebalance_freq=20,
        top_fraction=0.10,
        strategy_name="momentum",
        portfolio_config=PortfolioConfig(
            initial_cash=1_000_000.0,
            commission_rate=0.0003,
            slippage_rate=0.0002,
            sell_tax_rate=0.001,
        ),
    ),
    metadata=loaded.metadata,
)

print(result.metrics)
print(result.metadata)
print(result.portfolio_result.daily_snapshots[-1])
PY
```

当前回测口径：

- T 日收盘后生成信号。
- 成交只能发生在 T+1 或之后；当前默认近似为 T+1 收盘价成交。
- 新持仓从 T+1 收盘后承担后续收益。
- 成本包括 `commission_rate`、`slippage_rate`、`sell_tax_rate`。
- 缺失成交价或不可交易目标不被静默填充。

## 8. 参数扫描

默认动量参数网格：

| 参数 | 默认列表 |
|---|---|
| `lookback` | `[5, 10, 20, 30, 60]` |
| `rebalance_freq` | `[5, 10, 20, 30]` |
| `fraction` | `[0.05, 0.10, 0.20]` |

默认共 `5 * 4 * 3 = 60` 组。

```bash
uv run --python 3.11 python - <<'PY'
from engine.data_loader import LoaderConfig, load_backtest_data
from engine.scanner import run_parameter_sweep, write_sweep_csv

loaded = load_backtest_data(
    LoaderConfig(
        data_dir="data",
        quality_report_path="reports/data_quality_report.csv",
        start_date="2019-01-01",
        end_date="2025-12-31",
    )
)

sweep = run_parameter_sweep(loaded.close_df)
write_sweep_csv(sweep, "reports/momentum_param_sweep_local.csv")

print({"success": sweep.success_count, "failed": sweep.failed_count, "rows": len(sweep.rows)})
PY
```

失败处理：

- 默认 `continue_on_error=True`。
- 单组失败不会丢行，CSV 中保留 `status=failed` 和 `error_message`。
- 报告自由文本字段会做公式注入防护。

## 9. 候选报告与聚宽人工验证

```bash
uv run --python 3.11 python - <<'PY'
from engine.candidates import load_sweep_csv, select_candidates, write_candidate_csv

sweep = load_sweep_csv("reports/momentum_param_sweep_local.csv")
selection = select_candidates(sweep, max_candidates=4)
write_candidate_csv(selection, "reports/momentum_candidates_local.csv")

print(selection.rows)
print(selection.warnings)
PY
```

候选报告用途：

- 输出本地 Sharpe 最优、收益最优、保守低换手等候选。
- 候选数不超过 4 组。
- 提供 `joinquant_*` 字段作为人工回填与差异记录位置。
- 不自动调用聚宽，不提交平台任务，不轮询平台结果。

聚宽对比建议只看方向一致性：

- 候选排序方向。
- 收益与回撤量级。
- 换手特征。
- 成本、复权、股票池、交易约束差异是否可解释。

不要要求第一版与聚宽逐日净值完全一致。

## 10. 报告图表

标准图表生成入口会读取 `reports/` 下已经存在的 CSV，并输出 PNG 与 Markdown 图表索引：

```bash
uv run --python 3.11 python - <<'PY'
from engine.charts import generate_report_charts

artifacts = generate_report_charts("reports")
for artifact in artifacts:
    print(artifact.path)
PY
```

当前会按已有文件自动生成：

| 输入文件 | 输出图表 |
|---|---|
| `reports/equity_curve.csv` | `equity_curve.png`、`drawdown.png`、`monthly_returns.png`、`turnover_holdings.png` |
| `reports/momentum_param_sweep_local.csv` | `param_heatmap_sharpe_top*.png`、`param_heatmap_cumulative_return_top*.png` |
| `reports/momentum_candidates_local.csv` | `candidates_compare.png` |

图表统一写入 `reports/charts/`，索引写入 `reports/charts/index.md`。如果只运行了单次回测但还没有参数扫描或候选 CSV，入口会只生成单次回测相关图表。

推荐查看顺序：

1. 先看 `equity_curve.png` 和 `drawdown.png`，判断收益路径与风险是否可接受。
2. 再看 `monthly_returns.png`，确认收益是否集中在少数月份。
3. 参数扫描完成后看热力图，优先选择一片稳定区域，而不是孤立最优格子。
4. 生成候选后看 `candidates_compare.png`，对比 Sharpe、收益、回撤和换手。

### 10.1 本地 Notebook 探索

本地研究入口位于 `notebooks/local_research_intro.ipynb`，目录说明见 `notebooks/README.md`。它面向交互式观察：Notebook 开头使用 `%matplotlib inline`，图表直接嵌入 `.ipynb`，默认读取 `reports/equity_curve.csv` 展示净值和回撤。

首次使用前同步 exploration 依赖组。该组在 `pyproject.toml` 的 `[dependency-groups].exploration` 中声明，包含 `jupyter`、`ipykernel` 和 `mplfinance`：

```bash
uv sync --python 3.11 --group exploration
uv run --python 3.11 --group exploration jupyter notebook notebooks/local_research_intro.ipynb
```

净值 / 回撤展示规则：

| 输入情况 | Notebook 行为 |
|---|---|
| `reports/equity_curve.csv` 不存在 | 只提示先运行本地回测并输出净值曲线 CSV；不生成替代数据。 |
| 缺少 `trade_date` | 提示字段缺失，跳过时间序列绘制。 |
| 存在 `nav` | 直接用 `nav` 绘制净值曲线。 |
| 缺少 `nav` 但存在 `total_value` | 用首个有效 `total_value` 归一化得到净值。 |
| 缺少 `drawdown` | 根据净值曲线计算回撤并展示。 |

OHLCV / K 线展示是可选研究单元。只有当用户自备 `data/ohlcv.csv`，且字段包含 `open/high/low/close/volume` 或 `Open/High/Low/Close/Volume`，并存在 `trade_date`、`date` 或 `Date` 日期字段时，Notebook 才导入 `mplfinance` 绘制 K 线。缺文件、缺字段或有效 OHLCV 行为空时，Notebook 会提示并跳过 K 线单元；不要用 `reports/equity_curve.csv` 或净值曲线伪造 K 线。

边界如下：

| 项 | 规则 |
|---|---|
| 正式报告 | 仍使用 `generate_report_charts("reports")` 生成 `reports/charts/*.png` 与 `reports/charts/index.md`。 |
| Notebook 图表 | 默认只 inline 展示，不调用 `savefig`，不写入 `reports/charts/`。 |
| OHLCV / K 线 | 仅当用户自备 `open/high/low/close/volume` 或 `Open/High/Low/Close/Volume` 字段完整的数据时使用 `mplfinance`；缺字段时跳过。 |
| 临时输出 | `.ipynb_checkpoints/`、`notebooks/outputs/` 和 `notebooks/temp/` 不作为交付物。 |

## 11. 偏差审计

当你有 baseline 与 enhanced 两组结果时，可以运行偏差审计：

```bash
uv run --python 3.11 python - <<'PY'
from engine.bias_audit import AuditComparableRun, run_bias_audit, write_bias_audit_report

baseline = [
    AuditComparableRun(
        run_id="base-1",
        params={"strategy_name": "momentum", "lookback": 20},
        metrics={"total_return": 0.10, "max_drawdown": -0.20, "sharpe": 1.0, "turnover": 0.4},
    )
]
enhanced = [
    AuditComparableRun(
        run_id="enh-1",
        params={"strategy_name": "momentum", "lookback": 20},
        metrics={"total_return": 0.12, "max_drawdown": -0.18, "sharpe": 1.1, "turnover": 0.35},
    )
]

result = run_bias_audit(baseline, enhanced)
write_bias_audit_report(result, "reports/bias_audit_report.csv")
print(result.rows)
print(result.warnings)
PY
```

偏差审计适合记录：

- 固定股票池与 PIT 股票池差异。
- 交易状态约束前后差异。
- 涨跌停约束前后差异。
- 事件 `available_at` 纳入前后差异。
- 候选排序变化。

注意：真实 W3 数据源曾在 `2025-02-11..2026-02-18` limited window 内完成验证。CR-012 后，当前 strict readiness 仍需按 `snapshot_asof` PIT、dataset-specific `available_at`、tradability / lifecycle 缺口归因和 blocked claim 重新审计；超出该窗口、切换数据源或扩展事件口径时，也必须重新确认 exact source/interface 并回归全链路。

### 11.1 CR-011 因子研究报告、panel 与稳健性验证

CR-011 的新版实验 17-21 研究链路用于回答“补齐生产级数据和交易约束后，原实验 17-21 的因子结论是否仍然稳健”。它不覆盖旧报告，而是在新目录下输出可追溯结果。

| 输出类别 | 路径 | 用户应检查 |
|---|---|---|
| 新版研究报告 | `reports/experiment_17_21_cr011/**` | 报告 metadata 是否披露 benchmark、PIT、可交易性、复权、暴露、容量成本和 blocked / allowed claims。 |
| factor panel audit | `reports/experiment_17_21_cr011/**` | 是否同时包含 `raw`、`directional`、`winsorized`、`zscore` 四阶段，且 manifest stage 顺序 exact。 |
| robust validation | `reports/experiment_17_21_cr011/**` | 是否同时包含 `rolling`、`annual`、`market_state`、`parameter_grid`、`cost_grid` 五类视图。 |
| 旧 baseline | `reports/experiment_17_21/factor_strategy_report.md` | 只能阅读为旧 fixed-snapshot / proxy benchmark 基线；不得写入或覆盖。 |

报告解读顺序建议：

1. 先看 benchmark policy 与 PIT universe metadata，确认是否仍有 `required_missing`、`unavailable` 或 blocked claim。
2. 再看 factor panel 四阶段，确认因子方向、截尾、标准化和 row count 是否完整。
3. 然后看 robust validation 五类视图，优先关注年度、滚动窗口和市场状态分段是否一致。
4. 最后看容量、成本和参数网格敏感性，避免只依据单一成本假设或单个参数组合下结论。

默认安全边界：不真实联网、不写真实 lake、不读取或打印凭据、不读取 / 列出 / 迁移 / 复制 / 删除旧 `data/**`，不覆盖旧 `reports/experiment_17_21/factor_strategy_report.md`。需要真实数据补齐时，先回到 4.4 的 dry-run / 外置 lake runbook，并由用户显式授权。

## 12. RSI/MACD 策略扩展

策略统一入口为 `strategies.base.run_strategy`：

```bash
uv run --python 3.11 python - <<'PY'
from engine.data_loader import LoaderConfig, load_backtest_data
from strategies.base import StrategyInput, run_strategy

loaded = load_backtest_data(
    LoaderConfig(
        data_dir="data",
        quality_report_path="reports/data_quality_report.csv",
        start_date="2019-01-01",
        end_date="2025-12-31",
    )
)

signal_date = loaded.close_df.index[-1]
rsi = run_strategy("rsi", StrategyInput(loaded.close_df, signal_date, {"period": 14, "top_fraction": 0.10}))
macd = run_strategy("macd", StrategyInput(loaded.close_df, signal_date, {"fast": 12, "slow": 26, "signal": 9, "top_fraction": 0.10}))

print(rsi.target_symbols)
print(macd.target_symbols)
PY
```

扩展新策略时应保持：

- 策略函数只接收 `StrategyInput` 并返回 `StrategyResult`。
- 不读写文件。
- 不依赖回测全局状态。
- 排名 tie-breaker 稳定。
- 非法参数应抛出清晰错误。

## 13. W3 真实性增强启用指南

当前 W3 增强模块存在；JQData limited window 曾完成 PIT / W3 source/interface 验证，CR-012 后仅作为历史证据和对照来源：

| 能力 | 模块 | 当前状态 |
|---|---|---|
| PIT 股票池 | `engine.universe` | `jqdata.index_members.snapshot` 曾用于 `2025-02-11..2026-02-18` limited window；当前 strict 声明需按 `snapshot_asof` 重新审计。 |
| 交易状态 | `engine.trade_status` | `jqdata.trade_status.daily` 曾发布，当前 strict 声明需与 as-of PIT denominator 和缺口归因一起复验。 |
| 涨跌停约束 | `engine.trading_constraints` | `jqdata.prices_limit.daily` 曾发布，换窗口或换源时需重新确认 source/interface。 |
| 事件 available_at | `engine.events` | `jqdata.events.disclosure` 当前覆盖 ST 状态变更事件；空事件表在 source/interface 与 `available_at_rule` 冻结时允许通过。 |

启用前必须完成：

1. 确认 `market_data/source_registry.py` 中 exact `source` / `interface` 与目标窗口匹配。
2. 扩展或复核数据准备请求、raw cache、manifest 字段和标准化映射。
3. 扩展质量报告检查。
4. 对 `data_prep`、`normalizer`、`quality`、`data_loader`、组合约束和偏差审计执行回归。
5. 在报告中保留新增约束对收益、回撤、换手和候选排序的影响说明。

不要把当前 fail-fast 防线误解为真实 PIT / 交易状态 / 涨跌停 / 事件数据已接入。

## 14. 日志诊断

STORY-004..013 相关入口会输出结构化诊断日志。最小字段：

| 字段 | 说明 |
|---|---|
| `event_name` | `start`、`end`、`structured_error` 或降级事件名。 |
| `run_id` | 单次诊断运行 ID。 |
| `module` | 模块名，如 `data_loader`、`backtest`、`scanner`。 |
| `story_id` | 对应 Story ID。 |
| `status` | 当前状态，如 `success`、`degraded`、`unfilled`、`single_group_failed`。 |
| `params_summary` | 参数摘要，不应包含敏感凭据。 |
| `elapsed_seconds` | 从 start 到当前事件的耗时。 |
| `structured_error` | 错误路径中的结构化错误对象。 |

示例查看方式：

```bash
uv run --python 3.11 python - <<'PY'
import logging
from engine.diagnostics import LOGGER_NAME

logging.basicConfig(level=logging.INFO)
logging.getLogger(LOGGER_NAME).setLevel(logging.INFO)
print("诊断日志会在相关模块运行时以 JSON 行输出。")
PY
```

## 15. 数据质量与坑点说明

| 坑点 | 风险 | 当前处理 |
|---|---|---|
| 复权口径混用 | 动量排名和收益不可比 | 默认 `qfq`；loader 检测到混用会失败。 |
| 停牌 / 无成交 | 假设成交会高估收益 | 缺失成交价或不可交易目标不静默填充；交易状态真实启用前仍需披露限制。 |
| 涨跌停 | 涨停买入/跌停卖出不一定成交 | `jqdata.prices_limit.daily` 曾在 limited window 发布；CR-012 后当前 strict 声明需重新确认 source/interface 和 coverage。 |
| 新股 / 退市 / ST | 样本选择和可交易性偏差 | 第一版不完整建模，需在报告 metadata 中披露。 |
| 财报披露日 | 使用报告期日期会产生未来函数 | 事件数据必须使用真实 `available_at`。 |
| 指数成分历史 | 固定当前股票池导致幸存者偏差 | 固定池标记 `is_pit_universe=false`；PIT 真实启用前为 ADVISORY。 |
| `available_at` 缺失 | 决策时点不可审计 | 日线价格可用默认收盘后推导；事件类字段必须显式提供。 |
| 数据源迟到修正 | 最近数据可能被后续修订 | 默认最近 5 个交易日回补，质量报告披露新鲜度。 |
| 参数扫描过拟合 | 样本内最优不代表样本外稳定 | 候选报告仅用于少量人工平台验证。 |
| CSV 公式注入 | 表格软件可能执行自由文本 | 自由文本字段以 `'` 转义危险前缀。 |

## 16. 输出文件字段说明

### `reports/data_quality_report.csv`（legacy quality report）

该路径是 `legacy old report`，用于解释旧 flat/report 链路字段；它不是 CR-007 的 current quality truth，也不能作为 coverage proof。当前 quality truth 必须来自 configured lake root 下的 lake `quality/catalog`，并带有 `dataset`、`start/end`、`denominator`、`run_id/source/interface`、`quality_status`、`catalog/lineage`。缺少这些 lake quality/catalog current truth 字段时，必须返回结构化缺口或先执行 dry-run，不得用旧报告补证。

关键字段：

| 字段 | 说明 |
|---|---|
| `dataset` | `prices`、`index_members`、`trade_calendar` 或 `overall`。 |
| `coverage_start` / `coverage_end` | 实际数据覆盖范围。 |
| `requested_start` / `requested_end` | 本次质量检查请求范围。 |
| `missing_rate` | 请求区间内缺失比例。 |
| `failed_batch_count` | manifest 中失败批次数量。 |
| `failed_symbol_dates` | 失败 symbol/date 或请求项。 |
| `missing_required_fields` | 缺失必需字段。 |
| `duplicate_record_count` | 重复记录数量。 |
| `abnormal_price_count` | 异常价格数量，如 `close<=0`。 |
| `data_freshness_trade_days` | 按交易日计算的新鲜度缺口。 |
| `quality_status` | `pass`、`warn` 或 `fail`。 |
| `available_at_rule` | 可用时点规则。 |
| `adjustment_policy` | 复权口径。 |
| `is_pit_universe` | 是否 PIT 股票池。 |

### `reports/momentum_param_sweep_local.csv`

关键字段：

| 字段 | 说明 |
|---|---|
| `run_id` | 扫描组 ID。 |
| `strategy_name` | 策略名，默认 `momentum`。 |
| `lookback` | 动量窗口。 |
| `rebalance_freq` | 调仓频率，单位为交易日。 |
| `fraction` | 选择前多少比例的股票。 |
| `status` | `success` 或 `failed`。 |
| `error_message` | 失败原因；成功为空。 |
| `cumulative_return` / `annual_return` / `max_drawdown` / `sharpe` / `turnover` | 核心指标。 |
| `quality_status` | 数据质量摘要。 |
| `elapsed_seconds` | 单组耗时。 |
| `adjustment_policy` / `available_at_rule` / `is_pit_universe` | 数据和偏差 metadata。 |

### `reports/momentum_candidates_local.csv`

关键字段：

| 字段 | 说明 |
|---|---|
| `candidate_id` | 候选编号。 |
| `candidate_type` | 候选类型，如 `best_sharpe`、`best_return`、`conservative_low_turnover`。 |
| `selection_reason` | 选择理由。 |
| `lookback` / `rebalance_freq` / `fraction` | 待回填平台的参数。 |
| `local_*` | 本地指标。 |
| `joinquant_*` | 人工聚宽验证结果填写位。 |
| `difference_note` | 差异解释。 |
| `quality_status` | 数据质量摘要。 |
| `limitations_metadata` | 限制项说明。 |

### `reports/experiment_17_21_cr011/**`

该目录是 CR-011 新版实验 17-21 报告、factor panel audit 和 robust validation 的隔离输出根。它与旧 `reports/experiment_17_21/factor_strategy_report.md` 分开，避免把旧 fixed-snapshot / proxy benchmark baseline 覆盖为生产级结论。

关键字段或视图：

| 字段 / 视图 | 说明 |
|---|---|
| `benchmark_policy` | 真实 benchmark 与 proxy benchmark 的消费口径；不得把 `proxy_baseline` 填充为真实 `hs300_index`。 |
| `universe_mode` / `pit_status` | PIT / fixed universe、股票 lifecycle 和 as-of gate 状态。 |
| `tradability_status` | 停牌、ST、无成交、上市天数、涨跌停和事件状态门控。 |
| `execution_price_policy` | open/high/low/close/VWAP 或 close proxy 降级合同，必须是 exact policy。 |
| `adjustment_policy` / `corporate_action_audit` | 复权链路和公司行动 available_at 审计状态。 |
| `exposure_status` | 行业、市值、风格暴露和中性化输入状态。 |
| `liquidity_capacity_cost` | 流动性、容量、冲击成本和成本敏感性摘要。 |
| `panel_stage` | 仅允许 `raw`、`directional`、`winsorized`、`zscore` 四阶段。 |
| `validation_view` | 仅允许 `rolling`、`annual`、`market_state`、`parameter_grid`、`cost_grid` 五类。 |
| `network_calls` / `lake_writes` / `credential_reads` / `legacy_data_operations` / `old_report_overwrites` | 默认必须为 `0`，用于证明未授权路径没有真实联网、写湖、读凭据、操作旧数据或覆盖旧报告。 |

## 17. 常见故障排查

| 问题现象 | 可能原因 | 解决方法 |
|---|---|---|
| `配置包含未知键` 或 `配置缺少键` | `config/data_prep.yaml` 与 `DATA_PREP_CONFIG_KEYS` 不一致 | 按默认配置补齐或删除未知键。 |
| `source/interface 未解析` | 请求的窗口或数据集没有已注册 exact source/interface，或未走已验证的 JQData limited window 注册项 | 确认 `market_data/source_registry.py`、账号权限窗口和 `available_at` 规则，再回归 acquire、normalize、validate、publish、read、revalidate、replay。 |
| `安装路径被非目录占用` | raw、manifest 或报告父路径被普通文件占用 | 删除或改名冲突文件，确保父路径是目录。 |
| `raw 解析失败` | raw JSONL 损坏，或第一行不是 `batch_metadata` | 回看对应 raw 文件和 manifest 的 `batch_id`；必要时重跑该批次。 |
| `标准化映射失败` | AKShare 返回字段变化，或 target dataset 与字段不匹配 | 检查 raw 字段名和 `FIELD_ALIASES`，必要时扩展映射并回归。 |
| `当前质量证明缺失` | configured lake root 下的 `quality/catalog` 缺少 dataset、start/end、denominator、run_id/source/interface、quality_status 或 catalog/lineage | 先执行 dry-run，确认外置 lake root、dataset、interface、date range 和 run_id；不得用 legacy old report 或旧 `data/**` 补证。 |
| CR-011 新报告写入旧实验目录 | 输出根误指向 `reports/experiment_17_21` 或旧 `factor_strategy_report.md` | 改为 `reports/experiment_17_21_cr011/**`；旧报告只读为 baseline，不覆盖。 |
| CR-011 factor panel audit 失败 | 缺少 `raw`、`directional`、`winsorized`、`zscore` 任一阶段，或 manifest stage 顺序不 exact | 补齐四阶段后重新验证；缺阶段时不得声明 `factor_panel_audited`。 |
| CR-011 robust validation 失败 | 缺少 `rolling`、`annual`、`market_state`、`parameter_grid`、`cost_grid` 任一视图，或成本 / 市场状态输入不足 | 补齐五类视图和输入；blocked claims 未解除前不得生成同名 allowed claim。 |
| `legacy 质量报告未通过: status=fail` | 旧 flat/report 链路覆盖缺口、schema 缺失、重复记录、异常价格或缺失率过高 | 可查看 `data_quality_report.csv/.md` 作为 legacy quality report 线索，但它的 coverage proof forbidden，不能替代 lake `quality/catalog`。 |
| `validate PASS 后 reader 仍读不到新数据` | validate / parity 只生成 candidate 或 evidence，没有经过 Explicit Publish Gate | 检查 catalog current pointer；没有明确 publish intent / approval 时这是预期结果，不要把 candidate 提升为 current truth。 |
| `S09 真实抓取被阻断` | 缺 S09 LLD approved、S09 CP5 approved、per-run `authorization_id` 或 dataset/date/source/lake/window/rollback policy | 先完成 S09 Batch-B 门控；Batch-A verified 不能作为真实抓取、写湖、读凭据或 publish 授权。 |
| DuckDB 相关路径不可用 | 当前 CR014 Batch-A 不引入 DuckDB 依赖，也不写 `.duckdb` | 使用 pandas/pyarrow fallback 或数据湖侧只读 audit evidence；不得把 DuckDB view / SQL result 当 source of truth。 |
| `复权口径不匹配` | parquet 中 `adjustment_policy` 混用或与 loader 配置不一致 | 统一为 `qfq` 或显式调整 loader 配置，并重新生成质量报告。 |
| `调仓 schedule 为空` | 历史窗口太长、回测区间太短或交易日历不足 | 缩短 `lookback_days`，扩大日期范围，或检查交易日历。 |
| 候选报告为空 | 扫描报告为空或没有成功行 | 先修复扫描失败原因，再运行候选选择。 |
| Notebook 启动时报缺少 `jupyter`、`ipykernel` 或 `mplfinance` | 尚未同步 exploration 依赖组 | 运行 `uv sync --python 3.11 --group exploration`，再用 `uv run --python 3.11 --group exploration jupyter notebook notebooks/local_research_intro.ipynb` 启动。 |
| Notebook 跳过 K 线图 | `data/ohlcv.csv` 不存在，或缺少日期 / OHLCV 必需字段 | 使用自备 OHLCV CSV，并提供 `trade_date`、`date` 或 `Date`，以及完整的 `open/high/low/close/volume` 或 `Open/High/Low/Close/Volume` 字段。 |
| 聚宽结果差异较大 | 本地未完整建模平台撮合、停牌、涨跌停、ST、退市、财报披露日或 PIT 成分 | 只做方向一致性分析；必要时逐项启用真实性增强并做偏差审计。 |
| 文档里看到历史 FAIL | 验证报告保留审计上下文 | 以最近的 PASS / `CLOSED / REGRESSION_PASS` 结论为当前状态。 |

## 18. 验证状态与限制

当前用户文档基于以下事实：

- `STORY-001` 至 `STORY-013` 均为 `verified`。
- CR-011 `S01` 至 `S08` 均为 `verified / CP7 PASS`；文档刷新已完成，CP8 人工终验已 approved，CR-011 已关闭。
- CR-012 limited-window readiness audit 口径修正已完成代码、测试和文档增量；CR-013 已完成 `S01` 至 `S04` 的 CP7 验证与文档收敛，当前等待 meta-po 创建 CP8 终验。
- CR-014 Batch-A `S01` 至 `S08` 均为 `verified / CP7 PASS`；交付范围是离线合同、静态护栏和研究消费边界，不代表真实全 A 数据已经抓取、写湖、publish 或可声明 production current truth。
- CR-014 S09 仍为后续 Batch-B planned Story；必须等 S09 LLD approved、S09 CP5 approved 和每次真实 run 的 `authorization_id` 及 dataset/date/source/lake/window/rollback policy 后才能执行。
- CR-011 新版研究报告、factor panel 与 robust validation 输出路径为 `reports/experiment_17_21_cr011/**`；旧 `reports/experiment_17_21/factor_strategy_report.md` 仅作 baseline 引用，不得覆盖。
- 历史 STORY-003 FAIL 已由 `BUG-STORY-003-001` 回归 PASS 覆盖。
- 2026-05-15 独立验收中发现的 F-004 日志 REQUIRED 缺口已于 2026-05-16 回归关闭。
- 当前过程文档已完成 CR-011 收尾；README、本手册与 TEST-STRATEGY 已完成 CR-011 文档刷新，CP8 已通过并关闭 CR-011。
- 当前 README、本手册、CR-013 full-history roadmap、TEST-STRATEGY 和 CR-013 报告摘要对 limited-window supported、2020-2024 blocked、真实 VWAP / minute / tick / level2 / order-match blocked、unsupported register excluded denominator 和五类 forbidden counters 的声明已收敛一致。
- 当前 README、本手册和 full-history roadmap 已补充 CR-014 Batch-A / S09 Batch-B 边界：Parquet/catalog 为事实源，DuckDB 只读且不写 `.duckdb`，validate/parity PASS 不自动 publish，研究消费层只读 published truth / clean reader output / structured claim metadata。
- CR-001 目录结构收敛已完成：历史基线曾以 `local_backtest/` 作为仓库根，`work/studies/quant-trading/local_backtest/` 与 `delivery/` 清理前均无文件，已用 `rmdir` 删除空目录树。CR060 后，future-facing canonical 项目名为 `quant-lab`，`local_backtest` 仅作为 legacy alias / 历史审计名保留。
- 当前 production 项目不生成 `delivery/**`、安装脚本、真实生产数据或报告样本；正式用户文档出口为 `README.md` + `docs/USER-MANUAL.md`。

仍需注意的非阻塞事项：

| 项 | 状态 | 说明 |
|---|---|---|
| W3 / PIT 完整历史数据源 | ADVISORY | `2025-02-11..2026-02-18` limited window 曾完成真实 PIT / 交易状态 / 涨跌停 / 事件数据链路；CR-012 后必须按 `snapshot_asof` PIT、dataset-specific `available_at`、tradability / lifecycle 缺口归因和 blocked claim 重新审计，才能声明当前 `production_strict_research`。完整历史和持续生产 current truth 仍需账号权限或数据采购确认。 |
| CR-014 S09 真实执行 | BLOCKED UNTIL AUTHORIZED | Batch-A 不授权真实 provider fetch、raw / manifest / run metadata 写湖、credential read、current pointer publish 或 S09 real execution；S09 必须另走 LLD、CP5 和 per-run 授权。 |
| DuckDB 查询层 | ADVISORY | 当前只冻结只读候选边界；不引入 DuckDB 依赖、不打开或写入 `.duckdb`、不把 DuckDB 作为 source of truth。 |
| CR-011 CP8 人工终验 | PASS | 用户已 approve `checkpoints/CP8-CR011-DELIVERY-READINESS.md`，CR-011 已关闭。 |
| CR-013 CP8 终验 | PENDING | CR013-S01..S04 已 CP7 PASS；文档收敛复核无 BLOCKING / REQUIRED 缺口，等待 meta-po 创建 CP8 自动预检与人工终验稿。 |
| Guardrail 脚本 | 流程债 | `scripts/check_delivery_guardrails.py` 缺失，不能执行项目规则中的该检查。 |
| `VALIDATION-ENV.yaml` | ADVISORY | 历史 story_id 元数据滞后，但当前验证范围以 STATE、STORY-STATUS 和验证报告为准。 |
| git 审计 | ADVISORY | 过程记录中曾有“当前目录不是 git repository”的审计限制；本次文档生成环境可执行 git 命令，但大量文件未跟踪。正式交付前仍建议在目标 git worktree 中复核。 |
| 真实生产数据 | 不包含 | 文档、测试和示例不生成或引用真实生产行情样本。 |
| 目录边界 | 已收敛 | `work/` 与 `delivery/` 已作为空旧骨架清理；`llm-wiki` 保持外部知识库，不复制到本项目。 |

## 19. 参考过程证据

- [验证报告](../process/VERIFICATION-REPORT.md)
- [测试策略](../process/TEST-STRATEGY.md)
- [Story 状态](../process/STORY-STATUS.md)
- [HLD](../process/HLD.md)
- [架构决策](../process/ARCHITECTURE-DECISION.md)
- [F-004 回归 handoff](../process/handoffs/META-QA-REGRESSION-F004-LOGGING-2026-05-16.md)
- [CR-001 目录结构收敛](../process/changes/CR-001-DIRECTORY-STRUCTURE-CONVERGENCE-2026-05-16.md)
- [CR-001 meta-dev 清理 handoff](../process/handoffs/META-DEV-DIRECTORY-CONVERGENCE-CR-001-2026-05-16.md)
- [CR-001 meta-doc 文档刷新 handoff](../process/handoffs/META-DOC-DIRECTORY-DOCS-CR-001-2026-05-16.md)
- [CR-011 变更单](../process/changes/CR-011-FACTOR-RESEARCH-DATA-COMPLETION-2026-05-23.md)
- [CR-011 S08 CP7](../process/checks/CP7-CR011-S08-factor-panel-audit-and-robust-validation-VERIFICATION-DONE.md)
- [CR-013 变更单](../process/changes/CR-013-UNSUPPORTED-DATA-CLAIM-BOUNDARY-2026-05-24.md)
- [CR-013 CP7 汇总](../process/checks/CP7-CR013-BATCH-A-VERIFICATION-SUMMARY.md)
