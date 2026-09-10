---
title: Migrations and Backfills
bug_classes: [skipped-backfill-record, overwritten-live-update, nonresumable-migration, premature-cutover]
authority: design
mechanizable: property-test
maturity: draft
last_reviewed: 2026-09-09
---

# Migrations and Backfills

## Why review misses it

The transformation looks correct on one row. Its failure lives between rows or
between attempts: a cursor advances before a write commits, live traffic changes
a row already read, or a deployment assumes that a background job has finished.
A small fixture hides the time during which old and new forms must coexist.

## The default

**Run a live backfill as bounded, restartable batches that preserve concurrent
writes, and verify the target invariant before switching readers or removing
the source representation.**

## Rules

1. **Define the target invariant and eligible population before writing the
   job — design authority.** A processed-row count does not say which records
   must exist or what their new values must mean.
2. **Expand the schema and make live writes maintain the migration invariant
   before scanning — design authority.** Rows inserted or updated behind the
   scan cursor otherwise escape the backfill.
3. **Traverse a stable unique key and persist explicit progress.** Offset
   pagination over changing rows can skip or repeat records independently of
   whether the transformation itself is correct.
4. **Commit each batch's effects with its checkpoint, or make replay safe.** A
   checkpoint ahead of durable effects loses work; one behind them repeats work.
5. **Protect transformations from concurrent source changes.** Use an atomic
   update, row lock, or source-version comparison; recompute after a conflict
   instead of overwriting newer data with a stale derivation.
6. **Make retried effects safe and retained progress sufficient to resume.**
   Idempotence prevents duplicate effects; resumability also requires knowing
   what remains after a crash.
7. **Bound batch size, lock wait, and resource use; make pausing preserve
   progress.** A correct transformation can still exhaust the capacity needed
   by live requests.
8. **Reconcile the invariant under a defined cutover boundary before switching
   readers — design authority.** An empty queue cannot rule out skipped records
   or writes that reintroduce the old form.
9. **Write a recovery plan for each phase.** Reverting application code cannot
   reconstruct discarded information or undo unrelated writes after a backfill.

For compatible representations, use [Schema and API Evolution](schema-and-api-evolution.md).
For atomic publication, use [Invariants Across Intermediate Steps](../state/invariants-across-intermediate-steps.md).

## Anti-patterns

**"It is just one update statement."** A single statement simplifies atomicity,
but an unbounded update may hold locks or generate more write traffic than the
service can absorb. Rehearse its actual cost; use bounded batches when the full
operation cannot fit the live workload's budget.

**"Retry the script from the top."** Restarting is easy, but adding the same
adjustment again corrupts data. Assign a deterministic target value from a
versioned source, or record that an adjustment was applied atomically with the
adjustment; persist progress to avoid rescanning everything after every failure.

**"Checkpoint first so we cannot repeat a batch."** This avoids duplicate work
only by risking missing work after a crash. Commit checkpoint and writes in one
transaction where possible; otherwise checkpoint after effects and make their
replay safe.

**"Read, transform, save."** Application code is convenient for complex
transformations, but the source can change between read and save. Compare the
source version in the conditional write, and reload and recompute when the
comparison fails.

**"The job says complete, so drop the old column."** Job completion describes
attempts, not correctness or consumer migration. Reconcile missing and
mismatched targets, establish that live writers maintain them, and satisfy the
compatibility window before removing the source.

## What it costs

Restartability adds progress records, replay semantics, and failure-path tests.
Smaller batches reduce individual lock duration but add transaction overhead.
Concurrent-write protection can cause conflicts and retries. Reconciliation adds
read load; schedule it explicitly, and define whether its snapshot or write
barrier establishes a cutover that remains true after the check finishes.

## Review questions

- Which records are eligible, and what invariant defines completion?
- Can inserts or updates behind the cursor escape this migration?
- What happens if the process dies immediately before or after batch commit?
- Can a stale transformation overwrite a concurrent live update?
- How do we pause and resume without losing or duplicating effects?
- Which check proves readiness to switch readers?
- After which phase does recovery require a forward repair?

## How to mechanize

**Property test — generate batches, live writes, crashes, and restarts against a
small reference model.** Track source versions, target values, and progress.
Inject failure before and after each durable boundary, and repeat completed
batches. Once live changes stop and retries succeed, require every eligible
record to satisfy the target invariant, with no duplicated effects or overwritten
newer values. Generate insertions on both sides of the cursor and updates to
already processed rows.

Ordinary types do not encode crash points, and static checks cannot establish
that arbitrary transformations preserve meaning under live writes. This makes
generated execution histories the highest applicable rung here. Bound the model
explicitly: it explores sampled schedules, not every database execution.

Run representative histories against the real transaction and isolation behavior
too. Separately rehearse workload cost on representative data volume and define
pause thresholds. These checks address operational feasibility; they do not
replace the invariant that determines completion.

## References

- GitLab, *Development Documentation*, "Batched background migrations" and
  "Batching best practices", accessed September 2026 — bounded background work,
  retryable jobs, migration completion, and pacing.
- Pramod Sadalage and Martin Fowler, "Evolutionary Database Design", May 2016 —
  versioned migration steps and coexistence of data and schema changes.
