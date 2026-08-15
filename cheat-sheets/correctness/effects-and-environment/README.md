# Correctness / Effects and Environment

**Interaction with systems outside the program's core.**

Effects fail where an assumption meets a filesystem, network, subprocess,
queue, configuration, dependency, runtime, or platform. These boundaries can
make partial progress, repeat work, block indefinitely, and behave differently
from an in-memory test double.

## Sheets

| Sheet | Covers |
|---|---|
| [Overview](overview.md) | Minimum partial-I/O, deadline, retry, subprocess, queue, configuration, and platform guidance |
| [Resource Lifecycle](resource-lifecycle.md) | Acquire, use, and release; ownership; partial acquisition; cancellation during cleanup |

## Planned sheets

See the [roadmap](../../../docs/roadmap.md#effects-and-environment).

---

[← Correctness](../README.md)
