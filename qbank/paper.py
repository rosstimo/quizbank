from __future__ import annotations

from collections import OrderedDict
from typing import Any

from tools import build_typst


SECTION_ORDER = (
    "true_false",
    "mcq",
    "fill_blank",
    "numeric",
    "short_answer",
    "matching",
    "ordering",
    "essay",
    "code_review",
)

SECTION_TITLES = {
    "true_false": "True / False",
    "mcq": "Multiple Choice Questions",
    "fill_blank": "Fill in the Blank",
    "numeric": "Numeric Response",
    "short_answer": "Short Answer",
    "matching": "Matching",
    "ordering": "Ordering",
    "essay": "Written Response",
    "code_review": "Code Review",
}

RENDERERS = {
    "true_false": "render_tf",
    "mcq": "render_mc",
    "fill_blank": "render_fib",
    "numeric": "render_numeric",
    "short_answer": "render_sa",
    "matching": "render_matching",
    "ordering": "render_ordering",
    "essay": "render_essay",
    "code_review": "render_cr",
}


def _paper_kind(item: dict[str, Any]) -> str:
    item_type = str(item.get("type", ""))
    if item_type in {"mcq_one", "mcq_multi"}:
        return "mcq"
    return item_type


def _group_items(items: list[dict[str, Any]]) -> OrderedDict[str, list[dict[str, Any]]]:
    grouped: OrderedDict[str, list[dict[str, Any]]] = OrderedDict(
        (kind, []) for kind in SECTION_ORDER
    )
    for item in items:
        kind = _paper_kind(item)
        grouped.setdefault(kind, []).append(item)
    return OrderedDict((kind, values) for kind, values in grouped.items() if values)


def _format_points(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:g}"


def _section_instruction(kind: str, group: list[dict[str, Any]]) -> str | None:
    if kind == "true_false":
        return "Circle one choice."
    if kind == "mcq":
        item_types = {str(item.get("type", "")) for item in group}
        if item_types == {"mcq_one"}:
            return "Circle one choice."
        if item_types == {"mcq_multi"}:
            return "Circle all that apply."
        return "Circle the requested choice(s)."
    return None


def _section_title(kind: str, group: list[dict[str, Any]], show_points: bool) -> str:
    title = SECTION_TITLES.get(kind, kind.replace("_", " ").title())
    if show_points and group:
        values = sorted({float(item.get("points", 0)) for item in group})
        if len(values) == 1:
            value = values[0]
            unit = "pt" if value == 1 else "pts"
            title = f"{title} ({_format_points(value)} {unit} each)"
        else:
            low = _format_points(values[0])
            high = _format_points(values[-1])
            title = f"{title} ({low}-{high} pts each)"

    instruction = _section_instruction(kind, group)
    if instruction:
        title = f"{title}: {instruction}"
    return title


def _question_markdown(number: int, item: dict[str, Any]) -> str:
    item_type = str(item.get("type", ""))
    stem = str(item.get("stem", "")).rstrip()

    if item_type == "fill_blank":
        stem = stem.replace("{{blank}}", "____________________")

    if item_type == "true_false":
        # Kept as a plain-text fallback; the paper renderer uses native Typst
        # for the larger, circle-friendly T / F choice.
        return f"**{number}.) T\u2002/\u2002F** {stem}\n"

    lines: list[str] = [f"**{number}.)** {stem}", ""]

    if item_type in {"mcq_one", "mcq_multi"}:
        for index, choice in enumerate(item.get("choices", []) or []):
            text = str(choice.get("text", "")).rstrip()
            # Markdown list markers add an unwanted bullet in the paper PDF. A hard line
            # break keeps A/B/C/D choices aligned while remaining plain text.
            lines.append(f"{build_typst.choice_letter(index)}. {text}  ")
        lines.append("")
    elif item_type == "numeric":
        unit = item.get("unit")
        suffix = f" {unit}" if unit else ""
        lines.extend([f"**Answer:** ______________________________{suffix}", ""])
    elif item_type == "short_answer":
        response_lines = int(item.get("response_lines", 3))
        for _ in range(response_lines):
            lines.extend(["---", ""])
    elif item_type == "essay":
        response_lines = int(item.get("response_lines", 8))
        for _ in range(response_lines):
            lines.extend(["---", ""])
    elif item_type == "code_review":
        language = str(item.get("language", "text"))
        lines.extend([f"```{language}", str(item.get("code", "")), "```", ""])
        response_lines = int(item.get("response_lines", 3))
        for prompt in item.get("prompts", []) or []:
            lines.extend([str(prompt), ""])
            for _ in range(response_lines):
                lines.extend(["---", ""])
    elif item_type == "matching":
        pairs = item.get("pairs", []) or []
        targets = sorted(str(pair.get("target", "")) for pair in pairs)
        lines.extend(["**Choices:** " + ", ".join(targets), ""])
        for pair in pairs:
            lines.append(f"- {pair.get('source', '')}: ____________________")
        lines.append("")
    elif item_type == "ordering":
        values = sorted(str(value) for value in (item.get("items", []) or []))
        lines.extend(["**Put these in order:** " + ", ".join(values), ""])
        for index in range(1, len(values) + 1):
            lines.append(f"{index}. ______________________________")
        lines.append("")

    return "\n".join(lines)


def _question_typst(number: int, item: dict[str, Any]) -> str:
    if str(item.get("type", "")) == "true_false":
        stem = str(item.get("stem", "")).rstrip()
        stem_typst = build_typst.md_to_typst(stem + "\n").strip()
        return (
            f"#strong[{number}.)] "
            '#text(size: 14pt, weight: "bold")[T#h(0.65em)/#h(0.65em)F] '
            f"{stem_typst}"
        )
    return build_typst.md_to_typst(_question_markdown(number, item)).strip()


def _answer_key_markdown(numbered: list[tuple[int, dict[str, Any]]]) -> str:
    lines = ["# Answer Key", ""]
    for number, item in numbered:
        answer = build_typst.answer_for(item)
        solution = str(item.get("solution") or "").strip()
        lines.append(f"{number}. `{answer}`")
        if solution:
            lines.append(f"    - {solution}")
    lines.append("")
    return "\n".join(lines)


def build_paper_typst(
    assessment: dict[str, Any],
    items: list[dict[str, Any]],
    include_key: bool,
    show_points: bool = True,
) -> str:
    """Build question-aware Typst source while preserving QMP text via Pandoc fragments."""
    grouped = _group_items(items)
    title = str(assessment.get("title") or assessment.get("id") or "Assessment")
    title_typst = build_typst.md_to_typst(f"# {title}\n").strip()
    paper_instructions = (assessment.get("metadata") or {}).get("paper_instructions")

    out = [
        '#import "renderers.typ": *',
        "",
        '#set page("us-letter", margin: (top: 1in, bottom: 0.75in, left: 1in, right: 0.75in))',
        '#set text(font: "Libertinus Serif", size: 12pt)',
        "",
        title_typst,
        "",
    ]

    if isinstance(paper_instructions, str) and paper_instructions.strip():
        out.extend([build_typst.md_to_typst(paper_instructions).strip(), ""])

    out.extend(
        [
            "#table(",
            "  columns: (auto, 1fr, auto, 1fr),",
            "  align: (left, bottom),",
            "  stroke: none,",
            "  [Name:], [#line(length: 100%)],",
            "  [Date:], [#line(length: 100%)],",
            ")",
            "#v(0.8em)",
            "",
        ]
    )

    numbered: list[tuple[int, dict[str, Any]]] = []
    number = 1
    first_section = True
    for kind, group in grouped.items():
        if not first_section:
            out.extend(["#pagebreak()", ""])
        first_section = False

        title_text = _section_title(kind, group, show_points)
        out.extend([f"== *{title_text}*", "#v(0.45em)", ""])
        renderer = RENDERERS.get(kind, "render_sa")
        for item in group:
            body = _question_typst(number, item)
            out.extend([f"#{renderer}([", body, "])", "#v(0.35em)", ""])
            numbered.append((number, item))
            number += 1

    if include_key:
        out.extend(
            [
                "#pagebreak()",
                build_typst.md_to_typst(_answer_key_markdown(numbered)).strip(),
                "",
            ]
        )

    return "\n".join(out)
