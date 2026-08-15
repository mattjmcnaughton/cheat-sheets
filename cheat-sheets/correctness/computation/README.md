# Correctness / Computation

**Whether the program derives the promised result.**

Computation fails when valid-looking operations implement the wrong rule, omit
an edge case, depend on ambient nondeterminism, or do not terminate within the
declared bounds. The contract may be understood and every value well-formed;
the algorithm still fails its precondition, postcondition, or invariant.

## Sheets

| Sheet | Covers |
|---|---|
| [Overview](overview.md) | Minimum precondition, postcondition, termination, determinism, and edge-case guidance |

## Planned sheets

See the [roadmap](../../../docs/roadmap.md#computation).

---

[← Correctness](../README.md)
