---
checkpoint_id: "CP7"
checkpoint_name: "CR011-S06 行业 / 市值 / 风格暴露 CP7 复验完成检查"
type: "rolling_auto"
status: "PASS"
owner: "meta-qa"
created_at: "2026-05-24T14:55:35+08:00"
checked_at: "2026-05-24T14:55:35+08:00"
target:
  phase: "story-execution"
  change_id: "CR-011"
  story_id: "CR011-S06-industry-market-cap-style-exposure-data"
  story_slug: "industry-market-cap-style-exposure-data"
  wave_id: "CR011-DATA-BATCH-A-VERIFY-W6-REVERIFY"
  blocker_id: "CR011-S06-CP7-F01"
  artifacts:
    - "market_data/readers.py"
    - "engine/research_dataset.py"
    - "tests/test_cr011_exposure_claims.py"
    - "process/stories/CR011-S06-industry-market-cap-style-exposure-data.md"
    - "process/stories/CR011-S06-industry-market-cap-style-exposure-data-LLD.md"
    - "process/checks/CP7-CR011-S06-industry-market-cap-style-exposure-data-VERIFICATION-DONE.md"
    - "process/checks/CP6-CR011-S06-CP7-BLOCKER-FIX-CODING-DONE.md"
source_handoff: "process/handoffs/META-QA-CR011-S06-CP7-REVERIFY-2026-05-24.md"
failed_cp7: "process/checks/CP7-CR011-S06-industry-market-cap-style-exposure-data-VERIFICATION-DONE.md"
blocker_fix_cp6: "process/checks/CP6-CR011-S06-CP7-BLOCKER-FIX-CODING-DONE.md"
validation_env: "process/VALIDATION-ENV.yaml"
manual_checkpoint: "checkpoints/CP5-CR011-DATA-BATCH-A-LLD-BATCH.md"
implementation_scope: "offline-only"
---

# CP7 CR011-S06 Story 复验完成门检查结果

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| CP7 复验 handoff 已读取 | PASS | `process/handoffs/META-QA-CR011-S06-CP7-REVERIFY-2026-05-24.md` | 指向 `CR011-S06-industry-market-cap-style-exposure-data`，要求确认 `CR011-S06-CP7-F01` 是否关闭，并限制写入范围为本复验 CP7 与 Story 验证状态字段。 |
| 验证环境已确认 | PASS | `process/VALIDATION-ENV.yaml` | `approval.confirmed=true`；该文件的历史 `story_id=STORY-001` 仅作为非阻断观察项，本轮验证对象以用户指令和复验 handoff 为准。 |
| Story 已进入待复验 | PASS | `process/stories/CR011-S06-industry-market-cap-style-exposure-data.md` | 复验开始时 `status=ready-for-verification`。 |
| LLD 已确认且关键输入已消费 | PASS | `process/stories/CR011-S06-industry-market-cap-style-exposure-data-LLD.md` | frontmatter `tier=M`、`confirmed=true`；已消费第 6 节接口设计、第 7 节核心流程、第 10 节测试设计、第 13 节回滚与发布策略。 |
| 首次 CP7 失败事实已读取 | PASS | `process/checks/CP7-CR011-S06-industry-market-cap-style-exposure-data-VERIFICATION-DONE.md` | 首次 CP7 结论为 `FAIL`，阻断项为 `CR011-S06-CP7-F01`：缺 canonical top-level `float_market_cap_availability`。 |
| blocker-fix CP6 已通过 | PASS | `process/checks/CP6-CR011-S06-CP7-BLOCKER-FIX-CODING-DONE.md` | frontmatter `status=PASS`；声明已写入 `float_market_cap_availability`，并保留 `float_market_cap` alias。 |
| blocker-fix 调度证据完整 | PASS | `process/handoffs/META-DEV-CR011-S06-CP7-FIX-2026-05-24.md` | `dispatch.mode=spawn_agent`，agent/thread id=`019e58b9-c810-75e2-b93c-cb90dcc60000`，`completed_at` 与 `closed_at` 已回填。 |
| 写入边界受控 | PASS | 本轮命令和写入文件清单 | 未修改生产代码、测试代码、`process/STATE.md`、`process/STORY-STATUS.md`、`process/DEVELOPMENT-PLAN.yaml`、S07/S08、connector/runtime/storage、`data/**`、`.env`、旧报告或 `delivery/**`。 |
| 离线边界受控 | PASS | 命令均设置 `UV_OFFLINE=1` | 未真实联网、未真实 Tushare 抓取、未写真实 lake、未读取或打印凭据、未读取或列出旧 `data/**`。 |

## LLD Consumption

| LLD 输入 | 状态 | 验证入口 | 结论 |
|---|---|---|---|
| 第 6 节接口设计 | PASS | `read_exposure_inputs`、`build_exposure_availability_matrix`、`evaluate_neutralization_claims`、`merge_exposure_claims_into_metadata` | S06 定向测试和源码扫描确认 exposure reader、availability matrix、neutralization gate、metadata merge 接口可用。 |
| 第 7 节核心处理流程 | PASS | fake reader result -> availability matrix -> PIT/as-of gate -> claims gate -> metadata merge | 主路径、缺字段、current snapshot、future availability、上游 PIT gate fail、metric missing 均由定向测试覆盖。 |
| 第 10 节测试设计 | PASS | `tests/test_cr011_exposure_claims.py` | T01-T11 覆盖 PIT exposure available、缺行业、缺市值 / 流通市值、缺 style、current snapshot、as-of、typed missing、CR008 合并、安全边界、PIT gate fail、partial coverage。 |
| 第 13 节回滚与发布策略 | PASS | 离线命令、静态扫描、安全边界计数 | 未触发真实数据、旧报告、凭据、connector/runtime/storage 或 claims 语义覆盖类回滚条件；本次验证仅确认 blocker fix。 |
| frontmatter 强输入 | PASS | LLD frontmatter | `tier=M`、`confirmed=true`、`shared_fragments`、`open_items=4` 已作为验证上下文消费。 |

## 测试策略执行

| 测试设计方法 | 是否执行 | 发现数量 | 说明 |
|---|---|---:|---|
| 等价分区 | PASS | 0 | 覆盖 available、required_missing、source_unresolved、blocked_non_pit、pit_incomplete、metric_missing 等 exposure / claims 分区。 |
| 边界值分析 | PASS | 0 | 复验首次 CP7 字段命名边界：canonical `float_market_cap_availability` 已存在并由测试断言；`float_market_cap` 仅作为 alias。 |
| 状态转换测试 | PASS | 0 | 覆盖 reader result 到 availability matrix、claim gate、metadata merge 的状态转换。 |
| 错误推测 | PASS | 0 | 覆盖 current snapshot、future availability、PIT gate 未通过、缺 neutralized metrics、forbidden import、凭据泄漏和危险命令风险。 |

## ISO 25010 质量评估

| 质量特征 | 优先级 | 评估结果 | 说明 |
|---|---|---|---|
| 功能适合性 | P0 | PASS | 4 类 availability 进入 metadata：`industry_availability`、`market_cap_availability`、`float_market_cap_availability`、`style_exposure_availability`；中性化 / pure alpha blocked claims 逻辑通过。 |
| 可靠性 | P0 | PASS | py_compile、S06 定向 pytest 和相关回归均通过。 |
| 安全性 | P0 | PASS | dangerous-command-scan 等价扫描、forbidden import、禁止路径操作和运行时安全计数均无阻断。 |
| 可维护性 | P1 | PASS | canonical 字段命名与复验 handoff 一致；兼容 alias 明确且由测试覆盖。 |
| 可移植性 | P1 | PASS | Python 3.11 + uv 离线验证可运行；未依赖真实 provider 或本机私有数据。 |
| 易用性 | P2 | PASS | metadata、allowed / blocked claims、known limitations 和安全边界计数均结构化输出。 |
| 兼容性 | P2 | PASS | CR008、CR011-S02、CR011-S05、执行价与 benchmark policy 相关回归通过。 |
| 性能效率 | P3 | PASS | 复验使用小规模 fixture 和静态扫描，未触发真实 lake、外部 provider 或重型风险模型。 |

## 8 维度验收矩阵

| 维度 | 阻断等级 | 状态 | 说明 |
|---|---|---|---|
| 完整性 | BLOCKING | PASS | S06 产物和复验对象均存在：`market_data/readers.py`、`engine/research_dataset.py`、`tests/test_cr011_exposure_claims.py`、Story、LLD、CP6 blocker-fix。 |
| 平台适配 | BLOCKING | PASS | 本地 Python 研究工具；`uv run --python 3.11` 离线语法检查和测试均可执行。 |
| 验收标准覆盖 | BLOCKING | PASS | 首次 CP7 blocker `CR011-S06-CP7-F01` 已关闭；S06 原核心验收项和相关回归均有验证记录。 |
| 安全合规 | BLOCKING | PASS | 网络、真实 lake、凭据、旧数据、旧报告、危险命令、connector/runtime/storage 边界计数均为 0。 |
| 命名规范 | REQUIRED | PASS | canonical top-level 字段为 `float_market_cap_availability`；`float_market_cap` 仅保留为兼容 alias。 |
| Frontmatter 完整性 | REQUIRED | PASS | Story、LLD、首次 CP7、blocker-fix CP6、handoff 均具备可消费 frontmatter。 |
| 可安装性 / 可运行性 | REQUIRED | PASS | 无安装脚本范围；py_compile、定向测试、相关回归和静态扫描通过。 |
| 文档覆盖 | OPTIONAL | SKIP | 当前非 documentation 阶段，且用户禁止写 `delivery/**`；LLD 中历史 `float_market_cap` 描述不阻断本次代码/测试 canonical 字段复验。 |

## Checklist

| # | 检查项 | 状态 | 证据 | 处理意见 |
|---|---|---|---|---|
| 1 | `CR011-S06-CP7-F01` 是否关闭 | PASS | `engine/research_dataset.py:274`、`engine/research_dataset.py:2617`、`tests/test_cr011_exposure_claims.py:75` | canonical `float_market_cap_availability` 已存在，且被 S06 测试覆盖。 |
| 2 | `float_market_cap` alias 不替代 canonical 字段 | PASS | `engine/research_dataset.py:2618`、`tests/test_cr011_exposure_claims.py:76` | alias 等于 canonical 字段，用于兼容；canonical 字段仍为 top-level metadata 主字段。 |
| 3 | 4 类 availability 进入 metadata | PASS | S06 定向测试 `8 passed` + `rg` 精确扫描 | `industry_availability`、`market_cap_availability`、`float_market_cap_availability`、`style_exposure_availability` 均可断言。 |
| 4 | 缺行业阻断行业 claims | PASS | `tests/test_cr011_exposure_claims.py::test_missing_industry_blocks_industry_neutral_claims` | 行业中性、行业归因、行业内 z-score、分行业 IC 均 blocked。 |
| 5 | 缺市值 / 流通市值阻断 size / capacity claims | PASS | `tests/test_cr011_exposure_claims.py::test_missing_float_cap_blocks_size_market_cap_and_capacity_claims` | `market_cap_neutral_ic`、`size_neutral`、`market_cap_weighted_ic`、容量相关 size claim blocked。 |
| 6 | 缺 style exposure 阻断 pure alpha / risk-model claims | PASS | `tests/test_cr011_exposure_claims.py::test_missing_style_blocks_pure_alpha_and_risk_model_claims` | `pure_alpha`、`style_neutral_ic`、`risk_model_adjusted_alpha` blocked，allowed 不含 pure alpha。 |
| 7 | 当前快照、future availability、PIT gate 未通过不得证明 PIT exposure | PASS | `tests/test_cr011_exposure_claims.py::test_current_snapshot_future_asof_and_pit_gate_cannot_prove_pit_exposure` | current snapshot -> `blocked_non_pit`；future availability -> `pit_incomplete`；上游 PIT gate fail -> `blocked_non_pit`。 |
| 8 | 不伪造完整风险模型或中性化指标 | PASS | `tests/test_cr011_exposure_claims.py::test_metric_missing_does_not_fabricate_neutralized_values` | 缺下游 neutralized metrics 时写 `neutralization_metric_missing`，不伪造 risk-model-adjusted alpha。 |
| 9 | CR008 claims 合并不破坏 | PASS | S06 定向测试 + CR008 回归 | `allowed_claims` / `blocked_claims` / `known_limitations` 保持 ordered unique 和结构化合并。 |
| 10 | 相关回归不破坏 | PASS | 相关回归命令 | `55 passed in 2.19s`。 |
| 11 | dangerous-command-scan | PASS | `rg` 危险命令扫描 | 无 `rm -rf`、提权、下载、shell 执行或删除类危险命令命中。 |
| 12 | forbidden import 边界 | PASS | production import scan | `market_data/readers.py`、`engine/research_dataset.py` 无 connector/runtime/storage、联网库、Tushare/AkShare/TickFlow 导入。 |
| 13 | forbidden file / credential boundary | PASS | production forbidden operation scan + S06 forbidden boundary 测试 | 未发现 `.env`、token、旧 `data/**`、旧报告或真实 lake 操作；测试断言 fake secret 不泄漏。 |
| 14 | 写入范围 | PASS | 本 CP7 复验文件 + Story 顶层状态字段 | 未修改生产代码或测试代码；仅写本复验 CP7，并将 Story `status` 推进为 `verified`。 |

## Acceptance Criteria Coverage

| 验收标准 | 状态 | 验证证据 | 说明 |
|---|---|---|---|
| 行业、市值、流通市值、beta/style exposure 4 类 availability 均进入报告 metadata | PASS | `engine/research_dataset.py:2615-2619`、`tests/test_cr011_exposure_claims.py:73-77` | `float_market_cap_availability` 作为 canonical top-level 字段存在；`float_market_cap` 作为 alias 保留。 |
| 缺行业/市值/风格时，对应中性化、pure alpha 声明输出次数为 0 | PASS | S06 定向 pytest | 行业、市值 / 流通市值、style 三类缺失均阻断对应 claims。 |
| 当前快照用于证明 PIT exposure 的次数为 0 | PASS | S06 current snapshot 测试 | `pit_status=non_pit_snapshot` 被标为 `blocked_non_pit`，reason 为 `current_snapshot_not_pit_exposure`。 |
| exposure 缺 effective/available_at 且进入 production_strict 决策的次数为 0 | PASS | S06 current snapshot / future as-of 测试 | 缺 PIT 字段或 future availability 不证明 PIT exposure。 |
| 默认验证路径 `network_calls=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_operations=0` | PASS | S06 forbidden boundary 测试 + 本轮静态扫描 | 四项计数均为 0。 |

## Verification Commands

| 命令 | 状态 | 输出摘要 |
|---|---|---|
| `UV_OFFLINE=1 UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/cr011-s06-reverify-pycache uv run --python 3.11 python -m py_compile engine/research_dataset.py tests/test_cr011_exposure_claims.py` | PASS | 退出码 0，无输出。 |
| `UV_OFFLINE=1 UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/cr011-s06-reverify-pycache uv run --python 3.11 python -m py_compile market_data/readers.py engine/research_dataset.py tests/test_cr011_exposure_claims.py` | PASS | 退出码 0，无输出；补充覆盖 S06 reader 合同文件。 |
| `UV_OFFLINE=1 UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/cr011-s06-reverify-pycache PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr011_exposure_claims.py` | PASS | `8 passed in 1.34s`。 |
| `UV_OFFLINE=1 UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/cr011-s06-reverify-pycache PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr011_adjustment_audit.py tests/test_cr011_pit_universe_lifecycle.py tests/test_cr008_factor_auxiliary_data_contract.py tests/test_cr011_execution_price_policy.py tests/test_cr011_benchmark_policy_consumption.py` | PASS | `55 passed in 2.19s`。 |
| `rg -n "float_market_cap_availability" engine/research_dataset.py tests/test_cr011_exposure_claims.py process/stories/CR011-S06-industry-market-cap-style-exposure-data.md process/stories/CR011-S06-industry-market-cap-style-exposure-data-LLD.md` | PASS | 命中生产代码、测试和 Story 状态说明；LLD 保留历史 `float_market_cap` 描述，本轮不写 LLD。 |
| `rg -n "market_data\\.connectors\|market_data\\.runtime\|market_data\\.storage\|requests\|httpx\|aiohttp\|socket\|tushare\|akshare\|TickFlow\|Tushare\|AkShare" market_data/readers.py engine/research_dataset.py` | PASS | exit code 1，无生产文件命中。 |
| `rg -n "(^|[^A-Za-z0-9_])(rm\\s+-rf\|sudo\|curl\|wget\|ssh\|scp\|mkfs\|dd\\s+if=\|chmod\\s+777\|chown\|eval\\(\|exec\\(\|subprocess\|os\\.system\|shutil\\.rmtree)([^A-Za-z0-9_]|$)" market_data/readers.py engine/research_dataset.py tests/test_cr011_exposure_claims.py process/stories/CR011-S06-industry-market-cap-style-exposure-data.md` | PASS | exit code 1，无命中。 |
| `rg -n "open\\(\|read_text\\(\|write_text\\(\|unlink\\(\|rmdir\\(\|remove\\(\|rmtree\|Path\\([^\\n]*(data\|reports\|delivery)\|reports/experiment_17_21/factor_strategy_report\\.md\|TUSHARE_TOKEN\|\\.env" market_data/readers.py engine/research_dataset.py` | PASS | exit code 1，无生产文件命中。 |
| `rg -n "network_calls\|lake_writes\|credential_reads\|legacy_data_operations\|old_report\|forbidden\|secret\|credential\|\\.env\|TUSHARE_TOKEN" tests/test_cr011_exposure_claims.py engine/research_dataset.py` | PASS | 命中安全计数字段、脱敏敏感词正则和 S06 forbidden boundary 测试；未显示凭据值。 |

## Security Boundary Counts

| 边界 | 状态 | 计数 | 证据 | 说明 |
|---|---|---:|---|---|
| network_calls | PASS | 0 | `tests/test_cr011_exposure_claims.py::test_s06_forbidden_boundaries_are_static_and_no_secret_leakage` + `UV_OFFLINE=1` | 未执行联网命令；生产文件无网络库、provider SDK 或真实 Tushare/AkShare/TickFlow 导入。 |
| lake_writes | PASS | 0 | S06 forbidden boundary 测试 + production forbidden operation scan | 未写真实 lake；复验只读取源码和运行离线 fixture 测试。 |
| credential_reads | PASS | 0 | `.env` / token scan + S06 测试 | 未读取 `.env`、token、密码、私钥、cookie、session；未打印凭据。 |
| legacy_data_operations | PASS | 0 | 用户禁令 + 本轮命令审计 | 未读取、列出、迁移、复制或删除旧 `data/**`。 |
| old_report_operations | PASS | 0 | production forbidden operation scan | 未读取或覆盖 `reports/experiment_17_21/factor_strategy_report.md`。 |
| real_tushare_fetches | PASS | 0 | `UV_OFFLINE=1` + production import scan | 未真实 Tushare 抓取。 |
| forbidden_scope_writes | PASS | 0 | 写入文件清单 | 未写生产代码、测试代码、`process/STATE.md`、`process/STORY-STATUS.md`、`process/DEVELOPMENT-PLAN.yaml`、S07/S08、connector/runtime/storage、`data/**`、`.env`、旧报告或 `delivery/**`。 |
| dangerous_command_findings | PASS | 0 | dangerous-command-scan 等价 `rg` 扫描 | 无破坏性命令、下载、提权、shell 执行或删除类危险命令命中。 |
| connector/runtime/storage imports | PASS | 0 | production import scan | 无 `market_data.connectors`、`market_data.runtime`、`market_data.storage` 导入。 |

## Agent Dispatch Evidence

| 检查项 | 状态 | 证据 | 说明 |
|---|---|---|---|
| blocker-fix 子 agent 调度模式 | PASS | `process/handoffs/META-DEV-CR011-S06-CP7-FIX-2026-05-24.md` | `dispatch.mode=spawn_agent`，非 inline fallback。 |
| blocker-fix agent 标识 | PASS | blocker-fix handoff frontmatter | `agent_name=dev-zhang the 2nd`，agent_id/thread_id=`019e58b9-c810-75e2-b93c-cb90dcc60000`。 |
| blocker-fix 平台工具证据 | PASS | blocker-fix handoff dispatch | `tool_name=spawn_agent`，`spawned_at=2026-05-24T14:43:58+08:00`，`completed_at=2026-05-24T14:47:05+08:00`，`closed_at=2026-05-24T14:49:44+08:00`。 |
| blocker-fix CP6 | PASS | `process/checks/CP6-CR011-S06-CP7-BLOCKER-FIX-CODING-DONE.md` | `status=PASS`，验证命令和安全边界计数已记录。 |
| CP7 复验 handoff | PASS | `process/handoffs/META-QA-CR011-S06-CP7-REVERIFY-2026-05-24.md` | meta-po 已回填 handoff：`dispatch.mode=spawn_agent`，agent/thread id=`019e58c2-6271-7131-adf0-5e026d7680af`，`completed_at=2026-05-24T14:55:35+08:00`，`closed_at=2026-05-24T14:59:28+08:00`。 |
| inline fallback 授权 | N/A | N/A | 本轮未进行生产实现 fallback；仅执行验证与允许范围内的检查结果写入。 |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| BLOCKING 维度全部通过 | PASS | `## 8 维度验收矩阵` | 完整性、平台适配、验收标准覆盖、安全合规均通过。 |
| REQUIRED 维度无未处理失败 | PASS | `## 8 维度验收矩阵` | 命名规范、Frontmatter、可运行性均通过；无豁免项。 |
| `CR011-S06-CP7-F01` 已关闭 | PASS | canonical 字段扫描 + S06 定向测试 | `float_market_cap_availability` 已作为 canonical top-level metadata 字段存在并由测试覆盖；`float_market_cap` alias 不替代 canonical 字段。 |
| 验证命令全部执行 | PASS | `## Verification Commands` | py_compile、S06 定向测试、相关回归、canonical 字段扫描和安全扫描均已执行。 |
| 安全边界计数均为 0 | PASS | `## Security Boundary Counts` | `network_calls=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_operations=0`，旧报告覆盖次数 0。 |
| Story 状态处理 | PASS | `process/stories/CR011-S06-industry-market-cap-style-exposure-data.md` | CP7 复验 PASS 后，Story 顶层 `status` 推进为 `verified`。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| CP7 复验完成检查 | `process/checks/CP7-CR011-S06-industry-market-cap-style-exposure-data-REVERIFY-DONE.md` | PASS | 本文件，结论为 `PASS`。 |
| Story 验证状态字段 | `process/stories/CR011-S06-industry-market-cap-style-exposure-data.md` | PASS | 顶层 `status` 更新为 `verified`。 |

## Defects And Repair Guidance

| 缺陷 ID | 严重度 | 当前状态 | 关闭证据 | 后续建议 |
|---|---|---|---|---|
| `CR011-S06-CP7-F01` | BLOCKING | CLOSED | `engine/research_dataset.py:2617` 写入 `float_market_cap_availability`；`tests/test_cr011_exposure_claims.py:75` 断言 canonical 字段；S06 pytest `8 passed`；相关回归 `55 passed` | 无需回修；后续文档阶段可在允许范围内把 LLD 历史 `float_market_cap` 描述补充为 canonical 字段 + alias 说明。 |

## 结论

- 结论：`PASS`
- 阻断项：0。`CR011-S06-CP7-F01` 已关闭。
- 豁免项：0。
- 安全边界：通过，`network_calls=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_operations=0`、旧报告覆盖次数 0、危险命令高风险项 0。
- 下一步：`CR011-S06-industry-market-cap-style-exposure-data` 可保持 `verified`，由 meta-po 在允许范围内同步全局状态。
