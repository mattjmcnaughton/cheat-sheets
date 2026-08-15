---
title: Change Correctness Overview
bug_classes: [mixed-version-failure, incompatible-schema-change, unsafe-migration, flag-path-drift, premature-deprecation]
authority: organizational
mechanizable: property-test
maturity: draft
last_reviewed: 2026-08-15
---

# Change Correctness Overview

## Why review misses it

A diff proves only the new world. Releases create a sequence of mixed worlds:
old code reads new data, new code reads old data, workers finish jobs enqueued
before deployment, and rollback restores code without restoring schema or
rewriting data. Fixtures are freshly created in the latest shape, while feature
flags leave paths compiled but unexercised. The incompatible step often lands
in a later, individually harmless cleanup diff.

## The default

**Evolve every shared contract with expand–migrate–contract: add a form both old
and new code tolerate, deploy code that reads both and writes compatibly,
migrate and verify data, then remove the old form only after measured use is
zero through the rollback window.**

## Rules

1. **List every old/new code and data pairing before release.** Include rolling
   deploys, queued work, replicas, caches, clients, and rollback.
2. **Expand before requiring.** Add optional fields, tolerant readers, and new
   endpoints before any writer depends on them.
3. **Keep new readers compatible with old data and old readers tolerant of new
   data.** Preserve unknown fields where round-tripping would otherwise erase
   them.
4. **Separate schema change, backfill, behavior switch, and cleanup into
   independently reversible releases.** Do not make rollback depend on undoing
   a long data rewrite.
5. **Make migrations resumable, idempotent, rate-limited, and observable.**
   Record progress and verify invariants before advancing.
6. **Test both states of every release flag and give the flag an owner and
   removal date.** Avoid interacting flags; test combinations you permit.
7. **Measure legacy reads, writes, and callers before deprecation.** Remove only
   after a communicated support window and observed zero use.
   *(Organizational authority: support policy and client coordination require a
   mandate.)*
8. **Treat rollback as forward compatibility.** Before rollout, prove the old
   binary can safely read every value the new binary may write.

## Anti-patterns

**“Deploy code and migration together.”** Coordination feels atomic, but
rolling processes and replicas ensure they are not atomic.

**“The new field has a default, so make it required.”** Fresh rows look valid;
old rows, cached payloads, and lagging clients still lack it.

**“Rollback means redeploy the old binary.”** Code rolls back quickly; destructive
schema changes and newly written enum values do not.

**“Keep the flag forever for safety.”** A flag preserves an escape hatch only
while both paths are tested. Later it preserves stale, combinatorial behavior.

**“Nobody uses the old contract.”** Absence in tests or recent team memory is
not usage evidence; instrument the boundary before announcing removal.

## What it costs

You carry duplicate readers or writers, temporary columns, flags, telemetry,
and cleanup releases. Backfills consume controlled capacity and prolong the
period when two representations coexist. Compatibility can delay a desirable
breaking change. Budget the cleanup when approving the expansion or the
temporary state becomes permanent architecture.

## Review questions

- Can the previous binary read every value this version writes?
- Can this version read data and queued work produced by the previous version?
- Which release expands, migrates, switches behavior, and contracts?
- Is the migration resumable and safe to run twice?
- What evidence proves the backfill is complete and correct?
- Are both flag states and permitted combinations exercised before rollout?
- What metric identifies remaining legacy callers, reads, or writes?
- What exactly happens if rollout stops halfway and rolls back?

## How to mechanize

**Type — unavailable across deployed versions.** Types protect one build; they
cannot make an older binary understand a newly emitted value. Keep wire schemas
explicit, but do not mistake compilation for compatibility.

**Lint — partial.** Fail schema checks on removed fields, reused field numbers,
new required fields, destructive migrations without an approved exception, and
flags without owners or expiry dates. Static checks cannot prove semantic
compatibility or live usage.

**Property test — the highest repeatable rung.** Keep serializers and readers
from the oldest supported and new versions in the test suite. Generate values
from each supported schema and assert every permitted writer-reader pairing
succeeds and preserves shared fields. Run migrations twice, resume after every
checkpoint, and assert the same final state. Exercise both flag states against
pre-migration, partial, and migrated fixtures.

**Runtime assertion and observation — gate each phase.** Assert dual-written
representations agree and reconciliation counts are zero before contract.
Measure old-format reads and writes, unknown-value failures, migration progress,
flag-state errors, and clients by contract version. Automate rollout gates, but
require the support owner to authorize irreversible deletion; telemetry cannot
prove an offline client will never return.

## References

- Protocol Buffers, [Updating A Message Type](https://protobuf.dev/programming-guides/proto3/#updating) — compatibility rules, reserved fields, and unknown fields.
- Kubernetes, [API Deprecation Policy](https://kubernetes.io/docs/reference/using-api/deprecation-policy/) — primary support and removal policy for versioned APIs.
- Martin Fowler, [Parallel Change](https://martinfowler.com/bliki/ParallelChange.html) — expand and contract as a staged compatibility technique.
- IETF, [RFC 8594: The Sunset HTTP Header Field](https://www.rfc-editor.org/rfc/rfc8594) — communicating expected resource retirement.
- PostgreSQL, [ALTER TABLE](https://www.postgresql.org/docs/current/sql-altertable.html) — authoritative locking and validation behavior for live schema changes.
