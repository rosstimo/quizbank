# Fall 2026 Course Banks

`main` is the durable Fall 2026 Quizbank authority. Course planning repositories may retain historical migration sources and candidate banks, but current authored/validated Quizbank schema, tooling, and promoted banks live here.

See [`docs/COURSE_BANK_STATUS.md`](docs/COURSE_BANK_STATUS.md) for the cross-course reconciliation audit and remaining coverage gaps.

## Banks on `main`

```text
banks/rcet2265.bank.json                    durable course bank; currently an empty scaffold
banks/rcet3371.bank.json                    durable course bank; 20-question starter pool
banks/rcet3373.bank.json                    durable course bank; 27-question starter theory pool
banks/rcet3373-w03-lookup-timing.bank.json  W03D03 review staging bank; 10 questions
banks/rcet3373-w03-interrupts.bank.json     W03D04 review staging bank; 10 questions
banks/rcet3375.bank.json                    durable laboratory bank; 18 questions
banks/rcet3375-legacy-section01.bank.json   legacy renderer/migration benchmark; 21 questions
```

Review-staging and legacy banks are intentionally separate from durable course banks. After instructor review, promote accepted items into the durable course bank, preserve stable IDs/provenance, then retire staging files when they no longer serve a review/provenance purpose.

All newly generated or migrated questions remain `reviewed: false` until Tim has reviewed technical truth, wording, distractors, calculations/units, sources, and intended assessment use.

## Validate

Always specify the bank explicitly because this repository contains multiple banks.

```sh
./quizbank validate --bank banks/rcet2265.bank.json
./quizbank validate --bank banks/rcet3371.bank.json
./quizbank validate --bank banks/rcet3373.bank.json
./quizbank validate --bank banks/rcet3373-w03-lookup-timing.bank.json
./quizbank validate --bank banks/rcet3373-w03-interrupts.bank.json
./quizbank validate --bank banks/rcet3375.bank.json
```

For a less strict first inspection while editing:

```sh
./quizbank validate --bank banks/rcet3373.bank.json --lint-level warn
```

## List a bank

```sh
./quizbank list --bank banks/rcet3373.bank.json
```

This displays question/category/assessment counts and available assessment IDs.

## Build paper quizzes

Example RCET3373 paper form:

```sh
./quizbank build rcet3373-w1-starter \
  --bank banks/rcet3373.bank.json \
  --seed 337301 \
  --format pdf
```

Build editable Typst source instead:

```sh
./quizbank build rcet3373-w1-starter \
  --bank banks/rcet3373.bank.json \
  --seed 337301 \
  --format typst
```

Build without an answer key:

```sh
./quizbank build rcet3373-w1-starter \
  --bank banks/rcet3373.bank.json \
  --seed 337301 \
  --format pdf \
  --no-key
```

## Build Canvas QTI

```sh
./quizbank build rcet3373-w1-starter \
  --bank banks/rcet3373.bank.json \
  --seed 337301 \
  --format qti
```

QTI exports the automatically gradable item types supported by the JSON model. Manually graded types remain available in paper/Markdown/Typst outputs and are reported rather than silently discarded.

## Full-bank instructor review

```sh
./quizbank review \
  --bank banks/rcet3373.bank.json \
  --format pdf \
  --format markdown
```

The review command renders every question through the normal paper pipeline with an answer key. GitHub Actions also builds review bundles for changed banks.

The browsable Markdown under `reference/F26/` is generated from the banks on `main`. It is convenient for navigation and question-by-question review, but JSON remains authoritative.

## Seed rule

A seeded pool is repeatable. Keep the seed with the quiz record when a specific paper/Canvas form must be regenerated later.

Suggested convention:

```text
course + week/lab + form
337301 = RCET3373 Week 1 form 1
337302 = RCET3373 Week 1 form 2
337501 = RCET3375 Lab 1 form 1
```

The exact convention can change; consistency matters more than the number scheme.

## Review workflow

For each candidate question:

1. verify technical truth against the official source listed in `source`;
2. edit wording into the instructor's voice;
3. verify distractors represent plausible misconceptions rather than tricks;
4. verify calculations and units;
5. decide whether the question is retrieval, practice, readiness, quiz, or assessment quality;
6. set `metadata.reviewed` to `true` only after that review;
7. add tags such as `quiz-ready`, `assessment-ready`, or `prelab` as conventions stabilize;
8. preserve teaching provenance when promoting from a course planning repository.

## Adding questions while teaching

The durable bank should be comprehensive. It is fine to capture a useful misconception immediately after class, but new material should enter as review staging until its wording and technical basis are checked.

Prefer stable concept-based category IDs and use week/semester placement as metadata. That keeps questions reusable when pacing changes in a later semester.
