---
title: Computation Correctness Overview
bug_classes: [wrong-result, violated-precondition, non-termination, nondeterministic-result, edge-case-failure]
authority: design
mechanizable: property-test
maturity: draft
last_reviewed: 2026-08-15
---

# Computation Correctness Overview

## Why review misses it

A plausible algorithm reads like a proof even when no proof exists. Reviewers
follow the happy path with ordinary values; they rarely enumerate empty input,
ties, extrema, malformed state, or a loop whose measure does not decrease.
Implicit iteration order and ambient time or randomness also hide because one
developer's run is stable. The diff shows operations, but not the precondition,
postcondition, or invariant that decides whether those operations are right.

## The default

**Write the precondition, postcondition, and a decreasing termination measure
before implementing a computation; reject inputs outside the domain and test
the resulting laws at empty, singleton, tied, and extreme inputs.**

## Rules

1. **State accepted inputs and promised outputs beside the interface.** Include
   units, ordering, mutation, precision, and failure behavior.
2. **Validate preconditions at the first boundary you control.** Do not let an
   invalid value travel until an unrelated operation fails.
3. **Express the result as independently checkable invariants.** For a sort,
   require both ordering and preservation of the input multiset.
4. **Choose an algorithm against declared bounds.** A correct exhaustive search
   is incorrect in practice when valid input makes completion unattainable.
   *(Design authority: agree bounds and latency with callers.)*
5. **Give every loop and recursion a well-founded measure that strictly
   decreases.** Treat retry loops as loops too; cap attempts or honor a deadline.
6. **Make ties and iteration order explicit.** Add a stable tiebreaker instead
   of inheriting map, filesystem, or scheduler order.
7. **Inject time, randomness, locale, and external state.** Keep the pure
   computation deterministic for the same explicit inputs.
8. **Handle empty, singleton, duplicate, boundary, and maximum-size inputs on
   purpose.** Return a defined result or a named error; never inherit an
   accidental exception.

## Anti-patterns

**“The examples pass.”** Examples communicate intent efficiently, but they
sample points rather than prove the rule between them.

**“This loop obviously finishes.”** The body usually advances; one continue,
retry, or rounding case leaves the measure unchanged and spins forever.

**“Any tied result is fine.”** That is valid only if callers agree. Otherwise a
hash iteration order leaks into output and creates flaky tests or changing
artifacts.

**“Normalize bad input and continue.”** Lenient parsing feels helpful, but it
silently changes the problem being solved. Reject values unless normalization
is part of the contract.

## What it costs

You spend design time naming contracts and writing independent oracles.
Deterministic sorting may add a tiebreak comparison; validation adds branches;
bounded algorithms may refuse work an unbounded version once attempted. These
costs buy reproducible failures and a defined domain rather than plausible
answers.

## Review questions

- What exact precondition does this change require, and where is it enforced?
- What postcondition lets us check the result without repeating the algorithm?
- What strictly decreases on every loop or recursive path?
- What happens for empty, singleton, duplicate, tied, and extreme inputs?
- Can valid input exceed this algorithm's time or space bounds?
- Which ambient values can change the result between identical calls?
- Is every invalid input rejected or handled by an explicit contract?

## How to mechanize

**Type — partial.** Use distinct types for units and validated domain values,
but recognize that a type rarely proves an algorithm's result or termination.

**Lint — partial.** Fail on unbounded retries, ignored parse errors, ambient
clock or random access inside designated pure modules, and iteration over
unordered collections when producing ordered output. Static shape cannot prove
semantic correctness.

**Property test — the highest useful rung.** Generate valid and invalid inputs,
including shrinking toward zero and boundaries. Assert the postconditions,
metamorphic laws, and equivalence to a small, simple reference implementation.
For sorting, assert ordered output and multiset preservation; for parsing,
assert `decode(encode(x)) == x`. Run identical inputs under varied hash seeds
and assert identical output.

**Runtime assertion and observation — retain the boundary checks.** Assert loop
budgets, output invariants, and impossible states. Record deadline exhaustion,
invariant failures, and repeated identical requests producing different result
digests. Observation detects violations; it cannot establish correctness.

## References

- C. A. R. Hoare, [An Axiomatic Basis for Computer Programming](https://doi.org/10.1145/363235.363259), *Communications of the ACM* 12(10), 1969 — preconditions, postconditions, and invariants.
- Edsger W. Dijkstra, [Guarded commands, nondeterminacy and formal derivation of programs](https://doi.org/10.1145/360933.360975), *Communications of the ACM* 18(8), 1975.
- Koen Claessen and John Hughes, [QuickCheck: A Lightweight Tool for Random Testing of Haskell Programs](https://doi.org/10.1145/351240.351266), ICFP 2000 — generated properties and shrinking.
- Python, [Reproducibility](https://docs.python.org/3/library/random.html#notes-on-reproducibility) — guarantees and limits for deterministic pseudo-random sequences.
