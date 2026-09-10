# Cheat Sheets

Short, prescriptive reference cards on **software behaving as expected**.

One topic per sheet. Each gives you a default you can apply without reading the
rest of it, the rules behind that default, and the questions to ask when you are
reviewing someone else's version of the same problem. They are written for
someone mid-task, not someone studying — closer to a card taped above a desk
than to a chapter.

## Who this is for

Two readers, on the same page:

- **The author**, reaching for a default before writing the code. Read **The
  default**, then **Rules**. That is usually enough.
- **The reviewer**, looking for what to ask. Read **Review questions**. They are
  phrased to be said out loud and to be lifted into a review template unchanged.

Everything else — why the bug survives review, what the guidance costs, how to
make a machine catch it — is there when you need to argue the case.

## Sheets

### [Correctness](cheat-sheets/correctness/README.md)

Divided by where expectation and behavior come apart.

**[Data](cheat-sheets/correctness/data/README.md)** — the values themselves.

- [Time and Time Zones](cheat-sheets/correctness/data/time-and-time-zones.md)
- [Numbers and Money](cheat-sheets/correctness/data/numbers-and-money.md)
- [Absence and Emptiness](cheat-sheets/correctness/data/absence-and-emptiness.md)
- [Boundaries and Ranges](cheat-sheets/correctness/data/boundaries-and-ranges.md)
- [Equality and Ordering](cheat-sheets/correctness/data/equality-and-ordering.md)
- [Text and Encoding](cheat-sheets/correctness/data/text-and-encoding.md)

**[State](cheat-sheets/correctness/state/README.md)** — what the program holds
and how it changes.

- [Mutation and Aliasing](cheat-sheets/correctness/state/mutation-and-aliasing.md)
- [Resource Lifecycle](cheat-sheets/correctness/state/resource-lifecycle.md)
- [Concurrency and Shared State](cheat-sheets/correctness/state/concurrency-and-shared-state.md)
- [Caching and Staleness](cheat-sheets/correctness/state/caching-and-staleness.md)
- [Invariants Across Intermediate Steps](cheat-sheets/correctness/state/invariants-across-intermediate-steps.md)
- [Leases and Fencing](cheat-sheets/correctness/state/leases-and-fencing.md)
- [Ordering and Causality](cheat-sheets/correctness/state/ordering-and-causality.md)
- [Replication and Read Consistency](cheat-sheets/correctness/state/replication-and-read-consistency.md)

**[Contracts](cheat-sheets/correctness/contracts/README.md)** — what a caller is
promised.

- [Input Validation at Boundaries](cheat-sheets/correctness/contracts/input-validation-at-boundaries.md)
- [Error and Failure Semantics](cheat-sheets/correctness/contracts/error-and-failure-semantics.md)
- [Nullability and Partiality in Signatures](cheat-sheets/correctness/contracts/nullability-and-partiality-in-signatures.md)
- [Retries and Idempotency](cheat-sheets/correctness/contracts/retries-and-idempotency.md)
- [Timeouts and Cancellation](cheat-sheets/correctness/contracts/timeouts-and-cancellation.md)
- [Partial Writes Across Services](cheat-sheets/correctness/contracts/partial-writes-across-services.md)

**[Change](cheat-sheets/correctness/change/README.md)** — behavior drifting from
expectation over time.

- [Schema and API Evolution](cheat-sheets/correctness/change/schema-and-api-evolution.md)
- [Migrations and Backfills](cheat-sheets/correctness/change/migrations-and-backfills.md)
- [Config and Feature Flags](cheat-sheets/correctness/change/config-and-feature-flags.md)
- [Refactoring Without Semantic Drift](cheat-sheets/correctness/change/refactoring-without-semantic-drift.md)
- [Deprecation](cheat-sheets/correctness/change/deprecation.md)

**[Execution](cheat-sheets/correctness/execution/README.md)** — reaching a usable
result within the operation's work, memory, and numerical limits.

- [Termination and Progress](cheat-sheets/correctness/execution/termination-and-progress.md)
- [Algorithmic Complexity and Input Size](cheat-sheets/correctness/execution/algorithmic-complexity-and-input-size.md)
- [Bounded Work and Backpressure](cheat-sheets/correctness/execution/bounded-work-and-backpressure.md)
- [Streaming and Incremental Processing](cheat-sheets/correctness/execution/streaming-and-incremental-processing.md)
- [Numerical Stability](cheat-sheets/correctness/execution/numerical-stability.md)

## How a sheet is built

Eight sections, the same eight every time, in the same order:

| Section | What it gives you |
|---|---|
| Why review misses it | Why a careful reader of the diff does not catch this |
| The default | One prescriptive rule, standing alone |
| Rules | Numbered, prescription first, one line of reasoning each |
| Anti-patterns | Named, with the plausible reasoning that leads to each |
| What it costs | The performance, ergonomic, and complexity bill |
| Review questions | Five to eight, ready to ask out loud |
| How to mechanize | How to stop relying on anyone remembering this |
| References | Primary sources, specs, papers, incident write-ups |

**How to mechanize** is the section that matters most, and the one a sheet is
most likely to fail. It works down a ladder — make the bad state
unrepresentable, fail the build, check the invariant against generated inputs,
assert at runtime, watch it in production — and stops at the highest rung that
genuinely applies, naming the rungs it cannot reach and why. A sheet that ends
at "be careful" has added nothing: everyone was already being careful.

## What this is not

No severity scores, no risk ratings, no Top 10. There is no principled way to
rank these against each other, and a fake ranking would rot. No tools are named
and no products are recommended; techniques are named instead. Testing and
observability get no sheets of their own — they are cross-cutting, and they live
in **How to mechanize**.

There is also no tooling in this repository: no site generator, no CI, no link
checker, no generated indexes. It is Markdown that reads on GitHub, and every
index is written by hand.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md), then copy
[`_template/sheet-template.md`](_template/sheet-template.md). The structure is
modelled on the conventions of the OWASP Cheat Sheet Series; no OWASP text,
branding, or licensing is reproduced here, and this project is not affiliated
with the OWASP Foundation.

Prose is [CC BY-SA 4.0](LICENSE); code samples are CC0.
