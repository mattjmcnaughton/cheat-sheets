# Correctness / State

**What the program holds, and how it changes.**

The `data` sheets deal with values considered one at a time: is this number
right, does this timestamp mean what you think, is this string the same string.
State is what happens once values are held somewhere and modified over time —
by a second reference, a second thread, a second process, or a second machine.

The failure shape here is different. A data bug is wrong the moment it is
written. A state bug is correct at every individual step and wrong in the
sequence: each write is valid, each read is valid, and the interleaving is not.
Choose mechanization for the failure: static checks can catch shared defaults,
while invariants spanning updates need checks of behavior over time.

| Sheet | Bug classes | Highest rung |
|---|---|---|
| [Mutation and Aliasing](mutation-and-aliasing.md) | Shared mutable defaults, shallow-copy aliases, escaped mutable state, false immutability | lint |
| [Resource Lifecycle](resource-lifecycle.md) | Leaks, use after close, double release, failed partial acquisition | lint |
| [Concurrency and Shared State](concurrency-and-shared-state.md) | Lost updates, check-and-act races, inconsistent snapshots, deadlocks | property test |
| [Caching and Staleness](caching-and-staleness.md) | Stale fills, incomplete keys, stale negative entries, stampedes | property test |
| [Invariants Across Intermediate Steps](invariants-across-intermediate-steps.md) | Partial publication, write skew, mixed versions, partial failure | property test |
| [Leases and Fencing](leases-and-fencing.md) | Expired owners, unfenced effects, reused epochs, non-atomic fence checks | property test |
| [Ordering and Causality](ordering-and-causality.md) | Timestamp-based causal assumptions, reordered effects, skipped predecessors, concurrent conflicts | property test |
| [Replication and Read Consistency](replication-and-read-consistency.md) | Read regressions, stale leaders, mixed replica snapshots | property test |

**Highest rung** is the strongest concrete check described by the sheet,
following the [mechanization ladder](../../../CONTRIBUTING.md#the-mechanization-ladder).
The two lint entries target bounded Python patterns. The remaining sheets use
generated operation histories because ordinary types and static checks do not
establish their cross-step or distributed guarantees.

## Where the boundaries run

- **Mutation** defines which references may change a value; **Resource
  Lifecycle** defines who releases a handle and when its use must end.
- **Concurrency** defines the synchronization protocol; **Intermediate Steps**
  defines the invariant, publication boundary, and coherent read.
- **Caching** governs derived copies and their freshness; **Replication**
  governs which committed history a read must observe.
- **Leases** orders ownership epochs; **Ordering** governs effects and
  dependencies within or across those epochs.

---

[← Correctness](../README.md)
