# Repository instructions

## Purpose and scope

- This is a Markdown-only collection of short, prescriptive cheat sheets about
  software correctness. It has no build, site generator, linter, or CI.
- Keep changes focused. Do not add tooling, generated indexes, or new document
  structure unless the task explicitly requires it.
- Read `CONTRIBUTING.md` and `_template/sheet-template.md` before adding or
  substantially changing a sheet.

## Sheet structure

- Use lowercase kebab-case paths under `cheat-sheets/<area>/<section>/`.
- Include every required front matter field and use only the values documented
  in `CONTRIBUTING.md`.
- Keep the eight required H2 sections in their documented order and under their
  exact names. Keep each sheet under 1,500 words.
- When adding, removing, or renaming a sheet, update the relevant section index
  and the root index. Use relative links for repository content.

## Writing

- Write for an engineer who is mid-task: second person, imperative, present
  tense, prescription first, and one line of rationale per rule.
- Make **The default** useful on its own. Put incidents and historical context
  in **References**, not in the opening.
- Name techniques rather than products. Do not add severity rankings, vendor
  promotion, or unsupported empirical claims.
- Make **How to mechanize** name a concrete check at the highest applicable rung
  and explain why higher rungs do not apply. “Be careful” is not mechanization.
- Prefer short Python examples. Use another language only when its semantics are
  the point, and keep wrong examples in **Anti-patterns** beside a correction.

## Research and external sources

- External URLs may be used during research, but do not commit them anywhere in
  this repository, including prose, comments, metadata, or agent notes.
- Cite external sources without links. Include enough identifying information
  to find the source: author or organization, title, standard, paper, report,
  issue or DOI identifier, and date where available.
- Relative links between files in this repository are allowed.

## Before finishing

- Preserve unrelated work already present in the working tree.
- Review the diff for scope, prose quality, required headings, front matter,
  index updates, and valid relative links.
- Search the entire working tree for external URL-like text and remove any
  matches. Run `git diff --check`.
