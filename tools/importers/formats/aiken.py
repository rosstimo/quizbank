from __future__ import annotations
from pathlib import Path
import re
from typing import List, Dict
from tools.importers.common import coerce_list_tags, to_bool, choice_letter

FORMAT_NAME = "aiken"

AIKEN_CH_RE = re.compile(r"^[A-Z]\.\s+(?P<t>.+)$")
AIKEN_ANS_RE = re.compile(r"^ANSWER\s*:\s*([A-Z])\s*$", re.IGNORECASE)

def import_items(path: Path, opts) -> List[Dict]:
    text = path.read_text(encoding="utf-8")
    lines = [l.rstrip("\n") for l in text.splitlines()]
    out: List[Dict] = []
    i = 0
    while i < len(lines):
        while i < len(lines) and not lines[i].strip():
            i += 1
        if i >= len(lines): break
        q = lines[i].strip()
        i += 1
        choices: List[Dict] = []
        while i < len(lines) and AIKEN_CH_RE.match(lines[i]):
            m = AIKEN_CH_RE.match(lines[i])
            choices.append({"text": m.group("t").strip()})
            i += 1
        if i >= len(lines) or not AIKEN_ANS_RE.match(lines[i]):
            while i < len(lines) and lines[i].strip():
                i += 1
            continue
        ansL = AIKEN_ANS_RE.match(lines[i]).group(1).upper()
        i += 1

        item = {
            "id": "",
            "version": 1,
            "type": "mcq_one",
            "points": int(opts.default_points or 1),
            "topic": opts.topic or "Imported",
            "difficulty": opts.difficulty,
            "tags": coerce_list_tags(opts.tags),
            "stem": q,
            "choices": choices,
            "author": opts.author,
            "license": opts.license,
        }
        idx = ord(ansL) - ord("A")
        if 0 <= idx < len(choices):
            item["choices"][idx]["correct"] = True
        if opts.shuffle_choices is not None:
            item["shuffle_choices"] = bool(opts.shuffle_choices)
        out.append(item)
    return out
