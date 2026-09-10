---
title: Resource Lifecycle
bug_classes: [resource-leak, use-after-close, double-release, partial-acquisition-leak]
authority: individual
mechanizable: lint
maturity: draft
last_reviewed: 2026-09-08
---

# Resource Lifecycle

## Why review misses it

Acquisition and release look balanced on the successful path. The missing
release lives on a return, exception, or failed second acquisition. A handle
can also escape into a callback whose execution outlives the scope that owns
it; the caller and callback each look reasonable in isolation.

## The default

**Give each acquired resource one owner and one bounded lifetime; register its
cleanup immediately, and finish every use before that owner releases it.**

## Rules

1. **Acquire resources inside a context manager or an equivalent structured
   scope.** A cleanup statement after the work is skipped when the work raises.
2. **Register cleanup after each successful acquisition.** If the third open
   fails, the first two still need releasing.
3. **State whether a parameter is borrowed or ownership is transferred.**
   Closing a borrowed connection can break its next caller.
4. **Join resource-using tasks before leaving the owning scope.** Scheduling
   work does not prove that work has finished with the handle.
5. **Release dependent resources in reverse acquisition order.** A wrapper may
   need its underlying stream during its own cleanup.
6. **Handle cleanup failure explicitly without silently losing the original
   failure.** A failed close can matter, but it must not erase why work failed.
7. **Treat close, flush, commit, and durable persistence as separate promises.**
   Releasing a handle does not by itself prove the operation committed.
8. **Make repeated close safe only where your ownership protocol needs it.**
   Idempotent cleanup does not make use after close valid.

For references that share mutable state without owning its lifetime, see
[Mutation and Aliasing](mutation-and-aliasing.md).
For stopping work before releasing its resources, see
[Timeouts and Cancellation](../contracts/timeouts-and-cancellation.md).
For limiting resources held by admitted work, use
[Bounded Work and Backpressure](../execution/bounded-work-and-backpressure.md).

## Anti-patterns

**"Close it at the end."** The successful path is easy to scan, but failure
skips the last line. Put acquisition under structured cleanup:

```python
# Wrong: processing failure skips close.
stream = open(path, encoding="utf-8")
process(stream)
stream.close()

# Right: scope exit attempts cleanup on success and exceptions.
with open(path, encoding="utf-8") as stream:
    process(stream)
```

**"Garbage collection will close it."** Reachability is convenient to leave to
the runtime, but it does not define a timely release boundary. Close explicitly
when the work ends; use finalization only as a fallback.

**"The caller can finish reading later."** Returning an iterator avoids
buffering, but returning it from inside the file's owning scope leaves it using
a closed handle. Keep iteration inside the scope or expose a context-managed
iterator that transfers a clear cleanup obligation.

**"Cleanup cannot fail."** Suppressing every close error simplifies the error
path but can hide failed output. Preserve the work exception and expose cleanup
failure through exception chaining or a separate recorded failure.

## What it costs

Structured ownership constrains API shapes: a stream cannot freely escape its
scope. Joining tasks can extend that scope, and closing network resources can
take time or fail. Returning materialized data avoids lifetime coupling at the
cost of memory. Choose that trade-off at the boundary.

## Review questions

- Who owns this handle, and which scope ends its lifetime?
- If the next acquisition fails, what releases resources already acquired?
- Can a callback, iterator, or task use this after scope exit?
- Does this code close a resource it only borrowed?
- What happens if cleanup raises while another exception is active?
- Does successful close actually establish the durability this caller needs?

## How to mechanize

**Lint — require structured acquisition for known resource APIs.** Fail the
build when a file open or a designated connection-acquisition call appears
outside a `with` statement or an approved owning helper. Give ownership-transfer
factories an explicit, reviewed exemption. This is an AST check over a bounded
set of APIs, not a proof that every resource is released.

Python's ordinary annotations do not consume an owner or invalidate every alias
after close. Ownership types can provide stronger guarantees in other
languages; they are unavailable for these arbitrary Python handles.

For dynamic acquisition counts, register each context as it is entered:

```python
from contextlib import ExitStack

with ExitStack() as stack:
    streams = [stack.enter_context(open(p, encoding="utf-8")) for p in paths]
    consume(streams)
```

Supplement lint with failure injection at every acquisition and use point.
Record acquired handles, release attempts, and successful releases; check that
every acquired handle receives its required cleanup and no use follows release.
Inject cleanup failure too. A process kill cannot run language-level cleanup;
test any persistent recovery obligation separately.

## References

- Python Software Foundation, *Python 3 Language Reference*, §8.5, "The with
  statement" — entry, exit, and exception behavior.
- Python Software Foundation, *Python 3 Library Reference*, "contextlib",
  "ExitStack" — incremental registration and reverse-order cleanup.
- Python Software Foundation, *Python 3 Language Reference*, "Data model",
  "Objects, values and types" — explicit release of external resources.
