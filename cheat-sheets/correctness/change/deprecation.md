---
title: Deprecation
bug_classes: [unannounced-contract-removal, hidden-consumer-breakage, renewed-deprecated-dependency, premature-retirement]
authority: organizational
mechanizable: lint
maturity: draft
last_reviewed: 2026-09-09
---

# Deprecation

## Why review misses it

Removing an unused symbol looks correct in the repository that defines it.
Consumers can live in another repository, an old executable, a scheduled job,
or a stored payload. A quiet usage chart also looks reassuring when the missing
traffic actually comes from a cache, an instrumentation gap, or an infrequent
workflow that has not run during the observation window.

## The default

**Deprecate before removing: publish the replacement and retirement conditions,
block new dependencies, migrate known consumers, and remove only after checking
usage evidence against the promised support window.**

## Rules

1. **Name the exact retiring surface and its replacement.** A package, endpoint,
   field, behavior, and version have different consumers; a broad announcement
   does not tell a caller what to change.
2. **Set an owner, support window, and removal criteria — organizational
   authority.** Retirement changes a promise to consumers and needs a decision
   about how long that promise remains in force.
3. **Publish migration instructions before starting the retirement clock.**
   Consumers need an available replacement and a way to verify equivalent
   behavior, not merely notice that the old surface is discouraged.
4. **Keep deprecation distinct from shutdown.** A deprecation marker does not
   itself change behavior; announce removal timing and consequences separately.
5. **Block new dependencies while tracking existing ones.** A shrinking backlog
   cannot converge if examples, templates, or generated clients keep creating
   new users of the old surface.
6. **Inventory consumers and instrument the relevant boundary.** Include batch,
   offline, delayed, and rollback paths; record enough identity to assign
   migration work without collecting unrelated request data.
7. **Choose an observation window from actual consumer cycles.** Zero events
   over a week says little about a quarterly job or an offline client.
8. **Treat missing evidence as uncertainty, not proof of non-use.** Verify the
   measurement path and ask owners of known consumers to confirm migration;
   acknowledge unmanaged consumers when accepting the remaining uncertainty.
9. **Stage removal with a defined recovery path — design authority.** A
   controlled disablement can expose residual users, but irreversible deletion
   of data or identifiers requires a separate decision.

For the compatibility window, use [Schema and API Evolution](schema-and-api-evolution.md).
For data conversion and cleanup, use [Migrations and Backfills](migrations-and-backfills.md).

## Anti-patterns

**"There are no references in this repository."** Search is a useful local
check, but cannot see independent clients, reflection, or stored requests.
Combine source inventory with boundary instrumentation and the agreed support
policy before removing a shared contract.

**"The dashboard shows zero."** Metrics make use visible, but only for traffic
that reaches the measured path and survives sampling. Test the instrumentation,
check its coverage and retention, and include known dormant consumers before
interpreting the quiet period.

**"Mark it deprecated and remove it next release."** One release is easy to
schedule, but consumer upgrades need not follow the producer's release cadence.
Publish and honor a support window tied to the consumer agreement; track the
remaining migration work explicitly.

**"Redirect every call to the replacement."** Forwarding seems compatible, but
the replacement may have different errors, side effects, authorization, or
response meaning. Use an adapter only where it preserves the old contract;
otherwise require an explicit consumer migration.

**"Leave the compatibility layer forever."** An adapter prevents immediate
breakage, but indefinite retention keeps the old contract alive and can invite
new dependencies. Retain it for a stated support obligation, with an owner and
review date, or finish the migration and remove it.

## What it costs

A retirement window requires parallel support, consumer coordination, and usage
instrumentation. Some consumers cannot be enumerated or forced to upgrade.
Choose an explicit support policy for that case rather than extending the window
silently. A reversible disablement may reveal real breakage, so define who can
restore service and which effects restoration cannot undo.

## Review questions

- What exact surface is deprecated, and is its replacement usable now?
- Which published support promise governs the removal date?
- What prevents this change from creating new dependencies on the old surface?
- Which consumers are invisible to repository search or request metrics?
- Does the observation window cover scheduled and offline use?
- Have we tested that real use reaches the measurement?
- What can be restored if a remaining consumer appears after disablement?

## How to mechanize

**Lint — reject new references to a declared deprecated surface.** Record
existing direct call sites as a baseline, resolve references by symbol where
possible, and fail the build when a change introduces another use. Include
examples and generated-client inputs in the scan. Require the baseline to shrink
as consumers migrate; time-limit exceptions rather than suppressing the rule
for an entire package.

Types cannot make dependence on an existing callable surface unrepresentable
while still supporting its callers. A static check can stop new direct uses in
controlled code, but cannot establish that independent or dynamic consumers no
longer exist. That removal condition remains at the observation rung.

For removal, count uses by supported consumer identity and version at the actual
boundary; retain evidence for the agreed observation window. Exercise a known
use to verify instrumentation, reconcile it with the consumer inventory, and
record owner confirmations and coverage gaps. Gate retirement on the declared
support policy and these checks. No finite quiet interval proves that an unknown
consumer will never call again.

## References

- Sanjay Dalal and Erik Wilde, *The Deprecation HTTP Response Header Field*,
  RFC 9745, March 2025 — deprecation signals lifecycle information without
  changing resource behavior.
- Erik Wilde, *The Sunset HTTP Header Field*, RFC 8594, May 2019 — communicating
  expected retirement timing and its distinction from deprecation.
