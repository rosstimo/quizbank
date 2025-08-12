#!/usr/bin/env python3
r"""
Validate YAML quiz items against JSON Schema and lint QMP (Quiz Markdown Profile).

QMP rules enforced (default: error):
  - Ban LaTeX wrappers: \( \) \[ \] \text{...}
  - Ban raw HTML tags: <tag ...>
  - Require balanced $ inline math and $$ display math (ignoring backticks)
  - Image paths in Markdown must be under qbank/media/ or media/

Usage:
  python tools/validate_items.py [FILES or GLOBS...]
Options:
  --schema PATH             Path to schema JSON (default: schemas/quiz-item.schema.json)
  --lint-level {off,warn,error}   Lint severity (default: error)

Examples:
  python tools/validate_items.py qbank/**/*.yaml
  python tools/validate_items.py --lint-level warn qbank/example-topic/*.yaml
"""

from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

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

# ---------------- Schema loading ----------------

def load_schema(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.stderr.write(f"Schema not found: {path}\n")
        sys.exit(2)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"Schema JSON is invalid: {path}\n{e}\n")
        sys.exit(2)

# ---------------- YAML loading ----------------

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
        raise ValueError("Top-level YAML must be a single object, not a list.")
    return data

# ---------------- QMP Lint ----------------

RE_LATEX_WRAPPERS = re.compile(r"(\\\(|\\\)|\\\[|\\\]|\\text\{)")
RE_HTML_TAG = re.compile(r"<[A-Za-z][^>]*>")  # crude but effective, avoids bare '<' comparisons
RE_CODE_FENCE = re.compile(r"```.*?```", flags=re.DOTALL)
RE_CODE_INLINE = re.compile(r"`[^`]*`")
RE_IMG = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")

def strip_code(text: str) -> str:
    """Remove fenced and inline code to avoid false positives when linting."""
    text = RE_CODE_FENCE.sub("", text)
    text = RE_CODE_INLINE.sub("", text)
    return text

def check_dollar_balance(text: str) -> Iterable[str]:
    """Ensure $ and $$ are balanced after removing code spans."""
    src = strip_code(text)
    # Count $$ pairs
    num_doubled = src.count("$$")
    if num_doubled % 2 != 0:
        yield "unbalanced $$ display-math delimiters"
    # Remove $$ so we can count single dollars
    src_no_dd = src.replace("$$", "")
    # Count single dollars not escaped
    singles = 0
    i = 0    # ensure i is defined
    for i, ch in enumerate(src_no_dd):
        if ch == "$":
            # consider escaped \$ as not a delimiter
            if i > 0 and src_no_dd[i-1] == "\\":
                continue
            singles += 1
    if singles % 2 != 0:
        yield "unbalanced $ inline-math delimiters"

def check_images(text: str) -> Iterable[str]:
    for m in RE_IMG.finditer(text):
        url = m.group(1).strip()
        if url.startswith("http://") or url.startswith("https://"):
            continue  # external allowed if you want; change policy if not
        if not (url.startswith("qbank/media/") or url.startswith("media/")):
            yield f"image path outside media folder: {url}"

def lint_qmp_string(s: str) -> List[str]:
    issues: List[str] = []
    if not s:
        return issues
    if RE_LATEX_WRAPPERS.search(s):
        issues.append("contains LaTeX wrappers (use $...$ or $$...$$, not \\( \\) \\[ \\] or \\text{...})")
    if RE_HTML_TAG.search(s):
        issues.append("contains raw HTML tags (not allowed in QMP)")
    issues.extend(check_dollar_balance(s))
    issues.extend(check_images(s))
    return issues

def iter_qmp_fields(item: Dict[str, Any]) -> Iterable[Tuple[str, str]]:
    """Yield (path, string) for all QMP text-bearing fields to lint."""
    # stem
    stem = item.get("stem")
    if isinstance(stem, str):
        yield ("stem", stem)
    # choices[].text
    for i, ch in enumerate(item.get("choices", []) or []):
        if isinstance(ch, dict) and isinstance(ch.get("text"), str):
            yield (f"choices[{i}].text", ch["text"])
        if isinstance(ch, dict) and isinstance(ch.get("rationale"), str):
            yield (f"choices[{i}].rationale", ch["rationale"])
    # feedback
    fb = item.get("feedback") or {}
    if isinstance(fb.get("correct"), str):
        yield ("feedback.correct", fb["correct"])
    if isinstance(fb.get("incorrect"), str):
        yield ("feedback.incorrect", fb["incorrect"])
    # solution
    if isinstance(item.get("solution"), str):
        yield ("solution", item["solution"])

def lint_item(item: Dict[str, Any]) -> List[Tuple[str, str]]:
    """Return list of (path, message) lint violations."""
    problems: List[Tuple[str, str]] = []
    for path, text in iter_qmp_fields(item):
        for msg in lint_qmp_string(text):
            problems.append((path, msg))
    return problems

# ---------------- Validation orchestration ----------------

def validate_file(path: Path, validator: Draft202012Validator, lint_level: str) -> int:
    try:
        data = load_yaml(path)
    except Exception as e:
        print(f"{path}: FAIL")
        print(f"  - (root): {e}")
        return 1

    errors = sorted(validator.iter_errors(data), key=lambda e: (list(e.path), e.message))
    if errors:
        print(f"{path}: FAIL")
        for err in errors:
            loc = ".".join(str(p) for p in err.path) or "(root)"
            print(f"  - {loc}: {err.message}")
        return 1

    # Lint QMP fields
    lint_issues = lint_item(data)
    if lint_issues:
        level = lint_level.lower()
        if level == "off":
            print(f"{path}: OK  (lint skipped)")
            return 0
        elif level == "warn":
            print(f"{path}: OK  (with {len(lint_issues)} lint warning{'s' if len(lint_issues)!=1 else ''})")
            for loc, msg in lint_issues:
                print(f"  ! {loc}: {msg}")
            return 0
        else:
            print(f"{path}: FAIL")
            for loc, msg in lint_issues:
                print(f"  - {loc}: {msg}")
            return 1

    print(f"{path}: OK")
    return 0

def expand_globs(patterns: List[str]) -> List[Path]:
    files: List[Path] = []
    for pat in patterns:
        if any(ch in pat for ch in "*?[]"):
            files.extend(Path().glob(pat))
        else:
            files.append(Path(pat))
    # Deduplicate and keep only files ending with .yml/.yaml
    uniq: List[Path] = []
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

def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(argument_default=None)
    parser.add_argument("paths", nargs="*", help="YAML files or globs to validate")
    parser.add_argument("--schema", default=str(SCHEMA_PATH), help=f"Path to schema JSON (default: {SCHEMA_PATH})")
    parser.add_argument("--lint-level", choices=["off", "warn", "error"], default="error", help="QMP lint severity")
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
        failures += validate_file(f, validator, args["lint_level"] if isinstance(args, dict) else args.lint_level)

    return 1 if failures else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
