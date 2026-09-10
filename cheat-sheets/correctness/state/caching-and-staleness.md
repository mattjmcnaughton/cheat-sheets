---
title: Caching and Staleness
bug_classes: [stale-refill, missing-cache-key-dimension, negative-cache-staleness, cache-stampede]
authority: design
mechanizable: property-test
maturity: draft
last_reviewed: 2026-09-08
---

# Caching and Staleness

## Why review misses it

A cache hit returns the right shape even when it represents an old state or a
different request. The write that makes it wrong may be in another service.
Deleting a key looks sufficient until an older in-flight read completes after
the deletion and fills it again.

## The default

**Cache only behind a stated freshness contract: key by every input that changes
the answer, retain enough age or version information to enforce that contract,
and define what happens when a fresh answer cannot be obtained.**

## Rules

1. **Choose the permitted staleness for each use of the value.**
   **Needs design authority:** agree whether stale data may drive the decision;
   a display and an authorization decision need not share a policy.
2. **Include every result-changing dimension in the key.** Tenant, identity,
   locale, filters, and representation version can all change the answer.
3. **Name the authority from which entries are rebuilt.** Eviction must not
   destroy the only copy of data described as a cache.
4. **Measure freshness from the relevant source observation or version.**
   Starting a TTL after a slow read can grant a new lifetime to old data.
5. **Prevent an older fill from undoing a completed invalidation.** Compare a
   generation or source version atomically when publishing the fill.
6. **Give cached absence its own expiry and invalidation behavior.** A negative
   answer can hide an object created after the lookup.
7. **Coalesce concurrent fills for the same key and bound backend concurrency.**
   A simultaneous expiry can turn one hot key into many source reads.
8. **Make stale-on-error behavior explicit and bounded.** A failed refresh must
   not silently renew freshness or turn an outage into unlimited stale serving.

For lag at the source replica itself, see
[Replication and Read Consistency](replication-and-read-consistency.md).
For cached rollout decisions, see
[Config and Feature Flags](../change/config-and-feature-flags.md).

## Anti-patterns

**"The TTL is the staleness bound."** Expiry is simple to configure, but a slow
fill or lagging source can already be old when inserted. Account for source
age and fill time; reject the entry when its full age exceeds the contract.

**"Delete after writing and we are done."** Invalidating after commit avoids
publishing uncommitted data, but an earlier read can still repopulate the key.
Use generation-checked publication or accept and bound that race explicitly.

**"Cache not found like any other value."** Repeated misses are expensive, but
a long-lived negative entry can mask newly created data. Invalidate absence on
creation and choose a negative expiry consistent with discovery requirements.

**"Serve stale whenever refresh fails."** This preserves availability while
quietly changing correctness. Permit stale serving only for named uses and
within a hard age limit; otherwise return an explicit unavailable result.

**"The key is just the object ID."** A compact key is convenient, but a cached
projection can depend on who requested it. Include the relevant identity or
cache the unfiltered source and apply access decisions separately.

## What it costs

Freshness requires metadata, invalidation work, or validation reads. More key
dimensions reduce sharing and increase memory use. Coalesced fills make callers
wait together and need bounded failure handling. A strict freshness boundary
can make a request unavailable when the authority cannot be reached.

## Review questions

- Which decision may use this cached value, and how old may it be?
- Can two requests with this key legitimately receive different answers?
- Does this TTL include source lag and time spent filling the entry?
- Can an old fill publish after an invalidation completes?
- How does a newly created object invalidate cached absence?
- What happens when many callers miss this key together?
- Does a failed refresh preserve the original age or reset it?

## How to mechanize

**Property test — generate cache histories with a controllable clock.** Model
source writes, reads that pause before publication, invalidations, expiry,
negative results, and refresh failures. Check every returned entry against the
declared version or age contract. For a generation-based design, increment the
generation on invalidation and require fill publication to compare and install
atomically; reject a fill started under an earlier generation.

Types can require a timestamp field but cannot prove that it measures source
age. Static checks cannot establish whether a cache key captures every semantic
input or whether distributed invalidations arrive in time. That leaves
generated operation histories as the highest rung for this contract.

Include this forced schedule: start an old read, commit a new value, invalidate,
then complete the old read. Also generate create-after-negative, source outage,
and many simultaneous misses. Assert the configured bound on active backend
fills and require fresh-only paths to fail rather than return expired data.
In production, record source age where measurable, rejected old fills, and
stale-serving counts; a hit-rate metric alone cannot check correctness.

## References

- Roy T. Fielding, Mark Nottingham, and Julian Reschke, *HTTP Caching*, RFC
  9111, June 2022, §§2, 4.1–4.4 — cache selection, age, validation, and
  invalidation for HTTP; application caches need their own explicit contract.
- Rajesh Nishtala et al., *Scaling Memcache at Facebook*, USENIX NSDI 2013,
  §3.2.1 — stale fills and coordinated cache population.
