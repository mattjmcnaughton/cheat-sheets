---
title: Boundaries and Ranges
bug_classes: [off-by-one, inclusive-exclusive-mismatch, pagination-gap, pagination-duplicate, interval-overlap]
authority: individual
mechanizable: property-test
maturity: draft
last_reviewed: 2026-08-14
---

# Boundaries and Ranges

## Why review misses it

`<` and `<=` are both valid, both idiomatic, one character apart, and nothing in
the diff says which is correct — the convention that decides it lives in a doc
comment or someone else's spec, not in the expression. A range also has the same
type under both: `(int, int)` for `[a, b)` and for `[a, b]`, same shape, same
printed form, so a reviewer reading `fetch(start, end)` has no signal at all.
And the failure is one element wide, surfacing only when data lands on the seam
— the last row of a page, a record written at 23:59, an interval where
`start == end` — while fixtures and the reviewer's mental example are drawn from
the middle.

## The default

**Represent every range — index, slice, page, time window, interval — as
half-open `[start, end)`, start included and end excluded; where a boundary you
do not control uses another convention, convert once at that boundary and put
the convention in the name (`end_exclusive`, `last_inclusive`).**

## Rules

1. **Default every range to half-open `[start, end)`.** The length is
   `end - start`, the empty range is `start == end`, and adjacent ranges share
   one number rather than needing a `+1` between them (Dijkstra, EWD 831).
2. **Never write `+ 1` or `- 1` to reconcile two ranges.** Each is a convention
   mismatch patched at the arithmetic instead of at the edge.
3. **Derive a midpoint from the width, not the endpoints:** `low + (high - low)
   / 2`, never `(low + high) / 2`. Endpoint arithmetic can exceed the type on
   large ranges — the defect that sat in `Arrays.binarySearch` for nine years —
   and the width is the quantity a half-open range makes primitive. Whether the
   sum wraps is a numeric problem ([numbers-and-money](numbers-and-money.md)).
4. **Name any bound that is not half-open** — `end_exclusive`,
   `last_inclusive` — in the parameter, field, and column. The type cannot carry
   the convention, so the identifier must.
5. **Read the spec at each boundary instead of assuming half-open.** HTTP byte
   ranges are inclusive at both ends — `bytes=0-499` is 500 bytes, RFC 9110
   §14.1.1 — and SQL `BETWEEN` is inclusive; assuming your preferred default is
   how two internally consistent systems disagree.
6. **Convert a human-facing inclusive date to an exclusive instant at the parse
   boundary, once:** `end_exclusive = start_of_day(end_date + 1 day)`, then
   query with `<`. "Through 31 August" means every instant of that day.
7. **Paginate by position in a total order, not by offset.** `OFFSET` counts
   rows that move under concurrent writes, silently skipping or repeating one; a
   keyset cursor `WHERE (created_at, id) > (?, ?)` is the same half-open rule.
   What makes that comparison a legal total order is
   [equality-and-ordering](equality-and-ordering.md).
8. **Make `start == end` a valid empty range and reject `end < start` at
   construction.** Conflating "empty" with "invalid" produces ranges that
   silently match everything; whether a bound may be absent at all is
   [absence-and-emptiness](absence-and-emptiness.md).
9. **Define `contains`, `overlaps`, `adjacent`, and `split` once and call
   them.** Half-open overlap is `a.start < b.end and b.start < a.end`; inlined
   at call sites, it gets written with `<=` somewhere.
10. **Use half-open intervals for time spans too.** A local day is not always
    24 hours, but `[midnight, next midnight)` still tiles the year
    ([time-and-time-zones](time-and-time-zones.md)).

## Anti-patterns

**"The API documents an inclusive `end_date`, so query with `<=`."** The
reasoning is right — the doc says inclusive — and the fix is still wrong
whenever the column holds a timestamp rather than a date.

```python
# Wrong: drops every event after midnight on the last day.
rows = q.filter(created_at >= start_date, created_at <= end_date)

# Right: convert the inclusive bound to an exclusive instant, once.
end_exclusive = start_of_day(end_date + timedelta(days=1), tz)
rows = q.filter(created_at >= start_instant, created_at < end_exclusive)
```

**"Store inclusive, because that is what the user asked for."** Reports say
"1–31 August", and matching storage to the domain's language feels honest. Now
every consumer must know, and adjacency needs `+1` in a unit — days?
microseconds? — that no two of them guess alike.

**"`LIMIT 20 OFFSET 40` — pagination is solved."** It is trivial, supports
jumping to page 7, and yields a page count. It also drops a row whenever
something is inserted before the cursor between requests; in an export, that
means a customer's record is not in the file.

**"Overlap is `a.start <= b.end and b.start <= a.end`."** Lifted from a
closed-interval formulation, where it is correct. On half-open ranges `[9, 10)`
and `[10, 11)` "overlap" at 10, so a booking system refuses back-to-back
appointments and nobody can explain why.

## What it costs

Half-open ranges cost nothing at runtime and less code than the alternative: the
adjustments disappear. Three real bills. Humans specify ranges inclusively, so
you own a conversion layer at every human-facing edge — request parsers, report
parameters, exports — plus the naming discipline to keep it visible. Keyset
pagination gives up random page access and exact page counts, and needs a
composite index on the sort key plus its tiebreaker. And a range type costs a
wrapper at every serialization boundary, since JSON and SQL columns flatten it
back to a pair of numbers.

## Review questions

- Is this range half-open, and where is that recorded — in the name, the type,
  or nowhere?
- What does this return when `start == end`, and when `end < start`?
- If a row's timestamp is exactly the `end` value, is that row in the result?
- This `+ 1` — which two conventions is it reconciling, and why here rather than
  at the boundary?
- Does the `end_date` in the API documentation mean the same thing as the
  comparison in the query underneath it?
- If a row is inserted while the client is between pages, which row gets skipped
  or repeated?
- Do these intervals tile the span exactly, or can they gap or double-count at a
  seam?

## How to mechanize

**Type — real, but smaller than it looks.** `[a, b)` and `[a, b]` are both
`(int, int)`, so no type checker tells them apart. A `Range` type still buys
three things: a validating constructor makes `end < start` unconstructible; one
factory states the convention once; and `length`, `contains`, and `overlaps`
live on the type, so `<` versus `<=` is decided once, not at forty call sites.
It stops there — nothing stops a caller passing `Range(start, last_inclusive)`,
and the distinction evaporates on serialization.

**Lint — unavailable for the part that matters.** A linter can ban patterns
wrong under either convention: `range(1, len(xs) + 1)`, `BETWEEN` on a timestamp
column, a bare `OFFSET` in a paginating query. It cannot tell a correct `<=`
from an incorrect one: both are well-formed, both are right elsewhere in the
same file, and the fact separating them is in a document the linter cannot read.

**Property test — the highest rung that bites; spend the effort here.** Range
invariants are algebraic and total, which is what generated inputs find and
examples miss, because authors pick the middle (Claessen & Hughes, 2000). Assert
that splitting anywhere yields disjoint parts whose union is the original
(`xs[:i] + xs[i:] == xs`, generalized); that `len(r) == r.end - r.start`
whenever `start <= end`; that `[a,b)` and `[b,c)` never overlap; that parsing an
inclusive `end_date` yields an instant strictly after every instant of that
date. Then pagination completeness:

```python
@given(rows=st.lists(row(), unique_by=key_of), size=st.integers(1, 5))
def test_pages_tile_the_scan(rows, size):
    seen, cursor = [], None
    while page := fetch_page(rows, after=cursor, limit=size):
        seen += page
        cursor = key_of(page[-1])
    assert seen == sorted(rows, key=key_of)
```

Interleave inserts and deletes between fetches too. Shrinking then hands you the
minimal counterexample: the empty or single-element range.

**Runtime assertion — where generation cannot reach.** Assert `start <= end` in
the constructor; assert each page cursor is strictly greater than the last, so a
stalled cursor fails instead of looping; assert a tiling covers its span where
it is built, not in the report that consumes it.

**Observation — for boundaries shared with another system.** Reconcile a
paginated export's row count against a `COUNT(*)` over the same predicate and
alert on drift: a one-row gap is invisible on a dashboard, obvious in a
reconciliation.

## References

- E. W. Dijkstra, [Why numbering should start at zero (EWD 831)](https://www.cs.utexas.edu/~EWD/transcriptions/EWD08xx/EWD831.html) (1982) — the case for `a <= i < b`.
- Joshua Bloch, [Extra, Extra — Read All About It: Nearly All Binary Searches and Mergesorts are Broken](https://research.google/blog/extra-extra-read-all-about-it-nearly-all-binary-searches-and-mergesorts-are-broken/), Google Research (2006) — a midpoint taken from endpoints rather than width, broken in the JDK for about nine years.
- [JDK-5045582: (coll) binarySearch() fails for size larger than 1<<30](https://bugs.openjdk.org/browse/JDK-5045582).
- [RFC 9110 §14.1.1, Byte Ranges](https://www.rfc-editor.org/rfc/rfc9110#section-14.1.1) — byte positions inclusive at both ends: a deployed spec that is not half-open.
- [Python tutorial: An Informal Introduction to Python](https://docs.python.org/3/tutorial/introduction.html) — slice semantics and `s[:i] + s[i:] == s`.
- Koen Claessen and John Hughes, [QuickCheck: A Lightweight Tool for Random Testing of Haskell Programs](https://dl.acm.org/doi/10.1145/351240.351266), ICFP 2000.
