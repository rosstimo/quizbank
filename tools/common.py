#!/usr/bin/env python3
"""
Common helpers for Quizbank tools.

Single source of truth for converting our Quiz Markdown Profile (QMP)
to other formats via Pandoc.

Dependencies:
  - pandoc must be installed and on PATH

Typical use:
  from tools.common import qmp_to_html, qmp_to_latex

  html = qmp_to_html(stem)    # for QTI (Canvas)
  tex  = qmp_to_latex(stem)   # for LaTeX builder
"""

from __future__ import annotations
import functools
import shutil
import subprocess
from typing import List, Optional

# Pandoc reader: GitHub-flavored Markdown + $...$ / $$...$$ math
PANDOC_FROM = "gfm+tex_math_dollars"

def have_pandoc() -> bool:
    """Return True if pandoc is available on PATH."""
    return shutil.which("pandoc") is not None

class PandocError(RuntimeError):
    pass

def _run_pandoc(text: str, to_fmt: str, extra_args: Optional[List[str]] = None) -> str:
    if not have_pandoc():
        raise PandocError("pandoc not found in PATH")
    args = ["pandoc", "-f", PANDOC_FROM, "-t", to_fmt]
    if extra_args:
        args.extend(extra_args)
    try:
        proc = subprocess.run(
            args,
            input=text.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise PandocError(f"pandoc failed ({to_fmt}): {e.stderr.decode('utf-8', 'ignore')}") from e
    return proc.stdout.decode("utf-8")

@functools.lru_cache(maxsize=512)
def _convert_cached(text: str, to_fmt: str, extra_key: str) -> str:
    extra = extra_key.split("\x1f") if extra_key else None
    return _run_pandoc(text, to_fmt, extra)

def pandoc_convert(text: str, to_fmt: str, extra_args: Optional[List[str]] = None) -> str:
    """
    Low-level converter. Prefer qmp_to_html / qmp_to_latex helpers below.
    Caches by (text, to_fmt, extra_args).
    """
    extra_key = "\x1f".join(extra_args) if extra_args else ""
    return _convert_cached(text, to_fmt, extra_key)

def qmp_to_html(text: str) -> str:
    """
    Convert QMP -> HTML suitable for Canvas/QTI.
    Uses --mathjax so TeX math renders on platforms with MathJax enabled (Canvas does).
    """
    return pandoc_convert(text, "html", ["--mathjax"])

def qmp_to_latex(text: str) -> str:
    """Convert QMP -> LaTeX for paper exports."""
    return pandoc_convert(text, "latex")

def qmp_to_plain(text: str) -> str:
    """Convert QMP -> plain text (rare, but handy for logs or titles)."""
    return pandoc_convert(text, "plain")
