from __future__ import annotations

import copy
import json
import random
import sysconfig
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from tools.validate_items import lint_item


def _schema_dir() -> Path:
    candidates = (
        Path(__file__).resolve().parents[1] / "schemas",
        Path.cwd() / "schemas",
        Path(sysconfig.get_path("data")) / "share" / "quizbank" / "schemas",
    )
    for candidate in candidates:
        if (candidate / "bank.schema.json").is_file():
            return candidate
    raise RuntimeError("Quizbank's JSON Schema files are missing from the installation")


SCHEMA_DIR = _schema_dir()
DEFAULT_BANK_SCHEMA = SCHEMA_DIR / "bank.schema.json"
DEFAULT_ITEM_SCHEMA = SCHEMA_DIR / "quiz-item.schema.json"


class BankError(RuntimeError):
    """A bank could not be loaded or used."""


@dataclass(frozen=True)
class Problem:
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


class BankValidationError(BankError):
    def __init__(self, path: Path, problems: list[Problem]):
        self.path = path
        self.problems = problems
        super().__init__(f"{path} has {len(problems)} validation problem(s)")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BankError(f"Bank not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BankError(
            f"Invalid JSON in {path} at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(data, dict):
        raise BankError(f"Bank must be a JSON object: {path}")
    return data


def _schema_problems(data: dict[str, Any]) -> list[Problem]:
    bank_schema = _read_json(DEFAULT_BANK_SCHEMA)
    item_schema = _read_json(DEFAULT_ITEM_SCHEMA)
    registry = Registry().with_resource(
        item_schema["$id"], Resource.from_contents(item_schema)
    )
    validator = Draft202012Validator(bank_schema, registry=registry)
    problems: list[Problem] = []
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        location = ".".join(str(part) for part in error.absolute_path) or "(root)"
        problems.append(Problem(location, error.message))
    return problems


def _duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def _semantic_problems(data: dict[str, Any], lint_level: str) -> list[Problem]:
    problems: list[Problem] = []
    categories = data.get("categories", [])
    questions = data.get("questions", [])
    assessments = data.get("assessments", [])

    category_ids = [entry.get("id") for entry in categories if isinstance(entry, dict)]
    question_ids = [entry.get("id") for entry in questions if isinstance(entry, dict)]
    assessment_ids = [entry.get("id") for entry in assessments if isinstance(entry, dict)]

    for label, values in (
        ("category", category_ids),
        ("question", question_ids),
        ("assessment", assessment_ids),
    ):
        for duplicate in sorted(_duplicates(v for v in values if isinstance(v, str))):
            problems.append(Problem(f"{label}s", f"duplicate {label} id: {duplicate}"))

    category_set = {value for value in category_ids if isinstance(value, str)}
    question_set = {value for value in question_ids if isinstance(value, str)}
    parents = {
        entry["id"]: entry.get("parent")
        for entry in categories
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }
    for category_id, parent in parents.items():
        if parent and parent not in category_set:
            problems.append(
                Problem(f"categories.{category_id}.parent", f"unknown category: {parent}")
            )
        visited: set[str] = set()
        current: str | None = category_id
        while current:
            if current in visited:
                problems.append(
                    Problem(f"categories.{category_id}.parent", "category parent cycle")
                )
                break
            visited.add(current)
            current = parents.get(current)

    for question in questions:
        if not isinstance(question, dict):
            continue
        qid = question.get("id", "?")
        for category_id in question.get("category_ids", []) or []:
            if category_id not in category_set:
                problems.append(
                    Problem(
                        f"questions.{qid}.category_ids", f"unknown category: {category_id}"
                    )
                )
        if lint_level != "off":
            for field, message in lint_item(question):
                prefix = "warning: " if lint_level == "warn" else ""
                problems.append(Problem(f"questions.{qid}.{field}", prefix + message))

    for assessment in assessments:
        if not isinstance(assessment, dict):
            continue
        aid = assessment.get("id", "?")
        for entry in assessment.get("items", []) or []:
            qid = entry if isinstance(entry, str) else entry.get("id")
            if qid not in question_set:
                problems.append(
                    Problem(f"assessments.{aid}.items", f"unknown question: {qid}")
                )
        for index, pool in enumerate(assessment.get("pools", []) or []):
            where = pool.get("where", {}) if isinstance(pool, dict) else {}
            for category_id in where.get("category_ids", []) or []:
                if category_id not in category_set:
                    problems.append(
                        Problem(
                            f"assessments.{aid}.pools.{index}.where.category_ids",
                            f"unknown category: {category_id}",
                        )
                    )
    default_assessment = (data.get("metadata") or {}).get("default_assessment")
    if default_assessment and default_assessment not in set(assessment_ids):
        problems.append(
            Problem(
                "metadata.default_assessment",
                f"unknown assessment: {default_assessment}",
            )
        )
    return problems


def validate_data(data: dict[str, Any], lint_level: str = "error") -> list[Problem]:
    if lint_level not in {"off", "warn", "error"}:
        raise ValueError(f"Unknown lint level: {lint_level}")
    schema = _schema_problems(data)
    if schema:
        return schema
    semantic = _semantic_problems(data, lint_level)
    if lint_level == "warn":
        return [problem for problem in semantic if not problem.message.startswith("warning: ")]
    return semantic


def validate_path(path: Path, lint_level: str = "error") -> list[Problem]:
    return validate_data(_read_json(path), lint_level=lint_level)


def _matches(question: dict[str, Any], where: dict[str, Any]) -> bool:
    if where.get("types") and question.get("type") not in where["types"]:
        return False
    if where.get("difficulty") and question.get("difficulty") not in where["difficulty"]:
        return False
    if where.get("category_ids"):
        if not set(where["category_ids"]).intersection(question.get("category_ids", [])):
            return False
    if where.get("tags") and not set(where["tags"]).issubset(question.get("tags", [])):
        return False
    if where.get("outcomes") and not set(where["outcomes"]).issubset(
        question.get("outcomes", [])
    ):
        return False
    return True


class Bank:
    def __init__(self, path: Path, data: dict[str, Any]):
        self.path = path
        self.data = data
        self.info = data["bank"]
        self.categories = data["categories"]
        self.questions = data["questions"]
        self.assessments = data["assessments"]
        self.questions_by_id = {question["id"]: question for question in self.questions}
        self.assessments_by_id = {
            assessment["id"]: assessment for assessment in self.assessments
        }
        self.categories_by_id = {
            category["id"]: category for category in self.categories
        }

    @classmethod
    def load(cls, path: Path | str, lint_level: str = "error") -> "Bank":
        bank_path = Path(path)
        data = _read_json(bank_path)
        problems = validate_data(data, lint_level=lint_level)
        if problems:
            raise BankValidationError(bank_path, problems)
        return cls(bank_path, data)

    def assessment(self, assessment_id: str | None) -> dict[str, Any]:
        if not assessment_id:
            default_id = (self.data.get("metadata") or {}).get("default_assessment")
            if default_id:
                assessment_id = str(default_id)
        if assessment_id:
            try:
                return self.assessments_by_id[assessment_id]
            except KeyError as exc:
                known = ", ".join(sorted(self.assessments_by_id)) or "none"
                raise BankError(
                    f"Assessment '{assessment_id}' not found. Available: {known}"
                ) from exc
        if len(self.assessments) == 1:
            return self.assessments[0]
        if not self.assessments:
            raise BankError("This bank has no assessments")
        known = ", ".join(sorted(self.assessments_by_id))
        raise BankError(f"Choose an assessment: {known}")

    def resolve(
        self, assessment_id: str | None, seed: int = 42
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        assessment = copy.deepcopy(self.assessment(assessment_id))
        rng = random.Random(seed)
        selected: list[dict[str, Any]] = []
        selected_ids: set[str] = set()

        def add(qid: str, points: float | int | None = None) -> None:
            if qid in selected_ids:
                return
            question = copy.deepcopy(self.questions_by_id[qid])
            if points is not None:
                question["points"] = points
            if not question.get("topic") and question.get("category_ids"):
                category = self.categories_by_id.get(question["category_ids"][0])
                if category:
                    question["topic"] = category["title"]
            selected.append(question)
            selected_ids.add(qid)

        for entry in assessment.get("items", []) or []:
            if isinstance(entry, str):
                add(entry)
            else:
                add(entry["id"], entry.get("points"))

        for pool_index, pool in enumerate(assessment.get("pools", []) or []):
            candidates = sorted(
                (
                    question
                    for question in self.questions
                    if question["id"] not in selected_ids
                    and _matches(question, pool.get("where", {}))
                ),
                key=lambda question: question["id"],
            )
            pick = pool["pick"]
            if pick > len(candidates):
                pool_name = pool.get("id", str(pool_index + 1))
                raise BankError(
                    f"Pool '{pool_name}' requests {pick} question(s), but only "
                    f"{len(candidates)} match"
                )
            for question in rng.sample(candidates, pick):
                add(question["id"], pool.get("points"))

        if assessment.get("shuffle_questions"):
            rng.shuffle(selected)
        if not selected:
            raise BankError(f"Assessment '{assessment['id']}' selects no questions")
        return assessment, selected
