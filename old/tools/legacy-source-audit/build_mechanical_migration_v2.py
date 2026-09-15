from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import build_mechanical_migration as base

ORIGINAL_CONVERT = base.convert


def choose_best(items: list[dict[str, Any]]) -> dict[str, Any]:
    kind_rank = {
        "json-bank": 0,
        "json-item": 1,
        "yaml-item": 2,
        "yaml-list": 3,
        "typst-bank": 4,
        "markdown-keyed": 5,
        "gift": 6,
        "typst-mc-call": 7,
        "typst-tf-call": 7,
        "typst-numbered-sa": 8,
        "markdown-q": 9,
        "markdown-matching": 9,
        "markdown-numbered": 10,
        "markdown-heading": 10,
        "typst-bare-question": 11,
    }
    return min(
        items,
        key=lambda item: (
            0 if item.get("branch") == base.CURRENT_BRANCH else 1,
            kind_rank.get(str(item.get("source_kind")), 20),
            str(item.get("path") or ""),
            int(item.get("ordinal") or 0),
        ),
    )


def convert(
    best: dict[str, Any],
    occurrences: list[dict[str, Any]],
    owner: str,
    topic: str,
):
    item, problem = ORIGINAL_CONVERT(best, occurrences, owner, topic)
    if item is None:
        return None, problem

    raw = dict(best.get("raw") or {})
    hints = raw.get("legacy_ref_hints") or []
    if hints:
        source = dict(item.get("source") or {})
        existing = list(source.get("reference_hints") or [])
        for hint in hints:
            text = str(hint).strip()
            if text and text not in existing:
                existing.append(text)
        source["reference_hints"] = existing
        item["source"] = source

    metadata = dict(item.get("metadata") or {})
    verification = dict(metadata.get("verification") or {})
    verification.setdefault("status", "pending")
    metadata["verification"] = verification
    item["metadata"] = metadata
    return item, problem


def main() -> int:
    base.choose_best = choose_best
    base.convert = convert
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
