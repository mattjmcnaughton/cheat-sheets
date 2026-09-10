---
title: Retries and Idempotency
bug_classes: [duplicate-side-effect, idempotency-key-reuse, lost-deduplication-record, retry-amplification]
authority: design
mechanizable: property-test
maturity: draft
last_reviewed: 2026-09-09
---

# Retries and Idempotency

## Why review misses it

The operation succeeds once in the test and its retry loop looks defensive.
Duplication needs a particular gap: the effect commits, the reply or acknowledgment
disappears, and another attempt runs. A mock that raises before doing anything
cannot expose that gap, and a sequential duplicate test misses competing workers.

## The default

**Retry a logical operation only when repeating it is safe; reuse its identity
across attempts and couple duplicate detection atomically with the effect it
protects.**

## Rules

1. **Define the intended effect that must not repeat.** Repeating an assignment
   may be harmless while repeating its notification or accounting entry is not.
2. **Create one operation identity per caller intent, before the first attempt.**
   Reuse it after timeouts and restarts; a new identity requests a new operation.
3. **Scope the identity and bind it to the intended request.** **Needs design
   authority:** agree caller scope, operation kind, semantic request comparison,
   retention, and the response to the same key with different intent.
4. **Commit duplicate detection and the protected local mutation together.**
   Use a uniqueness constraint and a transaction so two concurrent first attempts
   cannot both apply the effect.
5. **Return the established outcome or an explicit in-progress result.** A
   duplicate must not execute a second effect merely because the first response
   is unavailable.
6. **Retain deduplication evidence for the supported replay horizon.** Include
   delayed delivery, manual replay, and offline clients; after expiry, reject an
   old identity or explicitly end the guarantee.
7. **Retry only classified transient failures within one shared budget.**
   Bound attempts and elapsed time, use backoff with jitter, and honor valid
   server retry guidance within the remaining deadline.
8. **Assign one layer responsibility for automatic retries.** Independent retry
   loops multiply downstream attempts and can keep work alive after the caller
   has stopped waiting.
9. **Acknowledge delivery only after the durable effect commits.** A consumer
   that crashes before acknowledgment must safely handle redelivery.

An external effect cannot join a local deduplication transaction merely because
the request carries a key. Require the destination's idempotency contract or use
[Partial Writes Across Services](partial-writes-across-services.md). Propagate the
budget described in [Timeouts and Cancellation](timeouts-and-cancellation.md).

## Anti-patterns

**"Generate the key inside the retry loop."** Every attempt looks independent,
so the receiver correctly performs each one. Allocate and persist the identity
at the logical operation boundary, then reuse it for every attempt.

**"Look up the key, do the work, then save it."** This reads naturally but leaves
both a concurrency race and a crash gap. Make the unique claim, local mutation,
and outcome record one transaction.

**"Hash the payload to recognize duplicates."** Identical payloads can represent
two intentional purchases or sends. Use caller intent as the identity and a
request fingerprint only to detect conflicting reuse of that identity.

**"Retry every exception."** A uniform policy saves branching but repeats
permanent rejection and programming defects. Classify retryable failures and
stop when the operation budget expires; uncertainty alone does not authorize a
non-idempotent repeat.

**"The broker promises exactly once."** That promise may cover only broker state.
A database write or external request can still repeat. Name the exact transaction
boundary and deduplicate every effect outside it at its destination.

## What it costs

Durable operation records need storage, expiry rules, and concurrent-access
control. Keeping original results may retain data longer than the business
record itself. Backoff delays recovery, while retries spend downstream capacity.
If the effect cannot be deduplicated or checked, expose the uncertainty instead
of hiding it behind an automatic retry.

## Review questions

- What identifies one caller intent across attempts and process restarts?
- Which effects are covered by the idempotency guarantee?
- What prevents two simultaneous first attempts from both applying the effect?
- What happens when the same key arrives with a different request?
- Can the effect commit without its deduplication record?
- What happens to a delayed replay after the record expires?
- Which layer owns retries, and what limits total attempts and elapsed time?
- Does the test lose a reply after a successful commit?

## How to mechanize

**Property test — generate duplicate deliveries, concurrent attempts, and crashes
around commit.** For each operation identity, generate repeated matching requests
and conflicting requests; interrupt execution before and after the deduplication
claim, effect, commit, and acknowledgment. Restart against the same durable store.
Assert at most one protected effect, consistent results for matching duplicates,
and explicit rejection of conflicting intent.

Generate expiration and delayed replay together and check the documented
retention policy. Separately generate transient and permanent failures against
a fake clock, asserting that retry counts and the overall deadline remain bounded.

A key type cannot prove atomicity between the key and the effect. Static checks
cannot establish crash recovery or destination semantics. Generated histories
are the highest applicable rung. Run the concurrency and commit cases against
the actual storage mechanism; keep external test effects isolated and observable.
These checks establish behavior for exercised histories, not a universal
exactly-once guarantee for arbitrary external systems.

## References

- R. Fielding, M. Nottingham, and J. Reschke, *HTTP Semantics*, RFC 9110, §9.2.2,
  June 2022 — idempotent method semantics and restrictions on automatic retries.
- Malcolm Featonby, *Making retries safe with idempotent APIs*, Amazon Builders'
  Library, 2021 — caller request identities, atomic recording, late arrivals,
  and conflicting reuse.
- Marc Brooker, *Timeouts, retries, and backoff with jitter*, Amazon Builders'
  Library, 2019 — bounded retries, amplification across layers, and jitter.
- Chris Richardson, *Pattern: Idempotent Consumer*, Microservices Patterns,
  accessed 2026-09-09 — recording processed identities with consumer effects.
