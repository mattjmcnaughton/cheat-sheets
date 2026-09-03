---
title: Contract Correctness Overview
bug_classes: [invalid-input-acceptance, undocumented-failure, incompatible-response, unsafe-retry, cancellation-loss]
authority: design
mechanizable: property-test
maturity: draft
last_reviewed: 2026-08-15
---

# Contract Correctness Overview

## Why review misses it

Caller and callee can each be internally correct against different promises.
The signature often omits valid ranges, failure effects, retry behavior,
ordering, freshness, and compatibility rules; prose may describe them far from
the diff. Tests written by one side repeat that side's interpretation, so the
mismatch appears only when an independent implementation reaches the boundary.

## The default

**Define each boundary as accepted inputs, success result, failure result and
effects, then encode that contract in the interface and test every independent
implementation against the same executable examples.**

## Rules

1. **Specify accepted input completely.** Include syntax, units, ranges,
   required combinations, size limits, and how unknown fields are handled;
   reject invalid input before causing effects.
2. **Return a typed success shape.** Keep values callers must distinguish in
   separate fields or variants rather than magic strings, sentinel numbers, or
   undocumented nulls.
3. **Define failures as part of the interface.** Give each expected failure a
   stable machine-readable category and state whether any effect may already
   have happened.
4. **State retry semantics explicitly.** Say which operations are idempotent,
   which require an operation key, and what result a duplicate receives; never
   infer safety from an HTTP method or transport error alone.
5. **Propagate deadlines and cancellation.** Bound downstream work by the
   caller's remaining budget, stop work when cancellation is authoritative, and
   state when work may continue after the response ends.
6. **Preserve compatibility deliberately.** Accept old valid inputs during the
   announced window, ignore or reject unknown fields by stated policy, and add
   rather than reinterpret existing values.
7. **Keep validation consistent across implementations.** Generate clients and
   validators from one schema where possible, then test semantics the schema
   cannot express from one shared conformance suite.
8. **Expose partial outcomes.** Return which items succeeded, failed, or remain
   unknown; never report whole-request success after silently dropping work.
9. **Agree on the contract before either side ships.** *(Design authority:
   producers and consumers must share the same versioning, errors, retries,
   cancellation, and partial-success semantics.)*

## Anti-patterns

**"The signature is the contract."** Types capture useful shape, but usually
omit ranges, effects, freshness, ordering, timeout outcomes, and compatibility.
Record those promises where both sides test them.

**"Return a generic error."** One error path is easy to propagate. It forces
callers to parse text or retry everything, including permanent rejection and
operations that may already have completed.

**"Validate on both sides for safety."** Client validation improves feedback,
but only the callee controls the boundary. Two hand-written validators drift;
keep server validation authoritative and derive or conformance-test the rest.

**"A timeout means nothing happened."** A timeout proves only that no answer
arrived in time. Retrying an operation with an unknown outcome duplicates its
effects unless the contract supplies identity or status lookup.

**"Adding a field cannot break anyone."** Required fields, stricter validators,
closed enumerations, and consumers that reject unknown data turn additive
changes into incompatibilities.

## What it costs

Precise contracts require design work, stable error and operation identifiers,
schema evolution, and a conformance suite maintained independently of either
implementation. Idempotency records and status lookup consume storage;
cancellation propagation complicates APIs; compatibility windows retain old
paths. The payoff is localized disagreement: an integration fails at the
boundary instead of corrupting state behind it.

## Review questions

- Which inputs are valid, and can the interface express every constraint?
- What may the caller assume after each success and failure variant?
- If the response is lost, how does the caller learn whether effects happened?
- Can this operation be retried, and what identifies a duplicate?
- Does cancellation stop downstream work, and how is the remaining deadline
  propagated?
- What does an older consumer do with each new field or enum value?
- Can a partial result be mistaken for complete success?
- Which shared conformance test would fail if caller and callee disagreed here?

## How to mechanize

**Type — encode shape and expected variants.** Use distinct request and result
types, closed success variants, and explicit expected-failure variants. Types
cannot encode all cross-field constraints, side effects, retry safety, or
compatibility with implementations in other languages.

**Lint — enforce interface hygiene.** Fail the build on undocumented public
errors, unbounded outbound calls, discarded cancellation, bare nullable results,
and handlers that perform effects before boundary validation. A static check
cannot prove that prose and behavior agree.

**Property test — the highest shared rung.** Generate valid and invalid requests
from the contract and run them against every implementation. Assert equivalent
success and error categories, no effects after rejected input, stable duplicate
outcomes, and encode/decode round trips across supported versions.

**Runtime assertion — defend each boundary.** Validate requests before effects,
enforce deadlines, reject conflicting reuse of an operation key, and assert that
every batch item appears exactly once among success, failure, and unknown.

**Observation — detect disagreements in production.** Measure validation
failures by contract version, unknown error categories, retries and duplicate
keys, deadline overruns, and partial-result counts. Observation cannot identify
the intended promise when no contract states it; stop there and fix the design.

## References

- [RFC 9110: HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110) — authoritative definitions of methods, status semantics, safety, and idempotency.
- [RFC 9457: Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457) — a standard machine-readable error representation.
- [RFC 8927: JSON Type Definition](https://www.rfc-editor.org/rfc/rfc8927) — a specification for portable request and response schemas.
- Protocol Buffers, [Language Guide](https://protobuf.dev/programming-guides/proto3/) — authoritative field, unknown-field, and evolution semantics for a widely used interface definition language.
- gRPC, [Cancellation](https://grpc.io/docs/guides/cancellation/) and [Deadlines](https://grpc.io/docs/guides/deadlines/) — protocol implementation guidance for propagating termination and time budgets.
- Consumer-Driven Contracts authors, [Pact specification](https://github.com/pact-foundation/pact-specification) — an executable, implementation-neutral contract format and conformance specification.
