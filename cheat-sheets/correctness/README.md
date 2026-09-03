# Correctness

**Software doing what it was expected to do.**

This area is divided by *where expectation and behavior come apart*, not by
technology or layer. A bug in a timestamp and a bug in a currency amount are the
same kind of problem — a value that does not mean what the reader assumed — and
they belong together, whatever language or service they appear in.

| Section | Where it comes apart | Sheets |
|---|---|---|
| [Computation](computation/README.md) | The result derived by the program | 1 |
| [Data](data/README.md) | The values themselves | 7 |
| [State](state/README.md) | What the program holds and how it changes | 2 |
| [Contracts](contracts/README.md) | What a caller is promised | 4 |
| [Effects and Environment](effects-and-environment/README.md) | Interaction with systems outside the core | 2 |
| [Persistence](persistence/README.md) | Data surviving concurrent work and process lifetime | 2 |
| [Failure and Recovery](failure-and-recovery/README.md) | Correctness after interruption or degradation | 1 |
| [Capacity](capacity/README.md) | Behavior at resource and load limits | 1 |
| [Change](change/README.md) | Behavior drifting from expectation over time | 1 |

The sections separate along how the failure hides:

**Computation** performs valid operations but derives the wrong result, fails to
terminate, or depends on ambient nondeterminism.

**Data** is wrong the moment the value is written. The wrong code and the right
code usually look identical, because the defect is in the type the value arrived
in, not the operation performed on it.

**State** is correct at every individual step and wrong in the sequence. Each
write is valid, each read is valid, and the interleaving is not.

**Contracts** are correct on each side and wrong between them. The caller's code
holds against the contract they believed in, and so does the callee's.

**Effects and Environment** are correct against an assumed filesystem, network,
process, queue, configuration, or platform that behaves differently in use.

**Persistence** is correct for one statement or writer and wrong across a
transaction boundary, concurrent history, crash, or durability setting.

**Failure and Recovery** is correct on the forward path and cannot safely
resume, compensate, reconcile, or restore after interruption.

**Capacity** is correct for one request and wrong when rates, retained bytes, or
resource totals reach their supported limits.

**Change** is correct at the moment of the change. What breaks is the
relationship between new code and data written by the old code — introduced by
one diff and detonating in another.

Every sheet is written for two readers at once: an author reaching for a default
before writing the code, and a reviewer looking for what to ask about it. **The
default** and **Rules** serve the first; **Review questions** serves the second.

---

[← All cheat sheets](../../README.md)
