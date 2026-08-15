---
title: Persistence Correctness Overview
bug_classes: [lost-update, write-skew, constraint-race, torn-workflow, durability-assumption, storage-model-mismatch]
authority: design
mechanizable: property-test
maturity: draft
last_reviewed: 2026-08-15
---

# Persistence Correctness Overview

## Why review misses it

Each statement is correct in isolation. The defect lives between statements,
between two transactions, or between an acknowledged commit and a crash. Unit
tests run one writer against an empty store and replace the storage engine with
a map, hiding isolation, constraints, locking, serialization failures, replicas,
and durability settings. A reviewer cannot infer the actual guarantee from a
method named `save`.

## The default

**State each persistent invariant, enforce it in the storage system, and update
all data needed for that invariant in one retryable transaction at an isolation
level proven sufficient under concurrent execution.**

## Rules

1. **Write the invariant before the transaction.** Name what must remain unique,
   referenced, non-negative, ordered, or mutually exclusive; then choose schema,
   constraint, and transaction boundaries from it.
2. **Enforce invariants with storage constraints.** Use primary, unique, foreign
   key, check, and exclusion constraints rather than a read-then-decide check
   that races another writer.
3. **Make the transaction match the business atomic unit.** Commit all related
   rows and the durable intent for any later external effect together; never
   expose half of a workflow as complete.
4. **Choose isolation from the anomaly you must prevent.** Do not equate
   “transactional” with serial execution; prove the chosen level prevents lost
   updates, write skew, phantoms, and stale decisions relevant to the invariant.
   *(Design authority: every writer must use the compatible protocol.)*
5. **Update from the expected version or current value atomically.** Use a
   compare-and-swap version predicate, atomic increment, or locked row; treat
   zero affected rows as a conflict rather than overwriting a concurrent edit.
6. **Retry the whole transaction on serialization failure or deadlock.** Start
   from fresh reads, bound attempts with jitter, and keep external side effects
   outside the retried closure.
7. **Use the storage model it actually provides.** Define partition and sort
   keys, consistency of reads, null and uniqueness semantics, and cross-record
   atomicity explicitly; do not project relational guarantees onto a key-value,
   document, log, cache, or object store.
8. **Define when “committed” is durable enough.** Record the required flush,
   replication, acknowledgement, and failover guarantee, and test under the
   production settings rather than relying on the API verb.
9. **Evolve schema and writers compatibly.** Deploy additive schema first,
   tolerate old and new representations during migration, backfill idempotently,
   validate constraints, then remove the old path.

## Anti-patterns

**“Check, then insert.”** The preflight check gives a friendly error and avoids
handling constraint failures, but two transactions can both pass it. Keep the
check for ergonomics; let the constraint decide correctness.

**“Last write wins is simplest.”** It resolves conflicts without coordination,
but silently discards one valid edit when updates derive from a stale snapshot.

**“It is inside a transaction, so races are impossible.”** Transactions provide
the configured isolation level, not automatic serializability. Two individually
valid transactions can jointly violate a cross-row invariant.

**“The in-memory repository implements the contract.”** A map makes tests fast,
but usually has stronger reads, simpler nulls, no deadlocks, and different
constraints. It verifies domain branching, not persistence behavior.

**“Commit returned, so no acknowledged data can disappear.”** The call may
acknowledge before local media flush or replica confirmation, depending on
configuration. Name and test the durability point you require.

## What it costs

Constraints and stronger isolation add contention, aborts, and operational
care. Version columns complicate APIs; retry loops increase tail latency;
durable synchronous acknowledgement costs throughput. Compatible migrations
temporarily duplicate representations and code. Narrow transactions, indexes,
partitioned ownership, and commutative updates can reduce contention without
weakening the invariant.

## Review questions

- What persistent invariant does this change preserve, and where is it enforced?
- Can two concurrent executions both pass this read and then conflict on write?
- Which isolation anomaly would violate the invariant at the configured level?
- Does the transaction include every row and durable intent in the business
  operation, but exclude remote side effects?
- How does this update detect a stale version or lost race?
- Which failures retry the whole transaction, and is the retry body effect-free?
- What exactly does acknowledgement guarantee across crash and failover?
- Can old and new application versions safely share this schema during rollout?

## How to mechanize

**Type cannot carry the central guarantee.** Distinct IDs, versions, and
validated records prevent category mistakes, but a type checker cannot see
another transaction or the deployed durability setting.

**Lint — guard transaction shape.** Reject remote calls inside transaction
callbacks, writes without a transaction in designated modules, and updates to
versioned tables lacking a version predicate. Static checks cannot establish
cross-process isolation.

**Property test — reach the highest useful rung.** Generate operation histories,
run them under barriers that force competing reads before writes, and assert
constraints and conservation laws after every commit. Replay transactions after
injected serialization failures and crashes; assert the final state equals some
legal serial ordering and no committed operation is applied twice.

**Runtime assertion — let storage reject invalid state.** Install constraints,
check affected-row counts, reject unknown schema versions, and fail closed when
the configured isolation or durability mode is weaker than required.

**Observation — reconcile production state.** Count constraint violations,
deadlocks, serialization retries, stale-version conflicts, replication lag, and
failed backfills. Run invariant queries that find orphaned, duplicate, negative,
or otherwise impossible records and alert before repairing them.

## References

- ISO/IEC, [SQL standards catalogue (ISO/IEC 9075)](https://www.iso.org/standard/76583.html) — the governing SQL transaction and constraint standard.
- PostgreSQL, [Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html) — anomalies, serialization failures, and retry requirements.
- PostgreSQL, [Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html) — primary, unique, foreign-key, check, and exclusion enforcement.
- PostgreSQL, [Reliability and the Write-Ahead Log](https://www.postgresql.org/docs/current/wal-reliability.html) — flush, media, and durability assumptions.
- SQLite, [Atomic Commit](https://www.sqlite.org/atomiccommit.html) — concrete crash and storage assumptions behind transactional commit.
- Berenson et al., [A Critique of ANSI SQL Isolation Levels](https://www.microsoft.com/en-us/research/publication/a-critique-of-ansi-sql-isolation-levels/), SIGMOD 1995 — formalizes common isolation anomalies beyond dirty reads.
