from __future__ import annotations

from pathlib import Path
from typing import Any

from qbank.bank import Bank
from qbank.reference import (
    TYPE_LABELS,
    _answer_for,
    _grouped_questions,
    _question_body,
    _question_heading,
    _slug,
)


def _value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    if isinstance(value, dict):
        return "; ".join(f"{key}={_value(item)}" for key, item in value.items())
    return str(value)


def _source_lines(question: dict[str, Any]) -> list[str]:
    source = question.get("source")
    if not isinstance(source, dict) or not source:
        return []
    return [
        "**Source / provenance:** "
        + " · ".join(f"**{key}:** {_value(value)}" for key, value in source.items()),
        "",
    ]


def _metadata_lines(question: dict[str, Any]) -> list[str]:
    metadata = question.get("metadata")
    if not isinstance(metadata, dict) or not metadata:
        return []
    return [
        "**Stored metadata:** "
        + " · ".join(f"**{key}:** {_value(value)}" for key, value in metadata.items()),
        "",
    ]


def _choice_rationale_lines(question: dict[str, Any]) -> list[str]:
    if question.get("type") not in {"mcq_one", "mcq_multi"}:
        return []
    rows: list[str] = []
    for index, choice in enumerate(question.get("choices", []) or []):
        rationale = str(choice.get("rationale") or "").strip()
        if rationale:
            letter = chr(ord("A") + index)
            rows.append(f"- **{letter}:** {rationale}")
    if not rows:
        return []
    return ["**Choice rationales:**", "", *rows, ""]


def _summary_line(question: dict[str, Any]) -> str:
    pieces = [
        f"**Type:** {TYPE_LABELS.get(str(question.get('type')), str(question.get('type', '')))}",
        f"**Difficulty:** {str(question.get('difficulty', 'unrated')).title()}",
        f"**Points:** {question.get('points', 0)}",
        f"**Version:** {question.get('version', '?')}",
    ]
    categories = question.get("category_ids") or []
    if categories:
        pieces.append("**Categories:** " + ", ".join(f"`{category}`" for category in categories))
    tags = question.get("tags") or []
    if tags:
        pieces.append("**Tags:** " + ", ".join(f"`{tag}`" for tag in tags))
    return " · ".join(pieces)


def render_triage(bank: Bank) -> str:
    lines = [
        f"# {bank.info['title']} — Instructor Triage",
        "",
        "> Review worksheet generated from the JSON bank. The bank remains the source of truth. "
        "Check exactly one decision for each question and add notes only when useful.",
        "",
        f"**Source bank:** `{bank.path.name}`  ",
        f"**Questions:** {len(bank.questions)}",
        "",
        "Decision meanings:",
        "",
        "- **Keep**: acceptable for promotion with no grading-relevant content change.",
        "- **Cut**: do not promote this question.",
        "- **Needs work**: concept is useful, but wording, key, distractors, scope, or provenance needs revision.",
        "",
    ]

    for group_title, questions in _grouped_questions(bank):
        lines.extend([f"## {group_title}", ""])
        for question in questions:
            qid = question["id"]
            lines.extend(
                [
                    f'<a id="triage-{_slug(qid)}"></a>',
                    f"### {_question_heading(question)}",
                    "",
                    "- [ ] **Keep**",
                    "- [ ] **Cut**",
                    "- [ ] **Needs work**",
                    "",
                    "**Reviewer notes:**",
                    "",
                    "> ",
                    "",
                    f"> {_summary_line(question)}",
                    "",
                    "#### Question",
                    "",
                ]
            )
            lines.extend(_question_body(question))
            lines.extend(
                [
                    "#### Key / grading information",
                    "",
                    f"**Answer:** {_answer_for(question)}",
                    "",
                ]
            )

            solution = str(question.get("solution") or "").strip()
            if solution:
                lines.extend([f"**Solution / explanation:** {solution}", ""])

            feedback = question.get("feedback") or {}
            if isinstance(feedback, dict):
                correct_feedback = str(feedback.get("correct") or "").strip()
                incorrect_feedback = str(feedback.get("incorrect") or "").strip()
                if correct_feedback:
                    lines.extend([f"**Correct feedback:** {correct_feedback}", ""])
                if incorrect_feedback:
                    lines.extend([f"**Incorrect feedback:** {incorrect_feedback}", ""])

            sample_answer = str(question.get("sample_answer") or "").strip()
            if sample_answer:
                lines.extend([f"**Sample answer:** {sample_answer}", ""])

            rubric = str(question.get("rubric") or "").strip()
            if rubric:
                lines.extend([f"**Rubric:** {rubric}", ""])

            lines.extend(_choice_rationale_lines(question))
            lines.extend(_source_lines(question))
            lines.extend(_metadata_lines(question))
            lines.extend(["---", ""])

    return "\n".join(lines).rstrip() + "\n"


def build_triage(bank: Bank, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = _slug(bank.info["id"])
    path = output_dir / f"{stem}-triage.md"
    path.write_text(render_triage(bank), encoding="utf-8")
    return path
