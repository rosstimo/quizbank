# Quizbank Usage Guide

Quizbank keeps assessment content in JSON banks and generates the formats needed for different jobs. The JSON bank is the authored source of truth.

## The two Markdown outputs are different

Quizbank now has two separate Markdown workflows.

### Printable assessment Markdown

Use `build --format markdown` when you want the Markdown representation of one assessment. This is part of the same assessment pipeline that produces Typst, PDF, LaTeX, and QTI.

```bash
/path/to/quizbank/quizbank build quiz-example-001 \
  --bank /path/to/course/F26/QuizBanks/course.bank.json \
  --format markdown
```

This output is quiz-oriented: selected questions first, then the normal compact answer key.

### GitHub reference/practice Markdown

Use `reference` when you want a browsable representation of the entire bank for GitHub, practice, review, and question-bank maintenance.

```bash
/path/to/quizbank/quizbank reference \
  --bank /path/to/course/F26/QuizBanks/course.bank.json \
  --output-dir /path/to/course/F26/QuizBanks/Markdown
```

For a bank whose ID is `course.topic`, Quizbank creates:

```text
Markdown/
├── course-topic.md
└── keys/
    └── course-topic-key.md
```

The question document:

- groups questions by their primary category;
- shows the stable question ID;
- shows type, difficulty, points, tags, and variant group when present;
- does not expose the answer;
- links each individual question directly to its matching key entry.

The key document:

- has a stable anchor for every key entry;
- links each entry back to the exact question;
- repeats the original question and choices/prompts;
- shows the keyed answer;
- shows the solution/reasoning;
- includes correct/incorrect feedback when present;
- includes official and teaching provenance from the JSON bank.

This reference export does **not** replace PDF, Typst, LaTeX, QTI, or printable Markdown generation. It is a separate view of the bank.

## Banks can live anywhere

Quizbank does not require a bank to be copied into its own repository. The launchers mount the requested bank directory into the container automatically.

Linux/macOS:

```bash
/home/tim/src/quizbank/quizbank validate \
  --bank /home/tim/Documents/course/F26/QuizBanks/course.bank.json
```

A relative path is interpreted from the directory where you run the command:

```bash
cd /home/tim/Documents/course
/home/tim/src/quizbank/quizbank validate \
  --bank F26/QuizBanks/course.bank.json
```

The launcher also locates its own `compose.yaml`, so your current working directory does not need to be the Quizbank repository.

Windows PowerShell:

```powershell
C:\src\quizbank\quizbank.ps1 validate `
  --bank C:\Users\Tim\Documents\course\F26\QuizBanks\course.bank.json
```

## Output directories can live anywhere

An explicit `--output-dir` is mounted separately and can point to another repository or directory.

```bash
/home/tim/src/quizbank/quizbank reference \
  --bank /home/tim/Documents/course/F26/QuizBanks/course.bank.json \
  --output-dir /home/tim/Documents/course/F26/QuizBanks/Markdown
```

The parent directory of the requested output directory must already exist. Quizbank creates the final output directory and its `keys/` directory as needed.

The same external-output behavior applies to `build`:

```bash
/home/tim/src/quizbank/quizbank build quiz-example-001 \
  --bank /home/tim/Documents/course/F26/QuizBanks/course.bank.json \
  --format pdf,qti \
  --output-dir /home/tim/Documents/course/generated-assessments
```

## Common workflow for a course bank

### 1. Validate

```bash
/path/to/quizbank/quizbank validate --bank /path/to/course.bank.json
```

### 2. Inspect the bank and available assessments

```bash
/path/to/quizbank/quizbank list --bank /path/to/course.bank.json
```

### 3. Generate/update GitHub practice material

```bash
/path/to/quizbank/quizbank reference \
  --bank /path/to/course.bank.json \
  --output-dir /path/to/course/QuizBanks/Markdown
```

Commit both the JSON source and generated reference Markdown if you want the rendered practice material visible on GitHub.

### 4. Build a specific assessment

```bash
/path/to/quizbank/quizbank build assessment-id \
  --bank /path/to/course.bank.json \
  --seed 3375
```

The same bank can generate PDF, Typst, LaTeX, printable Markdown, and Canvas QTI without creating separate authored copies of the questions.

### 5. Build only what you need

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

Use `--no-key` when producing a paper format that should not contain the answer key.

## Stable IDs matter

A stable question ID such as:

```text
pic.flags.002
```

identifies the same question across:

- JSON source;
- GitHub practice Markdown;
- GitHub answer key;
- generated assessments;
- Canvas imports;
- future item statistics.

Do not reuse a stable ID for unrelated content. Increment the question `version` when a grading-relevant change is made.

## Suggested course-repository organization

The reference exporter works well with topic-oriented JSON banks and Markdown:

```text
F26/QuizBanks/
├── README.md
├── memory-systems.bank.json
├── pic-architecture.bank.json
├── pic-io.bank.json
├── pic-assembly.bank.json
└── Markdown/
    ├── memory-systems.md
    ├── pic-architecture.md
    ├── pic-io.md
    ├── pic-assembly.md
    └── keys/
        ├── memory-systems-key.md
        ├── pic-architecture-key.md
        ├── pic-io-key.md
        └── pic-assembly-key.md
```

Use course topics/categories for file organization. Keep difficulty, question type, week, lab part, tags, and variant groups as metadata so they remain filterable without scattering related questions across directories.
