---
title: State Correctness Overview
bug_classes: [invariant-violation, lost-update, stale-read, resource-leak, duplicate-transition]
authority: design
mechanizable: assertion
maturity: draft
last_reviewed: 2026-08-15
---

# State Correctness Overview

## Why review misses it

Each line can perform a legal read or write while the sequence is illegal. The
missing fact is temporal: another reference mutates the object, another worker
writes between check and update, a retry repeats a transition, or an error path
skips cleanup. Unit tests execute one favorable ordering with fresh state, so a
reviewer sees neither the interleaving nor the lifetime that breaks the
invariant.

## The default

**Put each mutable invariant behind one owner, perform each state transition as
one atomic and retry-safe operation, and make acquisition, visibility, and
release explicit.**

## Rules

1. **Write the invariant beside the state and enforce it at the mutation
   boundary.** Do not require every caller to reconstruct which combinations of
   fields are legal.
2. **Assign one owner to mutable state.** Cross ownership boundaries with
   commands or snapshots, following
   [Mutation and Aliasing](mutation-and-aliasing.md) for object graphs.
3. **Combine check and update atomically.** Use a transaction, conditional
   write, compare-and-swap, or lock over the whole invariant; a check followed
   by an unguarded write loses races.
4. **Define every transition from a named prior state.** Reject illegal and
   duplicate transitions instead of treating them as harmless assignments.
5. **Make retries safe before enabling them.** Carry an operation identity or
   make the transition naturally idempotent, and return the recorded outcome
   when the same operation arrives again.
6. **Acquire resources only with guaranteed release.** Bind files, locks,
   transactions, and subscriptions to lexical scope or a `finally` path, and
   handle partial acquisition in reverse order.
7. **Choose the visibility guarantee each reader needs.** Do not let a cache,
   replica, or snapshot answer when the caller requires read-your-writes or a
   fresh decision.
8. **Version concurrent writes.** Reject a write based on stale state with an
   expected version rather than silently replacing a newer value.
9. **Agree on atomic boundaries and consistency guarantees.** *(Design
   authority: all writers and readers must preserve the same invariant and
   interpret versions, retries, and stale reads consistently.)*

## Anti-patterns

**"Check, then act."** Reading before writing makes validation clear, but
another writer can change the premise between those operations. Put the
condition into the atomic write.

**"The assignment is atomic."** One field write may be indivisible while the
business transition spans several fields, records, or side effects. Readers can
still observe an impossible intermediate state.

**"Retry the whole function."** Retries improve availability only after the
operation survives duplication. Otherwise a timeout can turn one charge,
increment, or message into two.

**"Cleanup happens at the end."** The normal path reaches the final `close`;
exceptions, cancellation, and early returns do not. Bind release when you
acquire.

**"The cache is only an optimization."** Once a decision reads it, stale data
changes behavior. Define its permitted age and bypass it where freshness is a
correctness requirement.

## What it costs

Ownership narrows convenient access, atomic transitions add contention, and
version checks force callers to retry or resolve conflicts. Idempotency records
consume storage, while stronger reads add latency and reduce availability.
Resource scopes can hold capacity longer than hand-tuned release. Choose the
weakest guarantees that still preserve the named invariant, and document where
staleness or duplication is acceptable.

## Review questions

- What invariant must hold before and after this transition, and where is it
  enforced?
- Who can mutate this state, through which operation?
- Can another writer act between this check and update?
- What happens if this operation runs twice after a timeout?
- Can any reader observe the intermediate state?
- Which resource remains acquired on each error, cancellation, and early-return
  path?
- Can this write overwrite a value read from an older version?
- How stale may this read be before its decision becomes wrong?

## How to mechanize

**Type — use it for ownership and transition vocabulary, but do not claim it
proves interleavings.** Expose immutable snapshots, private mutable storage, and
state-specific command types. Use scoped resource guards and ownership types
where available. Types cannot prove that a database transaction includes every
participating writer.

**Lint — reject visible lifecycle mistakes.** Fail the build on unscoped
resource acquisition, mutable global state, discarded transaction results, and
read-modify-write helpers that lack a lock, transaction, or expected version.
Static checks cannot determine whether a chosen lock protects the full domain
invariant.

**Property test — generate sequences, not just values.** Apply legal, illegal,
duplicate, and reordered commands to a model and implementation; assert equal
outcomes and the invariant after every step. Inject failures after each resource
acquisition and side effect.

**Runtime assertion — the highest dependable baseline.** Put invariant checks
and allowed-transition checks inside the owner. Make conditional writes assert
the expected version, track resource state to reject double-close and
use-after-close, and store operation identities under a uniqueness constraint.

**Observation — cover state shared beyond one assertion boundary.** Reconcile
derived state against its source, alert on impossible state combinations,
version conflicts, duplicate-operation attempts, leaked-resource growth, and
cache age beyond its contract. Metrics detect violations; they do not make a
multi-step update atomic.

## References

- ISO/IEC, [ISO/IEC 9075-2:2023](https://www.iso.org/standard/76584.html) — the SQL foundation standard covering transactions and integrity constraints.
- PostgreSQL, [Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html) — authoritative documentation of anomalies, isolation levels, and serialization failures.
- Python, [The `with` statement](https://docs.python.org/3/reference/compound_stmts.html#the-with-statement) — language-defined guaranteed cleanup around execution.
- C. A. R. Hoare, [Monitors: An Operating System Structuring Concept](https://doi.org/10.1145/355620.361161), *Communications of the ACM* 17(10), 1974 — encapsulating shared state and synchronizing operations over it.
- Chris Newcombe et al., [How Amazon Web Services Uses Formal Methods](https://www.amazon.science/publications/how-amazon-web-services-uses-formal-methods), *Communications of the ACM* 58(4), 2015 — a primary account of model checking distributed protocols and finding subtle execution sequences.
