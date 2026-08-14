---
title: Text and Encoding
bug_classes: [implicit-encoding, normalization-mismatch, lowercase-not-casefold, length-unit-confusion, byte-order-collation]
authority: individual
mechanizable: lint
maturity: draft
last_reviewed: 2026-08-14
---

# Text and Encoding

## Why review misses it

Two strings differing only in normalization render identically in a diff — `é`
as U+00E9 and as U+0065 U+0301 are the same pixels — so the input that breaks
the function is invisible on the page. Worse, the defect is usually a
*disagreement between two call sites*, and only one of them is in the diff:
each canonicalizer is defensible alone, and no reviewer sees both. The test
suite hides the rest, because ASCII is a fixed point of every normalization
form, every case folding, and every length calculation, so a suite full of
`"alice"` passes under every wrong choice here.

## The default

**Name the encoding explicitly at every boundary — UTF-8 unless a spec says
otherwise — normalize to NFC at one place you can point to, and pick the
comparison for the job: exact match for identity, case folding for lookup keys,
a locale-aware collator for anything a human sees ordered.**

## Rules

1. **Name the encoding at every decode and encode.** A platform default is a
   property of the host's locale, not of the data — the same bytes decode
   differently in your terminal, your container, and your CI.
2. **Normalize to NFC once, at the input boundary, and route every writer of the
   field through it.** Formats and databases do not normalize for you, and two
   spellings of one name will not join.
3. **Check that the whole canonicalization pipeline is idempotent, not just each
   step.** NFC is; NFC composed with folding, trimming, and a local rule need
   not be, and a canonicalizer that disagrees with itself on the second
   application has handed one user another user's account. (If trimming can
   empty the value, see [absence-and-emptiness](absence-and-emptiness.md).)
4. **Use NFKC only for keys you compare, never for text you store or return.**
   Compatibility folding is lossy — `ﬁ` → `fi`, `²` → `2`, `ᴮ` → `B` — so it
   fixes lookups by destroying what the user typed.
5. **Case-fold for caseless comparison; lowercase only for display.**
   `"ß".lower()` is `"ß"` but its folding is `"ss"`, and lowercasing is
   locale-sensitive: under a Turkish locale `I` becomes `ı` and an ASCII keyword
   match silently fails.
6. **Say which length you mean — bytes, code points, or grapheme clusters — and
   slice only on grapheme boundaries.** A protocol and a column usually mean
   bytes, a spec field may mean code points, a user always means grapheme
   clusters; the family emoji is one character to them, seven code points, 25
   UTF-8 bytes, and cutting by either of the other two yields mojibake or a
   severed combining mark.
7. **Sort human-visible lists with a locale-aware collator, passing the locale in
   as an argument.** Code-point order is alphabetical in no language; where you
   need a stable machine order, choose it deliberately and say so.
8. **Treat identity, search, and sort as three transforms:** exact match after
   NFC, folding plus accent stripping, and a collator. Whether the comparator
   that results obeys the comparator laws is
   [equality-and-ordering](equality-and-ordering.md).

## Anti-patterns

**"Just open the file."** `open(path).read()` and `data.decode()` read cleanly
and work on every developer machine, because those machines have a UTF-8 locale.
They fail on the host whose locale is `C` or a legacy code page: the same bytes
become different text, silently.

**"Lowercase both sides."** Everyone was taught it, it is one call, and it is
right for ASCII. But it fails on `ß`, it is locale-sensitive, and lowercasing is
a *mapping* built for display, not for matching.

```python
# wrong: a display transform used as a comparison
if user.name.lower() == query.lower(): ...

# right: normalize both sides, then fold
if unicodedata.normalize("NFC", user.name).casefold() \
        == unicodedata.normalize("NFC", query).casefold(): ...
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

**"`ORDER BY` gives me sorted."** Byte order looks sorted for English test data.
It files every accented word after `Z`, and when the database collation and the
application sort disagree, a paginated list skips and repeats rows at each seam.

## What it costs

Normalization is nearly free: ASCII is unchanged by every form, and a quick-check
pass over normalized text is close to a scan. Three real costs. Collation is
expensive next to `memcmp` — a collator builds a sort key per string from
megabytes of locale data, so cache the keys if you sort the same corpus often.
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

**Type — not reachable, and worth saying why.** Almost every language has
exactly one string type, so "raw user input", "NFC-normalized string",
"case-folded key", and "UTF-8 bytes" are the same type and flow into each other
silently. A `NormalizedString` whose only constructor normalizes buys something
real: a function demanding one cannot be handed raw input. It leaks everywhere
else — every standard-library call takes and returns a bare
`str`, every serializer parses and emits one, every format string unwraps it,
and one `.strip()` in the middle yields a bare value that still type-checks.
Worth it for a few identity-bearing fields; not a portable ceiling.

**Lint — the ceiling that travels.** In Python, ban: `open()`, `bytes.decode()`,
and `str.encode()` with no `encoding=` (turn on `EncodingWarning` via
`-X warn_default_encoding` and promote it to an error); `.lower()` or `.upper()`
beside `==` or `in`, or as a dict key, requiring `.casefold()`; `len()` feeding a
user-facing length validator; `[:n]` slicing of text bound for a fixed-width
field; `sorted()` on strings with no `key=` in a display path; and
`errors="replace"` on anything later stored or compared. AST rules over known
call names, catching every anti-pattern above.

**Property test — for what a lint cannot see.** Assert
`canonicalize(canonicalize(x)) == canonicalize(x)` over generated Unicode,
compatibility characters and astral planes included: that one property is the
incident. Assert `decode(encode(x)) == x`, that precomposed and decomposed pairs
compare equal under the identity comparator, and that `truncate(s, n)` yields
well-formed text of at most `n` grapheme clusters.

**Runtime assertion — at the boundaries.** Assert values are NFC on the way into
storage; the quick-check is cheap enough to leave on. Reject ill-formed input
rather than substituting U+FFFD on any field carrying identity. Before inserting
a canonicalized identifier, assert idempotence and check for a collision — the
check that turns an account takeover into a failed registration.

**Observation — for what only production knows.** Export the Unicode and CLDR
data versions per process and alert on skew across the fleet; segmentation and
collation change between versions. Count U+FFFD and mojibake signatures (`Ã©`,
`â€™`) in stored text — any at all means something upstream decoded wrong.

## References

- Spotify Engineering, [Creative usernames and Spotify account hijacking](https://engineering.atspotify.com/2013/06/creative-usernames) (2013) — a non-idempotent username canonicalizer let `ᴮᴵᴳᴮᴵᴿᴰ` fold to `BIGBIRD` on registration and to `bigbird` on password reset, taking over an existing account.
- [UAX #15: Unicode Normalization Forms](https://unicode.org/reports/tr15/) — NFC, NFD, NFKC, NFKD, and what compatibility folding discards.
- [UAX #29: Unicode Text Segmentation](https://unicode.org/reports/tr29/) — grapheme cluster boundaries, the "user-perceived character".
- [UTS #10: Unicode Collation Algorithm](https://www.unicode.org/reports/tr10/) — sort keys, strength levels, locale tailoring.
- [CaseFolding.txt](https://www.unicode.org/Public/UCD/latest/ucd/CaseFolding.txt) — the folding mappings, including `ß` → `ss` and the Turkic entries.
- [RFC 3629: UTF-8, a transformation format of ISO 10646](https://www.rfc-editor.org/rfc/rfc3629).
- [PEP 597: Add optional EncodingWarning](https://peps.python.org/pep-0597/) and [PEP 540: Add a new UTF-8 Mode](https://peps.python.org/pep-0540/) — the platform default you cannot rely on, and the lint hook for it.
