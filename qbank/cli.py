from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Sequence

from qbank import __version__
from qbank.bank import (
    Bank,
    BankError,
    BankValidationError,
    validate_data,
    validate_path,
)
from qbank.exporters import ALL_FORMATS, build_outputs, dependency_versions
from qbank.migrate import migrate_legacy, write_json
from qbank.reference import build_reference


def _discover_bank() -> Path:
    candidates = sorted(Path("banks").glob("*.bank.json"))
    if not candidates:
        candidates = sorted(Path("banks").glob("*.json"))
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise BankError(
            "No bank found under banks/. Create one with 'quizbank new' or pass --bank."
        )
    names = ", ".join(str(path) for path in candidates)
    raise BankError(f"More than one bank found; pass --bank. Available: {names}")


def _bank_path(value: str | None) -> Path:
    external = os.environ.get("QUIZBANK_EXTERNAL_BANK")
    if value and external:
        return Path(external)
    return Path(value) if value else _discover_bank()


def _output_path(value: str) -> Path:
    external = os.environ.get("QUIZBANK_EXTERNAL_OUTPUT")
    return Path(external) if external else Path(value)


def _print_validation_error(error: BankValidationError) -> None:
    print(f"FAIL {error.path}", file=sys.stderr)
    for problem in error.problems:
        print(f"  - {problem}", file=sys.stderr)


def _overview(bank: Bank) -> None:
    print(f"{bank.info['title']} ({bank.info['id']})")
    print(
        f"{len(bank.questions)} questions, {len(bank.categories)} categories, "
        f"{len(bank.assessments)} assessments"
    )
    if bank.assessments:
        print("\nAssessments:")
        for assessment in bank.assessments:
            explicit = len(assessment.get("items", []) or [])
            pools = len(assessment.get("pools", []) or [])
            parts = [f"{explicit} fixed"] if explicit else []
            if pools:
                parts.append(f"{pools} pool(s)")
            summary = ", ".join(parts) or "empty"
            print(f"  {assessment['id']:<28} {summary:<18} {assessment['title']}")


def _parse_formats(values: list[str]) -> set[str]:
    requested = {
        part.strip().lower()
        for value in values
        for part in value.split(",")
        if part.strip()
    }
    if "all" in requested:
        return set(ALL_FORMATS)
    unknown = requested.difference(ALL_FORMATS)
    if unknown:
        raise BankError(
            f"Unknown format(s): {', '.join(sorted(unknown))}. "
            f"Choose from: {', '.join(ALL_FORMATS)}, all"
        )
    return requested


def _starter(bank_id: str, title: str) -> dict:
    return {
        "$schema": "../schemas/bank.schema.json",
        "format_version": 1,
        "bank": {"id": bank_id, "title": title, "language": "en-US"},
        "categories": [],
        "questions": [],
        "assessments": [],
        "metadata": {},
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quizbank",
        description="Author once in a JSON bank, then build paper, Canvas, and reference outputs.",
    )
    parser.add_argument("--version", action="version", version=f"quizbank {__version__}")
    sub = parser.add_subparsers(dest="command")

    list_parser = sub.add_parser("list", help="Show the contents of a bank")
    list_parser.add_argument("--bank")

    validate_parser = sub.add_parser("validate", help="Validate a JSON bank")
    validate_parser.add_argument("--bank")
    validate_parser.add_argument("--lint-level", choices=("off", "warn", "error"), default="error")

    build_parser = sub.add_parser("build", help="Build an assessment")
    build_parser.add_argument("assessment", nargs="?", help="Assessment id; optional when the bank contains one")
    build_parser.add_argument("--bank")
    build_parser.add_argument(
        "--format",
        action="append",
        default=[],
        help="markdown, typst, latex, qti, pdf, or all (default: all)",
    )
    build_parser.add_argument("--output-dir", default="build")
    build_parser.add_argument("--seed", type=int, default=42, help="Seed for question pools and shuffling")
    build_parser.add_argument("--no-key", action="store_true", help="Omit the answer key from paper outputs")

    reference_parser = sub.add_parser(
        "reference",
        help="Build GitHub-friendly practice questions and a linked answer key from the whole bank",
    )
    reference_parser.add_argument("--bank")
    reference_parser.add_argument("--output-dir", default="reference")

    new_parser = sub.add_parser("new", help="Create an empty JSON bank")
    new_parser.add_argument("output", nargs="?", default="banks/new.bank.json")
    new_parser.add_argument("--id", required=True, dest="bank_id")
    new_parser.add_argument("--title", required=True)
    new_parser.add_argument("--force", action="store_true")

    migrate_parser = sub.add_parser("migrate", help="Combine legacy YAML questions and quizzes into one JSON bank")
    migrate_parser.add_argument("--items", default="qbank")
    migrate_parser.add_argument("--quizzes", default="quizzes")
    migrate_parser.add_argument("--output", default="banks/migrated.bank.json")
    migrate_parser.add_argument("--id", required=True, dest="bank_id")
    migrate_parser.add_argument("--title", required=True)
    migrate_parser.add_argument("--description", default="")
    migrate_parser.add_argument("--force", action="store_true")

    sub.add_parser("doctor", help="Show the isolated export toolchain")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        if args.command is None:
            try:
                _overview(Bank.load(_discover_bank()))
            except BankError:
                parser.print_help()
            return 0

        if args.command == "list":
            _overview(Bank.load(_bank_path(args.bank)))
            return 0

        if args.command == "validate":
            path = _bank_path(args.bank)
            problems = validate_path(path, lint_level=args.lint_level)
            if problems:
                print(f"FAIL {path}", file=sys.stderr)
                for problem in problems:
                    print(f"  - {problem}", file=sys.stderr)
                return 1
            bank = Bank.load(path, lint_level="off")
            print(
                f"OK {path}: {len(bank.questions)} questions, "
                f"{len(bank.assessments)} assessments"
            )
            return 0

        if args.command == "build":
            bank = Bank.load(_bank_path(args.bank))
            assessment, items = bank.resolve(args.assessment, seed=args.seed)
            formats = _parse_formats(args.format or ["all"])
            results = build_outputs(
                assessment,
                items,
                _output_path(args.output_dir),
                formats,
                include_key=not args.no_key,
            )
            print(
                f"Built {assessment['title']} from {len(items)} question(s), seed {args.seed}:"
            )
            for result in results:
                detail = f" ({result.detail})" if result.detail else ""
                print(f"  {result.path}{detail}")
            return 0

        if args.command == "reference":
            bank = Bank.load(_bank_path(args.bank))
            output_dir = _output_path(args.output_dir)
            results = build_reference(bank, output_dir)
            print(f"Built GitHub reference from {len(bank.questions)} question(s):")
            for path in results:
                print(f"  {path}")
            return 0

        if args.command == "new":
            output = Path(args.output)
            data = _starter(args.bank_id, args.title)
            problems = validate_data(data)
            if problems:
                raise BankValidationError(output, problems)
            write_json(output, data, force=args.force)
            print(f"Created {output}")
            return 0

        if args.command == "migrate":
            output = Path(args.output)
            data = migrate_legacy(
                Path(args.items),
                Path(args.quizzes),
                args.bank_id,
                args.title,
                args.description,
            )
            schema_path = Path("schemas/bank.schema.json").resolve()
            data["$schema"] = Path(
                os.path.relpath(schema_path, start=output.parent.resolve())
            ).as_posix()
            problems = validate_data(data)
            if problems:
                raise BankValidationError(output, problems)
            write_json(output, data, force=args.force)
            print(
                f"Migrated {len(data['questions'])} questions and "
                f"{len(data['assessments'])} assessments to {output}"
            )
            return 0

        if args.command == "doctor":
            print("Quizbank export toolchain:")
            for name, version in dependency_versions():
                print(f"  {name:<8} {version}")
            return 0

        parser.error(f"Unknown command: {args.command}")
    except BankValidationError as error:
        _print_validation_error(error)
        return 1
    except (BankError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Cancelled", file=sys.stderr)
        return 130
    return 0
