#!/usr/bin/env python3
"""phase_pin_lint.py — M-10. The tenth known apparatus failure species.

    HISTORY MAY BE PINNED. LIVE STATE MUST BE DERIVED.

That is the whole rule, and it is worth the file because the tree has now paid
for it four times in two rounds:

    B4 -> B5   `grid lowering_spike.inputs_model.implemented === false`, an
               assertion correct while the port was open, which became the
               mechanism preventing the record from admitting the port closed.
               Four passes stale.
    B5         the negative case guarding it forged `implemented = True` and
               expected "must stay false" — so the battery was ENFORCING the
               stale value, and 298/298 stayed green over a record that
               contradicted the code.
    B5         `entries.find(x => x.revision === 3 && x.canonical)`, hand-edited
               on every supersession, in grid_check.
    B5         three battery cases selecting `revision == 3`. When @4 became
               canonical they went on mutating a superseded revision nothing
               asserts over, and reported their own forgeries as UNCAUGHT.

The shape is always the same: an instrument whose intended subject is the LIVE
state locates or characterises that subject with a literal belonging to one
PHASE. The artifact stays green and the instrument stops measuring.

WHAT THIS DELIBERATELY DOES NOT DO
──────────────────────────────────
It is not "no literals in expectations". That would be too blunt and would fire
on the many cases whose subject really is history — `implementation-provenance@1`
must stay on the record AS a false claim, `film.native-emission@1` carries the
readback record no later revision repeats. Those are correct exactly because
they are pinned; deriving them would make them stop testing history.

So the exemption is EXPLICIT and carries a reason:

    # HISTORY_PIN_OK: this case's subject is @1, kept as history

Per GPT's ruling, and per this tree's own habit: the bounded catalogue holds the
species that have actually gone wrong here, and stops.

Usage:  phase_pin_lint.py <case-body-file> <want-string>
        prints one violation per line; exit 1 if any, 0 if clean.
"""
import re
import sys

EXEMPT = "HISTORY_PIN_OK"

# Each rule is (name, regex, where, why). `where` is "body", "want" or "both".
RULES = [
    ("revision-selected-by-number",
     r"""\[\s*['"]revision['"]\s*\]\s*==\s*\d+|(?<![\w.])revision\s*==\s*\d+""",
     "body",
     "selects a law revision by NUMBER. When that revision is superseded the case "
     "goes on mutating history, which nothing asserts over — it stops testing and "
     "says nothing. Select by `e.get('canonical')` unless the subject IS history"),

    ("polarity-pinned-expectation",
     r"must stay (?:true|false)\b",
     "want",
     "expects a POLARITY the round can invert. `must stay false` was correct while "
     "the feature was open and became a case enforcing a lie the moment it closed. "
     "Expect the DERIVATION — that the record equals the live value — not a value"),

    ("canonical-selected-by-at-revision",
     r"""canonical['"]?\s*\]?\s*(?:==|=)\s*True[\s\S]{0,80}?revision['"]?\s*\]?\s*==\s*\d+""",
     "body",
     "makes a numbered revision canonical, or selects the canonical one by number. "
     "Canonicity is the live property; the number is a phase label for it"),
]


def violations(body: str, want: str):
    if EXEMPT in body or EXEMPT in want:
        return []
    out = []
    for name, rx, where, why in RULES:
        hay = {"body": body, "want": want, "both": body + "\n" + want}[where]
        m = re.search(rx, hay)
        if m:
            out.append(f"{name}: {why} [matched {m.group(0)[:60]!r}]")
    return out


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: phase_pin_lint.py <case-body-file> <want-string>", file=sys.stderr)
        return 2
    try:
        body = open(sys.argv[1], encoding="utf-8").read()
    except OSError:
        # A LINT THAT CANNOT READ ITS SUBJECT MUST NOT REPORT CLEAN — which is
        # M-1's finding exactly, one instrument over: the banned-phrase tripwire
        # that scanned the empty string and reported success.
        print("phase-pin-lint: could not read the case body — refusing to report clean")
        return 1
    found = violations(body, sys.argv[2])
    for v in found:
        print(v)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
