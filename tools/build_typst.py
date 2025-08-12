#!/usr/bin/env python3
r"""
Build a Typst source (.typ) by piping one consolidated Markdown doc through Pandoc.

Author in QMP (Pandoc-flavored Markdown: gfm+tex_math_dollars).
We assemble a Markdown quiz doc (title, items, optional answer key), then:
  Markdown --(pandoc -t typst)--> Typst

Usage:
  python tools/build_typst.py quizzes/quiz-example.yaml --out build/typst/quiz-example.typ
Options:
  --bank DIR            Root of the question bank (default: qbank)
  --seed N              RNG seed when quiz.pick is set (default: 42)
  --no-key              Omit the answer key section
  --inline-solutions    Print solutions under each question
"""

from __future__ import annotations
import argparse
import random
import subprocess
from pathlib import Path
from typing import Any, Dict, List

import yaml


# ---------------- YAML helpers ----------------

def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def find_item_files(bank_dir: Path) -> List[Path]:
    return [p for p in bank_dir.rglob("*.y*ml") if p.is_file()]

def index_items_by_id(bank_dir: Path) -> Dict[str, Path]:
    idx: Dict[str, Path] = {}
    for p in find_item_files(bank_dir):
        try:
            data = load_yaml(p)
        except Exception:
            continue
        if isinstance(data, dict) and isinstance(data.get("id"), str):
            idx.setdefault(data["id"], p)
    return idx

def load_items_by_ids(entries: List[Any], id2path: Dict[str, Path]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for e in entries:
        if isinstance(e, str):
            qid, pts = e, None
        elif isinstance(e, dict) and "id" in e:
            qid, pts = e["id"], e.get("points")
        else:
            raise ValueError(f"Bad quiz item entry: {e!r}")
        p = id2path.get(qid)
        if not p:
            raise FileNotFoundError(f"Question ID not found: {qid}")
        data = load_yaml(p)
        if pts is not None:
            data["points"] = pts
        items.append(data)
    return items

def sample_items(items: List[Dict[str, Any]], pick: int | None, seed: int) -> List[Dict[str, Any]]:
    if not pick or pick >= len(items):
        return items
    rng = random.Random(seed)
    return rng.sample(items, k=pick)


# ---------------- Quiz -> Markdown assembly ----------------

def choice_letter(i: int) -> str:
    return chr(ord("A") + i)

def answer_for(it: Dict[str, Any]) -> str:
    t = it.get("type")
    if t == "mcq_one":
        for i, c in enumerate(it.get("choices", [])):
            if c.get("correct") is True:
                return choice_letter(i)
        return "?"
    if t == "mcq_multi":
        letters = [choice_letter(i) for i, c in enumerate(it.get("choices", [])) if c.get("correct")]
        return ", ".join(letters) if letters else "?"
    if t == "true_false":
        return "True" if it.get("answer") is True else "False"
    if t == "numeric":
        ans = it.get("answer")
        tol = it.get("tolerance")
        unit = it.get("unit")
        parts = [str(ans)]
        if tol is not None:
            parts.append(f"±{tol}")
        if unit:
            parts.append(unit)
        return " ".join(parts)
    if t == "short_answer":
        answers = it.get("answers") or []
        if not answers:
            return "?"
        plain = next((a for a in answers if not a.get("regex")), None)
        if plain:
            return str(plain.get("text", "")).strip()
        rx = str(answers[0].get("text", "")).strip().strip("/")
        rx = rx.removeprefix("(?i)")
        return rx or "?"
    return "?"

def md_from_item(n: int, it: Dict[str, Any], inline_solutions: bool) -> str:
    t = it.get("type")
    stem = it.get("stem", "")
    pts = it.get("points", 0)
    lines: List[str] = []
    lines.append(f"### {n}. ({pts} pt{'s' if pts != 1 else ''})")
    lines.append("")
    lines.append(stem.rstrip())
    lines.append("")
    if t in {"mcq_one", "mcq_multi"}:
        for i, c in enumerate(it.get("choices", [])):
            text = str(c.get("text", "")).rstrip()
            # keep it simple: labeled bullet; Pandoc will format nicely
            lines.append(f"- {choice_letter(i)}. {text}")
        lines.append("")
    elif t == "true_false":
        lines.append("- A. True")
        lines.append("- B. False")
        lines.append("")
    elif t == "numeric":
        unit = it.get("unit")
        hint = f" (unit: {unit})" if unit else ""
        lines.append(f"_Answer: numeric{hint}_")
        lines.append("")
    elif t == "short_answer":
        lines.append("_Answer: short text_")
        lines.append("")
    else:
        lines.append("_Unsupported type in renderer_")
        lines.append("")

    if inline_solutions:
        sol = (it.get("solution") or "").strip()
        if sol:
            lines.append(f"> **Solution:** {sol}")
            lines.append("")

    return "\n".join(lines)

def build_markdown_doc(quiz: Dict[str, Any], items: List[Dict[str, Any]], no_key: bool, inline_solutions: bool) -> str:
    title = quiz.get("title") or quiz.get("id") or "Quiz"
    instr = (quiz.get("instructions") or "").rstrip()

    out: List[str] = []
    out.append(f"# {title}")
    out.append("")
    if instr:
        out.append(instr)
        out.append("")

    for n, it in enumerate(items, start=1):
        out.append(md_from_item(n, it, inline_solutions))

    if not no_key:
        out.append("## Answer Key")
        out.append("")
        for n, it in enumerate(items, start=1):
            ans = answer_for(it)
            sol = (it.get("solution") or "").strip()
            out.append(f"{n}. `{ans}`")
            if sol and not inline_solutions:
                out.append(f"    - {sol}")
        out.append("")

    return "\n".join(out)


# ---------------- Pandoc: Markdown -> Typst ----------------

def md_to_typst(md_text: str) -> str:
    """Call pandoc to convert Markdown -> Typst. Requires pandoc on PATH."""
    try:
        proc = subprocess.run(
            ["pandoc", "-f", "gfm+tex_math_dollars", "-t", "typst"],
            input=md_text.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    except FileNotFoundError:
        raise RuntimeError("pandoc not found in PATH")
    except subprocess.CalledProcessError as e:
        raise RuntimeError("pandoc failed:\n" + e.stderr.decode("utf-8", "ignore"))
    return proc.stdout.decode("utf-8")


# ---------------- Main ----------------

def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(argument_default=None)
    ap.add_argument("quiz_file", help="Path to quiz assembly YAML")
    ap.add_argument("--bank", default="qbank", help="Root of the question bank")
    ap.add_argument("--seed", type=int, default=42, help="Random seed for sampling when 'pick' is set")
    ap.add_argument("--out", required=True, help="Output .typ file")
    ap.add_argument("--no-key", action="store_true", help="Omit the answer key section")
    ap.add_argument("--inline-solutions", action="store_true", help="Print solutions under each question")
    args = ap.parse_args(argv)

    quiz = load_yaml(Path(args.quiz_file))
    id2path = index_items_by_id(Path(args.bank))
    items = load_items_by_ids(quiz.get("items", []), id2path)
    items = sample_items(items, quiz.get("pick"), args.seed)

    md_doc = build_markdown_doc(quiz, items, args.no_key, args.inline_solutions)
    typst_body = md_to_typst(md_doc)

    # Prepend a tiny preamble. Keep it minimal so Pandoc’s doc structure stays intact.
    preamble = "#set page(margin: 1in)\n#let horizontalrule = line(length: 100%)\n\n"
    out_text = preamble + typst_body

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out_text, encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(None))
