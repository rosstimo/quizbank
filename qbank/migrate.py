from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

from qbank.bank import BankError


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if len(slug) < 3:
        slug = f"cat-{slug or 'other'}"
    return slug


def _load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise BankError(f"Could not parse {path}: {exc}") from exc


def _categories_for_topic(
    topic: str, categories: dict[str, dict[str, Any]]
) -> list[str]:
    parts = [part.strip() for part in topic.split(">") if part.strip()]
    parent: str | None = None
    path_parts: list[str] = []
    for part in parts:
        path_parts.append(_slug(part))
        category_id = ".".join(path_parts)
        entry: dict[str, Any] = {"id": category_id, "title": part}
        if parent:
            entry["parent"] = parent
        categories.setdefault(category_id, entry)
        parent = category_id
    return [parent] if parent else []


def migrate_legacy(
    items_dir: Path,
    quizzes_dir: Path,
    bank_id: str,
    title: str,
    description: str = "",
) -> dict[str, Any]:
    item_paths = sorted(items_dir.rglob("*.yaml")) + sorted(items_dir.rglob("*.yml"))
    if not item_paths:
        raise BankError(f"No YAML questions found under {items_dir}")

    categories: dict[str, dict[str, Any]] = {}
    questions: list[dict[str, Any]] = []
    authors: set[str] = set()
    licenses: set[str] = set()
    for path in item_paths:
        question = _load_yaml(path)
        if not isinstance(question, dict):
            raise BankError(f"Question must be one YAML object: {path}")
        if question.get("type") == "fill_in_the_blank":
            legacy_blanks = question.pop("blanks", []) or []
            answers: list[dict[str, Any]] = []
            for blank in legacy_blanks:
                if not isinstance(blank, dict):
                    continue
                for text in [blank.get("correct"), *(blank.get("alternatives", []) or [])]:
                    if text:
                        answers.append({"text": str(text), "case_sensitive": True})
            question["type"] = "fill_blank"
            question["stem"] = str(question.get("stem", "")).replace("____", "{{blank}}")
            question["answers"] = answers
            question.setdefault("metadata", {})["legacy_blanks"] = legacy_blanks
        topic = question.get("topic")
        if isinstance(topic, str) and topic.strip():
            question["category_ids"] = _categories_for_topic(topic, categories)
        if question.get("author"):
            authors.add(str(question["author"]))
        if question.get("license"):
            licenses.add(str(question["license"]))
        questions.append(question)

    assessments: list[dict[str, Any]] = []
    for path in sorted(quizzes_dir.glob("*.y*ml")) if quizzes_dir.exists() else []:
        quiz = _load_yaml(path)
        if not isinstance(quiz, dict):
            raise BankError(f"Assessment must be one YAML object: {path}")
        assessment = {
            key: value
            for key, value in quiz.items()
            if key
            in {
                "id",
                "title",
                "description",
                "instructions",
                "version",
                "items",
                "shuffle_questions",
                "time_limit_min",
                "attempts",
            }
        }
        if quiz.get("pick") is not None:
            assessment.setdefault("metadata", {})["legacy_pick"] = quiz["pick"]
        assessments.append(assessment)

    info: dict[str, Any] = {"id": bank_id, "title": title}
    if description:
        info["description"] = description
    if authors:
        info["authors"] = sorted(authors)
    if len(licenses) == 1:
        info["license"] = next(iter(licenses))

    return {
        "$schema": "../schemas/bank.schema.json",
        "format_version": 1,
        "bank": info,
        "categories": list(categories.values()),
        "questions": questions,
        "assessments": assessments,
        "metadata": {
            "migrated_from": {
                "items": str(items_dir),
                "assessments": str(quizzes_dir),
            }
        },
    }


def write_json(path: Path, data: dict[str, Any], force: bool = False) -> None:
    if path.exists() and not force:
        raise BankError(f"Refusing to overwrite {path}; pass --force to replace it")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
