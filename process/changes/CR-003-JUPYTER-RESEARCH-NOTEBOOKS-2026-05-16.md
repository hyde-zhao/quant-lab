---
cr_id: "CR-003"
status: "closed"
impact_level: "medium"
rollback_to: "story-execution"
approval_result: "accepted-completed"
created_at: "2026-05-16T19:19:17+08:00"
created_by: "meta-po"
approved_by: "user"
approved_at: "2026-05-16T19:19:17+08:00"
source: "user"
linked_issue: ""
completion_result: "completed"
closed_at: "2026-05-16T19:33:15+08:00"
---

# CR-003：本地 Jupyter 探索型研究入口

## 变更描述

用户希望在 `local_backtest` 中采用“本地 Jupyter 研究：`%matplotlib inline + mplfinance`，图表嵌入 `.ipynb`，探索阶段不存图”的方案。本变更目标是为本地探索型研究提供 Notebook 支持、模板、文档和必要依赖，同时不能破坏 CR-002 已完成的正式报告图表 PNG 脚本化保存能力。

本 CR 只定义探索入口与最小实施边界：Notebook 用于交互式研究和人工观察，不作为正式可复现报告替代物；正式报告图表仍由 `engine.charts.generate_report_charts` 输出 `reports/charts/*.png` 与 `reports/charts/index.md`。

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `process/USE-CASES.md` | 原文档更新 | 既有 UC-03/UC-04 “热力图和 Notebook 为可选展示”作为旧基线保留；本 CR 增量映射为“本地探索 Notebook 入口” | `## 修订记录` | approved-for-later-doc-sync |
| `process/REQUIREMENTS.md` | 原文档更新 | 既有 REQ-033 / A-005 “CSV 必需、Notebook 和热力图可选展示”保留；本 CR 不把 Notebook 升级为正式报告必需物，只补足探索入口 | `## 修订记录` | approved-for-later-doc-sync |
| `process/HLD.md` | 不变 | HLD 的正式报告与离线边界不变；Notebook 属展示层可选增强 | 不适用 | approved |
| `process/STORY-BACKLOG.md` | 不变 | 关联 STORY-006 / STORY-007 的报告与扫描输出，不新增完整 Story 拆解 | 不适用 | approved |
| `pyproject.toml` / `uv.lock` | 原文档更新 | 保留现有 pandas / matplotlib / pytest 依赖；按 uv 规范增加 Notebook 探索所需依赖或 dev 依赖 | 不适用 | pending-after-implementation |
| `README.md` | 原文档更新 | 保留 CR-002 的脚本化 PNG 报告说明，追加 Jupyter 探索入口与“不存图”边界 | 项目文档修订记录或相关章节 | pending-after-implementation |
| `docs/USER-MANUAL.md` | 原文档更新 | 保留现有标准报告图表章节，追加 Notebook 探索流程、OHLCV 限制和故障排除 | 项目文档修订记录或相关章节 | pending-after-implementation |
| `notebooks/` | 新增 | 不适用 | Notebook 或 bootstrap 文档内部说明 | pending-after-implementation |

## 旧基线映射

| 原基线对象 | 新增 / 修改对象 | 保留策略 | 映射说明 |
|---|---|---|---|
| REQ-033 / A-005：CSV 是第一版报告必需输出，Notebook 和热力图为可选展示 | CR-003-REQ-001：提供本地探索 Notebook 入口 | 原文保留 + CR 摘录保留 | 不改变正式验收主路径；Notebook 只服务探索和人工观察 |
| CR-002：正式报告图表 PNG 脚本化保存 | CR-003-REQ-002：Notebook 内联图表不默认保存图片 | 原文保留 | 两条路径并存：正式报告可复现保存，探索阶段内联展示 |
| `reports/equity_curve.csv` | Notebook 净值 / 回撤示例输入 | 原文保留 | Notebook 可读取现有示例 CSV 展示净值与回撤，不依赖私有行情 |
| OHLCV K 线研究 | Notebook K 线 cell 或说明 | CR 摘录保留 | `mplfinance` 仅在存在 `open/high/low/close/volume` 数据时使用；无 OHLCV 时不得伪造 K 线 |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论（true/false） | 处理动作 |
|------|----------|-----------|--------------------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | `process/REQUIREMENTS.md` / CR delta | true | 记录增量需求：Notebook 探索入口、inline 图表、不替代正式报告；后续由 meta-pm 或 meta-doc 同步修订记录 |
| 场景层 | 是否改变测试矩阵覆盖范围 | `process/USE-CASES.md` / 本地探索场景 | true | 增加“研究者在 Jupyter 中查看净值/回撤/可选 K 线”的探索场景；不改变正式报告验收矩阵 |
| 计划层 | 是否改变 Phase、Wave、任务依赖 | STORY-006、STORY-007、依赖管理、文档 | true | 回退到 `story-execution` 做局部增强；需要 meta-se 边界复核、meta-dev 实施、meta-qa 验证、meta-doc 文档同步 |
| 安全层 | 是否引入新的高风险动作或权限要求 | 本地 Notebook、依赖、数据读取 | false | 仅本地读取示例 CSV 或用户自备 OHLCV；不联网、不读取凭据、不写真实数据；Notebook 输出不作为入库报告 |
| 交付层 | 是否需要重新生成交付物或回归子集 | README、USER-MANUAL、Notebook 文件、pytest / uv sync | true | 更新文档入口；如新增依赖需 `uv sync` 更新锁文件；运行聚焦回归，确认 CR-002 图表保存路径未破坏 |

## 回退决策

- 影响范围：局部
- 回退到阶段：`story-execution`
- 需要重新确认的对象：
  - Notebook 定位：仅探索，不替代正式报告。
  - 依赖策略：优先使用 `uv` 管理；`mplfinance` 可作为项目依赖或 dev 依赖，由 meta-se/meta-dev 给出最小方案。
  - 输出路径：可新增 `notebooks/`，不得把 Notebook 输出或真实行情样本当作正式交付报告。
  - 回归边界：必须确认 `engine.charts.generate_report_charts("reports")` 和 `reports/charts/*.png` 能力仍保留。

## 最小可交付范围

必须包含：

1. 新增 `notebooks/` 下的探索入口：可以是 `.ipynb` 示例，也可以是 bootstrap Markdown 文档加最小 notebook；优先给出能在本地 Jupyter 中打开的示例。
2. Notebook 使用 `%matplotlib inline`，图表嵌入 `.ipynb`，探索阶段不默认保存图片。
3. Notebook 不依赖真实私有数据；可读取现有 `reports/equity_curve.csv` 展示净值和回撤。
4. 可提供 K 线 cell，但必须说明只有存在 OHLCV 数据时才使用 `mplfinance`，不得用净值曲线伪造 K 线。
5. 使用 `uv` 管理依赖；如新增 `mplfinance` / `jupyter` / `ipykernel`，必须通过 `uv add` 或等价 uv 流程维护 `pyproject.toml` 与 `uv.lock`。
6. README 和 `docs/USER-MANUAL.md` 增加 Jupyter 研究入口，并明确 CR-002 的正式 PNG 报告路径仍是可复现报告能力。

明确不包含：

1. 不把 Notebook 当正式可复现报告替代物。
2. 不删除、不降级、不改写 CR-002 的 `reports/charts/*.png` 和 Markdown 索引能力。
3. 不引入 Web Dashboard、远程 Notebook 服务、自动上传、真实私有行情样例或凭据。
4. 不把 Notebook 执行输出、`.ipynb_checkpoints/`、临时图像或真实数据纳入正式交付物。
5. 不扩大回测、扫描、指标、数据准备和候选筛选的计算口径。

## 验收口径

| 编号 | 验收项 | 通过标准 |
|---|---|---|
| CR-003-AC-001 | Notebook 探索入口 | `notebooks/` 存在可读入口；示例能说明 `%matplotlib inline` 与本地启动方式 |
| CR-003-AC-002 | 内联图表不存图 | Notebook 示例默认只 inline 展示，不调用 `savefig`，不向 `reports/charts/` 写入新文件 |
| CR-003-AC-003 | 示例数据安全 | 示例可用 `reports/equity_curve.csv` 或合成数据运行；不要求真实私有行情 |
| CR-003-AC-004 | mplfinance 边界 | K 线示例仅在 OHLCV 字段存在时启用，并明确缺 OHLCV 时跳过或提示 |
| CR-003-AC-005 | 依赖管理 | 依赖变更通过 `uv` 维护，`pyproject.toml` / `uv.lock` 一致 |
| CR-003-AC-006 | CR-002 回归 | `generate_report_charts("reports")` 仍能生成或识别既有 PNG 图表路径；相关 pytest 不回退 |
| CR-003-AC-007 | 文档入口 | README 与 `docs/USER-MANUAL.md` 同时说明 Notebook 探索路径和正式报告路径差异 |

## 子 Agent 调度状态

当前 meta-po 工具面未提供 `spawn_agent` / `resume_agent` / `send_input`，因此不能直接拉起下游子 agent，也不能伪造调度证据。已创建 handoff，等待主线程按 handoff 代发真实子 agent 并回填调度证据。

| Agent | Handoff | 当前状态 |
|---|---|---|
| meta-se / se-sun the 2nd | `process/handoffs/META-SE-CR003-JUPYTER-BOUNDARY-REVIEW-2026-05-16.md` | completed / spawn_agent / `019e3085-af15-7e23-9bec-4993ad42c54d` |
| meta-dev / dev-qian the 2nd | `process/handoffs/META-DEV-CR003-JUPYTER-IMPLEMENT-2026-05-16.md` | completed / spawn_agent / `019e3086-fb15-7142-b839-b72cade549e2` |
| meta-qa / qa-wu the 2nd | `process/handoffs/META-QA-CR003-JUPYTER-VERIFY-2026-05-16.md` | completed / spawn_agent / `019e308c-f0c2-73f1-9f30-fc5070042578` |
| meta-doc / doc-zheng the 2nd | `process/handoffs/META-DOC-CR003-JUPYTER-DOCS-2026-05-16.md` | completed / spawn_agent / `019e308b-5947-7611-bffc-15fc60d142b1` |

## 处理结论

- 审批结论：`accepted-completed`
- [ ] 自动批准（低风险）
- [x] 待人工确认（中风险，用户已在请求中授权最小实现边界）
- [ ] 待人工审批（高风险）

## 完成回填

| 项目 | 结果 |
|---|---|
| 关闭时间 | `2026-05-16T19:33:15+08:00` |
| 架构复核 | `meta-se / se-sun the 2nd` CONDITIONAL：可局部实施，不重开 HLD / Story Plan；建议 exploration 依赖组、Notebook 不存图、OHLCV 条件检查和 `.gitignore` |
| 实现 | `meta-dev / dev-qian the 2nd` 完成；新增 exploration 依赖组、Notebook 入口、`.gitignore`、README / USER-MANUAL 文档入口、CP6 与 DEV-LOG |
| 文档 | `meta-doc / doc-zheng the 2nd` 完成；README 与 USER-MANUAL 已明确 Jupyter 探索入口和正式 PNG 报告边界 |
| 验证 | `meta-qa / qa-wu the 2nd` PASS |
| 测试证据 | `uv sync --python 3.11 --group exploration` PASS；`uv lock --check` PASS；`uv run --python 3.11 pytest -q` 12 passed in 3.26s |
| Notebook 证据 | `nbformat validate` PASS；包含 `%matplotlib inline`；不含 `savefig` 和 `reports/charts` 写入 |
| CR-002 回归 | `generate_report_charts("reports")` 返回 `artifact_count=4`；`reports/charts/*.png` 和 `index.md` 非空 |
| 安全边界 | `.gitignore` 覆盖 checkpoint / outputs / tmp；`delivery/` 不存在；安全扫描无凭据或远程服务 |
| 非阻塞建议 | `CR003-QA-ADV-001`：Notebook cell 缺少 `id` 字段，`nbformat validate` 通过但有 `MissingIDFieldWarning`；不阻塞 |
| 检查点 | `process/checks/CP6-CR003-JUPYTER-NOTEBOOKS.md`、`process/checks/CP7-CR003-JUPYTER-NOTEBOOKS.md` |

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| Story | STORY-006 | 单次回测指标、报告与 metadata；Notebook 可读取 equity curve 展示净值 / 回撤 |
| Story | STORY-007 | 参数扫描报告；Notebook 后续可读取扫描 CSV 做探索图 |
| 需求 | REQ-033 / A-005 | 旧基线为 CSV 必需、Notebook 可选展示 |
| 变更 | CR-002 | 正式报告 PNG 生成能力；本 CR 不得破坏 |
| 候选输出 | `notebooks/` | 本地探索入口，不包含真实私有数据 |
| 候选依赖 | `mplfinance` | 仅 OHLCV 数据可用时用于 K 线展示 |
