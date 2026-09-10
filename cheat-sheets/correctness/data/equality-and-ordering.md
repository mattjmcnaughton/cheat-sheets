---
title: Equality and Ordering
bug_classes: [equals-hashcode-contract, non-transitive-comparator, mutable-key, compare-inconsistent-with-equals, nan-trichotomy]
authority: individual
mechanizable: property-test
maturity: draft
last_reviewed: 2026-09-08
---

# Equality and Ordering

## Why review misses it

A comparator can look correct pairwise while violating transitivity across
three values. A geometry comparator that chooses horizontal or vertical order
for each pair has no fixed ordering key. Small sorting fixtures may never
exercise the merge path that detects the defect. Equality/hash mismatches hide
in another way: the missing corresponding method is outside the diff.

## The default

**Derive equality from a fixed tuple of immutable fields, derive the hash from
that same tuple, and write every comparator as a lexicographic chain of keys
extracted from single elements — never as a branch that picks a field per
pair.**

## Rules

1. **Generate equality and hashing together, over one tuple of fields** — a
   frozen dataclass or a record. Equal objects must hash equal; a mismatch loses
   objects in hash containers and piles duplicates into sets.
2. **Never let a field used in equality, hashing, or a sort key change after
   insertion or during a sort.** A key that moves invalidates the bucket it was
   filed under; a key read live from shared state makes the comparator
   non-deterministic mid-sort. Handle shared mutable references as described in
   [mutation-and-aliasing](../state/mutation-and-aliasing.md).
3. **Build comparators as an ordered chain of keys, each computed from one
   element alone, and never by subtracting.** Branching on the pair is how
   non-transitivity gets in; `a.count - b.count` overflows and flips sign
   ([numbers-and-money](numbers-and-money.md) owns the arithmetic).
4. **Keep `compare(a, b) == 0` and `a.equals(b)` in agreement, or keep the type
   out of sorted sets and maps.** Sorted collections define membership by
   `compare` and hash collections by `equals`; disagreement puts a value twice
   in one and loses it from the other.
5. **Set a policy for `NaN` and `-0.0` in any sort key.** `NaN` is not equal to
   itself, breaking reflexivity and trichotomy at once; Python treats signed zeros as equal with equal hashes; Java boxed doubles
   distinguish them consistently in equality, hashing, and order.
6. **Choose identity or value equality per type, once, and say which.** Entities
   compare by identifier, values by content; a type quietly doing both gets
   compared the wrong way somewhere.
7. **Follow the language protocol for unsupported equality operands.** Return
   false from Java `equals`; return `NotImplemented` from Python `__eq__` so the
   other operand can participate. Reject unsupported ordering operands. A comparator owes
   you consistency, not cultural correctness: collation belongs to
   [text-and-encoding](text-and-encoding.md), absent values to
   [absence-and-emptiness](absence-and-emptiness.md).

When changing an existing comparator, use
[Refactoring Without Semantic Drift](../change/refactoring-without-semantic-drift.md).

## Anti-patterns

**"Compare on whichever dimension matters here."** Real orderings are
context-sensitive, so the comparator notices context. Each branch is defensible;
the whole is not a total order. Move context into a per-element key, so the pair
gets no vote.

```python
# WRONG: picks an axis per pair. Not transitive.
def compare(a, b):
    if abs(a.top - b.top) < 5:          # "same line" -> left to right
        return sign(a.left - b.left)
    return sign(a.top - b.top)

# RIGHT: band each element once, then sort lexicographically.
def sort_key(r):
    return (r.line_band, r.left)        # line_band comes from r alone
```

**"Equality with a tolerance."** Approximate results need a tolerance, so
`__eq__` gets an epsilon. Approximate equality is not transitive — `a ≈ b`, `b
≈ c`, `a ≉ c` — and it wrecks any hash container on the type. Put tolerance in
an `is_close` helper no collection calls.

**"Equality here, hashing over there."** A field joins `equals` because it
really is part of identity, and the hash method sits elsewhere in the file, so
newly equal objects can still have different hashes and fail lookup. The mirror
image is `unsafe_hash=True` over every field, including the mutable one a
caller sets after the object lands in a set.

**"`<` and `>` are the comparison."** Shown in Java because the JVM makes it
explicit: `Double.equals` deliberately disagrees with `==` — `NaN` equals
itself, `+0.0` does not equal `-0.0` — so hash tables work.

```java
// WRONG: every NaN pair reports 0, so the ordering is not total.
(a, b) -> a.score < b.score ? -1 : a.score > b.score ? 1 : 0
// RIGHT: a total order; NaN sorts to one end, -0.0 before 0.0.
Comparator.comparingDouble(x -> x.score)
```

## What it costs

Derived equality still compares fields and hashing still computes a hash;
the cost depends on those fields. Two real bills. Immutability is
contagious — freezing the fields that define identity forces copy-on-write
wherever those objects are edited. And making `compare` agree with `equals`
usually means adding a tie-break field nobody cares about.

## Review questions

- Which fields define equality here, and does the hash use exactly that set?
- Is every field in equality or in the sort key immutable after construction?
- Is this object ever a key in a hash container or in a sorted collection?
- Does this comparator branch on the pair to choose what to compare, or is it a
  fixed chain of per-element keys?
- Does `compare(a, b) == 0` mean the same thing here as `a == b`, and if not,
  where is that written down?
- Can this sort key ever be `NaN`, `null`, or `-0.0`, and what happens then?

## How to mechanize

**Type — partial; take the two things it buys.** *Derive* rather than
implement: a frozen dataclass using default equality/hash settings keeps the
selected fields aligned. Freezing is shallow: require immutable, hashable field
values. And *withhold order*: a type with no meaningful total order should not
implement the comparison interface at all, so "sorted wrong" fails static
checking where supported, or raises at runtime in Python. There it stops: a
type system can require that you implement `compare`; ordinary interface
checking does not prove that the implementation obeys equality, ordering, or
hashing laws — `(T, T) -> int` is satisfied by `return 1`. These are laws about
behavior, not shapes. Python promotes exactly one into the language: overriding
`__eq__` without `__hash__` makes the class unhashable.

**Lint — further than you would expect, and still not the ceiling.** For
classes intended to be hashable, check that equality and hashing are derived
from compatible fields; allow intentionally unhashable value types. Flag
subtraction inside a fixed-width comparison method. Both are shapes, which is
the limit — a comparator branching on the pair has perfect shape and passes
them.

**Property test — the ceiling, because the contracts *are* properties.**
Generate values, pairs, and triples and assert `x == x`; `a == b` implies `b ==
a`; equality and ordering are transitive; `sign(compare(a, b)) ==
-sign(compare(b, a))`; `compare(a, b) == 0` exactly when `a == b`; and `a == b`
implies `hash(a) == hash(b)`. Sort a generated list and assert the output is
ordered and a permutation of the input, with cases large and varied enough to
exercise the target implementation merging runs. Do not rely on the sort to
detect invalid comparators: Python does not provide the JDK contract check.
Seed the generator with law-breakers: `NaN`, `-0.0`, equal-but-not-identical
instances, subclass instances, `None`.

**Runtime assertion — for what generation cannot reach.** Validate `NaN` and
absent sort keys against the chosen policy at the boundary. Where a comparison
key comes from shared mutable state, snapshot it once per element and sort the
snapshots; checking only before and after cannot detect a value that changes
and changes back. Never silence the contract exception by restoring the legacy
merge sort; it buys a silently wrong order instead of a loud one.

**Observation — where hash containers are load-bearing.** Export a deduplicating
set's size against the expected distinct count; alert on drift.

## References

- tabulapdf/tabula-java, issue #116 — `Rectangle` and `TextChunk` comparators using "multiple comparisons to decide which dimension to compare on", rejected by TimSort as `Comparison method violates its general contract!`.
- Oracle, *Java SE 7 and JDK 7 Compatibility* — the replaced sort "may throw an `IllegalArgumentException` if it detects a `Comparable` that violates the `Comparable` contract".
- npgall/cqengine, issue #41 — the same exception from a comparison key that changed mid-sort under concurrent modification.
- de Gouw, Rot, de Boer, Bubel & Hähnle, *OpenJDK's java.utils.Collection.sort() Is Broken*, CAV 2015 — verification that found a real bug in TimSort's `mergeCollapse`.
- Java SE 21 API documentation, `java.lang.Object` — the `equals` contract; equal objects must hash equal.
- Java SE 21 API documentation, `java.util.Comparator` — "consistent with equals", and the warning about sorted sets and maps.
- Java SE 21 API documentation, `java.lang.Double` — why `equals` treats `NaN` and signed zero unlike `==`.
- Python 3 documentation, *Data model* — equal objects must hash equal; `__eq__` without `__hash__` sets `__hash__` to `None`.
- Python 3 documentation, *Expressions: value comparisons* — collections assume element reflexivity and test identity first, so `[nan] == [nan]` is true.
- Joshua Bloch, *Effective Java*, 3rd edition, items 10 and 11.
