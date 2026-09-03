---
title: Capacity Correctness Overview
bug_classes: [unbounded-queue, memory-exhaustion, disk-exhaustion, overload-collapse, missing-backpressure, silent-work-loss]
authority: design
mechanizable: property-test
maturity: draft
last_reviewed: 2026-08-15
---

# Capacity Correctness Overview

## Why review misses it

Every request succeeds in isolation, so the handler looks correct. The failure
lives in totals and rates outside the diff: arrivals exceed completions, queued
objects retain memory, retries amplify load, or disk fills hours later. Fast
fixtures never hold a producer above a consumer's rate, and mocks make every
downstream dependency immediately available. An unbounded queue therefore
looks safer than refusal until it consumes the process.

## The default

**Bound every resource and queue, admit work only while capacity exists, and
propagate backpressure or return an explicit retryable refusal before the
system exhausts memory, disk, threads, connections, or deadlines.**

## Rules

1. **Assign a hard bound to every queue, batch, cache, upload, worker pool,
   connection pool, and retained artifact.** “Available memory” is not a bound.
2. **Choose admission behavior before saturation.** Reject, shed, sample, or
   defer work explicitly; never let allocation decide by crashing.
   *(Design authority: callers must understand refusal and retry semantics.)*
3. **Propagate backpressure to the producer.** Stop reads, reduce concurrency,
   or block within a deadline instead of buffering an unlimited rate mismatch.
4. **Reserve capacity for recovery and health operations.** Keep cancellation,
   status, cleanup, and administrative traffic from competing in the saturated
   pool they must repair.
5. **Bound retries by attempts and deadline, and add jitter.** Retries consume
   the same constrained resource and can turn overload into sustained collapse.
6. **Account for bytes, not only item counts.** Ten messages can exceed memory
   when one message is enormous; enforce per-item and aggregate limits.
7. **Put quotas and retention on disk growth.** Include logs, temporary files,
   dead letters, caches, and partially uploaded objects in the budget.
8. **Fail partially accepted work explicitly.** Acknowledge only after durable
   admission, or return a token whose state distinguishes queued, rejected, and
   completed work.

## Anti-patterns

**“Buffer the spike.”** A bounded burst buffer is useful; an unbounded one only
moves overload into memory and increases the age of already-doomed work.

**“Add more workers.”** Concurrency raises throughput until the bottleneck;
beyond it, workers multiply contention, connections, and queued requests.

**“Never reject customer traffic.”** Refusal feels like failure, but controlled
refusal preserves useful service while indiscriminate acceptance causes timeouts
and process-wide failure.

**“Retry until it works.”** Retries handle transient faults, but without a
budget they amplify the exact dependency that is already saturated.

**“Count jobs, not size.”** Uniform test jobs make counts convenient. Production
payload variance makes one admitted item consume the entire byte budget.

## What it costs

You reject work that an unconstrained system might have completed during a
short spike, and clients must implement deadlines and retryable refusal.
Resource accounting, reserved pools, and per-tenant quotas add state and policy.
The benefit is a known failure mode with bounded blast radius instead of a slow
queue followed by global exhaustion.

## Review questions

- What resource grows with each admitted unit, and what is its hard bound?
- What happens at the bound: block, reject, shed, or overwrite?
- How does the producer learn that the consumer is saturated?
- Are both item count and total bytes constrained?
- Can retries or fan-out multiply one request into unbounded work?
- Is capacity reserved for cancellation, cleanup, and health checks?
- What fills disk if this path runs continuously for a week?
- When is accepted work acknowledged, and can it still be lost afterward?

## How to mechanize

**Type — unavailable for aggregate capacity.** A bounded-item type can enforce
one payload's size, but ordinary types cannot track process-wide memory, disk,
or concurrent admissions.

**Lint — partial.** Fail on queue constructors without a capacity, retries
without attempt and deadline arguments, reads without byte limits, and temporary
files without cleanup. A static check cannot know whether the chosen bound fits.

**Property test — the highest repeatable rung.** Generate producer and consumer
rates, payload sizes, cancellation, and downstream stalls. Assert queue length,
resident bytes, concurrency, and retry count never exceed configured bounds;
assert every item is exactly one of rejected, queued, completed, or explicitly
failed. Use a deterministic scheduler or model so overload interleavings shrink.

**Runtime assertion and observation — enforce real budgets.** Reject admission
atomically when counters would exceed limits. Export queue items and bytes,
oldest-item age, refusals, retries, memory, disk free space, and pool saturation;
alert before the recovery reserve is consumed. Load tests and metrics validate
chosen limits, but cannot prove behavior under every production dependency.

## References

- IETF, [RFC 9110 §15.6.4: 503 Service Unavailable](https://www.rfc-editor.org/rfc/rfc9110#section-15.6.4) — explicit temporary refusal and `Retry-After`.
- IETF, [RFC 6585 §4: 429 Too Many Requests](https://www.rfc-editor.org/rfc/rfc6585#section-4) — rate-limit refusal semantics.
- Reactive Streams, [Specification](https://github.com/reactive-streams/reactive-streams-jvm/blob/v1.0.4/README.md) — asynchronous flow control with bounded demand.
- AWS, [The Amazon Builders' Library: Avoiding insurmountable queue backlogs](https://aws.amazon.com/builders-library/avoiding-insurmountable-queue-backlogs/) — primary engineering account of queue age, load shedding, and retry amplification.
