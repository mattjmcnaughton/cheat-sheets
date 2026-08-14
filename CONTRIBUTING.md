# Contributing

This repository is prose. There is no build, no site generator, no linter, and
no CI. A contribution is a Markdown file that reads well on GitHub.

## What a sheet is

A sheet is a reference card for someone mid-task: an author reaching for a
default before writing the code, and a reviewer looking for what to ask about
it. It is not a tutorial, not a survey, and not a textbook chapter.

One sheet per topic. If your sheet needs two "The default" rules, it is two
sheets.

## Adding a sheet

1. Copy [`_template/sheet-template.md`](_template/sheet-template.md) to
   `cheat-sheets/<area>/<section>/<topic>.md`.
2. Fill in every section. Delete the guidance comments.
3. Add a row to the section `README.md` table.
4. Link it from any existing sheet whose topic brushes against it.

File and directory names are lowercase kebab-case: `time-and-time-zones.md`. No
`_cheat_sheet` suffix — the path already says it. `README.md`,
`CONTRIBUTING.md`, and `LICENSE` keep their conventional names.

## Structure

Front matter fields, all required:

| Field | Values |
|---|---|
| `title` | Title Case, matches the `#` heading |
| `bug_classes` | kebab-case slugs, one per failure mode the sheet prevents |
| `authority` | `individual`, `design`, or `organizational` |
| `mechanizable` | `type`, `lint`, `property-test`, `assertion`, `observation`, or `none` |
| `maturity` | `draft` or `reviewed` |
| `last_reviewed` | `YYYY-MM-DD` |

Then exactly these H2 sections, in this order, with these names: **Why review
misses it**, **The default**, **Rules**, **Anti-patterns**, **What it costs**,
**Review questions**, **How to mechanize**, **References**.

A sheet opens on why the bug survives review, not on a war story. Real incidents
still matter — they are what makes the guidance more than opinion — but they
belong in **References**, cited for the mechanism they demonstrate, and in a
clause inside a rule where one is genuinely load-bearing. A reader reaching for
a default is mid-task and does not need the history first.

Do not add sections, rename them, or reorder them. Sub-headings inside a section
are fine if a sheet genuinely needs them; most do not.

`authority` records the highest authority any single rule needs. If one rule
requires agreement on a shared data model, the sheet is `design`, and that rule
says so inline. `mechanizable` records the highest rung of the ladder that **How to mechanize**
actually reaches — not the highest rung that exists.

## The mechanization ladder

**How to mechanize** works down this ladder and stops at the highest rung that
applies:

1. **Type** — make the bad state unrepresentable.
2. **Lint or static check** — a rule that fails the build on the pattern.
3. **Property test** — an invariant checked against generated inputs.
4. **Runtime assertion** — a check that fails loudly in the wrong state.
5. **Observation** — a metric, alert, or reconciliation job, for what only
   shows up in production.

Say which rungs are unavailable and why. A **How to mechanize** that ends at "be
careful" will be sent back: everyone was already being careful, and the sheet
has added nothing.

## Style

- **Under 1,500 words.** Cut rather than pad.
- **Second person, imperative, present tense.** "Store instants in UTC," not
  "instants should generally be stored in UTC."
- **No hedging where the guidance is settled.** Hedge only where the trade-off
  is real, and then say what it depends on.
- **Prescription first, rationale second.** One line of reasoning per rule.
- **Name techniques, never products.** No tool comparisons, no vendor links, no
  "we use X at Y." A sheet that promotes a product will be rejected outright.
- **No severity scores, risk ratings, or CVSS analogue.** There is no
  principled scale here and a fake one will rot.
- **Empirical claims get a citation.** If you cannot find a real source, drop
  the claim or say in the sheet that you could not find one. Never invent an
  incident, paper, or spec.
- **Stay in your lane.** When a sheet brushes a neighbour's topic, give it one
  sentence and a relative link. Do not cover it. Each idea is explained at
  length in exactly one sheet.

## Code blocks

Python is the lingua franca. Write examples in Python unless the bug class only
exists in another language.

- Default to a fenced ` ```python ` block. Keep it under about ten lines and
  make it read as the smallest thing that shows the point.
- Add a `java`, `go`, or `typescript` block **only** when the failure is
  specific to that language's semantics — the `equals`/`hashCode` contract, a
  zero value that is indistinguishable from absence, `undefined` versus `null`.
  Introduce it with a sentence saying why that language is shown.
- Three code blocks per sheet is a lot. Prose prescribes; code illustrates.
- Language-neutral pseudocode is allowed where no real language is honest about
  the idea. Fence it as ` ```text `, use `name: Type` for declarations and `//`
  for comments, and keep it obviously not-a-language.
- Show wrong code only under **Anti-patterns**, and always with the corrected
  form nearby.

## Review bar

Before merging a sheet, a reviewer checks:

- The eight headings are present, correctly named, and in order.
- **The default** stands alone. Read it cold, with the rest of the sheet
  covered: is it actionable?
- Every rule is actionable by one engineer, or flagged as needing design or
  organizational authority — and the front matter agrees.
- **How to mechanize** names a concrete check at a real rung, and says what is
  out of reach.
- Every reference resolves and is a primary source, spec, paper, or incident
  write-up.
- Nothing in the sheet is explained at length in another sheet.
- Word count is under 1,500.

Changes to the template, the section list, or the set of sheets in a section are
structural. Open an issue first.

## Licensing

Prose in this repository is [CC BY-SA 4.0](LICENSE). By contributing you agree
to license your contribution under those terms.
