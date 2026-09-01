from __future__ import annotations

import shutil
from pathlib import Path

from qbank.cli import main


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "banks" / "example.bank.json"


def test_reference_export_links_each_question_to_its_key(tmp_path: Path) -> None:
    result = main(
        [
            "reference",
            "--bank",
            str(EXAMPLE),
            "--output-dir",
            str(tmp_path),
        ]
    )
    assert result == 0

    questions_path = tmp_path / "example-bank.md"
    key_path = tmp_path / "keys" / "example-bank-key.md"
    assert questions_path.is_file()
    assert key_path.is_file()

    questions = questions_path.read_text(encoding="utf-8")
    key = key_path.read_text(encoding="utf-8")

    assert '<a id="q-example-topic-001"></a>' in questions
    assert (
        "[Answer and explanation](keys/example-bank-key.md#key-example-topic-001)"
        in questions
    )

    assert '<a id="key-example-topic-001"></a>' in key
    assert "[Back to this question](../example-bank.md#q-example-topic-001)" in key
    assert (
        "In most programming languages, what is the common term for a value like `true` or `false`?"
        in key
    )
    assert "**Answer:** B. Boolean" in key
    assert "**Why:** The correct answer is **Boolean**." in key


def test_reference_export_keeps_printable_markdown_separate(tmp_path: Path) -> None:
    reference_dir = tmp_path / "reference"
    build_dir = tmp_path / "build"

    assert (
        main(
            [
                "reference",
                "--bank",
                str(EXAMPLE),
                "--output-dir",
                str(reference_dir),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "build",
                "quiz-example-001",
                "--bank",
                str(EXAMPLE),
                "--format",
                "markdown",
                "--output-dir",
                str(build_dir),
            ]
        )
        == 0
    )

    reference = (reference_dir / "example-bank.md").read_text(encoding="utf-8")
    printable = (
        build_dir / "quiz-example-001" / "quiz-example-001.md"
    ).read_text(encoding="utf-8")

    assert "Answer and explanation" in reference
    assert "## Answer Key" not in reference
    assert "## Answer Key" in printable


def test_external_bank_env_maps_host_argument_to_mounted_file(
    tmp_path: Path, monkeypatch
) -> None:
    mounted_bank = tmp_path / "mounted.bank.json"
    shutil.copy2(EXAMPLE, mounted_bank)
    monkeypatch.setenv("QUIZBANK_EXTERNAL_BANK", str(mounted_bank))

    result = main(["validate", "--bank", "/host/path/not-visible-in-container.bank.json"])
    assert result == 0


def test_external_output_env_maps_requested_output_directory(
    tmp_path: Path, monkeypatch
) -> None:
    mounted_output = tmp_path / "mounted-output"
    monkeypatch.setenv("QUIZBANK_EXTERNAL_OUTPUT", str(mounted_output))

    result = main(
        [
            "reference",
            "--bank",
            str(EXAMPLE),
            "--output-dir",
            "/host/output/not-visible-in-container",
        ]
    )
    assert result == 0
    assert (mounted_output / "example-bank.md").is_file()
    assert (mounted_output / "keys" / "example-bank-key.md").is_file()
