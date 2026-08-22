// Quizbank paper-renderer controls.
// Based on the RCET3375 modular Typst assessment layout used in Spring 2026.

// Maximum questions of each type before a forced page break.
// Typst may break earlier when the remaining page space is insufficient.
#let pagebreak_every_tf = 15
#let pagebreak_every_mc = 5
#let pagebreak_every_fib = 10
#let pagebreak_every_numeric = 5
#let pagebreak_every_sa = 5
#let pagebreak_every_matching = 2
#let pagebreak_every_ordering = 3
#let pagebreak_every_essay = 1
#let pagebreak_every_cr = 1

// Student response-space defaults.
#let sa_lines_default = 3
#let cr_lines_per_followup = 3

// Keep ordinary questions together when they fit on a page.
// Code-review questions are allowed to continue because code plus follow-ups
// can legitimately exceed a page.
#let keep_questions_together = true
