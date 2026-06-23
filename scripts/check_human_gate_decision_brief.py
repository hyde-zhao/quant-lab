#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_CHECKPOINT_SECTIONS = [
    "## 自动预检摘要",
    "## Decision Brief",
    "待人工决策清单",
    "## Entry Criteria",
    "## Checklist",
    "## Exit Criteria",
    "## Deliverables",
    "## 人工审查结果",
]

REQUIRED_LAUNCH_SNIPPETS = [
    "请审查：",
    "自动预检结论：",
    "本轮待人工决策项：",
    "如果你回复 approve",
    "待人工决策清单：",
    "不授权项：",
]

REQUIRED_LAUNCH_SNIPPET_GROUPS = [
    ("上下文胶囊 / Context Capsule Summary", ["上下文胶囊：", "Context Capsule Summary"]),
    ("决策收集覆盖 / Decision Collection Coverage", ["决策收集覆盖：", "Decision Collection Coverage"]),
]

EXACT_REPLY_LINES = ["approve", "修改: <具体修改点>", "reject"]
LEGACY_DESIGN_PATH_RE = re.compile(r"(?<!process/)docs/design/[A-Za-z0-9._/\-]+")


def _normalize_markdown_path(raw_path: str) -> str:
    return raw_path.strip().strip("`'\".,;:，。；：）)]}").rstrip("/")


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    return path.read_text(encoding="utf-8")


def count_decisions(text: str) -> int:
    dq_ids = set(re.findall(r"\bDQ-CP[2358]-[A-Z0-9-]+-\d+\b", text))
    if dq_ids:
        return len(dq_ids)
    ids = set(re.findall(r"\bD-CP[2358]-[A-Z0-9-]+-\d+\b", text))
    return len(ids)


def validate_path_alias_references(text: str, errors: list[str]) -> None:
    legacy_paths = {
        _normalize_markdown_path(match.group(0))
        for match in LEGACY_DESIGN_PATH_RE.finditer(text)
    }
    if not legacy_paths:
        return

    process_paths = {
        _normalize_markdown_path(path)
        for path in re.findall(r"process/docs/design/[A-Za-z0-9._/\-]+", text)
    }
    missing_aliases = sorted(
        path for path in legacy_paths if f"process/{path}" not in process_paths
    )
    if missing_aliases:
        errors.append(
            "checkpoint 存在仅以 docs/design/* 作为设计证据入口的路径，"
            "需同时提供对应 process/docs/design/* 入口: "
            + ", ".join(missing_aliases)
        )


def validate_checkpoint(text: str, errors: list[str]) -> int:
    for section in REQUIRED_CHECKPOINT_SECTIONS:
        if section not in text:
            errors.append(f"checkpoint 缺少必要章节或字段: {section}")

    if "| 决策 ID |" not in text and "| ID | 决策" not in text:
        errors.append("checkpoint 缺少待人工决策表头")

    if "推荐方案" not in text:
        errors.append("checkpoint 决策表缺少推荐方案")

    if "备选方案" not in text:
        errors.append("checkpoint 决策表缺少备选方案")

    if "回退" not in text:
        errors.append("checkpoint Decision Brief 缺少回退 / 切换条件说明")

    if "不授权" not in text and "not-authorized" not in text:
        errors.append("checkpoint 缺少不授权范围说明")

    if "auto_final_authorization: false" not in text and "自动终验授权" not in text:
        errors.append("checkpoint 缺少自动终验不授权说明")

    validate_path_alias_references(text, errors)

    return count_decisions(text)


def validate_launch_message(
    text: str,
    checkpoint_path: Path,
    expected_decision_count: int | None,
    errors: list[str],
) -> None:
    for snippet in REQUIRED_LAUNCH_SNIPPETS:
        if snippet not in text:
            errors.append(f"launch message 缺少必要内容: {snippet}")

    for label, alternatives in REQUIRED_LAUNCH_SNIPPET_GROUPS:
        if not any(snippet in text for snippet in alternatives):
            errors.append(f"launch message 缺少必要内容: {label}")

    if str(checkpoint_path) not in text:
        errors.append(f"launch message 未包含 checklist 路径: {checkpoint_path}")

    decision_count_match = re.search(r"本轮待人工决策项：\s*(\d+)", text)
    if not decision_count_match:
        errors.append("launch message 未写明待人工决策项数量")
    else:
        message_decision_count = int(decision_count_match.group(1))
        if expected_decision_count is not None and message_decision_count != expected_decision_count:
            errors.append(
                "launch message 待决策项数量与 checkpoint 不一致: "
                f"message={message_decision_count}, checkpoint={expected_decision_count}"
            )
        if message_decision_count > 0 and "| 决策 ID |" not in text:
            errors.append("launch message 待决策项大于 0 但未打印决策表")

    lines = {line.strip() for line in text.splitlines()}
    for reply in EXACT_REPLY_LINES:
        if reply not in lines:
            errors.append(f"launch message 缺少 exact 回复行: {reply}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="检查 CP2/CP3/CP5/CP8 人工门禁 Decision Brief。")
    parser.add_argument(
        "--checkpoint-file",
        required=True,
        type=Path,
        help="待校验的 checkpoints/CP*.md 文件。",
    )
    parser.add_argument(
        "--launch-message-file",
        type=Path,
        help="可选：待发送给用户的人工门禁消息草稿。",
    )
    args = parser.parse_args(argv)

    errors: list[str] = []

    try:
        checkpoint_text = read_text(args.checkpoint_file)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    decision_count = validate_checkpoint(checkpoint_text, errors)

    if args.launch_message_file is not None:
        try:
            launch_text = read_text(args.launch_message_file)
        except FileNotFoundError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        validate_launch_message(launch_text, args.checkpoint_file, decision_count, errors)

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    print(f"PASS: human gate decision brief valid; decision_count={decision_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
