---
title: Termination and Progress
bug_classes: [non-decreasing-loop, cyclic-traversal, stalled-convergence, starvation, false-completion]
authority: design
mechanizable: property-test
maturity: draft
last_reviewed: 2026-09-10
---

# Termination and Progress

## Why review misses it

The happy path changes the loop condition, but an early `continue` does not.
A recursive call handles a smaller example without handling a smaller argument
on every branch. Fixtures use trees while production data contains a cycle.
Each individual step can be valid even though the operation never reaches its
promised result. A passing timeout test only shows that the test runner stops
waiting; it does not establish progress inside the operation.

## The default

**For every operation expected to finish, identify a finite amount of remaining
work that strictly decreases on each step; if progress depends on another
actor, state that dependency and return an explicit incomplete outcome when
your work budget is exhausted.**

## Rules

1. **Write down the exit condition and a well-founded progress measure before
   writing the loop.** A nonnegative integer that strictly decreases cannot
   decrease forever; a value that merely changes can oscillate.
2. **Check the measure on every back edge and recursive branch.** Error
   recovery, skipped records, and early `continue` paths must also advance or
   terminate the operation.
3. **Separate terminating steps from a terminating sequence of steps.** A
   finite iteration count does not help if one iteration waits forever; put
   waiting behavior in the [deadline contract](../contracts/timeouts-and-cancellation.md).
4. **Track visited identities when traversing a finite graph.** Enqueue each
   identity once, rather than treating every outgoing edge as a new object to
   visit; decide whether a cycle means reuse or invalid input.
5. **Keep a finite traversal's input fixed, or define a stopping frontier.**
   **Needs design authority:** a scan of a collection that keeps growing needs
   an agreed snapshot or cutoff, not an assumption that the producer stops.
6. **Bound convergence attempts and detect stagnation.** A tolerance may never
   be reached, and rounding can make the next iterate identical to the current
   one; return failure instead of presenting the last iterate as converged.
7. **State fairness assumptions for ongoing workers.** **Needs design
   authority:** if older work must eventually run, bound how often newer work
   can overtake it and include recurring high-priority arrivals in the model.
8. **Distinguish completion, budget exhaustion, and cancellation in the result.**
   A caller must not treat a stopped search as evidence that no answer exists;
   define these outcomes in [failure semantics](../contracts/error-and-failure-semantics.md).

## Anti-patterns

**"Skipping bad records keeps the batch moving."** A `continue` can bypass the
only increment. Iterate over a finite collection so the skipped path consumes
an item too.

```python
# Wrong: an invalid record leaves i unchanged.
while i < len(records):
    if not valid(records[i]):
        continue
    i += 1

# Right: each pass consumes one record from this fixed list.
for record in records:
    if not valid(record):
        continue
```

**"The recursive version matches the data model."** Parent/child naming makes
cycles easy to overlook. For graph inputs, use an explicit worklist and a
visited set; for promised trees, reject cycles at the boundary. An explicit
stack also avoids tying acceptable depth to the interpreter's call stack.

**"Stop when two approximations become equal."** Equality looks definitive but
may indicate rounding stagnation far from the target. Check the problem's
residual or error criterion, then report nonconvergence if the value stops
changing before that criterion holds. Choose the criterion using
[numerical stability](numerical-stability.md).

**"After enough iterations, return the best answer."** A budget protects
execution, but a partial answer may violate the function's promise. Return a
tagged partial result with its remaining frontier, or raise the agreed failure;
only label it complete when the completion condition holds.

## What it costs

Visited sets retain identities proportional to the reachable graph. Snapshots
or cutoffs require agreement with producers. Explicit incomplete outcomes add
caller branches. A progress argument takes effort, especially for mutually
recursive code, but often exposes a simpler traversal. None of these choices
establishes a wall-clock bound without assumptions about the cost of each step.

## Review questions

- What decreases on every iteration or recursive call in this change?
- Can any skip, recovery, or retry path leave that measure unchanged?
- Can this input contain a cycle, or grow while it is traversed?
- Can an individual step block even if the number of steps is finite?
- What does this operation return when it stops without completing?
- Can a sustained stream of newer work starve an older item?
- Does convergence mean the requested accuracy, or merely no further change?

## How to mechanize

**Property test — check progress and completion against a finite model.**
Generate finite directed graphs including self-loops and disconnected cycles.
Instrument the traversal to count expansions; assert each reachable identity is
expanded once, the result equals a simple reference reachability set, and the
expansion count never exceeds the number of identities. Make the test harness
fail on excess steps so a regression does not hang the suite.

For iterative solvers, generate cases that converge, stagnate, and exceed the
iteration budget. Assert that only results satisfying the convergence criterion
carry a success outcome. These are sampled checks, not a termination proof.

Ordinary Python types do not express decreasing measures, and a syntactic lint
rule cannot establish progress through arbitrary callbacks or external actors.
If the implementation uses a verification language, a static proof of a
well-founded decreasing measure is a higher rung: check all loop and recursive
transitions together with the assumptions that each step terminates. That proof
is stronger than the Python checks described here and still does not establish
an elapsed-time limit.

## References

- Dafny contributors, *Dafny Online Tutorial: Termination*, version 3.10.0 —
  decreasing measures, lower bounds, recursive calls, and intentionally
  nonterminating computations.
- Leslie Lamport, *Specifying Systems*, 2002, chapter 8, “Liveness and
  Fairness” — eventual progress depends on explicit scheduling assumptions.
- Python Software Foundation, *Python 3 Library Reference*, `sys.getrecursionlimit`
  and `sys.setrecursionlimit` — interpreter recursion depth and stack limits.
