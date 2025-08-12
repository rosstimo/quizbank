# Quizbank

Plain text quiz question bank in **YAML**. This is the single source of truth for everything:

* Canvas LMS imports (QTI 1.2/2.1 for Classic and New Quizzes)
* Printable paper quizzes (Typst, LaTeX, Markdown)
* Other exports via small build scripts

## Repo layout

```
quizbank/
├── README.md                      # You are here
├── .gitignore
├── schemas/                       # JSON Schemas for validation
├── tools/                         # Scripts for validation and export
├── qbank/                         # Authored questions (YAML, one per file)
├── quizzes/                       # Quiz assembly files (YAML)
├── templates/                     # Export templates (Typst, LaTeX, QTI Jinja)
└── build/                         # Generated output (ignored in git)
```

## Authoring rules

* **One item per file.** Keep files short and focused.
* **IDs:** lowercase letters, digits, dots, underscores, hyphens. Example: `cs.arrays.007`.
* **Version:** bump `version` on any content change that affects grading.
* **Media:** store under `qbank/media/` and reference by relative path.
* **Markdown in text:** `stem`, `choices[].text`, `solution`, and `feedback.*` accept Markdown with inline math.
* **No YAML anchors or tags.** Keep it simple for tooling and AI generation.

## YAML item shape (summary)

Each file must validate against `schemas/quiz-item.schema.json`.

Required top-level keys:

* `id` string
* `version` integer
* `type` one of: `mcq_one`, `mcq_multi`, `true_false`, `numeric`, `short_answer`
* `points` number
* `stem` markdown string

Type-specific keys:

* `mcq_one` / `mcq_multi`: `choices[]` with `text` and optional `correct: true`. Exactly one correct for `mcq_one`, at least one for `mcq_multi`.
* `true_false`: `answer` boolean
* `numeric`: `answer` number, optional `tolerance` and `unit`
* `short_answer`: `answers[]` entries with `text`, optional `regex`, `case_sensitive`, `score`

Optional common keys: `topic`, `outcomes[]`, `difficulty`, `tags[]`, `attachments[]`, `shuffle_choices`, `feedback.correct`, `feedback.incorrect`, `solution`, `author`, `license`.

## Quiz assembly files

A quiz file in `quizzes/` lists item IDs and options.

Example:

```yaml
id: quiz-algebra-01
title: Linear Functions Check
shuffle_questions: true
pick: 12
items:
  - alg.slope.001
  - alg.slope.param.001.*
  - alg.lines.truefalse.003
```

## Workflow

1. **Write** items under `qbank/<topic>/`.
2. **Validate** everything:

   ```bash
   make validate
   ```
3. **Export** when ready:

   * Canvas: build QTI 1.2/2.1 zip in `build/qti/` and import via Canvas > Settings > Import Course Content.
   * Paper: render Typst/LaTeX/Markdown from templates.

## Conventions that save time

* Enforce unique `id`. Never reuse IDs across different content.
* Keep distractor rationales for MCQs. It helps feedback and later review.
* Short files. Prefer many small YAML files over a few giant ones.

