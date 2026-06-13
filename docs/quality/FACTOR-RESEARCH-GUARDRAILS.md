# 因子研究护栏

- source_cr: `CR-037`
- run_id: `run-stage6-full-ch6-20260611`
- status: `active`
- runtime_authorization: `not-authorized`

## 核心规则

| guardrail_id | rule |
|---|---|
| `G-CR037-LEAKAGE-001` | feature available_at 必须早于 label_available_at；ML 研究必须使用 purge / embargo 时间切分。 |
| `G-CR037-OOS-001` | 进入组合实践前必须至少有样本外或观察期证据，不能只凭 2000-2019 样本内 t 值准入。 |
| `G-CR037-PHACKING-001` | 任何新增因子或异象必须报告全量候选、参数网格和未通过对象，禁止只汇报样本内显著结果。 |
| `G-CR037-RUNTIME-001` | CR-037 不授权 provider fetch、lake write、publish、QMT、simulation、live、账户、订单或凭据读取。 |

## 准入边界

- `baseline` 和 `candidate` 只能作为 CR-038 / CR-039 的研究输入，不自动授权组合优化、模拟盘或实盘。
- `watch`、`reject`、`needs-more-data` 必须保留风险说明；策略层默认不得直接消费。
- ML 研究必须先声明时间切分、purge / embargo、label overlap 防护和解释性边界。
- 任一新增 provider fetch、lake write、catalog publish、QMT、simulation、live、账户 / 订单或凭据读取都必须另起 CR。

## 证据入口

- report: `process/research/stage6_full_run_20260611/chapter6_factor_robustness/run-stage6-full-ch6-20260611/CHAPTER6-RUN-REPORT.md`
- admission: `process/research/stage6_full_run_20260611/chapter6_factor_robustness/run-stage6-full-ch6-20260611/ROBUSTNESS-ADMISSION-SUMMARY.json`
- leakage_audit: `reports/stage6_full_run_20260611/chapter6_factor_robustness/run-stage6-full-ch6-20260611/ml_leakage_audit.md`
