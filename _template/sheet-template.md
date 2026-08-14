---
title: Sheet Title In Title Case
bug_classes: [kebab-case-slug, one-per-failure-mode]
authority: individual        # individual | design | organizational
mechanizable: lint           # type | lint | property-test | assertion | observation | none
maturity: draft              # draft | reviewed
last_reviewed: YYYY-MM-DD
---

# Sheet Title In Title Case

<!--
Copy this file to cheat-sheets/<area>/<section>/<topic>.md and replace every
section. Delete these comments. Keep the eight H2 headings, in this order, with
these exact names — indexes and reviewers rely on them. Under 1,500 words.

A sheet opens on why the bug survives review, not on a war story. Incidents
belong in References, cited for the mechanism they demonstrate.

Front matter:
  bug_classes  the specific failure modes this sheet prevents, not its subject
  authority    the highest authority any rule needs: individual (an engineer can
               do it in the change they are writing), design (needs agreement on
               an interface or data model), organizational (needs budget, policy,
               or a mandate)
  mechanizable the highest rung of the ladder How to mechanize actually reaches
-->

## Why review misses it

<!-- Why a careful reader of the diff does not catch this. The answer is a
property of the diff — the wrong code looks like the right code, the failure
lives in data or in a clock, the test suite runs under conditions that hide it.
"Reviewers are busy" is not an answer. -->

## The default

<!-- One prescriptive rule in bold, actionable without reading the rest of the
sheet. This is the author's section. If a reader takes only this sentence and
nothing else, they should be materially better off. -->

## Rules

<!-- Numbered. Prescription first, one-line rationale second. Each rule is
actionable by an individual engineer unless flagged as needing design or
organizational authority — and if any is, the front matter must say so. Six to
ten rules; cut rather than pad. -->

## Anti-patterns

<!-- Named, with the plausible reasoning that leads people to each one. Nobody
adopts an anti-pattern for a stupid reason; state the good reason, then what it
costs. Four or five. -->

## What it costs

<!-- The performance, ergonomic, and complexity bill for following the rules.
Where the cost is genuinely near zero, say so in one line rather than
manufacturing a trade-off. -->

## Review questions

<!-- Five to eight, flat bulleted list, phrased for a reviewer to ask out loud.
Each should be liftable into a review template unchanged. Questions about this
change, not about the topic in general. -->

## How to mechanize

<!-- Work down the ladder and stop at the highest rung that applies:
  1. Type          make the bad state unrepresentable
  2. Lint          a rule that fails the build on the pattern
  3. Property test an invariant checked against generated inputs
  4. Assertion     a check that fails loudly in the wrong state
  5. Observation   a metric, alert, or reconciliation job

State plainly which rungs are unavailable and why. Name the check concretely
enough that a reader could write it. "Be careful" is a failed section. -->

## References

<!-- Papers, primary docs, specs, incident write-ups. Markdown links with real,
resolvable URLs. No blogspam, no vendor marketing. Every empirical claim in the
sheet is backed by something in this list. -->
