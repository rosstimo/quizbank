# tests/test_importers_from_samples.py
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, List

import jsonschema
import pytest
import yaml

# Repo root on sys.path so "tools.*" imports work when running pytest at repo root.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Where sample inputs must live:
SAMPLES_ROOT = REPO_ROOT / "samples"

from tools.importers.registry import discover_importers
from tools.importers.common import assign_ids, write_item_yaml

ALLOWED_TYPES = {"mcq_one", "mcq_multi", "true_false", "numeric", "short_answer"}

def load_schema() -> Dict:
    schema_path = REPO_ROOT / "schemas" / "quiz-item.schema.json"
    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)

SCHEMA = load_schema()
VALIDATOR = jsonschema.Draft7Validator(SCHEMA)

def validate_item(item: Dict):
    errors = sorted(VALIDATOR.iter_errors(item), key=lambda e: list(e.path))
    if errors:
        msg = "\n".join(f"- {e.message} @ path {list(e.path)}" for e in errors)
        raise AssertionError(f"Schema validation failed:\n{msg}")

def assert_type_specific(item: Dict):
    t = item.get("type")
    assert t in ALLOWED_TYPES, f"Unsupported type: {t}"
    if t in {"mcq_one", "mcq_multi"}:
        choices = item.get("choices") or []
        assert isinstance(choices, list) and len(choices) >= 2
        corr = [i for i, c in enumerate(choices) if c.get("correct") is True]
        if t == "mcq_one":
            assert len(corr) == 1, "mcq_one must have exactly one correct choice"
        else:
            assert len(corr) >= 1, "mcq_multi must have at least one correct choice"
    elif t == "true_false":
        assert isinstance(item.get("answer"), bool)
    elif t == "numeric":
        assert isinstance(item.get("answer"), (int, float))
        if "tolerance" in item:
            assert isinstance(item["tolerance"], (int, float))
    elif t == "short_answer":
        answers = item.get("answers") or []
        assert isinstance(answers, list) and len(answers) >= 1

def sample_path_for(format_name: str) -> Path:
    """
    Enforce one sample file per importer:
      samples/<format>/<file>
    Accept any file in the directory.
    """
    fmt_dir = SAMPLES_ROOT / format_name
    assert fmt_dir.is_dir(), f"Missing sample dir for '{format_name}': {fmt_dir}"
    candidates = [p for p in fmt_dir.iterdir() if p.is_file()]
    assert len(candidates) >= 1, (
        f"Expected at least one sample file for '{format_name}' under {fmt_dir}. Found: {[p.name for p in candidates]}"
    )
    return candidates[0]  # Return the first file found

def fake_opts(**overrides):
    class O: pass
    o = O()
    o.default_points = overrides.get("default_points", 1)
    o.topic = overrides.get("topic", "Imported")
    o.difficulty = overrides.get("difficulty", "easy")
    o.tags = overrides.get("tags", "")
    o.author = overrides.get("author", "Test")
    o.license = overrides.get("license", "CC-BY-4.0")
    o.shuffle_choices = overrides.get("shuffle_choices", None)
    o.csv_map = overrides.get("csv_map", None)
    return o

def test_all_importers_have_samples():
    importers = discover_importers()
    assert importers, "No importers discovered in tools/importers/formats/"
    missing = []
    extras = []

    # Check each importer has a sample
    for fmt in sorted(importers.keys()):
        try:
            _ = sample_path_for(fmt)
        except AssertionError as e:
            missing.append(str(e))

    # Also flag any sample folders without a matching importer (helps cleanup)
    if SAMPLES_ROOT.exists():
        for d in sorted([p for p in SAMPLES_ROOT.iterdir() if p.is_dir()]):
            fmt = d.name
            if fmt not in importers:
                extras.append(f"Sample dir exists with no importer: {d}")

    err = ""
    if missing:
        err += "\n".join(missing)
    if extras:
        err += ("\n" if err else "") + "\n".join(extras)
    if err:
        pytest.fail(err)

@pytest.mark.parametrize("fmt", sorted(discover_importers().keys()))
def test_importer_parses_sample_and_validates(tmp_path: Path, fmt: str):
    importers = discover_importers()
    importer = importers.get(fmt)
    assert callable(importer), f"Importer for '{fmt}' is not callable"

    src = sample_path_for(fmt)  # enforced by previous test
    opts = fake_opts()

    items = importer(src, opts)
    assert items, f"{fmt} importer returned no items for {src.name}"

    # Normalize and validate
    assign_ids(items, id_prefix=f"test.{fmt}", start_index=1)
    outdir = tmp_path / "out"
    outdir.mkdir()

    for idx, it in enumerate(items, 1):
        validate_item(it)
        assert_type_specific(it)
        assert isinstance(it.get("points"), int)
        p = write_item_yaml(it, outdir, idx)
        loaded = yaml.safe_load(p.read_text(encoding="utf-8"))
        validate_item(loaded)
        assert loaded["id"] == it["id"]

@pytest.mark.parametrize("fmt", ["csv"])
def test_debug_mcq_multi(tmp_path: Path, fmt: str):
    importers = discover_importers()
    importer = importers.get(fmt)
    assert callable(importer), f"Importer for '{fmt}' is not callable"

    src = sample_path_for(fmt)  # enforced by previous test
    opts = fake_opts()

    items = importer(src, opts)
    assert items, f"{fmt} importer returned no items for {src.name}"

    # Print the generated items for debugging
    for idx, item in enumerate(items, 1):
        print(f"Item {idx}: {item}")

    # Validate the first mcq_multi item to reproduce the error
    for item in items:
        if item["type"] == "mcq_multi":
            validate_item(item)

@pytest.mark.parametrize("fmt", ["csv"])
def test_debug_short_answer(tmp_path: Path, fmt: str):
    importers = discover_importers()
    importer = importers.get(fmt)
    assert callable(importer), f"Importer for '{fmt}' is not callable"

    src = sample_path_for(fmt)  # enforced by previous test
    opts = fake_opts()

    items = importer(src, opts)
    assert items, f"{fmt} importer returned no items for {src.name}"

    # Print the generated items for debugging
    for idx, item in enumerate(items, 1):
        print(f"Item {idx}: {item}")

    # Validate the first short_answer item to reproduce the error
    for item in items:
        if item["type"] == "short_answer":
            validate_item(item)
