# RCET3371 Git bank reconciliation

Date: 2026-09-15

## Purpose

Reconcile the Fall 2026 Git banks authored in `RCET3371-planning` with the durable `banks/rcet3371.bank.json` authority before copying questions. This pass is deliberately an audit first: preserve stable durable IDs, preserve teaching provenance, and do not mark any question reviewed automatically.

## Sources inspected

Planning authority contains three Git banks grounded in W02D01 teaching evidence and its accuracy review:

- `rcet3371-f26-git-basics-states.bank.json`: 11 questions
- `rcet3371-f26-git-diff-recovery.bank.json`: 9 questions
- `rcet3371-f26-git-history.bank.json`: 8 questions

Total planning candidates: **28**.

The durable RCET3371 starter bank already contains Git material, including `git.workflow.001`, `git.workflow.002`, `git.hygiene.001`, and `git.hygiene.002`. Those existing durable items must not be duplicated merely because the planning banks use different IDs.

## Concept overlap

The following planning targets substantially overlap durable starter-bank concepts and should normally be reconciled into the existing durable family rather than added as near-duplicates:

| Planning target | Existing durable coverage | Action |
| --- | --- | --- |
| Git mental model / repository states | `git.workflow.001` | Keep durable item; use planning provenance/corrections when reviewing or revising it. |
| `git status` as first diagnostic | `git.workflow.002` | Keep durable item; planning `git.states.001` is a close variant. |
| generated files / secrets should not be tracked | `git.hygiene.001` | Keep durable item; do not add a second generic hygiene question unless it tests a different state transition. |
| `.gitignore` does not untrack existing tracked content | `git.hygiene.002` | Keep durable item; preserve planning recovery material for the actual untrack command. |

## High-value planning coverage missing from the durable Git starter family

These are distinct enough to justify promotion candidates after Tim review:

### Basics and state transitions

- Git versus GitHub (`git.basics.001`)
- local Git without a GitHub remote (`git.basics.002`)
- what `git init` creates (`git.repo.001`)
- role of `.git` (`git.repo.002`)
- what `git add` changes (`git.states.002`)
- what `git commit` records (`git.states.003`)
- `user.name` / `user.email` identity (`git.config.001`)
- centralized versus distributed repository authority (`git.repo.003`)
- staged and unstaged changes can coexist for one path (`git.states.004`)

The shell-redirection item `git.shell.001` is valid taught material but is lower priority for the durable RCET3371 Git concept bank because it tests shell behavior rather than Git itself.

### Diff and recovery

All nine planning questions add useful state-specific coverage beyond the durable starter bank, but some should be treated as variants rather than nine independent core concepts:

- bare `git diff` means working tree versus index (`git.diff.001`, `git.diff.002`)
- `git diff --staged` means index versus `HEAD` (`git.diff.003`)
- unstage while retaining the working file (`git.restore.001`, `git.restore.002`)
- stop tracking while retaining the working file with `git rm --cached` (`git.restore.003`)
- restore one path from an older commit without moving `HEAD` (`git.restore.004`)
- compare the three common diff views (`git.diff.004`)
- diagnose before restoring a damaged working-tree file (`git.restore.005`)

Recommended durable shape: keep one easy and one applied variant for the diff-state family, one applied unstage item, then retain the distinct untrack, historical-path restore, multi-view diff, and recovery-order targets. That avoids bloating the bank with wording variants while preserving assessment depth.

### History and object model

The eight history questions are largely new durable coverage:

- `git show` for a commit (`git.history.001`)
- `git log` for history (`git.history.002`)
- unique abbreviated object IDs (`git.history.003`)
- `git log -S` occurrence-count semantics (`git.history.004`)
- root/merge commit parent exceptions (`git.history.005`)
- commit object identity includes tree/parents/metadata/message, not only working files (`git.history.006`)
- amend replaces the tip commit and rewrites published history (`git.history.007`)
- applied diagnosis of the common `git log -S` misconception (`git.history.008`)

For the durable bank, `git.history.004` and `git.history.008` should be treated as a variant pair. The applied code-review version is stronger for a paper assessment; the direct MCQ is useful for practice.

## Promotion recommendation

Do **not** blindly append all 28 planning questions. A useful durable reconciliation is approximately **20-22 Git questions total**, counting the four existing durable Git questions. That provides enough variants for practice without turning equivalent wording into separate concepts.

Suggested promotion set from planning, all remaining `reviewed: false` until Tim review:

1. `git.basics.001`
2. `git.basics.002`
3. `git.repo.001`
4. `git.repo.002`
5. `git.states.002`
6. `git.states.003`
7. `git.config.001`
8. `git.repo.003`
9. `git.states.004`
10. one of `git.diff.001` / `git.diff.002`, with the second retained as a practice variant only if desired
11. `git.diff.003`
12. one of `git.restore.001` / `git.restore.002`
13. `git.restore.003`
14. `git.restore.004`
15. `git.diff.004`
16. `git.restore.005`
17. `git.history.001`
18. `git.history.002`
19. `git.history.003`
20. one of `git.history.004` / `git.history.008`, with the other retained as a practice variant if desired
21. `git.history.005`
22. `git.history.006`
23. `git.history.007`

Because four durable Git questions already exist and several entries above are variant choices, the final durable count should be chosen during content review rather than by an arbitrary numeric target.

## Provenance rule

When a planning question is promoted, carry forward its W02D01 teaching references and official Git documentation references into the durable question metadata/source fields. Do not replace those with a generic `starter-bank` origin. If a planning candidate supersedes an existing durable question, preserve the durable ID where practical and record the planning source as reconciliation provenance.

## Next step

Tim reviews the proposed keep/promote/variant decisions. After that review, update `banks/rcet3371.bank.json` in one controlled pass, validate the complete JSON bank, regenerate Markdown reference output, and render the full-bank instructor review artifact. No question should receive `metadata.reviewed=true` as part of mechanical reconciliation.