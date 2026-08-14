---
title: Absence and Emptiness
bug_classes: [null-vs-empty-conflation, missing-vs-default-conflation, zero-value-as-unset, patch-erases-field, absent-read-as-success]
authority: design
mechanizable: type
maturity: draft
last_reviewed: 2026-08-14
---

# Absence and Emptiness

## Why review misses it

The four states are spelled the same way in most languages. `None`, `""`, `[]`,
`0`, and `False` are all falsy, so `if not value:` — a line no reviewer stops on
— silently treats "the user cleared this field" and "the user never mentioned
it" as one case. Worse, the distinction is usually destroyed upstream of the
diff: by the time the deserializer hands you a struct, the fact that the key was
absent from the body is gone, and reading the handler cannot recover it. Tests
hide it because fixture authors fill in every field, and the path that matters —
a client that omits the key — is the one nobody writes a fixture for.

## The default

**Treat "missing", "null", "empty", and "defaulted" as four different values:
keep them distinct in the type at every boundary you control, never test them
with a single truthiness check, and never store a default as if the caller had
supplied it.**

## Rules

1. **Never test presence with truthiness.** `if not x` is true for `0`, `""`,
   `[]`, and `False`, all of which a caller can legitimately mean. Ask
   `x is None` and `len(x) == 0` separately.
2. **Never let a scalar's zero value stand for "unset".** Use explicit presence —
   an optional wrapper, a pointer, a protobuf `optional` field — so "0" and "not
   sent" are different bytes on the wire.
3. **Preserve "key absent" through deserialization with a sentinel distinct from
   null.** A three-state field needs three inhabitants; `Optional[T]` has two.
   *(Design authority: this changes a shared wire contract — agree it with the
   other side.)*
4. **Apply defaults at read time, and record that the value was defaulted.** A
   default written into storage is indistinguishable from a choice, and you
   cannot change it later without rewriting history.
5. **State your PATCH semantics and pick a format that can express them.** JSON
   Merge Patch spends `null` on "remove", so it cannot set a member to null
   (RFC 7396); use JSON Patch (RFC 6902) or a field mask when clearing and
   omitting must differ.
6. **In SQL, assume `NULL` is contagious and unequal to itself.** Comparisons
   with `NULL` yield unknown, not false, so `WHERE col <> 'x'` silently drops
   null rows; use `IS [NOT] DISTINCT FROM` for null-safe equality. Where nulls
   sort belongs to [equality-and-ordering](equality-and-ordering.md).
7. **Do not use `NULL` as a stand-in for an empty string or collection.** Add
   `NOT NULL` and store the empty value so the column has one meaning — and know
   that Oracle equates `''` with `NULL` regardless. Whether `""`, `" "`, and a
   zero-width space are *the same* value is a text question
   ([text-and-encoding](text-and-encoding.md)).
8. **Return an empty collection for "no results"; reserve null for "not asked"
   or "unknown".** Returning `null` for "nothing found" makes every caller write
   a branch that most callers forget; whether an empty *range* is legal is a
   different question ([boundaries-and-ranges](boundaries-and-ranges.md)).
9. **Merge configuration layers before defaults are applied.** Otherwise a lower
   layer's default overwrites a higher layer's deliberate setting, and nobody
   can tell which won.

## Anti-patterns

**"Falsy means absent."** One check covers every empty-ish case and it reads
beautifully. Then a user sets a quota to `0` or a description to `""`, the code
takes the "they didn't tell us" branch, and it substitutes the default they had
just overridden.

**"The zero value is the default."** Go is worth showing because it has no way
to express "no value": every field starts at its zero value, and `encoding/json`
documents that "unmarshaling a JSON null into any other Go type has no effect on
the value and produces no error" — so `{"retries": 0}`, `{"retries": null}`, and
`{}` all arrive as `0`.

```go
// Wrong: three different requests produce the same struct.
type Config struct {
    Retries int      `json:"retries"`
    Tags    []string `json:"tags"`
}

// Right: absence is representable, and Marshal round-trips it (Go 1.24+).
type Config struct {
    Retries *int      `json:"retries,omitzero"` // nil = not sent, &0 = sent as 0
    Tags    *[]string `json:"tags,omitzero"`    // nil = not sent, &[] = clear it
}
```

**"Normalize at the edge so the core is simple."** Filling defaults in at the
API boundary is real hygiene and does simplify the core. It also means that when
you change default retention from 30 days to 90, you cannot tell which rows
chose 30 and which inherited it.

**"Omitted means unchanged."** Merge semantics make partial updates easy and are
what most clients expect. But once `null` is spent on "remove", nothing encodes
"set this to null", and a client that omits its empty fields on serialization
silently fails to clear anything.

## What it costs

At the type level, close to free: an optional wrapper is a pointer or a tag
word, and the branch it forces on you is a branch you owed anyway. The real
costs are ergonomic. Tri-state fields leak — every consumer, mapper, and UI form
handles three cases, and the "absent" sentinel must survive serialization, so it
becomes part of the contract you version. Storing "was this supplied?" alongside
the value roughly doubles the columns of a configuration table. There is also a
real argument for the opposite move: the Kubernetes API conventions advise
avoiding APIs that *require* distinguishing unset from null, because designing
the distinction away is cheaper than propagating it. Take that route where you
can.

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
class Missing:                       # key never sent; distinct from None
    pass
MISSING = Missing()

@dataclass(frozen=True)
class ProfilePatch:
    display_name: str | None | Missing = MISSING   # set | cleared | untouched

@dataclass(frozen=True)
class NonEmpty[T]:
    first: T                          # emptiness has no representation
    rest: tuple[T, ...] = ()

def notify(recipients: NonEmpty[Address]) -> None: ...
```

This rung is unavailable in SQL: a column is nullable or not, and no type
distinguishes "no row supplied a value" from "the value is empty". Fall to
constraints there — `NOT NULL` plus a `CHECK` forbidding the sentinel.

**Lint — for what the type system cannot see.** Ban implicit truthiness on
values annotated `Optional[...]`, a collection, or a number; require `is None`
or an explicit `len(...)`. Fail the build on a proto3 scalar declared without
`optional` where the API distinguishes unset, and on `omitempty` applied to Go
bools, numbers, and pointers where `omitzero` is meant.

**Property test — for the round trip.** Generate records covering all four
states per field and assert `decode(encode(x)) == x`; it fails the moment the
encoder cannot express one of them. Assert that an empty patch is the identity.

**Runtime assertion — at the boundaries.** Assert that every required key was
actually present rather than trusting a zero value to prove it, and assert
non-emptiness on inputs whose result is meaningless over nothing: a fan-out with
no recipients, an average with a zero denominator.

**Observation — for the empty-result failure mode.** Alert on jobs that succeed
having written zero rows, and on any backup or export whose artifact is missing
or implausibly small. This is the one rung that catches a pipeline where every
check asks "did anything report an error?" and none asks "is there an object
here, with rows in it?" — an "OK" with nothing behind it.

## References

- GitLab, [Postmortem of database outage of January 31](https://about.gitlab.com/blog/postmortem-of-database-outage-of-january-31/) (2017) — five backup and replication procedures each produced nothing, and an absent artifact read as health.
- Tony Hoare, [Null References: The Billion Dollar Mistake](https://www.infoq.com/presentations/Null-References-The-Billion-Dollar-Mistake-Tony-Hoare/), QCon London 2009 — the design argument and the ALGOL W origin. The dollar figure is rhetorical, not measured.
- Protocol Buffers, [Application Note: Field Presence](https://protobuf.dev/programming-guides/field_presence/) — implicit versus explicit presence, and why proto3 needed `optional`.
- [RFC 7396: JSON Merge Patch](https://www.rfc-editor.org/rfc/rfc7396) — `null` means remove, so null cannot be set.
- [RFC 6902: JSON Patch](https://www.rfc-editor.org/rfc/rfc6902) — explicit `add`/`remove`/`replace` when the distinction matters.
- PostgreSQL, [Comparison Functions and Operators](https://www.postgresql.org/docs/current/functions-comparison.html) — null comparisons yield unknown; `IS DISTINCT FROM`.
- Oracle Database, [Nulls](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/Nulls.html) — a zero-length character value is treated as null.
- Kubernetes, [API Conventions](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-architecture/api-conventions.md) — optional fields, pointers for unset-versus-zero, and the advice to avoid needing the distinction.
- Go, [`encoding/json`](https://pkg.go.dev/encoding/json) — `omitempty` versus `omitzero`; null unmarshals as a no-op.
