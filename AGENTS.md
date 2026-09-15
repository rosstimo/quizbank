# Quizbank repository instructions

`main` is the durable released source of truth for Quizbank schema, tooling, and RCET authored/review-staging JSON banks.

## Source ownership

- Durable authored banks live under `banks/` in this repository.
- Course planning repositories may retain historical migration banks, provenance, candidate questions, and temporary staging material, but those copies are not durable assessment authority after promotion here.
- Generated Markdown under `reference/F26/` is a browsable review view only. JSON remains authoritative.
- Migration inventories and retired branch-bound automation belong under `migration/` or `old/`, not in the active workflow path.

## Review discipline

- Do not set `metadata.reviewed` to `true` merely because a bank validates or renders.
- Preserve stable question IDs. Increment a question `version` when a grading-relevant change is made.
- Preserve teaching and official-source provenance when promoting questions from a planning repository.
- Prefer concept/topic categories over week numbers; pacing belongs in metadata/tags.
- Reconcile duplicates before promotion rather than copying the same question into multiple durable course banks.
- RCET3373 owns theory questions for shared embedded topics. RCET3375 may test the same underlying fact only when the item measures a distinct lab-book, implementation, troubleshooting, measurement, or design target.

## Pull requests

For substantive bank/tooling changes, use a feature branch and keep Tim's review/merge gate intact.

A bank change should pass JSON validation and the full-bank review-artifact workflow. Generated Markdown references are regenerated from the current checkout and are not a substitute for review artifacts.
