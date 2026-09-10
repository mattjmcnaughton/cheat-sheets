---
title: Replication and Read Consistency
bug_classes: [read-after-write-regression, non-monotonic-read, stale-leader-read, mixed-replica-snapshot]
authority: design
mechanizable: property-test
maturity: draft
last_reviewed: 2026-09-08
---

# Replication and Read Consistency

## Why review misses it

The query is correct at each replica. The unexpected answer comes from routing
this request to a replica that has not applied the state the caller already
observed. Tests using one connection to one server cannot expose that
regression. A successful write acknowledgement also leaves unstated which
replicas can already answer reads about it.

## The default

**Choose a read guarantee for each operation, carry the session's required
version or dependency information, and wait, reroute, or fail when a replica
cannot satisfy it.**

## Rules

1. **Name the required guarantee at the read boundary.**
   **Needs design authority:** agree whether the operation needs read-your-writes,
   monotonic reads, bounded staleness, or a linearizable read.
2. **Separate acknowledgement durability from query visibility.** A replica
   may have received or persisted a write without applying it for reads.
3. **Carry the acknowledged write position into dependent reads.** Route only
   to a replica whose applied history includes that write, or wait for it.
4. **Carry previously observed progress when monotonic reads are promised.**
   Read-your-writes alone does not prevent regression on another writer's data.
5. **Use a protocol that establishes current authority for linearizable reads.**
   A server calling itself leader may already have been replaced.
6. **Keep all fields of a coherent read on one suitable snapshot.** Individually
   fresh reads from different replicas can still describe different moments.
7. **Make failover preserve or explicitly reject session requirements.** A
   position from an old history must not be silently treated as comparable to
   an unrelated new history.
8. **Enforce the same guarantee on cache hits and fallback paths.** Routing the
   database read correctly does not help if an earlier layer returns old data.

For visibility dependencies between events, see
[Ordering and Causality](ordering-and-causality.md); for cached copies, see
[Caching and Staleness](caching-and-staleness.md).

## Anti-patterns

**"Read from any replica after the write succeeds."** This distributes load,
but a successful acknowledgement need not imply every replica has applied the
write. Require an applied-position barrier or use a read path with the needed
consistency guarantee.

**"Pin the session to one replica."** Affinity reduces switching but does not
ensure that replica saw the write, and failover can lose the session's floor.
Carry the required progress explicitly and validate it after rerouting.

**"Sleep briefly after writing."** A delay may hide lag in normal operation
but cannot bound catch-up during an outage. Wait for an actual applied position
with a deadline and a defined failure response.

**"The quorum math makes any read current."** Intersecting sets are only one
part of a protocol. Use the storage system's specified read algorithm, including
version selection and its concurrent-write and failure behavior.

**"The dashboard says replication lag is zero."** A sampled aggregate does
not certify this replica and this write. Validate a request-specific progress
requirement rather than treating monitoring as a read barrier.

## What it costs

Waiting for replica progress adds latency and can make reads unavailable during
a partition. Session tokens add routing and recovery state. Stronger reads may
need coordination with other replicas. Weaker reads can serve useful results
sooner, but only where the application accepts their possible observations.

## Review questions

- Which read guarantee does this caller actually depend on?
- Does this acknowledgement mean received, durable, or applied—and where?
- How does this read carry the caller's last successful write?
- Can switching replicas return state older than the caller already observed?
- How does this read establish that its leader still has authority?
- Are these related fields read from one coherent snapshot?
- What happens to the session token on failover, timeout, or a cache hit?

## How to mechanize

**Property test — check client histories while controlling replication.**
Generate writes, replica delays, reads, routing changes, and failovers. For a
single ordered replication history, record applied positions and session floors.
Assert that successful read-your-writes requests include the caller's preceding
acknowledged writes, and that monotonic reads never move below the session's
observed history. Check progress, not numeric payload values: a later valid
balance may be smaller than an earlier one.

Types can require a token but cannot show that a replica has applied it. Lint
can check that the token is forwarded, not that the storage protocol honors it.
Generated histories are the highest applicable rung for the read contract.

Force a read onto a lagging replica after acknowledgement, then repeat after
failover and through the cache. Require waiting, rerouting, or an explicit
failure rather than silent weakening. For linearizable reads, check recorded
invocation and response histories against a sequential model preserving
real-time order. A passing test covers those schedules, not every partition.
For sharded or divergent histories, test dependency-aware tokens rather than
assuming one scalar position orders everything.

## References

- Douglas B. Terry, *Replicated Data Consistency Explained Through Baseball*,
  Microsoft Research Technical Report MSR-TR-2011-137, 2011 — distinct read
  guarantees and session requirements.
- PostgreSQL Global Development Group, *PostgreSQL 18 Documentation*, §26.2,
  "Log-Shipping Standby Servers" — asynchronous replication and the distinction
  between remote write, flush, and apply acknowledgements.
- Diego Ongaro and John Ousterhout, *In Search of an Understandable Consensus
  Algorithm (Extended Version)*, 2014, §8 — precautions required for
  linearizable reads from a leader.
