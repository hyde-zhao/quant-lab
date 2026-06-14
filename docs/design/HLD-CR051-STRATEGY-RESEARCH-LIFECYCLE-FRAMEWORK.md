---
status: "active-cp3-approved-ready-for-story-planning"
version: "0.5"
change_id: "CR-051"
owner: "host-orchestrator"
source_cr: "process/changes/CR-051-STRATEGY-RESEARCH-LIFECYCLE-FRAMEWORK-2026-06-14.md"
source_decision: "USER-20260614-STRATEGY-RESEARCH-LIFECYCLE-FIRST"
runtime_authorized: false
provider_fetch_authorized: false
lake_write_authorized: false
trading_authorized: false
---

# CR051 策略研究生命周期框架 HLD

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 0.1 | 2026-06-14 | host-orchestrator | 初版 HLD 草案：定义策略研究生命周期、策略 taxonomy、仓库 / 归档 / 数据湖拓扑、研究 PC 与交易 PC 使用方式、后续 CR 路线 |
| 0.2 | 2026-06-14 | host-orchestrator | 补充项目整体迁移设计、Git 归档策略、迁移阶段门禁和回滚策略；将用户“推进 CR051”记录为 active-lock 解锁输入 |
| 0.3 | 2026-06-14 | host-orchestrator | 纳入用户当前硬件现状：NAS 512G SSD + 4T RAID + 14T HDD、研究主机 2T SSD、交易主机 512G SSD；细化冷热分层和主机职责 |
| 0.4 | 2026-06-14 | host-orchestrator | 纳入用户项目命名决策：正式项目名改为 `quant-lab`，`local_backtest` 作为 legacy alias 和历史审计名保留；新增命名迁移和兼容策略 |
| 0.5 | 2026-06-14 | host-orchestrator | 回填 CP3 approved：用户接受单主仓库、硬件冷热分层、交易主机边界、阶段化迁移、不授权真实操作和 `quant-lab` 正式命名 |

## 1. 问题定义

当前项目已有多因子研究闭环、paper simulation runner 和 QMT / MiniQMT 策略交付框架，但它们还不是一个完整的策略研究生命周期系统。缺口集中在：

1. 信息收集、idea、立项、研究协议、研究过程数据、研究报告、研究交付件、数据湖和交易交付之间没有统一生命周期。
2. 当前主要支持多因子策略中段能力，事件型、机器学习、择时、技术型、统计套利等策略类型没有统一 taxonomy 和扩展协议。
3. 研究过程中产生的大量 artifact、报告、模型、策略包、数据快照、外部资料和交易反馈缺少分层归档设计。
4. Git 仓库、外部 archive、market data lake、broker lake、研究 PC 和交易 PC 的职责边界未被统一冻结。
5. 后续 CR052+ 需要可恢复上下文，否则容易把多因子证明周期、事件型策略、ML Spike 和 QMT/MiniQMT 交付混在一起。

本 HLD 设计一个 `Strategy Research Lifecycle Framework`，作为后续策略研究、证明、消费和反馈的上层治理框架。

## 2. 目标与非目标

### 目标

| 目标 ID | 目标 | 可度量成功标准 |
|---|---|---|
| G-01 | 建立完整策略研究生命周期 | 覆盖不少于 10 个生命周期阶段：信息源、idea、立项、协议、研究运行、验证、准入、消费、交付、反馈 / 退役 |
| G-02 | 建立策略类型 taxonomy | 首版至少覆盖 8 类策略：多因子、事件型、择时、技术型、统计套利、ML、组合优化 / 增强指数、tick / 高频 Spike |
| G-03 | 冻结项目归档方式 | 明确 Git、external research archive、market data lake、broker lake、trading PC local archive 5 类存储的写入 owner 和禁止内容 |
| G-04 | 冻结仓库拓扑 | 首版明确采用 1 个主代码仓库 + 外部 artifact / data archive，不拆多代码仓库；列出切换条件 |
| G-05 | 定义研究 PC / 交易 PC 使用方式 | 明确研究 PC 可写代码和研究 archive；交易 PC 只消费 release package / read-only checkout，不写研究 archive |
| G-06 | 规划后续 CR | 至少定义 CR052..CR056 的标题、目标、前置条件、非授权边界和消费对象 |
| G-07 | 定义本项目整体迁移路径 | 至少覆盖现有 Git 仓库归档、目标目录结构、历史研究输出搬迁、验证门禁和回滚点 5 类事项 |
| G-08 | 冻结项目新名称和旧名兼容策略 | 正式新名为 `quant-lab`；`local_backtest` 保留为 legacy alias；历史审计文件不做批量重写 |

### 非目标

CR051 不做以下事项：

- 不实现多因子完整证明周期；该项进入 CR052。
- 不新增事件型、ML、择时或其他策略 pipeline；这些进入 CR053+。
- 不交付具体策略。
- 不恢复 CR046，不执行 QMT terminal shadow，不连接或安装 MiniQMT。
- 不读取凭据、账户、资金、持仓、委托、成交。
- 不触发 provider fetch、真实 market data lake write、catalog publish。
- 不 submit/cancel，不 simulation/live。

### 项目命名决策

用户已在 CP3 设计讨论中明确：CR051 后项目正式名称采用 `quant-lab`，理由是比 `local_backtest` 更简洁，且不再把项目范围限制为本地回测。

| 名称层级 | 主选值 | 兼容 / 迁移策略 |
|---|---|---|
| 正式项目显示名 | `quant-lab` | README、用户手册、新设计文档和后续 CR 使用新名。 |
| Git 仓库 / 目录名 | `quant-lab` | 目录实际重命名进入后续迁移阶段；CP3 不执行文件系统重命名。 |
| Python project name | `quant-lab` | 后续实现阶段评估修改 `pyproject.toml` 的 `name`；当前 `package = false`，但仍需测试命令和 lock 一致性校验。 |
| 逻辑根环境变量 | `QUANT_LAB_REPO_ROOT` | 新变量作为主名；`LOCAL_BACKTEST_REPO_ROOT` 保留为 legacy alias，迁移期内可读但不作为新文档主推。 |
| 历史审计名 | `local_backtest` | 旧 CR、process、handoff、测试证据和历史命令不批量替换，避免污染审计链。 |
| Windows 默认路径 | `C:\quant-lab\...` | CR046 / CR049 相关旧路径 `C:\local_backtest\...` 后续按 Story 单独迁移，必须允许用户覆盖。 |

命名迁移原则：

1. 新文档、新 Story、新迁移计划默认使用 `quant-lab`。
2. 历史 `process/`、旧 CR、旧 handoff、旧验证输出中的 `local_backtest` 表示当时项目身份，不批量重写。
3. 仓库目录重命名、远端仓库重命名、Git tag / push、Windows 路径重命名和环境变量替换均不是 CP3 授权动作。
4. 后续迁移实现必须提供 alias / compatibility 检查，确保旧文档中的命令不会被误解为仍要求创建旧项目结构。

## 3. Architecture Gray Areas

### GA-01：仓库是一个还是多个？

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| A. 单一主代码仓库 + 外部 archive/lake | 最简单；代码、schema、文档、测试、流程规则集中；适合单人 / 小团队研究；便于 CR 追溯 | 仓库可能变大；需要严格禁止大 artifact 入 Git | Git repo、research PC、CI、文档、schema、流程状态 | 推荐 | 默认采用；当多个团队并行、权限隔离或策略 IP 隔离成为硬要求时再拆 |
| B. 多代码仓库：research-core / data-lake / trading-runtime / strategy-packages | 权限隔离清晰；交易 PC 可只拉 runtime repo | 运维和跨 repo 追溯成本高；当前会制造过早复杂度 | repo 管理、release、CI、版本联动、权限 | 不推荐作为首版 | 当交易 runtime 进入真实生产、多用户权限和发布流程成熟后评估 |
| C. 单仓库包含所有 artifact | 操作直观；无需外部归档 | 高风险：真实数据、报告、模型、凭据、交易证据容易污染 Git | 安全、仓库体积、合规、恢复 | 禁止 | 不采用 |

结论：首版使用 **一个主代码仓库 + 外部 artifact / data archive**。

### GA-02：研究过程数据与 market data lake 是否合并？

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| A. 分离：market data lake、research archive、broker lake 独立 | 事实源边界清晰；研究 artifact 不污染生产数据；broker facts 可独立脱敏和保留 | 需要 manifest / registry 连接多个 root | 数据治理、归档、审计、安全 | 推荐 | 默认采用 |
| B. 合并到同一个 lake root 的不同前缀 | 路径统一 | 权限和生命周期混淆；研究临时产物可能被误认为 current truth | 数据湖、研究报告、交易事实 | 条件备选 | 只有具备强 ACL / namespace / retention policy 时可评估 |
| C. 都放在 Git / reports | 操作轻 | 大 artifact 和敏感数据污染仓库 | Git、安全、审计 | 禁止 | 不采用 |

结论：三类事实分离：`MARKET_DATA_LAKE_ROOT`、`RESEARCH_ARCHIVE_ROOT`、`BROKER_LAKE_ROOT` / trading archive。

### GA-03：交易 PC 是否直接使用研究仓库？

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| A. 交易 PC 只消费 release package，可选 read-only checkout | 最小权限；避免研究脚本 / 实验依赖进入交易环境；便于人工校验 zip + sha256 | 需要清晰 package / manifest / runbook | CR046、交易 PC、QMT terminal、MiniQMT runner | 推荐 | 默认采用 |
| B. 交易 PC clone 完整研究仓库并直接运行 | 方便同步最新代码 | 极易误运行研究脚本、读取 archive、污染交易环境 | 安全、依赖、运行授权 | 禁止作为默认 | 仅可在隔离测试机、明确 read-only 和无 runtime 授权下临时审查 |
| C. 自动同步研究结果到交易 PC | 自动化强 | 会绕过人工 gate、传输授权和 checksum 审查 | 传输、导入、交易授权 | 后置 | CR047/CR048/CR049 后按 runtime gate 再评估 |

结论：交易 PC 默认 **不作为研究环境**，只作为受控策略包消费端。

### GA-04：是否现在实现所有策略类型？

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| A. 先框架，再多因子证明周期，再逐类扩展 | 风险最低；先证明生命周期，再扩展策略族 | 事件型 / ML 交付较晚 | CR051..CR056 | 推荐 | 用户已确认 |
| B. 框架 + 多因子 + 事件型并行 | 快速覆盖更多策略 | 容易在 taxonomy 未稳定时扩散复杂度 | 需求、Story、测试 | 不推荐 |
| C. 直接做具体策略 | 快速看到结果 | 生命周期和归档继续缺失，后续不可复用 | 研究质量、交付质量 | 不推荐 |

结论：采用 A。

## 4. 推荐架构

```text
                         Git repository: quant-lab
                         legacy alias: local_backtest
              docs / schemas / code / tests / redacted fixtures / manifests
                                      |
                                      v
Research PC  ----------------  Research Workspace  ----------------
  full dev checkout             idea / project / run / report        |
  writes code + docs            writes external archive              |
                                      |                              |
                                      v                              |
                        RESEARCH_ARCHIVE_ROOT                        |
        information_sources / ideas / projects / runs / reports / deliverables
                                      |
                                      v
                         StrategyAdmissionPackage
                                      |
                                      v
                         StrategyCoreContract
                                      |
            +-------------------------+-------------------------+
            |                                                   |
            v                                                   v
   Paper Simulation Consumer                         Strategy Package Builder
   CR041 / future CR055                              CR046 / future CR047
            |                                                   |
            v                                                   v
   paper evidence archive                      strategy-package.zip + sha256
                                                              |
                                                              v
                                                    Trading PC / QMT PC
                                                   read-only package usage
                                                              |
                                                              v
                                               trading local archive / broker lake
                                               shadow / runtime evidence only
```

## 5. 仓库与归档拓扑

### 5.1 存储分层

| 层 | 推荐位置 | 写入方 | 可放内容 | 禁止内容 |
|---|---|---|---|---|
| 主 Git 仓库 | `quant-lab`（legacy alias: `local_backtest`） | 研究开发 / meta-flow | 代码、schema、文档、测试、redacted fixture、小型 manifest、CR / CP 状态 | 真实凭据、真实账户、交易密码、原始大数据、完整模型大 artifact、broker facts |
| Research Archive | `$RESEARCH_ARCHIVE_ROOT` | 研究 PC | 信息源快照、idea 附件、研究项目、run artifact、模型 artifact、研究报告、交付件草案 | 未脱敏凭据、交易账户敏感明细、直接可下单 payload |
| Market Data Lake | `$MARKET_DATA_LAKE_ROOT` | data lake pipeline | raw / manifest / canonical / gold / quality / catalog | 策略研究临时产物、交易事实、broker order / fill |
| Broker / Trading Archive | `$BROKER_LAKE_ROOT` 或交易 PC local archive | 交易运行流程 | 订单、回报、shadow evidence、runtime evidence、脱敏日志、incident | 研究代码、未授权策略实验、市场数据 current truth |
| Strategy Package Exchange | 手工 / 受控文件通道 | 后续 CR047+ | `strategy-package-*.zip`、`.sha256`、`manifest.yaml`、docs bundle | 自动执行脚本、未审查凭据、未授权 runner config |

### 5.2 Research Archive 目录设计

```text
$RESEARCH_ARCHIVE_ROOT/
  registry/
    information_sources.yaml
    strategy_ideas.yaml
    research_projects.yaml
    strategy_registry.yaml
    research_runs.yaml
  information_sources/
    <source_id>/
      source-card.yaml
      raw-notes/
      normalized-summary.md
      license-and-usage.md
  ideas/
    <idea_id>/
      idea-card.yaml
      hypothesis.md
      source-refs.yaml
      triage-decision.md
  projects/
    <project_id>/
      charter.yaml
      protocol.yaml
      data-contract.yaml
      decision-log.md
      runs/
        <run_id>/
          run-manifest.yaml
          config/
          inputs/
          outputs/
          validation/
          reports/
          deliverables/
      final/
        research-report.md
        admission-package.json
        strategy-core-contract.yaml
        handoff-summary.md
  deliverables/
    <strategy_id>/<version>/
      strategy-package-inputs/
      checksums/
      release-notes.md
  feedback/
    paper/
    shadow/
    live/
    retirement/
```

规则：

1. Archive root 不进入 Git。
2. Git 只保存 archive manifest、schema、redacted summary 和可复验入口。
3. 每个 `run_id` 必须有 `run-manifest.yaml`，记录 code commit、data release、config hash、random seed、inputs refs、outputs refs。
4. 任何从 archive 进入交易 PC 的 artifact 必须经过 strategy package exchange，不允许直接复制整个 project 目录。

### 5.3 Git 仓库目录使用

| 路径 | 用途 | CR051 后建议 |
|---|---|---|
| `docs/research/` | 长期研究框架、协议、手册、策略族说明 | 新增生命周期、taxonomy、protocol、archive governance 文档 |
| `docs/design/` | HLD、蓝图、领域图、依赖图、ADR | 新增 CR051 HLD，后续更新 BLUEPRINT / DOMAIN / DEPENDENCY |
| `process/research/` | 过程证据、run summary、审计恢复点 | 只放小型摘要和指针；大 artifact 外置 |
| `engine/research_*` | 研究生命周期和 registry 的未来代码 | CR051 后续实现时新增 |
| `tests/` | schema / guardrail / fixture tests | 后续验证 no-real-operation、archive manifest、taxonomy route |
| `reports/` | 历史本地报告 / 小型输出 | 不再作为主归档根；未来只保留兼容 / redacted summary |

### 5.4 本项目迁移目标结构

用户已明确：本次项目改造完成后，会将当前 legacy `local_backtest` 全部迁移为本 HLD 设计后的 `quant-lab` 结构，包括 Git 归档。因此 CR051 必须把迁移作为一等设计目标，而不是只设计未来新项目。

首版迁移目标仍保持一个主代码仓库，但把仓库内容按“长期真相、运行态、外部归档指针”分层：

| 迁移后区域 | 目标职责 | 当前来源 | 迁移动作 | Git 保留策略 |
|---|---|---|---|---|
| `docs/research/` | 研究生命周期、taxonomy、协议、归档治理、策略族手册 | `docs/CR030-*`、`docs/research/*`、CR051 HLD | 归并为 CR051 后的长期研究治理文档 | 保留全文；作为长期文档 |
| `docs/design/` | HLD、ADR、蓝图、领域对象、依赖图、Feature 设计矩阵 | `process/HLD.md`、`process/ARCHITECTURE-DECISION.md`、`docs/design/*` | 将 legacy 过程设计迁到 scoped 或 canonical 设计文档 | 保留当前和新结构；旧路径只读索引 |
| `process/` | 当前工作流运行态、CR、CP、Story、handoff、context capsule | `process/*` | 保留审计历史；后续新增文件按 CR scoped 命名 | 保留小型 Markdown/YAML；不放大 artifact |
| `process/research/` | 小型 run summary、manifest 指针、redacted evidence | 当前 `process/research/*` | 大 artifact 移出到 `$RESEARCH_ARCHIVE_ROOT`，仓库只留 summary / manifest / checksum / pointer | 只保留小型摘要和指针 |
| `$RESEARCH_ARCHIVE_ROOT` | 研究附件、run artifact、模型、完整报告、候选交付件 | 未来从 `process/research/*`、`reports/*`、实验输出搬迁 | 由迁移脚本 / 清单逐项复制，生成 manifest；本 HLD 不执行搬迁 | 不进入 Git |
| `$MARKET_DATA_LAKE_ROOT` | 市场数据 current truth | 现有外置 lake | 不迁入 Git；只在 manifest 中引用 data release | 不进入 Git |
| `$BROKER_LAKE_ROOT` / trading archive | 交易运行事实、shadow/runtime evidence | 后续 CR048+ | 仅未来 runtime gate 授权后写入 | 不进入 Git |
| `reports/` | 兼容入口 / 人工查看摘要 | 历史 `reports/*` | 降级为兼容区；新研究不以其为主归档 | 只保留小型 redacted summary |

迁移后的仓库不得把外部 archive、market data lake、broker lake 或交易 PC local archive 合并进 Git。当前已有 `process/research/*` 可先作为历史摘要留存；只有在 CR051/CR052 后续实现阶段明确识别为大 artifact 或敏感事实的文件，才搬出到 archive，并用 manifest 回链。

### 5.5 Git 归档策略

CR051 设计要求在实施大规模结构迁移前建立明确 Git 归档点：

| 归档点 | 触发时机 | 动作 | 目的 |
|---|---|---|---|
| `pre-cr051-migration-baseline` | CR051 实施前 | 将当前全部修改提交到 Git；可选打 tag | 为结构迁移提供硬回退点 |
| `cr051-design-approved` | CP3 approved 后 | 提交 CR051 设计、CP2/CP3、迁移计划 | 冻结迁移目标，不再边改目标边迁移 |
| `cr051-pre-file-move` | 执行目录移动 / 大批量重命名前 | 提交实现前准备和验证脚本 | 让文件移动可单独回滚 |
| `cr051-post-file-move` | 目录移动完成、静态检查通过后 | 提交机械迁移结果 | 将机械迁移与语义修改隔离 |
| `cr051-verified` | CP7 PASS / PASS_WITH_RISK 后 | 提交验证修复和报告 | 作为 CP8 终验候选 |

本轮已按用户要求完成 `bd679fe Archive workspace before CR051 migration`，作为 CR051 前基线提交。后续是否创建 Git tag 属于独立 Git 归档动作，可在 CP3 / CP5 Decision Brief 中作为人工决策项确认；默认不自动 push、不自动删除分支、不自动重写历史。

### 5.6 迁移阶段门禁

项目整体迁移必须拆成可验证阶段：

| 阶段 | 目标 | 允许动作 | 禁止动作 | 验证 |
|---|---|---|---|---|
| M0 Baseline Archive | 固化当前仓库状态 | `git add --all`、`git commit`、可选 tag | `git reset --hard`、删除历史、push | `git status --short` clean |
| M1 Design Freeze | 冻结目标结构和迁移规则 | 更新 CR051 HLD / ADR / CP2 / CP3 | 移动大量文件 | CP2 / CP3 approved |
| M2 Inventory | 盘点待迁移文件和归档分类 | 生成迁移清单、大小 / 敏感性 / owner 分类 | 读取凭据、读取未授权外部 lake 数据 | 清单审查 |
| M3 Mechanical Move | 执行目录移动 / 重命名 / import 修正 | 仅按清单移动仓库内文件和更新引用 | 删除未分类文件、搬入外部大数据 | diff review、路径引用检查 |
| M4 Archive Externalization | 将大 artifact 外置并写 manifest | 仅处理经 M2 分类可外置的 artifact | 复制凭据、账户、broker facts 或真实 lake current truth | manifest checksum / pointer test |
| M5 Verification | 验证新结构可用 | 运行目标测试、CR tracking、路径 guardrail | 真实 trading runtime、provider fetch、lake write、publish | CP6 / CP7 |
| M6 Release Readiness | 形成迁移说明和回滚方案 | release docs、migration notes、feedback plan | 自动真实发布 / push | CP8 approved |

### 5.7 迁移回滚策略

迁移回滚不依赖删除历史文件，而依赖 Git 归档点和清单化移动：

1. 若设计未通过，回退到 `pre-cr051-migration-baseline`，CR051 保持 blocked 或 changes_requested。
2. 若机械移动失败，回退到 `cr051-pre-file-move`，重新生成迁移清单。
3. 若外置归档失败，保留 Git 小型摘要，撤销 archive manifest pointer，不删除原始 Git 历史。
4. 若验证失败，生成 `NEEDS_REWORK`，修复引用、测试或 guardrail 后重新 CP6 / CP7。
5. 任何回滚都不得读取、打印或提交凭据，不得删除外置 lake / archive 原始数据，不得自动 push。

## 6. 研究 PC 与交易 PC 使用方式

### 6.0 当前硬件事实与推荐分层

用户当前可用硬件：

| 设备 / 存储 | 容量 | 推荐职责 | 不建议职责 |
|---|---:|---|---|
| 主力研究主机 SSD | 2T | 主开发仓库、虚拟环境、常用研究 workspace、近期 run cache、可复验小样本 fixture、报告草案 | 长期保存全量市场数据湖、长期保存所有大 artifact |
| 交易主机 SSD | 512G | 只读策略包消费区、QMT / MiniQMT 相关运行环境、少量 shadow/runtime 日志、checksum 校验工作区 | 研究开发、全量 research archive、全量 market data lake、实验批量运行 |
| NAS SSD | 512G | NAS 热数据层：近期研究 run cache、活跃 strategy package exchange、近期 manifest / checksum 索引 | 长期冷归档、全量历史行情 |
| NAS 4T RAID HDD | 4T | NAS 温数据层：`RESEARCH_ARCHIVE_ROOT` 主体、研究报告、run artifact、模型 artifact、可复验交付件、重要快照 | 未脱敏交易凭据、交易账户敏感原文 |
| NAS 14T HDD | 14T | NAS 冷数据层：长期 archive、旧 run、历史快照、备份、非活跃大 artifact、可恢复归档 | 高频热读写 workspace、交易主机实时运行目录 |

推荐逻辑：

1. 研究主机 2T SSD 承担高频读写和开发效率，保留完整 Git checkout、`.venv` / uv cache、近期 experiment workspace，但不作为长期 archive 唯一真相源。
2. NAS 4T RAID 作为 `RESEARCH_ARCHIVE_ROOT` 默认主位置，承载可恢复研究项目和较重要 artifact；NAS 512G SSD 作为活跃热层，减少常用 manifest 和近期 run 的访问延迟。
3. NAS 14T HDD 作为长期冷归档和备份层，不要求高性能；适合旧研究、历史 run、快照和迁移前归档副本。
4. 交易主机 512G SSD 只保留交易环境、策略包、校验文件和少量运行证据；默认不 clone 完整研究 archive，不运行研究脚本。
5. 所有路径先以环境变量 / 配置表达，不在 Git 写死 NAS 私有挂载路径。

### 6.0.1 基于现状的路径角色建议

| 逻辑根 | 首选物理位置 | 备选位置 | 说明 |
|---|---|---|---|
| `QUANT_LAB_REPO_ROOT` | 主力研究主机 2T SSD | 交易主机 read-only checkout；legacy alias: `LOCAL_BACKTEST_REPO_ROOT` | 主仓库 canonical；交易主机只在必要时只读查看。 |
| `RESEARCH_WORKSPACE_ROOT` | 主力研究主机 2T SSD | NAS SSD 热层 | 近期研究执行目录，可清理 / 可重建，不是长期真相源。 |
| `RESEARCH_ARCHIVE_ROOT` | NAS 4T RAID HDD | NAS 14T HDD 冷层 | 研究项目、run artifact、报告和交付件归档主根。 |
| `RESEARCH_HOT_CACHE_ROOT` | NAS 512G SSD | 主力研究主机 SSD | 近期 run、manifest index、常用报告和 package exchange 热缓存。 |
| `RESEARCH_COLD_ARCHIVE_ROOT` | NAS 14T HDD | NAS 4T RAID HDD | 历史 run、旧快照、迁移前归档副本。 |
| `MARKET_DATA_LAKE_ROOT` | 既有外置 lake / NAS 专用数据区 | 后续单独确认 | 仍与 research archive 分离；CR051 不执行 lake 搬迁。 |
| `STRATEGY_PACKAGE_EXCHANGE_ROOT` | NAS SSD 热层或研究主机 staging | 手工复制到交易主机 | 放 zip、sha256、manifest、docs bundle；传输仍需后续授权。 |
| `TRADING_LOCAL_ARCHIVE_ROOT` | 交易主机 512G SSD 小型目录 | NAS broker/trading archive | 只保存脱敏 shadow/runtime evidence 和少量日志；长期回收需独立策略。 |

### 6.0.2 容量水位和保留策略

| 层 | 建议水位 | 保留策略 | 触发动作 |
|---|---:|---|---|
| 研究主机 2T SSD | 70% soft / 85% hard | 仅保留近期活跃项目、近期 run、开发 cache | 超过 soft 时归档非活跃 run 到 NAS；超过 hard 时停止新大 run 并要求清理 |
| 交易主机 512G SSD | 60% soft / 75% hard | 仅保留当前策略包、最近运行证据、必要日志 | 超过 soft 时清理旧 package / 日志；超过 hard 时禁止导入新 package |
| NAS 512G SSD | 75% soft / 90% hard | 热缓存和 exchange 文件短期保留 | 定期下沉到 4T RAID 或 14T 冷层 |
| NAS 4T RAID | 75% soft / 90% hard | 主 archive，保留 active / important projects | 超过 soft 时把 closed / old runs 下沉到 14T 冷层 |
| NAS 14T HDD | 80% soft / 92% hard | 冷归档和备份 | 超过 soft 时生成清理候选清单；不得自动删除 |

这些水位是设计默认值，不是自动执行策略。任何删除、迁移、压缩、去重或远程同步都必须在后续实现 / 运维 CR 中另行授权。

### 6.1 研究 PC

研究 PC 是完整研发环境：

| 能力 | 允许 | 约束 |
|---|---|---|
| Git 操作 | clone / branch / commit / test | 不提交 archive 大文件、真实凭据、真实账户 |
| 研究运行 | 运行离线研究、生成报告、写 `$RESEARCH_ARCHIVE_ROOT` | provider / lake / publish 仍需独立授权 |
| 数据消费 | 只读 `$MARKET_DATA_LAKE_ROOT` current truth 或 fixture | 缺数据返回 required_missing，不自动补数 |
| 策略包准备 | 生成 strategy package inputs / manifest / checksum 草案 | 不传输到交易 PC，除非后续 CR 授权 |

### 6.2 交易运行 PC

交易 PC 是受控运行环境：

| 能力 | 默认 | 约束 |
|---|---|---|
| Git 仓库 | 可选 read-only checkout 或不 checkout | 默认不作为研究开发环境 |
| 策略包 | 只接收 `zip + sha256 + manifest + docs bundle` | 人工校验 checksum，导入 / 运行需独立 gate |
| QMT terminal | 未来 CR048 处理 | CR051 不授权 |
| MiniQMT runner | 未来 CR049 处理 | CR051 不安装、不连接 |
| 运行证据 | 写 trading local archive / broker lake | 不写研究 archive，不回写 Git |

交易主机 512G SSD 容量有限，因此默认只保留：

1. 当前被人工批准导入的 strategy package。
2. 对应 `manifest.yaml`、`.sha256`、docs bundle。
3. 最近 shadow / runtime evidence 的脱敏摘要。
4. QMT / MiniQMT 运行所需最小配置和日志。

交易主机不得作为 `RESEARCH_ARCHIVE_ROOT`，不得保存全量 market data lake，不得保存历史大 run。

### 6.3 研究过程中的仓库使用

| 阶段 | Git | Research Archive | Data Lake | Trading PC |
|---|---|---|---|---|
| 信息收集 | source schema / summary | 原始资料、摘要、许可证 | N/A | 不参与 |
| idea | idea schema / redacted card | idea 附件、来源引用 | N/A | 不参与 |
| 立项 | charter schema / template | charter、protocol、decision log | 只读数据需求 | 不参与 |
| 研究运行 | code / tests / config schema | run artifact、报告、模型 | 只读 current truth | 不参与 |
| 准入 | admission schema / report summary | admission package、evidence | 只读 lineage | 不参与 |
| 交付准备 | package schema / manifest | strategy-core input、deliverable draft | 只读 | 只接收授权 package |
| 运行反馈 | feedback schema | paper/shadow/live summary | N/A | 写 trading evidence，脱敏摘要回流 |

## 7. 生命周期状态机

```text
captured
  -> triaged
  -> chartered
  -> protocol_ready
  -> research_running
  -> validation_ready
  -> admission_review
  -> research_only | paper_candidate | delivery_candidate | rejected
  -> packaged
  -> paper_observed
  -> shadow_observed
  -> runtime_candidate
  -> live_observed
  -> rework | retired
```

| 状态 | 进入条件 | 退出条件 | 失败路径 |
|---|---|---|---|
| `captured` | idea-card 存在 | triage decision | 缺来源则 archived / rejected |
| `chartered` | 立项目标、范围、成功标准齐全 | protocol approved | 缺数据 / 样本不可得则 blocked |
| `research_running` | run manifest 和数据合同齐全 | run output recorded | 数据缺失、泄漏、配置无 hash 则 fail-closed |
| `admission_review` | validation evidence 完整 | admission decision | blocked claims 未解则 research_only / rejected |
| `delivery_candidate` | StrategyAdmissionPackage pass + StrategyCoreContract 可生成 | 进入 CR055 / CR047 | 不等于 trade-ready |
| `runtime_candidate` | paper/shadow evidence + runtime gate | 进入 CR048/CR049/后续交易 CR | 缺授权则 blocked |
| `retired` | 退役决策 | 归档完成 | 不得再被自动选为新策略 |

## 8. 策略类型 Taxonomy

| StrategyFamily | 首版状态 | 专属研究协议 | 进入条件 |
|---|---|---|---|
| `multifactor_cross_sectional` | CR052 首个完整证明周期 | 因子构造、因子检验、组合模型、稳健性、成本容量、准入 | CR051 approved |
| `event_driven` | CR053 candidate | 事件定义、available_at、事件窗口、对照组、异常收益、事件组合 | CR052 证明生命周期稳定 |
| `market_timing` | later candidate | 市场状态变量、仓位函数、walk-forward、回撤控制 | 生命周期稳定且数据支持 |
| `technical_signal` | later candidate | 指标定义、参数稳定性、过拟合控制、交易成本 | 生命周期稳定 |
| `statistical_arbitrage` | later candidate | pair selection、spread、协整 / 相关稳定、容量和交易约束 | minute / borrow / execution assumptions 明确 |
| `ml_strategy` | CR054 Spike | feature store、label、walk-forward、model registry、drift | 用户接受 ML 依赖和模型治理成本 |
| `enhanced_indexing_optimizer` | later Spike | 约束优化、tracking error、风险暴露、成本优化 | P0 多因子不足且接受 optimizer |
| `tick_or_hft` | CR050 / later Spike | tick / order book / replay / latency / resource control | MiniQMT / Level2 / runtime 权限独立就绪 |

## 9. 领域对象

| 对象 | Owner | 关键字段 | Git / Archive 归属 |
|---|---|---|---|
| `InformationSource` | FEAT-10 | source_id、source_type、license、trust_level、captured_at、usage_boundary | Git 存 schema / summary；archive 存原始材料 |
| `StrategyIdea` | FEAT-10 | idea_id、hypothesis、source_refs、family_hint、expected_edge、failure_mode | Git 可存 redacted card；archive 存附件 |
| `ResearchProject` | FEAT-10 | project_id、idea_id、family、objective、success_criteria、scope、owner | Git 存 schema；archive 存 charter |
| `ResearchProtocol` | FEAT-10 / family owner | family、steps、required_evidence、fail_closed_rules | Git 存模板和版本 |
| `ResearchRun` | FEAT-10 | run_id、commit、data_release、config_hash、artifact_refs | Git 存 manifest summary；archive 存 artifact |
| `ValidationEvidence` | FEAT-10 | leakage、robustness、cost、capacity、sample_split、blocked_claims | archive + Git summary |
| `StrategyAdmissionPackage` | FEAT-03 / FEAT-10 | admission_status、blocked_reasons、unlock_conditions、allowed_claims | archive canonical；Git 可存 redacted fixture |
| `StrategyCoreContract` | FEAT-09 / FEAT-10 | strategy_id、input_schema、target_portfolio_schema、risk_assumptions | archive + strategy package input |
| `StrategyPackage` | FEAT-09 | zip、manifest、sha256、docs bundle | exchange area / trading PC |
| `LiveFeedbackRecord` | FEAT-10 / FEAT-06 | run_id、strategy_id、drift、performance、incident、retirement_decision | broker/trading archive + redacted summary |

## 10. 后续 CR 路线

| CR | 标题 | 目标 | 前置条件 | 非授权边界 |
|---|---|---|---|---|
| CR052 | 多因子策略完整证明周期 | 在 CR051 框架上跑通多因子从 idea 到 delivery-candidate 的完整证明周期 | CR051 CP8 approved | 不启动 QMT/MiniQMT，不 simulation/live |
| CR053 | 事件型策略研究流程 | 建立事件型策略 protocol、event spec、available_at、事件窗口和异常收益验证 | CR052 proof cycle pass | 不默认真实事件补数，不运行交易 |
| CR054 | ML 策略研究协议 Spike | 设计 ML feature / label / walk-forward / model registry / drift | CR052 pass + 用户接受 Spike | 不默认新增 ML 依赖，不训练真实大模型 |
| CR055 | 研究消费桥 | 把 StrategyAdmissionPackage 转为 StrategyCoreContract / paper input / package input | CR051 / CR052 | 不真实传输交易 PC，不导入 QMT |
| CR056 | 研究反馈闭环 | paper / shadow / runtime evidence 回流研究、退役和再研究 | CR055 + 后续 runtime evidence schema | 不读取敏感账户原文，不自动触发交易 |

## 11. 与 CR046 的关系

| 项 | CR051 职责 | CR046 职责 | 边界 |
|---|---|---|---|
| 策略研究生命周期 | 定义 idea -> project -> run -> admission -> feedback | 不负责 | CR051 上游 |
| StrategyCoreContract | 定义研究侧如何产生和治理 | 定义交易包如何消费 | 双方通过 contract 对接 |
| QMT / MiniQMT 交付 | 只提供 delivery-candidate 输入 | 定义 package / target / validation framework | CR051 不恢复 CR046 |
| 运行授权 | 不授权 | 不授权，后续 CR048/CR049 | 二者都不执行 runtime |

## 12. 非功能设计

| 质量属性 | 设计要求 | 验证方式 |
|---|---|---|
| 可复现 | 每个 run 必须记录 commit、data release、config hash、random seed、artifact refs | manifest fixture / schema test |
| 可审计 | idea、project、protocol、run、report、admission、package、feedback 全链路有 ID | traceability test |
| 安全 | Git 不存真实凭据、账户、broker facts、大型真实数据 | forbidden content scan |
| 可扩展 | 策略族通过 protocol 扩展，不改生命周期主状态机 | taxonomy route fixture |
| 可移植 | 研究 PC 和交易 PC 分离，交易 PC 消费 package | package manifest review |
| 可回退 | 每个 project/run/package 有 previous ref 和 retirement/rework 记录 | archive manifest review |
| 可迁移 | 现有项目迁移具备 Git 归档点、迁移清单、机械移动隔离和回滚路径 | migration checklist / path reference test |

## 13. 风险

| 风险 ID | 风险 | 严重度 | 缓解 |
|---|---|---:|---|
| R-01 | 研究 archive 与 market data lake 混用，污染 current truth | High | 强制分离 root；Git 只存 pointers |
| R-02 | 交易 PC clone 完整研究仓库后误运行实验脚本 | High | 默认只消费 release package；checkout 只读 |
| R-03 | CR051 过大导致实现阶段失焦 | Medium | CR051 只完成框架；多因子放 CR052，事件/ML 放后续 |
| R-04 | 多策略 taxonomy 过度设计 | Medium | 首版只定义协议和 extension point；只实现多因子证明周期 |
| R-05 | archive 中保存未脱敏外部信息或敏感材料 | High | source card 必须记录 usage boundary；敏感信息禁止进 Git |
| R-06 | Research pass 被误读为 trade-ready | High | admission gate 明确 research-only / paper-candidate / delivery-candidate / runtime-candidate |
| R-07 | 迁移时把过程 artifact 或真实数据误纳入 Git | High | M2 inventory 分类 + forbidden content scan + Git 只存 summary / manifest / pointer |
| R-08 | 大规模文件移动与语义修改混在一个提交，难以回滚 | Medium | 使用 Git 归档点，机械移动与语义修改分提交 |
| R-09 | 迁移后旧路径引用失效 | Medium | 路径引用检查、兼容索引、release migration notes |

## 14. ADR 候选

| ADR | 决策 | 推荐 |
|---|---|---|
| ADR-CR051-01 | 仓库拓扑 | 单一主代码仓库 + 外部 research archive / data lake / broker archive |
| ADR-CR051-02 | PC 使用边界 | 研究 PC 为开发和研究环境；交易 PC 为 package 消费和运行证据环境 |
| ADR-CR051-03 | 策略类型扩展 | 先生命周期框架，再多因子 proof cycle，再逐类扩展 |
| ADR-CR051-04 | 归档边界 | Git 存 schema / docs / small redacted fixture；大 artifact 和敏感事实外置 |
| ADR-CR051-05 | 准入声明 | `delivery_candidate` 不等于 `runtime_candidate`，更不等于 `trade-ready` |
| ADR-CR051-06 | 项目迁移 | 当前仓库整体迁移采用先 Git 归档、再设计冻结、再清单化机械迁移、再验证的阶段化方案 |
| ADR-CR051-07 | 项目命名 | 正式名称采用 `quant-lab`；`local_backtest` 作为 legacy alias 和历史审计名保留；不批量重写历史过程证据 |

## 15. 自审

| 检查项 | 结果 | 说明 |
|---|---|---|
| 是否覆盖用户要求的归档方式 | PASS | §5 覆盖 Git、research archive、market data lake、broker archive、strategy exchange |
| 是否覆盖信息、idea、项目、研究过程、报告、交付件 | PASS | §5.2、§7、§9 |
| 是否覆盖研究 PC / 交易 PC 使用仓库方式 | PASS | §6 |
| 是否覆盖仓库一个还是多个 | PASS | §3 GA-01 |
| 是否覆盖后续 CR 上下文 | PASS | §10 |
| 是否保持不授权边界 | PASS | §2、§11、§13 |
| 是否覆盖项目整体迁移和 Git 归档 | PASS | §5.4、§5.5、§5.6、§5.7 |
| 是否覆盖项目命名和旧名兼容 | PASS | §2 项目命名决策、§5、§6、§14 |
| 是否需要拆分 HLD | NOT_NOW | 当前核心产物是一个生命周期框架；后续实现可拆 CR052+，本 HLD 不拆 |

## 16. CP3 确认记录

| 项 | 内容 |
|---|---|
| CP3 checklist | `process/checkpoints/CP3-CR051-HLD-REVIEW.md` |
| 自动预检 | `process/checks/CP3-CR051-HLD-CONSISTENCY.md`，PASS |
| 人工结论 | approved |
| 审查人 | user |
| 审查时间 | 2026-06-14T08:03:59+08:00 |
| 接受决策 | DQ-CP3-CR051-01..06 |
| 下一阶段 | story-planning / CP4 |

CP3 approved 只确认架构和迁移设计方向，不授权目录重命名、NAS mount / scan / copy / delete / migration execution、provider/lake/publish、QMT/MiniQMT runtime、账户查询、交易、凭据读取、Git push、远端仓库改名或历史过程文件批量替换。
