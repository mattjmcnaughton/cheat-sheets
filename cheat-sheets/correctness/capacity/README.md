# Correctness / Capacity

**Behavior at resource and load limits.**

Capacity failures hide in totals and rates. One request succeeds while queues,
bytes, retries, workers, connections, or retained artifacts grow without bound.
Correct behavior includes controlled refusal and backpressure before exhaustion
turns a local limit into system-wide failure.

## Sheets

| Sheet | Covers |
|---|---|
| [Overview](overview.md) | Minimum bounds, admission, backpressure, quota, retry, and overload guidance |

## Planned sheets

See the [roadmap](../../../docs/roadmap.md#capacity).

---

[← Correctness](../README.md)
