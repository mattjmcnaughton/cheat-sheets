---
title: Refactoring Without Semantic Drift
bug_classes: [changed-evaluation-order, changed-aliasing-contract, lost-edge-case-behavior, changed-error-timing]
authority: individual
mechanizable: property-test
maturity: draft
last_reviewed: 2026-09-09
---

# Refactoring Without Semantic Drift

## Why review misses it

The new expression communicates the intent more clearly, so it looks equivalent.
The old expression also defined evaluation order, call count, exception timing,
mutation, and behavior on awkward inputs. Tests of ordinary return values can
stay green while any of those observable effects changes.

## The default

**Capture the old implementation's observable behavior before restructuring it,
then compare old and new on the same inputs and controlled dependencies; separate
intentional behavior changes from the refactor.**

## Rules

1. **State what must remain observable at the boundary.** Return values alone
   omit exceptions, effects, ordering, aliasing, and resource lifetimes.
2. **Add characterization cases before replacing the implementation.** Cases
   derived only from the new structure can miss behavior the old code contained.
3. **Keep discovered bug fixes separate from behavior-preserving edits.** A
   desirable correction still changes behavior and needs its own expectation.
4. **Preserve call count and evaluation order for effectful expressions.**
   Factoring a repeated call into a variable changes behavior if it reads time,
   consumes input, mutates state, or can fail.
5. **Check identity and mutation as well as value equality.** Returning an equal
   copy instead of an existing object changes what callers share and can mutate.
6. **Preserve eagerness, short-circuiting, and exception boundaries.** Moving
   work earlier can raise before validation or consume data the old path skipped.
7. **Control clocks, randomness, identifiers, and external effects in comparison
   tests.** Two executions against changing dependencies can disagree even when
   their implementations are equivalent.
8. **Make small transformations with a stable behavioral oracle.** Rewriting
   the code and every expected result together removes evidence of preservation.

For value and identity contracts, use [Equality and Ordering](../data/equality-and-ordering.md).
For ownership changes, use [Mutation and Aliasing](../state/mutation-and-aliasing.md).

## Anti-patterns

**"Use a shorter default expression."** A truthiness fallback reads naturally,
but it treats valid zero and empty values like absence. Preserve the exact
predicate when simplifying:

```python
# Wrong when zero is a valid explicit limit.
limit = supplied_limit or 100

# Right: preserve the distinction between zero and absence.
limit = 100 if supplied_limit is None else supplied_limit
```

**"Replace the loop with a lazy iterator."** Laziness avoids allocating a list,
but it moves work and failures into the caller's iteration and can outlive a
resource scope. Preserve eager evaluation, or make the lifetime and failure
change an explicit API change with its own tests.

**"Sort the output so the comparison passes."** Normalization removes noisy
differences, but sorting also hides an ordering regression when order is part of
the contract. Normalize only fields explicitly declared unobservable; compare
meaningful ordering and effect sequences directly.

**"Run both implementations on the real request."** Comparing production
results uses realistic inputs, but running both can send two messages or charge
twice. Compare inside an isolated replay environment or intercept effects before
they escape; choose exactly one implementation to perform real effects.

**"The old code is the specification."** Characterization preserves observed
behavior, including bugs. Use it to detect differences, then decide separately
which differences are corrections; do not treat passing characterization tests
as proof that the behavior is desirable or fully covered.

## What it costs

Keeping an old implementation or recorded behavior temporarily duplicates work.
Controlling dependencies requires a narrow seam around effects, and comparison
fixtures can be expensive to maintain. Capture only behavior that matters at the
boundary. Remove temporary comparison machinery after the change is established,
while retaining regression cases for meaningful edge conditions.

## Review questions

- Which observable behaviors must remain unchanged in this refactor?
- Were the expected results captured before replacing the implementation?
- Does any expression execute more often, earlier, or in a different order?
- Do equal results preserve the same mutation and identity promises?
- Can an exception now escape a different handler or occur during iteration?
- What differences does comparison normalization hide?
- Are intentional corrections separated from claims of equivalence?

## How to mechanize

**Property test — differentially compare old and new executions.** Generate
inputs from the supported domain, emphasizing empty values, boundaries, aliases,
and failures. Give each run an independent copy of the same initial state and
an equivalent scripted dependency trace. Compare return or exception outcome,
relevant final state, and ordered effects under an explicitly defined notion of
equivalence. Include exception type and timing when callers rely on them.

Ordinary types establish neither equivalence nor effect order. A static rename
can cover a bounded syntactic change, but static checks do not prove equivalence
for arbitrary restructuring; generated differential checks are the highest rung
used here. Passing samples provides evidence, not proof over every input.

Keep oracle fixtures independent of the new code. For nondeterministic fields,
inject deterministic dependencies before choosing to normalize output. Exercise
failures at dependency boundaries so a refactor cannot silently move work past a
commit, skip cleanup, or convert an expected error into a different outcome.

## References

- Martin Fowler, *Refactoring: Improving the Design of Existing Code*, second
  edition, 2018 — small transformations that preserve observable behavior.
- Martin Fowler, "Legacy Seam", January 2024 — identifying points where
  behavior can be substituted to bring existing code under test.
- Python Software Foundation, *Python 3 Language Reference*, "Expressions",
  "Boolean operations" and "Evaluation order" — short-circuit behavior and
  left-to-right expression evaluation.
