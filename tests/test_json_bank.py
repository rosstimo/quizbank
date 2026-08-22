from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from qbank import paper
from qbank.bank import Bank, BankError, validate_data
from qbank.cli import main
from qbank.migrate import migrate_legacy
from tools.build_qti import build_item_mcq_multi
from tools.validate_items import lint_qmp_string


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "banks" / "example.bank.json"


def example_data() -> dict:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def test_example_bank_validates() -> None:
    assert validate_data(example_data()) == []
    bank = Bank.load(EXAMPLE)
    assert len(bank.questions) == 7
    assert len(bank.assessments) == 2


def test_default_assessment_builds_without_an_id() -> None:
    bank = Bank.load(EXAMPLE)
    assessment, questions = bank.resolve(None)
    assert assessment["id"] == "quiz-example-001"
    assert [question["id"] for question in questions] == [
        "example.topic.001",
        "example.topic.002",
        "example.topic.003",
        "example.topic.004",
        "example.topic.005",
        "example.topic.006",
        "example.topic.007",
    ]


def test_pools_are_repeatable_and_respect_filters() -> None:
    bank = Bank.load(EXAMPLE)
    _, first = bank.resolve("quiz-example-random", seed=3375)
    _, second = bank.resolve("quiz-example-random", seed=3375)
    assert [question["id"] for question in first] == [
        question["id"] for question in second
    ]
    assert len(first) == 4
    assert sum("example.programming" in question["category_ids"] for question in first) == 1


def test_semantic_validation_reports_bad_references_and_duplicates() -> None:
    data = example_data()
    data["questions"].append(copy.deepcopy(data["questions"][0]))
    data["assessments"][0]["items"].append("missing.question")
    messages = [str(problem) for problem in validate_data(data)]
    assert any("duplicate question id: example.topic.001" in message for message in messages)
    assert any("unknown question: missing.question" in message for message in messages)


def test_pool_reports_when_too_few_questions_match() -> None:
    bank = Bank.load(EXAMPLE)
    bank.assessments_by_id["quiz-example-random"]["pools"][0]["pick"] = 99
    with pytest.raises(BankError, match="only 5 match"):
        bank.resolve("quiz-example-random")


def test_qmp_html_lint_ignores_inline_code() -> None:
    assert lint_qmp_string("A private `List<SensorSample>` owns the samples.") == []


def test_qmp_html_lint_still_rejects_raw_html() -> None:
    assert "contains raw HTML tags (not allowed in QMP)" in lint_qmp_string(
        "Do not use <strong>raw HTML</strong>."
    )


def test_native_paper_numeric_response_is_a_real_blank() -> None:
    markdown = paper._question_markdown(
        1,
        {
            "type": "numeric",
            "points": 1,
            "stem": "What voltage is measured?",
            "unit": "V",
        },
    )
    assert "Answer: numeric" not in markdown
    assert "______________________________ V" in markdown


def test_native_paper_renderer_keeps_ordinary_questions_together() -> None:
    renderer = (ROOT / "paper" / "renderers.typ").read_text(encoding="utf-8")
    assert "breakable: false" in renderer
    controls = (ROOT / "paper" / "inc.typ").read_text(encoding="utf-8")
    assert "pagebreak_every_mc = 5" in controls
    assert "pagebreak_every_cr = 1" in controls


def test_native_paper_starts_each_nonempty_section_on_new_page(monkeypatch) -> None:
    monkeypatch.setattr(paper.build_typst, "md_to_typst", lambda text: text)
    source = paper.build_paper_typst(
        {"id": "layout-check", "title": "Layout Check"},
        [
            {"type": "true_false", "points": 1, "stem": "First statement", "answer": True},
            {
                "type": "mcq_one",
                "points": 1,
                "stem": "Second question",
                "choices": [
                    {"text": "A", "correct": True},
                    {"text": "B"},
                ],
            },
        ],
        include_key=False,
    )
    assert source.count("#pagebreak()") == 1
    assert source.index("True / False") < source.index("#pagebreak()")
    assert source.index("#pagebreak()") < source.index("Multiple Choice Questions")


def test_native_paper_points_and_true_false_layout(monkeypatch) -> None:
    monkeypatch.setattr(paper.build_typst, "md_to_typst", lambda text: text)
    items = [
        {"type": "true_false", "points": 1, "stem": "Timer0 is 8-bit.", "answer": True},
        {"type": "true_false", "points": 1, "stem": "Timer1 is 16-bit.", "answer": True},
    ]
    with_points = paper.build_paper_typst(
        {"id": "points-check", "title": "Points Check"},
        items,
        include_key=False,
    )
    without_points = paper.build_paper_typst(
        {"id": "points-check", "title": "Points Check"},
        items,
        include_key=False,
        show_points=False,
    )
    assert "True / False (1 pt each)" in with_points
    assert "(1 pt)" not in with_points
    assert "**1.) T\u2002/\u2002F** Timer0 is 8-bit." in with_points
    assert "True / False (1 pt each)" not in without_points
    assert "True / False" in without_points


def test_native_paper_mc_choices_are_plain_lines_without_bullets() -> None:
    markdown = paper._question_markdown(
        1,
        {
            "type": "mcq_one",
            "points": 1,
            "stem": "Choose one.",
            "choices": [
                {"text": "Alpha", "correct": True},
                {"text": "Beta"},
            ],
        },
    )
    assert "\n- A. Alpha" not in markdown
    assert "A. Alpha  \nB. Beta" in markdown


def test_compose_runs_quizbank_from_mounted_workspace() -> None:
    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    assert 'working_dir: /workspace' in compose
    assert 'entrypoint: ["python", "-m", "qbank.cli"]' in compose
    assert 'PYTHONPATH: /workspace' in compose


def test_markdown_build_uses_json_bank(tmp_path: Path) -> None:
    result = main(
        [
            "build",
            "quiz-example-001",
            "--bank",
            str(EXAMPLE),
            "--format",
            "markdown",
            "--output-dir",
            str(tmp_path),
        ]
    )
    assert result == 0
    output = tmp_path / "quiz-example-001" / "quiz-example-001.md"
    content = output.read_text(encoding="utf-8")
    assert "# Sample Quiz: Basics" in content
    assert "```c" in content
    assert "## Answer Key" in content


def test_migrate_combines_yaml_items_and_quizzes(tmp_path: Path) -> None:
    items = tmp_path / "items"
    quizzes = tmp_path / "quizzes"
    items.mkdir()
    quizzes.mkdir()
    (items / "one.yaml").write_text(
        """id: test.item.001
version: 1
type: true_false
points: 1
topic: Timers > Timer2
stem: Timer2 has a postscaler.
answer: true
author: Tim Rossiter
license: CC-BY-4.0
""",
        encoding="utf-8",
    )
    (quizzes / "check.yaml").write_text(
        """id: test.quiz.001
title: Timer2 Check
items:
  - test.item.001
""",
        encoding="utf-8",
    )

    data = migrate_legacy(items, quizzes, "test.bank", "Test Bank")
    assert data["questions"][0]["category_ids"] == ["timers.timer2"]
    assert data["categories"][-1]["parent"] == "timers"
    assert data["assessments"][0]["items"] == ["test.item.001"]
    assert validate_data(data) == []


def test_repository_legacy_bank_migrates_cleanly() -> None:
    data = migrate_legacy(
        ROOT / "qbank",
        ROOT / "quizzes",
        "legacy.quizbank",
        "Legacy Quizbank",
    )
    assert len(data["questions"]) == 16
    assert {question["type"] for question in data["questions"]}.issuperset(
        {"fill_blank", "matching", "ordering", "essay"}
    )
    assert validate_data(data) == []


def test_qti_multiple_select_has_one_condition_per_correct_choice() -> None:
    item = example_data()["questions"][1]
    qti = build_item_mcq_multi(item)
    assert len(qti.element.findall(".//varequal")) == 4
