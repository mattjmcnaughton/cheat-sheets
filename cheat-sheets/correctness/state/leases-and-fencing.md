---
title: Leases and Fencing
bug_classes: [expired-owner-write, unfenced-side-effect, fencing-token-reuse, non-atomic-fence-check]
authority: design
mechanizable: property-test
maturity: draft
last_reviewed: 2026-09-08
---

# Leases and Fencing

## Why review misses it

The owner checks its lease, then writes. The diff hides the pause between those
operations: the process can stop running, the lease can expire, and a successor
can take over before the original request arrives. The old owner resumes with
the same local variables and no evidence that it has lost authority.

## The default

**Attach a monotonically increasing ownership epoch to every protected write,
and make the receiving resource atomically reject older epochs once a newer
epoch has been installed.**

## Rules

1. **Treat a lease as time-limited permission, not proof a former owner stopped.**
   Expiration cannot cancel a paused process or recall a request in transit.
2. **Allocate epochs in ownership order from an authority that cannot reuse
   them after restart or failover.** A random identifier is unique but does not
   establish which ownership came later.
3. **Carry the epoch to the component that performs the protected effect.**
   **Needs design authority:** extend the resource's write contract; checking
   only in the worker leaves delayed requests unfenced.
4. **Compare the epoch and perform the write in one atomic operation.** A
   separate check leaves a gap in which another owner can install a newer epoch.
5. **Persist the resource's highest accepted epoch with the protected state.**
   Losing that boundary on restart can admit an old owner's delayed request.
6. **Install the new epoch before treating handover at that resource as complete.**
   Highest-seen fencing rejects an old request only after the resource has seen
   the new epoch; it does not detect lease expiry by itself.
7. **Separate ownership epochs from operation identifiers and sequence numbers.**
   Two writes from the same owner share an epoch, so fencing alone neither
   deduplicates requests nor orders that owner's writes.
8. **Stop protected work when renewal is uncertain and reacquire after loss.**
   Local restraint reduces stale attempts; resource-side enforcement still
   supplies the safety boundary.

For the ordering of effects within an epoch, see
[Ordering and Causality](ordering-and-causality.md).

## Anti-patterns

**"Check the lease just before writing."** It narrows the apparent race but
cannot eliminate a pause after the check. Send the epoch with the write and
enforce it at the recipient.

**"Make the lease longer than the longest job."** Longer leases reduce renewal
pressure but do not bound process pauses or message delay. Use fencing and
choose lease duration for recovery behavior, not as a substitute for rejection.

**"Put the token in the request for auditing."** Recording ownership helps
diagnosis but does not prevent an old write. Reject older epochs before applying
the effect, atomically with the state change.

**"A fresh owner ID is a fence."** Uniqueness distinguishes owners without
ordering them. Use ordered epochs, or a recipient protocol that atomically
installs and validates the exact current owner.

**"One fenced database write protects the whole job."** The database may reject
old writes while a second endpoint still accepts them. Fence every protected
sink or redesign the job so all effects pass through an enforcing authority.

## What it costs

Fencing requires resource support, durable epoch state, and an ordered ownership
authority. A sink that cannot check ownership cannot inherit safety merely from
the caller using a lease. Handover across multiple sinks needs an explicit
protocol and may be temporarily unavailable while the new epoch is installed.

## Review questions

- Can this owner pause past expiry and later resume the write?
- Who allocates epochs, and can recovery reuse or decrease them?
- Which component rejects an old epoch before performing the effect?
- Are the comparison, epoch update, and effect atomic together?
- What happens if an old request arrives before the successor installs its epoch?
- Does epoch state survive resource restart and restore?
- What handles duplicates and reordering within the same epoch?

## How to mechanize

**Property test — generate handovers with delayed writes.** Model acquisition,
renewal, expiry, pauses, epoch installation, writes, and restart. At the real
resource adapter, force owner A to pause, let B acquire and install a newer
epoch, then deliver A's request. Assert rejection and no change to protected
state. Generate multiple handovers and out-of-order deliveries.

Types can require an epoch argument but cannot prove that the remote sink
enforces it. Lint can check argument presence, not atomic acceptance or durable
epoch ordering across processes. Generated histories therefore provide the
highest applicable rung for the end-to-end protocol.

Assert that the persisted highest epoch never decreases and that every accepted
write's epoch is at least the previously installed one. Deliver an old write
before installation too: either permit it under the stated handover contract
or verify the stronger authority check that rejects it. Test two writes racing
at the sink and repeat after restart; a mocked token comparison does not verify
the storage transaction.

## References

- Mike Burrows, *The Chubby Lock Service for Loosely-Coupled Distributed
  Systems*, USENIX OSDI 2006, §§2.1, 2.4 — acquisition counts, sequencers, and
  recipient-side rejection of delayed requests.
- Cary G. Gray and David R. Cheriton, *Leases: An Efficient Fault-Tolerant
  Mechanism for Distributed File Cache Consistency*, ACM SOSP 1989, DOI
  10.1145/74850.74870 — time-limited grants and their timing assumptions.
