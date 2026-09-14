#import "inc.typ": *

#let tf_local = counter("paper-tf")
#let mc_local = counter("paper-mc")
#let fib_local = counter("paper-fib")
#let numeric_local = counter("paper-numeric")
#let sa_local = counter("paper-sa")
#let matching_local = counter("paper-matching")
#let ordering_local = counter("paper-ordering")
#let essay_local = counter("paper-essay")
#let cr_local = counter("paper-cr")

#let guarded(counter_obj, every, body, breakable: false) = [
  #counter_obj.step()
  #context [
    #let n = counter_obj.at(here()).last()
    #if every > 0 and n > 1 and calc.rem(n - 1, every) == 0 { pagebreak() }
    #if breakable or not keep_questions_together {
      body
    } else {
      block(width: 100%, breakable: false)[#body]
    }
  ]
]

#let render_tf(body) = guarded(tf_local, pagebreak_every_tf, body)
#let render_mc(body) = guarded(mc_local, pagebreak_every_mc, body)
#let render_fib(body) = guarded(fib_local, pagebreak_every_fib, body)
#let render_numeric(body) = guarded(numeric_local, pagebreak_every_numeric, body)
#let render_sa(body) = guarded(sa_local, pagebreak_every_sa, body)
#let render_matching(body) = guarded(matching_local, pagebreak_every_matching, body)
#let render_ordering(body) = guarded(ordering_local, pagebreak_every_ordering, body)
#let render_essay(body) = guarded(essay_local, pagebreak_every_essay, body)

// Code review starts at most one question per page and remains breakable so a
// long code listing plus follow-ups can continue naturally onto the next page.
#let render_cr(body) = guarded(cr_local, pagebreak_every_cr, body, breakable: true)
