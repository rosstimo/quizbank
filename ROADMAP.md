# Quizbank Roadmap

Quizbank is intended to be a reusable instructor tool, independent of any one course or institution.

## Current supported workflow

The current JSON-bank CLI supports:

- bank creation, listing, validation, and linting;
- fixed and seeded pool-based assessment recipes;
- full-bank instructor review rendering;
- PDF, Typst, LaTeX, and Markdown output;
- Canvas-compatible QTI 1.2 export;
- migration of the repository's legacy YAML question/quiz format into JSON.

These are the capabilities the README may present as currently supported.

## Import/export direction

Desired broader interchange includes:

- GIFT import and export;
- Moodle XML import and export;
- additional generic interchange formats where they provide meaningful portability;
- stronger round-trip testing so an import/export path does not silently lose scoring, feedback, metadata, or unsupported question types.

The repository already contains older/import-oriented GIFT and Moodle XML components and samples. Treat those as implementation assets and compatibility fixtures until they are integrated into the current JSON-bank CLI, covered by tests, and documented as supported user workflows.

## Assessment creation direction

Future work may include:

- richer assessment/form recipes and variant generation;
- clearer reporting when a target LMS cannot represent a Quizbank question type;
- configurable paper layouts and instructor/student forms;
- easier bank editing and review, potentially through a UI;
- reusable templates and sample banks that demonstrate features without embedding a real instructor's live course material.

## Repository boundary

New features should preserve the separation between **Quizbank the tool** and **course banks that use the tool**. Tool tests/examples belong here. Real course questions, semester pacing, teaching provenance, and instructor review state belong in the course/instructor repository.
