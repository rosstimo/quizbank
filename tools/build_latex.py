#!/usr/bin/env python3
r"""
Build a LaTeX source (.tex) from a quiz assembly YAML and your YAML item bank.

Scope:
  - Supports mcq_one, mcq_multi, true_false, numeric, short_answer
  - Minimal Markdown -> LaTeX normalization:
      **bold** / __bold__  -> \textbf{}
      `code`               -> \verb|code|
      [text](url)          -> \href{url}{text}
    Everything else is lightly escaped so LaTeX doesn't explode.
"""

from __future__ import annotations
import argparse
import random
from pathlib import Path
from typing import Any, Dict, List

import yaml
try:
    from tools.common import pandoc_convert
except ModuleNotFoundError:
    from common import pandoc_convert


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


def qmp_to_tex(s: str) -> str:
    return pandoc_convert(s or "", to_fmt="latex")

def t(s: Any) -> str:
    return qmp_to_tex(str(s or "")).rstrip()

def choice_letter(i: int) -> str:
    return chr(ord("A") + i)


# ---------------- Rendering ----------------

def render_item_tex(n: int, it: Dict[str, Any]) -> str:
    typ = it.get("type")
    stem = t(it.get("stem"))
    pts = it.get("points", 0)

    lines: List[str] = []
    lines.append(r"\noindent\textbf{" + f"{n}. ({pts} pt{'s' if pts != 1 else ''})" + r"}")
    lines.append(r"")
    lines.append(stem)
    lines.append(r"")

    if typ in {"mcq_one", "mcq_multi"}:
        lines.append(r"\refstepcounter{qnum}")
        lines.append(r"\begingroup")
        lines.append(r"\renewcommand{\theHenumi}{\theqnum.\arabic{enumi}}")
        lines.append(r"\begin{enumerate}[label=\Alph*.]")
        for i, c in enumerate(it.get("choices", [])):
            lines.append(r"\item " + t(c.get("text", "")))
        lines.append(r"\end{enumerate}")
        lines.append(r"\endgroup")
        lines.append(r"")
    elif typ == "true_false":
        lines.append(r"\refstepcounter{qnum}")
        lines.append(r"\begingroup")
        lines.append(r"\renewcommand{\theHenumi}{\theqnum.\arabic{enumi}}")
        lines.append(r"\begin{enumerate}[label=\Alph*.]")
        lines.append(r"\item True")
        lines.append(r"\item False")
        lines.append(r"\end{enumerate}")
        lines.append(r"\endgroup")
        lines.append(r"")
    elif typ == "numeric":
        unit = it.get("unit")
        hint = f" (unit: {unit})" if unit else ""
        lines.append(r"\emph{Answer: numeric" + t(hint) + r"}")
        lines.append(r"")
    elif typ == "short_answer":
        lines.append(r"\emph{Answer: short text}")
        lines.append(r"")
    else:
        lines.append(r"\emph{Unsupported type in renderer}")
        lines.append(r"")

    return "\n".join(lines)

def answer_for(it: Dict[str, Any]) -> str:
    typ = it.get("type")
    if typ == "mcq_one":
        for i, c in enumerate(it.get("choices", [])):
            if c.get("correct") is True:
                return choice_letter(i)
        return "?"
    if typ == "mcq_multi":
        letters = [choice_letter(i) for i, c in enumerate(it.get("choices", [])) if c.get("correct")]
        return ", ".join(letters) if letters else "?"
    if typ == "true_false":
        return "True" if it.get("answer") is True else "False"
    if typ == "numeric":
        ans = it.get("answer")
        tol = it.get("tolerance")
        unit = it.get("unit")
        parts = [str(ans)]
        if tol is not None:
            parts.append(f"±{tol}")
        if unit:
            parts.append(str(unit))
        return " ".join(parts)
    if typ == "short_answer":
        answers = it.get("answers") or []
        if not answers:
            return "?"
        show = []
        for a in answers[:3]:
            txt = str(a.get("text", ""))
            show.append(f"/{txt}/" if a.get("regex") else txt)
        more = " ..." if len(answers) > 3 else ""
        return "; ".join(show) + more
    return "?"

def build_tex(quiz: Dict[str, Any], items: List[Dict[str, Any]]) -> str:
    title = t(quiz.get("title") or quiz.get("id") or "Quiz")
    instr = t(quiz.get("instructions") or "")

    out: List[str] = []
    out.append(r"\documentclass[11pt]{article}")
    out.append(r"\usepackage{iftex}")
    out.append(r"\ifPDFTeX")
    out.append(r"  \usepackage[T1]{fontenc}")
    out.append(r"  \usepackage[utf8]{inputenc}")
    out.append(r"  \usepackage{lmodern}")
    out.append(r"\else")
    out.append(r"  \usepackage{fontspec}")
    out.append(r"  % Pick Unicode fonts with broad coverage. Swap if you prefer others.")
    out.append(r"  \setmainfont{Noto Serif}[Scale=MatchLowercase]")
    out.append(r"  \setsansfont{Noto Sans}[Scale=MatchLowercase]")
    out.append(r"  \setmonofont{Noto Sans Mono}[Scale=MatchLowercase]")
    out.append(r"\fi")
    out.append(r"\usepackage[margin=1in]{geometry}")
    out.append(r"\usepackage{enumitem}")
    out.append(r"\usepackage{amsmath,amssymb}")
    out.append(r"\usepackage{graphicx}")
    out.append(r"\usepackage[hidelinks,hypertexnames=false]{hyperref}")
    out.append(r"% Ensure unique hyperlink anchors for enumerate items per question")
    out.append(r"\newcounter{qnum}")
    out.append(r"\setlist[enumerate]{itemsep=2pt,topsep=4pt}")
    out.append(r"\begin{document}")
    out.append(r"\begin{center}")
    out.append(r"\Large " + title + r"\\[6pt]")
    out.append(r"\normalsize")
    out.append(r"\end{center}")
    if instr:
        out.append(instr + r"\\[6pt]")
    out.append(r"\vspace{0.5\baselineskip}")

    # Questions
    for n, it in enumerate(items, start=1):
        out.append(render_item_tex(n, it))

    # Answer key
    out.append(r"\clearpage")
    out.append(r"\section*{Answer Key}")
    out.append(r"\begin{enumerate}")
    for n, it in enumerate(items, start=1):
        ans = t(answer_for(it))
        sol = t((it.get("solution") or "").strip())
        out.append(r"\item " + r"\textbf{" + ans + r"}")
        if sol:
            out.append(r"\begin{itemize}")
            out.append(r"\item \textit{Solution:} " + sol)
            out.append(r"\end{itemize}")
    out.append(r"\end{enumerate}")

    out.append(r"\end{document}")
    return "\n".join(out)


# ---------------- Main ----------------

def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(argument_default=None)
    ap.add_argument("quiz_file", help="Path to quiz assembly YAML")
    ap.add_argument("--bank", default="qbank", help="Root of the question bank")
    ap.add_argument("--seed", type=int, default=42, help="Random seed for sampling when 'pick' is set")
    ap.add_argument("--out", required=True, help="Output .tex file")
    args = ap.parse_args(argv)

    quiz = load_yaml(Path(args.quiz_file))
    id2path = index_items_by_id(Path(args.bank))
    items = load_items_by_ids(quiz.get("items", []), id2path)
    items = sample_items(items, quiz.get("pick"), args.seed)

    tex = build_tex(quiz, items)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(tex, encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
