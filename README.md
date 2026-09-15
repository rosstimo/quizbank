# Quizbank

Quizbank is a generic, shareable tool for creating and managing question banks and building assessments from them. Author questions, categories, metadata, and assessment recipes in JSON, then validate and render them through a consistent toolchain.

The repository contains **tooling and generic examples only**. An instructor's real course banks should live with that instructor/course material and use Quizbank as the schema, validation, rendering, import, and export engine.

## Current capabilities

From a JSON bank, Quizbank currently supports:

- schema validation and linting;
- fixed-question and seeded pool-based assessment forms;
- instructor review rendering of every question in a bank;
- printable PDF output;
- editable Typst and LaTeX source;
- Markdown output and answer keys;
- Canvas-compatible QTI 1.2 export;
- migration of the repository's legacy YAML question/quiz format into JSON.

The current CLI does **not** advertise Moodle XML or GIFT as first-class export formats. The repository contains older/import-oriented Moodle/GIFT components and samples, and broader import/export coverage is an intended direction rather than a capability this README promises today. See `ROADMAP.md`.

Quizbank runs its Python packages, Pandoc, Typst, and LaTeX inside a container. The host only needs Docker Desktop, Docker Engine with Compose, or Podman Compose.

## Start here

Linux and macOS:

```bash
./quizbank
./quizbank validate
./quizbank build
```

Windows PowerShell:

```powershell
.\quizbank.ps1
.\quizbank.ps1 validate
.\quizbank.ps1 build
```

With the included `banks/example.bank.json`, the default build produces the example assessment in all current export formats:

```text
build/quiz-example-001/
├── quiz-example-001.md
├── quiz-example-001.typ
├── quiz-example-001.tex
├── quiz-example-001.pdf
└── quiz-example-001-qti12.zip
```

Use a narrower export when that is all you need:

```bash
./quizbank build --format pdf
./quizbank build --format qti
./quizbank build --format markdown,latex
./quizbank build quiz-example-random --seed 42 --format pdf
./quizbank build --format pdf --no-key
./quizbank build --format pdf --no-points
```

Useful inspection commands:

```bash
./quizbank list
./quizbank validate --lint-level error
./quizbank review --format pdf --format markdown
./quizbank doctor
```

`make help` provides short aliases for common development commands.

## One JSON bank

A bank contains five main parts:

```json
{
  "$schema": "../schemas/bank.schema.json",
  "format_version": 1,
  "bank": {
    "id": "example-course",
    "title": "Example Course",
    "language": "en-US"
  },
  "categories": [
    {"id": "fundamentals", "title": "Fundamentals"}
  ],
  "questions": [
    {
      "id": "fundamentals.boolean.001",
      "version": 1,
      "type": "mcq_one",
      "points": 1,
      "category_ids": ["fundamentals"],
      "difficulty": "easy",
      "stem": "Which value is a Boolean value?",
      "choices": [
        {"text": "true", "correct": true},
        {"text": "42"},
        {"text": "hello"}
      ]
    }
  ],
  "assessments": [
    {
      "id": "fundamentals-check",
      "title": "Fundamentals Check",
      "items": ["fundamentals.boolean.001"]
    }
  ],
  "metadata": {
    "default_assessment": "fundamentals-check"
  }
}
```

The `metadata` objects deliberately accept extra fields. Quizbank can preserve information it does not interpret so a downstream course repository or future exporter/UI can use it later.

Current question types are:

`mcq_one`, `mcq_multi`, `true_false`, `numeric`, `short_answer`, `fill_blank`, `essay`, `code_review`, `matching`, and `ordering`.

Markdown is supported in question text, feedback, solutions, rubrics, and prompts. Use `$...$` or `$$...$$` for math. JSON Schema files under `schemas/` provide editor completion and validation.

## Fixed questions and generated forms

An assessment may list exact question IDs:

```json
{
  "id": "fundamentals-check",
  "title": "Fundamentals Check",
  "items": [
    "fundamentals.boolean.001",
    {"id": "fundamentals.numeric.001", "points": 3}
  ]
}
```

Or it may select seeded pools by category, type, difficulty, tags, or outcomes:

```json
{
  "id": "generated-form",
  "title": "Generated Form",
  "pools": [
    {
      "id": "true-false",
      "pick": 5,
      "where": {
        "category_ids": ["fundamentals"],
        "types": ["true_false"]
      }
    },
    {
      "id": "multiple-choice",
      "pick": 10,
      "where": {
        "category_ids": ["fundamentals"],
        "types": ["mcq_one"]
      }
    }
  ],
  "shuffle_questions": true
}
```

The seed makes generated forms repeatable. The same bank, assessment, and seed select the same questions.

## Create a bank for your own course

Keep your real bank in your course/project repository rather than adding it to Quizbank itself. Point Quizbank at it explicitly:

```bash
./quizbank new /path/to/my-course/bank.json \
  --id my-course \
  --title "My Course"

./quizbank validate --bank /path/to/my-course/bank.json
./quizbank build --bank /path/to/my-course/bank.json
```

When Quizbank is cloned alongside a course repository, relative paths work well too.

## Legacy YAML migration

The older one-question-per-YAML format remains available as migration input:

```bash
./quizbank migrate \
  --items qbank \
  --quizzes quizzes \
  --id migrated-example \
  --title "Migrated Example" \
  --output banks/migrated-example.bank.json
```

Migration preserves question content and creates category records from topic strings. It does not overwrite an existing JSON bank unless `--force` is supplied.

## Export behavior

| Format | Output | Notes |
|---|---|---|
| `pdf` | `.pdf` | Compiled with Typst inside the container |
| `typst` | `.typ` | Editable source |
| `latex` | `.tex` | Editable source |
| `markdown` | `.md` | Portable source and answer key |
| `qti` | `-qti12.zip` | Canvas-compatible QTI 1.2 package |
| `all` | all current formats | Default |

Paper formats support every current question type. QTI currently exports multiple choice, multiple select, true/false, numeric, short answer, and fill-in-the-blank items. Manually graded types that cannot be represented are reported rather than silently discarded.

## Development

```bash
make test
```

Tests run in the same containerized environment as normal commands. Generated files go under `build/` and are ignored by Git.

Generic examples and compatibility fixtures may live in this repository. Live semester/course banks, teaching records, and instructor-specific assessment state should not.
