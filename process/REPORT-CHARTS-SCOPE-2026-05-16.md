---
owner: "meta-po"
status: "ready-for-main-thread-implementation"
created_at: "2026-05-16T18:40:44+08:00"
change_id: "CR-002"
phase: "story-execution"
implementation_owner: "main-thread"
subagent_dispatch: "not-used"
---

# 回测报告图表能力实施范围

## 当前流程判断

- 当前 `process/STATE.md` 原状态为 `delivered`，CP8 已通过。
- 本次是交付后新增能力，按变更管理处理为 `CR-002`。
- 最小回退阶段为 `story-execution`，因为现有 HLD/Story 已覆盖“图表可由 CSV 派生”的架构前提，不需要重开 solution-design。
- 当前工具面没有可用的真实 `spawn_agent` / `resume_agent` / `send_input`，因此本轮不登记下游 agent 已完成；主线程可根据本文件直接实现。

## 实施边界

应修改或新增：

| 路径 | 建议动作 | 原因 |
|---|---|---|
| `engine/charts.py` | 新增 | 集中图表生成逻辑，避免扩大 `reporting.py` 的 CSV/Markdown 安全输出职责 |
| `tests/test_report_charts.py` 或 `tests/test_story_004_013.py` | 新增 / 修改 | 覆盖图表文件保存、缺列失败和离线副作用 |
| `README.md` | 实施后修改 | 增加图表生成最小示例和输出路径 |
| `docs/USER-MANUAL.md` | 实施后修改 | 增加使用说明、字段要求和故障排除 |

谨慎修改：

| 路径 | 原则 |
|---|---|
| `engine/reporting.py` | 仅在需要复用公共路径/字段工具时做小改；不要塞入绘图职责 |
| `engine/scanner.py` | 不改变扫描计算与失败行策略；最多增加便捷调用钩子 |
| `engine/backtest.py` | 不改变回测计算口径；最多暴露已有 nav/equity 数据 |
| `engine/contracts.py` | 只有需要稳定图表输出文件名常量时才改 |

不得修改：

| 路径 / 行为 | 原因 |
|---|---|
| 数据准备、AKShare adapter、manifest 写入 | 本 CR 不涉及联网数据链路 |
| 策略信号、组合成交、指标公式 | 图表必须由既有结果派生 |
| `process/**` | 流程文件由 meta-po 维护，避免主线程冲突 |
| `delivery/**` | 当前生产项目不使用该交付出口 |

## 图表清单

最小必需图表：

| 图表 | 输入 | 输出建议 | 说明 |
|---|---|---|---|
| 净值曲线 | `trade_date`/`date` + `nav`/`equity`/`final_nav` | `reports/charts/equity_curve.png` | 单次回测查看主图 |
| 回撤曲线 | 同净值曲线 | `reports/charts/drawdown.png` | 从净值序列计算 drawdown |
| Sharpe 热力图 | `lookback_days`, `rebalance_freq`, `top_fraction`, `sharpe`, `status` | `reports/charts/sweep_sharpe_heatmap.png` | 参数扫描查看主图 |
| 收益热力图 | `lookback_days`, `rebalance_freq`, `top_fraction`, `annual_return` 或 `total_return`, `status` | `reports/charts/sweep_return_heatmap.png` | 与 Sharpe 对照 |

可选但不阻塞：

| 图表 | 输入 | 说明 |
|---|---|---|
| 最大回撤热力图 | 扫描 CSV | 便于风险对比 |
| 换手率热力图 | 扫描 CSV | 便于成本敏感性分析 |
| Top 参数柱状图 | 扫描 CSV | 展示前 N 组候选 |

## 验收口径

主线程完成后建议用以下事实回填：

1. 新增图表 API 的路径与函数名。
2. 输出文件清单，至少包含 4 个 PNG。
3. 测试命令与结果，优先 `uv run --python 3.11 pytest -q`。
4. 是否更新 README / USER-MANUAL。
5. 是否保持回测与扫描核心结果不变。

## 风险与约束

- 图表生成应使用 matplotlib 非交互后端，适配无 GUI 环境。
- 图表函数应显式校验列名，缺列时给出中文可读错误。
- 参数扫描图表只统计 `status=success` 或空状态代表成功的行；失败行不得影响热力图数值，但失败数量可作为标题或日志信息。
- 图表文件属于运行产物，默认不要求提交。
