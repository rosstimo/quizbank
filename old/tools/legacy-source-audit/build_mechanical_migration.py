from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

CURRENT_BRANCH = "curriculum/f26-alignment-cleanup"

COURSE_TOPICS: dict[str, list[tuple[str, list[str]]]] = {
    "rcet2265": [
        ("debugging", ["debug", "breakpoint", "step over", "step into", "watch window"]),
        ("git", ["git ", "repository", "commit", "staging", "working tree", "clone", "push", "pull", "branch"]),
        ("console-io", ["console.", "readline", "writeline", "console input", "console output"]),
        ("types", ["int ", "double", "string", "bool", "datatype", "data type", "parse", "convert", "cast"]),
        ("operators", ["operator", "increment", "decrement", "modulus", "remainder", "+=", "-=", "*=", "/="]),
        ("program-structure", ["main method", "namespace", "class ", "method", "top-level", "statement", "entry point"]),
    ],
    "rcet3371": [
        ("git", ["git ", "repository", "commit", "diff", "log", "reset", "restore", "revert", "branch", "merge", "staging"]),
        ("oop", ["object", "class", "constructor", "property", "encapsulation", "inheritance", "composition", "collection"]),
        ("program-organization", ["method", "separation of concerns", "refactor", "responsibility", "service", "model"]),
        ("binary-bitwise", ["binary", "bitwise", "mask", "shift", "xor", "packed", "byte"]),
        ("gui", ["form", "event handler", "control", "winforms", "gui"]),
        ("debugging", ["debug", "breakpoint", "exception", "step into", "step over"]),
    ],
    "rcet3373": [
        ("i2c", ["i2c", "i²c", "sda", "scl", "sspcon", "mssp", "ack", "start condition", "stop condition"]),
        ("eeprom", ["eeprom", "eecon", "eedat", "eeadr", "wren", "eeif", "0x55", "0xaa"]),
        ("serial-eusart", ["uart", "usart", "eusart", "baud", "spbrg", "txsta", "rcsta", "rs-232", "rs232", "max232", "spen", "cren"]),
        ("adc", ["adc", "a/d", "analog-to-digital", "adcon", "adresh", "adresl", "go/done", "vref", "acquisition time", "sample-and-hold"]),
        ("timers", ["timer0", "timer1", "timer2", "tmr0", "tmr1", "tmr2", "prescaler", "postscaler", "pr2"]),
        ("interrupts", ["interrupt", "retfie", "isr", "gie", "peie", "flag bit", "interrupt flag"]),
        ("timing-delays", ["delay", "instruction cycle", "fosc", "tcy", "decfsz", "nested loop", "nop", "cycle time"]),
        ("digital-io", ["portb", "porta", "portc", "tris", "ansel", "digital i/o", "digital io", "input pin", "output pin"]),
        ("pic-architecture", ["pic16", "w register", "status register", "bank", "rp0", "rp1", "program counter", "pcl", "stack", "reset vector", "file register", "instruction set", "literal and control"]),
        ("memory-systems", ["sram", "dram", "ram", "rom", "eprom", "flash memory", "memory cell", "memory array", "address bus", "data bus", "access time"]),
        ("oscillator-electrical", ["oscillator", "crystal", "load capacitance", "absolute maximum", "vih", "vil", "voh", "vol", "drive current", "device dissipation"]),
    ],
    "rcet3375": [
        ("lab-measurement", ["lab book", "lab notebook", "measured", "measurement", "oscilloscope", "frequency counter", "waveform", "pulse width", "duty cycle", "instrument setting"]),
        ("lab-bringup", ["mplab", "pickit", "project", "psect", "configuration bit", "bring-up", "bringup", "built project"]),
        ("lab-wiring-loading", ["wiring", "breadboard", "load", "loading", "current calculation", "logic-level", "short circuit", "electrically acceptable"]),
        ("lab-io", ["matrix keypad", "dip switch", "dot matrix", "assigned load", "portb counter"]),
    ],
}

THEORY_MARKERS = tuple(word for topic, words in COURSE_TOPICS["rcet3373"] for word in words)
LAB_MARKERS = tuple(word for topic, words in COURSE_TOPICS["rcet3375"] for word in words)


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def topic_for(course: str, stem: str, path: str) -> str:
    haystack = norm(stem + " " + path)
    for topic, words in COURSE_TOPICS[course]:
        if any(word in haystack for word in words):
            return topic
    return "other"


def target_owner(source_course: str, stem: str, path: str, kind: str) -> str:
    if source_course != "rcet3375":
        return source_course
    lower_path = path.lower()
    current_lab = lower_path.startswith("f26/quizbanks/rcet3375-") and kind == "json-bank"
    haystack = norm(stem + " " + path)
    if current_lab or any(marker in haystack for marker in LAB_MARKERS):
        return "rcet3375"
    if any(marker in haystack for marker in THEORY_MARKERS):
        return "rcet3373"
    if "/quizzes/" in lower_path or "quiz_modular_typst" in lower_path:
        return "rcet3373"
    return "rcet3375"


def choose_best(items: list[dict[str, Any]]) -> dict[str, Any]:
    kind_rank = {
        "json-bank": 0, "json-item": 1, "yaml-item": 2, "yaml-list": 3,
        "typst-bank": 4, "gift": 5, "typst-mc-call": 6, "typst-tf-call": 6,
        "typst-numbered-sa": 7, "markdown-q": 8, "markdown-matching": 8,
        "markdown-numbered": 9, "markdown-heading": 9, "typst-bare-question": 10,
    }
    return min(items, key=lambda i: (
        0 if i.get("branch") == CURRENT_BRANCH else 1,
        kind_rank.get(str(i.get("source_kind")), 20),
        str(i.get("path") or ""),
        int(i.get("ordinal") or 0),
    ))


def stable_id(course: str, topic: str, signature: str) -> str:
    return f"{course}.{topic}.{signature[:10]}"


def provenance(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    seen = set()
    for item in sorted(items, key=lambda i: (str(i.get("branch")), str(i.get("path")), int(i.get("ordinal") or 0))):
        key = (item.get("branch"), item.get("path"), item.get("source_id"), item.get("ordinal"))
        if key in seen:
            continue
        seen.add(key)
        result.append({
            "repository_branch": item.get("branch"),
            "path": item.get("path"),
            "source_id": item.get("source_id") or None,
            "ordinal": item.get("ordinal"),
            "source_kind": item.get("source_kind"),
        })
    return result


def convert(best: dict[str, Any], occurrences: list[dict[str, Any]], owner: str, topic: str) -> tuple[dict[str, Any] | None, str | None]:
    raw = dict(best.get("raw") or {})
    stem = str(best.get("stem") or "").strip()
    qtype = raw.get("type") or best.get("type")
    if not stem or len(norm(stem)) < 8:
        return None, "empty-or-fragmentary-stem"
    if qtype not in {"mcq_one","mcq_multi","true_false","numeric","short_answer","fill_blank","essay","code_review","matching","ordering"}:
        return None, "unknown-question-type"

    if best.get("source_kind") == "json-bank" and best.get("branch") == CURRENT_BRANCH:
        item = raw
        item["source"] = dict(item.get("source") or {})
        item["source"]["legacy_occurrences"] = provenance(occurrences)
        item["metadata"] = dict(item.get("metadata") or {})
        item["metadata"].setdefault("migration", {})["signature"] = best["signature"]
        item["metadata"]["migration"]["owner"] = owner
        return item, None

    item: dict[str, Any] = {
        "id": stable_id(owner, topic, str(best["signature"])),
        "version": 1,
        "type": qtype,
        "points": 1,
        "topic": f"{owner.upper()} > {topic.replace('-', ' ').title()}",
        "category_ids": [topic],
        "difficulty": raw.get("difficulty") if raw.get("difficulty") in {"easy","medium","hard"} else "medium",
        "tags": ["legacy-migrated", topic],
        "stem": stem,
        "author": "Tim Rossiter",
        "license": "CC-BY-4.0",
        "source": {"legacy_occurrences": provenance(occurrences), "official_refs": []},
        "metadata": {
            "reviewed": False,
            "migration": {"signature": best["signature"], "owner": owner, "mechanical": True},
            "verification": {"status": "pending"},
        },
    }

    if qtype in {"mcq_one", "mcq_multi"}:
        choices = raw.get("choices")
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            item["choices"] = choices
        else:
            values = raw.get("legacy_choices") or []
            if len(values) < 2:
                return None, "mcq-missing-choices"
            correct = raw.get("legacy_correct")
            if not isinstance(correct, int) or correct < 0 or correct >= len(values):
                answer_text = str(raw.get("legacy_answer") or "").strip()
                if answer_text:
                    try:
                        correct = next(i for i, value in enumerate(values) if norm(str(value)) == norm(answer_text))
                    except StopIteration:
                        return None, "mcq-missing-key"
                else:
                    return None, "mcq-missing-key"
            item["choices"] = [{"text": str(value), "correct": i == correct} for i, value in enumerate(values)]
        item["shuffle_choices"] = True
    elif qtype == "true_false":
        answer = raw.get("answer")
        if not isinstance(answer, bool):
            return None, "true-false-missing-key"
        item["answer"] = answer
    elif qtype == "numeric":
        if not isinstance(raw.get("answer"), (int, float)) or isinstance(raw.get("answer"), bool):
            return None, "numeric-missing-key"
        item["answer"] = raw["answer"]
        item["tolerance"] = raw.get("tolerance", 0)
        if "unit" in raw:
            item["unit"] = raw.get("unit")
    elif qtype in {"short_answer", "fill_blank"}:
        answers = raw.get("answers")
        if isinstance(answers, list) and answers:
            item["answers"] = answers
        else:
            answer = str(raw.get("legacy_answer") or "").strip()
            if not answer:
                return None, "short-answer-missing-key"
            item["answers"] = [{"text": answer, "case_sensitive": False}]
    elif qtype == "essay":
        sample = str(raw.get("sample_answer") or raw.get("legacy_answer") or "").strip()
        rubric = str(raw.get("rubric") or "").strip()
        if sample:
            item["sample_answer"] = sample
        if rubric:
            item["rubric"] = rubric
        item["response_lines"] = int(raw.get("response_lines") or 8)
        if not sample and not rubric:
            return None, "essay-missing-key-or-rubric"
    elif qtype == "matching":
        pairs = raw.get("pairs")
        if not isinstance(pairs, list) or len(pairs) < 2:
            return None, "matching-missing-pairs"
        item["pairs"] = pairs
    elif qtype == "ordering":
        values = raw.get("items")
        if not isinstance(values, list) or len(values) < 2:
            return None, "ordering-missing-items"
        item["items"] = values
    elif qtype == "code_review":
        code = str(raw.get("code") or "").strip()
        prompts = raw.get("prompts")
        if not code or not isinstance(prompts, list) or not prompts:
            return None, "code-review-needs-source-recovery"
        item["code"] = code
        item["language"] = raw.get("language") or "text"
        item["prompts"] = prompts
        if raw.get("answers"):
            item["answers"] = raw["answers"]

    return item, None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("inventory")
    parser.add_argument("--course", required=True, choices=sorted(COURSE_TOPICS))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    data = json.loads(Path(args.inventory).read_text(encoding="utf-8"))
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in data.get("extracted_items", []):
        signature = str(record.get("signature") or "")
        if signature:
            groups[signature].append(record)

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    by_owner_topic: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    ledger = []

    for signature, occurrences in sorted(groups.items()):
        best = choose_best(occurrences)
        owner = target_owner(args.course, str(best.get("stem") or ""), str(best.get("path") or ""), str(best.get("source_kind") or ""))
        topic = topic_for(owner, str(best.get("stem") or ""), str(best.get("path") or ""))
        item, problem = convert(best, occurrences, owner, topic)
        ledger.append({
            "signature": signature,
            "owner": owner,
            "topic": topic,
            "canonical_id": item.get("id") if item else None,
            "status": "candidate" if item else "unresolved",
            "problem": problem,
            "best_source": {"branch": best.get("branch"), "path": best.get("path"), "source_id": best.get("source_id"), "source_kind": best.get("source_kind")},
            "occurrences": len(occurrences),
            "stem": best.get("stem"),
        })
        if item:
            by_owner_topic[(owner, topic)].append(item)

    export_root = output / "exports"
    for (owner, topic), questions in sorted(by_owner_topic.items()):
        target = export_root / owner
        target.mkdir(parents=True, exist_ok=True)
        (target / f"{topic}.jsonl").write_text("\n".join(json.dumps(q, ensure_ascii=False) for q in questions) + "\n", encoding="utf-8")

    (output / "mechanical-ledger.json").write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    counts = defaultdict(int)
    for row in ledger:
        counts[(row["status"], row["owner"], row["topic"])] += 1
    lines = [
        "# Mechanical question migration report", "",
        "> This pass preserves and classifies source material. It does not mark legacy questions verified.", "",
        f"**Unique source signatures:** {len(ledger)}  ",
        f"**Mechanically convertible:** {sum(r['status']=='candidate' for r in ledger)}  ",
        f"**Unresolved:** {sum(r['status']=='unresolved' for r in ledger)}", "",
        "| Status | Owner | Topic | Count |", "|---|---|---|---:|",
    ]
    for (status, owner, topic), count in sorted(counts.items()):
        lines.append(f"| {status} | {owner} | {topic} | {count} |")
    lines += ["", "## Unresolved source items", ""]
    for row in ledger:
        if row["status"] == "unresolved":
            lines.append(f"- `{row['signature']}` `{row['problem']}`: {str(row['stem'])[:180]} (`{row['best_source']['path']}`)")
    (output / "mechanical-report.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"signatures={len(ledger)} convertible={sum(r['status']=='candidate' for r in ledger)} unresolved={sum(r['status']=='unresolved' for r in ledger)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
