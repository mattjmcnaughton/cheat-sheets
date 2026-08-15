---
title: Resource Lifecycle
bug_classes: [resource-leak, double-close, use-after-close, partial-acquisition-leak, cleanup-cancellation]
authority: design
mechanizable: type
maturity: draft
last_reviewed: 2026-08-15
---

# Resource Lifecycle

## Why review misses it

The happy path places acquisition and release close enough to look paired. The
missing edge is elsewhere: an exception between two acquisitions, an early
return added later, cancellation while an asynchronous release is suspended,
or a helper that closes a resource its caller still owns. Tests usually use
cheap fakes, finish normally, and let process teardown reclaim leaks. Reviewers
therefore see correct operations without seeing the lifetime that makes them
correct.

## The default

**Acquire each resource into the smallest structured scope that can use it,
register cleanup immediately, and let that scope release it exactly once on
every exit.**

## Rules

1. **Bind acquisition and release with the language's structured cleanup
   construct.** A context manager, `defer`, or deterministic destructor covers
   returns and failures that a trailing `close` misses.
2. **Make ownership explicit at every boundary.** Say whether a parameter is
   borrowed or consumed and whether a return value transfers ownership;
   otherwise both sides may close it, or neither will. *(Design authority: both
   sides must honor the same interface contract.)*
3. **Register cleanup immediately after each successful acquisition.** If the
   third acquisition fails, the first two must already have independent cleanup
   actions.
4. **Release in reverse acquisition order.** Later resources commonly depend
   on earlier ones; unwinding the stack preserves that dependency.
5. **Make close-once observable and reject later use.** Treat `open → closing →
   closed` as a state machine, make repeated close harmless only when the API
   promises idempotence, and fail clearly on use after close.
6. **Keep the owner alive for every borrower, and end all borrows before
   release.** A borrowed stream, cursor, slice, or handle cannot outlive the
   object that supplies it.
7. **Give asynchronous cleanup a cancellation policy.** Once release starts,
   await it to completion in a bounded, cancellation-protected cleanup scope;
   report a timeout rather than silently abandoning the resource.
8. **Preserve the primary failure while recording cleanup failures.** Cleanup
   errors matter, but replacing the operation's exception destroys the cause;
   aggregate or chain both when the language permits.
9. **Keep retry and concurrency policy outside the resource wrapper.** The
   wrapper owns one lifetime; callers decide whether another attempt acquires a
   new resource.

## Anti-patterns

**“Close at the bottom.”** A final `close()` is direct and readable, but every
new return or exception creates an unreviewed leak path. Put the body inside a
structured scope instead.

**“The callee can clean up for me.”** Centralizing cleanup sounds safer. If the
callee only borrowed the handle, closing it invalidates the caller's next use;
if ownership transfers, encode and document that transfer.

**“Close is always harmless twice.”** Many APIs tolerate repeated close, so
defensive calls spread. Other resources flush, commit, return capacity to a
pool, or signal peers during close; require one owner and rely on idempotence
only when it is contractual.

**“Acquire everything, then install cleanup.”** Batch setup keeps code tidy,
but a failure halfway leaves no cleanup scope for completed acquisitions.
Enter each resource into an exit stack as soon as it succeeds.

**“Cancellation means stop everything now.”** Prompt cancellation improves
latency, but interrupting an asynchronous close can strand a transaction,
lease, or transport. Protect only the bounded cleanup phase, then restore or
propagate cancellation.

## What it costs

Structured scopes add indentation or wrapper types, and explicit ownership can
make convenient sharing awkward. Close-state checks add a branch and state;
bounded asynchronous cleanup delays cancellation and needs a timeout policy.
Preserving both body and cleanup failures complicates error handling. These
costs buy deterministic release; for process-lifetime resources, explicitly
declare that lifetime instead of manufacturing a local close.

## Review questions

- Which scope owns each acquired resource, and where does ownership transfer?
- Is cleanup registered immediately after every successful acquisition?
- What releases earlier resources when a later acquisition fails?
- Do return, exception, and cancellation exits run the same cleanup?
- Can any borrower escape beyond the owner's close?
- What happens on a second close or a use after close?
- Can asynchronous cleanup itself be cancelled or wait forever?
- If work and cleanup both fail, which errors reach the caller and telemetry?

## How to mechanize

**Type — available where ownership is encoded.** Use affine or move-only
resource types so transfer consumes the old binding and borrowing cannot outlive
the owner. Model open and closed handles as distinct types where operations can
return the next state. In languages without ownership checking, keep raw
handles private and expose only a scoped callback or context-manager API; the
type system then protects the wrapper boundary, not arbitrary aliases.

**Lint — enforce structured syntax.** Fail the build when a configured
acquisition function appears outside a context manager, deterministic scope, or
immediately registered cleanup; flag escaping a resource from such a scope.
Interprocedural ownership and reflective factories remain beyond a syntactic
check.

**Property test — enumerate exits.** Inject failure after each acquisition and
at each use step; assert acquired count equals released count, release order is
reversed, and every token is released once. Generate cancellation at every
await in use and cleanup.

**Runtime assertion — guard the state machine.** Tag handles `open`, `closing`,
or `closed`; reject operations outside `open`, count duplicate closes, and put a
deadline around asynchronous release. Keep these checks in debug builds or at
the wrapper when their production cost is material.

**Observation is containment, not proof.** Export active-resource gauges,
acquire/release totals, age of the oldest resource, cleanup failures, and
cleanup timeouts. Balanced totals cannot prove correct ownership because a
double close can hide a leak; types and failure-injection tests provide the
stronger rungs.

## References

- Python, [With Statement Context Managers](https://docs.python.org/3/reference/datamodel.html#with-statement-context-managers) — the protocol that guarantees exit handling around a suite.
- Python, [`contextlib.AsyncExitStack`](https://docs.python.org/3/library/contextlib.html#contextlib.AsyncExitStack) — immediate registration and reverse-order unwinding for partial and asynchronous acquisition.
- Go, [The Go Programming Language Specification: Defer statements](https://go.dev/ref/spec#Defer_statements) — deferred calls execute on function return in reverse order.
- Java SE, [`AutoCloseable`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/AutoCloseable.html) and [try-with-resources](https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html#jls-14.20.3) — close contracts and preservation of suppressed cleanup exceptions.
- Rust, [`Drop`](https://doc.rust-lang.org/reference/destructors.html) — deterministic destruction and reverse-order cleanup.
- Nathaniel J. Smith, [Notes on structured concurrency, or: Go statement considered harmful](https://vorpus.org/blog/notes-on-structured-concurrency-or-go-statement-considered-harmful/) — lexical lifetimes as the organizing principle for cleanup; concurrency policy itself is outside this sheet.
