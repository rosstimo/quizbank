# RCET Course Bank Status

Audit date: 2026-09-15

This document records the current relationship between durable Quizbank banks and assessment material still living in course planning repositories. Counts describe stored items, not necessarily unique or instructor-approved questions.

| Course | Durable bank on `main` | Current durable questions | Additional staged/historical material found | Status |
|---|---|---:|---|---|
| RCET2265 | `banks/rcet2265.bank.json` | 0 | RCET2265-planning retains a 40-question historical/staging snapshot: 32 questions across four JSON banks plus 8 conditionals questions from a legacy YAML set | **Major coverage gap.** Reconcile/dedupe these candidates into Quizbank; do not leave the durable course bank as an empty scaffold. |
| RCET3371 | `banks/rcet3371.bank.json` | 20 | RCET3371-planning retains 28 Git-focused questions across three JSON banks | **Reconciliation needed.** Determine overlap with the current 20-question durable starter bank and promote useful nonduplicates with provenance. |
| RCET3373 | `banks/rcet3373.bank.json` | 27 | `banks/rcet3373-w03-lookup-timing.bank.json` (10) and `banks/rcet3373-w03-interrupts.bank.json` (10) are already on `main` as review staging; PR #5 stages 3 taught Timer0 questions | **Current but not consolidated.** Tim review/promotion into the durable course bank remains the gate. Do not treat staging-bank presence as assessment approval. |
| RCET3375 | `banks/rcet3375.bank.json` | 18 | `banks/rcet3375-legacy-section01.bank.json` contains 21 legacy benchmark questions; RCET3375-planning retains a 36-question lab snapshot across six Lab 01/02 banks plus larger migration inventories | **Reconciliation needed.** Compare lab-specific planning items against the durable bank and legacy benchmark, then promote only distinct current lab-book/implementation/troubleshooting targets. |

## Durable model

- `banks/<course>.bank.json` is the long-lived course bank.
- Temporary review banks may live beside it when a topic set needs human review before promotion.
- Planning repositories remain valid provenance/staging sources, but they should not be treated as competing authored authorities.
- Generated `reference/F26/` Markdown is a review surface, not authored content.

## Current repository health

- `main` contains the JSON schema/tooling, validation CI, and full-bank PDF/Markdown review artifacts.
- Validation CI tests the checkout being proposed and compares feature/curriculum pushes against `main`.
- PR #5 (`curriculum/f26-w04-timer0-taught`) is mergeable and both validation and review-artifact workflows are green. It remains `reviewed: false` content awaiting Tim's review.
- The active Markdown-reference workflow previously depended on retired branches (`curriculum/f26-question-banks` and `agent/json-bank-cli`). The shared-authority cleanup replaces that dependency with the renderer and banks from the current checkout.
- The old all-branch source-audit workflow is migration-era automation. Its source inventory is already preserved; the workflow and its helper scripts are archived rather than kept active.

## Reconciliation order

1. Keep tooling/schema/workflows on `main` self-contained and branch-independent.
2. Review and decide current open Quizbank staging PRs without marking questions reviewed automatically.
3. RCET2265: promote the mature Weeks 1-2 planning candidates into a non-empty durable bank, deduping and preserving provenance.
4. RCET3371: reconcile the 28 planning Git questions against the 20-question durable starter bank.
5. RCET3373: promote accepted Week 3 and taught Week 4 staging questions into `rcet3373.bank.json`; retire staging banks after promotion.
6. RCET3375: reconcile the 36 planning lab questions and legacy benchmark against the durable lab bank, keeping theory ownership in RCET3373 and lab-specific measurement/implementation targets in RCET3375.
7. Once useful unique work has been preserved, retire obsolete development branches such as `agent/json-bank-cli` and `dunno`.
