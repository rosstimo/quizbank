from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from qbank.bank import Bank


TYPE_LABELS = {
    "mcq_one": "Multiple choice",
    "mcq_multi": "Multiple select",
    "true_false": "True/false",
    "numeric": "Numeric",
    "short_answer": "Short answer",
    "fill_blank": "Fill in the blank",
    "essay": "Essay / manual response",
    "code_review": "Code review",
    "matching": "Matching",
    "ordering": "Ordering",
}


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "item"


def _file_stem(bank_id: str) -> str:
    return _slug(bank_id)


def _choice_letter(index: int) -> str:
    return chr(ord("A") + index)


def _answer_for(question: dict[str, Any]) -> str:
    question_type = question.get("type")
    if question_type == "mcq_one":
        for index, choice in enumerate(question.get("choices", [])):
            if choice.get("correct") is True:
                return f"{_choice_letter(index)}. {choice.get('text', '')}"
        return "?"
    if question_type == "mcq_multi":
        answers = [
            f"{_choice_letter(index)}. {choice.get('text', '')}"
            for index, choice in enumerate(question.get("choices", []))
            if choice.get("correct") is True
        ]
        return "; ".join(answers) if answers else "?"
    if question_type == "true_false":
        return "True" if question.get("answer") is True else "False"
    if question_type == "numeric":
        answer = str(question.get("answer"))
        tolerance = question.get("tolerance")
        unit = question.get("unit")
        if tolerance not in (None, 0):
            answer += f" ±{tolerance}"
        if unit:
            answer += f" {unit}"
        return answer
    if question_type in {"short_answer", "fill_blank"}:
        answers = question.get("answers") or []
        if not answers:
            return "?"
        plain = next((answer for answer in answers if not answer.get("regex")), None)
        if plain:
            return str(plain.get("text", "")).strip()
        return str(answers[0].get("text", "")).strip()
    if question_type == "essay":
        return str(question.get("sample_answer") or question.get("rubric") or "Manual grading")
    if question_type == "code_review":
        answers = question.get("answers") or []
        return "; ".join(str(answer) for answer in answers) or "Manual grading"
    if question_type == "matching":
        return "; ".join(
            f"{pair.get('source', '')} → {pair.get('target', '')}"
            for pair in question.get("pairs", [])
        )
    if question_type == "ordering":
        return " → ".join(str(item) for item in question.get("items", []))
    return "?"


def _question_body(question: dict[str, Any]) -> list[str]:
    question_type = question.get("type")
    stem = str(question.get("stem", "")).rstrip()
    if question_type == "fill_blank":
        stem = stem.replace("{{blank}}", "__________")

    lines = [stem, ""]
    if question_type in {"mcq_one", "mcq_multi"}:
        for index, choice in enumerate(question.get("choices", [])):
            lines.append(f"- {_choice_letter(index)}. {choice.get('text', '')}")
        lines.append("")
    elif question_type == "true_false":
        lines.extend(["- True", "- False", ""])
    elif question_type == "numeric":
        unit = question.get("unit")
        hint = f" in {unit}" if unit else ""
        lines.extend([f"_Numeric response{hint}._", ""])
    elif question_type == "short_answer":
        lines.extend(["_Short response._", ""])
    elif question_type == "fill_blank":
        lines.extend(["_Fill in the blank._", ""])
    elif question_type == "essay":
        lines.extend(["_Written response._", ""])
    elif question_type == "code_review":
        language = str(question.get("language", "text"))
        lines.extend([f"```{language}", str(question.get("code", "")), "```", ""])
        for prompt in question.get("prompts", []) or []:
            lines.extend([f"- {prompt}", ""])
    elif question_type == "matching":
        pairs = question.get("pairs", []) or []
        targets = sorted(str(pair.get("target", "")) for pair in pairs)
        lines.extend(["**Choices:** " + "; ".join(targets), ""])
        for pair in pairs:
            lines.append(f"- {pair.get('source', '')}: ____________________")
        lines.append("")
    elif question_type == "ordering":
        values = sorted(str(value) for value in (question.get("items", []) or []))
        lines.extend(["**Put these in order:** " + "; ".join(values), ""])
        for index in range(1, len(values) + 1):
            lines.append(f"{index}. ______________________________")
        lines.append("")
    return lines


def _metadata_line(question: dict[str, Any]) -> str:
    pieces = [
        f"**Type:** {TYPE_LABELS.get(str(question.get('type')), str(question.get('type', '')))}",
        f"**Difficulty:** {str(question.get('difficulty', 'unrated')).title()}",
        f"**Points:** {question.get('points', 0)}",
    ]
    tags = question.get("tags") or []
    if tags:
        pieces.append("**Tags:** " + ", ".join(f"`{tag}`" for tag in tags))
    variant_group = (question.get("metadata") or {}).get("variant_group")
    if variant_group:
        pieces.append(f"**Variant group:** `{variant_group}`")
    return " · ".join(pieces)


def _source_lines(bank: Bank, question: dict[str, Any]) -> list[str]:
    source = question.get("source") or {}
    official_refs = source.get("official_refs") or []
    teaching_refs = source.get("teaching_refs") or []
    catalog = ((bank.data.get("metadata") or {}).get("source_catalog") or {})
    official_catalog = catalog.get("official") or {}

    lines: list[str] = []
    if official_refs:
        lines.append("**Official reference:**")
        for ref in official_refs:
            entry = official_catalog.get(ref) if isinstance(official_catalog, dict) else None
            if isinstance(entry, dict):
                title = entry.get("title") or ref
                url = entry.get("url")
                location = entry.get("location")
                text = f"- {title}"
                if location:
                    text += f" — {location}"
                if url:
                    text += f"  \n  {url}"
                lines.append(text)
            else:
                lines.append(f"- {ref}")
        lines.append("")
    if teaching_refs:
        lines.append("**Teaching/course provenance:**")
        lines.extend(f"- `{ref}`" for ref in teaching_refs)
        lines.append("")
    return lines


def _primary_category(bank: Bank, question: dict[str, Any]) -> str | None:
    category_ids = question.get("category_ids") or []
    return str(category_ids[0]) if category_ids else None


def _grouped_questions(bank: Bank) -> list[tuple[str, list[dict[str, Any]]]]:
    grouped: dict[str | None, list[dict[str, Any]]] = {}
    for question in bank.questions:
        grouped.setdefault(_primary_category(bank, question), []).append(question)

    groups: list[tuple[str, list[dict[str, Any]]]] = []
    seen: set[str | None] = set()
    for category in bank.categories:
        category_id = category["id"]
        if category_id in grouped:
            groups.append((category.get("title") or category_id, grouped[category_id]))
            seen.add(category_id)
    for category_id, questions in grouped.items():
        if category_id in seen:
            continue
        title = "Other questions" if category_id is None else category_id
        groups.append((title, questions))
    return groups


def _question_heading(question: dict[str, Any]) -> str:
    title = question.get("title")
    if title:
        return f"`{question['id']}` — {title}"
    return f"`{question['id']}`"


def render_questions(bank: Bank, question_filename: str, key_filename: str) -> str:
    lines = [
        f"# {bank.info['title']} — Practice Questions",
        "",
        "> Generated by Quizbank's GitHub-reference exporter. The JSON bank remains the source of truth.",
        "",
        f"[Open the answer key](keys/{key_filename})",
        "",
        f"**Source bank:** `{bank.path.name}`  ",
        f"**Questions:** {len(bank.questions)}",
        "",
    ]

    for group_title, questions in _grouped_questions(bank):
        lines.extend([f"## {group_title}", ""])
        for question in questions:
            qid = question["id"]
            lines.extend(
                [
                    f'<a id="q-{_slug(qid)}"></a>',
                    f"### {_question_heading(question)}",
                    "",
                    f"> {_metadata_line(question)}",
                    "",
                    f"[Answer and explanation](keys/{key_filename}#key-{_slug(qid)})",
                    "",
                ]
            )
            lines.extend(_question_body(question))
    return "\n".join(lines).rstrip() + "\n"


def render_key(bank: Bank, question_filename: str, key_filename: str) -> str:
    lines = [
        f"# {bank.info['title']} — Answer Key",
        "",
        "> Generated by Quizbank's GitHub-reference exporter. Each key entry repeats the original question and links back to it.",
        "",
        f"[Back to all practice questions](../{question_filename})",
        "",
        f"**Source bank:** `{bank.path.name}`  ",
        f"**Questions:** {len(bank.questions)}",
        "",
    ]

    for group_title, questions in _grouped_questions(bank):
        lines.extend([f"## {group_title}", ""])
        for question in questions:
            qid = question["id"]
            lines.extend(
                [
                    f'<a id="key-{_slug(qid)}"></a>',
                    f"### {_question_heading(question)}",
                    "",
                    f"[Back to this question](../{question_filename}#q-{_slug(qid)})",
                    "",
                    f"> {_metadata_line(question)}",
                    "",
                    "#### Question",
                    "",
                ]
            )
            lines.extend(_question_body(question))
            lines.extend(["#### Key", "", f"**Answer:** {_answer_for(question)}", ""])

            solution = str(question.get("solution") or "").strip()
            if solution:
                lines.extend([f"**Why:** {solution}", ""])

            feedback = question.get("feedback") or {}
            correct_feedback = str(feedback.get("correct") or "").strip()
            incorrect_feedback = str(feedback.get("incorrect") or "").strip()
            if correct_feedback:
                lines.extend([f"**Correct feedback:** {correct_feedback}", ""])
            if incorrect_feedback:
                lines.extend([f"**If incorrect:** {incorrect_feedback}", ""])

            lines.extend(_source_lines(bank, question))
    return "\n".join(lines).rstrip() + "\n"


def build_reference(bank: Bank, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    key_dir = output_dir / "keys"
    key_dir.mkdir(parents=True, exist_ok=True)

    stem = _file_stem(bank.info["id"])
    question_filename = f"{stem}.md"
    key_filename = f"{stem}-key.md"
    question_path = output_dir / question_filename
    key_path = key_dir / key_filename

    question_path.write_text(
        render_questions(bank, question_filename, key_filename), encoding="utf-8"
    )
    key_path.write_text(render_key(bank, question_filename, key_filename), encoding="utf-8")
    return [question_path, key_path]
