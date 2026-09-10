---
title: Time and Time Zones
bug_classes: [utc-drift, dst-gap, dst-overlap, monotonic-vs-wall, midnight-assumption]
authority: design
mechanizable: lint
maturity: draft
last_reviewed: 2026-09-08
---

# Time and Time Zones

## Why review misses it

`end - start` looks like harmless arithmetic, but its meaning depends on the
clock and time-zone semantics. A conversion can also become wrong after a zone
rule update. Tests running only in UTC, away from transitions and clock
corrections, leave those dependencies invisible to a reviewer.

## The default

**Store and compute instants in UTC; carry an IANA time zone identifier
alongside any time a human reads or a business rule depends on; and measure
elapsed time with a monotonic clock, never by subtracting two wall-clock
readings.**

## Rules

1. **Represent a moment as an instant in UTC and a calendar time as a local
   date-time plus a zone identifier — never let one stand in for the other.**
   They are different kinds of value, and a type that blurs them gets converted
   at the wrong boundary.
2. **Never store a fixed UTC offset as a substitute for a zone.** `-05:00` is a
   fact about one moment; `America/New_York` survives the next rule change. An
   absent zone is absent, not UTC — see
   [absence-and-emptiness](absence-and-emptiness.md).
3. **Store a future civil-time schedule as local time plus a zone and resolution
   policy.** Keep a UTC instant when that is the promised deadline instead.
   **Needs design authority:** agree which value is authoritative and how zone
   updates affect pending events.
4. **Measure durations, timeouts, and backoff with a monotonic clock.** Wall
   clocks step for NTP corrections, leap seconds, and manual changes.
5. **Resolve DST gaps and overlaps with an explicit policy at each call site.**
   A local time may not exist or may exist twice, and implicit library behavior does not document your domain's choice.
6. **Assume nothing about a day: not that it is 24 hours, not that midnight
   exists, not that a local time is unique.** Transitions can invalidate each assumption — express spans as half-open `[start, end)` intervals, which
   tile correctly even when a day is 23 hours long
   ([boundaries-and-ranges](boundaries-and-ranges.md)).
7. **Decide whether you are adding calendar units or physical units, and use
   the matching API.** Across an offset transition, a calendar day need not equal 86,400 seconds.
   In Python, convert aware datetimes to UTC before adding physical durations
   or subtracting instants: arithmetic with the same `tzinfo` uses wall fields. Overflow in the arithmetic itself is a numeric problem
   ([numbers-and-money](numbers-and-money.md)).
8. **Set the process time zone explicitly; never read the host's local zone.**
   Otherwise correctness depends on machine configuration nobody reviews.
9. **Serialize instants as RFC 3339, and when the zone carries meaning,
   annotate it per RFC 9557** (`2026-08-13T09:00:00-04:00[America/New_York]`).
   An offset alone cannot be recomputed after a rule change; rendering for a
   human is a separate, formatting problem
   ([text-and-encoding](text-and-encoding.md)).
10. **Treat the tz database as versioned deployed data, not as part of the
    platform.** Track releases and deploy relevant rule changes before affected events fire.

For dependencies between distributed events, use
[Ordering and Causality](../state/ordering-and-causality.md).

## Anti-patterns

**"Store local time, convert on read."** The reasoning is sound: users think in
local time, and storing what they typed avoids a lossy conversion. But every
consumer must then know the zone, and the ambiguous hour each autumn has two
valid answers with nothing recorded to pick between them.

**"UTC everywhere, including display and scheduling."** UTC fixed a real class
of bugs, so it gets applied to everything. Then a recurring 09:00 standup stored
as `13:00Z` starts arriving at 08:00 local the week the clocks change: the
user's intent was a wall time and you stored an instant.

**"The offset is the time zone."** An ISO string carries `+02:00`, so it looks
complete. It identifies the moment correctly and says nothing about what that
clock will read next March.

**"Normalize to midnight."** Truncating to the start of the day makes date
comparisons clean. In zones where DST transitions at midnight, the day starts at
01:00 and your normalized value is a local time that never happened.

**"Retry after five seconds," on the wall clock.** Sleeping until `now() + 5s`
reads naturally and is right almost always. When NTP steps the clock backwards
during an incident, the retry loop stalls for the length of the step — exactly
when you need it.

## What it costs

Separate types and time-zone lookups add representation and operational costs.
Monotonic readings have a clock-specific origin: do not treat them as portable
timestamps or compare them across machines or reboots. Check your clock API for
cross-process and suspend behavior, so durations and instants become separate
things, carried separately. Storing local time plus a zone for scheduled events
can require a derived UTC firing index; recompute that index when relevant zone
rules change. And pinning the tz database makes it a deployment dependency:
someone has to notice releases and ship them, ongoing work nothing will remind
you to do.

## Review questions

- Which of these values is an instant and which is a wall time — does the type
  say so, or only the variable name?
- What does this do on the night the local clock repeats 01:30, and the morning
  it skips 02:30?
- Is this duration monotonic, or two subtracted wall-clock readings?
- For this scheduled event, are we storing a UTC instant or a local time plus a
  zone — and which did the user mean?
- Where does the zone come from: the request, the user's profile, or whatever
  the host is set to?
- If tz rules change for this region next month, which stored rows become wrong,
  and how would we find out?
- Does "today" here mean the user's today or the server's?

## How to mechanize

**Type — partially available; take it where it exists.** Where the standard
library models instants and local date-times as distinct types with no implicit
conversion — Java's `Instant`, `LocalDateTime`, `ZonedDateTime` — use them, to
prevent accidental interchange. They do not determine gap policies or preserve
scheduling intent automatically. For the Python checks below, this rung is
unavailable out of the box: aware and naive values share one `datetime` type,
differing only by a runtime `tzinfo` flag, so `naive - aware` type-checks and
fails at runtime. A wrapper type restores the distinction but leaks at every
stdlib call and serialization boundary — hence a portable ceiling one rung
down.

**Lint — enforce the chosen Python clock APIs.** Ban the naive constructors and
the wall-clock stopwatch: in Python, `datetime.now()` without `tz=`,
`datetime.utcnow()`, `date.today()`, and `time.time()` for elapsed time;
require `datetime.now(tz=...)` and `time.monotonic()`. In instant-handling
code, reject offset-free parses and zone attachment with `replace(tzinfo=...)`;
civil-time parsing needs a separate validated resolver. A handful of AST rules
against known call names.

**Property test — for arithmetic lints cannot see.** Generate local times
around a known transition (`America/New_York` in March and November,
`Australia/Lord_Howe` for its 30-minute shift); test your resolver, not just
`datetime` construction: reject gaps when that is the policy, and verify both
overlap choices map to the intended UTC instants. Python zone attachment does
not itself reject nonexistent local times. Assert elapsed time is never
negative over clock sequences containing backward steps. Assert calendar
arithmetic against the selected gap/overlap policy; shifting a nonexistent time
can make add-then-subtract non-invertible.

**Runtime assertion — at the boundaries.** Reject naive date-times arriving from
deserialization and leaving for storage. Assert every measured duration is
non-negative rather than letting one reach a sleep, a rate limiter, or a random
bound. A negative duration that flows onward surfaces as a panic in unrelated
code; caught at the source, it is a labelled error naming the clock.

**Observation — for what only production knows.** Export the tz database version
per process; alert on skew across the fleet or age past a few months. Reconcile
scheduled jobs against intended local times on transition days, and alert on any
that fired twice or not at all.

## References

- Cloudflare, *How and why the leap second affected Cloudflare DNS* (2017) — the leap second at the end of 2016 made an elapsed-time subtraction go negative, panicking a DNS server.
- Microsoft, *Summary of Windows Azure Service Disruption on Feb 29th, 2012* — certificate validity computed as "today, next year" on a leap day.
- Russ Cox, *Proposal: Monotonic Elapsed Time Measurements in Go* (2017) — why wall and monotonic readings must be separated.
- RFC 3339, *Date and Time on the Internet: Timestamps*.
- RFC 9557, *Timestamps with Additional Information* — the `[Area/Location]` annotation.
- Python 3 documentation, `datetime` — same-zone arithmetic and conversion to UTC.
- Python 3 documentation, `time.monotonic` — clock origin, cross-process behavior, and platform details.
- PEP 495, *Local Time Disambiguation* — `fold`, and a precise statement of the ambiguous hour.
- IANA, *Time Zone Database* — release notes record the rule changes that invalidate stored offsets.
