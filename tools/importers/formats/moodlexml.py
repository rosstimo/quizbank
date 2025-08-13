from __future__ import annotations
from pathlib import Path
from typing import List, Dict
from xml.etree import ElementTree as ET
from tools.importers.common import html_to_qmp, coerce_list_tags

FORMAT_NAME = "moodlexml"

def _strip_html(s: str) -> str:
    import re
    return re.sub(r"<[^>]+>", "", s or "")

def import_items(path: Path, opts) -> List[Dict]:
    xml = ET.fromstring(path.read_text(encoding="utf-8"))
    items: List[Dict] = []
    for q in xml.findall(".//question"):
        qtype = q.get("type", "").strip()
        name = q.findtext("name/text") or ""
        title = _strip_html(name).strip()
        stem_html_el = q.find("questiontext/text")
        stem_md = html_to_qmp(stem_html_el.text or "") if stem_html_el is not None else ""
        pts = int(opts.default_points or 1)
        base = {
            "id": "", "version": 1, "points": pts,
            "topic": opts.topic or "Imported", "difficulty": opts.difficulty,
            "tags": coerce_list_tags(opts.tags),
            "stem": stem_md, "author": opts.author, "license": opts.license,
        }

        if qtype == "multichoice":
            choices: List[Dict] = []
            single = (q.get("single", "") == "true") or (q.findtext("single") or "").strip() == "true"
            for ans in q.findall("answer"):
                txt_md = html_to_qmp((ans.findtext("text") or ""))
                frac = float(ans.get("fraction", ans.findtext("fraction") or "0"))
                correct = frac > 0
                choices.append({"text": txt_md, **({"correct": True} if correct else {})})
            if choices:
                items.append({**base, "type": "mcq_one" if single or sum(1 for c in choices if c.get("correct")) <= 1 else "mcq_multi",
                              "choices": choices})

        elif qtype == "truefalse":
            ans_true = False
            for ans in q.findall("answer"):
                frac = float(ans.get("fraction", ans.findtext("fraction") or "0"))
                txt = (ans.findtext("text") or "").strip().lower()
                if frac > 0:
                    ans_true = (txt == "true")
                    break
            items.append({**base, "type": "true_false", "answer": ans_true})

        elif qtype == "shortanswer":
            answers = []
            for ans in q.findall("answer"):
                txt = (ans.findtext("text") or "").strip()
                if txt:
                    case = (ans.get("casesensitive", ans.findtext("casesensitive") or "0").strip() == "1")
                    frac = float(ans.get("fraction", ans.findtext("fraction") or "1"))
                    answers.append({"text": txt, "case_sensitive": case, "score": frac/100 if frac > 1 else frac})
            if answers:
                items.append({**base, "type": "short_answer", "answers": answers})

        elif qtype == "numerical":
            best = None
            for ans in q.findall("answer"):
                txt = (ans.findtext("text") or "").strip()
                tol = ans.findtext("tolerance")
                frac = float(ans.get("fraction", ans.findtext("fraction") or "1"))
                try:
                    val = float(txt)
                except ValueError:
                    continue
                entry = {"val": val, "tol": float(tol) if tol else None, "frac": frac}
                if not best or entry["frac"] > best["frac"]:
                    best = entry
            if best:
                item = {**base, "type": "numeric", "answer": best["val"]}
                if best["tol"] is not None:
                    item["tolerance"] = best["tol"]
                items.append(item)

        else:
            continue
    return items
