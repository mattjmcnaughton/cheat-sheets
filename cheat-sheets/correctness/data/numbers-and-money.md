---
title: Numbers and Money
bug_classes: [float-equality, binary-float-for-currency, integer-overflow, rounding-mode, currency-mismatch]
authority: design
mechanizable: type
maturity: draft
last_reviewed: 2026-09-08
---

# Numbers and Money

## Why review misses it

The wrong code is shorter than the right code and reads as elementary. `total +=
price * quantity` and `if balance == 0` are lines a reviewer scans past, because
the defect is not in the operation but in the type the values arrived in,
declared in a file the diff does not touch. Then the error hides behind size:
small representation errors pass ordinary fixtures but can change a rounding
decision even in one calculation. Test data makes it worse — engineers write
`19.50` and `0.25`, exactly representable in binary, and never `0.10` or `1.15`,
which are not.

## The default

**Represent money as an integer count of minor units paired with an ISO 4217
currency code — never as a binary float — round only at named boundaries with an
explicitly chosen mode, and size integers so they cannot wrap on any value the
system can hold.**

## Rules

1. **Make money a type carrying an amount and a currency, not a bare number.**
   An unlabelled `amount` gets added to another currency, to a rate, or to a
   quantity, and nothing objects.
2. **Store the amount as integer minor units or as a decimal type — never as
   `float`/`double`.** Binary floating point cannot represent most decimal
   fractions, so the value you stored is not the one you wrote.
3. **Take the number of minor units from ISO 4217, per currency.** Two places is
   not universal: JPY has zero, KWD has three.
4. **Use a domain-derived tolerance when comparing approximate results.**
   Combine relative tolerance with an absolute tolerance near zero; reserve exact
   equality for cases where exact represented values are the intended contract. What `NaN` then does to a comparator is a
   separate problem ([equality-and-ordering](equality-and-ordering.md)).
5. **Round once, at a named boundary, with the mode written at the call site.**
   Keep intermediate precision sufficient for the calculation; decimal arithmetic
   also rounds when its context precision is exhausted.
6. **Round half-even unless a rule or contract mandates otherwise, and never
   substitute truncation.** Half-even avoids consistently rounding ties away from zero; it does not
   guarantee unbiased totals for every input distribution.
7. **Split money with an allocation that sums back to the whole.** Dividing 1.00
   three ways gives 0.34, 0.33, 0.33 — distribute the remainder rather than
   losing or minting a cent.
8. **Size integers from the largest value the system can hold, and use checked
   or arbitrary-precision arithmetic wherever a fixed width can
   wrap.** Silent wraparound turns a large balance negative; the *units* of a
   duration or tick count are a clock question
   ([time-and-time-zones](time-and-time-zones.md)).
9. **Serialize money as a string plus a currency code, and declare the column
   `DECIMAL`/`NUMERIC` or an integer — never `FLOAT`, `DOUBLE`, or a bare JSON
   number.** Many JSON parsers decode numbers into doubles, destroying a correct
   decimal in transit. **Needs design authority**: both sides must agree the
   wire shape, whose encoding is a format question
   ([text-and-encoding](text-and-encoding.md)).

For error introduced by approximate algorithms, use
[Numerical Stability](../execution/numerical-stability.md).

## Anti-patterns

**"Floats are fine — we round for display."** Small errors look harmless, but
a value near a rounding boundary can produce the wrong cent in one transaction.
Parse the decimal input exactly before calculation and apply the named policy.

**"Multiply by 100 and cast to int."** A tidy route to minor units from a price
that arrived as a float. The cast truncates, and the float was already low.

```python
# wrong
int(1.15 * 100)      # 114 — the product is slightly below 115
round(2.675, 2)      # 2.67 — the stored value is below the tie

# right
int(Decimal("1.15").scaleb(2))                               # 115
Decimal("2.675").quantize(Decimal("0.01"), ROUND_HALF_EVEN)  # 2.68
```

**"`Decimal` everywhere, constructed from what we have."** Adopting a decimal
type is the right move, and `Decimal(0.1)` looks like it does it. It preserves
the binary error exactly, to fifty digits. Construct from strings and integers.

**"64 bits is enough for anyone."** True of any one balance, false of the
aggregate: minor units of a low-denomination currency, summed across a large
book, reach the width far sooner than any single value suggests.

## What it costs

Decimal arithmetic and arbitrary-precision integers have different costs from
hardware floats; benchmark your actual hot path before choosing a
representation. The real bill is ergonomic. A `Money` type cannot be added to a
raw number, so every boundary — ORM, JSON, template, test fixture — needs an
explicit conversion, and each is somewhere the discipline can leak. Percentages
and tax rates are not money, so you keep two numeric vocabularies and convert
on purpose. And rules 5 through 7 make division a named remainder policy
someone must decide rather than inherit.

## Review questions

- Is this value money? If so, what type is it, and where is its currency?
- Does a float ever touch it between request and database — including the JSON
  parser and the column type?
- Where does rounding happen, how many times, and in which mode — written here,
  or inherited?
- When this amount is split or prorated, do the parts sum back to the original?
- What is the largest value this integer can hold, and what happens one above
  it?
- What stops two different currencies being added together on this path?
- Which comparison here is `==` on a float, and what tolerance should it be?

## How to mechanize

**Type — prevent mixing money with unrelated quantities.** Require a `Money`
parameter instead of a bare number and run a static type checker. Integer fields
exclude fractional units in checked code. A runtime currency string does not
make currency mismatches unrepresentable: validate currencies and amounts at
input, then reject mismatched addition at runtime. Python annotations alone do
not validate constructor arguments.

```python
@dataclass(frozen=True)
class Money:
    minor_units: int      # exact; no float enters
    currency: str         # ISO 4217 alpha code

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise CurrencyMismatch(self.currency, other.currency)
        return Money(self.minor_units + other.minor_units, self.currency)

    def __float__(self) -> float:      # refuse the lossy exit
        raise TypeError("Money is not a float")
```

Overflow is what the type cannot carry in Python, whose `int` is arbitrary
precision: the width constraint lives at the storage and wire boundary, so
declare it there. In fixed-width languages, use checked
operations; saturation silently changes the amount and is unsuitable for money.

**Lint — for what the type cannot stop at construction.** Fail the build on
`Decimal` or `Money` built from a float; on approximate-result comparisons
lacking a tolerance; on `round()` in money paths without an explicit mode; and
on migrations declaring `FLOAT`, `DOUBLE`, or `REAL` for a money column. All
are AST or schema rules.

**Property test — for the arithmetic laws.** Generate amounts and split counts;
assert `sum(allocate(total, n)) == total` for every positive `n`; assert
same-currency addition is associative and subtraction reverses addition when
all intermediate values fit the declared limits; assert serialize-then-parse is
the identity.

**Runtime assertion — at the edges the type does not own.** Reject inbound
amounts that are not whole minor units for their currency, and values exceeding
the declared storage width, before the write rather than after. In a
double-entry system, assert each transaction balances per currency under the
ledger's accounting rules.

**Observation — for the residue only production shows.** Reconcile ledger
totals against external statements and alert on any nonzero residual. Track the
signed sum of rounding adjustments: investigate sustained drift against the
intended rounding and allocation policy.

## References

- U.S. General Accounting Office, *Patriot Missile Defense: Software Problem Led to System Failure at Dhahran, Saudi Arabia* (GAO/IMTEC-92-26, B-247094, 1992) — a chopped 24-bit constant for one tenth drifted the clock ~0.34 s over ~100 hours of uptime; 28 died.
- David Goldberg, *What Every Computer Scientist Should Know About Floating-Point Arithmetic*, ACM Computing Surveys 23(1), 1991, DOI 10.1145/103162.103163 — representation error, rounding, and inexact comparison.
- IEEE 754-2019, *Standard for Floating-Point Arithmetic* — binary and decimal formats, and the rounding-direction attributes.
- Mike Cowlishaw, *General Decimal Arithmetic* — the specification behind most decimal implementations.
- Python 3 documentation, `math.isclose` and `decimal` — combined tolerances and context precision.
- PEP 327, *Decimal Data Type* — the case for a decimal type, and its constructor rules.
- ISO 4217, *Currency codes* — the code list and each currency's minor unit.
- ESA, *Ariane 501 — Presentation of Inquiry Board report* (1996) — an unprotected 64-bit float to 16-bit signed integer conversion.
