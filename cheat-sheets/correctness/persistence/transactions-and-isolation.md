---
title: Transactions and Isolation
bug_classes: [lost-update, write-skew, phantom-write, split-invariant, non-atomic-side-effect]
authority: design
mechanizable: property-test
maturity: draft
last_reviewed: 2026-08-15
---

# Transactions and Isolation

## Why review misses it

Each statement is correct against the state it reads. The bug exists only in an
interleaving: two transactions read the same version, independently pass a
check, then write a combined state neither observed. Unit tests execute one
transaction at a time, while mocks omit locks, constraints, snapshots, and
abort behavior. A diff also hides transaction boundaries in framework defaults
and isolation names whose guarantees differ from the invariant the code needs.

## The default

**Put every read and write needed to preserve one invariant in one transaction,
enforce the invariant with a database constraint where possible, and choose an
isolation guarantee that rejects every conflicting interleaving.**

## Rules

1. **Draw transaction boundaries around invariants, not repository methods or
   request convenience.** A check and every write justified by it belong in the
   same atomic unit. *(Design authority: agree on the invariant and its owning
   boundary.)*
2. **State the required phenomena, not only an isolation label.** Require, for
   example, that concurrent on-call removals cannot both commit; map that need
   to the actual datastore guarantee.
3. **Put row-local and relational invariants in constraints.** Uniqueness,
   foreign keys, and check constraints close paths that bypass application
   validation.
4. **Prevent lost updates deliberately.** Use an atomic conditional update, a
   version predicate, a lock, or isolation that aborts a stale writer; a
   read-modify-write sequence alone is unsafe.
5. **Treat multi-row absence checks as write-skew candidates.** Two writers can
   alter different rows after reading the same valid snapshot; lock a stable
   predicate, materialize the invariant into a constrained row, or require
   serializable execution.
6. **Protect predicates against phantoms.** If correctness depends on “no row
   matches,” require predicate/range protection or make the forbidden condition
   a unique constrained key.
7. **Handle transaction abort as a normal result.** Roll back the whole unit and
   return a retryable outcome; retry policy and concurrency control belong at a
   higher boundary, not inside individual statements.
8. **Keep irreversible external effects out of the commit gap.** Record an
   intent in the same transaction, publish it after commit, and make consumers
   deduplicate by a stable identifier; a database rollback cannot unsend a
   message or reverse an API call.
9. **Keep transactions short without splitting the invariant.** Perform remote
   calls and expensive computation before opening the transaction, then
   revalidate assumptions inside it.

## Anti-patterns

**“Validation passed, then save.”** Separating validation from persistence
keeps layers clean, but another transaction can change the premise between the
two operations. Recheck and write atomically, backed by a constraint when the
invariant is expressible.

**“Repeatable reads prevent races.”** A stable snapshot prevents changing
answers to some reads, yet two transactions can update disjoint rows and create
write skew. Demand the exact conflict behavior rather than trusting the label.

**“One transaction per row.”** Small transactions reduce lock time. They also
split a multi-row invariant, exposing valid intermediate states that combine
into an invalid final state.

**“Count, then insert.”** Checking that a range has capacity reads naturally.
Concurrent inserts can both observe room, and a new matching row is a phantom;
reserve capacity atomically or constrain a materialized counter/key.

**“Send, then commit.”** Sending first avoids losing the notification after a
commit. A later rollback produces a notification for state that never existed;
sending after commit has the opposite loss window. Persist an intent atomically
and dispatch it with deduplication.

## What it costs

Stronger isolation and predicate protection increase aborts, lock waits, and
bookkeeping; hot constrained rows can become bottlenecks. Constraints require
schema changes and return less domain-friendly errors unless translated.
Version predicates and retries add control flow. Persisted effect intents add a
table, dispatcher, retention, deduplication state, and delivery lag; they give
atomic intent, not instantaneous or exactly-once external execution. Shortening
transactions improves throughput only while the complete invariant remains
inside the boundary.

## Review questions

- Which invariant does this transaction preserve, in one sentence?
- Are every read, check, and write that justifies that invariant inside one
  transaction?
- Which concurrent interleaving would cause a lost update or write skew here?
- Does any decision depend on no matching row existing, and what prevents a
  phantom?
- Which constraint independently rejects the invalid final state?
- What exact isolation guarantees does this datastore provide for these reads
  and writes?
- What does the caller do when commit aborts?
- Can an external effect happen without the state commit, or the commit without
  a durable effect intent?

## How to mechanize

**Type is unavailable for isolation.** Types can distinguish a transaction
handle and prevent calls outside its lexical scope, but they cannot prove that
concurrent executions preserve a data-dependent invariant.

**Lint is only a guardrail.** Fail the build when persistence code sends network
effects inside a transaction callback, or when a transaction handle escapes
its scope. Static syntax cannot infer multi-row invariants or datastore
isolation semantics, so lint is not the highest useful rung.

**Property test — the highest reachable rung.** Generate pairs and triples of
operations plus scheduler barriers after reads and before writes; execute all
interleavings against the real datastore and assert the invariant after every
commit. Include identical-row lost updates, disjoint-row write skew, absent-row
phantoms, abort injection, and effect-intent deduplication. Record the isolation
configuration with the test so a default change cannot silently weaken it.

**Runtime assertion — constraints are the final gate.** Encode uniqueness,
references, bounds, and materialized aggregate limits in schema constraints;
check affected-row counts for versioned updates and fail when the expected
version did not match. Assert one durable intent identifier per logical effect.

**Observation detects escapees, not correctness.** Reconcile cross-row and
cross-table invariants, alert on constraint violations and serialization-abort
rates, and compare committed effect intents with completed deliveries. A quiet
dashboard cannot exclude an untested interleaving, so observation does not
replace constraints and schedule-controlled property tests.

## References

- Jim Gray, [The Transaction Concept: Virtues and Limitations](https://jimgray.azurewebsites.net/papers/thetransactionconcept.pdf) (1981) — atomic units, consistency, and recovery foundations.
- Hal Berenson et al., [A Critique of ANSI SQL Isolation Levels](https://www.microsoft.com/en-us/research/publication/a-critique-of-ansi-sql-isolation-levels/) (SIGMOD 1995) — lost update, phantoms, and the limits of phenomenon-based isolation definitions.
- Atul Adya, [Weak Consistency: A Generalized Theory and Optimistic Implementations for Distributed Transactions](https://pmg.csail.mit.edu/papers/adya-phd.pdf) (MIT, 1999) — dependency-based definitions of isolation anomalies.
- Alan Fekete et al., [Making Snapshot Isolation Serializable](https://doi.org/10.1145/1071610.1071615) (ACM TODS, 2005) — write skew under snapshot isolation and conditions for preventing it.
- Martin Kleppmann et al., [A Highly-Available Move Operation for Replicated Trees](https://martin.kleppmann.com/papers/move-op.pdf) (2018), Appendix A — a compact formal account of transactions and isolation anomalies; use the anomaly definitions, not its distributed design.
- Hector Garcia-Molina and Kenneth Salem, [Sagas](https://doi.org/10.1145/38713.38742) (SIGMOD 1987) — primary evidence that external or long-lived effects need explicit compensation semantics rather than ordinary rollback.
