---
title: Text and Encoding
bug_classes: [implicit-encoding, normalization-mismatch, lowercase-not-casefold, length-unit-confusion, byte-order-collation]
authority: design
mechanizable: lint
maturity: draft
last_reviewed: 2026-09-08
---

# Text and Encoding

## Why review misses it

Canonically equivalent strings can render identically despite containing
different code points. The defect often lies between two canonicalizers, only
one of which appears in the diff. Simple lowercase ASCII fixtures hide
normalization, folding, and length-unit mistakes because their representations
agree under each choice.

## The default

**Name the encoding explicitly at every boundary — UTF-8 unless a spec says
otherwise — preserve opaque values exactly, and define one canonicalization
policy per human-text field (NFC by default). Use that policy consistently for
identity, an explicit matching policy for search, and locale-aware collation
for human alphabetical ordering.**

## Rules

1. **Name the encoding at every decode and encode.** Defaults depend on the API and runtime configuration, not the data contract;
   Python byte decoding defaults to UTF-8, while file defaults can depend on mode.
2. **Normalize human text to NFC at a named boundary unless its contract says
   otherwise.** Preserve passwords, signatures, and opaque identifiers exactly
   under their protocol. **Needs design authority:** agree canonicalization and
   collision handling for shared identity fields before changing stored keys.
3. **Check that the whole canonicalization pipeline is idempotent, not just each
   step.** NFC is; NFC composed with folding, trimming, and a local rule need
   not be, and a canonicalizer that disagrees with itself on the second
   application has handed one user another user's account. (If trimming can
   empty the value, see [absence-and-emptiness](absence-and-emptiness.md).)
4. **Keep original display text when deriving NFKC lookup keys.**
   Compatibility folding is lossy — `ﬁ` → `fi`, `²` → `2`, `ᴮ` → `B` — so it
   fixes lookups by destroying what the user typed.
5. **Use the specified caseless-matching algorithm, not ad hoc lowercasing.**
   Unicode folding maps `ß` to `ss`; Python `str.lower()` is locale-independent,
   while some other APIs apply locale-specific casing. Specify Turkic tailoring
   when needed and normalize after folding when the key must remain normalized.
6. **Name the length unit and truncate at boundaries appropriate to the output.**
   Protocols and columns specify their own units. Use grapheme clusters for
   display truncation; `👨‍👩‍👧‍👦` has seven code points and 25 UTF-8 bytes but one
   extended grapheme cluster. A byte limit still applies after segmentation.
7. **Sort human-visible lists with a locale-aware collator, passing the locale in
   as an argument.** Code-point order does not implement locale collation; where you
   need a stable machine order, choose it deliberately and say so.
8. **Specify identity, search, and sort separately.** Do not strip accents or
   fold case unless the matching policy requires those distinctions to collapse. Whether the comparator
   that results obeys the comparator laws is
   [equality-and-ordering](equality-and-ordering.md).

For decoding across arbitrary input chunks, use
[Streaming and Incremental Processing](../execution/streaming-and-incremental-processing.md).

## Anti-patterns

**"Just open the file."** Implicit text-file encoding can pass locally and fail
on another runtime configuration. Use `open(path, encoding="utf-8")` for a UTF-8
contract. `data.decode()` already defaults to UTF-8; naming it explicitly records
the contract but does not fix a locale-dependent decoder.

**"Lowercase both sides."** Everyone was taught it, it is one call, and it is
right for ASCII. But it does not implement Unicode caseless matching for `ß`; use the
contract's folding and normalization pipeline.

```python
# wrong: a display transform used as a comparison
if user.name.lower() == query.lower(): ...

# right: canonical caseless matching (Unicode D145)
def caseless(s):
    return unicodedata.normalize("NFD",
        unicodedata.normalize("NFD", s).casefold())
if caseless(user.name) == caseless(query): ...
```

**"`len()` is the length."** The limit says 20 characters and the language has a
`len`, so the check writes itself. But `len` counts code points in Python, UTF-16
code units in JavaScript, and bytes in Go — three answers, none of them what the
user counted in the textbox.

```python
if len(display_name) > 20: reject()             # wrong: code points
if grapheme_count(display_name) > 20: reject()  # right: what the user counts
```

**"Normalize defensively at every layer."** Each layer protects itself, which
feels robust — until one of the canonicalizers that must now agree forever
applies NFKC in the display path and rewrites the user's name.

**"`ORDER BY` gives me sorted."** The configured database collation may look
correct for ASCII fixtures but differ from the requested locale, and when the
database collation and the application sort disagree, a paginated list skips
and repeats rows at each seam.

## What it costs

Normalization, segmentation, and collation require scanning text and consulting
Unicode data. Benchmark repeated sorts before caching collation keys; invalidate
cached keys when the locale or collation version changes.
Grapheme segmentation needs a library plus versioned tables, a deployment
dependency exactly like the tz database
([time-and-time-zones](time-and-time-zones.md)). And the ergonomic bill is
largest: the language gives you one `==` and one `len`, and you now maintain the
discipline that says which of three comparisons and which of three lengths each
site meant.

## Review questions

- Which encoding does this decode assume, and is it named at the call site?
- Where is this text normalized, to which form, and does every writer go
  through it?
- Is this comparison for identity, for search, or for sort — and does the
  transform match?
- Is this `.lower()` display or comparison? If comparison, why not folding?
- This length limit: bytes, code points, or grapheme clusters — and which does
  the user see?
- Can this truncation split a UTF-8 sequence or a grapheme cluster?
- Whose locale orders this list — the request, the profile, or the host?
- If this canonicalizer ran twice instead of once, would it agree with itself?

## How to mechanize

**Type — not reachable, and worth saying why.** Plain string APIs do not
distinguish raw, normalized, and case-folded text. Python does distinguish
`str` from `bytes`, but `bytes` carries no encoding label. A `NormalizedString`
whose only constructor normalizes buys something real: a function demanding one
cannot be handed raw input. It leaks everywhere else — every standard-library
call takes and returns a bare `str`, every serializer parses and emits one,
every format string unwraps it, and callers must explicitly revalidate
bare-string results before wrapping them. Worth it for a few identity-bearing
fields; not a portable ceiling.

**Lint — the ceiling that travels.** In Python, add an AST check requiring an
explicit encoding argument on text `open()`, `bytes.decode()`, and
`str.encode()`. Accept positional arguments and exempt binary file mode. `-X
warn_default_encoding` with `-W error::EncodingWarning` catches implicit file
encodings at runtime, not `encode()`/`decode()` defaults. In designated
text-handling paths, flag `.lower()` or `.upper()` beside `==` or `in`, or as a
dict key, requiring `.casefold()`; `len()` feeding a user-facing length
validator; `[:n]` slicing of text bound for a fixed-width field; `sorted()` on
strings with no `key=` in a display path; and `errors="replace"` on anything
later stored or compared. Scope these AST rules to known calls and fields; they
cannot infer user intent or prove the whole canonicalization pipeline correct.

**Property test — for what a lint cannot see.** Assert
`canonicalize(canonicalize(x)) == canonicalize(x)` over generated Unicode,
including compatibility characters and astral planes, to catch
repeated-application disagreements. For Unicode scalar-value strings under the
declared encoding, assert `decode(encode(x)) == x`. Under canonical-equivalence
identity, assert that precomposed and decomposed pairs compare equal. Assert
that `truncate(s, n)` yields well-formed text of at most `n` grapheme clusters.

**Runtime assertion — at the boundaries.** Assert values are NFC on the way
into storage; validate at the write boundary. Reject ill-formed input rather
than substituting U+FFFD on any field carrying identity. Before inserting a
canonicalized identifier, assert idempotence and enforce a unique constraint on
the canonical key so concurrent registrations cannot bypass a separate
collision check.

**Observation — for what only production knows.** Export the Unicode and CLDR
data versions per process and alert on skew across the fleet; segmentation and
collation change between versions. Count U+FFFD and mojibake signatures (`Ã©`,
`â€™`) in stored text — investigate changes; these strings can also be
legitimate user input.

## References

- Spotify Engineering, *Creative usernames and Spotify account hijacking* (2013) — a non-idempotent username canonicalizer let `ᴮᴵᴳᴮᴵᴿᴰ` fold to `BIGBIRD` on registration and to `bigbird` on password reset, taking over an existing account.
- Unicode Standard 17.0, §3.13, *Default Case Algorithms*, D145 — canonical caseless matching.
- Python 3 documentation, *Built-in Types* — `str.lower`, `str.casefold`, and UTF-8 defaults for byte encoding/decoding.
- UAX #15, *Unicode Normalization Forms* — NFC, NFD, NFKC, NFKD, and what compatibility folding discards.
- UAX #29, *Unicode Text Segmentation* — grapheme cluster boundaries, the "user-perceived character".
- UTS #10, *Unicode Collation Algorithm* — sort keys, strength levels, locale tailoring.
- Unicode Character Database, `CaseFolding.txt` — the folding mappings, including `ß` → `ss` and the Turkic entries.
- RFC 3629, *UTF-8, a transformation format of ISO 10646*.
- PEP 597, *Add optional EncodingWarning*, and PEP 540, *Add a new UTF-8 Mode* — the platform default you cannot rely on, and the lint hook for it.
