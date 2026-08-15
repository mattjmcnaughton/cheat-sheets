---
title: Data Correctness Overview
bug_classes: [representation-mismatch, boundary-value-error, lossy-conversion, invalid-data-acceptance]
authority: design
mechanizable: type
maturity: draft
last_reviewed: 2026-08-15
---

# Data Correctness Overview

## Why review misses it

The operation in the diff can be correct while its value means the wrong thing.
A bare number does not reveal its unit, a string does not reveal its encoding,
and a timestamp does not reveal whether it is an instant or wall time. Happy-path
fixtures reuse the same assumptions as the implementation, so they confirm the
calculation without challenging the representation, boundary, or conversion.

## The default

**Represent each domain value with its meaning and constraints in the type,
validate it once at every untrusted boundary, and preserve information until a
named conversion deliberately changes it.**

## Rules

1. **Name the meaning in the type, not only the variable.** Distinguish units,
   identifiers, currencies, instants, local times, and normalized text so an
   invalid combination cannot look like ordinary arithmetic or comparison.
2. **Parse untrusted input into a domain value at the boundary.** Reject the
   entire value on malformed syntax, invalid range, unknown unit, or impossible
   combination; do not pass partly validated primitives inward.
3. **Preserve distinctions the domain uses.** Keep missing, null, empty, and
   defaulted separate; apply the focused guidance in
   [Absence and Emptiness](absence-and-emptiness.md).
4. **Make every conversion explicit and test its limits.** Name source and
   destination units, reject overflow and lost precision, and avoid a
   parse-format-parse chain when a direct conversion exists. Apply
   [Numbers and Money](numbers-and-money.md) to numeric representation.
5. **Define boundaries and equality before using them.** State inclusivity,
   ordering, normalization, and exceptional values rather than inheriting an
   operator's defaults; use [Boundaries and Ranges](boundaries-and-ranges.md)
   and [Equality and Ordering](equality-and-ordering.md).
6. **Round-trip every storage and wire representation.** Assert that encoding
   then decoding preserves the domain value, including extremes and unusual
   but valid values.
7. **Keep text and time policies at their boundaries.** Name encodings and
   normalization as described in [Text and Encoding](text-and-encoding.md);
   separate instants, wall times, zones, and durations as described in
   [Time and Time Zones](time-and-time-zones.md).
8. **Agree on shared representations before changing them.** *(Design
   authority: coordinate schemas, units, defaults, and migration behavior with
   every producer and consumer.)*

## Anti-patterns

**"The primitive is simpler."** A string or integer makes plumbing easy, but it
also permits every invalid unit, format, and combination until distant code
guesses what it means.

**"Validate it where it is used."** Local checks feel defensive. They drift,
leave unchecked paths, and let invalid data travel far enough to lose its
source; parse once and carry a validated value.

**"Normalize everything immediately."** A canonical form simplifies matching,
but a lossy conversion can erase spelling, precision, provenance, or the
difference between omitted and empty before the domain chooses to discard it.

**"Representative examples are enough."** Typical values prove the middle.
They do not exercise zero, empty, maximum width, encoding errors, interval
seams, daylight transitions, or serialization loss.

## What it costs

Domain types add constructors, adapters, and explicit conversions at every
boundary. Validation and round-trip tests add code, while preserving provenance
can add storage. The runtime cost is usually one boundary check; the larger bill
is coordinating representation changes. Pay it at the edge rather than through
repeated checks and ambiguous primitives throughout the core.

## Review questions

- What does each primitive value mean, including its unit, encoding, and valid
  range, and does its type preserve that meaning?
- Where does untrusted input become a validated domain value?
- Which valid distinctions does this conversion collapse?
- What happens at zero, empty, minimum, maximum, and exactly on each boundary?
- Does encode then decode preserve every supported value?
- Are comparison, ordering, rounding, and normalization policies explicit?
- Which producers and consumers must agree before this representation changes?

## How to mechanize

**Type — reach this rung for domain distinctions.** Introduce validated types
such as `UserId`, `NonEmptyText`, `Money`, and separate `Instant` from
`LocalDateTime`; expose constructors that reject invalid values and conversion
functions that name both units. Prevent direct construction outside the
boundary module.

**Lint — catch primitive escape hatches.** Fail the build on unchecked casts,
implicit encodings, naive date-time constructors, binary floats in money paths,
and raw primitives passed to APIs that require domain types.

**Property test — exercise the value space.** Generate valid values and assert
serialization round trips, conversion inverses where losslessness is promised,
and domain laws at minima, maxima, emptiness, and seams. Generate invalid values
and assert the boundary rejects them without producing a partial object.

**Runtime assertion — protect external boundaries.** Check schema constraints,
range, unit, encoding, and cross-field invariants before accepting or storing a
value. Assert that lossy conversions occur only through explicitly named APIs.

**Observation — detect escaped corruption.** Reconcile independent totals and
counts, measure validation failures by boundary and reason, and alert on stored
rows that violate constraints. Observation cannot prove that two valid-looking
values carry the same intended meaning; types and contracts must do that.

## References

- International Organization for Standardization, [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html) — the product quality model defines functional correctness as providing correct results with the needed precision.
- W3C, [Data on the Web Best Practices](https://www.w3.org/TR/dwbp/) — specify formats, preserve metadata, and assess data quality at publication boundaries.
- [RFC 8949: Concise Binary Object Representation](https://www.rfc-editor.org/rfc/rfc8949) — a primary serialization specification illustrating typed values, validity, and deterministic encoding concerns.
- Python, [`dataclasses`](https://docs.python.org/3/library/dataclasses.html) — language-authoritative support for explicit value records and frozen instances.
