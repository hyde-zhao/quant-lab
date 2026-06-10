---
cr_id: CR-037
title: 第6章因子稳健性、失效风险与研究规范
status: draft-not-active
created_at: 2026-06-10
created_by: codex
owner: meta-po
source: user
change_type: add
impact_level: high
workflow_mode_after_change: standard
activation_policy: "draft only; activate after CR-035/CR-036 provide candidate factors/anomalies or user narrows scope"
parent_cr: CR-034
source_decision_id: USER-20260610-BOOK-RESEARCH-PLAN
related_changes:
  - CR-030
  - CR-034
  - CR-035
  - CR-036
---

# CR-037 第6章因子稳健性、失效风险与研究规范

## 背景与上下文

第6章讨论 p-hacking、因子动物园、因子大战、行为金融解释、投资者情绪、风险补偿 / 错误定价 / 数据窥探、样本外失效风险、机器学习与因子投资。它不是单个因子复刻 CR，而是给第3章因子、第5章异象和第7章策略实践建立研究质量护栏。

CR-030 已建立多因子研究合同，CR-034 已关闭第三章七因子数据和复刻，CR-035/CR-036 将分别输出模型和异象候选。CR-037 的职责是防止后续策略研究只依赖样本内显著性，补齐样本外、滚动、分市场状态、参数敏感性和数据窥探风险证据。

## 目标

1. 建立项目内因子研究 guardrails，覆盖 p-hacking、多重检验、样本外和失效风险。
2. 对第3章七因子和第5章异象候选执行 rolling IC、rolling long-short、decay、年度分解和市场状态分层。
3. 建立因子失效监控指标：RankIC 衰减、收益衰减、换手漂移、相关性漂移、容量 / 成本敏感性。
4. 为机器学习研究建立 leakage guard、purge / embargo、样本切分和可解释性边界。
5. 输出因子 / 异象准入分级：baseline、candidate、watch、reject、needs-more-data。

## Non-Goals

- 不训练复杂 ML 模型作为默认交付。
- 不把样本内显著性自动转为策略准入。
- 不做 QMT、simulation、live 或真实订单。
- 不触发 provider fetch、lake write、catalog publish。
- 不覆盖 CR-035/036 的原始报告，只生成稳健性补充证据。

## 影响范围

| 维度 | 影响 | 处理 |
|---|---|---|
| 需求层 | 新增因子稳健性、样本外失效和研究规范 | 写入 docs/quality 和 process/research |
| 场景层 | 增加滚动、年度、市场状态、参数敏感性和 ML leakage 场景 | 作为后续策略准入前置 |
| 计划层 | 依赖 CR-035/036 产物 | 可分批先覆盖第三章七因子 |
| 安全层 | 只读研究 artifact | 禁止 provider/lake/publish/交易 |
| 交付层 | 新增 guardrail 文档和 robustness reports | 小型 CSV/报告可提交，大型中间数据不默认提交 |

## 输出规划

| 输出 | 路径 | 说明 |
|---|---|---|
| 因子研究护栏 | `docs/quality/FACTOR-RESEARCH-GUARDRAILS.md` | 长期规范 |
| rolling IC | `reports/chapter6_factor_robustness/<run_id>/rolling_ic.csv` | 滚动稳定性 |
| 年度分解 | `reports/chapter6_factor_robustness/<run_id>/annual_factor_metrics.csv` | 年度收益 / IC / turnover |
| 市场状态结果 | `reports/chapter6_factor_robustness/<run_id>/market_state_results.csv` | 牛熊 / 波动 / 流动性 / 情绪 proxy 分层 |
| 衰减报告 | `reports/chapter6_factor_robustness/<run_id>/decay_report.csv` | 持有期 / 标签窗口敏感性 |
| ML leakage audit | `reports/chapter6_factor_robustness/<run_id>/ml_leakage_audit.md` | purge / embargo / label overlap 审计 |
| 人读报告 | `process/research/chapter6_factor_robustness/<run_id>/CHAPTER6-RUN-REPORT.md` | 第6章研究报告 |
| 准入摘要 | `process/research/chapter6_factor_robustness/<run_id>/ROBUSTNESS-ADMISSION-SUMMARY.json` | 给 CR-038/039 消费 |

## 分级规则草案

| 分级 | 条件 |
|---|---|
| baseline | 样本内、验证期、2020-2026 YTD 均方向稳定，rolling 指标不过度衰减，成本敏感性可接受 |
| candidate | 样本内有效，样本外部分有效，需要组合层约束 |
| watch | 显著性或方向不稳定，但有经济解释或特定市场状态有效 |
| reject | 多窗口方向反转或完全由数据窥探 / 不可交易假设驱动 |
| needs-more-data | 数据字段、样本长度或质量不足 |

## 验收标准

- [ ] 至少覆盖第三章七因子的 rolling / annual / sample-out 稳健性。
- [ ] 若 CR-036 已完成，覆盖第5章异象候选。
- [ ] 明确所有因子的准入分级和理由。
- [ ] 明确哪些指标只用于研究，不得直接用于 production。
- [ ] ML 相关内容必须通过 leakage audit，不得出现标签前视或 overlap。
- [ ] operation counts 中 provider fetch、lake write、publish、QMT、simulation、live 均为 0。
- [ ] 峰值内存低于 16GB。

## 激活条件

本 CR 当前为 `draft-not-active`。推荐在 CR-035 至少产出模型 baseline 后启动；如用户要求先做稳健性，可将范围收窄为“第三章七因子稳健性一期”。
