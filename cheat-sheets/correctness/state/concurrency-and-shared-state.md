---
title: Concurrency and Shared State
bug_classes: [lost-update, check-then-act-race, inconsistent-snapshot, deadlock]
authority: design
mechanizable: property-test
maturity: draft
last_reviewed: 2026-09-08
---

# Concurrency and Shared State

## Why review misses it

The diff shows one execution from top to bottom. The bug needs another
execution inserted between a check and its use, or between two field reads.
Individually synchronized methods can still compose into an unsynchronized
operation. Tests that run callers sequentially never construct the failing
history.

## The default

**Protect each shared invariant with one synchronization protocol that covers
the complete read, decision, and update, and require every participating reader
and writer to follow it.**

## Rules

1. **Prefer a single owner or immutable snapshots before sharing mutation.**
   Removing shared writes removes the need to coordinate those writes.
2. **Define the operation that must appear indivisible before choosing a lock.**
   Protecting individual fields does not protect a relationship between them.
3. **Use the same protocol on every path to the protected state.**
   **Needs design authority:** agree the protocol across shared APIs; one
   unlocked helper can invalidate the guarantee.
4. **Keep check-and-act inside one critical section or conditional update.**
   An observation made before acquiring the lock may already be obsolete.
5. **Acquire multiple locks in one documented order.** Opposite acquisition
   orders can leave each caller waiting for the other.
6. **Avoid blocking I/O and unknown callbacks while holding a lock.** They can
   stall other callers or reenter code that needs the same lock.
7. **Wait on a condition predicate while holding its associated lock.** A
   notification is a reason to recheck state, not a reservation of that state.
8. **Match the primitive to the concurrency boundary.** A thread lock does
   not coordinate another process or remote writer, and a blocking lock can
   stall an asynchronous event loop.

Use [Mutation and Aliasing](mutation-and-aliasing.md) for snapshot ownership,
and [Invariants Across Intermediate Steps](invariants-across-intermediate-steps.md)
for atomic publication and storage transactions.

## Anti-patterns

**"The container is thread-safe."** Safe individual operations are attractive,
but a membership test followed by removal is still two operations. Provide one
operation with a documented atomic boundary:

```python
# Wrong: two callers can both see an available item.
if stock[item] > 0:
    stock[item] -= 1

# Right: every stock reader and writer uses stock_lock.
with stock_lock:
    if stock[item] > 0:
        stock[item] -= 1
```

**"The interpreter serializes it."** Runtime behavior can hide interleavings
in a small test, but it is not a contract for a compound domain operation.
Use explicit synchronization instead of relying on interpreter scheduling.

**"Release the lock for the slow part, then continue."** This reduces lock
hold time but invalidates assumptions read before the release. Revalidate a
version when reacquiring the lock or retry the whole decision.

**"A sleep gives the other thread time."** Delays make the test appear
coordinated without fixing its schedule. Use barriers or explicit scheduler
hooks to place callers at the intended interleaving.

## What it costs

Locks serialize work and introduce waiting. Finer lock scopes increase the
number of protocols to reason about; one coarse lock can be easier to verify.
Optimistic updates avoid holding locks during work but require conflict
detection and retries. Neither approach guarantees fairness without a separate
progress contract.

## Review questions

- Which complete operation must look indivisible to another caller?
- Do all readers and writers use the same synchronization protocol?
- Can another caller change this value between the check and the write?
- Can this callback reenter the object while its lock is held?
- In what order does each path acquire these locks?
- What predicate does this waiter recheck after waking?
- Does this primitive coordinate every process or task that can access state?

## How to mechanize

**Property test — generate concurrent histories against a sequential model.**
For a stock allocator, generate reserve and release operations with stable
reservation identifiers. Schedule competing calls at read and write boundaries;
record invocation, completion, and result. Check that some sequential ordering
respects non-overlapping calls and produces those results without exceeding
capacity or releasing an unknown reservation.

Ordinary Python types do not express lock ownership. A lint can identify a
missing lock around a known field but cannot establish the full protocol
through arbitrary aliases and callbacks. Neither proves that complete
operations preserve the invariant, so generated histories are the applicable
rung here.

Include two callers taking the last item, inverse lock acquisition paths, and
a wakeup where another caller consumes the resource first. Use deterministic
scheduling hooks rather than hoping stress finds the interleaving. Bound test
completion to expose deadlock; a passing bound does not prove starvation freedom.
Retain minimized failing schedules as regression cases.

## References

- Maurice P. Herlihy and Jeannette M. Wing, *Linearizability: A Correctness
  Condition for Concurrent Objects*, ACM TOPLAS 12(3), 1990, DOI
  10.1145/78969.78972 — histories and atomic operation specifications.
- Python Software Foundation, *Python 3 Library Reference*, "threading",
  "Lock objects" and "Condition objects" — lock scope and predicate waits.
- Python Software Foundation, *Python 3 Library Reference*, "asyncio",
  "Synchronization Primitives" — task synchronization and thread-safety limits.
