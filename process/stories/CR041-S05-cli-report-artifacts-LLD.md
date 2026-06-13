---
story_id: "CR041-S05-cli-report-artifacts"
title: "CLI and Report Artifacts"
story_slug: "cli-report-artifacts"
lld_version: "1.0"
tier: "M"
status: "confirmed"
confirmed: true
created_by: "meta-po-inline-fallback"
created_at: "2026-06-10T22:48:00+08:00"
confirmed_by: "user"
confirmed_at: "2026-06-10T23:23:00+08:00"
shared_fragments:
  - "process/context/CP3-CR041-DESIGN-CONTEXT.yaml"
feature_design_refs: []
lld_policy:
  required_level: "full-lld"
  trigger_reasons:
    - "CLI runner"
    - "report artifact contract"
    - "no-real-operation counters"
  rationale: "CLI 和报告是用户消费 CR041 的入口，必须冻结 artifact schema 和安全边界。"
open_items: 0
---

# LLD: CR041-S05 - CLI and Report Artifacts

## 0. 上游设计依据

| 来源 | 路径 / ID | 被本 LLD 消费的内容 |
|---|---|---|
| S01..S04 LLD | `process/stories/CR041-S0*-*-LLD.md` | admission、order intents、fills、ledger 输出契约。 |
| CR041 | `process/changes/CR-041-API-LESS-PAPER-SIMULATION-RUNNER-2026-06-10.md` | 验收标准和不授权边界。 |
| AGENTS | `AGENTS.md` | Python 命令使用 `uv run`；不授权 provider/lake/publish。 |

## 1. Goal

创建本地 CLI runner 和报告 artifact 设计，使用户能可复跑地执行 CR041 API-less paper simulation，并获得 `order_intents`、`fills`、`positions`、`cash_ledger`、`equity_curve`、`reconciliation`、`run_manifest` 和安全计数。

## 2. Requirements（Functional / Non-Functional）

### 2.1 Functional

- CLI 入口：`uv run --python 3.11 python scripts/run_paper_simulation.py --admission-package <path> --target-portfolio <path> --market-data <path> --run-id <id> --output-root <path>`。
- 输出目录默认 `reports/paper_simulation/<run-id>/` 和 `process/research/paper_simulation/<run-id>/`；不得写 catalog current pointer。
- 报告包含 JSON 和 Markdown summary，列出策略、时间范围、成本、成交率、partial/rejected、净值、回撤、换手和 forbidden operation counters。
- 输出 `run_manifest.json`，记录输入路径、hash、配置、代码版本占位、生成时间和 no-real-operation counters。
- CLI 必须离线运行，不 provider fetch，不 lake write，不 publish，不 broker SDK import。

### 2.2 Non-Functional

- 可复跑：同 run_id 默认拒绝覆盖，除非显式 `--overwrite`；overwrite 只允许目标 output-root 内本 run 目录。
- 安全：所有 forbidden operation counters 为 0；报告显式写 not_authorization。
- 可验证：单元测试覆盖 CLI dry-run / artifact schema / no-real-operation scan。

## 3. 模块拆分与职责

| 模块 / 文件组 | 职责 | 说明 |
|---|---|---|
| `scripts/run_paper_simulation.py` | CLI 参数解析、读取输入、调用 engine、写 artifacts | 当前 Story primary owner。 |
| `engine/paper_simulation.py` | 提供 `run_paper_simulation` orchestration 和 JSON-safe serializer | shared，消费 S01..S04。 |
| `tests/test_cr041_paper_simulation.py` | 覆盖 engine 和 CLI artifact contract | 当前 Story primary owner。 |

## 4. 代码结构与文件影响范围

| 动作 | 文件路径 | 变更内容 |
|---|---|---|
| 创建 | `scripts/run_paper_simulation.py` | 新增 CLI runner；只读输入，写本地报告目录。 |
| 创建 | `tests/test_cr041_paper_simulation.py` | 新增 CR041 全链路 fixture、artifact schema 和 no-real-operation tests。 |
| 创建 | `engine/paper_simulation.py` | 新增 orchestration result、serializer 和 markdown summary helper。 |

## 5. 数据模型与持久化设计

| 对象 / 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `PaperSimulationRunManifest` | dict | run_id、inputs、hashes、config、artifact paths 必填 | 复跑审计。 |
| `PAPER-SIMULATION-REPORT.json` | dict | summary + artifacts + counters | 机器可读报告。 |
| `PAPER-SIMULATION-REPORT.md` | markdown | 摘要和风险边界 | 人读报告。 |
| `order_intents.json` | list | S02 schema | 本地 intent。 |
| `fills.json` | list | S03 schema | 本地成交。 |
| `positions.csv/json` | table | S04 schema | 本地持仓。 |
| `equity_curve.csv/json` | table | S04 schema | 本地净值。 |

持久化限定在用户指定 output root 下的 run 目录；不写数据湖、broker lake 或 catalog。

## 6. API / Interface 设计

| 接口 / 入口 | 输入 | 输出 | 调用方 | 说明 |
|---|---|---|---|---|
| `run_paper_simulation(config)` | 输入路径、初始资金、费用、滑点、run_id、output_root | `PaperSimulationRunResult` | CLI / tests | 本地 orchestration。 |
| `write_paper_simulation_artifacts(result, output_root, overwrite=False)` | result、输出根目录 | artifact path map | CLI | 默认拒绝覆盖。 |
| `main(argv=None)` | CLI 参数 | exit code | 用户 / tests | 不读取 env 凭据。 |

## 7. 核心处理流程

1. 解析 CLI 参数，校验输入文件存在。
2. 读取 admission package、target portfolio、market data、cost config。
3. 调用 S01 reader、S02 builder、S03 fill engine、S04 ledger。
4. 汇总 forbidden operation counters，必须全 0。
5. 写 artifacts 到 run 目录，生成 JSON/MD 报告。
6. 输出 run summary；不触发任何真实外部接口。

## 8. 技术设计细节

- CLI 库：第一版使用标准库 `argparse`，避免新增依赖；仍通过 `uv run --python 3.11 python` 执行。
- 文件格式：target portfolio 和 market data fixture 第一版支持 JSON/CSV 中至少一种；实现时优先 JSON fixture，CSV 可作为增强。
- 覆盖策略：无 `--overwrite` 时目录存在直接失败，防止报告误覆盖。
- 图示类型选择：线性 orchestration，无需 Mermaid。

## 9. 安全与性能设计

| 维度 | 设计措施 | 验证方式 |
|---|---|---|
| 安全 | CLI 参数不接受 token/password/account 字段 | 参数和输入扫描测试。 |
| 安全 | 不 provider fetch、不 lake write、不 publish | 静态扫描和 counters。 |
| 性能 | 本地日频小规模数据，内存处理 | fixture 全链路测试。 |

## 10. 测试设计

| 测试场景 | 前置条件 | 操作 | 预期结果 | 验证方式 |
|---|---|---|---|---|
| S05-T01 CLI 全链路 fixture | admission/target/market fixture | main / runner | 生成全部 artifacts | pytest |
| S05-T02 默认拒绝覆盖 | run dir 已存在 | runner | fail-closed | pytest |
| S05-T03 forbidden counters | 注入非 0 counter | runner | blocked | pytest |
| S05-T04 报告声明边界 | 正常运行 | 读 MD/JSON | not_authorization true，simulation/live false | pytest |
| S05-T05 输入缺失 | market path 不存在 | CLI | 非 0 exit / blocked result | pytest |

## 11. 实施步骤

| TASK-ID | 动作 | 目标文件 | 详细描述 | 对应测试 |
|---|---|---|---|---|
| CR041-S05-T1 | 创建 | `engine/paper_simulation.py` | 实现 orchestration result 和 serializer | S05-T01 |
| CR041-S05-T2 | 创建 | `scripts/run_paper_simulation.py` | 实现 argparse CLI 和本地输入校验 | S05-T01、S05-T05 |
| CR041-S05-T3 | 创建 | `engine/paper_simulation.py` | 实现 artifact writer 和 markdown summary | S05-T01、S05-T04 |
| CR041-S05-T4 | 创建 | `tests/test_cr041_paper_simulation.py` | 添加全链路、覆盖、防副作用测试 | S05-T01..S05-T05 |

## 12. 风险、难点与预研建议

### 12.1 实现灰区与取舍记录

| Clarification ID | 问题 | 选项与推荐 | 决策 / 答案 | 影响面 | 证据 | 重访条件 |
|---|---|---|---|---|---|---|
| N/A | 无阻断澄清项 | 第一版使用本地文件输入和 argparse CLI | 推荐方案符合 uv / no dependency 边界 | CLI / 文档 / 测试 | AGENTS.md Python 约束 | 若未来需要 Typer 或服务化 runner，另起 CR。 |

| 风险 / 难点 | 影响 | 缓解措施 / 预研建议 |
|---|---|---|
| 输出目录误覆盖 | 证据不可审计 | 默认拒绝覆盖，需显式 `--overwrite`。 |
| 用户把本地 paper simulation 当真实仿真账户 | 权限风险 | 报告和 manifest 强制 not_authorization。 |

### OPEN / Spike 跟踪

| ID | 类型（OPEN / Spike） | 问题 | 下一动作 | 责任方 |
|---|---|---|---|---|
| N/A | OPEN | 无 | 无 | N/A |

## 13. 回滚与发布策略

- 发布方式：本地 CLI + tests；不启动服务。
- 回滚触发条件：报告覆盖、真实操作计数非 0 未阻断、输出声明误写为 simulation-ready。
- 回滚动作：回退 CLI 和 artifact writer，保留 engine 内部函数。

## 14. Definition of Done

- [ ] 14 个章节全部填写完成
- [ ] 文件影响范围、接口、测试与实施步骤可直接指导编码
- [ ] `confirmed=false` 时不进入实现
- [ ] OPEN / Spike 已清点

## 人工确认区

CP5 批次人工确认文件：`process/checkpoints/CP5-CR041-ALL-STORIES-LLD-BATCH.md`。
