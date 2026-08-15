# Correctness / State

**What the program holds, and how it changes.**

The `data` sheets deal with values considered one at a time: is this number
right, does this timestamp mean what you think, is this string the same string.
State is what happens once values are held somewhere and modified over time —
by a second reference, a second thread, a second process, or a second machine.

The failure shape here is different. A data bug is wrong the moment it is
written. A state bug is correct at every individual step and wrong in the
sequence: each write is valid, each read is valid, and the interleaving is not.
That is why these sheets lean harder on the lower rungs of the mechanization
ladder — invariant assertions and reconciliation — than the `data` sheets do.

## Sheets

| Sheet | Covers |
|---|---|
| [Overview](overview.md) | Minimum ownership, transition, atomicity, lifecycle, and visibility guidance |
| [Mutation and Aliasing](mutation-and-aliasing.md) | Two names for one object; defensive copying; when shared mutable structure stops being an optimization and starts being a bug |

## Planned sheets

These filenames are provisional.

| Sheet | Covers |
|---|---|
| `concurrency-and-shared-state.md` | Races, atomicity of compound operations, lock scope, what "thread-safe" does and does not promise |
| `caching-and-staleness.md` | Invalidation, negative caching, stampedes, and how long a wrong answer is allowed to live |
| `invariants-across-intermediate-steps.md` | Multi-step updates that pass through states no reader should ever see |
| `leases-and-fencing.md` | Expiring exclusivity, the gap between "my lease expired" and "I noticed", fencing tokens |
| `ordering-and-causality.md` | Happens-before, causal vs. wall-clock ordering, message reordering and its consequences |
| `replication-and-read-consistency.md` | Read-your-writes, monotonic reads, and what a replica is allowed to tell you |

To start one, copy [`_template/sheet-template.md`](../../../_template/sheet-template.md)
and read [`CONTRIBUTING.md`](../../../CONTRIBUTING.md).

---

[← Correctness](../README.md)
