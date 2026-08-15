---
title: Retries and Idempotency
bug_classes: [duplicate-side-effect, retry-storm, idempotency-key-collision, inconsistent-replay-result, lost-operation-result]
authority: design
mechanizable: property-test
maturity: draft
last_reviewed: 2026-08-15
---

# Retries and Idempotency

## Why review misses it

The retry loop looks like ordinary error handling, and each individual attempt is
correct. The failure lives between attempts: a response disappears after the
effect commits, ownership expires while work continues, or two workers observe no
deduplication record simultaneously. Unit tests return either success or failure;
they rarely deliver the important third outcome, “the operation completed but the
caller did not learn that it completed.”

## The default

**Assume every remotely invoked operation may be attempted more than once: attach
one stable idempotency key to the logical intent, atomically claim that key with the
effect, replay the recorded result within a documented scope, and retry only
transient failures with bounded exponential backoff and jitter.**

## Rules

1. **Model delivery as at least once, not exactly once.** A timeout or broken
   connection cannot distinguish “not run” from “committed, reply lost”; design the
   effect for repeated attempts.
2. **Generate one key per logical intent and reuse it for every attempt.** A new key
   on retry defeats deduplication; reusing a key for a changed request aliases two
   intents.
3. **Bind the key to a canonical request fingerprint.** Reject the same key with
   different operation, principal, target, or payload rather than replaying an
   unrelated result.
4. **Define deduplication scope and retention in the contract.** State tenant,
   operation, region, and time window; a key unique in one process is not unique
   after failover. *(Design authority: caller and executor must agree.)*
5. **Atomically claim the key and durable effect.** Put the deduplication record and
   state change in one transaction, or use a transactional outbox/inbox; “check,
   act, then record” races and crashes between steps.
6. **Record a stable terminal result, not merely “seen.”** Concurrent and later
   attempts must receive the same success identity or deterministic failure; an
   in-progress state needs explicit ownership and recovery rules.
7. **Retry only classified transient outcomes.** Retry connection loss, overload,
   and explicitly retryable conflicts; do not retry malformed requests, permanent
   policy failures, or an unknown operation unless it is idempotent.
8. **Bound attempts by a deadline and add exponential backoff with jitter.** Caps
   protect latency and capacity; jitter prevents synchronized clients from
   repeating overload. Deadline propagation belongs in
   [timeouts-and-cancellation](timeouts-and-cancellation.md).
9. **Reconcile effects whose atomic boundary cannot include the dedup store.** Use
   a stable downstream key and a repair job; never call two independent systems
   “atomic” because errors are rare.

## Anti-patterns

**“Retry on every exception.”** It centralizes resilience and handles transient
faults. It also repeats permanent failures, overloads an unhealthy dependency, and
duplicates effects whose completion is unknown.

**“Check then insert.”** Looking up the key before work avoids duplicate calls in
the common case. Two workers can both miss, both perform the effect, and only then
compete to insert the marker.

**“Mark it processed first.”** Claiming before work closes that race. A crash after
the marker but before the effect now loses the operation unless the state machine
distinguishes claimed, completed, and recoverable claims.

**“Idempotent means return success twice.”** Suppressing the second effect is not
enough when the caller needs the original resource ID or response. Persist and
replay the stable result.

**“Exactly once through configuration.”** Broker settings can reduce duplicates,
but cannot atomically encompass an arbitrary database or external side effect.
State the real transaction boundary and reconcile beyond it.

## What it costs

Deduplication adds a write and lookup to every logical operation, durable response
storage, an index on scope plus key, and cleanup after the retention window.
Canonical request fingerprints constrain future schema evolution. Holding claims
while work runs creates contention; expiring them creates a takeover race that
needs fencing or transactional ownership. Backoff increases user-visible latency,
while low retry caps expose transient faults. Cross-system effects require an
outbox, consumer inbox, and operational reconciliation rather than one call.

## Review questions

- If the effect commits and the reply is lost, what does the next attempt do?
- Is this key stable across attempts and unique to one unchanged logical intent?
- What principal, operation, region, and duration define the deduplication scope?
- Are claiming the key and committing the effect in one atomic boundary?
- What stable result does a concurrent or later duplicate receive?
- Which outcomes are retryable, and what bounds attempts, elapsed time, and delay?
- How is an abandoned in-progress claim recovered without two owners acting?
- What reconciliation detects duplication or loss beyond the transaction boundary?

## How to mechanize

**Type — unavailable as the ceiling.** Distinct `IdempotencyKey` and
`RequestFingerprint` types prevent accidental swaps, but no type proves two
processes claimed atomically or that a remote effect happened once.

**Lint — unavailable for the core guarantee.** Static checks can require retry
calls to name a policy and forbid unbounded loops, but cannot infer side effects or
transaction boundaries across services.

**Property test — the highest effective rung.** Generate histories with duplicate
delivery, concurrent attempts, crashes before and after each durable write, and
lost replies. Assert one committed logical effect per `(scope, key)`, identical
terminal results for identical fingerprints, rejection for changed fingerprints,
and eventual completion after recoverable claims. Run the state machine against
the real transactional adapter, not only a mock.

**Runtime assertion — enforce local invariants.** Add a unique constraint on
`(scope, key)`, a check that completed rows contain a result, and compare stored
and incoming fingerprints before replay. Cap attempts and elapsed retry time.

**Observation — cover external boundaries.** Count attempts per intent, key
conflicts, stale claims, retryable outcomes, and reconciled duplicate or missing
effects. Alert on retry amplification and oldest pending outbox age. Observation
cannot prove absence of duplicates; retention eventually removes the evidence.

## References

- [RFC 9110 §9.2.2, Idempotent Methods](https://www.rfc-editor.org/rfc/rfc9110#section-9.2.2) — when a client may automatically retry an HTTP request.
- [The Idempotency-Key HTTP Header Field](https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/) — key uniqueness, fingerprinting, expiry, and concurrent-request behavior; Internet-Draft, not a final RFC.
- Pat Helland, [Life beyond Distributed Transactions: an Apostate's Opinion](https://dl.acm.org/doi/10.1145/3012426.3025012), CIDR 2007 — retries, identity, and application-level uncertainty outside one transaction.
- Martin Kleppmann et al., [Transactions: Myths, Surprises and Opportunities](https://doi.org/10.1145/3448016.3457553), SIGMOD 2021 — transaction guarantees and distributed transaction boundaries.
- Marc Brooker, [Exponential Backoff and Jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) — simulations of synchronized retry contention and jitter; provider-authored technical analysis.
