---
version: "3.3"
last_updated: "2026-06-14T13:42:40+08:00"
status: "cr053-closed-current-delivery"
confirmed: true
confirmed_by: "user"
confirmed_at: "2026-05-14"
source_hld: "process/HLD.md"
companion_hld: "process/HLD-DATA-LAKE.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
story_count: 152
wave_count: 70
baseline_story_count: 13
cr004_story_count: 5
cr005_story_count: 6
cr006_story_count: 4
cr007_story_count: 5
cr008_story_count: 6
cr010_story_count: 16
cr011_story_count: 8
cr013_story_count: 4
cr014_story_count: 8
cr015_story_count: 7
cr016_story_count: 7
cr017_story_count: 6
cr018_story_count: 9
cr019_story_count: 10
cr025_story_count: 6
cr030_story_count: 8
cr020_story_count: 6
cr046_story_count: 7
cr051_story_count: 6
cr053_story_count: 5
active_change: "CR-053"
secondary_change: "CR-020/CR-030 legacy"
cr004_status: "draft-pending-cp4"
cr004_confirmed: false
cr005_status: "verified-cp7-pass"
cr005_confirmed: true
cr006_status: "cp5-required-fixes-pending"
cr006_confirmed: true
cr007_status: "story-execution-s01-verified-s02-dev-ready"
cr007_confirmed: true
cr008_status: "draft-pending-cp3-cp4"
cr008_confirmed: false
cr010_status: "remaining-batches-registered-cp4-addendum-approved"
cr010_confirmed: true
cr010_confirmed_by: "user"
cr010_confirmed_at: "2026-05-22T15:09:54+08:00"
cr010_remaining_batches_confirmed_at: "2026-05-22T19:33:44+08:00"
cr010_remaining_batches_approval_source: "user-preauthorized"
cr011_status: "data-batch-a-cp5-approved-story-execution"
cr011_confirmed: true
cr011_confirmed_by: "user"
cr011_confirmed_at: "2026-05-24T08:25:22+08:00"
cr011_lld_batches:
  - "CR011-DATA-BATCH-A"
  - "CR011-RESEARCH-BATCH-B"
  - "CR011-VALIDATION-BATCH-C"
cr013_status: "draft-pending-cp3-cp4"
cr013_lld_batches:
  - "CR013-BATCH-A"
cr014_status: "batch-a-cp5-pending-batch-b-planned"
cr014_lld_batches:
  - "CR014-FULL-HISTORY-LAKE-BATCH-A"
  - "CR014-REAL-RUN-BATCH-B"
cr015_status: "story-plan-cp4-pending"
cr016_status: "story-plan-cp4-pending-later-gated"
cr017_status: "story-plan-cp4-pending"
cr018_status: "story-plan-cp4-pending-cp3"
cr019_status: "story-plan-cp4-pass-pending-lld"
cr025_status: "story-plan-cp4-pass-pending-lld"
cr030_status: "story-plan-cp4-pass-pending-lld"
cr046_status: "story-plan-cp4-pass-pending-lld"
cr046_lld_batch: "CR046-DUAL-TARGET-FRAMEWORK-BATCH-A"
cr051_status: "closed-current-delivery"
cr053_status: "closed-current-delivery"
cr051_lld_batch: "CR051-STRATEGY-RESEARCH-LIFECYCLE-BATCH-A"
cr020_status: "fixture-static-verified-pending-manual-windows-qmt-validation"
cr015_lld_batches:
  - "CR015-QMT-FOUNDATION-BATCH-A"
cr016_lld_batches:
  - "CR016-QMT-ACTIVATION-BATCH-A"
cr017_lld_batches:
  - "CR017-ADJUSTMENT-DUAL-VIEW-BATCH-A"
cr018_lld_batches:
  - "CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A"
cr019_lld_batches:
  - "CR019-STAGE6-QMT-BRIDGE-BATCH-A"
cr025_lld_batches:
  - "CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT-BATCH-A"
cr030_lld_batches:
  - "CR030-MULTIFACTOR-RESEARCH-LOOP-BATCH-A"
cr020_lld_batches:
  - "CR020-QMT-GATEWAY-READONLY-BATCH-A"
cr051_lld_batches:
  - "CR051-STRATEGY-RESEARCH-LIFECYCLE-BATCH-A"
cr053_lld_batches:
  - "CR053-MIGRATION-INVENTORY-BATCH-A"
created_by: "meta-se"
---

# Story Backlog

> STORY-001..013 的基线 Backlog 已由用户确认通过并已验证完成。CR-013 追加的 CR013-S01..S04 当前为 `draft-pending-cp3-cp4`，只能作为 meta-po 发起 CP3/CP4 与后续 CP5 全量 LLD 的规划草案；未经 CP5，不得进入实现。

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 0.1 | 2026-05-14 | meta-se | 按已确认 HLD M0-M4 拆解 13 个 draft Story，并建立 Wave 与依赖 DAG |
| 0.2 | 2026-05-14 | meta-po | 记录 Story Plan 人工确认通过；W0 首个可执行 Story 为 STORY-001 |
| 0.3 | 2026-05-17 | meta-se | 按 CR-004 追加 STORY-014 至 STORY-018 和 CR4-W0 至 CR4-W4；旧 STORY-001..013 verified 状态不改写；CR-004 增量待 CP4 人工确认 |
| 0.4 | 2026-05-17 | meta-se | 按 CR-005 追加 CR005-S01 至 CR005-S06 和 CR5-W0 至 CR5-W5；将 Backtrader 纳入 CR-005 optional backend，强制依赖 dataset schema、quality/catalog/readers 与本地基准契约稳定 |
| 0.5 | 2026-05-17 | meta-se | 按 CR-005 追加修改点修订 CR005-S02/S03/S06：PIT as-of join、`adj_factor` + adjusted price 和 Backtrader 干净 feed 职责边界进入 Story 验收与 dev_gate |
| 0.6 | 2026-05-17 | meta-se | 按 CR-005 第三轮评审修订 CR005-S01/S02/S03/S04/S05/S06：前移 `market_data/cli.py` 或等价 backfill job 所有权，补齐 `BenchmarkResult`、`hs300_index` backfill spec、accuracy/quality AC、proxy_baseline 边界和 CR005-S04/S06 dev_gate |
| 0.7 | 2026-05-18 | meta-se | 按 CR-006 新增 `CR006-S01-legacy-data-dir-config-resolver`、`CR006-S02-engine-experiments-path-migration`、`CR006-S03-docs-runbook-and-cleanup-guardrails`，建立 `CR006-BATCH-A`，明确 legacy flat dir 与 structured lake root 分离、文件所有权、依赖、dev_gate 和禁止真实数据操作 |
| 0.8 | 2026-05-18 | meta-se | 按 CR-006 CP3 前修改意见替换 CR006-S01..S03 并新增 S04：新主线改为 Tushare-first acquisition、canonical/gold 到轻量 engine adapter、Backtrader clean feed contract、旧 `data/` reference-only guardrail；旧 repo `data/` 不作为 fallback 或覆盖证明 |
| 0.9 | 2026-05-18 | meta-se | 处理 CR006-BATCH-A LLD 双 lane review 计划侧 REQUIRED：同步 Tushare-first 权威 AC 映射，闭环 CR005 verified / CP7 PASS 状态，将 S04 计划依赖口径收敛为 contract |
| 1.0 | 2026-05-20 | meta-se | 按 CR-007 新增 CR007-S01..S05 和 `CR007-BATCH-A`：长周期 prices backfill planner、benchmark/calendar backfill、index_members/index_weights/stock_basic readiness、实验十三真实 benchmark 消费、legacy quality report/docs/guardrail；建立全量 LLD 批次和安全边界 |
| 1.1 | 2026-05-21 | meta-se | 按 CR-008 新增 CR008-S01..S06 和 `CR008-BATCH-A`：`research_input_v1`、proxy/real benchmark 字段隔离、research dataset builder、quality/adjustment/label gate、PIT/fixed universe、因子辅助数据合同；CR007-S02 可并行实现，CR007-S04/S05 在 CR008 设计确认前 hold |
| 1.2 | 2026-05-22 | meta-se | 按 CR-010 新增 CR010-S01..S12 与 `CR010-DL-BATCH-A`、`CR010-DL-BATCH-B`、`CR010-QF-BATCH-C`：生产级数据湖 plan/run/normalize/validate/publish/read/revalidate/replay、P0 dataset 生产化、W3 fail-fast、`realism_mode` 与 16 experiments 真实性报告；CR007/CR008/CR009 已验证结论不回滚 |
| 1.3 | 2026-05-22 | meta-po | 按用户给定 CR-010 剩余能力计划登记 `CR010-OPS-BATCH-D` 与 CR010-S13..S16：backup/archive/restore env、backup CLI、restore CLI/drill、retention policy；本轮只更新编排与检查点，不修改代码 |
| 1.4 | 2026-05-23 | meta-se | 按 CR-011 追加 CR011-S01..S08 与 `CR011-DATA-BATCH-A`、`CR011-RESEARCH-BATCH-B`、`CR011-VALIDATION-BATCH-C`：真实 benchmark policy 消费、PIT universe、tradability gates、execution price/VWAP 降级、adjustment audit、industry/market cap/style exposure、liquidity/capacity/cost sensitivity、factor panel audit/robust validation；本轮只补 Story Plan，不生成 LLD / CP3 / CP4 检查点、不实现代码 |
| 1.5 | 2026-05-24 | meta-po | 回写 CR011-DATA-BATCH-A 的 S01..S06 六份 LLD、六份 Story 级 CP5 自动预检和批次人工审查结果；CP5 已由用户 approve，S01 已调度进入 in-development，S02..S06 保持 lld-approved 并等待依赖 / 文件所有权串行调度；仍不授权真实联网、写湖、凭据读取、旧 data 或旧报告覆盖 |
| 1.6 | 2026-05-24 | meta-po | 收敛 CR011-S01 / S02 CP7 PASS / verified 状态；S02 已由 replacement meta-dev/dev-zhang 完成 CP6 接管复核，并由 meta-qa/qa-shi 完成 CP7 PASS；S03 dev_gate 已通过并由 meta-dev/dev-he 开始离线实现 |
| 1.7 | 2026-05-25 | meta-se | 按 CR-013 追加 CR013-S01..S04 与 `CR013-BATCH-A`：full-history readiness gap register、execution/VWAP claim boundary、unsupported register and docs refresh、full-history backfill roadmap；本轮只补 Story Plan 与 CP3/CP4 自动预检，不生成 LLD、不修改 README/docs/代码/测试/报告证据、不执行真实数据操作 |
| 1.8 | 2026-05-27 | meta-se | 按 CR-014 CP3 R2 approved 口径追加 CR014-S01..S08 与 `CR014-FULL-HISTORY-LAKE-BATCH-A`：全 A universe/lifecycle、Parquet layout/manifest/catalog publish gate、P0 plan/run/normalize/validate/publish、DuckDB read-only audit/parity、full-history readiness/claim boundary、incremental refresh/replay/retention、research consumer read-only/docs 后续边界、W3/minute/tick/Level2/VWAP blocked 决策边界；本轮只做 Story Plan 与 CP4，不生成 LLD、不实现、不改依赖、不真实写入 |
| 1.9 | 2026-05-27 | meta-po | 按用户要求将真实 provider 抓取与 raw/manifest 写湖拆分为后续 `CR014-S09-windowed-real-fetch-lake-write-run` 与 `CR014-REAL-RUN-BATCH-B`；S09 只在 S01..S08 完成后进入独立 LLD / CP5 / 用户真实运行授权，按分时段窗口执行，不自动 publish current pointer |
| 2.0 | 2026-05-28 | meta-se | 按 CR-015 / CR-016 / CR-017 CP3 approved 口径追加 20 个 Story 与 8 个增量 Wave：CR017 复权双视图 6 个、CR015 QMT foundation 7 个、CR016 activation / ops 7 个；CR017 raw / policy 合同作为 CR015 raw 执行价隔离前置，CR016 真实激活 / small_live / scale_up 均 later-gated；本轮只做 Story Plan 与 CP4，不生成 LLD、不实现、不真实抓取、不真实写湖、不真实 QMT 操作 |
| 2.1 | 2026-05-29 | meta-se | 按 CR-018 CP2 approved 口径追加 CR018-S01..S09 与 4 个增量 Wave：production current truth scoped release、P0/P1 dataset group、Explicit Publish Gate、release-level rollback、publish 后研究重跑和 QMT 后置；本轮只做设计、ADR、Story Plan 与 CP3/CP4 检查点，不生成 LLD、不实现、不真实抓取、不真实写湖、不 publish current pointer、不启动 QMT |
| 2.2 | 2026-05-30 | meta-se | 按 CR-019 CP3 approved 口径追加 CR019-S01..S10 与 5 个增量 Wave：阶段六 admission、多基准 primary benchmark、QMT C 侧 Python client / 薄 CLI、Windows FastAPI gateway 生命周期、配对式 token/HMAC、完整 endpoint matrix、运行门控、fallback / incident、后置能力 register 与文档 runbook；CP4 自动预检 PASS；本轮只做 Story Plan / CP4，不生成 LLD、不实现、不改依赖、不启动服务、不读凭据、不调用真实 QMT / provider / lake / broker / publish / simulation / live |
| 2.3 | 2026-06-01 | meta-se | 按 CR-025 CP3 approved 口径追加 CR025-S01..S06 与 4 个增量 Wave：clean feed gate / backend selector、semantic diff schema / artifact、`order_intent_draft_v1`、Backtrader module reference/no-copy guardrail、optional runtime boundary、no-real-operation safety、QMT 后续路线衔接和验证策略；CP4 自动预检 PASS；本轮只做 Story Plan / CP4，不生成 LLD、不实现、不改依赖、不运行 Backtrader、不复制 / 裁剪 / 改写 GPLv3 源码、不触发真实 broker / QMT / provider / lake / publish / simulation / live、不读取凭据 |
| 2.3.1 | 2026-06-02 | meta-se | 按 CR-025 CP5 前定位澄清修订 S02 / S04 / S06：Backtrader 只作为 lightweight execution engine 执行语义参考，多因子研究闭环（FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪、策略准入包）另起后续 CR，参考 Qlib / Alphalens / vnpy.alpha；CR025 仍保持 6 Story / 4 Wave / 1 LLD batch |
| 2.4 | 2026-06-03 | meta-se | 按 CR-030 CP3 approved 口径追加 CR030-S01..S08 与 4 个增量 Wave：外部项目矩阵与总合同、FactorSpec / FactorRunSpec、FactorPanel / LabelWindow、单因子评价、多因子组合、ExperimentManifest / ResearchReportCatalog、StrategyAdmissionPackage / `order_intent_draft_v1` handoff、安全验证与文档边界；CP4 自动预检 PASS；本轮只做 Story Plan / CP4，不生成 LLD、不实现、不改依赖、不运行外部项目、不触发 provider/lake/publish/QMT/simulation/live、不读取凭据 |
| 2.5 | 2026-06-05 | meta-se | 按 CR-020 CP3 approved 口径追加 CR020-S01..S06 与 4 个增量 Wave：Windows gateway runtime admission、S 端 QMT login / session ready gate、Linux C 端 REST transport、HMAC pairing / allowlist / scope / nonce fail-closed、`query_positions` 单接口只读准入、docs/runbook 与 CP7 实机只读验收边界；CP4 自动预检 PASS；本轮只做 Story Plan / CP4，不生成 LLD、不实现、不改依赖、不启动 gateway、不绑定端口、不连接 QMT / MiniQMT / XtQuant、不读取真实 `.env`、不输出凭据、不交易、不账户写入、不 simulation/live、不 provider/lake/publish/reports overwrite |
| 2.6 | 2026-06-05 | meta-po | CR020-S01..S06 已完成 CP5 approved、代码 / 文档实现、CP6 PASS 与 CP7 fixture/static PASS；`75 passed`、`py_compile` PASS、`git diff --check` PASS，真实 `.env` 读取、gateway 启动、端口绑定、QMT 连接和真实 `query_positions` 均为 0。当前等待用户按 Windows S 端和 Linux C 端手工安装调试手册执行真实只读验证，CR-020 不关闭、不授权交易 / 账户写入 / simulation/live / provider/lake/publish / 凭据输出 |
| 2.7 | 2026-06-14 | host-orchestrator | 按 CR-051 CP3 approved 口径追加 CR051-S01..S06 与 3 个增量 Wave：策略研究生命周期和 taxonomy、仓库 / 归档 / 数据湖边界、研究主机与交易主机工作流、registry / evidence 合同、后续 CR roadmap、`quant-lab` canonical name 与 `local_backtest` legacy alias；CP4 自动预检 PASS；本轮只做 Story Plan / CP4，不生成 LLD、不实现、不执行目录重命名、不操作 NAS、不运行 QMT / MiniQMT、不 provider/lake/publish、不 git push |
| 2.8 | 2026-06-14 | host-orchestrator | 按 CR-053 CP3 approved 口径追加 CR053-S01..S05 与 3 个增量 Wave：root map / host mapping、repo inventory、path reference dry-run、manifest transfer / backup plan、CR058 migration input；CP4 自动预检 PASS；本轮只做 Story Plan / CP4，不生成 LLD、不实现、不执行 NAS mount / scan / copy / delete、不移动目录、不调整现有 `MARKET_DATA_LAKE_ROOT`、不 git push |
| 2.9 | 2026-06-14 | host-orchestrator | 用户回复“同意”后回填 CR053 CP5 approved：S01-S04 full-lld 与 S05 technical-note 均确认，Story 卡片推进到 `dev-ready`；后续 CP6 仅允许静态 Markdown 报告 / guardrail evidence，不授权真实迁移、NAS 操作、lake 移动、Windows full mount、凭据读取、provider/lake/publish、QMT/MiniQMT runtime 或 git push/tag |
| 3.0 | 2026-06-14 | meta-dev / host-orchestrator | 用户明确授权使用 meta-dev 子 Agent 推进 CR053 CP6；dev-shi 生成五份 `docs/release/*CR053.md` 静态报告、CP6 implementation evidence、CP6 context 和 CP6 自动检查，S01-S05 均进入 `ready-for-verification`；下一步仅允许 CP7 静态验证，不授权真实迁移、NAS、lake、git push、runtime 或凭据读取 |
| 3.1 | 2026-06-14 | meta-qa / host-orchestrator | 用户明确授权使用 meta-qa 子 Agent 推进 CR053 CP7；qa-cao 完成静态验证，生成 verification / test / review / fixes 质量产物、CP7 context 和 CP7 自动检查，S01-S05 均收敛为 `verified`；下一步进入 CP8 release-readiness / close gate，仍不授权真实迁移、NAS、lake、git push、runtime 或凭据读取 |
| 3.2 | 2026-06-14 | meta-qa / host-orchestrator | 用户明确授权使用 meta-qa 子 Agent 推进 CR053 CP8；qa-jin 完成 release-readiness，生成 CR053 专属 release context / release docs / follow-up tracking / CP8 自动预检 / 人工检查点 / human gate message；当前等待用户 approve / 修改 / reject，approve 只关闭静态 dry-run 交付，不授权真实迁移、NAS、lake、git push、runtime、凭据读取或自动启动 CR058/CR060+ |
| 3.3 | 2026-06-14 | host-orchestrator | 用户回复“同意”批准 CR053 CP8；CR053 静态 migration inventory / dry-run 交付关闭为 `closed-current-delivery`，S01-S05 保持 verified；CR058 / CR060+ / data lake migration / trading runtime 仅为后续候选，不自动启动，也不授权真实迁移、NAS、lake、git remote、runtime 或凭据读取 |

## Story 列表

| Story ID | 标题 | 目标 | 范围 | 非范围 | 优先级 | 依赖 | Wave | 量化验收标准摘要 | 需求映射 | HLD 映射 | ADR 映射 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CR053-S01-root-map-and-host-mapping-contract | 迁移 root map 与主机映射合同 | 定义 quant-lab root map、Linux 研究机三分区统一视图、Windows package exchange 窄映射和数据湖 alias 兼容 | `docs/release/NAS-MAPPING-CR053.md` 静态报告合同、root map schema、host map schema | 不执行 mount / scan / mkdir / copy / delete；不替换 `MARKET_DATA_LAKE_ROOT` | P0 | 无 | CR053-W1-MAPPING-INVENTORY | 7 类 root 100% 覆盖；Windows 交易机 full archive mount allowed count=0 | SC-CR053-01..06 | HLD-CR053 §5 | ADR-CR053-001/006/007 |
| CR053-S02-repo-inventory-and-path-classification | Git 内 inventory 与路径分类器 | 设计 repo-local inventory 报告合同，分类路径、owner、artifact class、move_action、risk 和 verification_rule | `docs/release/MIGRATION-INVENTORY-CR053.md` 静态报告合同、forbidden content policy | 不扫 NAS、不扫全部 untracked data、不读 `.env` | P0 | CR053-S01 | CR053-W1-MAPPING-INVENTORY | inventory 必填字段覆盖率 100%；forbidden 操作计数=0 | SC-CR053-01..04 | HLD-CR053 §8 | ADR-CR053-001/004 |
| CR053-S03-path-reference-and-legacy-alias-dry-run | 路径引用与 legacy alias dry-run | 设计 `local_backtest` / legacy env / docs link 引用扫描 dry-run 和 manual-review 合同 | `docs/release/PATH-REFERENCES-CR053.md` 静态报告合同 | 不批量改写历史 process / CR / handoff；不 git history rewrite | P0 | CR053-S02 | CR053-W2-REFERENCE-BACKUP | 引用分类 100% 输出 action；manual-review 项不自动改写 | SC-CR053-02 | HLD-CR053 §8 / §12 | ADR-CR053-004 |
| CR053-S04-manifest-transfer-and-backup-plan | manifest-first transfer 与 backup plan | 设计 transfer manifest、backup plan、restore rehearsal 和数据湖现有备份合同的关系 | `docs/release/BACKUP-PLAN-CR053.md` 静态报告合同 | 不执行真实备份、restore、NAS copy / delete 或 lake migration | P0 | CR053-S01 | CR053-W2-REFERENCE-BACKUP | transfer / backup 字段覆盖率 100%；restore drill 仅为计划状态 | SC-CR053-03..06 | HLD-CR053 §6 / §7 | ADR-CR053-002/003/006 |
| CR053-S05-cr058-migration-input-and-close-gate | CR058 真实迁移输入与关闭门禁 | 聚合 CR053 dry-run 输出，定义 CR058 mechanical move 输入、rollback_ref 和关闭门禁 | `docs/release/MIGRATION-PLAN-CR053.md` 静态报告合同、后续 CR058 / CR059 gate | 不执行真实 move、远端 rename、git push/tag 或 NAS 操作 | P1 | CR053-S02, CR053-S03, CR053-S04 | CR053-W3-MIGRATION-GATE | CR058 输入 5 项前置均齐全；缺任一项 blocked | SC-CR053-06 | HLD-CR053 §15 | ADR-CR053-004 |
| STORY-001 | 工程基线与数据契约骨架 | 建立本地 Python 研究工具的目录、依赖和契约骨架 | `pyproject.toml`、`uv.lock`、`config/`、`engine/`、`strategies/`、`data/`、`reports/`、契约常量/文档内联 | 不实现回测逻辑；不联网 | P0 | 无 | M0 | 目录与文件边界覆盖 100% P0 路径；Python 依赖统一由 uv 管理 | REQ-001, REQ-013, REQ-036 | §3, §5, §6, §16 | ADR-002 |
| STORY-002 | 数据准备节流重试与 manifest | 实现独立联网数据准备编排和 JSONL checkpoint | data_prep 入口、AKShare adapter 边界、节流、重试、退避、断点续传、raw 写入、manifest | 不写回测主路径；不生成策略报告 | P0 | STORY-001 | M0 | 相邻请求间隔 >=2 秒；单批 <=50；并发 <=1；每批 manifest 字段完整 | REQ-016, REQ-047, REQ-048, REQ-049, REQ-050, REQ-051, REQ-055 | §8.1, §8.2, §8.4, §12.1 | ADR-001, ADR-005 |
| STORY-003 | 标准化 parquet 与数据质量报告 | 从 raw 派生三类 parquet，并输出质量报告和降级状态 | normalizer、parquet writer、quality reporter、`pass/warn/fail`、数据新鲜度 | 不实现策略回测；不做自动清理 raw | P0 | STORY-001, STORY-002 | M0 | 三类 parquet schema 校验；质量报告字段覆盖 HLD 列表；缺失率阈值按 ADR-006 处理 | REQ-021, REQ-022, REQ-052, REQ-053, REQ-054, REQ-056, REQ-057 | §8.3, §8.5, §12.1, §12.4 | ADR-003, ADR-006 |
| STORY-004 | 离线 Data Loader 与合同校验 | 让回测主路径只读本地 parquet、manifest、质量报告并校验数据契约 | `engine/data_loader.py`、复权一致、`available_at`、固定股票池、质量状态消费 | 不触发 data_prep；不计算策略信号 | P0 | STORY-003 | M1 | 合规 parquet 返回 `close_df`、universe、calendar、metadata；合同 fail 时拒绝运行 | REQ-002, REQ-003, REQ-016, REQ-034, REQ-037, REQ-038, REQ-057 | §8.3, §9.1, §9.3, §11, §12.2 | ADR-001, ADR-003, ADR-006 |
| STORY-005 | 动量信号与组合成交引擎 | 实现 T 日收盘动量信号、T+1 成交、等权组合和成本扣除 | `strategies/momentum.py`、`engine/portfolio.py`、缺失/不可交易分层处理 | 不输出扫描 CSV；不实现 PIT/涨跌停增强 | P0 | STORY-004 | M1 | 动量剔除历史窗口不足和端点缺失；成交日不早于 T+1；成本三项均记录 | REQ-004, REQ-005, REQ-006, REQ-007, REQ-008, REQ-009, REQ-039, REQ-040 | §9.2, §10, §12.2 | ADR-002, ADR-004 |
| STORY-006 | 指标、单次回测报告与 metadata | 完成默认单次回测编排、绩效指标和限制项 metadata | `engine/backtest.py`、`engine/metrics.py`、报告 builder、默认回测输出 | 不执行 60 组扫描；不生成候选报告 | P0 | STORY-005 | M1 | 2019-2025 合规数据输出完整净值；指标至少 5 项；metadata 限制项全量披露 | REQ-010, REQ-015, REQ-017, REQ-023, REQ-024, REQ-025, REQ-031, REQ-035, REQ-041 | §12.2, §13, §14 | ADR-002, ADR-003, ADR-004, ADR-007 |
| STORY-007 | 60 组参数扫描报告 | 实现动量参数网格扫描并保留失败行 | `engine/scanner.py`、扫描 CSV、失败行、耗时字段、质量摘要 | 不选择聚宽候选；不做并行优化作为验收阻塞 | P0 | STORY-006 | M2 | 默认网格输出 60 行；失败组合不丢行；主路径网络调用为 0 | REQ-011, REQ-012, REQ-026, REQ-027, REQ-032, REQ-034 | §12.3, §13, §16 | ADR-001, ADR-006, ADR-007 |
| STORY-008 | 候选报告与聚宽人工验证模板 | 从扫描结果生成不超过 4 组候选和差异分析字段 | `engine/candidates.py`、候选 CSV、聚宽手动回填字段、方向一致性模板 | 不自动调用聚宽；不轮询平台任务 | P0 | STORY-007 | M2 | 候选数 <=4；覆盖默认、Sharpe 最优、收益最优、保守低换手；选择理由非空 | REQ-018, REQ-028, REQ-029, REQ-030, REQ-041 | §11, §12.3, §16 | ADR-001, ADR-007 |
| STORY-009 | PIT 股票池 Provider 增强契约 | 增量引入按日期可用的历史成分股股票池契约 | PIT provider、成分股 raw/manifest/quality 扩展、loader 按日查询 | 不重构成完整事件驱动框架 | P1 | STORY-008 | M3 | 按日期返回股票池与 `available_at`；偏差字段可量化比较固定池与 PIT 池 | REQ-042, REQ-058 | §17, §14 | ADR-007 |
| STORY-010 | 交易状态与不可交易约束 | 增强停牌、无成交、特殊处理和可交易性判断 | trade status parquet、quality 检查、组合层不可交易规则 | 不实现涨跌停价格约束；不处理事件字段 | P1 | STORY-009 | M3 | 不可交易目标 100% 记录原因；成交明细包含留现金/延后处理 | REQ-043, REQ-058 | §10, §17 | ADR-004, ADR-007 |
| STORY-011 | 涨跌停与事件 available_at 增强 | 增强涨跌停约束和事件级可用时点门控 | limit fields、event `available_at` 契约、数据准备/loader/report 扩展 | 不把财报事件默认加入动量第一版信号 | P1 | STORY-009, STORY-010 | M3 | 涨停买入/跌停卖出受限时拒绝或延后；事件字段缺 `available_at` 时失败 | REQ-044, REQ-045, REQ-058 | §9.3, §10, §17 | ADR-006, ADR-007 |
| STORY-012 | 偏差审计报告 | 输出真实性增强前后的影响审计 | bias audit report、受影响样本数、收益/回撤/换手/候选排序变化 | 不新增交易规则；不自动聚宽验证 | P1 | STORY-010, STORY-011 | M3 | 审计报告覆盖至少 5 类限制项；四类核心指标变化均输出 | REQ-046, REQ-058 | §14, §17 | ADR-007 |
| STORY-013 | 策略扩展接口与 RSI/MACD 示例 | 复用轻量回测层扩展指标型策略接口 | strategy interface、`strategies/rsi.py`、`strategies/macd.py` 示例、横向报告字段 | 不以 Notebook/热力图作为阻塞项；不引入大型框架 | P2 | STORY-008 | M4 | 新策略不修改组合层/指标层主契约；至少 2 个策略函数示例可进入同一报告 schema | REQ-019, REQ-033 | §16, §17 | ADR-002 |
| STORY-014 | CR-004 market_data 包骨架与数据湖契约 | 创建独立可迁移 `market_data/` 包和 raw/manifest/canonical/gold/quality/catalog 契约 | 包骨架、schema registry、source registry、lake layout、配置样例、迁移边界 | 不实现 connector 请求；不改 `engine/**` | P0 | 无 | CR4-W0 | `market_data` 不 import `engine`；6 个数据湖层级有路径契约；canonical/manifest 字段表完整 | CR-004-AC-001, CR-004-AC-003 | §21.1-§21.4 | ADR-008, ADR-011 |
| STORY-015 | CR-004 connector runtime 与 raw/manifest 写入 | 用 fake connector 跑通 plan/fetch/runtime/storage，真实 adapter 默认关闭 | fake connector、TickFlow/AkShare/Tushare adapter 边界、限速、重试、熔断、raw writer、manifest writer | 不写 canonical；不真实联网；不提交凭据 | P0 | STORY-014 | CR4-W1 | fake raw + manifest deterministic；重试次数有上限；熔断可测试；真实 adapter 未启用时 fail fast | CR-004-AC-002, CR-004-AC-003 | §21.3, §21.6, §21.7 | ADR-010, ADR-011 |
| STORY-016 | CR-004 canonical 标准化、质量校验与只读 reader | 从 raw/manifest 派生 canonical parquet、quality、catalog，并提供只读 reader | normalization、validation、quality、catalog、readers | 不调用 connector；不改实验入口 | P0 | STORY-015 | CR4-W2 | canonical schema 稳定；字段缺失/重复/异常价格/覆盖缺口可识别；reader 网络调用为 0 | CR-004-AC-004, CR-004-AC-005 | §21.4, §21.7, §21.8 | ADR-009, ADR-011 |
| STORY-017 | CR-004 CLI offline 闭环与多源比对接口 | 提供 plan/fetch/normalize/validate/read 或等价 CLI，并稳定 fake/reference 多源比对 | CLI、comparison API、offline smoke tests | 不启用真实多源联网比对；不修改 `engine/**` | P0 | STORY-016 | CR4-W3 | CLI offline smoke 通过；多源比对输出字段完整；默认 source 为 fake/offline | CR-004-AC-006, CR-004-AC-007 | §21.7, §21.8 | ADR-010, ADR-012 |
| STORY-018 | CR-004 实验十/十二只读接入与真实沪深 300 基准路线 | 让实验十/十二按 reader 只读接入，并规划真实沪深 300 基准 gold/canonical 路径 | experiments reader adapter、benchmark reader contract、兼容参数、文档化开放问题 | 不在实验入口联网；不抓取真实基准数据；不删除旧 `--data-dir` 路径 | P1 | STORY-016, STORY-017 | CR4-W4 | 实验接入只读 reader；真实基准缺失时结构化提示；旧路径可回退；默认网络调用为 0 | CR-004-AC-008 | §21.7, §21.9, §21.12 | ADR-009, ADR-012 |
| CR005-S01 | Tushare connector 真实写湖边界 | 将 Tushare 从 fail-fast 边界升级为显式启用的真实写湖 source，并冻结 `hs300_index` backfill job spec | `market_data/connectors/tushare.py`、`market_data/config.py`、`market_data/source_registry.py`、`market_data/runtime.py`、`market_data/storage.py`、`market_data/cli.py` 或等价 job、后续 CP5 才能改 `pyproject.toml`/`uv.lock` | 不写 canonical/gold；不改 Data Loader/实验/Backtrader；不提交 token 或真实数据 | P0 | STORY-015 | CR5-W0 | import 网络调用 0；无 token/未启用/未 allowlist 时 100% fail fast；plan/dry-run 不联网；backfill spec 字段覆盖 dataset/source/interface/index_code/date range/lake root/run/resume/path/errors | CR005-AC-001, CR005-AC-002, CR005-AC-015, CR005-AC-016 | §22.1, §22.6, §22.7 | ADR-013 |
| CR005-S02 | Tushare 多 dataset schema、PIT 字段与复权 normalization | 扩展 dataset schema、exact interface 映射、PIT 可得性字段、adjusted price normalization 与 hs300 raw->canonical 字段映射 | `market_data/contracts.py`、`market_data/source_registry.py`、`market_data/normalization.py`、测试 | 不读取真实 token；不改 reader 消费方；不写实验/Backtrader | P0 | CR005-S01, STORY-016 | CR5-W1 | 至少 4 个 P0 dataset 有 schema；`hs300_index` 字段含 benchmark_kind/source_interface/lineage；raw 到 dataset 仅 exact 映射；非行情字段具备 `available_date`/`effective_date`/`available_at`；`adj_factor` 与 adjusted price 口径冲突 fail | CR005-AC-003, CR005-AC-004, CR005-AC-005, CR005-AC-006, CR005-AC-012, CR005-AC-013, CR005-AC-016 | §22.4, §22.6, §22.7 | ADR-014, ADR-017 |
| CR005-S03 | 多 dataset quality/catalog/readers 与 PIT/复权 gate | 为新增 dataset 建立质量门、catalog、只读 reader、PIT as-of gate、复权一致 gate 和 hs300 专项 accuracy gate | `market_data/validation.py`、`market_data/catalog.py`、`market_data/readers.py`、测试 | 不调用 connector；不改实验/Backtrader；不写真实数据 | P0 | CR005-S02 | CR5-W2 | 每个 dataset quality CSV 含 fetch/dataset 双状态、coverage、thresholds、denominator、复现字段；`hs300_index` 记录 missing dates/gap reason/duplicate key/lineage；reader 网络调用 0；PIT as-of 违规和复权口径混用均阻断消费 | CR005-AC-007, CR005-AC-008, CR005-AC-012, CR005-AC-013, CR005-AC-016, CR005-AC-018 | §22.6, §22.8, §22.9 | ADR-014, ADR-017 |
| CR005-S04 | 沪深 300 本地基准与实验只读接入 | 以 `hs300_index` canonical/gold 提供本地 benchmark resolver、`BenchmarkResult` typed schema 和实验只读基准 | `market_data/benchmarks.py`、`experiments/run_experiment_10.py`、`experiments/run_experiment_12.py`、测试 | 不联网抓基准；不自动补数；不静默代理；不把旧 proxy 填充为 hs300 | P0 | CR005-S01, CR005-S03, STORY-018 | CR5-W3 | 基准缺失返回 typed unavailable/required_missing 并携带只读 remediation spec；实验入口网络调用 0；旧 `--data-dir` 仅保留本地价格路径，proxy 只能命名为 `proxy_baseline` | CR005-AC-003, CR005-AC-008, CR005-AC-015, CR005-AC-017, CR005-AC-018, CR005-AC-019 | §22.6, §22.7, §22.8 | ADR-015 |
| CR005-S05 | 多源 comparison 与回补文档 | 稳定 Tushare vs reference/AkShare fixture 比对和显式回补 runbook | `market_data/comparison.py`、`README.md`、`docs/USER-MANUAL.md`、测试 | 不拥有 backfill job 主入口；不启用默认真实多源联网；不写真实数据；不改 Backtrader | P1 | CR005-S03 | CR5-W4 | comparison 至少含 10 个标准字段；默认测试不联网；文档说明显式 backfill、quality/catalog、禁用边界和 proxy_baseline 口径 | CR005-AC-009, CR005-AC-010, CR005-AC-015, CR005-AC-016, CR005-AC-019 | §22.7, §22.9 | ADR-012, ADR-013, ADR-015 |
| CR005-S06 | Backtrader optional backend | 作为可选后端读取数据层已 PIT/复权清洗的 factor panel / score / OHLCV feed 和 BenchmarkResult，并输出对照报告 | `engine/backtest.py` 或 selector、`engine/backtrader_adapter.py`、后续 CP5 才能改 `pyproject.toml`/`uv.lock`、测试、文档 | 不读取 `TUSHARE_TOKEN`；不导入 `market_data.connectors`；不联网；不生成 PIT；不计算复权因子；不触发补数；不替代轻量主路径 | P1 | CR005-S02, CR005-S03, CR005-S04 | CR5-W5 | 未安装返回 backend_unavailable；benchmark unavailable 只报告对照缺失；Backtrader adapter 静态不导入 connector/runtime；hs300 backfill/readers/BenchmarkResult/policy 未稳定时 dev_gate=false | CR005-AC-011, CR005-AC-014, CR005-AC-015, CR005-AC-017, CR005-AC-019 | §22.6, §22.8, §22.12 | ADR-016, ADR-017 |
| CR006-S01-tushare-first-data-acquisition-runbook | Tushare-first 数据获取与 runbook | 冻结 Tushare-first acquisition/runbook、raw/manifest 审计职责、canonical/gold 产出和 no-old-data 采集边界 | `market_data/cli.py` 或等价 job、`market_data/connectors/tushare.py`、`market_data/storage.py`、`market_data/normalization.py`、`market_data/validation.py`、runbook/测试 | 不读取旧 `data/**`；不承诺覆盖旧数据；不由回测运行时触发 fetch；不记录 token 或真实路径 | P0 | CR005-S01, CR005-S02, CR005-S03 | CR006-BATCH-A | raw/manifest 存在但仅用于审计/复现/质量追溯；canonical/gold 可追溯到 manifest run；旧 `data/**` 读取、列出、迁移、复制、比对、删除次数为 0 | CR006-AC-001, CR006-AC-002, CR006-AC-003, CR006-AC-009 | §23.1, §23.4, §23.6, §23.7 | ADR-018 |
| CR006-S02-canonical-gold-lightweight-engine-adapter | canonical/gold 到轻量 engine 适配 | 为当前轻量回测框架定义 canonical/gold reader 或由 canonical/gold 派生的 external `legacy_flat`，替代 repo `data/` 默认 fallback | `engine/data_loader.py`、`engine/backtest.py`、`experiments/run_experiment_*.py`、`market_data/readers.py`、adapter 测试 | 不读取 raw/manifest 作为运行输入；不默认读取 repo `data/`；不改 Tushare fetch | P0 | CR006-S01-tushare-first-data-acquisition-runbook, CR005-S03 | CR006-BATCH-A | 轻量回测运行输入来自 canonical/gold 或带 lineage 的 external `legacy_flat`；quality fail 阻断；repo `data/` 默认消费次数为 0 | CR006-AC-004, CR006-AC-005, CR006-AC-006, CR006-AC-010 | §23.3, §23.4, §23.6, §23.8 | ADR-018 |
| CR006-S03-backtrader-clean-feed-contract | Backtrader clean feed contract | 为 Backtrader optional backend 定义 quality gate 后的 clean OHLCV/factor/score feed 和 unavailable/error contract | `engine/backtrader_adapter.py`、`engine/backtest.py` 或 selector、`market_data/readers.py`、feed contract 测试 | 不读取 Tushare token；不导入 connector/runtime/storage；不读取 raw/manifest；不自动补数；不替代轻量主路径 | P1 | CR006-S01-tushare-first-data-acquisition-runbook, CR006-S02-canonical-gold-lightweight-engine-adapter, CR005-S06 | CR006-BATCH-A | Backtrader feed 只来自 quality gate 后 clean 数据；PIT/复权由数据层完成；未安装返回 backend_unavailable；联网次数为 0；消费层不触发 fetch/backfill | CR006-AC-007, CR006-AC-008, CR006-AC-011 | §23.3, §23.6, §23.8, §23.10 | ADR-016, ADR-017, ADR-018 |
| CR006-S04-old-data-reference-only-guardrail | 旧 data reference-only 护栏 | 固化旧 `data/` 保持现状、仅供人工参考/比对，不作为 fallback、迁移源或覆盖证明 | `README.md`、`docs/USER-MANUAL.md`、`.gitignore`、guardrail 测试或静态检查 | 不读取/列出/迁移/复制/删除真实 `data/**`；不记录真实路径/凭据；不执行清理 | P1 | CR006-S01-tushare-first-data-acquisition-runbook, CR006-S02-canonical-gold-lightweight-engine-adapter, CR006-S03-backtrader-clean-feed-contract | CR006-BATCH-A | 文档与 guardrail 明确 repo `data/` reference-only；默认 fallback 次数为 0；旧数据覆盖性比对需另行授权；S04 只依赖 S02/S03 契约冻结，不等待其 CP6 runtime | CR006-AC-012, CR006-AC-013, CR006-AC-014 | §23.1, §23.4, §23.10, §23.13 | ADR-018 |
| CR007-S01-prices-long-horizon-backfill-planner | 长周期 prices backfill planner | 为 `prices.daily` + `prices.adj_factor` 提供 2015-2025 或用户指定区间的分批 dry-run、resume、coverage gate 和 runbook | `market_data/cli.py`、`market_data/runtime.py`、`market_data/connectors/tushare.py`、`market_data/normalization.py`、`market_data/validation.py`、测试 | 不真实抓取；不写真实 lake；不默认全市场无股票池抓取；不读取旧 `data/**` | P0 | CR006-S01-tushare-first-data-acquisition-runbook, CR005-S02, CR005-S03 | CR007-BATCH-A | dry-run 网络调用 0、写入 0；plan 输出 batch_count、symbols/universe、date slices、resume policy、target paths、coverage gate；旧 `data/**` 操作 0 | CR007-AC-001, CR007-AC-002, CR007-AC-006 | §24.1, §24.5, §24.7 | ADR-019 |
| CR007-S02-benchmark-calendar-backfill | benchmark 与交易日历同区间 backfill | 补齐 `hs300_index` 与 `trade_calendar` 同区间 plan/normalize/validate/catalog/reader，先闭环 2025 小窗口再支持长周期 | `market_data/cli.py`、`market_data/normalization.py`、`market_data/validation.py`、`market_data/catalog.py`、`market_data/readers.py`、`market_data/benchmarks.py`、测试 | 不用代理填充 hs300；不自动联网；不改实验十三消费逻辑 | P0 | CR007-S01-prices-long-horizon-backfill-planner, CR005-S04 | CR007-BATCH-A | coverage denominator 为 trade_calendar open dates；`hs300_index` 与 `prices` 同区间 coverage gap 返回 required_missing；2025 小窗口与长周期计划均可表达 | CR007-AC-003, CR007-AC-004, CR007-AC-007 | §24.1, §24.5, §24.7 | ADR-020 |
| CR007-S03-index-members-stock-basic-datasets | 成分、权重与股票基础信息 readiness | 补齐 `index_members`、`index_weights`、`stock_basic` 的 exact interface、schema、normalizer、quality/catalog/readers 和 PIT / 非 PIT readiness | `market_data/contracts.py`、`market_data/source_registry.py`、`market_data/connectors/tushare.py`、`market_data/normalization.py`、`market_data/validation.py`、`market_data/readers.py`、测试 | 不把 `index_weights` 当作完整成分 PIT；PIT 不完整不得标 available；不改实验报告 | P0 | CR007-S01-prices-long-horizon-backfill-planner, CR005-S02, CR005-S03 | CR007-BATCH-A | 三类 dataset 有 readiness status；PIT 不完整返回 warn/unavailable；reader 不导入 connector/runtime；quality fail 阻断消费 | CR007-AC-005, CR007-AC-008, CR007-AC-009 | §24.1, §24.5, §24.7 | ADR-021 |
| CR007-S04-experiment-real-benchmark-consumption | 实验真实 benchmark 消费 | 修改实验十三优先消费真实 `hs300_index`，复核实验十/十二参数和 metadata，代理仅作 `proxy_baseline` 对照 | `experiments/run_experiment_13.py`、`experiments/run_experiment_10.py`、`experiments/run_experiment_12.py`、`market_data/benchmarks.py`、测试 | 不联网；不自动 backfill；不把 proxy 填充为 hs300；不改数据层抓取 | P0 | CR007-S02-benchmark-calendar-backfill, CR007-S03-index-members-stock-basic-datasets | CR007-BATCH-A | 真实 benchmark available 且 coverage=1.0 时实验十三输出 hs300 metadata；缺失时只输出 proxy_baseline 和 missing reason；网络调用 0 | CR007-AC-010, CR007-AC-011 | §24.7, §24.8 | ADR-020, ADR-021 |
| CR007-S05-data-quality-report-and-doc-guardrail | 质量报告与文档护栏 | 把旧 `reports/data_quality_report.csv` 标记为 legacy，文档化 lake quality/catalog 当前真相源，扩展 no-old-data / no-legacy-report guardrail | `README.md`、`docs/USER-MANUAL.md`、`.gitignore`、guardrail 测试 | 不覆盖旧报告；不读取旧报告内容；不操作旧 `data/**`；不执行真实抓取 | P1 | CR007-S01-prices-long-horizon-backfill-planner, CR007-S02-benchmark-calendar-backfill, CR007-S03-index-members-stock-basic-datasets, CR007-S04-experiment-real-benchmark-consumption | CR007-BATCH-A | 文档明确旧质量报告 legacy；当前质量真相源为 lake quality/catalog；禁止旧报告作为 coverage 证明；静态 guardrail 覆盖相关短语 | CR007-AC-012, CR007-AC-013 | §24.7, §24.10, §24.13 | ADR-022 |
| CR008-S01-research-input-contract-and-report-metadata | research input 合同与报告 metadata | 定义 `research_input_v1`、新报告必填 metadata 和 legacy report 边界 | `engine/research_dataset.py` 或合同模块、`experiments/**` 报告 helper、测试 | 不实现真实数据抓取；不读取旧报告内容；不触发 backfill | P0 | CR007-S02-benchmark-calendar-backfill | CR008-BATCH-A | metadata 必填字段覆盖 coverage、benchmark、universe、adjustment、label window、quality/readiness、known limitations；旧报告 current truth 使用次数为 0 | CR008-AC-001, CR008-AC-002 | §25.1, §25.4, §25.7 | ADR-024 |
| CR008-S02-proxy-real-benchmark-field-separation | proxy / real benchmark 字段隔离 | 将代理 benchmark 与真实 `hs300_index` 字段拆分，并修订新报告字段语义 | `experiments/run_experiment_13.py`、`experiments/run_experiment_15_factor_framework.py`、`market_data/benchmarks.py`、测试 | 不改数据生产；不以 proxy 填充 hs300；不读取旧报告 | P0 | CR007-S02-benchmark-calendar-backfill, CR008-S01-research-input-contract-and-report-metadata | CR008-BATCH-A | 缺真实 benchmark 时 `hs300_*` 输出次数为 0；proxy 只写 `proxy_*` / `proxy_baseline`；missing reason 必填 | CR008-AC-003, CR008-AC-004 | §25.3, §25.7, §25.13 | ADR-025 |
| CR008-S03-research-dataset-builder | 统一 research dataset builder | 新增只读 `ResearchDatasetRequest` / `ResearchDataset` / `GateResult` builder，聚合价格、日历、benchmark、universe 和 metadata | `engine/research_dataset.py`、`engine/data_loader.py`、`market_data/readers.py`、测试 | 不导入 connector/runtime/storage；不触发 fetch/backfill；不读取旧 `data/**` | P0 | CR008-S01-research-input-contract-and-report-metadata, CR008-S02-proxy-real-benchmark-field-separation | CR008-BATCH-A | builder 消费路径网络调用 0；forbidden import 0；missing 只返回 typed result / remediation spec | CR008-AC-005, CR008-AC-006 | §25.4, §25.5, §25.7 | ADR-026 |
| CR008-S04-quality-adjustment-label-window-gates | 质量、复权与 label window gate | 将 quality、单一复权口径和 `forward_return_horizon` 标签窗口变成研究准入门 | `engine/research_dataset.py`、`engine/quality.py` 或 gate helper、测试 | 不覆盖 quality 报告；不读取旧 quality CSV；不静默截断样本 | P0 | CR008-S03-research-dataset-builder | CR008-BATCH-A | quality fail、复权混用、label window 不足在严肃研究中 fail；探索截断必须写 `label_available_end` 和截断数量 | CR008-AC-007, CR008-AC-008 | §25.8, §25.10 | ADR-028 |
| CR008-S05-pit-universe-consumption-contract | PIT / fixed universe 消费合同 | 定义 `universe_mode`、`is_pit_universe`、`pit_status` 和幸存者偏差披露 | `engine/universe.py`、`engine/research_dataset.py`、`market_data/readers.py`、测试 | 不把 `index_weights` 当完整成分；不把 fixed snapshot 标 PIT；不改真实抓取 | P0 | CR007-S03-index-members-stock-basic-datasets, CR008-S03-research-dataset-builder | CR008-BATCH-A | 严肃研究要求 PIT 时 unavailable 必须 fail；探索 fixed snapshot 必须输出 survivorship warning | CR008-AC-009, CR008-AC-010 | §25.8, §25.13 | ADR-027 |
| CR008-S06-factor-research-auxiliary-data-contract | 因子研究辅助数据合同 | 定义可交易性、OHLCV/VWAP、行业、市值、复权审计、流动性和风格暴露缺失时的 allowed claims | `engine/research_dataset.py`、`market_data/readers.py`、`experiments/run_experiment_15_factor_framework.py`、测试 | 不授权新增真实辅助数据抓取；不声明未控制的中性化或可交易结论 | P1 | CR008-S03-research-dataset-builder, CR008-S04-quality-adjustment-label-window-gates, CR008-S05-pit-universe-consumption-contract | CR008-BATCH-A | 缺行业/市值/可交易性/风格暴露时对应严肃结论输出次数为 0；limitations/allowed_claims 必填 | CR008-AC-011, CR008-AC-012 | §25.5, §25.9, §25.13 | ADR-029 |
| CR010-S01-multidataset-plan-run-publish-cli-contract | multi-dataset plan/run/publish CLI 合同 | 建立 plan/run/normalize/validate/publish/read/revalidate/replay 生命周期与 publish gate | `market_data/cli.py`、`market_data/catalog.py`、`market_data/runtime.py`、`market_data/storage.py`、测试 | 不真实联网；不写真实 lake；不读取旧 `data/**` | P0 | CR009 closed, CR007-S01, CR007-S02 | CR010-DL-BATCH-A | dry-run 网络调用 0；未 publish 不可作为 current truth；publish 记录 coverage/source/run/lineage/available_at_rule | CR010-AC-001, CR010-AC-002 | `process/HLD-DATA-LAKE.md` §3, §5 | ADR-030, ADR-031, ADR-034, ADR-035 |
| CR010-S02-prices-adj-factor-history-backfill-loop | prices + adj_factor 历史回补闭环 | 补齐 `prices` 与 `adj_factor` 的 P0 字段、`available_at_rule`、复权一致性与恢复策略 | `market_data/contracts.py`、`market_data/normalization.py`、`market_data/validation.py`、测试 | 不执行全历史真实抓取；不在 consumer 计算复权 | P0 | CR010-S01-multidataset-plan-run-publish-cli-contract | CR010-DL-BATCH-A | `prices` / `adj_factor` 字段齐全；同一 run 不混用 `adjustment_policy`；缺 `adj_factor` 时 production_strict fail | CR010-AC-003, CR010-AC-004 | `process/HLD-DATA-LAKE.md` §4, §6 | ADR-032, ADR-035 |
| CR010-S03-hs300-index-trade-calendar-backfill-loop | hs300_index + trade_calendar 回补闭环 | 补齐 benchmark 与交易日历同区间 quality、coverage denominator、publish/read 合同 | `market_data/normalization.py`、`market_data/validation.py`、`market_data/benchmarks.py`、测试 | 不用 proxy 填充 hs300；不自动联网 | P0 | CR010-S01-multidataset-plan-run-publish-cli-contract, CR007-S02-benchmark-calendar-backfill | CR010-DL-BATCH-A | coverage denominator 使用 `trade_calendar.is_open=true`；缺 benchmark 返回 required_missing / benchmark_unavailable | CR010-AC-005, CR010-AC-006 | `process/HLD-DATA-LAKE.md` §4, §5 | ADR-032, ADR-034 |
| CR010-S04-index-members-weights-stock-basic-readiness | index_members / index_weights / stock_basic readiness 强化 | 强化 PIT/readiness/status 字段、source/interface exact 和禁止替代规则 | `market_data/contracts.py`、`market_data/source_registry.py`、`market_data/normalization.py`、`market_data/readers.py`、测试 | 不把 `index_weights` 或 `stock_basic` 当前快照证明 PIT | P0 | CR010-S01-multidataset-plan-run-publish-cli-contract, CR007-S03-index-members-stock-basic-datasets | CR010-DL-BATCH-A | PIT 不完整返回 warn/unavailable；`index_members` 缺失时 production_strict fail；stock_basic 仅辅助 | CR010-AC-007, CR010-AC-008 | `process/HLD-DATA-LAKE.md` §4, §7 | ADR-033, ADR-034 |
| CR010-S05-catalog-coverage-production-readiness-report | catalog coverage 与 production readiness report | 输出统一 coverage/readiness/current truth report，区分 legacy quality report | `market_data/catalog.py`、`market_data/validation.py`、`market_data/readers.py`、报告 helper、测试 | 不覆盖旧 `reports/data_quality_report.csv`；不记录私有路径/token | P0 | CR010-S01, CR010-S02, CR010-S03, CR010-S04 | CR010-DL-BATCH-A | report 覆盖 dataset coverage、quality/readiness、PIT、lineage、known_limitations；legacy report 不作为 current truth | CR010-AC-009 | `process/HLD-DATA-LAKE.md` §5, §8 | ADR-034, ADR-035 |
| CR010-S06-pit-source-interface-spike-readiness | PIT source/interface Spike 与 readiness 加固 | 对 PIT exact source/interface 做 Spike 记录，未确认前保持 unresolved fail-fast | `market_data/source_registry.py`、`market_data/contracts.py`、`market_data/readers.py`、测试 | 不真实启用 provider；不把 Spike 结论直接标 production available | P1 | CR010-S04-index-members-weights-stock-basic-readiness | CR010-DL-BATCH-B | 未确认 source/interface 返回 source_unresolved / required_missing；不允许模糊匹配 | CR010-AC-010 | `process/HLD-DATA-LAKE.md` §4.2, §7 | ADR-033 |
| CR010-S07-trade-status-contract-reader-fail-fast | trade_status 合同 / reader / fail-fast | 定义 `trade_status` dataset contract、reader result 和 production_strict gate | `market_data/contracts.py`、`market_data/readers.py`、`engine/trade_status.py`、测试 | 不默认全可交易；不自动抓取交易状态 | P1 | CR010-S06-pit-source-interface-spike-readiness | CR010-DL-BATCH-B | source/interface 未确认时 required_missing；exploratory 写 limitation；production_strict fail | CR010-AC-011 | `process/HLD-DATA-LAKE.md` §4.2, §7 | ADR-033 |
| CR010-S08-prices-limit-contract-gate-fail-fast | prices_limit 合同 / trading constraint gate / fail-fast | 定义涨跌停 dataset contract、reader result 和交易约束 gate | `market_data/contracts.py`、`market_data/readers.py`、`engine/trading_constraints.py`、测试 | 不忽略涨跌停后声明真实可成交；不自动抓取 | P1 | CR010-S06-pit-source-interface-spike-readiness | CR010-DL-BATCH-B | 未确认 source/interface 时 required_missing；production_strict 缺失 fail | CR010-AC-012 | `process/HLD-DATA-LAKE.md` §4.2, §7 | ADR-033 |
| CR010-S09-events-available-at-contract-fail-fast | events 合同 / available_at gate / fail-fast | 定义 events dataset contract，缺 explicit `available_at` 时禁止进入决策 | `market_data/contracts.py`、`market_data/readers.py`、`engine/events.py`、测试 | 不用日期推导事件可用时点；不自动抓取事件 | P1 | CR010-S06-pit-source-interface-spike-readiness | CR010-DL-BATCH-B | events 缺 `available_at` fail；reader/engine gate 均不返回 available | CR010-AC-013 | `process/HLD-DATA-LAKE.md` §4.2, §4.3 | ADR-032, ADR-033 |
| CR010-S10-realism-mode-research-metadata | 统一 `realism_mode` 与 research metadata | 在研究/实验 metadata 中引入 `realism_mode=exploratory/production_strict` 和真实性状态 | `engine/research_dataset.py`、`experiments/reporting.py`、测试 | 不替代现有 `analysis_mode`；不把 exploratory 报告说成 production_strict | P0 | CR010-S05-catalog-coverage-production-readiness-report, CR010-S07, CR010-S08, CR010-S09 | CR010-QF-BATCH-C | exploratory 默认可运行但写 limitation；production_strict 对缺 PIT/W3/benchmark/复权/quality fail 正确 fail | CR010-AC-014 | `process/HLD.md` §26, `process/HLD-DATA-LAKE.md` §7 | ADR-031, ADR-032, ADR-033 |
| CR010-S11-experiments-smoke-limitation-matrix | 16 experiments 真实数据 smoke 与 limitation matrix | 输出每个 experiment 的 coverage、benchmark、universe、adjustment、quality/readiness、W3、claims 和 strict 可行性 | `experiments/**`、`experiments/reporting.py`、测试 | 不触发 backfill；真实 lake smoke 需用户授权 | P0 | CR010-S10-realism-mode-research-metadata | CR010-QF-BATCH-C | 16 个 experiments fixture/offline smoke 可跑；每个报告有 allowed_claims / blocked_claims / production_strict status | CR010-AC-015 | `process/HLD.md` §26, `process/HLD-DATA-LAKE.md` §7 | ADR-031, ADR-034 |
| CR010-S12-backtrader-vectorbt-clean-feed-boundary | Backtrader / VectorBT clean feed 边界回归 | 回归 optional backend / scanner accelerator 只读 clean feed，静态禁止生产层 import | `engine/backtrader_adapter.py`、可选 VectorBT adapter、`engine/research_dataset.py`、测试 | 不引入新默认后端；不触发补数或真实源 | P1 | CR010-S10-realism-mode-research-metadata | CR010-QF-BATCH-C | Backtrader/VectorBT 消费路径网络调用 0；缺数据返回 typed unavailable；clean feed lineage 完整 | CR010-AC-016 | `process/HLD.md` §26, `process/HLD-DATA-LAKE.md` §7 | ADR-031, ADR-034 |
| CR010-S13-backup-archive-restore-env-manifest-contract | backup/archive/restore env 与 manifest/checksum/脱敏契约 | 定义 hot/archive/backup/restore root、backup/restore manifest、checksum、报告脱敏和路径冲突 fail-fast | `market_data/cli.py`、`market_data/storage.py`、备份/恢复 manifest helper、测试 | 不执行真实备份或恢复；不打印 `.env`、token、NAS 凭据或真实私有路径 | P0 | CR010-S05-catalog-coverage-production-readiness-report | CR010-OPS-BATCH-D | 四类 root 均可配置；`restore-root==lake-root` fail-fast；checksum skip/mismatch fail；报告路径脱敏 | CR010-AC-017 | `process/HLD-DATA-LAKE.md` §8 | ADR-034, ADR-035 |
| CR010-S14-backup-cli-dry-run-execute-verify-report | backup CLI dry-run / execute / verify / report | 新增 `backup-plan`、`backup-run`、`backup-verify`、`backup-report`，默认 dry-run，`--execute` 才复制 | `market_data/cli.py`、backup helper、测试 | 不默认复制真实数据；不读取旧 `data/**`；不记录私有路径 | P0 | CR010-S13-backup-archive-restore-env-manifest-contract | CR010-OPS-BATCH-D | dry-run 复制次数为 0；execute 需要显式 flag；verify/report 校验 manifest 与 checksum，输出脱敏报告 | CR010-AC-018 | `process/HLD-DATA-LAKE.md` §8 | ADR-035 |
| CR010-S15-restore-cli-drill-read-revalidate-replay | restore CLI 与 restore drill | 新增 `restore-plan`、`restore-run`、`restore-drill`，drill 只读执行 read/revalidate/replay | `market_data/cli.py`、restore helper、reader/revalidate/replay 集成、测试 | 不覆盖 hot lake；不联网；不把 restore root 与 lake root 指向同一目录 | P0 | CR010-S13-backup-archive-restore-env-manifest-contract, CR010-S14-backup-cli-dry-run-execute-verify-report | CR010-OPS-BATCH-D | `restore-root==lake-root` fail-fast；restore-drill `network_calls=0`；read/revalidate/replay 全部基于恢复副本 | CR010-AC-019 | `process/HLD-DATA-LAKE.md` §8 | ADR-034, ADR-035 |
| CR010-S16-retention-policy-archive-backup-cleanup | retention policy 与 archive/backup cleanup | 定义 archive/backup retention policy、过期对象计划、manifest/checksum 校验和 dry-run cleanup report | retention helper、`market_data/cli.py`、测试 | 不默认删除真实数据；不绕过 manifest；不清理旧 `data/**` | P1 | CR010-S13-backup-archive-restore-env-manifest-contract | CR010-OPS-BATCH-D | retention 计划默认 dry-run；delete 需要显式 `--execute`；checksum 缺失或 mismatch 阻断清理 | CR010-AC-020 | `process/HLD-DATA-LAKE.md` §8 | ADR-035 |
| CR011-S01-real-benchmark-and-policy-consumption | 真实 benchmark 与 policy 消费 | 让实验 17-21 v2 只读 `hs300_index` / benchmark policy，并严格隔离 `hs300_*` 与 `proxy_*` 字段 | `market_data/benchmarks.py`、`engine/research_dataset.py`、`experiments/run_experiment_17_21_factor_suite.py`、新版报告 metadata | 不自动抓取 benchmark；不覆盖旧报告；不用 proxy 填充 `hs300_*` | P0 | CR010-S03-hs300-index-trade-calendar-backfill-loop, CR010-S05-catalog-coverage-production-readiness-report, CR008-S02-proxy-real-benchmark-field-separation | CR011-DATA-BATCH-A | 输出 `benchmark_policy_id/benchmark_kind/hs300_available/hs300_coverage_ratio/proxy_baseline_used/benchmark_missing_reason` 6 字段；proxy 写入 `hs300_*` 次数为 0 | CR011-AC-001 | `process/HLD.md` §27, `process/HLD-DATA-LAKE.md` §14 | ADR-036 |
| CR011-S02-pit-universe-and-stock-lifecycle-completion | PIT 股票池与股票生命周期 | 基于 PIT membership、权重和生命周期字段建立 as-of universe gate | `market_data/readers.py`、`engine/research_dataset.py`、universe gate helper、新版报告 metadata | 不用 `index_weights` 或 `stock_basic` 当前快照证明 PIT；不真实补数 | P0 | CR010-S04-index-members-weights-stock-basic-readiness, CR010-S06-pit-source-interface-spike-readiness, CR008-S05-pit-universe-consumption-contract | CR011-DATA-BATCH-A | production_strict 必须满足 `universe_mode=pit`、`is_pit_universe=true`、`pit_status=pass`、`as_of_join_violation_count=0` | CR011-AC-002 | `process/HLD.md` §27, `process/HLD-DATA-LAKE.md` §14 | ADR-037 |
| CR011-S03-tradability-status-and-price-limit-gates | 可交易性与涨跌停门控 | 将停牌、涨跌停、ST、无成交、上市天数、事件状态纳入因子策略 gate | `market_data/readers.py`、`engine/trade_status.py`、`engine/trading_constraints.py`、`engine/events.py`、`engine/research_dataset.py` | 不默认全可交易；不接真实 provider；不忽略 W3 missing | P0 | CR011-S02-pit-universe-and-stock-lifecycle-completion, CR010-S07-trade-status-contract-reader-fail-fast, CR010-S08-prices-limit-contract-gate-fail-fast, CR010-S09-events-available-at-contract-fail-fast | CR011-DATA-BATCH-A | 6 类 gate 均输出 `available / required_missing / blocked`；production_strict 缺任一 P0 gate 时通过次数为 0；上市天数 / lifecycle gate 消费 CR011-S02 合同，未冻结时返回 `required_missing` | CR011-AC-003 | `process/HLD.md` §27, `process/HLD-DATA-LAKE.md` §14 | ADR-038 |
| CR011-S04-ohlcv-vwap-clean-execution-feed | OHLCV / VWAP 干净执行 feed | 定义 `open/close/vwap/close_proxy` 执行价 policy 和 VWAP 缺失降级合同 | `market_data/readers.py`、`engine/research_dataset.py`、`engine/backtest.py` 或 execution policy helper、报告 metadata | 不实现分钟级撮合；不把 close proxy 声明为 VWAP；不自动推导真实 VWAP | P1 | CR011-S03-tradability-status-and-price-limit-gates, CR010-S02-prices-adj-factor-history-backfill-loop | CR011-DATA-BATCH-A | `execution_price_policy` 只允许 4 值；`close_proxy` 时 `execution_degradation_reason` 必填且真实 VWAP/真实成交声明为 0 | CR011-AC-004 | `process/HLD.md` §27, `process/HLD-DATA-LAKE.md` §14 | ADR-039 |
| CR011-S05-adjustment-and-corporate-action-audit | 复权与公司行动审计 | 将 `adj_factor` lineage、复权一致性和 corporate action availability 纳入研究 metadata | `market_data/readers.py`、`engine/research_dataset.py`、factor return input helper、报告 metadata | 不声明缺公司行动时完整审计；不混用复权口径；不覆盖旧报告 | P1 | CR010-S02-prices-adj-factor-history-backfill-loop, CR008-S04-quality-adjustment-label-window-gates | CR011-DATA-BATCH-A | `adjustment_policy/adj_factor_lineage/corporate_action_status/adjustment_audit_status` 4 字段必填；复权混用进入因子计算次数为 0 | CR011-AC-005 | `process/HLD.md` §27, `process/HLD-DATA-LAKE.md` §14 | ADR-040 |
| CR011-S06-industry-market-cap-style-exposure-data | 行业 / 市值 / 风格暴露 | 定义行业、市值、流通市值、beta/style exposure availability 和中性化 blocked claims | `market_data/readers.py`、`engine/research_dataset.py`、factor analysis metadata、报告 metadata | 不用当前快照支撑 PIT exposure；不实现完整风险模型平台 | P1 | CR008-S06-factor-research-auxiliary-data-contract, CR011-S02-pit-universe-and-stock-lifecycle-completion | CR011-DATA-BATCH-A | 缺行业/市值/风格时，对应行业中性、市值中性、风格中性、pure alpha 声明输出次数为 0 | CR011-AC-006 | `process/HLD.md` §27, `process/HLD-DATA-LAKE.md` §14 | ADR-041 |
| CR011-S07-liquidity-capacity-and-cost-sensitivity | 流动性 / 容量 / 成本敏感性 | 基于 amount、volume、turnover、ADV 或等价输入输出容量与成本敏感性报告 | `engine/research_dataset.py`、`engine/portfolio.py` 或 capacity helper、`experiments/run_experiment_17_21_factor_suite.py`、新版报告 | 不声明缺流动性时容量可行；不只输出单一成本点 | P1 | CR011-S03-tradability-status-and-price-limit-gates, CR011-S04-ohlcv-vwap-clean-execution-feed, CR011-S06-industry-market-cap-style-exposure-data | CR011-RESEARCH-BATCH-B | 固定输出 `[0,5,10,20]` bps 四档成本网格；容量报告包含成交额占比、换手、持仓数、样本损失、成本侵蚀 5 类字段 | CR011-AC-007 | `process/HLD.md` §27, `process/HLD-DATA-LAKE.md` §14 | ADR-042 |
| CR011-S08-factor-panel-audit-and-robust-validation | 因子审计面板与稳健性验证 | 版本化保存 raw/directional/winsorized/zscore factor panel，并输出 rolling/年度/市场状态/参数/成本稳健性 | `experiments/run_experiment_17_21_factor_suite.py`、factor panel writer、robust validation helper、`reports/experiment_17_21_cr011/**` | 不覆盖旧 `reports/experiment_17_21/factor_strategy_report.md`；不生成 LLD 或代码于本轮 | P1 | CR011-S01-real-benchmark-and-policy-consumption, CR011-S02-pit-universe-and-stock-lifecycle-completion, CR011-S05-adjustment-and-corporate-action-audit, CR011-S07-liquidity-capacity-and-cost-sensitivity | CR011-VALIDATION-BATCH-C | 四阶段 factor panel 均存在；稳健性报告包含 rolling、年度、市场状态、参数敏感性、成本敏感性 5 个视图；旧报告覆盖次数为 0 | CR011-AC-008 | `process/HLD.md` §27, `process/HLD-DATA-LAKE.md` §14 | ADR-043 |
| CR013-S01-full-history-readiness-gap-register | full-history readiness gap register | 固化 2020-2024 10 个正式 dataset 的 `limited_window_only`、target-window coverage 缺口、remediation 和 evidence paths | `reports/data_lake_readiness_2020_2024/readiness_summary.md`、`reports/data_lake_readiness_2020_2024/readiness_matrix.csv` 的只读消费合同；后续版本化 gap register 输出 | 不补真实数据；不写 lake；不覆盖旧报告；不读取旧 `data/**` | P0 | CR011-S08-factor-panel-audit-and-robust-validation | CR013-BATCH-A | 10 个 dataset 100% 进入 gap register；full-history production strict allowed claim 输出次数为 0；旧证据覆盖次数为 0 | REQ-083, REQ-087 | `process/HLD.md` §29, `process/HLD-DATA-LAKE.md` §16 | ADR-044, ADR-047 |
| CR013-S02-execution-vwap-claim-boundary | execution / VWAP claim boundary | 将真实 VWAP、VWAP fill、分钟 / 逐笔 / 盘口 / 撮合执行价保持 blocked，并定义解除条件 | `reports/data_lake_readiness_2020_2024/execution_price_audit.csv` 的只读消费合同、execution blocked claim summary | 不从 close proxy、`amount/volume` 或其他日频字段派生真实 VWAP；不构造伪分钟数据 | P0 | CR011-S04-ohlcv-vwap-clean-execution-feed | CR013-BATCH-A | `blocked_claims` 包含 `real_vwap_execution` 和 `vwap_fill_claim`；真实 VWAP / 分钟执行价 allowed claim 输出次数为 0 | REQ-084, REQ-086 | `process/HLD.md` §29, `process/HLD-DATA-LAKE.md` §16 | ADR-045, ADR-047 |
| CR013-S03-unsupported-register-and-doc-refresh | unsupported register and docs refresh | 把 unsupported register 的 research-only / unsupported / contract-supported-but-unavailable 项纳入 README / USER-MANUAL / report 声明合同 | `reports/data_lake_readiness_limited_2025_2026/unsupported_data_register.csv` 的只读消费合同、文档刷新目标文件边界、report summary schema | 本轮不修改 README.md 或 docs/USER-MANUAL.md；不把 excluded 项计入 pass 分母；不修改研究策略逻辑 | P0 | CR013-S01-full-history-readiness-gap-register, CR013-S02-execution-vwap-claim-boundary | CR013-BATCH-A | 9 行 register 100% 进入 supported / research-only / unsupported / blocked 摘要；`pass_denominator=excluded` 计入 formal pass 分母次数为 0 | REQ-085, REQ-086, REQ-087 | `process/HLD.md` §29, `process/HLD-DATA-LAKE.md` §16 | ADR-046, ADR-047 |
| CR013-S04-full-history-backfill-roadmap | full-history backfill roadmap | 制定 2020-2024 full-history 补数、复验、发布、证据保留和权限授权路线图 | S01/S02/S03 输出、REQ-083..087、ADR-044..047；后续 Story / CP5 授权点 | 不执行 provider fetch；不读取凭据；不写 `/mnt/ugreen-data-lake`；不读取旧 `data/**`；不生成真实执行命令 | P1 | CR013-S01-full-history-readiness-gap-register, CR013-S02-execution-vwap-claim-boundary | CR013-BATCH-A | 路线图列出 10 个 dataset 补齐、execution/VWAP 解除条件、新 run/report 命名、old_baseline_preserved 和授权门；真实操作计数均为 0 | REQ-083, REQ-084, REQ-086, REQ-087 | `process/HLD.md` §29, `process/HLD-DATA-LAKE.md` §16 | ADR-044, ADR-045, ADR-047 |
| CR014-S01-a-share-universe-lifecycle-contract | 全 A universe / lifecycle / code-change 合同 | 冻结全 A since-inception universe、最近已闭市交易日、退市/摘牌/代码变更和 coverage denominator 合同 | lifecycle schema、code-change mapping、calendar policy、required_missing / blocked_claims 合同；Story 卡片与 LLD 输入 | 不抓 provider；不读凭据；不写 lake；不修改旧 `data/**`；不声明数据已覆盖 | P0 | 无 | CR014-W1-CONTRACTS | lifecycle 必需字段 10 类 100% 进入合同；缺字段时 allowed full-A claim 输出次数为 0 | REQ-088, REQ-089, REQ-097 | `process/HLD-DATA-LAKE.md` §17.1, §17.7.1 | ADR-050 |
| CR014-S02-parquet-layout-manifest-catalog-publish-gate | Parquet layout / manifest / catalog current pointer / publish gate | 冻结 Parquet lake 分区、manifest、catalog current pointer、candidate 与 publish gate 读写边界 | layout spec、manifest fields、catalog pointer schema、publish gate state machine | 不改代码；不真实写 raw/canonical/gold/quality/catalog；不更新 current pointer | P0 | CR014-S01-a-share-universe-lifecycle-contract | CR014-W1-CONTRACTS | validate pass 自动更新 pointer 次数为 0；catalog pointer 必填字段 100% 进入合同 | REQ-090, REQ-091 | `process/HLD-DATA-LAKE.md` §17.5, §17.7.1 | ADR-048, ADR-052 |
| CR014-S03-p0-plan-run-normalize-validate-publish-contract | P0 dataset plan/run/normalize/validate/publish 合同 | 定义 P0 7 类 dataset 与 lifecycle/code-change 的 plan/run/normalize/replay/validate/publish 合同和 CP5 授权门 | P0 dataset contract、Provider Adapter / Run Gate、Normalize / Replay、Validate、Publish Gate dev_gate | CP5 前 provider_fetch=0、lake_write=0、credential_read=0、dependency_change=0；不实现真实 pipeline | P0 | CR014-S01-a-share-universe-lifecycle-contract, CR014-S02-parquet-layout-manifest-catalog-publish-gate | CR014-W2-PIPELINE | CP5 前真实操作计数均为 0；run/normalize/replay/validate/publish 每阶段输入输出和 candidate/published 状态 100% 定义 | REQ-090, REQ-091, REQ-092, REQ-094 | `process/HLD-DATA-LAKE.md` §17.7.1 | ADR-048, ADR-051, ADR-052 |
| CR014-S04-duckdb-readonly-query-audit-parity-boundary | DuckDB read-only query/audit/parity 边界 | 冻结 DuckDB 只读候选层读取 published current truth 或受控 candidate audit path 的边界与 parity 输出 | DuckDB read-only connection policy、SQL template boundary、parity evidence schema、fallback pandas/pyarrow 策略 | 不改 `pyproject.toml`/`uv.lock`；不写 `.duckdb` 事实源；不触发 publish | P1 | CR014-S02-parquet-layout-manifest-catalog-publish-gate, CR014-S03-p0-plan-run-normalize-validate-publish-contract | CR014-W2-PIPELINE | DuckDB query/view/parity/report 反向成为事实源次数为 0；dependency_change=0 before CP5 | REQ-093, REQ-094, REQ-096 | `process/HLD-DATA-LAKE.md` §17.6, §17.7.1 | ADR-049, ADR-052 |
| CR014-S05-full-history-readiness-gap-claim-boundary | full-history readiness audit / gap register / claim boundary | 定义全 A since-inception readiness matrix、gap register、allowed_claims / blocked_claims / required_missing 输出合同 | readiness summary schema、coverage numerator/denominator、gap register、claim boundary builder | 不读取或覆盖旧 reports；不外推 CR-010/012/013 旧基线；不执行真实补数 | P0 | CR014-S01-a-share-universe-lifecycle-contract, CR014-S02-parquet-layout-manifest-catalog-publish-gate, CR014-S03-p0-plan-run-normalize-validate-publish-contract, CR014-S04-duckdb-readonly-query-audit-parity-boundary | CR014-W3-AUDIT-OPS | 任一 P0 gate 未通过时 full-A allowed claim 输出次数为 0；blocked_claims 100% 写缺口、证据和解除条件 | REQ-088, REQ-095, REQ-096 | `process/HLD-DATA-LAKE.md` §17.10, §17.13 | ADR-048, ADR-049, ADR-050, ADR-051 |
| CR014-S06-incremental-refresh-replay-retention-contract | incremental refresh / replay / retention 合同 | 定义增量刷新、最近 N 个交易日回补、replay、candidate retention 和 current pointer 不污染策略 | incremental planner、replay contract、resume_conflict、retention policy、permission counters | 不触发 provider；不读取凭据；不写 raw；不改 current pointer；不删除旧数据 | P0 | CR014-S02-parquet-layout-manifest-catalog-publish-gate, CR014-S03-p0-plan-run-normalize-validate-publish-contract | CR014-W3-AUDIT-OPS | replay `provider_fetches=0`、`credential_reads=0`、`raw_writes=0`、`current_pointer_changes=0`；resume_conflict 有结构化输出 | REQ-092, REQ-094 | `process/HLD-DATA-LAKE.md` §17.7.1, §17.8 | ADR-051, ADR-052 |
| CR014-S07-research-consumer-readonly-docs-runbook-boundary | research consumer read-only contract 与 docs/runbook 后续边界 | 冻结研究消费层只读 published current truth / blocked claims / required_missing 的契约，并定义 README/USER-MANUAL 后续刷新边界 | `engine/research_dataset.py` / reports / docs 的消费合同、forbidden import、docs/runbook LLD 输入 | 本阶段不改 README/docs/代码；研究层不得直接 DuckDB 写入/发布/扫未发布 lake | P1 | CR014-S04-duckdb-readonly-query-audit-parity-boundary, CR014-S05-full-history-readiness-gap-claim-boundary, CR014-S06-incremental-refresh-replay-retention-contract | CR014-W4-CONSUMER-BOUNDARY | consumer provider/lake/credential/old data 操作次数为 0；实验入口直接 DuckDB 连接次数为 0，除非后续独立 ADR/CP5 | REQ-093, REQ-094, REQ-095 | `process/HLD.md` §30.2, §30.3 | ADR-049, ADR-051, ADR-052 |
| CR014-S08-w3-minute-tick-level2-vwap-blocked-decision-boundary | W3 / minute / tick / Level2 / VWAP blocked 决策边界 | 固化 W3、minute/tick/Level2/order match、execution VWAP 与真实撮合执行价不进入 CR-014 P0 的 blocked / unsupported 决策边界 | unsupported decision matrix、解除条件、future CR / Story gate、claim boundary link | 不接入或构造微观结构数据；不由 close proxy 或 amount/volume 派生真实 VWAP | P0 | CR014-S05-full-history-readiness-gap-claim-boundary | CR014-W4-CONSUMER-BOUNDARY | W3/minute/tick/Level2/VWAP production allowed claim 输出次数为 0；解除条件 100% 指向后续 source/interface + Story + CP5 + 用户授权 | REQ-084, REQ-095, REQ-096 | `process/HLD-DATA-LAKE.md` §17.2, §17.10; `process/HLD.md` §30.1 | ADR-045, ADR-046, ADR-050, ADR-051 |
| CR014-S09-windowed-real-fetch-lake-write-run | 分时段真实抓取与 raw/manifest 写湖执行 | 在 CR014-S01..S08 完成后，按 dataset/date window 执行真实 provider 抓取与 raw/manifest/run metadata 写湖 | 独立 S09 LLD、CP5、authorization_id、分时段窗口计划、run-scoped manifest、resume token、失败窗口隔离 | 不属于当前 BATCH-A CP5；不自动 normalize；不自动 publish current pointer；不执行 retention delete/archive；不读取/覆盖旧 `data/**` 或旧 reports | P0 | CR014-S01..S08 全部 verified | CR014-W5-REAL-RUN | 每次真实 run 必须有 authorization_id、dataset、date range、window policy、source/interface allowlist、lake root；raw/manifest 写湖后 current_pointer_changes=0 | REQ-090, REQ-091, REQ-092, REQ-094 | `process/HLD-DATA-LAKE.md` §17.7.1, §17.8 | ADR-048, ADR-051, ADR-052 |
| CR017-S01-adjustment-policy-requirements-and-adr-refresh | 复权口径合同与迁移声明冻结 | 将 CP3 已批准的 raw/qfq/hfq/returns_adjusted 和旧 qfq 兼容决策落为可实现合同、迁移声明和测试入口 | `market_data/adjustment_policy.py`、`docs/ADJUSTMENT-POLICY-MIGRATION.md`、policy enum、consumer matrix | 不修改已批准的过程文档；不真实抓取、不写 lake、不发布 current pointer、不覆盖旧 qfq | P0 | CR014-S02-parquet-layout-manifest-catalog-publish-gate | CR017-W1-ADJUSTMENT-CONTRACTS | policy id 覆盖 4 类；QMT execution 非 raw allowed 次数为 0；默认真实操作计数均为 0 | REQ-098, REQ-099, REQ-101, REQ-103, REQ-104 | `process/HLD-DATA-LAKE.md` §18.1-§18.7 | ADR-053, ADR-054 |
| CR017-S02-raw-prices-and-adj-factor-contract-hardening | raw prices 与 adj_factor 事实源合同强化 | 强化 `prices_raw` 与 `adj_factor` 的字段、factor direction、lineage、quality 和 required_missing 合同 | `market_data/adjustment_contracts.py`、`market_data/contracts.py`、`market_data/validation.py`、raw/factor schema tests | 不拥有 connector/runtime；不真实补数；不由 qfq/hfq 覆盖 raw | P0 | CR017-S01-adjustment-policy-requirements-and-adr-refresh, CR010-S02-prices-adj-factor-history-backfill-loop | CR017-W1-ADJUSTMENT-CONTRACTS | raw/factor 必需 metadata 覆盖率 100%；factor direction 缺失时派生成功次数为 0 | REQ-098, REQ-100, REQ-104 | `process/HLD-DATA-LAKE.md` §18.5, §18.6 | ADR-053 |
| CR017-S03-qfq-hfq-derived-view-normalization | qfq / hfq 派生 view normalization | 设计 qfq、hfq 和 returns_adjusted 派生候选逻辑，记录 as-of、base date、derivation_version 和 lineage | `market_data/adjustment_derivation.py`、`market_data/normalization.py`、derivation tests | 不发布 current pointer；不真实全量重算；不覆盖旧 qfq | P0 | CR017-S02-raw-prices-and-adj-factor-contract-hardening | CR017-W2-DERIVATION-READERS | 3 类 derived view 均有独立 view_id / lineage；qfq 100% 记录 as_of_trade_date | REQ-099, REQ-100, REQ-104 | `process/HLD-DATA-LAKE.md` §18.5-§18.7 | ADR-053, ADR-054 |
| CR017-S04-reader-api-and-policy-gates | reader API 与单口径 policy gates | 提供显式 `research_adjustment_policy` reader API 和 single-policy gate，并向 QMT handoff 只输出研究 metadata | `market_data/adjustment_readers.py`、`market_data/readers.py`、`engine/research_dataset.py`、reader policy tests | reader 不触发 backfill；不扫未发布 candidate；不把复权价作为执行价 | P0 | CR017-S03-qfq-hfq-derived-view-normalization | CR017-W2-DERIVATION-READERS | 未指定或混用 policy blocked 覆盖率 100%；QMT handoff 复权价执行 allowed 次数为 0 | REQ-101, REQ-102, REQ-104 | `process/HLD-DATA-LAKE.md` §18.7, §18.8 | ADR-054, ADR-055, ADR-058 |
| CR017-S05-validation-quality-parity-and-leakage-tests | 复权 quality / parity / leakage 验证矩阵 | 建立 TS-017-01..03 对应的公式 parity、quality、single-policy 和 QMT raw 执行价泄漏测试矩阵 | `tests/test_cr017_adjustment_quality_parity.py`、`tests/test_cr017_adjustment_leakage_gates.py`、`market_data/validation.py` | 只用 fixture；不读真实数据；不把 warning 当 production pass | P0 | CR017-S02-raw-prices-and-adj-factor-contract-hardening, CR017-S03-qfq-hfq-derived-view-normalization, CR017-S04-reader-api-and-policy-gates | CR017-W2-DERIVATION-READERS | TS-017-01..03 均有正向和失败场景；缺 direction / as-of / 单口径 / raw execution 时 fail | REQ-098, REQ-099, REQ-100, REQ-101, REQ-102, REQ-121 | `process/HLD-DATA-LAKE.md` §18.6, §18.9 | ADR-053, ADR-054, ADR-058 |
| CR017-S06-research-qmt-consumer-docs-and-migration-guide | 研究 / QMT 消费边界与迁移指南 | 将 chart、长期研究、因子研究、QMT order intent 的复权消费矩阵和 blocked claims 写入迁移指南与后续文档边界 | `docs/ADJUSTMENT-POLICY-MIGRATION.md`、`README.md`、`docs/USER-MANUAL.md`、consumer boundary tests | 不修改 CP3 过程文档；不授权真实运行；scale_up 必须等待 CR017 verified | P0 | CR017-S04-reader-api-and-policy-gates, CR017-S05-validation-quality-parity-and-leakage-tests | CR017-W3-CONSUMER-MIGRATION | consumer guidance 覆盖 4 类消费方；CR017 未 verified 时 scale_up allowed 次数为 0 | REQ-101, REQ-102, REQ-103, REQ-118, REQ-119, REQ-120, REQ-121 | `process/HLD.md` §31; `process/HLD-DATA-LAKE.md` §18; `process/HLD-QMT-TRADING.md` §7.1 | ADR-054, ADR-055, ADR-058, ADR-059 |
| CR015-S01-qmt-environment-and-interface-spike | QMT 环境与接口边界 spike | 定义 Linux 研究节点与 Windows QMT 节点的环境、transport、ack/error enum 和 forbidden boundary | `trading/qmt_environment.py`、`trading/qmt_transport.py`、environment boundary tests、runbook input | 不安装依赖；不运行真实 QMT；不读取凭据；不真实调用 broker API | P0 | 无 | CR015-W1-FOUNDATION-CONTRACTS | direct broker import 次数为 0；真实操作计数均为 0；transport enum 完整 | REQ-105, REQ-110, REQ-111, REQ-121 | `process/HLD-QMT-TRADING.md` §3, §6, §7.1 | ADR-055, ADR-061 |
| CR015-S02-qmt-broker-adapter-contract | QMT broker adapter 合同 | 定义唯一 broker adapter 的 mode gate、submit/cancel contract、mock event 和 blocked reason | `trading/qmt_adapter.py`、`trading/qmt_transport.py`、adapter contract tests | 不实现真实 adapter；不真实 order/cancel/account write；不引入依赖 | P0 | CR015-S01-qmt-environment-and-interface-spike, CR017-S01-adjustment-policy-requirements-and-adr-refresh | CR015-W1-FOUNDATION-CONTRACTS | 未授权 live mode blocked；非 raw execution policy allowed 次数为 0；mock event 覆盖 6 类 | REQ-105, REQ-110, REQ-111, REQ-121 | `process/HLD-QMT-TRADING.md` §5, §7.1 | ADR-055, ADR-061 |
| CR015-S03-oms-order-state-machine | OMS order intent 与订单状态机 | 建立 order intent、幂等 key、状态迁移、manual_review 和 frozen 合同 | `trading/oms.py`、`trading/qmt_adapter.py`、state machine tests | 不真实写 broker facts；不把 unknown/timeout 静默成功 | P0 | CR015-S02-qmt-broker-adapter-contract, CR017-S01-adjustment-policy-requirements-and-adr-refresh | CR015-W2-OMS-RISK-LAKE | HLD 状态覆盖率 100%；intent 100% 写 research policy 与 raw execution policy | REQ-106, REQ-107, REQ-121 | `process/HLD-QMT-TRADING.md` §7.1, §7.3 | ADR-057 |
| CR015-S04-pretrade-risk-gate | pre-trade hard risk gate | 实现现金、整手、T+1、持仓、价格口径、重复、限额和异常价格 hard block 合同 | `trading/pretrade_risk.py`、`trading/oms.py`、risk gate tests | 不查询真实账户；风控失败不得触达 adapter | P0 | CR015-S03-oms-order-state-machine, CR017-S02-raw-prices-and-adj-factor-contract-hardening, CR017-S04-reader-api-and-policy-gates | CR015-W2-OMS-RISK-LAKE | ADR-058 规则覆盖率 100%；任一 fail 时 adapter_calls=0 | REQ-109, REQ-110, REQ-121 | `process/HLD-QMT-TRADING.md` §7.1, §7.4 | ADR-058 |
| CR015-S05-broker-lake-schema-and-writer | broker lake schema 与 dry-run writer | 定义外置 broker lake 的 8 类 schema、dry-run writer、retention 和 redaction gate | `trading/broker_lake.py`、`trading/oms.py`、broker lake tests | 不写仓库 data/reports；不写真实 broker lake；不输出敏感值 | P0 | CR015-S03-oms-order-state-machine | CR015-W2-OMS-RISK-LAKE | 8 类 schema 覆盖；未授权 broker_lake_write=0；本地 data/reports 写入 blocked | REQ-108, REQ-111, REQ-121 | `process/HLD-QMT-TRADING.md` §5, §7.1 | ADR-056 |
| CR015-S06-target-portfolio-to-order-intent-shadow-mode | 目标组合到 order intent 的 shadow 流程 | 串联 target portfolio -> intent -> risk -> mock event -> dry-run plan，证明 foundation 离线闭环 | `trading/shadow_pipeline.py`、OMS/risk/broker lake shared files、shadow pipeline tests | 仅 shadow/dry-run/mock；不启用 simulation/live；不读取真实账户 | P0 | CR015-S03-oms-order-state-machine, CR015-S04-pretrade-risk-gate, CR015-S05-broker-lake-schema-and-writer, CR017-S04-reader-api-and-policy-gates | CR015-W3-SHADOW-RUNBOOK | 输出 intent/risk/state/dry-run plan 4 类结果；真实操作计数均为 0 | REQ-106, REQ-109, REQ-110, REQ-121 | `process/HLD-QMT-TRADING.md` §7.1 | ADR-055, ADR-056, ADR-057, ADR-058 |
| CR015-S07-docs-and-foundation-runbook-boundary | foundation 文档与 runbook 边界 | 输出 QMT foundation 用户文档和 runbook 边界，明确 CR015 不授权真实交易，CR016 管理后续激活 | `docs/QMT-TRADING-RUNBOOK.md`、`README.md`、`docs/USER-MANUAL.md`、runbook tests | 文档不得声明真实交易已支持；不得解除 VWAP/minute/tick/Level2/order-match blocked claim | P1 | CR015-S01-qmt-environment-and-interface-spike, CR015-S02-qmt-broker-adapter-contract, CR015-S03-oms-order-state-machine, CR015-S04-pretrade-risk-gate, CR015-S05-broker-lake-schema-and-writer, CR015-S06-target-portfolio-to-order-intent-shadow-mode, CR017-S06-research-qmt-consumer-docs-and-migration-guide | CR015-W3-SHADOW-RUNBOOK | runbook 覆盖 5 类 foundation 章节；真实交易支持声明次数为 0 | REQ-105, REQ-110, REQ-111, REQ-120, REQ-121 | `process/HLD-QMT-TRADING.md` §11, §15 | ADR-055, ADR-056, ADR-058, ADR-061 |
| CR016-S01-simulation-account-order-enable-gate | simulation 阶段 order enable gate | 定义 shadow -> simulation stage gate、order enable 条件、授权字段、blocked reason 和 safety counters | `trading/stage_gate.py`、`trading/qmt_adapter.py`、simulation gate tests | CR015 未 verified、runbook / 授权 / 对账缺失时 blocked；不授权真实运行 | P0 | CR015-S07-docs-and-foundation-runbook-boundary, CR017-S06-research-qmt-consumer-docs-and-migration-guide | CR016-W1-SIMULATION-OPS-GATES | 5 个 stage 顺序可枚举；跳阶段和缺授权 blocked；真实调用计数为 0 | REQ-112, REQ-113, REQ-114, REQ-115, REQ-121 | `process/HLD-QMT-TRADING.md` §7.2, §7.4 | ADR-059, ADR-060 |
| CR016-S02-reconciliation-service-and-reports | 盘前 / 盘中 / 盘后 reconciliation 服务与报告 | 定义对账服务和报告合同，覆盖委托、成交、持仓、资产、现金和 broker lake facts 差异 | `trading/reconciliation.py`、`trading/broker_lake.py`、`trading/oms.py`、reconciliation tests | 不查询真实账户；不覆盖旧报告；超阈值不得自动继续 | P0 | CR015-S03-oms-order-state-machine, CR015-S05-broker-lake-schema-and-writer, CR016-S01-simulation-account-order-enable-gate | CR016-W1-SIMULATION-OPS-GATES | 覆盖 3 个对账阶段；超阈值后继续下单 allowed 次数为 0 | REQ-116, REQ-117, REQ-121 | `process/HLD-QMT-TRADING.md` §7.2, §8 | ADR-060 |
| CR016-S03-monitoring-heartbeat-and-kill-switch | monitoring heartbeat 与 kill switch | 定义 heartbeat、risk/recon/manual 触发下的停止新单、撤单计划、冻结、incident 和恢复 gate | `trading/monitoring.py`、`trading/kill_switch.py`、OMS/adapter shared files、kill switch tests | 当前不执行真实撤单；只生成 plan；真实动作需后续授权 | P0 | CR015-S02-qmt-broker-adapter-contract, CR015-S03-oms-order-state-machine, CR016-S02-reconciliation-service-and-reports | CR016-W1-SIMULATION-OPS-GATES | kill switch 行为覆盖 5 类输出；触发后新单 allowed 次数为 0 | REQ-117, REQ-121 | `process/HLD-QMT-TRADING.md` §7.2, §8, §9 | ADR-060 |
| CR016-S04-simulation-live-runbook-and-approval-gates | simulation / live runbook 与审批门 | 建立 simulation、live_readonly、small_live 的 runbook 与审批门，覆盖启动、审批、异常、对账、kill switch、恢复和回滚 | `docs/QMT-SIMULATION-LIVE-RUNBOOK.md`、`README.md`、`docs/USER-MANUAL.md`、approval tests | runbook 不等于自动授权；不包含敏感值；不执行真实动作 | P0 | CR016-S01-simulation-account-order-enable-gate, CR016-S02-reconciliation-service-and-reports, CR016-S03-monitoring-heartbeat-and-kill-switch | CR016-W1-SIMULATION-OPS-GATES | runbook 覆盖 7 类章节；缺 P0 章节 runbook_status=fail | REQ-112, REQ-113, REQ-114, REQ-117, REQ-121 | `process/HLD-QMT-TRADING.md` §11 | ADR-059, ADR-060, ADR-061 |
| CR016-S05-live-readonly-and-small-live-admission | live_readonly 与 small_live 准入门 | 定义 live_readonly 和 small_live 的准入、退出、回退、资金上限、观察窗口和失败阈值 | `trading/live_admission.py`、`trading/stage_gate.py`、live admission tests | later-gated；无 per-run 授权不得真实运行；不自动放大资金 | P0 | CR016-S04-simulation-live-runbook-and-approval-gates, CR015-S07-docs-and-foundation-runbook-boundary | CR016-W2-LIVE-SCALE-DOCS-GATED | live/small gate 均含准入、退出、回退、观察窗口、失败阈值；无授权真实调用为 0 | REQ-112, REQ-114, REQ-116, REQ-117, REQ-119, REQ-121 | `process/HLD-QMT-TRADING.md` §7.4, §11 | ADR-059, ADR-060 |
| CR016-S06-scale-up-and-research-maturity-gates | scale_up 与研究成熟度 gate | 定义资金放大前的研究成熟度、运行稳定性、CR017 verified 和 blocked claims gate | `trading/scale_up_gate.py`、`engine/research_dataset.py`、scale-up tests | later-gated；CR017 未 verified 或任一 P0 gate 缺失时 scale_up blocked | P0 | CR016-S05-live-readonly-and-small-live-admission, CR017-S06-research-qmt-consumer-docs-and-migration-guide, CR011-S08-factor-panel-audit-and-robust-validation | CR016-W2-LIVE-SCALE-DOCS-GATED | scale_up 至少检查 5 类前置；CR017 未 verified 时 allowed 次数为 0 | REQ-118, REQ-119, REQ-120, REQ-121 | `process/HLD-QMT-TRADING.md` §7.4, §11 | ADR-059, ADR-060 |
| CR016-S07-docs-user-manual-and-incident-playbooks | 用户文档与 incident playbooks | 补齐 staged activation、故障处理、暂停/恢复、人工接管和 incident playbook 文档 | `docs/QMT-INCIDENT-PLAYBOOK.md`、`README.md`、`docs/USER-MANUAL.md`、docs tests | 文档不授权真实运行；不写真实运行报告；不输出敏感值 | P1 | CR016-S04-simulation-live-runbook-and-approval-gates, CR016-S05-live-readonly-and-small-live-admission, CR016-S06-scale-up-and-research-maturity-gates | CR016-W2-LIVE-SCALE-DOCS-GATED | 文档覆盖 5 个 stage 和 5 类 incident；真实操作默认 allowed 次数为 0 | REQ-113, REQ-114, REQ-116, REQ-117, REQ-119, REQ-120, REQ-121 | `process/HLD-QMT-TRADING.md` §11, §15 | ADR-059, ADR-060, ADR-061 |
| CR018-S01-production-current-truth-definition-and-dataset-groups | production current truth 定义与 dataset group | 冻结 scoped release、P0/P1 dataset group、release claim matrix 和 readiness summary 合同 | `process/HLD-DATA-LAKE.md` §19、`market_data/contracts.py`、`market_data/catalog.py`、readiness summary schema | 不真实抓取；不写 lake；不 publish current pointer；不修改代码于本轮 | P0 | CR014-S09-windowed-real-fetch-lake-write-run candidate evidence | CR018-W1-SCOPE-CONTRACT | release scope、as_of、P0/P1、allowed/blocked claims 字段覆盖率 100%；current truth publish 操作为 0 | REQ-123, REQ-124, REQ-125, REQ-135, REQ-136, REQ-137 | `process/HLD-DATA-LAKE.md` §19.1-§19.6 | ADR-062, ADR-063 |
| CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill | PIT / lifecycle / ST / suspend / trade_status / prices_limit readiness | 将 P0 PIT universe、lifecycle、code-change、ST、停牌、交易状态和涨跌停 readiness 纳入 production gate | `market_data/contracts.py`、`market_data/validation.py`、`market_data/readers.py`、gate tests | 不伪造 available；不以当前快照替代 PIT；不执行真实 provider fetch 于本轮 | P0 | CR018-S01-production-current-truth-definition-and-dataset-groups | CR018-W2-P0-P1-READINESS | P0 gate 缺失时 production publish allowed 次数为 0；as-of join 违规计数必须为 0 | REQ-126, REQ-127, REQ-130 | `process/HLD-DATA-LAKE.md` §19.4, §19.9 | ADR-063 |
| CR018-S03-real-benchmark-index-components-weights-backfill | 四类 benchmark 行情 / 成分 / 权重 readiness | 覆盖 HS300、ZZ500、ZZ1000、中证全指的行情、成分、权重和 coverage denominator | `market_data/benchmarks.py`、`market_data/contracts.py`、`market_data/validation.py`、benchmark tests | 不用 proxy 填充真实 benchmark；不允许 benchmark 缺失时 production pass | P0 | CR018-S01-production-current-truth-definition-and-dataset-groups | CR018-W2-P0-P1-READINESS | 四类 benchmark 均输出 prices/components/weights readiness；proxy 写入真实 benchmark 字段次数为 0 | REQ-128, REQ-130, REQ-133 | `process/HLD-DATA-LAKE.md` §19.4, §19.8 | ADR-064 |
| CR018-S04-industry-market-cap-liquidity-and-exposure-data | P1 行业 / 市值 / 风格 / 流动性 / 容量合同 | 建立 P1 auxiliary availability 与 blocked claim 规则，阻断中性化、pure alpha、容量和 scale_up 声明 | `engine/research_dataset.py`、`market_data/readers.py`、claim boundary tests | 不让 P1 缺失阻断 core current truth；不声明缺数据下的容量可行 | P1 | CR018-S01-production-current-truth-definition-and-dataset-groups | CR018-W2-P0-P1-READINESS | P1 缺失时对应中性化、pure alpha、capacity、scale_up allowed claim 输出次数为 0 | REQ-135, REQ-136 | `process/HLD-DATA-LAKE.md` §19.4, §19.12 | ADR-063 |
| CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness | raw / adj_factor / qfq / hfq / returns_adjusted publish readiness | 将 CR017 复权双视图和 raw 执行价边界并入 P0 production quality gate | `market_data/adjustment_policy.py`、`market_data/validation.py`、`market_data/readers.py`、adjustment tests | 不覆盖旧 qfq；不以复权价作为 QMT 执行价；不发布 current pointer 于本轮 | P0 | CR018-S01-production-current-truth-definition-and-dataset-groups, CR017-S05-validation-quality-parity-and-leakage-tests | CR018-W2-P0-P1-READINESS | raw/adj_factor/qfq/hfq/returns_adjusted readiness 全部可追溯；复权混用通过次数为 0 | REQ-129, REQ-130 | `process/HLD-DATA-LAKE.md` §19.4, §19.9; `process/HLD.md` §32 | ADR-063, ADR-065 |
| CR018-S06-production-quality-readiness-audit-and-rollback-gate | production quality / readiness / rollback gate | 聚合 P0/P1 readiness、audit evidence、blocked claims 和 release-level rollback contract | `market_data/validation.py`、`market_data/catalog.py`、`market_data/publish.py`、rollback tests | 不执行真实 rollback；不允许 dataset 局部 rollback 改变 current truth | P0 | CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill, CR018-S03-real-benchmark-index-components-weights-backfill, CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness | CR018-W3-PUBLISH-ROLLBACK | readiness audit 字段覆盖 release/dataset/quality/blocked/rollback；P0 fail 时 publish allowed 次数为 0 | REQ-124, REQ-130, REQ-132, REQ-137 | `process/HLD-DATA-LAKE.md` §19.9-§19.11 | ADR-065 |
| CR018-S07-explicit-publish-gate-and-current-reader-smoke | Explicit Publish Gate 与 current reader smoke | 建立 release-level publish 审批、dataset-level 明细、current pointer 读烟测和 publish evidence | `market_data/publish.py`、`market_data/catalog.py`、`market_data/readers.py`、publish gate tests | 不在 CP5 前真实 publish；不由 validate 自动更新 current pointer | P0 | CR018-S06-production-quality-readiness-audit-and-rollback-gate | CR018-W3-PUBLISH-ROLLBACK | publish 必须显式审批；current reader smoke 覆盖 P0 dataset；自动 publish 次数为 0 | REQ-124, REQ-125, REQ-131, REQ-132 | `process/HLD-DATA-LAKE.md` §19.7, §19.10 | ADR-065 |
| CR018-S08-production-current-truth-research-rerun | published current truth 研究重跑 | 在 published release 后重跑阶段三到阶段五核心研究并输出 production pass/fail 与差异摘要 | `engine/research_dataset.py`、`experiments/**` rerun entry、`reports/production_current_truth/**` | 不覆盖旧报告；不以 candidate 或 proxy 作为 production rerun 输入；不启动 QMT | P0 | CR018-S07-explicit-publish-gate-and-current-reader-smoke | CR018-W4-RERUN-QMT-ADMISSION | rerun 报告必须记录 release_id、benchmark、PIT、tradability、adjustment、blocked claims；QMT admission 前 PASS 必填 | REQ-133, REQ-137 | `process/HLD.md` §32; `process/HLD-DATA-LAKE.md` §19.13 | ADR-066 |
| CR018-S09-qmt-simulation-admission-boundary-after-data-lake | QMT admission 后置边界 | 将 QMT simulation/live_readonly/small_live/scale_up 的准入改为消费 S08 PASS 与 release readiness | `trading/stage_gate.py`、`trading/live_admission.py`、QMT admission tests、runbook input | 不真实调用 QMT；不发单、不撤单、不查账户；不解除 small_live / scale_up later gate | P0 | CR018-S08-production-current-truth-research-rerun, CR015-S07-docs-and-foundation-runbook-boundary, CR016-S04-simulation-live-runbook-and-approval-gates | CR018-W4-RERUN-QMT-ADMISSION | S08 未 PASS 时 QMT stage allowed 次数为 0；simulation/live/small/scale 均输出 blocked reason | REQ-123, REQ-134, REQ-137 | `process/HLD.md` §32; `process/HLD-DATA-LAKE.md` §19.13 | ADR-066 |
| CR019-S01-stage6-admission-gate-package | 阶段六 admission gate 与 package 合同 | 冻结实验 49-66 gate、旧失败策略 blocked evidence、pre-sim、连续 5 个真实交易日 dry-run evidence 和 admission package schema | `engine/stage6_admission.py`、`reports/stage6_admission/**`、admission gate tests | 不启动 simulation；不调用 QMT；不真实抓取或写 lake；不包装旧失败策略 | P0 | CR018-S08-production-current-truth-research-rerun, CR016-S04-simulation-live-runbook-and-approval-gates | CR019-W1-ADMISSION-BENCHMARK | 任一 P0 gate 未过时 `admission_status=blocked`；旧失败策略 simulation_ready 次数为 0；真实操作计数为 0 | REQ-138, REQ-144, REQ-154 | `process/HLD.md` §33.1, §33.4, §33.12 | ADR-067 |
| CR019-S02-primary-benchmark-dashboard | 多基准看板与 primary benchmark policy | 定义 HS300、ZZ500、ZZ1000、中证全指多基准看板、primary benchmark 选择规则和 admission report 字段 | `engine/benchmark_policy.py`、`reports/stage6_admission/benchmark_dashboard_schema.md`、benchmark policy tests | 不真实补 benchmark；不以 proxy 冒充真实 benchmark；不 publish | P0 | CR019-S01-stage6-admission-gate-package, CR018-S03-real-benchmark-index-components-weights-backfill | CR019-W1-ADMISSION-BENCHMARK | 4 类 benchmark 字段覆盖率 100%；primary 选择规则有 universe / 风格依据；proxy 写入真实 benchmark 字段次数为 0 | REQ-138, REQ-154 | `process/HLD.md` §33.4, §33.6 | ADR-067 |
| CR019-S03-qmt-cside-client-cli-contract | QMT C 侧 Python client 与薄 CLI 合同 | 在 local_backtest 侧规划类型化 Python client / 函数调用主接口和复用同一 client 的薄 CLI wrapper | `trading/qmt_client.py`、`trading/qmt_cli.py`、C 侧 contract tests | 不导入 `xtquant`；不读取凭据；CLI 不复制业务逻辑；不启动服务 | P0 | CR015-S02-qmt-broker-adapter-contract, CR016-S04-simulation-live-runbook-and-approval-gates | CR019-W2-CS-TRANSPORT | C 侧 direct xtquant import 次数为 0；CLI 100% 复用 client；typed blocked result 覆盖 health/capabilities/query/order 类别 | REQ-142, REQ-145, REQ-159, REQ-160 | `process/HLD.md` §33.4, §33.9; `process/HLD-QMT-TRADING.md` §17.1 | ADR-068, ADR-069 |
| CR019-S04-windows-gateway-lifecycle-deployment | Windows FastAPI gateway 生命周期与部署合同 | 规划 Windows 可运行 / 可安装 gateway 命令、配置、bind host/port、防火墙、heartbeat、service lifecycle 和 install boundary | `trading/qmt_gateway_service.py`、`trading/qmt_gateway_config.py`、`docs/QMT-GATEWAY-INSTALL.md`、gateway lifecycle tests | 不新增依赖；不启动 FastAPI；不打开端口；不访问真实 QMT 服务端 | P0 | CR019-S03-qmt-cside-client-cli-contract | CR019-W2-CS-TRANSPORT | gateway 命令 / 配置 / bind / firewall / heartbeat 字段覆盖率 100%；公网默认暴露 allowed 次数为 0 | REQ-145, REQ-149, REQ-159 | `process/HLD.md` §33.4, §33.9, §33.10; `process/HLD-QMT-TRADING.md` §17.1, §17.3 | ADR-068 |
| CR019-S05-pairing-hmac-auth-redaction | 配对式 token/HMAC 与日志脱敏合同 | 定义 pair request/list/approve/complete、client id、secret 领取、HMAC headers、timestamp、nonce、scope、redaction 和 no-auth 临时模式边界 | `trading/qmt_auth.py`、`trading/qmt_redaction.py`、auth/redaction tests | 不读取或生成真实 secret；不记录 pairing code；no-auth 不作为默认；HMAC 不替代交易授权 | P0 | CR019-S03-qmt-cside-client-cli-contract, CR019-S04-windows-gateway-lifecycle-deployment | CR019-W3-AUTH-ENDPOINT-GATE | HMAC 失败 / 过期 / replay / scope 不足时 QMT adapter call=0；日志中 secret/token/account/session/.env 出现次数为 0 | REQ-148, REQ-151, REQ-152 | `process/HLD.md` §33.10, §33.10.1, §33.13; `process/HLD-QMT-TRADING.md` §17.3 | ADR-071 |
| CR019-S06-qmt-endpoint-matrix-contract | 完整 QMT endpoint matrix 与 typed blocked result | 定义 health/capabilities、validate/dry-run、行情、账户、持仓、委托、成交、simulation/live、reconciliation、kill-switch 等接口类别及 allowed/blocked contract | `trading/qmt_endpoint_matrix.py`、`trading/qmt_gateway_contracts.py`、endpoint matrix tests | 不把 endpoint 可见写成真实授权；不退回 dry-run-only；不调用真实 QMT | P0 | CR019-S03-qmt-cside-client-cli-contract, CR019-S04-windows-gateway-lifecycle-deployment, CR019-S05-pairing-hmac-auth-redaction | CR019-W3-AUTH-ENDPOINT-GATE | HLD §33.11 endpoint 类别覆盖率 100%；每类 endpoint 至少 1 个 blocked case；真实 QMT 调用计数为 0 | REQ-146, REQ-147, REQ-152 | `process/HLD.md` §33.11; `process/HLD-QMT-TRADING.md` §17.2 | ADR-070 |
| CR019-S07-run-gate-blocked-reason-integration | 运行门控与 blocked reason 集成 | 将 run mode、CR016 stage gate、pre-trade risk、kill switch、per-run authorization、raw execution policy 接到 gateway blocked reason 合同 | `trading/qmt_gateway_gates.py`、`trading/stage_gate.py`、`trading/pretrade_risk.py`、run gate tests | HMAC pass 不等于交易授权；不得绕过 CR015/016 gate；不得触发真实账户或 broker 操作 | P0 | CR019-S01-stage6-admission-gate-package, CR019-S06-qmt-endpoint-matrix-contract, CR015-S04-pretrade-risk-gate, CR016-S03-monitoring-heartbeat-and-kill-switch, CR016-S04-simulation-live-runbook-and-approval-gates | CR019-W3-AUTH-ENDPOINT-GATE | 缺任一 gate 时 adapter_call / real_order / account_query 均为 0；blocked reason 覆盖 gate、auth、risk、kill-switch、authorization | REQ-144, REQ-147, REQ-152, REQ-154 | `process/HLD.md` §33.11, §33.12, §33.13; `process/HLD-QMT-TRADING.md` §17.2 | ADR-070, ADR-071 |
| CR019-S08-fallback-incident-signed-file-boundary | fallback / incident / signed file fail-closed 边界 | 定义 gateway 不可达、auth fail、heartbeat fail、部署不满足和 gate fail 时的 blocked-only 或人工 dry-run / signed file drop fallback | `trading/qmt_gateway_fallback.py`、`docs/QMT-INCIDENT-PLAYBOOK.md`、fallback tests | 不自动真实 fallback；不发单、不撤单、不查账户、不写 broker lake | P0 | CR019-S04-windows-gateway-lifecycle-deployment, CR019-S05-pairing-hmac-auth-redaction, CR019-S06-qmt-endpoint-matrix-contract, CR019-S07-run-gate-blocked-reason-integration | CR019-W4-FALLBACK-DEFERRED | gateway/auth/heartbeat/gate fail 时真实 QMT / broker lake 写入计数均为 0；dry-run file 只可人工处理 | REQ-145, REQ-150, REQ-152 | `process/HLD.md` §33.12; `process/HLD-QMT-TRADING.md` §17.4 | ADR-072 |
| CR019-S09-deferred-capability-register | Backtrader / Qlib / minute / Level2 后置能力 register | 固化 Backtrader W6、Qlib W7、minute Spike、Level2 Spike 的触发条件、阻断声明和后续 CR / CP 入口 | `docs/CR019-DEFERRED-CAPABILITIES.md`、deferred capability tests | 不新增依赖；不接 Qlib provider；不申请 Level2；不把后置能力列为 P0 | P1 | CR019-S01-stage6-admission-gate-package, CR019-S02-primary-benchmark-dashboard | CR019-W4-FALLBACK-DEFERRED | 4 类后置能力均有触发条件和 blocked reason；阶段六 P0 依赖新增次数为 0 | REQ-139, REQ-140, REQ-141, REQ-143, REQ-155, REQ-156, REQ-157, REQ-158 | `process/HLD.md` §33.14, §33.16 | ADR-073 |
| CR019-S10-docs-runbook-user-manual-boundary | CR-019 文档、runbook 与用户手册边界 | 汇总 admission、QMT C/S bridge、pairing/HMAC、endpoint/gate/fallback、后置能力和真实操作禁止声明到用户可读文档边界 | `docs/QMT-C-S-BRIDGE-RUNBOOK.md`、`README.md`、`docs/USER-MANUAL.md`、`docs/QMT-SIMULATION-LIVE-RUNBOOK.md`、docs tests | 文档不授权 simulation/live；不写真实 runbook 凭据；不修改过程 HLD/ADR；不发布 delivery | P1 | CR019-S01-stage6-admission-gate-package, CR019-S02-primary-benchmark-dashboard, CR019-S03-qmt-cside-client-cli-contract, CR019-S04-windows-gateway-lifecycle-deployment, CR019-S05-pairing-hmac-auth-redaction, CR019-S06-qmt-endpoint-matrix-contract, CR019-S07-run-gate-blocked-reason-integration, CR019-S08-fallback-incident-signed-file-boundary, CR019-S09-deferred-capability-register | CR019-W5-DOCS-RUNBOOK | 用户文档必须包含 7 个 DQ 决策、10 个 Story 边界和 no-real-operation 表；“runbook/Story verified 授权真实交易”匹配次数为 0 | REQ-151, REQ-152, REQ-153 | `process/HLD.md` §33; `process/HLD-QMT-TRADING.md` §17 | ADR-067..073 |
| CR025-S01-clean-feed-gate-backend-selector | clean feed gate 与 backend selector | 冻结 CR-025 clean feed gate、lightweight 默认路径、Backtrader optional selector、未安装/未选择 structured unavailable 和 lazy import 边界 | `engine/backtrader_adapter.py`、`engine/backtest.py` 或 selector、`tests/test_cr025_clean_feed_gate.py` | 不改依赖；不运行 Backtrader；不生成 PIT/复权/benchmark/tradability/quality truth；不联网补数 | P0 | CR006-S03-backtrader-clean-feed-contract, CR005-S06-backtrader-optional-backend | CR025-W1-FEED-GOVERNANCE | PIT/available_at/复权/benchmark/tradability/quality/lineage/limitations gate 覆盖率 100%；默认 Backtrader import 次数为 0；未安装返回 structured unavailable | REQ-161, REQ-162, REQ-163, REQ-167 | `process/HLD.md` §34.4, §34.6, §34.11 | ADR-074 |
| CR025-S02-semantic-diff-schema-artifact | semantic diff schema 与 artifact | 定义 lightweight baseline 与 Backtrader-style execution semantic reference 的成交、现金、成本、滑点、净值、仓位和差异原因 artifact 合同 | `engine/semantic_diff.py`、`reports/semantic_diff/**`、`tests/test_cr025_semantic_diff_contract.py` | 不把 reference 覆盖 baseline；不声明 production truth、simulation-ready 或 QMT admission pass；不实现 FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪或策略准入包 | P0 | CR025-S01-clean-feed-gate-backend-selector, CR025-S04-backtrader-module-reference-no-copy-guardrail | CR025-W2-SEMANTIC-DIFF | diff 字段不少于 10 类；每类执行语义差异有 reason 或 unavailable；Backtrader result 覆盖 lightweight result 次数为 0；多因子研究闭环字段实现项为 0 | REQ-164, REQ-166 | `process/HLD.md` §34.6, §34.9, §34.13 | ADR-074, ADR-075, ADR-076, ADR-078 |
| CR025-S03-order-intent-draft-qmt-boundary | `order_intent_draft_v1` 与 QMT 后续边界 | 将 target portfolio / semantic diff evidence 转为 `order_intent_draft_v1` 草案，冻结 raw execution policy、lineage、limitations 和 QMT later-gated 消费边界 | `engine/order_intent_draft.py`、`tests/test_cr025_order_intent_draft_contract.py` | 不启动 CR-020；不调用 QMT / MiniQMT / XtQuant；不写 broker lake；不生成可提交订单 | P0 | CR025-S02-semantic-diff-schema-artifact, CR015-S03-oms-order-state-machine, CR015-S06-target-portfolio-to-order-intent-shadow-mode, CR017-S04-reader-api-and-policy-gates | CR025-W3-ORDER-INTENT-QMT | draft 必填字段覆盖率 100%；`execution_price_policy != raw` hard block；QMT API / order / cancel / account query / broker_lake_write 均为 0 | REQ-169, REQ-171 | `process/HLD.md` §34.7; `process/HLD-QMT-TRADING.md` §18 | ADR-077 |
| CR025-S04-backtrader-module-reference-no-copy-guardrail | Backtrader 模块 reference / no-copy guardrail | 将 HLD §34.5 的 `reference_only` / `adapt_interface` / `migration_candidate` / `exclude` 矩阵落入后续 LLD 输入和 forbidden source-copy 扫描策略；矩阵仅服务 execution semantic reference | `docs/CR025-BACKTRADER-MODULE-REFERENCE.md`、`tests/test_cr025_backtrader_no_copy_guardrail.py` | 不复制、裁剪、改写或源码级移植 Backtrader GPLv3 源码；不复制 samples/tests/datas；不把 Backtrader indicators / Strategy / analyzer 体系写成多因子研究主框架 | P0 | 无 | CR025-W1-FEED-GOVERNANCE | `migration_candidate` 当前为空；forbidden path 覆盖源码/样例/测试数据/live store/line runtime；源码复制 / 移植项为 0；Backtrader 承接 FactorSpec / IC / RankIC 等多因子能力次数为 0 | REQ-172, REQ-173, RA-066 | `process/HLD.md` §34.5, §34.14 | ADR-075, ADR-076, ADR-078 |
| CR025-S05-no-real-operation-safety-verification | no-real-operation safety 与验证策略 | 建立 CR-025 fixture-only 验证矩阵、forbidden import / forbidden source copy scan、schema contract、semantic diff contract 和真实操作安全计数 | `tests/test_cr025_no_real_operation_safety.py`、`tests/test_cr025_forbidden_source_copy.py`、`tests/test_cr025_schema_contracts.py` | 不执行 Backtrader 真实运行；不触发 provider/lake/publish/broker/QMT/simulation/live；不读取凭据 | P0 | CR025-S01-clean-feed-gate-backend-selector, CR025-S02-semantic-diff-schema-artifact, CR025-S03-order-intent-draft-qmt-boundary, CR025-S04-backtrader-module-reference-no-copy-guardrail | CR025-W4-SAFETY-VERIFICATION-DOCS | fixture-only 验证覆盖 TS-025-01..11；real_broker/QMT/provider/lake/broker_lake/publish/simulation/live/credential 计数均为 0；依赖 diff 为 0 | REQ-165, REQ-168 | `process/HLD.md` §34.8, §34.13, §34.14 | ADR-074..078 |
| CR025-S06-route-docs-and-follow-up-handoff | QMT 后续路线衔接与用户文档边界 | 汇总 CR-025 semantic diff、order intent draft、Backtrader reference/no-copy、optional runtime boundary、CR-020..CR-024 后续路线和多因子研究后续 CR 边界到文档 / follow-up handoff | `docs/CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT.md`、`README.md`、`docs/USER-MANUAL.md` | 文档不授权真实交易、gateway 启动、dependency install、Backtrader run、simulation/live 或 publish；不把 Qlib / Alphalens / vnpy.alpha 或多因子研究闭环并入 CR-025 | P1 | CR025-S01-clean-feed-gate-backend-selector, CR025-S02-semantic-diff-schema-artifact, CR025-S03-order-intent-draft-qmt-boundary, CR025-S04-backtrader-module-reference-no-copy-guardrail, CR019-S09-deferred-capability-register | CR025-W4-SAFETY-VERIFICATION-DOCS | 文档包含 6 个 CP3 DQ、6 个 Story 边界、CR-020..CR-024 不继承授权声明、后续多因子研究 CR 边界和 no-real-operation 表；“CR-025 verified 授权真实操作”匹配次数为 0 | REQ-166, REQ-170, REQ-171 | `process/HLD.md` §34; `process/HLD-QMT-TRADING.md` §18 | ADR-074..078 |
| CR030-S01-external-reference-matrix-and-loop-contract | 外部项目矩阵与多因子闭环总合同 | 冻结 CR-030 外部项目 reference / optional Spike / exclude / forbidden migration 分类、自有闭环主线、CR-026 后置条件和全局 no-real-operation 边界 | `docs/CR030-MULTIFACTOR-REFERENCE-MATRIX.md`、`tests/test_cr030_external_reference_guardrails.py` | 不 clone/install/run 外部项目；不复制源码；不把外部项目设为默认 truth / runner / provider / optimizer | P0 | 无 | CR030-W1-CONTRACT-GOVERNANCE | 10 类外部项目均有分类、license/dependency/provider/runtime boundary、切换条件和 not-authorized；外部 runtime/default truth/source migration 命中次数为 0 | REQ-174, REQ-175, REQ-182, REQ-184, REQ-185 | `process/HLD.md` §35.4, §35.5, §35.15 | ADR-079, ADR-080, ADR-086 |
| CR030-S02-factor-spec-run-spec-contract | FactorSpec / FactorRunSpec 契约 | 定义因子身份、版本、方向、输入字段、窗口、预处理、universe、availability、lineage、run_id、dataset_release、benchmark、cost、seed、code_version、config_hash 和 failure policy | `engine/multifactor_contracts.py`、`tests/test_cr030_factor_spec_run_spec_contract.py` | 不直接采用 Qlib/Alphalens/Zipline/LEAN 对象；不从零绕开现有基线；不实现外部 runner | P0 | CR030-S01-external-reference-matrix-and-loop-contract | CR030-W1-CONTRACT-GOVERNANCE | `FactorSpec` / `FactorRunSpec` P0 字段覆盖率 100%；缺必填字段返回 structured blocked reason；外部对象作为 internal truth 次数为 0 | REQ-176, REQ-183, REQ-185 | `process/HLD.md` §35.6, §35.7 | ADR-081 |
| CR030-S03-factor-panel-label-window-fail-closed | FactorPanelContract / LabelWindowSpec 防泄漏合同 | 定义因子面板、标签窗口、available_at、decision_time、lineage、复权口径、quality status、blocked reason 和 fail-closed 错误码 | `engine/factor_panel_contracts.py`、`tests/test_cr030_factor_panel_label_window_gates.py` | 不用外部框架生成 PIT / label truth；不接受缺 `available_at` 的字段进入评价；不写真实 lake | P0 | CR030-S02-factor-spec-run-spec-contract, CR011-S08-factor-panel-audit-and-robust-validation | CR030-W2-PANEL-EVALUATION | 前视 / label overlap / lineage 缺失 / 复权混用 / quality 缺失均 fail-closed；评价和组合继续次数为 0 | REQ-177, REQ-182, REQ-183, REQ-185 | `process/HLD.md` §35.7.3, §35.8, §35.10 | ADR-081, ADR-082 |
| CR030-S04-factor-evaluation-report | 单因子评价报告标准化 | 标准化 coverage、IC、RankIC、ICIR、分层收益、多空收益、turnover、成本敏感性、暴露、分段分析、allowed/blocked claims 和 catalog 入口 | `engine/factor_evaluation.py`、`reports/factor_evaluation/**`、`tests/test_cr030_factor_evaluation_report.py` | 不用单一全样本指标声明生产有效；不覆盖旧实验报告；不运行 Alphalens | P0 | CR030-S03-factor-panel-label-window-fail-closed | CR030-W2-PANEL-EVALUATION | 报告字段覆盖 REQ-178；输入 gate fail 时只能输出 `blocked` / `research_limited`；生产有效声明误用次数为 0 | REQ-178, REQ-182, REQ-185 | `process/HLD.md` §35.6, §35.8, §35.13 | ADR-082, ADR-084 |
| CR030-S05-multifactor-combiner-portfolio-plan | 多因子组合与组合计划 | 定义标准化、winsorization、中性化、正交化、规则权重 / 轻量线性组合、缺失值、约束、成本、容量、调仓和 `MultiFactorPortfolioPlan` | `engine/multifactor_combiner.py`、`tests/test_cr030_multifactor_combiner.py` | 不默认引入 optimizer / cvxpy / EnhancedIndexing / vectorbt；不生成 broker order | P0 | CR030-S04-factor-evaluation-report | CR030-W3-COMBINATION-MANIFEST | P0 组合只使用可解释规则或轻量线性组合；optimizer 需求进入 Spike；真实 order 生成次数为 0 | REQ-179, REQ-182, REQ-185 | `process/HLD.md` §35.6, §35.8, §35.13 | ADR-083 |
| CR030-S06-experiment-manifest-report-catalog | ExperimentManifest / ResearchReportCatalog 追踪 | 定义 run manifest、config hash、data release、factor versions、label window、benchmark、cost、code_version、artifact refs、allowed/blocked claims 和 catalog 查询入口 | `engine/research_manifest.py`、`reports/research_catalog/**`、`tests/test_cr030_experiment_manifest_catalog.py` | 不采用 MLflow / pickle recorder 默认 truth；不 publish current pointer；不覆盖旧 reports | P0 | CR030-S04-factor-evaluation-report | CR030-W3-COMBINATION-MANIFEST | manifest/catalog P0 字段覆盖率 100%；缺 P0 字段进入 admission 次数为 0；旧报告 overwrite 次数为 0 | REQ-180, REQ-182, REQ-185 | `process/HLD.md` §35.6, §35.8, §35.13 | ADR-084 |
| CR030-S07-strategy-admission-package-handoff | StrategyAdmissionPackage 与研究到执行 handoff | 汇总数据、因子、组合、回测、成本、benchmark、稳健性、消融、冻结、pre-sim、5 日 dry-run 前置状态、blocked reasons、解除条件和 `order_intent_draft_v1` 草稿边界 | `engine/strategy_admission_package.py`、`tests/test_cr030_strategy_admission_package.py` | 不生成真实 order；不调用 QMT / MiniQMT / XtQuant；不启动 gateway；不查账户；不写 broker lake | P0 | CR030-S05-multifactor-combiner-portfolio-plan, CR030-S06-experiment-manifest-report-catalog, CR019-S01-stage6-admission-gate-package, CR025-S03-order-intent-draft-qmt-boundary | CR030-W4-ADMISSION-SAFETY-DOCS | 任一 Stage6 P0 gate fail 或无独立 QMT CR 时 `admission_status=blocked`；`qmt_api_call`、`real_order`、`account_query` 均为 0 | REQ-181, REQ-182, REQ-185 | `process/HLD.md` §35.6, §35.8, §35.12 | ADR-085 |
| CR030-S08-safety-docs-and-follow-up-boundary | 安全验证、文档与后续 Spike 边界 | 建立 CR-030 no-real-operation safety、external source-copy / runtime forbidden scan、CR-026 / optimizer / ML / vectorbt / PyBroker / RQAlpha / vn.py 后续 Spike 条件和用户文档边界 | `docs/CR030-MULTIFACTOR-RESEARCH-LOOP.md`、`README.md`、`docs/USER-MANUAL.md`、`tests/test_cr030_no_real_operation_safety.py` | 文档不授权外部项目运行、依赖安装、provider/lake/publish、QMT/simulation/live、凭据读取或真实交易；不启动 CR-026 | P1 | CR030-S01-external-reference-matrix-and-loop-contract, CR030-S02-factor-spec-run-spec-contract, CR030-S03-factor-panel-label-window-fail-closed, CR030-S04-factor-evaluation-report, CR030-S05-multifactor-combiner-portfolio-plan, CR030-S06-experiment-manifest-report-catalog, CR030-S07-strategy-admission-package-handoff | CR030-W4-ADMISSION-SAFETY-DOCS | 文档覆盖 7 个 CP3 DQ、8 个 Story 边界、CR-026 后置条件和 no-real-operation 表；“CR-030 verified 授权真实操作 / QMT-ready / simulation-ready / live-ready”语义匹配次数为 0 | REQ-175, REQ-182, REQ-184, REQ-185 | `process/HLD.md` §35.14, §35.15, §35.17 | ADR-079..086 |
| CR020-S01-windows-gateway-runtime-admission | Windows gateway runtime 与准入合同 | 冻结 Windows S 端 gateway Typer CLI、配置读取、bind / lifecycle / heartbeat、read-only admission 状态和 CP5 前运行禁止边界 | `trading/qmt_gateway_cli.py`、`trading/qmt_gateway_service.py`、`trading/qmt_gateway_config.py`、`tests/test_cr020_windows_gateway_runtime_admission.py` | 不新增依赖；不启动 gateway；不绑定端口；不连接 QMT / MiniQMT / XtQuant；不读取真实 `.env` | P0 | CR019-S04-windows-gateway-lifecycle-deployment | CR020-W1-GATEWAY-RUNTIME-SESSION | gateway lifecycle/config/admission 字段覆盖率 100%；public bind 默认 allowed 次数为 0；CP5 前 service_start/port_bind/qmt_call 均为 0 | CP2-CR020 D1, D7 | `process/HLD.md` §36.3, §36.8, §36.12, §36.17 | ADR-087, ADR-088, ADR-093 |
| CR020-S02-server-qmt-login-session | Server QMT 登录与 session ready gate | 定义 S 端 QMT login、session state、credential_ref、session ready gate、fail-closed 错误和只读查询前置阻断 | `trading/qmt_gateway_session.py`、`.env.example`、`tests/test_cr020_server_qmt_login_session.py` | 不读取真实 `.env`；不输出账号/密码/token/session；不真实登录 QMT；不查账户；不写账户 | P0 | CR020-S01-windows-gateway-runtime-admission | CR020-W1-GATEWAY-RUNTIME-SESSION | `.env.example` 仅含 placeholder；credential leak 次数为 0；session_not_ready 时 query_positions adapter_call=0 | CP2-CR020 D2, D3 | `process/HLD.md` §36.4, §36.9, §36.10, §36.17 | ADR-088, ADR-089, ADR-090 |
| CR020-S03-linux-client-rest-transport | Linux C 端 REST transport 与 Python client | 冻结 Linux C 端 typed Python REST client、Typer CLI 验收面、request/response/error contract、timeout/retry 和 CLI 不承载业务运行边界 | `trading/qmt_client.py`、`trading/qmt_client_cli.py`、`tests/test_cr020_linux_client_rest_transport.py` | 不在 Linux C 侧导入 XtQuant；不把 CLI 当业务运行时；不启动 gateway；不读取凭据；不调用真实 QMT | P0 | CR020-S01-windows-gateway-runtime-admission | CR020-W2-CLIENT-AUTH | Python REST client 是业务唯一入口；CLI 100% 复用 client；Linux C 侧 XtQuant import 次数为 0 | CP2-CR020 D1, D2 | `process/HLD.md` §36.3, §36.5, §36.8, §36.17 | ADR-087, ADR-088, ADR-093 |
| CR020-S04-hmac-pairing-allowlist-scope | HMAC pairing / allowlist / scope / nonce fail-closed | 定义 S/C pairing、client id、HMAC headers、timestamp、nonce replay、allowlist、scope matrix、redaction 和 no-auth 禁止边界 | `trading/qmt_auth.py`、`trading/qmt_redaction.py`、`tests/test_cr020_hmac_pairing_allowlist_scope.py` | 不生成或记录真实 secret；不允许 no-auth 默认；不绕过 scope；不输出 pairing code、token、session、私钥或账号 | P0 | CR020-S01-windows-gateway-runtime-admission, CR020-S03-linux-client-rest-transport | CR020-W2-CLIENT-AUTH | HMAC 缺失/错误/过期、nonce replay、allowlist 不匹配、scope 不足时 adapter_call=0；敏感日志泄露次数为 0 | CP2-CR020 D4 | `process/HLD.md` §36.10, §36.11, §36.14, §36.17 | ADR-091 |
| CR020-S05-query-positions-readonly | `query_positions` 单接口只读准入 | 定义 CR-020 唯一真实只读查询接口、scope=`qmt:positions:read`、session/auth gate、response redaction、blocked endpoint matrix 和 failure reason | `trading/qmt_endpoint_matrix.py`、`trading/qmt_gateway_contracts.py`、`trading/qmt_gateway_service.py`、`trading/qmt_client.py`、`tests/test_cr020_query_positions_readonly.py` | 不启用其他 QMT endpoint；不执行订单/撤单/改单/账户写入；不 simulation/live；不写 broker lake；不输出未脱敏持仓敏感值 | P0 | CR020-S02-server-qmt-login-session, CR020-S03-linux-client-rest-transport, CR020-S04-hmac-pairing-allowlist-scope | CR020-W3-READONLY-POSITIONS | `query_positions` scope 固定为 `qmt:positions:read`；其他 endpoint blocked；order/cancel/account_write/broker_lake/provider/lake/publish 计数均为 0 | CP2-CR020 D5 | `process/HLD.md` §36.4, §36.9, §36.11, §36.17 | ADR-090, ADR-091, ADR-092 |
| CR020-S06-docs-runbook-cp7-real-machine-validation | 文档、runbook 与 CP7 实机只读验收边界 | 汇总 Windows S 端安装 / 启动前置、Linux C 端调用、pairing/HMAC、credential redaction、rollback、incident、CP7 实机只读验收证据和不授权声明 | `docs/QMT-GATEWAY-INSTALL.md`、`docs/QMT-C-S-BRIDGE-RUNBOOK.md`、`tests/test_cr020_docs_runbook_no_authorization.py` | 文档不写真实凭据；不把 CP3/CP4/CP5 设计确认写成运行授权；不授权交易、账户写入、simulation/live、provider/lake/publish | P1 | CR020-S01-windows-gateway-runtime-admission, CR020-S02-server-qmt-login-session, CR020-S03-linux-client-rest-transport, CR020-S04-hmac-pairing-allowlist-scope, CR020-S05-query-positions-readonly | CR020-W4-DOCS-REAL-MACHINE-VALIDATION | 文档覆盖 7 个 CP3 DQ、6 个 Story 边界和 no-real-operation 表；CP7 evidence 仅允许只读持仓查询；凭据泄露和真实交易授权声明次数为 0 | CP2-CR020 D6, D7 | `process/HLD.md` §36.14, §36.15, §36.17 | ADR-087..093 |

## Wave 分组

| Wave | 对应 HLD 阶段 | Story | 串并行策略 | 进入条件 | 退出条件 | 完成准则 |
|---|---|---|---|---|---|---|
| W0 | M0 - 数据准备与缓存可追溯 | STORY-001, STORY-002, STORY-003 | 串行；STORY-002/003 均依赖契约骨架，STORY-003 依赖 manifest/raw | HLD confirmed；Story 计划确认后方可进入 LLD | 三类 parquet、manifest、quality report 契约完成 | M0 产物支持后续 M1 离线读取 |
| W1 | M1 - 本地动量最小回测器 | STORY-004, STORY-005, STORY-006 | 串行；loader -> signal/portfolio -> metrics/report | W0 完成或用户提供合规 parquet/manifest/quality | 默认回测输出净值、指标和 metadata | 覆盖 2019-2025 的单次动量回测主路径 |
| W2 | M2 - 参数扫描与候选报告 | STORY-007, STORY-008 | 串行；扫描报告先于候选报告 | W1 完成 | 60 行扫描 CSV 和 <=4 候选 CSV | 第一版本地研究主路径闭环 |
| W3 | M3 - 真实性增强 | STORY-009, STORY-010, STORY-011, STORY-012 | 串行规划；为保持 5 个 Wave 与 M0-M4 一一对应，本轮不拆 M3 子 Wave | W2 完成；增强需求仍需 Story 计划确认 | 真实性限制可量化审计 | 增强不破坏 M0-M2 离线隔离 |
| W4 | M4 - 策略扩展 | STORY-013 | 单 Story 串行；当前计划按 Wave 顺序在 W3 后执行 | W3 完成；若后续人工确认重排，可在 W2 后单独执行 | RSI/MACD 等策略复用主契约 | 新策略不修改组合和指标主接口 |
| CR4-W0 | CR-004 契约阶段 | STORY-014 | 无上游依赖；可作为 CR-004 首个 CP5 批次 A 的 LLD 输入 | CP3/CP4 对 CR-004 增量确认通过 | `market_data/` 包骨架和数据湖契约稳定 | 下游 Story 可基于冻结 schema/source registry 设计 |
| CR4-W1 | CR-004 获取运行时 | STORY-015 | 依赖 STORY-014；LLD 可与 STORY-016 草案小批次评审，但开发需等待 STORY-014 契约冻结 | STORY-014 LLD 确认，schema/source registry 冻结 | fake connector、runtime、raw/manifest 写入完成 | fake/offline 获取闭环可被 normalization 消费 |
| CR4-W2 | CR-004 标准化读取 | STORY-016 | 依赖 STORY-015；开发默认串行，避免 manifest/canonical 契约冲突 | STORY-015 verified 或至少 manifest/raw contract frozen | canonical、quality、catalog、reader 完成 | reader 可供 CLI 和实验接入 |
| CR4-W3 | CR-004 操作闭环 | STORY-017 | 依赖 STORY-016；与 STORY-018 的 LLD 可在 reader 契约冻结后并行起草 | STORY-016 reader contract frozen | CLI offline smoke 与 fake/reference comparison 完成 | 默认路径 offline 可交给 QA 验证 |
| CR4-W4 | CR-004 实验接入 | STORY-018 | 依赖 STORY-016/017；开发应在 reader/CLI 稳定后执行，避免实验入口反复变更 | STORY-016 verified，STORY-017 comparison/CLI contract frozen | 实验十/十二只读接入路线和基准只读契约完成 | 后续可接入真实沪深 300 基准文件 |
| CR5-W0 | CR-005 Tushare 写湖边界 | CR005-S01 | 可与 CR005-S02 起草 LLD，但开发需等待 STORY-015 raw/manifest contract 和 source registry 稳定 | CP3/CP4 对 CR-005 增量确认通过；STORY-015 verified 或 contract frozen | Tushare 真实 source 显式启用边界、token env、plan/dry-run 和 `hs300_index` backfill job spec 稳定 | 下游 dataset normalization 和 benchmark resolver remediation spec 可引用数据层 job |
| CR5-W1 | CR-005 dataset schema/normalization | CR005-S02 | 依赖 CR005-S01 与 STORY-016；开发默认串行，避免 contracts/normalization 冲突 | CR005-S01 connector result/raw contract frozen；CR-004 canonical 基础已稳定 | 多 dataset schema、exact interface 映射、PIT 字段和 adjusted price normalization 稳定 | quality/catalog/readers 可按 dataset、PIT 和复权策略扩展 |
| CR5-W2 | CR-005 quality/catalog/readers | CR005-S03 | 依赖 CR005-S02；CR005-S04/S06 的 LLD 可在 PIT/复权/reader/hs300 quality contract 冻结后起草 | CR005-S02 dataset schema、PIT 字段、复权价格和 hs300 raw->canonical 契约 confirmed | 多 dataset quality CSV、catalog、readers、PIT as-of gate、复权一致 gate 和 hs300 accuracy gate 完成 | 实验基准和 Backtrader 可只读消费干净数据 |
| CR5-W3 | CR-005 本地基准 | CR005-S04 | 依赖 CR005-S01、CR005-S03 与 STORY-018；LLD 可基于冻结契约起草，开发需等 backfill job spec、reader quality、BenchmarkResult schema、benchmark policy 冻结 | `hs300_index` reader/quality contract frozen；CR005-S01 backfill job spec frozen；实验只读接入边界保留 | 基准 resolver 返回 typed `BenchmarkResult`，含 available/unavailable/required_missing/quality_failed、remediation spec、catalog/lineage | 实验十/十二可使用真实本地基准或结构化缺失，不联网、不静默代理 |
| CR5-W4 | CR-005 comparison/文档 | CR005-S05 | 依赖 CR005-S03；可与 CR005-S04 LLD 并行，开发需避开 CLI/job 主入口文件所有权 | quality/catalog/readers contract frozen；CR005-S01 backfill job spec frozen | comparison 输出与显式回补 runbook 完成 | 用户可安全执行真实回补准备；文档不把回补描述为消费层自动动作 |
| CR5-W5 | CR-005 Backtrader optional backend | CR005-S06 | LLD 可在 CR005-S02/S03/S04 contract frozen 后起草；开发必须等待 PIT/复权/quality/readers/benchmark verified | CR005-S02 PIT/复权契约 confirmed；CR005-S03 reader quality verified；CR005-S04 BenchmarkResult schema 与 benchmark policy frozen；CP5 批次 D 人工确认 | optional backend 可用或 structured unavailable，不影响轻量主路径 | Backtrader 对照报告只消费本地数据湖派生的干净 feed，不触发补数 |
| CR006-BATCH-A | CR-006 Tushare-first 数据方案 | CR006-S01-tushare-first-data-acquisition-runbook, CR006-S02-canonical-gold-lightweight-engine-adapter, CR006-S03-backtrader-clean-feed-contract, CR006-S04-old-data-reference-only-guardrail | LLD 可按 max_parallel_lld=3 分轮起草并统一确认；开发默认按 S01 -> S02 -> S03/S04 顺序；S04 对 S02/S03 是 contract 依赖，可在其契约冻结后收敛，不要求等待 S02/S03 CP6 runtime | CR-006 CP3/CP4 人工确认通过；不得触碰真实 `data/**` 或凭据；CR006-BATCH-A CP5 全量确认前不得实现 | 四张 Story 卡片、文件所有权、dev_gate、raw/manifest 审计边界和 old data reference-only guardrail 稳定 | Tushare-first structured lake 成为正式 LLD 输入；旧 `data/` 仍保持现状且不参与默认运行 |
| CR007-BATCH-A | CR-007 canonical 数据覆盖与真实 benchmark | CR007-S01-prices-long-horizon-backfill-planner, CR007-S02-benchmark-calendar-backfill, CR007-S03-index-members-stock-basic-datasets, CR007-S04-experiment-real-benchmark-consumption, CR007-S05-data-quality-report-and-doc-guardrail | LLD 可按 max_parallel_lld=3 分轮起草并统一确认；开发默认 S01 -> S02 -> S03 -> S04 -> S05；S02/S03 可并行起草 LLD，但因共享 `market_data/normalization.py`、`validation.py`、`readers.py` 默认不得并行开发；S05 依赖前四者合同冻结 | CR-007 CP3/CP4 人工确认通过；不得触碰 `.env`、真实 lake、旧 `data/**` 或旧报告内容；CP5 全量确认前不得实现 | 五张 Story 卡片、长期 coverage policy、benchmark/calendar gate、dataset readiness、实验消费与 legacy quality guardrail 稳定 | CR007-BATCH-A 可交给 meta-dev 生成全量 LLD，但不得实现 |
| CR008-BATCH-A | CR-008 研究级数据层口径硬化 | CR008-S01-research-input-contract-and-report-metadata, CR008-S02-proxy-real-benchmark-field-separation, CR008-S03-research-dataset-builder, CR008-S04-quality-adjustment-label-window-gates, CR008-S05-pit-universe-consumption-contract, CR008-S06-factor-research-auxiliary-data-contract | LLD 可按 max_parallel_lld=3 分轮起草并统一确认；开发默认 S01/S02 合同先行 -> S03 builder -> S04/S05 gates -> S06 辅助数据合同；S04/S05 可并行起草 LLD，但因共享 `engine/research_dataset.py` 默认不得并行开发 | CR-008 CP3/CP4 人工确认通过；不得实现 CR008；不得触碰 `.env`、真实 lake、旧 `data/**`、旧质量报告内容或凭据；CR008-BATCH-A CP5 全量确认前不得实现 | 六张 Story 卡片、`research_input_v1`、benchmark 字段隔离、builder 只读边界、quality/adjustment/label gate、PIT/fixed universe 与 auxiliary allowed claims 稳定 | CR008-BATCH-A 可交给 meta-dev 生成全量 LLD；CR007-S02 可并行实现，CR007-S04/S05 继续 hold 到 CR008 设计确认 |
| CR010-DL-BATCH-A | CR-010 数据湖基础生产化 | CR010-S01-multidataset-plan-run-publish-cli-contract, CR010-S02-prices-adj-factor-history-backfill-loop, CR010-S03-hs300-index-trade-calendar-backfill-loop, CR010-S04-index-members-weights-stock-basic-readiness, CR010-S05-catalog-coverage-production-readiness-report | LLD 可按 max_parallel_lld=3 分轮起草并统一确认；开发默认 S01 -> S02/S03/S04 -> S05；S02/S03/S04 共享 `contracts.py`、`normalization.py`、`validation.py`、`readers.py` 时默认不得并行开发 | CR-010 CP3/CP4 人工确认通过；CR009 关闭；不得真实抓取、真实 lake 写入、旧 `data/**` 操作或凭据读取；CP5 全量确认前不得实现 | multi-dataset pipeline 离线可验证；P0 dataset quality/catalog/readiness 可用；publish gate 可用 | 真实小窗口 smoke 需要用户另行授权 |
| CR010-DL-BATCH-B | CR-010 W3 数据契约与 fail-fast | CR010-S06-pit-source-interface-spike-readiness, CR010-S07-trade-status-contract-reader-fail-fast, CR010-S08-prices-limit-contract-gate-fail-fast, CR010-S09-events-available-at-contract-fail-fast | LLD 可并行起草；开发默认 S06 合同先行 -> S07/S08/S09；共享 `market_data/contracts.py`、`readers.py` 和 engine gate 文件时由 meta-po 判定文件无冲突后才可并行 | CR010-DL-BATCH-A 相关 reader/catalog 合同已冻结；未确认真实 source/interface 前不得接 provider | W3 source/interface 未确认时全链路 fail-fast；PIT/trade_status/prices_limit/events 不伪造可用 | exploratory 可 limitation；production_strict fail |
| CR010-QF-BATCH-C | CR-010 实验消费与真实性报告 | CR010-S10-realism-mode-research-metadata, CR010-S11-experiments-smoke-limitation-matrix, CR010-S12-backtrader-vectorbt-clean-feed-boundary | LLD 默认串行 S10 -> S11/S12；S11 改 `experiments/**`，S12 改 adapter，若文件无冲突可并行开发；任何真实 smoke 另走 QA 授权 | CR010-DL-BATCH-A/B 离线验证通过；`realism_mode` 合同确认；不得触发 backfill | 16 个 experiments fixture/offline 可在 exploratory 跑通；production_strict 对缺口正确 fail；optional backend clean feed 边界回归 | 真实 lake 小窗口/1 年 smoke 需用户授权 |
| CR010-OPS-BATCH-D | CR-010 备份、归档、恢复与保留策略 | CR010-S13-backup-archive-restore-env-manifest-contract, CR010-S14-backup-cli-dry-run-execute-verify-report, CR010-S15-restore-cli-drill-read-revalidate-replay, CR010-S16-retention-policy-archive-backup-cleanup | LLD 默认 S13 合同先行 -> S14/S15/S16；S14/S15/S16 可并行起草 LLD，开发需按文件所有权重新判定 | NFS hot/archive/backup/restore root 已就绪；DL-BATCH-A current truth/report 合同冻结；CP5 全量确认前不得实现 | backup/restore/retention CLI 默认 dry-run；`--execute` 才复制/恢复/删除；restore drill 网络调用 0；报告脱敏 | archive/backup/restore 可审计、可恢复、可 dry-run 验证 |
| CR011-DATA-BATCH-A | CR-011 数据与研究消费合同 | CR011-S01-real-benchmark-and-policy-consumption, CR011-S02-pit-universe-and-stock-lifecycle-completion, CR011-S03-tradability-status-and-price-limit-gates, CR011-S04-ohlcv-vwap-clean-execution-feed, CR011-S05-adjustment-and-corporate-action-audit, CR011-S06-industry-market-cap-style-exposure-data | LLD 可按 max_parallel_lld=3 分轮起草；CP5 必须等六张 LLD 和自动预检全部完成后统一确认；开发默认 S01/S02/S03/S05 合同先行，S04 依赖 S03，S06 依赖 S02/CR008-S06；共享 `engine/research_dataset.py` / `market_data/readers.py` 默认不得并行开发 | CR-011 CP3/CP4 通过；CR010-DL-BATCH-A verified；CR010-DL-BATCH-B / QF-BATCH-C 的相关合同至少冻结；不得真实联网、读凭据、写 lake、操作旧 data 或覆盖旧报告 | benchmark、PIT、tradability、execution、adjustment、exposure 六类门禁进入研究消费合同 | 新版实验 17-21 可基于门禁决定 exploratory / production_strict |
| CR011-RESEARCH-BATCH-B | CR-011 容量成本研究 | CR011-S07-liquidity-capacity-and-cost-sensitivity | 单 Story；LLD 等 CR011-DATA-BATCH-A 相关合同冻结后起草；开发需等 CP5-B approved 且 S03/S04/S06 依赖满足 | DATA-BATCH-A 的 tradability、execution、exposure 合同冻结；CP5-B 前不得实现 | 容量与成本敏感性报告合同稳定 | 报告固定四档成本网格并阻断缺流动性时的容量声明 |
| CR011-VALIDATION-BATCH-C | CR-011 因子面板审计与稳健性验证 | CR011-S08-factor-panel-audit-and-robust-validation | 单 Story；LLD 需消费前两批全部 Story 合同；开发需等 DATA-BATCH-A 与 RESEARCH-BATCH-B 对应 CP5 和依赖满足 | CR011-S01/S02/S05/S07 合同冻结；旧报告 forbidden path 生效；CP5-C 前不得实现 | factor panel audit 与 robust validation 报告合同稳定 | 新版报告版本化输出，不覆盖旧实验 17-21 baseline |
| CR013-BATCH-A | CR-013 unsupported data 与 claim boundary | CR013-S01-full-history-readiness-gap-register, CR013-S02-execution-vwap-claim-boundary, CR013-S03-unsupported-register-and-doc-refresh, CR013-S04-full-history-backfill-roadmap | LLD 可按 max_parallel_lld=3 分轮起草并统一确认；开发默认 S01/S02 合同先行 -> S03 声明刷新 -> S04 路线图。S01 与 S02 可并行起草 LLD；S03 依赖 S01/S02；S04 依赖 S01/S02。任何 Story 在 CP5 全量确认前不得实现 | CR-013 CP3/CP4 通过；CR011 closed 状态不回滚；只读 CR-013 证据文件；不得 provider fetch、读凭据、写真实 lake、读旧 data 或覆盖旧报告 | full-history blocked、execution/VWAP blocked、unsupported register excluded denominator 和 future backfill roadmap 合同稳定 | CR-013 后续 LLD / 实现只能在 CP5 全量确认和用户权限边界内推进 |
| CR014-W1-CONTRACTS | CR-014 全 A 与数据湖事实合同 | CR014-S01-a-share-universe-lifecycle-contract, CR014-S02-parquet-layout-manifest-catalog-publish-gate | LLD 可同批起草；开发必须 S01 合同冻结后再做 S02，避免 denominator / lifecycle 与 layout/catalog 字段冲突。CP5 前 implementation_allowed=false | CR-014 CP3 R2 已 approved；CP4 自动预检通过；本阶段真实 provider_fetch=0、lake_write=0、credential_read=0、duckdb_dependency_change=0 | universe/lifecycle/code-change 合同、Parquet layout、manifest、catalog current pointer 和 Explicit Publish Gate 合同稳定 | 下游 plan/run/normalize/validate/publish 与 DuckDB read-only 只能引用冻结合同，不得自行扩展事实源 |
| CR014-W2-PIPELINE | CR-014 P0 pipeline 与 DuckDB 只读候选层 | CR014-S03-p0-plan-run-normalize-validate-publish-contract, CR014-S04-duckdb-readonly-query-audit-parity-boundary | S03 先冻结 plan->run->normalize/replay->validate->publish 状态机；S04 在 S02/S03 合同冻结后收敛。DuckDB 依赖变更不进入 CP5 前范围 | S01/S02 合同冻结；CP5 前不得实现真实 Provider Adapter / Run Gate、不得写 raw/manifest/run metadata、不得改依赖 | CP5+显式授权后的单写者写湖边界、candidate/published 分离、DuckDB read-only query/audit/parity 读边界稳定 | DuckDB query/view/parity/report 反向成为 source of truth 次数必须为 0 |
| CR014-W3-AUDIT-OPS | CR-014 full-history readiness 与 replay/retention | CR014-S05-full-history-readiness-gap-claim-boundary, CR014-S06-incremental-refresh-replay-retention-contract | S05 消费 S01..S04 全部事实/候选边界；S06 消费 S02/S03 并可与 S05 并行起草 LLD。实现前由 CP5 重新判定文件所有权 | S01..S04 合同冻结；CP5 前不得读取旧 reports、旧 data、真实 lake 或凭据 | readiness matrix、gap register、claim boundary、incremental refresh、replay 和 retention candidate 策略稳定 | 任一 P0 gate 未通过时 full-A allowed claim 输出为 0；replay 不触发 provider、不写 raw、不改 current pointer |
| CR014-W4-CONSUMER-BOUNDARY | CR-014 研究消费与 unsupported 决策边界 | CR014-S07-research-consumer-readonly-docs-runbook-boundary, CR014-S08-w3-minute-tick-level2-vwap-blocked-decision-boundary | S07 依赖 S04/S05/S06；S08 依赖 S05。LLD 可并行起草，开发需避开 `engine/research_dataset.py` 与文档文件所有权冲突 | S05/S06 合同冻结；CP5 前不得修改 README/docs/代码/测试/报告 | 研究消费层只读 published current truth；docs/runbook 后续刷新范围、W3/minute/tick/Level2/VWAP unsupported/blocked 解除条件稳定 | research consumer 不直接 DuckDB 写入/发布/扫未发布 lake；unsupported claim 不被计入 allowed production claim |
| CR017-W1-ADJUSTMENT-CONTRACTS | CR-017 复权事实源与 policy 合同 | CR017-S01-adjustment-policy-requirements-and-adr-refresh, CR017-S02-raw-prices-and-adj-factor-contract-hardening | LLD 可先 S01 后 S02；开发默认串行，避免 `contracts.py` / `validation.py` 合同冲突 | CR-017 CP3 approved；CR014 catalog / publish 合同可引用；CP5 前真实抓取 / 写湖 / publish / 迁移均为 0 | policy enum、raw/factor schema、factor direction 和 legacy qfq 兼容合同稳定 | qfq/hfq 派生 Story 可引用冻结合同；QMT raw 执行价边界有上游事实 |
| CR017-W2-DERIVATION-READERS | CR-017 派生 view、reader 与质量门 | CR017-S03-qfq-hfq-derived-view-normalization, CR017-S04-reader-api-and-policy-gates, CR017-S05-validation-quality-parity-and-leakage-tests | LLD 可按 max_parallel_lld=3 同轮起草；开发默认 S03 -> S04 -> S05 串行，因共享 `normalization.py`、`readers.py`、`validation.py` | CR017-S02 合同冻结 | qfq/hfq/returns_adjusted 派生、single-policy reader 和 TS-017 测试矩阵稳定 | 同一研究 run 混用 raw/qfq/hfq blocked；复权价进入 QMT 执行价 allowed 次数为 0 |
| CR017-W3-CONSUMER-MIGRATION | CR-017 研究 / QMT 消费迁移边界 | CR017-S06-research-qmt-consumer-docs-and-migration-guide | 单 Story；LLD 需等 S04/S05 合同冻结；开发需与 CR015/CR016 文档共享文件串行合并 | CR017-S04/S05 合同冻结 | 研究消费矩阵、QMT raw-only handoff、legacy qfq migration guide 和 scale_up blocked claim 稳定 | CR017 未 verified 时 production adjustment governance claim 和 scale_up allowed 次数为 0 |
| CR015-W1-FOUNDATION-CONTRACTS | CR-015 QMT 环境与 adapter 合同 | CR015-S01-qmt-environment-and-interface-spike, CR015-S02-qmt-broker-adapter-contract | LLD 可与 CR017-W1 并行起草；开发 S01 -> S02，真实 adapter 依赖不进入本批默认范围 | CR-015 CP3 approved；CR017-S01 policy 合同可作为 raw execution 边界 | node role、transport、adapter mode、mock event 和 forbidden direct broker boundary 稳定 | 策略层直连 QMT / XtQuant 次数为 0；真实 order/cancel/account write 调用为 0 |
| CR015-W2-OMS-RISK-LAKE | CR-015 OMS、risk 与 broker lake | CR015-S03-oms-order-state-machine, CR015-S04-pretrade-risk-gate, CR015-S05-broker-lake-schema-and-writer | LLD 可按 S03/S04/S05 分轮；开发默认 S03 -> S04/S05 串行，因共享 `trading/oms.py` | CR015-S02 和 CR017 raw/policy 合同冻结 | order intent、状态机、hard risk、broker lake schema 和 dry-run writer 稳定 | 风控失败 adapter_calls=0；broker lake 未授权真实写入为 0 |
| CR015-W3-SHADOW-RUNBOOK | CR-015 shadow 闭环与 foundation runbook | CR015-S06-target-portfolio-to-order-intent-shadow-mode, CR015-S07-docs-and-foundation-runbook-boundary | LLD 可同批；开发 S06 后 S07，文档与 CR017/CR016 共享文件需串行合并 | CR015-S03/S04/S05、CR017-S04/S06 合同冻结 | target portfolio -> order intent -> risk -> mock event -> dry-run plan 闭环和 foundation runbook 稳定 | CR015 foundation 只允许 shadow / dry-run / mock；真实操作计数均为 0 |
| CR016-W1-SIMULATION-OPS-GATES | CR-016 simulation、reconciliation、monitoring、runbook | CR016-S01-simulation-account-order-enable-gate, CR016-S02-reconciliation-service-and-reports, CR016-S03-monitoring-heartbeat-and-kill-switch, CR016-S04-simulation-live-runbook-and-approval-gates | LLD 可按 max_parallel_lld=3 分两轮；开发必须等待 CR015 foundation verified，并默认 S01 -> S02 -> S03 -> S04 串行 | CR015-S07 和 CR017-S06 合同冻结；真实运行仍需后续 per-run 授权 | simulation gate、reconciliation、kill switch 和 approval runbook 合同稳定 | 阶段不可跳过；无完整授权时真实调用为 0 |
| CR016-W2-LIVE-SCALE-DOCS-GATED | CR-016 live_readonly / small_live / scale_up later-gated | CR016-S05-live-readonly-and-small-live-admission, CR016-S06-scale-up-and-research-maturity-gates, CR016-S07-docs-user-manual-and-incident-playbooks | LLD 可设计但开发为 later-gated；small_live 和 scale_up 不属于当前可直接实现项 | CR016-S04 合同冻结；CR017 verified 是 scale_up 前置；用户后续显式授权真实运行 | live_readonly / small_live / scale_up gate 和 incident playbook 设计稳定 | CR017 未 verified 时 scale_up allowed 次数为 0；真实 VWAP/minute/tick/Level2/order-match blocked claim 不解除 |
| CR018-W1-SCOPE-CONTRACT | CR-018 release scope 与 dataset group | CR018-S01-production-current-truth-definition-and-dataset-groups | 单 Story 串行；作为后续 P0/P1 readiness、publish 和 research rerun 的合同前置 | CR018 CP3 approved；CR018-S01 LLD/CP5 approved 前不得实现 | current truth scoped release、P0/P1 group、claim matrix 稳定 | D1-D4 CP2 决策 100% 回写到合同；真实操作计数为 0 |
| CR018-W2-P0-P1-READINESS | CR-018 P0/P1 dataset readiness | CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill, CR018-S03-real-benchmark-index-components-weights-backfill, CR018-S04-industry-market-cap-liquidity-and-exposure-data, CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness | LLD 可并行起草；开发因共享 `market_data/contracts.py`、`validation.py`、`readers.py` 默认串行或由 LLD 指定 merge_owner；S04 为 P1，不阻断 P0 core release，但阻断对应声明 | CR018-S01 合同冻结；CR017-S05 复权质量合同可引用 | P0 readiness 可汇入 publish gate；P1 blocked claims 可汇入 research/QMT gate | P0 fail 时 production current truth allowed 次数为 0；P1 缺失时中性化 / pure alpha / capacity / scale_up allowed claim 为 0 |
| CR018-W3-PUBLISH-ROLLBACK | CR-018 Explicit Publish Gate 与 rollback | CR018-S06-production-quality-readiness-audit-and-rollback-gate, CR018-S07-explicit-publish-gate-and-current-reader-smoke | 串行；S06 聚合 readiness 和 rollback contract，S07 才能定义 publish/current reader smoke | CR018-W2 P0 readiness contract stable；CP5 approved 前不得真实 publish | release-level publish/rollback 与 current reader smoke 设计稳定 | validate 自动 publish 次数为 0；rollback 粒度保持 release-level |
| CR018-W4-RERUN-QMT-ADMISSION | CR-018 published truth research rerun 与 QMT admission | CR018-S08-production-current-truth-research-rerun, CR018-S09-qmt-simulation-admission-boundary-after-data-lake | 串行；S08 published release 研究重跑 PASS 是 S09 QMT admission 的前置；S09 不授权真实 QMT | CR018-S07 publish gate 合同冻结；CR015/016/017 foundation 只作为技术前置，不替代 S08 PASS | production rerun 与 QMT blocked reason 设计稳定 | S08 未 PASS 时 QMT simulation/live_readonly/small_live/scale_up allowed 次数为 0 |
| CR019-W1-ADMISSION-BENCHMARK | CR-019 阶段六 admission 与 benchmark | CR019-S01-stage6-admission-gate-package, CR019-S02-primary-benchmark-dashboard | LLD 可同批起草；开发默认 S01 -> S02，避免 admission package 与 benchmark 字段漂移 | CP3 approved；CR018-S08 verified；CR016 runbook / stage gate 作为只读输入 | admission gate、旧失败 blocked evidence、多基准和 primary benchmark 合同稳定 | 任一 P0 gate 未过时 admission blocked；旧失败策略 ready 次数为 0 |
| CR019-W2-CS-TRANSPORT | CR-019 QMT C/S transport 基础 | CR019-S03-qmt-cside-client-cli-contract, CR019-S04-windows-gateway-lifecycle-deployment | LLD 可并行起草；开发默认 S03 C 侧合同先行，S04 基于 client / REST contract 收敛 gateway 生命周期 | CP3 approved；CR015/016 foundation 只作为只读合同输入；CP5 前不得实现 | C 侧 Python client / 薄 CLI 与 Windows gateway lifecycle / bind / firewall 合同稳定 | C 侧 xtquant import 次数为 0；gateway 服务启动次数为 0 |
| CR019-W3-AUTH-ENDPOINT-GATE | CR-019 鉴权、endpoint matrix 与运行门控 | CR019-S05-pairing-hmac-auth-redaction, CR019-S06-qmt-endpoint-matrix-contract, CR019-S07-run-gate-blocked-reason-integration | LLD 可按 max_parallel_lld=3 同轮起草；开发默认 S05 -> S06 -> S07，避免 auth header、endpoint schema 和 gate reason 冲突 | CR019-W1/W2 合同冻结；CR015 risk / CR016 kill-switch / stage gate 可引用 | pairing/HMAC、完整 endpoint matrix、typed blocked result 和 run gate 分离稳定 | HMAC pass 不授权交易；缺任一 gate 时真实 QMT / account / order / cancel 调用为 0 |
| CR019-W4-FALLBACK-DEFERRED | CR-019 fallback / incident 与后置能力 | CR019-S08-fallback-incident-signed-file-boundary, CR019-S09-deferred-capability-register | LLD 可并行起草；S08 开发需等 W3 gate 合同冻结；S09 仅定义后置 register，不新增依赖 | CR019-W1/W3 合同冻结；CP5 前不得改 docs 或代码 | fail-closed fallback、signed file dry-run、Backtrader/Qlib/minute/Level2 deferred register 稳定 | fallback 自动真实 QMT 次数为 0；后置能力进入 P0 次数为 0 |
| CR019-W5-DOCS-RUNBOOK | CR-019 文档 / runbook 收敛 | CR019-S10-docs-runbook-user-manual-boundary | 单 Story；需等待 S01..S09 合同冻结后起草 LLD；开发需与既有 README / USER-MANUAL / QMT runbook 文件所有权串行合并 | CR019-S01..S09 Story 合同冻结；CP5 全量确认后才能实现 | 用户手册、README、QMT C/S bridge runbook 和 incident 边界稳定 | 文档不得写成真实 operation authorization；敏感值泄露次数为 0 |
| CR025-W1-FEED-GOVERNANCE | CR-025 clean feed 与 license governance | CR025-S01-clean-feed-gate-backend-selector, CR025-S04-backtrader-module-reference-no-copy-guardrail | LLD 可并行起草；开发可并行但需避开 `engine/backtrader_adapter.py` 与文档/测试文件冲突；二者共同冻结 optional runtime 输入边界、execution semantic reference 口径和 GPLv3 no-copy forbidden path | CR-025 CP3 approved；CR005/CR006 Backtrader clean feed 与 optional backend 既有合同可引用；CP5 前不得实现；多因子研究闭环另起后续 CR | clean feed gate、backend selector、structured unavailable、module reference matrix 和 no-copy guardrail 稳定 | 默认 Backtrader import 次数为 0；源码复制 / 移植项为 0；Backtrader 承接 FactorSpec / IC / RankIC 等多因子能力次数为 0；真实操作计数均为 0 |
| CR025-W2-SEMANTIC-DIFF | CR-025 semantic diff artifact | CR025-S02-semantic-diff-schema-artifact | 单 Story；依赖 W1 的 feed / no-copy 合同；LLD 冻结 diff schema、artifact 路径、字段枚举和 limitations；不新增 factor tear sheet / IC report | CR025-S01/S04 Story 合同冻结；CP5 前不得运行 Backtrader 或生成真实报告；FactorSpec / IC / RankIC / 分层收益等研究评价合同不属于本 Wave | semantic diff schema 与 artifact contract 稳定 | 至少 10 类执行语义 diff 字段；reference 不覆盖 baseline；research comparison 标签必填；多因子研究闭环字段实现项为 0 |
| CR025-W3-ORDER-INTENT-QMT | CR-025 order intent draft / QMT handoff | CR025-S03-order-intent-draft-qmt-boundary | 单 Story；依赖 semantic diff 合同和既有 QMT OMS / shadow order intent 合同；开发需与 `trading/oms.py` 保持只读或串行 | CR025-S02 合同冻结；CR015/CR017 相关 order intent / raw execution policy 合同可引用；不继承 QMT 运行授权 | `order_intent_draft_v1` 字段、失败路径和 QMT later-gated 边界稳定 | draft 字段覆盖率 100%；非 raw execution blocked；QMT / broker lake 操作计数为 0 |
| CR025-W4-SAFETY-VERIFICATION-DOCS | CR-025 安全验证与路线文档 | CR025-S05-no-real-operation-safety-verification, CR025-S06-route-docs-and-follow-up-handoff | LLD 可并行起草；S05 拥有测试矩阵，S06 拥有文档收敛；开发需串行合并 README / USER-MANUAL，且 CP5 前 implementation_allowed=false | CR025-S01..S04 Story 合同冻结；CR019 deferred register 可引用；CP5 全量确认后才能实现；多因子研究闭环只登记后续 CR 候选 | fixture-only 验证矩阵、forbidden scan、QMT 后续路线、后续多因子研究 CR 边界和用户文档边界稳定 | TS-025-01..11 覆盖；dependency/Backtrader run/source copy/real operation/credential 计数均为 0；CR-025 文档声称交付多因子研究主框架次数为 0 |
| CR030-W1-CONTRACT-GOVERNANCE | CR-030 外部矩阵与核心合同治理 | CR030-S01-external-reference-matrix-and-loop-contract, CR030-S02-factor-spec-run-spec-contract | LLD 可并行起草但 S02 需消费 S01 的 reference matrix / no-real-operation 术语；开发默认 S01 -> S02，避免外部项目边界和 schema provenance 漂移 | CR-030 CP3 approved；CP4 前不实现；不授权外部项目运行、依赖变更、源码迁移、provider/lake/publish、QMT 或凭据读取 | 外部矩阵、自有闭环主线、CR-026 后置条件、FactorSpec / FactorRunSpec 合同稳定 | 10 类外部项目分类完整；FactorSpec / FactorRunSpec P0 字段覆盖率 100%；外部默认 truth / runner / provider 次数为 0 |
| CR030-W2-PANEL-EVALUATION | CR-030 面板 / 标签与单因子评价 | CR030-S03-factor-panel-label-window-fail-closed, CR030-S04-factor-evaluation-report | S03 是 S04 的 contract 前置；LLD 可在 S02 合同冻结后分轮起草，开发默认 S03 -> S04，因共享 factor panel / evaluation 输入语义 | CR030-S02 合同冻结；CR011 factor panel audit 可只读引用；CP5 前不得实现或改报告 | FactorPanelContract、LabelWindowSpec、leakage gate、FactorEvaluationReport 和 blocked claims 稳定 | 前视 / label overlap / lineage / 复权混用 fail-closed；报告字段覆盖 REQ-178；生产有效声明误用为 0 |
| CR030-W3-COMBINATION-MANIFEST | CR-030 多因子组合与研究追踪 | CR030-S05-multifactor-combiner-portfolio-plan, CR030-S06-experiment-manifest-report-catalog | LLD 可并行起草；S05 依赖 S04 报告，S06 依赖 S04 报告并为 S07 提供 manifest/catalog；开发需按文件 owner 避免 `reports/**` 合并冲突 | CR030-S04 评价合同冻结；optimizer / ML workflow 后置 | MultiFactorCombiner、MultiFactorPortfolioPlan、ExperimentManifest 和 ResearchReportCatalog 合同稳定 | P0 组合不引入 optimizer；manifest/catalog P0 字段覆盖率 100%；旧报告覆盖和 publish 次数为 0 |
| CR030-W4-ADMISSION-SAFETY-DOCS | CR-030 准入包、安全验证与文档 | CR030-S07-strategy-admission-package-handoff, CR030-S08-safety-docs-and-follow-up-boundary | S07 依赖 S05/S06 以及 CR019/CR025 只读合同；S08 聚合 S01..S07。LLD 可在全量批次中分轮起草，开发默认 S07 -> S08 串行合并 docs / README / USER-MANUAL | CR030-S05/S06 合同冻结；CR019 admission 与 CR025 order intent draft 可引用；CP5 前不得实现或授权真实操作 | StrategyAdmissionPackage、`order_intent_draft_v1` draft handoff、no-real-operation safety、CR-026/optimizer 后续 Spike 和文档边界稳定 | admission blocked reason 完整；QMT/API/order/account/provider/lake/publish/credential 计数均为 0；文档声称 CR-030 授权真实操作次数为 0 |
| CR020-W1-GATEWAY-RUNTIME-SESSION | CR-020 Windows gateway runtime 与 session | CR020-S01-windows-gateway-runtime-admission, CR020-S02-server-qmt-login-session | LLD 可并行起草，但 S02 必须消费 S01 的 gateway lifecycle / config / admission 合同；开发默认 S01 -> S02，避免 gateway runtime 与 session ready gate 冲突 | CR-020 CP3 approved；CP4 只做规划；CP5 前 implementation_allowed=false，且不启动服务、不绑定端口、不连接 QMT、不读真实 `.env` | Windows S 端 Typer CLI、gateway lifecycle/config、QMT login/session ready gate 和 redacted credential_ref 合同稳定 | gateway lifecycle/config 字段覆盖率 100%；session_not_ready 阻断 query；service_start/port_bind/qmt_call/credential_read 均为 0 |
| CR020-W2-CLIENT-AUTH | CR-020 Linux client transport 与鉴权 | CR020-S03-linux-client-rest-transport, CR020-S04-hmac-pairing-allowlist-scope | LLD 可按 Story/file owner 并行起草；开发默认 S03 client contract 先行，S04 在 client headers / auth contract 稳定后收敛，避免 request schema 与 HMAC header 漂移 | CR020-S01 runtime 合同冻结；CP5 前不得实现、不得改依赖、不得读取凭据或执行真实请求 | Linux C 端 Python REST client、Typer CLI 验收面、pairing/HMAC、allowlist、scope、nonce 和 redaction 合同稳定 | Linux C 端 XtQuant import 次数为 0；HMAC / scope / nonce / allowlist fail-closed；敏感值泄露次数为 0 |
| CR020-W3-READONLY-POSITIONS | CR-020 持仓只读查询准入 | CR020-S05-query-positions-readonly | 单 Story；LLD 必须消费 S02 session ready、S03 REST client 和 S04 auth/scope 合同；开发需在三个上游合同冻结且 CP5 confirmed 后才可实现 | CR020-S02/S03/S04 合同冻结；CP5 前不得执行 query、不得连接 QMT、不得输出真实持仓或账户敏感值 | `query_positions` 单接口、scope=`qmt:positions:read`、blocked endpoint matrix、response redaction 和 failure reason 合同稳定 | 除 `query_positions` 外真实 endpoint allowed 次数为 0；order/cancel/account_write/broker_lake/provider/lake/publish/simulation/live 计数均为 0 |
| CR020-W4-DOCS-REAL-MACHINE-VALIDATION | CR-020 文档、runbook 与 CP7 实机只读验收 | CR020-S06-docs-runbook-cp7-real-machine-validation | 单 Story；需等待 S01..S05 合同冻结后起草 LLD；开发需与既有 README / USER-MANUAL / QMT runbook 文件所有权串行合并；CP7 真实机器验证必须另由 meta-po / meta-qa 按授权门控发起 | CR020-S01..S05 Story 合同冻结；CP5 全量 LLD 确认后才能实现；CP7 前不得把文档当作运行授权 | QMT gateway install/runbook、C/S bridge runbook、credential redaction、rollback/incident、CP7 read-only evidence 和不授权声明稳定 | 文档覆盖 7 个 CP3 DQ、6 个 Story 边界和 no-real-operation 表；凭据泄露、交易授权声明、simulation/live 授权声明匹配次数为 0 |

## 依赖 DAG 摘要

```mermaid
graph TD
  STORY-001 --> STORY-002
  STORY-001 --> STORY-003
  STORY-002 --> STORY-003
  STORY-003 --> STORY-004
  STORY-004 --> STORY-005
  STORY-005 --> STORY-006
  STORY-006 --> STORY-007
  STORY-007 --> STORY-008
  STORY-008 --> STORY-009
  STORY-009 --> STORY-010
  STORY-009 --> STORY-011
  STORY-010 --> STORY-011
  STORY-010 --> STORY-012
  STORY-011 --> STORY-012
  STORY-008 --> STORY-013
  STORY-014 --> STORY-015
  STORY-015 --> STORY-016
  STORY-016 --> STORY-017
  STORY-016 --> STORY-018
  STORY-017 --> STORY-018
  STORY-015 --> CR005-S01
  STORY-016 --> CR005-S02
  CR005-S01 --> CR005-S02
  CR005-S02 --> CR005-S03
  CR005-S01 --> CR005-S04
  STORY-018 --> CR005-S04
  CR005-S03 --> CR005-S04
  CR005-S03 --> CR005-S05
  CR005-S02 --> CR005-S06
  CR005-S03 --> CR005-S06
  CR005-S04 --> CR005-S06
  CR005-S01 --> CR006-S01
  CR005-S02 --> CR006-S01
  CR005-S03 --> CR006-S01
  CR006-S01 --> CR006-S02
  CR005-S03 --> CR006-S02
  CR006-S01 --> CR006-S03
  CR006-S02 --> CR006-S03
  CR005-S06 --> CR006-S03
  CR006-S01 --> CR006-S04
  CR006-S02 --> CR006-S04
  CR006-S03 --> CR006-S04
  CR006-S01 --> CR007-S01
  CR005-S02 --> CR007-S01
  CR005-S03 --> CR007-S01
  CR007-S01 --> CR007-S02
  CR005-S04 --> CR007-S02
  CR007-S01 --> CR007-S03
  CR005-S02 --> CR007-S03
  CR005-S03 --> CR007-S03
  CR007-S02 --> CR007-S04
  CR007-S03 --> CR007-S04
  CR007-S01 --> CR007-S05
  CR007-S02 --> CR007-S05
  CR007-S03 --> CR007-S05
  CR007-S04 --> CR007-S05
  CR007-S02 --> CR008-S01
  CR007-S02 --> CR008-S02
  CR008-S01 --> CR008-S02
  CR008-S01 --> CR008-S03
  CR008-S02 --> CR008-S03
  CR008-S03 --> CR008-S04
  CR007-S03 --> CR008-S05
  CR008-S03 --> CR008-S05
  CR008-S03 --> CR008-S06
  CR008-S04 --> CR008-S06
  CR008-S05 --> CR008-S06
  CR009-CLOSED --> CR010-S01
  CR007-S01 --> CR010-S01
  CR007-S02 --> CR010-S01
  CR010-S01 --> CR010-S02
  CR010-S01 --> CR010-S03
  CR010-S01 --> CR010-S04
  CR007-S02 --> CR010-S03
  CR007-S03 --> CR010-S04
  CR010-S02 --> CR010-S05
  CR010-S03 --> CR010-S05
  CR010-S04 --> CR010-S05
  CR010-S04 --> CR010-S06
  CR010-S06 --> CR010-S07
  CR010-S06 --> CR010-S08
  CR010-S06 --> CR010-S09
  CR010-S05 --> CR010-S10
  CR010-S07 --> CR010-S10
  CR010-S08 --> CR010-S10
  CR010-S09 --> CR010-S10
  CR010-S10 --> CR010-S11
  CR010-S10 --> CR010-S12
  CR010-S05 --> CR010-S13
  CR010-S13 --> CR010-S14
  CR010-S13 --> CR010-S15
  CR010-S14 --> CR010-S15
  CR010-S13 --> CR010-S16
  CR010-S03 --> CR011-S01
  CR010-S05 --> CR011-S01
  CR008-S02 --> CR011-S01
  CR010-S04 --> CR011-S02
  CR010-S06 --> CR011-S02
  CR008-S05 --> CR011-S02
  CR010-S07 --> CR011-S03
  CR010-S08 --> CR011-S03
  CR010-S09 --> CR011-S03
  CR011-S02 --> CR011-S03
  CR011-S03 --> CR011-S04
  CR010-S02 --> CR011-S04
  CR010-S02 --> CR011-S05
  CR008-S04 --> CR011-S05
  CR008-S06 --> CR011-S06
  CR011-S02 --> CR011-S06
  CR011-S03 --> CR011-S07
  CR011-S04 --> CR011-S07
  CR011-S06 --> CR011-S07
  CR011-S01 --> CR011-S08
  CR011-S02 --> CR011-S08
  CR011-S05 --> CR011-S08
  CR011-S07 --> CR011-S08
  CR011-S08 --> CR013-S01
  CR011-S04 --> CR013-S02
  CR013-S01 --> CR013-S03
  CR013-S02 --> CR013-S03
  CR013-S01 --> CR013-S04
  CR013-S02 --> CR013-S04
  CR014-S01-a-share-universe-lifecycle-contract --> CR014-S02-parquet-layout-manifest-catalog-publish-gate
  CR014-S01-a-share-universe-lifecycle-contract --> CR014-S03-p0-plan-run-normalize-validate-publish-contract
  CR014-S02-parquet-layout-manifest-catalog-publish-gate --> CR014-S03-p0-plan-run-normalize-validate-publish-contract
  CR014-S02-parquet-layout-manifest-catalog-publish-gate --> CR014-S04-duckdb-readonly-query-audit-parity-boundary
  CR014-S03-p0-plan-run-normalize-validate-publish-contract --> CR014-S04-duckdb-readonly-query-audit-parity-boundary
  CR014-S01-a-share-universe-lifecycle-contract --> CR014-S05-full-history-readiness-gap-claim-boundary
  CR014-S02-parquet-layout-manifest-catalog-publish-gate --> CR014-S05-full-history-readiness-gap-claim-boundary
  CR014-S03-p0-plan-run-normalize-validate-publish-contract --> CR014-S05-full-history-readiness-gap-claim-boundary
  CR014-S04-duckdb-readonly-query-audit-parity-boundary --> CR014-S05-full-history-readiness-gap-claim-boundary
  CR014-S02-parquet-layout-manifest-catalog-publish-gate --> CR014-S06-incremental-refresh-replay-retention-contract
  CR014-S03-p0-plan-run-normalize-validate-publish-contract --> CR014-S06-incremental-refresh-replay-retention-contract
  CR014-S04-duckdb-readonly-query-audit-parity-boundary --> CR014-S07-research-consumer-readonly-docs-runbook-boundary
  CR014-S05-full-history-readiness-gap-claim-boundary --> CR014-S07-research-consumer-readonly-docs-runbook-boundary
  CR014-S06-incremental-refresh-replay-retention-contract --> CR014-S07-research-consumer-readonly-docs-runbook-boundary
  CR014-S05-full-history-readiness-gap-claim-boundary --> CR014-S08-w3-minute-tick-level2-vwap-blocked-decision-boundary
  CR014-S01-a-share-universe-lifecycle-contract --> CR014-S09-windowed-real-fetch-lake-write-run
  CR014-S02-parquet-layout-manifest-catalog-publish-gate --> CR014-S09-windowed-real-fetch-lake-write-run
  CR014-S03-p0-plan-run-normalize-validate-publish-contract --> CR014-S09-windowed-real-fetch-lake-write-run
  CR014-S04-duckdb-readonly-query-audit-parity-boundary --> CR014-S09-windowed-real-fetch-lake-write-run
  CR014-S05-full-history-readiness-gap-claim-boundary --> CR014-S09-windowed-real-fetch-lake-write-run
  CR014-S06-incremental-refresh-replay-retention-contract --> CR014-S09-windowed-real-fetch-lake-write-run
  CR014-S07-research-consumer-readonly-docs-runbook-boundary --> CR014-S09-windowed-real-fetch-lake-write-run
  CR014-S08-w3-minute-tick-level2-vwap-blocked-decision-boundary --> CR014-S09-windowed-real-fetch-lake-write-run
  CR014-S02-parquet-layout-manifest-catalog-publish-gate --> CR017-S01-adjustment-policy-requirements-and-adr-refresh
  CR017-S01-adjustment-policy-requirements-and-adr-refresh --> CR017-S02-raw-prices-and-adj-factor-contract-hardening
  CR010-S02 --> CR017-S02-raw-prices-and-adj-factor-contract-hardening
  CR017-S02-raw-prices-and-adj-factor-contract-hardening --> CR017-S03-qfq-hfq-derived-view-normalization
  CR017-S03-qfq-hfq-derived-view-normalization --> CR017-S04-reader-api-and-policy-gates
  CR017-S02-raw-prices-and-adj-factor-contract-hardening --> CR017-S05-validation-quality-parity-and-leakage-tests
  CR017-S03-qfq-hfq-derived-view-normalization --> CR017-S05-validation-quality-parity-and-leakage-tests
  CR017-S04-reader-api-and-policy-gates --> CR017-S05-validation-quality-parity-and-leakage-tests
  CR017-S04-reader-api-and-policy-gates --> CR017-S06-research-qmt-consumer-docs-and-migration-guide
  CR017-S05-validation-quality-parity-and-leakage-tests --> CR017-S06-research-qmt-consumer-docs-and-migration-guide
  CR015-S01-qmt-environment-and-interface-spike --> CR015-S02-qmt-broker-adapter-contract
  CR017-S01-adjustment-policy-requirements-and-adr-refresh --> CR015-S02-qmt-broker-adapter-contract
  CR015-S02-qmt-broker-adapter-contract --> CR015-S03-oms-order-state-machine
  CR017-S01-adjustment-policy-requirements-and-adr-refresh --> CR015-S03-oms-order-state-machine
  CR015-S03-oms-order-state-machine --> CR015-S04-pretrade-risk-gate
  CR017-S02-raw-prices-and-adj-factor-contract-hardening --> CR015-S04-pretrade-risk-gate
  CR017-S04-reader-api-and-policy-gates --> CR015-S04-pretrade-risk-gate
  CR015-S03-oms-order-state-machine --> CR015-S05-broker-lake-schema-and-writer
  CR015-S03-oms-order-state-machine --> CR015-S06-target-portfolio-to-order-intent-shadow-mode
  CR015-S04-pretrade-risk-gate --> CR015-S06-target-portfolio-to-order-intent-shadow-mode
  CR015-S05-broker-lake-schema-and-writer --> CR015-S06-target-portfolio-to-order-intent-shadow-mode
  CR017-S04-reader-api-and-policy-gates --> CR015-S06-target-portfolio-to-order-intent-shadow-mode
  CR015-S01-qmt-environment-and-interface-spike --> CR015-S07-docs-and-foundation-runbook-boundary
  CR015-S02-qmt-broker-adapter-contract --> CR015-S07-docs-and-foundation-runbook-boundary
  CR015-S03-oms-order-state-machine --> CR015-S07-docs-and-foundation-runbook-boundary
  CR015-S04-pretrade-risk-gate --> CR015-S07-docs-and-foundation-runbook-boundary
  CR015-S05-broker-lake-schema-and-writer --> CR015-S07-docs-and-foundation-runbook-boundary
  CR015-S06-target-portfolio-to-order-intent-shadow-mode --> CR015-S07-docs-and-foundation-runbook-boundary
  CR017-S06-research-qmt-consumer-docs-and-migration-guide --> CR015-S07-docs-and-foundation-runbook-boundary
  CR015-S07-docs-and-foundation-runbook-boundary --> CR016-S01-simulation-account-order-enable-gate
  CR017-S06-research-qmt-consumer-docs-and-migration-guide --> CR016-S01-simulation-account-order-enable-gate
  CR015-S03-oms-order-state-machine --> CR016-S02-reconciliation-service-and-reports
  CR015-S05-broker-lake-schema-and-writer --> CR016-S02-reconciliation-service-and-reports
  CR016-S01-simulation-account-order-enable-gate --> CR016-S02-reconciliation-service-and-reports
  CR015-S02-qmt-broker-adapter-contract --> CR016-S03-monitoring-heartbeat-and-kill-switch
  CR015-S03-oms-order-state-machine --> CR016-S03-monitoring-heartbeat-and-kill-switch
  CR016-S02-reconciliation-service-and-reports --> CR016-S03-monitoring-heartbeat-and-kill-switch
  CR016-S01-simulation-account-order-enable-gate --> CR016-S04-simulation-live-runbook-and-approval-gates
  CR016-S02-reconciliation-service-and-reports --> CR016-S04-simulation-live-runbook-and-approval-gates
  CR016-S03-monitoring-heartbeat-and-kill-switch --> CR016-S04-simulation-live-runbook-and-approval-gates
  CR016-S04-simulation-live-runbook-and-approval-gates --> CR016-S05-live-readonly-and-small-live-admission
  CR015-S07-docs-and-foundation-runbook-boundary --> CR016-S05-live-readonly-and-small-live-admission
  CR016-S05-live-readonly-and-small-live-admission --> CR016-S06-scale-up-and-research-maturity-gates
  CR017-S06-research-qmt-consumer-docs-and-migration-guide --> CR016-S06-scale-up-and-research-maturity-gates
  CR011-S08 --> CR016-S06-scale-up-and-research-maturity-gates
  CR016-S04-simulation-live-runbook-and-approval-gates --> CR016-S07-docs-user-manual-and-incident-playbooks
  CR016-S05-live-readonly-and-small-live-admission --> CR016-S07-docs-user-manual-and-incident-playbooks
  CR016-S06-scale-up-and-research-maturity-gates --> CR016-S07-docs-user-manual-and-incident-playbooks
  CR014-S09-windowed-real-fetch-lake-write-run --> CR018-S01-production-current-truth-definition-and-dataset-groups
  CR018-S01-production-current-truth-definition-and-dataset-groups --> CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill
  CR018-S01-production-current-truth-definition-and-dataset-groups --> CR018-S03-real-benchmark-index-components-weights-backfill
  CR018-S01-production-current-truth-definition-and-dataset-groups --> CR018-S04-industry-market-cap-liquidity-and-exposure-data
  CR018-S01-production-current-truth-definition-and-dataset-groups --> CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness
  CR017-S05-validation-quality-parity-and-leakage-tests --> CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness
  CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill --> CR018-S06-production-quality-readiness-audit-and-rollback-gate
  CR018-S03-real-benchmark-index-components-weights-backfill --> CR018-S06-production-quality-readiness-audit-and-rollback-gate
  CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness --> CR018-S06-production-quality-readiness-audit-and-rollback-gate
  CR018-S06-production-quality-readiness-audit-and-rollback-gate --> CR018-S07-explicit-publish-gate-and-current-reader-smoke
  CR018-S07-explicit-publish-gate-and-current-reader-smoke --> CR018-S08-production-current-truth-research-rerun
  CR018-S08-production-current-truth-research-rerun --> CR018-S09-qmt-simulation-admission-boundary-after-data-lake
  CR015-S07-docs-and-foundation-runbook-boundary --> CR018-S09-qmt-simulation-admission-boundary-after-data-lake
  CR016-S04-simulation-live-runbook-and-approval-gates --> CR018-S09-qmt-simulation-admission-boundary-after-data-lake
  CR018-S08-production-current-truth-research-rerun --> CR019-S01-stage6-admission-gate-package
  CR016-S04-simulation-live-runbook-and-approval-gates --> CR019-S01-stage6-admission-gate-package
  CR019-S01-stage6-admission-gate-package --> CR019-S02-primary-benchmark-dashboard
  CR018-S03-real-benchmark-index-components-weights-backfill --> CR019-S02-primary-benchmark-dashboard
  CR015-S02-qmt-broker-adapter-contract --> CR019-S03-qmt-cside-client-cli-contract
  CR016-S04-simulation-live-runbook-and-approval-gates --> CR019-S03-qmt-cside-client-cli-contract
  CR019-S03-qmt-cside-client-cli-contract --> CR019-S04-windows-gateway-lifecycle-deployment
  CR019-S03-qmt-cside-client-cli-contract --> CR019-S05-pairing-hmac-auth-redaction
  CR019-S04-windows-gateway-lifecycle-deployment --> CR019-S05-pairing-hmac-auth-redaction
  CR019-S03-qmt-cside-client-cli-contract --> CR019-S06-qmt-endpoint-matrix-contract
  CR019-S04-windows-gateway-lifecycle-deployment --> CR019-S06-qmt-endpoint-matrix-contract
  CR019-S05-pairing-hmac-auth-redaction --> CR019-S06-qmt-endpoint-matrix-contract
  CR019-S01-stage6-admission-gate-package --> CR019-S07-run-gate-blocked-reason-integration
  CR019-S06-qmt-endpoint-matrix-contract --> CR019-S07-run-gate-blocked-reason-integration
  CR015-S04-pretrade-risk-gate --> CR019-S07-run-gate-blocked-reason-integration
  CR016-S03-monitoring-heartbeat-and-kill-switch --> CR019-S07-run-gate-blocked-reason-integration
  CR016-S04-simulation-live-runbook-and-approval-gates --> CR019-S07-run-gate-blocked-reason-integration
  CR019-S04-windows-gateway-lifecycle-deployment --> CR019-S08-fallback-incident-signed-file-boundary
  CR019-S05-pairing-hmac-auth-redaction --> CR019-S08-fallback-incident-signed-file-boundary
  CR019-S06-qmt-endpoint-matrix-contract --> CR019-S08-fallback-incident-signed-file-boundary
  CR019-S07-run-gate-blocked-reason-integration --> CR019-S08-fallback-incident-signed-file-boundary
  CR019-S01-stage6-admission-gate-package --> CR019-S09-deferred-capability-register
  CR019-S02-primary-benchmark-dashboard --> CR019-S09-deferred-capability-register
  CR019-S01-stage6-admission-gate-package --> CR019-S10-docs-runbook-user-manual-boundary
  CR019-S02-primary-benchmark-dashboard --> CR019-S10-docs-runbook-user-manual-boundary
  CR019-S03-qmt-cside-client-cli-contract --> CR019-S10-docs-runbook-user-manual-boundary
  CR019-S04-windows-gateway-lifecycle-deployment --> CR019-S10-docs-runbook-user-manual-boundary
  CR019-S05-pairing-hmac-auth-redaction --> CR019-S10-docs-runbook-user-manual-boundary
  CR019-S06-qmt-endpoint-matrix-contract --> CR019-S10-docs-runbook-user-manual-boundary
  CR019-S07-run-gate-blocked-reason-integration --> CR019-S10-docs-runbook-user-manual-boundary
  CR019-S08-fallback-incident-signed-file-boundary --> CR019-S10-docs-runbook-user-manual-boundary
  CR019-S09-deferred-capability-register --> CR019-S10-docs-runbook-user-manual-boundary
  CR006-S03-backtrader-clean-feed-contract --> CR025-S01-clean-feed-gate-backend-selector
  CR005-S06-backtrader-optional-backend --> CR025-S01-clean-feed-gate-backend-selector
  CR025-S01-clean-feed-gate-backend-selector --> CR025-S02-semantic-diff-schema-artifact
  CR025-S04-backtrader-module-reference-no-copy-guardrail --> CR025-S02-semantic-diff-schema-artifact
  CR025-S02-semantic-diff-schema-artifact --> CR025-S03-order-intent-draft-qmt-boundary
  CR015-S03-oms-order-state-machine --> CR025-S03-order-intent-draft-qmt-boundary
  CR015-S06-target-portfolio-to-order-intent-shadow-mode --> CR025-S03-order-intent-draft-qmt-boundary
  CR017-S04-reader-api-and-policy-gates --> CR025-S03-order-intent-draft-qmt-boundary
  CR025-S01-clean-feed-gate-backend-selector --> CR025-S05-no-real-operation-safety-verification
  CR025-S02-semantic-diff-schema-artifact --> CR025-S05-no-real-operation-safety-verification
  CR025-S03-order-intent-draft-qmt-boundary --> CR025-S05-no-real-operation-safety-verification
  CR025-S04-backtrader-module-reference-no-copy-guardrail --> CR025-S05-no-real-operation-safety-verification
  CR025-S01-clean-feed-gate-backend-selector --> CR025-S06-route-docs-and-follow-up-handoff
  CR025-S02-semantic-diff-schema-artifact --> CR025-S06-route-docs-and-follow-up-handoff
  CR025-S03-order-intent-draft-qmt-boundary --> CR025-S06-route-docs-and-follow-up-handoff
  CR025-S04-backtrader-module-reference-no-copy-guardrail --> CR025-S06-route-docs-and-follow-up-handoff
  CR019-S09-deferred-capability-register --> CR025-S06-route-docs-and-follow-up-handoff
  CR030-S01-external-reference-matrix-and-loop-contract --> CR030-S02-factor-spec-run-spec-contract
  CR030-S02-factor-spec-run-spec-contract --> CR030-S03-factor-panel-label-window-fail-closed
  CR011-S08-factor-panel-audit-and-robust-validation --> CR030-S03-factor-panel-label-window-fail-closed
  CR030-S03-factor-panel-label-window-fail-closed --> CR030-S04-factor-evaluation-report
  CR030-S04-factor-evaluation-report --> CR030-S05-multifactor-combiner-portfolio-plan
  CR030-S04-factor-evaluation-report --> CR030-S06-experiment-manifest-report-catalog
  CR030-S05-multifactor-combiner-portfolio-plan --> CR030-S07-strategy-admission-package-handoff
  CR030-S06-experiment-manifest-report-catalog --> CR030-S07-strategy-admission-package-handoff
  CR019-S01-stage6-admission-gate-package --> CR030-S07-strategy-admission-package-handoff
  CR025-S03-order-intent-draft-qmt-boundary --> CR030-S07-strategy-admission-package-handoff
  CR030-S01-external-reference-matrix-and-loop-contract --> CR030-S08-safety-docs-and-follow-up-boundary
  CR030-S02-factor-spec-run-spec-contract --> CR030-S08-safety-docs-and-follow-up-boundary
  CR030-S03-factor-panel-label-window-fail-closed --> CR030-S08-safety-docs-and-follow-up-boundary
  CR030-S04-factor-evaluation-report --> CR030-S08-safety-docs-and-follow-up-boundary
  CR030-S05-multifactor-combiner-portfolio-plan --> CR030-S08-safety-docs-and-follow-up-boundary
  CR030-S06-experiment-manifest-report-catalog --> CR030-S08-safety-docs-and-follow-up-boundary
  CR030-S07-strategy-admission-package-handoff --> CR030-S08-safety-docs-and-follow-up-boundary
  CR019-S04-windows-gateway-lifecycle-deployment --> CR020-S01-windows-gateway-runtime-admission
  CR020-S01-windows-gateway-runtime-admission --> CR020-S02-server-qmt-login-session
  CR020-S01-windows-gateway-runtime-admission --> CR020-S03-linux-client-rest-transport
  CR020-S01-windows-gateway-runtime-admission --> CR020-S04-hmac-pairing-allowlist-scope
  CR020-S03-linux-client-rest-transport --> CR020-S04-hmac-pairing-allowlist-scope
  CR020-S02-server-qmt-login-session --> CR020-S05-query-positions-readonly
  CR020-S03-linux-client-rest-transport --> CR020-S05-query-positions-readonly
  CR020-S04-hmac-pairing-allowlist-scope --> CR020-S05-query-positions-readonly
  CR020-S01-windows-gateway-runtime-admission --> CR020-S06-docs-runbook-cp7-real-machine-validation
  CR020-S02-server-qmt-login-session --> CR020-S06-docs-runbook-cp7-real-machine-validation
  CR020-S03-linux-client-rest-transport --> CR020-S06-docs-runbook-cp7-real-machine-validation
  CR020-S04-hmac-pairing-allowlist-scope --> CR020-S06-docs-runbook-cp7-real-machine-validation
  CR020-S05-query-positions-readonly --> CR020-S06-docs-runbook-cp7-real-machine-validation
```

## 阻塞项

| ID | 阻塞项 | 状态 | 影响 | 需要谁决策 |
|---|---|---|---|---|
| BLK-001 | 无 BLOCKING 阻塞项 | CLOSED | Story 计划可提交给 meta-po 发起人工确认 | - |
| CR4-BLK-001 | CR-004 尚未完成 CP3/CP4 人工确认 | OPEN | STORY-014..018 不得进入实现；可提交 meta-po 发起 CP3/CP4 | meta-po / user |
| CR4-BLK-002 | TickFlow/Tushare exact source/interface 和凭据策略未确认 | OPEN | 不阻塞 fake/offline 最小闭环；阻塞真实 adapter 启用 | user / 后续数据源 owner |
| CR5-BLK-001 | CR-005 尚未完成 CP3/CP4 人工确认 | RESOLVED：CR-005 CP3/CP4/CP5 批次已按检查点门控获批，CR005-S01..S06 已 verified / CP7 PASS | 不再阻塞 CR006；保留为历史阻塞项闭环记录 | meta-po / user |
| CR5-BLK-002 | Backtrader 依赖版本与 optional dependency 策略未确认 | RESOLVED：CR005-S06 CP5 Batch D 已确认 dependency group/version/lazy import，CP6/CP7 均 PASS | 不再阻塞 CR005-S06 或 CR006-S03；后续新增后端策略仍需新门控 | user / meta-qa / meta-dev |
| CR5-BLK-003 | `hs300_index` 基准口径和真实 lake root 未确认 | SUPERSEDED：真实 lake root 由用户本机配置且不记录真实值；CR005-S04/S05/S06 已以 typed unavailable / remediation spec 和文档边界 verified | 不再阻塞 CR006；真实抓取或真实 lake 写入仍需另行授权 | user / meta-po |
| CR5-BLK-004 | CR005-S02/S03 PIT、复权和 quality gate 契约尚未人工确认并验证 | RESOLVED：CR005-S02 blocker fix 后 CP7 重验 PASS，CR005-S03 CP7 PASS，CR005-S06 CP7 PASS | 不再阻塞 CR006-S03；Backtrader clean feed 可引用已验证契约 | meta-po / user |
| CR5-BLK-005 | 原 CP3/CP4 旧稿已被第三轮评审 superseded | RESOLVED：第三轮修订后的 CR005 CP3/CP4 自动预检与人工审查已 approved，旧稿仅保留历史追溯 | 不再阻塞 CR006；旧稿不得重新作为当前批准依据 | meta-po |
| CR6-BLK-001 | CR-006 尚未完成 CP3/CP4 人工确认 | RESOLVED：2026-05-18 用户“全部接受”，CP3/CP4 已回填 approved | CR006-S01..S04 可进入全量 LLD；CP5 全量确认前仍不得实现 | meta-po / user |
| CR6-BLK-002 | 旧 `data/**` 读取/比对授权未确认 | OPEN | 不阻塞 Tushare-first 设计；阻塞任何旧数据覆盖性分析、读取、列出、迁移、复制或删除动作 | user |
| CR7-BLK-001 | CR-007 尚未完成 CP3/CP4 人工确认 | RESOLVED：2026-05-20 用户原始回复 `同意` 已由 meta-po 回填 CP3/CP4 approved；CR007-BATCH-A CP5 也已 approved | 不再阻塞 CR007-S02；S03/S04/S05 仍受当前 Story DAG、文件冲突和 CR008 影响分析约束 | meta-po / user |
| CR7-BLK-002 | 真实 Tushare 长周期抓取和 `/mnt/ugreen-data-lake` 写入未授权 | OPEN | 不阻塞设计和 LLD；阻塞任何真实抓取、真实 lake 写入或大规模 backfill | user |
| CR8-BLK-001 | CR-008 尚未完成 CP3/CP4 人工确认 | OPEN | CR008-S01..S06 不得进入 LLD；CP3/CP4 通过后才可进入 CR008-BATCH-A 全量 LLD | meta-po / user |
| CR8-BLK-002 | CR008-BATCH-A 尚未完成全量 LLD 与 CP5 批次人工确认 | OPEN | CR008 任一 Story 不得实现；不得修改代码、测试或报告 | meta-po / user |
| CR8-BLK-003 | CR007-S04/S05 与 CR008 报告 metadata / benchmark 字段 / legacy report 口径重叠 | OPEN | CR007-S04/S05 在 CR008 CP3/CP4 结论前保持 hold；避免提前实现后返工 | meta-se / meta-po |
| CR10-BLK-001 | CR-010 尚未完成 CP3/CP4 人工确认 | RESOLVED for S01..S12；OPS-D addendum 已按用户预授权回填 CP4 approved | CR010-S01..S12 CP4 已 approved；S13..S16 可进入 LLD handoff，但真实子 agent 未调度前不得声明完成 | meta-po / user |
| CR10-BLK-002 | CR010 批次 CP5 尚未完成 | OPEN | DL-BATCH-A 已 approved 并 verified；DL-BATCH-B、QF-BATCH-C、OPS-BATCH-D 未完成 LLD/CP5，不得实现 | meta-po / user |
| CR10-BLK-003 | 真实联网、真实 lake 写入、旧 `data/**` 操作和凭据读取未授权 | PARTIAL | 真实联网/Tushare/写 lake/.env 读取已按用户授权用于小窗口 smoke 与 NFS 校验；旧 `data/**` 对比仍 deferred；本轮不打印凭据或真实私有路径 | user |
| CR10-BLK-004 | W3 exact source/interface 尚未确认 | OPEN | 不阻塞 fail-fast 合同；阻塞 PIT/trade_status/prices_limit/events production available 声明 | user / meta-se |
| CR10-BLK-005 | 当前线程无可调用子 agent 调度工具 | OPEN | 已创建 handoff-only；必须由主线程真实 `spawn_agent`/`resume_agent`/`send_input` 调度后，才能补齐 CP5/CP6/CP7 PASS | main-thread / meta-po |
| CR11-BLK-001 | CR-011 尚未完成 CP3/CP4 人工确认 | RESOLVED：CP3 人工审查 approved，CP4 自动预检 PASS | CR011-DATA-BATCH-A 已进入 LLD；CP5 批次确认前仍不得实现 | meta-po / user |
| CR11-BLK-002 | CR011 批次 CP5 尚未完成 | PARTIAL：DATA-BATCH-A 六份 Story 级 CP5 自动预检 PASS，批次人工审查已 approved；B/C 批次尚未开始 | DATA-BATCH-A 可按 Story DAG 与文件所有权进入离线实现；S07/S08 不得实现 | meta-po / user |
| CR11-BLK-003 | CR010-DL-BATCH-B / QF-BATCH-C 仍有 W3/realism 合同未最终 verified | OPEN | 不阻塞 Story Plan；阻塞 CR011 依赖真实可交易 / realism 的 dev_ready | meta-po / user |
| CR11-BLK-004 | 真实联网、真实 lake 写入、凭据读取、旧 `data/**` 操作和旧报告覆盖均未在本轮授权 | OPEN | 不阻塞设计；阻塞任何真实抓取、真实写湖、旧数据比对或旧报告覆盖 | user |
| CR13-BLK-001 | CR-013 HLD 增量尚需 meta-po 发起 CP3 人工确认 | OPEN | CR013-S01..S04 不得进入 LLD / CP5；本轮 CP3 仅为自动预检 | meta-po / user |
| CR13-BLK-002 | CR013-BATCH-A 尚未完成全量 LLD 与 CP5 批次人工确认 | OPEN | CR013 任一 Story 不得实现；不得修改 README/docs/代码/测试/报告证据 | meta-po / user |
| CR13-BLK-003 | provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 读取和旧报告覆盖未授权 | OPEN | 不阻塞设计和路线图；阻塞任何真实补数、VWAP/分钟数据接入或旧证据覆盖 | user |
| CR14-BLK-001 | CR014-FULL-HISTORY-LAKE-BATCH-A 尚未完成 CP5 批次人工确认 | OPEN | CR014-S01..S08 的 LLD 与 CP5 自动预检已完成，但 CP5 人工确认前不得实现、不得标记 dev-ready | meta-po / user |
| CR14-BLK-002 | S09 独立 CP5 + 用户显式授权前真实 provider fetch、真实 lake 写入、凭据读取、DuckDB 依赖变更均未授权 | OPEN | 不阻塞 BATCH-A 设计 / 离线实现；阻塞 Provider Adapter / Run Gate 真实写 raw/manifest/run metadata、Normalize/Replay 真实写 candidate、Publish Gate 更新 current pointer、DuckDB 依赖安装 | user |
| CR14-BLK-003 | Explicit Publish Gate 尚未通过任何真实 current pointer 更新授权 | OPEN | Validate / parity PASS 只能生成 candidate 或 audit evidence；reader/DuckDB 不得看到未发布 candidate 作为 current truth | user / meta-po |
| CR14-BLK-004 | CR014-REAL-RUN-BATCH-B / S09 尚未完成 LLD、CP5 和真实 run 授权 | OPEN | S09 只作为后续分时段真实抓取与 raw/manifest 写湖 Story；必须等 S01..S08 完成后单独推进 | meta-po / user |
| CR15-17-BLK-001 | CR015 / CR016 / CR017 三个 LLD 批次尚未生成全量 LLD 与 CP5 自动预检 | OPEN | 20 个新增 Story 不得进入实现；CP4 通过后由 meta-po 组织全量 LLD 设计并汇入 CP5 Decision Brief | meta-po / meta-dev / user |
| CR15-17-BLK-002 | 本轮未授权真实 QMT API、真实发单、撤单、账户写操作、真实抓取、真实写湖、publish current pointer 或依赖变更 | OPEN | 不阻塞 Story Plan / LLD；阻塞任何真实运行、真实数据写入、真实 broker lake 写入或依赖安装 | user |
| CR15-17-BLK-003 | CR016 activation 依赖 CR015 foundation verified | OPEN | CR016 simulation/live_readonly/small_live/scale_up Story 可写 LLD，但开发和运行必须等待 CR015 CP7 PASS 与对应授权 | meta-po / user |
| CR15-17-BLK-004 | CR017 未 verified 前阻断 scale_up 和生产策略复权治理完成声明 | OPEN | 不阻断 CR016 技术 simulation 设计；阻断 CR016-S06 scale_up dev_ready 和相关 allowed claim | meta-po / user |
| CR15-17-BLK-005 | CR016-S05/S06 small_live / scale_up 是 later-gated，不属于当前可直接实现真实操作项 | OPEN | 即使 CP5 通过，也必须由 meta-po 按 Story DAG、CR015/017 verified、per-run 授权和文件所有权重新计算 dev_ready | user / meta-po |
| CR19-BLK-001 | CR019-STAGE6-QMT-BRIDGE-BATCH-A 尚未进入全量 LLD 与 CP5 批次人工确认 | OPEN | 10 个 CR019 Story 只能进入 LLD 队列；CP5 全量确认前不得实现、不得标记 dev-ready | meta-po / meta-dev / user |
| CR19-BLK-002 | 本轮未授权代码实现、依赖变更、服务启动、凭据读取、真实 QMT / provider / lake / broker / publish / simulation / live 操作 | OPEN | 不阻塞 Story Plan / CP4；阻塞任何 FastAPI gateway 实现、真实 QMT API 调用、真实发单 / 撤单 / 账户查询、真实 lake 或 broker lake 写入 | user |
| CR19-BLK-003 | endpoint matrix 完整支持不代表真实 operation 授权，pairing/HMAC 不替代 run gate | OPEN | 后续 LLD / CP5 / CP6 / CP7 必须继续保持 endpoint 可见、调用方识别和真实交易授权三者分离 | meta-po / meta-dev / meta-qa |
| CR25-BLK-001 | CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT-BATCH-A 尚未进入全量 LLD 与 CP5 批次人工确认 | OPEN | 6 个 CR025 Story 只能进入 LLD 队列；CP5 全量确认前不得实现、不得标记 dev-ready | meta-po / meta-dev / user |
| CR25-BLK-002 | 本轮未授权 LLD、代码实现、依赖变更、Backtrader 运行、源码复制 / 裁剪 / 改写 / 移植、真实 broker / QMT / provider / lake / publish / simulation / live 或凭据读取 | OPEN | 不阻塞 Story Plan / CP4；阻塞任何 runtime、dependency、source migration 或真实外部操作 | user |
| CR25-BLK-003 | Backtrader GPLv3 源码级移植默认 no-copy，`migration_candidate` 当前为空 | OPEN | 后续 LLD / CP5 必须把源码、samples/tests/datas、live store、line/metaclass runtime 设为 forbidden；若用户要求源码级候选，回退 CP3 或另起 CR | user / meta-po / legal-package owner |
| CR30-BLK-001 | CR030-MULTIFACTOR-RESEARCH-LOOP-BATCH-A 尚未进入全量 LLD 与 CP5 批次人工确认 | OPEN | 8 个 CR030 Story 只能进入 LLD 队列；CP5 全量确认前不得实现、不得标记 dev-ready | meta-po / meta-dev / user |
| CR30-BLK-002 | 本轮未授权 LLD、代码实现、依赖变更、外部项目 clone/install/run、源码迁移、provider fetch、lake write、catalog publish、QMT/simulation/live/account/order/cancel 或凭据读取 | OPEN | 不阻塞 Story Plan / CP4；阻塞任何 runtime、dependency、source migration、真实数据写入或真实交易相关操作 | user |
| CR30-BLK-003 | CR-026 Qlib isolated runner、optimizer / ML workflow、vectorbt / PyBroker / RQAlpha / vn.py Spike 均保持后置 | OPEN | 不阻塞 CR-030 自有闭环 Story；阻塞将外部 runner / optimizer 并入 CR-030 P0 或并行启动 CR-026 | meta-po / user |
| CR30-BLK-004 | StrategyAdmissionPackage 不构成 QMT / simulation / live 授权 | OPEN | 不阻塞准入包合同设计；阻塞任何 QMT gateway、simulation、live_readonly、small_live、scale_up、账户查询、下单、撤单或 broker lake 写入 | user / meta-po |
| CR20-BLK-001 | CR020-QMT-GATEWAY-READONLY-BATCH-A 尚未进入全量 LLD 与 CP5 批次人工确认 | OPEN | 6 个 CR020 Story 只能进入 LLD 队列；CP5 全量确认前不得创建 LLD、不得实现、不得标记 dev-ready | meta-po / meta-dev / user |
| CR20-BLK-002 | 本轮未授权代码实现、依赖变更、gateway 启动、端口绑定、QMT / MiniQMT / XtQuant 连接、真实 `.env` 读取、凭据输出或任何真实操作 | OPEN | 不阻塞 Story Plan / CP4；阻塞服务启动、真实登录、持仓查询、交易、账户写入、simulation/live、provider/lake/publish/reports overwrite | user |
| CR20-BLK-003 | `query_positions` 单接口只读准入不等于交易、账户写入或后续 endpoint 授权 | OPEN | 不阻塞只读持仓查询合同设计；阻塞 order/cancel/modify/account_write/simulation/live/broker_lake_write 以及任何未列入 CR-020 的真实 endpoint | user / meta-po / meta-qa |

## 待确认问题

| ID | 问题 | 默认规划 | 状态 |
|---|---|---|---|
| SP-Q1 | 是否确认 13 个 Story、5 个 Wave 的拆解粒度 | 作为本轮 Story 计划提交确认 | RESOLVED：用户确认通过 |
| SP-Q2 | 是否确认 M3/M4 进入 Backlog 但不阻塞 M0-M2 第一版本地主路径 | M3/M4 保持 P1/P2 draft Story | RESOLVED：用户确认通过 |
| SP-Q3 | 是否确认本轮不生成安装规格和安装脚本 | 遵循交接文件允许输出范围 | RESOLVED：用户确认通过 |
| CR4-SP-Q1 | 是否确认 STORY-014..018 五个 Story 的 CR-004 最小闭环拆解 | 默认提交 CP4 确认 | OPEN |
| CR4-SP-Q2 | 是否确认 CP5 采用 A=014/015、B=016/017、C=018 三批滚动确认 | 默认提交 CP4 确认 | OPEN |
| CR4-SP-Q3 | 是否确认实验十/十二只做 reader 只读接入，不在实验入口联网 | 默认提交 CP4 确认 | OPEN |
| CR5-SP-Q1 | 是否确认 CR005-S01..S06 六个 Story 的拆解粒度 | 已由 CR005 CP4 / 后续 CP5 批次门控确认 | RESOLVED |
| CR5-SP-Q2 | 是否确认 Backtrader 并入 CR-005，且仅为 optional backend | 已由 CR005-S06 LLD、CP5 Batch D、CP7 PASS 确认 | RESOLVED |
| CR5-SP-Q3 | 是否确认 CR005-S06 必须晚于 CR005-S02/S03/S04 数据契约和质量门稳定 | 已由 CR005-S06 dev_gate 与 CP7 PASS 闭环 | RESOLVED |
| CR5-SP-Q4 | 是否确认 Tushare 只进入本地写湖链路，不直接接入 Data Loader/实验/Backtrader | 已由 CR005-S01/S04/S06 验证和 ADR-013/016/017 闭环 | RESOLVED |
| CR5-SP-Q5 | 是否确认 PIT 与复权统一由 Pandas 数据层完成，Backtrader 只消费干净 feed | 已由 CR005-S02/S03/S06 CP7 PASS 闭环 | RESOLVED |
| CR5-SP-Q6 | 是否确认消费层 `required_missing` 只携带 remediation spec，不自动执行数据层 backfill | 已由 CR005-S04/S05/S06 验证闭环 | RESOLVED |
| CR5-SP-Q7 | 是否确认 `market_data/cli.py` 或等价 backfill job 主所有权归 CR005-S01，不晚于 CR005-S04 | 已由 CR005-S01 backfill job spec 与后续 Story 验证闭环 | RESOLVED |
| CR6-SP-Q1 | 是否确认 CR006-BATCH-A 调整为 4 个 Story 的拆解粒度 | 默认确认：Tushare acquisition、轻量 adapter、Backtrader clean feed、old data guardrail | RESOLVED：用户“全部接受” |
| CR6-SP-Q2 | 是否确认 raw/manifest 仍需要，但只属于采集审计/复现/质量追溯层 | 默认确认；回测运行时不直接消费 raw/manifest | RESOLVED：用户“全部接受” |
| CR6-SP-Q3 | 是否确认轻量 engine 只消费 canonical/gold 或外置派生 `legacy_flat`，不默认 fallback repo `data/` | 默认确认；旧 `data/` reference-only | RESOLVED：用户“全部接受” |
| CR6-SP-Q4 | 是否确认 Backtrader 只消费 quality gate 后 clean feed | 默认确认；Backtrader 不读取 token/raw/manifest，不触发补数 | RESOLVED：用户“全部接受” |
| CR6-SP-Q5 | 是否确认 CR-006 不读取、迁移、复制、删除真实 `data/**` | 默认确认；旧数据覆盖性比对需另行授权 | RESOLVED：用户“全部接受”；旧数据读取/比对/迁移/复制/删除仍需另行授权 |
| CR7-SP-Q1 | 是否确认 CR007-BATCH-A 五个 Story 的拆解粒度 | 默认确认：prices planner、benchmark/calendar、dataset readiness、experiment benchmark、quality/docs guardrail | RESOLVED：CP4 approved |
| CR7-SP-Q2 | 是否确认 CR007-BATCH-A 采用全量 LLD 统一确认，CP5 通过前不得实现 | 默认确认；可按 max_parallel_lld=3 分轮写 LLD，但统一人工确认 | RESOLVED：CP5 batch approved |
| CR7-SP-Q3 | 是否确认真实抓取、真实 lake 写入、旧 `data/**` 操作和旧质量报告内容读取均不在默认设计/LLD/开发授权内 | 默认确认；需用户另行显式授权 | RESOLVED for default scope；真实抓取 / 真实 lake / 旧数据 / 旧报告内容读取仍需另行授权 |
| CR8-SP-Q1 | 是否确认 CR008-BATCH-A 六个 Story 的拆解粒度 | 默认确认：S01 research input、S02 benchmark 字段隔离、S03 builder、S04 quality/adjustment/label gate、S05 PIT/fixed universe、S06 auxiliary contract | OPEN |
| CR8-SP-Q2 | 是否确认 CR008-BATCH-A 采用全量 LLD 统一确认，CP5 通过前不得实现 | 默认确认；可按 max_parallel_lld=3 分轮写 LLD，但统一人工确认 | OPEN |
| CR8-SP-Q3 | 是否确认 CR007-S02 可与 CR008 solution-design 并行，CR007-S04/S05 在 CR008 CP3/CP4 前 hold | 默认确认；S02 是上游数据合同，S04/S05 与 CR008 字段/文档重叠 | OPEN |
| CR8-SP-Q4 | 是否确认 CR008 不引入 Qlib / Backtrader / VectorBT 为核心数据层 | 默认确认；仅作为后续 adapter / exporter 评估 | OPEN |
| CR8-SP-Q5 | 是否确认真实抓取、真实 lake 写入、旧 `data/**` 操作和旧质量报告内容读取均不在 CR008 默认授权内 | 默认确认；需用户另行显式授权 | OPEN |
| CR10-SP-Q1 | 是否确认 CR010-S01..S16 的拆解粒度 | 默认确认：5 个 P0 数据湖基础 Story、4 个 W3 fail-fast Story、3 个实验真实性 Story、4 个 OPS Story | RESOLVED：S01..S12 已 CP4 approved；S13..S16 按用户本轮计划登记并回填 CP4 addendum |
| CR10-SP-Q2 | 是否确认 CR010 采用 4 个开发批次并分别进行全量 LLD / CP5 确认 | 默认确认：`CR010-DL-BATCH-A`、`CR010-DL-BATCH-B`、`CR010-QF-BATCH-C`、`CR010-OPS-BATCH-D` | RESOLVED for planning；B/C/D 仍等待 LLD 与 CP5 |
| CR10-SP-Q3 | 是否确认真实回补授权逐级推进，小窗口 / 1 年 / 全历史互不继承授权 | 默认确认；小窗口真实联网/Tushare/写 lake 已单独授权并执行，后续 1 年 / 全历史仍需另行授权 | PARTIAL |
| CR10-SP-Q4 | 是否确认 W3 未确认 source/interface 前只实现合同和 fail-fast，不伪造 available | 默认确认；production_strict fail，exploratory 写 limitation | OPEN |
| CR10-SP-Q5 | 是否确认 experiments 默认 `realism_mode=exploratory`，production_strict 只用于显式验收 | 默认确认；报告必须输出 allowed_claims / blocked_claims | OPEN |
| CR10-SP-Q6 | 是否确认新增 OPS-BATCH-D 的 S13..S16 拆解粒度 | 默认确认：S13 契约、S14 backup CLI、S15 restore CLI/drill、S16 retention policy | RESOLVED：用户本轮给定全量实施计划并预授权 CP4 addendum |
| CR11-SP-Q1 | 是否确认 CR011-S01..S08 的拆解粒度 | 默认确认：6 个数据/消费合同 Story + 1 个容量成本 Story + 1 个审计验证 Story | OPEN |
| CR11-SP-Q2 | 是否确认 CR011 采用三个 CP5 批次 | 默认确认：`CR011-DATA-BATCH-A`、`CR011-RESEARCH-BATCH-B`、`CR011-VALIDATION-BATCH-C` | OPEN |
| CR11-SP-Q3 | 是否确认旧实验 17-21 报告不覆盖，新版报告版本化输出 | 默认确认；旧报告只作为 fixed/proxy/close baseline | OPEN |
| CR11-SP-Q4 | 是否确认 production_strict 缺 benchmark/PIT/tradability/execution/adjustment/exposure/capacity 任一 P0 gate 时 fail | 默认确认；exploratory 才允许 limitation 和 blocked claims | OPEN |
| CR11-SP-Q5 | 是否确认本轮不授权真实联网、真实 lake 写入、凭据读取、旧 `data/**` 操作或旧报告覆盖 | 默认确认；后续真实执行需用户另行授权 | OPEN |
| CR13-SP-Q1 | 是否确认 CR013-S01..S04 的拆解粒度 | 默认确认：S01 full-history gap register、S02 execution/VWAP claim boundary、S03 unsupported register/docs refresh、S04 full-history roadmap | OPEN |
| CR13-SP-Q2 | 是否确认 CR013-BATCH-A 采用全量 LLD 统一确认，CP5 通过前不得实现 | 默认确认；可按 max_parallel_lld=3 分轮写 LLD，但统一人工确认 | OPEN |
| CR13-SP-Q3 | 是否确认 CR-012 limited-window pass 不外推到 `2020-01-01..2024-12-31` | 默认确认；full-history 继续 blocked，直到新补数和新审计通过 | OPEN |
| CR13-SP-Q4 | 是否确认真实 VWAP / 分钟执行价继续 blocked，且不得由 close proxy 或 `amount/volume` 派生 | 默认确认；解除条件为真实 `vwap` + `vwap_status=available` + execution audit pass | OPEN |
| CR13-SP-Q5 | 是否确认本轮不授权 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 读取或旧报告覆盖 | 默认确认；S04 只做路线图，真实执行需另行授权 | OPEN |
| CR14-SP-Q1 | 是否确认 CR014-S01..S09 的拆解粒度 | 默认确认：S01 universe/lifecycle、S02 layout/manifest/catalog/publish、S03 P0 pipeline、S04 DuckDB read-only、S05 readiness/claim、S06 incremental/replay/retention、S07 consumer/docs boundary、S08 unsupported blocked boundary、S09 分时段真实抓取与 raw/manifest 写湖执行 | PENDING_CP5_DECISION_BRIEF |
| CR14-SP-Q2 | 是否确认 CR014 采用 BATCH-A / BATCH-B 两批推进 | 默认确认：`CR014-FULL-HISTORY-LAKE-BATCH-A` 统一确认 S01..S08 LLD；`CR014-REAL-RUN-BATCH-B` 在 S01..S08 完成后单独输出 S09 LLD / CP5 / 真实 run 授权 | PENDING_CP5_DECISION_BRIEF |
| CR14-SP-Q3 | 是否确认 CP5 前 `implementation_allowed=false` 且 provider_fetch=0、lake_write=0、credential_read=0、duckdb_dependency_change=0 | 默认确认；本阶段只做 Story Plan / CP4，不做 LLD、不实现、不改依赖、不真实写入 | PENDING_CP5_DECISION_BRIEF |
| CR14-SP-Q4 | 是否确认 Normalize / Replay 只生成 candidate，Validate/parity PASS 不自动 publish，只有 Explicit Publish Gate 更新 current pointer | 默认确认；DuckDB query/view/parity/report 不反向成为 source of truth | PENDING_CP5_DECISION_BRIEF |
| CR14-SP-Q5 | 是否确认 W3/minute/tick/Level2/execution VWAP 在 CR014 P0 中继续 blocked / unsupported | 默认确认；解除条件必须指向后续 source/interface + 独立 Story + CP5 + 用户显式授权 | PENDING_CP5_DECISION_BRIEF |
| CR14-SP-Q6 | 是否确认真实抓取与 raw/manifest 写湖拆分为 S09，且按 dataset/date window 分时段执行 | 默认确认；S09 必须等 S01..S08 verified、S09 LLD/CP5 approved、用户给出 authorization_id 和 dataset/date/source/lake 范围后才能真实执行 | PENDING_CP5_DECISION_BRIEF |
| CR15-17-SP-Q1 | 是否确认 CR017 6 个、CR015 7 个、CR016 7 个 Story 的拆解粒度 | 默认确认：先冻结 CR017 raw/policy 合同与 CR015 foundation，CR016 activation 真实阶段 later-gated | PENDING_CP5_DECISION_BRIEF |
| CR15-17-SP-Q2 | 是否确认三个 CP5 LLD 批次分别为 `CR017-ADJUSTMENT-DUAL-VIEW-BATCH-A`、`CR015-QMT-FOUNDATION-BATCH-A`、`CR016-QMT-ACTIVATION-BATCH-A`，但 CP5 人工确认需等待全部目标 Story LLD 与自动预检完成后统一发起 | 默认确认；LLD 可按 max_parallel_lld=3 分轮写作，CP5 必须全量确认 | PENDING_CP5_DECISION_BRIEF |
| CR15-17-SP-Q3 | 是否确认 CR017 合同是 CR015 raw 执行价隔离的 contract 前置，CR016 真实激活依赖 CR015 verified 与 CR017 口径边界 | 默认确认；CR016 技术 simulation 设计可并行，真实操作不并行 | PENDING_CP5_DECISION_BRIEF |
| CR15-17-SP-Q4 | 是否确认 CP5 前 implementation_allowed=false，且真实 QMT / broker / provider / lake / publish / dependency 操作计数均为 0 | 默认确认；本轮只做 Story Plan / CP4，不做 LLD、不实现、不真实运行 | PENDING_CP5_DECISION_BRIEF |
| CR15-17-SP-Q5 | 是否确认 small_live 与 scale_up 仅作为 later-gated Story 规划，不作为当前可直接实现项 | 默认确认；scale_up 必须等待 CR017 verified、运行稳定性和用户后续授权 | PENDING_CP5_DECISION_BRIEF |
| CR19-SP-Q1 | 是否确认 CR019-S01..S10 十个 Story 的拆解粒度 | 默认确认：2 个 admission/benchmark、2 个 C/S transport、3 个 auth/endpoint/gate、2 个 fallback/deferred、1 个 docs/runbook | CP4_AUTO_PASS_PENDING_CP5 |
| CR19-SP-Q2 | 是否确认 CR019 采用 5 个 Wave 和单一全量 LLD 批次 `CR019-STAGE6-QMT-BRIDGE-BATCH-A` | 默认确认；LLD 可按 max_parallel_lld=3 分轮起草，但 CP5 必须等待 10 张 LLD 与自动预检全部完成后统一人工确认 | CP4_AUTO_PASS_PENDING_CP5 |
| CR19-SP-Q3 | 是否确认完整 endpoint matrix 与真实运行授权分离，pairing/HMAC 只识别调用方 | 默认确认；endpoint 可见不授权 simulation/live/account/cancel，HMAC pass 后仍需 run mode、stage gate、risk gate、kill-switch、per-run authorization | CP4_AUTO_PASS_PENDING_CP5 |
| CR19-SP-Q4 | 是否确认 CP5 前 implementation_allowed=false 且真实操作计数均为 0 | 默认确认；本轮只做 Story Plan / CP4，不做 LLD、代码、依赖、服务、凭据、真实 QMT、provider、lake、broker、publish、simulation/live | CP4_AUTO_PASS_PENDING_CP5 |
| CR25-SP-Q1 | 是否确认 CR025-S01..S06 六个 Story 的拆解粒度 | 默认确认：S01 clean feed / selector、S02 semantic diff、S03 order intent draft、S04 no-copy guardrail、S05 safety verification、S06 docs / QMT route handoff | CP4_AUTO_PASS_PENDING_CP5 |
| CR25-SP-Q2 | 是否确认 CR025 采用 4 个 Wave 和单一全量 LLD 批次 `CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT-BATCH-A` | 默认确认；LLD 可按 max_parallel_lld=3 分轮起草，但 CP5 必须等待 6 张 LLD、clarification queue 和自动预检全部完成后统一人工确认 | CP4_AUTO_PASS_PENDING_CP5 |
| CR25-SP-Q3 | 是否确认 optional runtime 只能采用 optional dependency + lazy import，且 CP5 前 dependency_change=false | 默认确认；未安装 / 未选择 Backtrader 是合法环境，返回 structured unavailable；若 CP5 不授权依赖，保留 design/reference-only 和 unavailable 合同 | CP4_AUTO_PASS_PENDING_CP5 |
| CR25-SP-Q4 | 是否确认 `migration_candidate` 当前为空并延续 GPLv3 no-copy guardrail | 默认确认；源码级移植、samples/tests/datas 复制、line/metaclass runtime 和 live store 均为 forbidden path，例外需回退 CP3/另起 CR | CP4_AUTO_PASS_PENDING_CP5 |
| CR25-SP-Q5 | 是否确认 CP5 前 implementation_allowed=false 且真实操作执行计数为 0 | 默认确认；本轮只做 Story Plan / CP4，不做 LLD、代码、依赖、Backtrader 运行、源码移植、broker/QMT/provider/lake/publish/simulation/live 或凭据读取 | CP4_AUTO_PASS_PENDING_CP5 |
| CR25-SP-Q6 | 是否确认多因子研究闭环不并入 CR025 Story Plan | 默认确认；FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪和策略准入包另起后续 CR，参考 Qlib / Alphalens / vnpy.alpha；CR025 保持 6 Story / 4 Wave / 1 LLD batch | CP5_REFRESH_REQUIRED |
| CR30-SP-Q1 | 是否确认 CR030-S01..S08 八个 Story 的拆解粒度 | 默认确认：S01 外部矩阵 / 总合同，S02 因子定义 / 运行规格，S03 面板 / 标签，S04 单因子评价，S05 多因子组合，S06 manifest/catalog，S07 admission/handoff，S08 safety/docs | CP4_AUTO_PASS_PENDING_CP5 |
| CR30-SP-Q2 | 是否确认 CR030 采用 4 个 Wave 和单一全量 LLD 批次 `CR030-MULTIFACTOR-RESEARCH-LOOP-BATCH-A` | 默认确认；LLD 可按 `max_parallel_lld=3` 分轮起草，但 CP5 必须等待 8 张 LLD、clarification queue 和自动预检全部完成后统一人工确认 | CP4_AUTO_PASS_PENDING_CP5 |
| CR30-SP-Q3 | 是否确认 CR-026 Qlib runner 与 optimizer / ML workflow 后置 | 默认确认；外部 runner / optimizer / ML 只有在内部合同冻结、依赖隔离和运行授权明确后另起 CR / Spike | CP4_AUTO_PASS_PENDING_CP5 |
| CR30-SP-Q4 | 是否确认 CP5 前 implementation_allowed=false 且真实操作执行计数为 0 | 默认确认；本轮只做 Story Plan / CP4，不做 LLD、代码、依赖、外部运行、源码迁移、provider/lake/publish、QMT/simulation/live 或凭据读取 | CP4_AUTO_PASS_PENDING_CP5 |
| CR30-SP-Q5 | 是否确认 StrategyAdmissionPackage 只输出研究准入证据和 `order_intent_draft_v1` 草稿 | 默认确认；真实 QMT / simulation / live 仍由 CR-020..CR-024 独立授权，CR-030 不产生可提交订单 | CP4_AUTO_PASS_PENDING_CP5 |
| CR20-SP-Q1 | 是否确认 CR020-S01..S06 六个 Story 的拆解粒度 | 默认确认：S01 Windows gateway runtime / admission，S02 Server QMT login / session，S03 Linux client REST transport，S04 HMAC / allowlist / scope，S05 `query_positions` read-only，S06 docs / runbook / CP7 real-machine validation | CP4_AUTO_PASS_PENDING_CP5 |
| CR20-SP-Q2 | 是否确认 CR020 采用 4 个 Wave 和单一全量 LLD 批次 `CR020-QMT-GATEWAY-READONLY-BATCH-A` | 默认确认；LLD 可按 `max_parallel_lld=3` 基于 Story/file owner 分轮起草，但 CP5 必须等待 6 张 LLD、clarification queue、CP4 摘要和 CP5 自动预检全部完成后统一人工确认 | CP4_AUTO_PASS_PENDING_CP5 |
| CR20-SP-Q3 | 是否确认 CP5 前 `implementation_allowed=false` 且真实操作执行计数为 0 | 默认确认；本轮只做 Story Plan / CP4，不做 LLD、代码、依赖、gateway 启动、端口绑定、真实 `.env` 读取、QMT/MiniQMT/XtQuant 连接、交易、账户写入、simulation/live、provider/lake/publish/reports overwrite 或凭据输出 | CP4_AUTO_PASS_PENDING_CP5 |
| CR20-SP-Q4 | 是否确认 `query_positions` 是唯一真实只读查询接口，scope 固定为 `qmt:positions:read` | 默认确认；其他 endpoint、订单、撤单、改单、账户写入、broker lake、simulation/live 均保持 blocked / later-gated，必须后续独立 CR / CP / 授权 | CP4_AUTO_PASS_PENDING_CP5 |
| CR20-SP-Q5 | 是否确认 `.env` / credential_ref / HMAC / allowlist / redaction 采用 fail-closed 边界 | 默认确认；真实凭据只留本地未跟踪文件，过程产物仅保留 redacted `credential_ref`；auth、scope、nonce、allowlist、redaction 任一失败时 query 和 adapter call 均为 0 | CP4_AUTO_PASS_PENDING_CP5 |
| CR46-SP-Q1 | 是否确认 CR046-S01..S07 七个 Story 的拆解粒度 | 默认确认：S01 架构、S02 策略包、S03 QMT terminal target、S04 MiniQMT runner install design、S05 验证框架、S06 后续策略交付 gate、S07 研究框架 follow-up contract | CP4_AUTO_PASS_PENDING_CP5 |
| CR46-SP-Q2 | 是否确认 CR046 采用单一全量 LLD 批次 `CR046-DUAL-TARGET-FRAMEWORK-BATCH-A` | 默认确认；S01..S05 full-lld，S06..S07 technical-note；CP5 必须等待全部设计证据、clarification queue 和自动预检完成后统一人工确认 | CP4_AUTO_PASS_PENDING_CP5 |
| CR46-SP-Q3 | 是否确认 CP5 前 implementation_allowed=false 且真实操作执行计数为 0 | 默认确认；本轮只做 Story Plan / CP4，不做 LLD、代码、策略交付、QMT 运行验证、MiniQMT 连接 / 真实安装、submit/cancel、simulation/live、provider/lake/publish 或凭据读取 | CP4_AUTO_PASS_PENDING_CP5 |
| CR46-SP-Q4 | 是否确认具体策略交付、MiniQMT 实机 install / readonly 和研究框架完善均后置 | 默认确认；CR047 / CR049 / CR051 分别承接，CR046 只交付 framework-first 合同和验证框架 | CP4_AUTO_PASS_PENDING_CP5 |

## CR-046：QMT / MiniQMT 双目标策略交付框架

| 对象 | 状态 | 证据 | 下一步 |
|---|---|---|---|
| CP2 需求 / 场景基线 | approved | `process/checkpoints/CP2-CR046-REQUIREMENTS-BASELINE.md` | 已进入 CP3 / CP4 |
| CP3 HLD / ADR | approved | `process/checkpoints/CP3-CR046-HLD-REVIEW.md`、`docs/design/HLD-CR046-QMT-MINIQMT-DUAL-TARGET-FRAMEWORK.md`、`docs/design/ARCHITECTURE-DECISION-CR046.md` | 已批准 FEAT-09、平台无关 core、runner install dry-run 和证据分级 |
| Feature design | ready-for-cp5-review | `docs/design/FEATURE-DESIGN-MATRIX.md`、`docs/features/qmt-miniqmt-dual-target-framework/*` | 已作为 S01..S07 的 CP5 输入 |
| Story Plan / CP4 | PASS | `process/checks/CP4-CR046-STORY-DAG-PARALLEL-SAFETY.md` | 进入全量设计证据批次，CP5 前不得实现 |
| LLD batch / CP5 auto | approved | `process/checks/CP5-CR046-*`、`process/checkpoints/CP5-CR046-DUAL-TARGET-FRAMEWORK-BATCH-A-LLD-BATCH.md` | S01..S05 full-lld、S06..S07 technical-note 已 confirmed；CP5 人工确认 approved |
| CP6 implementation | PASS | `process/context/CP6-CR046-IMPLEMENTATION-CONTEXT.yaml`、`process/stories/CR046-BATCH-A-IMPLEMENTATION.md`、`process/checks/CP6-CR046-DUAL-TARGET-FRAMEWORK-BATCH-A-CODING-DONE.md` | framework-first 文档 / 契约实现完成；进入 CP7 |
| 安全边界 | not-authorized | CP2 / CP3 / CP4 不授权项 | 不授权具体策略交付、QMT 运行验证、MiniQMT 连接 / 真实安装、submit/cancel、simulation/live、provider/lake/publish 或凭据读取 |

### CR046 Story Plan 队列

| Story ID | 标题 | Wave | 状态 | LLD 策略 | Dev Gate | 阻塞 |
|---|---|---|---|---|---|---|
| CR046-S01-dual-target-strategy-architecture | 双目标策略交付架构与 FEAT-09 边界 | CR046-W1-ARCHITECTURE-CONTRACT | ready-for-verification | full-lld | runtime blocked | 无上游 Story；不得运行 |
| CR046-S02-strategy-package-contract-and-schema | 策略包合同、目录结构与 schema | CR046-W1-ARCHITECTURE-CONTRACT | ready-for-verification | full-lld | runtime blocked | 依赖 S01 contract |
| CR046-S03-qmt-terminal-target-framework | QMT terminal target 框架 | CR046-W2-TARGETS-INSTALL | ready-for-verification | full-lld | runtime blocked | 依赖 S02；QMT runtime not-authorized |
| CR046-S04-miniqmt-runner-install-and-runtime-boundary | MiniQMT runner 安装设计与运行边界 | CR046-W2-TARGETS-INSTALL | ready-for-verification | full-lld | runtime blocked | 依赖 S02；MiniQMT install / connection not-authorized |
| CR046-S05-verification-framework-and-evidence-model | 验证框架与证据模型 | CR046-W3-VALIDATION-GATES | ready-for-verification | full-lld | runtime blocked | 依赖 S01..S04 contract |
| CR046-S06-follow-up-strategy-delivery-gate | 后续具体策略交付门禁 | CR046-W4-FOLLOW-UP-HANDOFF | ready-for-verification | technical-note | runtime blocked | 依赖 S05；不启动 CR047 / CR049 |
| CR046-S07-research-framework-follow-up-contract | 研究框架反向完善合同 | CR046-W4-FOLLOW-UP-HANDOFF | ready-for-verification | technical-note | runtime blocked | 依赖 S01 / S05；不实施 CR051 |

### CR046 Wave 进度

| Wave | 总数 | lld-ready | lld-review | dev-ready | in-dev | verified | blocked |
|---|---:|---:|---:|---:|---:|---:|---:|
| CR046-W1-ARCHITECTURE-CONTRACT | 2 | 2 | 0 | 0 | 0 | 0 | 0 |
| CR046-W2-TARGETS-INSTALL | 2 | 2 | 0 | 0 | 0 | 0 | 0 |
| CR046-W3-VALIDATION-GATES | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| CR046-W4-FOLLOW-UP-HANDOFF | 2 | 2 | 0 | 0 | 0 | 0 | 0 |

## CR-051：策略研究生命周期与 quant-lab 迁移治理

| 对象 | 状态 | 证据 | 下一步 |
|---|---|---|---|
| CP2 需求 / 场景基线 | approved | `process/checkpoints/CP2-CR051-REQUIREMENTS-BASELINE.md` | 已进入 CP3 / CP4 |
| CP3 HLD / 架构决策 | approved | `process/checkpoints/CP3-CR051-HLD-REVIEW.md`、`docs/design/HLD-CR051-STRATEGY-RESEARCH-LIFECYCLE-FRAMEWORK.md` | 已批准单主仓库、外部 archive、硬件冷热分层、交易主机边界、阶段化迁移和 `quant-lab` 命名 |
| Feature design | approved | `docs/design/FEATURE-DESIGN-MATRIX.md`、`docs/features/strategy-research-lifecycle/*` | 已被 S01..S06 消费 |
| Story Plan / CP4 | PASS | `process/checks/CP4-CR051-STORY-DAG-PARALLEL-SAFETY.md` | 已完成 |
| LLD batch / CP5 | approved | `process/checkpoints/CP5-CR051-STRATEGY-RESEARCH-LIFECYCLE-BATCH-A-LLD-BATCH.md` | 用户已同意，6 个 Story 设计证据确认 |
| CP6 implementation | PASS | `process/context/CP6-CR051-IMPLEMENTATION-CONTEXT.yaml`、`process/checks/CP6-CR051-*-CODING-DONE.md` | 7 份 `docs/research/*` 合同文档和 6 份 Story IMPLEMENTATION 已生成 |
| CP7 verification | PASS | `docs/quality/VERIFICATION-REPORT-CR051.md`、`process/context/CP7-CR051-VERIFICATION-CONTEXT.yaml` | 6 个 Story 均已静态验证 PASS |
| 安全边界 | not-authorized | CP2 / CP3 / CP4 不授权项 | 不授权目录重命名、NAS 操作、外部 archive 搬迁、provider/lake/publish、QMT/MiniQMT runtime、凭据读取或 git push |

### CR051 Story Plan 队列

| Story ID | 标题 | Wave | 状态 | LLD 策略 | Dev Gate | 阻塞 |
|---|---|---|---|---|---|---|
| CR051-S01-lifecycle-and-taxonomy-framework | 策略研究生命周期与 taxonomy 框架 | CR051-W1-LIFECYCLE-ARCHIVE-IDENTITY | verified | full-lld | CP6/CP7 PASS | 输出 lifecycle / taxonomy；不得实现具体策略 |
| CR051-S02-repository-archive-and-data-lake-governance | 仓库、研究归档与数据湖边界治理 | CR051-W1-LIFECYCLE-ARCHIVE-IDENTITY | verified | full-lld | CP6/CP7 PASS | 输出 archive governance / manifest spec；不得操作 NAS / lake |
| CR051-S06-project-identity-rename-and-legacy-alias | 项目身份改名与 legacy alias 兼容 | CR051-W1-LIFECYCLE-ARCHIVE-IDENTITY | verified | technical-note | CP6/CP7 PASS | 输出 identity migration；不得真实重命名 / push |
| CR051-S03-research-pc-and-trading-pc-workflow | 研究主机与交易主机工作流边界 | CR051-W2-HOST-REGISTRY | verified | full-lld | CP6/CP7 PASS | 输出 host workflow；不得 transfer / import / runtime |
| CR051-S04-registry-and-evidence-contracts | 研究 registry 与证据合同 | CR051-W2-HOST-REGISTRY | verified | full-lld | CP6/CP7 PASS | 输出 registry spec；不得保存凭据 / broker facts |
| CR051-S05-follow-up-cr-roadmap-and-admission-gates | 后续 CR 路线与准入门禁 | CR051-W3-FOLLOW-UP-GATES | verified | technical-note | CP6/CP7 PASS | 后续 CR 仍 blocked_by=CR051 |

### CR051 Wave 进度

| Wave | 总数 | lld-ready | lld-review | ready-for-verification | in-dev | verified | blocked |
|---|---:|---:|---:|---:|---:|---:|---:|
| CR051-W1-LIFECYCLE-ARCHIVE-IDENTITY | 3 | 0 | 0 | 0 | 0 | 3 | 0 |
| CR051-W2-HOST-REGISTRY | 2 | 0 | 0 | 0 | 0 | 2 | 0 |
| CR051-W3-FOLLOW-UP-GATES | 1 | 0 | 0 | 0 | 0 | 1 | 0 |
