# Correctness

**Software doing what it was expected to do.**

This area is divided by *where expectation and behavior come apart*, not by
technology or layer. A bug in a timestamp and a bug in a currency amount are the
same kind of problem — a value that does not mean what the reader assumed — and
they belong together, whatever language or service they appear in.

| Section | Where it comes apart | Status |
|---|---|---|
| [Data](data/README.md) | The values themselves | 6 sheets |
| [State](state/README.md) | What the program holds and how it changes | Roadmap |
| [Contracts](contracts/README.md) | What a caller is promised | Roadmap |
| [Change](change/README.md) | Behavior drifting from expectation over time | Roadmap |

The four sections separate along how the failure hides:

**Data** is wrong the moment the value is written. The wrong code and the right
code usually look identical, because the defect is in the type the value arrived
in, not the operation performed on it.

**State** is correct at every individual step and wrong in the sequence. Each
write is valid, each read is valid, and the interleaving is not.

**Contracts** are correct on each side and wrong between them. The caller's code
holds against the contract they believed in, and so does the callee's.

**Change** is correct at the moment of the change. What breaks is the
relationship between new code and data written by the old code — introduced by
one diff and detonating in another.

Every sheet is written for two readers at once: an author reaching for a default
before writing the code, and a reviewer looking for what to ask about it. **The
default** and **Rules** serve the first; **Review questions** serves the second.

---

[← All cheat sheets](../../README.md)
