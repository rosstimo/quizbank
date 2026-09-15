# RCET2265 Fall 2026 Bank Reconciliation

Date: 2026-09-15

This record documents the one-time consolidation of RCET2265 planning-repository assessment candidates into Quizbank's durable `banks/rcet2265.bank.json`.

The migration does **not** approve any question. Every imported question is stored with `metadata.reviewed: false` pending Tim's content/difficulty/source review.

## Source

Repository: `rosstimo/RCET2265-planning`  
Ref at reconciliation: `main`

| Planning source | Git blob | Questions |
|---|---|---:|
| `F26/QuizBanks/rcet2265-f26-w01-debugging.bank.json` | `34bd9fb8262d4c1a1a90b458560406d4401f61d0` | 3 |
| `F26/QuizBanks/rcet2265-f26-w01-operators-variables.bank.json` | `c6fc3c35971511d3ea20e0f7017d10434ea88f52` | 8 |
| `F26/QuizBanks/rcet2265-f26-w01-types.bank.json` | `bdf26472ae1d48ec093df983352027f291315b41` | 11 |
| `F26/QuizBanks/rcet2265-f26-w02-console.bank.json` | `de123def11bb5c4909e9544e9a3b62e2c4109d98` | 10 |
| `F26/QuizBanks/W02D04-conditionals/rcet2265.controlflow.001.yaml` | `4fa75aabc26bcbc53861373e330bba04e2d30f49` | 1 |
| `F26/QuizBanks/W02D04-conditionals/rcet2265.controlflow.002.yaml` | `c91b147da229adb20e154e310a7583ae2e385ce1` | 1 |
| `F26/QuizBanks/W02D04-conditionals/rcet2265.controlflow.003.yaml` | `495c4d27fa55d73291b1de4d317312c52ca064db` | 1 |
| `F26/QuizBanks/W02D04-conditionals/rcet2265.controlflow.004.yaml` | `93f8cbbc1c8284491e91f86ae92a74b6f7bbba98` | 1 |
| `F26/QuizBanks/W02D04-conditionals/rcet2265.controlflow.005.yaml` | `088c746c0c493e55893e99b9c3cfca2e49bb0cb4` | 1 |
| `F26/QuizBanks/W02D04-conditionals/rcet2265.controlflow.006.yaml` | `d15cb7b13015dd4e2156db84d01d1def5d97d740` | 1 |
| `F26/QuizBanks/W02D04-conditionals/rcet2265.controlflow.007.yaml` | `b2762caa9d8a793171f5b74994522cba04ef8a75` | 1 |
| `F26/QuizBanks/W02D04-conditionals/rcet2265.controlflow.008.yaml` | `6702c89521b1b410b82e3cbaab2870b46d9b520c` | 1 |

Total: **40 unique questions**.

## Transformation

- The four JSON banks were combined without changing their stable question IDs.
- Existing question text, choices/answers, feedback, solutions, tags, difficulty, source references, and source catalogs were preserved.
- The eight W02D04 YAML items were mechanically converted using the same topic-to-category behavior used by `qbank.migrate`.
- Every question was explicitly forced to `metadata.reviewed: false`.
- A `reconciliation_source` metadata field identifies the planning source for imported JSON questions.
- Original source-bank assessment definitions are preserved in reconciliation metadata rather than treated as approved current assessments.
- The durable bank adds review-only assessments for each source set and one all-candidate review assessment.

## Verification

Generated bank:

- path: `banks/rcet2265.bank.json`
- Git blob on the reconciliation branch: `0580a616bd7a7ef2ac600f22752169b6be55c52e`
- SHA-256: `4e404e3c8d1a90bedd0e13d7e1d5009533c94f95d529d65df58645d773353cb0`
- questions: 40
- `metadata.reviewed: true`: 0
- question types: 26 multiple choice, 7 true/false, 3 numeric, 3 code review, 1 ordering
- difficulty: 19 easy, 13 medium, 8 hard

Quizbank strict validation passed in GitHub Actions run `34963601409` before the generated bank was committed.

The first attempted automation tried to check out the private planning repository from Quizbank Actions and failed because the repository-scoped `GITHUB_TOKEN` cannot read that private repository. No assessment data was changed by that failed run. The successful transfer used the authorized GitHub connector to read the exact source blobs above, then verified the generated bank checksum before strict validation.
