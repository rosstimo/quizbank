# Quizbank question consolidation and verification plan

This document governs the one-time consolidation of all known assessment questions into the current Quizbank JSON format and the ongoing workflow after migration.

## Completion definition

The migration is complete only when all of these gates pass:

1. every planning-repository branch and every Quizbank branch has been inventoried for question-bearing JSON, YAML, Typst, Markdown, and GIFT sources;
2. every real question occurrence is either mapped to a canonical item or explicitly retired with a reason;
3. equivalent copies are represented by one canonical item with all legacy occurrences preserved as provenance;
4. every canonical item validates against the current Quizbank schema;
5. every canonical item has course ownership, category, tags, difficulty, solution, correct feedback, incorrect feedback, author, license, and provenance;
6. technical answers and feedback have been checked against current authoritative documentation, with durable official URLs and a useful section/API/register/command locator;
7. outdated or ambiguous legacy wording has been corrected rather than preserving a formerly keyed answer that is no longer true;
8. each canonical question exists in the correct course planning repository on `curriculum/f26-alignment-cleanup`;
9. the Fall 2026 Quizbank course banks are generated/synchronized from those planning sources without introducing a second independently edited copy;
10. Markdown references regenerate successfully from all canonical banks;
11. repository agent instructions and CI workflows enforce the same gates for future questions; and
12. a final cross-repository audit reports no unmapped source questions, duplicate canonical IDs, missing required metadata, broken official references, or planning/Quizbank drift.

## Canonical ownership

A question has one canonical planning-repository owner. Historical locations remain provenance only.

- **RCET2265** owns introductory C#/.NET, console I/O, basic program structure, variables, types, operators, introductory debugging, and introductory source-control concepts taught in RCET2265.
- **RCET3371** owns advanced programming, program organization, object-oriented design, GUI/application architecture, debugging/recovery at the advanced-programming level, and Git topics taught as part of RCET3371.
- **RCET3373** owns digital/computer architecture theory and PIC theory: memory systems, PIC16F883 architecture, instruction set, banking, digital I/O theory, oscillator/instruction timing, software timing, subroutines/stack, interrupts, lookup tables, timers, ADC, EUSART/UART/RS-232 theory, EEPROM, I2C, and related device electrical/configuration theory.
- **RCET3375** owns laboratory readiness and lab-book assessment: project/tool bring-up, wiring, configuration evidence, implementation procedure, calculations made for a lab, measurement/oscilloscope/frequency-counter evidence, checkoff observations, troubleshooting, safety/loading verification, and questions whose answer is expected to exist in the student's lab notebook.

When an old RCET3375 quiz contains a pure theory question, canonical ownership moves to RCET3373. A lab question may reference the same underlying fact, but it must test a distinct lab-book or implementation target rather than copy the theory item.

## Source authority during consolidation

For equivalent questions, use this priority when choosing the canonical wording and keyed model:

1. current verified Quizbank-format planning item;
2. current Fall 2026 teaching/lab material plus its accuracy review;
3. reviewed Fall 2026 Quizbank item;
4. prior structured Typst/YAML/GIFT bank item;
5. prior Markdown quiz or assessment;
6. generated or AI-produced historical bank;
7. bare assessment prompt without an answer key.

Lower-priority occurrences are never discarded. They are listed in `source.legacy_occurrences` on the canonical item or in the migration ledger.

## Duplicate policy

Exact or normalized-stem duplicates are only the first pass. Near-duplicates are consolidated when they test the same knowledge with no meaningful change in reasoning.

Keep distinct variants when the values, register/pin, code path, failure symptom, direction of reasoning, or scenario create genuinely different practice. Related variants receive a common `metadata.variant_group`.

Never reuse an existing stable item ID for a different learning target.

## Canonical item metadata policy

Every production question must contain:

- `id`
- `version`
- `type`
- `points`
- `stem`
- `topic`
- at least one `category_ids` entry
- `difficulty`
- useful `tags`
- `feedback.correct`
- `feedback.incorrect`
- a worked `solution` or grading explanation
- `author`
- `license`
- `source.official_refs`
- `source.legacy_occurrences` when migrated from historical material
- `metadata.reviewed: true`
- `metadata.verification.status: verified`
- `metadata.verification.checked_on`

Multiple-choice items should also contain a rationale for every choice unless the rationale would merely repeat the choice text.

The bank-level `metadata.source_catalog.official` maps each `official_ref` to a title, durable URL, and useful locator. Feedback must identify the official source in student-readable language, not only a catalog key.

## Verification rules

A historical key is evidence of prior use, not proof of correctness.

- C#/.NET/Visual Studio questions are checked against current Microsoft Learn/.NET documentation.
- Git questions are checked against `git-scm.com/docs`.
- PIC16F883/device questions are checked first against the Microchip PIC16F882/883/884/886/887 data sheet, then the applicable Microchip Mid-Range MCU Family Reference Manual section when useful.
- Toolchain questions use current Microchip MPLAB X / PIC Assembler documentation.
- Other interfaces use the governing standard or an authoritative manufacturer document where the public standard text is not available.
- Course-specific lab questions additionally cite the current Fall 2026 lab/instruction source as teaching provenance.

If an old question depends on a version-specific fact, obsolete UI, ambiguous wording, or a now-false premise, rewrite it to a stable current learning target or retire it. Record the decision in the migration ledger.

## Migration artifacts

Each planning repository keeps the following under `F26/QuizBanks/migration/` during the migration:

- `source-inventory.json`: machine-readable cross-branch occurrence inventory;
- `source-inventory.md`: human-readable inventory summary;
- `migration-ledger.json`: every source occurrence mapped to canonical item or retirement decision;
- `migration-report.md`: totals, transformations, retirements, conflicts, and quality-gate results.

After completion these files remain as provenance. They are not question sources.

## Target organization

Each planning repository owns a comprehensive course bank plus optional generated topic references:

```text
F26/QuizBanks/
  rcetXXXX-f26.bank.json        # canonical authored bank for the course
  Markdown/                     # generated whole-bank practice/reference output
  migration/                    # audit/provenance only
```

The comprehensive bank uses stable concept categories rather than week numbers as its primary taxonomy. Week, lab, teaching-session, and historical placement belong in tags or provenance so questions survive pacing changes.

`rosstimo/quizbank` mirrors the four course banks for application/export use. Planning repositories remain the instructional ownership authority.

## Clean Git history

Migration commits are intentionally separated:

1. `audit:` inventory only;
2. `docs:` policy/ownership/instructions only;
3. `migrate:` mechanical format conversion and provenance capture;
4. `content:` answer corrections, deduplication, categorization, and official-source enrichment by coherent topic;
5. `ci:` validation/synchronization workflow changes;
6. `docs:` regenerated Markdown references and final verification report.

Do not combine unrelated curriculum changes into migration commits. Never rewrite historical branches merely to make them look current. Historical branches stay intact; canonical current content is assembled on the Fall 2026 cleanup branches.

## Ongoing rule after migration

New questions are authored only in the current Quizbank JSON schema in the owning planning repository. Teaching-transcript processing may propose candidates, but a candidate is not a production question until it has passed metadata, official-source, answer, duplicate, and validation gates. CI must fail if a production question is missing any required evidence or if a Quizbank mirror has drifted from its planning source.
