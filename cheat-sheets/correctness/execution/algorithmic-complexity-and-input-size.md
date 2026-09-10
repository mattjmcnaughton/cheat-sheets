---
title: Algorithmic Complexity and Input Size
bug_classes: [quadratic-scan, hidden-materialization, output-explosion, unbounded-input-cost]
authority: design
mechanizable: property-test
maturity: draft
last_reviewed: 2026-09-10
---

# Algorithmic Complexity and Input Size

## Why review misses it

A comprehension hides a scan inside a scan. A helper returns one object but
reads an entire input to construct it. Small fixtures cannot distinguish a
linear operation from a quadratic one in any useful way. The diff preserves
the result, so functional tests pass while valid larger inputs exceed memory
or execution limits. Input count alone also hides long strings, wide records,
deep nesting, and large intermediate results.

## The default

**Name the input dimensions that determine work and memory, set supported
limits for them, and choose an algorithm whose worst relevant case fits those
limits before accepting the input.**

## Rules

1. **Measure input size in the dimensions the algorithm consumes.** Include
   record count, total bytes, key length, nesting depth, and graph edges where
   applicable; equal row counts need not imply equal costs.
2. **Write the cost of composed operations, not just the outer loop.** A scan,
   sort, allocation, or remote lookup inside a helper still happens on every
   call.
3. **Separate worst-case, expected, and amortized claims.** A hash lookup's
   expected cost is not a worst-case guarantee, and occasional resizing may
   matter to a single operation's latency budget.
4. **Count intermediate and output size as well as input size.** A join or
   Cartesian product can emit multiplicative results even when its inputs each
   fit comfortably in memory.
5. **Choose representations that support the repeated operation.** Use a
   lookup index for repeated membership or a deque for removal from the front;
   account for index construction and retained storage too.
6. **Enforce limits before the expensive expansion or allocation.**
   **Needs design authority:** agree maximum supported sizes and rejection
   behavior with callers, including decompressed size and nesting depth.
7. **Exercise distributions that defeat the intended fast path.** Include
   all-distinct keys, repeated keys, absent matches, long common prefixes, and
   skewed joins according to the operations you actually perform.
8. **Budget total work even when results are lazy or paginated.** Iteration
   postpones work; it does not reduce the number of combinations a caller asks
   to consume. Use [bounded work](bounded-work-and-backpressure.md) for concurrent
   admission rather than confusing concurrency limits with algorithmic cost.

## Anti-patterns

**"A short comprehension is a cheap filter."** Membership in a list repeats a
linear scan for each item. For hashable keys with the intended equality
semantics, build the lookup once; this trades extra storage for expected faster
membership, not a universal worst-case bound.

```python
# Wrong for large inputs: repeated scans of allowed_ids.
selected = [row for row in rows if row.id in allowed_ids]

# Right for hashable IDs: build the lookup once.
allowed = set(allowed_ids)
selected = [row for row in rows if row.id in allowed]
```

**"Remove the first item until the list is empty."** It is an obvious queue,
but each removal shifts the remaining elements. Use `collections.deque` and
`popleft()` when you require repeated front removal; a simple `for` loop is
enough if you only need to visit a fixed collection once.

**"The iterator means constant memory."** Deferred output can still retain
input pools or lagging consumers. Check iterator storage behavior: Cartesian
product implementations can pool inputs, and splitting one iterator into two
can buffer values for the slower consumer. Stream with an explicit retained
state bound; see [incremental processing](streaming-and-incremental-processing.md).

**"We tested a million records."** One favorable distribution leaves key length,
join multiplicity, and absent-match scans untested. Derive cases from each cost
dimension and include the maximum supported shape, not only the headline count.

## What it costs

Indexes consume memory and must preserve the existing equality and duplicate
semantics. Limits make some previously accepted inputs explicit failures.
Operation counters require a small test seam around the expensive primitive;
wall-clock checks require a controlled environment and a stated allowance for
noise. Keep a simple bounded algorithm when its documented maximum fits the
budget; asymptotic improvement alone does not justify a more complex design.

## Review questions

- Which input dimensions determine this change's work and peak memory?
- What do the helpers inside this loop allocate, scan, sort, or fetch?
- Is the cost claim worst-case, expected, or amortized?
- Can duplicate keys or expansion multiply the output size?
- Where is oversized input rejected before expensive work begins?
- Which test input defeats the usual fast path?
- Does the replacement preserve order, duplicates, and equality semantics?

## How to mechanize

**Property test — enforce a cost budget alongside result equivalence.**
Generate bounded inputs across each relevant dimension and compare results
against a simple reference implementation. Instrument the primitive that
dominates the cost, such as key comparisons, edge visits, or remote calls.
For a merge of two sorted sequences, assert sorted output with the same
multiplicities and at most `max(0, n + m - 1)` key comparisons in the merge
itself. Count comparison cost separately if keys have unbounded length.

For a different algorithm, derive its own allowance instead of reusing that
formula. Check every generated case against the allowance; a doubling benchmark
alone can miss a rare expensive shape. Generated cases detect regressions but
do not prove the asymptotic bound. Validate elapsed time and peak memory at
supported limits separately on the intended deployment environment.

Ordinary types do not encode operation counts. A static ban on nested loops
rejects legitimate bounded work and misses expensive helpers, so it does not
establish this budget. Formal cost analysis can provide stronger guarantees
where available; this sheet's concrete check is the generated cost assertion.

## References

- Python Software Foundation, *Python 3 Library Reference*, `collections.deque`
  — approximately constant-time end operations versus linear-time front
  removal in lists.
- Python Software Foundation, *Python 3 Library Reference*, `itertools.product`
  and `itertools.tee` — retained input pools and auxiliary storage behind
  iterator interfaces.
- Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, and Clifford Stein,
  *Introduction to Algorithms*, fourth edition, 2022, chapters 2, 3, 11, and 16
  — merge analysis, asymptotic notation, hashing assumptions, and amortization.
