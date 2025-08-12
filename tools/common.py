# tools/common.py
import subprocess, shutil

def pandoc_convert(text: str, from_fmt: str = "gfm+tex_math_dollars", to_fmt: str = "html") -> str:
    """Convert QMP -> desired format via Pandoc. Requires pandoc on PATH."""
    if not shutil.which("pandoc"):
        raise RuntimeError("pandoc not found in PATH")
    p = subprocess.run(
        ["pandoc", "-f", from_fmt, "-t", to_fmt, "--mathjax"],  # or --katex
        input=text.encode("utf-8"), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
    )
    return p.stdout.decode("utf-8")
