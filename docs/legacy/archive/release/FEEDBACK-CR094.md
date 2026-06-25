---
status: ready
cr_id: CR-094
---

# CR094 Feedback

## 观察信号

| Signal ID | 信号 | 阈值 | 处理 |
|---|---|---|---|
| FB-CR094-01 | `meta-flow check cr-tracking --strict-warnings` 再次非零 | 任意非零退出 | 创建 issue 或后续 CR，优先判断是否为 current state conflict |
| FB-CR094-02 | standalone checker 输出形态差异影响使用 | 用户要求两套输出一致 | 启动 CR093-FU-02 |

## 后续候选

| Candidate ID | 类型 | 内容 | 当前状态 |
|---|---|---|---|
| CR-095 | follow-up | standalone checker 与主 CLI 输出收敛 | active-formal-cr；由 `CR093-FU-02` 转入 |

本文件只记录反馈入口；`CR093-FU-02` 已由用户明确选择并转为正式 `CR-095`。
