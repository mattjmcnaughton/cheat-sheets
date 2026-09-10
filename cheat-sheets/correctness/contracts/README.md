# Correctness / Contracts

**What a caller is promised.**

A contract is the set of expectations that survive a call: what inputs are
accepted, what the callee guarantees on success, what it guarantees on failure,
and what the caller must do to hold up their end. Contracts fail when the two
sides disagree — and both sides are usually written by people who each read the
signature and each concluded something reasonable.

The failure shape here is asymmetric. The caller's code is correct against the
contract they believed in, and so is the callee's. Nothing in either diff is
wrong; the mismatch only exists between them, which is why so much of this
sub-section is about making the promise explicit in the signature rather than in
the documentation.

| Sheet | Bug classes | Highest rung |
|---|---|---|
| [Input Validation at Boundaries](input-validation-at-boundaries.md) | Unchecked input, lossy coercion, stale validation, parser resource exhaustion | property test |
| [Error and Failure Semantics](error-and-failure-semantics.md) | Errors reported as success, undocumented partial effects, lost causes, ambiguous outcomes | property test |
| [Nullability and Partiality in Signatures](nullability-and-partiality-in-signatures.md) | Unchecked absence, ambiguous sentinels, hidden partial functions, invalid result combinations | type |
| [Retries and Idempotency](retries-and-idempotency.md) | Duplicate effects, reused operation keys, lost deduplication records, retry amplification | property test |
| [Timeouts and Cancellation](timeouts-and-cancellation.md) | Reset budgets, orphaned work, swallowed cancellation, timeout mistaken for rollback | property test |
| [Partial Writes Across Services](partial-writes-across-services.md) | Lost dual writes, hidden pending states, unsafe compensation, stranded workflows | property test |

**Highest rung** is the strongest concrete check described by the sheet,
following the [mechanization ladder](../../../CONTRIBUTING.md#the-mechanization-ladder).
The type entry requires checked callers and validated boundaries. The property
tests exercise acceptance predicates, failure postconditions, or operation
histories that signatures alone cannot establish.

## Where the boundaries run

- **Input Validation** defines how external representations enter the domain;
  **Nullability** defines which result cases a caller must handle.
- **Failure Semantics** defines the meaning and remaining state of an error;
  **Retries** defines when repeating an operation preserves its intended effect.
- **Timeouts** bounds waiting and defines cancellation ownership; it does not
  determine whether a remote effect committed.
- **Partial Writes** coordinates independent commit boundaries; State's
  [Intermediate Steps](../state/invariants-across-intermediate-steps.md) covers
  invariants within one publication boundary.
- Change's [Schema and API Evolution](../change/schema-and-api-evolution.md)
  covers compatibility when these promises change over time.

---

[← Correctness](../README.md)
