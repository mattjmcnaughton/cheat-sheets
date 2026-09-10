---
title: Schema and API Evolution
bug_classes: [incompatible-reader-writer, reused-field-identity, changed-default-semantics, premature-schema-contraction]
authority: design
mechanizable: lint
maturity: draft
last_reviewed: 2026-09-09
---

# Schema and API Evolution

## Why review misses it

The diff shows the new producer and consumer agreeing. It does not show an old
client, a delayed message, a stored record, or a rollback reading the new shape.
An unchanged field type can also hide a changed unit, default, or interpretation.
Successful parsing makes that behavioral mismatch look like compatibility.

## The default

**Expand the contract before using its new form, verify every supported old/new
reader-writer pairing, and remove the old form only after its consumers and
rollback obligations have expired.**

## Rules

1. **Define the supported reader-writer matrix, including rollback and retained
   data — design authority.** Deployment order alone does not bound the lifetime
   of messages, records, or independently upgraded clients.
2. **Check compatibility separately for each representation you expose.** A
   change safe for a binary encoding can break a textual encoding or generated
   source interface.
3. **Preserve existing meanings, units, defaults, and error promises.** Parsing
   the same shape does not preserve what callers infer from it.
4. **Specify how old readers handle unknown fields and enum values before
   adding them.** An additive change still breaks a reader that rejects the new
   value or routes it into an unsafe default branch.
5. **Treat a required input as a contract change, even when new clients always
   send it.** Old callers still omit it; provide an agreed interpretation for
   omission or introduce a separately supported contract.
6. **Reserve removed field identities in formats that permit it.** Reusing an
   identifier can make old data parse successfully with a different meaning.
7. **Deploy readers that tolerate both forms before enabling new writes.**
   Account for old readers that remain; they must still receive a form they
   understand until their support window closes.
8. **Gate removal on evidence of completed consumer migration — design
   authority.** A new schema's presence proves neither that old writers stopped
   nor that stored data can survive a rollback.

For moving existing records, use [Migrations and Backfills](migrations-and-backfills.md).
For the removal decision, use [Deprecation](deprecation.md).

## Anti-patterns

**"Adding a field cannot break anyone."** Additions avoid editing existing
fields, but strict readers may reject unknown keys and old code may mishandle
new enum cases. Exercise the actual supported parsers, including their unknown
value behavior, before enabling the addition.

**"The number has the same type."** Keeping an integer field avoids schema
churn, but changing cents to whole currency units silently changes its meaning.
Introduce a distinct field with explicit semantics and migrate consumers before
retiring the old one.

**"Rename and deploy everything together."** One release looks atomic in source
control, but rolling deployments leave old and new binaries active together.
Add the replacement, keep both contracts usable during migration, and remove the
old name in a later change.

**"The new decoder reads our fixtures."** Testing only new-reader/old-writer
compatibility supports an upgrade but says nothing about old readers seeing new
writes. Run both directions wherever the support matrix promises them.

**"Rollback means restoring the binary."** An old executable may no longer
understand records written after the upgrade. Rehearse its reads against those
records, or declare the point after which recovery requires a forward fix.

## What it costs

Parallel contracts require temporary adapters, additional fixtures, and an
explicit support window. Keeping old semantics may postpone a simplification.
Supporting every historical version forever is a separate commitment; bound the
matrix by the actual retention and support policies, and budget for migration
when you shorten that window.

## Review questions

- Which old readers can receive data written by this change?
- Which stored formats and generated interfaces are affected?
- Does a field's meaning or omission behavior change without a type change?
- What does each supported reader do with new fields or enum values?
- Can the rollback version read records created by the new version?
- What evidence permits deleting the old representation?

## How to mechanize

**Lint — compare the proposed schema with every supported baseline.** Fail the
build on removed required fields, reused identifiers, newly required inputs, or
incompatible type changes according to the actual encoding's rules. Keep the
supported baselines versioned; comparing only with the previous commit can miss
a client several releases behind. Require an explicit contract-version change
and migration decision for an intentional incompatibility.

Types in one build cannot constrain binaries already deployed or data already
stored, so the type rung is unavailable for the version transition. Schema
comparison catches structural incompatibility, not arbitrary behavioral drift.

Supplement the static gate with a compatibility matrix that runs real old and
new encoders and decoders. Generate boundary values, omitted fields, and unknown
values where permitted; check both parsing and agreed interpretation. Include
round trips through intermediaries when preservation of unknown fields matters.
Keep behavioral examples for units, defaults, and error responses: a schema
checker cannot infer their meaning from a field name.

## References

- Google, *Protocol Buffers Documentation*, "Language Guide (proto 3)",
  "Updating A Message Type" and "Unknown Fields", accessed September 2026 —
  binary compatibility, reserved identifiers, and representation-specific limits.
- Danilo Sato, "Parallel Change", May 2014 — expand, migrate, and contract
  as separate stages of an interface change.
- Pramod Sadalage and Martin Fowler, "Evolutionary Database Design", May 2016,
  "Multiple versions" — coexistence of application and database versions.
