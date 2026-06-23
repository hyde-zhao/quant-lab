from __future__ import annotations

from scripts.check_human_gate_decision_brief import validate_checkpoint


def _checkpoint_body(*, design_ref: str) -> str:
    return f"""
# CP5 CR118 人工审查

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---:|---|
| `process/checks/CP5-CR118.md` | PASS | 0 | ok |

## Decision Brief

### Context Capsule Summary

| 字段 | 内容 |
|---|---|
| capsule 路径 | `process/context/CP5-CR118-CONTEXT.yaml` |

### 待人工决策清单

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣分析 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|---|
| DQ-CP5-CR118-01 | implementation | 是否实现 | 推荐 | A. 暂停 | 推荐可检查 | 低 | 回退 |

| 字段 | 内容 |
|---|---|
| 用户需决策事项 | 是否批准 |
| 不授权项 | runtime、NAS、凭据、交易写或 publish |
| 自动终验授权 | `auto_final_authorization: false` |

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| 设计证据 | 待审查 | {design_ref} | ok |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 路径检查 | 待审查 | {design_ref} | ok |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| 用户确认 | 待审查 | 本文件人工审查结果 | 等待 |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| notes | {design_ref} | 待审查 | ok |

## 人工审查结果

- 结论：`approved | changes_requested | rejected`
"""


def test_checkpoint_accepts_process_design_entry_for_legacy_alias() -> None:
    errors: list[str] = []
    decision_count = validate_checkpoint(
        _checkpoint_body(
            design_ref=(
                "`process/docs/design/PATH-ALIAS-CHECKER-ENFORCEMENT-CANDIDATE-CR118.md` "
                "(`docs/design/PATH-ALIAS-CHECKER-ENFORCEMENT-CANDIDATE-CR118.md`)"
            )
        ),
        errors,
    )

    assert decision_count == 1
    assert errors == []


def test_checkpoint_rejects_design_alias_without_process_entry() -> None:
    errors: list[str] = []
    validate_checkpoint(
        _checkpoint_body(
            design_ref="`docs/design/PATH-ALIAS-CHECKER-ENFORCEMENT-CANDIDATE-CR118.md`"
        ),
        errors,
    )

    assert any("process/docs/design" in error for error in errors)
