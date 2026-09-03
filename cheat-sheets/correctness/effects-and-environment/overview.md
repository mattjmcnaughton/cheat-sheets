---
title: Effects and Environment Overview
bug_classes: [partial-io, non-atomic-side-effect, subprocess-deadlock, duplicate-delivery, configuration-drift, platform-assumption]
authority: design
mechanizable: type
maturity: draft
last_reviewed: 2026-08-15
---

# Effects and Environment Overview

## Why review misses it

The diff shows one call; the environment supplies the missing behavior. A file
write may stop early, a connection may disappear after the peer commits, a
subprocess may block on an unread pipe, and a queue may deliver the same message
again. Tests replace these boundaries with memory, fast loopback calls, known
executables, writable directories, and complete configuration. The happy path
therefore looks indistinguishable from code that assumes too much.

## The default

**Treat every effect as a fallible, repeatable boundary: declare its inputs and
platform assumptions, bound its time and resources, handle partial completion,
and make retries safe before performing it.**

## Rules

1. **Put effects behind narrow interfaces and keep decisions pure.** Make the
   filesystem, clock, network, process runner, queue, configuration, and random
   source explicit dependencies so tests can vary their behavior.
2. **Loop over partial reads and writes, or call an API that promises to.** A
   successful low-level call may transfer fewer bytes than requested; preserve
   the unconsumed suffix and distinguish end-of-stream from temporary absence.
3. **Bound every wait and payload.** Set connection and operation deadlines,
   cap response and file sizes, limit subprocess output, and propagate
   cancellation so a dependency cannot retain workers forever.
4. **Publish files with write–flush–close–rename where the required filesystem
   supports atomic replacement.** Create the temporary file on the same
   filesystem, preserve permissions deliberately, and clean abandoned
   temporaries; do not generalize the guarantee across filesystems.
5. **Use a structured subprocess API without a shell.** Pass an argument vector,
   set the working directory and environment explicitly, consume both output
   streams concurrently, enforce a deadline, and check termination status.
6. **Design network and queue operations for an unknown outcome.** If the reply
   is lost, you cannot know whether the peer acted; attach a stable operation
   key and make the receiver deduplicate or apply the operation idempotently.
   *(Design authority: sender and receiver must share this contract.)*
7. **Acknowledge queued work only after its durable effect commits.** Extend or
   renew leases for long work, expect redelivery, and make handlers safe under
   concurrent delivery.
8. **Validate configuration and dependency capabilities at startup.** Reject
   missing, malformed, contradictory, or unsupported settings before serving;
   log names and safe fingerprints, never secret values.
9. **Probe the deployed assumptions.** Test case sensitivity, rename semantics,
   path and encoding behavior, executable availability, protocol versions, and
   dependency limits in the target runtime rather than inferring them from a
   developer machine.

## Anti-patterns

**“The library call either succeeds or throws.”** High-level APIs often simplify
I/O, but streaming and low-level interfaces legitimately return partial
progress. Treating progress as completion truncates data without an exception.

**“Retry the request on any error.”** Retries improve availability, but a timeout
does not prove the first attempt failed. Retrying a non-idempotent effect can
charge, enqueue, or mutate twice.

**“Use the shell; it handles quoting.”** A shell makes pipelines convenient,
but turns data into syntax, inherits ambient state, and complicates cancellation
and child cleanup. Invoke the executable directly unless shell semantics are
the feature.

**“The container makes environments identical.”** Packaging fixes some files,
not filesystem semantics, CPU architecture, kernel limits, credentials,
network policy, locale, or remote dependency behavior.

**“A successful enqueue means the workflow succeeded.”** Enqueue confirms one
boundary only. Delivery, processing, acknowledgement, and the durable business
effect remain separate and may repeat.

## What it costs

Explicit adapters, idempotency keys, temporary files, startup checks, and fault
tests add code and storage. Deadlines reject work that might eventually finish;
output and payload limits reject unusually large valid inputs. Deduplication
needs retention and cleanup. Pay these costs at the boundary once rather than
scattering environment guesses through domain code.

## Review questions

- Which filesystem, network, process, queue, configuration, or platform
  assumptions does this change introduce?
- What happens after partial progress, end-of-stream, timeout, or cancellation?
- If the caller receives no reply, is retrying this exact operation safe?
- Can output, payload, concurrency, or waiting grow without a bound?
- Does the subprocess inherit a shell, environment, directory, descriptors, or
  credentials it does not need?
- When is queued work acknowledged, and what happens on concurrent redelivery?
- Which startup check proves the deployed dependency supports this behavior?

## How to mechanize

**Type — model effects and outcomes explicitly.** Return a result that separates
complete, partial, timed-out, cancelled, and unknown outcomes; require an
`OperationKey` for retryable mutations and a validated configuration type for
runtime settings. Types cannot prove remote idempotency or platform semantics.

**Lint — reject dangerous syntax.** Fail the build on shell-enabled subprocess
calls, unbounded network calls, ignored write counts and process statuses,
ambient temporary paths, and direct environment reads outside the configuration
adapter.

**Property test — inject hostile boundaries.** Generate short reads and writes,
disconnect after each byte, duplicate and reorder deliveries, and cancel at
every await point. Assert that output is complete or explicitly failed and that
replaying one operation key changes durable state at most once.

**Runtime assertion — validate before use.** Parse all configuration at startup,
assert payload and output limits while streaming, and reject acknowledgements
before the durable commit marker exists.

**Observation — expose boundary outcomes.** Count timeouts, retries,
redeliveries, deduplication hits, partial transfers, subprocess exits, startup
check failures, and abandoned temporary files; alert on sustained drift from the
normal baseline.

## References

- The Open Group, [`write()`](https://pubs.opengroup.org/onlinepubs/9799919799/functions/write.html) — partial writes, interruption, and error semantics.
- The Open Group, [`rename()`](https://pubs.opengroup.org/onlinepubs/9799919799/functions/rename.html) — atomic replacement guarantees and filesystem limits.
- Python, [`subprocess` — Subprocess management](https://docs.python.org/3/library/subprocess.html) — argument vectors, pipe deadlocks, timeouts, and status handling.
- [RFC 9110 §9.2.2, Idempotent Methods](https://www.rfc-editor.org/rfc/rfc9110#section-9.2.2) — retry consequences when a response is lost.
- POSIX, [Environment Variables](https://pubs.opengroup.org/onlinepubs/9799919799/basedefs/V1_chap08.html) — process environment representation and inherited variables.
- Unicode Consortium, [Unicode Standard Annex #15: Normalization Forms](https://unicode.org/reports/tr15/) — why visually equivalent path strings can have different code-point sequences.
