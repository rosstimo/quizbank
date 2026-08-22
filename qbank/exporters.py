from __future__ import annotations

import copy
import shutil
import subprocess
import sysconfig
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools import build_latex, build_qti, build_typst

from qbank import paper
from qbank.bank import BankError


ALL_FORMATS = ("markdown", "typst", "latex", "qti", "pdf")


@dataclass(frozen=True)
class BuildResult:
    path: Path
    detail: str = ""


def _write(path: Path, content: str) -> BuildResult:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return BuildResult(path)


def _paper_template_dir() -> Path:
    candidates = (
        Path(__file__).resolve().parents[1] / "paper",
        Path.cwd() / "paper",
        Path(sysconfig.get_path("data")) / "share" / "quizbank" / "paper",
    )
    for candidate in candidates:
        if (candidate / "inc.typ").is_file() and (candidate / "renderers.typ").is_file():
            return candidate
    raise BankError("Quizbank's paper Typst templates are missing from the installation")


def _copy_paper_templates(output_dir: Path) -> None:
    source = _paper_template_dir()
    shutil.copyfile(source / "inc.typ", output_dir / "inc.typ")
    shutil.copyfile(source / "renderers.typ", output_dir / "renderers.typ")


def _qti_package(
    assessment: dict[str, Any], items: list[dict[str, Any]], output: Path
) -> BuildResult:
    qti_items: list[build_qti.QtiItem] = []
    skipped: list[str] = []
    builders = {
        "mcq_one": build_qti.build_item_mcq_one,
        "mcq_multi": build_qti.build_item_mcq_multi,
        "true_false": build_qti.build_item_true_false,
        "numeric": build_qti.build_item_numeric,
        "short_answer": build_qti.build_item_short_answer,
    }
    for original in items:
        item = copy.deepcopy(original)
        item_type = item.get("type")
        if item_type == "fill_blank":
            item["type"] = "short_answer"
            item["stem"] = item.get("stem", "").replace("{{blank}}", "__________")
            item_type = "short_answer"
        builder = builders.get(str(item_type))
        if not builder:
            skipped.append(item["id"])
            continue
        qti_items.append(builder(item))
    if not qti_items:
        raise BankError("No selected questions can be represented in QTI 1.2")

    output.parent.mkdir(parents=True, exist_ok=True)
    assessment_xml = build_qti.build_assessment_xml(assessment["title"], qti_items)
    manifest_xml = build_qti.build_manifest_xml()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("assessment.xml", assessment_xml)
        archive.writestr("imsmanifest.xml", manifest_xml)
    detail = f"{len(qti_items)} item(s)"
    if skipped:
        detail += f"; skipped unsupported: {', '.join(skipped)}"
    return BuildResult(output, detail)


def build_outputs(
    assessment: dict[str, Any],
    items: list[dict[str, Any]],
    output_root: Path,
    formats: set[str],
    include_key: bool,
    show_points: bool = True,
) -> list[BuildResult]:
    assessment_id = assessment["id"]
    output_dir = output_root / assessment_id
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[BuildResult] = []

    md_text = build_typst.build_markdown_doc(
        assessment, items, no_key=not include_key, inline_solutions=False
    )
    if "markdown" in formats:
        results.append(_write(output_dir / f"{assessment_id}.md", md_text))

    typst_path = output_dir / f"{assessment_id}.typ"
    if formats.intersection({"typst", "pdf"}):
        _copy_paper_templates(output_dir)
        typst_text = paper.build_paper_typst(
            assessment,
            items,
            include_key=include_key,
            show_points=show_points,
        )
        result = _write(typst_path, typst_text)
        if "typst" in formats:
            results.append(result)

    if "latex" in formats:
        tex_text = build_latex.build_tex(assessment, items, include_key=include_key)
        results.append(_write(output_dir / f"{assessment_id}.tex", tex_text))

    if "qti" in formats:
        results.append(
            _qti_package(
                assessment, items, output_dir / f"{assessment_id}-qti12.zip"
            )
        )

    if "pdf" in formats:
        typst = shutil.which("typst")
        if not typst:
            raise BankError(
                "Typst is unavailable. Run Quizbank through ./quizbank so the container "
                "provides it, or request a source format instead."
            )
        pdf_path = output_dir / f"{assessment_id}.pdf"
        try:
            subprocess.run(
                [typst, "compile", str(typst_path), str(pdf_path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            raise BankError(f"Typst could not compile the PDF:\n{exc.stderr}") from exc
        results.append(BuildResult(pdf_path))

    return results


def dependency_versions() -> list[tuple[str, str]]:
    versions: list[tuple[str, str]] = []
    for command in ("python3", "pandoc", "typst", "xelatex"):
        executable = shutil.which(command)
        if not executable:
            versions.append((command, "missing"))
            continue
        proc = subprocess.run(
            [executable, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        first_line = proc.stdout.splitlines()[0] if proc.stdout else "available"
        versions.append((command, first_line))
    return versions
