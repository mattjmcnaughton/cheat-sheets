# Correctness / Persistence

**Data surviving concurrency, commits, crashes, and process lifetime.**

Persistence failures hide between statements and writers, or between an
acknowledged operation and the durability the application assumed. Storage
models, constraints, isolation, transaction boundaries, and flush settings are
part of behavior, not implementation details.

## Sheets

| Sheet | Covers |
|---|---|
| [Overview](overview.md) | Minimum invariant, constraint, transaction, isolation, durability, and schema guidance |
| [Transactions and Isolation](transactions-and-isolation.md) | Lost updates, write skew, phantoms, constraints, and external effects outside commit |

## Planned sheets

See the [roadmap](../../../docs/roadmap.md#persistence).

---

[← Correctness](../README.md)
