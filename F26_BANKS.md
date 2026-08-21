# Fall 2026 Course Banks

This branch is the Fall 2026 working branch for the JSON Quizbank design.

## Banks

```text
banks/rcet2265.bank.json   scaffold; populate from mature RCET2265 curriculum
banks/rcet3371.bank.json   Weeks 1-3 starter pool
banks/rcet3373.bank.json   Weeks 1-3 starter theory pool
banks/rcet3375.bank.json   Labs 01-03 readiness/troubleshooting pool
```

All newly generated starter questions are intentionally marked `reviewed: false`. A question should not become exam-ready merely because it validates.

## Validate

Because this repository now contains multiple banks, always specify the bank explicitly.

```sh
./quizbank validate --bank banks/rcet2265.bank.json
./quizbank validate --bank banks/rcet3371.bank.json
./quizbank validate --bank banks/rcet3373.bank.json
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

This displays question/category/assessment counts and the available assessment IDs.

## Build paper quizzes

Example Week 1 RCET3373 paper form:

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

QTI currently exports the automatically gradable item types supported by the JSON branch. Manually graded types remain useful in paper/Markdown/Typst outputs and are reported rather than silently discarded by the QTI exporter.

## Build everything

```sh
./quizbank build rcet3373-w1-starter \
  --bank banks/rcet3373.bank.json \
  --seed 337301 \
  --format all
```

Generated files go under `build/`.

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

For each starter question:

1. verify technical truth against the official source listed in `source`;
2. edit wording into the instructor's voice;
3. verify distractors represent plausible misconceptions rather than tricks;
4. verify calculations/units;
5. decide whether the question is retrieval, practice, readiness, quiz, or assessment quality;
6. set `metadata.reviewed` to `true` only after that review;
7. add tags such as `quiz-ready`, `assessment-ready`, or `prelab` as the working conventions emerge.

## Adding questions while teaching

The bank is intentionally comprehensive. It is fine to add a question immediately after seeing a useful misconception in class.

Prefer stable concept-based category IDs and use week/semester placement as metadata. That way a useful question survives if pacing changes next year.
