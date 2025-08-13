from __future__ import annotations
import re
import subprocess
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

# ---------- Pandoc bridge ----------
def html_to_qmp(html: str) -> str:
    """HTML -> GitHub-Flavored Markdown + $...$ math via pandoc, else crude strip."""
    if not html:
        return ""
    pandoc = shutil.which("pandoc")
    if not pandoc:
        text = re.sub(r"<[^>]+>", "", html)
        return re.sub(r"\s+\n", "\n", text).strip()
    try:
        p = subprocess.run(
            ["pandoc", "-f", "html", "-t", "gfm+tex_math_dollars", "--wrap=none"],
            input=html.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError("pandoc HTML->Markdown failed:\n" + e.stderr.decode("utf-8", "ignore"))
    return p.stdout.decode("utf-8").strip()

# ---------- YAML block-scalar helper ----------
class LiteralStr(str): pass
def _repr_literal(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
yaml.add_representer(LiteralStr, _repr_literal)

def blockify(s: Optional[str]) -> Optional[LiteralStr]:
    if s is None:
        return None
    s = str(s)
    if "\n" in s:
        return LiteralStr(s.rstrip("\n"))
    return s

# ---------- Common utils ----------
def slugify(s: str, maxlen: int = 50) -> str:
    s = re.sub(r"\s+", "-", s.strip().lower())
    s = re.sub(r"[^a-z0-9\-]+", "", s)
    return s[:maxlen] or "item"

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def coerce_list_tags(s: Optional[str]) -> List[str]:
    if not s:
        return []
    if isinstance(s, list):
        return [slugify(str(x)) for x in s]
    return [slugify(x) for x in re.split(r"[,\s]+", str(s)) if x.strip()]

def to_bool(s: str) -> bool:
    return str(s).strip().lower() in {"1", "true", "t", "yes", "y"}

def parse_letters(s: str) -> List[str]:
    return [x.strip().upper() for x in re.split(r"[,\s]+", s or "") if x.strip()]

def choice_letter(i: int) -> str:
    return chr(ord("A") + i)

def write_item_yaml(item: Dict[str, Any], outdir: Path, index: int) -> Path:
    base = slugify(item.get("topic", "")) or slugify(item.get("id", "item"))
    fname = f"q-{base}-{index:03d}.yaml"
    p = outdir / fname
    for k in ["stem", "solution"]:
        if k in item and item[k] is not None:
            item[k] = blockify(item[k])
    fb = item.get("feedback")
    if isinstance(fb, dict):
        for fk in ["correct", "incorrect"]:
            if fk in fb and fb[fk] is not None:
                fb[fk] = blockify(fb[fk])
    with p.open("w", encoding="utf-8") as f:
        yaml.safe_dump(item, f, sort_keys=False, allow_unicode=True)
    return p

def assign_ids(items: List[Dict[str, Any]], id_prefix: str, start_index: int = 1) -> None:
    i = start_index
    for it in items:
        if not it.get("id"):
            it["id"] = f"{id_prefix}.{i:03d}"
            i += 1
        if "points" not in it or it["points"] is None:
            it["points"] = 1
        if "difficulty" not in it or not it["difficulty"]:
            it["difficulty"] = "easy"
        if "tags" not in it:
            it["tags"] = []
        if it.get("type") in {"mcq_one", "mcq_multi"} and "shuffle_choices" not in it:
            it["shuffle_choices"] = True
