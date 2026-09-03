---
title: Mutation and Aliasing
bug_classes: [shared-mutation, defensive-copy-omission, shallow-copy-leak, mutable-default, read-only-view-mutation]
authority: design
mechanizable: type
maturity: draft
last_reviewed: 2026-08-15
---

# Mutation and Aliasing

## Why review misses it

The mutation is usually valid; the hidden second reference makes it wrong. A
reviewer sees a list appended to in one method, but not the caller still holding
the list passed to the constructor, the cache returning that same list to a
second request, or the shallow copy sharing every nested member. Assignment,
copying a reference, and copying a value also use similarly ordinary syntax.
Tests hide the defect by constructing fresh fixtures and checking immediately,
before another owner mutates the object.

## The default

**Keep mutable state behind one owner; cross an ownership boundary with an
immutable value or an explicit copy, and never expose the owner's mutable
object through an argument, return value, field, or cache.**

## Rules

1. **Give every mutable object one owner.** One place decides when it changes;
   everyone else sends operations or receives snapshots.
2. **Copy mutable inputs when you retain them.** A caller may reasonably mutate
   its object after the call, so retaining its reference silently grants it
   write access to your state.
3. **Return immutable values or copies from accessors.** A getter that returns
   an internal collection is also an undocumented setter.
4. **Prefer immutable domain values.** Replacement makes a state transition
   visible at the assignment and prevents distant code from changing an object
   in place.
5. **Choose shallow or deep copying from the object graph, not convenience.** A
   shallow copy isolates the outer container only; mutable descendants remain
   shared.
6. **Represent intentional sharing with an owner API.** Put mutation behind
   methods that preserve the invariant instead of handing out the collection
   and relying on callers to coordinate.
7. **Never use a mutable object as a default argument or shared template.** It
   survives calls and turns independent instances into aliases.
8. **Treat a read-only view as access control, not immutability.** If the owner
   changes the backing object, every view observes the change.
9. **Agree on ownership at interface boundaries.** State whether each mutable
   argument is borrowed, consumed, retained, or copied, and whether each return
   value is a snapshot or a live view. *(Design authority: both sides must
   implement the same ownership contract.)*

## Anti-patterns

**"The constructor now owns it."** Passing a value feels like transferring it,
but reference-oriented languages transfer only another reference. Both caller
and object can still mutate the same collection.

```python
# Wrong: caller and Cart share items; the property exposes them again.
class Cart:
    def __init__(self, items=[]):
        self._items = items
    @property
    def items(self): return self._items

# Right: retain and expose immutable snapshots.
class Cart:
    def __init__(self, items=()):
        self._items = tuple(items)
    @property
    def items(self): return self._items
```

**"I copied the list."** `list(records)` creates a new list but retains each
record. Mutating `copied[0]["status"]` still changes `records[0]`. Use immutable
records, or deep-copy at the boundary when the graph is genuinely independent.

**"It is read-only, so it cannot change."** A wrapper that rejects writes
through one reference can still reflect writes through the backing reference.
That is useful for a deliberately live view, but it is not a snapshot.

**"Sharing avoids allocations."** Reusing a buffer or template can remove
copies from a hot path. Without a measured need and an explicit borrow lifetime,
the optimization trades a visible allocation for invisible temporal coupling.

## What it costs

Immutable values allocate replacements, and defensive copies cost time and
memory proportional to the copied graph. Deep copies can be especially
expensive and may be undefined for resources, identities, or cyclic graphs.
Single ownership can also force callers through a narrower API instead of
performing convenient bulk edits. Measure before removing those boundaries:
structural sharing, immutable snapshots, or a scoped mutable builder usually
preserve ownership without copying the whole graph on every change.

## Review questions

- Who owns this mutable object after the call returns?
- Can the caller mutate an argument that this object retained?
- Does this accessor return a snapshot, an immutable value, or a live view?
- Is this copy deep enough for every mutable descendant that may change?
- Can two instances receive the same default collection or template?
- Which methods are allowed to change this state, and where is its invariant
  enforced?
- If this sharing is intentional, what bounds the borrow and prevents a write
  after it ends?
- Does the test mutate each side after the boundary and prove the other side is
  unchanged?

## How to mechanize

**Type — reachable when the ownership contract is in the model.** Use immutable
collection and record types for snapshots. Where the language supports affine
or ownership types, consume a value on transfer and permit either one mutable
borrow or multiple immutable borrows, never both. Elsewhere, expose an
immutable interface and keep the concrete mutable type private; this prevents
writes through the API, though it cannot stop the hidden owner from mutating a
live view.

**Lint — catch the syntactic leaks.** Fail the build on mutable default
arguments, public mutable fields, and accessors that directly return a private
mutable collection. A static check can also flag assigning a mutable parameter
to a long-lived field without an explicit copy or ownership annotation. It
cannot infer whether sharing was intended across arbitrary aliases.

**Property test — exercise both directions.** Generate nested mutable values,
construct the object, then mutate the original and assert the object's snapshot
does not change. Mutate a returned value and assert a subsequent read is
unchanged. Include nested mutation so a shallow copy fails.

**Runtime assertion — guard explicit borrows.** Track whether a mutable builder
or pooled buffer has been closed, moved, or returned, and reject later use.
Assert domain invariants inside the owner's mutation methods so no intermediate
write escapes unchecked.

**Observation cannot identify aliasing itself.** Production sees the corrupted
state, not which reference changed it. Reconcile the domain invariant and alert
on violations, but treat that as containment; types, static checks, and boundary
tests are what prevent the shared mutation.

## References

- Python, [Data model: Objects, values and types](https://docs.python.org/3/reference/datamodel.html#objects-values-and-types) — identity, mutability, and multiple references to one object.
- Python, [`copy` — Shallow and deep copy operations](https://docs.python.org/3/library/copy.html) — the precise difference between copying a container and recursively copying its contents.
- Python, [Default argument values](https://docs.python.org/3/tutorial/controlflow.html#default-argument-values) — why a mutable default is shared across calls.
- Rust, [The References and Borrowing](https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html) — enforcing one mutable reference or multiple immutable references in the type system.
- Java SE, [`Collections.unmodifiableList`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Collections.html#unmodifiableList(java.util.List)) — an unmodifiable view remains a live read-through view of its backing list.
- John Hogg, [Islands: Aliasing Protection in Object-Oriented Languages](https://doi.org/10.1145/117954.117975), OOPSLA 1991 — ownership boundaries for controlling aliasing.
