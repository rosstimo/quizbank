# Quizbank repository instructions

Quizbank is a generic, shareable tool for authoring, validating, reviewing, importing, and exporting question banks and assessments.

## Repository boundary

- `main` is the released source of truth for Quizbank schema, CLI/tooling, exporters/importers, tests, documentation, and generic examples/fixtures.
- Do **not** store an instructor's live course banks, teaching-derived question pools, semester-specific assessment state, or private curriculum provenance in this repository.
- Files under `banks/`, `samples/`, `qbank/`, `quizzes/`, and test fixtures must be generic examples, compatibility fixtures, or tool tests unless explicitly documented otherwise.
- Real course banks belong in the instructor/course repository that owns the curriculum. Those repositories may use Quizbank's schema and CLI directly without copying their content here.
- Historical repository content may remain reachable through Git history, but current-tree documentation and automation must not treat old course-specific snapshots as current authority.

## Bank and review discipline

- Do not infer instructor approval from successful schema validation, rendering, import, or export.
- Preserve stable question IDs when a downstream course bank depends on them. Increment `version` for grading-relevant changes according to the current schema/versioning rules.
- Prefer generic examples that exercise a feature clearly without encoding one instructor's live course sequence.
- Keep metadata extensible so downstream course repositories can retain provenance/review fields that Quizbank itself does not need to interpret.

## Capability claims

Document only capabilities implemented and tested by the current checkout. Keep intended formats such as broader Moodle/GIFT workflows in a roadmap until the CLI exposes and tests them as supported import/export paths.

## Pull requests

Use feature branches for substantive schema/tooling changes. Tooling changes should pass the relevant tests plus bank validation and review-artifact workflows against the generic example banks/fixtures.
