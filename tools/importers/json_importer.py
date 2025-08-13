from __future__ import annotations
from pathlib import Path
import json
from typing import List, Dict
from tools.importers.common import coerce_list_tags

FORMAT_NAME = "json"

def import_items(path: Path, opts) -> List[Dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data if isinstance(data, list) else [data]
    out: List[Dict] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        item = {
            "id": it.get("id", ""),
            "version": int(it.get("version", 1)),
            "type": it.get("type", "mcq_one"),
            "points": int(it.get("points", opts.default_points or 1)),
            "topic": it.get("topic") or opts.topic or "Imported",
            "difficulty": it.get("difficulty", opts.difficulty),
            "tags": coerce_list_tags(it.get("tags", [])),
            "stem": it.get("stem", ""),
            "author": it.get("author", opts.author),
            "license": it.get("license", opts.license),
        }
        for k in ["choices", "answer", "answers", "shuffle_choices", "feedback", "solution", "unit", "tolerance"]:
            if k in it:
                item[k] = it[k]
        out.append(item)
    return out
