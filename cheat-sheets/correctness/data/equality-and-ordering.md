---
title: Equality and Ordering
bug_classes: [equals-hashcode-contract, non-transitive-comparator, mutable-key, compare-inconsistent-with-equals, nan-trichotomy]
authority: individual
mechanizable: property-test
maturity: draft
last_reviewed: 2026-08-14
---

# Equality and Ordering

## Why review misses it

A comparator reads correctly because a reviewer checks it pairwise, and
transitivity is a property of *triples*: nothing in the diff puts three objects
side by side. Consider a comparator that picks its axis per pair — boxes on
roughly the same line order left to right, otherwise top to bottom. The geometry
is sound and the order is not transitive, since A and B can share a line, B and
C share a line, and A and C not. The failure is size-dependent on top of that:
the JDK detects an inconsistent ordering only while merging runs, and it
insertion-sorts short ones, so a five-element fixture cannot fire the check and
most inputs sort fine. The `equals`/`hashCode` variant hides differently again —
the bug is a method that is *absent*, and a diff shows lines added, not lines
that should have been.

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
   non-deterministic mid-sort.
3. **Build comparators as an ordered chain of keys, each computed from one
   element alone, and never by subtracting.** Branching on the pair is how
   non-transitivity gets in; `a.count - b.count` overflows and flips sign
   ([numbers-and-money](numbers-and-money.md) owns the arithmetic).
4. **Keep `compare(a, b) == 0` and `a.equals(b)` in agreement, or keep the type
   out of sorted sets and maps.** Sorted collections define membership by
   `compare` and hash collections by `equals`; disagreement puts a value twice
   in one and loses it from the other.
5. **Set a policy for `NaN` and `-0.0` in any sort key.** `NaN` is not equal to
   itself, breaking reflexivity and trichotomy at once; `-0.0 == 0.0`, yet the
   two may hash and sort apart.
6. **Choose identity or value equality per type, once, and say which.** Entities
   compare by identifier, values by content; a type quietly doing both gets
   compared the wrong way somewhere.
7. **Make `equals` false for `null` and foreign types rather than throwing, and
   make an *ordering* over incomparable types a hard error.** A comparator owes
   you consistency, not cultural correctness: collation belongs to
   [text-and-encoding](text-and-encoding.md), absent values to
   [absence-and-emptiness](absence-and-emptiness.md).

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

**"Equality with a tolerance."** Floats never match exactly, so `__eq__` gets an
epsilon. Approximate equality is not transitive — `a ≈ b`, `b ≈ c`, `a ≉ c` — and
it wrecks any hash container on the type. Put tolerance in an `is_close` helper
no collection calls.

**"Equality here, hashing over there."** A field joins `equals` because it really
is part of identity, and the hash method sits elsewhere in the file, so objects
inserted before the change stop answering to lookup. The mirror image is
`unsafe_hash=True` over every field, including the mutable one a caller sets
after the object lands in a set.

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

Near zero where equality is derived: a frozen dataclass or record costs a
constructor and nothing at comparison time. Two real bills. Immutability is
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

**Type — partial; take the two things it buys.** *Derive* rather than implement:
a frozen dataclass or a record gives structural equality and a matching hash
that cannot drift apart. And *withhold order*: a type with no meaningful total
order should not implement the comparison interface at all, so "sorted wrong"
becomes "does not compile". There it stops: a type system can require that you
implement `compare`; none can check that the
implementation is reflexive, symmetric, transitive, or consistent with hashing —
`(T, T) -> int` is satisfied by `return 1`. These are laws about behavior, not
shapes. Python promotes exactly one into the language: overriding `__eq__`
without `__hash__` makes the class unhashable.

**Lint — further than you would expect, and still not the ceiling.** "Defines
equality and not hashing, or the reverse" is decidable from the AST alone and is
a standard, widely implemented check; so is subtraction inside a comparison
method. Both are shapes, which is the limit — a comparator branching on the pair
has perfect shape and passes them.

**Property test — the ceiling, because the contracts *are* properties.**
Generate values, pairs, and triples and assert `x == x`; `a == b` implies
`b == a`; equality and ordering are transitive;
`sign(compare(a, b)) == -sign(compare(b, a))`; `compare(a, b) == 0` exactly when
`a == b`; and `a == b` implies `hash(a) == hash(b)`. Sort a generated list and
assert the output is ordered and a permutation of the input, with at least one
case of thirty-two or more elements — a sort that never merges never exercises
the contract check. Seed the generator with law-breakers: `NaN`, `-0.0`,
equal-but-not-identical instances, subclass instances, `None`.

**Runtime assertion — for what generation cannot reach.** Reject `NaN` and
absent sort keys at the boundary, not inside the comparator. Where a comparison
key comes from shared mutable state, snapshot it before the sort and assert it
unchanged after. Never silence the contract exception by restoring the legacy
merge sort; it buys a silently wrong order instead of a loud one.

**Observation — where hash containers are load-bearing.** Export a deduplicating
set's size against the expected distinct count; alert on drift.

## References

- tabulapdf/tabula-java, [issue #116](https://github.com/tabulapdf/tabula-java/issues/116) — `Rectangle` and `TextChunk` comparators using "multiple comparisons to decide which dimension to compare on", rejected by TimSort as `Comparison method violates its general contract!`.
- Oracle, [Java SE 7 and JDK 7 Compatibility](https://www.oracle.com/java/technologies/compatibility.html) — the replaced sort "may throw an `IllegalArgumentException` if it detects a `Comparable` that violates the `Comparable` contract".
- npgall/cqengine, [issue #41](https://github.com/npgall/cqengine/issues/41) — the same exception from a comparison key that changed mid-sort under concurrent modification.
- de Gouw, Rot, de Boer, Bubel & Hähnle, [OpenJDK's java.utils.Collection.sort() Is Broken](https://link.springer.com/chapter/10.1007/978-3-319-21690-4_16), CAV 2015 — verification that found a real bug in TimSort's `mergeCollapse`.
- [`java.lang.Object`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Object.html) — the `equals` contract; equal objects must hash equal.
- [`java.util.Comparator`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Comparator.html) — "consistent with equals", and the warning about sorted sets and maps.
- [`java.lang.Double`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Double.html) — why `equals` treats `NaN` and signed zero unlike `==`.
- Python, [Data model](https://docs.python.org/3/reference/datamodel.html) — equal objects must hash equal; `__eq__` without `__hash__` sets `__hash__` to `None`.
- Python, [Expressions: value comparisons](https://docs.python.org/3/reference/expressions.html) — collections assume element reflexivity and test identity first, so `[nan] == [nan]` is true.
- Joshua Bloch, *Effective Java*, 3rd edition, items 10 and 11.
