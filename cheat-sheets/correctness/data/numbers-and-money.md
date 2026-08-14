---
title: Numbers and Money
bug_classes: [float-equality, binary-float-for-currency, integer-overflow, rounding-mode, currency-mismatch]
authority: design
mechanizable: type
maturity: draft
last_reviewed: 2026-08-14
---

# Numbers and Money

## Why review misses it

The wrong code is shorter than the right code and reads as elementary. `total +=
price * quantity` and `if balance == 0` are lines a reviewer scans past, because
the defect is not in the operation but in the type the values arrived in,
declared in a file the diff does not touch. Then the error hides behind size:
one multiplication is accurate to fifteen digits, so unit tests pass, and the
discrepancy surfaces only after thousands of accumulations, or as the cent
reconciliation cannot account for. Test data makes it worse — engineers write
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
4. **Never compare floats with `==`; use a domain-derived tolerance, relative
   rather than absolute above unit scale.** A fixed `1e-9` epsilon is
   meaningless at magnitude 1e12. What `NaN` then does to a comparator is a
   separate problem ([equality-and-ordering](equality-and-ordering.md)).
5. **Round once, at a named boundary, with the mode written at the call site.**
   Intermediate rounding compounds the error, and an unstated mode is whatever
   the language chose.
6. **Round half-even unless a rule or contract mandates otherwise, and never
   substitute truncation.** Half-up biases every tie one way and truncation
   biases every value toward zero; both accumulate linearly.
7. **Split money with an allocation that sums back to the whole.** Dividing 1.00
   three ways gives 0.34, 0.33, 0.33 — distribute the remainder rather than
   losing or minting a cent.
8. **Size integers from the largest value the system can hold, and use checked,
   saturating, or arbitrary-precision arithmetic wherever a fixed width can
   wrap.** Silent wraparound turns a large balance negative; the *units* of a
   duration or tick count are a clock question
   ([time-and-time-zones](time-and-time-zones.md)).
9. **Serialize money as a string plus a currency code, and declare the column
   `DECIMAL`/`NUMERIC` or an integer — never `FLOAT`, `DOUBLE`, or a bare JSON
   number.** Many JSON parsers decode numbers into doubles, destroying a correct
   decimal in transit. **Needs design authority**: both sides must agree the
   wire shape, whose encoding is a format question
   ([text-and-encoding](text-and-encoding.md)).

## Anti-patterns

**"Floats are fine — we round for display."** True of one transaction: the error
is far below a cent, so the rendered figure is right. It stops being true at the
ledger, where thousands of sub-cent errors sum into a reconciliation break.

**"Multiply by 100 and cast to int."** A tidy route to minor units from a price
that arrived as a float. The cast truncates, and the float was already low.

```python
# wrong
int(1.15 * 100)      # 114 — 1.15 is stored as 1.1499999999999999
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

Software decimal arithmetic does not run on the FPU and is materially slower
than hardware floats; integer minor units are as fast as arithmetic gets. For
business software this is not a hot path; where it is, batch in integers rather
than reach back for floats. The real bill is ergonomic. A `Money` type cannot be
added to a raw number, so every boundary — ORM, JSON, template, test fixture —
needs an explicit conversion, and each is somewhere the discipline can leak.
Percentages and tax rates are not money, so you keep two numeric vocabularies
and convert on purpose. And rules 5 through 7 make division a named remainder
policy someone must decide rather than inherit.

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

**Type — reachable, and this is where the work belongs.** Model money as an
immutable value carrying integer minor units and a currency, with arithmetic
that refuses mismatched currencies and no path back to `float`. Mixed-currency
addition, sub-minor-unit amounts, and lossy coercion stop being representable.

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
declare it there. In fixed-width languages, use checked or saturating
operations, not the wrapping defaults.

**Lint — for what the type cannot stop at construction.** Fail the build on
`Decimal` or `Money` built from a float; on `==` between floats; on `round()` in
money paths without an explicit mode; and on migrations declaring `FLOAT`,
`DOUBLE`, or `REAL` for a money column. All are AST or schema rules.

**Property test — for the arithmetic laws.** Generate amounts and split counts;
assert `sum(allocate(total, n)) == total` for every `n`; assert Money addition
is associative and `a + b - b == a` (both hold for exact integers and fail for
floats, which makes the test a discriminator); assert serialize-then-parse is
the identity.

**Runtime assertion — at the edges the type does not own.** Reject inbound
amounts that are not whole minor units for their currency, and values exceeding
the declared storage width, before the write rather than after. In a
double-entry system, assert every transaction's legs sum to zero.

**Observation — for the residue only production shows.** Reconcile ledger totals
against external statements and alert on any nonzero residual. Track the signed
sum of rounding adjustments: steady drift one way is a biased rounding mode, not
noise.

## References

- U.S. General Accounting Office, [Patriot Missile Defense: Software Problem Led to System Failure at Dhahran, Saudi Arabia](https://www.gao.gov/products/imtec-92-26) (GAO/IMTEC-92-26, B-247094, 1992) — a chopped 24-bit constant for one tenth drifted the clock ~0.34 s over ~100 hours of uptime; 28 died.
- David Goldberg, [What Every Computer Scientist Should Know About Floating-Point Arithmetic](https://dl.acm.org/doi/10.1145/103162.103163), ACM Computing Surveys 23(1), 1991 — representation error, rounding, and inexact comparison.
- [IEEE 754-2019: Standard for Floating-Point Arithmetic](https://ieeexplore.ieee.org/document/8766229) — binary and decimal formats, and the rounding-direction attributes.
- Mike Cowlishaw, [General Decimal Arithmetic](https://speleotrove.com/decimal/) — the specification behind most decimal implementations.
- [PEP 327: Decimal Data Type](https://peps.python.org/pep-0327/) — the case for a decimal type, and its constructor rules.
- [ISO 4217 — Currency codes](https://www.iso.org/iso-4217-currency-codes.html) — the code list and each currency's minor unit.
- ESA, [Ariane 501 — Presentation of Inquiry Board report](https://www.esa.int/Newsroom/Press_Releases/Ariane_501_-_Presentation_of_Inquiry_Board_report) (1996) — an unprotected 64-bit float to 16-bit signed integer conversion.
