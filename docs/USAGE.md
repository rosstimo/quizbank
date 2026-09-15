# Quizbank Usage Guide

Quizbank is a reusable assessment tool. Keep real course banks in the repository or directory that owns the course material, and point Quizbank at those banks when validating, reviewing, or building assessments.

## Run Quizbank from anywhere

The `quizbank` and `quizbank.ps1` launchers resolve Quizbank's own Compose file, so the current working directory does not need to be the Quizbank repository.

Linux/macOS:

```bash
/path/to/quizbank/quizbank validate \
  --bank /path/to/my-course/QuizBanks/course.bank.json
```

Windows PowerShell:

```powershell
C:\path\to\quizbank\quizbank.ps1 validate `
  --bank C:\path\to\my-course\QuizBanks\course.bank.json
```

The bank's directory is bind-mounted read-only into the Quizbank container. An explicit output path is mounted separately and remains writable.

Relative paths are interpreted from the directory where the launcher is invoked:

```bash
cd /path/to/my-course
/path/to/quizbank/quizbank validate --bank QuizBanks/course.bank.json
```

## Create a bank outside the Quizbank repository

The parent directory must already exist.

```bash
/path/to/quizbank/quizbank new \
  /path/to/my-course/QuizBanks/course.bank.json \
  --id my-course \
  --title "My Course"
```

Then validate it:

```bash
/path/to/quizbank/quizbank validate \
  --bank /path/to/my-course/QuizBanks/course.bank.json
```

## Inspect a bank

```bash
/path/to/quizbank/quizbank list \
  --bank /path/to/my-course/QuizBanks/course.bank.json
```

Strict validation is the default:

```bash
/path/to/quizbank/quizbank validate \
  --bank /path/to/my-course/QuizBanks/course.bank.json \
  --lint-level error
```

## Build a specific assessment

```bash
/path/to/quizbank/quizbank build assessment-id \
  --bank /path/to/my-course/QuizBanks/course.bank.json \
  --seed 42 \
  --output-dir /path/to/my-course/generated
```

Available current build formats are PDF, Typst, LaTeX, Markdown, and Canvas-compatible QTI 1.2.

Examples:

```bash
/path/to/quizbank/quizbank build assessment-id \
  --bank /path/to/course.bank.json \
  --format pdf

/path/to/quizbank/quizbank build assessment-id \
  --bank /path/to/course.bank.json \
  --format qti

/path/to/quizbank/quizbank build assessment-id \
  --bank /path/to/course.bank.json \
  --format markdown,typst
```

Use `--no-key` to omit the answer key from paper outputs and `--no-points` to hide point values in paper section headings.

## Review every question in a bank

The `review` command runs every question through the normal paper rendering path. It is useful before an instructor approves a bank or after a schema/tooling change.

```bash
/path/to/quizbank/quizbank review \
  --bank /path/to/my-course/QuizBanks/course.bank.json \
  --format pdf \
  --format markdown \
  --output-dir /path/to/my-course/review
```

`review` does not emit QTI because it is an instructor-review view rather than an LMS assessment package.

## Build GitHub-friendly practice/reference Markdown

`reference` renders the whole bank as browsable question Markdown plus a linked answer key. This is separate from printable assessment Markdown.

```bash
/path/to/quizbank/quizbank reference \
  --bank /path/to/my-course/QuizBanks/course.bank.json \
  --output-dir /path/to/my-course/QuizBanks/Markdown
```

For a bank whose id is `example-bank`, the output is:

```text
Markdown/
├── example-bank.md
└── keys/
    └── example-bank-key.md
```

The question document groups questions by category, shows stable IDs and useful metadata, and links each question to its key entry. The key repeats the question, gives the keyed answer and explanation, and retains available provenance metadata.

## Migrate legacy Quizbank YAML

The current migration command converts the repository's older YAML question/quiz structure into one JSON bank:

```bash
/path/to/quizbank/quizbank migrate \
  --items qbank \
  --quizzes quizzes \
  --id migrated-bank \
  --title "Migrated Bank" \
  --output /path/to/output/migrated.bank.json
```

The output path may be outside the Quizbank repository. The legacy input directories themselves must currently be visible to the container, so the simplest migration workflow is still to run that command from the Quizbank checkout or stage the legacy inputs there temporarily.

## Stable question IDs

A stable question ID identifies the same authored question across JSON source, generated paper forms, reference Markdown, answer keys, and LMS exports. Do not reuse an existing ID for unrelated content. Increment the question `version` when a grading-relevant change is made.

## Suggested course-repository organization

A course may keep one bank or several topic-oriented banks. One workable layout is:

```text
QuizBanks/
├── README.md
├── fundamentals.bank.json
├── advanced-topic.bank.json
└── Markdown/
    ├── fundamentals.md
    ├── advanced-topic.md
    └── keys/
        ├── fundamentals-key.md
        └── advanced-topic-key.md
```

Keep course-specific approval state, provenance, semester pacing, and real question content in the course repository. Quizbank itself should contain only the reusable tool, generic examples, compatibility fixtures, and tests.
