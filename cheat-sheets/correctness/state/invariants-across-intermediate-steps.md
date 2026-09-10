---
title: Invariants Across Intermediate Steps
bug_classes: [partial-publication, write-skew, mixed-version-read, partial-failure-state]
authority: design
mechanizable: property-test
maturity: draft
last_reviewed: 2026-09-08
---

# Invariants Across Intermediate Steps

## Why review misses it

The final state is valid, and each assignment is valid on its own. A reader
running between assignments sees a combination the author never intended to
publish. A failure between writes can preserve that combination indefinitely.
Even a transaction can leave the business rule unprotected when two concurrent
decisions read compatible snapshots and update different rows.

## The default

**Publish every change to a shared invariant as one atomic transition, and make
readers observe one coherent version of all state used to check that invariant.**

## Rules

1. **Write the invariant as a predicate over the complete state it constrains.**
   A rule involving two rows cannot be established by validating each alone.
2. **Define which intermediate states are private and which are observable.**
   **Needs design authority:** agree the publication boundary with every reader
   of the shared representation.
3. **Build and validate replacement state before publishing it.** Exceptions
   during construction must not leave the shared object half updated.
4. **Put related durable writes in one storage transaction where possible.**
   Independent commits expose partial completion to other readers.
5. **Choose isolation for the decision as well as atomicity for the writes.**
   Concurrent transactions can violate a cross-row predicate unless the
   isolation level, locking, or constraints protect it.
6. **Read related values from one snapshot or under the same lock.** Two reads
   can each be correct yet come from different committed versions.
7. **Handle transaction abort by redoing the whole decision from fresh state.**
   Retrying only the final write reuses assumptions the conflict invalidated.
8. **Keep irreversible effects outside a transaction's retryable body.** A
   database rollback cannot retract a delivered message or external charge.

Use [Concurrency and Shared State](concurrency-and-shared-state.md) for lock
protocols. If the invariant crosses independent services, use
[Partial Writes Across Services](../contracts/partial-writes-across-services.md);
one service's transaction cannot provide global atomicity.
For transitions between stored representations, see
[Migrations and Backfills](../change/migrations-and-backfills.md).

## Anti-patterns

**"Replace the collection in place."** Reusing the object keeps references
stable, but readers can see it empty or partially rebuilt. Publish a completed
snapshot instead; all readers must acquire the same lock when obtaining it:

```python
# Wrong: readers can see an empty or partial collection.
state["routes"].clear()
state["routes"].extend(load_routes())

# Right: build privately, then publish under the shared protocol.
replacement = tuple(load_routes())  # Route values must also be immutable.
with state_lock:
    state["routes"] = replacement
```

**"It is in a transaction."** Atomic commit hides unfinished writes, but
snapshot isolation can still allow two callers to each remove a different
last-responsible worker. Protect the predicate with serializable execution or
an explicit locking or constraint design.

**"Read committed means the report is consistent."** Each statement may read
committed data from a different moment. Use one suitable snapshot for a report
whose fields must describe the same version.

**"Catch the exception and undo the first step."** Compensation looks like
rollback, but another reader may already have seen the intermediate state and
the undo can fail too. Use an atomic boundary or expose a named pending state
whose handling is part of the contract.

## What it costs

Private construction temporarily holds old and new state in memory. Locks and
stronger isolation can introduce waiting or transaction aborts. Long snapshots
can retain old storage versions. If global atomicity is unavailable, explicit
pending states move complexity into every consumer and recovery path.

## Review questions

- What exact predicate must remain true across these writes?
- Can a reader observe this object between the two assignments?
- What state remains if the second step raises or the process stops?
- Does this transaction protect the predicate against concurrent decisions?
- Do these reads describe one snapshot or several different moments?
- On conflict, does the retry reread all inputs to the decision?
- Can anything outside the transaction observe an effect before commit?

## How to mechanize

**Property test — inject failures and readers between transition steps.**
Generate valid initial states and operations, then stop execution before and
after each mutation and publication point. Run the real reader through its
normal synchronization path. Assert that it sees a valid old or new state,
never an invalid mixture. After injected failure and recovery, check the same
predicate again.

A type can represent valid snapshots but cannot prove that multiple reads came
from one snapshot. Static checks can require transaction wrappers without
proving the chosen isolation protects a domain predicate. Generated histories
are the highest applicable rung for this cross-step behavior.

For a cross-row rule, use two real database sessions: make both read the
predicate before either writes, then attempt both commits. Require an abort or
an invariant-preserving result. Verify the retry performs fresh reads. A mock
transaction cannot establish the actual database's isolation behavior.

## References

- PostgreSQL Global Development Group, *PostgreSQL 18 Documentation*, §13.2,
  "Transaction Isolation" — statement snapshots, repeatable read, serialization
  failures, and transaction retries.
- Hal Berenson et al., *A Critique of ANSI SQL Isolation Levels*, ACM SIGMOD
  1995, DOI 10.1145/223784.223785 — snapshot isolation and write skew.
