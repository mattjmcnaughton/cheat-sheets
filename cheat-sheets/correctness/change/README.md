# Correctness / Change

**Behavior drifting from expectation over time.**

The other sections ask whether values, transitions, and contracts are correct.
Change asks whether those promises survive a new schema, a configuration edit,
a refactor, or retirement of an interface that consumers still use.

The diff shows the new state of the code. Its counterpart can be an old client,
a retained record, a partially completed migration, or a configuration revision
that activates a previously dormant path. Review needs evidence about that
transition as well as the final implementation.

| Sheet | Bug classes | Highest rung |
|---|---|---|
| [Schema and API Evolution](schema-and-api-evolution.md) | Incompatible readers and writers, reused field identities, changed defaults, premature contraction | lint |
| [Migrations and Backfills](migrations-and-backfills.md) | Skipped records, overwritten live updates, lost progress, premature cutover | property test |
| [Config and Feature Flags](config-and-feature-flags.md) | Invalid combinations, mixed revisions, unstable cohorts, unsafe fallback | lint |
| [Refactoring Without Semantic Drift](refactoring-without-semantic-drift.md) | Changed evaluation order, aliasing, edge cases, and error timing | property test |
| [Deprecation](deprecation.md) | Unannounced removal, hidden consumers, renewed dependencies, premature retirement | lint |

**Highest rung** is the strongest concrete check described by the sheet,
following the [mechanization ladder](../../../CONTRIBUTING.md#the-mechanization-ladder).
Static checks cover declared schemas, configuration constraints, and new direct
uses of deprecated interfaces. Generated tests exercise migrations and behavioral
equivalence. Deprecation still needs observed usage and consumer agreements to
justify removal; blocking new references does not prove that old users are gone.

## Where the boundaries run

- **Evolution** defines which contract versions can coexist; **Migrations**
  moves existing records between those representations while writes continue.
- **Configuration** controls which behavior runs; **Refactoring** preserves
  observable behavior while changing its implementation.
- **Deprecation** governs the commitment to retire a surface and the evidence
  for removal; **Evolution** governs compatibility before that removal.

---

[← Correctness](../README.md)
