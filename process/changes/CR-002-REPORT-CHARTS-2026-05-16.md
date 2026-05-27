---
cr_id: "CR-002"
status: "closed"
impact_level: "medium"
rollback_to: "story-execution"
approval_result: "accepted-completed"
created_at: "2026-05-16T18:40:44+08:00"
created_by: "meta-po"
approved_by: "user"
approved_at: "2026-05-16T18:40:44+08:00"
source: "user"
linked_issue: ""
closed_at: "2026-05-16T18:50:58+08:00"
completion_result: "completed"
---

# CR-002：回测报告图表生成与保存能力

## 变更描述

用户要求在 `<workspace>/local_backtest` 的本地回测/参数扫描报告中查看各种图表，并明确要求拉起 `meta-po` 组织分析并实现。当前主线程会并行查看代码并做实现准备，本 CR 只固化流程组织、边界和验收口径，不修改业务代码。

最小可交付目标：为现有本地回测与参数扫描报告增加可复现、离线、可测试的图表生成与保存能力，使用户能够从已有 CSV/结果对象派生 PNG 图表文件。

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `process/USE-CASES.md` | 原文档更新 | 既有 UC-03/UC-04 作为旧基线保留；本 CR 作为“报告可视化查看”增量场景映射 | `## 修订记录` | approved-for-later-doc-sync |
| `process/REQUIREMENTS.md` | 原文档更新 | 既有 REQ-033 “图形化展示为可选增强”保留为历史基线；本 CR 将最小图表输出提升为当前变更的实现范围 | `## 修订记录` | approved-for-later-doc-sync |
| `process/HLD.md` | 不变 | HLD 已声明 CSV 为必需、图表可由 CSV 派生；本 CR 不要求重做架构 | 不适用 | approved |
| `process/STORY-BACKLOG.md` | 不变 | 关联 STORY-006 与 STORY-007 的报告层扩展，不新增完整 Story 拆解 | 不适用 | approved |
| `README.md` | 原文档更新 | 保留现有报告说明，实施完成后追加图表输出路径与使用方式 | 项目文档修订记录或相关章节 | pending-after-implementation |
| `docs/USER-MANUAL.md` | 原文档更新 | 保留现有 CSV 报告流程，实施完成后追加图表生成示例与故障排除 | 项目文档修订记录或相关章节 | pending-after-implementation |

### 文档处理完成回填

| 文档 | 完成状态 | 证据 |
|---|---|---|
| `README.md` | completed | 已说明 `generate_report_charts("reports")`、`reports/charts/*.png` 与 `reports/charts/index.md` |
| `docs/USER-MANUAL.md` | completed | 已说明图表入口、输出路径、无扫描 CSV 时只生成单次回测图表 |
| `reports/backtest_report.md` | completed | 已改为引用 `reports/charts/index.md`，并嵌入 PNG 图表 |

## 旧基线映射

| 原基线对象 | 新增 / 修改对象 | 保留策略 | 映射说明 |
|---|---|---|---|
| REQ-033：CSV 必需，图表可选增强 | CR-002-REQ-001：最小图表输出成为本变更验收范围 | 原文保留 + CR 摘录保留 | 不否定第一版验收；只对本次交付增量提出图表能力要求 |
| STORY-006：指标、单次回测报告与 metadata | CR-002-SCOPE-001：单次回测图表 | 原文保留 | 从 `reports/equity_curve.csv` / 单次结果对象派生净值、回撤等图表 |
| STORY-007：60 组参数扫描报告 | CR-002-SCOPE-002：参数扫描图表 | 原文保留 | 从 `reports/momentum_param_sweep_local.csv` 或扫描 rows 派生热力图/排名图 |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论（true/false） | 处理动作 |
|------|----------|-----------|--------------------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | `process/REQUIREMENTS.md` / CR delta | true | 不直接改需求正文；本 CR 记录增量需求，实施后再同步正式需求修订记录 |
| 场景层 | 是否改变测试矩阵覆盖范围 | `process/USE-CASES.md` / 报告查看场景 | true | 增加“用户查看本地回测/扫描图表”的验收口径，暂以本 CR 追溯 |
| 计划层 | 是否改变 Phase、Wave、任务依赖 | STORY-006、STORY-007、测试回归 | true | 回退到 `story-execution` 做局部增强；不重开 HLD/Story Plan |
| 安全层 | 是否引入新的高风险动作或权限要求 | 文件写入、CSV 解析、matplotlib 后端 | false | 仅写入 `reports/charts/**`，不联网、不执行外部命令、不读取凭据；使用非交互后端 |
| 交付层 | 是否需要重新生成交付物或回归子集 | README、USER-MANUAL、pytest 回归 | true | 实施后更新使用文档，并运行聚焦测试与必要全量回归 |

## 回退决策

- 影响范围：局部
- 回退到阶段：`story-execution`
- 需要重新确认的对象：
  - 图表输出范围与格式：本 CR 已由用户要求授权为最小实现范围。
  - 代码实现：由主线程在业务代码中执行，需避免与 meta-po 流程文件冲突。
  - 文档更新：实施验证后再同步 README / USER-MANUAL。

## 最小可交付范围

必须包含：

1. 由现有本地报告数据派生图表，不改变回测与扫描计算口径。
2. 保存图表到 `reports/charts/`，默认 PNG，父目录不存在时创建。
3. 单次回测至少覆盖：
   - 净值曲线图：基于 `reports/equity_curve.csv` 或等价 nav series。
   - 回撤曲线图：由净值序列派生 drawdown，不新增策略逻辑。
4. 参数扫描至少覆盖：
   - Sharpe 参数热力图或二维矩阵图。
   - 年化收益或累计收益参数热力图。
5. 图表生成主路径离线运行，网络调用次数为 0。
6. 图表函数可被测试用例用临时目录和合成数据验证。

明确不包含：

1. 不建设 Web Dashboard、Notebook 模板或交互式前端。
2. 不改动数据准备、AKShare adapter、策略信号、组合成交或核心指标公式。
3. 不引入真实生产数据、外部凭据、联网下载或平台自动上传。
4. 不把图表文件作为必须入库产物；生成物仍属于运行输出。

## 验收口径

| 编号 | 验收项 | 通过标准 |
|---|---|---|
| CR-002-AC-001 | 单次回测图表保存 | 给定包含日期与净值的合成 equity curve，运行图表生成函数后输出至少 `equity_curve.png` 与 `drawdown.png`，文件存在且 size > 0 |
| CR-002-AC-002 | 参数扫描图表保存 | 给定包含 60 组或小规模合成扫描 rows 的 DataFrame/CSV，输出至少 Sharpe 与收益类参数图，文件存在且 size > 0 |
| CR-002-AC-003 | 离线与副作用 | 图表生成不触发网络、不修改输入 CSV、不删除既有报告文件，只写 `reports/charts/**` |
| CR-002-AC-004 | 失败路径 | 输入文件缺失、必要列缺失或无成功扫描行时返回可读异常；不得输出 Python traceback 给用户入口 |
| CR-002-AC-005 | 依赖与后端 | 复用现有 `matplotlib>=3.8,<4.0`，使用非交互后端，适配无 GUI 环境 |
| CR-002-AC-006 | 回归 | 新增或更新测试通过；建议命令为 `uv run --python 3.11 pytest -q` |

## 主线程实现建议

建议主线程优先选择最小路径：

1. 新增 `engine/charts.py`，把图表生成逻辑与 `engine/reporting.py` 的 CSV 安全输出分开，避免扩大既有报告模块职责。
2. 对外暴露纯函数：
   - `render_equity_curve_chart(equity_curve, output_path) -> str`
   - `render_drawdown_chart(equity_curve, output_path) -> str`
   - `render_sweep_heatmaps(sweep_rows, output_dir) -> list[str]`
   - `render_report_charts(..., output_dir="reports/charts") -> list[str]`
3. 输入兼容 `pandas.DataFrame`、list[dict] 或 CSV path；内部统一转 DataFrame 后校验字段。
4. 参数扫描热力图优先固定两个维度为 `lookback_days` 与 `rebalance_freq`，按 `top_fraction` 分组或默认选取每个组合中 Sharpe 最优的一行，避免一次实现过多图形。
5. 测试放在现有 `tests/test_story_004_013.py` 或新建 `tests/test_report_charts.py`；使用 `tmp_path`，只断言文件存在、非空、输入不被改写和缺列错误。
6. 实施期间避免修改 `process/**`，防止与本 meta-po 流程文件发生冲突。

## 处理结论

- 审批结论：`accepted-completed`
- [ ] 自动批准（低风险）
- [x] 待人工确认（中风险，用户已在请求中授权最小实现）
- [ ] 待人工审批（高风险）

## 完成回填

| 项目 | 结果 |
|---|---|
| 关闭时间 | `2026-05-16T18:50:58+08:00` |
| 架构复核 | `meta-se / se-sun` 主体架构可接受；`CR002-SE-01..05` 已由后续整改覆盖 |
| 实现 | `meta-dev / dev-li` 已补齐 `engine/charts.py` 与测试 |
| 验证 | `meta-qa / qa-zhou` PASS |
| 测试证据 | `pytest` 12 passed；主线程复跑 `12 passed in 2.46s` |
| 图表证据 | `reports/charts/index.md` 657 bytes；4 个 PNG 均非空 |
| 检查点 | `process/checks/CP6-CR002-REPORT-CHARTS.md`、`process/checks/CP7-CR002-REPORT-CHARTS.md` |

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| Story | STORY-006 | 单次回测指标、报告与 metadata；本 CR 增加图表派生能力 |
| Story | STORY-007 | 参数扫描报告；本 CR 增加扫描图表派生能力 |
| 需求 | REQ-033 | 旧基线为图表可选；本 CR 将图表作为当前增量验收 |
| 代码建议 | `engine/charts.py` | 建议新增模块，由主线程实施 |
| 输出建议 | `reports/charts/**.png` | 运行产物，不默认入库 |
