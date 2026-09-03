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

## Sheets

| Sheet | Covers |
|---|---|
| [Overview](overview.md) | Minimum input, result, failure, retry, cancellation, and compatibility guidance |
| [Input Validation at Boundaries](input-validation-at-boundaries.md) | Where validation belongs, parse-don't-validate, and what "trusted" means one layer in |
| [Retries and Idempotency](retries-and-idempotency.md) | What may safely be retried, idempotency keys, and at-least-once delivery meeting non-idempotent handlers |
| [Timeouts and Cancellation](timeouts-and-cancellation.md) | Deadlines that propagate, work that outlives its caller, and what a timeout says about whether the work happened |

## Planned sheets

These filenames are provisional.

| Sheet | Covers |
|---|---|
| `error-and-failure-semantics.md` | Which failures are expected, what a caller may assume after one, and the difference between an error and a bug |
| `nullability-and-partiality-in-signatures.md` | Partial functions, what a signature promises about absence, and where the caller learns it |
| `partial-outcomes-and-batch-semantics.md` | Per-item success, failure, and unknown outcomes without reporting a partial result as complete |

To start one, copy [`_template/sheet-template.md`](../../../_template/sheet-template.md)
and read [`CONTRIBUTING.md`](../../../CONTRIBUTING.md).

---

[← Correctness](../README.md)
