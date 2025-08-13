#!/usr/bin/env python3
"""
Bulk-import questions in common formats into 1-item-per-file YAML for Quizbank.

Usage:
  python tools/import_items.py --format aiken --input aiken.txt \
      --outdir qbank/example-topic --id-prefix example.topic

Supported formats are discovered from tools/importers/formats/*.py
"""
from __future__ import annotations
import argparse
from pathlib import Path
from typing import Optional, List
from tools.importers.registry import discover_importers
from tools.importers.common import assign_ids, ensure_dir, write_item_yaml
import yaml

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(argument_default=None)
    ap.add_argument("--format", required=True, help="Input format name (auto-discovered)")
    ap.add_argument("--input", required=True, help="Input file path")
    ap.add_argument("--outdir", default="qbank/imported", help="Output directory for YAML items")
    ap.add_argument("--id-prefix", default="imported.item", help="ID prefix if source lacks stable IDs")
    ap.add_argument("--start-index", type=int, default=1, help="Starting index for generated IDs")
    ap.add_argument("--default-points", type=int, default=1)
    ap.add_argument("--topic", default="Imported")
    ap.add_argument("--difficulty", default="easy")
    ap.add_argument("--tags", default="", help="Comma-separated default tags")
    ap.add_argument("--author", default="Unknown")
    ap.add_argument("--license", default="CC-BY-4.0")
    ap.add_argument("--shuffle-choices", type=int, choices=[0,1], default=None, help="Set shuffle_choices for MCQ")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--csv-map", nargs="*", help="CSV mapping like stem=Stem,choiceA=A,choiceB=B,...")
    args = ap.parse_args(argv)

    importer_map = discover_importers()
    if not importer_map:
        raise SystemExit("No importers discovered under tools/importers/formats/")
    if args.format not in importer_map:
        raise SystemExit(f"Unknown format '{args.format}'. Known: {', '.join(sorted(importer_map))}")

    in_path = Path(args.input)
    if not in_path.exists():
        raise SystemExit(f"Input not found: {in_path}")

    importer = importer_map[args.format]
    items = importer(in_path, args)

    if not items:
        print("No items parsed.")
        return 1

    assign_ids(items, args.id_prefix, args.start_index)

    outdir = Path(args.outdir)
    ensure_dir(outdir)
    wrote = 0
    for idx, it in enumerate(items, args.start_index):
        if args.dry_run:
            print(yaml.safe_dump(it, sort_keys=False, allow_unicode=True))
        else:
            p = write_item_yaml(it, outdir, idx)
            wrote += 1
            print(f"Wrote {p}")

    print(f"Imported {wrote} item(s) to {outdir}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
