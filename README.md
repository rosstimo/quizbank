# Quizbank

Keep questions, categories, metadata, and assessment recipes in one JSON bank. Build a printable PDF, editable source, Markdown, or a Canvas QTI package from that bank.

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

The first command builds the local container image. Later commands reuse it. With the included example bank, `build` produces:

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
./quizbank build quiz-example-random --seed 3375 --format pdf
./quizbank build --format pdf --no-key
./quizbank build --format pdf --no-points
```

Paper outputs show point values in question-type section headers by default, such as `Multiple Choice Questions (1 pt each)`. Use `--no-points` to hide those labels. The JSON point values and QTI/Canvas scoring are unchanged.

Run `./quizbank doctor` to see the exact tools available inside the container. `make help` provides short aliases for the same commands.

## One JSON bank

Files under `banks/` are the authored source of truth. A bank contains five parts:

```json
{
  "$schema": "../schemas/bank.schema.json",
  "format_version": 1,
  "bank": {
    "id": "rcet3375",
    "title": "Advanced Digital Systems",
    "authors": ["Tim Rossiter"]
  },
  "categories": [
    {"id": "timers", "title": "Timers"},
    {"id": "timers.timer2", "title": "Timer2", "parent": "timers"}
  ],
  "questions": [
    {
      "id": "timers.timer2.001",
      "version": 1,
      "type": "mcq_one",
      "points": 1,
      "category_ids": ["timers.timer2"],
      "tags": ["prescaler"],
      "difficulty": "easy",
      "stem": "Which register selects the Timer2 prescaler?",
      "choices": [
        {"text": "T2CON", "correct": true},
        {"text": "OPTION_REG"}
      ],
      "solution": "The prescaler bits are in `T2CON`.",
      "metadata": {
        "source_page": 89,
        "reviewed": true
      }
    }
  ],
  "assessments": [
    {
      "id": "timer2-check",
      "title": "Timer2 Check",
      "items": ["timers.timer2.001"]
    }
  ],
  "metadata": {
    "default_assessment": "timer2-check"
  }
}
```

The `metadata` objects deliberately accept extra fields. Quizbank retains information an exporter does not understand so a richer exporter or future web UI can use it later.

The current question types are `mcq_one`, `mcq_multi`, `true_false`, `numeric`, `short_answer`, `fill_blank`, `essay`, `code_review`, `matching`, and `ordering`. Markdown is used for question text, feedback, solutions, rubrics, and prompts. Use `$...$` or `$$...$$` for math.

JSON Schema files under `schemas/` provide editor completion and validation. Point VS Code, Neovim, or another schema-aware editor at the `$schema` field in a bank.

## Fixed questions and generated forms

An assessment may list exact question IDs:

```json
{
  "id": "timer2-check",
  "title": "Timer2 Check",
  "items": [
    "timers.timer2.001",
    {"id": "timers.timer2.007", "points": 3}
  ]
}
```

It may also select seeded pools by category, type, difficulty, tags, or outcomes:

```json
{
  "id": "timer2-form",
  "title": "Timer2 Form",
  "pools": [
    {
      "id": "true-false",
      "pick": 5,
      "where": {
        "category_ids": ["timers.timer2"],
        "types": ["true_false"]
      }
    },
    {
      "id": "multiple-choice",
      "pick": 10,
      "where": {
        "category_ids": ["timers.timer2"],
        "types": ["mcq_one"],
        "tags": ["exam-ready"]
      }
    }
  ],
  "shuffle_questions": true
}
```

The seed makes a generated form repeatable. The same bank, assessment, and seed select the same questions.

## Move the old YAML bank into JSON

The legacy YAML files remain in the repository for comparison. Combine them into a JSON bank with:

```bash
./quizbank migrate \
  --items qbank \
  --quizzes quizzes \
  --id legacy.quizbank \
  --title "Legacy Quizbank" \
  --output banks/legacy.bank.json

./quizbank validate --bank banks/legacy.bank.json
```

Migration preserves question content and creates category records from `topic` strings such as `Example > Basics`. It does not overwrite an existing JSON bank unless `--force` is supplied.

Create a clean bank instead:

```bash
./quizbank new banks/rcet3375.bank.json \
  --id rcet3375 \
  --title "Advanced Digital Systems"
```

## Export behavior

| Format | Output | Notes |
|---|---|---|
| `pdf` | `.pdf` | Compiled with Typst inside the container |
| `typst` | `.typ` | Editable source |
| `latex` | `.tex` | Editable source |
| `markdown` | `.md` | Portable source and answer key |
| `qti` | `-qti12.zip` | Import into Canvas as QTI 1.2 |
| `all` | all of the above | Default |

Paper formats support every question type. QTI currently exports multiple choice, multiple select, true/false, numeric, short answer, and fill in the blank. It reports manually graded types that it leaves out instead of discarding them silently.

## Development without touching the host Python

```bash
make test
```

Tests run in the same containerized environment as normal commands. Generated files go under `build/` and are ignored by Git.

The original one-question-per-YAML tools are still present under `tools/`, `qbank/`, and `quizzes/` as migration inputs. New work should go into a JSON file under `banks/`.
