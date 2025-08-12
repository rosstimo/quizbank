#!/usr/bin/env python3
# tools/build_typst.py
from __future__ import annotations
import argparse, random, re
from pathlib import Path
from typing import Any, Dict, List
import yaml

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

# --- Minimal Markdown -> Typst normalization ---
MD_BOLD_STAR = re.compile(r"\*\*(.+?)\*\*")
MD_BOLD_USCORE = re.compile(r"__(.+?)__")

def md_to_typst(s: str | None) -> str:
    if not s:
        return ""
    # Convert Markdown strong to Typst strong (single *)
    s = MD_BOLD_STAR.sub(r"*\1*", s)
    s = MD_BOLD_USCORE.sub(r"*\1*", s)
    # Leave _emphasis_ and `code` alone (both valid in Typst)
    return s

def t_escape(s: str) -> str:
    # Escape braces so Typst doesn't treat them as code delimiters
    return s.replace("{", "\\{").replace("}", "\\}")

def norm(s: str | None) -> str:
    return t_escape(md_to_typst(s or "")).rstrip()

def choice_letter(i: int) -> str:
    return chr(ord("A") + i)

def render_item_typst(n: int, it: Dict[str, Any]) -> str:
    t = it.get("type")
    stem = norm(it.get("stem"))
    pts = it.get("points", 0)
    out = []
    out.append(f"=== {n}. ({pts} pt{'s' if pts != 1 else ''})")
    out.append(stem)
    out.append("")
    if t in {"mcq_one", "mcq_multi"}:
        for i, c in enumerate(it.get("choices", [])):
            text = norm(str(c.get("text", "")))
            out.append(f"- {choice_letter(i)}. {text}")
        out.append("")
    elif t == "true_false":
        out.append("- A. True")
        out.append("- B. False")
        out.append("")
    elif t == "numeric":
        unit = it.get("unit")
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
        show = []
        for a in answers[:3]:
            txt = str(a.get("text", ""))
            show.append(f"/{txt}/" if a.get("regex") else txt)
        more = " ..." if len(answers) > 3 else ""
        return "; ".join(show) + more
    return "?"

def build_typst(quiz: Dict[str, Any], items: List[Dict[str, Any]]) -> str:
    title = norm(quiz.get("title") or quiz.get("id") or "Quiz")
    instr = norm((quiz.get("instructions") or ""))
    lines: List[str] = []
    lines.append("#set page(margin: 1in)")
    lines.append("")
    lines.append(f"= {title}")
    lines.append("")
    if instr:
        lines.append(instr)
        lines.append("")
    for n, it in enumerate(items, start=1):
        lines.append(render_item_typst(n, it))
    lines.append("---")
    lines.append("")
    lines.append("== Answer Key")
    lines.append("")
    for n, it in enumerate(items, start=1):
        ans = norm(answer_for(it))
        sol = norm((it.get("solution") or "").strip())
        lines.append(f"{n}. *{ans}*")
        if sol:
            lines.append(f"    - {sol}")
    lines.append("")
    return "\n".join(lines)

def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(argument_default=None)
    ap.add_argument("quiz_file", help="Path to quiz assembly YAML")
    ap.add_argument("--bank", default="qbank", help="Root of the question bank")
    ap.add_argument("--seed", type=int, default=42, help="Random seed for sampling when 'pick' is set")
    ap.add_argument("--out", required=True, help="Output .typ file")
    args = ap.parse_args(argv)

    quiz = load_yaml(Path(args.quiz_file))
    id2path = index_items_by_id(Path(args.bank))
    items = load_items_by_ids(quiz.get("items", []), id2path)
    items = sample_items(items, quiz.get("pick"), args.seed)

    out = build_typst(quiz, items)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out, encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(None))
