# Law Ratification — 2026-07-22

Additive, permanent record of an architect ruling on the TRVM constitution.
This file is the **canonical provenance** for the ratifications below. It does
not edit, rename, or re-cite any frozen historical battery (`binding_run*.py`,
`fixture.py`, `compiler.py`). It updates only the governance index `LAWS.md`
and the additive checker `tools/laws_check.py`.

Where a law is promoted to Tier A here, its provenance is **this ruling**, not
a fabricated historical quote. The surviving citations are the *witnesses* that
earned the invariant; this ruling is the canonical *statement*.

---

## Ratified to Tier A (CANONICAL)

### Law 4 — ratified

> **Law 4 — Every reported reduction cost must name the reduction strategy
> under which it was measured.**

Eager/`first`, lazy-reference, or any later scheduler are different measurement
regimes; an unlabeled step count is not an honest result. This is exactly the
invariant enforced by the three surviving citations
(`forge/binding_run3.py:177`, `forge/binding_run3b.py:265`,
`forge/binding_run3c.py:307`).

Provenance: this ruling.

### Law 6 — ratified (now GLOBAL, no longer horizon-scoped)

> **Law 6 — A canonical shared observable must carry every state variable that
> can determine future behavior; if two states can lead to different futures,
> their Film bytes must differ.**

This unifies all surviving witnesses: different rotor state; different receipt
state; different one-shot/done-latch state; and any other hidden state that
changes a future transition. The later native Once work closed the temporary
horizon-scoped limitation, so the law is now **global**.

Witnesses: `forge/binding_run3k.py:32,313,325`, `forge/binding_run3h.py:21,285`.

Provenance: this ruling.

### Law 23 — ratified

> **Law 23 — A memoization key must include every dimension over which the
> memoized generator ranges.**

A key that omits depth, size, profile, policy or another ranged dimension
silently aliases different computations and can manufacture false coverage or
emergence results.

Witness (candidate): `TRVM_july_21_research/async-memokey-fix.patch`.

Provenance: this ruling.

---

## Reserved (canonical statement lost)

Laws **1, 2, 3, and 7** are marked:

```
RESERVED — canonical statement lost
```

They are **not** reconstructed laws. Do not invent them.

- the IDs remain reserved;
- they have no binding authority;
- they may not be cited;
- they may not be reused for new laws;
- they can be restored only if real historical text is found, or a later
  architect explicitly assigns a new statement.

---

## Series II numbering

There was no coherent numbered **20–25 series**. Only the attested numbers
survive:

```
Law 10
Law 13
Law 23
Law 26
```

Laws **20, 21, 22, 24, and 25** are removed from the numbered law index. Their
useful paraphrases are preserved in the `LAWS.md` appendix
**"Unnumbered candidate principles"**. They become laws only through a future
explicit ratification.

---

## Frozen-file ruling

Do **not** edit the historical `binding_run*.py`, `fixture.py`, or `compiler.py`
merely to modernize citations or print law metadata. The additive checker is
the correct enforcement layer.

For **future batteries only**, freeze this convention: a battery declares the
laws it asserts and prints them in its final verdict, e.g.

```python
ASSERTS_LAWS = ("L4", "L6")
```

Do not retrofit historical files.

---

## Provenance-rule typo fix

The `LAWS.md` provenance rule previously wrote the promotion direction as
`A→B`. Promotion runs from Tier **B** (reconstructed) to Tier **A**
(canonical), so the correct direction is:

```
B→A promotion
```

---

## Verification

After applying the `LAWS.md` and `tools/laws_check.py` edits ruled here:

```bash
python3 tools/laws_check.py --strict
```

Expected:

```
RESULT: OK
```

No historical battery modification is needed.
