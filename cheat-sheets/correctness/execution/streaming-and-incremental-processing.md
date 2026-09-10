---
title: Streaming and Incremental Processing
bug_classes: [chunk-dependent-parsing, truncated-stream-acceptance, lost-trailing-data, unbounded-parser-buffer, premature-publication]
authority: design
mechanizable: property-test
maturity: draft
last_reviewed: 2026-09-10
---

# Streaming and Incremental Processing

## Why review misses it

Tests hand a complete record to a method named `feed`. In production, a read
ends in the middle of a length prefix, delimiter, compressed block, or record.
Conversely, a read can contain several records. The parser looks correct for
each fixture because the fixture's chunk boundary supplies framing that the
format itself must supply. Partial output can also look valid before the
stream's final integrity check fails.

## The default

**Parse with persistent state and explicit end-of-input handling so every
partition of the same bytes yields the same records or failure; bound retained
state and publish only at the format's agreed validation boundary.**

## Rules

1. **Take record boundaries from the format, never from read boundaries.** A
   transport read supplies available bytes, not necessarily one application
   message.
2. **Retain incomplete parser state across feeds.** Preserve partial headers,
   tokens, and delimiters; delegate character decoding to an incremental
   decoder as described in [text and encoding](../data/text-and-encoding.md).
3. **Distinguish an empty feed, temporary lack of data, and end of input.**
   Interpret them according to the transport API; invoke an explicit parser
   finalization step only when the input is complete.
4. **Reject incomplete framing at end of input.** A parser that emitted useful
   records may still hold a partial final record or lack a required trailer;
   finalization must report that state.
5. **Preserve bytes beyond the current record or compressed member.**
   **Needs design authority:** specify whether trailing data starts another
   member, belongs to another protocol phase, or is invalid.
6. **Bound record size, nesting, and expansion before buffering them.** A
   missing delimiter must produce an oversized-record failure rather than
   unlimited accumulation; bound decompressed output separately from input.
7. **Define when emitted records become committed effects.** **Needs design
   authority:** stage output until stream-level checks pass when the whole
   stream is atomic, or specify independently validated records and partial
   success explicitly.
8. **Keep downstream consumption incremental too.** Accumulating all emitted
   records in a list defeats bounded processing; propagate capacity constraints
   using [backpressure](bounded-work-and-backpressure.md).

## Anti-patterns

**"Split every received chunk into lines."** It works when writes and reads
line up, but a record can span reads or a delimiter can straddle them. Keep the
unfinished suffix between feeds and extract complete framed records from the
accumulated state, enforcing a record-size cap along the way.

**"No exception means decompression succeeded."** A truncated compressed
stream can produce a valid-looking prefix without reaching its end marker.
For an already size-bounded, single-member input, check completion and trailing
data explicitly. Use output limits as well for untrusted compressed input.

```python
import zlib

# Wrong: accepts output without checking stream completion.
output = zlib.decompressobj().decompress(data)

# Right for a size-bounded, single-member input.
decoder = zlib.decompressobj()
output = decoder.decompress(data)
if not decoder.eof or decoder.unused_data:
    raise ValueError("incomplete stream or trailing data")
```

**"Use the advertised length to allocate the buffer."** A length prefix avoids
delimiter scanning but is still untrusted input. Validate its range before
allocation, reject lengths above the supported maximum, and retain at most the
bounded unread suffix while waiting for the remainder.

**"Write each decoded record immediately."** This keeps memory low but makes
whole-stream rollback impossible after a bad trailer. Stage records until the
required validation completes, or expose partial acceptance as part of the
contract; use [intermediate-step invariants](../state/invariants-across-intermediate-steps.md)
for the publication boundary.

## What it costs

An incremental parser owns state, limits, and a finalization protocol. Whole
stream validation may require temporary storage and delayed publication.
Partition testing adds many cases from a small input, so exhaust small examples
and sample larger ones. A supported maximum record size is an interface
constraint: callers need to know it before sending a stream that cannot be
accepted.

## Review questions

- What supplies framing when a read ends inside a header or record?
- Does one read containing several records preserve every record and suffix?
- What triggers finalization, and which incomplete states does it reject?
- Are trailing bytes rejected or passed to an explicitly supported next member?
- What bounds partial records, nesting, and expanded output?
- Can an output become externally visible before its required checks pass?
- Does a slower downstream consumer stop further input accumulation?

## How to mechanize

**Property test — vary chunking without changing the stream.** Generate valid
encoded records and partition their bytes into chunks, including single-byte
chunks, empty feeds where the parser API permits them, and multiple records per
feed. Feed each partition to a fresh parser, finalize it, and compare the
complete record sequence to an independent whole-input reference parser.

For invalid input, assert equivalent failure classification regardless of
chunking; error timing can differ. Truncate within required headers, bodies, and
trailers, and assert finalization fails. Do not require every prefix to fail:
some formats permit a shorter complete stream. Add oversize cases and assert
the retained-state budget is never exceeded before rejection. When effects
must be atomic, assert failed finalization leaves no published records.

Types can separate active and finalized parser states, but ordinary Python
types do not establish equivalence across arbitrary byte partitions. A static
pattern rule cannot verify a format's state machine or acceptance language.
Generated partition checks reach the highest concrete rung here; they find
counterexamples rather than proving correctness for all streams.

## References

- Python Software Foundation, *Socket Programming HOWTO*, “Using a Socket” —
  partial sends and receives, application framing, and connection completion.
- Python Software Foundation, *Python 3 Library Reference*, `codecs`,
  “IncrementalDecoder Objects” — persistent decoding state and final buffer
  handling.
- Python Software Foundation, *Python 3 Library Reference*, `zlib`,
  `Decompress.eof`, `unused_data`, `unconsumed_tail`, and `decompress` —
  truncated-stream detection, trailing data, and bounded output calls.
