from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import inventory_legacy_questions as base

ORIGINAL_PARSE_MARKDOWN = base.parse_markdown


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


def _ref_hints(text: str) -> list[str]:
    hints: list[str] = []
    patterns = [
        r"(?im)//\s*Ref:\s*([^\n|]+(?:/[^\n|]+)*)",
        r"(?is)<!--\s*Ref:\s*(.*?)\s*\|\s*Answer:",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            value = re.sub(r"\s+", " ", match.group(1)).strip(" -")
            if value and value not in hints:
                hints.append(value)
    return hints


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
                raw["answers"] = [{"text": answer, "case_sensitive": False} for answer in answers]
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

        hints = _ref_hints(block)
        if hints:
            raw["legacy_ref_hints"] = hints
        base.add_record(records, branch, path, "typst-bank", raw, ordinal)


def _clean_inline_tf(stem: str) -> tuple[str, bool | None]:
    match = re.search(r"\s*\((True|False)(?:\s*[-–:]\s*[^)]*)?\)\s*$", stem, re.I)
    if not match:
        return stem, None
    return stem[: match.start()].rstrip(), match.group(1).lower() == "true"


def _html_answer(block: str) -> str | None:
    match = re.search(r"(?is)<!--.*?\bAnswer:\s*(.*?)\s*-->", block)
    if not match:
        return None
    value = re.sub(r"\s+", " ", match.group(1)).strip()
    return value or None


def _numbered_keyed_blocks(text: str):
    starts = list(re.finditer(r"(?m)^\s*(\d+)\.\s+(.+?)\s*$", text))
    for index, match in enumerate(starts):
        stem = match.group(2).strip()
        if re.match(r"^[A-J][.)]\s", stem):
            continue
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        block = text[match.end():end]
        if "<!--" not in block or "Answer:" not in block:
            continue
        yield int(match.group(1)), stem, block


def enhanced_parse_markdown(
    branch: str, path: str, text: str, records: list[dict[str, Any]]
) -> None:
    start_index = len(records)
    ORIGINAL_PARSE_MARKDOWN(branch, path, text, records)
    new_records = records[start_index:]

    # Fix answer-bearing T/F lines from structured Q banks before grouping.
    for record in new_records:
        if record.get("branch") != branch or record.get("path") != path:
            continue
        cleaned, answer = _clean_inline_tf(str(record.get("stem") or ""))
        if answer is None:
            continue
        record["stem"] = cleaned
        record["signature"] = base.signature_for(cleaned)
        raw = dict(record.get("raw") or {})
        raw["stem"] = cleaned
        raw["type"] = "true_false"
        raw["answer"] = answer
        record["type"] = "true_false"
        record["raw"] = raw

    # Recover generated Markdown banks that store the key and source in hidden
    # comments immediately after each numbered question.
    for ordinal, visible_stem, block in _numbered_keyed_blocks(text):
        stem = re.sub(r"^T/F:\s*", "", visible_stem, flags=re.I).strip()
        answer = _html_answer(block)
        if not answer:
            continue
        choices = []
        for match in re.finditer(r"(?m)^\s*-?\s*([A-J])[.)]\s+(.+?)\s*$", block):
            choices.append((match.group(1).upper(), match.group(2).strip()))

        raw: dict[str, Any] = {"stem": stem}
        tf_prefix = bool(re.match(r"^T/F:\s*", visible_stem, re.I))
        if tf_prefix and answer.strip().upper()[:1] in {"T", "F"}:
            raw["type"] = "true_false"
            raw["answer"] = answer.strip().upper().startswith("T")
        elif choices and re.fullmatch(r"[A-J]", answer.strip(), re.I):
            raw["type"] = "mcq_one"
            raw["legacy_choices"] = [choice for _, choice in choices]
            raw["legacy_correct"] = ord(answer.strip().upper()) - ord("A")
        else:
            raw["type"] = "short_answer"
            raw["legacy_answer"] = answer

        hints = _ref_hints(block)
        if hints:
            raw["legacy_ref_hints"] = hints

        signature = base.signature_for(stem)
        matching = [
            record for record in records[start_index:]
            if record.get("branch") == branch
            and record.get("path") == path
            and base.normalized_stem(str(record.get("stem") or "")) == base.normalized_stem(stem)
        ]
        if matching:
            record = matching[0]
            record["stem"] = stem
            record["signature"] = signature
            record["type"] = raw["type"]
            record["raw"] = raw
            record["source_kind"] = "markdown-keyed"
            record["ordinal"] = ordinal
        else:
            base.add_record(records, branch, path, "markdown-keyed", raw, ordinal)


def main() -> int:
    base.parse_typst_tuple_bank = enhanced_parse_typst_tuple_bank
    base.parse_markdown = enhanced_parse_markdown
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
