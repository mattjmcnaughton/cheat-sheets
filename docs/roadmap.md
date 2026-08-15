# Cheat Sheet Roadmap

This roadmap is a coverage model, not a claim that correctness has a closed
checklist. Each section starts with an overview: minimum guidance a coding agent
can apply before a focused sheet exists. Focused sheets then replace breadth
with a stronger default, narrower rules, and more specific mechanization.

The five starred sheets were selected first because they recur across languages
and architectures, sit on common effect boundaries, and turn silent corruption
or indefinite work into explicit outcomes. Ordering within the remaining
backlog is provisional.

## Computation

- [x] [Overview](../cheat-sheets/correctness/computation/overview.md)
- [ ] Preconditions, Postconditions, and Invariants
- [ ] Termination and Progress
- [ ] Determinism and Reproducibility
- [ ] Algorithm Selection and Complexity Bounds
- [ ] Randomness and Sampling
- [ ] Numerical Stability

## Data

- [x] [Overview](../cheat-sheets/correctness/data/overview.md)
- [x] [Time and Time Zones](../cheat-sheets/correctness/data/time-and-time-zones.md)
- [x] [Numbers and Money](../cheat-sheets/correctness/data/numbers-and-money.md)
- [x] [Absence and Emptiness](../cheat-sheets/correctness/data/absence-and-emptiness.md)
- [x] [Boundaries and Ranges](../cheat-sheets/correctness/data/boundaries-and-ranges.md)
- [x] [Equality and Ordering](../cheat-sheets/correctness/data/equality-and-ordering.md)
- [x] [Text and Encoding](../cheat-sheets/correctness/data/text-and-encoding.md)
- [ ] Parsing and Serialization
- [ ] Units and Dimensional Values
- [ ] Identity and Identifiers

## State

- [x] [Overview](../cheat-sheets/correctness/state/overview.md)
- [x] [Mutation and Aliasing](../cheat-sheets/correctness/state/mutation-and-aliasing.md)
- [ ] Concurrency and Shared State
- [ ] Caching and Staleness
- [ ] Invariants Across Intermediate Steps
- [ ] Leases and Fencing
- [ ] Ordering and Causality
- [ ] Replication and Read Consistency

## Contracts

- [x] [Overview](../cheat-sheets/correctness/contracts/overview.md)
- [x] **★ [Input Validation at Boundaries](../cheat-sheets/correctness/contracts/input-validation-at-boundaries.md)**
- [x] **★ [Retries and Idempotency](../cheat-sheets/correctness/contracts/retries-and-idempotency.md)**
- [x] **★ [Timeouts and Cancellation](../cheat-sheets/correctness/contracts/timeouts-and-cancellation.md)**
- [ ] Error and Failure Semantics
- [ ] Nullability and Partiality in Signatures
- [ ] Partial Outcomes and Batch Semantics

## Effects and Environment

- [x] [Overview](../cheat-sheets/correctness/effects-and-environment/overview.md)
- [x] **★ [Resource Lifecycle](../cheat-sheets/correctness/effects-and-environment/resource-lifecycle.md)**
- [ ] Filesystem Operations
- [ ] Network and Partial I/O
- [ ] Subprocesses and Child Processes
- [ ] Queues and Delivery Semantics
- [ ] Configuration and Environment
- [ ] Dependency and Platform Assumptions

## Persistence

- [x] [Overview](../cheat-sheets/correctness/persistence/overview.md)
- [x] **★ [Transactions and Isolation](../cheat-sheets/correctness/persistence/transactions-and-isolation.md)**
- [ ] Constraints and Persistent Invariants
- [ ] Durability and Acknowledgement
- [ ] Optimistic Concurrency and Lost Updates
- [ ] Transactional Outbox and Inbox
- [ ] Storage Model Semantics

## Failure and Recovery

- [x] [Overview](../cheat-sheets/correctness/failure-and-recovery/overview.md)
- [ ] Crash Consistency and Restart Safety
- [ ] Compensation and Rollback
- [ ] Reconciliation and Repair
- [ ] Poison Work and Quarantine
- [ ] Backup and Restore
- [ ] Degraded Operation

## Capacity

- [x] [Overview](../cheat-sheets/correctness/capacity/overview.md)
- [ ] Backpressure and Admission Control
- [ ] Bounded Queues and Buffers
- [ ] Resource Budgets and Quotas
- [ ] Overload and Load Shedding
- [ ] Retry Amplification
- [ ] Disk and Retention Growth

## Change

- [x] [Overview](../cheat-sheets/correctness/change/overview.md)
- [ ] Schema and API Evolution
- [ ] Migrations and Backfills
- [ ] Config and Feature Flags
- [ ] Refactoring Without Semantic Drift
- [ ] Deprecation

## Cross-cutting coverage

Testing and observability remain in each sheet's **How to mechanize** section
rather than becoming separate topics. Security, accessibility, and product
requirements can define correctness obligations, but this collection does not
duplicate their specialist guidance; it covers how to preserve an obligation
once the contract states it.
