---
title: Bounded Work and Backpressure
bug_classes: [unbounded-backlog, hidden-waiter-growth, fanout-overload, capacity-leak, silent-load-shedding]
authority: design
mechanizable: property-test
maturity: draft
last_reviewed: 2026-09-10
---

# Bounded Work and Backpressure

## Why review misses it

Each request allocates a reasonable amount of memory and launches a reasonable
number of tasks. The failure appears when more requests arrive than finish.
A worker limit looks like a work limit, but a submission queue or a collection
of suspended tasks can keep growing behind it. Tests that wait for each result
before sending the next request never exercise this accumulation.

## The default

**Admit work only within explicit budgets for queued items, retained bytes, and
active operations; when a budget is exhausted, propagate waiting to a bounded
producer or return the agreed overload outcome before creating more work.**

## Rules

1. **Account for queued, active, and waiting work separately.** A semaphore
   around execution limits active operations, not the number of tasks already
   created and waiting to acquire it.
2. **Bound bytes as well as item counts.** Enforce a maximum item size or
   reserve weighted capacity; ten arbitrarily large payloads are not a memory
   bound, and decoded copies need their own allowance.
3. **Reserve capacity before spawning tasks or materializing large payloads.**
   Otherwise work consumes the resource while it waits for permission to use
   it; count already-buffered input against a separate bounded allowance.
4. **Choose an explicit overload policy for each admission boundary.**
   **Needs design authority:** agree whether callers wait, receive rejection,
   or permit loss; never silently drop work whose contract promises processing.
5. **Propagate downstream saturation all the way to the source.** Replacing a
   full queue with another queue or a new waiting task moves the backlog rather
   than bounding it.
6. **Apply shared budgets across fan-out and retries.** **Needs design
   authority:** per-request limits multiply across simultaneous requests, and
   retries consume the same capacity as fresh work; coordinate the budget with
   [retry behavior](../contracts/retries-and-idempotency.md).
7. **Release reservations on completion, rejection, and cancellation.** A
   reservation leaked on one failure path permanently shrinks capacity; use the
   ownership discipline in [resource lifecycle](../state/resource-lifecycle.md).
8. **Avoid waiting for capacity while holding resources the consumer needs.**
   A producer holding a required lock or worker slot can prevent the consumer
   from making space, turning backpressure into deadlock.

## Anti-patterns

**"The worker pool has only eight workers."** This limits simultaneous
execution but says nothing about pending submissions. Use a bounded admission
queue before submission and include queued payloads in the byte budget.

**"Each task acquires the semaphore first."** Millions of suspended tasks can
retain millions of payloads. Acquire before task creation, or use a fixed set
of workers reading a bounded queue. Ensure producers waiting to enqueue are
bounded too.

**"Check the queue size before adding."** The check seems readable, but another
producer can consume the remaining slot between check and insertion. Use the
queue's atomic nonblocking insertion and handle its full outcome. Here `jobs`
is an existing queue with a positive finite `maxsize`; `reject` reports the
agreed overload result.

```python
from queue import Full

# Wrong: admission and insertion are separate operations.
if jobs.qsize() < jobs.maxsize:
    jobs.put(payload)

# Right: insertion decides whether a slot is available.
try:
    jobs.put_nowait(payload)
except Full:
    reject(payload)
```

**"The bounded buffer drops old entries automatically."** That is convenient
for lossy telemetry but can erase accepted jobs. Use dropping only when the
contract permits it, report the loss, and otherwise reject before acceptance
or apply bounded waiting with a defined expiry outcome.

## What it costs

Backpressure exposes overload to producers as latency or rejection. Byte
accounting needs an explicit estimate of retained representation size and
headroom for runtime overhead. Shared limits add coordination; per-process
limits multiply as instances scale. Size budgets against the service's
operating envelope, and distinguish that design decision from a claim that a
bounded queue guarantees a particular throughput or latency.

## Review questions

- What bounds queued items, retained bytes, and active operations on this path?
- Can submissions or suspended producers grow despite the worker limit?
- Is capacity reserved before tasks and large buffers are created?
- What does the caller observe when admission fails?
- Do fan-out and retries consume the same shared budget?
- Which failure or cancellation paths release every reservation?
- Can a blocked producer hold anything required to drain the queue?

## How to mechanize

**Property test — generate admissions and completions against a capacity
model.** Model `submit(size)`, `start`, `complete`, `cancel`, and `reject`, and
exercise the implementation with generated sequences and controlled interleavings.
After each transition, assert queued count, charged bytes, and active count
stay within their distinct limits. Assert every accepted job remains accounted
for until its terminal outcome and every reservation is released exactly once.

Include a stopped consumer, simultaneous last-slot admissions, cancellation
before execution, oversized items, and retries during saturation. If submission
waits, assert the harness cannot create more than the configured number of
waiting producers. Avoid unbounded test waits: drive a controllable scheduler
or fail the test after a fixed number of model steps.

Ordinary types do not express the aggregate resources retained by dynamic tasks.
Static checks can flag specific unbounded constructors but cannot establish
capacity across arbitrary producers and consumers. A bounded queue enforces
its own item limit at runtime; the generated check here tests the larger
accounting protocol. Sampled schedules do not prove every interleaving or a
production memory bound.

## References

- Reactive Streams Special Interest Group, *Reactive Streams Specification for
  the JVM*, version 1.0.4, May 26, 2022, Publisher rule 1 and Subscriber demand
  rules — demand coordinates production across asynchronous boundaries.
- Python Software Foundation, *Python 3 Library Reference*, `queue.Queue`,
  `qsize`, `put_nowait`, and `Full` — positive item bounds and atomic admission
  rather than a size check followed by insertion.
- Python Software Foundation, *Python 3 Library Reference*, `collections.deque`
  — appending to a full bounded deque discards elements from the opposite end.
