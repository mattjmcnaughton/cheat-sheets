---
title: Timeouts and Cancellation
bug_classes: [reset-timeout-budget, orphaned-work, swallowed-cancellation, timeout-as-rollback]
authority: design
mechanizable: property-test
maturity: draft
last_reviewed: 2026-09-09
---

# Timeouts and Cancellation

## Why review misses it

Every dependency call has a timeout, so the request looks bounded. The total
includes queueing, retries, cleanup, and nested calls that may each start a fresh
budget. Tests return immediately and never show a child task running after its
parent exits or a remote write completing after the client gives up.

## The default

**Give the operation one deadline, pass its remaining budget to child work, and
treat timeout or cancellation as a request to stop waiting or working—not as
proof that an effect did not happen.**

## Rules

1. **Start the budget at the boundary whose latency you promise.** Include
   admission queues, connection acquisition, retries, and response processing
   rather than timing only the final read.
2. **Use a monotonic deadline for elapsed time inside one clock domain.**
   Wall-clock corrections must not extend or shorten a local operation budget.
3. **Propagate a remaining budget using the receiving protocol's deadline
   semantics.** **Needs design authority:** account for transit and clock skew;
   do not send a process-local monotonic timestamp to another machine.
4. **Cap each child by both its local allowance and the parent's remaining
   budget.** Starting a new full timeout at each layer defeats the outer limit.
5. **Stop admitting new work when the budget expires.** Check before dispatch
   and after queue waits; cancellation cannot undo a request already sent.
6. **Make child lifetime and cleanup ownership explicit.** Cancel when needed and
   await owned work before releasing its resources, or transfer durable work to
   a named owner.
7. **Propagate cancellation after required cleanup.** Swallowing it can leave
   parents waiting and violate structured task-lifetime assumptions.
8. **Separate cancellation requested from cancellation completed.** Cooperative
   tasks, blocking calls, and remote operations may not stop immediately.
9. **Resolve uncertain effects through operation status or safe replay.** A
   timeout response must not promise rollback without evidence from the owner
   of the effect.

Use [Resource Lifecycle](../state/resource-lifecycle.md) for release protocols
and [Retries and Idempotency](retries-and-idempotency.md) before repeating an
operation with an unknown outcome.
For completion rather than a limit on waiting, use
[Termination and Progress](../execution/termination-and-progress.md).

For cooperative asynchronous work within one event loop, keep a single deadline:

```python
import asyncio

async def load_pair(load_a, load_b):
    deadline = asyncio.get_running_loop().time() + 2.0
    async with asyncio.timeout_at(deadline):
        a = await load_a()
        b = await load_b()
        return a, b
```

This shares a local budget. It does not establish remote cancellation or a hard
wall-clock return bound if a child blocks the loop or delays cancellation cleanup.

## Anti-patterns

**"Every call gets two seconds."** Each dependency is protected individually,
but a chain can consume many full allowances. Derive all allowances from the
same parent deadline.

**"Catch cancellation and return a default."** This keeps the function's result
shape simple but tells its owner that abandoned work completed normally. Clean
up in a `finally` block or catch, clean up, and re-raise the cancellation.

**"Timeout means the write failed."** The caller's timer only describes its
waiting. The destination can commit while the response is lost. Return an
unknown outcome and retain the operation identity for resolution.

**"Fire and forget the child."** Detaching work improves apparent response time,
but the child can use released resources or lose its result. Keep it in an owned
task scope or hand it to a durable worker with explicit completion tracking.

**"Shield all cleanup."** Avoiding interruption can preserve an invariant, but
unbounded shielding makes cancellation ineffective. Bound the cleanup protocol
and define who recovers if it cannot complete within that bound.

## What it costs

Deadline propagation adds an argument or context to call paths. Short budgets
reject work that might have completed later. Waiting for cleanup can exceed the
user-visible response deadline; returning sooner requires separate resource
ownership for cleanup. A hard stop for non-cooperative work needs isolation and
a recovery protocol, since terminating execution can leave effects unresolved.

## Review questions

- Where does the operation's budget start, and does it include queueing?
- Does any nested call or retry reset the full timeout?
- Can this deadline be interpreted correctly in the receiving clock domain?
- What prevents dispatch after the budget has already expired?
- Who owns children and resources after the caller stops waiting?
- Can any handler swallow cancellation or block its delivery?
- What may already have committed when the timeout is reported?
- Is the promised bound for the response, for cleanup, or for both?

## How to mechanize

**Property test — generate time advances and cancellation points across the
operation lifetime.** Use an injectable clock and controllable dependencies.
Generate queue delays, retries, child completion, cancellation, and cleanup
completion. Assert that no new attempt starts with an exhausted budget, child
allowances never exceed the parent's remainder, and owned children terminate
before their resources are released.

Check the declared response and cleanup bounds separately. Include a dependency
that commits before losing its reply and one that delays cancellation. Require
the former to produce an unknown outcome and the latter to follow the documented
cleanup ownership policy rather than an assumed instantaneous stop.

A deadline type cannot prove that the clock advances or that a dependency honors
cancellation. Static checks can require a timeout argument without proving it
covers queueing and cleanup. Generated schedules are the highest applicable rung
for these temporal guarantees. Supplement the controllable model with focused
integration cases for the actual client's cancellation and connection behavior;
a fake that always stops instantly cannot establish those semantics.

## References

- Python Software Foundation, *Python 3.14 Library Reference*, "Coroutines and
  tasks," "Task cancellation," "Task groups," and "Timeouts" — cooperative
  cancellation, task ownership, timeout contexts, and cleanup delays.
- Marc Brooker, *Timeouts, retries, and backoff with jitter*, Amazon Builders'
  Library, 2019 — timeout coverage, resource use, and downstream retry behavior.
- Python Software Foundation, *Python 3.14 Library Reference*, "time — Time
  access and conversions," `monotonic` — elapsed-time measurement unaffected
  by system clock updates.
