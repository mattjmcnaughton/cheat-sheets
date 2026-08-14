---
title: Time and Time Zones
bug_classes: [utc-drift, dst-gap, dst-overlap, monotonic-vs-wall, midnight-assumption]
authority: individual
mechanizable: lint
maturity: draft
last_reviewed: 2026-08-13
---

# Time and Time Zones

## Why review misses it

The wrong code and the right code are the same code. `end - start` is arithmetic
a reviewer reads as obviously non-negative, because the property that fails
belongs to the clock, not to the diff. Time zone bugs hide the same way: the
conversion is correct against the tz database as it stands today, and that
database changes several times a year. Test suites make it worse — they run in
UTC, on machines whose clocks never step, on dates chosen for convenience, so
the two hours a year the code is wrong are exactly the hours no test exercises.
Catching this by reading requires simulating a specific instant in a specific
zone in your head.

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
3. **Store future scheduled events as local time plus a zone, not as a
   precomputed UTC instant.** Zone rules change between scheduling and firing,
   and the user meant 09:00 local.
4. **Measure durations, timeouts, and backoff with a monotonic clock.** Wall
   clocks step for NTP corrections, leap seconds, and manual changes.
5. **Resolve DST gaps and overlaps with an explicit policy at each call site.**
   A local time may not exist or may exist twice, and your library's default is
   rarely what your domain wants.
6. **Assume nothing about a day: not that it is 24 hours, not that midnight
   exists, not that a local time is unique.** Each is false somewhere, at least
   twice a year — so express spans as half-open `[start, end)` intervals, which
   tile correctly even when a day is 23 hours long
   ([boundaries-and-ranges](boundaries-and-ranges.md)).
7. **Decide whether you are adding calendar units or physical units, and use
   the matching API.** "One day later" and "86,400 seconds later" differ by an
   hour twice a year. Overflow in the arithmetic itself is a numeric problem
   ([numbers-and-money](numbers-and-money.md)).
8. **Set the process time zone explicitly; never read the host's local zone.**
   Otherwise correctness depends on machine configuration nobody reviews.
9. **Serialize instants as RFC 3339, and when the zone carries meaning,
   annotate it per RFC 9557** (`2026-08-13T09:00:00-04:00[America/New_York]`).
   An offset alone cannot be recomputed after a rule change; rendering for a
   human is a separate, formatting problem
   ([text-and-encoding](text-and-encoding.md)).
10. **Treat the tz database as versioned deployed data, not as part of the
    platform.** It is updated several times a year, and a stale copy is silently
    wrong one region at a time.

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

Near zero at the type level: zone-aware date-time types ship in every major
standard library and cost a few bytes and a lookup. Three real costs. Monotonic
readings are process-local: you cannot persist one, log it as a timestamp, or
compare it across machines, so durations and instants become separate things,
carried separately. Storing local time plus a zone for scheduled events means no
range query on an indexed UTC column tells you what fires next, so you store
both and accept the denormalization. And pinning the tz database makes it a
deployment dependency: someone has to notice releases and ship them, ongoing
work nothing will remind you to do.

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
conversion — Java's `Instant`, `LocalDateTime`, `ZonedDateTime` — use them, and
most of this sheet becomes unrepresentable rather than merely discouraged.
Python cannot reach this rung out of the box: aware and naive values share one
`datetime` type, differing only by a runtime `tzinfo` flag, so `naive - aware`
type-checks and fails at runtime. A wrapper type restores the distinction but
leaks at every stdlib call and serialization boundary — hence a portable ceiling
one rung down.

**Lint — available everywhere, so start here.** Ban the naive constructors and
the wall-clock stopwatch: in Python, `datetime.now()` without `tz=`,
`datetime.utcnow()`, `date.today()`, and `time.time()` for elapsed time; require
`datetime.now(tz=...)` and `time.monotonic()`. Ban parse formats with no offset,
and `datetime.replace(tzinfo=...)` on values from outside the process. A handful
of AST rules against known call names.

**Property test — for arithmetic lints cannot see.** Generate local times around
a known transition (`America/New_York` in March and November,
`Australia/Lord_Howe` for its 30-minute shift); assert local → instant → local
is identity outside the gap and raises inside it. Assert elapsed time is never
negative over clock sequences containing backward steps. Assert "add one day"
then "subtract one day" returns the original local time.

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

- Cloudflare, [How and why the leap second affected Cloudflare DNS](https://blog.cloudflare.com/how-and-why-the-leap-second-affected-cloudflare-dns/) (2017) — the 2017 leap second made an elapsed-time subtraction go negative, panicking a DNS server.
- Microsoft, [Summary of Windows Azure Service Disruption on Feb 29th, 2012](https://azure.microsoft.com/en-us/blog/summary-of-windows-azure-service-disruption-on-feb-29th-2012/) — certificate validity computed as "today, next year" on a leap day.
- Russ Cox, [Proposal: Monotonic Elapsed Time Measurements in Go](https://go.googlesource.com/proposal/+/refs/heads/master/design/12914-monotonic.md) (2017) — why wall and monotonic readings must be separated.
- [RFC 3339: Date and Time on the Internet: Timestamps](https://www.rfc-editor.org/rfc/rfc3339).
- [RFC 9557: Timestamps with Additional Information](https://www.rfc-editor.org/rfc/rfc9557) — the `[Area/Location]` annotation.
- [PEP 495: Local Time Disambiguation](https://peps.python.org/pep-0495/) — `fold`, and a precise statement of the ambiguous hour.
- [IANA Time Zone Database](https://www.iana.org/time-zones) — release notes record the rule changes that invalidate stored offsets.
