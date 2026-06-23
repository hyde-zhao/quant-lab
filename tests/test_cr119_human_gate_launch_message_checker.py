from __future__ import annotations

from pathlib import Path

from scripts.check_human_gate_decision_brief import (
    validate_checkpoint,
    validate_launch_message,
)


def _checkpoint_text() -> str:
    return """
# CP5 CR119 人工审查

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---:|---|
| `process/checks/CP5-CR119.md` | PASS | 0 | ok |

## Decision Brief

### Context Capsule Summary

| 字段 | 内容 |
|---|---|
| capsule 路径 | `process/context/CP5-CR119-CONTEXT.yaml` |

### Decision Collection Coverage

| 来源 | 路径 / 对象 | 扫描状态 | 候选问题数 | 纳入待决策数 | 分类 / N/A 原因 |
|---|---|---:|---:|---:|---|
| CP5 auto precheck | `process/checks/CP5-CR119.md` | scanned | 2 | 2 | ok |

### 待人工决策清单

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣分析 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|---|
| DQ-CP5-CR119-01 | implementation | 是否实现 | 推荐 | A. 暂停 | 推荐可检查 | 低 | 回退 |
| DQ-CP5-CR119-02 | runtime_authorization | 是否禁止 runtime | 不授权 | A. 暂停 | 推荐权限最小 | 低 | 回退 |

| 字段 | 内容 |
|---|---|
| 用户需决策事项 | DQ-CP5-CR119-01、DQ-CP5-CR119-02 |
| 不授权项 | runtime、NAS、凭据、交易写或 publish |
| 自动终验授权 | `auto_final_authorization: false` |

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| CP5 | 待审查 | `process/checks/CP5-CR119.md` | ok |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | launch message | 待审查 | DQ-CP5-CR119-01 | ok |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| 用户确认 | 待审查 | 本文件人工审查结果 | 等待 |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| checker | `scripts/check_human_gate_decision_brief.py` | 待审查 | ok |

## 人工审查结果

- 结论：`approved | changes_requested | rejected`
"""


def _valid_launch_message(checkpoint_path: Path) -> str:
    return f"""
请审查：{checkpoint_path}
自动预检结论：PASS
上下文胶囊：process/context/CP5-CR119-CONTEXT.yaml（read_profile=minimal）
本轮待人工决策项：2
决策收集覆盖：已扫描 3 个来源，发现候选问题 2 个，纳入待决策 2 个。
如果你回复 approve，表示你接受以下 2 项推荐方案，不表示授权以下禁止操作。
待人工决策清单：
| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣摘要 | 影响 / 风险 |
|---|---|---|---|---|---|---|
| DQ-CP5-CR119-01 | implementation | 是否实现 | 推荐 | A. 暂停 | 推荐可检查 | 低 |
| DQ-CP5-CR119-02 | runtime_authorization | 是否禁止 runtime | 不授权 | A. 暂停 | 推荐权限最小 | 低 |

不授权项：
- runtime、NAS、凭据、交易写或 publish。

approve
修改: <具体修改点>
reject
"""


def test_launch_message_requires_context_capsule_summary() -> None:
    checkpoint_path = Path("process/checkpoints/CP5-CR119.md")
    errors: list[str] = []
    decision_count = validate_checkpoint(_checkpoint_text(), errors)
    assert decision_count == 2
    assert errors == []

    launch_message = _valid_launch_message(checkpoint_path).replace(
        "上下文胶囊：process/context/CP5-CR119-CONTEXT.yaml（read_profile=minimal）\n",
        "",
    )
    validate_launch_message(launch_message, checkpoint_path, decision_count, errors)

    assert any("Context Capsule Summary" in error for error in errors)


def test_launch_message_requires_decision_collection_coverage_summary() -> None:
    checkpoint_path = Path("process/checkpoints/CP5-CR119.md")
    errors: list[str] = []
    decision_count = validate_checkpoint(_checkpoint_text(), errors)
    assert decision_count == 2
    assert errors == []

    launch_message = _valid_launch_message(checkpoint_path).replace(
        "决策收集覆盖：已扫描 3 个来源，发现候选问题 2 个，纳入待决策 2 个。\n",
        "",
    )
    validate_launch_message(launch_message, checkpoint_path, decision_count, errors)

    assert any("Decision Collection Coverage" in error for error in errors)


def test_launch_message_accepts_chinese_context_and_coverage_summaries() -> None:
    checkpoint_path = Path("process/checkpoints/CP5-CR119.md")
    errors: list[str] = []
    decision_count = validate_checkpoint(_checkpoint_text(), errors)
    assert decision_count == 2
    assert errors == []

    validate_launch_message(
        _valid_launch_message(checkpoint_path),
        checkpoint_path,
        decision_count,
        errors,
    )

    assert errors == []
