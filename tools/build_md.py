#!/usr/bin/env python3
"""
Build a Markdown quiz from YAML items and a quiz assembly file.

Usage:
  python tools/build_md.py quizzes/quiz-example.yaml > build/markdown/quiz-example.md

Options:
  --seed N        Random seed used when 'pick' < number of items (default: 42)
  --bank DIR      Root of the question bank (default: qbank)
  --out FILE      Write to a file instead of stdout
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path
from typing import Dict, List, Any

import yaml


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def find_item_files(bank_dir: Path) -> List[Path]:
    return [p for p in bank_dir.rglob("*.y*ml") if p.is_file()]


def index_items_by_id(bank_dir: Path) -> Dict[str, Path]:
    index: Dict[str, Path] = {}
    for p in find_item_files(bank_dir):
        try:
            data = load_yaml(p)
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        qid = data.get("id")
        if isinstance(qid, str) and qid not in index:
            index[qid] = p
    return index


def load_items_by_ids(ids_and_overrides: List[Any], id_to_path: Dict[str, Path]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for entry in ids_and_overrides:
        if isinstance(entry, str):
            qid, override_points = entry, None
        elif isinstance(entry, dict) and "id" in entry:
            qid = entry["id"]
            override_points = entry.get("points")
        else:
            raise ValueError(f"Unsupported item entry in quiz file: {entry!r}")

        p = id_to_path.get(qid)
        if not p:
            raise FileNotFoundError(f"Question ID not found in bank: {qid}")
        data = load_yaml(p)
        if override_points is not None:
            data["points"] = override_points
        items.append(data)
    return items


def sample_items(items: List[Dict[str, Any]], pick: int, seed: int) -> List[Dict[str, Any]]:
    if pick is None or pick >= len(items):
        return items
    rng = random.Random(seed)
    return rng.sample(items, k=pick)


def md_escape(s: str) -> str:
    # Light-touch escaping for headings or plain text; stems/choices already markdown.
    return s.replace("<", "&lt;").replace(">", "&gt;")


def choice_letter(i: int) -> str:
    return chr(ord("A") + i)


def render_item_md(idx: int, item: Dict[str, Any]) -> str:
    t = item.get("type")
    stem = item.get("stem", "").rstrip()
    points = item.get("points", 0)

    out: List[str] = []
    out.append(f"### {idx}. ({points} pt{'s' if points != 1 else ''})")
    out.append("")
    out.append(stem)
    out.append("")

    if t in {"mcq_one", "mcq_multi"}:
        choices = item.get("choices", [])
        for i, c in enumerate(choices):
            text = c.get("text", "")
            out.append(f"- {choice_letter(i)}. {text}")
        out.append("")
    elif t == "true_false":
        out.append("- A. True")
        out.append("- B. False")
        out.append("")
    elif t == "numeric":
        unit = item.get("unit")
        hint = f" (unit: {unit})" if unit else ""
        out.append(f"_Answer: numeric{hint}_")
        out.append("")
    elif t == "short_answer":
        out.append("_Answer: short text_")
        out.append("")
    else:
        out.append("_Unsupported type in renderer_")
        out.append("")

    return "\n".join(out)


def determine_answer(item: Dict[str, Any]) -> str:
    t = item.get("type")
    if t == "mcq_one":
        for i, c in enumerate(item.get("choices", [])):
            if c.get("correct") is True:
                return choice_letter(i)
        return "?"
    if t == "mcq_multi":
        letters = [choice_letter(i) for i, c in enumerate(item.get("choices", [])) if c.get("correct") is True]
        return ", ".join(letters) if letters else "?"
    if t == "true_false":
        return "True" if item.get("answer") is True else "False"
    if t == "numeric":
        ans = item.get("answer")
        tol = item.get("tolerance")
        unit = item.get("unit")
        parts = [str(ans)]
        if tol is not None:
            parts.append(f"±{tol}")
        if unit:
            parts.append(unit)
        return " ".join(parts)
    if t == "short_answer":
        answers = item.get("answers", [])
        if not answers:
            return "?"
        sample = []
        for a in answers[:3]:
            txt = a.get("text", "")
            if a.get("regex"):
                sample.append(f"/{txt}/")
            else:
                sample.append(txt)
        more = " ..." if len(answers) > 3 else ""
        return "; ".join(sample) + more
    return "?"


def build_markdown(quiz: Dict[str, Any], items: List[Dict[str, Any]]) -> str:
    title = quiz.get("title", quiz.get("id", "Quiz"))
    instructions = quiz.get("instructions")
    lines: List[str] = []
    lines.append(f"# {md_escape(title)}")
    lines.append("")
    if instructions:
        lines.append(instructions.rstrip())
        lines.append("")

    for n, it in enumerate(items, start=1):
        lines.append(render_item_md(n, it))

    # Answer key
    lines.append("---")
    lines.append("")
    lines.append("## Answer Key")
    lines.append("")
    for n, it in enumerate(items, start=1):
        ans = determine_answer(it)
        sol = it.get("solution")
        lines.append(f"{n}. **{ans}**")
        if sol:
            lines.append(f"    - {sol.strip()}")
    lines.append("")

    return "\n".join(lines)


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(argument_default=None)
    ap.add_argument("quiz_file", help="Path to quiz assembly YAML")
    ap.add_argument("--seed", type=int, default=42, help="Random seed when sampling with 'pick'")
    ap.add_argument("--bank", default="qbank", help="Root directory of the question bank")
    ap.add_argument("--out", default="-", help="Output file or '-' for stdout")
    args = ap.parse_args(argv)

    quiz_path = Path(args.quiz_file)
    if not quiz_path.exists():
        sys.stderr.write(f"Quiz file not found: {quiz_path}\n")
        return 2

    quiz = load_yaml(quiz_path)
    if not isinstance(quiz, dict):
        sys.stderr.write("Quiz YAML must be a single mapping\n")
        return 2

    bank_dir = Path(args.bank)
    id_index = index_items_by_id(bank_dir)

    raw_items = quiz.get("items", [])
    if not raw_items:
        sys.stderr.write("Quiz has no items\n")
        return 2

    items = load_items_by_ids(raw_items, id_index)
    pick = quiz.get("pick")
    items = sample_items(items, pick, args.seed)

    md = build_markdown(quiz, items)

    if args.out == "-" or args.out == "":
        sys.stdout.write(md)
    else:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md, encoding="utf-8")
        print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
