---
status: ready
cr_id: CR-093
---

# CR093 Feedback

## 观察信号

| Signal ID | 信号 | 阈值 | 处理 |
|---|---|---|---|
| FB-CR093-01 | `meta-flow check cr-tracking` 再次 exit 1 | 任意非零退出 | 创建 issue 或后续 CR，优先判断是否为真实 current conflict |
| FB-CR093-02 | warning-only 项需要清零 | 用户要求 strict-warnings 或 warning 影响后续门禁 | 启动 warning cleanup follow-up |
| FB-CR093-03 | standalone checker 与 meta-flow CLI 输出差异影响使用 | 用户要求两者输出一致 | 启动 checker convergence follow-up |

## 后续候选

| Candidate ID | 类型 | 内容 | 当前状态 |
|---|---|---|---|
| CR093-FU-01 | follow-up | broader `source=cp8-follow-up` warning cleanup | active: `process/changes/CR-094-WARNING-CLEANUP-STRICT-WARNINGS-READINESS-2026-06-19.md` |
| CR093-FU-02 | follow-up | standalone checker 与 meta-flow CLI 输出收敛 | candidate-not-started |

本文件只记录反馈入口，不表示后续候选已启动。
