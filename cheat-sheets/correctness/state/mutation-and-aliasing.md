---
title: Mutation and Aliasing
bug_classes: [shared-mutable-default, shallow-copy-alias, escaped-mutable-state, false-immutability]
authority: design
mechanizable: lint
maturity: draft
last_reviewed: 2026-09-08
---

# Mutation and Aliasing

## Why review misses it

Two variables look like two pieces of state in a diff. They can point to the
same list, or to different dictionaries containing the same list. A local edit
then changes a value held elsewhere, without another assignment at that site.
Tests that construct fresh inputs for every call never exercise that second
reference. A copy at the outermost level makes the code look isolated while
leaving the actual mutable child shared.

## The default

**Keep each mutable object under one owner's control; when you pass its value
across a boundary, return an immutable snapshot or copy every mutable part the
recipient may change.**

## Rules

1. **Define whether each boundary borrows, copies, or takes ownership of mutable
   input; agree on shared interfaces at design time.** A new variable name does
   not transfer ownership or revoke the caller's reference.
2. **Copy retained caller input and returned internal state at the required
   depth, unless the interface explicitly transfers ownership.** Either
   direction can let a caller change an object's state behind its methods.
3. **Use a shallow copy only when sharing every child is safe.** A new outer
   container still holds references to the old children.
4. **Build snapshots from immutable leaves as well as immutable containers.**
   A tuple containing a list, or a frozen record containing a dictionary, still
   exposes mutable state.
5. **Allocate mutable defaults separately for each call or instance.** A
   function default or mutable class attribute can carry changes into the next
   otherwise independent use.
6. **Create each independent child separately when constructing collections.**
   Repeating a list repeats references to its elements, not copies of them.
7. **Copy domain data explicitly when generic deep copying has unclear
   semantics.** Custom copying hooks and objects representing external
   resources prevent a blanket promise of independence.
8. **Keep shared mutation explicit when a live view is the intended contract.**
   Replacing it with a snapshot silently changes when consumers see updates.

For values used as collection keys, apply the stability rules in
[Equality and Ordering](../data/equality-and-ordering.md).
For handle ownership, see [Resource Lifecycle](resource-lifecycle.md); for
coordinating shared mutation, see
[Concurrency and Shared State](concurrency-and-shared-state.md).

## Anti-patterns

**"The dictionary is copied, so this edit is local."** Copying the envelope is
cheap and looks defensive, but it leaves its children shared. For a schema with
one list of string labels, copy that list too:

```python
source = {"labels": ["queued"]}
# WRONG: the new dictionary still points to source["labels"].
edited = source.copy()
edited["labels"].append("ready")  # Also changes source.

# RIGHT: copy the mutable child before editing it.
edited = {**source, "labels": list(source["labels"])}
edited["labels"].append("sent")  # Leaves source unchanged.
```

**"Frozen means immutable."** Freezing a record prevents ordinary field
assignment, which looks sufficient at the call site. It does not freeze a list
stored in that field. Convert a list of strings to a tuple during construction;
apply the same decision to every nested mutable field.

**"An empty list is a convenient default."** The literal reads like a fresh
empty value, but a function default is evaluated once when the function is
defined. Allocate inside the call when no list was supplied:

```python
# WRONG: omitted arguments share one list across calls.
def collect(item, items=[]):
    items.append(item)
    return items

# RIGHT: omitted arguments get a fresh list; supplied lists are mutated.
def collect(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items
```

**"Repeat the empty row to initialize the grid."** Repetition is concise, but
`rows = [[]] * count` gives every slot the same list. Use
`rows = [[] for _ in range(count)]` when each row must change independently.

**"Deep copy removes every alias."** Recursive copying appears to provide
universal isolation. It can copy too much, and its memoization preserves shared
children within the copied graph. Rebuild independent children separately when
that is your requirement; specify custom objects' copying behavior explicitly.

## What it costs

Copying adds allocation and work proportional to the data you duplicate.
Immutable snapshots make updates require new values. Copy only the state that
must be independent, and share immutable children deliberately. Ownership
transfer can avoid a copy, but in Python it depends on callers honoring the
agreement to stop using retained mutable references.

## Review questions

- Does this function borrow, copy, or take ownership of each mutable argument?
- Can changing the original input after this call change retained state?
- Can changing a returned value bypass this object's mutation methods?
- Which mutable children remain shared after this copy?
- Does this immutable wrapper contain any mutable values?
- Do two calls, instances, or collection slots share a default unintentionally?
- Does this consumer need a snapshot or a live view?

## How to mechanize

**Lint — reject shared mutable defaults.** Fail the build on function defaults
that are list, dictionary, or set literals, including mutable literals nested
inside tuples, and calls to their empty constructors. Check instance fields
for mutable class-level initializers; require per-instance construction or a
default factory, with an explicit exemption for intentional class state.

Python's ordinary type annotations do not express exclusive ownership or prove
that no other reference can mutate a value. A read-only interface limits
operations through that interface; it does not freeze the underlying object.
Those type-level guarantees are therefore unavailable for arbitrary mutable
objects in this sheet's Python setting.

The lint check catches the specified initialization patterns, not arbitrary
aliasing. Verify the remaining boundary contract with generated nested inputs:
retain an input, mutate its mutable descendants, and assert the owner's state
is unchanged; mutate an exported copy and assert the same. Include repeated
references and two independently constructed owners. Where mutation is
intentional, assert that only the documented owner changes. This behavioral
check supplements lint; neither proves isolation for every object graph.

## References

- Python Software Foundation, *Python 3 Library Reference*, "copy — Shallow and
  deep copy operations" — assignment, shallow copies, deep-copy memoization,
  custom copying hooks, and unsupported object kinds.
- Python Software Foundation, *Python 3 Library Reference*, "dataclasses — Data
  Classes", "Frozen instances" and "Default factory functions" — emulated
  immutability and fresh mutable field defaults.
- Python Software Foundation, *Python 3 Tutorial*, "More Control Flow Tools",
  "Default Argument Values" — evaluation of defaults at function definition.
- Python Software Foundation, *Python 3 Tutorial*, "Classes", "Class and
  Instance Variables" — shared mutable class attributes.
- Python Software Foundation, *Python 3 Library Reference*, "Built-in Types",
  "Common Sequence Operations" — sequence repetition retains element references.
