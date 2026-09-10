---
title: Numerical Stability
bug_classes: [catastrophic-cancellation, intermediate-overflow, accumulation-error, ill-conditioned-result, unjustified-tolerance]
authority: design
mechanizable: property-test
maturity: draft
last_reviewed: 2026-09-10
---

# Numerical Stability

## Why review misses it

Two formulas are equal over real numbers and look interchangeable in a diff.
Finite-precision evaluation can lose information in one formula before the
final operation runs. Small, well-scaled fixtures hide overflow, cancellation,
and accumulation of rounding error. A result with many displayed digits looks
precise even when the input uncertainty permits very few trustworthy digits.

## The default

**Choose an algorithm that preserves the required accuracy across the supported
input range, and check its result against an explicit error budget using an
independent higher-precision or exact reference where practical.**

## Rules

1. **Define the acceptable output error in domain units.** **Needs design
   authority:** choose absolute and relative allowances from the caller's
   decision, with an absolute allowance near zero, rather than adopting a
   convenient library default.
2. **Distinguish input sensitivity from algorithmic error.** A poorly
   conditioned problem amplifies small input changes even with a stable
   algorithm; report that limitation rather than promising unsupported digits.
3. **Use primitives designed for the expression you need.** Compute small
   changes with `log1p(x)` or `expm1(x)` instead of forming `1 + x` or
   subtracting `1` after rounding has erased the change.
4. **Avoid subtracting nearly equal approximations when an equivalent stable
   formulation exists.** The subtraction can expose errors already present in
   its operands; changing the final rounding mode cannot restore lost digits.
5. **Scale intermediate computations before they overflow or underflow.** A
   representable final answer does not make every intermediate representable;
   use a scaled norm calculation such as `hypot` rather than squaring first.
6. **Use an accurate summation method when the error budget needs it.**
   Account for dynamic range and cancellation among terms; `math.fsum` improves
   floating-point summation but does not repair errors in the terms themselves.
7. **Validate exceptional values and domain restrictions explicitly.** Decide
   how to handle nonfinite inputs, singular problems, and out-of-domain values
   before they become ordinary-looking output or comparisons that never pass.
8. **Recheck accuracy when changing precision or evaluation order.** Parallel
   reductions and algebraic refactors may alter rounding; preserve the stated
   error budget, and require bitwise reproducibility only when the contract
   actually calls for it.

Use [Numbers and Money](../data/numbers-and-money.md) to choose exact monetary
representation and rounding boundaries; this sheet governs approximate
computation after you have chosen the representation.

## Anti-patterns

**"The elementary formula is clearer."** A direct expression can round away
the small quantity it intends to measure. Use the specialized operation.

```python
import math

x = 1e-16
# Wrong: 1 + x rounds to 1.0 in binary64 arithmetic.
change = math.log(1 + x)       # 0.0
# Right: preserve the small increment during evaluation.
change = math.log1p(x)         # approximately 1e-16
```

**"The final answer fits, so intermediates fit."** Squaring large coordinates
can overflow even when their norm is representable. Use the scaled primitive.

```python
x = y = 1e200
# Wrong: the squared intermediates overflow to infinity.
distance = math.sqrt(x * x + y * y)
# Right: avoid those overflowing intermediates.
distance = math.hypot(x, y)    # approximately 1.4142e200
```

**"Add more tolerance until the test passes."** That hides either an unstable
algorithm or an unrealistic requirement. Compare against an independent
reference, identify where error enters, and change the algorithm or explicitly
renegotiate the domain's accuracy requirement.

**"Use more precision after the calculation."** Converting an already rounded
result cannot recover information. Raise precision before the sensitive
operations and preserve the intended input values; if the inputs themselves
are uncertain, report the sensitivity that remains.

## What it costs

Accurate summation and higher precision may require more computation and
storage. Stable formulas can be less recognizable than textbook expressions,
so name the quantity and explain the sensitive regime. A reference calculation
needs its own precision analysis. Some inputs cannot support the requested
accuracy without better measurements or a different problem formulation;
rejecting or flagging them is part of the interface design.

## Review questions

- What absolute and relative error does the caller permit for this result?
- Can intermediate values overflow, underflow, or erase a small difference?
- Is this failure caused by the algorithm or by sensitivity in the input?
- Does the chosen primitive preserve accuracy in the difficult regime?
- Does the reference calculation begin with the same intended input values?
- Are nonfinite values and singular or out-of-domain cases handled explicitly?
- Does this refactor change summation order or working precision?

## How to mechanize

**Property test — compare difficult inputs against an independent reference.**
Generate finite values over the supported exponent range, including mixed
signs, near cancellation, and values near domain boundaries. For summation,
construct an exact reference with rational values converted from each binary
float; compare the floating result to that exact sum using the domain's error
allowance. This checks arithmetic on the represented inputs, not uncertainty
in the original measurements.

For functions without a practical exact reference, use an independent
higher-precision implementation and increase reference precision until its
uncertainty is comfortably below the test allowance. Include analytically
known cases so two implementations do not silently share the same mistake.
Use exact rational comparison of errors where necessary to avoid rounding the
oracle back to the same precision as the implementation under test.

Ordinary float types do not carry an error budget, and a lint rule banning
subtraction or equality cannot distinguish intended operations from unstable
ones. A specialized static numerical analysis can be stronger for a bounded
expression, but the concrete rung here is a generated reference comparison.
Passing sampled cases does not establish stability over the entire domain or
turn uncertain measurements into exact data.

## References

- Nicholas J. Higham, *What Is Numerical Stability?*, August 4, 2020 — forward
  and backward error, conditioning, and the distinction between input
  sensitivity and algorithmic stability.
- David Goldberg, *What Every Computer Scientist Should Know About Floating-Point
  Arithmetic*, ACM Computing Surveys 23(1), 1991, DOI 10.1145/103162.103163 —
  cancellation and reformulation of expressions under finite precision.
- Python Software Foundation, *Python 3 Library Reference*, `math.log1p`,
  `math.expm1`, `math.hypot`, and `math.fsum` — specialized accurate operations
  and documented summation limitations.
- Python Software Foundation, *Python 3 Library Reference*, `fractions.Fraction`
  — exact rational conversion of represented floating-point values.
