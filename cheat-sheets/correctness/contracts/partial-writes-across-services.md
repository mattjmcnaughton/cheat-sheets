---
title: Partial Writes Across Services
bug_classes: [lost-dual-write, hidden-pending-state, unsafe-compensation, stranded-workflow]
authority: design
mechanizable: property-test
maturity: draft
last_reviewed: 2026-09-09
---

# Partial Writes Across Services

## Why review misses it

The function calls two services and handles both errors. Each service commits
correctly on its own, but the diff offers no single point where both effects
become durable. Exceptions do not cover a process stopping between calls, and a
compensation test often assumes nobody observed or changed the first effect.

## The default

**When effects cannot share a transaction, persist a recoverable workflow with
explicit intermediate states and make each step and compensation safe to repeat.**

## Rules

1. **Identify every independent commit boundary before promising atomicity.**
   Two successful API calls do not constitute one transaction, even when issued
   from the same function.
2. **Prefer one transactional owner when the invariant requires atomic change.**
   **Needs design authority:** agree whether the domain can tolerate intermediate
   states before splitting the invariant across services.
3. **Name the pending, completed, and recovery-required states.** **Needs design
   authority:** specify what each reader and subsequent command may do while
   only some effects are committed.
4. **Persist workflow identity and progress before relying on another step.**
   Recovery must resume after a crash without depending on the coordinator's
   memory or the original caller remaining connected.
5. **Commit a local mutation and its outgoing intent in one transaction.**
   A transactional outbox closes the local database/message gap; its relay can
   still deliver duplicates and does not create global atomicity.
6. **Give each participant a stable step identity and a resolution path.**
   After a lost reply, query the established outcome or repeat safely instead
   of assuming the step did not run.
7. **Define compensation as a new domain action with its own preconditions.**
   A refund or reservation release must preserve intervening legitimate changes;
   restoring a saved object can overwrite someone else's work.
8. **Persist compensation attempts and handle their failure too.** A recovery
   action can time out or partially succeed just like a forward action.
9. **Assign recovery ownership and an age bound for pending work.** **Needs design
   authority:** define automatic resumption, escalation, and the evidence needed
   for manual resolution when progress cannot safely continue.

Use [Invariants Across Intermediate Steps](../state/invariants-across-intermediate-steps.md)
inside one publication boundary. Use [Retries and Idempotency](retries-and-idempotency.md)
for step identities and duplicate effects, and
[Ordering and Causality](../state/ordering-and-causality.md) when dependencies
between messages must survive reordering.

## Anti-patterns

**"Write the row, then publish the event."** The order is easy to read, but a
crash between commits loses the event. Publishing first instead risks an event
for a write that never commits. Commit the row and an outbox intent together,
then relay the intent with duplicate-safe consumption.

**"Wrap both remote calls in a local transaction."** The local database can
rollback its own writes but cannot retract a remote commit. Use a shared
transaction protocol only when all participants actually support its guarantee;
otherwise expose and recover the partial workflow.

**"Compensation restores the old snapshot."** Snapshot restoration resembles
rollback but can erase a concurrent legitimate update. Compensate the specific
effect conditionally, using its identity and the current domain state.

**"Catch the second failure and undo the first."** This covers one exception
path, but misses coordinator crashes and failed undo. Persist progress and run
recovery from durable state, including uncertainty about either action.

**"Eventually consistent means it will finish."** The phrase does not specify a
worker, retry policy, or terminal outcome. Assign a recovery owner and define
when pending work becomes an explicit unresolved case requiring intervention.

## What it costs

Durable workflows add state, delivery machinery, and recovery operations.
Intermediate states complicate readers and may reserve resources until recovery
finishes. Compensation can have real business costs and cannot make already
observed effects disappear. If these costs are unacceptable for the invariant,
reconsider the service boundary rather than describing partial commits as atomic.

## Review questions

- Which effects commit independently in this change?
- What does a reader see after each possible prefix of committed steps?
- Can a crash lose an outgoing intent after its local write commits?
- How does recovery distinguish an unattempted step from one with a lost reply?
- Are forward and compensating actions safe under duplicate delivery?
- Can compensation overwrite a concurrent valid change?
- Who resumes a stopped workflow, and when is unresolved work escalated?
- Does the success response mean acceptance or completion of every required step?

## How to mechanize

**Property test — generate workflow histories with crashes and recovery.** Model
participant states and the allowed visible combinations. Generate forward steps,
duplicate or reordered delivery, response loss, coordinator restart, and
compensation failure. After every step, check the documented visible-state
invariant; after restart, require the same workflow identity and durable progress
to determine the next action.

For a reservation workflow, check that completion requires all required
reservations, cancellation releases only reservations owned by that workflow,
and retries do not create another reservation for the same step. Inject failure
both before and after each participant commit, then lose the reply. Include a
concurrent operation whose updates compensation must preserve.

Types can name pending states but cannot establish atomicity across independent
stores or guarantee that recovery runs. Static checks cannot prove delivery and
compensation behavior. Generated histories are the highest applicable rung.
Check eventual completion only under explicit assumptions that dependencies
recover and workers keep executing; otherwise require a durable unresolved state
with the promised escalation path. Exercise the real local transaction boundary
to verify that the domain write and outbox intent commit or abort together.

## References

- Hector Garcia-Molina and Kenneth Salem, *Sagas*, Princeton University technical
  report CS-TR-070-87, January 7, 1987 — sequences of committed subtransactions
  and compensating transactions.
- Chris Richardson, *Pattern: Transactional Outbox*, Microservices Patterns,
  accessed 2026-09-09 — atomically storing outgoing messages with local changes
  and handling duplicate publication by the relay.
- Chris Richardson, *Pattern: Saga*, Microservices Patterns, accessed 2026-09-09
  — local transactions, compensation, and the absence of automatic isolation.
