# Correctness / Data

**The values themselves.**

These sheets cover the point where a single value stops meaning what the
code assumes it means — before any question of state, contract, or change
arises. They sit close together on purpose, and each one hands its neighbours'
territory back with a link rather than covering it twice.

| Sheet | Bug classes | Highest rung |
|---|---|---|
| [Overview](overview.md) | Representation mismatch, boundary errors, lossy conversion | type |
| [Time and Time Zones](time-and-time-zones.md) | UTC drift, DST gaps and overlaps, wall vs. monotonic clocks, midnight assumptions | lint |
| [Numbers and Money](numbers-and-money.md) | Float equality, binary float for currency, integer overflow, rounding mode | type |
| [Absence and Emptiness](absence-and-emptiness.md) | Null vs. empty vs. missing vs. default collapsed into one | type |
| [Boundaries and Ranges](boundaries-and-ranges.md) | Off-by-one, inclusive/exclusive mismatch at API edges | property test |
| [Equality and Ordering](equality-and-ordering.md) | `equals`/`hashCode` contract, non-transitive comparators, `NaN` breaking trichotomy | property test |
| [Text and Encoding](text-and-encoding.md) | Normalization, case folding, grapheme vs. code point vs. byte, collation | lint |

**Highest rung** is the top of the [mechanization ladder](../../../CONTRIBUTING.md#the-mechanization-ladder)
that the sheet's guidance actually reaches — not the best that exists. The
overview and two focused sheets reach a type that makes bad states
unrepresentable. Two stop at lint, because the language offers one string type
and one date-time type and cannot tell your intent apart. Two stop at property
tests, because their invariants are laws about behaviour — transitivity, tiling
— that no type system checks.

## Where the boundaries run

- Float representation belongs to **Numbers**; what `NaN` does to a comparator
  belongs to **Equality**.
- Whether a value is absent belongs to **Absence**; whether `""` and `" "` are
  the same value belongs to **Text**.
- Whether a comparator is legal belongs to **Equality**; which collation is
  correct belongs to **Text**.
- Half-open intervals belong to **Boundaries**, including for time spans;
  **Time** links there rather than restating the convention.
- Integer overflow belongs to **Numbers**; **Boundaries** links there for the
  midpoint case.

---

[← Correctness](../README.md)
