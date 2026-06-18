# DEV-LOG

## 2026-06-11 - CR045 Bridge Batch A 实现 / CP6 完成

- Story 范围：`CR045-S01`..`CR045-S06`；执行 `process/handoffs/META-DEV-CR045-CP6-IMPLEMENT-2026-06-11.md`，消费 CP5 approved 批次 `process/checkpoints/CP5-CR045-BRIDGE-BATCH-A-LLD-BATCH.md`。
- 调度证据：handoff `dispatch.mode=spawn_agent`，agent_name=`dev-zhu`，agent_id/thread_id=`019eb748-a3bf-75d3-b37c-ce4ba4924235`，tool_name=`multi_agent_v1.spawn_agent`，spawned_at=`2026-06-11T23:16:11+08:00`。
- 实现文件清单：`engine/goldminer_bridge_contract.py`、`engine/goldminer_bridge_client.py`、`engine/goldminer_bridge_probe.py`、`tests/test_cr045_goldminer_bridge_contract.py`、`tests/test_cr045_goldminer_bridge_client.py`、`tests/test_cr045_goldminer_readonly_probe.py`、`tests/test_cr045_goldminer_no_operation_static.py`、`docs/goldminer/CR045-BRIDGE-RUNBOOK.md`。
- 过程文件清单：`process/stories/CR045-BRIDGE-BATCH-A-IMPLEMENTATION.md`、`process/checks/CP6-CR045-BRIDGE-BATCH-A-CODING-DONE.md`、6 个 CR045 Story 卡片状态、`DEV-LOG.md`。
- 实现摘要：新增 Goldminer Windows Bridge L2 skeleton 合同、WSL/Linux fixture client、readonly probe blocked-first skeleton、redaction/no-operation static tests 和用户 runbook；所有真实能力 flags 保持 false，readonly probe 在 L4 未授权时 blocked-first，operation counters 全 0。
- 关键决策与偏差：S06 保持 technical-note 范围，仅生成 runbook，不新增自动 manifest/schema/guard script；没有修改 HLD、ADR、Feature 设计、`pyproject.toml` 或 `uv.lock`。
- 验证命令：`PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr045_goldminer_bridge_contract.py tests/test_cr045_goldminer_bridge_client.py tests/test_cr045_goldminer_readonly_probe.py tests/test_cr045_goldminer_no_operation_static.py`，结果 `24 passed in 0.10s`。首次运行发现 `trade_password` 分类优先级问题，已修复后复跑通过。
- 验证命令：`git diff --check`，结果 PASS，无输出。
- 安全边界：未读取 `.env` / `.env.*`、token、account_id、账号、密码、session、cookie 或 private key；未启动 Windows bridge runtime；未导入或调用真实 `gm` / `gmtrade`；未登录/连接 Goldminer 或 broker；未查询 account/cash/position/order/fill；未下单、撤单、simulation/live、provider fetch、lake write 或 catalog publish。
- 状态回写：CR045-S01..S06 已推进到 `ready-for-verification`；CP6 结论 `PASS`，路径为 `process/checks/CP6-CR045-BRIDGE-BATCH-A-CODING-DONE.md`。
- meta-qa 验证入口：复跑目标 pytest 和 `git diff --check`；重点复核 no SDK/no network/no credential read、false flags、readonly blocked-first、zero counters、runbook 不构成运行授权。
- BLOCKING：无。等待 meta-po 拉起 meta-qa 执行 CP7；CP7 前不得标记 verified 或授权真实 L3/L4/L5 运行。

## 2026-06-05 - CR020-S03 实现 / CP6 完成

- Story 范围：`CR020-S03-linux-client-rest-transport`；执行用户直接指派的 meta-dev 实现子任务 B，消费已确认 LLD `process/stories/CR020-S03-linux-client-rest-transport-LLD.md` 与 CP5 approved 批次 `checkpoints/CP5-CR020-QMT-GATEWAY-READONLY-LLD-BATCH.md`。
- 调度证据：LLD 原始子 agent 为 `dev-zhu`，agent_id/thread_id=`019e94f2-7ff0-7293-b9f2-408dba709a5e`；本次实现为当前 Codex 线程按用户直接指令执行，CP6 记录 `dispatch_mode=direct-user-handoff-execution`。
- 实现文件清单：`trading/qmt_client.py`、`trading/qmt_client_cli.py`、`tests/test_cr020_linux_client_rest_transport.py`；过程文件清单：`process/checks/CP6-CR020-S03-linux-client-rest-transport-CODING-DONE.md`、`process/stories/CR020-S03-linux-client-rest-transport.md`、`DEV-LOG.md`。
- 实现摘要：`QmtClient` 增加 `QmtClientConfig`、`QmtRetryPolicy`、`QmtRestRequest`、`QmtTransportResult`、`QmtRestTransport` protocol 和 `QmtAuthHeaderProvider` protocol；默认无 `base_url` 或无 transport 时 fail-closed；`query_positions` 进入 CR020 typed REST client path，仍只在 fake/injected transport 下测试。
- CLI 摘要：新增 `trading/qmt_client_cli.py`，提供 command matrix 与 optional Typer app；Typer 缺失时输出 `typer_dependency_missing` blocked result；CLI 命令只调用 `QmtClient.health/capabilities/diagnostics/query_positions`，不复制 endpoint gate、auth、timeout、retry 或业务判定。
- 关键决策与偏差：未修改 `trading/qmt_transport.py`、`trading/qmt_gateway_contracts.py`、`trading/qmt_cli.py`；S03 所需新增错误理由采用 client 内 string reason normalization，未扩大 shared enum；`STATE.md` 未在本线程修改，避免与并行主线程调度状态写入冲突。
- 已知限制：本 Story 不提供真实 HTTP transport，不启动 gateway，不连接 QMT；S04 负责 HMAC / allowlist / scope provider，S05 负责 gateway route 和真实 `query_positions` redacted schema，S06 负责手动安装调试手册与 CP7 实机边界。
- 验证命令：`PYTHONPYCACHEPREFIX=/tmp/cr020-s03-pytest-pycache PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr020_linux_client_rest_transport.py`，结果 `9 passed in 0.08s`。
- 回归命令：`PYTHONPYCACHEPREFIX=/tmp/cr020-s03-regression-pycache PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr019_qmt_cside_client_cli.py tests/test_cr020_linux_client_rest_transport.py`，结果 `16 passed in 0.13s`。
- 编译命令：`PYTHONPYCACHEPREFIX=/tmp/cr020-s03-pycompile PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile trading/qmt_client.py trading/qmt_client_cli.py tests/test_cr020_linux_client_rest_transport.py`，退出码 0。
- 安全边界：未修改 `pyproject.toml` / `uv.lock`；未读取 `.env` / `.env.*`、账号、密码、token、session、交易密码、私钥；未启动 gateway、未绑定端口、未打开真实 socket、未连接 QMT / MiniQMT / XtQuant；未发单、撤单、账户写入、broker lake、provider、lake 或 publish。
- 状态回写：Story 已推进到 `ready-for-verification`；CP6 结论 `PASS`，路径为 `process/checks/CP6-CR020-S03-linux-client-rest-transport-CODING-DONE.md`。
- meta-qa 验证入口：复跑 S03 专项、CR019+CR020 组合回归和 py_compile；重点复核 fake transport/auth provider、Typer missing fail-closed、no-env-read、forbidden import、no socket/gateway/QMT、timeout/retry、redaction、account-like endpoint blocked。
- BLOCKING：无。等待 meta-po 拉起 meta-qa 执行 CP7；CP7 前不得标记 verified 或授权真实 Windows/QMT 运行。

## 2026-05-28 - CR017-S04 实现 / CP6 完成

- Story 范围：`CR017-S04-reader-api-and-policy-gates`；执行 `process/handoffs/META-DEV-CR017-S04-IMPLEMENT-2026-05-28.md`，消费 S03 CP7 PASS / verified 结果和 CP5 全量 LLD approved 门禁。
- 调度证据：handoff `dispatch.mode=spawn_agent`，agent_name=`dev-yang`，agent_id/thread_id=`019e6bd3-3af1-7d23-b48a-1b7a70d06ab2`，tool_name=`multi_agent_v1.spawn_agent`，spawned_at=`2026-05-28T07:44:29+08:00`；handoff completed_at 等待 meta-po 回填，本 CP6 checked_at=`2026-05-28T07:54:04+08:00`。
- 实现文件清单：`market_data/adjustment_readers.py`、`market_data/readers.py`、`engine/research_dataset.py`、`tests/test_cr017_reader_policy_gates.py`、`process/checks/CP6-CR017-S04-reader-api-and-policy-gates-CODING-DONE.md`、`process/stories/CR017-S04-reader-api-and-policy-gates.md`。
- 实现摘要：新增显式 `research_adjustment_policy` reader API、`single_policy_gate()`、未发布 candidate 阻断和 QMT metadata handoff；reader metadata 固定包含 `policy`、`view_id`、`source_run_id`、`quality_status`、`single_policy_gate_status`，并保留 `research_adjustment_policy`。
- `market_data/readers.py` 对 S04 API 做导出接入，不改变既有 `read_dataset` current pointer 读取语义；`engine/research_dataset.py` 支持从 `research_adjustment_policy` column / attrs / metadata / catalog coverage 抽取口径，并把 `single_policy_gate_status` 合并进研究数据集 metadata。
- 关键决策与偏差：QMT handoff 只输出 metadata 和 `execution_price_policy=raw`，不包含 adjusted execution price 值；`adjusted_execution_price_pass_count=0` 固化为验收计数。未实现 CR017-S05/S06、CR015 或 CR016。
- 已知限制：本 Story 只交付离线 reader/gate/handoff 合同；生产 reader 默认入口切换、用户迁移说明和完整质量 parity / leakage 验证由后续 S05/S06 收敛。
- 验证命令：`uv run --python 3.11 pytest -q tests/test_cr017_reader_policy_gates.py`，结果 `5 passed in 0.34s`。
- 回归命令：`uv run --python 3.11 pytest -q tests/test_cr017_reader_policy_gates.py tests/test_cr017_qfq_hfq_derivation.py tests/test_cr017_adjustment_policy_contract.py tests/test_cr017_raw_adj_factor_contract.py tests/test_market_data_contracts.py`，结果 `34 passed in 0.45s`。
- 安全边界：provider_fetch=0、lake_write=0、credential_read=0、current_pointer_publish=0、dependency_change=0、legacy_qfq_overwrite=0、qmt_api_call=0、real_order=0；未读取 `.env`、token、password、private key、cookie 或 session；未修改 `pyproject.toml`、`uv.lock`、`data/**`、`reports/**` 或 `delivery/**`。
- 状态回写：Story 已推进到 `ready-for-verification`；CP6 结论 `PASS`，路径为 `process/checks/CP6-CR017-S04-reader-api-and-policy-gates-CODING-DONE.md`。
- meta-qa 验证入口：复跑 S04 指定测试和 CR017 合同回归；重点复核未指定 policy blocked、混用 policy blocked、metadata 必填字段、未发布 candidate blocked、QMT raw-only handoff 和八项安全计数全为 0。
- BLOCKING：无。等待 meta-po 拉起 meta-qa 执行 CP7。

## 2026-05-27 - CR014-S03 实现 / CP6 完成

- Story 范围：`CR014-S03-p0-plan-run-normalize-validate-publish-contract`；执行用户本轮明确授权的 BATCH-A 受控离线实现，消费 S01/S02 CP7 PASS 合同，不修改 S01/S02 共享文件。
- 调度证据：按用户要求在 CP6 中记录 `dispatch_mode=spawn_agent`、role=`meta-dev`、agent_name=`dev-kong`、agent_id/thread_id=`019e66ba-bf09-7c31-98e9-86a4fdab70ec`、tool_name=`multi_agent_v1.spawn_agent`、handoff=`process/handoffs/META-DEV-CR014-S03-IMPLEMENTATION-2026-05-27.md`。
- 实现文件清单：`market_data/runtime.py`、`market_data/normalization.py`、`market_data/validation.py`、`market_data/cli.py`、`tests/test_cr014_p0_pipeline_contract.py`、`process/checks/CP6-CR014-S03-p0-plan-run-normalize-validate-publish-contract-CODING-DONE.md`。
- 实现摘要：新增 P0 dataset `plan -> run -> normalize/replay -> validate -> publish -> read/query` 合同；`plan` 只 dry-run；`run` 在 CP5/LLD/依赖/文件冲突/authorization/source-interface allowlist 未全部满足时 fail-closed 且 connector call count 为 0；normalize/replay 只产出未发布 candidate；validate PASS 不 publish；publish 委托 S02 explicit gate；read/query 只接受 published pointer 或受控 candidate audit evidence。
- 关键决策与偏差：未修改 `market_data/contracts.py`、`market_data/manifest.py`、`market_data/catalog.py`、`market_data/publish.py`；S03 通过 primary 文件适配 S01/S02 合同。现有 legacy `normalize/validate/publish/read` CLI 保持兼容，S03 新增隔离的 `p0-*` 命令，不改变既有真实 publish CLI 行为。
- 已知限制：S03 是合同实现，不执行真实 provider fetch、raw/manifest 写湖、catalog current pointer 发布或 S09 真实执行；授权满足后的真实 run 仍由后续 S09 / BATCH-B 处理。
- 验证命令：`UV_CACHE_DIR=/tmp/uv-cache-local-backtest UV_PROJECT_ENVIRONMENT=/tmp/cr014-s03-venv PYTHONPYCACHEPREFIX=/tmp/cr014-s03-pycompile PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile market_data/cli.py market_data/runtime.py market_data/normalization.py market_data/validation.py tests/test_cr014_p0_pipeline_contract.py`，退出码 0。
- 验证命令：`UV_CACHE_DIR=/tmp/uv-cache-local-backtest UV_PROJECT_ENVIRONMENT=/tmp/cr014-s03-venv PYTHONPYCACHEPREFIX=/tmp/cr014-s03-pycache PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr014_p0_pipeline_contract.py`，结果 `10 passed in 1.01s`。
- 验证命令：`UV_CACHE_DIR=/tmp/uv-cache-local-backtest UV_PROJECT_ENVIRONMENT=/tmp/cr014-s03-venv PYTHONPYCACHEPREFIX=/tmp/cr014-s03-pycache PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr014_universe_lifecycle_contract.py tests/test_cr014_catalog_publish_gate.py tests/test_cr014_p0_pipeline_contract.py`，结果 `25 passed in 1.04s`。
- 验证命令：`UV_CACHE_DIR=/tmp/uv-cache-local-backtest UV_PROJECT_ENVIRONMENT=/tmp/cr014-s03-venv PYTHONPYCACHEPREFIX=/tmp/cr014-s03-pycache PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_market_data_contracts.py tests/test_market_data_normalization_validation_readers.py tests/test_cr010_data_lake_publish_and_contracts.py tests/test_cr014_p0_pipeline_contract.py`，结果 `39 passed in 1.41s`。
- CLI smoke：`python -m market_data.cli p0-run ...` 返回结构化 `dev_gate_unsatisfied` / `authorization_required` / `source_interface_unresolved` / `run_not_allowed`，`connector_call_count=0`，所有 permission counters 为 0。
- 安全边界：未联网、未真实 provider fetch、未写真实 lake、未读取凭据、未触碰 `.env`、未操作旧 `data/**`、未覆盖旧 `reports/**`、未引入或写入 DuckDB、未发布 catalog current pointer、未执行 S09。`uv` 首次在仓库根生成的 `.venv` 已删除，后续验证使用 `/tmp` 环境。
- 状态回写：用户本轮明确禁止修改 Story、STATE、STORY-STATUS 和 handoff，因此未推进这些文件；CP6 已记录该偏差，等待 meta-po 收敛到 `ready-for-verification` 并分派 CP7。
- meta-qa 验证入口：复跑 S03 定向测试、S01/S02/S03 合同回归、market_data 相关回归和 CLI smoke；重点复核未授权 run connector call count、candidate 不发布、validate 不 publish、publish 未授权 pointer changes=0、read/query 不扫未发布 lake。
- BLOCKING：无阻断 CP7 的实现问题；流程状态回写由 meta-po 后续处理。

## 2026-05-22 - CR007-S04 实现 / CP6 完成

- Story 范围：`CR007-S04-experiment-real-benchmark-consumption`；执行 `process/handoffs/META-DEV-CR007-S04-IMPLEMENT-2026-05-22.md`，未启动 CR007-S05。
- 调度证据：主线程真实 `spawn_agent` 调度 meta-dev/dev-kong the 2nd，agent_id/thread_id=`019e4c55-7298-7420-aebd-29b3cee9ad3a`；handoff 已回填 `status=completed`，未使用 inline fallback。
- 实现文件清单：`experiments/run_experiment_13.py`、`experiments/run_experiment_10.py`、`experiments/run_experiment_12.py`、`tests/test_cr007_experiment_real_benchmark_consumption.py`；`market_data/benchmarks.py` 已复核，既有 helper 足够，本轮未修改。
- 过程文件清单：`process/checks/CP6-CR007-S04-experiment-real-benchmark-consumption-CODING-DONE.md`、`process/stories/CR007-S04-experiment-real-benchmark-consumption.md`、`process/handoffs/META-DEV-CR007-S04-IMPLEMENT-2026-05-22.md`、`process/STATE.md`、`DEV-LOG.md`。
- 实现摘要：实验十三新增真实 `hs300_index` available 分支，输出真实 benchmark metrics/equity/metadata；required missing 分支抛受控 `BenchmarkUnavailableError` 且消息含 status / missing reason；optional missing 分支仅输出 `proxy_baseline`，不填充 `hs300_index` 或 `hs300_*` 字段。
- 实验十/十二对齐：补齐 `benchmark_missing_reason`、`benchmark_kind` 和 missing path `benchmark_dataset=proxy_baseline`；available path 保持 `hs300_index`，relative-return flag 与真实可用性一致。
- 关键决策与偏差：LLD T3 允许必要时改 `market_data/benchmarks.py`；实现复核后确认 CR008 已有 `build_benchmark_field_payload` 和 S02 `resolve_hs300_benchmark(..., price_trade_dates=...)` 能满足 S04，故未修改该 shared 文件。静态 narrow scan 命中实验十/十二既有旧报告默认值和 `data_dir` helper，但本轮未执行旧 report / old data I/O，专项 AST 测试已验证无 literal old path I/O 调用。
- 验证命令：`uv run --python 3.11 pytest -q tests/test_cr007_experiment_real_benchmark_consumption.py`，结果 `7 passed in 0.69s`。
- 验证命令：`uv run --python 3.11 pytest -q tests/test_market_data_hs300_benchmark.py tests/test_cr008_proxy_real_benchmark_fields.py`，结果 `13 passed in 0.80s`。
- 验证命令：`uv run --python 3.11 python -m py_compile experiments/run_experiment_13.py experiments/run_experiment_10.py experiments/run_experiment_12.py market_data/benchmarks.py tests/test_cr007_experiment_real_benchmark_consumption.py`，结果 PASS，退出码 0。
- 静态复核：forbidden import 与危险命令 `rg` 均无命中；data job 命中仅为 remediation 字符串 / 测试断言集合，不是调用；credential / old data / old report 由专项 AST 测试和 narrow scan 复核通过。
- 缓存清理：已清理 pytest / py_compile 生成的 `experiments/__pycache__`、`market_data/__pycache__`、`tests/__pycache__`；清理后 `find experiments market_data tests -type d -name __pycache__ -print` 与 `find ... -name '*.pyc' -print` 均无输出。
- 安全边界：未联网、未真实 Tushare fetch、未真实 lake read/write、未读取、列出、迁移、复制、比对或删除旧 `data/**`，未读取或覆盖旧 `reports/data_quality_report.csv`，未读取 `.env`、token、NAS 凭据或真实私有路径，未修改 `delivery/**`、HLD、ADR、Development Plan、其他 LLD 或 CP5。
- 状态回写：Story 已推进到 `ready-for-verification`；CP6 结论 `PASS`；等待 meta-po 分派 meta-qa 执行 CP7，CP7 前不得启动 CR007-S05。
- meta-qa 验证入口：复跑 S04 专项测试、S02/CR008 benchmark 字段回归、py_compile；重点复核真实 hs300 输出、required missing fail fast、optional proxy 无 hs300 字段、实验十/十二 missing metadata、一切安全边界。
- BLOCKING：无。

## 2026-05-18 - CR005-S06 CP7 验证完成

- Story 范围：`CR005-S06` Backtrader optional backend；执行 `process/handoffs/META-QA-CR005-S06-CP7-VERIFY-2026-05-17.md`，未修改实现代码。
- 调度证据：主线程真实 `spawn_agent` 调度 meta-qa/qa-cao the 2nd，agent_id/thread_id=`019e36bb-f4d5-7153-8b8d-738352fbc0b0`；验证完成后已关闭该 agent。
- CP7 输出：`process/checks/CP7-CR005-S06-backtrader-optional-backend-VERIFICATION-DONE.md`，结论 `PASS`，无 BLOCKING / REQUIRED 失败项。
- 验证结果：S06 专项 `16 passed in 0.40s`；全量 pytest `106 passed in 2.95s`；真实 Backtrader tiny Cerebro smoke 输出 `Cerebro`；forbidden import/token/network scan 无输出。
- 复核结论：dependency group=`backtrader` 且锁定 `backtrader==1.9.78.123`；默认 `run_backtest(...)` / lightweight 路径不导入、不依赖 Backtrader；Backtrader 仅在 dependency probe/runtime lazy import；quality/PIT/复权/benchmark missing 均结构化阻断或透传，不 fetch/backfill/write。
- 边界：未联网、未真实 Tushare fetch、未读取 token、未写真实 `data/**`、`reports/**` 或 `delivery/**`；未将 `proxy_baseline` 当作 `hs300_index`。
- 状态回写：`CR005-S06` 已收敛为 `verified`；`process/STATE.md` 与 `process/STORY-STATUS.md` 已同步 CP7 结果。

## 2026-05-18 - CR005-S06 实现 / CP6 完成

- Story 范围：`CR005-S06` Backtrader optional backend；执行 `process/handoffs/META-DEV-CR005-S06-IMPLEMENT-2026-05-17.md`，未进入 CP7，未修改或导入 `market_data/connectors/**`、`market_data/runtime.py`、`market_data/storage.py`。
- 实现文件清单：`engine/backtrader_adapter.py`、`engine/backtest.py`、`tests/test_backtrader_optional_backend.py`、`README.md`、`docs/USER-MANUAL.md`、`pyproject.toml`、`uv.lock`。
- 过程文件清单：`process/checks/CP6-CR005-S06-backtrader-optional-backend-CODING-DONE.md`、`process/stories/CR005-S06-backtrader-optional-backend.md`、`process/handoffs/META-DEV-CR005-S06-IMPLEMENT-2026-05-17.md`、`DEV-LOG.md`。
- 实现摘要：新增 `BacktraderRequest` / `BacktraderResult` typed schema、dependency probe、quality/PIT/复权/benchmark 阻断、benchmark metadata 只读透传和 `run_backtrader_backend(...)`；`engine/backtest.py` 只新增 `select_backtest_backend(...)` 与 `run_backtest_with_backend(...)`，默认 `run_backtest(...)` 语义不变。
- 依赖决策：按用户确认执行 `uv add --group backtrader backtrader==1.9.78.123`，由 uv 更新 `pyproject.toml` / `uv.lock`；实现保持 lazy import，默认 lightweight 不导入 Backtrader。
- 关键边界：未联网、未真实 Tushare fetch、未读取 token、未写真实 `data/**`、`reports/**` 或 `delivery/**`；benchmark `required_missing` 仅透传 `missing_reason`、`next_action`、`remediation_job_spec`，不 fetch/backfill/write；`proxy_baseline` 不填充 `hs300_index`。
- 验证命令：`UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_backtrader_optional_backend.py`，结果 `16 passed in 0.38s`。
- 验证命令：`UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q`，结果 `106 passed in 3.30s`。
- 真实 Backtrader smoke：`UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 --group backtrader python -c "import backtrader as bt; cerebro = bt.Cerebro(); print(type(cerebro).__name__)"`，结果 `Cerebro`，结论 PASS；未触发真实 smoke 失败 fallback。
- fake smoke：`tests/test_backtrader_optional_backend.py::test_fake_backtrader_smoke_completed_path` 覆盖 completed 路径；dependency missing 测试覆盖 `backend_unavailable` 降级。
- 状态回写：`CR005-S06` 已推进到 `ready-for-verification`；CP6 结论 `PASS`；等待 meta-po 分派 meta-qa 执行 CP7。
- meta-qa 验证入口：复跑 S06 专项测试、全量 pytest、真实 Cerebro smoke；重点复核 lazy import、默认 lightweight 不导入 Backtrader、forbidden import/no token/no network/no write、quality/PIT/复权阻断和 benchmark missing 不补数。
- BLOCKING：无。

## 2026-05-18 - CR005-S06 CP5 批准 / 实现交接创建

- Story 范围：`CR005-S06` Backtrader optional backend；用户已 approve `checkpoints/CP5-CR005-BATCH-D-S06-LLD-BATCH.md`。
- 用户确认：dependency group 使用 `backtrader`，版本固定为 `backtrader==1.9.78.123`；实现阶段必须 lazy import，默认 `lightweight` 不依赖 Backtrader；CP6 必须验证 Python 3.11 import + tiny Cerebro smoke test；若真实 Backtrader smoke 失败，则降级为 `backend_unavailable` + fake smoke，不在本 Story 临时切换 fork。
- 状态回填：`process/stories/CR005-S06-backtrader-optional-backend-LLD.md` 已改为 `confirmed=true` / `implementation_allowed=true`；`process/stories/CR005-S06-backtrader-optional-backend.md` 已推进到 `dev-ready`。
- 已创建并调度实现 handoff：`process/handoffs/META-DEV-CR005-S06-IMPLEMENT-2026-05-17.md`；真实 `spawn_agent` 调度 meta-dev/dev-qin the 2nd，agent_id/thread_id=`019e36b0-6aa1-7b92-a9b9-4ef69d986471`，当前执行中。
- CP6 完成：meta-dev/dev-qin the 2nd 已完成实现并回填 `process/checks/CP6-CR005-S06-backtrader-optional-backend-CODING-DONE.md`，结论 `PASS`；主线程已关闭该 agent。
- 主线程复核：S06 专项 `16 passed in 0.40s`；全量 pytest `106 passed in 3.00s`；真实 Backtrader tiny Cerebro smoke 输出 `Cerebro`。
- CP7 调度：已创建 `process/handoffs/META-QA-CR005-S06-CP7-VERIFY-2026-05-17.md`，并真实 `spawn_agent` 调度 meta-qa/qa-cao the 2nd，agent_id/thread_id=`019e36bb-f4d5-7153-8b8d-738352fbc0b0`。
- 允许范围：`engine/backtrader_adapter.py`、`tests/test_backtrader_optional_backend.py`、必要的 `engine/backtest.py` wrapper/selector、`README.md`、`docs/USER-MANUAL.md`、`pyproject.toml`、`uv.lock`、CP6 和 Story/hand off 状态文件。
- 禁止范围：不得修改或导入 `market_data/connectors/**`、`market_data/runtime.py`、`market_data/storage.py`；不得联网、不得真实 Tushare fetch、不得读写 `TUSHARE_TOKEN`、不得写真实 `data/**`、`reports/**`、`delivery/**`。

## 2026-05-17 - CR005-S06 LLD / CP5 启动

- Story 范围：`CR005-S06` Backtrader optional backend；当前只启动 LLD/CP5，不进入实现。
- 前置事实：`CR005-S02`、`CR005-S03`、`CR005-S04`、`CR005-S05` 均已 verified / CP7 PASS；S06 LLD 可消费 PIT/复权、quality/readers、BenchmarkResult 与文档边界。
- 已创建 handoff：`process/handoffs/META-DEV-CR005-S06-LLD-2026-05-17.md`，批次为 `CR005-BATCH-D-S06-LLD`。
- 调度证据：主线程真实 `spawn_agent` 调度 meta-dev/dev-shi the 2nd，agent_id/thread_id=`019e3696-747c-7cc1-86fa-3f8fe7a2df54`；已完成并关闭，CP5 自动预检 `PASS`。
- LLD 输出：`process/stories/CR005-S06-backtrader-optional-backend-LLD.md`，14 个可见章节，frontmatter `status=ready-for-review`、`confirmed=false`、`implementation_allowed=false`。
- CP5 自动预检：`process/checks/CP5-CR005-S06-backtrader-optional-backend-LLD-IMPLEMENTABILITY.md`，结论 `PASS`；无阻断 Batch D 人工审查的问题。
- CP5 人工审查稿：`checkpoints/CP5-CR005-BATCH-D-S06-LLD-BATCH.md`，状态 `pending`，等待用户确认。
- 已更新 Story 状态：`process/stories/CR005-S06-backtrader-optional-backend.md` 进入 `lld-ready-for-review`，等待 CP5 Batch D 人工确认。
- 停止点：meta-dev 只允许输出 `process/stories/CR005-S06-backtrader-optional-backend-LLD.md` 和 `process/checks/CP5-CR005-S06-backtrader-optional-backend-LLD-IMPLEMENTABILITY.md`；完成后等待 CP5 Batch D 人工确认。
- 禁止范围：不得实现 Backtrader adapter、不得创建 `engine/backtrader_adapter.py`、不得修改 `pyproject.toml` / `uv.lock`、不得安装 Backtrader、不得联网、不得真实写 lake、不得读写 `TUSHARE_TOKEN`。
- 开放项：`CR5-Q3` Backtrader 依赖版本上限与 optional dependency 分组仍为 OPEN，LLD 必须显式给出选项或保持待确认，不能伪确定。

## 2026-05-17 - CR005-S04/S05 CP7 验证完成

- Story 范围：`CR005-S04`、`CR005-S05`；主线程真实并行 `spawn_agent` 调度两个 meta-qa 验证子 agent，均已 CP7 PASS，并已关闭子 agent。
- S04 调度证据：meta-qa/qa-kong the 2nd，agent_id/thread_id=`019e368a-3a6e-76d3-9852-51a4df77869f`，handoff=`process/handoffs/META-QA-CR005-S04-CP7-VERIFY-2026-05-17.md`，CP7=`process/checks/CP7-CR005-S04-hs300-local-benchmark-VERIFICATION-DONE.md`，结论 `PASS`。
- S05 调度证据：meta-qa/qa-hua the 2nd，agent_id/thread_id=`019e368a-3ad8-7331-b077-0795de00839c`，handoff=`process/handoffs/META-QA-CR005-S05-CP7-VERIFY-2026-05-17.md`，CP7=`process/checks/CP7-CR005-S05-comparison-backfill-docs-VERIFICATION-DONE.md`，结论 `PASS`。
- S04 验证结果：`tests/test_market_data_hs300_benchmark.py` 6 passed；`tests/test_market_data_hs300_benchmark.py tests/test_market_data_multidataset_quality_readers.py` 15 passed；全量离线 pytest 90 passed。验证覆盖 typed schema、四状态、dry-run remediation、no auto backfill、no network/no token/no write lake、实验十/十二只读接入和 proxy_baseline 边界。
- S05 验证结果：`tests/test_market_data_tushare_comparison.py` 5 passed；`tests/test_market_data_tushare_comparison.py tests/test_market_data_multidataset_quality_readers.py` 14 passed；`tests/test_market_data_cli_comparison.py` 6 passed；全量离线 pytest 90 passed。验证覆盖 comparison 10 字段、status summary、P0 dataset defaults、本地只读/远程 URL 拒绝、文档真实启用前置、显式 backfill、required_missing、proxy_baseline 与 Backtrader optional 口径。
- 状态回写：`CR005-S04` 与 `CR005-S05` 已从 `ready-for-verification` 收敛为 `verified`；`process/STATE.md` 与 `process/STORY-STATUS.md` 已同步 CP7 结果。
- 阻断项：无 BLOCKING / REQUIRED 失败项。保留非阻断观察：CR5-Q2 benchmark 口径仍未最终确认；当前实现只在调用方显式确认 `benchmark_kind` 时返回 available。
- 边界：未启动 `CR005-S06` 或 Backtrader；未执行真实联网、真实 Tushare fetch、真实写 lake；未写 token 或真实行情数据。

## 2026-05-17 - CR005-S04/S05 并行实现 / CP6 完成

- Story 范围：`CR005-S04`、`CR005-S05`；用户确认 CP5 Batch B2/C 通过后，主线程真实并行 `spawn_agent` 调度两个 meta-dev 实现子 agent，未进入 `CR005-S06`、Backtrader、真实联网、真实 Tushare fetch 或真实写 lake。
- S04 调度证据：meta-dev/dev-zhu the 2nd，agent_id/thread_id=`019e367e-b356-79c0-9023-863f58d9979a`，handoff=`process/handoffs/META-DEV-CR005-S04-IMPLEMENT-2026-05-17.md`，CP6=`process/checks/CP6-CR005-S04-hs300-local-benchmark-CODING-DONE.md`，结论 `PASS`。
- S05 调度证据：meta-dev/dev-lv the 2nd，agent_id/thread_id=`019e367e-b3af-7540-857d-1558c77acd34`，handoff=`process/handoffs/META-DEV-CR005-S05-IMPLEMENT-2026-05-17.md`，CP6=`process/checks/CP6-CR005-S05-comparison-backfill-docs-CODING-DONE.md`，结论 `PASS`。
- S04 实现摘要：新增 `market_data/benchmarks.py` 与 `tests/test_market_data_hs300_benchmark.py`，修改实验十/十二只读接入 benchmark metadata；缺 `hs300_index` 返回 typed `unavailable` / `required_missing` / `quality_failed`，只返回 `next_action` / `remediation_job_spec`，不自动补数、不联网、不写湖、不读 token。
- S05 实现摘要：扩展 `market_data/comparison.py` 的 CR005 本地 comparison 与 status summary，更新 `README.md`、`docs/USER-MANUAL.md` 和 `tests/test_market_data_tushare_comparison.py`；文档明确 Tushare 真实启用前置、显式 backfill、`required_missing` 边界、`proxy_baseline` 限制与 Backtrader optional backend。
- S04 验证命令：`UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_market_data_hs300_benchmark.py`，结果 `6 passed`；`UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_market_data_hs300_benchmark.py tests/test_market_data_multidataset_quality_readers.py`，结果 `15 passed`。
- S05 验证命令：`UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_market_data_tushare_comparison.py`，结果 `5 passed`；`UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_market_data_tushare_comparison.py tests/test_market_data_multidataset_quality_readers.py`，结果 `14 passed`；`UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_market_data_cli_comparison.py`，结果 `6 passed`。
- 状态回写：`CR005-S04` 与 `CR005-S05` 均已推进到 `ready-for-verification`；`process/STATE.md` 与 `process/STORY-STATUS.md` 已同步 CP6 结果。
- 下一步：并行调度 meta-qa 执行 S04/S05 CP7；QA 通过前不得标记 `verified`，不得启动 S06 或 Backtrader。

## 2026-05-17 - CR005-S03 CP7 验证完成

- Story 范围：仅 `CR005-S03`；执行 `process/handoffs/META-QA-CR005-S03-CP7-VERIFY-2026-05-17.md`，未进入 CR005-S04/S05/S06、Backtrader、真实联网、真实 Tushare fetch 或真实写 lake。
- 调度证据：主线程真实 `spawn_agent` 调度 meta-qa/qa-shi the 2nd，agent_id/thread_id=`019e363c-9916-7971-980a-699bcf023852`，spawned_at=`2026-05-17T22:00:28+08:00`，completed_at=`2026-05-17T22:02:18+08:00`。
- CP7 输出：`process/checks/CP7-CR005-S03-multidataset-quality-catalog-readers-VERIFICATION-DONE.md`，结论 `PASS`；`process/VERIFICATION-REPORT.md` 已追加 S03 CP7 摘要。
- 测试结果：S03 单测 `9 passed in 0.54s`；S03+S02 回归 `18 passed in 0.63s`；既有 normalization/validation/readers 回归 `9 passed in 0.50s`；全量 `79 passed in 3.09s`。
- 静态与边界复核：实现文件无 connector/runtime import、无 `TUSHARE_TOKEN`、无网络库、无 Backtrader 依赖、无危险命令；最近窗口未写 `data/**`、`reports/**` 或 `delivery/**`。
- 观察项：`__pycache__` 目录存在；本轮按用户禁令未清理 `engine/**` / `experiments/**`，不计入 S03 实现产物。
- 状态建议：建议 meta-po 将 `CR005-S03` 收敛为 `verified`；QA 未直接标记 Story verified。

## 2026-05-17 - CR005-S03 实现 / CP6 完成

- Story 范围：仅 `CR005-S03`；执行 `process/handoffs/META-DEV-CR005-S03-IMPLEMENT-2026-05-17.md`，未进入 CP7、CR005-S04/S05/S06、Backtrader、真实联网、真实 Tushare fetch 或真实写 lake。
- 调度证据：主线程真实 `spawn_agent` 调度 meta-dev/dev-yang the 2nd，agent_id/thread_id=`019e362c-89d6-7311-ac56-c546fdcd38c6`；handoff 已回填 `status=completed`，未使用 inline fallback。
- 实现文件清单：`market_data/validation.py`、`market_data/catalog.py`、`market_data/readers.py`、`market_data/contracts.py`、`tests/test_market_data_multidataset_quality_readers.py`。
- 过程文件清单：`process/checks/CP6-CR005-S03-multidataset-quality-catalog-readers-CODING-DONE.md`、`process/stories/CR005-S03-multidataset-quality-catalog-readers.md`、`process/STATE.md`、`process/STORY-STATUS.md`、`process/handoffs/META-DEV-CR005-S03-IMPLEMENT-2026-05-17.md`、`DEV-LOG.md`。
- 实现摘要：`validation.py` 扩展 quality row 至 S03 完整字段集，新增多 dataset quality、`validate_hs300_index`、PIT as-of gate 和复权一致 gate；`catalog.py` 扩展多 dataset catalog entry 与 policy-aware get/list；`readers.py` 新增结构化 `ReaderResult`、`QualityPolicy`、只读 `read_dataset` 和 clean `read_factor_panel`；`contracts.py` 仅补充 typed status 常量，未改写 S02 schema 语义。
- 关键决策与偏差：保持既有 `read_canonical(...)` 返回 DataFrame 的兼容行为；S03 新契约通过 `read_dataset(...)` 返回结构化结果；catalog 默认 `get(dataset)` 不阻断 warn，reader 显式 quality policy 才阻断 warn/fail，避免破坏 CR-004 旧测试。
- 已知限制：`hs300_index` benchmark 最终 available policy 仍按 CP5 风险接受由 S04 冻结；S03 只记录 `benchmark_kind` / `policy_unconfirmed` 并提供 gate，不宣称最终 benchmark available。
- 验证命令：`UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_market_data_multidataset_quality_readers.py`，初次结果 `9 passed in 1.09s`，末次复核 `9 passed in 0.50s`。
- S02 最小回归：`UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_market_data_multidataset_quality_readers.py tests/test_market_data_tushare_datasets.py`，结果 `18 passed in 0.53s`。
- 既有 reader/validation 回归：`UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_market_data_normalization_validation_readers.py`，结果 `9 passed in 0.47s`。
- 合并回归：`UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q tests/test_market_data_multidataset_quality_readers.py tests/test_market_data_tushare_datasets.py tests/test_market_data_normalization_validation_readers.py`，结果 `27 passed in 0.62s`。
- 全量离线回归：`UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q`，结果 `79 passed in 3.33s`。
- 越界复核：静态扫描确认 `readers.py`、`validation.py`、`catalog.py` 无 `market_data.connectors` / `market_data.runtime` import；实现文件无 `TUSHARE_TOKEN`、`requests`、`urllib`、`socket` 命中；reader no-write 测试通过；缓存目录已清理。
- 状态回写：`CR005-S03` 已推进到 `ready-for-verification`；CP6 结论 `PASS`；等待 meta-po 创建 CP7 meta-qa 验证 handoff。
- meta-qa 验证入口：复跑 S03 指定测试、S02 最小回归和全量离线 pytest；重点复核 hs300 open dates denominator、duplicate/lineage/policy_unconfirmed、quality fail/warn policy、PIT future availability、adjustment conflict/missing adjusted、reader no-write/no connector-runtime import。
- BLOCKING：无。不得在 CP7 前标记 `verified`；不得据此自动进入 S04/S05/S06 或 Backtrader。

## 2026-05-17 - CR005-S02 CP7 BLOCKING 修复完成

- Story 范围：仅 `CR005-S02`；执行 `process/handoffs/META-DEV-CR005-S02-CP7-BLOCKER-FIX-2026-05-17.md`，只修复 `CR005-S02-BLOCKER-001` 和 `CR005-S02-BLOCKER-002`，未进入 CR005-S03/S04/S05/S06、Backtrader 或 CP7 验证。
- 实现文件清单：`market_data/normalization.py`、`tests/test_market_data_tushare_datasets.py`；过程文件清单：`process/checks/CP6-CR005-S02-tushare-dataset-schema-normalization-CODING-DONE.md`、`process/stories/CR005-S02-tushare-dataset-schema-normalization.md`、`process/STATE.md`、`process/handoffs/META-DEV-CR005-S02-CP7-BLOCKER-FIX-2026-05-17.md`、`DEV-LOG.md`。
- `CR005-S02-BLOCKER-001` 修复：`_parse_date` 改为真实日历解析，`%Y%m%d` 使用 `datetime.strptime`，ISO-like 输入使用 `date.fromisoformat`；`20261340`、非法月份、非法日期和不可解析值均 `invalid_date` fail fast。
- `CR005-S02-BLOCKER-002` 修复：`normalize_run(..., dataset=prices)` 支持消费同一 manifest/run 中 exact `prices.adj_factor` success records，按 `trade_date,symbol` join 到 `prices.daily`，输出 `adj_factor`、`adjusted_open/high/low/close` 和统一 `adjustment_policy`；缺因子、duplicate key、policy 冲突和 key 不匹配均 fail fast。
- 关键决策与偏差：没有把 join 逻辑下沉到 Backtrader、reader、engine 或实验代码；没有修改 contracts/source_registry，因为现有 exact `prices.adj_factor` 契约已足够支撑修复；CP6 保留 Batch A 原始实现的真实 `spawn_agent` 调度证据，同时记录本次 handoff 在当前 Codex 线程执行且未伪造新的 agent_id/thread_id。
- 已知限制：本次只解决 S02 CP7 的两个 BLOCKING；不宣称 S02 verified，不刷新 S03/S04/S05/S06 的 dev_gate，不执行真实 Tushare fetch，不写真实 lake 数据。
- 验证命令：`TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q tests/test_market_data_tushare_datasets.py`，结果 `9 passed in 0.45s`。
- 验证命令：`TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q tests/test_market_data_tushare_connector.py tests/test_market_data_tushare_datasets.py`，结果 `14 passed in 0.44s`。
- 扩展回归命令：`TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q tests/test_market_data_tushare_connector.py tests/test_market_data_tushare_datasets.py tests/test_market_data_contracts.py tests/test_market_data_runtime_storage.py tests/test_market_data_normalization_validation_readers.py tests/test_market_data_cli_comparison.py`，结果 `51 passed in 0.78s`。
- 全量离线回归命令：`TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q`，结果 `70 passed in 3.16s`。
- 状态回写：`CR005-S02` 已推进到 `ready-for-verification`；CP6 更新为 `PASS`；等待 meta-po 创建 S02 CP7 重验 handoff。
- 越界复核：未修改 `market_data/connectors/tushare.py`、`market_data/config.py`、`market_data/storage.py`、`market_data/cli.py`、`engine/**`、`experiments/**`、`market_data/readers.py`、`data/**`、`reports/**`、`delivery/**`、`pyproject.toml` 或 `uv.lock`；未写真实 token/API key/cookie/session。
- BLOCKING：无。允许 meta-po 创建 `CR005-S02` CP7 重验 handoff；S02 仍不得标记 `verified`，直到 meta-qa CP7 PASS。

## 2026-05-17 - CR-005 CP5 Batch A LLD 起草

- Story 范围：`CR005-S01`、`CR005-S02`；执行 `process/handoffs/META-DEV-CR005-BATCH-A-LLD-2026-05-17.md`，本轮仅起草 LLD 和 Story 级 CP5 自动预检，不进入实现、CP6 或 CP7。
- 输出文件清单：`process/stories/CR005-S01-tushare-connector-real-lake-writer-LLD.md`、`process/stories/CR005-S02-tushare-dataset-schema-normalization-LLD.md`、`process/checks/CP5-CR005-S01-tushare-connector-real-lake-writer-LLD-IMPLEMENTABILITY.md`、`process/checks/CP5-CR005-S02-tushare-dataset-schema-normalization-LLD-IMPLEMENTABILITY.md`。
- LLD 摘要：S01 冻结 Tushare 默认 disabled、import no-network、missing token / not allowlisted fail fast、`market_data` 写湖层唯一调用边界、`hs300_index` backfill job spec、dry-run 默认、manifest/idempotency/resume/partial success 和 token 不外泄契约；S02 冻结多 dataset schema、`hs300_index` raw->canonical exact mapping、typed status、PIT 字段、`prices` + `adj_factor` adjusted price normalization 和 S03/S04 交接测试要求。
- 未决项：S01 `open_items=3`（CR5-Q1 Tushare 5000 限频/字段、CR5-Q4 lake root、error enum 是否升格全局常量）；S02 `open_items=4`（CR5-Q1 字段/限频、CR5-Q2 hs300 benchmark 口径、prices adjusted price 主选、S04 `next_action` 字段表冻结）。
- CP5 结果：两个 Story 级 CP5 自动预检均为 `PASS`；建议 meta-po 聚合生成 `checkpoints/CP5-CR005-BATCH-A-LLD-BATCH.md` 后发起批次人工确认。当前无阻断 CP5 人工审查的 FAIL；OPEN 项需在人工审查中作为风险接受或后续 Story 前置决策记录。
- 状态回写：已将 CR005-S01 / CR005-S02 Story 卡片更新为 `lld-ready-for-review`，`lld_gate.status=ready-for-review`；已更新 `process/STATE.md` 的 Batch A 状态为 `lld-ready-for-review`，下一步为 meta-po 发起 CP5 Batch A 人工审查。
- 越界复核：未修改 `market_data/**` 业务实现、测试实现、`pyproject.toml`、`uv.lock`、`data/**`、`reports/**`、`delivery/**`；未执行真实联网测试；未写真实行情数据、真实 token 或真实 Tushare 返回样本；未混入 CR005-S03/S04/S05/S06 或 Backtrader 实现。
- BLOCKING：无。CP5 Batch A 人工确认前不得实现真实 Tushare 调用、hs300 backfill、PIT/复权逻辑、Backtrader adapter、依赖变更或真实数据写入。

## 2026-05-16 - CR-003 Jupyter 探索入口实现

- 变更范围：`CR-003` 本地 Jupyter / Notebook 探索入口；执行 `process/handoffs/META-DEV-CR003-JUPYTER-IMPLEMENT-2026-05-16.md`，不重开 HLD / Story Plan。
- 实现文件清单：`pyproject.toml`、`uv.lock`、`.gitignore`、`notebooks/local_research_intro.ipynb`、`notebooks/README.md`、`README.md`、`docs/USER-MANUAL.md`、`process/checks/CP6-CR003-JUPYTER-NOTEBOOKS.md`。
- 关键决策与偏差：按 meta-se 条件结论新增 `[dependency-groups].exploration`，将 `jupyter`、`ipykernel`、`mplfinance` 留在探索依赖组；Notebook 使用 `%matplotlib inline`，读取 `reports/equity_curve.csv` 展示净值/回撤，缺文件只提示；OHLCV K 线只在字段完整时启用 `mplfinance`。
- CR-002 保护：未修改 `engine/charts.py`、`engine/backtest.py`、portfolio、metrics、scanner；`generate_report_charts("reports")` 已验证仍输出 `reports/charts/equity_curve.png`、`drawdown.png`、`monthly_returns.png`、`turnover_holdings.png`。
- 已知限制：Notebook 不执行真实私有数据；`data/ohlcv.csv` 仅作为用户自备数据约定路径；handoff dispatch 字段未由本线程回填，本次不标记 CR completed。
- 验证命令：`UV_CACHE_DIR=/tmp/uv-cache-local-backtest UV_PROJECT_ENVIRONMENT=/tmp/local-backtest-dev-venv uv add --group exploration jupyter ipykernel mplfinance`，通过并更新依赖锁定。
- 验证命令：`UV_CACHE_DIR=/tmp/uv-cache-local-backtest UV_PROJECT_ENVIRONMENT=/tmp/local-backtest-dev-venv uv run --python 3.11 pytest -q`，`12 passed in 3.71s`。
- 验证命令：`UV_CACHE_DIR=/tmp/uv-cache-local-backtest UV_PROJECT_ENVIRONMENT=/tmp/local-backtest-dev-venv uv run --python 3.11 --group exploration python - <<'PY' ... PY`，Notebook JSON、code boundary、`matplotlib` / `mplfinance` / `ipykernel` / `jupyter` import 均通过。
- 验证命令：`rg -n "savefig|reports/charts" notebooks || true`，仅命中 `notebooks/README.md` 中的正式报告边界说明；Notebook code cells 未命中。
- CP6：`process/checks/CP6-CR003-JUPYTER-NOTEBOOKS.md`，结论 `PASS`。
- meta-qa 验证入口：复跑 pytest、Notebook JSON/code boundary 检查、exploration import 检查，并确认 `notebooks/local_research_intro.ipynb` 不写正式报告图表目录。
- BLOCKING：无。待 meta-qa 验证与 meta-po 回填 CR-003 调度证据。

## 2026-05-16 - CR-001 目录结构收敛执行

- 变更范围：`CR-001` 目录结构收敛；执行 `process/handoffs/META-DEV-DIRECTORY-CONVERGENCE-CR-001-2026-05-16.md`，仅处理空目录核验、空目录删除和过程状态回写。
- 清理前核验：`find work -type f -print` 与 `find delivery -type f -print` 均无输出；`find work -type d -empty -print` 仅列出 `work/studies/quant-trading/local_backtest/{data,reports,notebooks,strategies,engine}`；`find delivery -type d -empty -print` 仅列出 `delivery/{skills,agents,rules,doc,scripts}`。
- 删除命令：使用 `rmdir` 删除 `work/studies/quant-trading/local_backtest/` 下五个空子目录、该旧骨架目录、清理后变空的 `work/studies/quant-trading/`、`work/studies/`、`work/`，以及 `delivery/` 下五个空子目录和 `delivery/` 本身。
- 清理后核验：`find work -maxdepth 6 -print`、`find delivery -maxdepth 6 -print`、`find work -type f -print`、`find delivery -type f -print` 均返回目录不存在；无残留文件。
- 已删除空目录：`work/studies/quant-trading/local_backtest/data/`、`reports/`、`notebooks/`、`strategies/`、`engine/`、`work/studies/quant-trading/local_backtest/`、`work/studies/quant-trading/`、`work/studies/`、`work/`、`delivery/skills/`、`delivery/agents/`、`delivery/rules/`、`delivery/doc/`、`delivery/scripts/`、`delivery/`。
- 保留目录：无因非空被保留的 `work/` 或 `delivery/` 目录。
- 状态回写：已更新 `process/handoffs/META-DEV-DIRECTORY-CONVERGENCE-CR-001-2026-05-16.md`、`process/STATE.md`、`process/STORY-STATUS.md`、`process/DOCUMENTATION-READINESS-ROUTING-2026-05-16.md`、`checkpoints/CP8-DELIVERY-READINESS.md`、`process/changes/CR-001-DIRECTORY-STRUCTURE-CONVERGENCE-2026-05-16.md`。
- 越界复核：未修改 `engine/**`、`strategies/**`、`tests/**`、`config/**`、真实 `data/**`、真实 `reports/**`；未写 `delivery/**` 内容；未生成安装脚本；未复制 `llm-wiki` 学习资料；未修改 README / USER-MANUAL 正文。
- BLOCKING：无。当前可交给 meta-doc 按 `process/handoffs/META-DOC-DIRECTORY-DOCS-CR-001-2026-05-16.md` 刷新 `README.md` 与 `docs/USER-MANUAL.md`。

## 2026-05-15 - STORY-005 至 STORY-013 批量 LLD 起草

- Story 范围：`STORY-005` 至 `STORY-013`，覆盖 W1-W4 剩余 9 个缺失 LLD；未修改 `STORY-004` LLD。
- 状态：已创建 9 个 LLD 草案，均为 frontmatter `status=ready-for-review`、`confirmed=false`，并将对应 Story 卡片从 `package-draft` 推进到 `package-ready-for-review`；等待 meta-po 聚合 STORY-004 至 STORY-013 的批量 LLD / Story Package 人工确认。
- 输出文件清单：`process/stories/STORY-005-momentum-portfolio-engine-LLD.md`、`process/stories/STORY-006-backtest-metrics-report-metadata-LLD.md`、`process/stories/STORY-007-parameter-sweep-report-LLD.md`、`process/stories/STORY-008-candidate-report-jq-template-LLD.md`、`process/stories/STORY-009-pit-universe-provider-contract-LLD.md`、`process/stories/STORY-010-trade-status-constraints-LLD.md`、`process/stories/STORY-011-limit-event-available-at-LLD.md`、`process/stories/STORY-012-bias-audit-report-LLD.md`、`process/stories/STORY-013-strategy-extension-rsi-macd-LLD.md`。
- open_items 摘要：`STORY-005=3`（STORY-004 loader schema、sell_buffer 精确定义、全部未成交失败阈值）；`STORY-006=2`（Sharpe 标准差为 0、PortfolioResult 成交金额字段）；`STORY-007=1`（扫描 CSV 字段清单）；`STORY-008=1`（保守低换手排序规则）；`STORY-009=4`（历史成分股 source/interface、available_at 日期粒度、PIT 缺口质量状态、fixed/PIT 混合模式）；`STORY-010=3`（状态缺失策略、卖出不可交易原因枚举、交易状态 source/interface）；`STORY-011=3`（涨跌停拒绝/延后、limit 与 qfq 口径一致性、事件类型启用范围）；`STORY-012=2`（审计输入形态、enhanced 候选报告是否重新生成）；`STORY-013=2`（RSI/MACD 默认参数、策略接口返回目标集合或权重前置集合）。
- 状态回写：已更新 `process/STORY-STATUS.md`、`process/LLD-BATCH-PLAN.md`、`process/STATE.md`，标记缺失 LLD 数为 0，下一步为 meta-po 创建批量 Story Package 检查点。
- 越界复核：未实现任何 `engine/**`、`strategies/**` 代码；未生成真实 `data/**`、`reports/**`；未写 `delivery/**`；未生成安装脚本；未创建 guardrail 脚本；未将任何新增 LLD 标记为 `confirmed=true`；未推进任何 Story 到 `in-development`。
- BLOCKING：无。当前阻塞仅为人工确认门控：批量 LLD / Story Package 未确认前不得实现 `STORY-004+`。

## 2026-05-15 - STORY-004 LLD 起草

- Story：`STORY-004` 离线 Data Loader 与合同校验。
- 状态：已创建 `process/stories/STORY-004-offline-data-loader-contract-validator-LLD.md`，frontmatter `status=ready-for-review`、`confirmed=false`、`tier=L`、`open_items=4`；Story 已推进到 `ready-for-lld-review`，等待 meta-po 发起人工确认。
- LLD 摘要：设计覆盖离线 parquet loader、schema/contract validator、日期区间与股票池过滤、复权一致性、`available_at <= decision_time`、PIT/固定股票池警示字段消费、质量报告 `pass/warn/fail` 启动策略、`close_df/universe/calendar/metadata` 标准数据契约、STORY-005 输入边界、失败路径、测试设计和回滚策略。
- 未决点：`O-01` 确认质量报告缺失时是否允许内存 `calculate_quality(...)` 重算但不写报告；`O-02` 确认 fail 是否永远拒绝启动；`O-03` 确认 Markdown 质量报告不作为机器解析入口；`O-04` 确认未来 PIT 股票池声明缺 `snapshot_date/available_at` 时拒绝还是警示。
- 流程状态：`process/stories/STORY-004-offline-data-loader-contract-validator.md`、`process/STORY-STATUS.md`、`process/STATE.md` 已同步到 `ready-for-lld-review` / `waiting-for-lld-approval` 口径。
- 越界复核：未实现 `engine/data_loader.py`；未修改 `engine/contracts.py` 或任何 `engine/**` 代码；未生成真实 `data/*.parquet`、`data/raw/**`、`data/manifests/**`、`reports/data_quality_report.*`、`delivery/**` 或安装脚本；未创建 `scripts/check_delivery_guardrails.py`；未推进 `STORY-005+`。

## 2026-05-17 - CR005-S03 LLD / CP5 起草完成

- Story 范围：仅 `CR005-S03`；执行 `process/handoffs/META-DEV-CR005-S03-LLD-2026-05-17.md`，只完成 LLD 与 CP5 自动预检，未实现代码、未进入 CP6/CP7、未进入 CR005-S04/S05/S06 或 Backtrader。
- 调度证据：主线程真实 `spawn_agent` 调度 meta-dev/dev-xu the 2nd，agent_id/thread_id=`019e3612-e8d5-75a0-bdfd-d0986b413d53`；handoff 已回填 `status=completed`，未使用 inline fallback。
- LLD 输出：`process/stories/CR005-S03-multidataset-quality-catalog-readers-LLD.md`，frontmatter `status=ready-for-review`、`confirmed=false`、`implementation_allowed=false`、`tier=L`、`open_items=5`。
- CP5 输出：`process/checks/CP5-CR005-S03-multidataset-quality-catalog-readers-LLD-IMPLEMENTABILITY.md`，结论 `PASS`，FAIL 0，OPEN 5。
- LLD 摘要：设计冻结多 dataset quality CSV、catalog entry、只读 reader、PIT as-of gate、复权一致 gate 和 `hs300_index` accuracy gate；明确 `fetch_status` 与 `dataset_status` 分离、quality `fail` 阻断、`warn` 仅显式策略放行、reader 默认离线且不导入 connector/runtime。
- 依赖类型：`CR005-S03` 对 `CR005-S02` 为 `contract` 依赖；S02 LLD confirmed 且 CP7 PASS，P0 dataset schema、PIT 字段、adjusted price / `adj_factor`、exact source interface、unknown/fuzzy fail fast 已作为强输入消费。
- 文件所有权：后续实现允许范围为 `market_data/validation.py`、`market_data/catalog.py`、`market_data/readers.py`、必要时 `market_data/contracts.py` 和 `tests/test_market_data_multidataset_quality_readers.py`；本轮未修改这些源码/测试源码。
- Batch / Wave：`CR005-BATCH-B1-S03-LLD` / `CR5-W2`；等待 meta-po 生成或回填 `checkpoints/CP5-CR005-BATCH-B1-S03-LLD-BATCH.md` 并发起人工确认。
- 未决点：`O-S03-01` hs300 benchmark 口径由 S04 冻结；`O-S03-02` catalog 持久化格式按现有代码最小扩展；`O-S03-03` quality_policy 命名实现时与 reader 风格对齐；`O-S03-04` fake backfill -> resolver available 由 S04 补 resolver 侧集成；`O-S03-05` Backtrader feed shape 由 S06 冻结。
- 越界复核：未修改 `market_data/**` 源码、测试源码、`pyproject.toml`、`uv.lock`、`engine/**`、`experiments/**`、真实 `data/**`、`reports/**`；未联网、未真实 Tushare fetch、未写真实 lake、未启动 Backtrader 实现。

## 2026-05-15 - STORY-003 BUG-STORY-003-001 修复提交

- Story：`STORY-003` 标准化 parquet 与数据质量报告。
- Bug：`BUG-STORY-003-001`，BLOCKING，`engine/quality.py` 在 prices 必需字段缺失时抛裸 `KeyError`。
- 状态：已修复并将 Story 提交到 `ready-for-verification`；等待 meta-po 复核后重新分派 meta-qa 回归验证，不直接标记 `verified`。
- 实现文件清单：`engine/quality.py`。
- 关键决策与偏差：`calculate_quality(...)` 继续先计算 `schema_errors`；`_price_metrics(...)` 新增对 prices schema 缺失的结构化降级路径，缺字段时返回可渲染指标并依赖 `missing_required_fields` 触发 `quality_status=fail`。未修改 `engine/contracts.py`、`engine/normalizer.py`、已确认 LLD、Story 计划、需求、HLD 或 ADR。
- 已知限制：本次仅修复 BUG 指定的必需字段缺失路径；`process/VERIFICATION-REPORT.md` 仍保留 meta-qa 上轮 FAIL 结论，等待回归报告刷新。
- 验证命令：`uv run --python 3.11 python -m py_compile engine/quality.py`，通过。
- 验证命令：`PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python - <<'PY' ... PY`，在 `/tmp/story003-quality-regression-*` 临时目录写入 fixture parquet/manifest，覆盖缺 `prices.close`、缺 `prices.symbol`、缺 `prices.trade_date`、完整数据 pass、少量缺失 warn、缺失率 `>5%` fail、覆盖缺口 fail、重复键 fail、`close<=0` fail，全部通过。
- 越界复核：`find data reports delivery -maxdepth 3 -type f | sort` 仅返回 `data/.gitkeep`、`reports/.gitkeep`；未写真实 `data/*.parquet`、`data/raw/**`、`data/manifests/**`、`reports/data_quality_report.*`、`delivery/**`；未推进或实现 STORY-004+；未调用 AKShare/聚宽。
- meta-qa 验证入口：复用 STORY-003 上轮临时目录 fixture，重点回归 `calculate_quality(...)` 的 prices schema 缺失路径和既有 `T-QUALITY-PASS-01`、`T-QUALITY-WARN-01`、`T-QUALITY-FAIL-01`、覆盖缺口、重复键、`close<=0` 路径。
- 风险提示：由于仓库没有 `.git` 元数据，本轮无法输出 git diff 统计；已通过目标文件读取、py_compile、临时目录回归和真实目录扫描完成自检。
- BLOCKING：待 meta-qa 回归确认后关闭。

## 2026-05-15 - STORY-003 实现完成

- Story：`STORY-003` 标准化 parquet 与数据质量报告。
- 状态：已按确认版 LLD 实现完成，并将 Story 推进到 `ready-for-verification`；等待 meta-po 分派 meta-qa 验证。
- 实现文件清单：`engine/normalizer.py`、`engine/quality.py`、`engine/contracts.py`。
- 关键决策与偏差：未创建正式测试文件；按用户边界使用临时目录运行 raw/manifest/parquet/report 样例验证。`engine/contracts.py` 仅追加 schema version、dataset 名称、parquet 文件名、质量报告字段/格式和默认披露常量，保持纯常量模块。
- 已知限制：实现入口只处理本地 raw cache、manifest、parquet 和报告渲染；不调用 AKShare、聚宽或远程数据源；不写真实 `data/*.parquet` 或真实 `reports/data_quality_report.*`；未进入 STORY-004+ 的 Data Loader、回测、扫描或策略范围。
- 验证命令：`uv run python -m py_compile engine/contracts.py engine/normalizer.py engine/quality.py`，通过。
- 验证命令：`uv run python - <<'PY' ... PY`，在 `/tmp/story003-*` 临时目录验证 raw JSONL 解析、exact interface 映射、三类 parquet schema、质量 `pass/warn/fail`、未知 interface、损坏 raw、CSV/Markdown 报告渲染，结果通过。
- 验证命令：`uv run python - <<'PY' ... PY` 静态扫描 `engine/normalizer.py`、`engine/quality.py`，确认未包含 `akshare`、`run_data_prep`、`AkshareAdapter` 令牌，结果通过。
- 未执行项：`uv run --python 3.11 python scripts/check_delivery_guardrails.py` 因仓库不存在 `scripts/check_delivery_guardrails.py` 无法执行，未发现可替代的同名脚本。
- meta-qa 验证入口：可直接用临时目录构造 STORY-002 raw `.jsonl` 与 manifest fixture，调用 `engine.normalizer.run_normalization(...)` 生成隔离 parquet，再调用 `engine.quality.calculate_quality(...)` 与 `render_quality_reports(...)` 验证字段、阈值和报告格式。
- 风险提示：质量降级策略为“failed manifest 批次披露并触发 warn，除非同时出现 schema/覆盖/重复/异常价格/缺失率 > 5% 等 fail 条件”；这是 LLD 允许的本地缓存合规降级路径。
- BLOCKING：无。

## 2026-05-14 - STORY-003 LLD 起草

- Story：`STORY-003` 标准化 parquet 与数据质量报告。
- 状态：已创建 `process/stories/STORY-003-parquet-quality-report-LLD.md`，frontmatter `status=ready-for-review`、`confirmed=false`、`tier=L`、`open_items=0`。
- LLD 摘要：设计覆盖 raw `.jsonl` 到三类标准 parquet 的 exact interface 映射、schema version 策略、字段契约校验、parquet 原子写入、质量报告 CSV/Markdown 输出、`manifest_run_id` 关联、缺失率分母、交易日/自然日新鲜度、`close <= 0` 异常价格、数据源失败但本地 parquet 合规时的 warn/pass 降级、未来函数和幸存者偏差可检测字段。
- 未决点：无阻塞性 OPEN / Spike；待人工确认 exact interface 映射白名单、质量报告 CSV/Markdown 双格式、缺 `is_pit_universe` 时填 `false` 并披露、以及 manifest 不重写历史行而通过报告关联的设计。
- 流程状态：`process/stories/STORY-003-parquet-quality-report.md`、`process/STORY-STATUS.md`、`process/STATE.md` 已同步到 `ready-for-lld-review` / `waiting-for-lld-approval` 口径。
- 越界复核：未实现 `engine/normalizer.py`、`engine/quality.py`；未修改 `engine/contracts.py`；未生成 `data/*.parquet`、`reports/data_quality_report.*`、`delivery/**` 或安装脚本；未写真实 `data/raw/**` / `data/manifests/**`；未调用真实 AKShare 网络接口。

## 2026-05-14 - STORY-002 LLD 起草

- Story：`STORY-002` 数据准备节流重试与 manifest。
- 状态：已创建 `process/stories/STORY-002-data-prep-throttle-manifest-LLD.md`，frontmatter `status=ready-for-review`、`confirmed=false`、`tier=L`、`open_items=0`。
- LLD 摘要：设计覆盖 Batch Planner 稳定批次算法、canonical `batch_id`、`.jsonl` raw 缓存、JSONL manifest append-only 策略、`running/skipped/success/partial_success/failed` 写入顺序、UTC 毫秒时间戳、1 次初始请求 + 3 次重试、`exponential_jitter` 退避、fake adapter 测试入口和 STORY-003 边界。
- 未决点：无阻塞性 OPEN / Spike；需人工确认 raw `.jsonl` 形态、`batch_id` 摘要格式、manifest append/resume 语义、`partial_success` 续传语义，以及 STORY-002 中 `standardized_output_path` 为空并由 STORY-003 后续关联的边界。
- 流程状态：`process/stories/STORY-002-data-prep-throttle-manifest.md`、`process/STORY-STATUS.md`、`process/STATE.md` 已同步到 `ready-for-lld-review` / `ready-for-review` 口径。
- 越界复核：未实现 `engine/data_prep.py`、`engine/akshare_adapter.py`、`engine/manifest.py`；未修改 `engine/contracts.py`；未写入 `data/raw/**`、`data/manifests/**`、`delivery/**`；未生成 `engine/normalizer.py`、`engine/quality.py` 或 `reports/data_quality_report.*`；未推进 STORY-003；未调用真实 AKShare 网络接口。
## 2026-05-17 - CR-004 CP5 Batch A STORY-014/015 实现完成

- Story 范围：`STORY-014`、`STORY-015`；按 `checkpoints/CP5-CR004-BATCH-A-LLD-REVIEW.md` 的 `approved-with-constraints` 结论执行，遵守 `process/constraints/CR004-QUALITY-DATALOADER-CONFIRMATION-CONSTRAINTS-2026-05-17.md`，未提前进入 Data Loader、STORY-016/017、quality gate、多源比对或实验接入。
- 实现文件清单：`market_data/__init__.py`、`market_data/py.typed`、`market_data/contracts.py`、`market_data/config.py`、`market_data/source_registry.py`、`market_data/lake_layout.py`、`market_data/connectors/__init__.py`、`market_data/connectors/protocol.py`、`market_data/connectors/fake.py`、`market_data/connectors/akshare.py`、`market_data/connectors/tushare.py`、`market_data/connectors/tickflow.py`、`market_data/runtime.py`、`market_data/storage.py`、`tests/test_market_data_contracts.py`、`tests/test_market_data_runtime_storage.py`。
- 关键决策与偏差：实现保持 stdlib-only，不修改 `pyproject.toml` / `uv.lock`；真实 adapter 默认 fail-fast；TickFlow 使用 `source_unresolved`；fake `prices.daily` 输出 deterministic rows，并提供 `source_run_id`、`adjustment_policy=none`、`available_at=16:00:00+08:00`；raw 使用 `.tmp` 原子写入、checksum、row_count，manifest append 失败时隔离 orphan raw；resume 使用 `run_id + batch_id + source + interface + params_hash` 幂等键。
- 已知限制：真实 TickFlow/Tushare/AkShare exact API、凭据、配额仍为 OPEN，不启用真实联网；Batch A 只冻结 `prices` + raw/manifest 基础契约，`index_members`、`trade_calendar`、quality gate、多源比对、reader、CLI 和 Data Loader 留给后续 Story。
- 验证命令：`uv run --python 3.11 pytest -q tests/test_market_data_contracts.py tests/test_market_data_runtime_storage.py`，结果 `22 passed in 0.17s`。
- 主线程复核命令：`uv run --python 3.11 pytest -q tests/test_market_data_contracts.py tests/test_market_data_runtime_storage.py`，结果 `22 passed in 0.14s`。
- 主线程全量复核命令：`uv run --python 3.11 pytest -q`，结果 `41 passed in 3.20s`。
- 静态检查：`rg -n "from engine|import engine|from experiments|import experiments|from reports|import reports" market_data`，无输出。
- 缓存检查：`find market_data tests -type d -name '__pycache__' -o -name '*.pyc' -o -path '*/.ipynb_checkpoints/*'`，清理后无输出。
- 状态回写：`STORY-014`、`STORY-015` 已更新为 `ready-for-verification`；CP6 结果写入 `process/checks/CP6-STORY-014-cr004-market-data-package-lake-contracts-CODING-DONE.md` 与 `process/checks/CP6-STORY-015-cr004-connector-runtime-raw-manifest-CODING-DONE.md`。
- meta-qa 验证入口：运行上述两个 `tests/test_market_data*.py`，重点复核 fake/offline 无网络、真实 adapter fail-fast、resume/manifest 一致性、orphan raw、脱敏和文件边界；不得进入 CP7 前置以外的 STORY-016/017 范围。
- 风险提示：仓库当前已有真实 `data/*.parquet` 与 `reports/*` 历史产物，本轮未修改；测试只使用 `tmp_path`。
- BLOCKING：无。等待 meta-po 分派 CP7；本轮不进入 CP7。
## 2026-05-17 - CR-005 CP6 Batch A 实现完成

- Story 范围：`CR005-S01`、`CR005-S02`；执行 `process/handoffs/META-DEV-CR005-BATCH-A-IMPLEMENT-2026-05-17.md`，严格按 S01 -> S02 串行实现，未进入 CR005-S03/S04/S05/S06、Backtrader 或 CP7。
- 实现文件清单：`.gitignore`、`market_data/connectors/tushare.py`、`market_data/config.py`、`market_data/source_registry.py`、`market_data/storage.py`、`market_data/cli.py`、`market_data/contracts.py`、`market_data/normalization.py`、`tests/test_market_data_tushare_connector.py`、`tests/test_market_data_tushare_datasets.py`、`process/stories/CR005-S01-tushare-connector-real-lake-writer.md`、`process/stories/CR005-S02-tushare-dataset-schema-normalization.md`、两个 CP6 文件、handoff 和 `process/STATE.md`。
- S01 摘要：Tushare connector 保持默认 disabled，新增显式真实执行分支、provider 延迟导入 / 测试注入、`hs300_index.daily -> index_daily` 参数映射；新增 `hs300-backfill` CLI job spec，默认 dry-run，`--lake-root` 或 `MARKET_DATA_LAKE_ROOT` 未配置时结构化 `lake_root_missing`，不静默写 `./data`。
- S02 摘要：新增 P0 dataset 契约和 Tushare exact mapping，覆盖 `prices`、`hs300_index`、`trade_calendar`、`index_weights`；normalization 支持 hs300 raw->canonical exact mapping、PIT 字段校验、`prices` adjusted OHLC + `adj_factor` + `adjustment_policy`，unknown/fuzzy mapping、非法日期、duplicate key、复权口径冲突均 fail fast。
- 关键决策与偏差：未修改 `pyproject.toml` / `uv.lock`，未新增 `tushare` 或 Backtrader 依赖；为兼容既有 CR-004 validation，旧 `CANONICAL_PRICES_COLUMNS` 保持最小兼容字段，CR005 严格 adjusted schema 放入 `CR005_CANONICAL_PRICES_COLUMNS` 与 `DATASET_SCHEMA_REGISTRY`。
- O-S01-02 落实：真实 lake root 只接受显式 `--lake-root` 或 `MARKET_DATA_LAKE_ROOT`；`.gitignore` 阻止 repo 内 `data/`、`reports/`、raw/canonical/gold/quality/catalog/manifest、`.env*`、parquet/jsonl artifacts 入库，同时允许 `tests/fixtures/` 小型脱敏样本。
- 安全与越界复核：默认测试 `TUSHARE_TOKEN=`，未联网、未执行真实 Tushare fetch、未写真实行情数据、未提交真实 token 或真实 Tushare 返回样本；未修改 `engine/data_loader.py`、`engine/backtest.py`、`experiments/**`、`market_data/readers.py`、`data/**`、`reports/**`、`delivery/**`。
- 验证命令：`TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q tests/test_market_data_tushare_connector.py tests/test_market_data_tushare_datasets.py`，结果 `12 passed in 0.46s`。
- 验证命令：`TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q tests/test_market_data_contracts.py tests/test_market_data_runtime_storage.py`，结果 `22 passed in 0.19s`。
- 扩展回归命令：`TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q tests/test_market_data_tushare_connector.py tests/test_market_data_tushare_datasets.py tests/test_market_data_contracts.py tests/test_market_data_runtime_storage.py tests/test_market_data_normalization_validation_readers.py tests/test_market_data_cli_comparison.py`，结果 `49 passed in 0.97s`。
- 全量离线回归命令：`TUSHARE_TOKEN= UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --python 3.11 pytest -q`，结果 `68 passed in 3.82s`。
- CP6：`process/checks/CP6-CR005-S01-tushare-connector-real-lake-writer-CODING-DONE.md`、`process/checks/CP6-CR005-S02-tushare-dataset-schema-normalization-CODING-DONE.md`，结论均为 `PASS`。
- meta-qa CP7 建议：复跑上述离线命令；重点验证 lake root missing / env 优先级、token 不外泄、Tushare import no-network、hs300 duplicate/invalid/missing schema、PIT available fields、adjustment_policy conflict；不要执行真实联网或真实写湖。
- BLOCKING：无阻断 CP7 的项。仍有后续 Story 风险接受项：CR5-Q1 真实 Tushare 字段/限频、CR5-Q2 hs300 benchmark 口径、S04 `next_action` 字段表，均不阻断本批 CP7。

## 2026-05-29 - CR018-S01 production current truth 定义与 dataset group 实现完成

- Story：`CR018-S01-production-current-truth-definition-and-dataset-groups`，Wave：`CR018-W1-SCOPE-CONTRACT`。
- 状态：已按 confirmed LLD 与 CP5 approved 批次完成受控离线实现；Story 已推进到 `ready-for-verification`，等待 meta-po 拉起 meta-qa 执行 CP7。
- 实现文件清单：`market_data/release_scope.py`、`market_data/dataset_groups.py`、`market_data/catalog.py`、`tests/test_cr018_release_scope_dataset_groups.py`、`README.md`、`docs/USER-MANUAL.md`、`process/stories/CR018-S01-production-current-truth-definition-and-dataset-groups.md`、`process/checks/CP6-CR018-S01-production-current-truth-definition-and-dataset-groups-CODING-DONE.md`。
- 关键决策与偏差：`release_scope` 固定第一版 scoped release 为 `2015-01-05..latest_closed_trade_date`，pre-2015 / since-inception 输出 `blocked/future_backfill`；`dataset_groups` 固化 P0 required_for_publish 与 P1 auxiliary blocked claims；`catalog.py` 仅增加只读 metadata helper，不调用 publish 或 current pointer 写入。
- 已知限制：S01 只定义合同、JSON-ready summary 和文档边界，不执行真实 provider fetch、真实 lake write、catalog current pointer publish、凭据读取、DuckDB 依赖变更或 QMT operation；CR014 S14 candidate 仍不是 production current truth。
- 验证命令：`PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr018_release_scope_dataset_groups.py`，结果 `7 passed in 0.05s`。
- 静态自检：`git diff --check -- market_data/release_scope.py market_data/dataset_groups.py market_data/catalog.py tests/test_cr018_release_scope_dataset_groups.py README.md docs/USER-MANUAL.md` 无输出。
- CP6：`process/checks/CP6-CR018-S01-production-current-truth-definition-and-dataset-groups-CODING-DONE.md`，结论 `PASS`。
- meta-qa 验证入口：复跑 S01 指定测试，重点检查 release scope、pre-2015 blocked、P0/P1 registry、P1 blocked claims、unknown dataset readiness blocked、JSON-ready summary、catalog helper no-publish 和文档边界。
- 真实操作计数：`provider_fetch=0`、`lake_write=0`、`credential_read=0`、`current_pointer_publish=0`、`qmt_operation=0`；`pyproject.toml`、`uv.lock`、真实 lake 数据均未修改。
- BLOCKING：无。

## 2026-05-29 - CR018 published current truth 阶段三到阶段五真实重跑完成

- 用户目标：基于已发布的 `published current truth` 重跑阶段三到阶段五核心研究，为后续 QMT admission 提供真实生产口径证据。
- 执行范围：只读 `/mnt/ugreen-data-lake` published catalog current pointer；不读取 `.env`，不调用 provider，不执行真实 lake write，不发布 catalog current pointer，不操作 QMT，不改 DuckDB 依赖。
- 前置修复：修正 `scripts/cr018_release_catalog_publish.py` 中 `trade_status` release publish 指针，避免 current pointer 只指向 2015 单文件；修复后 `trade_status` 指向 `canonical/trade_status/1.0/run_id=run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529`，覆盖 `2015-01-01..2026-05-28`，`coverage_denominator=11311360`。
- 新增脚本：`scripts/cr018_run_production_current_truth_research.py`，用于读取 published current truth、生成标准研究输入快照、重跑阶段三 IC / 分组 / 组合、阶段四低波稳健性、阶段五风险 / 成本 / 容量 / 可交易性，并输出 QMT admission evidence。
- 执行命令：`uv run --python 3.11 python scripts/cr018_run_production_current_truth_research.py --lake-root /mnt/ugreen-data-lake --release-id release-cr018-production-current-truth-20150101-20260528-20260529 --run-id run-cr018-production-rerun-20150101-20260528-20260529-01 --start-date 2015-01-01 --end-date 2026-05-28 --overwrite`，结果命令退出码 `0`，报告状态 `fail`。
- 核心结果：`single_volatility_20d_top20` 年化 `2.6937%`，沪深300 `399300.SZ` 年化 `2.7673%`，低波超额 `-0.0736%`；低波最大回撤 `-55.8749%`，沪深300最大回撤 `-46.6961%`；低波 Rank IC 均值 `0.088391`。
- QMT admission：`qmt-admission-evidence.json` 显示 `allowed=false`、`qmt_admission_allowed_count=0`、阻断原因为 `production_rerun_strategy_criteria_failed`；CR018-S09 继续 later-gated。
- Phase 5 可交易性：低波 Top20 `unfilled_trade_count=185`，原因包括 `missing_execution_price=164`、`limit_down_sell_blocked=12`、`limit_up_buy_blocked=6`、`not_tradable=2`、`st_buy_blocked=1`。
- 证据文件：`process/checks/REAL-TUSHARE-CR018-PRODUCTION-RERUN-2026-05-29.md`；报告目录：`reports/production_current_truth/release-cr018-production-current-truth-20150101-20260528-20260529/run-cr018-production-rerun-20150101-20260528-20260529-01/`。
- 验证命令：`uv run --python 3.11 python -m py_compile scripts/cr018_run_production_current_truth_research.py scripts/cr018_release_catalog_publish.py` 无输出，通过；`git diff --check -- scripts/cr018_run_production_current_truth_research.py scripts/cr018_release_catalog_publish.py` 无输出，通过；`uv run --python 3.11 python -m market_data.cli report-readiness --lake-root /mnt/ugreen-data-lake --realism-mode production_strict` 返回 `status=pass`。
- 已知非阻断项：研究运行期间出现 pandas `FutureWarning`，不影响本次报告生成；随后已将 bool 矩阵缺失填充从 `fillna` 改为 `where(...).astype(bool)`，避免后续运行继续触发同类 warning。

## 2026-05-29 - CR018-S04 P1 auxiliary claim boundary 实现完成

- Story：`CR018-S04-industry-market-cap-liquidity-and-exposure-data`，Wave：`CR018-W2-P0-P1-READINESS`。
- 调度证据：`process/handoffs/META-DEV-CR018-S04-IMPLEMENT-2026-05-29.md`，dispatch.mode=`spawn_agent`，tool_name=`multi_agent_v1.spawn_agent`，agent_name=`dev-xu`，agent_id/thread_id=`019e713c-4439-7ed1-acbf-ab5f4b77c2fc`。
- 实现文件清单：`market_data/readers.py`、`engine/research_dataset.py`、`tests/test_cr018_p1_auxiliary_claim_boundary.py`、`process/checks/CP6-CR018-S04-industry-market-cap-liquidity-and-exposure-data-CODING-DONE.md`、`DEV-LOG.md`。
- 实现摘要：reader 侧新增 `build_cr018_p1_auxiliary_availability_metadata()`，只消费显式传入的 P1 metadata，覆盖 industry、market_cap、float_market_cap、beta/style、ADV、turnover、liquidity、capacity、impact_cost，并固定 `unpublished_lake_scan_count=0`；research 侧新增 `build_cr018_p1_claim_boundary()`，P1 缺失时阻断 industry neutral、market cap neutral、pure alpha、capacity、scale_up、capital amplification，但不改变 P0 core current truth readiness。
- 关键决策与偏差：未改 `market_data/contracts.py`、`validation.py`、`benchmarks.py`、S03 primary 测试、依赖锁文件、真实 lake、catalog current pointer 或 QMT 入口；用户允许写入范围不包含 Story 卡片 / `STATE.md`，因此状态回写留给 meta-po。
- 已知限制：本 Story 只定义 availability / claim boundary 合同，不提供真实 P1 数据、不触发 provider fetch、不 publish、不解除 scale_up 或资金放大声明。
- 验证命令：`PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr018_p1_auxiliary_claim_boundary.py tests/test_cr018_release_scope_dataset_groups.py`，结果 `10 passed in 0.54s`。
- 静态自检：`git diff --check -- tests/test_cr018_p1_auxiliary_claim_boundary.py market_data/readers.py engine/research_dataset.py` 无输出；`git status --short -- market_data/__pycache__ tests/__pycache__ engine/__pycache__` 无输出。
- CP6：`process/checks/CP6-CR018-S04-industry-market-cap-liquidity-and-exposure-data-CODING-DONE.md`，结论 `PASS`。
- meta-qa 验证入口：复跑 S04 指定测试和 S01 release scope 回归；重点检查 P1 字段族覆盖、P1 missing 不阻断 P0 core readiness、六类声明 allowed count 为 0、reader 不扫描 unpublished lake、真实操作计数为 0。
- 真实操作计数：`provider_fetch=0`、`lake_write=0`、`credential_read=0`、`current_pointer_publish=0`、`current_truth_publish=0`、`qmt_operation=0`、`duckdb_dependency_change=0`、`unpublished_lake_scan=0`。
- BLOCKING：无。

## 2026-05-29 - CR018-S03 四类 benchmark readiness 实现完成

- Story：`CR018-S03-real-benchmark-index-components-weights-backfill`，Wave：`CR018-W2-P0-P1-READINESS`。
- 状态：已按 confirmed LLD 与 CP5 approved 批次完成受控离线实现；Story 已推进到 `ready-for-verification`，等待 meta-po 拉起 meta-qa 执行 CP7。
- 实现文件清单：`market_data/benchmarks.py`、`market_data/contracts.py`、`market_data/validation.py`、`tests/test_cr018_benchmark_group_readiness.py`、`process/stories/CR018-S03-real-benchmark-index-components-weights-backfill.md`、`process/checks/CP6-CR018-S03-real-benchmark-index-components-weights-backfill-CODING-DONE.md`、`DEV-LOG.md`。
- 实现摘要：`benchmarks.py` 新增 CR018 四类 benchmark registry、4 x 3 dataset requirements、fixture readiness rows 和 claim boundary；`contracts.py` 只追加 benchmark readiness constants / schema；`validation.py` 只追加 matrix readiness validator 与 components / weights PIT helper。
- 关键决策与偏差：四类 symbolic id 固定为 `HS300`、`ZZ500`、`ZZ1000`、`CSI_ALL_SHARE`；三类 dataset type 固定为 `prices`、`components`、`weights`，全部 `required_for_publish=True`；缺任一项时 production excess-return / index-enhancement / tracking-error allowed count 均为 0。工作区存在 S04 既有改动，本轮未修改 `engine/research_dataset.py`、`market_data/readers.py`、`tests/test_cr018_p1_auxiliary_claim_boundary.py` 或真实 lake/catalog 数据。
- 已知限制：本 Story 只定义离线 readiness 合同和校验 helper，不提供真实 benchmark 回补、不触发 provider fetch、不 publish、不解除 QMT admission；provider-specific index code 后续真实运行仍需 per-run authorization。
- 验证命令：`PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr018_benchmark_group_readiness.py tests/test_cr018_release_scope_dataset_groups.py`，结果 `13 passed in 0.44s`。
- CP6：`process/checks/CP6-CR018-S03-real-benchmark-index-components-weights-backfill-CODING-DONE.md`，结论 `PASS`。
- meta-qa 验证入口：复跑 S03 指定测试和 S01 release scope 回归；重点检查四类 benchmark、三类 dataset type、4 x 3 required_for_publish、缺失阻断三类真实 claims、当前成分快照 PIT 阻断、weights 不替代 membership、proxy-as-real count 为 0。
- 真实操作计数：`provider_fetch=0`、`lake_write=0`、`credential_read=0`、`current_pointer_publish=0`、`qmt_operation=0`、`duckdb_dependency_change=0`、`proxy_as_real_count=0`。
- BLOCKING：无。

## 2026-05-29 - CR018-S02 PIT / lifecycle / tradability readiness 实现完成

- Story：`CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill`，Wave：`CR018-W2-P0-P1-READINESS`。
- 执行 handoff：`process/handoffs/META-DEV-CR018-S02-IMPLEMENT-2026-05-29.md`；当前 handoff dispatch 仍为 `pending-spawn_agent`，本轮由用户在当前线程直接指定 meta-dev 执行，未伪造 agent_id / thread_id。
- 实现文件清单：`market_data/contracts.py`、`market_data/validation.py`、`market_data/readers.py`、`tests/test_cr018_pit_tradability_readiness.py`、`process/stories/CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill.md`、`process/checks/CP6-CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill-CODING-DONE.md`、`DEV-LOG.md`。
- 实现摘要：`contracts.py` 追加 S02 PIT / lifecycle / tradability reason codes、required fields、P0 blocked claims 和 forbidden operation counters；`validation.py` 新增 `validate_pit_universe_readiness()`、`validate_lifecycle_readiness()`、`validate_tradability_readiness()`，缺 PIT available 字段、当前快照、as-of violation、lifecycle/code-change/denominator、ST/suspend/trade_status/prices_limit 或涨跌停可成交假设均 fail closed；`readers.py` 新增 `read_pit_tradability_readiness()` 与 `format_readiness_blocked_reason()`，默认 published-only，只消费显式 metadata / readiness result，不扫描 unpublished lake。
- 关键决策与偏差：全部业务变更保持 additive，未删除 S03 benchmark 常量，未改变 S04 P1 helper 语义；Story 状态按 meta-dev 状态机推进到 `ready-for-verification`，但未修改 `STATE.md`，等待 meta-po 汇总状态。
- 已知限制：本 Story 只提供离线 readiness 合同和 helper，不提供真实 PIT/lifecycle/tradability 回补，不执行真实 publish，不解除 QMT admission；真实 provider fetch、真实 lake write、catalog current pointer publish、凭据读取、DuckDB 依赖变更和 QMT operation 仍 blocked。
- 验证命令：`PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr018_pit_tradability_readiness.py tests/test_cr018_benchmark_group_readiness.py tests/test_cr018_p1_auxiliary_claim_boundary.py tests/test_cr018_release_scope_dataset_groups.py`，结果 `25 passed in 0.59s`。
- 静态自检：`git diff --check -- market_data/contracts.py market_data/validation.py market_data/readers.py tests/test_cr018_pit_tradability_readiness.py` 无输出；`git diff --name-only -- pyproject.toml uv.lock` 无输出；`git status --short -- .pytest_cache tests/__pycache__ market_data/__pycache__ engine/__pycache__` 无输出。
- CP6：`process/checks/CP6-CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill-CODING-DONE.md`，结论 `PASS`。
- meta-qa 验证入口：复跑 handoff 指定 pytest 命令；重点检查 PIT available 字段 fail closed、当前快照不可替代历史 PIT、as-of violation 计数、lifecycle/code-change/active denominator 缺失、ST/suspend/trade_status/prices_limit 缺失、涨跌停不可假设、reader published-only / no unpublished scan。
- 真实操作计数：`provider_fetch=0`、`lake_write=0`、`credential_read=0`、`current_pointer_publish=0`、`current_truth_publish=0`、`qmt_operation=0`、`duckdb_dependency_change=0`、`unpublished_lake_scan=0`。
- BLOCKING：无。

## 2026-05-29 - CR018-S05 adjustment dual-view publish readiness 实现完成

- Story：`CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness`，Wave：`CR018-W2-P0-P1-READINESS`。
- 执行 handoff：`process/handoffs/META-DEV-CR018-S05-IMPLEMENT-2026-05-29.md`；handoff frontmatter 仍为 `pending-spawn_agent`，本轮由用户在当前线程直接指定 meta-dev 执行，未伪造 agent_id / thread_id。
- 实现文件清单：`market_data/adjustment_policy.py`、`market_data/validation.py`、`market_data/readers.py`、`tests/test_cr018_adjustment_publish_readiness.py`、`process/checks/CP6-CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness-CODING-DONE.md`、`DEV-LOG.md`。
- 实现摘要：`validation.py` 新增 `AdjustmentPublishReadinessResult` 与 `validate_adjustment_publish_readiness()`，raw / adj_factor / qfq / hfq / returns_adjusted 五类 view 必须全部字段 coverage=1.0、factor coverage=1.0、legacy baseline preserved 且真实操作计数为 0 才可进入 publish readiness；`readers.py` 新增 `build_cr018_adjustment_reader_policy_metadata()`，记录 adjustment policy、view kind、consumer kind、legacy baseline preserved 与 blocked reason，并强制 QMT execution 只能使用 `prices_raw`；`adjustment_policy.py` 新增 CR018 publish policy metadata helper，保留 old qfq baseline readonly。
- 关键决策与偏差：全部业务变更保持 additive，未改变 S02/S03/S04 validation / reader 语义，未修改 `market_data/contracts.py`、provider connector、真实 lake、catalog current pointer、QMT 入口、`engine/research_dataset.py`、S02/S03/S04 primary 测试、`pyproject.toml` 或 `uv.lock`；用户允许写入范围不包含 Story 卡片 / `STATE.md`，因此状态回写留给 meta-po。
- 已知限制：本 Story 只定义离线 readiness 合同、reader metadata 和 policy metadata，不执行真实 provider fetch、真实 lake write、catalog current pointer publish、凭据读取、DuckDB 依赖变更或 QMT operation；真实 publish 仍由后续 Explicit Publish Gate 与 per-run authorization 控制。
- 验证命令：`PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr018_adjustment_publish_readiness.py tests/test_cr018_pit_tradability_readiness.py tests/test_cr018_benchmark_group_readiness.py tests/test_cr018_p1_auxiliary_claim_boundary.py tests/test_cr018_release_scope_dataset_groups.py tests/test_cr017_adjustment_quality_parity.py tests/test_cr017_reader_policy_gates.py`，结果 `43 passed in 0.67s`。
- 静态自检：`git diff --check -- market_data/adjustment_policy.py market_data/validation.py market_data/readers.py tests/test_cr018_adjustment_publish_readiness.py` 无输出；`git diff --name-only -- pyproject.toml uv.lock` 无输出。
- CP6：`process/checks/CP6-CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness-CODING-DONE.md`，结论 `PASS`。
- meta-qa 验证入口：复跑 handoff 指定 pytest 命令；重点检查五类 readiness coverage=100%、缺 adj_factor 或 factor coverage 不足时 publish allowed=0、QMT adjusted view allowed=0、legacy qfq overwrite=0、reader metadata 字段完整、真实操作计数为 0。
- 真实操作计数：`provider_fetch=0`、`lake_write=0`、`credential_read=0`、`current_pointer_publish=0`、`catalog_current_pointer_publish=0`、`current_truth_publish=0`、`qmt_operation=0`、`qmt_adjusted_execution_allowed=0`、`legacy_qfq_overwrite=0`、`duckdb_dependency_change=0`、`unpublished_lake_scan=0`。
- BLOCKING：无。

## 2026-05-29 - CR018-S06 production quality / readiness / rollback gate 实现完成

- Story：`CR018-S06-production-quality-readiness-audit-and-rollback-gate`，Wave：`CR018-W3-PUBLISH-ROLLBACK`。
- 执行 handoff：`process/handoffs/META-DEV-CR018-S06-IMPLEMENT-2026-05-29.md`；handoff frontmatter `dispatch.mode=spawn_agent`、`tool_name=multi_agent_v1.spawn_agent`、agent_name=`dev-zhu`、agent_id/thread_id=`019e7179-7a76-7441-97e8-aa043e067fa3`。
- 实现文件清单：`market_data/validation.py`、`market_data/catalog.py`、`market_data/publish.py`、`tests/test_cr018_readiness_rollback_gate.py`、`process/checks/CP6-CR018-S06-production-quality-readiness-audit-and-rollback-gate-CODING-DONE.md`、`DEV-LOG.md`。
- 实现摘要：`validation.py` 新增 `ReleaseReadinessAuditReport` 与 `build_release_readiness_audit_report()`，聚合 release、dataset、quality、blocked_claims、rollback_target、evidence_refs、真实操作计数和历史 evidence delete counts；`catalog.py` 新增 `ReleaseRollbackContractResult` 与 `build_cr018_release_rollback_contract()`，强制 rollback scope 为 release，dataset-only rollback fail-closed；`publish.py` 新增 `ReleasePublishAuditHookResult` 与 `validate_release_publish_readiness_audit()`，publish 前 hook 只消费 readiness report，不写 current pointer。
- 关键决策与偏差：全部业务变更保持 additive，未改变 S02/S03/S05 既有 readiness helper 语义；P1 auxiliary missing 进入 `blocked_claims` 并标记 `capability_available=false`、`core_release_blocking=false`，不伪装为已具备能力；用户允许写入范围不包含 Story 卡片 / `STATE.md`，因此状态回写留给 meta-po。
- 已知限制：本 Story 只定义离线 / fixture / dry-run readiness audit、rollback metadata 和 publish hook 合同，不执行真实 provider fetch、真实 lake write、catalog current pointer publish、凭据读取、DuckDB 依赖变更或 QMT operation；真实 publish 仍由后续 Explicit Publish Gate 与 per-run authorization 控制。
- 验证命令：`PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile market_data/validation.py market_data/catalog.py market_data/publish.py`，无输出，通过。
- 验证命令：`PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr018_readiness_rollback_gate.py`，结果 `4 passed in 0.40s`。
- 验证命令：`PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr018_readiness_rollback_gate.py tests/test_cr018_adjustment_publish_readiness.py tests/test_cr018_pit_tradability_readiness.py tests/test_cr018_benchmark_group_readiness.py tests/test_cr018_p1_auxiliary_claim_boundary.py tests/test_cr018_release_scope_dataset_groups.py`，结果 `35 passed in 0.60s`。
- 静态自检：`git diff --check -- market_data/validation.py market_data/catalog.py market_data/publish.py tests/test_cr018_readiness_rollback_gate.py` 无输出；`git diff --name-only -- pyproject.toml uv.lock` 无输出；`git status --short -- .pytest_cache tests/__pycache__ market_data/__pycache__ engine/__pycache__` 无输出。
- CP6：`process/checks/CP6-CR018-S06-production-quality-readiness-audit-and-rollback-gate-CODING-DONE.md`，结论 `PASS`。
- meta-qa 验证入口：复跑 handoff 指定 pytest 命令；重点检查 release readiness audit 字段覆盖、P0 fail / required_missing / quality fail 时 publish allowed=0、P1 blocked claims 不伪装能力、release-level rollback、dataset-only rollback blocked、historical evidence delete counts=0、真实操作计数为 0。
- 真实操作计数：`provider_fetch=0`、`real_lake_write=0`、`lake_write=0`、`credential_read=0`、`current_pointer_publish=0`、`catalog_current_pointer_publish=0`、`current_truth_publish=0`、`qmt_operation=0`、`duckdb_dependency_change=0`、`dataset_level_rollback_only_allowed=0`、`historical_evidence_delete(raw/manifest/candidate/quality/release_history)=0`。
- BLOCKING：无。

## 2026-05-29 - CR018-S07 explicit publish gate 与 current reader smoke 实现完成

- Story：`CR018-S07-explicit-publish-gate-and-current-reader-smoke`，Wave：`CR018-W3-PUBLISH-ROLLBACK`。
- 执行 handoff：`process/handoffs/META-DEV-CR018-S07-IMPLEMENT-2026-05-29.md`；handoff frontmatter `dispatch.mode=spawn_agent`、`tool_name=multi_agent_v1.spawn_agent`、agent_name=`dev-zhang`、agent_id/thread_id=`019e7190-bef4-77c0-aefa-e247d20ed6de`。
- 实现文件清单：`market_data/publish.py`、`market_data/catalog.py`、`market_data/readers.py`、`tests/test_cr018_publish_current_reader_smoke.py`、`process/checks/CP6-CR018-S07-explicit-publish-gate-and-current-reader-smoke-CODING-DONE.md`、`DEV-LOG.md`。
- 实现摘要：`publish.py` 新增 `ReleasePublishRequest`、`ReleasePublishDecision`、`explicit_publish_gate()` 和 `forbid_auto_publish_guard()`，强制 `approval_id`、S06 readiness、release evidence、rollback target 全部满足才生成 plan；`catalog.py` 新增 `CurrentPointerUpdatePlan`、`PublishEvidenceRecord`、`build_cr018_current_pointer_update_plan()` 和 `build_cr018_publish_evidence_record()`，只生成 release-level plan / evidence checksum；`readers.py` 新增 `CurrentReaderSmokeResult` 与 `current_reader_smoke()`，覆盖 P0 dataset group，只读 published current pointer，禁止 candidate fallback。
- 关键决策与偏差：全部业务变更保持 additive，复用 S06 readiness / rollback report，不改变 CR014 `publish_current_pointer()` dry-run 合同，也不修改 S02/S03/S04/S05/S06 primary 测试；用户允许写入范围不包含 Story 卡片 / `STATE.md`，因此状态回写留给 meta-po。
- 已知限制：本 Story 只定义离线 / fixture / dry-run publish decision、pointer plan、publish evidence 和 current reader smoke 合同；真实 current pointer publish 仍需后续 per-run authorization，不由本 CP6 授权。
- 验证命令：`PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile market_data/publish.py market_data/catalog.py market_data/readers.py tests/test_cr018_publish_current_reader_smoke.py`，无输出，通过。
- 验证命令：`PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr018_publish_current_reader_smoke.py`，结果 `7 passed in 0.40s`。
- 验证命令：`PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr018_publish_current_reader_smoke.py tests/test_cr018_readiness_rollback_gate.py tests/test_cr018_adjustment_publish_readiness.py tests/test_cr018_pit_tradability_readiness.py tests/test_cr018_benchmark_group_readiness.py tests/test_cr018_p1_auxiliary_claim_boundary.py tests/test_cr018_release_scope_dataset_groups.py tests/test_cr014_catalog_publish_gate.py`，结果 `49 passed in 0.74s`。
- 静态自检：`git diff --check -- market_data/publish.py market_data/catalog.py market_data/readers.py tests/test_cr018_publish_current_reader_smoke.py` 无输出；`git diff --name-only -- pyproject.toml uv.lock` 无输出；`git status --short -- .pytest_cache tests/__pycache__ market_data/__pycache__ engine/__pycache__` 无输出。
- CP6：`process/checks/CP6-CR018-S07-explicit-publish-gate-and-current-reader-smoke-CODING-DONE.md`，结论 `PASS`。
- meta-qa 验证入口：复跑 handoff 指定 pytest 命令；重点检查缺 `approval_id` allowed count=0、P0 fail / evidence incomplete / rollback target missing 时 decision blocked 且 plan 为空、validate/parity/quality/DuckDB audit auto publish count=0、current reader smoke 覆盖 P0 group、缺 current pointer 返回 `catalog_not_published`、candidate fallback blocked、真实操作计数为 0。
- 真实操作计数：`current_pointer_publish=0`、`catalog_current_pointer_publish=0`、`current_truth_publish=0`、`real_lake_write=0`、`lake_write=0`、`credential_read=0`、`provider_fetch=0`、`qmt_operation=0`、`duckdb_dependency_change=0`、`auto_publish_count=0`、`candidate_read_count=0`、`unpublished_lake_scan_count=0`。
- BLOCKING：无。

## 2026-05-29 - CR018-S08 published current truth 研究重跑实现完成

- Story：`CR018-S08-production-current-truth-research-rerun`，Wave：`CR018-W4-RERUN-QMT-ADMISSION`。
- 执行 handoff：`process/handoffs/META-DEV-CR018-S08-IMPLEMENT-2026-05-29.md`；本轮由用户在当前线程直接指定 meta-dev 执行，handoff frontmatter 仍为 `pending-spawn_agent`，`process/STATE.md` 已记录 S08 execution agent 为 `dev-zhang the 2nd` / `019e71a9-6c49-79f1-aa78-b569801046d6` running，本轮不修改 handoff/STATE。
- 实现文件清单：`experiments/production_current_truth_rerun.py`、`engine/research_dataset.py`、`reports/production_current_truth/README.md`、`tests/test_cr018_production_current_truth_rerun.py`、`process/checks/CP6-CR018-S08-production-current-truth-research-rerun-CODING-DONE.md`、`DEV-LOG.md`。
- 实现摘要：新增 `ProductionRerunRequest`、`production_current_truth_rerun_entry()`、`build_rerun_report_payload()`、`build_qmt_admission_evidence()`、`old_report_overwrite_guard()` 和旧 proxy/fixed baseline diff helper；`engine/research_dataset.py` additive 增加 `load_production_current_truth_dataset()`，只消费 S07 published current reader metadata / current truth metadata，candidate、proxy、provider raw fallback、P0 required_missing、未 publish release 和 missing current pointer 全部 fail closed。
- 关键决策与偏差：S08 只交付 fixture / dry-run 合同，不执行阶段三到阶段五真实长任务；S08 未 PASS 时 `qmt_admission_allowed_count=0`；旧 baseline 仅用于 diff，不可作为 production input；旧报告目标冲突时 blocked 并返回 unique target 建议。用户允许写入范围不包含 Story 卡片 / `STATE.md` / handoff，因此状态回写留给 meta-po。
- 已知限制：真实 production rerun、真实写报告、真实 provider fetch、真实 lake write、catalog current pointer publish、凭据读取、DuckDB 依赖变更和 QMT operation 仍需后续 per-run authorization；`reports/production_current_truth/README.md` 位于仓库 `.gitignore` 的 `reports/` 规则下，但文件已在允许写入范围内创建。
- 验证命令：`PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr018_production_current_truth_rerun.py`，结果 `11 passed in 0.52s`。
- handoff 必跑验证：`PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr018_production_current_truth_rerun.py tests/test_cr018_publish_current_reader_smoke.py tests/test_cr018_readiness_rollback_gate.py tests/test_cr018_adjustment_publish_readiness.py tests/test_cr018_pit_tradability_readiness.py tests/test_cr018_benchmark_group_readiness.py tests/test_cr018_p1_auxiliary_claim_boundary.py tests/test_cr018_release_scope_dataset_groups.py tests/test_cr014_catalog_publish_gate.py`，结果 `60 passed in 0.71s`。
- 建议验证：`PYTHONPYCACHEPREFIX=/tmp/cr018-s08-pycompile-cache PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile experiments/production_current_truth_rerun.py engine/research_dataset.py` 无输出；`git diff --check -- experiments/production_current_truth_rerun.py engine/research_dataset.py reports/production_current_truth/README.md tests/test_cr018_production_current_truth_rerun.py` 无输出；`git diff --name-only -- pyproject.toml uv.lock` 无输出；缓存状态检查无输出。
- CP6：`process/checks/CP6-CR018-S08-production-current-truth-research-rerun-CODING-DONE.md`，结论 `PASS`。
- meta-qa 验证入口：复跑 handoff 必跑验证；重点检查未 publish / missing current pointer / P0 required_missing / candidate / proxy / provider raw fallback 均 blocked 且 allowed count=0，loader 只读 published current reader metadata，report payload 字段完整，S08 fail 时 QMT admission allowed count=0，old report overwrite blocked 或 unique target，真实操作计数均为 0。
- 真实操作计数：`old_report_overwrite=0`、`provider_fetch=0`、`lake_write=0`、`credential_read=0`、`qmt_operation=0`、`candidate_read_count=0`、`proxy_input_allowed_count=0`、`duckdb_dependency_change=0`、`real_stage_3_to_5_execution=0`、`catalog_current_pointer_publish=0`。
- BLOCKING：无。

## 2026-05-29 - CR018 production 数据湖 release current pointer 发布完成

- 用户授权：按建议顺序执行数据湖发布收敛；本轮不执行 provider fetch、不读取 `.env` token、不操作 QMT。
- 新增脚本：`scripts/cr018_release_catalog_publish.py`，用于将 full-history `prices` / `adj_factor` 聚合为 release-scoped canonical run、修正 `trade_calendar` / `events` catalog 元数据、生成 release readiness audit，并在显式审批 ID 下发布 10 个核心 dataset current pointer。
- release：`release-cr018-production-current-truth-20150101-20260528-20260529`；release run：`run-cr018-release-full-history-20150101-20260528-20260529`；approval id：`user-approved-cr018-production-current-truth-20260529`。
- 发布结果：`explicit_publish_gate.status=allowed`，`published_count=10`，`current_pointer_publish_count=10`，`catalog_current_pointer_publish_count=10`，`post_publish_readiness_status=pass`，`post_publish_blockers=[]`。
- 核心数据集：`prices`、`adj_factor`、`hs300_index`、`trade_calendar`、`index_members`、`index_weights`、`stock_basic`、`trade_status`、`prices_limit`、`events` 均为 `published/pass/available`。
- full-history 聚合：`prices` 2,768 个 parquet / 11,311,360 行，`adj_factor` 2,768 个 parquet / 11,823,057 行；全部通过 hardlink staging，未复制原始数据。
- 独立复验：`uv run --python 3.11 python -m market_data.cli report-readiness --lake-root /mnt/ugreen-data-lake --realism-mode production_strict` 返回 `status=pass`、`blockers=[]`、`candidate_unpublished_count=0`、`published_count=10`。
- 回归验证：`uv run --python 3.11 pytest -q tests/test_cr018_publish_current_reader_smoke.py tests/test_cr018_readiness_rollback_gate.py tests/test_cr014_catalog_publish_gate.py` 结果 `18 passed in 0.52s`。
- current reader smoke：`prices` / `001914.SZ` / `2019-12-16` 返回 `row_count=1`，`adjustment_policy=qfq`，`source_run_id=run-cr014-s14-prices-adj-factor-2019-234833`，`available_at_rule=daily_close_fact`。
- 证据文件：`process/checks/REAL-TUSHARE-CR018-RELEASE-PUBLISH-2026-05-29.md`；lake 证据在 `/mnt/ugreen-data-lake/quality/run-cr018-release-full-history-20150101-20260528-20260529/`。
- 真实操作计数：`provider_fetch=0`、`credential_read=0`、`qmt_operation=0`；本轮执行了用户授权的 catalog current pointer publish，计数为 `10`。
- 下一步：使用 published release current truth 重跑阶段三到阶段五核心研究；QMT simulation / live 仍后置，需另行 per-run authorization。

## 2026-06-05 - CR020-S04 HMAC pairing / allowlist / scope / nonce / redaction 实现完成

- Story：`CR020-S04-hmac-pairing-allowlist-scope`，Wave：`CR020-W2-CLIENT-AUTH`。
- 执行入口：用户在当前 Codex 线程直接指定 meta-dev 实现子任务 C；CP5 全量 LLD 人工稿 `checkpoints/CP5-CR020-QMT-GATEWAY-READONLY-LLD-BATCH.md` 已于 2026-06-05T08:25:46+08:00 approved。本轮未伪造 `spawn_agent` agent_id/thread_id。
- 实现文件清单：`trading/qmt_auth.py`、`trading/qmt_redaction.py`、`tests/test_cr020_hmac_pairing_allowlist_scope.py`、`process/checks/CP6-CR020-S04-hmac-pairing-allowlist-scope-CODING-DONE.md`、`process/stories/CR020-S04-hmac-pairing-allowlist-scope.md`、`DEV-LOG.md`。
- 实现摘要：`qmt_auth.py` 追加 CR020 schema、request source context、allowlist decision、scope decision、进程内 TTL nonce replay store、S03-compatible HMAC header provider、auth admission decision、no-auth runtime wrapper 和 zero counters；保留 CR019 `PairingApproval`、`QmtAuthConfig`、`validate_hmac_request` 等接口兼容。`qmt_redaction.py` 追加 response/error/diagnostics redaction decision，redaction failed 时返回 blocked 摘要，不允许 raw fallback。
- 关键决策与偏差：nonce store 采用 CP5 已接受的进程内 TTL 边界，不引入持久化或依赖；S04 未修改 `trading/qmt_client.py`、`trading/qmt_gateway_service.py`、`trading/qmt_endpoint_matrix.py`、`trading/qmt_gateway_config.py`、`pyproject.toml` 或 `uv.lock`；Story 卡片和 CP6 记录了 CP5/ADR 聚合状态滞后的事实。
- 已知限制：HMAC pass 只表示调用方识别与 endpoint scope 通过，不授权交易、账户写入、simulation/live、真实 `query_positions`、gateway 启动、QMT 连接或 provider/lake/publish；多进程 / 多实例 nonce 持久防重放仍按 `OPEN-CR020-S04-01` 后续 CR 或 CP5 修订处理。
- 验证命令：`uv run --python 3.11 pytest -q tests/test_cr020_hmac_pairing_allowlist_scope.py tests/test_cr019_qmt_pairing_hmac_auth.py`，结果 `26 passed in 0.10s`。
- 验证命令：`uv run --python 3.11 pytest -q tests/test_cr019_qmt_gateway_run_gates.py`，结果 `14 passed in 0.08s`。
- 静态自检：`uv run --python 3.11 python -m py_compile trading/qmt_auth.py trading/qmt_redaction.py tests/test_cr020_hmac_pairing_allowlist_scope.py` 退出码 0；`git diff --check -- trading/qmt_auth.py trading/qmt_redaction.py tests/test_cr020_hmac_pairing_allowlist_scope.py` 退出码 0，无输出。
- CP6：`process/checks/CP6-CR020-S04-hmac-pairing-allowlist-scope-CODING-DONE.md`，结论 `PASS`；Story 已推进到 `ready-for-verification`，等待 meta-po 路由 meta-qa 执行 CP7。
- meta-qa 验证入口：复跑上述两个 pytest 命令；重点检查 allowlist missing/mismatch/public source、HMAC missing/mismatch/expired、secret unavailable、nonce replay、scope insufficient、redaction failed 全部 blocked 且 adapter/QMT/trading/account-write/provider/lake/publish counters 为 0；检查 provider diagnostics 不含 raw secret/signature/nonce。
- 真实操作计数：`credential_read=0`、`gateway_start=0`、`service_bind=0`、`gateway_socket_open=0`、`qmt_operation=0`、`qmt_api_call=0`、`xtquant_import=0`、`real_order=0`、`account_write=0`、`provider_fetch=0`、`lake_write=0`、`broker_lake_write=0`、`publish=0`、`simulation_or_live_run=0`、`raw_fallback=0`。
- BLOCKING：无。

## 2026-06-05 - CR020-S01/S02 gateway runtime admission 与 session ready gate 基础合同实现完成

- Story：`CR020-S01-windows-gateway-runtime-admission`、`CR020-S02-server-qmt-login-session`；Wave：`CR020-W1-GATEWAY-RUNTIME-SESSION`。
- 执行 handoff：`process/handoffs/META-DEV-CR020-S01-S02-IMPLEMENT-2026-06-05.md`；handoff frontmatter `dispatch.mode=spawn_agent`、`tool_name=multi_agent_v1.spawn_agent`、agent_name=`dev-yang`、agent_id/thread_id=`019e952d-1570-7862-a2f0-e8e4ca5f9518`。
- 实现文件清单：`trading/qmt_gateway_cli.py`、`trading/qmt_gateway_session.py`、`trading/qmt_gateway_config.py`、`trading/qmt_gateway_service.py`、`.env.example`、`tests/test_cr020_windows_gateway_runtime_admission.py`、`tests/test_cr020_server_qmt_login_session.py`、`process/checks/CP6-CR020-S01-windows-gateway-runtime-admission-CODING-DONE.md`、`process/checks/CP6-CR020-S02-server-qmt-login-session-CODING-DONE.md`、`DEV-LOG.md`。
- 实现摘要：S01 新增 S 端 command matrix、optional Typer adapter、runtime flags、runtime admission decision、runtime action plan、health/diagnostics wrapper 和 zero counters；Typer 缺失时返回 `typer_dependency_missing`，模块 import 不失败。S02 新增 `QmtSessionState`、`QmtSessionBlockedReason`、`QmtCredentialRef`、`QmtSessionConfig`、`QmtSessionSnapshot`、`QmtSessionGateResult`、`QmtLoginAdapter` protocol、login plan、ready gate、diagnostics 和 session safety counters。
- 关键决策与偏差：按 CP5 DQ-CP5-CR020-03 采用 Typer optional adapter，不修改 `pyproject.toml` / `uv.lock`；`trading/qmt_gateway_config.py` 与 `trading/qmt_gateway_service.py` 只做 additive 扩展，CR019 lifecycle/config 兼容回归通过；并行 S04 已将 `credential_ref` 加入 redaction 敏感 key，本实现兼容该收紧，S02 公开 `credential_ref` 统一输出 `[REDACTED]`。用户给定主写入范围不包含 Story 卡片 / `STATE.md`，因此状态回写留给 meta-po。
- 已知限制：本轮只交付代码合同和 fixture-only 测试，不读取真实 `.env` / `.env.*`，不启动 gateway，不绑定端口，不打开 socket，不连接 QMT / MiniQMT / XtQuant，不执行真实 `query_positions`，不交易，不账户写入，不执行 provider/lake/publish；Windows 实机 QMT 登录和 ready 信号仍需用户按后续手册手动验证。
- 验证命令：`uv run --python 3.11 pytest -q tests/test_cr020_windows_gateway_runtime_admission.py tests/test_cr020_server_qmt_login_session.py`，结果 `20 passed in 0.08s`。
- 兼容回归：`uv run --python 3.11 pytest -q tests/test_cr019_qmt_gateway_lifecycle.py`，结果 `9 passed in 0.06s`。
- 静态自检：`uv run --python 3.11 python -m py_compile trading/qmt_gateway_cli.py trading/qmt_gateway_session.py trading/qmt_gateway_config.py trading/qmt_gateway_service.py tests/test_cr020_windows_gateway_runtime_admission.py tests/test_cr020_server_qmt_login_session.py` 退出码 0，无输出。
- CP6：`process/checks/CP6-CR020-S01-windows-gateway-runtime-admission-CODING-DONE.md`、`process/checks/CP6-CR020-S02-server-qmt-login-session-CODING-DONE.md`，结论均为 `PASS`。
- meta-qa 验证入口：复跑上述两个 CR020 定向 pytest 和 CR019 lifecycle 回归；重点检查 command matrix 六命令、Typer missing fail-closed、start/serve/bind/public bind blocked、session not ready 阻断 `query_positions`、`.env.example` placeholder-only、AST 禁止导入和所有 forbidden counters 为 0。
- 真实操作计数：`service_start=0`、`service_start_count=0`、`service_bind=0`、`port_bind_count=0`、`credential_read=0`、`qmt_login_call=0`、`qmt_operation=0`、`qmt_api_call=0`、`xtquant_import=0`、`query_positions_adapter_call=0`、`real_order=0`、`account_write=0`、`provider_fetch=0`、`lake_write=0`、`broker_lake_write=0`、`publish=0`、`simulation_or_live_run=0`、`gateway_socket_open=0`、`http_client_call=0`。
- BLOCKING：无。

## 2026-06-05 - CR020-S05/S06 query_positions runtime 与手工安装调试手册实现完成

- Story：`CR020-S05-query-positions-readonly`、`CR020-S06-docs-runbook-cp7-real-machine-validation`。
- 执行入口：CP5 全量 LLD 人工稿 `checkpoints/CP5-CR020-QMT-GATEWAY-READONLY-LLD-BATCH.md` 已 approved；S01/S02、S03、S04 由并行 meta-dev 子 agent 完成后，主线程串行集成 S05/S06。
- 实现文件清单：`trading/qmt_endpoint_matrix.py`、`trading/qmt_gateway_contracts.py`、`trading/qmt_gateway_service.py`、`trading/qmt_client.py`、`trading/qmt_auth.py`、`trading/qmt_runtime.py`、`trading/qmt_runtime_cli.py`、`.env.example`、`docs/QMT-GATEWAY-INSTALL.md`、`docs/QMT-C-S-BRIDGE-RUNBOOK.md`、`tests/test_cr020_query_positions_readonly.py`、`tests/test_cr020_runtime_manual_validation.py`、`tests/test_cr020_docs_runbook_no_authorization.py`、`tests/test_cr019_qmt_gateway_lifecycle.py`、`process/checks/CP6-CR020-S05-query-positions-readonly-CODING-DONE.md`、`process/checks/CP6-CR020-S06-docs-runbook-cp7-real-machine-validation-CODING-DONE.md`。
- 实现摘要：S05 新增 CR020 readonly endpoint overlay、`query_positions` request / redacted payload / counters / success-blocked result、gateway dispatcher gate chain、C 端 REST body bytes 与 HMAC dataclass request 兼容；新增 runtime 模块和 Typer CLI，支持用户手工在 Windows S 端 `serve`、Linux C 端 `query-positions`。S06 在 gateway install doc 与 C/S runbook 追加 Windows / Linux 手工安装调试手册、CP7 evidence schema、排障表和不授权边界。
- 关键决策与偏差：为满足用户“手动安装到 Windows 后用 CLI 验证 QMT 接口”的要求，新增实际 runtime 模块；真实运行仍只由用户手动执行。`pyproject.toml` / `uv.lock` 未修改；Typer 通过 `uv run --with typer` 手工注入；XtQuant 只在 runtime CLI serve 时懒加载，不在离线合同模块 import。
- 已知限制：当前自动验证只覆盖 fixture/static/py_compile；未在本机启动 gateway、未读取真实 `.env`、未连接 QMT、未执行真实 `query_positions`。Windows 实机验证需用户按文档手工执行并提交脱敏 evidence。
- 验证命令：`uv run --python 3.11 pytest -q tests/test_cr020_query_positions_readonly.py tests/test_cr020_runtime_manual_validation.py`，结果 `9 passed in 0.11s`。
- 验证命令：`uv run --python 3.11 pytest -q tests/test_cr020_docs_runbook_no_authorization.py tests/test_cr019_docs_runbook_boundary.py tests/test_cr019_qmt_gateway_lifecycle.py`，结果 `22 passed in 0.15s`。
- 聚合验证：`uv run --python 3.11 pytest -q tests/test_cr020_windows_gateway_runtime_admission.py tests/test_cr020_server_qmt_login_session.py tests/test_cr020_linux_client_rest_transport.py tests/test_cr020_hmac_pairing_allowlist_scope.py tests/test_cr020_query_positions_readonly.py tests/test_cr020_runtime_manual_validation.py tests/test_cr020_docs_runbook_no_authorization.py tests/test_cr019_qmt_gateway_lifecycle.py tests/test_cr019_docs_runbook_boundary.py`，结果 `75 passed in 0.33s`。
- 静态自检：`uv run --python 3.11 python -m py_compile trading/qmt_gateway_contracts.py trading/qmt_endpoint_matrix.py trading/qmt_gateway_service.py trading/qmt_client.py trading/qmt_auth.py trading/qmt_runtime.py trading/qmt_runtime_cli.py tests/test_cr020_query_positions_readonly.py tests/test_cr020_runtime_manual_validation.py tests/test_cr020_docs_runbook_no_authorization.py` 退出码 0；`git diff --check -- <CR020 target files>` 退出码 0。
- CP6：`process/checks/CP6-CR020-S05-query-positions-readonly-CODING-DONE.md`、`process/checks/CP6-CR020-S06-docs-runbook-cp7-real-machine-validation-CODING-DONE.md`，结论均为 `PASS`。
- meta-qa 验证入口：`meta-qa/qa-he` 已调度执行 CR020 fixture/static CP7；禁止读取真实 `.env`、启动 gateway、绑定端口或连接 QMT。
- 真实操作计数：`credential_read=0`、`service_start=0`、`service_bind=0`、`gateway_socket_open=0`、`qmt_operation=0`、`qmt_api_call=0`、`xtquant_import=0`、`real_order=0`、`real_cancel=0`、`account_write=0`、`provider_fetch=0`、`lake_write=0`、`broker_lake_write=0`、`publish=0`、`simulation_or_live_run=0`、`raw_positions_emit=0`。
- BLOCKING：无；真实 Windows/QMT 手工验证待用户执行。

## 2026-06-10 - CR038 第7章因子投资实践离线研究切片实现完成

- 任务：CR-038 第7章因子投资实践、风险模型与组合优化；本轮按 meta-po 冲突预检边界执行，仅实现本地离线研究切片。meta-po 已完成 CR020 no-overlap 冲突预检，并将 CR-038 formal tracking 激活为 `active-story-execution`。
- 实现文件清单：`engine/chapter7_factor_practice.py`、`scripts/run_chapter7_factor_practice.py`、`tests/test_chapter7_factor_practice.py`、`process/checks/CP6-CR038-CHAPTER7-FACTOR-PRACTICE-CODING-DONE.md`、`DEV-LOG.md`。
- 实现摘要：新增第7章纯 pandas engine，消费本地 factor panel、labels 和 CR-037 `ROBUSTNESS-ADMISSION-SUMMARY`；只允许 `baseline` / `candidate` 进入 alpha score，`watch` 仅记录观察策略，`reject` / `needs-more-data` / `blocked_missing_evidence` 默认排除，缺少可消费资产时 fail-closed。组合层输出 `equal_weight_baseline` 与 `risk_adjusted_constrained`，并生成 portfolio metrics、risk exposure、performance attribution、turnover cost analysis、capacity / liquidity proxy 和 portfolio admission summary。
- Runner 摘要：`scripts/run_chapter7_factor_practice.py` 默认写入 `reports/chapter7_factor_practice/<run_id>/` 和 `process/research/chapter7_factor_practice/<run_id>/`；产物包括 `alpha_scores.parquet`、`optimized_portfolios.parquet`、`portfolio_metrics.csv`、`risk_exposure.csv`、`performance_attribution.csv`、`turnover_cost_analysis.csv`、`capacity_liquidity_analysis.csv`、`CHAPTER7-RUN-REPORT.json/md` 和 `PORTFOLIO-ADMISSION-SUMMARY.json`。
- 关键决策与偏差：容量 / 流动性采用本地因子代理 `size_total_market_cap` 与 `abnormal_turnover_21_252`，不读取 broker、分钟线、盘口或外部 provider；`PORTFOLIO-ADMISSION-SUMMARY` 的 `simulation_candidate=false`，只作为 CR-039 研究输入，不构成交易准入。
- 已知限制：已执行本地 2000-2019 / 2020-2026 YTD runner，但仍只属于研究级组合实践；未触碰 QMT、simulation、live、provider、lake、publish、账户、订单、凭据或依赖变更。
- 验证命令：`PYTHONPYCACHEPREFIX=/tmp/cr038-chapter7-pycompile uv run --python 3.11 python -m py_compile engine/chapter7_factor_practice.py scripts/run_chapter7_factor_practice.py tests/test_chapter7_factor_practice.py`，无输出，通过。
- 验证命令：`PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_chapter7_factor_practice.py`，结果 `6 passed in 1.10s`。
- 章节回归：`PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_chapter4_factor_models.py tests/test_chapter5_anomalies.py tests/test_chapter6_factor_robustness.py tests/test_chapter7_factor_practice.py`，结果 `18 passed in 5.61s`。
- 本地研究跑批：`PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python scripts/run_chapter7_factor_practice.py --run-id run-cr038-chapter7-factor-practice-20260610`，结果 `status=PASS`；核心产物在 `process/research/chapter7_factor_practice/run-cr038-chapter7-factor-practice-20260610/` 与 `reports/chapter7_factor_practice/run-cr038-chapter7-factor-practice-20260610/`。
- CP6：`process/checks/CP6-CR038-CHAPTER7-FACTOR-PRACTICE-CODING-DONE.md`，结论 `PASS`。
- meta-qa 验证入口：复跑上述 pytest；重点检查 CR-037 baseline/candidate 消费、watch/reject 隔离、reject-only fail-closed、多档成本敏感性、容量代理字段、报告 / summary 字段和 operation_counts 全 0。
- 真实操作计数：`external_project_clone=0`、`external_project_install=0`、`external_project_run=0`、`source_migration_or_vendor=0`、`dependency_change=0`、`provider_fetch=0`、`lake_write=0`、`catalog_publish=0`、`reports_overwrite=0`、`qmt_operation=0`、`simulation_or_live=0`、`account_or_order_operation=0`、`credential_read=0`。
- BLOCKING：无；后续可由 meta-po 根据 QA 复核结论关闭 CR-038 或启动 CR-039 冲突预检。

## 2026-06-11 - CR045 CP5 前全量 LLD 设计证据完成

- 任务：基于 `process/handoffs/META-DEV-CR045-LLD-BATCH-2026-06-11.md`，按 `lld-designer` 工作流生成 CR045 CP5 前全量设计证据；本轮只写 LLD / technical-note / CP5 自动预检，不写实现代码。
- 批次：`CR045-BRIDGE-BATCH-A`；Wave / 调度范围：S01-S05 full-lld，S06 technical-note。
- 设计证据文件清单：
  - `process/stories/CR045-S01-windows-bridge-security-boundary-LLD.md`
  - `process/stories/CR045-S02-bridge-health-capabilities-skeleton-LLD.md`
  - `process/stories/CR045-S03-wsl-linux-client-contract-and-network-precheck-LLD.md`
  - `process/stories/CR045-S04-readonly-probe-allowlist-and-blocked-first-LLD.md`
  - `process/stories/CR045-S05-redaction-and-no-operation-static-validation-LLD.md`
  - `process/stories/CR045-S06-user-runbook-and-follow-up-gates.md#技术说明`
- CP5 自动预检文件清单：
  - `process/checks/CP5-CR045-S01-windows-bridge-security-boundary-LLD-IMPLEMENTABILITY.md`
  - `process/checks/CP5-CR045-S02-bridge-health-capabilities-skeleton-LLD-IMPLEMENTABILITY.md`
  - `process/checks/CP5-CR045-S03-wsl-linux-client-contract-and-network-precheck-LLD-IMPLEMENTABILITY.md`
  - `process/checks/CP5-CR045-S04-readonly-probe-allowlist-and-blocked-first-LLD-IMPLEMENTABILITY.md`
  - `process/checks/CP5-CR045-S05-redaction-and-no-operation-static-validation-LLD-IMPLEMENTABILITY.md`
  - `process/checks/CP5-CR045-S06-user-runbook-and-follow-up-gates-TECHNICAL-NOTE-IMPLEMENTABILITY.md`
- 设计摘要：S01 冻结 L1-L5 授权、zero secret custody、hard-off 和 no-operation counter baseline；S02 设计 health/capabilities schema 和 false flags；S03 设计 WSL/Linux client、fixture transport 和 network precheck；S04 设计 readonly probe skeleton、L4 未授权 blocked-first 和 negative fixtures；S05 设计 redaction evidence、artifact scan scope 和 forbidden counters；S06 technical-note 收敛 runbook、follow-up gates 和 CP8 wording。
- Story 状态：S01-S06 均更新为 `lld-ready-for-review`；`lld_gate.status=ready-for-review`；`implementation_allowed=false`、`design_evidence_confirmed=false`、`real_runtime_authorized=false` 均保持不变。
- clarification queue：未新增 LCQ；本轮无 `blocks_lld=true` item。CP2/CP3 已 approved 的 DQ 作为设计依据；S01-S06 均在设计证据中记录“无新增阻断灰区”或 technical-note 取舍记录。
- 依赖类型与文件所有权：全部依赖均按 `contract` 处理；future implementation owner 仍为 S02 `engine/goldminer_bridge_contract.py` / shared contract tests、S03 client、S04 readonly probe、S05 static validation tests、S06 runbook。CP5 前未创建任何 future implementation file。
- CP5 结果：6 份自动预检均为 `PASS`；阻断项 0，豁免项 0。默认 `process/context/CP5-LLD-CONTEXT.yaml` 缺失，按 handoff compact 输入和 CR045 scoped documents 执行，并在每份 CP5 中记录为 N/A。
- 不授权边界：未读取 `.env`、token、account_id、账号、密码、session、cookie、private key 或 Windows credential files；未启动 Windows bridge runtime；未登录/连接 Goldminer；未查询账户/资金/持仓/委托/成交；未下单/撤单；未 simulation/live；未 provider/lake/publish。
- 已知限制：CR045 当前只能进入 CP5 全量人工确认；CP5 approved 前不得实现。真实 Windows runtime、Goldminer readonly 字段、账号权限和 SDK 运行语义仍属于 L3/L4/L5 后续 gate，不阻塞 L2 skeleton 设计证据。
- 下一步：meta-po 收齐并聚合本批次设计证据，生成 `process/checkpoints/CP5-CR045-BRIDGE-BATCH-A-LLD-BATCH.md` 并发起统一人工确认。

## 2026-06-11 - CR045 Bridge Batch A CP7 验证完成

- 任务：按 `process/handoffs/META-QA-CR045-CP7-VERIFY-2026-06-11.md` 对 CR045 Goldminer Windows Bridge Batch A 执行 CP7 验证；范围限定为 L2 skeleton / fixture / static / runbook。
- 验证对象：`engine/goldminer_bridge_contract.py`、`engine/goldminer_bridge_client.py`、`engine/goldminer_bridge_probe.py`、4 个 `tests/test_cr045_goldminer_*.py`、`docs/goldminer/CR045-BRIDGE-RUNBOOK.md`、CP5/CP6/implementation/handoff/STATE 过程证据。
- 验证命令：`PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr045_goldminer_bridge_contract.py tests/test_cr045_goldminer_bridge_client.py tests/test_cr045_goldminer_readonly_probe.py tests/test_cr045_goldminer_no_operation_static.py`，结果 `24 passed in 0.10s`。
- 语法检查：`PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile engine/goldminer_bridge_contract.py engine/goldminer_bridge_client.py engine/goldminer_bridge_probe.py`，退出码 0，无输出。
- 静态检查：`git diff --check` 退出码 0，无输出；CR045 code forbidden import/call `rg` review 无实现层 SDK/network/process/runtime 调用，唯一命中为 client docstring 禁止说明。
- CP7 产物：`docs/quality/VERIFICATION-REPORT-CR045.md`、`docs/quality/TEST-REPORT-CR045.md`、`docs/quality/REVIEW-CR045.md`、`docs/quality/FIXES-CR045.md`、`process/checks/CP7-CR045-BRIDGE-BATCH-A-VERIFICATION-DONE.md`。
- 结论：`PASS_WITH_RISK`；无 P0/P1 缺陷，无 meta-dev 回修项。
- 剩余风险：L3 Windows bridge runtime、L4 real readonly、L5 submit/cancel/simulation/live 仍未授权；这些是 CP8 风险接受 / 不授权输入，不是本轮 L2 blocker。
- 不授权边界：未读取 `.env` / `.env.*`、token、account_id、账号、密码、session、cookie、private key；未启动 Windows bridge runtime；未导入或调用真实 `gm` / `gmtrade` runtime；未登录/连接 Goldminer 或 broker；未查询账户/cash/position/order/fill；未下单、撤单、simulation/live、provider fetch、lake write 或 catalog publish。

## 2026-06-14 - CR053 CP5 设计证据写作完成

- 任务：按 `lld-designer` 协议推进 CR053 `CR053-MIGRATION-INVENTORY-BATCH-A` CP5 设计证据；本轮只写 LLD / technical-note / CP5 自动预检，不写实现代码，不创建 CP5 人工 checkpoint。
- 批次：S01-S04 为 full-lld，S05 为 technical-note；CP3 已 approved，CP4 `process/checks/CP4-CR053-STORY-DAG-PARALLEL-SAFETY.md` 为 PASS。
- 设计证据文件清单：
  - `process/stories/CR053-S01-root-map-and-host-mapping-contract-LLD.md`
  - `process/stories/CR053-S02-repo-inventory-and-path-classification-LLD.md`
  - `process/stories/CR053-S03-path-reference-and-legacy-alias-dry-run-LLD.md`
  - `process/stories/CR053-S04-manifest-transfer-and-backup-plan-LLD.md`
  - `process/stories/CR053-S05-cr058-migration-input-and-close-gate.md#技术说明`
- CP5 自动预检文件清单：
  - `process/checks/CP5-CR053-S01-root-map-and-host-mapping-contract-LLD-IMPLEMENTABILITY.md`
  - `process/checks/CP5-CR053-S02-repo-inventory-and-path-classification-LLD-IMPLEMENTABILITY.md`
  - `process/checks/CP5-CR053-S03-path-reference-and-legacy-alias-dry-run-LLD-IMPLEMENTABILITY.md`
  - `process/checks/CP5-CR053-S04-manifest-transfer-and-backup-plan-LLD-IMPLEMENTABILITY.md`
  - `process/checks/CP5-CR053-S05-cr058-migration-input-and-close-gate-LLD-IMPLEMENTABILITY.md`
- 设计摘要：S01 冻结 7 类 logical root、Linux `/mnt/quant-lab/hot` / `archive` / `cold-backup` 逻辑视图、Windows package exchange 只读窄映射和 `MARKET_DATA_LAKE_ROOT` 不调整；S02 冻结 repo-local inventory 字段、path classification、move_action 和 forbidden content fail-closed；S03 冻结 legacy alias dry-run、manual-review 和历史证据保留策略；S04 冻结 manifest-first transfer、warm / cold backup 分层、restore rehearsal 和 lake policy boundary；S05 technical-note 汇总 CR058 input gate 和 CR053 close gate。
- Story 状态：S01-S05 均更新为 `lld-ready-for-review`；`lld_gate.status=ready-for-review`；`dev_gate.design_evidence_confirmed=false`、`lld_confirmed=false`、`implementation_allowed=false` 均保持未放行。
- clarification queue：未新增 LCQ；本轮无 `blocks_lld=true` item。S01-S05 设计证据均记录 OPEN / Spike / clarification 为 0。
- CP5 结果：5 份自动预检均为 `PASS`；阻断项 0，豁免项 0。等待 host-orchestrator 收齐后生成 `process/checkpoints/CP5-CR053-MIGRATION-INVENTORY-BATCH-A-LLD-BATCH.md` 并发起统一人工确认。
- 不授权边界：未执行 NAS mount / scan / mkdir / copy / delete / migration；未执行真实目录 move / rename；未替换 `MARKET_DATA_LAKE_ROOT` 或移动真实 lake；未读 `.env` / token / account / password / private key；未 provider fetch、lake write、catalog publish、QMT / MiniQMT runtime、git push / tag / history rewrite。
- 未运行检查：本轮为 CP5 设计证据写作，未运行 pytest、inventory scanner、NAS / lake / provider / QMT / Windows 映射或真实迁移命令。

## 2026-06-18 - CR091 QMT Strategy Runner 离线实现切片完成

- 任务：按用户明确授权，使用 meta-dev 子 agent 实现 CR091 已批准的离线 implementation slice；范围仅限 `trading/strategy_runner` 薄模块、离线 checker、fixtures/tests、fake transport 和脱敏 evidence。
- 实现文件清单：`trading/strategy_runner/__init__.py`、`trading/strategy_runner/adapters.py`、`trading/strategy_runner/target_portfolio.py`、`trading/strategy_runner/package_loader.py`、`trading/strategy_runner/cache.py`、`trading/strategy_runner/readonly_gateway.py`、`trading/strategy_runner/evidence.py`、`scripts/check_cr091_strategy_runner_package.py`、`tests/test_cr091_strategy_runner_contracts.py`、`tests/fixtures/cr091_strategy_runner/*`、`process/stories/CR091-QMT-STRATEGY-RUNNER-IMPLEMENTATION.md`、`process/checks/CP6-CR091-QMT-STRATEGY-RUNNER-CODING-DONE.md`。
- 实现摘要：新增 package-driven、multi-factor-first、broker-neutral 的轻量 runner 合同；`AdapterRegistry` 默认支持 `MultifactorAdmissionAdapter`、`LegacyStrategyResultAdapter`、`StrategyPackageAdapter`；所有成功 adapter 输出统一 `TargetPortfolioSnapshot` 并复用 `engine.order_intent_draft.build_order_intent_draft` 生成 `OrderIntentDraftV1`，保持 `qmt_allowed=false`、`not_authorization=true`。
- Package / cache：新增 manifest/checksum 校验和 immutable local cache / active pointer 只读解析；manifest flags、checksum、active pointer、immutable marker 异常均 fail closed。
- Readonly / evidence：新增默认 fake transport 的 readonly wrapper，仅允许 `health`、`capabilities`、`query_positions`，交易写 endpoint 返回 `blocked_scope_denied`；evidence 只输出 redacted summary、target/order intent 计数和 forbidden operation counters。
- 主线程复核补丁：收紧 package wrapper 授权 flags、payload checksum 覆盖、readonly counters / status 纳入 evidence 判定，并补充 3 项 fail-closed 回归测试。
- 验证命令：`PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr091_strategy_runner_contracts.py`，结果 `13 passed in 0.15s`。
- 验证命令：`PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python scripts/check_cr091_strategy_runner_package.py --package-root tests/fixtures/cr091_strategy_runner/cr091_strategy_package --json`，结果 exit code 0，`passed=true`，`target_count=2`，`order_intent_count=2`，forbidden counters 全 0。
- 静态检查：`git diff --check` 退出码 0，无输出。
- CP6：`process/checks/CP6-CR091-QMT-STRATEGY-RUNNER-CODING-DONE.md`，结论 `PASS`。
- 不授权边界：未启动 QMT / MiniQMT / XtQuant / gateway / runner runtime；未访问 NAS；未读取 `.env`、凭据、账号、账户、资金、持仓、委托、成交或日志原文；未执行 submit / cancel、simulation / live、provider / lake / publish；未修改 `AGENTS.md`。
- 已知限制：本次只证明离线 runner 合同、adapter、package intake、fake readonly gateway 与脱敏 evidence；不证明真实 QMT / MiniQMT / XtQuant / gateway runtime 可用，不构成交易授权。下单 / 撤单仍需 CR092 或等价后续 CR；NAS package distribution 仍需 CR093 或等价后续 CR。
