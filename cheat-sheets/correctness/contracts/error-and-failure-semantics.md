---
title: Error and Failure Semantics
bug_classes: [error-as-success, undocumented-partial-effects, lost-error-cause, ambiguous-operation-outcome]
authority: design
mechanizable: property-test
maturity: draft
last_reviewed: 2026-09-09
---

# Error and Failure Semantics

## Why review misses it

An exception handler makes control flow look complete. The diff shows the
reported error but rarely the state left behind, the caller's retry policy, or
which dependency failures the handler accidentally catches. Two functions can
raise the same exception while leaving entirely different recovery obligations.

## The default

**Give every expected failure a stable meaning and an explicit guarantee about
remaining state; report an unknown outcome when you cannot establish whether an
effect committed.**

## Rules

1. **List expected failures separately from violated internal invariants.**
   A caller can repair an invalid request; an implementation defect needs to
   remain visible as a defect.
2. **Specify the state guarantee for each failure.** **Needs design authority:**
   agree whether the operation leaves state unchanged, preserves invariants
   with documented partial effects, or leaves an outcome requiring resolution.
3. **Expose stable machine-readable categories for recovery decisions.**
   Human-readable messages can change without changing the contract.
4. **Catch failures only where you can recover or translate their meaning.**
   Broad catches around unrelated work turn programming mistakes into plausible
   domain failures.
5. **Preserve the original cause when translating an error.** Diagnostic context
   lets maintainers distinguish the domain rejection from the dependency that
   caused it.
6. **Keep success claims within what you actually know.** An accepted request,
   queued job, or returned connection acknowledgment need not mean the business
   operation completed.
7. **Treat a lost reply after dispatch as an unresolved outcome.** A local
   failure to receive success does not establish that the remote effect failed.
8. **Make batch partial success explicit per item.** A single success flag
   cannot tell a caller which items need further work without risking duplicates.

Keep the error category separate from retry authorization: use
[Retries and Idempotency](retries-and-idempotency.md) for whether another attempt
is safe, and [Partial Writes Across Services](partial-writes-across-services.md)
for recovery spanning independently committed effects.

## Anti-patterns

**"Return an empty result when anything goes wrong."** The page can still render,
but callers treat an outage as authoritative absence:

```python
# Wrong: defects and connection failures become valid empty results.
try:
    records = read_records()
except Exception:
    records = []

# Right: translate only the failure understood at this boundary.
try:
    records = read_records()
except ConnectionError as exc:
    raise RecordsUnavailable("record lookup failed") from exc
```

**"Match the exception message."** It is available without changing an interface,
but wording and localization become accidental control flow. Branch on a stable
code or exception class and keep the message for people.

**"Throw means nothing happened."** Local construction may provide this guarantee;
a remote service may commit and lose its response. Expose an unknown outcome and
an operation identifier that supports a status lookup or safe repeat.

**"Log it and continue."** Keeping a batch alive is useful, but a final success
response hides skipped items. Return item-level results and define whether
unattempted items differ from attempted failures.

**"Wrap everything in one generic error."** A uniform response is easy to render,
but destroys distinctions the caller needs for recovery. Keep a stable category
and internal cause while omitting sensitive internals from the public payload.

## What it costs

Failure categories and postconditions become part of the interface you maintain.
Guaranteeing unchanged state can require private construction or transactions.
Unknown outcomes require a resolution path and sometimes durable operation
records. Do not promise a stronger failure guarantee than the implementation can
provide across its actual side effects.

## Review questions

- Which failures can the caller act on, and how are they distinguished?
- What state remains after each failure point in this change?
- Does the handler catch only exceptions it understands?
- Can a failed lookup become indistinguishable from an empty successful one?
- Does this success response mean accepted, committed, or completed?
- Can an effect commit before the error response is produced?
- Can a batch caller identify completed, failed, and unattempted items?

## How to mechanize

**Property test — inject faults and check each documented failure postcondition.**
Generate valid initial state and requests. Fail each dependency call and each
step around mutation, commit, and response delivery. For an unchanged-state
guarantee, compare the observable state with the pre-call snapshot; for a weaker
guarantee, check the named invariant and the exact permitted partial effects.
Verify that the returned category gives the caller the promised recovery path.

Types can describe a closed set of results, but cannot prove the state left by
an exception or a lost remote reply. Static checks can ban broad catches without
establishing the operation's failure guarantee. Generated fault histories are
the highest applicable rung for those postconditions.

Include a dependency that commits successfully and then drops its reply. Require
an unresolved outcome rather than a claim of no effect. Exercise the real storage
boundary for commit behavior; a fake that automatically undoes every thrown
exception would conceal the bug under test. For local atomic publication, see
[Invariants Across Intermediate Steps](../state/invariants-across-intermediate-steps.md).

## References

- David Abrahams, *Exception-Safety in Generic Components*, Boost community
  documentation, accessed 2026-09-09 — basic and strong exception guarantees.
- M. Nottingham, E. Wilde, and S. Dalal, *Problem Details for HTTP APIs*, RFC 9457,
  July 2023 — machine-readable problem categories and separation from diagnostic
  implementation details.
- Python Software Foundation, *Python 3.14 Tutorial*, §8, "Errors and Exceptions,"
  "Exception Chaining" — preserving causes when translating exceptions.
