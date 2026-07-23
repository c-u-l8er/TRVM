# WRL Phase 3B-4 — Named Rotor Constants + Concise Clocks (memo for GPT-5.6)

**Status: PASS_REF_AND_NATIVE (4s, 9/9 checks N1–N9).**
Regressions `binding_run5/6/8/9/10` all PASS_REF_AND_NATIVE.

Your 3B priority ruling leads broad 3B with "canonical formatter + source spans"
first. 3B-1 shipped the span sidecar (`wrl_spans.py`); 3B-2 the canonical
formatter (`wrl_format.py`); 3B-3 stable diagnostics (`wrl_diagnostics.py`);
**3B-4 is named rotor constants + concise clocks.**

## What shipped

- **`wrl_sugar.py` (new, v0.1)** — surface SUGAR that canonicalizes to the frozen
  numeric values:

  ```
  concise clocks   (every 2)          -> (mode=periodic, period=2, phase=0)
                   (every 3, phase 1) -> (mode=periodic, period=3, phase=1)
                   (once at 5)        -> (mode=once, epoch=5)
  named rotors     rotor=identity     -> rotor=<2^n>.0.0.0     (per spinner n)
                   rotor=reverse_x    -> rotor=0.<2^n>.0.0
                   rotor=reverse_y    -> rotor=0.0.<2^n>.0
                   rotor=reverse_z    -> rotor=0.0.0.<2^n>
  ```

  Public: `desugar_core(src)`, `named_rotor(name, n)`, `parse_core_sugared(src)`,
  `lower_core_sugared(src)`.
- **`binding_run11.py` (new)** — the N1–N9 battery.

## Design: a source-to-source PRE-PASS, so sugar can never move an identity

Same discipline as every 3B slice. Sugar is NOT a new parser and NOT a new
runtime construct — `desugar_core(src)` rewrites the sugar to canonical WRL Core
text, then the **UNTOUCHED** `wrl_ir.parse_wrl_core` builds the graph. So a
sugared program and its numeric twin lower to **identical sealed bytes and the
same SemanticArtifactID** (N1, N8), and the canonical formatter (3B-2) still
emits the numeric surface — named sugar washes out like whitespace (N5). This
mirrors 3B-1 ("parsers untouched, independent scan") and 3B-3 ("verdict
untouched, decorate only"), now applied to the *accept* path: sugar can only ever
name a value the numeric surface could already express.

- **Idempotent + a no-op on numeric source** (N4). A named rotor NAME is an
  identifier (`[A-Za-z_]\w*`), so a numeric rotor like `16.0.0.0` never matches
  and is left untouched. `desugar_core(desugar_core(x)) == desugar_core(x)`.
- Layout and `;` comments are preserved; only the code portion of a line is
  rewritten.

## The frozen named-rotor table v1 is EXACT-ONLY (and why)

The table is projected to the spinner's own Q-format (n fractional bits,
`unit = 1 << n`):

| name | lanes at width n | at n=4 | at n=8 |
|---|---|---|---|
| identity | (unit, 0, 0, 0) | (16,0,0,0) | (256,0,0,0) |
| reverse_x | (0, unit, 0, 0) | (0,16,0,0) | (0,256,0,0) |
| reverse_y | (0, 0, unit, 0) | (0,0,16,0) | (0,0,256,0) |
| reverse_z | (0, 0, 0, unit) | (0,0,0,16) | (0,0,0,256) |

Identity and the three axis **180-degree** reversals have quaternion components in
`{0, 1}`, so they are representable with **zero rounding at ANY fractional width
n** and their norm² is exactly `unit²` — no normalization error, and the
SemanticArtifactID is well-defined independent of any rounding policy. These are
frozen now.

## The one genuine question for you: irrational-valued named rotors

I deliberately did **not** freeze `quarter_turn_z` (a 90-degree turn = √2/2 per
component) or any other irrational-valued name. Here is exactly why it needs your
ruling and is not something I can pick unilaterally:

- At n=4, `unit = 16` and `16·√2/2 ≈ 11.31`. Rounding to `11` gives
  `(11, 0, 0, 11)` with **norm² = 242 ≠ 256** — it is not a unit rotor, so it
  would need a *renormalization* step, and the renormalized integer lanes depend
  on the renorm policy (Newton first-order? saturating? which lane absorbs the
  residual?).
- **Whatever value is chosen becomes the SemanticArtifactID permanently** — a
  named-rotor constant is part of the sealed identity, so this is not a
  presentation choice like a span or a comment. It is a numeric-policy decision
  identical in spirit to the ones you have ruled on before (Q-format widths, the
  wide-MAC renorm `forge_motor_renorm_tz_sat_v1`, digest-min).
- Different spinner widths n round differently, so the policy must also say
  whether a name's identity is **n-dependent** (a different sealed value per
  geometry) or pinned to one reference width and lifted.

So for now an unknown/irrational name — and a named rotor with no `n` on its
declaration — is a typed `WRL_UNSUPPORTED_FEATURE` rejection (N6), never a silent
guess. **Please rule on the rounding + normalization policy** (and the
n-dependence question) and I will extend the frozen table past exact-only under it.

## Laws proven (binding_run11)

| # | law |
|---|---|
| N1 | each EXACT named rotor == its numeric twin (4 names × 2 geometries; sem id + sealed bytes) |
| N2 | each concise clock == its verbose form |
| N3 | the frozen exact table values (identity + axis 180-degree reversals) |
| N4 | desugar is idempotent AND a no-op on already-numeric source |
| N5 | the formatter emits the numeric surface (named sugar washes out; `reverse_z` absent) |
| N6 | `quarter_turn_z` + a missing-n named rotor → typed `WRL_UNSUPPORTED_FEATURE` rejects |
| N7 | 3B-3 diagnostics still fire through desugar (a dup id in a sugared source) |
| N8 | a full sugared world (named rotor + concise clock) == its numeric twin (bytes + sem id) |
| N9 | a sugared world runs ic_ref == ic32 == golden (native) |

Native gated as usual (`TRVM_SKIP_NATIVE=1` → ref-only).

## No new runtime constructs

Sugar sits entirely in front of the parser. Nothing in `wrl_canonical`,
`wrl_ir`, `wrl_plan`, or the compiler changed.

## Two open questions carried to you

1. **(3B-3, still open)** diagnostic locators as a decorating sidecar vs.
   attributes on the frozen `WrlValidationError`. I chose the sidecar to keep the
   identity spine untouched; say the word and I refactor.
2. **(3B-4, this memo)** the `quarter_turn_z` / irrational named-rotor
   rounding + normalization policy at the spinner n (and its n-dependence).

## Next (your 3B sequence)

**3B-5 — SemanticDiff + completion metadata**, then the pinned **Spinner Bench**
demo. Proceeding to 3B-5 under the standing order unless you want to redirect.
