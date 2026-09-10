# Correctness / Execution

**Whether the computation finishes within its limits and delivers a usable
result.**

A formula can express the intended answer while its evaluation loses the
required accuracy. A loop can make valid updates without reaching completion.
A parser can accept every complete fixture while failing on the same bytes
delivered in different chunks. These failures live in how work proceeds, grows,
and consumes finite resources.

| Sheet | Bug classes | Highest rung |
|---|---|---|
| [Termination and Progress](termination-and-progress.md) | Non-decreasing loops, cyclic traversals, stalled convergence, starvation, false completion | property test |
| [Algorithmic Complexity and Input Size](algorithmic-complexity-and-input-size.md) | Quadratic scans, hidden materialization, output explosion, unbounded input cost | property test |
| [Bounded Work and Backpressure](bounded-work-and-backpressure.md) | Unbounded backlogs, hidden waiters, fan-out overload, capacity leaks, silent load shedding | property test |
| [Streaming and Incremental Processing](streaming-and-incremental-processing.md) | Chunk-dependent parsing, accepted truncation, lost trailing data, unbounded buffering, premature publication | property test |
| [Numerical Stability](numerical-stability.md) | Cancellation, intermediate overflow, accumulation error, ill-conditioned results, unjustified tolerances | property test |

**Highest rung** is the strongest concrete check described by the sheet,
following the [mechanization ladder](../../../CONTRIBUTING.md#the-mechanization-ladder).
These sheets use generated inputs and operation histories to check progress,
cost, capacity, parsing equivalence, and accuracy. They distinguish those
sampled checks from formal proofs and deployment-specific measurements.

## Where the boundaries run

- **Termination** asks whether the operation reaches completion;
  **Complexity** asks how much work and storage completion requires.
- **Complexity** bounds one computation's cost as its input grows;
  **Bounded Work** governs admission when computations overlap or accumulate.
- **Streaming** preserves meaning across chunk boundaries and finalization;
  [Text and Encoding](../data/text-and-encoding.md) defines how bytes represent
  characters, and **Bounded Work** governs downstream capacity.
- **Numerical Stability** preserves accuracy during approximate computation;
  [Numbers and Money](../data/numbers-and-money.md) defines representation and
  monetary rounding.
- [State](../state/README.md) governs ownership and valid transitions;
  [Contracts](../contracts/README.md) defines what callers observe when execution
  cannot satisfy its promises.

---

[← Correctness](../README.md)
