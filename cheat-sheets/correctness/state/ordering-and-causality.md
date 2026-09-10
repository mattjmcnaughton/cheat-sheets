---
title: Ordering and Causality
bug_classes: [timestamp-as-causality, out-of-order-application, skipped-predecessor, conflicting-concurrent-update]
authority: design
mechanizable: property-test
maturity: draft
last_reviewed: 2026-09-08
---

# Ordering and Causality

## Why review misses it

Two sends appear in the correct order in one function. Delivery, processing,
and commitment are separate events, and a retry or a second consumer can
reverse the effects. Timestamps make a log look ordered without establishing
which event depended on which earlier state.

## The default

**Carry the ordering information your operation needs—an entity version,
sequence, or dependency set—and validate it where effects are applied; do not
infer causality from wall-clock timestamps or arrival order.**

## Rules

1. **Name the scope of required order: entity, partition, session, or global.**
   **Needs design authority:** agree this with producers and consumers; an
   order inside one partition does not order events in another.
2. **Allocate versions through the authority that serializes the entity's
   updates.** Independent counters at competing writers can assign the same
   version to conflicting changes.
3. **Distinguish replacement snapshots from predecessor-dependent deltas.**
   A complete version 12 snapshot may supersede version 10; a delta for version
   12 may require version 11 first.
4. **Apply an effect and advance its consumed version atomically.** Advancing
   first can skip work after a crash; advancing later can replay the effect.
5. **Make gaps trigger a defined wait, replay, or resynchronization path.**
   Silently skipping a missing predecessor changes the meaning of later deltas.
6. **Preserve dependency information across asynchronous handoffs.** The
   consumer cannot honor a causal predecessor that the message discarded.
7. **Choose an explicit policy for concurrent updates.** Reject, merge, or
   resolve them by a domain rule; an arbitrary tie-break is not evidence of
   causal order.
8. **Use logical clocks only for the guarantees they actually establish.**
   Lamport order respects causality in one direction; a lower logical timestamp
   does not prove that one event caused another.

For clock selection, see [Time and Time Zones](../data/time-and-time-zones.md).
For former owners sending late writes, see [Leases and Fencing](leases-and-fencing.md).

## Anti-patterns

**"The latest timestamp wins."** Timestamps are easy to compare but clock skew
can let an older action overwrite a later dependent one. Use authoritative
versions, or explicitly accept timestamp resolution as a conflict policy.

**"The queue is ordered."** Ordered delivery simplifies a single consumer;
parallel processing and retries can still reorder completion. Enforce sequence
at application time for each entity that requires it.

**"Anything with a larger version is safe."** That rule works for complete
replacement snapshots under a shared version order. For deltas, require the
expected predecessor and recover gaps before applying later changes.

**"Record the offset, then do the work."** Saving progress first avoids replay,
but a crash can permanently lose the effect. Commit progress with the effect
where possible; otherwise use a durable operation identity and a recovery
protocol that tolerates replay.

**"Sort by timestamp and node ID to recover history."** A tie-break creates a
deterministic display, not missing dependency information. Carry the dependency
or serialize the relevant updates before publishing them.

## What it costs

Per-entity sequencing limits parallelism for that entity. Gap recovery needs
retained history or a snapshot source. Dependency tracking adds metadata and
can delay visibility while predecessors are unavailable. A global order adds
coordination even between unrelated operations; require it only where the
invariant needs it.

## Review questions

- What scope is actually ordered by this sequence number?
- Who prevents competing writers from allocating the same entity version?
- Is this event a full replacement or a delta requiring its predecessor?
- What happens when version 12 arrives before version 11?
- Can a crash commit progress without committing the effect, or the reverse?
- Does this timestamp establish causality or merely choose a winner?
- Which dependencies must be visible before this effect becomes visible?

## How to mechanize

**Property test — generate reordered, duplicated, and delayed event streams.**
Create a reference sequence of entity changes, then vary delivery and consumer
completion order. For deltas, assert that every applied event had its required
predecessor and that consumed versions advance with committed effects. For
complete snapshots, assert that accepted versions never decrease. Require
convergence to the reference only after all required events or a valid recovery
snapshot have arrived and processing has completed.

Types can distinguish snapshots from deltas but cannot prove delivery order or
the presence of a remote predecessor. Static checks cannot recover discarded
causal metadata. Generated histories are therefore the highest applicable rung
for the cross-process behavior.

Inject crashes between effect and progress writes, test conflicting payloads
with the same version, and deliberately omit a predecessor. Check the named gap
policy instead of requiring progress through missing information. For causal
visibility, generate a dependency graph and assert that visible events include
their required predecessors. Preserve failing delivery schedules for replay.

## References

- Leslie Lamport, *Time, Clocks, and the Ordering of Events in a Distributed
  System*, Communications of the ACM 21(7), July 1978, DOI
  10.1145/359545.359563 — happened-before and logical clock ordering.
- Diego Ongaro and John Ousterhout, *In Search of an Understandable Consensus
  Algorithm (Extended Version)*, 2014, §§5.3, 8 — ordered replicated logs and
  client request identities for duplicate suppression.
