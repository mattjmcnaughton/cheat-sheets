# Correctness / Failure and Recovery

**Correctness after interruption or degradation.**

The forward path is not enough. A fresh process must be able to discover what
happened, resume or compensate safely, quarantine work that cannot progress,
reconcile disagreement, and restore data into a verified usable system.

## Sheets

| Sheet | Covers |
|---|---|
| [Overview](overview.md) | Minimum restart, compensation, reconciliation, poison-work, degradation, and restore guidance |

## Planned sheets

See the [roadmap](../../../docs/roadmap.md#failure-and-recovery).

---

[← Correctness](../README.md)
