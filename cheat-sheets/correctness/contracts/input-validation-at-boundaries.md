---
title: Input Validation at Boundaries
bug_classes: [unparsed-input, ambiguous-input, invalid-domain-state, inconsistent-validation, unusable-validation-error]
authority: design
mechanizable: type
maturity: draft
last_reviewed: 2026-08-15
---

# Input Validation at Boundaries

## Why review misses it

Invalid input usually has the same primitive type as valid input. A reviewer sees
`user_id: str` flow into business logic, but cannot see whether it was decoded,
trimmed, defaulted, or checked elsewhere. Happy-path fixtures start after parsing,
so they omit malformed encodings, duplicate fields, unknown members, and values
that are individually legal but impossible together. Validation then accumulates
as scattered conditionals whose gaps appear only when a new caller reaches an old
internal path.

## The default

**At every trust or representation boundary, parse external bytes and primitives
once into domain types that can represent only accepted states; reject ambiguous
syntax, then apply named semantic and cross-field rules before the value enters
the core.**

## Rules

1. **Parse, do not merely validate.** Return an `OrderId`, `EmailAddress`, or
   `NonEmpty[Item]`, not the original string plus a promise that somebody checked
   it; the type carries evidence to every later call.
2. **Validate at each trust or representation boundary.** Decode HTTP, queue,
   file, database, and command-line values as they enter your model, even when an
   upstream producer also validates; contracts and stored data drift independently.
3. **Separate syntax from semantics.** First reject malformed JSON, dates, and
   identifiers; then check domain facts such as `start < end`, supported currency,
   or whether two fields may coexist. This keeps parse errors stable when business
   policy changes.
4. **Reject ambiguity instead of guessing.** Refuse duplicate object keys,
   trailing junk, lossy numeric coercion, unknown enum values, and dates without a
   required format; two plausible interpretations make retries and audits unsafe.
5. **Define unknown-field policy explicitly.** Reject unknown members for commands
   where a misspelling changes intent; preserve or ignore them only where the
   versioning contract says so. *(Design authority: all producers must share this
   evolution rule.)*
6. **Validate relationships after parsing fields.** Bounds, mutually exclusive
   options, and conditional requirements are properties of the whole value, not
   independent widgets.
7. **Return structured, useful errors without echoing secrets.** Include a stable
   code, field path, rejected constraint, and all safely discoverable independent
   failures; keep human wording separate from machine behavior.
8. **Normalize only when the contract declares values equivalent.** Case-folding,
   trimming, and defaulting change data; preserve the submitted representation
   when it matters and never use normalization to make invalid syntax valid.
9. **Recheck mutable facts at the committing operation.** Parsing can prove shape
   and local invariants, but availability, uniqueness, authorization, and current
   state can change between validation and use.

## Anti-patterns

**“Validate, then pass the string.”** A regex is quick and avoids wrapper types.
The next refactor calls the consumer without the regex, or interprets the same
string differently. Parse once and pass the resulting domain value.

**“Be liberal in what you accept.”** Compatibility feels safer when the parser
accepts several spellings and silently drops unknown fields. It also turns typos
into successful requests and makes producers depend on undocumented coercions.

**“The UI already checks it.”** Client feedback should be immediate, but every
boundary has other clients and older versions. Treat client checks as usability,
not evidence received by the core.

**“One generic invalid-input message.”** It avoids exposing internals and is easy
to localize. It forces callers to guess which field failed and encourages retries
of requests that can never succeed; expose constraints, not implementation detail.

**“Sanitize everything at ingress.”** Rewriting input sounds defensive, but this
sheet is about constructing correct values, not context-specific security escaping.
Escape at the output context; do not mutate a name because it might later reach SQL
or HTML.

## What it costs

Boundary types add constructors, mapping code, and error schemas. Strict parsing
can reject clients that relied on coercion, so tightening an existing contract may
need telemetry and a versioned rollout. Cross-field checks make streaming parsers
buffer more input, and collecting multiple errors costs work compared with failing
fast. The payoff is a simpler core whose functions do not repeatedly defend
against malformed primitive values.

## Review questions

- Where does external representation become a domain type in this change?
- Which checks are syntactic, which are semantic, and which depend on mutable state?
- Can duplicate, unknown, or trailing input be interpreted in more than one way?
- Does any validated primitive escape instead of the parsed value?
- What happens when fields are valid separately but invalid together?
- Does the error identify a stable code, field path, and violated constraint?
- Is any normalization changing a value the contract does not declare equivalent?

## How to mechanize

**Type — reachable for local and structural validity.** Give each domain value a
private or validating constructor and expose a parser returning either that type or
a structured error. Model alternatives as tagged unions and cross-field states as
separate variants, so downstream functions cannot receive an unparsed string or an
impossible combination. Generated schema types help only if construction cannot
bypass their invariants.

**Lint — reinforce the boundary.** Forbid raw request dictionaries and primitive
IDs in core modules; require boundary adapters to call the declared parser. Flag
constructors that are public solely to bypass validation.

**Property test — exercise the parser contract.** Generate arbitrary bytes and
assert parsing never crashes; accepted values satisfy every constructor invariant;
and `parse(render(value)) == value`. Generate duplicate keys, extra suffixes, and
near-boundary numbers and assert rejection is deterministic.

**Runtime assertion — for facts types cannot encode.** Enforce database constraints
for uniqueness and relationships, and assert domain constructors are not bypassed
at deserialization boundaries.

**Observation — for contract drift.** Count rejection codes by producer and schema
version; alert on a new code or sustained increase before loosening the parser.
No higher rung can prove mutable external facts or producer compatibility: types
prove only properties retained in the in-process value.

## References

- Alexis King, [Parse, don't validate](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/) (2019) — preserving evidence of validation in the returned type.
- [RFC 8259: The JavaScript Object Notation (JSON) Data Interchange Format](https://www.rfc-editor.org/rfc/rfc8259) — grammar, interoperability limits, and unpredictable behavior for duplicate names.
- [RFC 9457: Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457) — a standard structured error representation.
- [JSON Schema Validation: A Vocabulary for Structural Validation](https://json-schema.org/draft/2020-12/json-schema-validation) — structural and semantic assertion keywords.
- [PostgreSQL: Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html) — primary, unique, check, and foreign-key constraints at the committing boundary.
