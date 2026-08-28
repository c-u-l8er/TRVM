# Upstream RFC 8785 reference vectors — COMPLETE for the applicable suite

`input/<name>.json` is fed to the canonicaliser; the result must equal the octets in
`outhex/<name>.txt`, which is ASCII hexadecimal.

## Provenance

```
repository   github.com/cyberphone/json-canonicalization
path         testdata/
commit       19d51d7fe467d4706a3ff08adf8a748f29fc21e0   (2024-12-13)
```

All six vectors of the upstream `testdata/input/` set are present: `arrays`, `french`,
`structures`, `unicode`, `values`, `weird`. `values` is also RFC 8785 sections 3.2.2 / 3.2.3
verbatim.

## Why `outhex` and not `output`

P4.3 and P4.4 could not import `weird` and `unicode` because their expected output contains
unescaped U+0080, U+007F and a combining mark, and no text channel available to this tree could be
shown to have preserved them byte for byte. **A conformance vector that might be wrong is worse than
one that is narrow**, so they were declared open rather than guessed.

Upstream publishes `testdata/outhex/`, which states the expected canonical output as ASCII
hexadecimal. That is the transport-safe representation the problem needed, and it is a strictly
better test boundary than comparing decoded text: the comparison is against octets.

`outhex/{arrays,unicode,weird}.txt` are upstream verbatim. `outhex/{french,structures,values}.txt`
are the hex of the `output/*.json` files imported at P4.3, kept so that **every** vector is compared
as octets rather than some as text.

## Why the inputs carry `\u` escapes

`input/weird.json` upstream contains literal `€`, `😂`, `ö` and a Hebrew letter. Those are re-expressed
here as `\u20ac`, `\ud83d\ude02`, `\u00f6` and `\ufb33` — **the same JSON value**, since an escape
and a literal denote one string, and transport-safe. The code points were read from the authoritative
`outhex` bytes rather than from a rendering of the file, and the round trip is what proves them: if a
single escape were wrong the canonical output would not equal the upstream octets. `input/unicode.json`
already used escapes upstream.

## What is established, and what is not

Six vectors covering member ordering by UTF-16 code unit (including an empty key, numeric-looking
keys, a surrogate pair that must sort before U+FB33, and an escaped newline as a key), ECMAScript
number serialisation, string escaping, unescaped C1 controls and U+007F, combining marks preserved
without normalisation, and array/structure nesting.

This is the whole of upstream `testdata/input/`. It is **not** the ~100M-case ECMAScript number
stress corpus that project also publishes, and that remains a separately described strengthening
target rather than a silent omission.
