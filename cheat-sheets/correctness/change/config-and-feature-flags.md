---
title: Config and Feature Flags
bug_classes: [invalid-config-combination, mixed-config-revision, unstable-feature-cohort, unsafe-flag-fallback]
authority: design
mechanizable: lint
maturity: draft
last_reviewed: 2026-09-09
---

# Config and Feature Flags

## Why review misses it

The code diff shows both branches but not which combinations production selects.
A configuration edit can change behavior without touching application code.
Repeated flag reads can even select different branches inside one operation,
while tests keep the flag constant and exercise only the default configuration.

## The default

**Treat configuration as a versioned input: validate each supported combination,
activate one coherent revision per operation, and test the intended rollout and
fallback before changing live behavior.**

## Rules

1. **Declare accepted keys, types, ranges, and cross-field constraints in one
   schema.** Parsing a value does not establish that the combination is usable.
2. **Version the effective configuration and its evaluation rules.** A revision
   must identify defaults, overrides, and targeting logic, not just one edited
   file, if it is to explain the behavior that ran.
3. **Load and validate a complete candidate before activating it.** Publish the
   revision as one coherent snapshot so readers cannot mix dependent settings.
4. **Capture relevant decisions once at the operation boundary.** Re-evaluating
   a dynamic flag midway through a write can mix incompatible protocols.
5. **Define permitted combinations and dependencies — design authority.**
   Independent booleans can expose states that neither implementation supports;
   use an explicit mode when choices are mutually exclusive.
6. **Assign stable cohorts using an agreed identity and deterministic rule —
   design authority.** Per-request randomness can move the same workflow between
   treatments; document when changing the rule intentionally changes membership.
7. **Choose and test failure behavior for unavailable configuration.** Retaining
   a valid previous revision, disabling a feature, or rejecting work have
   different consequences; a generic false value is not universally safe.
8. **Give each temporary flag an owner and removal condition.** A flag left
   behind retains another branch that later edits must still preserve.
9. **Verify rollback against effects already produced by the new mode.** Turning
   a flag off changes future decisions; it does not reverse data writes or
   restore an old reader's compatibility.

For snapshot ownership, use [Mutation and Aliasing](../state/mutation-and-aliasing.md).
For changed data formats, use [Schema and API Evolution](schema-and-api-evolution.md).

## Anti-patterns

**"A string is close enough to a boolean."** Environment settings arrive as text,
so coercion is tempting. In Python a nonempty string is truthy, even when it says
false. Parse only the vocabulary your configuration contract accepts:

```python
# Wrong: bool("false") is True.
new_mode = bool(raw)

# Right: reject values outside the declared vocabulary.
if raw not in {"true", "false"}:
    raise ValueError("expected true or false")
new_mode = raw == "true"
```

**"Read the flag wherever it is needed."** Local reads avoid passing arguments,
but a refresh can split one operation across two modes. Capture an immutable
decision snapshot at entry and pass the relevant decision through the operation.

**"Test everything off and everything on."** These configurations are simple,
but neither exercises a dependency enabled without its prerequisite. Reject
unsupported combinations and test the permitted combinations that alter the same
workflow; sample broader combinations only with an explicit coverage limit.

**"The kill switch always makes rollback safe."** A switch is fast to operate,
but the new branch may already have emitted data the old branch cannot read.
Prove that the fallback handles those effects, or use a forward recovery mode.

**"Keep the old flag name for the next experiment."** Reusing a name avoids
registration work but can activate old overrides or stale clients unexpectedly.
Use a new identity, remove old evaluations, and retire its stored configuration.

## What it costs

Snapshots require deciding how long an operation may retain an old revision.
Long operations may need explicit safe transition points for urgent operational
changes. Version history, validation, and rollout fixtures add maintenance work.
Combination testing grows with interacting decisions; remove obsolete flags and
restrict supported states to keep the space tractable.

## Review questions

- Which configuration revision and targeting rule explain this operation?
- Can dependent settings come from different revisions?
- What rejects an unsupported combination before activation?
- Does one workflow keep a stable decision throughout its effects?
- What happens when configuration is missing, malformed, or unavailable?
- Can the fallback handle data already produced by the new branch?
- Who removes this flag, and what triggers removal?

## How to mechanize

**Lint — validate every checked-in configuration and planned rollout variant
against its schema and cross-field constraints.** Fail the gate on unknown keys,
invalid values, missing prerequisites, and expired temporary flags without a
recorded extension. Check the resolved configuration after applying defaults
and overrides, not each fragment separately. Run the same validation before
publishing a dynamic candidate.

Types can constrain an in-process representation but cannot establish that an
external configuration revision is valid for the deployed binary and its rollout
rules. Static validation is the highest rung for the declared configuration
surface; it does not prove the behavior of every runtime cohort.

Supplement it with tests of both sides of each changed decision and its
interacting flags. Refresh configuration during a generated operation and check
that the operation retains one revision. Simulate evaluation failure and verify
the declared fallback. Record effective revision and non-sensitive decision
identifiers so production failures can be reproduced without logging secrets.

## References

- Pete Hodgson, "Feature Toggles (aka Feature Flags)", October 2017 — toggle
  decisions, cohorts, testing configurations, and temporary-flag lifetimes.
- Google, *The Site Reliability Workbook*, chapter 14, "Configuration Design
  and Best Practices", 2018 — semantic validation and configuration interfaces.
- Python Software Foundation, *Python 3 Library Reference*, "Built-in Types",
  "Truth Value Testing" — nonempty strings are true regardless of their text.
