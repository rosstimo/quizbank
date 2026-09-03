from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from tools import inventory_legacy_questions as base


def _tuple_block(block: str, field: str) -> str | None:
    match = re.search(rf"\b{re.escape(field)}\s*:\s*\((.*?)\)\s*,?\s*(?:\n\s*[A-Za-z_][A-Za-z0-9_]*\s*:|\n\s*\)|$)", block, re.S)
    return match.group(1) if match else None


def _boolean_field(block: str, field: str) -> bool | None:
    match = re.search(rf"\b{re.escape(field)}\s*:\s*(true|false)\b", block, re.I)
    if not match:
        return None
    return match.group(1).lower() == "true"


def _integer_field(block: str, field: str) -> int | None:
    match = re.search(rf"\b{re.escape(field)}\s*:\s*(-?\d+)\b", block)
    return int(match.group(1)) if match else None


def _quoted_tuple(block: str, field: str) -> list[str]:
    value = _tuple_block(block, field)
    return base.quoted_strings(value) if value else []


def enhanced_parse_typst_tuple_bank(
    branch: str, path: str, text: str, records: list[dict[str, Any]]
) -> None:
    name = Path(path).name.lower()
    if not (name.endswith("_bank.typ") or "/banks/" in path.lower() or "bank" in name):
        return

    filename_type: str | None = None
    if name.startswith("mc_") or name == "mc_bank.typ":
        filename_type = "mcq_one"
    elif name.startswith("tf_") or name == "tf_bank.typ":
        filename_type = "true_false"
    elif name.startswith("sa_") or name == "sa_bank.typ":
        filename_type = "short_answer"
    elif name.startswith("fib_") or name == "fib_bank.typ":
        filename_type = "fill_blank"
    elif name.startswith("cr_") or name == "cr_bank.typ":
        filename_type = "code_review"

    for ordinal, (key, block) in enumerate(base.split_typst_entries(text), 1):
        text_field = base.typst_field(block, "text")
        stem_field = base.typst_field(block, "stem")
        question_field = base.typst_field(block, "question")
        before = base.typst_field(block, "before")
        after = base.typst_field(block, "after")
        answer_text = base.typst_field(block, "answer")
        answer_bool = _boolean_field(block, "answer")
        code = base.typst_field(block, "code")
        language = base.typst_field(block, "lang") or base.typst_field(block, "language")
        choices = _quoted_tuple(block, "choices")
        followups = _quoted_tuple(block, "followups") or _quoted_tuple(block, "prompts")
        answers = _quoted_tuple(block, "answers")
        correct = _integer_field(block, "correct")
        shuffle = _boolean_field(block, "shuffle")

        qtype = filename_type
        if qtype is None:
            if code and followups:
                qtype = "code_review"
            elif before is not None or after is not None:
                qtype = "fill_blank"
            elif choices:
                qtype = "mcq_one"
            elif answer_bool is not None:
                qtype = "true_false"
            elif answer_text is not None:
                qtype = "short_answer"

        if qtype == "fill_blank":
            if before is None and after is None:
                stem = text_field or stem_field or question_field or ""
            else:
                stem = f"{before or ''} {{{{blank}}}} {after or ''}".strip()
        else:
            stem = text_field or stem_field or question_field or ""

        if not stem:
            continue

        raw: dict[str, Any] = {"id": key, "type": qtype, "stem": stem}

        if qtype in {"mcq_one", "mcq_multi"}:
            if choices:
                raw["legacy_choices"] = choices
            if correct is not None:
                # The historical Typst helpers use zero-based indexes.
                raw["legacy_correct"] = correct
            if answer_text is not None:
                raw["legacy_answer"] = answer_text
            if shuffle is not None:
                raw["shuffle_choices"] = shuffle
        elif qtype == "true_false":
            if answer_bool is not None:
                raw["answer"] = answer_bool
            elif answer_text is not None and answer_text.strip().lower() in {"true", "false", "t", "f"}:
                raw["answer"] = answer_text.strip().lower().startswith("t")
        elif qtype in {"short_answer", "fill_blank"}:
            if answer_text is not None:
                raw["legacy_answer"] = answer_text
            elif answers:
                raw["answers"] = [
                    {"text": answer, "case_sensitive": False} for answer in answers
                ]
        elif qtype == "code_review":
            if code:
                raw["code"] = code
            if language:
                raw["language"] = language
            if followups:
                raw["prompts"] = followups
            if answers:
                raw["answers"] = answers
        elif qtype == "essay":
            if answer_text is not None:
                raw["sample_answer"] = answer_text

        # Preserve old inline Ref comments for the enrichment pass. They are
        # evidence locators, not verified citations until mapped to an official document.
        refs = []
        for match in re.finditer(r"(?im)//\s*Ref:\s*([^\n|]+(?:/[^\n|]+)*)", block):
            value = re.sub(r"\s+", " ", match.group(1)).strip()
            if value and value not in refs:
                refs.append(value)
        if refs:
            raw["legacy_ref_hints"] = refs

        base.add_record(records, branch, path, "typst-bank", raw, ordinal)


def main() -> int:
    base.parse_typst_tuple_bank = enhanced_parse_typst_tuple_bank
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
