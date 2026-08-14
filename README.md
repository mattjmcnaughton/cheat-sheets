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
and how it changes. Roadmap only.

**[Contracts](cheat-sheets/correctness/contracts/README.md)** — what a caller is
promised. Roadmap only.

**[Change](cheat-sheets/correctness/change/README.md)** — behavior drifting from
expectation over time. Roadmap only.

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
