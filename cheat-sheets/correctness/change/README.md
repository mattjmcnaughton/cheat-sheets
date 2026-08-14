# Correctness / Change

**Behavior drifting from expectation over time.**

Every other sub-section asks whether the code is right now. This one asks
whether it is still right after the schema gained a column, the flag flipped,
the endpoint gained a version, or the function was cleaned up by someone who
believed the change was cosmetic.

The failure shape here is the most distinctive in the area: nothing is wrong at
the moment of the change, and the change is often correct in isolation. What
breaks is the relationship between the new code and data written by the old
code, or clients still speaking the old contract. The bug is introduced by a
diff and detonates in a different one, which is why review — anchored on a
single diff — is structurally poor at catching it.

## Planned sheets

None of these are written yet. Filenames are provisional.

| Sheet | Covers |
|---|---|
| `schema-and-api-evolution.md` | Compatible vs. breaking changes, expand-and-contract, and what old readers do with new fields |
| `migrations-and-backfills.md` | Long-running data changes against live traffic, resumability, and code that must handle both shapes at once |
| `config-and-feature-flags.md` | Flags as untested code paths, combinations nobody exercised, and the cost of never deleting one |
| `refactoring-without-semantic-drift.md` | Behaviour-preserving change, characterization tests, and the edge cases the old code handled by accident |
| `deprecation.md` | Announcing, measuring, and actually removing; how to know a thing is unused rather than assume it |

To start one, copy [`_template/sheet-template.md`](../../../_template/sheet-template.md)
and read [`CONTRIBUTING.md`](../../../CONTRIBUTING.md).

---

[← Correctness](../README.md)
