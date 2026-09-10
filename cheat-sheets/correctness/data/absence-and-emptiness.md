---
title: Absence and Emptiness
bug_classes: [null-vs-empty-conflation, missing-vs-default-conflation, zero-value-as-unset, patch-erases-field, absent-read-as-success]
authority: design
mechanizable: type
maturity: draft
last_reviewed: 2026-09-08
---

# Absence and Emptiness

## Why review misses it

In Python, `None`, `""`, `[]`, `0`, and `False` are all falsy, so a presence
check can silently replace a deliberate empty value with a default. The
distinction may already be lost before the diff: a deserializer that fills
omitted fields leaves the handler no way to recover which keys were sent.
Fixtures that populate every field never exercise this path.

## The default

**Preserve every distinction your contract needs between missing, null, empty,
and defaulted: represent presence explicitly, avoid truthiness for presence
checks, and retain provenance when an inherited default must differ from an
explicit choice.**

## Rules

1. **Never test presence with truthiness.** `if not x` is true for `0`, `""`,
   `[]`, and `False`, all of which a caller can legitimately mean. Ask
   `x is None` and `len(x) == 0` separately.
2. **Never let a scalar's zero value stand for "unset".** Use explicit presence —
   an optional wrapper, a pointer, a protobuf `optional` field — so "0" and "not
   sent" are different bytes on the wire.
3. **Preserve "key absent" through deserialization with a sentinel distinct from
   null.** `Optional[T]` distinguishes null from a value, but adds no missing state.
   *(Design authority: this changes a shared wire contract — agree it with the
   other side.)*
4. **Choose whether defaults follow current policy or are fixed at creation.**
   Apply inherited defaults on read; persist creation-time choices when history
   must remain stable, with provenance if later behavior needs the distinction.
5. **State your PATCH semantics and pick a format that can express them.** JSON
   Merge Patch spends `null` on "remove", so it cannot set a member to null
   (RFC 7396); use JSON Patch (RFC 6902) when storing null and removing a member must differ. Merge Patch already
   distinguishes removal from omission.
6. **In SQL, test nullness with `IS NULL`, not equality.** Ordinary comparisons
   with `NULL` yield unknown, not false, so `WHERE col <> 'x'` silently drops
   null rows; use `IS [NOT] DISTINCT FROM` for null-safe equality. Where nulls
   sort belongs to [equality-and-ordering](equality-and-ordering.md).
7. **Do not use `NULL` as a stand-in for an empty string or collection.** Add
   `NOT NULL` and store the empty value when absence is not a domain state. Check database semantics: some treat
   zero-length strings as null. Whether `""`, `" "`, and a
   zero-width space are *the same* value is a text question
   ([text-and-encoding](text-and-encoding.md)).
8. **Return an empty collection for "no results"; reserve null for "not asked"
   or "unknown".** Returning `null` for "nothing found" makes every caller write
   a branch that most callers forget; whether an empty *range* is legal is a
   different question ([boundaries-and-ranges](boundaries-and-ranges.md)).
9. **Merge configuration layers before defaults are applied.** An eagerly defaulted higher-priority layer can mask a supplied value in a
   lower-priority layer even when the higher layer omitted the field.

For caller-visible absence, see
[Nullability and Partiality in Signatures](../contracts/nullability-and-partiality-in-signatures.md).

## Anti-patterns

**"Falsy means absent."** One check covers every empty-ish case and it reads
beautifully. Then a user sets a quota to `0` or a description to `""`, the code
takes the "they didn't tell us" branch, and it substitutes the default they had
just overridden.

**"The zero value is the default."** Go is worth showing because a plain scalar
field cannot express presence. When decoded into a fresh struct,
`{"retries": 0}`, `{"retries": null}`, and `{}` all leave an `int` field at zero.

```go
// Wrong: three different requests produce the same struct.
type Config struct {
    Retries int      `json:"retries"`
    Tags    []string `json:"tags"`
}

// Better: distinguish omitted/null from a supplied zero (Go 1.24+).
type Config struct {
    Retries *int      `json:"retries,omitzero"` // nil = omitted OR null; &0 = zero
    Tags    *[]string `json:"tags,omitzero"`    // nil = omitted OR null; &[] = empty
}
```

Pointers still conflate omitted and null on decode. Use a presence-aware decoder
when your contract requires all three states.

**"Normalize at the edge so the core is simple."** Filling defaults in at the
API boundary is real hygiene and does simplify the core. It also means that when
you change default retention from 30 days to 90, you cannot tell which rows
chose 30 and which inherited it.

**"Omitted means unchanged."** Merge semantics make partial updates easy and are
what most clients expect. But once `null` is spent on "remove", nothing encodes
"set this to null", and a client that omits its empty fields on serialization
silently fails to clear anything.

## What it costs

Explicit presence adds representation and handling costs that depend on the
language and wire format. Tri-state fields leak — every consumer, mapper, and
UI form handles three cases, and the "absent" sentinel must survive
serialization, so it becomes part of the contract you version. Persisting
provenance also adds fields and migration work. There is also a real argument
for the opposite move: the Kubernetes API conventions advise avoiding APIs that
*require* distinguishing unset from null, because designing the distinction
away is cheaper than propagating it. Take that route where you can.

## Review questions

- For this field, which of missing, null, empty, and defaulted are legal, and
  which of them does the type permit?
- If the client omits this key, what does the handler see, and is that
  distinguishable from the client sending zero?
- Is this default applied on read or written into storage — and can we still
  tell it was a default?
- Does `if not x` here need to be `x is None`, or is empty the same case?
- When a PATCH omits this field it stays; how does a client clear it?
- Does this query still return the right rows when the column is `NULL`, and
  should the column be `NOT NULL` instead?
- What tells us this job produced data rather than merely not failing?

## How to mechanize

**Type — reachable, so start here.** Three moves. Turn on
non-nullable-by-default where the language offers it, so nullability is a
declaration rather than an accident. Add a `MISSING` sentinel type where a field
needs three states, so `str | None | Missing` type-checks the way the domain
works. And make emptiness unrepresentable where an operation cannot handle it,
structurally rather than by asserting in a constructor.

```python
from dataclasses import dataclass
from enum import Enum

class Missing(Enum):
    VALUE = 0
MISSING = Missing.VALUE

@dataclass(frozen=True)
class ProfilePatch:
    display_name: str | None | Missing = MISSING   # set | cleared | untouched

@dataclass(frozen=True)
class NonEmpty[T]:
    first: T                          # emptiness has no representation
    rest: tuple[T, ...] = ()

def notify(recipients: NonEmpty[Address]) -> None: ...
```

Run a static type checker to reject nullable or possibly empty inputs where a
consumer requires a value or `NonEmpty`. Annotations do not validate inbound
data. In SQL, use a presence column when null alone is insufficient and add
constraints tying the presence state to the stored value.

**Lint — for what the type system cannot see.** In presence-handling code, flag
implicit truthiness on optional values, collections, and numbers; require `is
None` or an explicit `len(...)`. Fail the build on a proto3 scalar declared
without `optional` where the API distinguishes unset, and on Go scalar fields
using omission tags when explicit zero must survive. Do not flag pointer
`omitempty` indiscriminately: non-nil pointers to zero are retained.

**Property test — for the round trip.** Generate records covering each legal
presence and provenance state per field and assert `decode(encode(x)) == x`; it
fails the moment the encoder cannot express one of them. Assert that an empty
patch is the identity.

**Runtime assertion — at the boundaries.** Assert that every required key was
actually present rather than trusting a zero value to prove it, and assert
non-emptiness on inputs whose result is meaningless over nothing: a fan-out with
no recipients, an average with a zero denominator.

**Observation — check expected output.** For jobs required to produce data,
alert on success with zero rows or missing artifacts. Compare output with a
stated expectation; an empty result can also be valid.

## References

- GitLab, *Postmortem of database outage of January 31* (2017) — five backup and replication procedures each produced nothing, and an absent artifact read as health.
- Tony Hoare, *Null References: The Billion Dollar Mistake*, QCon London 2009 — the design argument and the ALGOL W origin. The dollar figure is rhetorical, not measured.
- Protocol Buffers, *Application Note: Field Presence* — implicit versus explicit presence, and why proto3 needed `optional`.
- RFC 7396, *JSON Merge Patch* — `null` means remove, so null cannot be set.
- RFC 6902, *JSON Patch* — explicit `add`/`remove`/`replace` when the distinction matters.
- PostgreSQL, *Comparison Functions and Operators* — null comparisons yield unknown; `IS DISTINCT FROM`.
- Oracle Database 19c, *Nulls* — a zero-length character value is treated as null.
- Kubernetes, *API Conventions* — optional fields, pointers for unset-versus-zero, and the advice to avoid needing the distinction.
- Go, `encoding/json` package documentation — omission tags and type-dependent null handling.
