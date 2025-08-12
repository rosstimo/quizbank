#!/usr/bin/env python3
"""
Validate YAML quiz items against JSON Schema.

Usage:
  python tools/validate_items.py [FILES or GLOBS...]
Examples:
  python tools/validate_items.py qbank/**/*.yaml
  python tools/validate_items.py qbank/algebra/q-*.yaml
If no args are given, defaults to qbank/**/*.yaml
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

try:
    import yaml  # PyYAML
except ImportError:
    sys.stderr.write("Missing dependency: PyYAML\n")
    sys.exit(2)

try:
    from jsonschema import Draft202012Validator
except ImportError:
    sys.stderr.write("Missing dependency: jsonschema\n")
    sys.exit(2)


SCHEMA_PATH = Path("schemas/quiz-item.schema.json")


def load_schema(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.stderr.write(f"Schema not found: {path}\n")
        sys.exit(2)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"Schema JSON is invalid: {path}\n{e}\n")
        sys.exit(2)


def load_yaml(path: Path):
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise ValueError(f"YAML parse error: {e}") from e
    if isinstance(data, list):
        # If someone used multi-doc YAML by mistake, fail loudly.
        raise ValueError("Top-level YAML must be a single object, not a list.")
    return data


def validate_file(path: Path, validator: Draft202012Validator) -> int:
    try:
        data = load_yaml(path)
    except Exception as e:
        print(f"{path}: FAIL")
        print(f"  - (root): {e}")
        return 1

    errors = sorted(validator.iter_errors(data), key=lambda e: (list(e.path), e.message))
    if not errors:
        print(f"{path}: OK")
        return 0

    print(f"{path}: FAIL")
    for err in errors:
        loc = ".".join(str(p) for p in err.path) or "(root)"
        print(f"  - {loc}: {err.message}")
    return 1


def expand_globs(patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    for pat in patterns:
        # Use Path.glob to allow ** recursive patterns
        if any(ch in pat for ch in "*?[]"):
            files.extend(Path().glob(pat))
        else:
            files.append(Path(pat))
    # Deduplicate and keep only files ending with .yml/.yaml
    uniq = []
    seen = set()
    for p in files:
        if p.is_dir():
            continue
        if p.suffix.lower() not in {".yaml", ".yml"}:
            continue
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            uniq.append(p)
    return uniq


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(argument_default=None)
    parser.add_argument("paths", nargs="*", help="YAML files or globs to validate")
    parser.add_argument(
        "--schema",
        default=str(SCHEMA_PATH),
        help=f"Path to schema JSON (default: {SCHEMA_PATH})",
    )
    args = parser.parse_args(argv)

    schema = load_schema(Path(args.schema))
    validator = Draft202012Validator(schema)

    patterns = args.paths or ["qbank/**/*.yaml"]
    files = expand_globs(patterns)
    if not files:
        print("No YAML files found to validate.")
        return 1

    failures = 0
    for f in files:
        failures += validate_file(f, validator)

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
