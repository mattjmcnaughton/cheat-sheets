---
title: Failure and Recovery Overview
bug_classes: [restart-loop, partial-rollback, unreconciled-state, poison-message, unverified-backup, recovery-overload]
authority: organizational
mechanizable: type
maturity: draft
last_reviewed: 2026-08-15
---

# Failure and Recovery Overview

## Why review misses it

Recovery code runs after control flow has been interrupted, memory has vanished,
dependencies disagree, and operators are under pressure. The diff usually shows
the forward path plus a catch block; it does not show a crash between two durable
writes, repeated startup, an old work item that always fails, or a restore onto
different infrastructure. Tests assert an error was returned, not that the next
process can discover and finish the work.

## The default

**Make durable progress restartable: record intent and phase before acting,
resume or compensate idempotently after interruption, quarantine work that
cannot progress, and continuously prove recovery by reconciliation and restore
tests.**

## Rules

1. **Place a crash boundary after every durable write and external effect.** For
   each boundary, specify what a fresh process reads and whether it resumes,
   repeats safely, compensates, or stops for intervention.
2. **Persist workflow identity, intent, phase, attempts, and last error.** Never
   depend on stack state or logs to decide what recovery must do.
3. **Make startup and replay idempotent.** Reopening resources, applying
   migrations, acquiring leases, and resuming work must tolerate having partly
   succeeded before the crash.
4. **Prefer rollback inside one transactional boundary; compensate across
   boundaries.** Define each compensation as a new, retryable business action,
   because a remote effect cannot be atomically erased and compensation can
   fail too. *(Design authority: participating systems must expose the needed
   identities and inverse actions.)*
5. **Reconcile from authoritative state.** Periodically compare intended and
   observed outcomes, classify drift, and repair with the same idempotent
   commands as normal processing rather than editing records by hand.
6. **Bound retries and quarantine poison work.** Record the terminal reason,
   preserve payload and identity under access controls, continue unrelated
   work, and provide an audited replay path after correction.
7. **Apply backoff with jitter and a global recovery budget.** After restart or
   dependency recovery, admit work gradually so retries, reconciliation, and
   normal traffic do not recreate the outage.
8. **Define a degraded mode that preserves core invariants.** Shed optional
   work, serve explicitly stale or partial data only where acceptable, and fail
   closed when proceeding would corrupt state or violate safety.
9. **Test restore, not backup creation.** Set recovery-point and recovery-time
   objectives, retain independent copies, restore into an isolated environment,
   verify application invariants, and rehearse cutover. *(Organizational
   authority: retention, access, capacity, and exercises require ownership and
   budget.)*

## Anti-patterns

**“Catch, log, and continue.”** Keeping the process alive feels resilient, but
it discards the durable fact that work is incomplete and lets later steps run
against an invalid state.

**“Retry forever.”** Transient failures do recover, but deterministic bad input
or revoked authorization consumes the queue indefinitely and hides behind a
growing attempt count.

**“Delete the partial record on failure.”** Cleanup restores a tidy view, but
can erase the only evidence needed to resume, compensate, audit, or reconcile;
the deletion can also fail halfway.

**“The backup job is green.”** Successful copying proves bytes were written,
not that keys, dependencies, procedures, capacity, and application versions can
restore those bytes within the objective.

**“Serve something rather than nothing.”** Degradation can preserve useful
reads, but fabricated success, silently stale authorization, or unrecorded
writes converts availability loss into corruption or unsafe behavior.

## What it costs

Durable workflow state, deduplication, quarantine storage, reconciliation, and
restore environments consume storage and engineering time. Compensation expands
the domain model. Backoff and load shedding delay completion; fail-closed modes
reduce availability. Recovery exercises require capacity and interrupt normal
work, but without them recovery time remains an assumption.

## Review questions

- What happens if the process stops after each write or external call in this
  change?
- Which durable record lets a fresh process distinguish not-started, in-progress,
  completed, compensating, and terminal work?
- Can resume, replay, and compensation run more than once safely?
- Which source is authoritative, and how does reconciliation detect and repair
  disagreement?
- When does failing work leave the retry path, and how is it inspected and
  replayed?
- What limits the load created when many workers restart together?
- Which operations remain available in degraded mode, and which invariant makes
  the rest fail closed?
- When was this data last restored and verified against the stated objectives?

## How to mechanize

**Type — encode workflow states.** Use a closed state machine whose transitions
require workflow identity and reject impossible phase changes. Types cannot
prove that a remote effect occurred or that backup media is usable.

**Lint — enforce recovery plumbing.** Reject unbounded retry loops, swallowed
exceptions, handlers without an operation identity, and new workflow states
without explicit resume and terminal transitions.

**Property test — crash at every boundary.** Generate workflows and terminate
the worker before and after each durable operation; restart repeatedly and
assert the invariant, eventual terminal state under a healthy dependency, and
at-most-once business effect despite at-least-once execution.

**Runtime assertion — stop impossible progress.** Validate legal state
transitions, lease ownership, attempt and age limits, and compensation
preconditions. Quarantine rather than discard a record that violates them.

**Observation — the highest complete rung.** Alert on workflow age, retry and
quarantine growth, reconciliation drift, compensation failures, restart storms,
recovery-budget saturation, and restore-test age. Run scheduled isolated
restores; measure achieved recovery point and time, then verify domain
invariants before recording success.

## References

- SQLite, [Atomic Commit](https://www.sqlite.org/atomiccommit.html) — recovery
  behavior around interruption and hot journals.
- PostgreSQL, [Continuous Archiving and Point-in-Time Recovery](https://www.postgresql.org/docs/current/continuous-archiving.html) — base backups, archived logs, and recovery targets.
- NIST, [SP 800-34 Rev. 1: Contingency Planning Guide for Federal Information Systems](https://csrc.nist.gov/pubs/sp/800/34/r1/final) — recovery objectives, alternate processing, testing, and exercises.
- Kubernetes, [Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/) — retry limits, delayed retries, and terminal failed work.
- Erlang/OTP, [Supervisor Behaviour](https://www.erlang.org/doc/system/sup_princ.html) — restart strategies and restart-intensity limits.
- [RFC 9110 §15, Status Codes](https://www.rfc-editor.org/rfc/rfc9110#section-15) — explicit partial, temporary, and unavailable HTTP outcomes for degraded operation.
