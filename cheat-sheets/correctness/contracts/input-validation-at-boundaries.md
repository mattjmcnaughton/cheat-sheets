---
title: Input Validation at Boundaries
bug_classes: [unchecked-external-input, lossy-input-coercion, stale-validation, parser-resource-exhaustion]
authority: design
mechanizable: property-test
maturity: draft
last_reviewed: 2026-09-09
---

# Input Validation at Boundaries

## Why review misses it

The handler receives a value with a familiar name and annotation, so its body
looks like ordinary domain code. The diff does not show which callers bypass
validation, whether the decoder silently coerces a value, or whether a fact
checked at entry is still true when the write happens.

## The default

**Parse external input into a bounded, validated domain value before using it;
recheck facts that can change in the same protected operation that acts on them.**

## Rules

1. **Identify every entry from a different trust or representation boundary.**
   Include persisted records, queued messages, imports, and internal service
   responses; being inside the network does not establish the required shape.
2. **Specify accepted representations before choosing a decoder.**
   **Needs design authority:** agree field presence, unknown-field handling,
   coercions, and limits with the interface's producers and consumers.
3. **Bound input work before and during parsing.** Cap encoded size, nesting,
   collection length, and decompressed output so rejection does not itself
   require unbounded memory or CPU.
4. **Return a validated value rather than a boolean about the original input.**
   Copy or reconstruct mutable data so later mutation cannot invalidate the
   result behind the consumer's back.
5. **Validate relationships as well as individual fields.** A valid start and
   end can still describe a forbidden interval when considered together.
6. **Reject unintended coercions explicitly.** Converting text, booleans, or
   fractional numbers to integers can accept a request the contract excludes.
7. **Check changing preconditions at the point of mutation.** Authorization,
   balances, and availability need protection against changes after entry checks.
8. **Keep input errors distinct from broken internal invariants.** Report a
   stable rejection for bad input; do not disguise an implementation defect as
   something the caller can repair.

For a JSON field whose contract is an integer count from 1 through 100, exclude
booleans explicitly; Python treats `bool` as an `int` subclass:

```python
def parse_count(raw: object) -> int:
    if type(raw) is not int or not 1 <= raw <= 100:
        raise ValueError("count must be an integer from 1 through 100")
    return raw
```

This function validates at runtime. Its return annotation alone does not encode
the range. Use [Absence and Emptiness](../data/absence-and-emptiness.md) for field
meaning and [Text and Encoding](../data/text-and-encoding.md) for normalization.
For choosing limits from processing cost, use
[Algorithmic Complexity and Input Size](../execution/algorithmic-complexity-and-input-size.md).

## Anti-patterns

**"The frontend already checked it."** Reusing client validation avoids duplicate
code, but alternate clients and stored messages can skip it. Enforce the contract
at the receiving boundary and use client checks for earlier feedback.

**"Cast it into the expected type."** A type hint looks like a concise parser:

```python
from typing import cast

# Wrong: no runtime inspection happens.
count = cast(int, payload["count"])
# Right: validate the actual value.
count = parse_count(payload["count"])
```

**"Validate once, then keep the original dictionary."** This avoids copying,
but another reference can alter the checked data. Construct an owned domain
value or enforce an ownership protocol that prevents mutation.

**"A valid identifier grants access."** Checking identifier syntax is easy to
reuse, but says nothing about permission to act on that resource. Authorize the
operation separately and protect mutable authorization facts as needed.

## What it costs

Parsing creates a boundary layer and may allocate owned values. Size limits and
strict coercion rules reject inputs previously accepted by accident. Rechecking
mutable facts adds synchronization or transaction work. Keep pure shape checks
at entry and place only changing preconditions inside that protected operation.

## Review questions

- Which entry paths can reach this code without the proposed parser?
- What happens for a boolean, fractional number, unknown field, or absent field?
- What bounds memory and work before the parser finishes?
- Can another reference mutate the value after validation?
- Which relationships between fields are checked?
- Which preconditions can change before the write, and what protects them?
- Does malformed input produce a documented rejection without domain effects?

## How to mechanize

**Property test — generate raw representations against an independent acceptance
predicate.** Generate valid inputs, boundary values, wrong primitive types,
missing fields, unknown fields, and malformed containers. Assert that every
accepted result satisfies the domain predicate and every forbidden representation
is rejected before a domain write. Generate valid domain values and require their
canonical encoding to parse back to an equivalent value.

Types cannot establish facts about bytes arriving from outside the typed program;
ordinary Python annotations also cannot express this numeric range. Static
checks can enforce calls through a parser but cannot prove that its predicates
match the contract. Generated input checks are the highest applicable rung for
that acceptance behavior. Keep the expected predicate separate from the parser
so the test does not merely repeat the implementation.

Exercise configured size and nesting limits through the actual decoder, including
streamed or compressed input where supported. For changing preconditions, use
[Concurrency and Shared State](../state/concurrency-and-shared-state.md) to test
the protected decision under competing writes.

## References

- OWASP Foundation, *Input Validation Cheat Sheet*, OWASP Cheat Sheet Series,
  accessed 2026-09-09 — boundary validation, syntactic and semantic checks,
  allowlists, and input limits.
- Python Software Foundation, *Python 3.14 Library Reference*, "typing — Support
  for type hints," `cast` — returning a value unchanged without runtime checking.
- Python Software Foundation, *Python 3.14 Library Reference*, "Built-in Types,"
  "Boolean Type — bool" — the relationship between booleans and integers.
