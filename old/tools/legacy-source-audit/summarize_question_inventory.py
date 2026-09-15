from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def source_priority(item: dict[str, Any], current_branch: str) -> tuple[int, int, str, int]:
    branch = str(item.get("branch") or "")
    kind = str(item.get("source_kind") or "")
    path = str(item.get("path") or "")
    branch_rank = 0 if branch == current_branch else 1
    kind_rank = {
        "json-bank": 0,
        "json-item": 1,
        "yaml-item": 2,
        "yaml-list": 3,
        "typst-bank": 4,
        "gift": 5,
        "typst-mc-call": 6,
        "typst-tf-call": 6,
        "typst-numbered-sa": 7,
        "markdown-q": 8,
        "markdown-matching": 8,
        "markdown-numbered": 9,
        "markdown-heading": 9,
        "typst-bare-question": 10,
        "typst-bare-question": 10,
    }.get(kind, 20)
    return (branch_rank, kind_rank, path, int(item.get("ordinal") or 0))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("inventory")
    parser.add_argument("--current-branch", default="curriculum/f26-alignment-cleanup")
    args = parser.parse_args()

    inventory_path = Path(args.inventory)
    out_dir = inventory_path.parent
    data = json.loads(inventory_path.read_text(encoding="utf-8"))
    items = [item for item in data.get("extracted_items", []) if item.get("signature")]

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        groups[str(item["signature"])].append(item)

    signature_lines = []
    rows = []
    for signature in sorted(groups):
        occurrences = groups[signature]
        best = min(occurrences, key=lambda item: source_priority(item, args.current_branch))
        signature_lines.append(signature)
        rows.append({
            "signature": signature,
            "type": best.get("type") or "",
            "stem": str(best.get("stem") or "").replace("\t", " ").replace("\n", " "),
            "best_branch": best.get("branch") or "",
            "best_path": best.get("path") or "",
            "best_source_id": best.get("source_id") or "",
            "best_source_kind": best.get("source_kind") or "",
            "occurrences": len(occurrences),
        })

    (out_dir / "unique-signatures.txt").write_text("\n".join(signature_lines) + "\n", encoding="utf-8")
    with (out_dir / "unique-records.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["signature"], delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} unique signatures from {len(items)} extracted occurrences.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
