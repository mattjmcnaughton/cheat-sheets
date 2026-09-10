---
title: Nullability and Partiality in Signatures
bug_classes: [unchecked-absence, ambiguous-result-sentinel, hidden-partial-function, invalid-result-combination]
authority: design
mechanizable: type
maturity: draft
last_reviewed: 2026-09-09
---

# Nullability and Partiality in Signatures

## Why review misses it

The successful branch returns exactly what the signature promises. An empty
input, failed lookup, or missing branch instead returns a sentinel or falls off
the end. A caller's happy-path test never exercises the disagreement, and a
comment about what "normally exists" looks like a precondition.

## The default

**Expose every expected absence or undefined case in the return type, and require
callers to handle it before using the successful value.**

## Rules

1. **State the valid input domain and every expected result case.** A signature
   returning a value must not silently return `None` for a permitted input.
2. **Use `T | None` only when absence has one meaning the caller can act on.**
   Several different recovery actions require separate named result variants.
3. **Keep successful emptiness separate from absence when they mean different
   things.** An empty collection can mean a completed search with no matches;
   it must not also hide an unavailable backend.
4. **Replace independent result fields with mutually exclusive variants.**
   **Needs design authority:** agree a shared outcome model so callers cannot
   receive combinations such as success with only an error payload.
5. **Check optional values explicitly and keep the narrowed value local.**
   Truthiness also rejects valid zeroes and empty strings; rereading mutable
   state can invalidate an earlier check.
6. **Make required and optional arguments explicit independently of nullability.**
   A nullable argument without a default is still required at the call site.
7. **Use a checked input representation for a partial operation when practical.**
   If the operation needs a first item, accepting that item separately avoids
   pretending an arbitrary list is nonempty.
8. **Distinguish expected alternatives from defects and transport failure.**
   A missing record is not evidence that a query succeeded when the query failed.

This signature promises absence on empty input and preserves a valid zero:

```python
def first(values: list[int]) -> int | None:
    return values[0] if values else None

value = first([0])
if value is not None:
    print(value + 1)
```

Use [Absence and Emptiness](../data/absence-and-emptiness.md) for the meaning of
missing data and [Error and Failure Semantics](error-and-failure-semantics.md)
for guarantees attached to unsuccessful operations.

## Anti-patterns

**"Return an impossible value."** A sentinel avoids changing the signature, but
future valid inputs can collide with it. Return an explicit optional or variant:

```python
# Wrong: zero may be a real identifier.
def find_id(name: str) -> int:
    return ids.get(name, 0)

# Right: the signature exposes a missing lookup.
def find_id(name: str) -> int | None:
    return ids.get(name)
```

**"Cast away the optional because it always exists."** This quiets the checker
without handling an absent value. Check the value and implement the missing
case, or change the producer's representation to establish presence.

**"Every outcome fits in `(ok, value, error)`."** One tuple is convenient, but
allows contradictory fields and makes consumers invent their own checks. Use
separate success and failure variants containing only their relevant payloads.

**"Return nothing when no branch matches."** An implicit `None` is brief but
can contradict a non-null annotation. Make the missing case explicit and fail
static checking when an expected result path has no return.

## What it costs

Callers must write branches they could previously omit. Variant types add names
and can require coordinated interface changes. Excessively broad unions make
simple operations cumbersome; model only outcomes that callers need to handle
differently. Strict checking needs typed boundaries so unchecked values do not
silence the checks.

## Review questions

- What does this function return for every permitted empty or missing input?
- Can a sentinel collide with a successful result?
- Does `None` represent one actionable case or several unrelated failures?
- Can the result represent success and failure simultaneously?
- Does this caller handle absence before accessing the value?
- Does the presence check apply to the same value subsequently used?
- Are omitted arguments and explicitly null arguments both permitted here?

## How to mechanize

**Type — represent absence and mutually exclusive outcomes explicitly.** Use
`T | None` for one absent case and a union of separate result classes when cases
carry different payloads. Give each variant only its relevant fields. Within
statically checked code, this excludes contradictory result combinations and
rejects use of a possibly absent value where a concrete value is required.

Run strict type checking over the producer and its callers. Require explicit
return annotations at public boundaries, enable optional-value and missing-return
diagnostics, and prevent unchecked dynamic values from entering those paths.
Use an exhaustive branch with `assert_never` for a closed union of outcomes;
adding a variant must fail callers that omit it. This reaches the highest rung
for result representation, not for the correctness of the producer's lookup.

Python does not enforce annotations at runtime. Validate external values and
avoid casts or ignored diagnostics that bypass the checked representation.

Keep small expected-failure type-check fixtures: dereference `T | None` without
a guard, omit one return path, and leave a new outcome unhandled. Require each
fixture to produce its intended diagnostic. This checks that configuration and
annotations enforce the promise, rather than assuming a green checker covered
untyped code. Runtime parsing of external results belongs in
[Input Validation at Boundaries](input-validation-at-boundaries.md).

## References

- Python Typing Team, *Specification for the Python Type System*, "Union and
  Optional" and "Static, dynamic, and gradual typing," accessed 2026-09-09 —
  optional values, unions, and the limits of unchecked types.
- Python Typing Team, *Unreachable Code and Exhaustiveness Checking*, accessed
  2026-09-09 — using `Never` and `assert_never` to reject omitted cases.
- Python Software Foundation, *Python 3.14 Library Reference*, "typing — Support
  for type hints" — annotations are not enforced by the Python runtime.
