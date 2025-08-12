#!/usr/bin/env python3
"""
Build a QTI 1.2 package (zip) for Canvas from a quiz assembly YAML and your YAML item bank.

Supported item types (for now):
  - mcq_one     (single correct)
  - true_false

Unsupported types will be skipped with a warning.

Usage:
  python tools/build_qti.py quizzes/quiz-example.yaml --out build/qti/quiz-example-qti12.zip

Options:
  --bank DIR    Root of the question bank (default: qbank)
  --title STR   Override quiz title (defaults to quiz.title or quiz.id)
  --seed N      Random seed used when 'pick' < number of items (default: 42)
"""

from __future__ import annotations

import argparse
import random
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
import xml.etree.ElementTree as ET

import yaml


# -------------------- YAML helpers --------------------

def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def find_item_files(bank_dir: Path) -> List[Path]:
    return [p for p in bank_dir.rglob("*.y*ml") if p.is_file()]

def index_items_by_id(bank_dir: Path) -> Dict[str, Path]:
    index: Dict[str, Path] = {}
    for p in find_item_files(bank_dir):
        try:
            data = load_yaml(p)
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        qid = data.get("id")
        if isinstance(qid, str) and qid not in index:
            index[qid] = p
    return index

def load_items_by_ids(ids_and_overrides: List[Any], id_to_path: Dict[str, Path]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for entry in ids_and_overrides:
        if isinstance(entry, str):
            qid, override_points = entry, None
        elif isinstance(entry, dict) and "id" in entry:
            qid = entry["id"]
            override_points = entry.get("points")
        else:
            raise ValueError(f"Unsupported item entry in quiz file: {entry!r}")

        p = id_to_path.get(qid)
        if not p:
            raise FileNotFoundError(f"Question ID not found in bank: {qid}")
        data = load_yaml(p)
        if override_points is not None:
            data["points"] = override_points
        items.append(data)
    return items

def sample_items(items: List[Dict[str, Any]], pick: int | None, seed: int) -> List[Dict[str, Any]]:
    if pick is None or pick >= len(items):
        return items
    rng = random.Random(seed)
    return rng.sample(items, k=pick)


# -------------------- QTI 1.2 building --------------------

def mattext(parent: ET.Element, text: str, texttype: str = "text/plain") -> ET.Element:
    material = ET.SubElement(parent, "material")
    m = ET.SubElement(material, "mattext", {"texttype": texttype})
    # QTI 1.2 expects entities handled; ElementTree escapes by default.
    m.text = text if text is not None else ""
    return m

def choice_ident(idx: int) -> str:
    # A, B, C...
    return chr(ord("A") + idx)

@dataclass
class QtiItem:
    ident: str
    title: str
    element: ET.Element

def build_item_mcq_one(item: Dict[str, Any]) -> QtiItem:
    qid = item["id"]
    title = item.get("topic") or qid
    points = float(item.get("points", 1))
    stem = item.get("stem", "")
    shuffle = "Yes" if item.get("shuffle_choices", True) else "No"
    choices = item.get("choices", [])

    # Find correct index
    correct_idx = None
    for i, c in enumerate(choices):
        if c.get("correct") is True:
            correct_idx = i
            break
    if correct_idx is None:
        raise ValueError(f"mcq_one item has no correct choice: {qid}")

    # <questestinterop><assessment><section><item>...
    item_el = ET.Element("item", {"ident": qid, "title": title})

    presentation = ET.SubElement(item_el, "presentation")
    mattext(presentation, stem, "text/plain")
    response_lid = ET.SubElement(presentation, "response_lid", {"ident": "response1", "rcardinality": "Single"})
    render_choice = ET.SubElement(response_lid, "render_choice", {"shuffle": shuffle})

    for i, c in enumerate(choices):
        ident = choice_ident(i)
        rl = ET.SubElement(render_choice, "response_label", {"ident": ident})
        mattext(rl, c.get("text", ""), "text/plain")

    # Scoring
    resprocessing = ET.SubElement(item_el, "resprocessing")
    outcomes = ET.SubElement(resprocessing, "outcomes")
    ET.SubElement(outcomes, "decvar", {"varname": "SCORE", "vartype": "Decimal", "minvalue": "0", "maxvalue": str(points)})
    # correct branch
    respcondition = ET.SubElement(resprocessing, "respcondition", {"continue": "No"})
    conditionvar = ET.SubElement(respcondition, "conditionvar")
    ET.SubElement(conditionvar, "varequal", {"respident": "response1"}).text = choice_ident(correct_idx)
    ET.SubElement(respcondition, "setvar", {"varname": "SCORE", "action": "Set"}).text = str(points)

    return QtiItem(ident=qid, title=title, element=item_el)

def build_item_true_false(item: Dict[str, Any]) -> QtiItem:
    qid = item["id"]
    title = item.get("topic") or qid
    points = float(item.get("points", 1))
    stem = item.get("stem", "")
    answer_true = bool(item.get("answer", False))
    shuffle = "No"  # keep order True/False

    item_el = ET.Element("item", {"ident": qid, "title": title})

    presentation = ET.SubElement(item_el, "presentation")
    mattext(presentation, stem, "text/plain")
    response_lid = ET.SubElement(presentation, "response_lid", {"ident": "response1", "rcardinality": "Single"})
    render_choice = ET.SubElement(response_lid, "render_choice", {"shuffle": shuffle})

    for ident, text in [("A", "True"), ("B", "False")]:
        rl = ET.SubElement(render_choice, "response_label", {"ident": ident})
        mattext(rl, text, "text/plain")

    correct_ident = "A" if answer_true else "B"

    resprocessing = ET.SubElement(item_el, "resprocessing")
    outcomes = ET.SubElement(resprocessing, "outcomes")
    ET.SubElement(outcomes, "decvar", {"varname": "SCORE", "vartype": "Decimal", "minvalue": "0", "maxvalue": str(points)})

    respcondition = ET.SubElement(resprocessing, "respcondition", {"continue": "No"})
    conditionvar = ET.SubElement(respcondition, "conditionvar")
    ET.SubElement(conditionvar, "varequal", {"respident": "response1"}).text = correct_ident
    ET.SubElement(respcondition, "setvar", {"varname": "SCORE", "action": "Set"}).text = str(points)

    return QtiItem(ident=qid, title=title, element=item_el)

def build_assessment_xml(quiz_title: str, qti_items: List[QtiItem]) -> bytes:
    # QTI 1.2 single assessment with one section containing all items
    questestinterop = ET.Element("questestinterop")
    assessment = ET.SubElement(questestinterop, "assessment", {"ident": "ASSESSMENT", "title": quiz_title})
    section = ET.SubElement(assessment, "section", {"ident": "root_section"})
    for q in qti_items:
        section.append(q.element)

    # Serialize with XML declaration
    xml_bytes = ET.tostring(questestinterop, encoding="utf-8", xml_declaration=True)
    return xml_bytes

def build_manifest_xml() -> bytes:
    # Minimal IMS Content Packaging manifest. Canvas tolerates minimal manifests for QTI imports.
    manifest = ET.Element("manifest", {"identifier": "MANIFEST", "version": "1.1.4",
                                       "xmlns": "http://www.imsproject.org/xsd/imscp_rootv1p1p2",
                                       "xmlns:imsmd": "http://www.imsglobal.org/xsd/imsmd_rootv1p2p1",
                                       "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                                       "xsi:schemaLocation": "http://www.imsproject.org/xsd/imscp_rootv1p1p2 "
                                                             "imscp_rootv1p1p2.xsd "
                                                             "http://www.imsglobal.org/xsd/imsmd_rootv1p2p1 "
                                                             "imsmd_rootv1p2p1.xsd"})
    # Minimal organizations/resources pointing to assessment.xml
    ET.SubElement(manifest, "organizations")
    resources = ET.SubElement(manifest, "resources")
    res = ET.SubElement(resources, "resource", {"identifier": "RES-ASSMT", "type": "imsqti_xmlv1p2", "href": "assessment.xml"})
    ET.SubElement(res, "file", {"href": "assessment.xml"})
    return ET.tostring(manifest, encoding="utf-8", xml_declaration=True)


# -------------------- Orchestration --------------------

def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(argument_default=None)
    ap.add_argument("quiz_file", help="Path to quiz assembly YAML")
    ap.add_argument("--bank", default="qbank", help="Root directory of the question bank")
    ap.add_argument("--title", default=None, help="Override quiz title")
    ap.add_argument("--seed", type=int, default=42, help="Random seed when sampling with 'pick'")
    ap.add_argument("--out", required=True, help="Output path for QTI zip (e.g., build/qti/quiz-qti12.zip)")
    args = ap.parse_args(argv)

    quiz_path = Path(args.quiz_file)
    if not quiz_path.exists():
        sys.stderr.write(f"Quiz file not found: {quiz_path}\n")
        return 2

    quiz = load_yaml(quiz_path)
    if not isinstance(quiz, dict):
        sys.stderr.write("Quiz YAML must be a single mapping\n")
        return 2

    bank_dir = Path(args.bank)
    id_index = index_items_by_id(bank_dir)

    raw_items = quiz.get("items", [])
    if not raw_items:
        sys.stderr.write("Quiz has no items\n")
        return 2

    items = load_items_by_ids(raw_items, id_index)
    pick = quiz.get("pick")
    items = sample_items(items, pick, args.seed)

    title = args.title or quiz.get("title") or quiz.get("id") or "Assessment"

    qti_items: List[QtiItem] = []
    skipped = 0
    for it in items:
        t = it.get("type")
        try:
            if t == "mcq_one":
                qti_items.append(build_item_mcq_one(it))
            elif t == "true_false":
                qti_items.append(build_item_true_false(it))
            else:
                skipped += 1
                sys.stderr.write(f"[skip] Unsupported type for QTI 1.2: {t} (id={it.get('id')})\n")
        except Exception as e:
            sys.stderr.write(f"[skip] Could not build item {it.get('id')}: {e}\n")
            skipped += 1

    if not qti_items:
        sys.stderr.write("No items could be exported to QTI 1.2\n")
        return 2

    assessment_xml = build_assessment_xml(title, qti_items)
    manifest_xml = build_manifest_xml()

    out_zip = Path(args.out)
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("assessment.xml", assessment_xml)
        z.writestr("imsmanifest.xml", manifest_xml)

    print(f"Wrote {out_zip} ({len(qti_items)} items, {skipped} skipped)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
