---
name: creating-cheat-sheets
description: Adds and reviews correctness cheat sheets using this repository's template, style, mechanization ladder, citations, roadmap, and hand-written indexes. Use when creating or expanding a cheat sheet in this repository.
---

# Creating Cheat Sheets

Create one focused, prescriptive correctness reference card and wire it into the
collection.

## Workflow

1. Read `CONTRIBUTING.md`, `_template/sheet-template.md`, the target section's
   `README.md`, and two neighboring sheets.
2. Read `docs/roadmap.md`. Confirm the topic's owning section and boundary with
   adjacent topics. Prefer a focused planned topic; use an overview only when
   explicitly asked for minimum section-wide guidance.
3. Search existing sheets for overlapping rules and links. Explain an idea at
   length in one sheet only; hand neighboring territory back with a relative
   link.
4. Copy the template to
   `cheat-sheets/correctness/<section>/<topic>.md`. Use a lowercase kebab-case
   filename and complete every required front-matter field.
5. Research references before making empirical claims. Prefer specifications,
   standards, language documentation, papers, and first-party incident reports.
   Open every reference and verify that its title, author, year, and cited claim
   match. Remove a claim when no authoritative source supports it.
6. Write **The default** first. It must stand alone and prescribe one action.
   Write the numbered rules and review questions next, then the remaining
   sections. Keep the sheet under 1,500 words and delete all template comments.
7. Work down the mechanization ladder. Set `mechanizable` to the highest rung
   the sheet genuinely reaches, explain what that rung enforces, and state why
   stronger-looking approaches cannot prove the remaining behavior.
8. Add the sheet to the target section's `README.md`. Remove its provisional
   planned row. Update sheet counts and links in `cheat-sheets/correctness/README.md`
   and `README.md`. Mark and link the matching item in `docs/roadmap.md`.
9. Run the validator, inspect the diff, and correct every failure:

   ```sh
   python skills/creating-cheat-sheets/scripts/validate.py \
     cheat-sheets/correctness/<section>/<topic>.md
   git diff --check
   ```

10. Verify remote references separately; the validator checks only local links
    and structure. Report the word count, checks run, and any URL that could not
    be independently verified.

## Editorial Decisions

- Use second person, imperative, present tense. Put the prescription before its
  rationale.
- Give an overview a broad minimum baseline, not compressed versions of every
  future sheet. Link focused sheets and let them supersede the overview.
- Choose `authority` from the strongest rule: mark the rule inline when it needs
  design or organizational authority.
- Treat a timeout, retry, acknowledgement, commit, and cancellation as distinct
  outcomes unless a cited contract proves otherwise.
- Name techniques rather than products. Language and platform documentation may
  appear when it is the primary source for behavior.
- Do not add severity scores, generic exhortations, invented incidents, or a
  mechanization section that ends at “be careful.”

## Validation Scope

Run the validator without arguments to check every completed sheet:

```sh
python skills/creating-cheat-sheets/scripts/validate.py
```

It checks front matter, heading order, title agreement, word count, rule and
review-question counts, leftover template comments, local links, and inclusion
in the section index. It does not judge prose, verify remote citations, or prove
that the selected mechanization rung is honest; review those manually.
