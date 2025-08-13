from __future__ import annotations
from pathlib import Path
import re
from typing import List, Dict
from tools.importers.common import coerce_list_tags, choice_letter

FORMAT_NAME = "gift"

GIFT_Q = re.compile(r"(?P<stem>.*?)\{(?P<body>.*)\}\s*$", re.DOTALL)

def split_gift_questions(text: str) -> List[str]:
    out, buf, depth = [], [], 0
    for ch in text:
        buf.append(ch)
        if ch == "{": depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                out.append("".join(buf).strip())
                buf = []
    return out

def parse_gift(block: str, opts) -> Dict | None:
    m = GIFT_Q.search(block)
    if not m:
        return None
    stem = m.group("stem").strip()
    body = m.group("body").strip()

    if re.fullmatch(r"[tT](rue)?|[fF](alse)?", body):
        ans = body.lower().startswith("t")
        return {
            "id": "", "version": 1, "type": "true_false",
            "points": int(opts.default_points or 1),
            "topic": opts.topic or "Imported", "difficulty": opts.difficulty,
            "tags": coerce_list_tags(opts.tags), "stem": stem,
            "answer": ans, "author": opts.author, "license": opts.license,
        }

    if body.startswith("#"):
        parts = body[1:].split(":")
        ans = float(parts[0].strip())
        item = {
            "id": "", "version": 1, "type": "numeric",
            "points": int(opts.default_points or 1),
            "topic": opts.topic or "Imported", "difficulty": opts.difficulty,
            "tags": coerce_list_tags(opts.tags), "stem": stem,
            "answer": ans, "author": opts.author, "license": opts.license,
        }
        if len(parts) > 1 and parts[1].strip():
            item["tolerance"] = float(parts[1].strip())
        return item

    if body.startswith("=") or body.startswith("%"):
        entries = re.split(r"(?<!\\)~", body)
        equals = [e for e in entries if e.strip().startswith("=")]
        if len(equals) == len(entries):
            answers = []
            for e in equals:
                txt = e.strip()[1:].strip()
                if txt:
                    answers.append({"text": txt, "case_sensitive": False})
            if answers:
                return {
                    "id": "", "version": 1, "type": "short_answer",
                    "points": int(opts.default_points or 1),
                    "topic": opts.topic or "Imported", "difficulty": opts.difficulty,
                    "tags": coerce_list_tags(opts.tags), "stem": stem,
                    "answers": answers, "author": opts.author, "license": opts.license,
                }

    choices = []
    correct_count = 0
    for tok in re.split(r"(?<!\\)~", body):
        tok = tok.strip()
        if not tok: continue
        score_m = re.match(r"^%(-?\d+(?:\.\d+)?)%\s*", tok)
        if tok.startswith("="):
            txt = tok[1:].strip()
            choices.append({"text": txt, "correct": True})
            correct_count += 1
        elif score_m:
            txt = tok[score_m.end():].strip()
            choices.append({"text": txt})
        else:
            choices.append({"text": tok})
    if choices:
        return {
            "id": "", "version": 1,
            "type": "mcq_multi" if correct_count > 1 else "mcq_one",
            "points": int(opts.default_points or 1),
            "topic": opts.topic or "Imported", "difficulty": opts.difficulty,
            "tags": coerce_list_tags(opts.tags), "stem": stem,
            "choices": choices, "author": opts.author, "license": opts.license,
            **({"shuffle_choices": bool(opts.shuffle_choices)} if opts.shuffle_choices is not None else {}),
        }
    return None

def import_items(path: Path, opts) -> List[Dict]:
    text = path.read_text(encoding="utf-8")
    blocks = split_gift_questions(text)
    items: List[Dict] = []
    for b in blocks:
        it = parse_gift(b, opts)
        if it:
            items.append(it)
    return items
