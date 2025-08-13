from __future__ import annotations
from pathlib import Path
from typing import List, Dict
import csv
from tools.importers.common import (
    coerce_list_tags, parse_letters, choice_letter, to_bool
)

FORMAT_NAME = "csv"

def import_items(path: Path, opts) -> List[Dict]:
    mapping: Dict[str, str] = {}
    for m in (opts.csv_map or []):
        if "=" not in m:
            raise ValueError(f"Bad --csv-map entry: {m!r}")
        k, v = m.split("=", 1)
        mapping[k.strip()] = v.strip()

    def col(row: Dict[str,str], key: str, default: str = "") -> str:
        name = mapping.get(key, key)
        return row.get(name, default)

    out: List[Dict] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t = (col(row, "type") or "mcq_one").strip().lower()
            stem = (col(row, "stem") or "").strip()
            if not stem:
                continue
            item: Dict[str, any] = {
                "id": (col(row, "id") or "").strip(),
                "version": 1,
                "type": t,
                "points": int(col(row, "points") or opts.default_points or 1),
                "topic": (col(row, "topic") or opts.topic or "Imported").strip(),
                "difficulty": (col(row, "difficulty") or opts.difficulty).strip(),
                "tags": coerce_list_tags(col(row, "tags")),
                "stem": stem,
                "author": opts.author,
                "license": opts.license,
            }
            if t in {"mcq_one", "mcq_multi"}:
                letters = ["A","B","C","D","E"]
                choices = []
                correct_answers = set(parse_letters(col(row, "correct")))
                for idx, L in enumerate(letters):
                    txt = col(row, f"choice{L}")
                    if txt and txt.strip():
                        choice = {"text": txt.strip()}
                        if choice_letter(idx) in correct_answers:
                            choice["correct"] = True
                        choices.append(choice)
                if not choices:
                    continue
                item["choices"] = choices
                if opts.shuffle_choices is not None:
                    item["shuffle_choices"] = bool(opts.shuffle_choices)
            elif t == "true_false":
                ans = col(row, "answer") or col(row, "correct")
                item["answer"] = to_bool(ans)
            elif t == "numeric":
                item["answer"] = float(col(row, "answer") or 0)
                tol = (col(row, "tolerance") or "").strip()
                if tol:
                    item["tolerance"] = float(tol)
                unit = (col(row, "unit") or "").strip()
                if unit:
                    item["unit"] = unit
            elif t == "short_answer":
                answers = col(row, "answers").strip()
                if answers:
                    import json
                    print(f"DEBUG: Raw answers field: {answers}")  # Debugging output
                    try:
                        # Ensure proper parsing of JSON strings
                        item["answers"] = json.loads(answers)
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Invalid JSON format for answers: {answers}. Error: {e}")
            fc = (col(row, "feedback_correct") or "").strip()
            fi = (col(row, "feedback_incorrect") or "").strip()
            sol = (col(row, "solution") or "").strip()
            if fc or fi:
                item["feedback"] = {}
                if fc: item["feedback"]["correct"] = fc
                if fi: item["feedback"]["incorrect"] = fi
            if sol:
                item["solution"] = sol
            out.append(item)
    return out
