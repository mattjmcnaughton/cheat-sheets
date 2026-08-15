---
title: Timeouts and Cancellation
bug_classes: [missing-deadline, timeout-budget-overrun, orphaned-work, cancellation-leak, unknown-completion]
authority: design
mechanizable: lint
maturity: draft
last_reviewed: 2026-08-15
---

# Timeouts and Cancellation

## Why review misses it

Every call returns quickly in tests, so an omitted deadline is invisible. A local
five-second timeout also looks bounded in isolation while three sequential calls,
retries, queueing, and cleanup consume twenty seconds. When timeout fires, control
returns to the caller and the diff appears finished, but work may still hold a
connection, commit remotely, or publish a result. The leak is in a different task
or process than the line review examines.

## The default

**Give each operation one absolute deadline, propagate its remaining budget through
every blocking call and retry, make cancellation cooperative with bounded cleanup,
and treat a timeout as unknown completion unless the operation proves otherwise.**

## Rules

1. **Accept and propagate an absolute deadline or cancellation context.** A fresh
   duration at each layer resets the budget; an absolute deadline preserves the
   caller's end-to-end limit. *(Design authority: shared interfaces must carry it.)*
2. **Set every blocking operation to no later than the remaining deadline.** Cover
   connection acquisition, DNS, reads, writes, locks, queues, subprocesses, and
   sleeps; one unbounded phase defeats the whole budget.
3. **Reserve budget for retries, response transfer, and cleanup.** Do not give the
   first dependency call the entire remaining interval, leaving no time to abort or
   return a useful result.
4. **Treat timeout as “the caller stopped waiting,” not “the effect did not
   happen.”** Query status or retry only with stable intent and idempotency; see
   [retries-and-idempotency](retries-and-idempotency.md).
5. **Make cancellation cooperative and poll at bounded intervals.** Long loops and
   streaming handlers must reach cancellation points; code that never yields
   cannot be cancelled safely.
6. **Release owned resources in unconditional cleanup.** Close bodies, roll back
   transactions, release locks, terminate or reap subprocesses, and unregister
   waiters even when cancellation interrupts an await.
7. **Define cancellation ownership.** Cancelling a child must not cancel unrelated
   siblings; cancelling a parent must reach every owned child. Use shielding only
   around short, mandatory cleanup.
8. **Detach work only by transferring ownership durably.** Before returning, put
   the job in a durable queue with status, deadline, idempotency identity, and an
   operator-visible owner; a spawned task is not durable background work.
9. **Use a monotonic clock to compute remaining local budget.** Wall-clock changes
   must not lengthen or shorten waits; convert an external deadline once, then
   measure elapsed time monotonically.

## Anti-patterns

**“Five seconds per call.”** Uniform local limits are easy to reason about. In a
call chain they reset repeatedly and exceed the user's budget; near expiry they
also start work that cannot possibly finish.

**“The timeout killed it.”** Returning from a wait feels like stopping the
operation. Threads, subprocesses, and remote servers may continue, so immediately
repeating a non-idempotent effect can perform it twice.

**“Catch cancellation and continue.”** Cleanup code wants to finish and broad
exception handlers want to preserve service. Swallowing the signal makes parents
believe a child stopped while it still owns resources; clean up, then re-raise.

**“Fire and forget.”** Detaching keeps request latency low. Process exit loses the
task, failures have no observer, and request-scoped credentials or connections may
vanish underneath it; transfer to durable owned work instead.

**“One timer around the handler.”** It bounds the response observed by the caller,
not queueing, blocked threads, remote work, or cleanup unless the signal reaches
those operations.

## What it costs

Deadline and cancellation parameters spread through interfaces, adapters, and test
doubles. Short budgets reject work that might have completed; generous cleanup
reserves reduce useful execution time. Cooperative cancellation adds checks to CPU
loops and cannot safely interrupt arbitrary foreign code. Durable detachment needs
a queue, status storage, workers, and reconciliation. Cleanup itself can block, so
you must choose between leaking a resource and abandoning graceful shutdown after
a second, bounded deadline.

## Review questions

- What is the end-to-end deadline, and where is it first established?
- Does each blocking phase use the remaining budget rather than a fresh timeout?
- How much budget remains for retries, response transfer, and cleanup?
- After this timeout, can the remote effect still commit, and how does the caller
  resolve that uncertainty?
- Which cancellation point stops long-running or streaming work?
- Which locks, transactions, bodies, subprocesses, and waiters are released on
  every cancellation path?
- Does detached work have durable ownership, status, identity, and a deadline?
- Can cancelling this child accidentally cancel shared or unrelated work?

## How to mechanize

**Type — unavailable as the ceiling.** A required `Deadline` or `Context` parameter
makes omission visible, but types cannot prove a callee propagates it, uses the
remaining budget, or cleans up when interrupted.

**Lint — the highest broadly enforceable rung.** Fail the build when production
code calls known blocking APIs without a deadline-bearing context or explicit
timeout; forbid creating a fresh root context below an entry point; flag spawned
tasks whose handle is neither awaited nor transferred to an approved durable
executor. Require cancellation exceptions to be re-raised after cleanup.

**Property test — schedule the races.** With a fake monotonic clock and controlled
futures, inject cancellation before, during, and after each await. Assert elapsed
budget never increases, no child outlives its owner, cleanup runs once, and retries
stop before the deadline.

**Runtime assertion — catch contract violations nearby.** Reject already-expired
work at entry, assert child deadlines do not exceed parent deadlines, and track
resource counts before and after cancellation in integration tests.

**Observation — find production leaks.** Measure deadline exceeded by operation and
phase, work continuing after caller cancellation, task age, open resources, and
detached jobs without owners. Alert on budget overruns and orphan age. No rung can
forcibly cancel arbitrary remote effects; only their protocol can expose status or
compensation.

## References

- [gRPC: Deadlines](https://grpc.io/docs/guides/deadlines/) — propagation, clock-skew conversion, and `DEADLINE_EXCEEDED` without proof the operation did not complete.
- [Go `context` package](https://pkg.go.dev/context) — the standard contract for deadlines, cancellation propagation, and releasing context resources.
- [Python `asyncio` task documentation](https://docs.python.org/3/library/asyncio-task.html) — cancellation injection, cleanup, shielding, timeout transformation, and task references.
- [POSIX `pthread_cancel`](https://pubs.opengroup.org/onlinepubs/9799919799/functions/pthread_cancel.html) — deferred cancellation, cancellation points, and cleanup handlers.
- [RFC 9110 §9.2.2, Idempotent Methods](https://www.rfc-editor.org/rfc/rfc9110#section-9.2.2) — retrying after a connection fails before a response is read.
