# OPEN REQUIREMENT — the ECMAScript number stress corpus

**STATUS: DECLARED-OPEN. Not green, not counted as conformance, and not silently absent.**

## What IS green

The complete upstream `testdata/input/` set — `arrays`, `french`, `structures`, `unicode`, `values`,
`weird` — is imported and every one is compared **as octets** against upstream `outhex`. See
`../../vectors/jcs-upstream/PROVENANCE.md` for the pinned commit. That includes the two vectors
P4.3 and P4.4 had to declare open: `weird` (unescaped U+0080 and U+007F) and `unicode` (a combining
mark preserved without normalisation).

## What is still open

The reference project also publishes a generated corpus of on the order of 10^8 ECMAScript
number-serialisation cases. It is not vendored here and is not run.

**What that means for a conformance claim.** Number serialisation is exercised by `values`, by the
RFC's own worked example, and by the `es6-number-boundaries` vector (1e21, 1e20, 1e-7, 5e-324, the
largest double, and negative zero) — the boundaries where a naive formatter, a shortest-round-trip
printer and a fixed-precision printer diverge. It is **not** exercised exhaustively, so an
implementation passing this corpus has agreed with RFC 8785 on every published fixture and on the
stated boundaries, and has **not** been shown to agree on all 2^64 doubles.

**How this closes.** Vendor or stream the number corpus and run it, or state a defensible sample size
and a published hash target for that sample. Until then this row is OPEN, and no document in this
tree claims exhaustive number conformance.
